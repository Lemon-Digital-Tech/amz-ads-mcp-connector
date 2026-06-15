# Amazon Ads MCP Connector

Connect any MCP-compatible AI client (Claude Desktop, Claude Code, Codex, Cursor)
to the **official Amazon Ads MCP Server** — with automatic token refresh so it
never breaks mid-session.

Each team member runs one setup command, authorizes their own Amazon account, and
gets a working connection. No coding required.

> 🇻🇳 **Người không rành kỹ thuật?** Đọc bản hướng dẫn từng bước bằng tiếng Việt:
> [docs/HUONG-DAN-SU-DUNG.md](docs/HUONG-DAN-SU-DUNG.md)

---

## How it works

```
Your AI client ──http──> 127.0.0.1:9080/mcp ──https+auth──> advertising-ai.amazon.com/mcp
                          (local auth proxy)   auto-refreshes        (Amazon, official)
                                               the access token
```

Amazon's MCP endpoint uses a short-lived access token (~1h). AI clients only
support static config, so a raw setup would die every hour. This connector runs a
tiny **local proxy** that holds your refresh token and mints fresh access tokens
automatically — your client config never changes and never needs re-auth.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.10+ | macOS/Linux: preinstalled or `brew install python`. Windows: python.org (check "Add to PATH"). |
| Amazon Ads API access | Your company's LWA app must be approved for the Ads API. |
| Company Client ID + Secret | Shared by your team lead (same for everyone). |
| Your own Amazon login | You authorize your personal account → your own refresh token. |
| (Codex/stdio clients only) Node.js | For the `npx mcp-remote` bridge. |

---

## Quick start (every team member)

```bash
git clone <this-repo-url> amazon-ads-mcp-connector
cd amazon-ads-mcp-connector
python3 scripts/setup.py
```

The wizard will:
1. Ask for the **Client ID / Client Secret** (from your team lead) and **region** (NA/EU/FE).
2. Open your browser to **authorize your Amazon account** → click Allow.
3. List your advertiser profiles and save your personal refresh token.
4. Install a **background service** that keeps the proxy running (auto-start on login).
5. Print the **exact config** to paste into your AI client.

> Windows: run the same command in PowerShell. Use `python` if `python3` isn't found.

Then **restart your AI client** and ask:

```
List the Amazon advertiser accounts I have access to
```

---

## Client configuration

The setup wizard prints this for you, but to re-print anytime:

```bash
python3 scripts/gen-client-config.py
```

- **Claude Code:** `claude mcp add --transport http amazon-ads http://127.0.0.1:9080/mcp`
- **Claude Desktop / Cursor / Codex:** see `docs/clients.md` for the JSON/TOML snippet.
- **stdio-only clients:** bridge with `npx -y mcp-remote http://127.0.0.1:9080/mcp`.

---

## Account context modes

- **Dynamic (default):** the AI asks which advertiser account to use, per task —
  best when you manage many profiles/marketplaces. Multi-marketplace: pick the
  marketplace first, then the profile.
- **Fixed:** pin one profile. Set `AMAZON_AD_API_FIXED_PROFILE_ID` in your runtime
  `.env` (path printed at the end of setup), then restart the proxy.

---

## Safety (recommended for first 2 weeks)

The server exposes **write** tools (create/pause/delete campaigns, adjust bids).
Amazon recommends starting **read-only**. To disable risky tools, see
`docs/clients.md` → "Disabling write tools".

---

## Managing the proxy

| Action | macOS | Windows |
|---|---|---|
| Logs | `~/.config/amazon-ads-mcp/proxy.log` | `%LOCALAPPDATA%\amazon-ads-mcp\proxy.log` |
| Restart | `launchctl kickstart -k gui/$(id -u)/com.lemondigital.amazon-ads-mcp-proxy` | `Restart-ScheduledTask -TaskName AmazonAdsMcpProxy` |
| Stop | `launchctl unload ~/Library/LaunchAgents/com.lemondigital.amazon-ads-mcp-proxy.plist` | `Stop-ScheduledTask -TaskName AmazonAdsMcpProxy` |

Linux uses systemd: `systemctl --user restart amazon-ads-mcp-proxy`.

---

## Troubleshooting

See `docs/troubleshooting.md`. Common ones:
- **"Failed to connect" in client** → proxy not running; check the log, restart it.
- **401 / token errors** → refresh token expired/revoked; re-run `python3 scripts/setup.py`.
- **Port 9080 in use** → re-run setup with `--port 9091` and update your client config.

---

## What NOT to commit

`.env`, `*.log`, `*.access_token` are gitignored. Your refresh token is personal —
never share it or paste it into chat.
