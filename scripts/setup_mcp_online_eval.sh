#!/usr/bin/env bash
# Ensure LangSmith online evaluator scopes to kb-gateway MCP runs (W11).
# Idempotent: apply_rule.py create-or-updates Correctness rule from template.
set -euo pipefail

TEMPLATE_ROOT="/mnt/blockstorage/business/Keyflo_AI/08_Development/langsmith-platform-template"
PROJECT="${LANGSMITH_PROJECT:-LANGCHAIN-APP}"
ACCOUNT="${LANGSMITH_ACCOUNT:-learning}"

cd "$TEMPLATE_ROOT"
source /mnt/blockstorage/env/load.sh global 2>/dev/null || true
[[ "$ACCOUNT" == "keyflo" ]] && source /mnt/blockstorage/env/load.sh keyflo 2>/dev/null || true

echo "Applying correctness-mcp-surface → $PROJECT (account=$ACCOUNT)"
python3 scripts/apply_rule.py apply correctness-mcp-surface \
  --account "$ACCOUNT" \
  --project "$PROJECT" \
  --var "surface=mcp"

echo "Done. Verify: python3 scripts/apply_rule.py list --account $ACCOUNT --project $PROJECT"