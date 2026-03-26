#!/bin/bash
set -e

KAFKA_BROKER="localhost:9092"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/infrastructure/docker-compose.yml"

run_kafka_topics() {
  if command -v kafka-topics.sh >/dev/null 2>&1; then
    kafka-topics.sh "$@"
    return
  fi

  if command -v docker >/dev/null 2>&1; then
    docker compose -f "${COMPOSE_FILE}" exec -T kafka kafka-topics "$@"
    return
  fi

  echo "Error: kafka-topics.sh not found and Docker is unavailable."
  echo "Install Kafka CLI or enable Docker Desktop WSL integration first."
  exit 1
}

echo "Creating Kafka topics..."

# Raw logs topic - high throughput, 6 partitions
run_kafka_topics --create --if-not-exists \
  --bootstrap-server $KAFKA_BROKER \
  --topic raw-logs \
  --partitions 6 \
  --replication-factor 1 \
  --config retention.ms=86400000 \
  --config compression.type=lz4

# Processed features topic - ML input
run_kafka_topics --create --if-not-exists \
  --bootstrap-server $KAFKA_BROKER \
  --topic processed-features \
  --partitions 6 \
  --replication-factor 1 \
  --config retention.ms=86400000

# Anomaly events topic - alert triggers
run_kafka_topics --create --if-not-exists \
  --bootstrap-server $KAFKA_BROKER \
  --topic anomaly-events \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=604800000

echo "✅ All topics created successfully!"
run_kafka_topics --list --bootstrap-server $KAFKA_BROKER
