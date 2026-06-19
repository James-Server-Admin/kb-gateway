# kb-gateway

HTTP MCP gateway for the **learning corpus** — Pinecone + Neo4j + agentic router.

## Cole — start here (KeyFlo org)

**MCP endpoint:** `https://kb-mcp.waytie.com/mcp`

```bash
git clone git@github.com:KeyFlo-ai/kb-gateway.git
cd kb-gateway
gh auth login
./scripts/setup-mcp.sh          # pulls KB_GATEWAY_MCP_* from GitHub variables
# paste config/mcp.json → Cursor Settings → MCP
```

→ Full guide: [`docs/COLE-SETUP.md`](docs/COLE-SETUP.md) · GitHub variable `COLE_SETUP` points here.

**HTTP API (no MCP):** [`KeyFlo-ai/knowledge-base`](https://github.com/KeyFlo-ai/knowledge-base) · `https://kb-api.keyflo.ai`

---

| Audience | Start here |
|---|---|
| **Cole / KeyFlo collaborators** | [`docs/COLE-SETUP.md`](docs/COLE-SETUP.md) |
| **Friends (external)** | [`docs/FRIEND-SETUP.md`](docs/FRIEND-SETUP.md) · Request: **https://kb-access.waytie.com** |
| **External collaborators** | [`James-Server-Admin/kb-gateway`](https://github.com/James-Server-Admin/kb-gateway) |
| **LLMs / agents** | [`AGENTS.md`](AGENTS.md) |
| **Discovery** | [`llms.txt`](llms.txt) |

**Production:** `https://kb-mcp.waytie.com/mcp`

## What it does

Remote agents call MCP tools instead of holding Pinecone/Neo4j credentials:

| Tool | Purpose |
|---|---|
| `route_query` | **Default** — auto-pick graph vs vector vs both |
| `query_namespace` | Semantic RAG (`patterns`, `course-transcripts`, `langchain-docs`) |
| `graph_query` | Neo4j coverage / disputes / topic depth |
| `list_namespaces` | Corpus inventory |
| `health` | Dependency check |

## Quick start (server operator)

```bash
source /mnt/blockstorage/env/load.sh kb-gateway
/root/.venv-langchain-course/bin/python -m kb_gateway --transport streamable-http
# binds 127.0.0.1:8790 — public via kb-mcp.waytie.com nginx
```

## Architecture

[`ARCHITECTURE.md`](ARCHITECTURE.md) · [`RUNBOOK.md`](RUNBOOK.md) · [`docs/client-setup.md`](docs/client-setup.md)

## Related

- [`KeyFlo-ai/knowledge-base`](https://github.com/KeyFlo-ai/knowledge-base) — parallel HTTP API
- [`okrealai/langchain-course`](https://github.com/okrealai/langchain-course) — router runtime deps
