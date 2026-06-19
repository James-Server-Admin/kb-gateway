# Deployment — remote access for agents everywhere

Corpus guidance: `mcp-server-as-internal-boundary.md` — stdio for local single-user; **HTTP + token auth** for remote multi-agent use.

## Recommended stack

```
Remote agents (Cursor cloud, Paperclip, Cole laptop, GitHub Actions self-hosted)
        │
        ▼
  Tailscale or Cloudflare Tunnel + Access
        │
        ▼
  kb-gateway (streamable-http on Tailscale IP :8790)
        │
        ├── langchain-course runtime (router + RAG)
        ├── Pinecone `learning` (cloud, keys server-side only)
        └── Neo4j `learning-kg-neo4j` (localhost:7689, never public)
```

## 1. Systemd service (server)

```bash
# After clone to /mnt/blockstorage/business/Keyflo_AI/08_Development/kb-gateway
sudo cp deploy/kb-gateway.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now kb-gateway
```

Service runs as root with `EnvironmentFile=/mnt/blockstorage/env/global.env` plus token file.

## 2. Secrets

Register via NEW-SECRET-INTAKE:

| Secret | Scope | Consumer |
|---|---|---|
| `KB_GATEWAY_API_TOKEN` | `/mnt/blockstorage/env/kb-gateway.env` | Remote MCP clients (systemd only) |
| Existing `LEARNING_*` | global.env | Server runtime only |

Never give remote agents Pinecone or Neo4j credentials — they use MCP tools only.

## 3. Exposure options

| Method | When | Notes |
|---|---|---|
| **Tailscale IP (direct)** | **Default — already running** | Gateway on server at `100.122.28.113:8790`. Bearer token required. Anyone on tailnet. |
| **Tailscale Serve (HTTPS)** | Optional polish | Enable on tailnet; `sudo tailscale serve --bg http://127.0.0.1:8790` if you want HTTPS + MagicDNS |
| **SSH stdio** | Local Cursor → server | No HTTP; see [`client-setup.md`](client-setup.md) |
| **Cloudflare Tunnel** | Public HTTPS with Access | Zero trust; no open ports |

Gateway binds the server's **Tailscale IP** (`KB_GATEWAY_HOST=100.122.28.113`) — reachable only on your tailnet, not the public internet.

## 4. Auth

- Set `KB_GATEWAY_API_TOKEN` (long random)
- Set `KB_GATEWAY_PUBLIC_URL` to the HTTPS URL clients use (issuer for MCP auth)
- Clients send `Authorization: Bearer <token>`

Dev on localhost only: `--no-auth` flag (never in production).

## 5. Health check

```bash
curl -s -H "Authorization: Bearer $KB_GATEWAY_API_TOKEN" \
  https://your-host/mcp  # MCP handshake via client
scripts/smoke_test.sh
```

## 6. Future: per-business KB manifests

Follow `langchain-course/KB-ORGANIZATION.md` — each business gets dedicated Pinecone index + MCP token. This gateway starts with `learning` (personal-accumulation, cross-business read OK).
