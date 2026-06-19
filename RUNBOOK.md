# Runbook — kb-gateway

**Owner:** James Smith · **Backup:** Cole Wrightson  
**Last reviewed:** 2026-06-19 · **Production:** true (`https://kb-mcp.keyflo.ai/mcp`)

## 1. System overview

HTTP MCP gateway for learning corpus queries. Entry: `python -m kb_gateway --transport streamable-http`.

| Component | Location |
|---|---|
| Service | `kb-gateway.service` |
| Public URL | `https://kb-mcp.keyflo.ai/mcp` |
| Audit log | `logs/audit.jsonl` (JSONL, no secrets) |
| LangSmith | project `LANGCHAIN-APP`, metadata `surface=mcp` |

## 2. Owners & escalation

| Severity | Response | Action |
|---|---|---|
| P1 — gateway down | 4h | Restart systemd; check Neo4j + Pinecone |
| P2 — auth failures | 24h | Rotate token in `learning-kb-api-keys.txt`; re-sync GH vars |
| P3 — stale answers | best effort | LangSmith trace → graph rebuild / ingest drift |

## 3. SLAs & monitoring

| Metric | Target | Where |
|---|---|---|
| `health` ok | 99% when server up | smoke_test.sh |
| p95 route_query latency | < 45s | `scripts/usage_report.sh` |
| Auth reject rate | alert if spike | nginx/CF logs; audit log errors |

## 4. Observability (W9–W15)

### Daily / weekly operator checklist

1. **Usage:** `./scripts/usage_report.sh 7`
2. **LangSmith:** project `LANGCHAIN-APP` → filter `metadata.surface = mcp` → review errors
3. **Audit log:** `tail logs/audit.jsonl` — client, tool, latency, route (no question text)
4. **Routing regression:** `./scripts/eval_routes.sh` (fast)
5. **Answer smoke:** `./scripts/eval_quality.py` (slower; full LLM)
6. **Human review:** LangSmith → Annotation queues → `kb-gateway-review` (weekly sample)
7. **Cost:** `cd /root/langchain-course && ./run scripts/cost_report.py --days 7`

### Trace metadata (stamped on every tool call)

| Key | Example |
|---|---|
| `surface` | `mcp` |
| `client` | `cole`, `james`, `operator` |
| `tool` | `route_query` |
| `environment` | `production` |

Client derived from bearer token labels in `learning-kb-api-keys.txt` (`# cole-2026-06`).

### Online evaluator (MCP-scoped)

Setup once (or after LangSmith changes):

```bash
./scripts/setup_mcp_online_eval.sh
```

Filter: `and(eq(is_root, true), eq(metadata.surface, "mcp"))` · sampling ~10%.

### Annotation queue

```bash
./scripts/setup_review_queue.sh
```

Route borderline runs to `kb-gateway-review` via LangSmith online eval rule or manual enqueue.

### Audit log schema

```json
{"ts":"...","client":"cole","tool":"route_query","latency_ms":1200,"route":"vector","status":"ok","question_len":42,"question_hash":"..."}
```

Never contains bearer tokens or full question text.

## 5. Change process

Draft → `scripts/smoke_test.sh` → PR review → merge → `systemctl restart kb-gateway` → `./scripts/usage_report.sh 1`

## 6. MCP config

See `docs/COLE-SETUP.md` and `docs/client-setup.md`. Tokens in `learning-kb-api-keys.txt` + GH variables.

## 7. Incident response

| Failure | Signal | Fix |
|---|---|---|
| Neo4j down | health.checks.neo4j error | `docker start learning-kg-neo4j` |
| Pinecone auth | query_namespace ERROR | Check `LEARNING_PINECONE_API_KEY` in global.env |
| LC import fail | langchain_course check | Verify `/root/langchain-course` + venv |
| 401 on MCP | Bearer mismatch | Re-run `scripts/sync-cole-gh-variables.sh` |
| 421 on MCP | nginx Host header | See `deploy/nginx-kb-mcp.conf` |

## Smoke test

```bash
scripts/smoke_test.sh
./scripts/usage_report.sh 1
```
