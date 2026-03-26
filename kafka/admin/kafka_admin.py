from confluent_kafka.admin import AdminClient, NewTopic
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LogGuard-KafkaAdmin")

KAFKA_BROKER = "localhost:9092"

TOPICS = [
    NewTopic("raw-logs", num_partitions=6, replication_factor=1, config={
        "retention.ms": "86400000",
        "compression.type": "lz4"
    }),
    NewTopic("processed-features", num_partitions=6, replication_factor=1, config={
        "retention.ms": "86400000"
    }),
    NewTopic("anomaly-events", num_partitions=3, replication_factor=1, config={
        "retention.ms": "604800000"
    }),
]


def create_topics():
    """Create all required Kafka topics."""
    admin = AdminClient({"bootstrap.servers": KAFKA_BROKER})
    existing = admin.list_topics(timeout=10).topics.keys()

    to_create = [t for t in TOPICS if t.topic not in existing]
    if not to_create:
        logger.info("All topics already exist.")
        return

    futures = admin.create_topics(to_create)
    for topic, future in futures.items():
        try:
            future.result()
            logger.info(f"✅ Created topic: {topic}")
        except Exception as e:
            logger.error(f"❌ Failed to create topic {topic}: {e}")


def list_topics():
    """List all Kafka topics."""
    admin = AdminClient({"bootstrap.servers": KAFKA_BROKER})
    metadata = admin.list_topics(timeout=10)
    for topic in sorted(metadata.topics.keys()):
        logger.info(f"  📌 {topic}")


def delete_topics(topic_names: list):
    """Delete specified Kafka topics."""
    admin = AdminClient({"bootstrap.servers": KAFKA_BROKER})
    futures = admin.delete_topics(topic_names)
    for topic, future in futures.items():
        try:
            future.result()
            logger.info(f"🗑️ Deleted topic: {topic}")
        except Exception as e:
            logger.error(f"❌ Failed to delete topic {topic}: {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LogGuard Kafka Admin Utility")
    parser.add_argument("action", choices=["create", "list", "delete"])
    parser.add_argument("--topics", nargs="+", help="Topic names (for delete)")
    args = parser.parse_args()

    if args.action == "create":
        create_topics()
    elif args.action == "list":
        list_topics()
    elif args.action == "delete":
        if args.topics:
            delete_topics(args.topics)
        else:
            logger.error("Specify --topics for delete action")
