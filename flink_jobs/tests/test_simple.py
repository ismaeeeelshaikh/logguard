from kafka import KafkaConsumer, KafkaProducer
import json
p = KafkaProducer(bootstrap_servers='localhost:9092', value_serializer=lambda v: json.dumps(v).encode('utf-8'))
p.send('processed-features', {'test': 'data'})
p.flush()
c = KafkaConsumer('processed-features', bootstrap_servers='localhost:9092', value_deserializer=lambda m: json.loads(m.decode('utf-8')), auto_offset_reset='earliest', consumer_timeout_ms=5000)
for msg in c:
    print(msg.value)
    break
