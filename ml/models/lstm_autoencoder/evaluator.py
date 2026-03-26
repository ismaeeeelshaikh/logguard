"""
LSTM Autoencoder evaluator — reconstruction error analysis and visualization.

Provides tools to:
  1. Compute reconstruction errors per sample
  2. Analyze the error distribution for normal vs anomaly samples
  3. Generate evaluation metrics and plots
  4. Find optimal threshold using different strategies
"""

import numpy as np
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score,
    precision_recall_curve, roc_curve,
    confusion_matrix, classification_report
)
from typing import Tuple, Dict, Optional

from .architecture import get_reconstruction_errors


class LSTMEvaluator:
    """
    Evaluator for the LSTM Autoencoder model.
    Focuses on reconstruction error analysis for anomaly detection.
    """
    
    def __init__(self, model, scaler=None):
        """
        Args:
            model: Trained LSTM Autoencoder keras model
            scaler: Optional fitted StandardScaler for normalizing inputs
        """
        self.model = model
        self.scaler = scaler
    
    def evaluate(
        self,
        X_sequences: np.ndarray,
        y_labels: np.ndarray,
        threshold: Optional[float] = None,
        threshold_percentile: float = 99.0
    ) -> Dict:
        """
        Full evaluation of the LSTM model on labeled data.
        
        Args:
            X_sequences: 3D input sequences (n, seq_len, n_features)
            y_labels: Binary labels (0=normal, 1=anomaly)
            threshold: Pre-computed threshold, or None to auto-compute
            threshold_percentile: Percentile for auto-threshold (default P99)
        
        Returns:
            dict with all metrics and analysis results
        """
        # Normalize if scaler is available
        if self.scaler is not None:
            n, seq_len, n_features = X_sequences.shape
            X_flat = X_sequences.reshape(-1, n_features)
            X_norm = self.scaler.transform(X_flat).reshape(n, seq_len, n_features)
        else:
            X_norm = X_sequences
        
        # Compute reconstruction errors
        recon_errors = get_reconstruction_errors(self.model, X_norm)
        
        # Normal vs anomaly error statistics
        normal_errors = recon_errors[y_labels == 0]
        anomaly_errors = recon_errors[y_labels == 1]
        
        # Auto-compute threshold if not provided
        if threshold is None:
            threshold = float(np.percentile(normal_errors, threshold_percentile))
        
        # Predictions
        y_pred = (recon_errors >= threshold).astype(int)
        
        # Metrics
        precision = precision_score(y_labels, y_pred, zero_division=0)
        recall = recall_score(y_labels, y_pred, zero_division=0)
        f1 = f1_score(y_labels, y_pred, zero_division=0)
        roc_auc = roc_auc_score(y_labels, recon_errors)
        pr_auc = average_precision_score(y_labels, recon_errors)
        cm = confusion_matrix(y_labels, y_pred)
        
        results = {
            "threshold": threshold,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "roc_auc": roc_auc,
            "pr_auc": pr_auc,
            "confusion_matrix": cm,
            "normal_error_stats": {
                "mean": float(normal_errors.mean()),
                "std": float(normal_errors.std()),
                "median": float(np.median(normal_errors)),
                "p95": float(np.percentile(normal_errors, 95)),
                "p99": float(np.percentile(normal_errors, 99)),
                "max": float(normal_errors.max()),
            },
            "anomaly_error_stats": {
                "mean": float(anomaly_errors.mean()),
                "std": float(anomaly_errors.std()),
                "median": float(np.median(anomaly_errors)),
                "min": float(anomaly_errors.min()),
            },
            "separation_ratio": float(
                anomaly_errors.mean() / max(normal_errors.mean(), 1e-8)
            ),
            "reconstruction_errors": recon_errors,
            "y_pred": y_pred,
        }
        
        return results
    
    def find_optimal_threshold(
        self,
        recon_errors: np.ndarray,
        y_labels: np.ndarray,
        beta: float = 1.0
    ) -> Tuple[float, float]:
        """
        Search thresholds to maximize F-beta score.
        
        Args:
            recon_errors: Per-sample reconstruction errors
            y_labels: True binary labels
            beta: F-beta weight (1.0 = F1, 2.0 = weight recall more)
        
        Returns:
            (best_threshold, best_f_score)
        """
        # Use percentile-based thresholds for efficiency
        percentiles = np.arange(90, 99.9, 0.1)
        normal_errors = recon_errors[y_labels == 0]
        
        best_threshold = 0.0
        best_f = 0.0
        
        for pct in percentiles:
            threshold = np.percentile(normal_errors, pct)
            y_pred = (recon_errors >= threshold).astype(int)
            
            if y_pred.sum() == 0:
                continue
            
            p = precision_score(y_labels, y_pred, zero_division=0)
            r = recall_score(y_labels, y_pred, zero_division=0)
            
            if p + r == 0:
                continue
            
            f = (1 + beta**2) * (p * r) / ((beta**2 * p) + r)
            if f > best_f:
                best_f = f
                best_threshold = threshold
        
        return best_threshold, best_f
    
    def print_report(self, results: Dict) -> None:
        """Print a formatted evaluation report."""
        print(f"\n{'='*60}")
        print(f"  LSTM Autoencoder Evaluation Report")
        print(f"{'='*60}")
        print(f"  Threshold:        {results['threshold']:.6f}")
        print(f"  Precision:        {results['precision']:.4f}")
        print(f"  Recall:           {results['recall']:.4f}")
        print(f"  F1 Score:         {results['f1_score']:.4f}")
        print(f"  ROC AUC:          {results['roc_auc']:.4f}")
        print(f"  PR AUC:           {results['pr_auc']:.4f}")
        print(f"  Separation Ratio: {results['separation_ratio']:.2f}x")
        print(f"\n  Normal Error:  mean={results['normal_error_stats']['mean']:.6f}, "
              f"std={results['normal_error_stats']['std']:.6f}")
        print(f"  Anomaly Error: mean={results['anomaly_error_stats']['mean']:.6f}, "
              f"std={results['anomaly_error_stats']['std']:.6f}")
        print(f"\n  Confusion Matrix:")
        print(f"  {results['confusion_matrix']}")
        print(f"{'='*60}\n")
