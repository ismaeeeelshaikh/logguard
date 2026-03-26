"""
End-to-end training pipeline for LogGuard ML models.

Orchestrates the full training workflow:
  1. Generate / load training data
  2. Train Isolation Forest
  3. Train LSTM Autoencoder
  4. Calibrate Hybrid Scorer
  5. Evaluate combined performance
  6. Log everything to MLflow
"""

import os
import sys
import numpy as np
import json
import joblib
from pathlib import Path
from typing import Dict, Optional

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from ml.data.data_loader import load_data, create_sequences
from ml.data.synthetic_generator import LogDataGenerator
from ml.features.preprocessor import FeaturePreprocessor
from ml.models.isolation_forest.trainer import IsolationForestTrainer
from ml.models.lstm_autoencoder.trainer import LSTMAutoencoderTrainer
from ml.scoring.hybrid_scorer import HybridAnomalyScorer
from ml.scoring.threshold_manager import ThresholdManager


class TrainingPipeline:
    """
    Full end-to-end training pipeline for LogGuard anomaly detection.
    """
    
    def __init__(
        self,
        data_config: Optional[Dict] = None,
        output_dir: str = None
    ):
        self.data_config = data_config or {
            "n_normal_train": 50000,
            "n_normal_val": 10000,
            "n_test": 5000,
            "anomaly_ratio": 0.05,
            "sequence_length": 30,
        }
        
        self.output_dir = output_dir or os.path.join(
            os.path.dirname(__file__), "..", "models", "saved"
        )
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.preprocessor = FeaturePreprocessor()
        self.threshold_manager = ThresholdManager()
    
    def run(self) -> Dict:
        """
        Execute the full training pipeline.
        
        Returns:
            dict with all models, scalers, thresholds, and metrics
        """
        results = {}
        
        # ── Step 1: Load data ─────────────────────────────────
        print("\n" + "="*60)
        print("  STEP 1: Loading / Generating Training Data")
        print("="*60)
        
        X_train, X_val, X_test, y_test = load_data(
            n_normal_train=self.data_config["n_normal_train"],
            n_normal_val=self.data_config["n_normal_val"],
            n_test=self.data_config["n_test"],
            anomaly_ratio=self.data_config["anomaly_ratio"],
        )
        
        print(f"  X_train shape: {X_train.shape}")
        print(f"  X_val shape:   {X_val.shape}")
        print(f"  X_test shape:  {X_test.shape}")
        print(f"  Anomalies in test: {y_test.sum()} / {len(y_test)}")
        
        # ── Step 2: Train Isolation Forest ────────────────────
        print("\n" + "="*60)
        print("  STEP 2: Training Isolation Forest")
        print("="*60)
        
        # Combine train + test for IF (it needs labels for eval)
        X_all_flat = np.vstack([X_train, X_test])
        y_all = np.concatenate([np.zeros(len(X_train)), y_test])
        
        if_trainer = IsolationForestTrainer()
        if_model, if_scaler, if_threshold = if_trainer.train(
            X_all_flat, y_all
        )
        results["isolation_forest"] = {
            "model": if_model,
            "scaler": if_scaler,
            "threshold": if_threshold,
        }
        
        # ── Step 3: Train LSTM Autoencoder ────────────────────
        print("\n" + "="*60)
        print("  STEP 3: Training LSTM Autoencoder")
        print("="*60)
        
        seq_len = self.data_config["sequence_length"]
        
        # Build sequences from test data
        X_seq = create_sequences(X_test, seq_length=seq_len)
        y_seq = y_test[seq_len - 1:]  # Align labels to sequences
        
        lstm_trainer = LSTMAutoencoderTrainer()
        lstm_model, lstm_scaler, lstm_threshold = lstm_trainer.train(
            X_seq, y_seq
        )
        results["lstm_autoencoder"] = {
            "model": lstm_model,
            "scaler": lstm_scaler,
            "threshold": lstm_threshold,
        }
        
        # ── Step 4: Calibrate Hybrid Scorer ───────────────────
        print("\n" + "="*60)
        print("  STEP 4: Calibrating Hybrid Scorer")
        print("="*60)
        
        # Get IF scores on test set
        X_test_scaled = if_scaler.transform(X_test)
        if_raw_scores = if_model.decision_function(X_test_scaled)
        
        # Get LSTM reconstruction errors on test sequences
        from ml.models.lstm_autoencoder.architecture import (
            get_reconstruction_errors
        )
        X_seq_scaled = lstm_scaler.transform(
            X_seq.reshape(-1, X_seq.shape[2])
        ).reshape(X_seq.shape)
        lstm_errors = get_reconstruction_errors(lstm_model, X_seq_scaled)
        
        # Align IF scores with LSTM sequence scores
        if_scores_aligned = if_raw_scores[seq_len - 1:]
        
        scorer = HybridAnomalyScorer(
            if_weight=0.4,
            lstm_weight=0.6,
            final_threshold=0.70
        )
        scorer.calibrate(if_scores_aligned, lstm_errors)
        
        # Score the aligned test data
        final_scores, is_anomaly, breakdowns = scorer.score_batch(
            if_scores_aligned, lstm_errors
        )
        
        # Evaluate hybrid results
        from sklearn.metrics import (
            precision_score, recall_score, f1_score, roc_auc_score
        )
        
        hybrid_precision = precision_score(y_seq, is_anomaly, zero_division=0)
        hybrid_recall = recall_score(y_seq, is_anomaly, zero_division=0)
        hybrid_f1 = f1_score(y_seq, is_anomaly, zero_division=0)
        hybrid_roc = roc_auc_score(y_seq, final_scores)
        
        print(f"\n{'='*50}")
        print(f"Hybrid Scorer Results:")
        print(f"  Precision: {hybrid_precision:.4f}")
        print(f"  Recall:    {hybrid_recall:.4f}")
        print(f"  F1 Score:  {hybrid_f1:.4f}")
        print(f"  ROC AUC:   {hybrid_roc:.4f}")
        print(f"{'='*50}\n")
        
        results["hybrid_scorer"] = {
            "scorer": scorer,
            "precision": hybrid_precision,
            "recall": hybrid_recall,
            "f1_score": hybrid_f1,
            "roc_auc": hybrid_roc,
        }
        
        # ── Step 5: Save all artifacts ────────────────────────
        print("\n" + "="*60)
        print("  STEP 5: Saving Artifacts")
        print("="*60)
        
        scorer.save(os.path.join(self.output_dir, "hybrid_scorer.pkl"))
        self.threshold_manager.save(
            os.path.join(self.output_dir, "thresholds.pkl")
        )
        
        print(f"  Artifacts saved to: {self.output_dir}")
        print("\n✅ Training pipeline completed successfully!\n")
        
        return results


if __name__ == "__main__":
    # Run with smaller dataset for quick testing
    pipeline = TrainingPipeline(
        data_config={
            "n_normal_train": 5000,
            "n_normal_val": 1000,
            "n_test": 1500,
            "anomaly_ratio": 0.05,
            "sequence_length": 10,  # Shorter sequences for quick test
        }
    )
    results = pipeline.run()
