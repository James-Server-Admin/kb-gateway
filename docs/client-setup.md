# Client setup — wire remote agents to kb-gateway

## Cursor (remote / cloud agent)

Add MCP server in Cursor settings (Streamable HTTP):

**After Tailscale Serve is enabled** (see [`deployment.md`](deployment.md)), use the HTTPS URL Tailscale assigns to `vetriq-server`:

```json
{
  "mcpServers": {
    "keyflo-learning-kb": {
      "url": "https://YOUR-TAILSCALE-OR-TUNNEL-HOST/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_KB_GATEWAY_API_TOKEN"
      }
    }
  }
}
```

Read [`AGENTS.md`](../AGENTS.md) in repo — Cursor agents should load it for routing rules.

## Cursor / Claude on the server (stdio)

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

Env loads from `bootstrap.load_env()` via langchain-course — no keys in config JSON.

## Claude Desktop (Mac, via SSH)

Desktop runs locally; MCP runs on server over SSH wrapper:

```json
{
  "mcpServers": {
    "keyflo-learning-kb": {
      "command": "ssh",
      "args": [
        "blockstorage-server",
        "/root/.venv-langchain-course/bin/python",
        "-m", "kb_gateway",
        "--transport", "stdio",
        "--no-auth"
      ]
    }
  }
}
```

## Python (scripts)

```python
from kb_gateway.tools import route_query, query_namespace, graph_query

print(route_query("how do I structure a Meta lead gen campaign?")["answer"])
```

Requires server env + `LANGCHAIN_COURSE_REPO`.

## Which tool to call

When unsure → **`route_query`**. See [`routing.md`](routing.md).
