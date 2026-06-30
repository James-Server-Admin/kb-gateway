# Client setup — wire remote agents to kb-gateway

**Canonical guide:** [`docs/CLIENT-SETUP.md`](CLIENT-SETUP.md)

## Remote MCP (HTTPS)

```json
{
  "mcpServers": {
    "learning-kb": {
      "url": "https://kb-mcp.waytie.com/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_KB_GATEWAY_MCP_TOKEN"
      }
    }
  }
}
```

Clone `James-Server-Admin/kb-gateway`, run `./scripts/setup-mcp.sh` — pulls token from GitHub variables.

## Tailscale (optional private path)

On tailnet `smithjsfamily@gmail.com`: `http://100.122.28.113:8790/mcp` with same bearer token.

## Cursor on the server (stdio)

```json
{
  "mcpServers": {
    "learning-kb": {
      "command": "/root/.venv-langchain-course/bin/python",
      "args": ["-m", "kb_gateway", "--transport", "stdio", "--no-auth"],
      "cwd": "/mnt/blockstorage/business/Keyflo_AI/08_Development/kb-gateway",
      "env": {}
    }
  }
}
```

## Which tool to call

Default agent Q&A → **`answer_learning_kb`**. Broad research / "what do we know about X" → **`answer_learning_kb(intent="broad")`** or direct **`query_all`**. When graph-vs-vector routing or structural claims matter → **`answer_learning_kb(intent="structural")`** or direct **`route_query`**. Paper evidence → **`answer_learning_kb(namespace="research-papers")`**.

Responses expose `retrieval_status`, `evidence.sources`, and `next_steps`; cite sources and follow next steps before saying there is no context. See [`routing.md`](routing.md). Read [`AGENTS.md`](../AGENTS.md).
