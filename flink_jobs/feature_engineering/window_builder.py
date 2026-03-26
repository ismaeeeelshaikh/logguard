from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.window import TumblingEventTimeWindows, SlidingEventTimeWindows
from pyflink.common import Time, WatermarkStrategy
from pyflink.datastream.functions import WindowFunction
from collections import Counter
import math
import numpy as np
from typing import List

# Top-100 most common log templates across all tenants
# This vocabulary is shared and version-controlled
TEMPLATE_VOCABULARY_SIZE = 100

class HostWindowAggregator(WindowFunction):
    """
    Aggregates all log events in a time window for a single host
    into a fixed-length feature vector for ML inference.
    
    Window: 60-second tumbling + 300-second sliding
    """
    
    def apply(self, key: tuple, window, inputs):
        out = []
        events = list(inputs)
        
        if not events:
            return
        
        # ── Basic count features ─────────────────────────────
        total_logs = len(events)
        error_count = sum(1 for e in events if e.severity in ('ERROR', 'FATAL'))
        warn_count  = sum(1 for e in events if e.severity == 'WARN')
        
        error_rate = error_count / total_logs if total_logs > 0 else 0.0
        warn_rate  = warn_count  / total_logs if total_logs > 0 else 0.0
        
        # ── Template distribution features ───────────────────
        template_counts = Counter(e.template_id for e in events)
        unique_templates = len(template_counts)
        
        # Shannon entropy of template distribution
        # High entropy = many different unusual log types = suspicious
        entropy = 0.0
        for count in template_counts.values():
            p = count / total_logs
            entropy -= p * math.log2(p) if p > 0 else 0
        
        # ── Response time features ───────────────────────────
        response_times = [e.response_time_ms for e in events if e.response_time_ms is not None]
        avg_rt = float(np.mean(response_times)) if response_times else 0.0
        p95_rt = float(np.percentile(response_times, 95)) if response_times else 0.0
        
        # ── Template frequency vector (bag-of-templates) ─────
        # Fixed-size vector using known vocabulary
        template_vector = [0.0] * TEMPLATE_VOCABULARY_SIZE
        for template_id, count in template_counts.items():
            vocab_idx = hash(template_id) % TEMPLATE_VOCABULARY_SIZE
            template_vector[vocab_idx] += count / total_logs  # TF normalization
        
        # ── Assemble final feature record ────────────────────
        feature_record = {
            "feature_id": f"{key[0] if isinstance(key, tuple) else key}_{window.start}",
            "window_start": window.start,
            "window_end": window.end,
            "host": key[0] if isinstance(key, tuple) else key,
            "tenant_id": events[0].tenant_id,
            "log_volume": total_logs,
            "error_rate": error_rate,
            "warn_rate": warn_rate,
            "unique_template_count": unique_templates,
            "template_entropy": entropy,
            "avg_response_time_ms": avg_rt,
            "p95_response_time_ms": p95_rt,
            "template_vector": template_vector,
            "sequence_window_id": 0  # ML team will use this for LSTM sequencing
        }
        
        return [feature_record] # out.collect(feature_record)
