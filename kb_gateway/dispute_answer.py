"""Dispute-first answer formatting for answer_learning_kb (W1.2).

Operates on pre-formatted DISPUTE lines from agentic_router._graph_facts only.
Claim.statement similarity matching is kb-gateway#11 — not implemented here.
"""

from __future__ import annotations

DISPUTE_LINE_PREFIX = "DISPUTE ("
DISAGREEMENT_HEADER = "## Disagreement in the corpus"
RECOMMENDATION_HEADER = "## Recommendation"


def extract_dispute_lines(graph_context: str) -> list[str]:
    """Return non-empty lines beginning with DISPUTE ( from graph context."""
    if not graph_context:
        return []
    lines: list[str] = []
    for raw in graph_context.splitlines():
        line = raw.strip()
        if line.startswith(DISPUTE_LINE_PREFIX):
            lines.append(line)
    return lines


def has_dispute_lines(graph_context: str) -> bool:
    return bool(extract_dispute_lines(graph_context))


def format_dispute_first_answer(
    raw_answer: str | None,
    graph_context: str,
    *,
    dispute_lines: list[str] | None = None,
) -> str:
    """Prepend disagreement section when graph_context carries DISPUTE facts."""
    lines = dispute_lines if dispute_lines is not None else extract_dispute_lines(graph_context)
    if not lines:
        return raw_answer or ""

    body = (raw_answer or "").strip()
    dispute_block = "\n".join(f"- {line}" for line in lines)
    parts = [DISAGREEMENT_HEADER, "", dispute_block]
    if body:
        parts.extend(["", RECOMMENDATION_HEADER, "", body])
    return "\n".join(parts)


def apply_dispute_first_answer(
    raw_answer: str | None,
    graph_context: str | None,
) -> str:
    """Apply dispute-first contract when graph_context contains DISPUTE lines."""
    gctx = (graph_context or "").strip()
    if not has_dispute_lines(gctx):
        return raw_answer or ""
    return format_dispute_first_answer(raw_answer, gctx)
