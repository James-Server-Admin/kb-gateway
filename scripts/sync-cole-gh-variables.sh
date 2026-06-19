#!/usr/bin/env bash
# Back-compat alias — use sync-gh-variables.sh
exec "$(dirname "$0")/sync-gh-variables.sh" "$@"
