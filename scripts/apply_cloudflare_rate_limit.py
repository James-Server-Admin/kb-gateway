#!/usr/bin/env python3
"""Apply kb-mcp Cloudflare rate limiting rules via Rulesets API (W17).

Requires token with Zone WAF Edit on keyflo.ai (not DNS-only).
Token: KEYFLO_CLOUDFLARE_WAF_API_TOKEN or keyflo-cloudflare-waf-api-token.txt

Docs: https://developers.cloudflare.com/waf/rate-limiting-rules/create-api/
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ZONE_ID = os.environ.get("KEYFLO_CLOUDFLARE_ZONE_ID", "de7eee6a85993f509d73eb927a833de3")
API = "https://api.cloudflare.com/client/v4"
PHASE = "http_ratelimit"

RULES = [
    {
        "description": "kb-gateway RL-mcp-burst",
        "expression": '(http.host eq "kb-mcp.keyflo.ai" and http.request.uri.path eq "/mcp")',
        "action": "block",
        "enabled": True,
        "ratelimit": {
            "characteristics": ["ip.src", "cf.colo.id"],
            "period": 60,
            "requests_per_period": 120,
            "mitigation_timeout": 60,
        },
    },
    {
        "description": "kb-gateway RL-mcp-path",
        "expression": '(http.host eq "kb-mcp.keyflo.ai" and http.request.uri.path contains "/mcp")',
        "action": "block",
        "enabled": True,
        "ratelimit": {
            "characteristics": ["ip.src", "cf.colo.id"],
            "period": 60,
            "requests_per_period": 200,
            "mitigation_timeout": 60,
        },
    },
]


def load_token() -> str:
    if t := os.environ.get("KEYFLO_CLOUDFLARE_WAF_API_TOKEN"):
        return t.strip()
    for path in (
        os.environ.get("KEYFLO_CLOUDFLARE_WAF_API_TOKEN_PATH"),
        "/mnt/blockstorage/private/credentials/keyflo-cloudflare-waf-api-token.txt",
        os.environ.get("KEYFLO_CLOUDFLARE_API_TOKEN_PATH"),
        "/mnt/blockstorage/private/credentials/keyflo-cloudflare-api-token.txt",
    ):
        if path and Path(path).is_file():
            return Path(path).read_text().strip()
    raise SystemExit(
        "No WAF token. Create keyflo-cloudflare-waf-api-token.txt with Zone WAF Edit "
        "or run: python3 /mnt/blockstorage/private/credentials/scripts/provision-keyflo-cloudflare-waf-token.py"
    )


def cf(method: str, path: str, token: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"{API}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode()
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            raise SystemExit(f"HTTP {exc.code}: {payload}") from exc


def get_entrypoint(token: str) -> dict | None:
    resp = cf("GET", f"/zones/{ZONE_ID}/rulesets/phases/{PHASE}/entrypoint", token)
    if resp.get("success"):
        return resp.get("result")
    errors = resp.get("errors") or []
    codes = {e.get("code") for e in errors}
    if 10000 in codes or 9109 in codes:
        raise SystemExit(
            "Authentication failed — token lacks Zone WAF Edit on keyflo.ai. "
            "Current keyflo-cloudflare-api-token.txt is DNS-only. "
            "Create a WAF token: provision-keyflo-cloudflare-waf-token.py "
            "or Cloudflare dashboard → Zone WAF Edit scoped to keyflo.ai."
        )
    if any("not found" in (e.get("message") or "").lower() for e in errors):
        return None
    raise SystemExit(f"GET entrypoint failed: {errors}")


def create_entrypoint(token: str) -> str:
    body = {
        "name": "zone",
        "kind": "zone",
        "phase": PHASE,
        "rules": RULES,
    }
    resp = cf("POST", f"/zones/{ZONE_ID}/rulesets", token, body)
    if not resp.get("success"):
        raise SystemExit(f"Create ruleset failed: {resp.get('errors')}")
    rid = resp["result"]["id"]
    print(f"Created {PHASE} entrypoint ruleset {rid} with {len(RULES)} rules")
    return rid


def ensure_rules(token: str, ruleset_id: str, existing: list[dict]) -> None:
    existing_desc = {r.get("description") for r in existing}
    for rule in RULES:
        if rule["description"] in existing_desc:
            print(f"  skip exists: {rule['description']}")
            continue
        resp = cf("POST", f"/zones/{ZONE_ID}/rulesets/{ruleset_id}/rules", token, rule)
        if not resp.get("success"):
            raise SystemExit(f"Add rule {rule['description']} failed: {resp.get('errors')}")
        print(f"  added: {rule['description']} (id={resp.get('result', {}).get('id')})")


def main() -> int:
    dry = "--dry-run" in sys.argv
    token = load_token()
    verify = cf("GET", "/user/tokens/verify", token)
    if not verify.get("success"):
        raise SystemExit(f"Token verify failed: {verify.get('errors')}")

    if dry:
        print(f"DRY-RUN: would apply {len(RULES)} rate limit rules on zone {ZONE_ID}")
        for r in RULES:
            print(f"  - {r['description']}: {r['ratelimit']['requests_per_period']}/60s")
        return 0

    entry = get_entrypoint(token)
    if entry is None:
        create_entrypoint(token)
    else:
        rid = entry["id"]
        rules = entry.get("rules") or []
        print(f"Entrypoint ruleset {rid} — {len(rules)} existing rule(s)")
        ensure_rules(token, rid, rules)

    # Re-fetch to confirm
    entry = get_entrypoint(token)
    names = [r.get("description") for r in (entry or {}).get("rules") or []]
    for rule in RULES:
        if rule["description"] not in names:
            raise SystemExit(f"Gate failed: missing rule {rule['description']}")
    print("Cloudflare rate limit rules OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
