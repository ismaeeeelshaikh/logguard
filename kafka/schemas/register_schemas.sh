#!/bin/bash
set -e

SCHEMA_REGISTRY="http://localhost:8081"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Registering raw_log schema..."
RAW_SCHEMA=$(python3 -c "import json, pathlib; print(json.dumps(pathlib.Path('${SCRIPT_DIR}/raw_log.avsc').read_text()))")
curl -s -X POST \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  --data "{\"schema\": $RAW_SCHEMA}" \
  "$SCHEMA_REGISTRY/subjects/raw-logs-value/versions"
echo ""

echo "Registering processed_features schema..."
PROCESSED_SCHEMA=$(python3 -c "import json, pathlib; print(json.dumps(pathlib.Path('${SCRIPT_DIR}/processed_features.avsc').read_text()))")
curl -s -X POST \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  --data "{\"schema\": $PROCESSED_SCHEMA}" \
  "$SCHEMA_REGISTRY/subjects/processed-features-value/versions"
echo ""

echo "Verifying registered schemas..."
curl -s "$SCHEMA_REGISTRY/subjects"
echo ""
echo "✅ Schema registration complete!"
