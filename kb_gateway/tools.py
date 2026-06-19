"""Tool implementations — delegate to langchain-course runtime (read-mostly)."""

from __future__ import annotations

import json
from typing import Any

from .config import ALLOWED_NAMESPACES
from . import graph as kg
from .lc_bootstrap import ensure_langchain_course
from .observability import instrument_tool


@instrument_tool("route_query")
def route_query(question: str, k: int = 6, max_retries: int = 2) -> dict[str, Any]:
    """Agentic router: auto-pick graph vs vector vs both."""
    ensure_langchain_course()
    from runtime.agentic_router import route_query as _rq

    return _rq(question, k=k, max_retries=max_retries)


@instrument_tool("query_namespace")
def query_namespace(
    question: str,
    namespace: str = "patterns",
    k: int = 4,
    rerank: bool = False,
    use_grader: bool = False,
) -> dict[str, Any]:
    """RAG query against whitelisted Pinecone namespace."""
    if namespace not in ALLOWED_NAMESPACES:
        raise ValueError(
            f"namespace {namespace!r} not allowed. Use one of: {sorted(ALLOWED_NAMESPACES)}"
        )
    ensure_langchain_course()
    import config
    from runtime.query import query

    if namespace not in config.NAMESPACES:
        raise ValueError(f"namespace {namespace!r} not registered in langchain-course config")
    result = query(
        question=question,
        namespace=namespace,
        k=k,
        rerank=rerank,
        use_grader=use_grader,
    )
    return {
        "answer": result.get("answer"),
        "namespace": namespace,
        "source_documents": result.get("source_documents"),
        "structured_response": result.get("structured_response"),
    }


@instrument_tool("list_namespaces")
def list_namespaces() -> list[dict[str, Any]]:
    """Registered namespaces with live vector counts (collaborator subset highlighted)."""
    ensure_langchain_course()
    import config
    from pinecone import Pinecone
    import os

    idx = Pinecone(api_key=os.environ["PINECONE_API_KEY"]).Index(config.index_name())
    stats = idx.describe_index_stats()
    counts = {ns: info.get("vector_count", 0) for ns, info in (stats.get("namespaces") or {}).items()}
    out = []
    for ns, meta in sorted(config.NAMESPACES.items()):
        out.append({
            "namespace": ns,
            "vector_count": counts.get(ns, 0),
            "allowed_for_remote": ns in ALLOWED_NAMESPACES,
            "default_doc_type": meta.get("default_doc_type"),
            "description": meta.get("desc"),
        })
    return out


@instrument_tool("graph_query")
def graph_query(
    mode: str,
    *,
    lane: str | None = None,
    topics: str | None = None,
    limit: int = 12,
) -> dict[str, Any]:
    """Read-only Neo4j: stats | lane | topics | disputes."""
    if mode == "stats":
        return {"mode": "stats", "stats": kg.corpus_stats()}
    if mode == "lane":
        if lane not in kg.LANE_KEYWORDS:
            raise ValueError(f"lane must be one of {sorted(kg.LANE_KEYWORDS)}")
        return {
            "mode": "lane",
            "lane": lane,
            "keywords": kg.LANE_KEYWORDS[lane],
            "topics": kg.topics_for_keywords(kg.LANE_KEYWORDS[lane], limit=limit),
        }
    if mode == "topics":
        kws = [w.lower() for w in (topics or "").split() if len(w) >= 3]
        if not kws:
            raise ValueError("topics mode requires space-separated keywords (3+ chars each)")
        return {"mode": "topics", "keywords": kws, "topics": kg.topics_for_keywords(kws, limit=limit)}
    if mode == "disputes":
        return {"mode": "disputes", "disputes": kg.marketing_disputes()}
    raise ValueError("mode must be stats | lane | topics | disputes")


@instrument_tool("health")
def health() -> dict[str, Any]:
    """Liveness + dependency checks (no secrets)."""
    status: dict[str, Any] = {"ok": True, "checks": {}}
    try:
        ensure_langchain_course()
        status["checks"]["langchain_course"] = "ok"
    except Exception as exc:
        status["ok"] = False
        status["checks"]["langchain_course"] = str(exc)
    try:
        stats = kg.corpus_stats()
        status["checks"]["neo4j"] = {"ok": True, "topics": stats.get("topics")}
    except Exception as exc:
        status["ok"] = False
        status["checks"]["neo4j"] = str(exc)
    return status


def dumps(obj: Any) -> str:
    return json.dumps(obj, indent=2, default=str)
