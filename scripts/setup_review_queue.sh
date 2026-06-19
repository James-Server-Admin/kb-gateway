#!/usr/bin/env bash
# Create kb-gateway-review annotation queue (W13).
set -euo pipefail

cd "$(dirname "$0")/.."
source /mnt/blockstorage/env/load.sh global 2>/dev/null || true

PY="${PY:-/root/.venv-langchain-course/bin/python}"

"$PY" <<'PY'
import sys
sys.path.insert(0, "/root/langchain-course")
import bootstrap
bootstrap.load_env()
from lib.langsmith_queues import get_or_create_queue

qid = get_or_create_queue(
    "kb-gateway-review",
    "Human review for borderline kb-gateway MCP answers (operator labels)",
)
print(f"queue_id={qid}")
print("Review in LangSmith → Annotation queues → kb-gateway-review")
PY
