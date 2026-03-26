#!/usr/bin/env python3
import json
import urllib.request
import os

SCHEMA_REGISTRY = "http://localhost:8081"
SCHEMA_DIR = os.path.dirname(os.path.abspath(__file__))

schemas = {
    "raw-logs-value": os.path.join(SCHEMA_DIR, "raw_log.avsc"),
    "processed-features-value": os.path.join(SCHEMA_DIR, "processed_features.avsc"),
}

for subject, filepath in schemas.items():
    print(f"Registering schema: {subject}")
    with open(filepath, "r") as f:
        schema_str = f.read()

    payload = json.dumps({"schema": schema_str}).encode("utf-8")
    url = f"{SCHEMA_REGISTRY}/subjects/{subject}/versions"
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/vnd.schemaregistry.v1+json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode())
            print(f"  ✅ Registered with id={result.get('id')}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  ❌ Error: {e.code} - {body}")

# Verify
print("\nVerifying registered subjects...")
req = urllib.request.Request(f"{SCHEMA_REGISTRY}/subjects")
with urllib.request.urlopen(req) as resp:
    subjects = json.loads(resp.read().decode())
    for s in subjects:
        print(f"  📌 {s}")

print("\n✅ Schema registration complete!")
