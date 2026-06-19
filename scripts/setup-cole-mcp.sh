#!/usr/bin/env bash
# Back-compat alias — use setup-mcp.sh
exec "$(dirname "$0")/setup-mcp.sh" "$@"
