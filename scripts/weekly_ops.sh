#!/usr/bin/env bash
# W16 — weekly operator automation chain.
set -euo pipefail

cd "$(dirname "$0")/.."
source /srv/org/env/load.sh global 2>/dev/null || true

DAYS="${1:-7}"
echo "# kb-gateway weekly ops — last ${DAYS}d"
echo

./scripts/usage_report.sh "$DAYS"
echo
./scripts/verify_remote_mcp.sh
echo
./scripts/eval_routes.sh
echo
./scripts/assess_langsmith_split.sh 2>/dev/null || echo "(assess_langsmith_split: skip if not installed yet)"
echo
echo "WEEKLY_OPS OK"
