#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# Local user-space Java install (no sudo required)
export JAVA_HOME="$HOME/tools/java/jdk-11.0.30+7"
export PATH="$JAVA_HOME/bin:$PATH"

source .venv310/bin/activate
python3 -u log_processor.py
