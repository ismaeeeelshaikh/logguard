# 🛠️ LogGuard — Person 1: Data Engineer
## Role: Data Pipeline & Infrastructure Lead

---

## 📌 Your Responsibility Summary

Tum is project ki **neenv** ho. Tumhara kaam hai ek aisi robust data pipeline banana jo:
- Har jagah se logs collect kare (servers, apps, containers)
- Unhe real-time Kafka me bheje
- Flink ke through process kare
- Clean, structured data ML team aur Backend team ko deta rahe

Agar tumhari pipeline nahi chal rahi, toh poora LogGuard ruk jaata hai. **Highest priority role.**

---

## 🧰 Tech Stack (Tumhara Arsenal)

| Technology | Purpose | Seekhne ki zaroorat |
|---|---|---|
| **Apache Kafka** | Distributed message broker | High ⭐⭐⭐ |
| **Fluentbit** | Lightweight log collector agent | Medium ⭐⭐ |
| **Apache Flink (PyFlink)** | Stream processing engine | High ⭐⭐⭐ |
| **Drain3** | Automatic log template parsing | Medium ⭐⭐ |
| **Docker & Docker Compose** | Local dev environment | Medium ⭐⭐ |
| **Kubernetes + Helm** | Production deployment | High ⭐⭐⭐ |
| **Avro + Schema Registry** | Data serialization & schema enforcement | Medium ⭐⭐ |
| **MinIO / AWS S3** | Flink checkpoint storage | Low ⭐ |
| **Python** | Flink jobs + utility scripts | Medium ⭐⭐ |

---

## 📁 Folder Structure (Tumhara Code)

```
logguard/
├── infrastructure/
│   ├── docker-compose.yml          ← Local dev: Kafka, Zookeeper, Schema Registry
│   ├── docker-compose.elastic.yml  ← Elasticsearch + Kibana local
│   └── docker-compose.storage.yml  ← TimescaleDB + Redis local
│
├── collectors/
│   ├── fluentbit/
│   │   ├── fluent-bit.conf         ← Main Fluentbit config
│   │   ├── parsers.conf            ← Log format parsers (Nginx, syslog, etc.)
│   │   └── k8s-daemonset.yaml      ← Kubernetes DaemonSet manifest
│   └── logstash/
│       ├── logstash.conf           ← Legacy source pipeline config
│       └── Dockerfile
│
├── kafka/
│   ├── topic_setup.sh              ← Script to create all Kafka topics
│   ├── schemas/
│   │   ├── raw_log.avsc            ← Avro schema for raw logs
│   │   └── processed_features.avsc ← Avro schema for ML features
│   └── admin/
│       └── kafka_admin.py          ← Topic management utility
│
├── flink_jobs/
│   ├── requirements.txt
│   ├── log_processor.py            ← Main Flink streaming job
│   ├── parsers/
│   │   ├── drain3_parser.py        ← Drain3 template extraction
│   │   └── normalizer.py           ← Feature normalization
│   ├── feature_engineering/
│   │   ├── window_builder.py       ← Sliding/tumbling window logic
│   │   └── feature_vector.py       ← Final feature vector assembly
│   └── tests/
│       ├── test_drain3.py
│       └── test_feature_engineering.py
│
└── helm/
    ├── kafka/                      ← Bitnami Kafka Helm chart values
    ├── flink/                      ← Flink Kubernetes Operator config
    └── fluentbit/                  ← Fluentbit Helm chart values
```

---

## 🚀 Phase 1: Local Development Environment Setup (Week 1)

### Step 1.1 — Docker Compose Setup

Ye file banao `infrastructure/docker-compose.yml`:

```yaml
version: '3.8'

services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - "2181:2181"

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
      - "9101:9101"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: 'zookeeper:2181'
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: 'false'

  schema-registry:
    image: confluentinc/cp-schema-registry:7.5.0
    depends_on:
      - kafka
    ports:
      - "8081:8081"
    environment:
      SCHEMA_REGISTRY_HOST_NAME: schema-registry
      SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS: 'kafka:29092'

  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    ports:
      - "8080:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: local
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:29092
      KAFKA_CLUSTERS_0_SCHEMAREGISTRY: http://schema-registry:8081
```

### Step 1.2 — Kafka Topics Create Karo

`kafka/topic_setup.sh` banao:

```bash
#!/bin/bash
set -e

KAFKA_BROKER="localhost:9092"

echo "Creating Kafka topics..."

# Raw logs topic - high throughput, 6 partitions
kafka-topics.sh --create \
  --bootstrap-server $KAFKA_BROKER \
  --topic raw-logs \
  --partitions 6 \
  --replication-factor 1 \
  --config retention.ms=86400000 \
  --config compression.type=lz4

# Processed features topic - ML input
kafka-topics.sh --create \
  --bootstrap-server $KAFKA_BROKER \
  --topic processed-features \
  --partitions 6 \
  --replication-factor 1 \
  --config retention.ms=86400000

# Anomaly events topic - alert triggers
kafka-topics.sh --create \
  --bootstrap-server $KAFKA_BROKER \
  --topic anomaly-events \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=604800000

echo "✅ All topics created successfully!"
kafka-topics.sh --list --bootstrap-server $KAFKA_BROKER
```

### Step 1.3 — Avro Schemas Define Karo

`kafka/schemas/raw_log.avsc`:
```json
{
  "type": "record",
  "name": "RawLog",
  "namespace": "com.logguard",
  "fields": [
    {"name": "log_id", "type": "string"},
    {"name": "timestamp", "type": "long", "logicalType": "timestamp-millis"},
    {"name": "host", "type": "string"},
    {"name": "source", "type": "string"},
    {"name": "severity", "type": {"type": "enum", "name": "Severity", "symbols": ["DEBUG","INFO","WARN","ERROR","FATAL"]}},
    {"name": "raw_message", "type": "string"},
    {"name": "service_name", "type": ["null", "string"], "default": null},
    {"name": "container_id", "type": ["null", "string"], "default": null},
    {"name": "tenant_id", "type": "string"}
  ]
}
```

`kafka/schemas/processed_features.avsc`:
```json
{
  "type": "record",
  "name": "ProcessedFeatures",
  "namespace": "com.logguard",
  "fields": [
    {"name": "feature_id", "type": "string"},
    {"name": "window_start", "type": "long", "logicalType": "timestamp-millis"},
    {"name": "window_end", "type": "long", "logicalType": "timestamp-millis"},
    {"name": "host", "type": "string"},
    {"name": "tenant_id", "type": "string"},
    {"name": "log_volume", "type": "int"},
    {"name": "error_rate", "type": "float"},
    {"name": "warn_rate", "type": "float"},
    {"name": "unique_template_count", "type": "int"},
    {"name": "template_entropy", "type": "float"},
    {"name": "avg_response_time_ms", "type": ["null", "float"], "default": null},
    {"name": "p95_response_time_ms", "type": ["null", "float"], "default": null},
    {"name": "template_vector", "type": {"type": "array", "items": "float"}},
    {"name": "sequence_window_id", "type": "int"}
  ]
}
```

---

## 🚀 Phase 2: Fluentbit Log Collector Setup (Week 2)

### Step 2.1 — Fluentbit Config

`collectors/fluentbit/fluent-bit.conf`:
```ini
[SERVICE]
    Flush         1
    Daemon        Off
    Log_Level     info
    Parsers_File  parsers.conf
    HTTP_Server   On
    HTTP_Listen   0.0.0.0
    HTTP_Port     2020

# ─── INPUT SOURCES ────────────────────────────────────────

[INPUT]
    Name              tail
    Path              /var/log/nginx/access.log
    Parser            nginx
    Tag               nginx.access
    Refresh_Interval  5
    Mem_Buf_Limit     50MB
    Skip_Long_Lines   On

[INPUT]
    Name              tail
    Path              /var/log/syslog
    Parser            syslog-rfc3164
    Tag               system.syslog
    Refresh_Interval  5

[INPUT]
    Name              systemd
    Tag               system.journald
    Read_From_Tail    On
    Strip_Underscores On

# ─── FILTERS ──────────────────────────────────────────────

[FILTER]
    Name    record_modifier
    Match   *
    Record  host ${HOSTNAME}
    Record  tenant_id ${LOGGUARD_TENANT_ID}

[FILTER]
    Name   grep
    Match  nginx.access
    Exclude log ^$

# ─── OUTPUT TO KAFKA ──────────────────────────────────────

[OUTPUT]
    Name                          kafka
    Match                         *
    Brokers                       kafka:29092
    Topics                        raw-logs
    Timestamp_Key                 timestamp
    Timestamp_Format              double
    Retry_Limit                   false
    rdkafka.compression.codec     lz4
    rdkafka.request.required.acks -1
```

`collectors/fluentbit/parsers.conf`:
```ini
[PARSER]
    Name        nginx
    Format      regex
    Regex       ^(?<remote>[^ ]*) (?<host>[^ ]*) (?<user>[^ ]*) \[(?<time>[^\]]*)\] "(?<method>\S+)(?: +(?<path>[^\"]*?)(?: +\S*)?)?" (?<code>[^ ]*) (?<size>[^ ]*)(?: "(?<referer>[^\"]*)" "(?<agent>[^\"]*)")?$
    Time_Key    time
    Time_Format %d/%b/%Y:%H:%M:%S %z

[PARSER]
    Name        syslog-rfc3164
    Format      regex
    Regex       ^\<(?<pri>[0-9]+)\>(?<time>[^ ]* {1,2}[^ ]* [^ ]*) (?<host>[^ ]*) (?<ident>[a-zA-Z0-9_\/\.\-]*)(?:\[(?<pid>[0-9]+)\])?(?:[^\:]*\:)? *(?<message>.+)$
    Time_Key    time
    Time_Format %b %d %H:%M:%S

[PARSER]
    Name        json
    Format      json
    Time_Key    timestamp
    Time_Format %Y-%m-%dT%H:%M:%S.%L%z
```

### Step 2.2 — Kubernetes DaemonSet

`collectors/fluentbit/k8s-daemonset.yaml`:
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentbit
  namespace: logguard
  labels:
    app: fluentbit
spec:
  selector:
    matchLabels:
      app: fluentbit
  template:
    metadata:
      labels:
        app: fluentbit
    spec:
      serviceAccountName: fluentbit
      tolerations:
        - key: node-role.kubernetes.io/master
          effect: NoSchedule
      containers:
        - name: fluentbit
          image: fluent/fluent-bit:2.2
          resources:
            limits:
              memory: 200Mi
              cpu: 200m
            requests:
              memory: 100Mi
              cpu: 100m
          volumeMounts:
            - name: varlog
              mountPath: /var/log
              readOnly: true
            - name: varlibdockercontainers
              mountPath: /var/lib/docker/containers
              readOnly: true
            - name: fluentbit-config
              mountPath: /fluent-bit/etc/
          env:
            - name: HOSTNAME
              valueFrom:
                fieldRef:
                  fieldPath: spec.nodeName
            - name: LOGGUARD_TENANT_ID
              valueFrom:
                secretKeyRef:
                  name: logguard-secrets
                  key: tenant-id
      volumes:
        - name: varlog
          hostPath:
            path: /var/log
        - name: varlibdockercontainers
          hostPath:
            path: /var/lib/docker/containers
        - name: fluentbit-config
          configMap:
            name: fluentbit-config
```

---

## 🚀 Phase 3: Apache Flink Stream Processing Job (Week 3–4)

### Step 3.1 — Drain3 Log Parser

`flink_jobs/parsers/drain3_parser.py`:
```python
from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig
import json
import re
from typing import Optional

class LogGuardParser:
    """
    Drain3-based log template extractor.
    Automatically discovers log patterns without manual regex.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        config = TemplateMinerConfig()
        config.load(config_path or "drain3.ini")
        self.miner = TemplateMiner(config=config)
        self._numeric_pattern = re.compile(r'\b\d+\.?\d*\b')
        
    def parse(self, log_message: str) -> dict:
        """
        Parse a raw log message into template + parameters.
        
        Returns:
            {
              "template": "User <*> logged in from <*>",
              "template_id": "a3f8b2",
              "parameters": ["john_doe", "192.168.1.1"],
              "response_time_ms": 145.0  # extracted if present
            }
        """
        result = self.miner.add_log_message(log_message)
        
        if result is None:
            return {
                "template": log_message[:200],
                "template_id": "unknown",
                "parameters": [],
                "response_time_ms": None
            }
        
        template = result["template_mined"]
        
        # Extract response time if pattern like "in 145ms" or "took 145ms"
        response_time = self._extract_response_time(log_message)
        
        return {
            "template": template,
            "template_id": result["cluster_id"],
            "parameters": result.get("change_type", ""),
            "response_time_ms": response_time
        }
    
    def _extract_response_time(self, log_message: str) -> Optional[float]:
        """Extract response time in ms from common log patterns."""
        patterns = [
            r'(\d+\.?\d*)\s*ms',
            r'took\s+(\d+\.?\d*)',
            r'duration[=:]\s*(\d+\.?\d*)',
            r'"(?:GET|POST|PUT|DELETE)[^"]*"\s+\d+\s+(\d+)',  # Nginx response time
        ]
        for pattern in patterns:
            match = re.search(pattern, log_message, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return None
    
    def get_template_vocabulary(self) -> dict:
        """Return all discovered templates — expose this to dashboard."""
        return {
            cluster.cluster_id: cluster.get_template()
            for cluster in self.miner.drain.id_to_cluster.values()
        }
```

### Step 3.2 — Feature Engineering

`flink_jobs/feature_engineering/window_builder.py`:
```python
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
    
    def apply(self, key: str, window, inputs, out):
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
            "feature_id": f"{key}_{window.start}",
            "window_start": window.start,
            "window_end": window.end,
            "host": key,
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
        
        out.collect(feature_record)
```

### Step 3.3 — Main Flink Job

`flink_jobs/log_processor.py`:
```python
from pyflink.datastream import StreamExecutionEnvironment, RuntimeExecutionMode
from pyflink.datastream.connectors.kafka import FlinkKafkaConsumer, FlinkKafkaProducer
from pyflink.common import WatermarkStrategy, Time
from pyflink.datastream.window import TumblingEventTimeWindows, SlidingEventTimeWindows
from pyflink.common.serialization import SimpleStringSchema
from parsers.drain3_parser import LogGuardParser
from feature_engineering.window_builder import HostWindowAggregator
import json
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LogGuard-Flink")

def create_log_processor_job():
    """
    Main Flink streaming job for LogGuard.
    
    Flow:
      Kafka(raw-logs) 
        → Parse (Drain3 template extraction)
        → KeyBy(host)
        → Window(60s tumbling + 300s sliding)
        → Aggregate features
        → Kafka(processed-features)
    """
    
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_runtime_mode(RuntimeExecutionMode.STREAMING)
    env.set_parallelism(4)
    
    # ── Enable checkpointing for fault tolerance ──────────────
    env.enable_checkpointing(30_000)  # Every 30 seconds
    checkpoint_config = env.get_checkpoint_config()
    checkpoint_config.set_checkpoint_storage_uri("s3://logguard-checkpoints/flink/")
    checkpoint_config.set_min_pause_between_checkpoints(5_000)
    checkpoint_config.set_checkpoint_timeout(60_000)
    
    # ── Kafka Consumer ────────────────────────────────────────
    kafka_props = {
        "bootstrap.servers": "kafka:29092",
        "group.id": "logguard-flink-processor",
        "auto.offset.reset": "latest",
        "enable.auto.commit": "false"  # Flink manages offsets
    }
    
    consumer = FlinkKafkaConsumer(
        topics="raw-logs",
        deserialization_schema=SimpleStringSchema(),
        properties=kafka_props
    )
    consumer.set_start_from_latest()
    
    # ── Kafka Producer ────────────────────────────────────────
    producer = FlinkKafkaProducer(
        topic="processed-features",
        serialization_schema=SimpleStringSchema(),
        producer_config={
            "bootstrap.servers": "kafka:29092",
            "transaction.timeout.ms": "60000"
        }
    )
    
    # ── Initialize parser (shared across workers) ─────────────
    parser = LogGuardParser()
    
    # ── Build the pipeline ────────────────────────────────────
    raw_stream = env.add_source(consumer)
    
    parsed_stream = (
        raw_stream
        .map(lambda raw: json.loads(raw))                     # Deserialize JSON
        .map(lambda event: {                                   # Parse + enrich
            **event,
            **parser.parse(event.get("raw_message", ""))
        })
        .filter(lambda e: e.get("host") is not None)          # Drop malformed events
        .assign_timestamps_and_watermarks(
            WatermarkStrategy
            .for_bounded_out_of_orderness(Time.seconds(5))    # Allow 5s late arrivals
            .with_timestamp_assigner(lambda e, _: e["timestamp"])
        )
    )
    
    # 60-second tumbling window per host
    feature_stream_60s = (
        parsed_stream
        .key_by(lambda e: e["host"])
        .window(TumblingEventTimeWindows.of(Time.seconds(60)))
        .apply(HostWindowAggregator())
    )
    
    # 300-second sliding window (slides every 60s) — for LSTM context
    feature_stream_300s = (
        parsed_stream
        .key_by(lambda e: e["host"])
        .window(SlidingEventTimeWindows.of(Time.seconds(300), Time.seconds(60)))
        .apply(HostWindowAggregator())
    )
    
    # Union both feature streams and publish
    feature_stream_60s.union(feature_stream_300s) \
        .map(lambda f: json.dumps(f)) \
        .add_sink(producer)
    
    logger.info("Starting LogGuard Flink job...")
    env.execute("LogGuard Log Processor")


if __name__ == "__main__":
    create_log_processor_job()
```

---

## 🧪 Testing Guide

### Unit Tests Kaise Chalao

```bash
# 1. Environment setup
cd flink_jobs/
pip install -r requirements.txt

# 2. Unit tests
pytest tests/ -v --cov=parsers --cov=feature_engineering

# 3. Integration test with local Kafka
docker-compose -f ../infrastructure/docker-compose.yml up -d
python log_processor.py  # Run locally

# 4. Send sample logs to test
python tests/send_sample_logs.py --count 1000 --anomaly-rate 0.05
```

### Sample Log Generator (Testing ke liye)

`tests/send_sample_logs.py`:
```python
import json
import random
import time
from datetime import datetime
from kafka import KafkaProducer

NORMAL_TEMPLATES = [
    "User {user} logged in successfully from {ip}",
    "GET /api/v1/{endpoint} 200 {time}ms",
    "Database connection pool: {n}/{total} connections active",
    "Cache hit for key {key}: {time}ms",
    "Health check passed: {service}",
]

ANOMALY_TEMPLATES = [
    "ERROR: Database connection refused after {n} retries",
    "FATAL: Out of memory - killing process {pid}",
    "WARN: Disk usage at {pct}% on {mount}",
    "ERROR: Authentication failed for user {user} from {ip}",
    "ERROR: Response timeout after {ms}ms for {endpoint}",
]

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode()
)

def send_logs(count: int = 1000, anomaly_rate: float = 0.05):
    for i in range(count):
        is_anomaly = random.random() < anomaly_rate
        template = random.choice(ANOMALY_TEMPLATES if is_anomaly else NORMAL_TEMPLATES)
        
        log_event = {
            "log_id": f"log_{i}_{int(time.time())}",
            "timestamp": int(datetime.utcnow().timestamp() * 1000),
            "host": random.choice(["web-01", "web-02", "db-01", "cache-01"]),
            "source": "test_generator",
            "severity": "ERROR" if is_anomaly else random.choice(["INFO", "INFO", "INFO", "WARN"]),
            "raw_message": template.format(
                user="testuser", ip="10.0.0.1", time=random.randint(10, 5000),
                endpoint="users", n=random.randint(1, 100), total=100,
                key="session_abc", service="api", pid=random.randint(1000, 9999),
                pct=random.randint(80, 99), mount="/data", ms=random.randint(100, 10000)
            ),
            "tenant_id": "tenant_001"
        }
        
        producer.send("raw-logs", value=log_event)
        time.sleep(0.01)  # 100 logs/second
        
    producer.flush()
    print(f"✅ Sent {count} logs ({int(count * anomaly_rate)} anomalies injected)")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--anomaly-rate", type=float, default=0.05)
    args = parser.parse_args()
    send_logs(args.count, args.anomaly_rate)
```

---

## ✅ Deliverables / Checkpoints

### Week 1 Checkpoint
- [ ] Docker Compose environment chalu ho (Kafka UI `localhost:8080` pe accessible)
- [ ] Teeno Kafka topics create ho jayein
- [ ] Avro schemas Schema Registry mein register ho jayein

### Week 2 Checkpoint
- [ ] Fluentbit local machine ke `/var/log/syslog` se logs padh le
- [ ] Logs Kafka ke `raw-logs` topic mein dikhe (Kafka UI se verify karo)
- [ ] Kubernetes DaemonSet YAML ready ho (actual deploy Phase 5 mein)

### Week 3 Checkpoint
- [ ] Drain3 parser 10 alag-alag log formats pe test ho
- [ ] Feature engineering unit tests 90%+ coverage ke saath pass ho

### Week 4 Checkpoint
- [ ] Flink job locally chal raha ho
- [ ] `processed-features` topic mein feature vectors aa rahe ho
- [ ] 1000 sample logs bhejo, sab process ho jayein bina error ke
- [ ] **ML Engineer ko handoff karo**: `processed-features` schema document share karo

---

## 🤝 Dependencies on Other Team Members

| Dependency | Tumhe kya chahiye | Kisse maango |
|---|---|---|
| Backend Engineer | TimescaleDB schema for feature storage | Person 3 |
| ML Engineer | Final feature vector format confirmation | Person 2 |
| ML Engineer | Template vocabulary size (top-K) | Person 2 |

---

## 📊 Performance Targets

| Metric | Target |
|---|---|
| Log ingestion throughput | ≥ 50,000 logs/second per broker |
| Flink processing latency (P99) | ≤ 500ms |
| Kafka consumer lag (normal) | ≤ 10,000 messages |
| Flink checkpoint time | ≤ 10 seconds |
| Zero data loss | Exactly-once semantics via checkpointing |

---

## 📚 Resources to Study

1. **Kafka Fundamentals**: https://kafka.apache.org/documentation/
2. **PyFlink Docs**: https://nightlies.apache.org/flink/flink-docs-master/api/python/
3. **Drain3 Paper + Repo**: https://github.com/logpai/Drain3
4. **Fluentbit Docs**: https://docs.fluentbit.io/
5. **Avro + Schema Registry**: https://docs.confluent.io/platform/current/schema-registry/

---

*LogGuard Data Engineer Task File — v1.0*  
*Coordinate karte raho ML Engineer (Person 2) se — tumhari output unka input hai.*
