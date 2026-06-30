"""Run uvicorn for KB access portal."""

import os
import sys

import uvicorn

if __name__ == "__main__":
    sys.path.insert(0, "/mnt/blockstorage/env")
    from load_credentials import load_kb_access

    load_kb_access()
    host = os.environ.get("KB_ACCESS_HOST", "127.0.0.1")
    port = int(os.environ.get("KB_ACCESS_PORT", "8792"))
    uvicorn.run("access.server:app", host=host, port=port, log_level="info")
