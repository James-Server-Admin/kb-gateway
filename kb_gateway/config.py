"""Environment configuration (no secrets in repo)."""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_LC_REPO = "/root/kb-core"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8790

# Collaborator-safe Pinecone namespaces (fail-closed whitelist).
#
# This is the EXPOSURE list — the ARCHITECTURE.md L2 security boundary, not a
# routing convenience: gateway tokens are shared with EXTERNAL collaborators
# (kb-access: friends, Cole), so anything listed here is remote-visible.
# REGISTRATION lives in kb-core config.py NAMESPACES. Every kb-core-registered
# namespace must appear either here or in EXCLUDED_NAMESPACES below with a
# reason, so the two lists can never silently diverge (enforced by
# tests/test_namespace_whitelist.py; kb-index-remediation W_502).
#
# research-papers (added 2026-06-24): external whitepapers exposed through
# query_all/query_namespace alongside the course corpus.
ALLOWED_NAMESPACES = frozenset(
    {
        "patterns",
        "course-transcripts",
        "langchain-docs",
        "research-papers",
    }
)

# Shared rationale for the three namespaces the W_502 first draft wrongly
# exposed (reverted on review).
_PENDING_OWNER_TIER = (
    "PENDING operator access-tier decision (PR #3 review BLOCKER 2026-07-02): "
    "contains infra runbooks/registry SoT/execution-routine material; gateway "
    "tokens are shared with external collaborators (kb-access) — exposure "
    "requires role-gated namespaces (owner-only tier) which does not exist yet."
)

# Registered in kb-core config.py NAMESPACES but intentionally NOT exposed to
# remote clients (kb-index-remediation W_502). One entry per exclusion with
# WHY; move a namespace to ALLOWED_NAMESPACES only with an operator-reviewed
# PR.
EXCLUDED_NAMESPACES: dict[str, str] = {
    "course-code": "24 vectors of repo scripts/notebooks — low value via MCP",
    "session-compactions": "compaction RECORDs from the estate compaction sink (canon#814/#815) — private episodic layer, James-lane only; never collaborator-safe",
    "own-notes": "personal operator notes (18 vectors) — not collaborator-safe",
    "orchestrations": _PENDING_OWNER_TIER,
    "pinecone-platform": _PENDING_OWNER_TIER,
    "platform-fabric": _PENDING_OWNER_TIER,
    "github-platform": "platform template — queryable via github-platform-bootstrap",
    "langsmith-platform": "platform template — queryable via langsmith-platform-bootstrap",
    "neo4j-platform": "platform template — queryable via neo4j-platform-bootstrap",
    "pinecone-platform-smoke": "W18 smoke-test artifacts — verification residue, not knowledge",
    "keyflo-copy-eval-feedback": "Keyflo product-eval feedback store — not learning KB content",
}


def langchain_course_repo() -> Path:
    return Path(os.environ.get("LANGCHAIN_COURSE_REPO", DEFAULT_LC_REPO))


def gateway_host() -> str:
    return os.environ.get("KB_GATEWAY_HOST", DEFAULT_HOST)


def gateway_port() -> int:
    return int(os.environ.get("KB_GATEWAY_PORT", str(DEFAULT_PORT)))


def api_token() -> str | None:
    return os.environ.get("KB_GATEWAY_API_TOKEN") or None


def api_tokens() -> frozenset[str]:
    """All accepted bearer tokens (env + optional keys file)."""
    tokens: set[str] = set()
    if t := api_token():
        tokens.add(t)
    path = os.environ.get("KB_GATEWAY_API_KEYS_PATH")
    if path:
        p = Path(path)
        if p.is_file():
            for line in p.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    tokens.add(line)
    return frozenset(tokens)


def public_url() -> str:
    return os.environ.get("KB_GATEWAY_PUBLIC_URL", f"http://{gateway_host()}:{gateway_port()}")


def audit_log_path() -> Path:
    return Path(
        os.environ.get(
            "KB_GATEWAY_AUDIT_LOG",
            "/mnt/blockstorage/business/Keyflo_AI/08_Development/kb-gateway/logs/audit.jsonl",
        )
    )


def observability_surface() -> str:
    return os.environ.get("KB_GATEWAY_SURFACE", "mcp")


def observability_environment() -> str:
    return os.environ.get("KB_GATEWAY_ENVIRONMENT", "production")


def token_client_map() -> dict[str, str]:
    """Map bearer token → client label from keys file (# cole-2026-06 lines)."""
    mapping: dict[str, str] = {}
    if t := api_token():
        mapping[t] = os.environ.get("KB_GATEWAY_DEFAULT_CLIENT", "operator")
    path = os.environ.get("KB_GATEWAY_API_KEYS_PATH")
    if not path:
        return mapping
    p = Path(path)
    if not p.is_file():
        return mapping
    lines = p.read_text().splitlines()
    label = "unknown"
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            body = line.lstrip("#").strip()
            if body:
                parts = body.split()
                if parts:
                    tag = parts[0].split("-")[0].lower()
                    if tag:
                        label = tag
            continue
        mapping[line] = label
    return mapping
