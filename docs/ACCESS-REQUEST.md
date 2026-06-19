# Access request portal — link + approve

**Public link to share:** https://kb-access.waytie.com

Friends submit name, email, and GitHub username. You get a Slack message with **Approve** / **Deny** links. Approval automatically:

1. Invites them to `James-Server-Admin/kb-gateway` (read)
2. Issues an MCP bearer token
3. Restarts `kb-gateway` to pick up the token
4. Emails them a claim link (if Resend is configured)
5. Shows their token + Cursor MCP JSON on the claim page (one time)

---

## What you do

1. **Share the link:** https://kb-access.waytie.com  
2. **Watch Slack** (paperclip-notifier webhook) for incoming requests  
3. **Click Approve** — done

No manual token copy, no hunting for GitHub usernames.

---

## What friends do

1. Open https://kb-access.waytie.com  
2. Fill the form (name, email, GitHub username)  
3. Wait for approval email (or link from you)  
4. Open claim link → copy MCP config into Cursor  
5. Accept GitHub repo invite  

Setup guide after claim: [`FRIEND-SETUP.md`](FRIEND-SETUP.md)

---

## Operator deploy (once)

```bash
chmod +x scripts/setup-kb-access-portal.sh
sudo ./scripts/setup-kb-access-portal.sh
```

Creates approve HMAC secret, DNS `kb-access.waytie.com`, nginx, certbot, `kb-access.service`.

**Service:** `systemctl status kb-access`  
**Pending requests:** `/mnt/blockstorage/private/kb-access-requests/*.json` (mode 700, contains tokens after approve)

---

## GitHub variable

`ACCESS_REQUEST_URL` = `https://kb-access.waytie.com` (sync via `scripts/sync-gh-variables.sh`)

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| No Slack notification | Check `paperclip-notifier.env` → `SLACK_WEBHOOK_URL`; `journalctl -u kb-access` |
| Approve fails on GitHub | `gh auth status` as okrealai; user must exist on GitHub |
| No approval email | Resend optional — forward claim link from approve confirmation page |
| 401 after claim | `systemctl restart kb-gateway`; verify token in `learning-kb-api-keys.txt` |
