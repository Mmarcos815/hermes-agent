#!/usr/bin/env python3
"""
Red Team MCP Server
===================
Wraps 5 OWASP API exploitation tools as MCP tools over stdio transport.

Tools:
  1. bola_exploit      — Scan target for BOLA (Broken Object Level Authorization)
  2. jwt_forgery       — Generate and test JWT alg=none forgeries
  3. oauth_test        — Test OAuth redirect_uri and state parameter
  4. graphql_scan      — Test GraphQL introspection and batch queries
  5. ssrf_probe        — Test SSRF vectors against target

Each tool delegates to the corresponding script in learning/03_api_exploitation/.
"""
import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SERVER_NAME = "redteam-mcp"
SERVER_VERSION = "1.0.0"

# Resolve the exploit scripts directory relative to this file
SCRIPT_DIR = Path(__file__).resolve().parent.parent / "learning" / "03_api_exploitation"

# Map tool names to script files
SCRIPTS = {
    "bola_exploit": SCRIPT_DIR / "01_bola_exploit.py",
    "jwt_forgery": SCRIPT_DIR / "02_jwt_attack.py",
    "oauth_test": SCRIPT_DIR / "03_oauth_exploit.py",
    "graphql_scan": SCRIPT_DIR / "04_graphql_exploit.py",
    "ssrf_probe": SCRIPT_DIR / "05_ssrf_tool.py",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_script(script_path: Path, env_overrides: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Run a Python script as a subprocess and capture JSON output."""
    if not script_path.exists():
        return {"error": f"Script not found: {script_path}"}

    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
            cwd=str(SCRIPT_DIR.parent.parent),
        )
        output = result.stdout.strip()
        # Try to parse the last JSON object from stdout
        if output:
            lines = output.splitlines()
            for line in reversed(lines):
                line = line.strip()
                if line.startswith("{") or line.startswith("["):
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        continue
            # If no JSON found, return raw output
            return {"output": output[-2000:], "exit_code": result.returncode}
        return {"output": "", "exit_code": result.returncode, "stderr": result.stderr.strip()[-500:]}
    except subprocess.TimeoutExpired:
        return {"error": "Script timed out after 60s"}
    except Exception as e:
        return {"error": str(e)}


def _validate_target(target: str) -> str:
    """Validate and normalize a target URL."""
    if not target:
        return "http://localhost:5016"
    target = target.strip()
    if not target.startswith(("http://", "https://")):
        target = "http://" + target
    return target.rstrip("/")


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

app = FastMCP(SERVER_NAME)


@app.tool(
    name="bola_exploit",
    description=(
        "Scan a target API for BOLA (Broken Object Level Authorization) vulnerabilities. "
        "Attempts to access other users' data by manipulating object IDs in API requests. "
        "Tests /api/Users/{id}, /api/BasketItems/{id}, /api/Orders/{id}, /api/Addresses/{id}."
    ),
)
def bola_exploit(target: str = "http://localhost:5016") -> str:
    """
    Scan target for BOLA vulnerabilities.

    Args:
        target: Base URL of the target API (default: http://localhost:5016)
    """
    target = _validate_target(target)
    env = {"BOLA_TARGET": target}
    result = _run_script(SCRIPTS["bola_exploit"], env_overrides=env)
    return json.dumps(result, indent=2)


@app.tool(
    name="jwt_forgery",
    description=(
        "Generate and test JWT alg=none forgeries against a target. "
        "Tests multiple variants: alg=none with empty signature, alg=None, alg=NONE, "
        "alg=none with original signature, and alg=empty string."
    ),
)
def jwt_forgery(target: str = "http://localhost:5016") -> str:
    """
    Generate and test JWT alg=none forgeries.

    Args:
        target: Base URL of the target API (default: http://localhost:5016)
    """
    target = _validate_target(target)
    env = {"JWT_TARGET": target}
    result = _run_script(SCRIPTS["jwt_forgery"], env_overrides=env)
    return json.dumps(result, indent=2)


@app.tool(
    name="oauth_test",
    description=(
        "Test OAuth/OpenID Connect implementation for misconfigurations. "
        "Checks: redirect_uri open redirect, state parameter CSRF, scope escalation, "
        "PKCE bypass, user enumeration, and admin endpoint exposure."
    ),
)
def oauth_test(target: str = "http://localhost:5016") -> str:
    """
    Test OAuth redirect_uri and state parameter.

    Args:
        target: Base URL of the target API (default: http://localhost:5016)
    """
    target = _validate_target(target)
    env = {"OAUTH_TARGET": target}
    result = _run_script(SCRIPTS["oauth_test"], env_overrides=env)
    return json.dumps(result, indent=2)


@app.tool(
    name="graphql_scan",
    description=(
        "Test GraphQL API for common vulnerabilities. "
        "Checks: introspection query (schema leak), nested query DoS, "
        "field suggestion enumeration, batch query DoS, alias-based rate limit bypass."
    ),
)
def graphql_scan(target: str = "http://localhost:5016") -> str:
    """
    Test GraphQL introspection and batch queries.

    Args:
        target: Base URL of the target API (default: http://localhost:5016)
    """
    target = _validate_target(target)
    env = {"GQL_TARGET": target}
    result = _run_script(SCRIPTS["graphql_scan"], env_overrides=env)
    return json.dumps(result, indent=2)


@app.tool(
    name="ssrf_probe",
    description=(
        "Test SSRF (Server-Side Request Forgery) vectors against a target. "
        "Probes: AWS/GCP/Azure metadata endpoints, file:// reads, "
        "internal port scan, profile image URL SSRF, product image URL processing."
    ),
)
def ssrf_probe(target: str = "http://localhost:5016") -> str:
    """
    Test SSRF vectors against target.

    Args:
        target: Base URL of the target API (default: http://localhost:5016)
    """
    target = _validate_target(target)
    env = {"SSRF_TARGET": target}
    result = _run_script(SCRIPTS["ssrf_probe"], env_overrides=env)
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(transport="stdio")
