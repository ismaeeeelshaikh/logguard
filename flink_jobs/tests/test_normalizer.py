import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from parsers.normalizer import LogNormalizer


@pytest.fixture
def normalizer():
    return LogNormalizer()


def test_normalize_masks_ip_uuid_hex_email_and_numbers(normalizer):
    raw = (
        "INFO user=john email=john.doe@example.com ip=10.0.0.5 "
        "uuid=123e4567-e89b-12d3-a456-426614174000 ptr=0x1A2B retries=42"
    )
    normalized = normalizer.normalize(raw)

    assert "<IP>" in normalized
    assert "<UUID>" in normalized
    assert "<HEX>" in normalized
    assert "<EMAIL>" in normalized
    assert "<NUM>" in normalized


def test_normalize_strips_whitespace(normalizer):
    raw = "   WARN: request took 145ms   "
    normalized = normalizer.normalize(raw)
    assert normalized.startswith("WARN")
    assert normalized.endswith("ms")


def test_extract_severity_direct_levels(normalizer):
    assert normalizer.extract_severity("DEBUG starting worker") == "DEBUG"
    assert normalizer.extract_severity("INFO healthy") == "INFO"
    assert normalizer.extract_severity("WARN low disk") == "WARN"
    assert normalizer.extract_severity("ERROR timeout") == "ERROR"
    assert normalizer.extract_severity("FATAL crash") == "FATAL"


def test_extract_severity_aliases(normalizer):
    assert normalizer.extract_severity("warning high memory") == "WARN"
    assert normalizer.extract_severity("critical db down") == "FATAL"


def test_extract_severity_missing(normalizer):
    assert normalizer.extract_severity("request completed successfully") is None
