"""
Feature preprocessor for LogGuard ML models.
Handles scaling, encoding, and transformation of raw feature vectors
from the Flink pipeline into model-ready inputs.

Must match the Flink output format exactly.
"""

import numpy as np
import joblib
from sklearn.preprocessing import StandardScaler
from typing import Optional, Tuple
from pathlib import Path

from .feature_config import (
    N_TOTAL_FEATURES,
    N_BASE_FEATURES,
    TEMPLATE_VOCABULARY_SIZE,
    FEATURE_RANGES,
    BASE_FEATURE_NAMES,
    DEFAULT_SEQUENCE_LENGTH,
)


class FeaturePreprocessor:
    """
    Preprocesses raw feature vectors for ML model consumption.
    
    Pipeline:
      1. Validate feature count & ranges
      2. Clip outliers to expected ranges
      3. StandardScaler normalization
    
    Supports both flat (IF) and sequential (LSTM) inputs.
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self._is_fitted = False
    
    def fit(self, X: np.ndarray) -> 'FeaturePreprocessor':
        """Fit the scaler on training data (normal data only)."""
        X_clipped = self._clip_features(X)
        self.scaler.fit(X_clipped)
        self._is_fitted = True
        return self
    
    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform a 2D feature array using the fitted scaler."""
        if not self._is_fitted:
            raise RuntimeError("Preprocessor not fitted. Call fit() first.")
        X_clipped = self._clip_features(X)
        return self.scaler.transform(X_clipped)
    
    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """Fit and transform in one step."""
        self.fit(X)
        return self.transform(X)
    
    def transform_sequences(
        self,
        X_seq: np.ndarray
    ) -> np.ndarray:
        """
        Transform 3D sequence data (n_samples, seq_len, n_features).
        Reshapes to 2D, transforms, then reshapes back.
        """
        if not self._is_fitted:
            raise RuntimeError("Preprocessor not fitted. Call fit() first.")
        
        n_samples, seq_len, n_features = X_seq.shape
        X_flat = X_seq.reshape(-1, n_features)
        X_transformed = self.transform(X_flat)
        return X_transformed.reshape(n_samples, seq_len, n_features)
    
    def build_sequences(
        self,
        X: np.ndarray,
        seq_length: int = DEFAULT_SEQUENCE_LENGTH
    ) -> np.ndarray:
        """
        Convert 2D array (n_samples, n_features) to 3D array
        (n_sequences, seq_length, n_features) for LSTM input.
        Uses sliding window with step=1.
        """
        if len(X) < seq_length:
            # Pad with copies of first sample
            padding = np.tile(X[0], (seq_length - len(X), 1))
            X = np.vstack([padding, X])
        
        sequences = []
        for i in range(len(X) - seq_length + 1):
            sequences.append(X[i:i + seq_length])
        return np.array(sequences, dtype=np.float32)
    
    def _clip_features(self, X: np.ndarray) -> np.ndarray:
        """Clip base features to expected ranges for robustness."""
        X_clipped = X.copy()
        for i, name in enumerate(BASE_FEATURE_NAMES):
            if name in FEATURE_RANGES and i < X.shape[1]:
                low, high = FEATURE_RANGES[name]
                X_clipped[:, i] = np.clip(X_clipped[:, i], low, high)
        return X_clipped
    
    def save(self, path: str) -> None:
        """Save the fitted preprocessor to disk."""
        joblib.dump({
            'scaler': self.scaler,
            'is_fitted': self._is_fitted,
        }, path)
    
    @classmethod
    def load(cls, path: str) -> 'FeaturePreprocessor':
        """Load a fitted preprocessor from disk."""
        data = joblib.load(path)
        preprocessor = cls()
        preprocessor.scaler = data['scaler']
        preprocessor._is_fitted = data['is_fitted']
        return preprocessor
    
    @staticmethod
    def validate_features(X: np.ndarray) -> bool:
        """Validate that input has the expected number of features."""
        if X.ndim == 2:
            return X.shape[1] == N_TOTAL_FEATURES
        elif X.ndim == 3:
            return X.shape[2] == N_TOTAL_FEATURES
        return False
