"""KB access request portal — self-service request + operator approve links."""

from __future__ import annotations

import hashlib
import html
import hmac
import json
import os
import urllib.request
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from access import provision, store
from kb_gateway.config import api_tokens, token_client_map
from kb_gateway.context import set_client

app = FastAPI(title="KB Access Portal", version="1.0.0")


def _public_url() -> str:
    return os.environ.get("KB_ACCESS_PUBLIC_URL", "https://kb-access.waytie.com").rstrip("/")


def _approve_secret() -> str:
    path = os.environ.get(
        "KB_ACCESS_APPROVE_SECRET_PATH",
        "/mnt/blockstorage/private/credentials/kb-access-approve-secret.txt",
    )
    p = Path(path)
    if not p.is_file():
        raise RuntimeError(f"Missing approve secret at {path}")
    return p.read_text().strip()


def _sign(request_id: str, action: str) -> str:
    msg = f"{action}:{request_id}".encode()
    return hmac.new(_approve_secret().encode(), msg, hashlib.sha256).hexdigest()


def _verify(request_id: str, action: str, sig: str) -> bool:
    expected = _sign(request_id, action)
    return hmac.compare_digest(expected, sig)


def _slack_notify(text: str) -> None:
    url = os.environ.get("SLACK_WEBHOOK_URL", "").strip()
    if not url:
        return
    body = json.dumps({"text": text}).encode()
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        urllib.request.urlopen(req, timeout=15)
    except Exception:
        pass


def _client_for_token(token: str) -> str | None:
    for expected in api_tokens():
        if hmac.compare_digest(token, expected):
            return token_client_map().get(expected, "unknown")
    return None


def _page(title: str, body: str) -> HTMLResponse:
    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{title}</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:42rem;margin:2rem auto;padding:0 1rem;line-height:1.5}}
label{{display:block;margin:.75rem 0 .25rem;font-weight:600}}
input,textarea,select{{width:100%;padding:.5rem;font-size:1rem}}
button{{margin-top:1rem;padding:.6rem 1.2rem;font-size:1rem;cursor:pointer}}
.card{{border:1px solid #ddd;border-radius:8px;padding:1rem;margin:1rem 0}}
code,pre{{background:#f4f4f4;padding:.2rem .4rem;border-radius:4px;word-break:break-all}}
</style></head><body>
<h1>{title}</h1>
{body}
</body></html>"""
    return HTMLResponse(html)


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    return _page(
        "Request learning KB access",
        """
<p>Query ~116 marketing &amp; engineering courses from Cursor via MCP.</p>
<form method="post" action="/request">
  <label for="name">Name</label>
  <input id="name" name="name" required maxlength="120"/>
  <label for="email">Email</label>
  <input id="email" name="email" type="email" required maxlength="200"/>
  <label for="github_username">GitHub username</label>
  <input id="github_username" name="github_username" required maxlength="80"
         placeholder="your-handle (not email)"/>
  <label for="note">Note (optional)</label>
  <textarea id="note" name="note" rows="3" maxlength="500"
            placeholder="How you plan to use it"></textarea>
  <button type="submit">Request access</button>
</form>
<p><small>Read-only learning corpus — not Keyflo product data. James approves each request.</small></p>
<p><a href="/query">Query from browser</a></p>
""",
    )


@app.get("/query", response_class=HTMLResponse)
def query_page() -> HTMLResponse:
    return _page(
        "Query learning KB",
        """
<form method="post" action="/query">
  <label for="token">MCP bearer token</label>
  <input id="token" name="token" type="password" required autocomplete="off"/>
  <label for="question">Question</label>
  <textarea id="question" name="question" rows="5" required maxlength="4000"></textarea>
  <label for="intent">Intent</label>
  <select id="intent" name="intent">
    <option value="auto">auto</option>
    <option value="broad">broad</option>
    <option value="structural">structural</option>
  </select>
  <button type="submit">Ask</button>
</form>
<p><small>Uses the same read-only token as MCP. No Pinecone or Neo4j keys are sent to the browser.</small></p>
""",
    )


@app.post("/query", response_class=HTMLResponse)
def submit_query(
    token: str = Form(...),
    question: str = Form(...),
    intent: str = Form("auto"),
) -> HTMLResponse:
    client = _client_for_token(token.strip())
    if client is None:
        raise HTTPException(403, "Invalid token")
    set_client(client)
    try:
        from kb_gateway import tools

        result = tools.answer_learning_kb(
            question=question,
            intent=intent,
            k=8,
            max_retries=2,
            include_raw=False,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        return _page(
            "Query failed",
            f"<p>Gateway query failed: <code>{html.escape(str(exc))}</code></p><p><a href=\"/query\">Try again</a></p>",
        )

    answer = html.escape(str(result.get("answer") or "No answer returned."))
    status = html.escape(str(result.get("retrieval_status") or "unknown"))
    evidence = html.escape(json.dumps(result.get("evidence", {}), indent=2, default=str))
    next_steps = result.get("next_steps") or []
    steps_html = "".join(f"<li>{html.escape(str(step))}</li>" for step in next_steps)
    return _page(
        "Learning KB answer",
        f"""
<div class="card">
<p><strong>Status:</strong> <code>{status}</code></p>
<pre>{answer}</pre>
</div>
<div class="card">
<h2>Evidence</h2>
<pre>{evidence}</pre>
</div>
{f'<div class="card"><h2>Next steps</h2><ul>{steps_html}</ul></div>' if steps_html else ''}
<p><a href="/query">Ask another question</a></p>
""",
    )


@app.post("/request")
def submit_request(
    name: str = Form(...),
    email: str = Form(...),
    github_username: str = Form(...),
    note: str = Form(""),
) -> HTMLResponse:
    gh = github_username.strip().lstrip("@")
    if not gh or "@" in gh or " " in gh:
        raise HTTPException(400, "Invalid GitHub username")
    rec = store.create(name=name, email=email, github_username=gh, note=note)
    base = _public_url()
    approve = f"{base}/admin/approve/{rec['id']}?sig={_sign(rec['id'], 'approve')}"
    deny = f"{base}/admin/deny/{rec['id']}?sig={_sign(rec['id'], 'deny')}"
    _slack_notify(
        f"*KB access request* `{rec['id']}`\n"
        f"• Name: {rec['name']}\n"
        f"• Email: {rec['email']}\n"
        f"• GitHub: `{rec['github_username']}`\n"
        f"• Note: {rec['note'] or '—'}\n"
        f"• <{approve}|Approve>\n"
        f"• <{deny}|Deny>"
    )
    return _page(
        "Request submitted",
        f"""
<div class="card">
<p>Thanks, {rec['name']}. Your request <code>{rec['id']}</code> is pending.</p>
<p>You'll get an email at <strong>{rec['email']}</strong> when approved (check spam).</p>
<p>Accept the GitHub invite to <code>James-Server-Admin/kb-gateway</code> when it arrives.</p>
</div>
""",
    )


@app.get("/admin/approve/{request_id}")
def admin_approve(request_id: str, sig: str) -> HTMLResponse:
    if not _verify(request_id, "approve", sig):
        raise HTTPException(403, "Invalid signature")
    rec = store.get(request_id)
    if rec is None:
        raise HTTPException(404, "Request not found")
    if rec["status"] == "approved":
        claim = f"{_public_url()}/claim/{request_id}?code={rec.get('claim_code', '')}"
        return _page("Already approved", f"<p>Already approved. <a href=\"{claim}\">Claim page</a></p>")
    if rec["status"] == "denied":
        raise HTTPException(400, "Request was denied")
    code = store.new_claim_code()
    claim_url = f"{_public_url()}/claim/{request_id}?code={code}"
    try:
        token = provision.provision_access(
            github_username=rec["github_username"],
            email=rec["email"],
            name=rec["name"],
            claim_url=claim_url,
        )
    except Exception as exc:
        return _page("Approval failed", f"<p>Provisioning error: {exc}</p><p>Fix and retry approve link.</p>")
    store.update(
        request_id,
        status="approved",
        claim_code=code,
        api_token=token,
        token_hint=token[:8] + "…",
    )
    return _page(
        "Approved",
        f"""
<div class="card">
<p>Approved <strong>{rec['name']}</strong> (@{rec['github_username']}).</p>
<p>GitHub invite sent · MCP token issued · kb-gateway restarted.</p>
<p>Claim link (also emailed if Resend configured):</p>
<p><a href="{claim_url}">{claim_url}</a></p>
</div>
""",
    )


@app.get("/admin/deny/{request_id}")
def admin_deny(request_id: str, sig: str) -> HTMLResponse:
    if not _verify(request_id, "deny", sig):
        raise HTTPException(403, "Invalid signature")
    rec = store.get(request_id)
    if rec is None:
        raise HTTPException(404, "Request not found")
    store.update(request_id, status="denied")
    return _page("Denied", f"<p>Request <code>{request_id}</code> denied.</p>")


@app.get("/claim/{request_id}", response_class=HTMLResponse)
def claim_access(request_id: str, code: str) -> HTMLResponse:
    rec = store.get(request_id)
    if rec is None or rec.get("status") != "approved":
        raise HTTPException(404, "Not found or not approved")
    if not code or not hmac.compare_digest(rec.get("claim_code", ""), code):
        raise HTTPException(403, "Invalid claim code")
    if rec.get("claimed_at"):
        return _page(
            "Already claimed",
            "<p>This link was already used. Check your email or ask James to rotate your token.</p>",
        )
    token = rec.get("api_token")
    if not token:
        raise HTTPException(500, "Token not on record — contact James")
    from datetime import datetime, timezone

    store.update(request_id, claimed_at=datetime.now(timezone.utc).isoformat())
    mcp_url = os.environ.get("KB_GATEWAY_PUBLIC_URL", "https://kb-mcp.waytie.com").rstrip("/") + "/mcp"
    cfg = json.dumps(
        {
            "mcpServers": {
                "learning-kb": {
                    "url": mcp_url,
                    "headers": {"Authorization": f"Bearer {token}"},
                }
            }
        },
        indent=2,
    )
    return _page(
        "Your MCP access",
        f"""
<div class="card">
<p>Hi {rec['name']}, you're set up.</p>
<ol>
<li>Accept GitHub invite: <a href="https://github.com/James-Server-Admin/kb-gateway">James-Server-Admin/kb-gateway</a></li>
<li>Paste into Cursor → Settings → MCP:</li>
</ol>
<pre>{cfg}</pre>
<p>Or clone the repo and run <code>./scripts/setup-friend-mcp.sh</code> with
<code>export KB_GATEWAY_MCP_TOKEN="…"</code></p>
<p><strong>Save this token now</strong> — this page won't show it again.</p>
</div>
""",
    )
