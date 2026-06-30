# kb-gateway

HTTP MCP gateway for James's **learning corpus** — Pinecone + Neo4j + agentic router.

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
| `answer_learning_kb` | **Canonical structured answer** — stable wrapper over routing/full-corpus retrieval with sanitized evidence |
| `query_all` | **Default for broad research** — full-corpus search with namespace-tagged sources |
| `route_query` | Use when graph vs vector routing matters, or the question is structural/ambiguous |
| `query_namespace` | Semantic RAG (`patterns`, `course-transcripts`, `langchain-docs`, `research-papers`) |
| `graph_query` | Neo4j coverage / disputes / topic depth |
| `list_namespaces` | Corpus inventory |
| `health` | Dependency check |

Browser/mobile query page: `https://kb-access.waytie.com/query` uses the same issued MCP bearer token and returns the `answer_learning_kb` contract without exposing Pinecone/Neo4j credentials.

For new agents, call `answer_learning_kb` first. Use `intent="broad"` for full-corpus research, `intent="structural"` for coverage/dispute questions, and `namespace="research-papers"` when external paper evidence is the target. Responses include `retrieval_status`, `evidence.sources`, and `next_steps`; do not make a no-context claim from one empty result.

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
