"""FastMCP server — streamable HTTP + stdio transports."""

from __future__ import annotations

from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP

from .auth import StaticTokenVerifier
from .config import api_tokens, gateway_host, gateway_port, public_url
from . import tools as T

INSTRUCTIONS = """
James learning KB gateway. Exposes read-mostly access to the learning corpus:
Pinecone vector index `learning` + Neo4j knowledge graph + agentic router.

WHEN TO USE WHICH TOOL:
- query_all — default for broad research / "what do we know" / full-corpus synthesis
- route_query — use when graph-vs-vector routing is ambiguous or structural claims matter
- query_namespace — semantic/how-to when you know you need passages (patterns | course-transcripts | langchain-docs | research-papers)
- graph_query — coverage, topic depth, disputes (mode: stats | lane | topics | disputes)
- list_namespaces — discover corpora
- health — dependency check

Do NOT use for Keyflo product messaging (use keyflo_source_of_truth / Qdrant).
Do NOT claim "not covered" from one empty vector/router result; use full-corpus plus graph/tooling-health checks.
Read-only only — no writes.
""".strip()


def build_mcp(*, enable_auth: bool | None = None) -> FastMCP:
    tokens = api_tokens()
    use_auth = enable_auth if enable_auth is not None else bool(tokens)

    kwargs: dict = {
        "name": "keyflo-learning-kb",
        "instructions": INSTRUCTIONS,
        "host": gateway_host(),
        "port": gateway_port(),
        "streamable_http_path": "/mcp",
        "stateless_http": True,
    }

    if use_auth:
        if not tokens:
            raise RuntimeError("KB_GATEWAY_API_TOKEN or KB_GATEWAY_API_KEYS_PATH required when auth enabled")
        kwargs["auth"] = AuthSettings(
            issuer_url=public_url(),
            resource_server_url=public_url(),
            required_scopes=["learning:read"],
        )
        kwargs["token_verifier"] = StaticTokenVerifier(tokens)

    mcp = FastMCP(**kwargs)

    @mcp.tool()
    def route_query(question: str, k: int = 6, max_retries: int = 2) -> str:
        """Classify and answer using agentic router (graph | vector | both). Use when routing is ambiguous."""
        return T.dumps(T.route_query(question, k=k, max_retries=max_retries))

    @mcp.tool()
    def query_all(question: str, k: int = 8) -> str:
        """Full-corpus search: course-transcripts + patterns + research-papers (whitepapers)
        merged into one answer with namespace-tagged sources. Prefer this for general research /
        'what do we know about X' — it sees the WHOLE knowledge base, not just one namespace."""
        return T.dumps(T.query_all(question, k=k))

    @mcp.tool()
    def query_namespace(
        question: str,
        namespace: str = "patterns",
        k: int = 4,
        rerank: bool = False,
    ) -> str:
        """Semantic RAG against whitelisted namespace: patterns | course-transcripts | langchain-docs | research-papers."""
        return T.dumps(T.query_namespace(question, namespace=namespace, k=k, rerank=rerank))

    @mcp.tool()
    def graph_query(
        mode: str,
        lane: str = "",
        topics: str = "",
        limit: int = 12,
    ) -> str:
        """Read-only Neo4j. mode=stats|lane|topics|disputes. lane=copy|design|campaign|tracking for mode=lane."""
        return T.dumps(
            T.graph_query(mode, lane=lane or None, topics=topics or None, limit=limit)
        )

    @mcp.tool()
    def list_namespaces() -> str:
        """List Pinecone namespaces with vector counts and remote-allowed flag."""
        return T.dumps(T.list_namespaces())

    @mcp.tool()
    def health() -> str:
        """Health check: langchain-course + Neo4j reachability."""
        return T.dumps(T.health())

    return mcp
