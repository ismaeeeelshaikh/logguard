import os
import mlflow
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, accuracy_score
import joblib

class IFTrainer:
    """Trains and logs an Isolation Forest model using MLflow."""
    
    def __init__(self, experiment_name: str = "LogAnomalyDetection"):
        self.experiment_name = experiment_name
        
        # Configure MLflow
        mlflow.set_tracking_uri("http://localhost:5000")
        mlflow.set_experiment(experiment_name)
        
    def train_and_evaluate(self, X_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray,
                           n_estimators: int = 200, contamination: float = 0.05, 
                           max_samples: str = 'auto', random_state: int = 42) -> Pipeline:
        """Trains IF, evaluates on test set, and logs metrics/model to MLflow."""
        
        print("Starting MLflow Run...")
        with mlflow.start_run(run_name=f"IF_n{n_estimators}_c{contamination}") as run:
            # 1. Pipeline Definition
            pipeline = Pipeline([
                ('scaler', StandardScaler()),
                ('iforest', IsolationForest(
                    n_estimators=n_estimators,
                    contamination=contamination,
                    max_samples=max_samples,
                    random_state=random_state,
                    n_jobs=-1
                ))
            ])
            
            # 2. Log Parameters
            mlflow.log_params({
                "model_type": "IsolationForest",
                "n_estimators": n_estimators,
                "contamination": contamination,
                "max_samples": max_samples,
                "random_state": random_state,
                "scaler": "StandardScaler"
            })
            
            print(f"Training Isolation Forest (n_estimators={n_estimators}, contamination={contamination})...")
            # 3. Train
            pipeline.fit(X_train)
            
            # 4. Predict
            # IF returns -1 for anomaly, 1 for normal. Convert to 1 for anomaly, 0 for normal
            print("Evaluating model...")
            y_pred_raw = pipeline.predict(X_test)
            y_pred = np.where(y_pred_raw == -1, 1, 0)
            
            # 5. Metrics Calculation
            metrics = {
                "precision": precision_score(y_test, y_pred, zero_division=0),
                "recall": recall_score(y_test, y_pred, zero_division=0),
                "f1_score": f1_score(y_test, y_pred, zero_division=0),
                "accuracy": accuracy_score(y_test, y_pred),
                "roc_auc": roc_auc_score(y_test, y_pred)
            }
            
            # 6. Log Metrics
            mlflow.log_metrics(metrics)
            print("Metrics:", metrics)
            
            # 7. Log Model
            print("Saving model to MLflow and local disk...")
            
            # Create models dir if not exists
            if not os.path.exists('/home/krisss/logguard/ml/models/saved'):
                os.makedirs('/home/krisss/logguard/ml/models/saved')
            
            # Save local copy
            model_path = '/home/krisss/logguard/ml/models/saved/isolation_forest.joblib'
            joblib.dump(pipeline, model_path)
            
            # Log to MLflow
            mlflow.sklearn.log_model(
                sk_model=pipeline,
                artifact_path="isolation_forest_model",
                registered_model_name="IsolationForest_AnomalyDetector"
            )
            
            print(f"Run completed. Run ID: {run.info.run_id}")
            
            return pipeline

if __name__ == "__main__":
    import sys
    sys.path.append("/home/krisss/logguard")
    from ml.data.data_loader import load_data
    
    # Load Data
    print("Loading data...")
    X_train, X_val, X_test, y_test = load_data(
        n_normal_train=10000, 
        n_normal_val=2000, 
        n_test=3000, 
        anomaly_ratio=0.05
    )
    
    # Train
    trainer = IFTrainer()
    trainer.train_and_evaluate(
        X_train=X_train, 
        X_test=X_test, 
        y_test=y_test,
        n_estimators=150,
        contamination=0.06
    )
