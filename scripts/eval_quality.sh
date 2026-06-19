#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source /mnt/blockstorage/env/load.sh global 2>/dev/null || true
exec /root/.venv-langchain-course/bin/python scripts/eval_quality.py "$@"
