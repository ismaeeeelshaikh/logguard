import pytest
import sys
import os
import math
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from feature_engineering.feature_vector import FeatureVectorAssembler


@pytest.fixture
def assembler():
    return FeatureVectorAssembler(template_vocab_size=100)


def make_feature_record(**overrides):
    """Helper to create a feature record with defaults."""
    record = {
        "feature_id": "web-01_1710835200000",
        "window_start": 1710835200000,
        "window_end": 1710835260000,
        "host": "web-01",
        "tenant_id": "tenant_001",
        "log_volume": 150,
        "error_rate": 0.05,
        "warn_rate": 0.10,
        "unique_template_count": 12,
        "template_entropy": 2.5,
        "avg_response_time_ms": 120.5,
        "p95_response_time_ms": 450.0,
        "template_vector": [0.0] * 100,
        "sequence_window_id": 0,
    }
    record.update(overrides)
    return record


class TestFeatureVectorAssembler:
    """Tests for feature vector assembly and normalization."""

    def test_assemble_returns_numpy_array(self, assembler):
        record = make_feature_record()
        vec = assembler.assemble(record)
        assert isinstance(vec, np.ndarray)

    def test_assemble_correct_dimension(self, assembler):
        record = make_feature_record()
        vec = assembler.assemble(record)
        expected_dim = 7 + 100  # 7 scalar + 100 template vocab
        assert vec.shape == (expected_dim,)

    def test_assemble_scalar_values(self, assembler):
        record = make_feature_record(
            log_volume=200,
            error_rate=0.1,
            warn_rate=0.2,
            unique_template_count=15,
            template_entropy=3.0,
            avg_response_time_ms=100.0,
            p95_response_time_ms=500.0,
        )
        vec = assembler.assemble(record)
        assert vec[0] == 200.0    # log_volume
        assert vec[1] == pytest.approx(0.1)   # error_rate
        assert vec[2] == pytest.approx(0.2)   # warn_rate
        assert vec[3] == 15.0     # unique_template_count
        assert vec[4] == pytest.approx(3.0)   # template_entropy
        assert vec[5] == pytest.approx(100.0) # avg_response_time_ms
        assert vec[6] == pytest.approx(500.0) # p95_response_time_ms

    def test_assemble_with_none_values(self, assembler):
        record = make_feature_record(
            avg_response_time_ms=None,
            p95_response_time_ms=None,
        )
        vec = assembler.assemble(record)
        assert vec[5] == 0.0
        assert vec[6] == 0.0

    def test_assemble_template_vector(self, assembler):
        tv = [0.0] * 100
        tv[0] = 0.5
        tv[50] = 0.3
        record = make_feature_record(template_vector=tv)
        vec = assembler.assemble(record)
        assert vec[7] == pytest.approx(0.5)
        assert vec[57] == pytest.approx(0.3)

    def test_get_feature_dim(self, assembler):
        assert assembler.get_feature_dim() == 107

    def test_fit_scaler(self, assembler):
        records = [
            make_feature_record(log_volume=100, error_rate=0.01),
            make_feature_record(log_volume=200, error_rate=0.05),
            make_feature_record(log_volume=300, error_rate=0.09),
        ]
        assembler.fit_scaler(records)
        assert assembler._means is not None
        assert assembler._stds is not None
        assert assembler._means.shape == (107,)

    def test_normalize_after_fit(self, assembler):
        records = [
            make_feature_record(log_volume=100, error_rate=0.01),
            make_feature_record(log_volume=200, error_rate=0.05),
            make_feature_record(log_volume=300, error_rate=0.09),
        ]
        assembler.fit_scaler(records)
        normalized = assembler.normalize(make_feature_record(log_volume=200, error_rate=0.05))
        # Mean value should normalize to ~0
        assert abs(normalized[0]) < 1.0  # log_volume near mean

    def test_normalize_without_fit(self, assembler):
        """Without fitting, normalize should return raw vector."""
        record = make_feature_record()
        vec_raw = assembler.assemble(record)
        vec_norm = assembler.normalize(record)
        np.testing.assert_array_equal(vec_raw, vec_norm)

    def test_different_vocab_sizes(self):
        assembler_50 = FeatureVectorAssembler(template_vocab_size=50)
        assembler_200 = FeatureVectorAssembler(template_vocab_size=200)
        assert assembler_50.get_feature_dim() == 57
        assert assembler_200.get_feature_dim() == 207

    def test_zero_log_volume(self, assembler):
        record = make_feature_record(log_volume=0, error_rate=0.0, warn_rate=0.0)
        vec = assembler.assemble(record)
        assert vec[0] == 0.0

    def test_high_entropy(self, assembler):
        record = make_feature_record(template_entropy=8.0)
        vec = assembler.assemble(record)
        assert vec[4] == pytest.approx(8.0)
