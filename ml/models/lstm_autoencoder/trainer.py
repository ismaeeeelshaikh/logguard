"""
LSTM Autoencoder trainer with MLflow experiment tracking.

Trains the LSTM Autoencoder on NORMAL sequences only.
The model learns what "normal" looks like.
When given anomalous sequences, reconstruction error will be high.
"""

import os
import sys
import mlflow
import mlflow.tensorflow
import numpy as np
import json
import yaml
import joblib
from pathlib import Path
from tensorflow import keras
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score,
    confusion_matrix
)

from .architecture import build_lstm_autoencoder, get_reconstruction_errors


class LSTMAutoencoderTrainer:
    """
    Trainer for the LSTM Autoencoder anomaly detection model.
    
    Workflow:
      1. Isolate normal sequences for training
      2. Normalize features using StandardScaler
      3. Train autoencoder (input == target)
      4. Compute reconstruction errors on full dataset
      5. Find P99 threshold from normal samples
      6. Evaluate and log to MLflow
    """
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "hyperparams.yaml"
            )
        
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        
        mlflow.set_tracking_uri("http://localhost:5000")
        mlflow.set_experiment("logguard-lstm-autoencoder")
    
    def train(
        self,
        X_sequences: np.ndarray,   # shape: (n, seq_len, n_features)
        y_labels: np.ndarray       # shape: (n,) — only used for evaluation
    ):
        """
        Train LSTM Autoencoder on NORMAL sequences only.
        
        Args:
            X_sequences: 3D array of shape (n_samples, seq_len, n_features)
            y_labels: Binary labels (0=normal, 1=anomaly), used only for eval
        
        Returns:
            Tuple of (model, scaler, threshold)
        """
        
        # ── Use only normal sequences for training ────────────
        X_normal = X_sequences[y_labels == 0]
        X_train, X_val = train_test_split(
            X_normal, test_size=0.1, random_state=42
        )
        
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
            X_train_norm = scaler.fit_transform(X_train_flat).reshape(
                n, seq_len, n_features
            )
            X_val_norm = scaler.transform(
                X_val.reshape(-1, n_features)
            ).reshape(len(X_val), seq_len, n_features)
            X_all_norm = scaler.transform(
                X_sequences.reshape(-1, n_features)
            ).reshape(len(X_sequences), seq_len, n_features)
            
            # ── Build model ───────────────────────────────────
            model = build_lstm_autoencoder(
                sequence_length=seq_len,
                n_features=n_features,
                encoding_dim=params["encoding_dim"],
                lstm_units=params["lstm_units"],
                dropout_rate=params["dropout_rate"]
            )
            
            model.summary()
            
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
            recall = recall_score(y_labels, y_pred, zero_division=0)
            f1 = f1_score(y_labels, y_pred, zero_division=0)
            roc_auc = roc_auc_score(y_labels, recon_errors)
            
            mlflow.log_metrics({
                "eval_precision": precision,
                "eval_recall": recall,
                "eval_f1": f1,
                "eval_roc_auc": roc_auc,
                "reconstruction_threshold_p99": threshold,
                "mean_normal_recon_error": float(normal_errors.mean()),
                "mean_anomaly_recon_error": float(
                    recon_errors[y_labels == 1].mean()
                ),
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
            
            # ── Save confusion matrix ─────────────────────────
            cm = confusion_matrix(y_labels, y_pred)
            mlflow.log_text(str(cm), "confusion_matrix.txt")
            
            # ── Save artifacts ────────────────────────────────
            scaler_path = "/tmp/lstm_scaler.pkl"
            joblib.dump(scaler, scaler_path)
            mlflow.log_artifact(scaler_path, "artifacts")
            
            threshold_config = {
                "lstm_threshold": threshold,
                "threshold_percentile": 99,
                "sequence_length": seq_len,
                "n_features": n_features
            }
            mlflow.log_dict(threshold_config, "threshold_config.json")
            
            # Save model locally
            local_model_dir = os.path.join(
                os.path.dirname(__file__), "..", "saved"
            )
            os.makedirs(local_model_dir, exist_ok=True)
            local_model_path = os.path.join(
                local_model_dir, "lstm_autoencoder.keras"
            )
            model.save(local_model_path)
            
            # Register model in MLflow
            mlflow.tensorflow.log_model(
                model,
                artifact_path="lstm_autoencoder",
                registered_model_name="logguard-lstm-autoencoder"
            )
            
            print(f"✅ LSTM model registered. Run ID: {run.info.run_id}")
        
        return model, scaler, threshold


if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from ml.data.data_loader import load_data, create_sequences
    
    # Load data
    print("Loading data...")
    X_train, X_val, X_test, y_test = load_data(
        n_normal_train=5000,
        n_normal_val=1000,
        n_test=1500,
        anomaly_ratio=0.05
    )
    
    # Build sequences from test data for evaluation
    X_seq = create_sequences(X_test, seq_length=30)
    # Align labels: each sequence gets the label of its last element
    y_seq = y_test[29:]  # drop first (seq_len - 1) labels
    
    # Train
    trainer = LSTMAutoencoderTrainer()
    model, scaler, threshold = trainer.train(X_seq, y_seq)
