# Client setup — wire remote agents to kb-gateway

kb-gateway runs on the **blockstorage server** 24/7 (`kb-gateway.service`). Neo4j and Pinecone keys stay server-side — clients only need a bearer token.

## Remote MCP (Tailscale — recommended)

Anyone on your **smithjsfamily@** tailnet (Cole, your Mac, laptop):

```json
{
  "mcpServers": {
    "keyflo-learning-kb": {
      "url": "http://100.122.28.113:8790/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_KB_GATEWAY_API_TOKEN"
      }
    }
  }
}
```

Traffic stays inside the tailnet. Keyflo learning KB only.

## Cursor / Claude on the server (stdio)

When the agent runs on the server itself:

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

## Cursor / Claude with SSH to server (stdio)

If you prefer stdio over HTTP from a local machine:

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

## Python (scripts on server)

```python
from kb_gateway.tools import route_query, query_namespace, graph_query

print(route_query("how do I structure a Meta lead gen campaign?")["answer"])
```

## Which tool to call

When unsure → **`route_query`**. See [`routing.md`](routing.md).

Read [`AGENTS.md`](../AGENTS.md) in repo — agents should load it for routing rules.
