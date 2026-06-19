#!/usr/bin/env bash
# Sync MCP handoff variables to kb-gateway GitHub repo.
set -euo pipefail

REPO="${KB_GATEWAY_GH_REPO:-James-Server-Admin/kb-gateway}"
KEYS="/mnt/blockstorage/private/credentials/learning-kb-api-keys.txt"

source /mnt/blockstorage/env/load.sh kb-gateway 2>/dev/null || true
BASE="${KB_GATEWAY_PUBLIC_URL:-https://kb-mcp.waytie.com}"
BASE="${BASE%/}"
URL="${KB_GATEWAY_MCP_URL:-${BASE}/mcp}"

cole_token="$(python3 - <<'PY'
from pathlib import Path
p = Path("/mnt/blockstorage/private/credentials/learning-kb-api-keys.txt")
lines = [l.strip() for l in p.read_text().splitlines()]
for i, line in enumerate(lines):
    if line.startswith("# cole") and i + 1 < len(lines):
        nxt = lines[i + 1]
        if nxt and not nxt.startswith("#"):
            print(nxt)
            break
PY
)"

if [[ -z "$cole_token" ]]; then
  echo "error: no cole token in $KEYS" >&2
  exit 1
fi

unset GH_TOKEN GITHUB_TOKEN
gh auth switch --user okrealai >/dev/null 2>&1 || true

gh variable set KB_GATEWAY_MCP_URL --body "$URL" -R "$REPO"
gh variable set KB_GATEWAY_MCP_TOKEN --body "$cole_token" -R "$REPO"
gh variable set CLIENT_SETUP --body "Read docs/CLIENT-SETUP.md. Run ./scripts/setup-mcp.sh then add config/mcp.json to Cursor MCP." -R "$REPO"
gh variable set COLE_SETUP --body "Read docs/CLIENT-SETUP.md (alias). Run ./scripts/setup-mcp.sh." -R "$REPO"

echo "ok: synced variables to $REPO"
