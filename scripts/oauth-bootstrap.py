#!/usr/bin/env python3
"""
OAuth authorization-code flow for the Amazon Ads API. Cross-platform.

Opens the browser, captures the auth code on a local callback, exchanges it for
access + refresh tokens, then lists the advertiser profiles. Returns the refresh
token + profile IDs to the caller (setup.py) and also prints them.

Reads CLIENT_ID / CLIENT_SECRET / REGION from <HOME>/config/.env.
Stdlib only.
"""
import http.server
import json
import os
import secrets
import socketserver
import sys
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

HOME = Path(os.environ.get("AMAZON_ADS_MCP_HOME", Path(__file__).resolve().parent.parent))
ENV_PATH = HOME / "config" / ".env"

# LWA endpoints differ slightly by region's Amazon retail domain; auth.amazon.com
# (the .com auth host) works for all regions for the token grant.
AUTH_HOSTS = {
    "NA": "https://www.amazon.com/ap/oa",
    "EU": "https://eu.account.amazon.com/ap/oa",
    "FE": "https://apac.account.amazon.com/ap/oa",
}
TOKEN_URL = "https://api.amazon.com/auth/o2/token"
API_BASE = {
    "NA": "https://advertising-api.amazon.com",
    "EU": "https://advertising-api-eu.amazon.com",
    "FE": "https://advertising-api-fe.amazon.com",
}
REDIRECT_URI = "http://localhost:8000/auth/callback"
SCOPE = "advertising::campaign_management"
STATE = secrets.token_urlsafe(24)
captured = {"code": None, "state": None, "error": None}


def load_env() -> dict:
    env = {}
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/auth/callback":
            self.send_response(404)
            self.end_headers()
            return
        q = urllib.parse.parse_qs(parsed.query)
        captured["code"] = q.get("code", [None])[0]
        captured["state"] = q.get("state", [None])[0]
        captured["error"] = q.get("error", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        msg = ("<h1>Authorization captured.</h1><p>Close this tab and return to the terminal.</p>"
               if not captured["error"] else f"<h1>OAuth error</h1><pre>{captured['error']}</pre>")
        self.wfile.write(msg.encode())


def exchange(code, cid, secret):
    data = urllib.parse.urlencode({
        "grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT_URI,
        "client_id": cid, "client_secret": secret,
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=data,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def fetch_profiles(access_token, cid, region):
    req = urllib.request.Request(
        f"{API_BASE[region]}/v2/profiles",
        headers={"Authorization": f"Bearer {access_token}", "Amazon-Advertising-API-ClientId": cid},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def run() -> dict:
    """Run the flow. Returns {'refresh_token','profile_ids','profiles'}."""
    env = load_env()
    cid = env.get("AMAZON_AD_API_CLIENT_ID", "")
    secret = env.get("AMAZON_AD_API_CLIENT_SECRET", "")
    region = env.get("AMAZON_AD_API_REGION", "NA").upper()
    if not cid or "XXXX" in cid or not secret or "XXXX" in secret:
        raise SystemExit("ERROR: set CLIENT_ID and CLIENT_SECRET in config/.env first.")

    auth_url = AUTH_HOSTS[region] + "?" + urllib.parse.urlencode({
        "client_id": cid, "scope": SCOPE, "response_type": "code",
        "redirect_uri": REDIRECT_URI, "state": STATE,
    })

    httpd = socketserver.TCPServer(("127.0.0.1", 8000), Handler)
    httpd.timeout = 1
    print(f"\nOpening browser to authorize. If it doesn't open, paste:\n  {auth_url}\n")
    webbrowser.open(auth_url)
    print("Waiting for callback (up to 5 min)...")
    for _ in range(300):
        httpd.handle_request()
        if captured["code"] or captured["error"]:
            break
    httpd.server_close()

    if captured["error"]:
        raise SystemExit(f"OAuth denied: {captured['error']}")
    if not captured["code"]:
        raise SystemExit("Timed out waiting for authorization.")
    if captured["state"] != STATE:
        raise SystemExit("State mismatch — aborting (possible CSRF).")

    tokens = exchange(captured["code"], cid, secret)
    refresh_token = tokens["refresh_token"]
    profiles = fetch_profiles(tokens["access_token"], cid, region)
    for p in profiles:
        info = p.get("accountInfo", {})
        print(f"  - {p.get('profileId')}  {p.get('countryCode')}  {info.get('type')}  {info.get('name')}")
    profile_ids = ",".join(str(p.get("profileId")) for p in profiles)
    return {"refresh_token": refresh_token, "profile_ids": profile_ids, "profiles": profiles}


if __name__ == "__main__":
    out = run()
    print("\nrefresh_token:", out["refresh_token"][:20] + "...")
    print("profile_ids:", out["profile_ids"])
    sys.exit(0)
