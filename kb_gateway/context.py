"""Request context for observability (client + tool)."""

from __future__ import annotations

from contextvars import ContextVar

_client: ContextVar[str] = ContextVar("kb_gateway_client", default="unknown")
_tool: ContextVar[str] = ContextVar("kb_gateway_tool", default="unknown")


def set_client(client: str) -> None:
    _client.set(client or "unknown")


def set_tool(tool: str) -> None:
    _tool.set(tool or "unknown")


def get_client() -> str:
    return _client.get()


def get_tool() -> str:
    return _tool.get()
