#!/usr/bin/env python3
"""Route-first CLI entry for learning KB queries (W1.1 local equivalent).

Default path uses answer_learning_kb(intent=auto) — agentic route_query first,
vector fallback on router failure. Explicit --broad preserves full-corpus mode.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow `python scripts/learning_kb_query.py` from repo root.
_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from kb_gateway import context
from kb_gateway.tools import answer_learning_kb, dumps


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Query the learning KB via route-first default wiring.",
    )
    parser.add_argument("question", nargs="+", help="Natural-language question")
    parser.add_argument(
        "--broad",
        action="store_true",
        help="Explicit full-corpus vector mode (skips route-first default)",
    )
    parser.add_argument("--json", action="store_true", help="Emit answer_learning_kb JSON")
    parser.add_argument(
        "--caller-context",
        help="Caller context as JSON/base64url JSON or @file; defaults to SM_CALLER_* env",
    )
    parser.add_argument("-k", type=int, default=8, help="Retrieval depth (1-12)")
    args = parser.parse_args(argv)

    question = " ".join(args.question).strip()
    if not question:
        parser.error("question is required")

    context.set_client("local")
    context.set_caller_context(context.load_caller_context_arg(args.caller_context))
    intent = "broad" if args.broad else "auto"
    result = answer_learning_kb(question=question, intent=intent, k=args.k)

    if args.json:
        print(dumps(result))
        return 0

    routing = result.get("routing") or {}
    degradation = routing.get("degradation")
    print(f"tool_used: {result.get('tool_used')}")
    if degradation:
        print(f"DEGRADATION: {degradation}")
    if routing.get("route"):
        print(f"route: {routing['route']} ({routing.get('route_reason', '')})")
    print()
    print(result.get("answer") or "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
