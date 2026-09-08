#!/usr/bin/env python3
"""
HackerOne MCP — Token Status Detector
Checks if HACKERONE_API_TOKEN is properly configured where Hermes can read it.
Reports what's missing and exactly where to paste the token.

Usage:
  python h1_token_status.py
"""

import os
import sys
from pathlib import Path

HERMES_HOME = Path(os.environ.get("HERMES_HOME") or Path.home() / ".hermes")
PROJECT_ENV_PATHS = [
    Path.cwd() / ".env",
    Path.cwd().parent / ".env",
    HERMES_HOME.parent / ".env",  # OneDrive/Desktop/bionic_daughter_agent/.env
]
HERMES_ENV_PATH = HERMES_HOME / ".env"


def find_token_in_file(path: Path) -> str | None:
    """Return token value if HACKERONE_API_TOKEN is set in a .env file."""
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.strip() == "HACKERONE_API_TOKEN":
            return value.strip().strip('"').strip("'")
    return None


def main():
    print("=" * 70)
    print(" HACKERONE MCP — TOKEN STATUS CHECK")
    print("=" * 70)
    print()

    # 1. Check shell env
    shell_token = os.environ.get("HACKERONE_API_TOKEN", "")
    if shell_token:
        print(f"[1/4] Shell environment:  SET (length {len(shell_token)})")
    else:
        print("[1/4] Shell environment:  NOT SET")
    print()

    # 2. Check ~/.hermes/.env (where Hermes ACTUALLY reads)
    hermes_token = find_token_in_file(HERMES_ENV_PATH)
    if hermes_token:
        print(f"[2/4] {HERMES_ENV_PATH}:")
        print(f"      SET (length {len(hermes_token)}) — Hermes will find this")
    else:
        print(f"[2/4] {HERMES_ENV_PATH}:")
        print(f"      NOT SET — this is the file Hermes reads from")
    print()

    # 3. Check common project .env locations (informational only)
    print("[3/4] Other .env files (informational — Hermes does NOT read these):")
    found_in_others = False
    for p in PROJECT_ENV_PATHS:
        t = find_token_in_file(p)
        if t:
            found_in_others = True
            print(f"      FOUND in {p} (length {len(t)})")
        elif p.exists():
            print(f"      empty/missing key in {p}")
    if not found_in_others:
        print("      (token not in any project .env — must be in ~/.hermes/.env)")
    print()

    # 4. Verdict
    print("[4/4] VERDICT:")
    print()
    if hermes_token:
        print("  STATUS: OK — HackerOne MCP will work when Hermes boots")
        print()
        # 5. Optional: validate token format (HackerOne tokens are base64 of uuid:hash)
        if len(hermes_token) >= 40:
            print(f"  Token length {len(hermes_token)} chars — looks plausible")
        else:
            print(f"  WARNING: token only {len(hermes_token)} chars — may be incomplete")
    else:
        print("  STATUS: NOT CONFIGURED — HackerOne MCP will error on every tool call")
        print()
        print("  TO FIX:")
        print(f"  1. Get your HackerOne API token:")
        print(f"     https://hackerone.com/settings/api_tokens")
        print(f"  2. Add this line to {HERMES_ENV_PATH}:")
        print()
        print(f'     HACKERONE_API_TOKEN=your_token_here')
        print()
        print(f"  3. Save the file. Restart Hermes (or the gateway).")
        print(f"     The token will be picked up on the next MCP server boot.")
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()