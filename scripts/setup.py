#!/usr/bin/env python3
"""
One-command setup wizard for the Amazon Ads MCP connector. Cross-platform.

What it does:
  1. Resolves a per-user runtime home (macOS/Linux: ~/.config/amazon-ads-mcp,
     Windows: %LOCALAPPDATA%\\amazon-ads-mcp) — a TCC/permission-safe location.
  2. Copies the proxy there and writes config/.env.
  3. Collects the shared company Client ID / Client Secret (env vars, flags, or
     prompt) and the region.
  4. Runs the personal OAuth flow to obtain THIS user's refresh token + profiles.
  5. Installs the keep-alive service for the OS (launchd / systemd / Task Scheduler).
  6. Prints ready-to-paste MCP client config (Claude Desktop, Claude Code, Codex, Cursor).

Usage:
  python3 scripts/setup.py
  AMAZON_AD_API_CLIENT_ID=... AMAZON_AD_API_CLIENT_SECRET=... python3 scripts/setup.py
  python3 scripts/setup.py --region EU --port 9080
Stdlib only.
"""
import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parent.parent
IS_WIN = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"


def runtime_home() -> Path:
    if IS_WIN:
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "amazon-ads-mcp"


def prompt(label, default="", secret=False):
    val = os.environ.get(f"AMAZON_AD_API_{label.upper()}", "")
    if val:
        return val
    suffix = f" [{default}]" if default else ""
    if secret:
        import getpass
        v = getpass.getpass(f"{label}{suffix}: ").strip()
    else:
        v = input(f"{label}{suffix}: ").strip()
    return v or default


def write_env(home: Path, client_id, client_secret, region, refresh_token, profile_ids, port):
    (home / "config").mkdir(parents=True, exist_ok=True)
    env_path = home / "config" / ".env"
    env_path.write_text(
        "# Amazon Ads MCP connector — per-user credentials. DO NOT SHARE / COMMIT.\n"
        f"AMAZON_AD_API_CLIENT_ID=\"{client_id}\"\n"
        f"AMAZON_AD_API_CLIENT_SECRET=\"{client_secret}\"\n"
        f"AMAZON_AD_API_REFRESH_TOKEN=\"{refresh_token}\"\n"
        f"AMAZON_AD_API_REGION=\"{region}\"\n"
        f"AMAZON_AD_API_PROFILE_IDS=\"{profile_ids}\"\n"
        "# Pin a single profile (Fixed mode) by setting the line below; leave blank for Dynamic.\n"
        "AMAZON_AD_API_FIXED_PROFILE_ID=\"\"\n"
        f"AMAZON_ADS_MCP_PORT=\"{port}\"\n"
    )
    try:
        os.chmod(env_path, 0o600)
    except Exception:
        pass
    return env_path


def install_service(home: Path, port: int):
    proxy = home / "proxy" / "mcp-auth-proxy.py"
    py = shutil.which("python3") or shutil.which("python") or sys.executable
    if IS_MAC:
        return _install_launchd(home, proxy, py)
    if IS_WIN:
        return _install_windows(home, proxy, py)
    return _install_systemd(home, proxy, py)


def _install_launchd(home, proxy, py):
    label = "com.lemondigital.amazon-ads-mcp-proxy"
    plist = Path.home() / "Library/LaunchAgents" / f"{label}.plist"
    plist.parent.mkdir(parents=True, exist_ok=True)
    plist.write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>{label}</string>
  <key>ProgramArguments</key><array><string>{py}</string><string>{proxy}</string></array>
  <key>EnvironmentVariables</key><dict><key>AMAZON_ADS_MCP_HOME</key><string>{home}</string></dict>
  <key>RunAtLoad</key><true/><key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>{home}/proxy.log</string>
  <key>StandardErrorPath</key><string>{home}/proxy.log</string>
</dict></plist>
""")
    subprocess.run(["launchctl", "unload", str(plist)], capture_output=True)
    subprocess.run(["launchctl", "load", str(plist)], capture_output=True)
    return f"launchd agent installed: {plist}"


def _install_systemd(home, proxy, py):
    unit_dir = Path.home() / ".config/systemd/user"
    unit_dir.mkdir(parents=True, exist_ok=True)
    unit = unit_dir / "amazon-ads-mcp-proxy.service"
    unit.write_text(f"""[Unit]
Description=Amazon Ads MCP auth proxy
After=network-online.target

[Service]
Environment=AMAZON_ADS_MCP_HOME={home}
ExecStart={py} {proxy}
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
""")
    subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
    subprocess.run(["systemctl", "--user", "enable", "--now", "amazon-ads-mcp-proxy"], capture_output=True)
    return f"systemd user service installed: {unit} (enable lingering: loginctl enable-linger $USER)"


def _install_windows(home, proxy, py):
    task = "AmazonAdsMcpProxy"
    # Run hidden at logon and keep alive via Task Scheduler.
    cmd = (f'$a = New-ScheduledTaskAction -Execute "{py}" -Argument "{proxy}"; '
           f'$t = New-ScheduledTaskTrigger -AtLogOn; '
           f'$s = New-ScheduledTaskSettingsSet -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1); '
           f'$env:AMAZON_ADS_MCP_HOME = "{home}"; '
           f'Register-ScheduledTask -TaskName "{task}" -Action $a -Trigger $t -Settings $s -Force; '
           f'Start-ScheduledTask -TaskName "{task}"')
    ps1 = home / "install-service.ps1"
    ps1.write_text(f'$env:AMAZON_ADS_MCP_HOME = "{home}"\n{cmd}\n')
    subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-Command", cmd], capture_output=True)
    return f"Windows scheduled task '{task}' registered (script: {ps1})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default=os.environ.get("AMAZON_AD_API_REGION", ""))
    ap.add_argument("--port", default=os.environ.get("AMAZON_ADS_MCP_PORT", "9080"))
    ap.add_argument("--no-service", action="store_true", help="skip keep-alive service install")
    args = ap.parse_args()

    print("=== Amazon Ads MCP connector — setup ===\n")
    home = runtime_home()
    (home / "proxy").mkdir(parents=True, exist_ok=True)
    shutil.copy2(PKG_ROOT / "proxy" / "mcp-auth-proxy.py", home / "proxy" / "mcp-auth-proxy.py")
    os.environ["AMAZON_ADS_MCP_HOME"] = str(home)

    client_id = prompt("CLIENT_ID")
    client_secret = prompt("CLIENT_SECRET", secret=True)
    region = (args.region or prompt("REGION", default="NA")).upper()
    if region not in {"NA", "EU", "FE"}:
        sys.exit("Region must be NA, EU, or FE.")

    # Pre-write env so oauth-bootstrap can read client id/secret/region.
    write_env(home, client_id, client_secret, region, "", "", args.port)

    print("\n--- Authorizing your Amazon account (personal refresh token) ---")
    sys.path.insert(0, str(PKG_ROOT / "scripts"))
    import importlib.util
    spec = importlib.util.spec_from_file_location("oauth_bootstrap", PKG_ROOT / "scripts" / "oauth-bootstrap.py")
    ob = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ob)
    result = ob.run()

    env_path = write_env(home, client_id, client_secret, region,
                         result["refresh_token"], result["profile_ids"], args.port)
    print(f"\n✓ Credentials saved: {env_path}")

    if not args.no_service:
        print("\n--- Installing keep-alive service ---")
        print("✓ " + install_service(home, int(args.port)))

    print("\n--- MCP client configuration ---")
    spec2 = importlib.util.spec_from_file_location("gen_client_config", PKG_ROOT / "scripts" / "gen-client-config.py")
    gcc = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(gcc)
    gcc.print_all(int(args.port))

    print("\n=== Setup complete. Restart your AI client to load the server. ===")


if __name__ == "__main__":
    main()
