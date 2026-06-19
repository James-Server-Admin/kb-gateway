"""Append-only MCP audit log (no secrets, no full question text)."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from .config import audit_log_path, observability_environment, observability_surface


def _default_path() -> Path:
    return audit_log_path()


def log_event(
    *,
    tool: str,
    client: str,
    status: str,
    latency_ms: int,
    question: str | None = None,
    route: str | None = None,
    error: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    path = _default_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    q_hash = None
    q_len = None
    if question is not None:
        q_len = len(question)
        q_hash = hashlib.sha256(question.encode()).hexdigest()[:16]
    row = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "surface": observability_surface(),
        "environment": observability_environment(),
        "client": client,
        "tool": tool,
        "status": status,
        "latency_ms": latency_ms,
        "question_len": q_len,
        "question_hash": q_hash,
        "route": route,
        "error": (error or "")[:200] if error else None,
    }
    if extra:
        row.update(extra)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, default=str) + "\n")
