# Endpoint catalog — learning KB

**Audience:** Coding agents (Cursor, Claude, CI, custom apps)  
**Last verified:** 2026-06-19 (live Pinecone + Neo4j stats)  
**Canonical doc:** this file · **Routing:** [`routing.md`](routing.md) · **MCP setup:** [`COLE-SETUP.md`](COLE-SETUP.md)

Use this catalog to pick the **right surface and tool** without guessing. Default broad research / "what do we know about X": **`query_all`**. Use **`route_query`** when graph-vs-vector routing is uncertain or structural claims matter.

---

## 1. Corpus inventory (what exists)

### Pinecone index `learning`

| Namespace | Vectors | Remote MCP | Doc type | Use for |
|-----------|---------|------------|----------|---------|
| `course-transcripts` | 92,420 | ✅ | transcript | Course lectures across business, tech, finance, creative, ops, engineering, marketing, and more (116 courses) |
| `langchain-docs` | 1,150 | ✅ | docs | LangChain / LangGraph / LangSmith official docs |
| `patterns` | 372 | ✅ | pattern | Proven process patterns (`patterns/*.md`) |
| `research-papers` | varies | ✅ | paper | External research papers / whitepapers |
| `course-code` | 24 | ❌ | code | langchain-course scripts/notebooks (operator only) |
| `orchestrations` | 151 | ❌ | orchestration | Codex/grok run syntheses (operator only) |
| `own-notes` | 18 | ❌ | notes | James operator notes (operator only) |

- **Embedding:** `text-embedding-3-large` · 3072-dim (immutable)  
- **Remote whitelist:** `patterns`, `course-transcripts`, `langchain-docs`, `research-papers` (`kb_gateway/config.py`)

### Neo4j graph `learning-kg-neo4j`

| Metric | Count |
|--------|------:|
| Courses | 116 |
| Lectures | 18,255 |
| Topics | 462 |
| Disciplines | 106 |
| Claims | 290 |

**Topology:** `Course → Lecture → COVERS → Topic` · `Claim —CONTRADICTS→ Claim` · `Discipline` taxonomy

**Graph answers that vectors cannot:** coverage counts, cross-course disputes, topic depth/breadth, lane-scoped inventory.

---

## 2. Access surfaces (pick one)

| Surface | Base URL | Auth | Best for |
|---------|----------|------|----------|
| **MCP** (recommended for agents) | `https://kb-mcp.waytie.com/mcp` | `Authorization: Bearer <token>` | Cursor / multi-tool agents — full tool set |
| **HTTP API** | `https://kb-api.keyflo.ai` | Same bearer token | Scripts, single-shot Q&A, no MCP client |
| **SSH + CLI** (server only) | `root@192.241.169.31` | SSH + `load.sh` | Debugging, multi-surface graph CLI, direct Pinecone |

**Not this corpus:** Keyflo product SoT → Qdrant `keyflo_source_of_truth` (separate skill).

---

## 3. Agent routing (30-second decision)

```
Question?
├─ Broad research / "what do we know?" ──────► query_all
├─ Unsure vector vs graph? ──────────────────► route_query
├─ How-to / passages / "explain X"? ─────────► query_namespace (pick namespace)
│   ├─ course material ──► course-transcripts
│   ├─ process/SOP ──────► patterns
│   └─ LangChain stack ──► langchain-docs
├─ Which courses cover X? / depth / lanes? ──► graph_query (mode=topics|lane|stats)
├─ Do courses disagree? ─────────────────────► graph_query (mode=disputes) or route_query
└─ What can I query? ────────────────────────► list_namespaces or graph_query (mode=stats)
```

| Question shape | Route | MCP tool | HTTP equivalent |
|----------------|-------|----------|-----------------|
| Open-ended / full-corpus research | vector merge | `query_all` | `POST /v1/query` default |
| Routing ambiguity / structural synthesis | auto | `route_query` | `POST /v1/query` with `all_namespaces=false` |
| Semantic how-to | vector | `query_namespace` | — (use MCP or SSH `query_db.py`) |
| Coverage / inventory | graph | `graph_query` | — |
| Disputes | graph | `graph_query` mode=disputes | `route_query` (classifier picks graph) |

---

## 4. Endpoint specs

Each entry follows the **endpoint card** template in [§7](#7-endpoint-card-template).

---

### EP-MCP-001 · `route_query`

| Field | Value |
|-------|-------|
| **Surface** | MCP @ `https://kb-mcp.waytie.com/mcp` |
| **Auth** | Bearer · scope `learning:read` |
| **When to use** | Routing ambiguity. Classifier picks `vector` \| `graph` \| `both`. Disputes, coverage, structural synthesis. |
| **When NOT** | You already know you only need one namespace and no graph facts. Latency-sensitive hot path where graph is unnecessary. |
| **Request** | `question: str` (3–4000 chars) · `k: int` default 6 (1–12) · `max_retries: int` default 2 (0–3) |
| **Response** | JSON string: `{ answer, route, route_reason, graph_context?, source_documents[], structured_response, retries }` |
| **Limits** | ~45s p95 · rate limit nginx 120 req/min/IP on `/mcp` |
| **Example** | `route_query("which courses cover StoryBrand?", k=6)` |
| **Composes with** | Read `route` + `graph_context` before citing structural claims |

---

### EP-MCP-001A · `query_all`

| Field | Value |
|-------|-------|
| **Surface** | MCP @ `https://kb-mcp.waytie.com/mcp` |
| **Auth** | Bearer · scope `learning:read` |
| **When to use** | Default for broad research, "what do we know about X", full-corpus synthesis, and avoiding false no-context from one namespace/router pass. |
| **When NOT** | You need graph coverage/dispute facts or a known single namespace. Pair with `graph_query` for absence/coverage claims. |
| **Request** | `question: str` (3–4000 chars) · `k: int` default 8 |
| **Response** | JSON string: `{ answer, namespaces, per_namespace_counts, source_documents[], structured_response }` |
| **Example** | `query_all("Pinecone database best practices and templates for querying the learning KB", k=8)` |
| **Composes with** | `route_query` or `graph_query` for structural, disagreement, or absence claims |

---

### EP-MCP-002 · `query_namespace`

| Field | Value |
|-------|-------|
| **Surface** | MCP |
| **When to use** | Passage retrieval when namespace is known. |
| **When NOT** | Coverage counts, disputes, "which courses" — use `graph_query` or `route_query`. |
| **Request** | `question: str` · `namespace: str` default `patterns` · `k: int` default 4 · `rerank: bool` default false |
| **Namespace enum** | `patterns` \| `course-transcripts` \| `langchain-docs` \| `research-papers` |
| **Response** | `{ answer, namespace, source_documents[], structured_response? }` |
| **Example** | `query_namespace("Facebook ads campaign structure", namespace="course-transcripts", k=8)` |

---

### EP-MCP-003 · `graph_query`

| Field | Value |
|-------|-------|
| **Surface** | MCP |
| **When to use** | Structural / inventory queries without full router LLM overhead. |
| **Request** | `mode: str` · optional `lane` · optional `topics` · `limit: int` default 12 |

**Modes:**

| mode | Required params | Returns |
|------|-----------------|---------|
| `stats` | — | `{ courses, lectures, topics, disciplines, claims }` |
| `lane` | `lane`: `copy` \| `design` \| `campaign` \| `tracking` | Top topics by lecture count for lane keywords |
| `topics` | `topics`: space-separated keywords (≥3 chars each) | Topic rows: `{ domain, topic, lectures, courses }` |
| `disputes` | — | Cross-course `Claim` contradictions (marketing/sales, confidence ≥0.6) |

**Lane keywords (built-in):**

| lane | Keywords (sample) |
|------|-------------------|
| `copy` | copy, headline, storytelling, persuasion, email, writing |
| `design` | design, creative, image, visual, scroll, contrast, canva, photoshop |
| `campaign` | campaign, ad set, budget, audience, targeting, objective, facebook |
| `tracking` | conversion, tracking, pixel, remarketing, attribution, landing page |

**Example:** `graph_query(mode="lane", lane="campaign", limit=5)`

**Gap vs SSH CLI:** Server `query_graph.py --topics` searches four surfaces (topic, narrow, discipline, lecture). MCP `graph_query` topics mode searches **Topic labels only**. For product-specific terms (e.g. "LangSmith tracing"), prefer `route_query` or SSH CLI.

---

### EP-MCP-004 · `list_namespaces`

| Field | Value |
|-------|-------|
| **Surface** | MCP |
| **When to use** | Discover corpora, vector counts, remote-allowed flag. |
| **Request** | (none) |
| **Response** | `[{ namespace, vector_count, allowed_for_remote, default_doc_type, description }]` |

---

### EP-MCP-005 · `health`

| Field | Value |
|-------|-------|
| **Surface** | MCP |
| **When to use** | Preflight before batch queries. |
| **Response** | `{ ok: bool, checks: { langchain_course, neo4j } }` |
| **Example** | Expect `ok: true`, `neo4j.topics: 462` |

---

### EP-HTTP-001 · `GET /health`

| Field | Value |
|-------|-------|
| **Surface** | HTTP @ `https://kb-api.keyflo.ai` |
| **Auth** | None |
| **Response** | `{ "status": "ok", "service": "learning-kb-api" }` |

---

### EP-HTTP-002 · `POST /v1/query`

| Field | Value |
|-------|-------|
| **Surface** | HTTP |
| **Auth** | Bearer (same token as MCP) |
| **When to use** | Single-shot Q&A from curl/scripts. Defaults to full-corpus `query_all`; set `all_namespaces=false` for router behavior. |
| **Request body** | `{ "question": string, "k": 6, "max_retries": 2, "all_namespaces": true }` |
| **Response** | Default: `{ answer, namespaces, per_namespace_counts, source_documents[] }`; router mode: `{ answer, route, route_reason, graph_context, source_documents[], retries }` |
| **Limits** | 30 req/hour/token · `k` 1–12 · question max 4000 chars |
| **Example** | See [`public-api.md`](https://github.com/KeyFlo-ai/knowledge-base/blob/main/docs/public-api.md) |

---

## 5. Response field glossary

| Field | Meaning | Trust for structure? |
|-------|---------|----------------------|
| `answer` | LLM synthesis from retrieved context | Cite sources; don't treat as authoritative alone |
| `route` | `vector` \| `graph` \| `both` | Which stores were used |
| `route_reason` | Classifier rationale | Debug routing |
| `graph_context` | Neo4j facts prepended to answer | **Yes** for coverage/disputes |
| `source_documents` | Chunk / file IDs | Always cite in agent output |
| `structured_response` | Full RAG response object (MCP namespace queries) | Optional parse |
| `lectures` / `courses` | Graph topic counts | **Yes** — graph-grounded |
| `confidence` (disputes) | CONTRADICTS edge weight | Higher = stronger disagreement signal |

---

## 6. Full-capacity agent playbook

1. **Start:** `health` → `list_namespaces` if corpus unfamiliar.  
2. **Plan:** Use [§3 routing](#3-agent-routing-30-second-decision) — don't default every question to `course-transcripts` or a single router pass.  
3. **Execute:**  
   - Broad research / "what do we know" → `query_all`  
   - Ambiguous graph-vs-vector or structural synthesis → `route_query`  
   - LangChain implementation → `query_namespace(..., namespace="langchain-docs")`  
   - Process/SOP from patterns → `query_namespace(..., namespace="patterns")`  
   - Marketing depth inventory → `graph_query(mode="lane", lane="copy"|"design"|"campaign"|"tracking")`  
   - Topic coverage → `graph_query(mode="topics", topics="...")`  
4. **Synthesize:** Merge `graph_context` (structure) + `answer` (passages). Cite `source_documents`.  
5. **Disputes:** If answer touches contested technique, call `graph_query(mode="disputes")` or ensure `route` was `graph`/`both`.  
6. **Boundaries:** Never query blocked namespaces. Never assert Keyflo product facts from this corpus.

---

## 7. Endpoint card template

Copy this block for each new endpoint (MCP tool, HTTP route, or CLI command).

```markdown
### EP-{SURFACE}-{NNN} · `{name}`

| Field | Value |
|-------|-------|
| **Surface** | MCP \| HTTP \| CLI |
| **URL / transport** | e.g. `https://kb-mcp.waytie.com/mcp` or `POST /v1/foo` |
| **Auth** | None \| Bearer \| SSH |
| **When to use** | One sentence — question types, latency profile |
| **When NOT** | Anti-patterns, wrong corpus, blocked namespaces |
| **Request** | Params with types, defaults, enums, max lengths |
| **Response** | Top-level keys + nested shapes |
| **Limits** | Rate, timeout, k bounds |
| **Example** | Minimal call that returns useful output |
| **Composes with** | Other endpoints to call before/after |
| **Failure modes** | 401, 429, 502, empty results — and fixes |
| **Gap notes** | Parity differences vs other surfaces (optional) |
```

**Checklist before marking an endpoint documented:**

- [ ] Enum values exhaustive  
- [ ] Example question → example response keys  
- [ ] "When NOT" prevents common misuse  
- [ ] Linked from `AGENTS.md` / `llms.txt`  
- [ ] Live stats or smoke command recorded  

---

## 8. Related docs

| Doc | Location |
|-----|----------|
| Pinecone namespaces | `KeyFlo-ai/knowledge-base` → `docs/pinecone.md` |
| Neo4j graph | `docs/neo4j.md` |
| Agentic router | `docs/agentic-router.md` |
| Routing decision table | `docs/routing.md` |
| HTTP API ops | `docs/public-api.md` |
| MCP client wiring | `docs/COLE-SETUP.md` |

---

## 9. Changelog

| Date | Change |
|------|--------|
| 2026-06-19 | Initial catalog from live index stats + MCP/HTTP inventory |
