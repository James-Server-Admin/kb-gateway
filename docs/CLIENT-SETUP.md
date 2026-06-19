# Client setup — kb-gateway MCP

**Repo:** `James-server/kb-gateway` (mirror: `okrealai/kb-gateway` until transfer)  
**Purpose:** Query the learning corpus via MCP (`route_query`, `query_namespace`, `graph_query`) from Cursor or any MCP client.

**No Tailscale required** — use the public HTTPS endpoint on James's domain.

---

## Quick start (5 minutes)

1. **Clone the repo**
   ```bash
   git clone git@github.com:James-server/kb-gateway.git
   cd kb-gateway
   gh auth login   # once, with your GitHub account
   ```

   If `James-server/kb-gateway` is not live yet, use `okrealai/kb-gateway` and set `KB_GATEWAY_GH_REPO=okrealai/kb-gateway`.

2. **Pull MCP config from GitHub variables**
   ```bash
   chmod +x scripts/setup-mcp.sh
   ./scripts/setup-mcp.sh
   cat config/mcp.json
   ```

3. **Add to Cursor** → Settings → MCP → paste the `learning-kb` block from `config/mcp.json`.

4. **Verify** — ask your agent: *"Use learning-kb route_query: what is PAS copy structure?"*

---

## MCP endpoint

| Item | Value |
|------|-------|
| URL | `https://kb-mcp.waytie.com/mcp` |
| Auth | `Authorization: Bearer <token>` (from GitHub variable `KB_GATEWAY_MCP_TOKEN` or operator-issued) |
| Tools | `route_query`, `query_namespace`, `graph_query`, `list_namespaces`, `health` |

Manual test:
```bash
export KB_GATEWAY_MCP_TOKEN="<your-token>"
curl -s -o /dev/null -w "%{http_code}\n" \
  -H "Authorization: Bearer $KB_GATEWAY_MCP_TOKEN" \
  https://kb-mcp.waytie.com/mcp
```
Expect `406` (MCP handshake), not `401`.

---

## Getting access

James issues bearer tokens (one per user) in `learning-kb-api-keys.txt` on the server. Each token maps to a `client=` label in the audit log.

For self-serve setup via GitHub variables, you need **read access** to the repo so `./scripts/setup-mcp.sh` can pull `KB_GATEWAY_MCP_URL` and your personal `KB_GATEWAY_MCP_TOKEN`.

---

## Alternative: HTTP query API (no MCP)

If you only need Q&A without MCP tools:

| Item | Value |
|------|-------|
| Repo | `KeyFlo-ai/knowledge-base` |
| URL | `https://kb-api.keyflo.ai/v1/query` |

Same corpus, simpler for scripts.

---

## Optional: Tailscale (private path)

James's tailnet also exposes the gateway at `http://100.122.28.113:8790/mcp` for tailnet members only (same bearer token).

---

## GitHub variables (repo admin sets these)

| Variable | Purpose |
|----------|---------|
| `KB_GATEWAY_MCP_URL` | `https://kb-mcp.waytie.com/mcp` |
| `KB_GATEWAY_MCP_TOKEN` | Per-user bearer token |
| `CLIENT_SETUP` | Pointer to this file |

---

## Which tool to use

| Question type | Tool |
|---------------|------|
| Not sure | `route_query` |
| How-to / passages | `query_namespace` |
| Coverage / disputes | `graph_query` |

Read [`AGENTS.md`](../AGENTS.md) for full routing rules.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `401` | Re-run `setup-mcp.sh`; token may have rotated |
| Cursor can't connect | Check URL ends with `/mcp`; restart Cursor |
| `502` / timeout | Ping James — `systemctl status kb-gateway` on server |
| Tailscale URL fails | Not on tailnet — use HTTPS URL instead |
