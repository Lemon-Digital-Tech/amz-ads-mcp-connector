#!/usr/bin/env python3
"""
Prints ready-to-paste MCP client configuration for the local auth proxy.

All clients connect to the SAME local endpoint (the proxy); the proxy handles
Amazon auth. Run standalone to re-print at any time:
  python3 scripts/gen-client-config.py [PORT]
Stdlib only.
"""
import sys


def print_all(port: int = 9080):
    url = f"http://127.0.0.1:{port}/mcp"

    print(f"""
All clients point at the local proxy: {url}
(The proxy injects Amazon auth — no tokens go in client config.)

────────────────────────────────────────────────────────────────────
CLAUDE CODE (CLI) — run this command:

  claude mcp add --transport http amazon-ads {url}

  Verify:  claude mcp list   (expect: amazon-ads ... ✓ Connected)

────────────────────────────────────────────────────────────────────
CLAUDE DESKTOP — add to claude_desktop_config.json, then restart the app.
  macOS:   ~/Library/Application Support/Claude/claude_desktop_config.json
  Windows: %APPDATA%\\Claude\\claude_desktop_config.json

  {{
    "mcpServers": {{
      "amazon-ads": {{
        "type": "http",
        "url": "{url}"
      }}
    }}
  }}

────────────────────────────────────────────────────────────────────
CODEX CLI — add to ~/.codex/config.toml

  # If your Codex build supports streamable-HTTP MCP servers:
  [mcp_servers.amazon-ads]
  url = "{url}"

  # If your Codex build is stdio-only, bridge with mcp-remote (needs Node):
  [mcp_servers.amazon-ads]
  command = "npx"
  args = ["-y", "mcp-remote", "{url}"]

────────────────────────────────────────────────────────────────────
CURSOR — add to ~/.cursor/mcp.json (or project .cursor/mcp.json)

  {{
    "mcpServers": {{
      "amazon-ads": {{
        "url": "{url}"
      }}
    }}
  }}

────────────────────────────────────────────────────────────────────
ANY stdio-only MCP client — universal bridge (needs Node.js):

  command: npx
  args:    ["-y", "mcp-remote", "{url}"]
────────────────────────────────────────────────────────────────────
""")


if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 else 9080
    print_all(p)
