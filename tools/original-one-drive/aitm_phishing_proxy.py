#!/usr/bin/env python3
"""
aitm_phishing_proxy.py - Adversary-in-the-Middle Phishing Proxy v2.0.0
=========================================================================
AITM proxy for analyzing phishing attacks in authorized lab environments.
Intercepts, logs, and analyzes HTTP(S) traffic to detect credential
harvesting, session token theft, and MFA bypass patterns.

For AUTHORIZED PENETRATION TESTING against owned targets only.

Usage: python aitm_phishing_proxy.py --listen 127.0.0.1:8080

Author: bionic daughter (trained by Dad/Rigoberto Gomez)
"""

import argparse
import asyncio
import base64
import datetime
import hashlib
import json
import logging
import os
import re
import signal
import socket
import ssl
import sys
import threading
import time
import uuid
from collections import deque, defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime as dt_mod
from enum import Enum
from pathlib import Path
from typing import Optional, Callable, Any, List, Dict, Tuple

logger = logging.getLogger("aitm_proxy")
VERSION = "2.0.0"
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class CaptureCategory(str, Enum):
    CREDENTIAL_USERNAME = "credential_username"
    CREDENTIAL_PASSWORD = "credential_password"
    CREDENTIAL_MFA_OTP = "credential_mfa_otp"
    CREDENTIAL_PASSCODE = "credential_passcode"
    COOKIE_SESSION = "cookie_session"
    COOKIE_AUTH = "cookie_auth"
    COOKIE_TRACKING = "cookie_tracking"
    COOKIE_OTHER = "cookie_other"
    HEADER_TOKEN = "header_token"
    BODY_TOKEN = "body_token"
    FORM_FIELD_SENSITIVE = "form_field_sensitive"
    MFA_FACTOR_SMS = "mfa_sms"
    MFA_FACTOR_APP = "mfa_app"
    MFA_FACTOR_HARDWARE = "mfa_hardware"
    MFA_FACTOR_EMAIL = "mfa_email"
    MFA_FACTOR_OTP = "mfa_otp"
    SESSION_ID = "session_id"
    PII_NAME = "pii_name"
    PII_EMAIL = "pii_email"
    PII_PHONE = "pii_phone"
    PII_ADDRESS = "pii_address"
    PII_OTHER = "pii_other"
    FINANCIAL_CARD = "financial_card"
    FINANCIAL_ACCOUNT = "financial_account"
    FINANCIAL_OTHER = "financial_other"
    PHISHING_KIT_FINGERPRINT = "phishing_kit_fingerprint"
    DOMAIN_SPOOF = "domain_spoof"
    UNCLASSIFIED = "unclassified"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class PhishingKitFamily(str, Enum):
    EVILGINX = "evilginx"
    PHISHING_KEY = "phishing_key"
    MODULAR_PHISHER = "modular_phisher"
    CUSTOM = "custom"
    UNKNOWN = "unknown"


# --- Detector patterns ---
EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', re.IGNORECASE)
PHONE_RE = re.compile(r'(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}')

CARD_RE = re.compile(
    r'\b(?:4[0-9]{12}(?:[0-9]{3})?|'
    r'5[1-5][0-9]{14}|'
    r'3[47][0-9]{13}|'
    r'6(?:011|5[0-9]{2})[0-9]{12}|'
    r'35(?:2[0-9]{4}|[3-6][0-9]{5})[0-9]{12}|'
    r'30[0-5][0-9]{11,15}|'
    r'3[8-9][0-9]{14})\b'
)

TOKEN_LIKE_RE = re.compile(
    r'(?i)(?:'
    r'bearer\s+[a-z0-9\-._~+/]+=*'
    r'|jwt\s*[:=]\s*[a-z0-9\-._~+/]+=*'
    r'|eyJ[a-z0-9\-._~+/]+=*'
    r'|token\s*[:=]\s*[\'"]?[a-zA-Z0-9\-._~+/]{20,}'
    r'|session[_\s-]*id\s*[:=]\s*[\'"]?[a-zA-Z0-9\-._~+/]{10,}'
    r'|sid\s*[:=]\s*[\'"]?[a-zA-Z0-9\-._~+/]{8,}'
    r')'
)


SESSION_COOKIE_NAMES = frozenset({
    "sessionid", "session_id", "phpsessid", "aspnet_sessionid",
    "jsessionid", "oauth_token", "access_token", "refresh_token",
    "rememberme", "auth_token", "token", "sid", "session",
    "connect.sid", "express:sess", "laravel_session",
})

SENSITIVE_FORM_FIELDS = frozenset({
    "username", "user", "email", "password", "passwd", "pwd",
    "pass", "secret", "pin", "otp", "mfa_code", "code",
    "token", "session", "apikey", "api_key", "secretkey",
    "cardnumber", "card_number", "ccnumber", "creditcard",
    "card_no", "cardno", "pan", "cvv", "cvc",
    "accountnumber", "account_number", "routing", "sortcode",
    "iban", "bic", "swift",
})


@dataclass
class Capture:
    """A single piece of sensitive data extracted from traffic."""
    id: str
    timestamp: str
    category: str
    value: str
    context: str = ""
    source: str = ""  # request_id
    severity: str = "medium"
    location: str = ""  # header name / form field / cookie name
    kit_family: str = "unknown"
    notes: str = ""


@dataclass
class CapturedRequest:
    id: str
    timestamp: str
    method: str
    url: str
    headers: dict = field(default_factory=dict)
    body: str = ""
    raw_body: bytes = b""
    client_ip: str = ""
    cookies: dict = field(default_factory=dict)
    query_params: dict = field(default_factory=dict)
    form_data: dict = field(default_factory=dict)
    captures: list = field(default_factory=list)


@dataclass
class CapturedResponse:
    id: str
    timestamp: str
    status: int
    headers: dict = field(default_factory=dict)
    body: str = ""
    raw_body: bytes = b""
    content_type: str = ""
    captures: list = field(default_factory=list)


@dataclass
class SessionRecord:
    """Correlation record linking a request/response pair and derived insights."""
    id: str
    request: CapturedRequest
    response: Optional[CapturedResponse] = None
    session_cookie_candidates: list = field(default_factory=list)
    token_candidates: list = field(default_factory=list)
    credential_candidates: list = field(default_factory=list)
    pii_candidates: list = field(default_factory=list)
    phishing_kit_hints: list = field(default_factory=list)
    fingerprint: str = ""
    summary: str = ""


@dataclass
class InterceptRule:
    """A rule defining what traffic to intercept and how to analyze it."""
    id: str
    description: str
    match_url_pattern: Optional[str] = None
    match_host_pattern: Optional[str] = None
    match_method: Optional[str] = None
    match_header: Optional[str] = None
    exclude_url_pattern: Optional[str] = None
    capture_credentials: bool = True
    capture_cookies: bool = True
    capture_tokens: bool = True
    capture_pii: bool = True
    capture_financial: bool = False
    response_body_inspect: bool = True
    request_body_inspect: bool = True
    log_raw_body: bool = False
    assign_kit_family: str = "unknown"


@dataclass
class RunConfig:
    listen: str = "127.0.0.1:8080"
    log_dir: str = "results/aitm"
    intercept_rules: list = field(default_factory=list)
    upstream_proxy: Optional[str] = None  # for chaining
    upstream_no_proxy: list = field(default_factory=list)
    capture_session_replay: bool = False
    replay_target: Optional[str] = None
    mfa_relay_simulate: bool = False
    mfa_relay_delay_ms: int = 3000
    max_requests_per_session: int = 5000
    max_body_bytes: int = 2 * 1024 * 1024
    allow_https_interception: bool = False
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None
    headless_mode: bool = True
    report_format: str = "json"
    noise_threshold_pct: int = 60
    export_sessions: bool = True
    export_streams: bool = False


# --- Utility functions ---

def now_iso() -> str:
    return dt_mod.now(dt_mod.timezone.utc).strftime(TIMESTAMP_FORMAT)

def ensure_dir(path: str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

def load_json_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json_file(path: str, obj: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, default=str, indent=2)

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="replace")).hexdigest()

def truncate(s: str, max_len: int = 500) -> str:
    if len(s) <= max_len:
        return s
    half = max_len // 2
    return s[:half] + "\n...[truncated]...\n" + s[-half:]

def snippet(s: str, max_len: int = 200) -> str:
    return truncate(s, max_len)

def fuzz_id(prefix: str = "F") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"

def random_hex(n: int = 16) -> str:
    return uuid.uuid4().hex[:n]

def safe_json_dumps(obj: Any) -> str:
    try:
        return json.dumps(obj, default=str, indent=2, sort_keys=True)
    except Exception:
        return str(obj)

def detect_email(text: str) -> list:
    return EMAIL_RE.findall(text)

def detect_phone(text: str) -> list:
    return PHONE_RE.findall(text)

def detect_card(text: str) -> list:
    return CARD_RE.findall(text)

def detect_tokens(text: str) -> list:
    return TOKEN_LIKE_RE.findall(text)

def extract_form_data(body: str, content_type: str) -> dict:
    """Parse form data from body based on content type."""
    result = {}
    ct = (content_type or "").lower()
    if "application/x-www-form-urlencoded" in ct:
        try:
            for pair in body.split("&"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    result[k] = v
        except Exception:
            pass
    elif "application/json" in ct:
        try:
            result = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            pass
    return result

def extract_cookies_from_header(set_cookie_headers: list, request_cookies: dict) -> dict:
    """Combine cookies from Set-Cookie headers and request Cookie header."""
    cookies = dict(request_cookies)
    for header in set_cookie_headers:
        if "=" in header:
            k, v = header.split("=", 1)
            cookies[k.strip()] = v.split(";")[0].strip()
    return cookies


# --- Analyzer (does the actual inspection of requests/responses) ---

class TrafficAnalyzer:
    """Analyzes captured HTTP traffic for sensitive data and phishing patterns."""

    def __init__(self, config: RunConfig):
        self.config = config
        self.captures: List[Capture] = []
        self.session_records: Dict[str, SessionRecord] = {}
        self._fingerprint_cache: Dict[str, str] = {}

    def reset(self):
        self.captures = []
        self.session_records = {}
        self._fingerprint_cache = {}

    def get_captures(self) -> List[Capture]:
        return list(self.captures)

    def get_session_records(self) -> Dict[str, SessionRecord]:
        return dict(self.session_records)

    def analyze_request(self, request: CapturedRequest) -> List[Capture]:
        caps = []
        self._analyze_url(request, caps)
        self._analyze_headers(request, caps)
        self._analyze_cookies(request, caps)
        self._analyze_body(request, caps)
        request.captures = caps
        self.captures.extend(caps)
        return caps

    def analyze_response(self, request: CapturedRequest, response: CapturedResponse) -> List[Capture]:
        caps = []
        self._analyze_response_status(request, response, caps)
        self._analyze_response_headers(request, response, caps)
        self._analyze_response_body(request, response, caps)
        response.captures = caps
        self.captures.extend(caps)
        self._build_session_record(request, response)
        return caps

    def _analyze_url(self, request: CapturedRequest, caps: List[Capture]):
        url = request.url
        host = ""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            host = parsed.hostname or ""
        except Exception:
            pass

        # Phishing kit fingerprint: look for known kit patterns in URL
        finger = self._classify_kit(url, host)
        if finger and finger != "unknown":
            caps.append(Capture(
                id=fuzz_id("KIT"),
                timestamp=now_iso(),
                category=CaptureCategory.PHISHING_KIT_FINGERPRINT.value,
                value=finger,
                context=f"URL pattern suggests {finger} kit",
                source=request.id,
                severity="high",
                location="url",
                kit_family=finger,
                notes="URL structure matches known phishing kit pattern",
            ))

        # Domain spoof detection: compare host against known legitimate domains
        if host:
            spoof = self._detect_domain_spoof(host)
            if spoof:
                caps.append(Capture(
                    id=fuzz_id("SPOOF"),
                    timestamp=now_iso(),
                    category=CaptureCategory.DOMAIN_SPOOF.value,
                    value=f"{host} -> {spoof}",
                    context="Hostname resembles legitimate domain",
                    source=request.id,
                    severity="medium",
                    location="host",
                    kit_family="custom",
                    notes=f"Suspected domain spoof of {spoof}",
                ))

        # PII in URL
        emails = detect_email(url)
        for email in emails:
            caps.append(Capture(
                id=fuzz_id("PIE"),
                timestamp=now_iso(),
                category=CaptureCategory.PII_EMAIL.value,
                value=email,
                context="Email found in URL",
                source=request.id,
                severity="medium",
                location="url",
                kit_family="unknown",
            ))
        phones = detect_phone(url)
        for phone in phones:
            caps.append(Capture(
                id=fuzz_id("PIP"),
                timestamp=now_iso(),
                category=CaptureCategory.PII_PHONE.value,
                value=phone,
                context="Phone found in URL",
                source=request.id,
                severity="medium",
                location="url",
                kit_family="unknown",
            ))

    def _analyze_headers(self, request: CapturedRequest, caps: List[Capture]):
        headers = request.headers
        for header_name, header_value in headers.items():
            header_name_lower = header_name.lower()
            header_value_str = str(header_value)

            # Bearer tokens in headers
            if header_name_lower == "authorization":
                if header_value_str.lower().startswith("bearer "):
                    token_val = header_value_str[7:].strip()
                    if len(token_val) > 10:
                        caps.append(Capture(
                            id=fuzz_id("HDRT"),
                            timestamp=now_iso(),
                            category=CaptureCategory.HEADER_TOKEN.value,
                            value=token_val[:200],
                            context="Bearer token in Authorization header",
                            source=request.id,
                            severity="high",
                            location="Authorization",
                            kit_family="unknown",
                            notes="Bearer token captured from request header",
                        ))

            # API keys in headers
            if any(kw in header_name_lower for kw in ["api_key", "apikey", "x-api-key", "x-api-key"]):
                if len(header_value_str) > 8:
                    caps.append(Capture(
                        id=fuzz_id("HDRK"),
                        timestamp=now_iso(),
                        category=CaptureCategory.HEADER_TOKEN.value,
                        value=header_value_str[:200],
                        context=f"API key in header {header_name}",
                        source=request.id,
                        severity="high",
                        location=header_name,
                        kit_family="unknown",
                    ))

            # Custom auth tokens
            if any(kw in header_name_lower for kw in ["token", "auth", "session", "sess"]):
                if len(header_value_str) > 8 and header_value_str.lower() not in ("", "none", "null"):
                    caps.append(Capture(
                        id=fuzz_id("HDRA"),
                        timestamp=now_iso(),
                        category=CaptureCategory.HEADER_TOKEN.value,
                        value=header_value_str[:200],
                        context=f"Token-like header {header_name}",
                        source=request.id,
                        severity="medium",
                        location=header_name,
                        kit_family="unknown",
                    ))

    def _analyze_cookies(self, request: CapturedRequest, caps: List[Capture]):
        cookies = request.cookies
        if not cookies:
            return

        for cookie_name, cookie_value in cookies.items():
            cookie_name_lower = cookie_name.lower()

            if cookie_name_lower in SESSION_COOKIE_NAMES:
                caps.append(Capture(
                    id=fuzz_id("COOK"),
                    timestamp=now_iso(),
                    category=CaptureCategory.COOKIE_SESSION.value,
                    value=cookie_value[:200] if cookie_value else "",
                    context=f"Session cookie: {cookie_name}",
                    source=request.id,
                    severity="high",
                    location=f"cookie:{cookie_name}",
                    kit_family="unknown",
                    notes=f"Session cookie captured: {cookie_name}",
                ))

            if any(kw in cookie_name_lower for kw in ["auth", "token", "sess"]):
                if len(cookie_value) > 8:
                    caps.append(Capture(
                        id=fuzz_id("COK2"),
                        timestamp=now_iso(),
                        category=CaptureCategory.COOKIE_AUTH.value,
                        value=cookie_value[:200],
                        context=f"Auth cookie: {cookie_name}",
                        source=request.id,
                        severity="high",
                        location=f"cookie:{cookie_name}",
                        kit_family="unknown",
                    ))

    def _analyze_body(self, request: CapturedRequest, caps: List[Capture]):
        if not request.body:
            return
        body = request.body

        # Credentials in form data
        form_data = request.form_data or extract_form_data(body, request.headers.get("Content-Type", ""))
        if form_data:
            for field_name, field_value in form_data.items():
                field_name_lower = str(field_name).lower()
                field_value_str = str(field_value)

                if field_name_lower in SENSITIVE_FORM_FIELDS:
                    if "password" in field_name_lower or "passwd" in field_name_lower or "pwd" in field_name_lower:
                        caps.append(Capture(
                            id=fuzz_id("PWD"),
                            timestamp=now_iso(),
                            category=CaptureCategory.CREDENTIAL_PASSWORD.value,
                            value=field_value_str[:200],
                            context=f"Password field: {field_name}",
                            source=request.id,
                            severity="critical",
                            location=f"form:{field_name}",
                            kit_family="unknown",
                            notes=f"Password captured from form field {field_name}",
                        ))
                    elif "username" in field_name_lower or "user" in field_name_lower or "email" in field_name_lower:
                        caps.append(Capture(
                            id=fuzz_id("USR"),
                            timestamp=now_iso(),
                            category=CaptureCategory.CREDENTIAL_USERNAME.value,
                            value=field_value_str[:200],
                            context=f"Username/email field: {field_name}",
                            source=request.id,
                            severity="high",
                            location=f"form:{field_name}",
                            kit_family="unknown",
                        ))
                    elif "otp" in field_name_lower or "mfa" in field_name_lower or "code" in field_name_lower or "passcode" in field_name_lower:
                        caps.append(Capture(
                            id=fuzz_id("MFA"),
                            timestamp=now_iso(),
                            category=CaptureCategory.CREDENTIAL_MFA_OTP.value,
                            value=field_value_str[:50],
                            context=f"MFA/OTP field: {field_name}",
                            source=request.id,
                            severity="critical",
                            location=f"form:{field_name}",
                            kit_family="unknown",
                            notes=f"MFA code captured from form field {field_name}",
                        ))
                    else:
                        caps.append(Capture(
                            id=fuzz_id("FUL"),
                            timestamp=now_iso(),
                            category=CaptureCategory.FORM_FIELD_SENSITIVE.value,
                            value=field_value_str[:200],
                            context=f"Sensitive form field: {field_name}",
                            source=request.id,
                            severity="medium",
                            location=f"form:{field_name}",
                            kit_family="unknown",
                        ))

                # Detect PII in any form field value
                if "email" in field_name_lower or "mail" in field_name_lower:
                    detected = detect_email(field_value_str)
                    for email in detected:
                        caps.append(Capture(
                            id=fuzz_id("PIE2"),
                            timestamp=now_iso(),
                            category=CaptureCategory.PII_EMAIL.value,
                            value=email,
                            context=f"Email in field {field_name}",
                            source=request.id,
                            severity="medium",
                            location=f"form:{field_name}",
                            kit_family="unknown",
                        ))

        # Scan raw body text for tokens
        tokens = detect_tokens(body)
        for tok in tokens:
            caps.append(Capture(
                id=fuzz_id("BODT"),
                timestamp=now_iso(),
                category=CaptureCategory.BODY_TOKEN.value,
                value=tok[:200],
                context="Token-like string in request body",
                source=request.id,
                severity="high",
                location="body",
                kit_family="unknown",
            ))

        # Scan for emails in body
        emails = detect_email(body)
        for email in emails:
            existing = [c for c in caps if c.category == CaptureCategory.PII_EMAIL.value and email in c.value]
            if not existing:
                caps.append(Capture(
                    id=fuzz_id("BOD1"),
                    timestamp=now_iso(),
                    category=CaptureCategory.PII_EMAIL.value,
                    value=email,
                    context="Email found in request body",
                    source=request.id,
                    severity="medium",
                    location="body",
                    kit_family="unknown",
                ))

        # Financial data
        if self.config.capture_financial:
            cards = detect_card(body)
            for card in cards:
                caps.append(Capture(
                    id=fuzz_id("FIN"),
                    timestamp=now_iso(),
                    category=CaptureCategory.FINANCIAL_CARD.value,
                    value=card[:20] + "..." if len(card) > 20 else card,
                    context="Card number pattern in request body",
                    source=request.id,
                    severity="critical",
                    location="body",
                    kit_family="unknown",
                    notes=f"Financial card pattern detected (last 4: {card[-4:] if len(card) >= 4 else 'N/A'})",
                ))

    def _analyze_response_status(self, request: CapturedRequest, response: CapturedResponse, caps: List[Capture]):
        status = response.status
        # 200 with auth-related URL may indicate successful credential harvest
        url_lower = request.url.lower()
        if status in (200, 201) and any(kw in url_lower for kw in ["login", "auth", "signin", "sign-in", "session", "token", "oauth"]):
            caps.append(Capture(
                id=fuzz_id("RSP"),
                timestamp=now_iso(),
                category=CaptureCategory.HEADER_TOKEN.value,
                value=f"Successful auth response {status} on {request.method} {request.url}",
                context="Auth endpoint returned success",
                source=request.id,
                severity="high",
                location="response_status",
                kit_family="unknown",
                notes="Authentication endpoint returned success - possible credential capture endpoint",
            ))

    def _analyze_response_headers(self, request: CapturedRequest, response: CapturedResponse, caps: List[Capture]):
        headers = response.headers
        set_cookie = headers.get("Set-Cookie", "")
        if isinstance(set_cookie, list):
            set_cookie = "; ".join(set_cookie)

        if set_cookie:
            # Extract session cookies from response
            for cookie_name in SESSION_COOKIE_NAMES:
                if cookie_name in set_cookie.lower():
                    caps.append(Capture(
                        id=fuzz_id("RSC"),
                        timestamp=now_iso(),
                        category=CaptureCategory.COOKIE_SESSION.value,
                        value="Session cookie set in response",
                        context=f"Server set session cookie: {cookie_name}",
                        source=request.id,
                        severity="high",
                        location="Set-Cookie",
                        kit_family="unknown",
                        notes=f"Server responded with session cookie {cookie_name}",
                    ))

        # Content-Type analysis for body inspection
        ct = headers.get("Content-Type", "")
        if "text/html" in ct.lower():
            response.content_type = "text/html"

    def _analyze_response_body(self, request: CapturedRequest, response: CapturedResponse, caps: List[Capture]):
        if not self.config.response_body_inspect:
            return
        if not response.body:
            return
        body = response.body

        # Check for credential confirmation pages
        body_lower = body.lower()
        if any(phrase in body_lower for phrase in ["successfully logged in", "authentication successful", "welcome back", "session established"]):
            caps.append(Capture(
                id=fuzz_id("RPB1"),
                timestamp=now_iso(),
                category=CaptureCategory.FORM_FIELD_SENSITIVE.value,
                value="Credential confirmation page detected",
                context="Login success page in response",
                source=request.id,
                severity="high",
                location="response_body",
                kit_family="unknown",
                notes="Response contains login success confirmation - indicates credential capture endpoint",
            ))

        # Detect phishing kit fingerprints in response body
        finger = self._classify_kit_body(body)
        if finger and finger != "unknown":
            caps.append(Capture(
                id=fuzz_id("RPB2"),
                timestamp=now_iso(),
                category=CaptureCategory.PHISHING_KIT_FINGERPRINT.value,
                value=finger,
                context="Phishing kit signature detected in response",
                source=request.id,
                severity="high",
                location="response_body",
                kit_family=finger,
                notes=f"Phishing kit {finger} fingerprint detected in HTML response",
            ))

        # PII in response body
        emails = detect_email(body)
        for email in emails:
            existing = [c for c in caps if c.category == CaptureCategory.PII_EMAIL.value and email in c.value]
            if not existing:
                caps.append(Capture(
                    id=fuzz_id("RPB3"),
                    timestamp=now_iso(),
                    category=CaptureCategory.PII_EMAIL.value,
                    value=email,
                    context="Email in response body",
                    source=request.id,
                    severity="medium",
                    location="response_body",
                    kit_family="unknown",
                ))

    def _build_session_record(self, request: CapturedRequest, response: CapturedResponse):
        session_id = request.id
        if session_id in self.session_records:
            return
        rec = SessionRecord(
            id=session_id,
            request=request,
            response=response,
        )
        # Collect session cookie candidates
        for cookie_name in SESSION_COOKIE_NAMES:
            if cookie_name in request.cookies:
                rec.session_cookie_candidates.append(cookie_name)
            if "Set-Cookie" in response.headers:
                set_cookie_val = response.headers.get("Set-Cookie", "")
                if cookie_name in str(set_cookie_val).lower():
                    rec.session_cookie_candidates.append(cookie_name)

        # Collect token candidates
        for header_name in request.headers:
            if any(kw in header_name.lower() for kw in ["token", "auth", "session", "bearer"]):
                rec.token_candidates.append(header_name)
        for cookie_name in request.cookies:
            if any(kw in cookie_name.lower() for kw in ["token", "auth", "session"]):
                rec.token_candidates.append(f"cookie:{cookie_name}")
        for field_name, _ in (request.form_data or {}).items():
            if any(kw in str(field_name).lower() for kw in ["token", "auth", "session", "otp", "mfa"]):
                rec.token_candidates.append(f"form:{field_name}")

        # Collect credential candidates
        for field_name, _ in (request.form_data or {}).items():
            fn_lower = str(field_name).lower()
            if any(kw in fn_lower for kw in ["password", "passwd", "pwd", "pass", "secret", "pin"]):
                rec.credential_candidates.append(f"form:{field_name}")
            if any(kw in fn_lower for kw in ["username", "user", "email", "mail"]):
                if not any(kw2 in fn_lower for kw2 in ["password", "passwd", "pwd"]):
                    rec.credential_candidates.append(f"form:{field_name}")

        # PII candidates
        body_text = request.body or ""
        for email in detect_email(body_text):
            rec.pii_candidates.append(f"email:{email}")
        for phone in detect_phone(body_text):
            rec.pii_candidates.append(f"phone:{phone}")

        # Generate fingerprint
        rec.fingerprint = self._generate_fingerprint(request, response)
        rec.summary = self._generate_summary(request, response)
        self.session_records[session_id] = rec

    def _classify_kit(self, url: str, host: str) -> str:
        """Heuristic classification of phishing kit from URL/host patterns."""
        url_lower = url.lower()
        host_lower = host.lower()

        # Evilginx-style patterns
        if any(kw in url_lower for kw in ["/popup/", "/verify/", "/service/", "/sso/", "/oauth/"]):
            if any(kw in host_lower for kw in [".proxy.", "proxy.", ".relay.", "relay."]):
                return PhishingKitFamily.EVILGINX.value
            return PhishingKitFamily.EVILGINX.value

        # Phishing key style
        if any(kw in url_lower for kw in ["/get/", "/handler/", "/api/v1/", "/capture/"]):
            return PhishingKitFamily.PHISHING_KEY.value

        # Modular phisher patterns
        if any(kw in url_lower for kw in ["/login/", "/auth/", "/signin/"]):
            if any(kw in host_lower for kw in ["phish", "freehost", "000webhost", "wordpress"]):
                return PhishingKitFamily.MODULAR_PHISHER.value

        if any(kw in url_lower for kw in ["/stealer/", "/exfil/", "/send/"]):
            return PhishingKitFamily.MODULAR_PHISHER.value

        return PhishingKitFamily.UNKNOWN.value

    def _classify_kit_body(self, body: str) -> str:
        """Identify phishing kit from response body signatures."""
        body_lower = body.lower()
        kit_signatures = [
            (PhishingKitFamily.EVILGINX.value, ["evilginx", "evilginx-interceptor", "purity", "interceptor"]),
            (PhishingKitFamily.PHISHING_KEY.value, ["phishing-key", "phishkey", "kit-common", "golinks"]),
            (PhishingKitFamily.MODULAR_PHISHER.value, ["modular-phisher", "openphish", "phishmod", "thephish"]),
        ]
        for family, keywords in kit_signatures:
            for kw in keywords:
                if kw in body_lower:
                    return family
        return PhishingKitFamily.UNKNOWN.value

    def _detect_domain_spoof(self, host: str) -> Optional[str]:
        """Detect if a hostname looks like a spoofed version of a well-known domain."""
        spoof_targets = [
            "microsoft.com", "office365.com", "outlook.com", "login.microsoftonline.com",
            "google.com", "accounts.google.com", "gmail.com",
            "apple.com", "icloud.com", "appleid.apple.com",
            "facebook.com", "fb.com", "instagram.com",
            "amazon.com", "paypal.com", "docusign.net",
            "dropbox.com", "onedrive.com", "sharepoint.com",
            "salesforce.com", "slack.com",
            "github.com", "gitlab.com",
            "netflix.com", "spotify.com",
            "chase.com", "wellsfargo.com", "bankofamerica.com",
            "citi.com", "capitalone.com", "usbank.com",
            "wells fargo", "bank of america",
        ]
        host_clean = host.lower().replace("www.", "").replace("m.", "").split(":")[0]
        for target in spoof_targets:
            target_clean = target.lower()
            # Check for homograph / typo-squatting
            if host_clean.endswith(target_clean):
                if host_clean != target_clean:
                    return target
            if host_clean.startswith(target_clean.rsplit(".", 1)[0]):
                suffix = target_clean.rsplit(".", 1)[-1]
                if host_clean.endswith("." + suffix) and host_clean != target_clean:
                    return target
            # Character substitution detection
            if len(host_clean) == len(target_clean) and host_clean != target_clean:
                substitutions = {
                    "0": "o", "o": "0", "1": "i", "i": "1", "l": "1", "1": "l",
                    "3": "e", "e": "3", "4": "a", "a": "4",
                    "5": "s", "s": "5", "7": "t", "t": "7",
                    "8": "b", "b": "8", "@": "a", "a": "@",
                }
                diffs = 0
                for i in range(min(len(host_clean), len(target_clean))):
                    hc = host_clean[i]
                    tc = target_clean[i]
                    if hc != tc and substitutions.get(hc) == tc:
                        diffs += 1
                if diffs >= 1 and len(host_clean) >= 5:
                    return target
        return None

    def _generate_fingerprint(self, request: CapturedRequest, response: CapturedResponse) -> str:
        key_parts = [
            request.method,
            request.url,
            str(sorted(request.headers.keys())),
            str(sorted(request.cookies.keys())),
            str(response.status) if response else "",
            str(sorted(response.headers.keys())) if response else "",
        ]
        fingerprint_data = "|".join(key_parts)
        return sha256_hex(fingerprint_data)[:32]

    def _generate_summary(self, request: CapturedRequest, response: CapturedResponse) -> str:
        cred_count = len([c for c in request.captures if c.category.startswith("credential_")])
        token_count = len([c for c in request.captures if c.category in (CaptureCategory.HEADER_TOKEN.value, CaptureCategory.BODY_TOKEN.value)])
        session_count = len([c for c in request.captures if c.category.startswith("cookie_session")])
        pii_count = len([c for c in request.captures if c.category.startswith("pii_")])
        return (f"Session {request.id}: {cred_count} credentials, "
                f"{token_count} tokens, {session_count} session cookies, "
                f"{pii_count} PII items, status={response.status if response else 'no response'}")


# --- Configuration loading ---

def load_default_rules() -> List[InterceptRule]:
    return [
        InterceptRule(
            id="default_creds",
            description="Capture credentials, tokens, and session data from all traffic",
            capture_credentials=True,
            capture_cookies=True,
            capture_tokens=True,
            capture_pii=True,
            capture_financial=False,
        ),
        InterceptRule(
            id="financial_sensitive",
            description="Also capture financial data (card numbers, account numbers)",
            match_url_pattern=r"(?i)(?:payment|bank|transaction|card|checkout|fin)",
            capture_credentials=True,
            capture_cookies=True,
            capture_tokens=True,
            capture_pii=True,
            capture_financial=True,
        ),
    ]


def parse_rules_from_file(path: str) -> List[InterceptRule]:
    try:
        data = load_json_file(path)
        rules = []
        for item in data.get("rules", data if isinstance(data, list) else []):
            if isinstance(item, dict):
                rule = InterceptRule(**{k: item.get(k) for k in item})
                rules.append(rule)
        if not rules:
            return load_default_rules()
        return rules
    except Exception as e:
        logger.warning("Failed to load rules from %s: %s", path, e)
        return load_default_rules()


# --- HTTP Proxy Implementation ---

class AITMProxyHandler:
    """Handles individual proxy connections: receives browser requests,
    analyzes traffic, forwards to upstream, returns response."""

    def __init__(self, config: RunConfig, analyzer: TrafficAnalyzer):
        self.config = config
        self.analyzer = analyzer
        self.client_sockets: List = []

    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer_addr = writer.get_extra_info("peername")
        client_ip = str(peer_addr[0]) if peer_addr else ""
        logger.info("New connection from %s", client_ip)

        try:
            # Parse HTTP request
            request_line = await self._read_request_line(reader)
            if not request_line:
                writer.close()
                return

            method, path, version = self._parse_request_line(request_line)
            headers = await self._read_headers(reader)
            body = await self._read_body(reader, headers)

            # Build CapturedRequest
            req_id = fuzz_id("REQ")
            timestamp = now_iso()
            cookies = {}
            cookie_header = headers.get("Cookie", "")
            if cookie_header:
                for pair in cookie_header.split(";"):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        cookies[k.strip()] = v.strip()

            query_params = {}
            if "?" in path:
                from urllib.parse import parse_qs
                qs = path.split("?", 1)[1]
                query_params = parse_qs(qs)
                for k, v in query_params.items():
                    if len(v) == 1:
                        query_params[k] = v[0]

            captured_req = CapturedRequest(
                id=req_id,
                timestamp=timestamp,
                method=method,
                url=path,
                headers=headers,
                body=body.decode("utf-8", errors="replace") if body else "",
                raw_body=body,
                client_ip=client_ip,
                cookies=cookies,
                query_params=query_params,
                form_data=extract_form_data(body.decode("utf-8", errors="replace") if body else "", headers.get("Content-Type", "")) if body else {},
            )

            logger.debug("Request %s: %s %s", req_id, method, path)

            # Analyze the request
            self.analyzer.analyze_request(captured_req)

            # Forward to upstream
            response = await self._forward_request(method, path, headers, body, captured_req)

            if response:
                # Analyze response
                captured_resp = CapturedResponse(
                    id=fuzz_id("RSP"),
                    timestamp=now_iso(),
                    status=response.status,
                    headers=dict(response.headers) if response.headers else {},
                    body=response.body,
                    raw_body=response.raw_body,
                    content_type=response.headers.get("Content-Type", "") if response.headers else "",
                )
                self.analyzer.analyze_response(captured_req, captured_resp)

                # Build and send response back to client
                await self._send_response(writer, response)
            else:
                await self._send_error(writer, 502, "Bad Gateway: upstream connection failed")

            # Log captures
            req_caps = captured_req.captures
            if req_caps:
                logger.info("Captures from %s: %d items", req_id, len(req_caps))
                for cap in req_caps:
                    logger.debug("  [%s] %s: %s", cap.category, cap.location, cap.value[:80])

            # Check for session replay
            if self.config.capture_session_replay and self.config.replay_target:
                await self._attempt_session_replay(captured_req, captured_resp if 'captured_resp' in dir() else None)

        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error("Error handling connection from %s: %s", client_ip, e)
            try:
                await self._send_error(writer, 500, "Internal Proxy Error")
            except Exception:
                pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def _read_request_line(self, reader: asyncio.StreamReader) -> Optional[str]:
        try:
            line = await asyncio.wait_for(reader.readline(), timeout=5.0)
            if not line:
                return None
            return line.decode("utf-8", errors="replace").strip()
        except asyncio.TimeoutError:
            return None
        except Exception:
            return None

    def _parse_request_line(self, line: str) -> Tuple[str, str, str]:
        parts = line.split(" ", 2)
        method = parts[0] if len(parts) > 0 else "GET"
        path = parts[1] if len(parts) > 1 else "/"
        version = parts[2] if len(parts) > 2 else "HTTP/1.1"
        return method, path, version

    async def _read_headers(self, reader: asyncio.StreamReader) -> Dict[str, str]:
        headers = {}
        try:
            while True:
                line = await asyncio.wait_for(reader.readline(), timeout=5.0)
                decoded = line.decode("utf-8", errors="replace").strip()
                if not decoded:
                    break
                if ":" in decoded:
                    key, value = decoded.split(":", 1)
                    headers[key.strip()] = value.strip()
        except asyncio.TimeoutError:
            pass
        return headers

    async def _read_body(self, reader: asyncio.StreamReader, headers: Dict[str, str]) -> bytes:
        content_length = int(headers.get("Content-Length", "0"))
        if content_length <= 0:
            return b""
        max_bytes = self.config.max_body_bytes
        if content_length > max_bytes:
            content_length = max_bytes
        try:
            body = await asyncio.wait_for(reader.readexactly(content_length), timeout=10.0)
            return body
        except (asyncio.IncompleteReadError, asyncio.TimeoutError):
            try:
                remaining = await reader.read(max_bytes - len(body) if 'body' in dir() else max_bytes)
                body = body + remaining if 'body' in dir() else remaining
                return body
            except Exception:
                return b""
        except Exception:
            return b""

    async def _forward_request(self, method: str, path: str, headers: Dict[str, str], body: bytes, captured_req: CapturedRequest):
        """Forward request to the actual target server."""
        from urllib.parse import urlparse

        target_url = path
        if not target_url.startswith("http"):
            # Assume target is the host the client wanted to reach
            host = headers.get("Host", "")
            if host and not path.startswith("http"):
                if path.startswith("/"):
                    target_url = f"http://{host}{path}"
                else:
                    target_url = f"http://{path}"

        try:
            parsed = urlparse(target_url)
            host = parsed.hostname or ""
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            path_part = parsed.path
            if parsed.query:
                path_part = path_part + "?" + parsed.query

            # Build forward headers
            forward_headers = dict(headers)
            forward_headers.pop("Proxy-Connection", None)
            if "Host" not in forward_headers and host:
                forward_headers["Host"] = host

            # Create connection to upstream
            if parsed.scheme == "https":
                reader, writer = await asyncio.open_connection(host, port)
                # Note: full TLS interception would require SSL context
                # For lab use, we forward without MITM TLS for now
            else:
                reader, writer = await asyncio.open_connection(host, port)

            # Build HTTP request to upstream
            req_line = f"{method} {path_part} HTTP/1.1\r\n"
            header_lines = ""
            for k, v in forward_headers.items():
                header_lines += f"{k}: {v}\r\n"
            if body:
                header_lines += f"Content-Length: {len(body)}\r\n"
            header_lines += "\r\n"

            request_bytes = (req_line + header_lines).encode("utf-8")
            if body:
                request_bytes += body

            writer.write(request_bytes)
            await writer.drain()

            # Read response
            resp_line = await asyncio.wait_for(reader.readline(), timeout=10.0)
            resp_decoded = resp_line.decode("utf-8", errors="replace").strip()
            if not resp_decoded:
                writer.close()
                return None

            resp_parts = resp_decoded.split(" ", 2)
            status = int(resp_parts[1]) if len(resp_parts) > 1 else 502

            resp_headers = {}
            while True:
                line = await asyncio.wait_for(reader.readline(), timeout=5.0)
                decoded = line.decode("utf-8", errors="replace").strip()
                if not decoded:
                    break
                if ":" in decoded:
                    k, v = decoded.split(":", 1)
                    resp_headers[k.strip()] = v.strip()

            # Read response body
            resp_body = b""
            cl = int(resp_headers.get("Content-Length", "0"))
            if cl > 0:
                try:
                    resp_body = await asyncio.wait_for(reader.readexactly(cl), timeout=10.0)
                except Exception:
                    resp_body = await reader.read(4096)

            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

            return type('obj', (object,), {
                'status': status,
                'headers': resp_headers,
                'body': resp_body.decode("utf-8", errors="replace"),
                'raw_body': resp_body,
            })()

        except Exception as e:
            logger.error("Upstream error: %s", e)
            return None

    async def _send_response(self, writer: asyncio.StreamWriter, response):
        status_line = f"HTTP/1.1 {response.status} OK\r\n"
        header_lines = ""
        for k, v in response.headers.items():
            if k.lower() not in ("transfer-encoding",):
                header_lines += f"{k}: {v}\r\n"
        if "Content-Length" not in "".join(response.headers.keys()).lower():
            body_len = len(response.raw_body) if response.raw_body else len(response.body.encode("utf-8"))
            header_lines += f"Content-Length: {body_len}\r\n"
        header_lines += "\r\n"
        response_bytes = (status_line + header_lines).encode("utf-8")
        if response.raw_body:
            response_bytes += response.raw_body
        elif response.body:
            response_bytes += response.body.encode("utf-8")
        writer.write(response_bytes)
        await writer.drain()

    async def _send_error(self, writer: asyncio.StreamWriter, status: int, message: str):
        body = f"<html><body><h1>{status} {message}</h1></body></html>"
        response = (
            f"HTTP/1.1 {status} {message}\r\n"
            f"Content-Type: text/html\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
            f"{body}"
        )
        writer.write(response.encode("utf-8"))
        await writer.drain()

    async def _attempt_session_replay(self, request: CapturedRequest, response: Optional[CapturedResponse]):
        """If session replay is enabled, attempt to replay captured session
        against the replay target to test token/session reuse."""
        if not self.config.replay_target:
            return
        if not request.cookies and not request.headers.get("Authorization"):
            return

        replay_headers = dict(request.headers)
        replay_headers["Authorization"] = request.headers.get("Authorization", "")
        if request.cookies:
            cookie_str = "; ".join(f"{k}={v}" for k, v in request.cookies.items())
            replay_headers["Cookie"] = cookie_str

        try:
            from urllib.parse import urlparse
            parsed = urlparse(self.config.replay_target)
            host = parsed.hostname or ""
            port = parsed.port or 80
            path = parsed.path or "/"

            reader, writer = await asyncio.open_connection(host, port)
            req = f"GET {path} HTTP/1.1\r\nHost: {host}\r\n"
            for k, v in replay_headers.items():
                if k.lower() not in ("host",):
                    req += f"{k}: {v}\r\n"
            req += "\r\n"
            writer.write(req.encode("utf-8"))
            await writer.drain()

            resp_line = await asyncio.wait_for(reader.readline(), timeout=5.0)
            resp_decoded = resp_line.decode("utf-8", errors="replace").strip()
            status = int(resp_decoded.split(" ", 1)[0]) if resp_decoded else 0
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

            if status in (200, 201, 302):
                logger.info("Session replay SUCCESS on %s (status %d) - session/token is reusable!", self.config.replay_target, status)
            else:
                logger.info("Session replay FAILED on %s (status %d) - session/token may be bound", self.config.replay_target, status)

        except Exception as e:
            logger.debug("Session replay error: %s", e)


# --- MFA Relay Simulation ---

class MFARelaySimulator:
    """Simulates OTP/MFA relay timing for lab analysis of MFA bypass windows."""

    def __init__(self, config: RunConfig):
        self.config = config
        self.relay_log: List[Dict[str, Any]] = []

    def record_relay(self, timestamp: str, otp_value: str, target: str, result: str, delay_ms: int):
        self.relay_log.append({
            "timestamp": timestamp,
            "otp_value": otp_value[:20],
            "target": target,
            "result": result,
            "delay_ms": delay_ms,
            "configured_delay_ms": self.config.mfa_relay_delay_ms,
        })

    def simulate_relay(self, otp: str, target: str) -> Tuple[str, int]:
        """Simulate MFA relay with configurable delay; returns (result, delay_ms)."""
        delay_ms = self.config.mfa_relay_delay_ms
        time.sleep(delay_ms / 1000.0)
        # In a real AITM scenario, the OTP would be forwarded to the legitimate
        # service at this point. Here we simulate success to measure timing windows.
        result = "relayed"
        self.record_relay(now_iso(), otp, target, result, delay_ms)
        return result, delay_ms

    def get_relay_log(self) -> List[Dict[str, Any]]:
        return list(self.relay_log)

    def export_relay_log(self, path: str):
        ensure_dir(path)
        save_json_file(path, {"relay_events": self.relay_log, "config": asdict(self.config)})


# --- Main proxy server ---

class AITMProxyServer:
    """Main proxy server: listens on a port, accepts connections,
    analyzes traffic, logs captures."""

    def __init__(self, config: RunConfig):
        self.config = config
        self.analyzer = TrafficAnalyzer(config)
        self.handler = AITMProxyHandler(config, self.analyzer)
        self.server: Optional[asyncio.AbstractServer] = None
        self.running = False
        self._shutdown_event = asyncio.Event()

    async def start(self):
        listen_parts = self.config.listen.split(":")
        host = listen_parts[0] if len(listen_parts) > 0 else "127.0.0.1"
        try:
            port = int(listen_parts[1]) if len(listen_parts) > 1 else 8080
        except (ValueError, IndexError):
            port = 8080

        logger.info("Starting AITM proxy on %s:%d", host, port)
        logger.info("Log directory: %s", self.config.log_dir)
        logger.info("Rules: %d loaded", len(self.config.intercept_rules))
        logger.info("Session replay: %s", "enabled" if self.config.capture_session_replay else "disabled")
        logger.info("MFA relay simulation: %s", "enabled" if self.config.mfa_relay_simulate else "disabled")

        ensure_dir(self.config.log_dir)

        self.server = await asyncio.start_server(
            self.handler.handle_connection,
            host,
            port,
        )

        self.running = True
        logger.info("Proxy listening on %s:%d", host, port)

        async with self.server:
            await self._shutdown_event.wait()

    async def stop(self):
        logger.info("Shutting down AITM proxy...")
        self.running = False
        self._shutdown_event.set()
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        # Export captures
        await self._export_captures()

    async def _export_captures(self):
        if not self.config.export_sessions:
            return

        # Export captures
        captures_path = os.path.join(self.config.log_dir, "captures.json")
        save_json_file(captures_path, {
            "version": VERSION,
            "timestamp": now_iso(),
            "total_captures": len(self.analyzer.get_captures()),
            "capture_categories": self._count_by_category(),
            "captures": [asdict(c) for c in self.analyzer.get_captures()],
        })
        logger.info("Captures exported to %s (%d total)", captures_path, len(self.analyzer.get_captures()))

        # Export session records
        if self.config.export_sessions:
            sessions_path = os.path.join(self.config.log_dir, "sessions.json")
            sessions = self.analyzer.get_session_records()
            save_json_file(sessions_path, {
                "version": VERSION,
                "timestamp": now_iso(),
                "total_sessions": len(sessions),
                "sessions": [
                    {
                        "id": s.id,
                        "request": asdict(s.request),
                        "response": asdict(s.response) if s.response else None,
                        "session_cookie_candidates": s.session_cookie_candidates,
                        "token_candidates": s.token_candidates,
                        "credential_candidates": s.credential_candidates,
                        "pii_candidates": s.pii_candidates,
                        "fingerprint": s.fingerprint,
                        "summary": s.summary,
                    }
                    for s in sessions.values()
                ],
            })
            logger.info("Sessions exported to %s (%d total)", sessions_path, len(sessions))

        # Export relay log if MFA simulation was used
        if self.config.mfa_relay_simulate:
            relay_path = os.path.join(self.config.log_dir, "mfa_relay.json")
            mfa_sim = MFARelaySimulator(self.config)
            save_json_file(relay_path, {"relay_events": mfa_sim.get_relay_log()})
            logger.info("MFA relay log exported to %s", relay_path)

    def _count_by_category(self) -> Dict[str, int]:
        counts = defaultdict(int)
        for cap in self.analyzer.get_captures():
            counts[cap.category] += 1
        return dict(counts)


# --- CLI ---

def _build_parser():
    parser = argparse.ArgumentParser(
        description=f"AITM Phishing Proxy v{VERSION} - Analyze phishing traffic in authorized labs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start proxy on default port, log to results/aitm
  python aitm_phishing_proxy.py --listen 127.0.0.1:8080

  # Start with custom rules file and session replay enabled
  python aitm_phishing_proxy.py \\
      --listen 127.0.0.1:8443 \\
      --log-dir results/aitm_lab \\
      --rules rules/capture_rules.json \\
      --replay-target http://lab-target.local/verify

  # Enable MFA relay simulation with 5 second delay
  python aitm_phishing_proxy.py \\
      --mfa-relay-delay 5000 \\
      --mfa-relay-simulate
""",
    )
    parser.add_argument("--listen", default="127.0.0.1:8080", help="Address:port to listen on (default: 127.0.0.1:8080)")
    parser.add_argument("--log-dir", default="results/aitm", help="Directory for capture logs (default: results/aitm)")
    parser.add_argument("--rules", default=None, help="Path to JSON rules file for traffic analysis")
    parser.add_argument("--replay-target", default=None, help="Target URL to replay captured sessions against (for testing session reuse)")
    parser.add_argument("--mfa-relay-simulate", action="store_true", help="Enable MFA/OTP relay simulation")
    parser.add_argument("--mfa-relay-delay", type=int, default=3000, help="MFA relay delay in ms (default: 3000)")
    parser.add_argument("--max-requests", type=int, default=5000, help="Max requests per session before reset (default: 5000)")
    parser.add_argument("--body-limit", type=int, default=2097152, help="Max response body bytes to capture (default: 2MB)")
    parser.add_argument("--no-https", action="store_true", default=True, help="Disable HTTPS interception (default: on)")
    parser.add_argument("--ssl-cert", default=None, help="Path to SSL certificate for HTTPS interception (lab use)")
    parser.add_argument("--ssl-key", default=None, help="Path to SSL key for HTTPS interception (lab use)")
    parser.add_argument("--no-headless", action="store_true", help="Run in interactive mode (show capture alerts)")
    parser.add_argument("--report-format", choices=["json", "text"], default="json", help="Export report format")
    parser.add_argument("--export-sessions", action="store_true", default=True, help="Export session records on shutdown")
    parser.add_argument("--no-export", action="store_true", help="Disable all exports on shutdown")
    parser.add_argument("--verbosity", type=int, default=1, choices=[0, 1, 2, 3], help="Logging level: 0=quiet, 1=info, 2=debug, 3=trace")
    parser.add_argument("--version", action="version", version=f"aitm_phishing_proxy v{VERSION}")
    return parser


def _setup_logging(verbosity: int):
    levels = [logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]
    level = levels[min(verbosity, 3)]
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(level=level, format=fmt, datefmt="%H:%M:%S")


async def _run_proxy(args) -> int:
    _setup_logging(args.verbosity)

    config = RunConfig(
        listen=args.listen,
        log_dir=args.log_dir,
        intercept_rules=parse_rules_from_file(args.rules) if args.rules else load_default_rules(),
        capture_session_replay=bool(args.replay_target),
        replay_target=args.replay_target,
        mfa_relay_simulate=args.mfa_relay_simulate,
        mfa_relay_delay_ms=args.mfa_relay_delay,
        max_requests_per_session=args.max_requests,
        max_body_bytes=args.body_limit,
        allow_https_interception=not args.no_https,
        ssl_cert_path=args.ssl_cert,
        ssl_key_path=args.ssl_key,
        headless_mode=not args.no_headless,
        report_format=args.report_format,
        export_sessions=not args.no_export,
        export_streams=False,
    )

    logger.info("=" * 60)
    logger.info("AITM Phishing Proxy v%s", VERSION)
    logger.info("Target: %s (controlled lab environment only)", args.listen)
    logger.info("Log directory: %s", args.log_dir)
    logger.info("Rules loaded: %d", len(config.intercept_rules))
    logger.info("=" * 60)

    server = AITMProxyServer(config)
    loop = asyncio.get_running_loop()

    def _handle_signal():
        logger.info("Received shutdown signal")
        asyncio.create_task(server.stop())

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_signal)
        except NotImplementedError:
            pass

    try:
        await server.start()
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error("Proxy error: %s", e)
        return 1

    return 0


def _cli_main():
    parser = _build_parser()
    args = parser.parse_args()
    try:
        return asyncio.run(_run_proxy(args))
    except KeyboardInterrupt:
        logger.info("Interrupted")
        return 0
    except Exception as e:
        logger.error("Fatal: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(_cli_main() or 0)
