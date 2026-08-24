"""W1.1 route-first default wiring tests (proposal/worktree lane).

Offline-first: mocks route_query/query_all — no Pinecone/Neo4j/LangSmith writes.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kb_gateway import context
from kb_gateway.config import EXCLUDED_NAMESPACES
from kb_gateway.tools import _pick_surface, answer_learning_kb

_ROUTE_OK = {
    "answer": "router answer",
    "route": "vector",
    "route_reason": "semantic retrieval",
    "graph_context": "",
    "source_documents": ["course-transcripts/foo.md"],
    "retrieval_status": "ok",
    "namespaces": ["course-transcripts"],
    "per_namespace_counts": {"course-transcripts": 1},
}

_QUERY_ALL_OK = {
    "answer": "vector answer",
    "source_documents": ["patterns/bar.md"],
    "retrieval_status": "ok",
    "namespaces": ["patterns"],
    "per_namespace_counts": {"patterns": 1},
    "errors": {},
}


def test_excluded_namespaces_count_is_ten():
    assert len(EXCLUDED_NAMESPACES) == 10


def test_pick_surface_auto_defaults_route_query():
    assert _pick_surface("what is PAS copy structure?", "auto", None) == "route_query"


def test_pick_surface_broad_stays_query_all():
    assert _pick_surface("anything", "broad", None) == "query_all"
    assert _pick_surface("anything", "full_corpus", None) == "query_all"


def test_pick_surface_structural_wording_still_route_query():
    """F4: STRUCTURAL_HINTS branch was removed as dead code (both arms returned the same
    value); this case keeps coverage that structural-shaped auto-intent wording still
    routes to route_query via the unconditional fallthrough."""
    assert _pick_surface("which courses cover negotiation?", "auto", None) == "route_query"


def test_pick_surface_namespace_overrides():
    assert _pick_surface("q", "auto", "patterns") == "query_namespace"


@patch("kb_gateway.tools.query_all", return_value=_QUERY_ALL_OK)
@patch("kb_gateway.tools.route_query", return_value=_ROUTE_OK)
def test_answer_learning_kb_auto_uses_route_query(mock_route, mock_query_all):
    context.set_client("local")
    out = answer_learning_kb("what is RAG?", intent="auto")
    mock_route.assert_called_once()
    mock_query_all.assert_not_called()
    assert out["tool_used"] == "route_query"
    assert out["routing"]["intent"] == "auto"
    assert "degradation" not in out["routing"]


@patch("kb_gateway.tools.query_all", return_value=_QUERY_ALL_OK)
@patch("kb_gateway.tools.route_query", return_value=_ROUTE_OK)
def test_answer_learning_kb_broad_skips_router(mock_route, mock_query_all):
    context.set_client("local")
    out = answer_learning_kb("what is RAG?", intent="broad")
    mock_route.assert_not_called()
    mock_query_all.assert_called_once()
    assert out["tool_used"] == "query_all"


@patch("kb_gateway.tools.query_all", return_value=_QUERY_ALL_OK)
@patch("kb_gateway.tools.route_query", side_effect=RuntimeError("router unavailable"))
def test_route_query_failure_falls_back_with_degradation(mock_route, mock_query_all):
    context.set_client("local")
    out = answer_learning_kb("what is RAG?", intent="auto")
    mock_route.assert_called_once()
    mock_query_all.assert_called_once()
    assert out["tool_used"] == "query_all"
    assert out["routing"]["degradation"] == "route_query_fallback"
    assert "route_query" in (out.get("errors") or {})


@patch("kb_gateway.tools.query_all", return_value=_QUERY_ALL_OK)
@patch("kb_gateway.tools.route_query", return_value=_ROUTE_OK)
def test_answer_learning_kb_response_shape_contract(mock_route, mock_query_all):
    context.set_client("local")
    out = answer_learning_kb("shape check", intent="auto")
    assert out["surface"] == "answer_learning_kb"
    assert "access" in out
    access = out["access"]
    assert access["client"] == "local"
    assert access["role"] == "owner"
    assert "allowed_namespaces" in access
    assert "raw_evidence_allowed" in access
    evidence = out["evidence"]
    assert "namespaces" in evidence
    assert "per_namespace_counts" in evidence
    assert "graph_context_present" in evidence
    assert isinstance(evidence["graph_context_present"], bool)
    assert "sources" in evidence
    assert "source_count" in evidence


@patch("kb_gateway.tools.query_all", return_value=_QUERY_ALL_OK)
@patch("kb_gateway.tools.route_query", side_effect=FileNotFoundError("missing GO manifest"))
def test_route_query_failure_negative_path_exercises_real_fallback(
    mock_route, mock_query_all
):
    """Negative path: real answer_learning_kb call, not a decoy assertion."""
    context.set_client("collaborator")
    with pytest.raises(Exception):
        answer_learning_kb("", intent="auto")
    out = answer_learning_kb("fallback probe", intent="auto")
    assert out["routing"]["degradation"] == "route_query_fallback"
    assert out["access"]["role"] == "collaborator"


_ROUTE_INDETERMINATE = {
    "answer": "route_query returned no usable evidence for this query scope.",
    "route": "graph",
    "route_reason": "structural",
    "graph_context": "",
    "graph_facts_error": "ServiceUnavailable: Neo4j is down",
    "source_documents": [],
    "retrieval_status": "indeterminate",
    "namespaces": [],
    "per_namespace_counts": {},
    "errors": {},
}


@patch("kb_gateway.tools.query_all", return_value=_QUERY_ALL_OK)
@patch("kb_gateway.tools.route_query", return_value=_ROUTE_INDETERMINATE)
def test_route_query_indeterminate_falls_back_with_degraded_degradation(
    mock_route, mock_query_all
):
    """F1: successful route_query with indeterminate status must fall back to query_all."""
    context.set_client("local")
    out = answer_learning_kb("what is RAG?", intent="auto")
    mock_route.assert_called_once()
    mock_query_all.assert_called_once()
    assert out["tool_used"] == "query_all"
    assert out["routing"]["degradation"] == "route_query_degraded_fallback"
    assert "route_query" in (out.get("errors") or {})
    assert "ServiceUnavailable" in out["errors"]["route_query"]
