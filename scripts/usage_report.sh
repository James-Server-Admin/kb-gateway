#!/usr/bin/env bash
# Usage report from audit log + LangSmith MCP metadata (W14).
set -euo pipefail

cd "$(dirname "$0")/.."
source /mnt/blockstorage/env/load.sh global 2>/dev/null || true

DAYS="${1:-7}"
AUDIT="${KB_GATEWAY_AUDIT_LOG:-logs/audit.jsonl}"
PY="${PY:-/root/.venv-langchain-course/bin/python}"

echo "# kb-gateway usage — last ${DAYS}d"
echo

if [[ -f "$AUDIT" ]]; then
  echo "## Audit log ($AUDIT)"
  "$PY" - <<PY
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

path = Path("$AUDIT")
cutoff = datetime.now(timezone.utc) - timedelta(days=int("$DAYS"))
by_client = Counter()
by_tool = Counter()
errors = 0
total = 0
latencies = []
for line in path.read_text().splitlines():
    if not line.strip():
        continue
    row = json.loads(line)
    ts = datetime.strptime(row["ts"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    if ts < cutoff:
        continue
    total += 1
    by_client[row.get("client", "?")] += 1
    by_tool[row.get("tool", "?")] += 1
    if row.get("status") != "ok":
        errors += 1
    if row.get("latency_ms"):
        latencies.append(row["latency_ms"])
print(f"- requests: {total}")
print(f"- errors: {errors}")
if latencies:
    latencies.sort()
    p95 = latencies[int(len(latencies) * 0.95) - 1] if len(latencies) > 1 else latencies[0]
    print(f"- latency p95 ms: {p95}")
print("- by client:")
for k, v in by_client.most_common():
    print(f"  - {k}: {v}")
print("- by tool:")
for k, v in by_tool.most_common():
    print(f"  - {k}: {v}")
PY
else
  echo "## Audit log: (none yet at $AUDIT)"
fi

echo
echo "## LangSmith (agentic_router with metadata.surface=mcp)"
"$PY" - <<PY
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, "/root/langchain-course")
import bootstrap
bootstrap.load_env()

from langsmith import Client

project = os.environ.get("LANGSMITH_PROJECT", "LANGCHAIN-APP")
since = datetime.now(timezone.utc) - timedelta(days=int("$DAYS"))
client = Client()
count = 0
for run in client.list_runs(
    project_name=project,
    start_time=since,
    filter='and(eq(name, "agentic_router"), eq(metadata_key, "surface"), eq(metadata_value, "mcp"))',
    limit=100,
):
    count += 1
print(f"- agentic_router runs (surface=mcp, cap 100 listed): {count}+")
print(f"- project: {project}")
print("- drill-down: LangSmith UI → filter metadata surface = mcp")
PY

echo
echo "For LLM cost (all LANGCHAIN-APP): cd /root/langchain-course && ./run scripts/cost_report.py --days $DAYS"
