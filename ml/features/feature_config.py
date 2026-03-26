"""
Feature configuration for LogGuard ML models.
Defines feature names, ranges, vocabulary size, and expected shapes.
Must stay in sync with the Flink feature engineering output (Task 1).
"""

# ── Base scalar features (from Flink window aggregator) ──────────────────
BASE_FEATURE_NAMES = [
    "log_volume",
    "error_rate",
    "warn_rate",
    "unique_template_count",
    "template_entropy",
    "avg_response_time_ms",
    "p95_response_time_ms",
]

# ── Template vector config ───────────────────────────────────────────────
TEMPLATE_VOCABULARY_SIZE = 100  # Top-K log templates (must match Flink)

# ── Derived full feature list ────────────────────────────────────────────
TEMPLATE_FEATURE_NAMES = [f"template_{i:03d}" for i in range(TEMPLATE_VOCABULARY_SIZE)]
ALL_FEATURE_NAMES = BASE_FEATURE_NAMES + TEMPLATE_FEATURE_NAMES

# ── Expected shapes ──────────────────────────────────────────────────────
N_BASE_FEATURES = len(BASE_FEATURE_NAMES)            # 7
N_TEMPLATE_FEATURES = TEMPLATE_VOCABULARY_SIZE         # 100
N_TOTAL_FEATURES = N_BASE_FEATURES + N_TEMPLATE_FEATURES  # 107

# ── LSTM sequence config ────────────────────────────────────────────────
DEFAULT_SEQUENCE_LENGTH = 30  # 30 windows × 60s = 30 minutes of context

# ── Feature value ranges (for sanity checking / clipping) ────────────────
FEATURE_RANGES = {
    "log_volume":             (0, 100_000),
    "error_rate":             (0.0, 1.0),
    "warn_rate":              (0.0, 1.0),
    "unique_template_count":  (0, 500),
    "template_entropy":       (0.0, 10.0),
    "avg_response_time_ms":   (0.0, 60_000.0),
    "p95_response_time_ms":   (0.0, 120_000.0),
}

# ── Anomaly type labels ─────────────────────────────────────────────────
ANOMALY_TYPES = {
    0: "normal",
    1: "spike",
    2: "silent",
    3: "pattern",
    4: "slowdown",
}

# ── Model performance targets ───────────────────────────────────────────
PERFORMANCE_TARGETS = {
    "isolation_forest_f1":  0.75,
    "lstm_autoencoder_f1":  0.78,
    "hybrid_scorer_f1":     0.82,
    "hybrid_roc_auc":       0.90,
    "inference_time_ms":    10.0,
    "false_positive_rate":  0.05,
}
