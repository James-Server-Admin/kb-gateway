"""W1.2 dispute-first answer contract tests (proposal/worktree lane).

Offline-first: mocks route_query/query_all — no Pinecone/Neo4j/LangSmith writes.
No Claim.statement similarity matching (kb-gateway#11).
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kb_gateway import context
from kb_gateway.dispute_answer import (
    apply_dispute_first_answer,
    extract_dispute_lines,
    format_dispute_first_answer,
    has_dispute_lines,
)
from kb_gateway.tools import answer_learning_kb

FIXTURES = Path(__file__).resolve().parent / "fixtures"
DISPUTE_CTX = (FIXTURES / "graph_context_dispute.txt").read_text(encoding="utf-8")
NO_DISPUTE_CTX = (FIXTURES / "graph_context_no_dispute.txt").read_text(encoding="utf-8")

_ROUTE_WITH_DISPUTE = {
    "answer": "Use rapport-building to open negotiations effectively.",
    "route": "graph",
    "route_reason": "dispute question",
    "graph_context": DISPUTE_CTX,
    "source_documents": ["course-transcripts/foo.md"],
    "retrieval_status": "ok",
    "namespaces": ["course-transcripts"],
    "per_namespace_counts": {"course-transcripts": 1},
}

_ROUTE_NO_DISPUTE = {
    "answer": "PAS is Problem-Agitate-Solution copy structure.",
    "route": "vector",
    "route_reason": "semantic retrieval",
    "graph_context": NO_DISPUTE_CTX,
    "source_documents": ["patterns/bar.md"],
    "retrieval_status": "ok",
    "namespaces": ["patterns"],
    "per_namespace_counts": {"patterns": 1},
}


def test_extract_dispute_lines_parses_graph_facts_format():
    lines = extract_dispute_lines(DISPUTE_CTX)
    assert len(lines) == 2
    assert all(line.startswith("DISPUTE (") for line in lines)


def test_has_dispute_lines_false_for_coverage_only():
    assert not has_dispute_lines(NO_DISPUTE_CTX)


def test_format_dispute_first_answer_opens_with_disagreement():
    out = format_dispute_first_answer("Recommendation body.", DISPUTE_CTX)
    assert out.startswith("## Disagreement in the corpus")
    assert "## Recommendation" in out
    assert out.index("## Disagreement in the corpus") < out.index("## Recommendation")
    assert "Recommendation body." in out


def test_format_preserves_both_courses_and_statements():
    out = format_dispute_first_answer("x", DISPUTE_CTX)
    assert "Course-A" in out
    assert "Course-B" in out
    assert "Course-C" in out
    assert "rapport-building small talk" in out
    assert "direct value proposition" in out
    assert "DISPUTE (opening):" in out
    assert "DISPUTE (framing):" in out


def test_apply_dispute_first_answer_no_dispute_passthrough():
    raw = "unchanged answer"
    assert apply_dispute_first_answer(raw, NO_DISPUTE_CTX) == raw


def test_buried_dispute_in_raw_answer_still_surfaces():
    buried = "Start with a single best-practice recommendation without naming disagreement."
    out = apply_dispute_first_answer(buried, DISPUTE_CTX)
    assert out.startswith("## Disagreement in the corpus")
    assert "DISPUTE (opening):" in out
    assert buried in out


@patch("kb_gateway.tools.query_all")
@patch("kb_gateway.tools.route_query", return_value=_ROUTE_WITH_DISPUTE)
def test_answer_learning_kb_dispute_fixture_contract(mock_route, mock_query_all):
    context.set_client("local")
    out = answer_learning_kb("do courses disagree about negotiation openings?", intent="structural")
    mock_route.assert_called_once()
    answer = out["answer"]
    assert answer.startswith("## Disagreement in the corpus")
    assert "Course-A" in answer and "Course-B" in answer
    assert out["surface"] == "answer_learning_kb"
    assert "access" in out
    assert out["access"]["client"] == "local"
    evidence = out["evidence"]
    assert evidence["graph_context_present"] is True
    assert "namespaces" in evidence
    assert "per_namespace_counts" in evidence
    assert "graph_context" in out
    assert "DISPUTE (opening):" in out["graph_context"]


@patch("kb_gateway.tools.query_all")
@patch("kb_gateway.tools.route_query", return_value=_ROUTE_NO_DISPUTE)
def test_answer_learning_kb_no_dispute_normal_flow(mock_route, mock_query_all):
    context.set_client("collaborator")
    out = answer_learning_kb("what is PAS copy structure?", intent="auto")
    assert out["answer"] == _ROUTE_NO_DISPUTE["answer"]
    assert not out["answer"].startswith("## Disagreement")
    assert out["access"]["role"] == "collaborator"


@patch("kb_gateway.tools.query_all")
@patch("kb_gateway.tools.route_query")
def test_claim_statement_similarity_not_in_scope(mock_route, mock_query_all):
    """W1.2 uses DISPUTE-line prefix only; kb-gateway#11 owns similarity matching."""
    context.set_client("local")
    mock_route.return_value = {
        **_ROUTE_WITH_DISPUTE,
        "answer": "ignored",
    }
    with patch("kb_gateway.graph.corpus_stats") as graph_stats:
        with patch("kb_gateway.graph.marketing_disputes") as marketing_disputes:
            answer_learning_kb("dispute probe", intent="structural")
    graph_stats.assert_not_called()
    marketing_disputes.assert_not_called()
    out = answer_learning_kb("dispute probe", intent="structural")
    assert out["answer"].startswith("## Disagreement in the corpus")
