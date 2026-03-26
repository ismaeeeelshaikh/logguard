"""
Unit tests for LSTM Autoencoder model architecture, training, and evaluation.
"""

import os
import sys
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from ml.data.synthetic_generator import LogDataGenerator
from ml.data.data_loader import load_data, create_sequences


class TestLSTMAutoencoder:
    """Tests for the LSTM Autoencoder anomaly detection pipeline."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data."""
        self.gen = LogDataGenerator(seed=456)
        self.seq_len = 10  # Short for fast tests
        self.n_features = 107
        
        # Generate small dataset
        X_train, X_val, X_test, y_test = load_data(
            n_normal_train=300,
            n_normal_val=50,
            n_test=100,
            anomaly_ratio=0.1
        )
        self.X_train = X_train
        self.X_test = X_test
        self.y_test = y_test
        
        # Build sequences
        self.X_seq = create_sequences(X_test, seq_length=self.seq_len)
        self.y_seq = y_test[self.seq_len - 1:]
    
    def test_sequence_creation(self):
        """Test that sequence creation produces correct shapes."""
        assert self.X_seq.ndim == 3
        assert self.X_seq.shape[1] == self.seq_len
        assert self.X_seq.shape[2] == self.X_test.shape[1]
        assert len(self.y_seq) == len(self.X_seq)
    
    def test_model_architecture(self):
        """Test that model builds with correct input/output shapes."""
        from ml.models.lstm_autoencoder.architecture import (
            build_lstm_autoencoder
        )
        
        n_features = self.X_seq.shape[2]
        model = build_lstm_autoencoder(
            sequence_length=self.seq_len,
            n_features=n_features,
            encoding_dim=16,
            lstm_units=[32, 16],
            dropout_rate=0.1
        )
        
        # Check model input shape
        assert model.input_shape == (None, self.seq_len, n_features)
        # Check model output shape (should match input)
        assert model.output_shape == (None, self.seq_len, n_features)
    
    def test_model_forward_pass(self):
        """Test that model can process input and produce output."""
        from ml.models.lstm_autoencoder.architecture import (
            build_lstm_autoencoder
        )
        
        n_features = self.X_seq.shape[2]
        model = build_lstm_autoencoder(
            sequence_length=self.seq_len,
            n_features=n_features,
            encoding_dim=16,
            lstm_units=[32, 16]
        )
        
        # Forward pass
        batch = self.X_seq[:5].astype(np.float32)
        output = model.predict(batch, verbose=0)
        
        assert output.shape == batch.shape
        assert not np.any(np.isnan(output))
    
    def test_reconstruction_errors(self):
        """Test reconstruction error computation."""
        from ml.models.lstm_autoencoder.architecture import (
            build_lstm_autoencoder, get_reconstruction_errors
        )
        
        n_features = self.X_seq.shape[2]
        model = build_lstm_autoencoder(
            sequence_length=self.seq_len,
            n_features=n_features,
            encoding_dim=16,
            lstm_units=[32, 16]
        )
        
        errors = get_reconstruction_errors(
            model, self.X_seq[:20].astype(np.float32)
        )
        
        assert len(errors) == 20
        assert not np.any(np.isnan(errors))
        assert np.all(errors >= 0)  # MSE should be non-negative
    
    def test_model_training_quick(self):
        """Test that model can train for a few epochs without errors."""
        from ml.models.lstm_autoencoder.architecture import (
            build_lstm_autoencoder
        )
        from sklearn.preprocessing import StandardScaler
        
        # Use only normal sequences
        X_normal = self.X_seq[self.y_seq == 0][:50]
        n, seq_len, n_features = X_normal.shape
        
        # Scale
        scaler = StandardScaler()
        X_flat = X_normal.reshape(-1, n_features)
        X_scaled = scaler.fit_transform(X_flat).reshape(n, seq_len, n_features)
        
        model = build_lstm_autoencoder(
            sequence_length=seq_len,
            n_features=n_features,
            encoding_dim=8,
            lstm_units=[16, 8]
        )
        
        # Train for 2 epochs
        history = model.fit(
            X_scaled, X_scaled,
            epochs=2,
            batch_size=16,
            verbose=0
        )
        
        assert "loss" in history.history
        assert len(history.history["loss"]) == 2
        assert all(l > 0 for l in history.history["loss"])
    
    def test_evaluator(self):
        """Test the LSTM evaluator module."""
        from ml.models.lstm_autoencoder.architecture import (
            build_lstm_autoencoder
        )
        from ml.models.lstm_autoencoder.evaluator import LSTMEvaluator
        from sklearn.preprocessing import StandardScaler
        
        n_features = self.X_seq.shape[2]
        
        model = build_lstm_autoencoder(
            sequence_length=self.seq_len,
            n_features=n_features,
            encoding_dim=8,
            lstm_units=[16, 8]
        )
        
        # Quick train on normal data
        X_normal = self.X_seq[self.y_seq == 0][:30]
        n, sl, nf = X_normal.shape
        scaler = StandardScaler()
        X_flat = X_normal.reshape(-1, nf)
        X_scaled = scaler.fit_transform(X_flat).reshape(n, sl, nf)
        
        model.fit(X_scaled, X_scaled, epochs=2, batch_size=16, verbose=0)
        
        evaluator = LSTMEvaluator(model, scaler)
        results = evaluator.evaluate(
            self.X_seq[:50],
            self.y_seq[:50]
        )
        
        assert "precision" in results
        assert "recall" in results
        assert "f1_score" in results
        assert "roc_auc" in results
        assert "normal_error_stats" in results
        assert "separation_ratio" in results


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
