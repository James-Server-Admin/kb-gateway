"""Bearer token verification for HTTP MCP (static API token)."""

from __future__ import annotations

from mcp.server.auth.provider import AccessToken

from .config import api_token, api_tokens, token_client_map
from .context import set_client


class StaticTokenVerifier:
    """Verify bearer tokens against KB_GATEWAY_API_TOKEN and optional keys file."""

    def __init__(self, expected: frozenset[str] | None = None) -> None:
        self._expected = expected if expected is not None else api_tokens()
        self._clients = token_client_map()

    async def verify_token(self, token: str) -> AccessToken | None:
        if not self._expected or token not in self._expected:
            return None
        client = self._clients.get(token, "unknown")
        set_client(client)
        return AccessToken(
            token=token,
            client_id="kb-gateway",
            scopes=["learning:read"],
            subject=client,
        )
