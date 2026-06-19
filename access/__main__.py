"""Run uvicorn for KB access portal."""

import os

import uvicorn

if __name__ == "__main__":
    host = os.environ.get("KB_ACCESS_HOST", "127.0.0.1")
    port = int(os.environ.get("KB_ACCESS_PORT", "8792"))
    uvicorn.run("access.server:app", host=host, port=port, log_level="info")
