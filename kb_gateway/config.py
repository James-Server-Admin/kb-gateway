"""Environment configuration (no secrets in repo)."""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_LC_REPO = "/root/langchain-course"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8790

# Collaborator-safe Pinecone namespaces (fail-closed whitelist)
# research-papers (added 2026-06-24): external whitepapers exposed through
# query_all/query_namespace alongside the course corpus.
ALLOWED_NAMESPACES = frozenset({"patterns", "course-transcripts", "langchain-docs", "research-papers"})


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
