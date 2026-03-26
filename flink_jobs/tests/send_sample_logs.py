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
