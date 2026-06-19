#!/usr/bin/env bash
# Ensure LangSmith online evaluator scopes to kb-gateway MCP runs (W11).
# Updates existing Correctness rule filter if present; else prints manual steps.
set -euo pipefail

LC="/root/langchain-course"
PROJECT="${LANGSMITH_PROJECT:-LANGCHAIN-APP}"
PROD_CHAINS='["retrieval_chain_without_lcel", "retrieval_chain_with_lcel", "namespace_rag_query", "course_rag_agent", "course_rag_target", "reflection_agent"]'
FILTER="and(eq(is_root, true), or(and(eq(metadata.environment, \"production\"), in(name, ${PROD_CHAINS})), eq(metadata.surface, \"mcp\")))"

cd "$LC"
source /mnt/blockstorage/env/load.sh global 2>/dev/null || true

if ! ./run scripts/manage_online_evaluator_rule.py list --project "$PROJECT" 2>/dev/null | grep -q Correctness; then
  echo "No Correctness rule in $PROJECT — create in LangSmith UI with filter:"
  echo "  $FILTER"
  echo "  sampling_rate: 0.1"
  exit 0
fi

echo "Updating Correctness rule filter for MCP surface..."
./run scripts/manage_online_evaluator_rule.py update \
  --project "$PROJECT" \
  --name Correctness \
  --sampling-rate 0.1 \
  --filter "$FILTER"

echo "Done. Verify in LangSmith → $PROJECT → Evaluators"
