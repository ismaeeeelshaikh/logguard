from pyflink.datastream import StreamExecutionEnvironment, RuntimeExecutionMode
from pyflink.datastream.connectors.kafka import FlinkKafkaConsumer, FlinkKafkaProducer
from pyflink.common import WatermarkStrategy, Time
from pyflink.common.time import Duration
from pyflink.common.watermark_strategy import TimestampAssigner
from pyflink.datastream.window import TumblingEventTimeWindows, SlidingEventTimeWindows, TumblingProcessingTimeWindows, SlidingProcessingTimeWindows
from pyflink.common.serialization import SimpleStringSchema
from parsers.drain3_parser import LogGuardParser
from feature_engineering.window_builder import HostWindowAggregator
import json
import os
import logging
from types import SimpleNamespace

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LogGuard-Flink")


class EventTimestampAssigner(TimestampAssigner):
    def extract_timestamp(self, value, record_timestamp) -> int:
        # Fallback to current record timestamp if event timestamp is missing/invalid.
        try:
            return int(value.get("timestamp", record_timestamp or 0))
        except Exception:
            return int(record_timestamp or 0)

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
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    # Load Kafka connector JAR for local PyFlink runtime if present.
    jar_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jars")
    connector_jar = os.path.join(jar_dir, "flink-connector-kafka-3.1.0-1.18.jar")
    kafka_clients_jar = os.path.join(jar_dir, "kafka-clients-3.4.0.jar")
    jars_to_load = []
    if os.path.exists(connector_jar):
        jars_to_load.append(f"file://{connector_jar}")
    if os.path.exists(kafka_clients_jar):
        jars_to_load.append(f"file://{kafka_clients_jar}")
    if jars_to_load:
        env.add_jars(*jars_to_load)
    
    # ── Enable checkpointing for fault tolerance ──────────────
    env.enable_checkpointing(30_000)  # Every 30 seconds
    checkpoint_config = env.get_checkpoint_config()
    checkpoint_uri = os.getenv(
        "LOGGUARD_CHECKPOINT_URI",
        "file:///tmp/logguard-flink-checkpoints",
    )
    # PyFlink API naming differs across versions, so keep it version-safe.
    if hasattr(checkpoint_config, "set_checkpoint_storage_uri"):
        checkpoint_config.set_checkpoint_storage_uri(checkpoint_uri)
    else:
        checkpoint_config.set_checkpoint_storage_dir(checkpoint_uri)
    checkpoint_config.set_min_pause_between_checkpoints(5_000)
    checkpoint_config.set_checkpoint_timeout(60_000)
    
    # ── Kafka Consumer ────────────────────────────────────────
    kafka_props = {
        "bootstrap.servers": bootstrap_servers,
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
            "bootstrap.servers": bootstrap_servers
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
            .for_bounded_out_of_orderness(Duration.of_seconds(5))
            .with_timestamp_assigner(EventTimestampAssigner())
        )
        .map(lambda e: SimpleNamespace(**e))
    )
    
    # 60-second tumbling window per host
    feature_stream_60s = (
        parsed_stream
        .key_by(lambda e: e.host)
        .window(TumblingProcessingTimeWindows.of(Time.seconds(60)))
        .apply(HostWindowAggregator())
    )
    
    # 300-second sliding window (slides every 60s) — for LSTM context
    feature_stream_300s = (
        parsed_stream
        .key_by(lambda e: e.host)
        .window(SlidingProcessingTimeWindows.of(Time.seconds(300), Time.seconds(60)))
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
