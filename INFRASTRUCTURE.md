# Infrastructure — kb-gateway

Credentials via `/srv/org/env/load.sh global` — **no values in this repo**.

| Resource | Location | Notes |
|---|---|---|
| Pinecone index | `learning` | Server-side only |
| Neo4j | `bolt://localhost:7689` | `learning-kg-neo4j` container |
| Langchain-course | `/root/langchain-course` | Router + RAG runtime |
| Python venv | `/root/.venv-langchain-course` | MCP + LC deps |
| Gateway bind | `127.0.0.1:8790` | Override via env |
| MCP path | `/mcp` | Streamable HTTP |
| Auth token | `KB_GATEWAY_API_TOKEN` | Register in SECRETS-REGISTRY |
| Public URL | `KB_GATEWAY_PUBLIC_URL` | For MCP OAuth metadata |

## Env vars

```
KB_GATEWAY_API_TOKEN=
KB_GATEWAY_HOST=127.0.0.1
KB_GATEWAY_PORT=8790
KB_GATEWAY_PUBLIC_URL=https://...
LANGCHAIN_COURSE_REPO=/root/langchain-course
LEARNING_KG_NEO4J_URI=
LEARNING_KG_NEO4J_USER=
LEARNING_KG_NEO4J_PASSWORD=
LEARNING_PINECONE_API_KEY=
OPENAI_API_KEY=
```

## GitHub

- Repo: `KeyFlo-ai/kb-gateway` (https://github.com/KeyFlo-ai/kb-gateway)
- Repo: `kb-gateway`

## Related services

- `docker ps | grep learning-kg-neo4j` — graph must be up
- Pinecone cloud — no local container
