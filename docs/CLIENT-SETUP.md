# Client setup — kb-gateway MCP

**Repo:** `James-Server-Admin/kb-gateway`  
**Purpose:** Query James's learning corpus via MCP (`answer_learning_kb`, `query_all`, `route_query`, `query_namespace`, `graph_query`) from Cursor or any MCP client.

**No Tailscale required** — use the public HTTPS endpoint on James's domain.

---

## Quick start (5 minutes)

1. **Clone the repo**
   ```bash
   git clone git@github.com:James-Server-Admin/kb-gateway.git
   cd kb-gateway
   gh auth login   # once, with your GitHub account
   ```

2. **Pull MCP config from GitHub variables**
   ```bash
   chmod +x scripts/setup-mcp.sh
   ./scripts/setup-mcp.sh
   cat config/mcp.json
   ```

3. **Add to Cursor** → Settings → MCP → paste the `learning-kb` block from `config/mcp.json`.

4. **Verify** — ask your agent: *"Use learning-kb answer_learning_kb: what is PAS copy structure?"*

---

## MCP endpoint

| Item | Value |
|------|-------|
| URL | `https://kb-mcp.waytie.com/mcp` |
| Auth | `Authorization: Bearer <token>` (from GitHub variable `KB_GATEWAY_MCP_TOKEN` or operator-issued) |
| Tools | `answer_learning_kb`, `query_all`, `route_query`, `query_namespace`, `graph_query`, `list_namespaces`, `health` |

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

**Friends (token from James, not GitHub variables):** see [`FRIEND-SETUP.md`](FRIEND-SETUP.md).

---

## Alternative: HTTP query API (no MCP)

If you only need Q&A without MCP tools:

| Item | Value |
|------|-------|
| Repo | `James-Server-Admin/keyflo-learning-kb` |
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
| Stable answer contract / default agent Q&A | `answer_learning_kb` |
| Broad research / "what do we know" | `query_all` |
| Not sure graph vs vector | `route_query` |
| How-to / passages | `query_namespace` |
| Coverage / disputes | `graph_query` |

Use `answer_learning_kb(intent="broad")` for full-corpus retrieval, `answer_learning_kb(intent="structural")` for coverage/dispute questions, and `answer_learning_kb(namespace="research-papers")` when paper/whitepaper evidence is the target. Cite `evidence.sources`; when `retrieval_status` is not `ok`, follow `next_steps` before making an absence claim.

Read [`AGENTS.md`](../AGENTS.md) for full routing rules.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `401` | Re-run `setup-mcp.sh`; token may have rotated |
| Cursor can't connect | Check URL ends with `/mcp`; restart Cursor |
| `502` / timeout | Ping James — `systemctl status kb-gateway` on server |
| Tailscale URL fails | Not on tailnet — use HTTPS URL instead |
