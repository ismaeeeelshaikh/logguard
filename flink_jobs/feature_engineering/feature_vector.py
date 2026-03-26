import numpy as np
from typing import List, Dict, Optional


class FeatureVectorAssembler:
    """
    Assembles the final feature vector from aggregated window features.
    This vector is what the ML model consumes for anomaly detection.
    """

    # Feature order must match ML model's expected input
    SCALAR_FEATURES = [
        "log_volume",
        "error_rate",
        "warn_rate",
        "unique_template_count",
        "template_entropy",
        "avg_response_time_ms",
        "p95_response_time_ms",
    ]

    def __init__(self, template_vocab_size: int = 100):
        self.template_vocab_size = template_vocab_size
        self._means: Optional[np.ndarray] = None
        self._stds: Optional[np.ndarray] = None

    def assemble(self, feature_record: Dict) -> np.ndarray:
        """
        Convert a feature record dict into a flat numpy vector.

        Returns:
            np.ndarray of shape (7 + template_vocab_size,)
        """
        scalar = np.array(
            [float(feature_record.get(f, 0.0) or 0.0) for f in self.SCALAR_FEATURES],
            dtype=np.float32,
        )
        template_vec = np.array(
            feature_record.get("template_vector", [0.0] * self.template_vocab_size),
            dtype=np.float32,
        )
        return np.concatenate([scalar, template_vec])

    def fit_scaler(self, feature_records: List[Dict]):
        """
        Compute mean/std from a batch of feature records for z-score normalization.
        Call this during training data preparation.
        """
        vectors = np.array([self.assemble(r) for r in feature_records])
        self._means = vectors.mean(axis=0)
        self._stds = vectors.std(axis=0)
        self._stds[self._stds == 0] = 1.0  # avoid division by zero

    def normalize(self, feature_record: Dict) -> np.ndarray:
        """
        Z-score normalize a feature vector using pre-fitted stats.
        """
        vec = self.assemble(feature_record)
        if self._means is not None and self._stds is not None:
            return (vec - self._means) / self._stds
        return vec

    def get_feature_dim(self) -> int:
        """Return total feature dimension."""
        return len(self.SCALAR_FEATURES) + self.template_vocab_size
