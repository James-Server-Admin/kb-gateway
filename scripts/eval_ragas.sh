#!/usr/bin/env bash
# W19 — RAGAS batch eval wrapper.
set -euo pipefail

cd "$(dirname "$0")/.."
source /srv/org/env/load.sh global 2>/dev/null || true

PY="${PY:-/root/.venv-langchain-course/bin/python}"
CAP="${1:-10}"

"$PY" scripts/eval_ragas.py "$CAP"
