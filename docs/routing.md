# Which database when — routing guide

See also [`AGENTS.md`](../AGENTS.md) · corpus pattern: `langchain-course/patterns/proven/kg-vector-routing.md`

| Question | Route | MCP tool |
|---|---|---|
| Broad research / "what do we know?" | vector merge | `query_all` |
| Not sure graph vs vector | auto | `route_query` |
| How do I X? / semantic how-to | vector | `query_namespace` (course-transcripts or patterns) |
| Which courses cover X? | graph | `graph_query` mode=topics |
| Coverage by marketing lane | graph | `graph_query` mode=lane |
| Do courses disagree? | graph | `graph_query` mode=disputes |
| Structural synthesis | both | `route_query` |

**Why:** vectors find similar passages; graph surfaces coverage, depth, and `CONTRADICTS` edges vectors cannot see. Vector-only on structural questions hallucinates ~25–33% (router backtest).

## Marketing lanes (graph_query mode=lane)

| lane | Use for |
|---|---|
| copy | headlines, persuasion, email |
| design | creative, visual, contrast |
| campaign | structure, audience, targeting |
| tracking | pixel, attribution |

## Allowed Pinecone namespaces (remote)

`patterns` · `course-transcripts` · `langchain-docs` · `research-papers`

Never expose `own-notes` / `orchestrations` via this gateway.
