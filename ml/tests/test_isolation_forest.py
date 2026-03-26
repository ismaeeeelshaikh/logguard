"""
Unit tests for Isolation Forest model training and evaluation.
"""

import os
import sys
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from ml.data.synthetic_generator import LogDataGenerator
from ml.data.data_loader import load_data
from ml.models.isolation_forest.evaluator import IsolationForestEvaluator


class TestIsolationForest:
    """Tests for the Isolation Forest anomaly detection pipeline."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data."""
        self.gen = LogDataGenerator(seed=123)
        
        # Small dataset for fast tests
        X_train, X_val, X_test, y_test = load_data(
            n_normal_train=500,
            n_normal_val=100,
            n_test=200,
            anomaly_ratio=0.1
        )
        self.X_train = X_train
        self.X_val = X_val
        self.X_test = X_test
        self.y_test = y_test
    
    def test_data_shapes(self):
        """Test that data loader produces correct shapes."""
        assert self.X_train.ndim == 2
        assert self.X_test.ndim == 2
        assert self.X_train.shape[1] == self.X_test.shape[1]
        assert len(self.y_test) == len(self.X_test)
    
    def test_data_has_anomalies(self):
        """Test that test data contains both normal and anomaly samples."""
        assert self.y_test.sum() > 0, "No anomalies in test data"
        assert (self.y_test == 0).sum() > 0, "No normal samples in test data"
    
    def test_isolation_forest_training(self):
        """Test that IF model can train and predict without errors."""
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(self.X_train)
        X_test_scaled = scaler.transform(self.X_test)
        
        model = IsolationForest(
            n_estimators=50,
            contamination=0.05,
            random_state=42
        )
        model.fit(X_train_scaled)
        
        # Test predictions
        predictions = model.predict(X_test_scaled)
        assert len(predictions) == len(self.X_test)
        assert set(np.unique(predictions)).issubset({-1, 1})
        
        # Test decision function
        scores = model.decision_function(X_test_scaled)
        assert len(scores) == len(self.X_test)
        assert not np.any(np.isnan(scores))
    
    def test_anomaly_scores_distribution(self):
        """Test that anomaly scores separate normal from anomalous."""
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(self.X_train)
        X_test_scaled = scaler.transform(self.X_test)
        
        model = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42
        )
        model.fit(X_train_scaled)
        
        scores = model.decision_function(X_test_scaled)
        
        # Normal samples should have higher scores (less anomalous)
        normal_mean = scores[self.y_test == 0].mean()
        anomaly_mean = scores[self.y_test == 1].mean()
        
        # Anomalies should have lower scores on average
        assert anomaly_mean < normal_mean, \
            f"Anomaly scores ({anomaly_mean:.4f}) not lower than normal ({normal_mean:.4f})"
    
    def test_evaluator(self):
        """Test the IF evaluator module."""
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(self.X_train)
        
        model = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42
        )
        model.fit(X_train_scaled)
        
        evaluator = IsolationForestEvaluator(model, scaler)
        results = evaluator.evaluate(self.X_test, self.y_test)
        
        assert "precision" in results
        assert "recall" in results
        assert "f1_score" in results
        assert "roc_auc" in results
        assert 0 <= results["precision"] <= 1
        assert 0 <= results["recall"] <= 1
        assert 0 <= results["f1_score"] <= 1
    
    def test_threshold_optimization(self):
        """Test that threshold optimization produces valid results."""
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(self.X_train)
        
        model = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42
        )
        model.fit(X_train_scaled)
        
        evaluator = IsolationForestEvaluator(model, scaler)
        
        # Get scores
        X_test_scaled = scaler.transform(self.X_test)
        raw_scores = model.decision_function(X_test_scaled)
        score_range = raw_scores.max() - raw_scores.min()
        anomaly_scores = 1 - (raw_scores - raw_scores.min()) / score_range
        
        threshold, best_f = evaluator.find_optimal_threshold(
            anomaly_scores, self.y_test
        )
        
        assert 0 < threshold < 1, f"Threshold {threshold} out of range"
        assert 0 <= best_f <= 1, f"F-score {best_f} out of range"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
