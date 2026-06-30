"""Tool implementations — delegate to langchain-course runtime (read-mostly)."""

from __future__ import annotations

import json
from typing import Any

from .config import ALLOWED_NAMESPACES
from . import graph as kg
from .lc_bootstrap import ensure_langchain_course
from .observability import instrument_tool


def _refused(structured_response: Any) -> bool:
    return bool(isinstance(structured_response, dict) and structured_response.get("refused"))


def _with_retrieval_status(result: dict[str, Any], *, surface: str) -> dict[str, Any]:
    """Prevent one-surface retrieval failures from becoming absence claims."""
    out = dict(result)
    source_documents = out.get("source_documents") or []
    graph_context = (out.get("graph_context") or "").strip()
    errors = out.get("errors") or {}
    no_evidence = not source_documents and not graph_context
    if no_evidence or _refused(out.get("structured_response")):
        original_answer = out.get("answer")
        out["retrieval_status"] = "indeterminate"
        out["original_answer"] = original_answer
        out["answer"] = (
            f"{surface} returned no usable evidence for this query scope. Do not treat "
            "this as proof that the learning KB lacks coverage; run/verify full-corpus "
            "vector retrieval plus graph/tooling-health checks before making an absence claim."
        )
    elif errors:
        out["retrieval_status"] = "partial"
    else:
        out["retrieval_status"] = "ok"
    if errors:
        out["errors"] = errors
    return out


@instrument_tool("route_query")
def route_query(question: str, k: int = 6, max_retries: int = 2) -> dict[str, Any]:
    """Agentic router: auto-pick graph vs vector vs both."""
    ensure_langchain_course()
    from runtime.agentic_router import route_query as _rq

    return _with_retrieval_status(_rq(question, k=k, max_retries=max_retries), surface="route_query")


@instrument_tool("query_all")
def query_all(question: str, k: int = 8) -> dict[str, Any]:
    """Core full-corpus RAG: course-transcripts + patterns + research-papers + langchain-docs
    merged into one answer with namespace-tagged sources. Use for general research /
    'what do we know about X' — it sees the WHOLE knowledge base, not one namespace."""
    ensure_langchain_course()
    from runtime.query import query_all as _qa

    result = _qa(question, k=k)
    return _with_retrieval_status({
        "answer": result.get("answer"),
        "context": result.get("context"),
        "namespaces": result.get("namespaces"),
        "per_namespace_counts": result.get("per_namespace_counts"),
        "errors": result.get("errors") or {},
        "source_documents": result.get("source_documents"),
        "structured_response": result.get("structured_response"),
    }, surface="query_all")


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
    return _with_retrieval_status({
        "answer": result.get("answer"),
        "namespace": namespace,
        "source_documents": result.get("source_documents"),
        "structured_response": result.get("structured_response"),
    }, surface=f"query_namespace:{namespace}")


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
