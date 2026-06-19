"""Persist KB access requests as JSON files."""

from __future__ import annotations

import json
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

Status = Literal["pending", "approved", "denied"]


def _dir() -> Path:
    import os

    p = Path(os.environ.get("KB_ACCESS_DATA_DIR", "/mnt/blockstorage/private/kb-access-requests"))
    p.mkdir(parents=True, exist_ok=True)
    return p


def _path(request_id: str) -> Path:
    safe = request_id.replace("/", "").replace("..", "")
    return _dir() / f"{safe}.json"


def create(*, name: str, email: str, github_username: str, note: str = "") -> dict[str, Any]:
    rid = uuid.uuid4().hex[:12]
    gh = github_username.strip().lstrip("@").lower()
    rec = {
        "id": rid,
        "status": "pending",
        "name": name.strip(),
        "email": email.strip().lower(),
        "github_username": gh,
        "note": note.strip()[:500],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _path(rid).write_text(json.dumps(rec, indent=2) + "\n")
    _path(rid).chmod(0o600)
    return rec


def get(request_id: str) -> dict[str, Any] | None:
    p = _path(request_id)
    if not p.is_file():
        return None
    return json.loads(p.read_text())


def update(request_id: str, **fields: Any) -> dict[str, Any]:
    rec = get(request_id)
    if rec is None:
        raise KeyError(request_id)
    rec.update(fields)
    rec["updated_at"] = datetime.now(timezone.utc).isoformat()
    _path(request_id).write_text(json.dumps(rec, indent=2) + "\n")
    _path(request_id).chmod(0o600)
    return rec


def new_claim_code() -> str:
    return secrets.token_urlsafe(18)
