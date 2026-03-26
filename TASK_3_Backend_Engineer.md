# ⚙️ LogGuard — Person 3: Backend Engineer
## Role: Inference Service, API & Alerting Lead

---

## 📌 Your Responsibility Summary

Tum LogGuard ka "nervous system" ho. Tumhara kaam:

1. **ML Inference Service** banana — Kafka se feature vectors consume karo, dono ML models se run karo, anomaly score produce karo
2. **FastAPI REST + WebSocket API** — Dashboard aur external systems ke liye endpoints
3. **Alerting Engine** — Anomaly detect hone pe Slack/PagerDuty/Email notifications
4. **Database layer** — TimescaleDB, Elasticsearch, Redis ka proper schema aur access layer
5. **Feedback API** — ML team ke retraining ke liye human feedback collect karo

Tumhara inference service **sub-2-second latency** pe chal rahi honi chahiye. Production mein yahi sab kuch monitor hoga.

---

## 🧰 Tech Stack (Tumhara Arsenal)

| Technology | Purpose | Seekhne ki zaroorat |
|---|---|---|
| **Python 3.11** | Primary language | High ⭐⭐⭐ |
| **FastAPI** | REST + WebSocket API framework | High ⭐⭐⭐ |
| **Kafka-Python / aiokafka** | Async Kafka consumer | High ⭐⭐⭐ |
| **MLflow** | Load production models | Medium ⭐⭐ |
| **TimescaleDB (asyncpg)** | Time-series anomaly storage | High ⭐⭐⭐ |
| **Elasticsearch-py** | Log search queries | Medium ⭐⭐ |
| **Redis (aioredis)** | LSTM state cache + pub/sub | Medium ⭐⭐ |
| **PostgreSQL (SQLAlchemy)** | App metadata, users, alert rules | Medium ⭐⭐ |
| **Celery** | Background tasks (notifications) | Medium ⭐⭐ |
| **Docker / Kubernetes** | Deployment | Medium ⭐⭐ |
| **Pytest + Testcontainers** | Integration testing | Medium ⭐⭐ |
| **Pydantic v2** | Data validation | Medium ⭐⭐ |

---

## 📁 Folder Structure (Tumhara Code)

```
logguard/
└── backend/
    ├── app/
    │   ├── main.py                      ← FastAPI app entry point
    │   ├── config.py                    ← Settings from env variables
    │   │
    │   ├── api/
    │   │   ├── v1/
    │   │   │   ├── anomalies.py         ← GET /anomalies endpoints
    │   │   │   ├── logs.py              ← GET /logs search endpoints
    │   │   │   ├── alerts.py            ← Alert rule CRUD
    │   │   │   ├── feedback.py          ← POST /feedback endpoint
    │   │   │   ├── hosts.py             ← Host status + stats
    │   │   │   └── websocket.py         ← WebSocket /ws/anomalies
    │   │   └── deps.py                  ← Shared dependencies (DB, auth)
    │   │
    │   ├── inference/
    │   │   ├── consumer.py              ← Kafka consumer loop (core!)
    │   │   ├── model_loader.py          ← Load IF + LSTM from MLflow
    │   │   ├── feature_buffer.py        ← Redis LSTM state buffer
    │   │   └── scorer.py               ← Hybrid scoring (synced with ML team)
    │   │
    │   ├── alerting/
    │   │   ├── engine.py               ← Alert rule evaluation
    │   │   ├── correlator.py           ← Multi-host incident correlation
    │   │   ├── notifiers/
    │   │   │   ├── slack.py
    │   │   │   ├── pagerduty.py
    │   │   │   └── email.py
    │   │   └── tasks.py                ← Celery tasks for async notifications
    │   │
    │   ├── db/
    │   │   ├── timescale.py            ← TimescaleDB connection + queries
    │   │   ├── elasticsearch.py        ← ES client + log search
    │   │   ├── redis_client.py         ← Redis connection + helpers
    │   │   ├── postgres.py             ← SQLAlchemy models + session
    │   │   └── schemas.sql             ← All DDL statements
    │   │
    │   ├── models/                     ← Pydantic models (not ML models)
    │   │   ├── anomaly.py
    │   │   ├── alert.py
    │   │   └── feedback.py
    │   │
    │   └── core/
    │       ├── auth.py                 ← JWT authentication
    │       ├── rca.py                  ← Root Cause Analysis engine
    │       └── logging.py              ← Structured logging setup
    │
    ├── tests/
    │   ├── conftest.py                 ← Testcontainers fixtures
    │   ├── test_inference_consumer.py
    │   ├── test_api_anomalies.py
    │   ├── test_alerting.py
    │   └── test_rca.py
    │
    ├── alembic/                        ← Database migrations
    ├── Dockerfile
    ├── docker-compose.backend.yml
    └── requirements.txt
```

---

## 🚀 Phase 1: Database Schema Setup (Week 9)

### Step 1.1 — Schema DDL

`app/db/schemas.sql`:
```sql
-- ─── TimescaleDB: Anomaly Scores (Time-Series) ─────────────────────────────

CREATE TABLE IF NOT EXISTS anomaly_scores (
    id              BIGSERIAL,
    scored_at       TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    host            TEXT            NOT NULL,
    tenant_id       TEXT            NOT NULL,
    final_score     FLOAT           NOT NULL,
    if_score        FLOAT           NOT NULL,
    lstm_score      FLOAT           NOT NULL,
    is_anomaly      BOOLEAN         NOT NULL DEFAULT FALSE,
    anomaly_type    TEXT,
    log_volume      INT,
    error_rate      FLOAT,
    feature_window_start  TIMESTAMPTZ,
    feature_window_end    TIMESTAMPTZ,
    raw_feature_vector    JSONB,
    
    PRIMARY KEY (id, scored_at)
);

-- Convert to TimescaleDB hypertable (partitioned by time)
SELECT create_hypertable('anomaly_scores', 'scored_at', if_not_exists => TRUE);

-- Index for dashboard queries
CREATE INDEX IF NOT EXISTS idx_anomaly_host_time
    ON anomaly_scores (tenant_id, host, scored_at DESC);

CREATE INDEX IF NOT EXISTS idx_anomaly_is_anomaly
    ON anomaly_scores (tenant_id, is_anomaly, scored_at DESC)
    WHERE is_anomaly = TRUE;

-- Continuous aggregate: 5-minute anomaly summary per host
CREATE MATERIALIZED VIEW IF NOT EXISTS anomaly_5min_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('5 minutes', scored_at) AS bucket,
    tenant_id,
    host,
    AVG(final_score)    AS avg_score,
    MAX(final_score)    AS max_score,
    COUNT(*)            AS window_count,
    SUM(CASE WHEN is_anomaly THEN 1 ELSE 0 END) AS anomaly_count
FROM anomaly_scores
GROUP BY bucket, tenant_id, host
WITH NO DATA;

-- Auto-refresh the continuous aggregate
SELECT add_continuous_aggregate_policy('anomaly_5min_summary',
    start_offset => INTERVAL '1 hour',
    end_offset   => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute'
);

-- Data retention: keep raw scores for 30 days, drop older
SELECT add_retention_policy('anomaly_scores', INTERVAL '30 days');


-- ─── PostgreSQL: Application Metadata ──────────────────────────────────────

CREATE TABLE IF NOT EXISTS tenants (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT UNIQUE NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    plan_tier   TEXT DEFAULT 'free'
);

CREATE TABLE IF NOT EXISTS users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email       TEXT UNIQUE NOT NULL,
    role        TEXT NOT NULL DEFAULT 'viewer'  -- viewer, analyst, admin
                    CHECK (role IN ('viewer', 'analyst', 'admin')),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    last_login  TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS alert_rules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    name            TEXT NOT NULL,
    description     TEXT,
    host_pattern    TEXT,               -- glob pattern: "web-*" or NULL for all
    score_threshold FLOAT NOT NULL DEFAULT 0.70,
    severity        TEXT DEFAULT 'high' CHECK (severity IN ('low','medium','high','critical')),
    notifier_type   TEXT NOT NULL,      -- slack, pagerduty, email
    notifier_config JSONB NOT NULL,     -- webhook URL, API key, etc.
    cooldown_minutes INT DEFAULT 15,    -- Min time between repeated alerts
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    created_by      UUID REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS anomaly_feedback (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    anomaly_id      BIGINT NOT NULL,    -- References anomaly_scores.id
    scored_at       TIMESTAMPTZ NOT NULL,
    host            TEXT NOT NULL,
    feedback_type   TEXT NOT NULL CHECK (feedback_type IN ('true_positive', 'false_positive')),
    submitted_by    UUID REFERENCES users(id),
    notes           TEXT,               -- Optional analyst comments
    feature_vector  JSONB,              -- Snapshot of the feature vector
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_feedback_tenant_date ON anomaly_feedback (tenant_id, created_at);

CREATE TABLE IF NOT EXISTS incidents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    started_at      TIMESTAMPTZ NOT NULL,
    resolved_at     TIMESTAMPTZ,
    affected_hosts  TEXT[] NOT NULL,
    max_severity    TEXT,
    anomaly_count   INT DEFAULT 0,
    status          TEXT DEFAULT 'open' CHECK (status IN ('open','investigating','resolved')),
    rca_summary     TEXT,               -- Auto-generated RCA text
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 🚀 Phase 2: FastAPI App Setup + Config (Week 9)

### Step 2.1 — App Config

`app/config.py`:
```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Application
    app_name: str = "LogGuard API"
    app_version: str = "1.0.0"
    debug: bool = False
    secret_key: str = "change-me-in-production"
    
    # Kafka
    kafka_bootstrap_servers: str = "kafka:29092"
    kafka_group_id: str = "logguard-inference-service"
    kafka_input_topic: str = "processed-features"
    kafka_output_topic: str = "anomaly-events"
    
    # TimescaleDB
    timescale_url: str = "postgresql+asyncpg://logguard:logguard@timescaledb:5432/logguard"
    
    # PostgreSQL (app metadata)
    postgres_url: str = "postgresql+asyncpg://logguard:logguard@postgres:5432/logguard_app"
    
    # Elasticsearch
    elasticsearch_hosts: list[str] = ["http://elasticsearch:9200"]
    elasticsearch_index_prefix: str = "logguard-logs"
    
    # Redis
    redis_url: str = "redis://redis:6379/0"
    redis_feature_buffer_ttl: int = 3600  # 1 hour TTL for LSTM buffers
    
    # MLflow
    mlflow_tracking_uri: str = "http://mlflow:5000"
    isolation_forest_model_name: str = "logguard-isolation-forest"
    lstm_model_name: str = "logguard-lstm-autoencoder"
    model_stage: str = "Production"
    
    # LSTM Inference Config
    lstm_sequence_length: int = 30
    
    # Scoring
    if_weight: float = 0.4
    lstm_weight: float = 0.6
    final_anomaly_threshold: float = 0.70
    
    # Alerting
    alert_cooldown_minutes: int = 15
    incident_correlation_window_seconds: int = 90
    incident_min_hosts: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

### Step 2.2 — Main FastAPI App

`app/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging

from app.config import get_settings
from app.inference.consumer import InferenceConsumer
from app.db.timescale import timescale_pool
from app.db.postgres import postgres_engine
from app.db.redis_client import redis_client
from app.api.v1 import anomalies, logs, alerts, feedback, hosts, websocket
from app.core.logging import configure_logging

configure_logging()
logger = logging.getLogger("logguard.main")
settings = get_settings()

# ── Global inference consumer (runs in background) ────────────────────────
inference_consumer: InferenceConsumer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: Initialize all connections + start Kafka consumer.
    Shutdown: Clean close of all connections.
    """
    global inference_consumer
    
    logger.info("🚀 LogGuard API starting up...")
    
    # Initialize DB connections
    await timescale_pool.connect()
    await redis_client.connect()
    
    # Load ML models from MLflow (once at startup)
    inference_consumer = InferenceConsumer(settings)
    await inference_consumer.initialize_models()
    
    # Start Kafka consumer as background task
    consumer_task = asyncio.create_task(
        inference_consumer.run(),
        name="kafka-inference-consumer"
    )
    
    logger.info("✅ LogGuard API ready.")
    
    yield  # API is running
    
    # Shutdown
    logger.info("🔴 LogGuard API shutting down...")
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass
    
    await timescale_pool.disconnect()
    await redis_client.disconnect()
    logger.info("✅ Shutdown complete.")


app = FastAPI(
    title="LogGuard API",
    version=settings.app_version,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://app.logguard.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Register all routers
app.include_router(anomalies.router, prefix="/api/v1/anomalies", tags=["Anomalies"])
app.include_router(logs.router,      prefix="/api/v1/logs",      tags=["Logs"])
app.include_router(alerts.router,    prefix="/api/v1/alerts",    tags=["Alerts"])
app.include_router(feedback.router,  prefix="/api/v1/feedback",  tags=["Feedback"])
app.include_router(hosts.router,     prefix="/api/v1/hosts",     tags=["Hosts"])
app.include_router(websocket.router, prefix="/ws",               tags=["WebSocket"])

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.app_version,
        "models_loaded": inference_consumer.models_ready if inference_consumer else False
    }
```

---

## 🚀 Phase 3: ML Inference Consumer — The Core (Week 10)

### Step 3.1 — Model Loader

`app/inference/model_loader.py`:
```python
import mlflow
import mlflow.sklearn
import mlflow.tensorflow
import joblib
import numpy as np
import logging
from typing import Optional

logger = logging.getLogger("logguard.model_loader")

class ModelRegistry:
    """
    Loads production ML models from MLflow Model Registry at startup.
    Both models are loaded once and kept in memory.
    Thread-safe for concurrent inference requests.
    """
    
    def __init__(self, settings):
        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        self.settings = settings
        
        self.if_model    = None  # IsolationForest
        self.if_scaler   = None  # StandardScaler for IF features
        self.lstm_model  = None  # Keras LSTM Autoencoder
        self.lstm_scaler = None  # StandardScaler for LSTM features
        
        self.if_threshold   = None
        self.lstm_threshold = None
        self.scorer_config  = None
        
        self._ready = False
    
    async def load(self) -> None:
        """Load all models. Called once at startup."""
        
        logger.info("Loading ML models from MLflow Registry...")
        
        try:
            # ── Load Isolation Forest ─────────────────────
            if_uri = f"models:/{self.settings.isolation_forest_model_name}/{self.settings.model_stage}"
            self.if_model = mlflow.sklearn.load_model(if_uri)
            
            # Load associated scaler and threshold from artifacts
            if_run_id = self._get_latest_run_id(self.settings.isolation_forest_model_name)
            artifacts = mlflow.artifacts.download_artifacts(
                run_id=if_run_id,
                artifact_path="artifacts/if_scaler.pkl"
            )
            self.if_scaler = joblib.load(artifacts)
            
            threshold_config = mlflow.artifacts.load_dict(
                run_id=if_run_id,
                artifact_path="threshold_config.json"
            )
            self.if_threshold = threshold_config["if_threshold"]
            
            logger.info(f"✅ Isolation Forest loaded. Threshold: {self.if_threshold:.4f}")
            
            # ── Load LSTM Autoencoder ─────────────────────
            lstm_uri = f"models:/{self.settings.lstm_model_name}/{self.settings.model_stage}"
            self.lstm_model = mlflow.tensorflow.load_model(lstm_uri)
            
            lstm_run_id = self._get_latest_run_id(self.settings.lstm_model_name)
            lstm_artifacts = mlflow.artifacts.download_artifacts(
                run_id=lstm_run_id,
                artifact_path="artifacts/lstm_scaler.pkl"
            )
            self.lstm_scaler = joblib.load(lstm_artifacts)
            
            lstm_config = mlflow.artifacts.load_dict(
                run_id=lstm_run_id,
                artifact_path="threshold_config.json"
            )
            self.lstm_threshold = lstm_config["lstm_threshold"]
            
            logger.info(f"✅ LSTM Autoencoder loaded. Threshold: {self.lstm_threshold:.6f}")
            
            self._ready = True
            
        except Exception as e:
            logger.error(f"❌ Failed to load models: {e}")
            raise RuntimeError(f"Model loading failed: {e}") from e
    
    @property
    def ready(self) -> bool:
        return self._ready
    
    def _get_latest_run_id(self, model_name: str) -> str:
        client = mlflow.MlflowClient()
        versions = client.get_latest_versions(model_name, stages=[self.settings.model_stage])
        if not versions:
            raise ValueError(f"No '{self.settings.model_stage}' model found: {model_name}")
        return versions[0].run_id
    
    def predict_isolation_forest(self, feature_vector: np.ndarray) -> tuple[float, float]:
        """
        Returns (raw_score, normalized_score) from IF model.
        raw_score: from decision_function (lower = more anomalous)
        """
        scaled = self.if_scaler.transform(feature_vector.reshape(1, -1))
        raw_score = float(self.if_model.decision_function(scaled)[0])
        return raw_score
    
    def predict_lstm(self, sequence: np.ndarray) -> float:
        """
        Returns reconstruction error (MSE) from LSTM.
        Higher = more anomalous.
        sequence shape: (1, seq_len, n_features)
        """
        scaled_flat = self.lstm_scaler.transform(
            sequence.reshape(-1, sequence.shape[-1])
        ).reshape(sequence.shape)
        
        reconstructed = self.lstm_model.predict(scaled_flat, verbose=0)
        mse = float(np.mean(np.power(sequence - reconstructed, 2)))
        return mse
```

### Step 3.2 — Kafka Consumer (The Heart)

`app/inference/consumer.py`:
```python
import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import numpy as np

from app.config import get_settings
from app.inference.model_loader import ModelRegistry
from app.inference.feature_buffer import LSTMFeatureBuffer
from app.inference.scorer import HybridScorer
from app.db.timescale import save_anomaly_score
from app.alerting.engine import AlertingEngine
from app.api.v1.websocket import broadcast_anomaly

logger = logging.getLogger("logguard.consumer")

class InferenceConsumer:
    """
    Core of LogGuard real-time inference.
    
    Lifecycle:
      1. Consume feature vector from Kafka (processed-features)
      2. Retrieve LSTM context from Redis buffer
      3. Run IF model (point anomaly)
      4. Run LSTM model (sequence anomaly)
      5. Compute hybrid score
      6. If anomaly: persist to TimescaleDB + alert + WebSocket broadcast
      7. Update Redis buffer with new vector
      8. Publish anomaly event to Kafka (anomaly-events)
    """
    
    def __init__(self, settings):
        self.settings  = settings
        self.registry  = ModelRegistry(settings)
        self.buffer    = LSTMFeatureBuffer(settings)
        self.scorer    = HybridScorer(settings)
        self.alerting  = AlertingEngine(settings)
        self.models_ready = False
        
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._producer: Optional[AIOKafkaProducer] = None
    
    async def initialize_models(self):
        """Called at startup — loads models from MLflow."""
        await self.registry.load()
        self.models_ready = True
        logger.info("✅ Models ready for inference.")
    
    async def run(self):
        """
        Main consumer loop. Runs forever as a background asyncio task.
        """
        
        self._consumer = AIOKafkaConsumer(
            self.settings.kafka_input_topic,
            bootstrap_servers=self.settings.kafka_bootstrap_servers,
            group_id=self.settings.kafka_group_id,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="latest",
            enable_auto_commit=False,      # Manual commit for exactly-once
            max_poll_records=50            # Batch up to 50 records per poll
        )
        
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self.settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            acks="all",
            enable_idempotence=True
        )
        
        await self._consumer.start()
        await self._producer.start()
        
        logger.info(f"🎧 Listening on Kafka topic: {self.settings.kafka_input_topic}")
        
        try:
            async for message in self._consumer:
                try:
                    await self._process_message(message.value)
                    await self._consumer.commit()  # Commit after successful processing
                except Exception as e:
                    logger.error(f"Processing error for message offset {message.offset}: {e}", exc_info=True)
                    # Don't commit — message will be reprocessed
                    await asyncio.sleep(0.1)
        
        except asyncio.CancelledError:
            logger.info("Consumer task cancelled — shutting down cleanly.")
        
        finally:
            await self._consumer.stop()
            await self._producer.stop()
    
    async def _process_message(self, feature_event: dict):
        """Process a single feature vector event."""
        
        start_time = asyncio.get_event_loop().time()
        
        host      = feature_event["host"]
        tenant_id = feature_event["tenant_id"]
        
        # ── Step 1: Extract flat feature vector (for IF) ──────
        feature_vector = np.array(self._extract_flat_features(feature_event), dtype=np.float32)
        
        # ── Step 2: Get LSTM sequence from Redis ──────────────
        sequence = await self.buffer.get_sequence(
            host=host,
            tenant_id=tenant_id,
            new_vector=feature_vector,
            seq_len=self.settings.lstm_sequence_length
        )
        
        # ── Step 3: Run Isolation Forest ──────────────────────
        if_raw_score = self.registry.predict_isolation_forest(feature_vector)
        
        # ── Step 4: Run LSTM (only if we have enough history) ─
        lstm_recon_error = 0.0
        if sequence is not None:
            lstm_recon_error = self.registry.predict_lstm(
                sequence.reshape(1, *sequence.shape)
            )
        
        # ── Step 5: Hybrid scoring ────────────────────────────
        final_score, is_anomaly, breakdown = self.scorer.score(
            if_raw_score=if_raw_score,
            lstm_recon_error=lstm_recon_error
        )
        
        # ── Step 6: Persist to TimescaleDB ───────────────────
        anomaly_record = {
            "scored_at": datetime.now(timezone.utc).isoformat(),
            "host": host,
            "tenant_id": tenant_id,
            "final_score": final_score,
            "if_score": breakdown["if_normalized"],
            "lstm_score": breakdown["lstm_normalized"],
            "is_anomaly": is_anomaly,
            "log_volume": feature_event.get("log_volume"),
            "error_rate": feature_event.get("error_rate"),
            "feature_window_start": feature_event.get("window_start"),
            "feature_window_end": feature_event.get("window_end"),
        }
        
        anomaly_id = await save_anomaly_score(anomaly_record)
        
        # ── Step 7: Anomaly actions ───────────────────────────
        if is_anomaly:
            logger.warning(
                f"🚨 ANOMALY on {host} | Score: {final_score:.3f} | "
                f"IF: {breakdown['if_normalized']:.3f} | LSTM: {breakdown['lstm_normalized']:.3f}"
            )
            
            # WebSocket broadcast to dashboard
            await broadcast_anomaly({
                "anomaly_id": str(anomaly_id),
                "host": host,
                "tenant_id": tenant_id,
                "final_score": final_score,
                "breakdown": breakdown,
                "timestamp": anomaly_record["scored_at"],
                "error_rate": feature_event.get("error_rate", 0)
            })
            
            # Trigger alert rules (async, non-blocking)
            asyncio.create_task(
                self.alerting.evaluate(anomaly_record, tenant_id=tenant_id)
            )
            
            # Publish to anomaly-events Kafka topic
            await self._producer.send(
                self.settings.kafka_output_topic,
                value={**anomaly_record, "breakdown": breakdown}
            )
        
        # ── Step 8: Update Redis buffer ───────────────────────
        await self.buffer.append_vector(host, tenant_id, feature_vector)
        
        # ── Performance logging ───────────────────────────────
        elapsed_ms = (asyncio.get_event_loop().time() - start_time) * 1000
        logger.debug(f"Processed {host} in {elapsed_ms:.1f}ms | anomaly={is_anomaly}")
        
        if elapsed_ms > 500:
            logger.warning(f"Slow inference on {host}: {elapsed_ms:.1f}ms")
    
    def _extract_flat_features(self, event: dict) -> list:
        """Extract ordered flat feature list matching training-time schema."""
        base = [
            event.get("log_volume", 0),
            event.get("error_rate", 0.0),
            event.get("warn_rate", 0.0),
            event.get("unique_template_count", 0),
            event.get("template_entropy", 0.0),
            event.get("avg_response_time_ms", 0.0),
            event.get("p95_response_time_ms", 0.0),
        ]
        template_vector = event.get("template_vector", [0.0] * 100)
        return base + template_vector  # Total: 107 features
```

### Step 3.3 — Redis LSTM Buffer

`app/inference/feature_buffer.py`:
```python
import numpy as np
import json
import logging
from typing import Optional
from app.db.redis_client import redis_client

logger = logging.getLogger("logguard.buffer")

class LSTMFeatureBuffer:
    """
    Maintains a rolling window of the last N feature vectors per host in Redis.
    This gives the LSTM its temporal context.
    
    Redis key format: lgbuf:{tenant_id}:{host}
    Value: JSON list of last `seq_len` vectors
    """
    
    def __init__(self, settings):
        self.seq_len = settings.lstm_sequence_length
        self.ttl     = settings.redis_feature_buffer_ttl
    
    def _key(self, host: str, tenant_id: str) -> str:
        return f"lgbuf:{tenant_id}:{host}"
    
    async def get_sequence(
        self,
        host: str,
        tenant_id: str,
        new_vector: np.ndarray,
        seq_len: int
    ) -> Optional[np.ndarray]:
        """
        Retrieve the current sequence buffer and append the new vector.
        Returns None if not enough history yet.
        """
        key = self._key(host, tenant_id)
        raw = await redis_client.get(key)
        
        if raw is None:
            # First time seeing this host — not enough history yet
            return None
        
        vectors = json.loads(raw)
        
        if len(vectors) < seq_len - 1:
            # Not enough history yet
            return None
        
        # Take last (seq_len - 1) vectors + current new vector
        recent = vectors[-(seq_len - 1):]
        sequence = np.array(recent + [new_vector.tolist()], dtype=np.float32)
        
        return sequence  # shape: (seq_len, n_features)
    
    async def append_vector(
        self,
        host: str,
        tenant_id: str,
        vector: np.ndarray
    ):
        """Append new vector to the host's buffer in Redis."""
        key = self._key(host, tenant_id)
        raw = await redis_client.get(key)
        
        vectors = json.loads(raw) if raw else []
        vectors.append(vector.tolist())
        
        # Keep only last seq_len vectors to bound memory
        if len(vectors) > self.seq_len:
            vectors = vectors[-self.seq_len:]
        
        await redis_client.setex(key, self.ttl, json.dumps(vectors))
```

---

## 🚀 Phase 4: API Endpoints (Week 10–11)

### Step 4.1 — Anomalies API

`app/api/v1/anomalies.py`:
```python
from fastapi import APIRouter, Query, Depends, HTTPException
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.db.timescale import get_anomalies, get_anomaly_timeline, get_host_stats
from app.core.rca import RootCauseAnalyzer
from app.api.deps import get_current_tenant

router = APIRouter()
rca_engine = RootCauseAnalyzer()

@router.get("/")
async def list_anomalies(
    host: Optional[str] = None,
    from_time: Optional[datetime] = None,
    to_time: Optional[datetime] = None,
    min_score: float = Query(default=0.70, ge=0.0, le=1.0),
    limit: int = Query(default=50, le=500),
    tenant_id: str = Depends(get_current_tenant)
):
    """
    List detected anomalies with optional filters.
    Used by dashboard anomaly table.
    """
    if from_time is None:
        from_time = datetime.now(timezone.utc) - timedelta(hours=24)
    if to_time is None:
        to_time = datetime.now(timezone.utc)
    
    anomalies = await get_anomalies(
        tenant_id=tenant_id,
        host=host,
        from_time=from_time,
        to_time=to_time,
        min_score=min_score,
        limit=limit
    )
    
    return {"anomalies": anomalies, "count": len(anomalies)}


@router.get("/timeline")
async def anomaly_timeline(
    host: Optional[str] = None,
    bucket_minutes: int = Query(default=5, ge=1, le=60),
    hours_back: int = Query(default=24, ge=1, le=168),
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Time-series data for the anomaly score chart.
    Returns bucketed average scores per host over time.
    """
    from_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    
    data = await get_anomaly_timeline(
        tenant_id=tenant_id,
        host=host,
        from_time=from_time,
        bucket_minutes=bucket_minutes
    )
    
    return {"timeline": data, "bucket_minutes": bucket_minutes}


@router.get("/{anomaly_id}/rca")
async def get_root_cause_analysis(
    anomaly_id: int,
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Auto-generate Root Cause Analysis for a specific anomaly.
    Queries Elasticsearch for unusual log patterns around the anomaly time.
    """
    # Fetch anomaly details
    anomaly = await get_anomalies(
        tenant_id=tenant_id,
        anomaly_id=anomaly_id,
        limit=1
    )
    
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    
    anomaly = anomaly[0]
    rca_result = await rca_engine.analyze(
        host=anomaly["host"],
        tenant_id=tenant_id,
        anomaly_time=anomaly["scored_at"],
        window_minutes=5
    )
    
    return {"anomaly_id": anomaly_id, "rca": rca_result}
```

### Step 4.2 — WebSocket for Real-Time Dashboard

`app/api/v1/websocket.py`:
```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json
import logging

router = APIRouter()
logger = logging.getLogger("logguard.websocket")

class ConnectionManager:
    """Manages active WebSocket connections for real-time anomaly push."""
    
    def __init__(self):
        self._active: List[WebSocket] = []
    
    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._active.append(ws)
        logger.info(f"WS connected. Total connections: {len(self._active)}")
    
    def disconnect(self, ws: WebSocket):
        self._active.remove(ws)
        logger.info(f"WS disconnected. Total connections: {len(self._active)}")
    
    async def broadcast(self, data: dict):
        """Push anomaly event to ALL connected dashboard clients."""
        message = json.dumps(data)
        dead_connections = []
        
        for ws in self._active:
            try:
                await ws.send_text(message)
            except Exception:
                dead_connections.append(ws)
        
        for ws in dead_connections:
            self._active.remove(ws)

manager = ConnectionManager()

async def broadcast_anomaly(anomaly_data: dict):
    """Called by inference consumer when anomaly is detected."""
    await manager.broadcast({"type": "anomaly", "data": anomaly_data})

@router.websocket("/anomalies")
async def anomaly_websocket(ws: WebSocket):
    """
    WebSocket endpoint for real-time anomaly streaming.
    
    Connect: ws://api/ws/anomalies
    Messages: {type: "anomaly", data: {host, score, timestamp, ...}}
    """
    await manager.connect(ws)
    try:
        while True:
            # Keep connection alive, respond to pings
            msg = await ws.receive_text()
            if msg == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(ws)
```

### Step 4.3 — Feedback API (For ML Retraining)

`app/api/v1/feedback.py`:
```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Literal
from app.db.postgres import get_db_session
from app.api.deps import get_current_user
import logging

router  = APIRouter()
logger  = logging.getLogger("logguard.feedback")

class FeedbackRequest(BaseModel):
    anomaly_id:    int
    scored_at:     str  # ISO timestamp
    host:          str
    feedback_type: Literal["true_positive", "false_positive"]
    notes:         str | None = None

@router.post("/")
async def submit_feedback(
    body: FeedbackRequest,
    user=Depends(get_current_user),
    db=Depends(get_db_session)
):
    """
    Submit analyst feedback on a detected anomaly.
    This data is used by the ML team's weekly retraining pipeline.
    
    Example:
      POST /api/v1/feedback
      {"anomaly_id": 4521, "scored_at": "2024-01-15T14:23:00Z",
       "host": "web-01", "feedback_type": "false_positive"}
    """
    
    await db.execute("""
        INSERT INTO anomaly_feedback
          (tenant_id, anomaly_id, scored_at, host, feedback_type, submitted_by, notes)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """,
        user.tenant_id,
        body.anomaly_id,
        body.scored_at,
        body.host,
        body.feedback_type,
        user.id,
        body.notes
    )
    
    logger.info(
        f"Feedback recorded: anomaly_id={body.anomaly_id} "
        f"type={body.feedback_type} by {user.email}"
    )
    
    return {"status": "recorded", "feedback_type": body.feedback_type}
```

---

## 🚀 Phase 5: Alerting Engine (Week 11–12)

`app/alerting/engine.py`:
```python
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.alerting.notifiers.slack import SlackNotifier
from app.alerting.notifiers.pagerduty import PagerDutyNotifier
from app.alerting.correlator import IncidentCorrelator
from app.db.postgres import get_alert_rules
from app.db.redis_client import redis_client

logger = logging.getLogger("logguard.alerting")

NOTIFIER_MAP = {
    "slack":      SlackNotifier,
    "pagerduty":  PagerDutyNotifier,
}

class AlertingEngine:
    """
    Evaluates configured alert rules against a new anomaly event.
    Implements cooldown deduplication and incident correlation.
    """
    
    def __init__(self, settings):
        self.settings   = settings
        self.correlator = IncidentCorrelator(settings)
    
    async def evaluate(self, anomaly: dict, tenant_id: str):
        """
        Called for every anomaly event. Non-blocking — runs as a background task.
        """
        
        host  = anomaly["host"]
        score = anomaly["final_score"]
        
        # ── Check if host is part of a correlated incident ──
        await self.correlator.record(host, tenant_id, anomaly["scored_at"])
        incident = await self.correlator.check_incident(tenant_id)
        
        if incident:
            logger.warning(
                f"🔴 Correlated incident detected: {incident['affected_hosts']} "
                f"({incident['anomaly_count']} anomalies)"
            )
            # Fire incident-level alert (higher severity)
            await self._fire_incident_alert(incident, tenant_id)
        
        # ── Evaluate individual alert rules ──────────────────
        rules = await get_alert_rules(tenant_id=tenant_id, is_active=True)
        
        for rule in rules:
            # Skip if score below rule threshold
            if score < rule["score_threshold"]:
                continue
            
            # Skip if host doesn't match rule pattern
            if rule["host_pattern"] and not self._host_matches(host, rule["host_pattern"]):
                continue
            
            # Cooldown check — prevent alert storm
            cooldown_key = f"alert_cd:{tenant_id}:{rule['id']}:{host}"
            if await redis_client.exists(cooldown_key):
                logger.debug(f"Alert rule {rule['id']} on cooldown for {host}")
                continue
            
            # Fire the alert
            await self._fire_alert(rule, anomaly)
            
            # Set cooldown
            await redis_client.setex(
                cooldown_key,
                rule["cooldown_minutes"] * 60,
                "1"
            )
    
    async def _fire_alert(self, rule: dict, anomaly: dict):
        """Dispatch notification via configured notifier."""
        notifier_class = NOTIFIER_MAP.get(rule["notifier_type"])
        if not notifier_class:
            logger.error(f"Unknown notifier type: {rule['notifier_type']}")
            return
        
        notifier = notifier_class(rule["notifier_config"])
        
        try:
            await notifier.send({
                "rule_name": rule["name"],
                "host": anomaly["host"],
                "score": anomaly["final_score"],
                "severity": rule["severity"],
                "timestamp": anomaly["scored_at"],
                "error_rate": anomaly.get("error_rate", 0),
                "dashboard_url": f"https://app.logguard.io/anomalies/{anomaly.get('id')}"
            })
            logger.info(f"✅ Alert sent via {rule['notifier_type']} for {anomaly['host']}")
        except Exception as e:
            logger.error(f"Failed to send alert via {rule['notifier_type']}: {e}")
    
    def _host_matches(self, host: str, pattern: str) -> bool:
        import fnmatch
        return fnmatch.fnmatch(host, pattern)
    
    async def _fire_incident_alert(self, incident: dict, tenant_id: str):
        """Fire a high-severity correlated incident alert."""
        # Use the highest-priority active rule for incident notification
        logger.warning(f"Incident alert for {len(incident['affected_hosts'])} hosts")
```

`app/alerting/notifiers/slack.py`:
```python
import httpx
import logging

logger = logging.getLogger("logguard.slack")

class SlackNotifier:
    
    def __init__(self, config: dict):
        self.webhook_url = config["webhook_url"]
        self.channel     = config.get("channel", "#alerts")
    
    async def send(self, alert_data: dict):
        score_pct = int(alert_data["score"] * 100)
        severity_emoji = {"low": "🟡", "medium": "🟠", "high": "🔴", "critical": "🚨"}.get(
            alert_data["severity"], "⚠️"
        )
        
        payload = {
            "channel": self.channel,
            "attachments": [{
                "color": "#FF0000" if alert_data["severity"] in ("high", "critical") else "#FFA500",
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": f"{severity_emoji} LogGuard Anomaly Detected"}
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*Host:*\n`{alert_data['host']}`"},
                            {"type": "mrkdwn", "text": f"*Anomaly Score:*\n{score_pct}%"},
                            {"type": "mrkdwn", "text": f"*Error Rate:*\n{alert_data['error_rate']*100:.1f}%"},
                            {"type": "mrkdwn", "text": f"*Severity:*\n{alert_data['severity'].upper()}"},
                        ]
                    },
                    {
                        "type": "actions",
                        "elements": [{
                            "type": "button",
                            "text": {"type": "plain_text", "text": "View in Dashboard"},
                            "url": alert_data["dashboard_url"],
                            "style": "danger"
                        }]
                    }
                ]
            }]
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.webhook_url, json=payload, timeout=5.0)
            resp.raise_for_status()
```

---

## 🧪 Testing Guide

`tests/conftest.py`:
```python
import pytest
import asyncio
from testcontainers.kafka import KafkaContainer
from testcontainers.redis import RedisContainer
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def kafka_container():
    with KafkaContainer() as kafka:
        yield kafka.get_bootstrap_server()

@pytest.fixture(scope="session")
async def redis_container():
    with RedisContainer() as redis:
        yield redis.get_connection_url()
```

---

## ✅ Deliverables / Checkpoints

### Week 9 Checkpoint
- [ ] All SQL schemas applied to local TimescaleDB
- [ ] FastAPI health endpoint `/health` return kare `{"status":"healthy"}`
- [ ] Postgres connection pooling working

### Week 10 Checkpoint
- [ ] Inference consumer chal raha ho (even with mock models)
- [ ] Feature vector kisi bhi host ke liye process ho
- [ ] Redis LSTM buffer correct sequence de raha ho

### Week 11 Checkpoint
- [ ] WebSocket se anomaly event dashboard tak pahunche (Postman se test karo)
- [ ] `/api/v1/anomalies/` endpoint live data return kare
- [ ] Feedback API kaam kare aur PostgreSQL mein row insert ho

### Week 12 Checkpoint
- [ ] Slack notifier kaam kare (test webhook pe)
- [ ] Alert cooldown Redis mein enforce ho
- [ ] Integration tests 80%+ pass ho with Testcontainers

---

## 🤝 Dependencies on Other Team Members

| Dependency | Kya chahiye | Kisse lo |
|---|---|---|
| Feature vector schema | Column names + dtypes | Person 1 |
| MLflow model URIs | Production model paths | Person 2 |
| Feedback table usage | Airflow DAG integration | Person 2 |
| Dashboard API contract | Which endpoints frontend needs | Person 4 |

---

## 📊 Performance Targets

| Metric | Target |
|---|---|
| End-to-end inference latency (P99) | ≤ 2 seconds |
| API response time (P95) | ≤ 200ms |
| WebSocket broadcast delay | ≤ 100ms |
| Kafka consumer lag (normal load) | ≤ 5,000 messages |
| Concurrent WebSocket connections | ≥ 100 |

---

## 📚 Resources to Study

1. **FastAPI Docs**: https://fastapi.tiangolo.com/
2. **aiokafka**: https://aiokafka.readthedocs.io/
3. **TimescaleDB Docs**: https://docs.timescale.com/
4. **Redis Async (aioredis)**: https://redis.readthedocs.io/en/stable/
5. **Testcontainers Python**: https://testcontainers-python.readthedocs.io/

---

*LogGuard Backend Engineer Task File — v1.0*  
*Tumhari inference service ke bina ML team ka kaam kisi kaam nahi. Closely coordinate karo.*
