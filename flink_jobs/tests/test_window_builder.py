import math
import os
import sys
import types
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Create minimal pyflink stubs so we can import and test HostWindowAggregator
if "pyflink" not in sys.modules:
    pyflink = types.ModuleType("pyflink")
    datastream = types.ModuleType("pyflink.datastream")
    datastream.StreamExecutionEnvironment = object
    window = types.ModuleType("pyflink.datastream.window")
    window.TumblingEventTimeWindows = object
    window.SlidingEventTimeWindows = object
    common = types.ModuleType("pyflink.common")
    common.Time = object
    common.WatermarkStrategy = object
    functions = types.ModuleType("pyflink.datastream.functions")
    functions.WindowFunction = object

    sys.modules["pyflink"] = pyflink
    sys.modules["pyflink.datastream"] = datastream
    sys.modules["pyflink.datastream.window"] = window
    sys.modules["pyflink.common"] = common
    sys.modules["pyflink.datastream.functions"] = functions

from feature_engineering.window_builder import HostWindowAggregator, TEMPLATE_VOCABULARY_SIZE


class _Collector:
    def __init__(self):
        self.items = []

    def collect(self, value):
        self.items.append(value)


def _event(severity, template_id, response_time_ms, tenant_id="tenant_001"):
    return SimpleNamespace(
        severity=severity,
        template_id=template_id,
        response_time_ms=response_time_ms,
        tenant_id=tenant_id,
    )


def test_apply_emits_single_feature_record():
    aggregator = HostWindowAggregator()
    collector = _Collector()
    window = SimpleNamespace(start=1000, end=61000)

    events = [
        _event("INFO", "tpl_login", 100.0),
        _event("ERROR", "tpl_login", 200.0),
        _event("WARN", "tpl_disk", None),
        _event("FATAL", "tpl_db", 400.0),
    ]

    aggregator.apply("web-01", window, events, collector)

    assert len(collector.items) == 1
    record = collector.items[0]

    assert record["feature_id"] == "web-01_1000"
    assert record["window_start"] == 1000
    assert record["window_end"] == 61000
    assert record["host"] == "web-01"
    assert record["tenant_id"] == "tenant_001"

    assert record["log_volume"] == 4
    assert record["error_rate"] == pytest.approx(0.5)
    assert record["warn_rate"] == pytest.approx(0.25)
    assert record["unique_template_count"] == 3

    expected_entropy = -(0.5 * math.log2(0.5) + 0.25 * math.log2(0.25) + 0.25 * math.log2(0.25))
    assert record["template_entropy"] == pytest.approx(expected_entropy)

    assert record["avg_response_time_ms"] == pytest.approx((100.0 + 200.0 + 400.0) / 3.0)
    assert record["p95_response_time_ms"] == pytest.approx(380.0)

    assert len(record["template_vector"]) == TEMPLATE_VOCABULARY_SIZE
    assert sum(record["template_vector"]) == pytest.approx(1.0)
    assert record["sequence_window_id"] == 0


def test_apply_ignores_empty_windows():
    aggregator = HostWindowAggregator()
    collector = _Collector()
    window = SimpleNamespace(start=0, end=60000)

    aggregator.apply("web-01", window, [], collector)

    assert collector.items == []


def test_apply_sets_zero_rt_when_missing():
    aggregator = HostWindowAggregator()
    collector = _Collector()
    window = SimpleNamespace(start=5000, end=65000)

    events = [
        _event("INFO", "tpl_a", None),
        _event("WARN", "tpl_b", None),
    ]

    aggregator.apply("cache-01", window, events, collector)

    record = collector.items[0]
    assert record["avg_response_time_ms"] == 0.0
    assert record["p95_response_time_ms"] == 0.0
