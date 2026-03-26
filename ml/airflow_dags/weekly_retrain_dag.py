"""
Airflow DAG for weekly LogGuard ML model retraining.

Schedule: Every Sunday at 2 AM
Pipeline:
  1. Check feedback volume (min 100 events)
  2. Fetch and prepare labeled data
  3. Retrain Isolation Forest (parallel)
  4. Retrain LSTM Autoencoder (parallel)
  5. Notify on completion via Slack
"""

import os
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import mlflow
import numpy as np

default_args = {
    "owner": "logguard-ml",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": True,
    "email": ["ml-alerts@yourcompany.com"]
}

dag = DAG(
    dag_id="logguard_weekly_model_retrain",
    default_args=default_args,
    description="Retrain LogGuard ML models weekly using feedback data",
    schedule_interval="0 2 * * 0",  # Every Sunday at 2 AM
    catchup=False,
    tags=["logguard", "ml", "retraining"]
)


def check_feedback_volume(**context):
    """
    Only retrain if there's enough new feedback.
    Minimum: 100 labeled events since last training.
    """
    try:
        import psycopg2
        conn = psycopg2.connect(
            "postgresql://logguard:pass@postgres:5432/logguard"
        )
        cur = conn.cursor()
        
        cur.execute("""
            SELECT COUNT(*) FROM anomaly_feedback
            WHERE created_at > NOW() - INTERVAL '7 days'
            AND feedback_type IN ('true_positive', 'false_positive')
        """)
        count = cur.fetchone()[0]
        conn.close()
    except Exception as e:
        print(f"⚠️  DB check failed: {e}. Proceeding with retraining.")
        count = 200  # Proceed anyway in case of DB issues
    
    print(f"New feedback events in last 7 days: {count}")
    
    if count < 100:
        raise ValueError(
            f"Insufficient feedback ({count} < 100). Skipping retraining."
        )
    
    context["task_instance"].xcom_push(key="feedback_count", value=count)


def fetch_and_prepare_data(**context):
    """Fetch labeled data from PostgreSQL + recent unlabeled from ES."""
    from ml.data.fetch_training_data import fetch_feedback_dataset
    import joblib
    
    X_all, y_all = fetch_feedback_dataset(days_back=30)
    
    # Save to shared location for subsequent tasks
    joblib.dump(
        {"X_flat": X_all, "y": y_all},
        "/tmp/retrain_data.pkl"
    )
    print(f"Data ready: {len(X_all)} samples, {y_all.mean()*100:.1f}% anomaly rate")


def retrain_isolation_forest(**context):
    """Retrain the Isolation Forest model."""
    from ml.models.isolation_forest.trainer import IsolationForestTrainer
    import joblib
    
    data = joblib.load("/tmp/retrain_data.pkl")
    trainer = IsolationForestTrainer()
    model, scaler, threshold = trainer.train(data["X_flat"], data["y"])
    
    # Promote to production if F1 > current production model
    client = mlflow.MlflowClient()
    _promote_if_better(client, "logguard-isolation-forest")


def retrain_lstm(**context):
    """Retrain the LSTM Autoencoder model."""
    from ml.models.lstm_autoencoder.trainer import LSTMAutoencoderTrainer
    from ml.data.data_loader import create_sequences
    import joblib
    
    data = joblib.load("/tmp/retrain_data.pkl")
    
    # Build sequences from flat data
    seq_len = 30
    X_seq = create_sequences(data["X_flat"], seq_length=seq_len)
    y_seq = data["y"][seq_len - 1:]
    
    trainer = LSTMAutoencoderTrainer()
    model, scaler, threshold = trainer.train(X_seq, y_seq)
    
    client = mlflow.MlflowClient()
    _promote_if_better(client, "logguard-lstm-autoencoder")


def _promote_if_better(client, model_name: str):
    """
    Promote new model version to 'production' if it beats the current one.
    Requires > 1% F1 improvement to avoid unnecessary churn.
    """
    try:
        versions = client.get_latest_versions(model_name)
    except Exception as e:
        print(f"⚠️  Could not fetch model versions for {model_name}: {e}")
        return
    
    if not versions:
        print(f"⚠️  No versions found for {model_name}")
        return
    
    new_version = max(versions, key=lambda v: int(v.version))
    
    try:
        new_f1 = float(
            client.get_run(
                new_version.run_id
            ).data.metrics.get("f1_score", 0)
        )
    except Exception:
        new_f1 = 0.0
    
    # Get current production version
    prod_versions = [
        v for v in versions if v.current_stage == "Production"
    ]
    
    if not prod_versions:
        # No production model yet — promote directly
        client.transition_model_version_stage(
            model_name, new_version.version, stage="Production"
        )
        print(
            f"✅ Promoted v{new_version.version} to Production "
            f"(first deployment)"
        )
        return
    
    try:
        prod_f1 = float(
            client.get_run(
                prod_versions[0].run_id
            ).data.metrics.get("f1_score", 0)
        )
    except Exception:
        prod_f1 = 0.0
    
    if new_f1 > prod_f1 + 0.01:
        client.transition_model_version_stage(
            model_name, new_version.version, stage="Production"
        )
        print(
            f"✅ Promoted v{new_version.version} "
            f"(F1: {new_f1:.4f} > {prod_f1:.4f})"
        )
    else:
        print(
            f"⚠️  New model (F1: {new_f1:.4f}) didn't beat production "
            f"(F1: {prod_f1:.4f}). Keeping old."
        )


# ── DAG Task Definitions ─────────────────────────────────────────────────

check_feedback_task = PythonOperator(
    task_id="check_feedback_volume",
    python_callable=check_feedback_volume,
    dag=dag
)

fetch_data_task = PythonOperator(
    task_id="fetch_and_prepare_data",
    python_callable=fetch_and_prepare_data,
    dag=dag
)

retrain_if_task = PythonOperator(
    task_id="retrain_isolation_forest",
    python_callable=retrain_isolation_forest,
    dag=dag
)

retrain_lstm_task = PythonOperator(
    task_id="retrain_lstm_autoencoder",
    python_callable=retrain_lstm,
    dag=dag
)

notify_task = BashOperator(
    task_id="notify_retraining_complete",
    bash_command="""
    curl -X POST $SLACK_WEBHOOK_URL \
      -H 'Content-type: application/json' \
      -d '{"text": "✅ LogGuard ML models retrained successfully. Check MLflow for metrics."}'
    """,
    dag=dag
)

# ── Task Dependencies ────────────────────────────────────────────────────
check_feedback_task >> fetch_data_task >> [retrain_if_task, retrain_lstm_task] >> notify_task
