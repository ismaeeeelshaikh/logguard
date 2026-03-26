# 🤖 LogGuard — Person 2: ML Engineer
## Role: Machine Learning & Model Training Lead

---

## 📌 Your Responsibility Summary

Tumhara kaam LogGuard ka "dimag" banana hai. Tum do ML models develop karoge:
1. **Isolation Forest** — Point anomalies detect karne ke liye (ek log event jo normal nahi lagta)
2. **LSTM Autoencoder** — Sequence anomalies detect karne ke liye (log patterns jo historically galat signal dete hain)

Tumhe models train karne ke saath-saath inhe production-ready banana hai: versioned, reproducible, aur automatically retrainable jab naya feedback aaye.

**Tumhari output directly ML inference service ka input hai (Person 3 ka kaam).**

---

## 🧰 Tech Stack (Tumhara Arsenal)

| Technology | Purpose | Seekhne ki zaroorat |
|---|---|---|
| **Python 3.11** | Primary language | High ⭐⭐⭐ |
| **scikit-learn** | Isolation Forest implementation | Medium ⭐⭐ |
| **TensorFlow 2.x / Keras** | LSTM Autoencoder | High ⭐⭐⭐ |
| **MLflow** | Experiment tracking + Model Registry | High ⭐⭐⭐ |
| **NumPy / Pandas** | Data manipulation | Medium ⭐⭐ |
| **Apache Airflow** | Retraining pipeline orchestration | Medium ⭐⭐ |
| **Jupyter Notebooks** | Experimentation + EDA | Low ⭐ |
| **Matplotlib / Seaborn** | Model evaluation plots | Low ⭐ |
| **Elasticsearch-py** | Fetch historical logs for training | Low ⭐ |
| **Docker** | Containerize training jobs | Medium ⭐⭐ |

---

## 📁 Folder Structure (Tumhara Code)

```
logguard/
├── ml/
│   ├── notebooks/
│   │   ├── 01_eda_log_analysis.ipynb         ← Data exploration
│   │   ├── 02_isolation_forest_training.ipynb ← IF model experiments
│   │   └── 03_lstm_autoencoder_training.ipynb ← LSTM model experiments
│   │
│   ├── data/
│   │   ├── fetch_training_data.py            ← Pull data from Elasticsearch
│   │   ├── data_loader.py                    ← Dataset class
│   │   └── synthetic_generator.py            ← Generate training data with anomalies
│   │
│   ├── features/
│   │   ├── feature_config.py                 ← Feature names, ranges, vocab size
│   │   └── preprocessor.py                   ← Scaler, encoder (must match Flink output!)
│   │
│   ├── models/
│   │   ├── isolation_forest/
│   │   │   ├── trainer.py                    ← Training logic
│   │   │   ├── evaluator.py                  ← Metrics, threshold tuning
│   │   │   └── hyperparams.yaml              ← Config file
│   │   └── lstm_autoencoder/
│   │       ├── architecture.py               ← Model definition
│   │       ├── trainer.py                    ← Training loop
│   │       ├── evaluator.py                  ← Reconstruction error analysis
│   │       └── hyperparams.yaml              ← Config file
│   │
│   ├── scoring/
│   │   ├── hybrid_scorer.py                  ← Combines IF + LSTM scores
│   │   └── threshold_manager.py              ← Dynamic threshold computation
│   │
│   ├── pipelines/
│   │   ├── training_pipeline.py              ← End-to-end training orchestration
│   │   └── retraining_pipeline.py            ← Feedback-based retraining
│   │
│   ├── airflow_dags/
│   │   └── weekly_retrain_dag.py             ← Airflow DAG for auto-retraining
│   │
│   ├── tests/
│   │   ├── test_isolation_forest.py
│   │   ├── test_lstm.py
│   │   └── test_hybrid_scorer.py
│   │
│   └── mlflow_server/
│       └── docker-compose.mlflow.yml         ← MLflow tracking server setup
```

---

## 🚀 Phase 1: MLflow Setup + Data Collection (Week 5)

### Step 1.1 — MLflow Server Setup

`ml/mlflow_server/docker-compose.mlflow.yml`:
```yaml
version: '3.8'
services:
  mlflow:
    image: ghcr.io/mlflow/mlflow:v2.9.2
    ports:
      - "5000:5000"
    environment:
      MLFLOW_BACKEND_STORE_URI: postgresql://mlflow:mlflow@postgres/mlflow
      MLFLOW_ARTIFACT_ROOT: s3://logguard-mlflow-artifacts/
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
      MLFLOW_S3_ENDPOINT_URL: http://minio:9000  # Use MinIO for local dev
    command: >
      mlflow server
        --host 0.0.0.0
        --port 5000
        --backend-store-uri postgresql://mlflow:mlflow@postgres/mlflow
        --default-artifact-root s3://logguard-mlflow-artifacts/
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: mlflow
      POSTGRES_PASSWORD: mlflow
      POSTGRES_DB: mlflow
    volumes:
      - mlflow_pgdata:/var/lib/postgresql/data

  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin123
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data

volumes:
  mlflow_pgdata:
  minio_data:
```

```bash
# Start MLflow server
docker-compose -f ml/mlflow_server/docker-compose.mlflow.yml up -d

# MLflow UI is now at: http://localhost:5000
```

### Step 1.2 — Synthetic Data Generator

`ml/data/synthetic_generator.py`:
```python
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
from typing import Tuple

FEATURE_NAMES = [
    "log_volume",
    "error_rate",
    "warn_rate",
    "unique_template_count",
    "template_entropy",
    "avg_response_time_ms",
    "p95_response_time_ms",
    # template_vector[0..99] will be added separately
]

class LogDataGenerator:
    """
    Generates realistic synthetic log feature data for model training.
    
    Normal behavior: Gaussian distributions around typical server metrics.
    Anomaly types:
      1. Spike anomaly     — sudden surge in error_rate or response_time
      2. Volume anomaly    — dramatic drop in log_volume (server silent)
      3. Pattern anomaly   — unusual template distribution (new attack pattern)
      4. Memory leak       — gradual increase in response_time over sequence
    """
    
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        random.seed(seed)
    
    def generate_normal_window(self) -> dict:
        """Generate one normal 60-second window feature vector."""
        log_volume = max(10, int(np.random.normal(500, 80)))
        error_rate = max(0, min(1, np.random.beta(1.5, 30)))  # Usually < 5%
        warn_rate  = max(0, min(1, np.random.beta(3, 20)))
        unique_templates = int(np.random.normal(12, 3))
        entropy    = max(0, np.random.normal(2.8, 0.4))
        avg_rt     = max(10, np.random.normal(150, 30))
        p95_rt     = avg_rt * np.random.uniform(1.8, 2.5)
        
        # Template vector: sparse, mostly zeros
        template_vector = np.zeros(100)
        active_templates = random.sample(range(100), k=min(unique_templates, 20))
        for idx in active_templates:
            template_vector[idx] = np.random.dirichlet(np.ones(len(active_templates)))[0]
        
        return {
            "log_volume": log_volume,
            "error_rate": error_rate,
            "warn_rate": warn_rate,
            "unique_template_count": unique_templates,
            "template_entropy": entropy,
            "avg_response_time_ms": avg_rt,
            "p95_response_time_ms": p95_rt,
            "template_vector": template_vector.tolist()
        }
    
    def generate_anomaly_window(self, anomaly_type: str = "random") -> dict:
        """Generate one anomalous window."""
        if anomaly_type == "random":
            anomaly_type = random.choice(["spike", "silent", "pattern", "slowdown"])
        
        base = self.generate_normal_window()
        
        if anomaly_type == "spike":
            base["error_rate"] = np.random.uniform(0.3, 0.9)
            base["log_volume"] = base["log_volume"] * random.uniform(3, 8)
            base["p95_response_time_ms"] = np.random.uniform(8000, 30000)
            
        elif anomaly_type == "silent":
            # Server going quiet — possibly crashed
            base["log_volume"] = random.randint(0, 15)
            base["error_rate"] = 0.0
            
        elif anomaly_type == "pattern":
            # Unusual template distribution — possible injection attack
            base["template_entropy"] = np.random.uniform(4.5, 6.0)
            base["unique_template_count"] = random.randint(40, 80)
            # Activate many unusual template slots
            tv = np.zeros(100)
            for i in range(60):
                tv[random.randint(0, 99)] = random.uniform(0.01, 0.05)
            base["template_vector"] = tv.tolist()
            
        elif anomaly_type == "slowdown":
            # Gradual memory leak / resource exhaustion
            base["avg_response_time_ms"] = np.random.uniform(3000, 10000)
            base["p95_response_time_ms"] = np.random.uniform(8000, 25000)
            base["error_rate"] = np.random.uniform(0.1, 0.3)
        
        return base
    
    def generate_dataset(
        self,
        n_normal: int = 50000,
        n_anomaly: int = 2500,  # 5% contamination
        sequence_length: int = 30  # for LSTM
    ) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
        """
        Returns:
          X_flat   — shape (n_samples, n_features)  — for Isolation Forest
          X_seq    — shape (n_samples, seq_len, n_features) — for LSTM  
          y_labels — shape (n_samples,)  — 0=normal, 1=anomaly
        """
        
        print(f"Generating {n_normal} normal + {n_anomaly} anomaly samples...")
        
        all_windows = []
        all_labels  = []
        
        for _ in range(n_normal):
            all_windows.append(self.generate_normal_window())
            all_labels.append(0)
        
        for _ in range(n_anomaly):
            all_windows.append(self.generate_anomaly_window())
            all_labels.append(1)
        
        # Flatten template_vector into individual columns
        rows = []
        for w in all_windows:
            flat = {k: v for k, v in w.items() if k != "template_vector"}
            for i, val in enumerate(w["template_vector"]):
                flat[f"template_{i:03d}"] = val
            rows.append(flat)
        
        df = pd.DataFrame(rows)
        y  = np.array(all_labels)
        
        # Shuffle
        idx = np.random.permutation(len(df))
        df  = df.iloc[idx].reset_index(drop=True)
        y   = y[idx]
        
        # Build sequence dataset for LSTM
        X_flat = df.values.astype(np.float32)
        X_seq  = self._build_sequences(X_flat, y, sequence_length)
        
        print(f"✅ Dataset ready: X_flat={X_flat.shape}, X_seq={X_seq.shape}")
        print(f"   Anomaly rate: {y.mean()*100:.1f}%")
        
        return df, X_flat, X_seq, y
    
    def _build_sequences(
        self,
        X: np.ndarray,
        y: np.ndarray,
        seq_len: int
    ) -> np.ndarray:
        """Build overlapping sequences for LSTM training."""
        sequences = []
        for i in range(len(X) - seq_len + 1):
            sequences.append(X[i:i + seq_len])
        # Pad beginning
        padding = [sequences[0]] * (seq_len - 1)
        sequences = padding + sequences
        return np.array(sequences, dtype=np.float32)


if __name__ == "__main__":
    gen = LogDataGenerator()
    df, X_flat, X_seq, y = gen.generate_dataset()
    
    # Save for notebook experimentation
    df.to_parquet("data/training_data.parquet", index=False)
    np.save("data/X_flat.npy", X_flat)
    np.save("data/X_seq.npy", X_seq)
    np.save("data/y_labels.npy", y)
    print("Saved to data/ directory.")
```

---

## 🚀 Phase 2: Isolation Forest Model (Week 6)

### Step 2.1 — IF Trainer

`ml/models/isolation_forest/trainer.py`:
```python
import mlflow
import mlflow.sklearn
import numpy as np
import yaml
import json
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score,
    confusion_matrix
)
from pathlib import Path
import joblib

class IsolationForestTrainer:
    
    def __init__(self, config_path: str = "hyperparams.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        
        mlflow.set_tracking_uri("http://localhost:5000")
        mlflow.set_experiment("logguard-isolation-forest")
    
    def train(self, X_flat: np.ndarray, y_labels: np.ndarray) -> IsolationForest:
        """
        Train Isolation Forest with proper MLflow tracking.
        """
        
        # Split: use labels only for evaluation, NOT training
        # IF is unsupervised — only trained on normal data
        X_normal = X_flat[y_labels == 0]
        X_test   = X_flat
        
        X_train, X_val_normal = train_test_split(X_normal, test_size=0.1, random_state=42)
        
        with mlflow.start_run(run_name="isolation-forest-v1") as run:
            
            # ── Log hyperparameters ───────────────────────
            params = self.config["isolation_forest"]
            mlflow.log_params(params)
            
            # ── Fit scaler on normal training data ────────
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled  = scaler.transform(X_test)
            
            # ── Train Isolation Forest ────────────────────
            model = IsolationForest(
                n_estimators=params["n_estimators"],
                contamination=params["contamination"],
                max_samples=params["max_samples"],
                max_features=params["max_features"],
                bootstrap=params["bootstrap"],
                n_jobs=-1,
                random_state=42
            )
            
            model.fit(X_train_scaled)
            
            # ── Evaluate ──────────────────────────────────
            # IF returns: -1 (anomaly), 1 (normal) from predict()
            # decision_function() returns anomaly score (lower = more anomalous)
            raw_scores = model.decision_function(X_test_scaled)
            
            # Convert to [0, 1] where 1 = most anomalous
            anomaly_scores = 1 - (raw_scores - raw_scores.min()) / (raw_scores.max() - raw_scores.min())
            
            # Find optimal threshold using PR curve
            threshold, best_f1 = self._find_optimal_threshold(anomaly_scores, y_labels)
            
            y_pred = (anomaly_scores >= threshold).astype(int)
            
            # ── Metrics ───────────────────────────────────
            precision = precision_score(y_labels, y_pred)
            recall    = recall_score(y_labels, y_pred)
            f1        = f1_score(y_labels, y_pred)
            roc_auc   = roc_auc_score(y_labels, anomaly_scores)
            pr_auc    = average_precision_score(y_labels, anomaly_scores)
            
            mlflow.log_metrics({
                "precision": precision,
                "recall": recall,
                "f1_score": f1,
                "roc_auc": roc_auc,
                "pr_auc": pr_auc,
                "optimal_threshold": threshold,
                "train_samples": len(X_train),
                "test_samples": len(X_test)
            })
            
            print(f"\n{'='*50}")
            print(f"Isolation Forest Results:")
            print(f"  Precision: {precision:.4f}")
            print(f"  Recall:    {recall:.4f}")
            print(f"  F1 Score:  {f1:.4f}")
            print(f"  ROC AUC:   {roc_auc:.4f}")
            print(f"  PR AUC:    {pr_auc:.4f}")
            print(f"  Threshold: {threshold:.4f}")
            print(f"{'='*50}\n")
            
            # ── Save confusion matrix ──────────────────────
            cm = confusion_matrix(y_labels, y_pred)
            mlflow.log_text(str(cm), "confusion_matrix.txt")
            
            # ── Log model artifacts ───────────────────────
            # Save scaler separately (must be applied at inference time too)
            joblib.dump(scaler, "/tmp/if_scaler.pkl")
            mlflow.log_artifact("/tmp/if_scaler.pkl", "artifacts")
            
            # Log threshold for inference service to use
            threshold_config = {
                "if_threshold": float(threshold),
                "contamination": params["contamination"],
                "feature_count": X_flat.shape[1]
            }
            mlflow.log_dict(threshold_config, "threshold_config.json")
            
            # Register model to MLflow Model Registry
            mlflow.sklearn.log_model(
                sk_model=model,
                artifact_path="isolation_forest",
                registered_model_name="logguard-isolation-forest",
                signature=mlflow.models.infer_signature(X_train_scaled, anomaly_scores[:len(X_train)])
            )
            
            print(f"✅ Model registered in MLflow. Run ID: {run.info.run_id}")
        
        return model, scaler, threshold
    
    def _find_optimal_threshold(
        self,
        scores: np.ndarray,
        y_true: np.ndarray,
        beta: float = 1.0  # F1 (equal precision/recall weight)
    ) -> tuple:
        """
        Sweep thresholds and find the one that maximizes F-beta score.
        Higher beta = weight recall more (prefer catching all anomalies).
        """
        best_threshold = 0.5
        best_f = 0.0
        
        for threshold in np.arange(0.1, 0.99, 0.01):
            y_pred = (scores >= threshold).astype(int)
            if y_pred.sum() == 0:
                continue
            p = precision_score(y_true, y_pred, zero_division=0)
            r = recall_score(y_true, y_pred, zero_division=0)
            if p + r == 0:
                continue
            f = (1 + beta**2) * (p * r) / ((beta**2 * p) + r)
            if f > best_f:
                best_f = f
                best_threshold = threshold
        
        return best_threshold, best_f
```

`ml/models/isolation_forest/hyperparams.yaml`:
```yaml
isolation_forest:
  n_estimators: 200          # More trees = better accuracy, slower training
  contamination: 0.01        # Expected anomaly rate in training data
  max_samples: "auto"        # 256 samples per tree by default
  max_features: 1.0          # Use all features per tree
  bootstrap: false           # Sampling without replacement
```

---

## 🚀 Phase 3: LSTM Autoencoder (Week 7)

### Step 3.1 — LSTM Architecture

`ml/models/lstm_autoencoder/architecture.py`:
```python
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import numpy as np

def build_lstm_autoencoder(
    sequence_length: int = 30,
    n_features: int = 107,          # 7 base features + 100 template vector
    encoding_dim: int = 32,         # Bottleneck size
    lstm_units: list = [128, 64],   # Encoder layers
    dropout_rate: float = 0.2
) -> keras.Model:
    """
    LSTM Autoencoder for sequence anomaly detection.
    
    Architecture:
      Input (seq_len, n_features)
        → LSTM(128) → LSTM(64) → Dense(32) [ENCODER]
        → RepeatVector(seq_len)
        → LSTM(64) → LSTM(128) [DECODER]
        → TimeDistributed(Dense(n_features))
        → Output (seq_len, n_features)
    
    Anomaly score = Mean Squared Reconstruction Error
    If reconstruction is poor → sequence is anomalous
    """
    
    # ── ENCODER ──────────────────────────────────────────────
    encoder_input = keras.Input(shape=(sequence_length, n_features), name="encoder_input")
    
    x = layers.LSTM(
        lstm_units[0],
        return_sequences=True,
        name="encoder_lstm_1"
    )(encoder_input)
    x = layers.Dropout(dropout_rate)(x)
    
    x = layers.LSTM(
        lstm_units[1],
        return_sequences=False,  # Compress to fixed vector
        name="encoder_lstm_2"
    )(x)
    x = layers.Dropout(dropout_rate)(x)
    
    # Bottleneck: compressed representation
    encoded = layers.Dense(
        encoding_dim,
        activation="relu",
        name="bottleneck"
    )(x)
    
    # ── DECODER ──────────────────────────────────────────────
    # Repeat the bottleneck vector for each time step
    x = layers.RepeatVector(sequence_length, name="repeat_vector")(encoded)
    
    x = layers.LSTM(
        lstm_units[1],
        return_sequences=True,
        name="decoder_lstm_1"
    )(x)
    x = layers.Dropout(dropout_rate)(x)
    
    x = layers.LSTM(
        lstm_units[0],
        return_sequences=True,
        name="decoder_lstm_2"
    )(x)
    
    # Reconstruct each time step's feature vector
    decoded = layers.TimeDistributed(
        layers.Dense(n_features, activation="linear"),
        name="output"
    )(x)
    
    model = keras.Model(inputs=encoder_input, outputs=decoded, name="LSTM_Autoencoder")
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-3),
        loss="mse",
        metrics=["mae"]
    )
    
    return model


def get_reconstruction_errors(
    model: keras.Model,
    X_sequences: np.ndarray,
    batch_size: int = 256
) -> np.ndarray:
    """
    Compute per-sample reconstruction error (MSE).
    High error = anomalous sequence.
    
    Returns: array of shape (n_samples,) with MSE per sequence
    """
    X_reconstructed = model.predict(X_sequences, batch_size=batch_size, verbose=0)
    
    # MSE per sample (mean over sequence and feature dimensions)
    mse = np.mean(np.power(X_sequences - X_reconstructed, 2), axis=(1, 2))
    return mse
```

### Step 3.2 — LSTM Trainer

`ml/models/lstm_autoencoder/trainer.py`:
```python
import mlflow
import mlflow.tensorflow
import numpy as np
import json
import yaml
from tensorflow import keras
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
from architecture import build_lstm_autoencoder, get_reconstruction_errors

class LSTMAutoencoderTrainer:
    
    def __init__(self, config_path: str = "hyperparams.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        
        mlflow.set_tracking_uri("http://localhost:5000")
        mlflow.set_experiment("logguard-lstm-autoencoder")
    
    def train(
        self,
        X_sequences: np.ndarray,   # shape: (n, seq_len, n_features)
        y_labels: np.ndarray       # shape: (n,)  — only used for evaluation
    ):
        """
        Train LSTM Autoencoder on NORMAL sequences only.
        The model learns what "normal" looks like.
        When given anomalous sequences, reconstruction error will be high.
        """
        
        # ── Use only normal sequences for training ────────────
        X_normal = X_sequences[y_labels == 0]
        X_train, X_val = train_test_split(X_normal, test_size=0.1, random_state=42)
        
        params = self.config["lstm_autoencoder"]
        
        with mlflow.start_run(run_name="lstm-autoencoder-v1") as run:
            
            mlflow.log_params(params)
            mlflow.log_param("train_samples", len(X_train))
            mlflow.log_param("sequence_length", X_sequences.shape[1])
            mlflow.log_param("n_features", X_sequences.shape[2])
            
            # ── Normalize features ────────────────────────────
            n, seq_len, n_features = X_train.shape
            X_train_flat = X_train.reshape(-1, n_features)
            
            scaler = StandardScaler()
            X_train_norm = scaler.fit_transform(X_train_flat).reshape(n, seq_len, n_features)
            X_val_norm   = scaler.transform(X_val.reshape(-1, n_features)).reshape(
                len(X_val), seq_len, n_features
            )
            X_all_norm   = scaler.transform(X_sequences.reshape(-1, n_features)).reshape(
                len(X_sequences), seq_len, n_features
            )
            
            # ── Build model ───────────────────────────────────
            model = build_lstm_autoencoder(
                sequence_length=seq_len,
                n_features=n_features,
                encoding_dim=params["encoding_dim"],
                lstm_units=params["lstm_units"],
                dropout_rate=params["dropout_rate"]
            )
            
            print(model.summary())
            
            # ── Callbacks ─────────────────────────────────────
            callbacks = [
                keras.callbacks.EarlyStopping(
                    monitor="val_loss",
                    patience=params["patience"],
                    restore_best_weights=True
                ),
                keras.callbacks.ReduceLROnPlateau(
                    monitor="val_loss",
                    factor=0.5,
                    patience=5,
                    min_lr=1e-6
                ),
                # Log each epoch to MLflow
                mlflow.tensorflow.keras.MlflowCallback(run)
            ]
            
            # ── Train ─────────────────────────────────────────
            history = model.fit(
                X_train_norm, X_train_norm,  # Autoencoder: input = target
                validation_data=(X_val_norm, X_val_norm),
                epochs=params["epochs"],
                batch_size=params["batch_size"],
                callbacks=callbacks,
                shuffle=True
            )
            
            # ── Compute reconstruction errors on full dataset ─
            recon_errors = get_reconstruction_errors(model, X_all_norm)
            
            # Find P99 threshold from NORMAL samples only
            normal_errors = recon_errors[y_labels == 0]
            threshold = float(np.percentile(normal_errors, 99))
            
            # Evaluate using full labeled dataset
            y_pred = (recon_errors >= threshold).astype(int)
            
            precision = precision_score(y_labels, y_pred, zero_division=0)
            recall    = recall_score(y_labels, y_pred, zero_division=0)
            f1        = f1_score(y_labels, y_pred, zero_division=0)
            roc_auc   = roc_auc_score(y_labels, recon_errors)
            
            mlflow.log_metrics({
                "eval_precision": precision,
                "eval_recall": recall,
                "eval_f1": f1,
                "eval_roc_auc": roc_auc,
                "reconstruction_threshold_p99": threshold,
                "mean_normal_recon_error": float(normal_errors.mean()),
                "mean_anomaly_recon_error": float(recon_errors[y_labels==1].mean()),
                "final_train_loss": float(history.history["loss"][-1]),
                "final_val_loss": float(history.history["val_loss"][-1])
            })
            
            print(f"\n{'='*50}")
            print(f"LSTM Autoencoder Results:")
            print(f"  Precision: {precision:.4f}")
            print(f"  Recall:    {recall:.4f}")
            print(f"  F1 Score:  {f1:.4f}")
            print(f"  ROC AUC:   {roc_auc:.4f}")
            print(f"  Recon Threshold (P99): {threshold:.6f}")
            print(f"{'='*50}\n")
            
            # ── Save artifacts ────────────────────────────────
            import joblib
            joblib.dump(scaler, "/tmp/lstm_scaler.pkl")
            mlflow.log_artifact("/tmp/lstm_scaler.pkl", "artifacts")
            
            threshold_config = {
                "lstm_threshold": threshold,
                "threshold_percentile": 99,
                "sequence_length": seq_len,
                "n_features": n_features
            }
            mlflow.log_dict(threshold_config, "threshold_config.json")
            
            # Register model
            mlflow.tensorflow.log_model(
                model,
                artifact_path="lstm_autoencoder",
                registered_model_name="logguard-lstm-autoencoder"
            )
            
            print(f"✅ LSTM model registered. Run ID: {run.info.run_id}")
        
        return model, scaler, threshold
```

`ml/models/lstm_autoencoder/hyperparams.yaml`:
```yaml
lstm_autoencoder:
  encoding_dim: 32
  lstm_units: [128, 64]
  dropout_rate: 0.2
  epochs: 100
  batch_size: 64
  patience: 10          # Early stopping patience
  learning_rate: 0.001
  sequence_length: 30   # 30 windows = 30 minutes of history per host
```

---

## 🚀 Phase 4: Hybrid Scorer (Week 7–8)

`ml/scoring/hybrid_scorer.py`:
```python
import numpy as np
from typing import Tuple

class HybridAnomalyScorer:
    """
    Combines Isolation Forest and LSTM Autoencoder scores
    into a single final anomaly score.
    
    The score fusion formula:
      final_score = w_if * normalized_if_score + w_lstm * normalized_lstm_score
    
    Where:
      - w_if   = 0.4 (IF catches point anomalies)
      - w_lstm = 0.6 (LSTM catches contextual/sequence anomalies)
    
    Final score range: [0, 1]
    Score >= threshold → flag as anomaly
    """
    
    def __init__(
        self,
        if_weight: float = 0.4,
        lstm_weight: float = 0.6,
        final_threshold: float = 0.70
    ):
        assert abs(if_weight + lstm_weight - 1.0) < 1e-6, "Weights must sum to 1.0"
        
        self.if_weight       = if_weight
        self.lstm_weight     = lstm_weight
        self.final_threshold = final_threshold
        
        # These are learned from training data
        self._if_score_min   = None
        self._if_score_max   = None
        self._lstm_error_min = None
        self._lstm_error_max = None
    
    def calibrate(
        self,
        if_scores: np.ndarray,
        lstm_errors: np.ndarray
    ):
        """
        Learn normalization bounds from training data.
        Must be called once after both models are trained.
        Save these with the model artifacts.
        """
        self._if_score_min   = float(if_scores.min())
        self._if_score_max   = float(if_scores.max())
        self._lstm_error_min = float(lstm_errors.min())
        self._lstm_error_max = float(lstm_errors.max())
        
        print("Scorer calibrated:")
        print(f"  IF range:   [{self._if_score_min:.4f}, {self._if_score_max:.4f}]")
        print(f"  LSTM range: [{self._lstm_error_min:.4f}, {self._lstm_error_max:.4f}]")
    
    def score(
        self,
        if_raw_score: float,
        lstm_recon_error: float
    ) -> Tuple[float, bool, dict]:
        """
        Score a single feature window.
        
        Args:
          if_raw_score      — from IsolationForest.decision_function()
          lstm_recon_error  — MSE from LSTM reconstruction
        
        Returns:
          final_score (float)   — [0, 1], higher = more anomalous
          is_anomaly  (bool)    — True if final_score >= threshold
          breakdown   (dict)    — individual model contributions
        """
        
        if self._if_score_min is None:
            raise RuntimeError("Scorer not calibrated. Call calibrate() first.")
        
        # Normalize IF score: raw IF score is inverted (lower = more anomalous)
        # We flip it so 1 = most anomalous
        if_range = max(self._if_score_max - self._if_score_min, 1e-8)
        if_normalized = 1.0 - (if_raw_score - self._if_score_min) / if_range
        if_normalized = float(np.clip(if_normalized, 0.0, 1.0))
        
        # Normalize LSTM error: higher error = more anomalous
        lstm_range = max(self._lstm_error_max - self._lstm_error_min, 1e-8)
        lstm_normalized = (lstm_recon_error - self._lstm_error_min) / lstm_range
        lstm_normalized = float(np.clip(lstm_normalized, 0.0, 1.0))
        
        # Weighted combination
        final_score = (self.if_weight * if_normalized) + (self.lstm_weight * lstm_normalized)
        final_score = float(np.clip(final_score, 0.0, 1.0))
        
        is_anomaly = final_score >= self.final_threshold
        
        breakdown = {
            "if_raw_score": if_raw_score,
            "if_normalized": if_normalized,
            "if_contribution": self.if_weight * if_normalized,
            "lstm_raw_error": lstm_recon_error,
            "lstm_normalized": lstm_normalized,
            "lstm_contribution": self.lstm_weight * lstm_normalized,
            "final_score": final_score,
            "threshold": self.final_threshold,
            "is_anomaly": is_anomaly,
            "dominant_model": "LSTM" if self.lstm_weight * lstm_normalized > self.if_weight * if_normalized else "IsolationForest"
        }
        
        return final_score, is_anomaly, breakdown
```

---

## 🚀 Phase 5: Automated Retraining with Airflow (Week 8)

`ml/airflow_dags/weekly_retrain_dag.py`:
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import mlflow
import psycopg2
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
    conn = psycopg2.connect("postgresql://logguard:pass@postgres:5432/logguard")
    cur  = conn.cursor()
    
    cur.execute("""
        SELECT COUNT(*) FROM anomaly_feedback
        WHERE created_at > NOW() - INTERVAL '7 days'
        AND feedback_type IN ('true_positive', 'false_positive')
    """)
    count = cur.fetchone()[0]
    conn.close()
    
    print(f"New feedback events in last 7 days: {count}")
    
    if count < 100:
        raise ValueError(f"Insufficient feedback ({count} < 100). Skipping retraining.")
    
    context["task_instance"].xcom_push(key="feedback_count", value=count)

def fetch_and_prepare_data(**context):
    """Fetch labeled data from PostgreSQL + recent unlabeled from Elasticsearch."""
    from data.fetch_training_data import fetch_feedback_dataset
    
    df, X_flat, X_seq, y = fetch_feedback_dataset(days_back=30)
    
    # Save to shared location for subsequent tasks
    import joblib
    joblib.dump({"X_flat": X_flat, "X_seq": X_seq, "y": y}, "/tmp/retrain_data.pkl")
    print(f"Data ready: {len(df)} samples, {y.mean()*100:.1f}% anomaly rate")

def retrain_isolation_forest(**context):
    from models.isolation_forest.trainer import IsolationForestTrainer
    import joblib
    
    data = joblib.load("/tmp/retrain_data.pkl")
    trainer = IsolationForestTrainer()
    model, scaler, threshold = trainer.train(data["X_flat"], data["y"])
    
    # Promote to production if F1 > current production model
    client = mlflow.MlflowClient()
    _promote_if_better(client, "logguard-isolation-forest")

def retrain_lstm(**context):
    from models.lstm_autoencoder.trainer import LSTMAutoencoderTrainer
    import joblib
    
    data = joblib.load("/tmp/retrain_data.pkl")
    trainer = LSTMAutoencoderTrainer()
    model, scaler, threshold = trainer.train(data["X_seq"], data["y"])
    
    client = mlflow.MlflowClient()
    _promote_if_better(client, "logguard-lstm-autoencoder")

def _promote_if_better(client, model_name: str):
    """Promote new model version to 'production' if it beats the current one."""
    versions = client.get_latest_versions(model_name)
    new_version = max(versions, key=lambda v: int(v.version))
    
    new_f1 = float(
        client.get_run(new_version.run_id).data.metrics.get("f1_score", 0)
    )
    
    # Get current production version
    prod_versions = [v for v in versions if v.current_stage == "Production"]
    
    if not prod_versions:
        # No production model yet — promote directly
        client.transition_model_version_stage(
            model_name, new_version.version, stage="Production"
        )
        print(f"✅ Promoted v{new_version.version} to Production (first deployment)")
        return
    
    prod_f1 = float(
        client.get_run(prod_versions[0].run_id).data.metrics.get("f1_score", 0)
    )
    
    if new_f1 > prod_f1 + 0.01:  # Only promote if F1 improves by >1%
        client.transition_model_version_stage(
            model_name, new_version.version, stage="Production"
        )
        print(f"✅ Promoted v{new_version.version} (F1: {new_f1:.4f} > {prod_f1:.4f})")
    else:
        print(f"⚠️  New model (F1: {new_f1:.4f}) didn't beat production (F1: {prod_f1:.4f}). Keeping old.")

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
```

---

## ✅ Deliverables / Checkpoints

### Week 5 Checkpoint
- [ ] MLflow server chal raha ho localhost:5000 pe
- [ ] 52,500 synthetic samples generate ho (50K normal + 2.5K anomaly)
- [ ] EDA notebook mein anomaly types visualized ho

### Week 6 Checkpoint
- [ ] Isolation Forest train ho, MLflow mein experiment log ho
- [ ] F1 Score ≥ 0.75 on validation set
- [ ] Model MLflow Registry mein "production" stage mein promote ho

### Week 7 Checkpoint
- [ ] LSTM Autoencoder train ho (< 2 hours on GPU)
- [ ] Reconstruction error clearly separation dikhe normal vs anomaly
- [ ] F1 Score ≥ 0.78 on validation set

### Week 8 Checkpoint
- [ ] Hybrid scorer calibrated aur tested
- [ ] Airflow DAG locally test ho
- [ ] **Backend Engineer ko handoff**: MLflow model URIs share karo + inference API guide likho

---

## 🤝 Dependencies on Other Team Members

| Dependency | Tumhe kya chahiye | Kisse lo |
|---|---|---|
| Feature vector schema | Final column names + shapes | Person 1 (Data Eng) |
| Feedback table schema | `anomaly_feedback` PostgreSQL table | Person 3 (Backend) |
| GPU infrastructure | Training server ya cloud GPU | Team decision |

---

## 📊 Performance Targets

| Metric | Target |
|---|---|
| Isolation Forest F1 | ≥ 0.75 |
| LSTM Autoencoder F1 | ≥ 0.78 |
| Hybrid Scorer F1 | ≥ 0.82 |
| Hybrid ROC AUC | ≥ 0.90 |
| Inference time (per sample) | ≤ 10ms |
| False positive rate | ≤ 5% |

---

## 📚 Resources to Study

1. **Isolation Forest Paper**: https://cs.nju.edu.cn/zhouzh/zhouzh.files/publication/icdm08b.pdf
2. **MLflow Docs**: https://mlflow.org/docs/latest/index.html
3. **Keras LSTM Guide**: https://keras.io/api/layers/recurrent_layers/lstm/
4. **Log Anomaly Detection Survey**: https://arxiv.org/abs/2309.11696
5. **Airflow Docs**: https://airflow.apache.org/docs/

---

*LogGuard ML Engineer Task File — v1.0*  
*Tumhara output Person 3 (Backend) seedha use karega inference mein. Closely coordinate karo.*
