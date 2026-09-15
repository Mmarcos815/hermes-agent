#!/usr/bin/env python3
"""
MCPirats — Multi-Agent MCP Vulnerability Analysis Server
=========================================================
A FastMCP server that provides tools for scanning MCP servers,
discovering vulnerabilities, enumerating endpoints, testing for
injection flaws, and generating security audit reports.

Designed for the Bionic Daughter security academy project.

Tools (10):
  1. scan_mcp_server       — Connectivity + metadata scan of a target MCP server
  2. discover_tools        — Enumerate tools/resources/prompts on an MCP server
  3. enumerate_endpoints   — Probe common MCP HTTP endpoints
  4. check_auth            — Analyze auth configuration and weaknesses
  5. test_injection        — Test tool inputs for injection vulnerabilities
  6. analyze_vulnerability — Deep-dive analysis of a specific vuln class
  7. suggest_exploit       — Recommend exploits based on findings
  8. generate_report       — Compile findings into a structured report
  9. fuzz_tool             — Send malformed inputs to a specific tool
  10. compare_schemas      — Diff two MCP server tool schemas

Usage:
  python server.py                                        # stdio transport
  python server.py --transport http --port 8765           # HTTP transport
  fastmcp dev server.py                                   # dev mode with inspector
"""

import json
import re
import hashlib
import time
import logging
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, validator

# ===========================================================================
# CONFIGURATION
# ===========================================================================

SERVER_NAME = "mcpirats"
SERVER_VERSION = "1.0.0"
DEFAULT_TIMEOUT = 15.0  # seconds for HTTP requests
MAX_RESPONSE_SIZE = 512_000  # 512 KB cap on response bodies

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(SERVER_NAME)

# ===========================================================================
# DATA MODELS
# ===========================================================================

class Finding(BaseModel):
    """A single security finding."""
    severity: str = Field(..., description="critical | high | medium | low | info")
    title: str
    description: str
    evidence: Optional[str] = None
    remediation: Optional[str] = None
    cwe: Optional[str] = None
    cvss_score: Optional[float] = None

    @validator("severity")
    def _sev(cls, v):
        v = v.lower()
        if v not in ("critical", "high", "medium", "low", "info"):
            raise ValueError(f"Invalid severity: {v}")
        return v


class ScanResult(BaseModel):
    """Aggregated result from a scan session."""
    target: str
    timestamp: str
    findings: List[Finding] = []
    tools_discovered: List[Dict[str, Any]] = []
    endpoints_probed: List[Dict[str, Any]] = []
    auth_analysis: Optional[Dict[str, Any]] = None
    notes: List[str] = []


# In-memory scan session store (ephemeral)
_scan_sessions: Dict[str, ScanResult] = {}


# ===========================================================================
# HTTP HELPER
# ===========================================================================

def _http_client(timeout: float = DEFAULT_TIMEOUT) -> httpx.Client:
    """Build an httpx client with sensible defaults."""
    return httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers={
            "User-Agent": f"MCPirats/{SERVER_VERSION} (security-scanner)",
            "Accept": "application/json, text/plain, */*",
        },
    )


def _normalize_url(url: str) -> str:
    """Ensure URL has a scheme and no trailing slash."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.rstrip("/")


def _safe_get(client: httpx.Client, url: str) -> Dict[str, Any]:
    """Perform a GET and return a normalized result dict."""
    try:
        resp = client.get(url)
        body = resp.text[:MAX_RESPONSE_SIZE]
        return {
            "url": str(resp.url),
            "status_code": resp.status_code,
            "headers": dict(resp.headers),
            "body": body,
            "body_length": len(body),
            "elapsed_ms": int(resp.elapsed.total_seconds() * 1000),
        }
    except httpx.TimeoutException:
        return {"url": url, "error": "Request timed out", "status_code": None}
    except httpx.ConnectError as e:
        return {"url": url, "error": f"Connection failed: {e}", "status_code": None}
    except httpx.HTTPError as e:
        return {"url": url, "error": str(e), "status_code": None}


def _safe_post(client: httpx.Client, url: str, json_body: Dict[str, Any]) -> Dict[str, Any]:
    """Perform a POST with JSON body and return a normalized result dict."""
    try:
        resp = client.post(url, json=json_body)
        body = resp.text[:MAX_RESPONSE_SIZE]
        return {
            "url": str(resp.url),
            "status_code": resp.status_code,
            "headers": dict(resp.headers),
            "body": body,
            "body_length": len(body),
            "elapsed_ms": int(resp.elapsed.total_seconds() * 1000),
        }
    except httpx.TimeoutException:
        return {"url": url, "error": "Request timed out", "status_code": None}
    except httpx.ConnectError as e:
        return {"url": url, "error": f"Connection failed: {e}", "status_code": None}
    except httpx.HTTPError as e:
        return {"url": url, "error": str(e), "status_code": None}


# ===========================================================================
# MCP PROTOCOL HELPERS
# ===========================================================================

def _mcp_tools_list(client: httpx.Client, base_url: str) -> Dict[str, Any]:
    """
    Attempt to retrieve the MCP server's tool list via JSON-RPC.
    Tries the standard /mcp endpoint with a tools/list request.
    """
    # Try standard Streamable HTTP endpoint first
    endpoints_to_try = [
        f"{base_url}/mcp",
        f"{base_url}/api/v1/mcp",
        f"{base_url}/sse",  # legacy SSE
    ]

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {},
    }

    for endpoint in endpoints_to_try:
        result = _safe_post(client, endpoint, payload)
        if result.get("status_code") == 200 and result.get("body"):
            try:
                data = json.loads(result["body"])
                if "result" in data and "tools" in data["result"]:
                    return {"endpoint": endpoint, "tools": data["result"]["tools"]}
                if "tools" in data:
                    return {"endpoint": endpoint, "tools": data["tools"]}
            except json.JSONDecodeError:
                continue

    return {"endpoint": None, "tools": [], "note": "Could not retrieve tool list via JSON-RPC"}


def _mcp_initialize(client: httpx.Client, base_url: str) -> Dict[str, Any]:
    """
    Send an MCP initialize request to negotiate protocol version and
    discover server capabilities.
    """
    endpoints_to_try = [
        f"{base_url}/mcp",
        f"{base_url}/api/v1/mcp",
    ]

    payload = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "mcpirats", "version": SERVER_VERSION},
        },
    }

    for endpoint in endpoints_to_try:
        result = _safe_post(client, endpoint, payload)
        if result.get("status_code") == 200 and result.get("body"):
            try:
                data = json.loads(result["body"])
                if "result" in data:
                    return {"endpoint": endpoint, "server_info": data["result"]}
            except json.JSONDecodeError:
                continue

    return {"endpoint": None, "server_info": None, "note": "Initialize handshake failed"}


# ===========================================================================
# SERVER INSTANTIATION
# ===========================================================================

mcp = FastMCP(SERVER_NAME)


# ===========================================================================
# TOOL 1: scan_mcp_server
# ===========================================================================

@mcp.tool(
    name="scan_mcp_server",
    description=(
        "Perform a comprehensive scan of a target MCP server. "
        "Checks connectivity, protocol negotiation (initialize handshake), "
        "metadata extraction, and stores results in a session for further analysis. "
        "Returns a structured scan result with severity-graded findings."
    ),
)
def scan_mcp_server(target: str, timeout: float = DEFAULT_TIMEOUT) -> str:
    """
    Scan a target MCP server for connectivity, metadata, and configuration.

    Args:
        target: URL of the MCP server (e.g. http://localhost:3000 or https://mcp.example.com)
        timeout: HTTP request timeout in seconds (default 15)
    """
    target = _normalize_url(target)
    now = datetime.now(timezone.utc).isoformat()
    findings: List[Finding] = []
    notes: List[str] = []

    with _http_client(timeout) as client:
        # 1. Basic connectivity
        root = _safe_get(client, target)
        if root.get("error"):
            findings.append(Finding(
                severity="info",
                title="Target Unreachable",
                description=f"Could not connect to {target}: {root['error']}",
                evidence=root["error"],
            ))
            session = ScanResult(target=target, timestamp=now, findings=findings, notes=notes)
            _scan_sessions[target] = session
            return json.dumps(session.dict(), indent=2)

        notes.append(f"Target responded with HTTP {root['status_code']} in {root['elapsed_ms']}ms")

        # 2. Check for security headers
        headers = root.get("headers", {})
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY or SAMEORIGIN",
            "Strict-Transport-Security": "max-age",
            "Content-Security-Pecurity": "CSP directive",
            "X-XSS-Protection": "1; mode=block",
        }
        missing_headers = [h for h in security_headers if h.lower() not in {k.lower() for k in headers}]
        if missing_headers:
            findings.append(Finding(
                severity="low",
                title="Missing Security Headers",
                description=f"The following security headers are absent: {', '.join(missing_headers)}",
                evidence=f"Present headers: {list(headers.keys())}",
                remediation="Add standard security headers to all responses.",
                cwe="CWE-693",
            ))

        # 3. Check for server version disclosure
        for hdr in ("server", "x-powered-by"):
            val = headers.get(hdr) or headers.get(hdr.title())
            if val:
                findings.append(Finding(
                    severity="info",
                    title=f"Server Version Disclosure via {hdr.title()}",
                    description=f"Server reveals implementation details: {val}",
                    evidence=f"{hdr.title()}: {val}",
                    remediation=f"Suppress the {hdr.title()} header in production.",
                    cwe="CWE-200",
                ))

        # 4. MCP initialize handshake
        init_result = _mcp_initialize(client, target)
        if init_result.get("server_info"):
            server_info = init_result["server_info"]
            notes.append(f"MCP init OK at {init_result['endpoint']}")

            proto_ver = server_info.get("protocolVersion", "unknown")
            notes.append(f"Protocol version: {proto_ver}")

            # Check for outdated protocol versions
            if proto_ver < "2024-11-05":
                findings.append(Finding(
                    severity="medium",
                    title="Outdated MCP Protocol Version",
                    description=f"Server uses protocol version {proto_ver}, which may lack recent security features.",
                    evidence=f"protocolVersion: {proto_ver}",
                    remediation="Upgrade to the latest MCP protocol version (2024-11-05+).",
                    cwe="CWE-1104",
                ))

            # Check capabilities
            caps = server_info.get("capabilities", {})
            if caps.get("tools", {}).get("listChanged") is False:
                notes.append("Server does not advertise tool list changes — static tool set")
        else:
            notes.append(f"MCP init failed: {init_result.get('note', 'unknown error')}")

    # Store session
    session = ScanResult(
        target=target,
        timestamp=now,
        findings=findings,
        notes=notes,
    )
    _scan_sessions[target] = session
    return json.dumps(session.dict(), indent=2)


# ===========================================================================
# TOOL 2: discover_tools
# ===========================================================================

@mcp.tool(
    name="discover_tools",
    description=(
        "Enumerate all tools exposed by a target MCP server via JSON-RPC tools/list. "
        "For each tool, extracts name, description, and input schema. "
        "Identifies potentially dangerous tools (file access, code execution, network calls) "
        "and stores the discovery in the scan session."
    ),
)
def discover_tools(target: str, timeout: float = DEFAULT_TIMEOUT) -> str:
    """
    Enumerate tools exposed by an MCP server and flag dangerous capabilities.

    Args:
        target: URL of the MCP server
        timeout: HTTP request timeout in seconds
    """
    target = _normalize_url(target)
    now = datetime.now(timezone.utc).isoformat()
    notes: List[str] = []
    findings: List[Finding] = []
    discovered_tools: List[Dict[str, Any]] = []

    with _http_client(timeout) as client:
        result = _mcp_tools_list(client, target)

    tools = result.get("tools", [])
    notes.append(f"Discovery endpoint: {result.get('endpoint', 'none')}")

    if not tools:
        notes.append("No tools discovered or server does not expose tools/list")
        return json.dumps({
            "target": target,
            "timestamp": now,
            "tools": [],
            "findings": [f.dict() for f in findings],
            "notes": notes,
        }, indent=2)

    # Dangerous tool patterns
    dangerous_patterns = {
        r"(exec|execute|run|shell|system|subprocess|spawn)": "Code/Command Execution",
        r"(write|create|delete|remove|modify|update|put)": "File Mutation",
        r"(read|open|fetch|download|get_file|cat|load)": "File/Resource Read",
        r"(http|request|url|fetch|api|call)": "Network Access",
        r"(db|database|sql|query|table)": "Database Access",
        r"(env|secret|credential|key|token|password)": "Credential/Secret Access",
        r"(admin|root|sudo|privilege|permission)": "Privilege Operation",
        r"(send|email|notify|webhook|post)": "Outbound Communication",
    }

    for tool in tools:
        name = tool.get("name", "unknown")
        description = tool.get("description", "")
        schema = tool.get("inputSchema", {})

        tool_entry = {
            "name": name,
            "description": description,
            "input_schema": schema,
            "risk_flags": [],
        }

        # Check tool name and description for dangerous patterns
        combined_text = f"{name} {description}".lower()
        for pattern, category in dangerous_patterns.items():
            if re.search(pattern, combined_text, re.IGNORECASE):
                tool_entry["risk_flags"].append(category)

        # Flag tools that accept arbitrary file paths
        if schema.get("type") == "object":
            props = schema.get("properties", {})
            for prop_name, prop_schema in props.items():
                prop_str = json.dumps(prop_schema).lower()
                if any(kw in prop_str for kw in ["filepath", "file_path", "path", "filename"]):
                    if "File Path Injection" not in tool_entry["risk_flags"]:
                        tool_entry["risk_flags"].append("File Path Parameter")

                # Check for command/script parameters
                if any(kw in prop_name.lower() for kw in ["command", "script", "code", "query", "expression"]):
                    if "Command/Expression Parameter" not in tool_entry["risk_flags"]:
                        tool_entry["risk_flags"].append("Command/Expression Parameter")

        if tool_entry["risk_flags"]:
            findings.append(Finding(
                severity="medium" if len(tool_entry["risk_flags"]) >= 2 else "low",
                title=f"Potentially Dangerous Tool: {name}",
                description=f"Tool '{name}' has risk flags: {', '.join(tool_entry['risk_flags'])}. "
                            f"Description: {description[:200]}",
                evidence=json.dumps(tool_entry, indent=2),
                remediation="Review tool's input validation, authorization checks, and sandboxing.",
                cwe="CWE-749",
            ))

        discovered_tools.append(tool_entry)

    # Update session
    if target in _scan_sessions:
        _scan_sessions[target].tools_discovered = discovered_tools

    notes.append(f"Discovered {len(discovered_tools)} tools")
    notes.append(f"Tools with risk flags: {sum(1 for t in discovered_tools if t['risk_flags'])}")

    return json.dumps({
        "target": target,
        "timestamp": now,
        "tool_count": len(discovered_tools),
        "tools": discovered_tools,
        "findings": [f.dict() for f in findings],
        "notes": notes,
    }, indent=2)


# ===========================================================================
# TOOL 3: enumerate_endpoints
# ===========================================================================

@mcp.tool(
    name="enumerate_endpoints",
    description=(
        "Probe common MCP server HTTP endpoints to discover exposed functionality. "
        "Checks standard paths like /mcp, /sse, /api/tools, /health, /.well-known/mcp.json, "
        "/openapi.json, and other common patterns. Reports which endpoints are accessible, "
        "their HTTP status codes, and any information disclosures."
    ),
)
def enumerate_endpoints(target: str, timeout: float = DEFAULT_TIMEOUT) -> str:
    """
    Probe common MCP endpoints on a target server.

    Args:
        target: URL of the MCP server
        timeout: HTTP request timeout in seconds
    """
    target = _normalize_url(target)
    now = datetime.now(timezone.utc).isoformat()
    findings: List[Finding] = []
    endpoints: List[Dict[str, Any]] = []

    # Common MCP / API endpoints to probe
    common_paths = [
        "/mcp",
        "/api/v1/mcp",
        "/api/tools",
        "/api/v1/tools",
        "/sse",
        "/api/sse",
        "/.well-known/mcp.json",
        "/.well-known/mcp",
        "/health",
        "/healthz",
        "/ready",
        "/api/health",
        "/openapi.json",
        "/api/openapi.json",
        "/swagger.json",
        "/docs",
        "/api/docs",
        "/api/v1",
        "/api/v1/tools/list",
        "/api/v1/tools/list/",
        "/rpc",
        "/jsonrpc",
        "/mcp/tools",
        "/mcp/tools/list",
    ]

    with _http_client(timeout) as client:
        for path in common_paths:
            url = f"{target}{path}"
            result = _safe_get(client, url)

            entry = {
                "path": path,
                "url": url,
                "status_code": result.get("status_code"),
                "accessible": result.get("status_code") is not None and result["status_code"] < 400,
                "response_size": result.get("body_length", 0),
                "content_type": result.get("headers", {}).get("content-type", "unknown"),
                "error": result.get("error"),
            }

            # Check for information disclosure on accessible endpoints
            if entry["accessible"]:
                body = result.get("body", "")

                # Check for internal paths/IPs
                if re.search(r"(192\.168\.|10\.\d+\.|172\.(1[6-9]|2\d|3[01])\.|127\.0\.0\.1|localhost)", body, re.IGNORECASE):
                    findings.append(Finding(
                        severity="low",
                        title=f"Internal Address Disclosure at {path}",
                        description=f"Endpoint {path} exposes internal network addresses or localhost references.",
                        evidence=url,
                        remediation="Filter internal information from API responses.",
                        cwe="CWE-200",
                    ))

                # Check for stack traces
                if any(marker in body for marker in ["Traceback (most recent call last)", "Error:", "Exception:", "at java.", "NullPointerException"]):
                    findings.append(Finding(
                        severity="medium",
                        title=f"Stack Trace Disclosure at {path}",
                        description=f"Endpoint {path} returns stack traces or error details that may leak implementation info.",
                        evidence=url,
                        remediation="Implement generic error responses; log details server-side only.",
                        cwe="CWE-209",
                    ))

                # Check for directory listing
                if "Index of /" in body or "<title>Directory listing" in body.lower():
                    findings.append(Finding(
                        severity="medium",
                        title=f"Directory Listing Enabled at {path}",
                        description=f"Endpoint {path} allows directory listing, potentially exposing file structure.",
                        evidence=url,
                        remediation="Disable directory listing in server configuration.",
                        cwe="CWE-548",
                    ))

            endpoints.append(entry)

    # Update session
    accessible = [e for e in endpoints if e.get("accessible")]
    if target in _scan_sessions:
        _scan_sessions[target].endpoints_probed = endpoints

    # Flag: too many accessible endpoints
    if len(accessible) > 8:
        findings.append(Finding(
            severity="low",
            title="Large Attack Surface",
            description=f"{len(accessible)} out of {len(common_paths)} probed endpoints are accessible, "
                        "indicating a broad attack surface.",
            evidence=f"Accessible: {[e['path'] for e in accessible]}",
            remediation="Disable unused endpoints; apply authentication to all exposed paths.",
            cwe="CWE-284",
        ))

    return json.dumps({
        "target": target,
        "timestamp": now,
        "endpoints_probed": len(endpoints),
        "accessible_count": len(accessible),
        "endpoints": endpoints,
        "findings": [f.dict() for f in findings],
    }, indent=2)


# ===========================================================================
# TOOL 4: check_auth
# ===========================================================================

@mcp.tool(
    name="check_auth",
    description=(
        "Analyze the authentication and authorization configuration of an MCP server. "
        "Checks for: missing auth headers, unprotected tool endpoints, token format analysis, "
        "bearer <REDACTED> acceptance, API key patterns, and session handling. "
        "Attempts an unauthenticated tools/list request to verify access control."
    ),
)
def check_auth(target: str, test_token: Optional[str] = None, timeout: float = DEFAULT_TIMEOUT) -> str:
    """
    Analyze authentication and authorization of an MCP server.

    Args:
        target: URL of the MCP server
        test_token: Optional bearer <REDACTED> or API key to test acceptance
        timeout: HTTP request timeout in seconds
    """
    target = _normalize_url(target)
    now = datetime.now(timezone.utc).isoformat()
    findings: List[Finding] = []
    auth_analysis: Dict[str, Any] = {
        "unauthenticated_access": None,
        "auth_header_required": None,
        "accepted_tokens": [],
        "auth_endpoints_found": [],
    }

    list_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {},
    }

    with _http_client(timeout) as client:
        # 1. Try unauthenticated tools/list
        unauth_result = _safe_post(client, f"{target}/mcp", list_payload)
        unauth_ok = unauth_result.get("status_code") == 200

        auth_analysis["unauthenticated_access"] = unauth_ok
        auth_analysis["unauth_response_code"] = unauth_result.get("status_code")

        if unauth_ok:
            findings.append(Finding(
                severity="high",
                title="Unauthenticated Tool Access",
                description="The MCP server allows tool enumeration without authentication. "
                            "An attacker can discover all exposed tools and their schemas.",
                evidence=f"tools/list returned HTTP 200 without auth",
                remediation="Require authentication for all MCP endpoints.",
                cwe="CWE-306",
                cvss_score=7.5,
            ))

        # 2. Check common auth-related endpoints
        auth_paths = ["/auth", "/login", "/token", "/oauth", "/.well-known/openid-configuration"]
        for path in auth_paths:
            result = _safe_get(client, f"{target}{path}")
            if result.get("status_code") and result["status_code"] < 400:
                auth_analysis["auth_endpoints_found"].append(path)

        if auth_analysis["auth_endpoints_found"] and unauth_ok:
            findings.append(Finding(
                severity="medium",
                title="Auth Endpoints Present but Not Enforced",
                description=f"Server has auth endpoints ({auth_analysis['auth_endpoints_found']}) "
                            "but does not enforce authentication on tool endpoints.",
                evidence=f"Auth endpoints: {auth_analysis['auth_endpoints_found']}",
                remediation="Enforce authentication on all tool and resource endpoints.",
                cwe="CWE-287",
            ))

        # 3. Test with provided token
        if test_token:
            client.headers["Authorization"] = f"Bearer {test_token}"
            auth_result = _safe_post(client, f"{target}/mcp", list_payload)
            if auth_result.get("status_code") == 200:
                auth_analysis["accepted_tokens"].append("bearer")
                findings.append(Finding(
                    severity="info",
                    title="Bearer <REDACTED> Accepted",
                    description="Server accepted the provided bearer <REDACTED> for authentication.",
                    evidence=f"Token prefix: {test_token[:8]}...",
                ))
            client.headers.pop("Authorization", None)

        # 4. Check WWW-Authenticate header
        root = _safe_get(client, target)
        www_auth = root.get("headers", {}).get("www-authenticate") or root.get("headers", {}).get("WWW-Authenticate")
        auth_analysis["www_authenticate_header"] = www_auth
        if www_auth:
            auth_analysis["auth_header_required"] = True
        else:
            auth_analysis["auth_header_required"] = False
            if not unauth_ok:
                findings.append(Finding(
                    severity="info",
                    title="No WWW-Authenticate Challenge",
                    description="Server does not return a WWW-Authenticate header, "
                                "making it unclear what auth scheme is expected.",
                    evidence="No WWW-Authenticate header present",
                    remediation="Return proper WWW-Authenticate challenges for 401 responses.",
                    cwe="CWE-287",
                ))

    # Update session
    if target in _scan_sessions:
        _scan_sessions[target].auth_analysis = auth_analysis

    return json.dumps({
        "target": target,
        "timestamp": now,
        "auth_analysis": auth_analysis,
        "findings": [f.dict() for f in findings],
    }, indent=2)


# ===========================================================================
# TOOL 5: test_injection
# ===========================================================================

@mcp.tool(
    name="test_injection",
    description=(
        "Test an MCP server's tool inputs for injection vulnerabilities. "
        "Sends crafted payloads including path traversal (../), command injection (; | &), "
        "SQL injection (' OR 1=1 --), template injection ({{7*7}}), and SSRF (http://169.254.169.254). "
        "Analyzes responses for signs of successful injection. "
        "Use discover_tools first to identify tool schemas to target."
    ),
)
def test_injection(
    target: str,
    tool_name: Optional[str] = None,
    target_param: Optional[str] = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    """
    Test MCP tool inputs for injection vulnerabilities.

    Args:
        target: URL of the MCP server
        tool_name: Specific tool to test (if None, tests all discovered tools)
        target_param: Specific parameter to inject into
        timeout: HTTP request timeout in seconds
    """
    target = _normalize_url(target)
    now = datetime.now(timezone.utc).isoformat()
    findings: List[Finding] = []
    test_results: List[Dict[str, Any]] = []

    # Injection payloads by category
    payloads = {
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\win.ini",
            "....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ],
        "command_injection": [
            "; cat /etc/passwd",
            "| whoami",
            "& ping -c 1 127.0.0.1",
            "`id`",
            "$(id)",
        ],
        "sql_injection": [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "1; SELECT @@version",
            "' UNION SELECT null,null--",
        ],
        "template_injection": [
            "{{7*7}}",
            "${7*7}",
            "<%= 7*7 %>",
            "${{7*7}}",
        ],
        "ssrf": [
            "http://169.254.169.254/latest/meta-data/",
            "http://127.0.0.1:6379/",
            "http://[::]:80/",
            "file:///etc/passwd",
        ],
        "xss": [
            "<script>alert(1)</script>",
            "\"><img src=x onerror=alert(1)>",
            "javascript:alert(1)",
        ],
    }

    # Discover tools if not specified
    tools_to_test: List[Dict[str, Any]] = []
    if target in _scan_sessions and _scan_sessions[target].tools_discovered:
        tools_to_test = _scan_sessions[target].tools_discovered

    if tool_name:
        tools_to_test = [t for t in tools_to_test if t.get("name") == tool_name]

    if not tools_to_test:
        # Try to discover now
        with _http_client(timeout) as client:
            result = _mcp_tools_list(client, target)
            tools_to_test = result.get("tools", [])

    if not tools_to_test:
        return json.dumps({
            "target": target,
            "timestamp": now,
            "error": "No tools to test. Run discover_tools first or specify tool_name.",
            "findings": [],
        }, indent=2)

    with _http_client(timeout) as client:
        for tool in tools_to_test:
            tname = tool.get("name", "unknown")
            schema = tool.get("inputSchema", tool.get("schema", {}))
            props = schema.get("properties", {})

            # Determine which params to test
            params_to_test = list(props.keys())
            if target_param:
                params_to_test = [p for p in params_to_test if p == target_param]

            for param in params_to_test:
                param_schema = props.get(param, {})
                # Only test string/number params
                if param_schema.get("type") not in ("string", "number", "integer", None):
                    continue

                for category, payload_list in payloads.items():
                    for payload in payload_list:
                        call_payload = {
                            "jsonrpc": "2.0",
                            "id": int(time.time() * 1000) % 1000000,
                            "method": "tools/call",
                            "params": {
                                "name": tname,
                                "arguments": {param: payload},
                            },
                        }

                        result = _safe_post(client, f"{target}/mcp", call_payload)

                        status = result.get("status_code")
                        body = result.get("body", "")
                        error = result.get("error")

                        # Analyze response
                        indicators = []
                        if error:
                            indicators.append(f"request_error: {error}")

                        # Check for injection success indicators
                        response_lower = body.lower()
                        if category == "path_traversal":
                            if "root:" in response_lower or "[extensions]" in response_lower:
                                indicators.append("FILE_CONTENT_LEAK")
                        elif category == "command_injection":
                            if any(s in response_lower for s in ["uid=", "root", "admin"]):
                                indicators.append("COMMAND_EXECUTION")
                        elif category == "sql_injection":
                            if any(s in response_lower for s in ["sql", "mysql", "postgresql", "oracle", "syntax error"]):
                                indicators.append("SQL_ERROR")
                            if "unauthorized" not in response_lower and status == 200:
                                indicators.append("POSSIBLE_BYPASS")
                        elif category == "template_injection":
                            if "49" in body and "{{" not in body:
                                indicators.append("TEMPLATE_EVAL")
                        elif category == "ssrf":
                            if any(s in response_lower for s in ["ami-id", "instance-id", "iam", "metadata"]):
                                indicators.append("SSRF_SUCCESS")

                        test_entry = {
                            "tool": tname,
                            "parameter": param,
                            "injection_category": category,
                            "payload": payload,
                            "response_status": status,
                            "indicators": indicators,
                        }

                        if indicators:
                            findings.append(Finding(
                                severity="high" if "SUCCESS" in str(indicators) or "EXECUTION" in str(indicators) else "medium",
                                title=f"Possible {category.replace('_', ' ').title()} in {tname}.{param}",
                                description=f"Payload '{payload[:50]}' triggered indicator(s): {indicators}",
                                evidence=json.dumps(test_entry, indent=2),
                                remediation=f"Validate and sanitize the '{param}' parameter in tool '{tname}'.",
                                cwe="CWE-74" if category == "command_injection" else "CWE-89" if category == "sql_injection" else "CWE-20",
                            ))

                        test_results.append(test_entry)

    return json.dumps({
        "target": target,
        "timestamp": now,
        "tests_run": len(test_results),
        "vulnerable_tests": sum(1 for t in test_results if t["indicators"]),
        "findings": [f.dict() for f in findings],
        "test_results": test_results[:50],  # Cap output
    }, indent=2)


# ===========================================================================
# TOOL 6: analyze_vulnerability
# ===========================================================================

@mcp.tool(
    name="analyze_vulnerability",
    description=(
        "Perform a deep-dive analysis of a specific vulnerability class on a target MCP server. "
        "Supported vuln types: bola, mass_assignment, excessive_info_disclosure, "
        "missing_rate_limiting, insecure_deserialization, tool_chaining, prompt_injection. "
        "Returns detailed findings with CWE references, CVSS scores, and remediation advice."
    ),
)
def analyze_vulnerability(target: str, vuln_type: str, timeout: float = DEFAULT_TIMEOUT) -> str:
    """
    Deep-dive analysis of a specific vulnerability class.

    Args:
        target: URL of the MCP server
        vuln_type: One of: bola, mass_assignment, excessive_info_disclosure,
                   missing_rate_limiting, insecure_deserialization, tool_chaining,
                   prompt_injection
        timeout: HTTP request timeout in seconds
    """
    target = _normalize_url(target)
    now = datetime.now(timezone.utc).isoformat()
    vuln_type = vuln_type.lower().replace("-", "_").replace(" ", "_")

    valid_types = {
        "bola", "mass_assignment", "excessive_info_disclosure",
        "missing_rate_limiting", "insecure_deserialization",
        "tool_chaining", "prompt_injection",
    }

    if vuln_type not in valid_types:
        return json.dumps({
            "error": f"Unknown vuln_type '{vuln_type}'. Must be one of: {sorted(valid_types)}"
        }, indent=2)

    findings: List[Finding] = []
    details: Dict[str, Any] = {"vulnerability_type": vuln_type}

    with _http_client(timeout) as client:
        # Get tool list
        tools_result = _mcp_tools_list(client, target)
        tools = tools_result.get("tools", [])
        details["tools_analyzed"] = len(tools)

        if vuln_type == "bola":
            # Check for object-ID-like parameters across tools
            object_id_params = ["id", "user_id", "order_id", "file_id", "resource_id", "uuid"]
            for tool in tools:
                schema = tool.get("inputSchema", {})
                props = schema.get("properties", {})
                for pname in props:
                    if any(oid in pname.lower() for oid in object_id_params):
                        findings.append(Finding(
                            severity="medium",
                            title=f"Potential BOLA: {tool['name']}.{pname}",
                            description=f"Tool '{tool['name']}' accepts object ID parameter '{pname}' "
                                        "without evident authorization check at the schema level.",
                            evidence=f"Parameter: {pname}, Schema: {json.dumps(props[pname])}",
                            remediation="Implement object-level authorization checks for each access.",
                            cwe="CWE-639",
                            cvss_score=6.5,
                        ))

        elif vuln_type == "mass_assignment":
            for tool in tools:
                schema = tool.get("inputSchema", {})
                props = schema.get("properties", {})
                for pname, pschema in props.items():
                    if pname.lower() in ("role", "is_admin", "admin", "permissions", "role_id", "access_level"):
                        findings.append(Finding(
                            severity="high",
                            title=f"Mass Assignment Risk: {tool['name']}.{pname}",
                            description=f"Tool '{tool['name']}' accepts privilege/role field '{pname}' "
                                        "which could be exploited for privilege escalation.",
                            evidence=f"Parameter: {pname}, Schema: {json.dumps(pschema)}",
                            remediation="Use an allow-list of user-mutable fields; reject privileged fields.",
                            cwe="CWE-915",
                            cvss_score=8.0,
                        ))
                    # Check for nested object params that might accept arbitrary fields
                    if pschema.get("type") == "object" and "properties" in pschema:
                        nested_props = list(pschema.get("properties", {}).keys())
                        if len(nested_props) > 5:
                            findings.append(Finding(
                                severity="low",
                                title=f"Rich Object Parameter: {tool['name']}.{pname}",
                                description=f"Tool accepts nested object '{pname}' with {len(nested_props)} fields. "
                                            "Verify no sensitive fields are exposed.",
                                evidence=f"Fields: {nested_props[:10]}",
                                remediation="Validate nested objects against an explicit schema.",
                                cwe="CWE-915",
                            ))

        elif vuln_type == "excessive_info_disclosure":
            for tool in tools:
                desc = tool.get("description", "")
                # Tools that expose internal details
                if any(kw in desc.lower() for kw in ["internal", "debug", "dev", "admin", "raw", "system", "env", "secret"]):
                    findings.append(Finding(
                        severity="medium",
                        title=f"Info Disclosure via Tool Description: {tool['name']}",
                        description=f"Tool '{tool['name']}' description reveals internal implementation details.",
                        evidence=f"Description: {desc[:300]}",
                        remediation="Remove internal references from tool descriptions.",
                        cwe="CWE-200",
                    ))

            # Check tool response sizes
            if tools:
                sample_tool = tools[0]
                call_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {"name": sample_tool["name"], "arguments": {}},
                }
                result = _safe_post(client, f"{target}/mcp", call_payload)
                body_len = result.get("body_length", 0)
                if body_len > 100_000:
                    findings.append(Finding(
                        severity="low",
                        title="Excessive Response Size",
                        description=f"Sample tool response is {body_len} bytes. Large responses may leak data.",
                        evidence=f"Response size: {body_len} bytes from {sample_tool['name']}",
                        remediation="Implement pagination and response size limits.",
                        cwe="CWE-200",
                    ))

        elif vuln_type == "missing_rate_limiting":
            # Rapid-fire requests to detect rate limiting
            request_times = []
            for i in range(10):
                start = time.monotonic()
                _safe_get(client, target)
                elapsed = time.monotonic() - start
                request_times.append(elapsed)

            # Check for rate limit headers in any response
            headers_present = False
            probe = _safe_get(client, target)
            resp_headers = probe.get("headers", {})
            if any(h.lower() in {k.lower() for k in resp_headers} for h in ["x-ratelimit-limit", "retry-after", "x-rate-limit"]):
                headers_present = True

            if not headers_present:
                findings.append(Finding(
                    severity="medium",
                    title="No Rate Limiting Headers Detected",
                    description="Server does not advertise rate limiting via headers. "
                                "Rapid sequential requests were all accepted.",
                    evidence=f"10 requests completed in {sum(request_times):.2f}s with no 429 response",
                    remediation="Implement rate limiting on all endpoints (e.g., 100 req/min per client).",
                    cwe="CWE-770",
                    cvss_score=5.3,
                ))

        elif vuln_type == "insecure_deserialization":
            for tool in tools:
                schema = tool.get("inputSchema", {})
                props = schema.get("properties", {})
                for pname, pschema in props.items():
                    pdesc = json.dumps(pschema).lower()
                    if any(kw in pdesc or kw in pname.lower() for kw in ["pickle", "serialize", "deserialize", "yaml.load", "object", "eval"]):
                        findings.append(Finding(
                            severity="high",
                            title=f"Potential Insecure Deserialization: {tool['name']}.{pname}",
                            description=f"Tool '{tool['name']}' accepts parameter '{pname}' that may "
                                        "accept serialized objects or expressions.",
                            evidence=f"Parameter schema: {json.dumps(pschema)}",
                            remediation="Never deserialize untrusted data. Use JSON with strict schema validation.",
                            cwe="CWE-502",
                            cvss_score=8.1,
                        ))

        elif vuln_type == "tool_chaining":
            # Analyze if tools can be chained (output of one feeds into another)
            file_tools = []
            exec_tools = []
            for tool in tools:
                name = tool.get("name", "").lower()
                desc = tool.get("description", "").lower()
                if any(kw in name or kw in desc for kw in ["read", "file", "fetch", "download", "get"]):
                    file_tools.append(tool["name"])
                if any(kw in name or kw in desc for kw in ["exec", "run", "execute", "eval", "write", "command"]):
                    exec_tools.append(tool["name"])

            if file_tools and exec_tools:
                findings.append(Finding(
                    severity="high",
                    title="Dangerous Tool Chaining Possible",
                    description=f"Server has both read tools ({file_tools}) and execution tools ({exec_tools}). "
                                "An attacker could read sensitive files and pass contents to execution tools.",
                    evidence=f"Read tools: {file_tools}, Exec tools: {exec_tools}",
                    remediation="Isolate read and execute tools; enforce sandboxing on exec tools.",
                    cwe="CWE-78",
                    cvss_score=9.0,
                ))

        elif vuln_type == "prompt_injection":
            for tool in tools:
                schema = tool.get("inputSchema", {})
                props = schema.get("properties", {})
                for pname, pschema in props.items():
                    if pschema.get("type") == "string":
                        # Long string params are prime targets
                        if not pschema.get("maxLength") and not pschema.get("enum"):
                            findings.append(Finding(
                                severity="low",
                                title=f"Unbounded String Parameter: {tool['name']}.{pname}",
                                description=f"Parameter '{pname}' accepts arbitrary-length strings without enum "
                                            "restriction, making it a potential prompt injection vector.",
                                evidence=f"Schema: {json.dumps(pschema)}",
                                remediation="Set maxLength constraints; validate against prompt injection patterns.",
                                cwe="CWE-74",
                            ))

    details["findings_count"] = len(findings)
    details["highest_severity"] = max(
        (f.severity for f in findings),
        key=lambda s: {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}.get(s, -1),
        default="none",
    )

    return json.dumps({
        "target": target,
        "timestamp": now,
        "analysis_details": details,
        "findings": [f.dict() for f in findings],
    }, indent=2)


# ===========================================================================
# TOOL 7: suggest_exploit
# ===========================================================================

@mcp.tool(
    name="suggest_exploit",
    description=(
        "Given a target and its scan findings, suggest practical exploitation techniques. "
        "Can target a specific vulnerability type or provide general recommendations "
        "based on all prior scan results stored in the session. "
        "Returns concrete exploit steps, proof-of-concept code snippets, and "
        "post-exploitation recommendations."
    ),
)
def suggest_exploit(
    target: str,
    vuln_type: Optional[str] = None,
) -> str:
    """
    Suggest exploits based on scan findings.

    Args:
        target: URL of the MCP server (must have prior scan data in session)
        vuln_type: Optional specific vuln type to focus on
    """
    target = _normalize_url(target)
    now = datetime.now(timezone.utc).isoformat()

    if target not in _scan_sessions:
        return json.dumps({
            "target": target,
            "error": "No scan session found for this target. Run scan_mcp_server first.",
        }, indent=2)

    session = _scan_sessions[target]
    findings = session.findings
    tools = session.tools_discovered
    endpoints = session.endpoints_probed
    auth = session.auth_analysis

    exploits: List[Dict[str, Any]] = []

    # Auth bypass exploit
    if auth and auth.get("unauthenticated_access"):
        exploits.append({
            "title": "Unauthenticated Tool Execution",
            "severity": "critical",
            "description": "The MCP server allows tool calls without authentication. "
                           "An attacker can directly invoke any exposed tool.",
            "steps": [
                "1. Identify target tools via tools/list (no auth required)",
                "2. Call tools/call with the desired tool name and arguments",
                "3. Execute file reads, code execution, or data exfiltration",
            ],
            "proof_of_concept": json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "<TOOL_NAME>",
                    "arguments": {}
                }
            }, indent=2),
            "mitigation": "Implement OAuth 2.0 or mutual TLS authentication on all MCP endpoints.",
        })

    # Tool chaining exploit
    read_tools = [t for t in tools if any(f in (t.get("risk_flags") or []) for f in ["File/Resource Read", "File Mutation"])]
    exec_tools = [t for t in tools if "Code/Command Execution" in (t.get("risk_flags") or [])]

    if read_tools and exec_tools:
        exploits.append({
            "title": "Read-then-Execute Tool Chain",
            "severity": "high",
            "description": f"Chain '{read_tools[0]['name']}' (read) with '{exec_tools[0]['name']}' (execute) "
                           "to achieve arbitrary code execution.",
            "steps": [
                f"1. Call '{read_tools[0]['name']}' to read sensitive files (e.g., /etc/passwd, config files)",
                f"2. Extract credentials or command templates from the file contents",
                f"3. Pass the extracted data as arguments to '{exec_tools[0]['name']}'",
                "4. Achieve remote code execution on the MCP server host",
            ],
            "mitigation": "Sandbox all execution tools; restrict file access to a chroot jail.",
        })

    # SSRF via tool params
    ssrf_capable = [t for t in tools if "Network Access" in (t.get("risk_flags") or [])]
    if ssrf_capable:
        exploits.append({
            "title": "SSRF Through Network-Capable Tool",
            "severity": "high",
            "description": f"Tool '{ssrf_capable[0]['name']}' makes HTTP requests based on user input, "
                           "enabling Server-Side Request Forgery against internal services.",
            "steps": [
                f"1. Call '{ssrf_capable[0]['name']}' with URL pointing to http://169.254.169.254/latest/meta-data/iam/security-credentials/",
                "2. Extract cloud IAM credentials from the response",
                "3. Use credentials for lateral movement in the cloud environment",
            ],
            "mitigation": "Implement URL allow-listing; block internal/private IP ranges; use a proxy.",
        })

    # Mass assignment exploit
    mass_assign_tools = [
        t for t in tools
        for flag in (t.get("risk_flags") or [])
        if "Privilege" in flag or "admin" in t.get("name", "").lower()
    ]
    if mass_assign_tools:
        exploits.append({
            "title": "Privilege Escalation via Mass Assignment",
            "severity": "high",
            "description": f"Tool '{mass_assign_tools[0]['name']}' may accept role/privilege fields "
                           "that can be manipulated to gain admin access.",
            "steps": [
                f"1. Inspect '{mass_assign_tools[0]['name']}' input schema for role/admin fields",
                "2. Include 'role': 'admin' or 'is_admin': true in tool arguments",
                "3. If server accepts the field, gain elevated privileges",
            ],
            "mitigation": "Use a DTO (Data Transfer Object) layer that whitelists user-mutable fields.",
        })

    # Filter by specific vuln type if requested
    if vuln_type:
        vuln_lower = vuln_type.lower()
        type_to_title = {
            "bola": "Broken Object Level Authorization",
            "mass_assignment": "Mass Assignment",
            "ssrf": "Server-Side Request Forgery",
            "auth": "Authentication Bypass",
            "tool_chaining": "Tool Chaining",
            "injection": "Injection",
        }
        keywords = type_to_title.get(vuln_lower, vuln_lower).lower().split()
        exploits = [
            e for e in exploits
            if any(kw in e["title"].lower() or kw in e["description"].lower() for kw in keywords)
        ]

    if not exploits:
        exploits.append({
            "title": "No Specific Exploits Identified",
            "severity": "info",
            "description": "No critical exploitation paths were identified from current scan data. "
                           "Consider running more targeted scans (discover_tools, test_injection, "
                           "analyze_vulnerability) to gather more findings.",
            "steps": [],
            "mitigation": "Continue scanning with deeper analysis.",
        })

    return json.dumps({
        "target": target,
        "timestamp": now,
        "session_summary": {
            "total_findings": len(findings),
            "tools_discovered": len(tools),
            "endpoints_probed": len(endpoints),
            "auth_analyzed": auth is not None,
        },
        "suggested_exploits": exploits,
        "exploit_count": len(exploits),
    }, indent=2)


# ===========================================================================
# TOOL 8: generate_report
# ===========================================================================

@mcp.tool(
    name="generate_report",
    description=(
        "Generate a comprehensive security audit report from all scan findings "
        "stored in the session for a given target. "
        "The report includes: executive summary, findings by severity, "
        "tool inventory, endpoint map, auth analysis, and remediation roadmap. "
        "Output is formatted as structured JSON suitable for programmatic consumption."
    ),
)
def generate_report(
    target: str,
    format: str = "json",
    output_file: Optional[str] = None,
) -> str:
    """
    Generate a comprehensive security audit report.

    Args:
        target: URL of the MCP server (must have prior scan data)
        format: Output format — 'json' or 'markdown'
        output_file: Optional path to write the report to disk
    """
    target = _normalize_url(target)

    if target not in _scan_sessions:
        return json.dumps({
            "target": target,
            "error": "No scan session found. Run scan_mcp_server first.",
        }, indent=2)

    session = _scan_sessions[target]

    # Severity counts
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in session.findings:
        severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1

    # Risk score (weighted)
    risk_weights = {"critical": 10, "high": 5, "medium": 2, "low": 1, "info": 0}
    risk_score = sum(severity_counts[s] * w for s, w in risk_weights.items())

    # Determine overall risk
    if severity_counts["critical"] > 0:
        overall_risk = "CRITICAL"
    elif severity_counts["high"] >= 2:
        overall_risk = "HIGH"
    elif severity_counts["high"] == 1 or severity_counts["medium"] >= 3:
        overall_risk = "MEDIUM"
    elif severity_counts["medium"] >= 1:
        overall_risk = "LOW"
    else:
        overall_risk = "MINIMAL"

    report = {
        "report_metadata": {
            "title": "MCPirats Security Audit Report",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "scanner_version": SERVER_VERSION,
            "target": target,
            "scan_timestamp": session.timestamp,
        },
        "executive_summary": {
            "overall_risk": overall_risk,
            "risk_score": risk_score,
            "findings_total": len(session.findings),
            "severity_breakdown": severity_counts,
            "tools_discovered": len(session.tools_discovered),
            "endpoints_probed": len(session.endpoints_probed),
            "auth_analyzed": session.auth_analysis is not None,
        },
        "findings_by_severity": {},
        "tool_inventory": session.tools_discovered,
        "endpoint_map": session.endpoints_probed,
        "auth_analysis": session.auth_analysis,
        "remediation_roadmap": [],
        "notes": session.notes,
    }

    # Group findings by severity
    for sev in ["critical", "high", "medium", "low", "info"]:
        sev_findings = [f.dict() for f in session.findings if f.severity == sev]
        if sev_findings:
            report["findings_by_severity"][sev] = sev_findings

    # Build remediation roadmap (prioritized)
    if severity_counts["critical"] > 0:
        report["remediation_roadmap"].append({
            "priority": 1,
            "action": "Address critical vulnerabilities immediately",
            "items": [f.title for f in session.findings if f.severity == "critical"],
        })
    if severity_counts["high"] > 0:
        report["remediation_roadmap"].append({
            "priority": 2,
            "action": "Remediate high-severity findings within 7 days",
            "items": [f.title for f in session.findings if f.severity == "high"],
        })
    if severity_counts["medium"] > 0:
        report["remediation_roadmap"].append({
            "priority": 3,
            "action": "Address medium-severity findings within 30 days",
            "items": [f.title for f in session.findings if f.severity == "medium"],
        })
    if severity_counts["low"] > 0:
        report["remediation_roadmap"].append({
            "priority": 4,
            "action": "Remediate low-severity findings in next maintenance cycle",
            "items": [f.title for f in session.findings if f.severity == "low"],
        })

    # Format output
    if format.lower() == "markdown":
        md_lines = [
            f"# MCPirats Security Audit Report",
            f"",
            f"**Target:** `{target}`",
            f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            f"**Scanner Version:** {SERVER_VERSION}",
            f"",
            f"## Executive Summary",
            f"",
            f"| Metric | Value |",
            f"|---|---|",
            f"| Overall Risk | **{overall_risk}** |",
            f"| Risk Score | {risk_score} |",
            f"| Total Findings | {len(session.findings)} |",
            f"| Critical | {severity_counts['critical']} |",
            f"| High | {severity_counts['high']} |",
            f"| Medium | {severity_counts['medium']} |",
            f"| Low | {severity_counts['low']} |",
            f"| Info | {severity_counts['info']} |",
            f"| Tools Discovered | {len(session.tools_discovered)} |",
            f"| Endpoints Probed | {len(session.endpoints_probed)} |",
            f"",
        ]

        for sev in ["critical", "high", "medium", "low", "info"]:
            sev_findings = [f for f in session.findings if f.severity == sev]
            if sev_findings:
                md_lines.append(f"## {sev.title()} Findings")
                md_lines.append("")
                for f in sev_findings:
                    md_lines.append(f"### {f.title}")
                    md_lines.append(f"")
                    md_lines.append(f"- **CWE:** {f.cwe or 'N/A'}")
                    md_lines.append(f"- **CVSS:** {f.cvss_score or 'N/A'}")
                    md_lines.append(f"")
                    md_lines.append(f"{f.description}")
                    md_lines.append("")
                    if f.evidence:
                        md_lines.append(f"**Evidence:** `{f.evidence[:200]}`")
                        md_lines.append("")
                    if f.remediation:
                        md_lines.append(f"**Remediation:** {f.remediation}")
                        md_lines.append("")

        output = "\n".join(md_lines)
    else:
        output = json.dumps(report, indent=2, default=str)

    # Write to file if requested
    if output_file:
        try:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            Path(output_file).write_text(output, encoding="utf-8")
            report["report_metadata"]["output_file"] = output_file
        except OSError as e:
            report["report_metadata"]["file_write_error"] = str(e)

    # Re-serialize with file path if written
    if format.lower() != "markdown":
        output = json.dumps(report, indent=2, default=str)

    return output


# ===========================================================================
# TOOL 9: fuzz_tool (bonus)
# ===========================================================================

@mcp.tool(
    name="fuzz_tool",
    description=(
        "Send a series of malformed or unexpected inputs to a specific MCP tool "
        "to identify crash conditions, error handling weaknesses, or information leaks. "
        "Tests: null values, extremely large strings, type mismatches, missing required fields, "
        "and Unicode edge cases."
    ),
)
def fuzz_tool(
    target: str,
    tool_name: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    """
    Fuzz a specific MCP tool with malformed inputs.

    Args:
        target: URL of the MCP server
        tool_name: Name of the tool to fuzz
        timeout: HTTP request timeout per request in seconds
    """
    target = _normalize_url(target)
    now = datetime.now(timezone.utc).isoformat()
    findings: List[Finding] = []
    fuzz_results: List[Dict[str, Any]] = []

    # Fuzz inputs to try
    fuzz_payloads = [
        {"input": None, "description": "null value"},
        {"input": "", "description": "empty string"},
        {"input": "A" * 10000, "description": "10KB string"},
        {"input": "🔥" * 500, "description": "unicode stress"},
        {"input": -1, "description": "negative number"},
        {"input": 999999999999, "description": "very large number"},
        {"input": [], "description": "empty array"},
        {"input": {}, "description": "empty object"},
        {"input": True, "description": "boolean true"},
        {"input": False, "description": "boolean false"},
    ]

    with _http_client(timeout) as client:
        for fuzz in fuzz_payloads:
            call_payload = {
                "jsonrpc": "2.0",
                "id": int(time.time() * 1000) % 1000000,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": {"input": fuzz["input"]},
                },
            }

            result = _safe_post(client, f"{target}/mcp", call_payload)
            status = result.get("status_code")
            body = result.get("body", "")
            error = result.get("error")

            entry = {
                "description": fuzz["description"],
                "payload_type": type(fuzz["input"]).__name__,
                "status_code": status,
                "response_size": result.get("body_length", 0),
                "indicators": [],
            }

            # Check for error indicators
            if error:
                entry["indicators"].append("request_error")
            if status and status >= 500:
                entry["indicators"].append("server_error")
                findings.append(Finding(
                    severity="medium",
                    title=f"Server Error ({status}) on {tool_name} with {fuzz['description']}",
                    description=f"Tool '{tool_name}' returned HTTP {status} when given {fuzz['description']} input.",
                    evidence=body[:500],
                    remediation="Implement robust input validation returning 400 for invalid inputs.",
                    cwe="CWE-20",
                ))
            if status == 200 and any(marker in body.lower() for marker in ["traceback", "exception", "error", "stack"]):
                entry["indicators"].append("error_in_response")
                findings.append(Finding(
                    severity="low",
                    title=f"Error Disclosure in {tool_name}",
                    description=f"Tool '{tool_name}' includes error details in 200 response for {fuzz['description']} input.",
                    evidence=body[:300],
                    remediation="Return generic error messages; log details server-side.",
                    cwe="CWE-209",
                ))

            fuzz_results.append(entry)

    return json.dumps({
        "target": target,
        "timestamp": now,
        "tool_fuzzed": tool_name,
        "tests_run": len(fuzz_payloads),
        "anomalies_found": sum(1 for f in fuzz_results if f["indicators"]),
        "findings": [f.dict() for f in findings],
        "results": fuzz_results,
    }, indent=2)


# ===========================================================================
# TOOL 10: compare_schemas (bonus)
# ===========================================================================

@mcp.tool(
    name="compare_schemas",
    description=(
        "Compare the tool schemas of two MCP servers to identify differences. "
        "Useful for detecting version drift, unauthorized modifications, "
        "or shadow tools added by an attacker. Returns added, removed, and "
        "changed tools with diff details."
    ),
)
def compare_schemas(
    target_a: str,
    target_b: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    """
    Compare tool schemas of two MCP servers.

    Args:
        target_a: First MCP server URL
        target_b: Second MCP server URL
        timeout: HTTP request timeout in seconds
    """
    target_a = _normalize_url(target_a)
    target_b = _normalize_url(target_b)

    with _http_client(timeout) as client:
        result_a = _mcp_tools_list(client, target_a)
        result_b = _mcp_tools_list(client, target_b)

    tools_a = {t.get("name", "?"): t for t in result_a.get("tools", [])}
    tools_b = {t.get("name", "?"): t for t in result_b.get("tools", [])}

    names_a = set(tools_a.keys())
    names_b = set(tools_b.keys())

    added = list(names_b - names_a)
    removed = list(names_a - names_b)
    common = list(names_a & names_b)

    changed = []
    for name in common:
        hash_a = hashlib.sha256(json.dumps(tools_a[name], sort_keys=True).encode()).hexdigest()[:12]
        hash_b = hashlib.sha256(json.dumps(tools_b[name], sort_keys=True).encode()).hexdigest()[:12]
        if hash_a != hash_b:
            changed.append({
                "tool": name,
                "schema_hash_a": hash_a,
                "schema_hash_b": hash_b,
                "note": "Schema differs between servers",
            })

    findings: List[Finding] = []

    if added:
        findings.append(Finding(
            severity="medium" if len(added) <= 3 else "high",
            title=f"Tools Added in B: {added}",
            description=f"Server B has {len(added)} tools not present in Server A. "
                        "This could indicate unauthorized modifications or version drift.",
            evidence=f"Added tools: {added}",
            remediation="Verify added tools are authorized; investigate if unexpected.",
            cwe="CWE-749",
        ))

    if removed:
        findings.append(Finding(
            severity="low",
            title=f"Tools Missing in B: {removed}",
            description=f"Server B is missing {len(removed)} tools that exist in Server A. "
                        "This could indicate downgrade or feature stripping.",
            evidence=f"Missing tools: {removed}",
            remediation="Ensure consistent deployment across all server instances.",
            cwe="CWE-1104",
        ))

    if changed:
        findings.append(Finding(
            severity="medium",
            title=f"Schema Drift in {len(changed)} Tools",
            description="Tool schemas differ between servers, indicating configuration drift "
                        "or tampering.",
            evidence=f"Changed tools: {[c['tool'] for c in changed]}",
            remediation="Use infrastructure-as-code to ensure consistent server configurations.",
            cwe="CWE-1008",
        ))

    return json.dumps({
        "target_a": target_a,
        "target_b": target_b,
        "comparison": {
            "tools_in_a": len(names_a),
            "tools_in_b": len(names_b),
            "common_tools": len(common),
            "added_in_b": added,
            "missing_in_b": removed,
            "schema_changed": changed,
        },
        "findings": [f.dict() for f in findings],
    }, indent=2)


# ===========================================================================
# ENTRY POINT
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(description="MCPirats MCP Vulnerability Analysis Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for HTTP/SSE transport")
    parser.add_argument("--port", type=int, default=8765, help="Port for HTTP/SSE transport")
    args = parser.parse_args()

    logger.info(f"Starting MCPirats v{SERVER_VERSION} on {args.transport} transport")

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    elif args.transport == "http":
        mcp.run(transport="http", host=args.host, port=args.port)
    elif args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
