"""
Dynamic threshold manager for LogGuard anomaly scoring.

Manages threshold computation and adaptation based on:
  1. Statistical percentile-based thresholds (P99 from normal data)
  2. Feedback-driven threshold adjustment
  3. Multi-strategy threshold selection (F1-optimal, precision-focused, recall-focused)
"""

import numpy as np
from sklearn.metrics import (
    precision_score, recall_score, f1_score
)
from typing import Dict, Tuple, Optional
import json
import joblib


class ThresholdManager:
    """
    Manages anomaly thresholds for both IF and LSTM models.
    
    Supports:
      - Percentile-based thresholds
      - F-beta optimized thresholds
      - Feedback-adjusted thresholds
      - Per-tenant threshold overrides
    """
    
    def __init__(self):
        self.thresholds = {}
        self._feedback_adjustments = {}
    
    def compute_percentile_threshold(
        self,
        normal_scores: np.ndarray,
        percentile: float = 99.0,
        model_name: str = "default"
    ) -> float:
        """
        Compute threshold at given percentile of normal score distribution.
        
        Args:
            normal_scores: Anomaly scores from normal data only
            percentile: Percentile to use (99.0 = 1% false positive rate)
            model_name: Name to store the threshold under
        
        Returns:
            Computed threshold value
        """
        threshold = float(np.percentile(normal_scores, percentile))
        
        self.thresholds[model_name] = {
            "value": threshold,
            "method": "percentile",
            "percentile": percentile,
            "normal_mean": float(normal_scores.mean()),
            "normal_std": float(normal_scores.std()),
        }
        
        return threshold
    
    def compute_fbeta_threshold(
        self,
        scores: np.ndarray,
        y_true: np.ndarray,
        beta: float = 1.0,
        model_name: str = "default"
    ) -> Tuple[float, float]:
        """
        Find threshold that maximizes F-beta score.
        
        Args:
            scores: Anomaly scores (higher = more anomalous)
            y_true: True binary labels
            beta: F-beta weight (1.0=F1, 2.0=recall-weighted)
            model_name: Name to store the threshold under
        
        Returns:
            (threshold, best_f_score)
        """
        best_threshold = 0.5
        best_f = 0.0
        
        # Search over a range of thresholds
        for t in np.arange(0.05, 0.99, 0.01):
            y_pred = (scores >= t).astype(int)
            if y_pred.sum() == 0:
                continue
            
            p = precision_score(y_true, y_pred, zero_division=0)
            r = recall_score(y_true, y_pred, zero_division=0)
            
            if p + r == 0:
                continue
            
            f = (1 + beta**2) * (p * r) / ((beta**2 * p) + r)
            if f > best_f:
                best_f = f
                best_threshold = t
        
        self.thresholds[model_name] = {
            "value": best_threshold,
            "method": "fbeta",
            "beta": beta,
            "best_f_score": best_f,
        }
        
        return best_threshold, best_f
    
    def adjust_from_feedback(
        self,
        model_name: str,
        false_positive_count: int,
        false_negative_count: int,
        total_feedback: int,
        adjustment_rate: float = 0.02
    ) -> float:
        """
        Adjust threshold based on user feedback.
        
        - Too many false positives → increase threshold (less sensitive)
        - Too many false negatives → decrease threshold (more sensitive)
        
        Args:
            model_name: Model to adjust threshold for
            false_positive_count: Number of FP feedback events
            false_negative_count: Number of FN feedback events
            total_feedback: Total feedback events
            adjustment_rate: Max adjustment per feedback cycle
        
        Returns:
            New adjusted threshold
        """
        if model_name not in self.thresholds:
            raise KeyError(f"No threshold found for model '{model_name}'")
        
        current = self.thresholds[model_name]["value"]
        
        fp_rate = false_positive_count / max(total_feedback, 1)
        fn_rate = false_negative_count / max(total_feedback, 1)
        
        # Adjust: more FPs → raise threshold, more FNs → lower threshold
        adjustment = adjustment_rate * (fp_rate - fn_rate)
        new_threshold = float(np.clip(current + adjustment, 0.05, 0.99))
        
        self.thresholds[model_name]["value"] = new_threshold
        self.thresholds[model_name]["last_adjustment"] = adjustment
        
        # Track history
        if model_name not in self._feedback_adjustments:
            self._feedback_adjustments[model_name] = []
        self._feedback_adjustments[model_name].append({
            "old_threshold": current,
            "new_threshold": new_threshold,
            "adjustment": adjustment,
            "fp_count": false_positive_count,
            "fn_count": false_negative_count,
        })
        
        return new_threshold
    
    def get_threshold(self, model_name: str) -> float:
        """Get the current threshold for a model."""
        if model_name not in self.thresholds:
            raise KeyError(f"No threshold found for model '{model_name}'")
        return self.thresholds[model_name]["value"]
    
    def get_all_thresholds(self) -> Dict:
        """Return all stored thresholds."""
        return self.thresholds.copy()
    
    def save(self, path: str) -> None:
        """Save thresholds to disk."""
        data = {
            "thresholds": self.thresholds,
            "feedback_history": self._feedback_adjustments,
        }
        joblib.dump(data, path)
    
    @classmethod
    def load(cls, path: str) -> 'ThresholdManager':
        """Load thresholds from disk."""
        data = joblib.load(path)
        manager = cls()
        manager.thresholds = data["thresholds"]
        manager._feedback_adjustments = data.get("feedback_history", {})
        return manager
