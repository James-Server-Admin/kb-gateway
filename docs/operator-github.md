# Operator: publish to KeyFlo-ai GitHub

The agent token (`GITHUB_AGENT_TOKEN`) cannot `CreateRepository` in KeyFlo-ai. A human with org admin must create the repo once, then push.

## One-time (James or Cole with org admin)

1. Create empty repo: **https://github.com/organizations/KeyFlo-ai/repositories/new**
   - Name: `kb-gateway`
   - Public
   - Do not add README (local repo has history)

2. Push from server:

```bash
cd /mnt/blockstorage/business/Keyflo_AI/08_Development/kb-gateway
git remote add origin git@github.com:KeyFlo-ai/kb-gateway.git 2>/dev/null || \
  git remote set-url origin git@github.com:KeyFlo-ai/kb-gateway.git
git push -u origin main
```

3. Add Cole as collaborator (read or maintain).

4. Issue Cole a **KB_GATEWAY_API_TOKEN** (not Pinecone/Neo4j keys). Token lives in `/mnt/blockstorage/env/kb-gateway.env` on the server — share via 1Password or Tailscale-only channel.

## Verify

- README + AGENTS.md visible on GitHub
- `docs/client-setup.md` linked for Cole's Cursor MCP config
