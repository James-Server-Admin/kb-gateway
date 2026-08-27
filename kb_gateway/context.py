"""Request context for observability (client, tool, and safe caller identity)."""

from __future__ import annotations

import base64
import json
import os
import re
from contextvars import ContextVar
from typing import Any, Mapping

_client: ContextVar[str] = ContextVar("kb_gateway_client", default="unknown")
_tool: ContextVar[str] = ContextVar("kb_gateway_tool", default="unknown")
_caller_context: ContextVar[dict[str, Any] | None] = ContextVar(
    "kb_gateway_caller_context",
    default=None,
)

_SAFE_VALUE = re.compile(r"^[A-Za-z0-9_./:-]+$")
_MAX_VALUE_LEN = 128
_RAW_TO_CALLER = {
    "team": "caller_team",
    "seat": "caller_seat",
    "role": "caller_role",
    "gate": "caller_gate",
    "trace_id": "caller_trace_id",
    "session_root": "caller_session_root",
    "project_root": "caller_session_root",
}
_IDENTITY_KEYS = ("caller_team", "caller_seat", "caller_role", "caller_gate", "caller_trace_id")
_MISSING_LABELS = {
    "caller_team": "team",
    "caller_seat": "seat",
    "caller_role": "role",
    "caller_gate": "gate",
    "caller_trace_id": "trace_id",
}


def set_client(client: str) -> None:
    _client.set(client or "unknown")


def set_tool(tool: str) -> None:
    _tool.set(tool or "unknown")


def get_client() -> str:
    return _client.get()


def get_tool() -> str:
    return _tool.get()


def _safe_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or len(text) > _MAX_VALUE_LEN or not _SAFE_VALUE.fullmatch(text):
        return None
    return text


def sanitize_caller_context(raw: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return audit-safe caller context fields without raw payload leakage."""
    if not raw:
        return {"caller_identity_status": "unknown"}

    out: dict[str, Any] = {}
    rejected = bool(raw.get("caller_context_rejected"))
    for raw_key, caller_key in _RAW_TO_CALLER.items():
        value = raw.get(caller_key, raw.get(raw_key))
        safe = _safe_string(value)
        if safe is not None:
            out[caller_key] = safe
        elif value not in (None, ""):
            rejected = True

    present = [key for key in _IDENTITY_KEYS if key in out]
    if len(present) == len(_IDENTITY_KEYS):
        status = "known"
    elif present:
        status = "partial"
        out["caller_identity_missing"] = [
            _MISSING_LABELS[key] for key in _IDENTITY_KEYS if key not in out
        ]
    else:
        status = "unknown"

    out["caller_identity_status"] = status
    if rejected:
        out["caller_context_rejected"] = True
    return out


def set_caller_context(raw: Mapping[str, Any] | None) -> dict[str, Any]:
    """Set sanitized caller context and return the stored dict."""
    sanitized = sanitize_caller_context(raw)
    _caller_context.set(sanitized)
    return dict(sanitized)


def clear_caller_context() -> None:
    _caller_context.set(None)


def get_caller_context() -> dict[str, Any]:
    current = _caller_context.get()
    if current is None:
        return {"caller_identity_status": "unknown"}
    return dict(current)


def parse_caller_context_payload(payload: str | None) -> dict[str, Any]:
    """Parse JSON or base64url JSON caller context; bad input becomes unknown."""
    text = (payload or "").strip()
    if not text:
        return sanitize_caller_context(None)
    candidates = [text]
    padded = text + ("=" * (-len(text) % 4))
    try:
        decoded = base64.urlsafe_b64decode(padded.encode()).decode()
        candidates.append(decoded)
    except Exception:
        pass
    for candidate in candidates:
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(data, Mapping):
            return sanitize_caller_context(data)
        return sanitize_caller_context({"caller_context_rejected": True})
    return sanitize_caller_context({"caller_context_rejected": True})


def caller_context_from_env() -> dict[str, Any]:
    raw = {
        "caller_team": os.environ.get("SM_CALLER_TEAM"),
        "caller_seat": os.environ.get("SM_CALLER_SEAT"),
        "caller_role": os.environ.get("SM_CALLER_ROLE"),
        "caller_gate": os.environ.get("SM_CALLER_GATE"),
        "caller_trace_id": os.environ.get("SM_TRACE_ID"),
        "caller_session_root": os.environ.get("SM_PROJECT_ROOT"),
    }
    return sanitize_caller_context(raw)


def set_caller_context_from_env() -> dict[str, Any]:
    return set_caller_context(caller_context_from_env())


def load_caller_context_arg(value: str | None) -> dict[str, Any]:
    """Load caller context from a JSON string, base64url JSON, or @file."""
    if not value:
        return caller_context_from_env()
    if value.startswith("@"):
        try:
            value = open(value[1:], encoding="utf-8").read()
        except OSError:
            return sanitize_caller_context({"caller_context_rejected": True})
    return parse_caller_context_payload(value)
