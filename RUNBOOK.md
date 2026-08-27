# Runbook — kb-gateway

**Owner:** James Smith · **Backup:** Cole Wrightson  
**Last reviewed:** 2026-06-19 · **Production:** true (`https://kb-mcp.waytie.com/mcp`)

## 1. System overview

HTTP MCP gateway for learning corpus queries. Entry: `python -m kb_gateway --transport streamable-http`.

| Component | Location |
|---|---|
| Service | `kb-gateway.service` |
| Public URL | `https://kb-mcp.waytie.com/mcp` (legacy: `kb-mcp.keyflo.ai`) |
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

### Retrieval contract eval

Run before changing MCP/HTTP query defaults, namespace allowlists, wrapper logic,
or agent-facing docs:

```bash
./scripts/eval_retrieval_contract.py \
  --id answer-learning-kb-canonical-surface \
  --id answer-learning-kb-abstention-citation-fields \
  --id pinecone-best-practices-template \
  --id research-papers-direct-namespace \
  --id learning-kb-broad-default
# Full set when time allows:
./scripts/eval_retrieval_contract.py --all
```

Required behavior:

- New agent-facing clients use `answer_learning_kb` as the canonical structured
  access method over `query_all`, `route_query`, and `query_namespace`.
- `answer_learning_kb` responses include citation fields (`evidence.source_count`,
  `evidence.sources`, namespace/count fields when available) and abstention
  fields (`retrieval_status`, `next_steps`, and `errors` when present).
- Broad research / "what do we know" uses `query_all` or local `--all-namespaces`.
- Structural, absence, coverage, or dispute questions use `route_query`/graph.
- Pinecone DB best-practice/template prompts use targeted `pinecone-platform`
  plus `patterns` after the broad pass.
- External paper/whitepaper evidence can be targeted through
  `query_namespace(namespace="research-papers")` or
  `answer_learning_kb(namespace="research-papers")`.
- No "not covered" or "no context" conclusion may come from one empty
  namespace, vector, router, or tool-error result.

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

### Caller identity join

Gateway callers may attach a safe caller context through `SM_CALLER_*` env, the
CLI `--caller-context` option, or the `X-KB-Caller-Context` header. The gateway
adds optional fields to audit rows and LangSmith metadata:

```json
{"caller_team":"kb-usage","caller_seat":"WKR-kb-usage-executor","caller_role":"executor","caller_gate":"B5","caller_trace_id":"tr-20260827-B5","caller_identity_status":"known"}
```

Primary join: `audit.caller_trace_id == session_manager.trace_spans.trace_id`.
Secondary join: `(caller_team, caller_seat, caller_role, caller_gate, ts window)`.
Legacy rows without context remain valid and carry
`caller_identity_status="unknown"`. The `client` field remains the bearer-token
auth label; it is not overloaded with team or seat identity.

## 5. Automation & cron (Phase 6 W16)

### Scripts

| Script | Cadence | Purpose |
|---|---|---|
| `verify_remote_mcp.sh` | daily | HTTPS 401/406 + local health |
| `weekly_ops.sh` | weekly | usage + verify + eval_routes + split assess |
| `mint_golden_from_traces.py` | on demand / weekly | Refresh `eval/golden_ragas.jsonl` |
| `eval_ragas.sh` | weekly / pre-release | RAGAS baseline (cap 10 default) |
| `eval_retrieval_contract.py` | pre-release / after doc or wrapper changes | False no-context and retrieval-contract regression |
| `assess_langsmith_split.sh` | monthly | D-008 HOLD/SPLIT recommendation |
| `check_cole_handoff.sh` | weekly | audit `client=cole` |

### Install cron

```bash
sudo cp deploy/cron-kb-gateway.example /etc/cron.d/kb-gateway-ops
sudo chmod 644 /etc/cron.d/kb-gateway-ops
```

Logs: `logs/cron-verify.log`, `logs/cron-weekly.log`

### WAF (W17)

See `deploy/cloudflare-waf-rate-limit.md` · `./scripts/setup_cloudflare_rate_limit.sh`

## 6. Change process

Draft → `scripts/smoke_test.sh` → PR review → merge → `systemctl restart kb-gateway` → `./scripts/usage_report.sh 1`

### Deploy-time artifacts (repoint / re-clone the router source)

If `LANGCHAIN_COURSE_REPO` is ever repointed to a fresh clone (e.g. a dedicated deploy clone
instead of a shared dev checkout — see `kb-gateway#6` activation 2026-08-24), the fresh clone will
be missing gitignored, locally-derived cache files that `route_query`'s graph arm needs:
`graph/out/_cache/{lectures.npy,lectures_meta.json}`. These are DEPLOY-TIME ARTIFACTS, not
committed to git — carry them over (`cp -n` from the prior working tree) or rebuild them before
the first live `route_query` call, otherwise the router degrades loudly (`routing.degradation`
stamped, `errors.route_query` populated) rather than silently, per the F1 fix — a correct but
avoidable degradation. Confirmed live during the `kb-gateway#12`/`kb-core#227` activation: first
post-restart `route_query` call caught the missing cache and degraded loudly exactly as designed;
copying the cache from the prior tree and re-probing cleared it (route `both`, zero degradation).

## 7. MCP config

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
