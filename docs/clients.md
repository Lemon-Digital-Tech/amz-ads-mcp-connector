# Per-client configuration

All clients connect to the **local proxy** at `http://127.0.0.1:9080/mcp`.
The proxy handles Amazon authentication — **no tokens go into client config**.

If you changed the port during setup, replace `9080` everywhere below.

---

## Claude Code (CLI)

```bash
claude mcp add --transport http amazon-ads http://127.0.0.1:9080/mcp
claude mcp list   # expect: amazon-ads ... ✓ Connected
```

Remove: `claude mcp remove amazon-ads`

---

## Claude Desktop

Edit the config file, then fully quit (Cmd+Q / exit tray) and reopen:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "amazon-ads": {
      "type": "http",
      "url": "http://127.0.0.1:9080/mcp"
    }
  }
}
```

If you already have other servers, add `amazon-ads` inside the existing
`mcpServers` object — don't create a second one.

---

## Codex CLI

Edit `~/.codex/config.toml`.

```toml
# Preferred — if your Codex build supports streamable-HTTP MCP servers:
[mcp_servers.amazon-ads]
url = "http://127.0.0.1:9080/mcp"
```

```toml
# Fallback — stdio-only builds, bridge with mcp-remote (needs Node.js):
[mcp_servers.amazon-ads]
command = "npx"
args = ["-y", "mcp-remote", "http://127.0.0.1:9080/mcp"]
```

---

## Cursor

Edit `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (per project):

```json
{
  "mcpServers": {
    "amazon-ads": {
      "url": "http://127.0.0.1:9080/mcp"
    }
  }
}
```

---

## Any stdio-only MCP client

Universal bridge (requires Node.js):

```
command: npx
args:    ["-y", "mcp-remote", "http://127.0.0.1:9080/mcp"]
```

---

## Disabling write tools (safety)

To prevent destructive actions during evaluation, filter tools at the client.

**Claude Code** (per-project `.mcp.json` or via flags) and most clients honor a
`disabledTools` / tool-permission list. Example tool names to block:

```
campaign_management-delete_campaign
campaign_management-delete_ad
campaign_management-delete_ad_association
campaign_management-update_campaign_state
reporting-delete_report
```

For Codex, set tool approval to "ask" so every write requires confirmation.
For Claude clients, keep "Ask before running" enabled for this server.

You can also restrict at the proxy by pinning Fixed mode to a single low-spend
test profile (`AMAZON_AD_API_FIXED_PROFILE_ID`) during the trial period.
