"""LangSmith metadata + audit instrumentation for MCP tools."""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from langsmith.run_helpers import tracing_context

from . import audit
from .config import observability_environment, observability_surface
from .context import get_client, get_tool, set_tool

F = TypeVar("F", bound=Callable[..., Any])


def trace_metadata() -> dict[str, str]:
    return {
        "surface": observability_surface(),
        "environment": observability_environment(),
        "client": get_client(),
        "tool": get_tool(),
        "service": "kb-gateway",
    }


def with_tracing(fn: F) -> F:
    """Wrap tool impl with LangSmith tracing_context metadata."""

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        with tracing_context(
            metadata=trace_metadata(),
            tags=["kb-gateway", observability_surface()],
        ):
            return fn(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


def instrument_tool(tool_name: str) -> Callable[[F], F]:
    """Decorator: time, audit-log, and trace a tool returning structured data."""

    def decorator(fn: F) -> F:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            set_tool(tool_name)
            client = get_client()
            question = kwargs.get("question") if "question" in kwargs else (args[0] if args else None)
            if not isinstance(question, str):
                question = None
            t0 = time.perf_counter()
            status = "ok"
            route = None
            err = None
            try:
                with tracing_context(
                    metadata={**trace_metadata(), "tool": tool_name},
                    tags=["kb-gateway", tool_name],
                ):
                    result = fn(*args, **kwargs)
                if isinstance(result, dict):
                    route = result.get("route")
                return result
            except Exception as exc:
                status = "error"
                err = str(exc)
                raise
            finally:
                latency_ms = int((time.perf_counter() - t0) * 1000)
                audit.log_event(
                    tool=tool_name,
                    client=client,
                    status=status,
                    latency_ms=latency_ms,
                    question=question,
                    route=route,
                    error=err,
                )

        return wrapper  # type: ignore[return-value]

    return decorator
