#!/usr/bin/env bash
# W17 — apply Cloudflare rate limits via API (needs WAF-scoped token).
set -euo pipefail

cd "$(dirname "$0")/.."
source /mnt/blockstorage/env/load.sh keyflo 2>/dev/null || true

PY="${PY:-/root/.venv-langchain-course/bin/python}"
WAF_TOKEN_PATH="/mnt/blockstorage/private/credentials/keyflo-cloudflare-waf-api-token.txt"

if [[ "${1:-}" == "--dry-run" ]]; then
  exec "$PY" scripts/apply_cloudflare_rate_limit.py --dry-run
fi

if [[ ! -f "$WAF_TOKEN_PATH" ]]; then
  echo "No WAF token at $WAF_TOKEN_PATH"
  echo
  echo "The DNS token (keyflo-cloudflare-api-token.txt) cannot manage WAF rules."
  echo "Option A — one-time in Cloudflare dashboard (cole@keyflo.ai):"
  echo "  Profile → API Tokens → Create → Zone → WAF → Edit, zone=keyflo.ai"
  echo "  Save to: $WAF_TOKEN_PATH"
  echo
  echo "Option B — provision script (needs Global API Key or parent token with API Tokens Edit):"
  echo "  KEYFLO_CLOUDFLARE_GLOBAL_API_KEY=... python3 \\"
  echo "    /mnt/blockstorage/private/credentials/scripts/provision-keyflo-cloudflare-waf-token.py"
  echo
  echo "Option C — nginx rate limit already on origin (deploy/nginx-kb-mcp-rate-limit.conf)"
  exit 1
fi

export KEYFLO_CLOUDFLARE_WAF_API_TOKEN_PATH="$WAF_TOKEN_PATH"
"$PY" scripts/apply_cloudflare_rate_limit.py
./scripts/verify_remote_mcp.sh
