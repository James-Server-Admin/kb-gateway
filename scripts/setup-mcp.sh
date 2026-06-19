#!/usr/bin/env bash
# Create config/mcp.json from GitHub repo variables.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="${KB_GATEWAY_GH_REPO:-James-server/kb-gateway}"
OUT="${ROOT}/config/mcp.json"

if ! command -v gh >/dev/null; then
  echo "error: install GitHub CLI (gh) and run: gh auth login" >&2
  exit 1
fi

fetch_var() {
  gh api "repos/${1}/actions/variables/${2}" --jq .value 2>/dev/null || true
}

URL="$(fetch_var "$REPO" KB_GATEWAY_MCP_URL)"
TOKEN="$(fetch_var "$REPO" KB_GATEWAY_MCP_TOKEN)"
if [[ -z "$URL" || -z "$TOKEN" ]] && [[ "$REPO" != "okrealai/kb-gateway" ]]; then
  REPO="okrealai/kb-gateway"
  URL="$(fetch_var "$REPO" KB_GATEWAY_MCP_URL)"
  TOKEN="$(fetch_var "$REPO" KB_GATEWAY_MCP_TOKEN)"
fi

if [[ -z "$URL" || -z "$TOKEN" ]]; then
  echo "error: KB_GATEWAY_MCP_URL or KB_GATEWAY_MCP_TOKEN not set on $REPO" >&2
  echo "  Try: KB_GATEWAY_GH_REPO=okrealai/kb-gateway ./scripts/setup-mcp.sh" >&2
  echo "  Operator: run scripts/sync-gh-variables.sh on the server" >&2
  exit 1
fi

mkdir -p "${ROOT}/config"
python3 - <<PY
import json
from pathlib import Path
cfg = {
    "mcpServers": {
        "learning-kb": {
            "url": "${URL}",
            "headers": {"Authorization": "Bearer ${TOKEN}"},
        }
    }
}
Path("${OUT}").write_text(json.dumps(cfg, indent=2) + "\n")
# Back-compat alias for Cole
cole = {
    "mcpServers": {
        "keyflo-learning-kb": {
            "url": "${URL}",
            "headers": {"Authorization": "Bearer ${TOKEN}"},
        }
    }
}
Path("${ROOT}/config/cole-mcp.json").write_text(json.dumps(cole, indent=2) + "\n")
PY
chmod 600 "$OUT" "${ROOT}/config/cole-mcp.json"
echo "Wrote $OUT (and config/cole-mcp.json for backward compat)"
echo "Merge into Cursor MCP settings or paste the mcpServers block."
