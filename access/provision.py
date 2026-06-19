"""Provision GitHub access + MCP bearer token."""

from __future__ import annotations

import os
import secrets
import subprocess
from pathlib import Path


def _keys_path() -> Path:
    return Path(
        os.environ.get(
            "KB_GATEWAY_API_KEYS_PATH",
            "/mnt/blockstorage/private/credentials/learning-kb-api-keys.txt",
        )
    )


def _gh_repo() -> str:
    return os.environ.get("KB_ACCESS_GH_REPO", "James-Server-Admin/kb-gateway")


def append_api_token(*, label: str) -> str:
    token = secrets.token_hex(32)
    path = _keys_path()
    line = f"# {label}\n{token}\n"
    with path.open("a") as f:
        f.write(line)
    return token


def invite_github_collaborator(username: str) -> None:
    repo = _gh_repo()
    env = os.environ.copy()
    env.pop("GH_TOKEN", None)
    env.pop("GITHUB_TOKEN", None)
    subprocess.run(
        [
            "gh",
            "api",
            f"repos/{repo}/collaborators/{username}",
            "-X",
            "PUT",
            "-f",
            "permission=read",
        ],
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )


def restart_kb_gateway() -> None:
    subprocess.run(["systemctl", "restart", "kb-gateway.service"], check=False)


def send_access_email(*, to_email: str, name: str, claim_url: str) -> bool:
    """Send claim link via Resend. Returns False if Resend not configured."""
    api_key = os.environ.get("KEYFLO_RESEND_ADMIN_API_KEY") or os.environ.get("KEYFLO_RESEND_API_KEY")
    if not api_key:
        return False
    from_addr = os.environ.get("KB_ACCESS_EMAIL_FROM", "James <hello@mail.keyflo.ai>")
    subject = "Learning KB access approved"
    html = f"""
<p>Hi {name},</p>
<p>Your access to the learning KB MCP was approved.</p>
<p><strong><a href="{claim_url}">Click here to get your setup link and token</a></strong></p>
<p>This link is personal — do not forward it.</p>
<p>After claiming, follow <a href="https://github.com/James-Server-Admin/kb-gateway/blob/main/docs/FRIEND-SETUP.md">FRIEND-SETUP.md</a>.</p>
"""
    import json
    import urllib.request

    body = json.dumps(
        {
            "from": from_addr,
            "to": [to_email],
            "subject": subject,
            "html": html,
        }
    ).encode()
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return 200 <= resp.status < 300
    except Exception:
        return False


def provision_access(*, github_username: str, email: str, name: str, claim_url: str) -> str:
    label = f"{github_username}-{secrets.token_hex(3)}"
    token = append_api_token(label=label)
    invite_github_collaborator(github_username)
    restart_kb_gateway()
    send_access_email(to_email=email, name=name, claim_url=claim_url)
    return token
