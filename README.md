# kb-gateway

HTTP MCP gateway for the **learning corpus** — Pinecone + Neo4j + agentic router — usable from anywhere.

**Production:** `https://kb-mcp.waytie.com/mcp` · **Repo home:** [`James-server/kb-gateway`](https://github.com/James-server/kb-gateway) (interim: [`okrealai/kb-gateway`](https://github.com/okrealai/kb-gateway))

| Audience | Start here |
|---|---|
| **Clients / collaborators** | [`docs/CLIENT-SETUP.md`](docs/CLIENT-SETUP.md) |
| **LLMs / agents** | [`AGENTS.md`](AGENTS.md) |
| **Humans** | This README |
| **Discovery** | [`llms.txt`](llms.txt) |
| **Gated project run dir** | [`../09_Projects/kb-gateway/run/STATE.md`](../09_Projects/kb-gateway/run/STATE.md) |

## What it does

Remote agents call MCP tools instead of holding Pinecone/Neo4j credentials:

| Tool | Purpose |
|---|---|
| `route_query` | **Default** — auto-pick graph vs vector vs both |
| `query_namespace` | Semantic RAG (`patterns`, `course-transcripts`, `langchain-docs`) |
| `graph_query` | Neo4j coverage / disputes / topic depth |
| `list_namespaces` | Corpus inventory |
| `health` | Dependency check |

## Quick start (server)

```bash
source /mnt/blockstorage/env/load.sh global
export KB_GATEWAY_API_TOKEN="<operator-issued>"
export KB_GATEWAY_PUBLIC_URL="https://kb-gateway.your-tailnet.example"

/root/.venv-langchain-course/bin/python -m kb_gateway --transport streamable-http
# MCP endpoint: http://127.0.0.1:8790/mcp
```

Local stdio (Cursor on server):

```bash
/root/.venv-langchain-course/bin/python -m kb_gateway --transport stdio --no-auth
```

## Client setup

See [`docs/client-setup.md`](docs/client-setup.md) for Cursor, Claude Desktop, and remote agent config.

## Architecture

[`ARCHITECTURE.md`](ARCHITECTURE.md) · [`RUNBOOK.md`](RUNBOOK.md)

## Related

- [`okrealai/langchain-course`](https://github.com/okrealai/langchain-course) — runtime deps (router, RAG, ingest)
- Gated routine: `/root/.claude/references/gated-execution-routine.md`
