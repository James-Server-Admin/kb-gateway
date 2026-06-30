# Cole setup — kb-gateway MCP (KeyFlo org)

**Start here if you have KeyFlo GitHub access.**

| Item | Value |
|------|-------|
| **This repo** | `KeyFlo-ai/kb-gateway` |
| **MCP URL** | `https://kb-mcp.waytie.com/mcp` |
| **HTTP API** (no MCP) | `KeyFlo-ai/knowledge-base` → `https://kb-api.keyflo.ai` |

---

## Quick start (Cursor — 5 min)

1. **Clone**
   ```bash
   git clone git@github.com:KeyFlo-ai/kb-gateway.git
   cd kb-gateway
   gh auth login   # once, as cwrightson
   ```

2. **Pull MCP config from GitHub variables**
   ```bash
   chmod +x scripts/setup-mcp.sh
   ./scripts/setup-mcp.sh
   cat config/mcp.json
   ```

3. **Cursor** → Settings → MCP → paste the `learning-kb` block from `config/mcp.json`.

4. **Verify** — ask your agent: *"Use learning-kb query_all: what is PAS copy structure?"*

Expect MCP handshake (not `401`). Same bearer token works for `kb-api.keyflo.ai` HTTP queries.

---

## GitHub variables (pre-configured on this repo)

**Settings → Secrets and variables → Actions → Variables**

| Variable | Purpose |
|----------|---------|
| `COLE_SETUP` | Pointer to this file |
| `KB_GATEWAY_MCP_URL` | `https://kb-mcp.waytie.com/mcp` |
| `KB_GATEWAY_MCP_TOKEN` | Your bearer token |
| `KB_GATEWAY_REPO` | `James-Server-Admin/kb-gateway` (external mirror) |

Manual test:
```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  -H "Authorization: Bearer $KB_GATEWAY_MCP_TOKEN" \
  https://kb-mcp.waytie.com/mcp
```
Expect `406` or `200`, not `401`.

---

## MCP tools

| Tool | When |
|------|------|
| `query_all` | **Default for broad research** / "what do we know about X" |
| `route_query` | Auto-pick vector vs graph when routing or structure matters |
| `query_namespace` | How-to / passage lookup in a known namespace |
| `graph_query` | Coverage, disputes, topic depth |
| `list_namespaces` | Corpus inventory |
| `health` | Dependency check |

Full routing rules: [`AGENTS.md`](../AGENTS.md)

---

## Alternative paths

| Path | Repo | Use when |
|------|------|----------|
| **MCP (recommended)** | `KeyFlo-ai/kb-gateway` (here) | Cursor / Claude Desktop / any MCP client |
| HTTP API | `KeyFlo-ai/knowledge-base` | Scripts, simple Q&A without MCP |
| External clone | `James-Server-Admin/kb-gateway` | Outside KeyFlo org (same MCP endpoint) |

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `401` | Re-run `./scripts/setup-mcp.sh`; token may have rotated |
| Variables missing | Confirm repo access; ask James to run `scripts/sync-gh-variables.sh` |
| Cursor can't connect | URL must end with `/mcp`; restart Cursor |
| `502` / timeout | Ping James — `systemctl status kb-gateway` on server |
