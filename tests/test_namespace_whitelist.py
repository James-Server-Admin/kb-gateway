"""Whitelist <-> registry parity checks (kb-index-remediation W_502).

Kills the two-place-whitelist silent-divergence failure mode: kb-core
config.py NAMESPACES is the REGISTRATION list, kb_gateway/config.py
ALLOWED_NAMESPACES is the EXPOSURE list. Every registered namespace must be
either exposed (ALLOWED_NAMESPACES) or explicitly excluded with a reason
(EXCLUDED_NAMESPACES) — a namespace in neither place fails these tests.

Offline: imports kb-core config.py directly (no Pinecone/Neo4j/env needed).
Run: /root/.venv-langchain-course/bin/python -m pytest tests/ -v
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kb_gateway.config import (  # noqa: E402
    ALLOWED_NAMESPACES,
    EXCLUDED_NAMESPACES,
    langchain_course_repo,
)

# The curated exposure set — the original 4 collaborator-safe namespaces.
# The W_502 first draft expanded this to 7; reverted on review (PR #3 BLOCKER
# 2026-07-02): gateway tokens are shared with external collaborators
# (kb-access), and pinecone-platform / platform-fabric / orchestrations carry
# infra SoT material that needs a not-yet-existing owner-only tier. Changing
# this set is an operator-reviewed decision — update the decision reference
# alongside the code.
CURATED_ALLOWED = frozenset(
    {
        "patterns",
        "course-transcripts",
        "langchain-docs",
        "research-papers",
    }
)


def _kb_core_registered_namespaces() -> frozenset[str]:
    """Load kb-core's NAMESPACES registry without triggering env bootstrap.

    Loaded from the explicit file path so the gateway repo's config/ directory
    can never shadow it as a namespace package.
    """
    repo = langchain_course_repo()
    config_path = repo / "config.py"
    if not config_path.is_file():
        pytest.skip(f"kb-core not present at {repo} (set LANGCHAIN_COURSE_REPO)")
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))  # config.py imports sibling `bootstrap`
    spec = importlib.util.spec_from_file_location("_kb_core_config_w502", config_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return frozenset(module.NAMESPACES)


def test_allowed_namespaces_match_curated_set():
    assert ALLOWED_NAMESPACES == CURATED_ALLOWED


def test_allowed_and_excluded_are_disjoint():
    overlap = ALLOWED_NAMESPACES & set(EXCLUDED_NAMESPACES)
    assert not overlap, f"namespaces both allowed and excluded: {sorted(overlap)}"


def test_every_exclusion_documents_why():
    undocumented = [ns for ns, why in EXCLUDED_NAMESPACES.items() if not why.strip()]
    assert not undocumented, f"exclusions missing a reason: {undocumented}"


def test_allowed_namespaces_are_registered_in_kb_core():
    registered = _kb_core_registered_namespaces()
    unknown = ALLOWED_NAMESPACES - registered
    assert not unknown, (
        f"ALLOWED_NAMESPACES not in kb-core NAMESPACES registry: {sorted(unknown)}"
    )


def test_registry_fully_partitioned_into_allowed_or_excluded():
    """Any namespace registered in kb-core but absent from BOTH gateway lists is
    the silent-divergence failure mode this file exists to prevent."""
    registered = _kb_core_registered_namespaces()
    unaccounted = registered - ALLOWED_NAMESPACES - set(EXCLUDED_NAMESPACES)
    assert not unaccounted, (
        "kb-core registers namespaces the gateway has no explicit intent for "
        f"(add to ALLOWED_NAMESPACES or EXCLUDED_NAMESPACES with a reason): "
        f"{sorted(unaccounted)}"
    )
    stale = set(EXCLUDED_NAMESPACES) - registered
    assert not stale, (
        f"EXCLUDED_NAMESPACES lists namespaces no longer registered in kb-core: "
        f"{sorted(stale)}"
    )
