#!/usr/bin/env bash
set -Eeuo pipefail

PACKAGE_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)"
SOURCE_ROOT="$(CDPATH= cd -- "$PACKAGE_ROOT/.." && pwd -P)"

export PYTHONDONTWRITEBYTECODE=1
python3 "$PACKAGE_ROOT/qa/release_check.py"

echo "PASS: RiqatonyDesk static/source release QA"
