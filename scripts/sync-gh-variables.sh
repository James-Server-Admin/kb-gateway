#!/usr/bin/env bash
# Sync MCP handoff variables to kb-gateway GitHub repos.
set -euo pipefail

KEYS="/mnt/blockstorage/private/credentials/learning-kb-api-keys.txt"
REPOS=(
  "KeyFlo-ai/kb-gateway"
  "James-Server-Admin/kb-gateway"
  "okrealai/kb-gateway"
)

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

COLE_SETUP_KEYFLO="Read docs/COLE-SETUP.md. Clone KeyFlo-ai/kb-gateway, run ./scripts/setup-mcp.sh, add config/mcp.json to Cursor MCP. URL: ${URL}"
COLE_SETUP_EXT="Read docs/CLIENT-SETUP.md. Clone James-Server-Admin/kb-gateway, run ./scripts/setup-mcp.sh. URL: ${URL}"

for REPO in "${REPOS[@]}"; do
  gh variable set KB_GATEWAY_MCP_URL --body "$URL" -R "$REPO"
  gh variable set KB_GATEWAY_MCP_TOKEN --body "$cole_token" -R "$REPO"
  gh variable set KB_GATEWAY_REPO --body "James-Server-Admin/kb-gateway" -R "$REPO"
  gh variable set CLIENT_SETUP --body "Read docs/CLIENT-SETUP.md. Run ./scripts/setup-mcp.sh then add config/mcp.json to Cursor MCP." -R "$REPO"
  gh variable set FRIEND_SETUP --body "Request access: https://kb-access.waytie.com — after approval follow docs/FRIEND-SETUP.md claim link." -R "$REPO"
  gh variable set ACCESS_REQUEST_URL --body "https://kb-access.waytie.com" -R "$REPO"
  if [[ "$REPO" == "KeyFlo-ai/kb-gateway" ]]; then
    gh variable set COLE_SETUP --body "$COLE_SETUP_KEYFLO" -R "$REPO"
  else
    gh variable set COLE_SETUP --body "$COLE_SETUP_EXT" -R "$REPO"
  fi
  echo "ok: synced variables to $REPO"
done
