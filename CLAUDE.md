# kb-gateway — operating manual

> AGENTS.md is a symlink to this file.

## Identity

HTTP MCP gateway exposing the **learning KB** (Pinecone + Neo4j + agentic router) to remote agents. GitHub: `KeyFlo-ai/kb-gateway`.

## Gated execution routine

- **Routine:** gated-execution-routine v1.2 → `/root/.claude/references/gated-execution-routine.md`
- **Run dir:** `/mnt/blockstorage/business/Keyflo_AI/09_Projects/kb-gateway/run/`
- **Resume:** `run/STATE.md` → `run/04-HARDENING-PLAN.md` → `run/CONTINUE.md`
- **Phase:** 4–5 shipped · CAPTURE done · **Phase 6 W16–W22 NEXT** (hardening & automation)

## Parent context

- Business: Keyflo → `/mnt/blockstorage/business/Keyflo_AI/CLAUDE.md`
- Runtime deps: `/root/langchain-course` (okrealai/langchain-course)
- Env: `source /mnt/blockstorage/env/load.sh global`

## Run (operator)

```bash
cd /mnt/blockstorage/business/Keyflo_AI/08_Development/kb-gateway
source /mnt/blockstorage/env/load.sh global
export KB_GATEWAY_API_TOKEN="<from secrets registry>"
/root/.venv-langchain-course/bin/python -m kb_gateway --transport streamable-http
```

Smoke: `scripts/smoke_test.sh`

## Hard rules

- READ ONLY at gateway layer — no ingest, no Neo4j writes
- Remote clients get MCP tools only — never Pinecone/Neo4j keys
- Namespace whitelist enforced in `kb_gateway/config.py`
- Default remote tool: `query_all` for broad research; `route_query` when routing is ambiguous or structural claims matter
- **Endpoint specs:** [`docs/ENDPOINT-CATALOG.md`](docs/ENDPOINT-CATALOG.md) — tools, HTTP parity, corpus inventory, routing tree

## Owners

- Primary: James Smith
- Backup: Cole (after token issued)
