#!/usr/bin/env bash
# W16 — verify public MCP endpoint auth + local health (no secrets printed).
set -euo pipefail

cd "$(dirname "$0")/.."
source /mnt/blockstorage/env/load.sh kb-gateway 2>/dev/null || source /mnt/blockstorage/env/load.sh global 2>/dev/null || true

BASE="${KB_GATEWAY_PUBLIC_URL:-https://kb-mcp.waytie.com}"
BASE="${BASE%/}"
URL="${BASE}/mcp"
PY="${PY:-/root/.venv-langchain-course/bin/python}"
KEYS="${KB_GATEWAY_API_KEYS_PATH:-/mnt/blockstorage/private/credentials/learning-kb-api-keys.txt}"

# Pick bearer token from keys file
TOKEN=$("$PY" -c "
from pathlib import Path
import os
p = Path('${KEYS}')
if os.environ.get('KB_GATEWAY_API_TOKEN'):
    print(os.environ['KB_GATEWAY_API_TOKEN']); raise SystemExit
if not p.is_file():
    raise SystemExit
lines = p.read_text().splitlines()
for i, line in enumerate(lines):
    s = line.strip()
    if s.startswith('#') and ('cole' in s.lower() or 'james' in s.lower()):
        for j in range(i+1, min(i+3, len(lines))):
            t = lines[j].strip()
            if t and not t.startswith('#'):
                print(t); raise SystemExit
for line in lines:
    t = line.strip()
    if t and not t.startswith('#'):
        print(t); raise SystemExit
" 2>/dev/null || true)
TOKEN="${KB_GATEWAY_API_TOKEN:-$TOKEN}"

echo "== remote MCP (no auth) =="
host="${URL#https://}"
host="${host%%/*}"
_resolve=()
if ! getent hosts "$host" >/dev/null 2>&1; then
  ip="$(dig +short "$host" @8.8.8.8 | head -1)"
  if [[ -n "$ip" ]]; then
    _resolve=(--resolve "${host}:443:${ip}")
  fi
fi
code_noauth=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "${_resolve[@]}" "$URL" || true)
echo "HTTP $code_noauth (expect 401)"
[[ "$code_noauth" == "401" ]] || { echo "FAIL: expected 401 without token"; exit 1; }

if [[ -z "$TOKEN" ]]; then
  echo "WARN: no token — skipping authenticated check"
else
  echo "== remote MCP (bearer) =="
  code_auth=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 \
    "${_resolve[@]}" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Accept: application/json, text/event-stream" \
    "$URL" || true)
  echo "HTTP $code_auth (expect 406 — MCP handshake)"
  [[ "$code_auth" == "406" || "$code_auth" == "200" ]] || {
    echo "FAIL: expected 406/200 with token, got $code_auth"
    exit 1
  }
fi

echo "== local health =="
"$PY" -c "
from kb_gateway.tools import health
import json, sys
h = health()
print(json.dumps(h, indent=2))
sys.exit(0 if h.get('ok') else 1)
"

echo "VERIFY_REMOTE_MCP OK"
