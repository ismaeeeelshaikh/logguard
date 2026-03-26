"""
Isolation Forest evaluator — metrics, threshold tuning, and analysis.
"""

import numpy as np
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score,
    confusion_matrix
)
from typing import Dict, Tuple, Optional


class IsolationForestEvaluator:
    """
    Evaluator for the Isolation Forest anomaly detection model.
    """
    
    def __init__(self, model, scaler=None):
        """
        Args:
            model: Trained IsolationForest model
            scaler: Optional fitted StandardScaler
        """
        self.model = model
        self.scaler = scaler
    
    def evaluate(
        self,
        X: np.ndarray,
        y_labels: np.ndarray,
        threshold: Optional[float] = None
    ) -> Dict:
        """
        Full evaluation of IF model on labeled data.
        
        Args:
            X: 2D feature array (n_samples, n_features)
            y_labels: Binary labels (0=normal, 1=anomaly)
            threshold: Pre-computed threshold, or None to optimize
        
        Returns:
            dict with metrics and analysis
        """
        # Scale if scaler provided
        X_scaled = self.scaler.transform(X) if self.scaler else X
        
        # Get raw anomaly scores
        raw_scores = self.model.decision_function(X_scaled)
        
        # Normalize to [0, 1] where 1 = most anomalous
        score_range = raw_scores.max() - raw_scores.min()
        if score_range > 0:
            anomaly_scores = 1 - (raw_scores - raw_scores.min()) / score_range
        else:
            anomaly_scores = np.zeros_like(raw_scores)
        
        # Find optimal threshold if not provided
        if threshold is None:
            threshold, _ = self.find_optimal_threshold(anomaly_scores, y_labels)
        
        y_pred = (anomaly_scores >= threshold).astype(int)
        
        precision = precision_score(y_labels, y_pred, zero_division=0)
        recall = recall_score(y_labels, y_pred, zero_division=0)
        f1 = f1_score(y_labels, y_pred, zero_division=0)
        roc_auc = roc_auc_score(y_labels, anomaly_scores)
        pr_auc = average_precision_score(y_labels, anomaly_scores)
        cm = confusion_matrix(y_labels, y_pred)
        
        return {
            "threshold": threshold,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "roc_auc": roc_auc,
            "pr_auc": pr_auc,
            "confusion_matrix": cm,
            "anomaly_scores": anomaly_scores,
            "y_pred": y_pred,
            "raw_scores": raw_scores,
        }
    
    def find_optimal_threshold(
        self,
        scores: np.ndarray,
        y_true: np.ndarray,
        beta: float = 1.0
    ) -> Tuple[float, float]:
        """Sweep thresholds and find the one that maximizes F-beta score."""
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
    
    def print_report(self, results: Dict) -> None:
        """Print a formatted evaluation report."""
        print(f"\n{'='*60}")
        print(f"  Isolation Forest Evaluation Report")
        print(f"{'='*60}")
        print(f"  Threshold: {results['threshold']:.4f}")
        print(f"  Precision: {results['precision']:.4f}")
        print(f"  Recall:    {results['recall']:.4f}")
        print(f"  F1 Score:  {results['f1_score']:.4f}")
        print(f"  ROC AUC:   {results['roc_auc']:.4f}")
        print(f"  PR AUC:    {results['pr_auc']:.4f}")
        print(f"\n  Confusion Matrix:")
        print(f"  {results['confusion_matrix']}")
        print(f"{'='*60}\n")
