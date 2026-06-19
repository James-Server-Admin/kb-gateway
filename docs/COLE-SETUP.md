# Cole setup — kb-gateway MCP

> **Canonical guide:** [`docs/CLIENT-SETUP.md`](CLIENT-SETUP.md)  
> This file is kept for backward compatibility with existing links and `COLE_SETUP` GitHub variable.

**Repo:** `James-server/kb-gateway`  
**URL:** `https://kb-mcp.waytie.com/mcp`

```bash
git clone git@github.com:James-server/kb-gateway.git
cd kb-gateway
./scripts/setup-mcp.sh   # or setup-cole-mcp.sh (alias)
cat config/mcp.json
```

Add the `learning-kb` block to Cursor MCP settings. Full steps in [`CLIENT-SETUP.md`](CLIENT-SETUP.md).
