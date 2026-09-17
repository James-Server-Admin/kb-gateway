#!/usr/bin/env bash
# W20 — LangSmith project split assessment (D-008 triggers). HOLD unless T1 or T2 >= 25%.
set -euo pipefail

cd "$(dirname "$0")/.."
source /srv/org/env/load.sh global 2>/dev/null || true

PY="${PY:-/root/.venv-langchain-course/bin/python}"
DAYS="${1:-7}"

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

def count_runs(filter_str=None):
    n = 0
    kwargs = dict(project_name=project, start_time=since, is_root=True, limit=100)
    if filter_str:
        kwargs["filter"] = filter_str
    for _ in client.list_runs(**kwargs):
        n += 1
        if n >= 100:
            break
    return n

total = count_runs()
mcp = count_runs('and(eq(is_root, true), eq(metadata_key, "surface"), eq(metadata_value, "mcp"))')
pct = (100.0 * mcp / total) if total else 0.0

print(f"# LangSmith split assessment (D-008) — last {int('$DAYS')}d")
print(f"project: {project}")
print(f"root runs (cap 100): {total}")
print(f"MCP surface=mcp runs (cap 100): {mcp}")
print(f"MCP share: {pct:.1f}%")
print()

t1 = pct >= 25.0
# T2 cost — simplified: defer to cost_report; flag as manual if unavailable
print("T1 (MCP runs >= 25%):", "FIRE" if t1 else "hold")
print("T2 (MCP cost >= 25%): run: cd /root/langchain-course && ./run scripts/cost_report.py --days $DAYS")
print()
if t1:
    print("RECOMMENDATION: monitor — need 2 consecutive weekly FIRE before SPLIT")
else:
    print("RECOMMENDATION: HOLD — keep LANGCHAIN-APP + metadata.surface=mcp")
PY
