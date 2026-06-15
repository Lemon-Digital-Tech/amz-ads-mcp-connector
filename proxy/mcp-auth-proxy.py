#!/usr/bin/env python3
"""
Local auth proxy for the Amazon Ads MCP Server. Cross-platform (macOS/Windows/Linux).

Why this exists:
  Amazon's MCP endpoint authenticates with a short-lived LWA access token
  (TTL ~1h). MCP clients (Claude Desktop / Claude Code / Codex / Cursor) only
  support STATIC headers, so a raw config would break every hour. This proxy
  holds the long-lived refresh token, mints a fresh access token on demand, and
  injects the required headers transparently — the client config never changes
  and never needs a restart for auth.

  Claude/Codex ──http──> 127.0.0.1:9080/mcp ──https+auth──> advertising-ai.amazon.com/mcp

Config: reads <HOME>/config/.env where <HOME> is:
  - $AMAZON_ADS_MCP_HOME if set, else
  - the parent directory of this script's folder.

Stdlib only — no pip install.
"""
import http.server
import json
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HOME = Path(os.environ.get("AMAZON_ADS_MCP_HOME", Path(__file__).resolve().parent.parent))
ENV_PATH = HOME / "config" / ".env"

LISTEN_HOST = os.environ.get("AMAZON_ADS_MCP_HOST", "127.0.0.1")
LISTEN_PORT = int(os.environ.get("AMAZON_ADS_MCP_PORT", "9080"))
TOKEN_URL = "https://api.amazon.com/auth/o2/token"
REFRESH_SKEW = 300  # refresh this many seconds before expiry

REGION_ENDPOINTS = {
    "NA": "https://advertising-ai.amazon.com/mcp",
    "EU": "https://advertising-ai-eu.amazon.com/mcp",
    "FE": "https://advertising-ai-fe.amazon.com/mcp",
}


def load_env() -> dict:
    if not ENV_PATH.exists():
        raise SystemExit(f"ERROR: {ENV_PATH} not found. Run the setup wizard first.")
    env = {}
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


class TokenManager:
    def __init__(self, env: dict):
        self._client_id = env["AMAZON_AD_API_CLIENT_ID"]
        self._client_secret = env["AMAZON_AD_API_CLIENT_SECRET"]
        self._refresh_token = env["AMAZON_AD_API_REFRESH_TOKEN"]
        self._access_token = None
        self._expires_at = 0.0
        self._lock = threading.Lock()

    @property
    def client_id(self) -> str:
        return self._client_id

    def get_access_token(self) -> str:
        with self._lock:
            if self._access_token and time.monotonic() < self._expires_at - REFRESH_SKEW:
                return self._access_token
            payload = urllib.parse.urlencode({
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            }).encode()
            req = urllib.request.Request(
                TOKEN_URL, data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                tok = json.loads(r.read())
            self._access_token = tok["access_token"]
            self._expires_at = time.monotonic() + float(tok.get("expires_in", 3600))
            print(f"[proxy] refreshed access token (expires_in={tok.get('expires_in')}s)", flush=True)
            return self._access_token


STRIP_REQUEST_HEADERS = {
    "host", "authorization", "amazon-ads-clientid", "content-length",
    "connection", "amazon-ads-ai-account-selection-mode", "amazon-advertising-api-scope",
}
STRIP_RESPONSE_HEADERS = {"content-length", "connection", "transfer-encoding"}


class ProxyHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    tokens: TokenManager = None
    upstream: str = ""
    fixed_profile_id: str = ""

    def log_message(self, *_):
        pass

    def _proxy(self, method: str):
        length = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(length) if length else b""

        out = {}
        for k, v in self.headers.items():
            if k.lower() not in STRIP_REQUEST_HEADERS:
                out[k] = v
        out["Authorization"] = f"Bearer {self.tokens.get_access_token()}"
        out["Amazon-Ads-ClientId"] = self.tokens.client_id
        out.setdefault("Accept", "application/json, text/event-stream")
        if self.fixed_profile_id:
            out["Amazon-Ads-AI-Account-Selection-Mode"] = "FIXED"
            out["Amazon-Advertising-API-Scope"] = self.fixed_profile_id

        req = urllib.request.Request(self.upstream, data=body or None, method=method, headers=out)
        try:
            resp = urllib.request.urlopen(req, timeout=120)
        except urllib.error.HTTPError as e:
            resp = e
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"proxy upstream failure: {e}"}).encode())
            return

        self.send_response(resp.status)
        for k, v in resp.headers.items():
            if k.lower() not in STRIP_RESPONSE_HEADERS:
                self.send_header(k, v)
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                self.wfile.write(chunk)
                self.wfile.flush()
        except Exception:
            pass

    def do_POST(self):
        self._proxy("POST")

    def do_GET(self):
        self._proxy("GET")

    def do_DELETE(self):
        self._proxy("DELETE")


def main():
    env = load_env()
    region = env.get("AMAZON_AD_API_REGION", "NA").upper()
    upstream = REGION_ENDPOINTS.get(region)
    if not upstream:
        raise SystemExit(f"ERROR: unknown region '{region}'. Use NA, EU, or FE.")

    ProxyHandler.tokens = TokenManager(env)
    ProxyHandler.upstream = upstream
    ProxyHandler.fixed_profile_id = env.get("AMAZON_AD_API_FIXED_PROFILE_ID", "").strip()
    ProxyHandler.tokens.get_access_token()  # fail fast on bad creds

    server = http.server.ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), ProxyHandler)
    mode = f"FIXED ({ProxyHandler.fixed_profile_id})" if ProxyHandler.fixed_profile_id else "DYNAMIC"
    print(f"[proxy] listening http://{LISTEN_HOST}:{LISTEN_PORT}/mcp", flush=True)
    print(f"[proxy] region={region} upstream={upstream} account-context={mode}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
