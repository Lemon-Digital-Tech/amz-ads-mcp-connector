# Troubleshooting

## Client shows "Failed to connect" / server not available

The proxy isn't running or isn't reachable.

1. Check the log:
   - macOS: `~/.config/amazon-ads-mcp/proxy.log`
   - Windows: `%LOCALAPPDATA%\amazon-ads-mcp\proxy.log`
2. Test it directly:
   ```bash
   curl -sS -X POST http://127.0.0.1:9080/mcp \
     -H "Accept: application/json, text/event-stream" \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}'
   ```
   Expect a JSON result naming "Amazon Ads MCP Server".
3. Restart the proxy (see README → Managing the proxy).

## 401 / "client initialization failed" / token errors

Your refresh token expired or was revoked (password change, app revoke, or long
inactivity). Re-run:

```bash
python3 scripts/setup.py
```

## Port 9080 already in use

Another app holds the port. Re-run setup on a different port and update your
client config to match:

```bash
python3 scripts/setup.py --port 9091
```

## Browser didn't open during setup

Copy the URL printed in the terminal and paste it into your browser manually.
After approving, you'll be redirected to `http://localhost:8000/auth/callback`
and the terminal continues.

## "redirect_uri mismatch" during authorization

The company LWA app must allow `http://localhost:8000/auth/callback` in its
**Allowed Return URLs** (team lead configures this once in the Amazon Developer
console → Login with Amazon → the app → Web Settings).

## No profiles returned after authorization

The Amazon account you authorized has no advertiser access in the chosen region,
or you picked the wrong region. Confirm the account manages live Ads accounts and
re-run with the correct `--region` (NA / EU / FE).

## macOS: launchd "Operation not permitted"

Don't place the runtime under `~/Documents`, `~/Desktop`, or `~/Downloads`
(macroOS TCC blocks background processes there). The wizard uses
`~/.config/amazon-ads-mcp` which is safe — don't move it.

## Windows: scheduled task didn't start

Open Task Scheduler, find `AmazonAdsMcpProxy`, and check Last Run Result. You can
also run the proxy manually to see errors:

```powershell
$env:AMAZON_ADS_MCP_HOME="$env:LOCALAPPDATA\amazon-ads-mcp"
python "$env:LOCALAPPDATA\amazon-ads-mcp\proxy\mcp-auth-proxy.py"
```

## Verifying which account a tool will act on

In Dynamic mode, ask: "Which advertiser accounts do I have access to?" then
specify the profile in your request. In Fixed mode, the proxy always uses
`AMAZON_AD_API_FIXED_PROFILE_ID`.
