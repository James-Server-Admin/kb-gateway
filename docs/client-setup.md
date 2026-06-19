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
    "keyflo-learning-kb": {
      "command": "/root/.venv-langchain-course/bin/python",
      "args": ["-m", "kb_gateway", "--transport", "stdio", "--no-auth"],
      "cwd": "/mnt/blockstorage/business/Keyflo_AI/08_Development/kb-gateway",
      "env": {}
    }
  }
}
```

## Which tool to call

When unsure → **`route_query`**. See [`routing.md`](routing.md). Read [`AGENTS.md`](../AGENTS.md).
