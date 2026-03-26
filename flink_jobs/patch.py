from pathlib import Path
p = Path("log_processor.py")
s = p.read_text()
s = s.replace('producer_config={\n            "bootstrap.servers": bootstrap_servers,\n            "transaction.timeout.ms": "60000"\n        }', 'producer_config={\n            "bootstrap.servers": bootstrap_servers\n        }')
p.write_text(s)
