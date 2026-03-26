"""
Unit tests for the Hybrid Anomaly Scorer.
"""

import os
import sys
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from ml.scoring.hybrid_scorer import HybridAnomalyScorer
from ml.scoring.threshold_manager import ThresholdManager


class TestHybridScorer:
    """Tests for the Hybrid Anomaly Scorer."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test scorer and sample data."""
        self.scorer = HybridAnomalyScorer(
            if_weight=0.4,
            lstm_weight=0.6,
            final_threshold=0.70
        )
        
        # Simulate IF + LSTM scores
        np.random.seed(42)
        n_samples = 100
        
        # Normal samples: IF scores positive (normal), LSTM errors low
        self.normal_if_scores = np.random.normal(0.1, 0.02, n_samples)
        self.normal_lstm_errors = np.random.exponential(0.01, n_samples)
        
        # Anomaly samples: IF scores negative (anomalous), LSTM errors high
        self.anomaly_if_scores = np.random.normal(-0.2, 0.05, 20)
        self.anomaly_lstm_errors = np.random.exponential(0.1, 20)
        
        # Combined for calibration
        self.all_if_scores = np.concatenate([
            self.normal_if_scores, self.anomaly_if_scores
        ])
        self.all_lstm_errors = np.concatenate([
            self.normal_lstm_errors, self.anomaly_lstm_errors
        ])
    
    def test_weight_validation(self):
        """Test that weights must sum to 1.0."""
        with pytest.raises(AssertionError):
            HybridAnomalyScorer(if_weight=0.5, lstm_weight=0.6)
    
    def test_calibration(self):
        """Test scorer calibration."""
        self.scorer.calibrate(self.all_if_scores, self.all_lstm_errors)
        
        assert self.scorer._if_score_min is not None
        assert self.scorer._if_score_max is not None
        assert self.scorer._lstm_error_min is not None
        assert self.scorer._lstm_error_max is not None
    
    def test_score_uncalibrated_raises(self):
        """Test that scoring without calibration raises error."""
        scorer = HybridAnomalyScorer()
        with pytest.raises(RuntimeError, match="not calibrated"):
            scorer.score(0.1, 0.01)
    
    def test_single_score(self):
        """Test single sample scoring."""
        self.scorer.calibrate(self.all_if_scores, self.all_lstm_errors)
        
        score, is_anomaly, breakdown = self.scorer.score(0.1, 0.01)
        
        assert 0.0 <= score <= 1.0
        assert isinstance(is_anomaly, bool)
        assert "final_score" in breakdown
        assert "if_normalized" in breakdown
        assert "lstm_normalized" in breakdown
        assert "dominant_model" in breakdown
    
    def test_normal_sample_not_anomalous(self):
        """Test that clearly normal samples score low."""
        self.scorer.calibrate(self.all_if_scores, self.all_lstm_errors)
        
        # High IF score (normal), low LSTM error (normal)
        score, is_anomaly, _ = self.scorer.score(
            float(self.all_if_scores.max()),
            float(self.all_lstm_errors.min())
        )
        
        assert score < 0.5, f"Normal sample scored too high: {score}"
    
    def test_anomaly_sample_is_anomalous(self):
        """Test that clearly anomalous samples score high."""
        self.scorer.calibrate(self.all_if_scores, self.all_lstm_errors)
        
        # Low IF score (anomalous), high LSTM error (anomalous)
        score, is_anomaly, _ = self.scorer.score(
            float(self.all_if_scores.min()),
            float(self.all_lstm_errors.max())
        )
        
        assert score > 0.5, f"Anomaly sample scored too low: {score}"
    
    def test_batch_scoring(self):
        """Test batch scoring."""
        self.scorer.calibrate(self.all_if_scores, self.all_lstm_errors)
        
        scores, is_anomaly, breakdowns = self.scorer.score_batch(
            self.all_if_scores[:10],
            self.all_lstm_errors[:10]
        )
        
        assert len(scores) == 10
        assert len(is_anomaly) == 10
        assert len(breakdowns) == 10
        assert all(0 <= s <= 1 for s in scores)
    
    def test_save_and_load(self, tmp_path):
        """Test scorer serialization."""
        self.scorer.calibrate(self.all_if_scores, self.all_lstm_errors)
        
        save_path = str(tmp_path / "scorer.pkl")
        self.scorer.save(save_path)
        
        loaded = HybridAnomalyScorer.load(save_path)
        
        assert loaded.if_weight == self.scorer.if_weight
        assert loaded.lstm_weight == self.scorer.lstm_weight
        assert loaded._if_score_min == self.scorer._if_score_min
        assert loaded._lstm_error_max == self.scorer._lstm_error_max
        
        # Verify scoring works after load
        score1, _, _ = self.scorer.score(0.0, 0.05)
        score2, _, _ = loaded.score(0.0, 0.05)
        assert abs(score1 - score2) < 1e-6
    
    def test_score_range_clipping(self):
        """Test that scores are properly clipped to [0, 1]."""
        self.scorer.calibrate(self.all_if_scores, self.all_lstm_errors)
        
        # Extreme IF score (way below min)
        score, _, _ = self.scorer.score(-10.0, 100.0)
        assert 0.0 <= score <= 1.0
        
        # Extreme positive values
        score, _, _ = self.scorer.score(10.0, 0.0)
        assert 0.0 <= score <= 1.0


class TestThresholdManager:
    """Tests for the Threshold Manager."""
    
    def test_percentile_threshold(self):
        """Test percentile-based threshold computation."""
        np.random.seed(42)
        manager = ThresholdManager()
        normal_scores = np.random.normal(0.3, 0.05, 1000)
        
        threshold = manager.compute_percentile_threshold(
            normal_scores, percentile=99.0, model_name="test_model"
        )
        
        assert threshold > 0
        assert threshold == pytest.approx(
            np.percentile(normal_scores, 99.0), abs=1e-6
        )
    
    def test_fbeta_threshold(self):
        """Test F-beta threshold optimization."""
        np.random.seed(42)
        manager = ThresholdManager()
        
        scores = np.concatenate([
            np.random.uniform(0.1, 0.5, 90),  # normal
            np.random.uniform(0.6, 0.95, 10),  # anomaly
        ])
        y_true = np.array([0]*90 + [1]*10)
        
        threshold, best_f = manager.compute_fbeta_threshold(
            scores, y_true, beta=1.0, model_name="test_f1"
        )
        
        assert 0 < threshold < 1
        assert 0 <= best_f <= 1
    
    def test_feedback_adjustment(self):
        """Test threshold adjustment from feedback."""
        manager = ThresholdManager()
        manager.thresholds["test"] = {"value": 0.5, "method": "manual"}
        
        # More false positives → should raise threshold
        new_threshold = manager.adjust_from_feedback(
            "test",
            false_positive_count=80,
            false_negative_count=20,
            total_feedback=100
        )
        
        assert new_threshold > 0.5, \
            "Threshold should increase with more false positives"
    
    def test_save_and_load(self, tmp_path):
        """Test threshold manager serialization."""
        manager = ThresholdManager()
        np.random.seed(42)
        manager.compute_percentile_threshold(
            np.random.normal(0.3, 0.05, 1000),
            percentile=99.0,
            model_name="test_model"
        )
        
        save_path = str(tmp_path / "thresholds.pkl")
        manager.save(save_path)
        
        loaded = ThresholdManager.load(save_path)
        assert loaded.get_threshold("test_model") == \
            manager.get_threshold("test_model")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
