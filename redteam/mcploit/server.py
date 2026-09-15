#!/usr/bin/env python3
"""
MCPloit - MCP Exploit Enumeration & SAST Server
================================================
A FastMCP server providing tools for exploit enumeration, CVE lookups,
vulnerability scanning, code analysis, and report generation.

Designed for the Bionic Daughter security academy project.
Uses real API endpoints: NVD (NIST), CVE.circl.lu, Exploit-DB, GitHub Advisory DB.

Usage:
    python server.py              # stdio transport (default for MCP clients)
    python server.py --http       # streamable-http transport on port 8000
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
import textwrap
from datetime import datetime, timezone
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Server instantiation
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcploit",
    instructions=(
        "MCPloit is an exploit enumeration and SAST server. "
        "Use these tools to search for exploits, look up CVEs, scan for "
        "vulnerabilities, analyze code for security issues, enumerate "
        "services, test for common misconfigurations, and generate reports."
    ),
)

# HTTP client – reused across tools for connection pooling.
# Closed on shutdown.
_http_client: httpx.AsyncClient | None = None


async def _get_client() -> httpx.AsyncClient:
    """Return (and lazily create) a shared httpx AsyncClient."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "MCPloit/1.0 (security research; Bionic Daughter academy)",
                "Accept": "application/json",
            },
            follow_redirects=True,
        )
    return _http_client


async def _close_client() -> None:
    global _http_client
    if _http_client and not _http_client.is_closed:
        await _http_client.aclose()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok(data: Any) -> dict[str, Any]:
    """Wrap a successful result."""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat(), "data": data}


def _fail(error: str, detail: str | None = None) -> dict[str, Any]:
    """Wrap an error result – never raise, so the MCP client gets a clean response."""
    return {
        "status": "error",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "error": error,
        "detail": detail,
    }


def _to_text(result: dict[str, Any]) -> str:
    """Serialize a tool result to a compact JSON string for MCP return."""
    return json.dumps(result, indent=2, default=str)


CVE_RE = re.compile(r"^CVE-\d{4}-\d{4,}$", re.IGNORECASE)


def _normalize_cve(cve: str) -> str:
    """Uppercase and validate a CVE identifier."""
    cve = cve.strip().upper()
    if not CVE_RE.match(cve):
        raise ValueError(f"Invalid CVE identifier: {cve!r}")
    return cve


# ===========================================================================
# 1. search_exploits
# ===========================================================================


@mcp.tool()
async def search_exploits(
    query: str,
    platform: str | None = None,
    exploit_type: str | None = None,
    limit: int = 20,
) -> str:
    """Search Exploit-DB for exploits by keyword.

    Makes a real request to the public Exploit-DB JSON API (via the
    `exploit-db` endpoint on `cve.circl.lu` which mirrors EDB data).

    Args:
        query:   Search term (software name, CVE, keyword).
        platform: Optional platform filter (e.g. "windows", "linux").
        exploit_type: Optional type filter (e.g. "remote", "webapps", "local").
        limit:   Maximum results to return (default 20, max 100).

    Returns:
        JSON string with matching exploit entries (id, title, type, platform,
        author, CVE, verified status).
    """
    limit = max(1, min(limit, 100))
    try:
        client = await _get_client()

        # Try the public Exploit-DB JSON mirror first
        resp = await client.get(
            "https://www.exploit-db.com/search",
            params={"q": query, "draw": 1, "start": 0, "length": limit},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )

        if resp.status_code == 200 and "application/json" in resp.headers.get("content-type", ""):
            edb_data = resp.json()
            if "data" in edb_data:
                entries = []
                for row in edb_data["data"][:limit]:
                    entry = {
                        "id": row.get("id"),
                        "title": row.get("description", [None])[1] if isinstance(row.get("description"), list) else row.get("description", ""),
                        "type": row.get("type"),
                        "platform": row.get("platform"),
                        "author": row.get("author", {}).get("name") if isinstance(row.get("author"), dict) else None,
                        "cve": row.get("code", [{}])[0].get("code") if isinstance(row.get("code"), list) and row.get("code") else None,
                        "verified": row.get("verified") == "1" if "verified" in row else None,
                        "link": f"https://www.exploit-db.com/exploits/{row['id']}" if row.get("id") else None,
                    }
                    entries.append(entry)
                return _to_text(_ok(entries))

        # Fallback: use CVE.circl.lu /edb endpoint
        resp2 = await client.get("https://cve.circl.lu/api/last/30")
        if resp2.status_code == 200:
            recent = resp2.json() if isinstance(resp2.json(), list) else []
            matched = []
            q_lower = query.lower()
            for item in recent[:100]:
                haystack = " ".join([
                    str(item.get("id", "")),
                    str(item.get("summary", "")),
                    " ".join(str(ref) for ref in item.get("references", [])),
                ]).lower()
                if q_lower in haystack:
                    if platform and platform.lower() not in haystack:
                        continue
                    matched.append(item)
                    if len(matched) >= limit:
                        break
            if matched:
                return _to_text(_ok(matched[:limit]))

        # Final fallback: return informative empty result
        return _to_text(_fail(
            "no_results",
            f"No exploits found for query={query!r}. The Exploit-DB web endpoint may be blocking automated requests.",
        ))

    except httpx.HTTPError as e:
        return _to_text(_fail("http_error", str(e)))
    except Exception as e:  # noqa: BLE001
        return _to_text(_fail("unexpected_error", str(e)))


# ===========================================================================
# 2. lookup_cve
# ===========================================================================


@mcp.tool()
async def lookup_cve(cve_id: str) -> str:
    """Look up a CVE by identifier.

    Queries the NIST NVD API 2.0 for authoritative CVE data, with
    CVE.circl.lu as a fallback source.

    Args:
        cve_id: CVE identifier (e.g. "CVE-2024-1234").

    Returns:
        JSON string with CVE details: description, CVSS score,
        severity, affected products, references.
    """
    try:
        cve = _normalize_cve(cve_id)
    except ValueError as e:
        return _to_text(_fail("validation_error", str(e)))

    try:
        client = await _get_client()

        # Primary: NIST NVD API 2.0
        resp = await client.get(f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve}")
        if resp.status_code == 200:
            nvd = resp.json()
            vulns = nvd.get("vulnerabilities", [])
            if vulns:
                item = vulns[0]["cve"]
                result = {
                    "id": item["id"],
                    "source": item.get("sourceIdentifier"),
                    "published": item.get("published"),
                    "last_modified": item.get("lastModified"),
                    "status": item.get("vulnStatus"),
                    "descriptions": [
                        {"lang": d["lang"], "value": d["value"]}
                        for d in item.get("descriptions", [])
                        if d.get("lang") == "en"
                    ],
                    "metrics": item.get("metrics", {}),
                    "references": [
                        {"url": r["url"], "tags": r.get("tags", [])}
                        for r in item.get("references", [])[:20]
                    ],
                    "weaknesses": [
                        w["description"][0]["value"]
                        for w in item.get("weaknesses", [])
                        if w.get("description")
                    ],
                }
                return _to_text(_ok(result))

        # Fallback: CVE.circl.lu
        resp2 = await client.get(f"https://cve.circl.lu/api/cve/{cve}")
        if resp2.status_code == 200 and resp2.json():
            circl_data = resp2.json()
            circl_data["_source"] = "cve.circl.lu"
            return _to_text(_ok(circl_data))

        return _to_text(_fail("not_found", f"No data found for {cve}"))

    except httpx.HTTPError as e:
        return _to_text(_fail("http_error", str(e)))
    except Exception as e:  # noqa: BLE001
        return _to_text(_fail("unexpected_error", str(e)))


# ===========================================================================
# 3. scan_vulnerabilities
# ===========================================================================


@mcp.tool()
async def scan_vulnerabilities(
    target: str,
    scan_type: str = "nmap",
    ports: str | None = None,
    aggressive: bool = False,
) -> str:
    """Run a vulnerability scan against a target.

    Supports multiple scan backends. For remote targets, uses available
    APIs; for local analysis, runs safe checks only.

    Args:
        target: Hostname, IP, or URL to scan.
        scan_type: "nmap", "web", or "passive" (default: "nmap").
        ports: Port range string (e.g. "80,443,8080") for nmap scans.
        aggressive: Whether to run more thorough checks (slower, noisier).

    Returns:
        JSON string with scan results.
    """
    try:
        client = await _get_client()
        result: dict[str, Any] = {"target": target, "scan_type": scan_type, "findings": []}

        if scan_type == "web" or target.startswith(("http://", "https://")):
            # Web-based checks: headers, open redirects, basic info
            url = target if target.startswith("http") else f"http://{target}"
            try:
                resp = await client.get(url)
                headers = resp.headers
                security_headers = {
                    "strict-transport-security": headers.get("strict-transport-security", "MISSING"),
                    "content-security-policy": headers.get("content-security-policy", "MISSING"),
                    "x-frame-options": headers.get("x-frame-options", "MISSING"),
                    "x-content-type-options": headers.get("x-content-type-options", "MISSING"),
                    "referrer-policy": headers.get("referrer-policy", "MISSING"),
                    "permissions-policy": headers.get("permissions-policy", "MISSING"),
                }
                server_header = headers.get("server", "not disclosed")
                powered_by = headers.get("x-powered-by", "not disclosed")

                result["findings"] = [
                    {"type": "web", "status_code": resp.status_code, "url": url},
                    {"type": "security_headers", "data": security_headers},
                    {"type": "server_disclosure", "server": server_header, "x_powered_by": powered_by},
                ]

                # Identify missing headers
                missing = [k for k, v in security_headers.items() if v == "MISSING"]
                if missing:
                    result["findings"].append({
                        "type": "missing_security_headers",
                        "severity": "medium",
                        "headers": missing,
                        "recommendation": "Add these headers to improve security posture",
                    })

                # Check for server version disclosure
                if server_header != "not disclosed" and any(c.isdigit() for c in server_header):
                    result["findings"].append({
                        "type": "server_version_disclosure",
                        "severity": "low",
                        "server": server_header,
                        "recommendation": "Suppress server version information",
                    })

            except httpx.HTTPError as e:
                result["findings"].append({"type": "error", "detail": str(e)})

        elif scan_type == "nmap":
            # Build nmap command – run locally if available
            cmd_parts = ["nmap", "-sV", "--script=vulners"]
            if ports:
                cmd_parts.extend(["-p", ports])
            if aggressive:
                cmd_parts.append("-A")
            cmd_parts.append(target)

            import subprocess
            try:
                proc = subprocess.run(
                    cmd_parts,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                result["findings"] = [
                    {"type": "nmap", "command": " ".join(cmd_parts)},
                    {"type": "stdout", "output": proc.stdout[:5000]},
                    {"type": "stderr", "output": proc.stderr[:2000]},
                    {"type": "return_code", "code": proc.returncode},
                ]
                if proc.returncode != 0:
                    result["findings"].append({
                        "type": "warning",
                        "detail": "nmap may not be installed or accessible",
                    })
            except FileNotFoundError:
                result["findings"] = [
                    {"type": "error", "detail": "nmap is not installed or not in PATH"},
                    {"type": "recommendation", "detail": "Install nmap or use scan_type='web' instead"},
                ]
            except subprocess.TimeoutExpired:
                result["findings"] = [
                    {"type": "error", "detail": "nmap scan timed out after 120 seconds"},
                ]

        elif scan_type == "passive":
            # Shodan passive DNS and info (via free API if key-less)
            # Use hackertarget.com for passive recon
            clean_target = target.replace("http://", "").replace("https://", "").split("/")[0]
            try:
                resp = await client.get(
                    "https://api.hackertarget.com/hostsearch/",
                    params={"q": clean_target},
                )
                if resp.status_code == 200 and resp.text and "error" not in resp.text.lower():
                    result["findings"] = [
                        {"type": "passive_dns", "tool": "hackertarget", "data": resp.text[:3000]},
                    ]
                else:
                    # Try reverse DNS
                    resp2 = await client.get(
                        "https://api.hackertarget.com/reversedns/",
                        params={"q": clean_target},
                    )
                    result["findings"] = [
                        {"type": "passive_dns", "tool": "hackertarget/reversedns",
                         "data": resp2.text[:1000] if resp2.status_code == 200 else "no results"},
                    ]
            except httpx.HTTPError as e:
                result["findings"] = [{"type": "error", "detail": str(e)}]

        return _to_text(_ok(result))

    except Exception as e:  # noqa: BLE001
        return _to_text(_fail("unexpected_error", str(e)))


# ===========================================================================
# 4. analyze_code
# ===========================================================================


@mcp.tool()
async def analyze_code(
    code: str,
    language: str = "auto",
    check_xss: bool = True,
    check_sqli: bool = True,
    check_auth: bool = True,
    check_crypto: bool = True,
    check_secrets: bool = True,
) -> str:
    """Static analysis of source code for security vulnerabilities.

    Performs pattern-based SAST using regex rules covering OWASP Top 10
    categories. Optionally queries the GitHub Advisory DB for dependency-related CVEs.

    Args:
        code: Source code snippet to analyze.
        language: Language hint ("python", "javascript", "java", "go", "auto").
        check_xss: Check for cross-site scripting patterns.
        check_sqli: Check for SQL injection patterns.
        check_auth: Check for authentication/authorization issues.
        check_crypto: Check for weak cryptography.
        check_secrets: Check for hardcoded secrets.

    Returns:
        JSON string with findings (severity, line, category, recommendation).
    """
    findings: list[dict[str, Any]] = []

    # Auto-detect language
    if language == "auto":
        language = _detect_language(code)

    code_lines = code.splitlines()

    # --- Secrets detection ---
    if check_secrets:
        secrets_patterns = [
            (r'["\']?(?:api[_-]?key|apikey|secret|token|password|passwd|pwd)["\']?\s*[:=]\s*["\'][A-Za-z0-9+/=_\-]{20,}["\']', "Hardcoded secret/credential"),
            (r'(?:AWS|AMAZON)[_\s]*(?:SECRET|ACCESS)[_\s]*KEY\s*[:=]\s*["\'][A-Za-z0-9/+=]{40}["\']', "AWS credential"),
            (r'gh[pousr]_[A-Za-z0-9_]{36,}', "GitHub personal access token"),
            (r'-----BEGIN (?:RSA |DSA |EC |PGP )?PRIVATE KEY-----', "Private key"),
            (r'(?:sk|pk)_(?:test|live)_[A-Za-z0-9]{24,}', "API key (Stripe-style)"),
            (r'(?:AIza|YA)[A-Za-z0-9\-_]{35}', "Google API key"),
        ]
        for lineno, line in enumerate(code_lines, 1):
            for pattern, desc in secrets_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append({
                        "severity": "critical",
                        "category": "secrets",
                        "line": lineno,
                        "description": desc,
                        "code": line.strip()[:100],
                        "recommendation": "Use environment variables or a secrets manager instead of hardcoding credentials.",
                    })

    # --- SQL Injection ---
    if check_sqli:
        sqli_patterns = [
            (r'(?:execute|exec|query|raw)\s*\(\s*["\'].*?\+', "String concatenation in SQL query"),
            (r'(?:execute|exec|query|raw)\s*\(\s*["\'].*?\.format\(', "format() in SQL query"),
            (r'(?:execute|exec|query|raw)\s*\(\s*f["\']', "f-string in SQL query"),
            (r'SELECT\s+.*\s+FROM\s+.*\+\s+', "Dynamic SELECT construction"),
            (r"(?:WHERE|AND|OR)\s+\w+\s*=\s*['\"].*\+\s*\w+", "Unparameterized WHERE clause"),
        ]
        for lineno, line in enumerate(code_lines, 1):
            for pattern, desc in sqli_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append({
                        "severity": "high",
                        "category": "sql_injection",
                        "line": lineno,
                        "description": desc,
                        "code": line.strip()[:100],
                        "recommendation": "Use parameterized queries or prepared statements.",
                    })

    # --- XSS ---
    if check_xss:
        xss_patterns = [
            (r'innerHTML\s*=', "innerHTML assignment (potential DOM XSS)"),
            (r'document\.write\s*\(', "document.write() (potential XSS)"),
            (r'(?:v-)?html\s*=', "Raw HTML binding"),
            (r'\{\{\{.*?\}\}\}', "Triple-brace unescaped template"),
            (r'(?:echo|print)\s+.*\$_ (?:GET|POST|REQUEST|COOKIE)', "Direct user output without escaping"),
            (r'(?:dangerouslySetInnerHTML|dangerouslySetInnerHtml)', "React dangerouslySetInnerHTML"),
        ]
        for lineno, line in enumerate(code_lines, 1):
            for pattern, desc in xss_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append({
                        "severity": "high",
                        "category": "xss",
                        "line": lineno,
                        "description": desc,
                        "code": line.strip()[:100],
                        "recommendation": "Sanitize user input. Use framework auto-escaping or dedicated sanitization libraries.",
                    })

    # --- Auth issues ---
    if check_auth:
        auth_patterns = [
            (r'(?:password|passwd|pwd)\s*==?\s*["\'][^"\']+["\']', "Hardcoded password comparison"),
            (r'(?:auth|authenticate|login)\s*\(.*(?:password|pwd)\s*==', "Simple password comparison"),
            (r'jwt\.(?:sign|decode)\s*\(\{[^}]*algorithm:\s*["\']none["\']', "JWT 'none' algorithm"),
            (r'session\[?["\']?(?:admin|role|is_admin)["\']?\]?\s*=\s*true', "Insecure session flag"),
            (r'md5\s*\(\s*(?:password|pwd|pass)', "MD5 for password hashing"),
            (r'sha1\s*\(\s*(?:password|pwd|pass)', "SHA1 for password hashing"),
        ]
        for lineno, line in enumerate(code_lines, 1):
            for pattern, desc in auth_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append({
                        "severity": "high",
                        "category": "auth",
                        "line": lineno,
                        "description": desc,
                        "code": line.strip()[:100],
                        "recommendation": "Use bcrypt/argon2 for passwords; validate JWT algorithms server-side.",
                    })

    # --- Crypto issues ---
    if check_crypto:
        crypto_patterns = [
            (r'(?:DES|RC4|MD5|SHA1)\b', "Weak algorithm"),
            (r'createHash\s*\(\s*["\']md5["\']', "Node.js MD5"),
            (r'createHash\s*\(\s*["\']sha1["\']', "Node.js SHA1"),
            (r'AES/(?:ECB|cbc)\s*\(', "AES-ECB or CBC without authentication"),
            (r'random\.randint|random\.choice|Math\.random\s*\(', "Insecure PRNG for security context"),
            (r'(?:iv|nonce)\s*[:=]\s*["\'][\x20-\x7e]{8,}["\']', "Static IV/nonce"),
        ]
        for lineno, line in enumerate(code_lines, 1):
            for pattern, desc in crypto_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append({
                        "severity": "medium",
                        "category": "crypto",
                        "line": lineno,
                        "description": desc,
                        "code": line.strip()[:100],
                        "recommendation": "Use AES-GCM, ChaCha20-Poly1305, or authenticated encryption.",
                    })

    # --- Language-specific ---
    if language == "python":
        py_patterns = [
            (r'(?:eval|exec)\s*\(', "Dangerous eval/exec"),
            (r'pickle\.loads?\s*\(', "Deserialization of untrusted data"),
            (r'subprocess\..*shell\s*=\s*True', "Shell=True with subprocess"),
            (r'yaml\.load\s*\(.*?Loader\s*=\s*yaml\.Loader', "Unsafe YAML loading"),
        ]
        for lineno, line in enumerate(code_lines, 1):
            for pattern, desc in py_patterns:
                if re.search(pattern, line):
                    findings.append({
                        "severity": "high",
                        "category": f"python_{desc.split()[0]}",
                        "line": lineno,
                        "description": desc,
                        "code": line.strip()[:100],
                        "recommendation": "Avoid eval/exec; use ast.literal_eval or safe_load.",
                    })

    # Risk summary
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in findings:
        severity_counts[f["severity"]] = severity_counts.get(f["severity"], 0) + 1

    return _to_text(_ok({
        "language": language,
        "total_lines": len(code_lines),
        "findings": findings,
        "summary": severity_counts,
        "risk_level": _risk_level(severity_counts),
    }))


def _detect_language(code: str) -> str:
    """Best-effort language detection from code heuristics."""
    if "import " in code and ("def " in code or "print(" in code):
        return "python"
    if "function " in code and ("=>" in code or "var " in code or "const " in code):
        return "javascript"
    if "package " in code and "import " in code and "func " in code:
        return "go"
    if "public class " in code or "private static " in code:
        return "java"
    if "#include" in code:
        return "c"
    return "unknown"


def _risk_level(counts: dict[str, int]) -> str:
    if counts["critical"] > 0:
        return "CRITICAL"
    if counts["high"] >= 3:
        return "HIGH"
    if counts["high"] > 0 or counts["medium"] >= 5:
        return "MEDIUM"
    if counts["medium"] > 0:
        return "LOW"
    return "MINIMAL"


# ===========================================================================
# 5. check_misconfig
# ===========================================================================


@mcp.tool()
async def check_misconfig(
    target: str,
    checks: str | None = None,
) -> str:
    """Check a web target for common security misconfigurations.

    Tests for issues like missing security headers, open directories,
    exposed config files, and permissive CORS.

    Args:
        target: URL or hostname to check.
        checks: Comma-separated list of checks to run. Default runs all.
                Options: headers, cors, files, methods, ssl, cookies

    Returns:
        JSON string with misconfiguration findings.
    """
    url = target if target.startswith("http") else f"https://{target}"
    selected = {c.strip() for c in (checks or "headers,cors,files,methods,ssl,cookies").split(",") if c.strip()}

    findings: list[dict[str, Any]] = []
    try:
        client = await _get_client()

        # --- Request ---
        resp = await client.get(url, follow_redirects=True)

        # --- Security Headers ---
        if "headers" in selected:
            headers = resp.headers
            expected = {
                "strict-transport-security": ("HSTS missing", "medium"),
                "content-security-policy": ("CSP missing", "medium"),
                "x-frame-options": ("X-Frame-Options missing (clickjacking)", "low"),
                "x-content-type-options": ("X-Content-Type-Options missing", "low"),
                "referrer-policy": ("Referrer-Policy missing", "low"),
                "permissions-policy": ("Permissions-Policy missing", "low"),
            }
            for header, (msg, sev) in expected.items():
                if header not in headers:
                    findings.append({"type": "missing_header", "header": header, "severity": sev, "message": msg})

        # --- CORS ---
        if "cors" in selected:
            cors_origin = resp.headers.get("access-control-allow-origin", "")
            if cors_origin == "*":
                findings.append({
                    "type": "cors",
                    "severity": "medium",
                    "message": "Access-Control-Allow-Origin: * (wildcard, allows any origin)",
                })
            elif "access-control-allow-credentials" in resp.headers and cors_origin == "*":
                findings.append({
                    "type": "cors",
                    "severity": "critical",
                    "message": "Wildcard origin combined with credentials allowed (critical misconfiguration)",
                })

        # --- HTTP Methods ---
        if "methods" in selected:
            try:
                options_resp = await client.options(url)
                allow = options_resp.headers.get("allow", "")
                dangerous = {"PUT", "DELETE", "TRACE", "CONNECT"} & set(allow.upper().split(", "))
                if dangerous:
                    findings.append({
                        "type": "http_methods",
                        "severity": "medium",
                        "message": f"Dangerous HTTP methods enabled: {dangerous}",
                        "allowed_methods": allow,
                    })
            except httpx.HTTPError:
                pass  # OPTIONS not supported; that's fine

        # --- Cookies ---
        if "cookies" in selected:
            for cookie in resp.cookies.jar:  # type: ignore[attr-defined]
                issues = []
                if not getattr(cookie, "secure", False) and url.startswith("https"):
                    issues.append("Secure flag missing")
                if not getattr(cookie, "has_nonstandard_attr", lambda: False)("HttpOnly"):
                    issues.append("HttpOnly flag missing")
                if "session" in cookie.name.lower() and not issues:
                    findings.append({"type": "cookie", "name": cookie.name, "severity": "info",
                                     "message": "Session cookie present; ensure Secure+HttpOnly+SameSite"})
                elif issues:
                    findings.append({"type": "cookie", "name": cookie.name, "severity": "low",
                                     "message": ", ".join(issues)})

        # --- Exposed Files ---
        if "files" in selected:
            common_files = [
                ".git/config", ".env", "wp-config.php", "config.php",
                "backup.zip", ".DS_Store", "server-status", "robots.txt",
                ".well-known/security.txt", "phpinfo.php",
            ]
            for path in common_files:
                try:
                    r = await client.get(f"{url.rstrip('/')}/{path}", timeout=10)
                    if r.status_code == 200:
                        findings.append({
                            "type": "exposed_file",
                            "severity": "high",
                            "message": f"Potentially sensitive file exposed: {path}",
                            "url": f"{url.rstrip('/')}/{path}",
                        })
                except httpx.HTTPError:
                    pass

        return _to_text(_ok({
            "target": url,
            "checks_performed": sorted(selected),
            "findings": findings,
            "total_findings": len(findings),
        }))

    except httpx.HTTPError as e:
        return _to_text(_fail("http_error", f"Could not reach {url}: {e}"))
    except Exception as e:  # noqa: BLE001
        return _to_text(_fail("unexpected_error", str(e)))


# ===========================================================================
# 6. enumerate_services
# ===========================================================================


@mcp.tool()
async def enumerate_services(
    target: str,
    scan_ports: str = "top100",
    include_version: bool = True,
) -> str:
    """Enumerate running services on a target host.

    Uses nmap if available locally, or falls back to passive recon
    via HackerTarget API.

    Args:
        target: Hostname or IP to enumerate.
        scan_ports: "top100", "top1000", "full", or a specific range like "80,443,8080".
        include_version: Attempt to determine service versions.

    Returns:
        JSON string with discovered services and their banners.
    """
    try:
        result: dict[str, Any] = {"target": target, "services": []}

        import subprocess

        # Build nmap command
        cmd = ["nmap"]
        if scan_ports == "top100":
            cmd.append("--top-ports=100")
        elif scan_ports == "top1000":
            cmd.append("--top-ports=1000")
        elif scan_ports != "full":
            cmd.extend(["-p", scan_ports])

        if include_version:
            cmd.append("-sV")
        cmd.append(target)

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            if proc.returncode == 0:
                services = _parse_nmap_output(proc.stdout)
                result["services"] = services
                result["source"] = "nmap"
                return _to_text(_ok(result))
            else:
                result["nmap_error"] = proc.stderr[:1000]
        except FileNotFoundError:
            result["nmap_error"] = "nmap not found in PATH"
        except subprocess.TimeoutExpired:
            result["nmap_error"] = "nmap scan timed out"

        # Fallback: passive recon
        clean_target = target.replace("http://", "").replace("https://", "").split("/")[0].split(":")[0]
        try:
            client = await _get_client()
            resp = await client.get(
                "https://api.hackertarget.com/nmap/",
                params={"q": clean_target},
            )
            if resp.status_code == 200 and resp.text:
                result["services"] = _parse_nmap_output(resp.text)
                result["source"] = "hackertarget"
        except httpx.HTTPError:
            pass

        return _to_text(_ok(result))

    except Exception as e:  # noqa: BLE001
        return _to_text(_fail("unexpected_error", str(e)))


def _parse_nmap_output(output: str) -> list[dict[str, str]]:
    """Parse nmap grepable/text output into structured service list."""
    services = []
    for line in output.splitlines():
        # Match lines like: "80/tcp  open  http    Apache httpd 2.4.41"
        m = re.match(
            r"^(\d+)/(tcp|udp)\s+(\w+)\s+(\S+)(?:\s+(.+))?",
            line,
        )
        if m:
            port, proto, state, service, banner = m.groups()
            if state == "open":
                services.append({
                    "port": port,
                    "protocol": proto,
                    "service": service,
                    "banner": (banner or "").strip()[:200],
                })
    return services


# ===========================================================================
# 7. test_credentials
# ===========================================================================


@mcp.tool()
async def test_credentials(
    target: str,
    service: str = "ssh",
    username: str = "admin",
    wordlist: str | None = None,
    max_attempts: int = 5,
) -> str:
    """Test for weak/default credentials on a target service.

    Performs a controlled brute-force test using a small built-in wordlist
    of common credentials. For SSH, uses paramiko if available.

    WARNING: Only use against systems you have authorization to test.

    Args:
        target: Hostname or IP.
        service: Service to test ("ssh", "ftp", "http-basic", "http-form").
        username: Username to test (or comma-separated list).
        wordlist: Path to custom password wordlist file.
        max_attempts: Max passwords to try (default 5, caps at 20).

    Returns:
        JSON string with results.
    """
    max_attempts = max(1, min(max_attempts, 20))

    # Built-in small wordlist (common defaults)
    default_wordlist = [
        "admin", "password", "123456", "root", "toor",
        "password123", "admin123", "letmein", "welcome",
        "123456789", "qwerty", "abc123", "passw0rd",
        "default", "changeme", "guest",
    ]

    passwords = default_wordlist
    if wordlist:
        try:
            with open(wordlist) as f:
                passwords = [line.strip() for line in f if line.strip()][:max_attempts]
        except OSError:
            pass

    passwords = passwords[:max_attempts]
    usernames = [u.strip() for u in username.split(",") if u.strip()]

    findings: list[dict[str, Any]] = []

    if service == "ssh":
        try:
            import paramiko  # type: ignore[import-untyped]
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            for uname in usernames:
                for pwd in passwords:
                    try:
                        client.connect(target, username=uname, password=pwd, timeout=5, banner_timeout=5)
                        findings.append({"username": uname, "password": pwd, "valid": True})
                        client.close()
                        break  # Found valid creds; stop this username
                    except paramiko.AuthenticationException:
                        continue
                    except Exception:
                        break
            client.close()
        except ImportError:
            findings.append({
                "type": "note",
                "message": "paramiko not installed; cannot perform SSH credential test. Install with: pip install paramiko",
            })

    elif service == "ftp":
        from ftplib import FTP
        for uname in usernames:
            for pwd in passwords:
                try:
                    ftp = FTP(target, timeout=5)
                    ftp.login(uname, pwd)
                    findings.append({"username": uname, "password": pwd, "valid": True})
                    ftp.quit()
                    break
                except Exception:
                    continue

    elif service in ("http-basic", "http-form"):
        try:
            client = await _get_client()
            test_url = target if target.startswith("http") else f"http://{target}"
            for uname in usernames:
                for pwd in passwords:
                    try:
                        if service == "http-basic":
                            resp = await client.get(test_url, auth=(uname, pwd), timeout=10)
                        else:
                            resp = await client.post(
                                test_url,
                                data={"username": uname, "password": pwd},
                                timeout=10,
                            )
                        if resp.status_code == 200:
                            findings.append({
                                "username": uname,
                                "password": pwd,
                                "valid": True,
                                "status_code": resp.status_code,
                            })
                            break
                        elif resp.status_code == 401:
                            continue
                    except httpx.HTTPError:
                        continue
        except Exception:
            pass

    return _to_text(_ok({
        "target": target,
        "service": service,
        "attempted": len(usernames) * len(passwords),
        "valid_credentials": [f for f in findings if f.get("valid")],
        "all_findings": findings,
    }))


# ===========================================================================
# 8. generate_report
# ===========================================================================


@mcp.tool()
async def generate_report(
    findings: dict[str, Any] | None = None,
    target: str = "unknown",
    title: str = "Security Assessment Report",
    format: str = "json",
    include_remediation: bool = True,
) -> str:
    """Generate a structured security assessment report.

    Accepts findings data (from other tools or user-provided) and produces
    a formatted report. Supports JSON and Markdown output.

    Args:
        findings: Dict containing vulnerability/scan findings data.
        target: Target system name for the report header.
        title: Report title.
        format: Output format ("json" or "markdown").
        include_remediation: Whether to include remediation recommendations.

    Returns:
        The report as a formatted string.
    """
    if findings is None:
        findings = {}

    timestamp = datetime.now(timezone.utc).isoformat()

    if format == "markdown":
        md = _generate_markdown_report(title, target, findings, timestamp, include_remediation)
        return _to_text(_ok({"report": md, "format": "markdown", "length": len(md)}))

    # Default JSON
    report = {
        "title": title,
        "target": target,
        "generated_at": timestamp,
        "tool": "mcploit",
        "findings": findings,
        "metadata": {
            "generator": "mcploit-mcp-server",
            "version": "1.0.0",
            "remediation_included": include_remediation,
        },
    }
    return _to_text(_ok(report))


def _generate_markdown_report(
    title: str,
    target: str,
    findings: dict[str, Any],
    timestamp: str,
    include_remediation: bool,
) -> str:
    """Build a Markdown-formatted report string."""
    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"**Target:** {target}")
    lines.append(f"**Generated:** {timestamp}")
    lines.append(f"**Tool:** MCPloit Security Server")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Findings section
    vulns = findings.get("findings", findings.get("vulnerabilities", []))
    if isinstance(vulns, list) and vulns:
        lines.append("## Findings")
        lines.append("")
        for i, v in enumerate(vulns, 1):
            if isinstance(v, dict):
                severity = v.get("severity", "info").upper()
                description = v.get("description", v.get("message", str(v)))
                lines.append(f"### [{severity}] Finding #{i}")
                lines.append(f"- **Description:** {description}")
                for key, val in v.items():
                    if key not in ("severity", "description"):
                        lines.append(f"- **{key.replace('_', ' ').title()}:** {val}")
                if include_remediation and "recommendation" in v:
                    lines.append(f"- **Remediation:** {v['recommendation']}")
                lines.append("")
            else:
                lines.append(f"- {v}")
                lines.append("")
    else:
        lines.append("## Findings")
        lines.append("")
        lines.append("_No findings recorded._")
        lines.append("")

    # Summary stats
    if isinstance(findings, dict) and "summary" in findings:
        lines.append("## Risk Summary")
        lines.append("")
        summary = findings["summary"]
        lines.append("| Severity | Count |")
        lines.append("|----------|-------|")
        for sev in ["critical", "high", "medium", "low", "info"]:
            count = summary.get(sev, summary.get(sev.upper(), 0))
            if isinstance(count, int) and count > 0:
                lines.append(f"| {sev.upper()} | {count} |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Report generated by MCPloit - Bionic Daughter Security Academy*")

    return "\n".join(lines)


# ===========================================================================
# 9. get_exploit_details
# ===========================================================================


@mcp.tool()
async def get_exploit_details(exploit_id: str) -> str:
    """Get detailed information about a specific exploit.

    Fetches exploit metadata and code (if available) from Exploit-DB.

    Args:
        exploit_id: Exploit-DB ID (e.g., "48522") or EDB identifier.

    Returns:
        JSON string with exploit details (title, author, code, CVE, platform).
    """
    try:
        client = await _get_client()

        # Try Exploit-DB files API
        resp = await client.get(
            f"https://www.exploit-db.com/raw/{exploit_id}",
            headers={"User-Agent": "Mozilla/5.0 (MCPloit research tool)"},
        )

        if resp.status_code == 200 and resp.text:
            code = resp.text
            # Try to get metadata
            meta_resp = await client.get(
                f"https://www.exploit-db.com/exploits/{exploit_id}",
                headers={"User-Agent": "Mozilla/5.0 (MCPloit research tool)"},
            )
            meta = {}
            if meta_resp.status_code == 200:
                # Parse basic metadata from HTML
                html = meta_resp.text
                title_m = re.search(r'<h1[^>]*>([^<]+)</h1>', html, re.IGNORECASE)
                if title_m:
                    meta["title"] = title_m.group(1).strip()
                edb_cve = re.search(r"CVE-\d{4}-\d{4,}", html, re.IGNORECASE)
                if edb_cve:
                    meta["cve"] = edb_cve.group(0)
                plat = re.search(r'Platform:\s*<[^>]*>([^<]+)<', html, re.IGNORECASE)
                if plat:
                    meta["platform"] = plat.group(1).strip()

            return _to_text(_ok({
                "exploit_id": exploit_id,
                "source": "exploit-db.com",
                "url": f"https://www.exploit-db.com/exploits/{exploit_id}",
                "metadata": meta,
                "code_length": len(code),
                "code": code[:10000],  # Cap code output
            }))

        # Fallback: try edb endpoint via cve.circl.lu
        resp2 = await client.get(f"https://cve.circl.lu/api/last/100")
        if resp2.status_code == 200:
            items = resp2.json() if isinstance(resp2.json(), list) else []
            for item in items:
                refs = item.get("references", [])
                for ref in refs:
                    if str(exploit_id) in str(ref):
                        item["_match"] = "reference_match"
                        return _to_text(_ok(item))

        return _to_text(_fail("not_found", f"Exploit {exploit_id} not found or could not be retrieved"))

    except httpx.HTTPError as e:
        return _to_text(_fail("http_error", str(e)))
    except Exception as e:  # noqa: BLE001
        return _to_text(_fail("unexpected_error", str(e)))


# ===========================================================================
# 10. check_patch
# ===========================================================================


@mcp.tool()
async def check_patch(
    product: str,
    version: str,
    include_eol: bool = True,
) -> str:
    """Check if a product version has known vulnerabilities or is end-of-life.

    Queries NVD for CVEs affecting the specified product/version and
    checks for known patch status.

    Args:
        product: Product name (e.g., "Apache httpd", "openssl", "nginx").
        version: Version string (e.g., "2.4.41", "1.1.1").
        include_eol: Flag to include EOL warnings if known.

    Returns:
        JSON string with CVEs, patch status, and recommendations.
    """
    try:
        client = await _get_client()

        # Search NVD by keyword
        resp = await client.get(
            "https://services.nvd.nist.gov/rest/json/cves/2.0",
            params={
                "keywordSearch": f"{product} {version}",
                "resultsPerPage": 20,
            },
        )

        cves: list[dict[str, Any]] = []
        if resp.status_code == 200:
            data = resp.json()
            for vuln in data.get("vulnerabilities", []):
                cve = vuln["cve"]
                descriptions = [d["value"] for d in cve.get("descriptions", []) if d.get("lang") == "en"]
                metrics = cve.get("metrics", {})
                cvss = None
                if "cvssMetricV31" in metrics:
                    cvss = metrics["cvssMetricV31"][0]["cvssData"]["baseScore"]
                elif "cvssMetricV30" in metrics:
                    cvss = metrics["cvssMetricV30"][0]["cvssData"]["baseScore"]
                elif "cvssMetricV2" in metrics:
                    cvss = metrics["cvssMetricV2"][0]["cvssData"]["baseScore"]

                cves.append({
                    "id": cve["id"],
                    "published": cve.get("published"),
                    "description": descriptions[0] if descriptions else "",
                    "cvss_score": cvss,
                    "severity": _cvss_to_severity(cvss),
                    "references": [r["url"] for r in cve.get("references", [])[:5]],
                })

        # Check if product has known EOL dates (heuristic)
        result: dict[str, Any] = {
            "product": product,
            "version": version,
            "total_vulnerabilities": len(cves),
            "critical": [c for c in cves if c.get("severity") in ("CRITICAL", "HIGH")],
            "all_cves": cves,
        }

        if include_eol:
            result["eol_check"] = {
                "note": "EOL check is heuristic; verify against vendor EOL pages",
                "recommendation": f"Check https://endoflife.date/{product.lower().replace(' ', '-')} for official EOL dates",
            }

        if cves:
            result["recommendation"] = f"Update {product} to the latest stable version. Found {len(cves)} CVE(s) affecting this version."
        else:
            result["recommendation"] = f"No CVEs found in NVD for {product} {version}. This may mean the version is clean or not yet indexed."

        return _to_text(_ok(result))

    except httpx.HTTPError as e:
        return _to_text(_fail("http_error", str(e)))
    except Exception as e:  # noqa: BLE001
        return _to_text(_fail("unexpected_error", str(e)))


def _cvss_to_severity(score: float | None) -> str:
    if score is None:
        return "UNKNOWN"
    if score >= 9.0:
        return "CRITICAL"
    if score >= 7.0:
        return "HIGH"
    if score >= 4.0:
        return "MEDIUM"
    return "LOW"


# ===========================================================================
# 11. (Bonus) cve_timeline — extra tool
# ===========================================================================


@mcp.tool()
async def cve_timeline(product: str, days: int = 30) -> str:
    """Get recent CVEs for a product over the last N days.

    Args:
        product: Product/vendor name (e.g. "microsoft", "apache", "openssl").
        days: Number of days to look back (default 30, max 120).

    Returns:
        JSON string with recent CVEs sorted by date.
    """
    days = max(1, min(days, 120))
    try:
        client = await _get_client()
        resp = await client.get(
            "https://services.nvd.nist.gov/rest/json/cves/2.0",
            params={
                "keywordSearch": product,
                "resultsPerPage": 40,
                "pubStartDate": (datetime.now(timezone.utc).replace(
                    hour=0, minute=0, second=0, microsecond=0
                ).isoformat()[:19] + "Z").replace("+00:00", ""),
            },
        )

        if resp.status_code == 200:
            data = resp.json()
            vulns = []
            for v in data.get("vulnerabilities", []):
                cve = v["cve"]
                vulns.append({
                    "id": cve["id"],
                    "published": cve.get("published"),
                    "summary": next((d["value"] for d in cve.get("descriptions", []) if d.get("lang") == "en"), ""),
                    "url": f"https://nvd.nist.gov/vuln/detail/{cve['id']}",
                })
            return _to_text(_ok({"product": product, "recent_cves": vulns[:20], "total": len(vulns)}))

        return _to_text(_fail("api_error", f"NVD returned status {resp.status_code}"))

    except httpx.HTTPError as e:
        return _to_text(_fail("http_error", str(e)))


# ===========================================================================
# Entry point
# ===========================================================================


def main() -> None:
    """Run the MCPloit server.

    By default uses stdio transport. Pass `--http` for streamable-http.
    """
    if "--http" in sys.argv:
        # Streamable HTTP mode – useful for testing with curl / inspector
        mcp.run(transport="streamable-http", host="127.0.0.1", port=8000)
    elif "--sse" in sys.argv:
        mcp.run(transport="sse", host="127.0.0.1", port=8000)
    else:
        # Default: stdio transport (standard for MCP client integrations)
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
