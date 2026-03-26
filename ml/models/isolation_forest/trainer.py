"""
Isolation Forest trainer with proper MLflow tracking.

Trains IF in unsupervised mode on normal-only data,
evaluates with labeled test data, and registers the model.
"""

import os
import sys
import mlflow
import mlflow.sklearn
import numpy as np
import yaml
import json
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score,
    confusion_matrix
)
from pathlib import Path


class IsolationForestTrainer:
    """
    Isolation Forest trainer with MLflow experiment tracking.
    
    The IF is trained unsupervised on normal data only.
    Labels are used only for evaluation and threshold tuning.
    """
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "hyperparams.yaml"
            )
        
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        
        mlflow.set_tracking_uri("http://localhost:5000")
        mlflow.set_experiment("logguard-isolation-forest")
    
    def train(
        self,
        X_flat: np.ndarray,
        y_labels: np.ndarray
    ):
        """
        Train Isolation Forest with proper MLflow tracking.
        
        Args:
            X_flat: 2D feature array (n_samples, n_features)
            y_labels: Binary labels (0=normal, 1=anomaly) — eval only
        
        Returns:
            Tuple of (model, scaler, threshold)
        """
        
        # Split: use labels only for evaluation, NOT training
        # IF is unsupervised — only trained on normal data
        X_normal = X_flat[y_labels == 0]
        X_test = X_flat
        
        X_train, X_val_normal = train_test_split(
            X_normal, test_size=0.1, random_state=42
        )
        
        with mlflow.start_run(run_name="isolation-forest-v1") as run:
            
            # ── Log hyperparameters ───────────────────────
            params = self.config["isolation_forest"]
            mlflow.log_params(params)
            
            # ── Fit scaler on normal training data ────────
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
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
            # IF returns anomaly scores via decision_function()
            raw_scores = model.decision_function(X_test_scaled)
            
            # Convert to [0, 1] where 1 = most anomalous
            score_range = raw_scores.max() - raw_scores.min()
            if score_range > 0:
                anomaly_scores = 1 - (raw_scores - raw_scores.min()) / score_range
            else:
                anomaly_scores = np.zeros_like(raw_scores)
            
            # Find optimal threshold using F1
            threshold, best_f1 = self._find_optimal_threshold(
                anomaly_scores, y_labels
            )
            
            y_pred = (anomaly_scores >= threshold).astype(int)
            
            # ── Metrics ───────────────────────────────────
            precision = precision_score(y_labels, y_pred, zero_division=0)
            recall = recall_score(y_labels, y_pred, zero_division=0)
            f1 = f1_score(y_labels, y_pred, zero_division=0)
            roc_auc = roc_auc_score(y_labels, anomaly_scores)
            pr_auc = average_precision_score(y_labels, anomaly_scores)
            
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
            scaler_path = "/tmp/if_scaler.pkl"
            joblib.dump(scaler, scaler_path)
            mlflow.log_artifact(scaler_path, "artifacts")
            
            # Log threshold for inference service
            threshold_config = {
                "if_threshold": float(threshold),
                "contamination": params["contamination"],
                "feature_count": X_flat.shape[1]
            }
            mlflow.log_dict(threshold_config, "threshold_config.json")
            
            # Save model locally
            local_model_dir = os.path.join(
                os.path.dirname(__file__), "..", "saved"
            )
            os.makedirs(local_model_dir, exist_ok=True)
            local_model_path = os.path.join(
                local_model_dir, "isolation_forest_v2.joblib"
            )
            joblib.dump(model, local_model_path)
            
            # Register model to MLflow Model Registry
            mlflow.sklearn.log_model(
                sk_model=model,
                artifact_path="isolation_forest",
                registered_model_name="logguard-isolation-forest",
            )
            
            print(f"✅ Model registered in MLflow. Run ID: {run.info.run_id}")
        
        return model, scaler, threshold
    
    def _find_optimal_threshold(
        self,
        scores: np.ndarray,
        y_true: np.ndarray,
        beta: float = 1.0
    ) -> tuple:
        """
        Sweep thresholds and find the one that maximizes F-beta score.
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


if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from ml.data.data_loader import load_data
    
    print("Loading data...")
    X_train, X_val, X_test, y_test = load_data(
        n_normal_train=10000,
        n_normal_val=2000,
        n_test=3000,
        anomaly_ratio=0.05
    )
    
    # Combine train + test with labels for the trainer
    X_all = np.vstack([X_train, X_test])
    y_all = np.concatenate([np.zeros(len(X_train)), y_test])
    
    trainer = IsolationForestTrainer()
    model, scaler, threshold = trainer.train(X_all, y_all)
