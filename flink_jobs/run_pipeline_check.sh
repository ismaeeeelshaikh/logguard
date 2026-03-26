#!/usr/bin/env bash
set -e
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
echo "Stopping existing jobs..."
pkill -f "python3 -u log_processor.py" || true
sleep 2

echo "Starting Flink job..."
cd /home/krisss/logguard/flink_jobs
source .venv310/bin/activate
nohup bash run_local_flink.sh > /tmp/logguard_flink.log 2>&1 &
sleep 10
tail -n 20 /tmp/logguard_flink.log

echo "Sending data..."
python tests/send_sample_logs.py --count 100 --anomaly-rate 0.05
sleep 5
python -c 'import json, time; from kafka import KafkaProducer; p = KafkaProducer(bootstrap_servers="localhost:9092", value_serializer=lambda v: json.dumps(v).encode("utf-8")); p.send("raw-logs", {"log_id": "future", "timestamp": int((time.time() + 600) * 1000), "host": "web-01", "source": "test", "severity": "INFO", "raw_message": "push watermark", "tenant_id": "tenant_001"}); p.flush(); print("Sent aggressive future timestamp messages")'

echo "Waiting for pipeline flush..."
sleep 15
tail -n 30 /tmp/logguard_flink.log

echo "Checking output..."
cd /home/krisss/logguard
docker compose -f infrastructure/docker-compose.yml exec -T kafka kafka-console-consumer --bootstrap-server kafka:29092 --topic processed-features --from-beginning --timeout-ms 5000 | head -n 5
