#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# Resolve JAVA_HOME from installed Java if not set or invalid.
if [[ -z "${JAVA_HOME:-}" || ! -x "${JAVA_HOME}/bin/java" ]]; then
	if command -v java >/dev/null 2>&1; then
		java_bin="$(readlink -f "$(command -v java)")"
		export JAVA_HOME="$(dirname "$(dirname "$java_bin")")"
	fi
fi

if [[ -z "${JAVA_HOME:-}" || ! -x "${JAVA_HOME}/bin/java" ]]; then
	echo "ERROR: Java not found. Install OpenJDK 11 and set JAVA_HOME." >&2
	echo "Example: sudo apt install -y openjdk-11-jdk" >&2
	exit 1
fi

export PATH="$JAVA_HOME/bin:$PATH"

source .venv310/bin/activate
python3 -u log_processor.py
