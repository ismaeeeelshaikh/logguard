"""
Hybrid Anomaly Scorer — combines Isolation Forest and LSTM Autoencoder scores.

Score fusion formula:
  final_score = w_if * normalized_if_score + w_lstm * normalized_lstm_score

Where:
  - w_if   = 0.4 (IF catches point anomalies)
  - w_lstm = 0.6 (LSTM catches contextual/sequence anomalies)

Final score range: [0, 1]
Score >= threshold → flag as anomaly
"""

import numpy as np
import json
import joblib
from typing import Tuple, Dict, Optional
from pathlib import Path


class HybridAnomalyScorer:
    """
    Combines Isolation Forest and LSTM Autoencoder scores
    into a single final anomaly score.
    """
    
    def __init__(
        self,
        if_weight: float = 0.4,
        lstm_weight: float = 0.6,
        final_threshold: float = 0.70
    ):
        assert abs(if_weight + lstm_weight - 1.0) < 1e-6, \
            "Weights must sum to 1.0"
        
        self.if_weight = if_weight
        self.lstm_weight = lstm_weight
        self.final_threshold = final_threshold
        
        # These are learned from training data
        self._if_score_min = None
        self._if_score_max = None
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
        self._if_score_min = float(if_scores.min())
        self._if_score_max = float(if_scores.max())
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
            if_raw_score: from IsolationForest.decision_function()
            lstm_recon_error: MSE from LSTM reconstruction
        
        Returns:
            final_score (float): [0, 1], higher = more anomalous
            is_anomaly (bool): True if final_score >= threshold
            breakdown (dict): individual model contributions
        """
        
        if self._if_score_min is None:
            raise RuntimeError(
                "Scorer not calibrated. Call calibrate() first."
            )
        
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
        final_score = (
            self.if_weight * if_normalized +
            self.lstm_weight * lstm_normalized
        )
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
            "dominant_model": (
                "LSTM"
                if self.lstm_weight * lstm_normalized > self.if_weight * if_normalized
                else "IsolationForest"
            )
        }
        
        return final_score, is_anomaly, breakdown
    
    def score_batch(
        self,
        if_raw_scores: np.ndarray,
        lstm_recon_errors: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, list]:
        """
        Score a batch of feature windows.
        
        Args:
            if_raw_scores: Array of IF decision_function() scores
            lstm_recon_errors: Array of LSTM reconstruction errors
        
        Returns:
            final_scores: Array of final scores
            is_anomaly: Boolean array
            breakdowns: List of breakdown dicts
        """
        final_scores = []
        is_anomaly_arr = []
        breakdowns = []
        
        for if_score, lstm_err in zip(if_raw_scores, lstm_recon_errors):
            score, is_anom, breakdown = self.score(
                float(if_score), float(lstm_err)
            )
            final_scores.append(score)
            is_anomaly_arr.append(is_anom)
            breakdowns.append(breakdown)
        
        return (
            np.array(final_scores),
            np.array(is_anomaly_arr),
            breakdowns
        )
    
    def save(self, path: str) -> None:
        """Save scorer configuration and calibration data."""
        config = {
            "if_weight": self.if_weight,
            "lstm_weight": self.lstm_weight,
            "final_threshold": self.final_threshold,
            "if_score_min": self._if_score_min,
            "if_score_max": self._if_score_max,
            "lstm_error_min": self._lstm_error_min,
            "lstm_error_max": self._lstm_error_max,
        }
        joblib.dump(config, path)
    
    @classmethod
    def load(cls, path: str) -> 'HybridAnomalyScorer':
        """Load scorer from saved configuration."""
        config = joblib.load(path)
        scorer = cls(
            if_weight=config["if_weight"],
            lstm_weight=config["lstm_weight"],
            final_threshold=config["final_threshold"]
        )
        scorer._if_score_min = config["if_score_min"]
        scorer._if_score_max = config["if_score_max"]
        scorer._lstm_error_min = config["lstm_error_min"]
        scorer._lstm_error_max = config["lstm_error_max"]
        return scorer
