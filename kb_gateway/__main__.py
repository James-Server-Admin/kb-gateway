"""CLI entry: python -m kb_gateway [--transport stdio|streamable-http]"""

from __future__ import annotations

import argparse

from .server import build_mcp


def main() -> None:
    p = argparse.ArgumentParser(description="James learning KB gateway (MCP)")
    p.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="streamable-http",
        help="stdio for local Cursor; streamable-http for remote agents",
    )
    p.add_argument("--no-auth", action="store_true", help="disable bearer auth (localhost dev only)")
    args = p.parse_args()

    if args.no_auth:
        from .context import set_client

        set_client("local")

    mcp = build_mcp(enable_auth=False if args.no_auth else None)
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
