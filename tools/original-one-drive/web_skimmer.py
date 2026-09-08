#!/usr/bin/env python3
"""
web_skimmer.py — Web Skimmer / Payment Interception Analyzer v1.0.0
=====================================================================
Analyzes web applications and payment flows for skimming
vulnerabilities — credential harvesting, payment card interception,
session token theft, and iframe-based attack vectors.

For AUTHORIZED PENETRATION TESTING against owned targets only.

Usage: python web_skimmer.py --target https://shop.example.com
       --scan payment-forms --output results/skim_report.json
"""

import argparse
import asyncio
import json
import logging
import os
import re
import signal
import sys
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, List, Dict, Tuple
from urllib.parse import urljoin, urlparse

try:
    import aiohttp
except ImportError:
    aiohttp = None

logger = logging.getLogger("web_skimmer")
VERSION = "1.0.0"
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SkimCategory(str, Enum):
    PAYMENT_CARD_INTERCEPTION = "payment_card_interception"
    CREDENTIAL_HARVESTING = "credential_harvesting"
    SESSION_HIJACKING = "session_hijacking"
    IFRAME_INJECTION = "iframe_injection"
    KEYLOGGER_PATTERN = "keylogger_pattern"
    DOM_MANIPULATION = "dom_manipulation"
    FORM_OVERLAY = "form_overlay"
    MAN_IN_THE_MIDDLE = "man_in_the_middle"
    MISCONFIGURED_CSP = "misconfigured_csp"
    INSECURE_TRANSMISSION = "insecure_transmission"


@dataclass
class SkimFinding:
    """A web skimming vulnerability finding."""
    id: str
    severity: Severity
    category: SkimCategory
    title: str
    description: str
    target: str = ""
    url: str = ""
    element: str = ""
    evidence: str = ""
    recommendation: str = ""
    confidence: float = 1.0


@dataclass
class SkimConfig:
    """Configuration for web skimming analysis."""
    target: str
    scan_type: str = "full"
    payment_form_selectors: List[str] = field(default_factory=lambda: [
        "form[name*='payment']",
        "form[name*='checkout']",
        "form[action*='pay']",
        "input[type='credit-card']",
        "input[name*='card_number']",
        "input[name*='cc_number']",
        "input[name*='pan']",
        "#card-number",
        "#cc-number",
        ".payment-form",
        ".checkout-form",
    ])
    credential_form_selectors: List[str] = field(default_factory=lambda: [
        "form[action*='login']",
        "form[action*='auth']",
        "form[action*='signin']",
        "input[name='username']",
        "input[name='password']",
        "input[type='password']",
        "#login-form",
        "#auth-form",
    ])
    js_scan_selectors: List[str] = field(default_factory=lambda: [
        "script[src*='tracker']",
        "script[src*='analytics']",
        "script[src*='pixel']",
        "script[src*='beacon']",
        "script[src*='telemetry']",
        "iframe[src]",
        "object[data]",
        "embed[src]",
    ])
    check_csp: bool = True
    check_hsts: bool = True
    check_mixed_content: bool = True
    check_form_action: bool = True
    check_js_events: bool = True
    check_network_requests: bool = True
    js_lint_threshold: int = 3


# --- Utility functions ---

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT)

def fuzz_id(prefix: str = "SK") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"

def truncate(s: str, max_len: int = 500) -> str:
    if len(s) <= max_len:
        return s
    half = max_len // 2
    return s[:half] + "\n...[truncated]...\n" + s[-half:]


# --- Detector patterns ---

CARD_PATTERN = re.compile(
    r'\b(?:4[0-9]{12}(?:[0-9]{3})?|'
    r'5[1-5][0-9]{14}|'
    r'3[47][0-9]{13}|'
    r'6(?:011|5[0-9]{2})[0-9]{12}|'
    r'35(?:2[0-9]{4}|[3-6][0-9]{5})[0-9]{12}|'
    r'30[0-5][0-9]{11,15}|'
    r'3[8-9][0-9]{14})\b'
)

EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', re.IGNORECASE)

SSN_PATTERN = re.compile(r'\b\d{3}[- ]?\d{2}[- ]?\d{4}\b')

PHONE_PATTERN = re.compile(
    r'(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}'
)

CVV_PATTERN = re.compile(r'\b\d{3,4}\b')

EXPIRY_PATTERN = re.compile(r'\b(0[1-9]|1[0-2])\/(\d{2})\b')

TOKEN_PATTERN = re.compile(
    r'(?:'
    r'eyJ[a-z0-9\-._~+/]+=*'  # JWT
    r'|[a-f0-9]{32,}'  # hex tokens
    r'|[A-Za-z0-9\-._~+/]{40,}'  # random tokens
    r')'
)

PASSWORD_FIELD_PATTERN = re.compile(
    r'<input[^>]+type=["\']password["\'][^>]*>',
    re.IGNORECASE
)

CARD_FIELD_PATTERN = re.compile(
    r'<input[^>]+(?:'
    r'name=["\'][^"\']*card[^"\']*["\']'
    r'|name=["\'][^"\']*cc[^"\']*["\']'
    r'|name=["\'][^"\']*pan[^"\']*["\']'
    r'|name=["\'][^"\']*cvv[^"\']*["\']'
    r'|id=["\'][^"\']*card[^"\']*["\']'
    r')(?:[^>]*)>',
    re.IGNORECASE
)

FORM_ACTION_PATTERN = re.compile(
    r'<form[^>]+action=["\']([^"\']*)["\']',
    re.IGNORECASE
)

IFRAME_PATTERN = re.compile(
    r'<iframe[^>]+src=["\']([^"\']*)["\'][^>]*>',
    re.IGNORECASE
)

SCRIPT_SRC_PATTERN = re.compile(
    r'<script[^>]+src=["\']([^"\']*)["\'][^>]*>',
    re.IGNORECASE
)

EXTERNAL_SCRIPT_PATTERN = re.compile(
    r'<script[^>]+src=["\'](https?://[^"\']*)["\'][^>]*>',
    re.IGNORECASE
)

EVENT_LISTENER_PATTERN = re.compile(
    r'(?:on\w+)\s*=\s*["\']([^"\']*)["\']',
    re.IGNORECASE
)

KEYLOGGER_EVENTS = [
    'onkeypress', 'onkeydown', 'onkeyup',
    'oninput', 'onchange', 'onblur',
]


# --- Analysis result types ---

@dataclass
class FormAnalysis:
    """Analysis of a single form."""
    url: str
    form_index: int
    action: str
    method: str = "GET"
    inputs: List[dict] = field(default_factory=list)
    sensitive_inputs: List[dict] = field(default_factory=list)
    is_https: bool = True
    has_csp: bool = False
    csp_header: str = ""
    issues: List[dict] = field(default_factory=list)


@dataclass
class JSAnalysis:
    """Analysis of JavaScript on a page."""
    url: str
    scripts: List[dict] = field(default_factory=list)
    external_scripts: List[dict] = field(default_factory=list)
    event_listeners: List[dict] = field(default_factory=list)
    keylogger_indicators: List[dict] = field(default_factory=list)
    suspicious_patterns: List[dict] = field(default_factory=list)
    issues: List[dict] = field(default_factory=list)


@dataclass
class NetworkAnalysis:
    """Analysis of network requests from a page."""
    url: str
    forms_submitted: List[dict] = field(default_factory=list)
    sensitive_data_sent: List[dict] = field(default_factory=list)
    insecure_requests: List[dict] = field(default_factory=list)
    issues: List[dict] = field(default_factory=list)


@dataclass
class SkimScanResult:
    """Complete skimming scan result for a URL."""
    target: str
    url: str
    timestamp: str
    forms: List[FormAnalysis] = field(default_factory=list)
    javascript: JSAnalysis = field(default_factory=JSAnalysis)
    network: NetworkAnalysis = field(default_factory=NetworkAnalysis)
    overall_risk: Severity = Severity.LOW
    findings: List[SkimFinding] = field(default_factory=list)
    summary: str = ""


# --- Main analyzer class ---

class WebSkimmerAnalyzer:
    """Analyzes web pages for skimming vulnerabilities."""

    def __init__(self, config: SkimConfig):
        self.config = config
        self.results: List[SkimScanResult] = []

    def analyze_page(self, html: str, url: str) -> SkimScanResult:
        """Analyze a single page's HTML for skimming indicators."""
        result = SkimScanResult(
            target=self.config.target,
            url=url,
            timestamp=now_iso(),
        )

        # Analyze forms
        result.forms = self._analyze_forms(html, url)

        # Analyze JavaScript
        result.javascript = self._analyze_javascript(html, url)

        # Check headers (from HTML meta / inline)
        self._check_security_headers(result, html)

        # Check for iframes
        self._check_iframes(result, html)

        # Generate findings
        result.findings = self._generate_findings(result)

        # Determine overall risk
        result.overall_risk = self._calculate_risk(result)

        # Generate summary
        result.summary = self._generate_summary(result)

        return result

    def _analyze_forms(self, html: str, url: str) -> List[FormAnalysis]:
        """Extract and analyze all forms from HTML."""
        forms = []
        parsed = urlparse(url)
        is_https = parsed.scheme == "https"

        # Find all form tags
        form_matches = re.finditer(
            r'<form[^>]*>(.*?)</form>',
            html,
            re.DOTALL | re.IGNORECASE
        )

        for idx, form_match in enumerate(form_matches):
            form_html = form_match.group(0)
            form_body = form_match.group(1)

            # Extract action
            action_match = re.search(
                r'action=["\']([^"\']*)["\']',
                form_html,
                re.IGNORECASE
            )
            action = action_match.group(1) if action_match else ""
            if action:
                action = urljoin(url, action)

            # Extract method
            method_match = re.search(
                r'method=["\']([A-Za-z]+)["\']',
                form_html,
                re.IGNORECASE
            )
            method = method_match.group(1).upper() if method_match else "GET"

            # Extract all inputs
            inputs = []
            input_matches = re.finditer(
                r'<input[^>]*>',
                form_html,
                re.IGNORECASE
            )
            for inp_match in input_matches:
                inp_html = inp_match.group(0)
                input_info = self._parse_input(inp_html)
                inputs.append(input_info)

                # Check if sensitive
                if self._is_sensitive_input(input_info):
                    input_info['sensitive'] = True
                    result_network = {
                        'type': 'sensitive_input',
                        'name': input_info.get('name', ''),
                        'value_pattern': input_info.get('value_pattern', ''),
                    }
                    forms[-1]['sensitive_inputs'].append(input_info) if forms else None

            # Determine form issues
            issues = []
            full_action = urljoin(url, action) if action else urljoin(url, form_match.group(0))

            if action:
                action_parsed = urlparse(action)
                if action and action_parsed.scheme == "http":
                    issues.append({
                        'type': 'insecure_form_action',
                        'severity': 'high',
                        'description': f"Form submits to {action} over HTTP (not HTTPS)",
                    })
                elif action and not action.startswith(('http://', 'https://', '/', '#')):
                    issues.append({
                        'type': 'relative_form_action',
                        'severity': 'low',
                        'description': f"Form action is relative: {action}",
                    })

            if method == "GET" and any(
                self._is_sensitive_input(inp) for inp in inputs
            ):
                issues.append({
                    'type': 'sensitive_data_in_get',
                    'severity': 'high',
                    'description': "Sensitive data submitted via GET method (exposed in URL/logs)",
                })

            # Check CSP for form
            has_csp = 'content-security-policy' in html.lower()

            form_analysis = FormAnalysis(
                url=url,
                form_index=idx,
                action=action,
                method=method,
                inputs=inputs,
                sensitive_inputs=[inp for inp in inputs if self._is_sensitive_input(inp)],
                is_https=is_https,
                has_csp=has_csp,
                issues=issues,
            )
            forms.append(form_analysis)

        # Also find forms without proper closing (self-closing or malformed)
        orphan_forms = re.finditer(
            r'<form[^>]*>',
            html,
            re.IGNORECASE
        )
        # Already covered above

        return forms

    def _parse_input(self, html: str) -> dict:
        """Parse an individual input element."""
        info = {
            'type': '',
            'name': '',
            'id': '',
            'value': '',
            'placeholder': '',
            'autocomplete': '',
            'pattern': '',
            'maxlength': '',
            'required': False,
            'value_pattern': '',
        }

        type_match = re.search(r'type=["\']([A-Za-z]+)["\']', html, re.IGNORECASE)
        info['type'] = type_match.group(1).lower() if type_match else ''

        name_match = re.search(r'name=["\']([^"\']*)["\']', html, re.IGNORECASE)
        info['name'] = name_match.group(1) if name_match else ''

        id_match = re.search(r'id=["\']([^"\']*)["\']', html, re.IGNORECASE)
        info['id'] = id_match.group(1) if id_match else ''

        value_match = re.search(r'value=["\']([^"\']*)["\']', html, re.IGNORECASE)
        info['value'] = value_match.group(1) if value_match else ''

        placeholder_match = re.search(
            r'placeholder=["\']([^"\']*)["\']', html, re.IGNORECASE
        )
        info['placeholder'] = placeholder_match.group(1) if placeholder_match else ''

        autocomplete_match = re.search(
            r'autocomplete=["\']([^"\']*)["\']', html, re.IGNORECASE
        )
        info['autocomplete'] = autocomplete_match.group(1) if autocomplete_match else ''

        pattern_match = re.search(r'pattern=["\']([^"\']*)["\']', html, re.IGNORECASE)
        info['pattern'] = pattern_match.group(1) if pattern_match else ''

        maxlength_match = re.search(r'maxlength=["\'](\d+)["\']', html, re.IGNORECASE)
        info['maxlength'] = maxlength_match.group(1) if maxlength_match else ''

        required_match = re.search(r'\brequired\b', html, re.IGNORECASE)
        info['required'] = bool(required_match)

        # Classify value pattern
        if info['type'] == 'password':
            info['value_pattern'] = 'password'
        elif info['name'] and 'card' in info['name'].lower():
            info['value_pattern'] = 'card_number'
        elif info['name'] and 'cvv' in info['name'].lower():
            info['value_pattern'] = 'cvv'
        elif info['name'] and 'expiry' in info['name'].lower():
            info['value_pattern'] = 'expiry'
        elif info['name'] and ('ssn' in info['name'].lower() or 'social' in info['name'].lower()):
            info['value_pattern'] = 'ssn'
        elif info['name'] and 'phone' in info['name'].lower():
            info['value_pattern'] = 'phone'
        elif info['name'] and 'email' in info['name'].lower():
            info['value_pattern'] = 'email'
        elif info['name'] and 'address' in info['name'].lower():
            info['value_pattern'] = 'address'

        return info

    def _is_sensitive_input(self, input_info: dict) -> bool:
        """Check if an input is sensitive."""
        sensitive_types = {'password', 'credit-card', 'tel', 'number'}
        sensitive_names = [
            'password', 'passwd', 'pwd', 'secret',
            'card_number', 'cc_number', 'cardnumber', 'ccnumber', 'pan',
            'cvv', 'cvc', 'card_code', 'security_code',
            'ssn', 'social_security', 'socialsecurity',
            'account_number', 'accountnumber', 'routing',
            'api_key', 'apikey', 'token', 'auth_token',
            'pin', 'personal_id',
        ]
        sensitive_placeholders = [
            'card number', 'card no', 'cardno', 'cc number',
            'cvv', 'cvc', 'security code', 'expiry', 'expiration',
            'ssn', 'social security', 'socialsecurity',
            'password', 'passwd', 'secret',
        ]

        if input_info.get('type') in sensitive_types:
            return True
        if input_info.get('name'):
            name_lower = input_info['name'].lower()
            if any(sn in name_lower for sn in sensitive_names):
                return True
        if input_info.get('placeholder'):
            ph_lower = input_info['placeholder'].lower()
            if any(sp in ph_lower for sp in sensitive_placeholders):
                return True
        if input_info.get('value_pattern') in (
            'password', 'card_number', 'cvv', 'expiry', 'ssn'
        ):
            return True
        if input_info.get('autocomplete') in (
            'cc-number', 'cc-csc', 'cc-exp', 'ssn',
            'current-password', 'new-password',
        ):
            return True

        return False

    def _analyze_javascript(self, html: str, url: str) -> JSAnalysis:
        """Analyze JavaScript on the page for skimming indicators."""
        analysis = JSAnalysis(url=url)

        # Find all scripts
        script_matches = re.finditer(
            r'<script[^>]*>(.*?)</script>',
            html,
            re.DOTALL | re.IGNORECASE
        )

        for script_match in script_matches:
            script_content = script_match.group(1)
            script_html = script_match.group(0)

            # Check for inline scripts
            if script_content.strip():
                analysis.scripts.append({
                    'type': 'inline',
                    'content_length': len(script_content),
                    'suspicious': self._check_script_content(script_content),
                })

            # Check for event listeners in the script tag
            events_found = EVENT_LISTENER_PATTERN.findall(script_html)
            for event in events_found:
                if any(e in event.lower() for e in KEYLOGGER_EVENTS):
                    analysis.event_listeners.append({
                        'event': event,
                        'location': 'inline_script',
                        'suspicious': True,
                    })

        # Find external scripts
        external_matches = EXTERNAL_SCRIPT_PATTERN.finditer(html)
        for ext_match in external_matches:
            src = ext_match.group(1)
            analysis.external_scripts.append({
                'src': src,
                'suspicious': self._is_suspicious_source(src),
            })

        # Check for inline event handlers on elements
        inline_events = EVENT_LISTENER_PATTERN.findall(html)
        for event in inline_events:
            if any(e in event.lower() for e in KEYLOGGER_EVENTS):
                if event not in [e['event'] for e in analysis.event_listeners]:
                    analysis.event_listeners.append({
                        'event': event,
                        'location': 'html_element',
                        'suspicious': True,
                    })

        # Analyze for keylogger patterns
        analysis.keylogger_indicators = self._detect_keylogger_patterns(html)

        # Analyze for suspicious DOM patterns
        analysis.suspicious_patterns = self._detect_suspicious_dom_patterns(html)

        # Generate JS issues
        if analysis.keylogger_indicators:
            for indicator in analysis.keylogger_indicators:
                analysis.issues.append({
                    'type': 'keylogger_pattern',
                    'severity': 'critical',
                    'description': indicator.get('description', 'Potential keylogger detected'),
                    'location': indicator.get('location', ''),
                })

        if analysis.suspicious_patterns:
            for pattern in analysis.suspicious_patterns:
                analysis.issues.append({
                    'type': 'suspicious_dom_pattern',
                    'severity': pattern.get('severity', 'medium'),
                    'description': pattern.get('description', ''),
                    'location': pattern.get('location', ''),
                })

        if analysis.external_scripts:
            for script in analysis.external_scripts:
                if script.get('suspicious'):
                    analysis.issues.append({
                        'type': 'suspicious_external_script',
                        'severity': 'high',
                        'description': f"External script from potentially suspicious source: {script['src']}",
                        'location': script['src'],
                    })

        return analysis

    def _check_script_content(self, content: str) -> bool:
        """Check if script content has suspicious indicators."""
        suspicious_patterns = [
            r'document\.write\s*\(',
            r'innerHTML\s*=',
            r'\.innerHTML\s*=',
            r'\.value\s*=\s*.*\+\s*.*',
            r'keylogger',
            r'keylog',
            r'keypress.*function',
            r'keydown.*function',
            r'getElementsByTagName.*input',
            r'document\.cookie.*=',
            r'decodeURIComponent.*document\.cookie',
            r'atob\s*\(',
            r'btoa\s*\(',
            r'eval\s*\(',
            r'Function\s*\(',
            r'XMLHttpRequest',
            r'fetch\s*\(',
            r'\.send\s*\(',
            r'FormData',
            r'navigator\.userAgent',
            r'window\.location',
            r'window\.location\.href',
            r'\.submit\s*\(',
            r'\.click\s*\(',
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True

        return False

    def _is_suspicious_source(self, src: str) -> bool:
        """Check if a script source is suspicious."""
        suspicious_domains = [
            'malware', 'phishing', 'steal', 'hack',
            'evil', 'spam', 'botnet',
            '127.0.0.1', 'localhost',
        ]

        src_lower = src.lower()
        for domain in suspicious_domains:
            if domain in src_lower:
                return True

        # Data URIs are suspicious for scripts
        if src.startswith('data:'):
            return True

        return False

    def _detect_keylogger_patterns(self, html: str) -> List[dict]:
        """Detect potential keylogger patterns in HTML/JS."""
        indicators = []

        # Check for key event handlers
        for event in KEYLOGGER_EVENTS:
            pattern = rf'{event}\s*=\s*["\'][^"\']*["\']'
            matches = re.finditer(pattern, html, re.IGNORECASE)
            for match in matches:
                indicators.append({
                    'type': 'key_event_handler',
                    'event': event,
                    'location': f'Line ~{html[:match.start()].count(chr(10)) + 1}',
                    'description': f'Key event handler detected: {event}',
                    'severity': 'high',
                })

        # Check for input event handlers that capture values
        input_capture_patterns = [
            (r'input.*value.*=', 'Input value capture'),
            (r'keypress.*value.*=', 'Keypress value capture'),
            (r'keydown.*value.*=', 'Keydown value capture'),
            (r'\.value\s*=\s*.*\w+.*\+\s*.*\.value', 'Value concatenation (possible exfiltration)'),
        ]

        for pattern, description in input_capture_patterns:
            matches = re.finditer(pattern, html, re.IGNORECASE)
            for match in matches:
                indicators.append({
                    'type': 'data_capture',
                    'description': description,
                    'location': f'Pattern match in HTML',
                    'severity': 'medium',
                })

        # Check for clipboard access
        clipboard_patterns = [
            r'navigator\.clipboard\.readText',
            r'navigator\.clipboard\.writeText',
            r'document\.execCommand.*copy',
            r'document\.execCommand.*paste',
        ]
        for pattern in clipboard_patterns:
            if re.search(pattern, html, re.IGNORECASE):
                indicators.append({
                    'type': 'clipboard_access',
                    'description': 'Clipboard read/write detected',
                    'severity': 'medium',
                })

        return indicators

    def _detect_suspicious_dom_patterns(self, html: str) -> List[dict]:
        """Detect suspicious DOM manipulation patterns."""
        patterns = []

        # Hidden iframes
        hidden_iframes = re.finditer(
            r'<iframe[^>]+style=["\']*(?:display\s*:\s*none|visibility\s*:\s*hidden|position\s*:\s*absolute[^;]*top\s*:\s*-9999)[^"\']*["\'][^>]*>',
            html,
            re.IGNORECASE
        )
        for match in hidden_iframes:
            patterns.append({
                'type': 'hidden_iframe',
                'description': 'Hidden iframe detected',
                'severity': 'high',
                'location': 'iframe element',
            })

        # Forms injected via JavaScript
        if re.search(r'createElement\s*\(\s*["\']form["\']\s*\)', html, re.IGNORECASE):
            patterns.append({
                'type': 'dynamic_form_creation',
                'description': 'Forms created dynamically via JavaScript',
                'severity': 'medium',
            })

        # Form action modification
        if re.search(r'action\s*=\s*["\'].*["\']', html, re.IGNORECASE):
            patterns.append({
                'type': 'form_action_modification',
                'description': 'Form action modification detected',
                'severity': 'medium',
            })

        # Overlay patterns (absolute positioned divs over forms)
        overlay_pattern = re.compile(
            r'position\s*:\s*absolute[^;]*>\s*z-index\s*:\s*(\d+)',
            re.IGNORECASE
        )
        z_index_matches = overlay_pattern.findall(html)
        if z_index_matches:
            max_z = max(int(z) for z in z_index_matches)
            if max_z > 100:
                patterns.append({
                    'type': 'high_z_index_element',
                    'description': f'Element with very high z-index ({max_z}) - possible overlay attack',
                    'severity': 'medium',
                })

        # Check for form action pointing to different domain
        form_actions = FORM_ACTION_PATTERN.findall(html)
        page_domain = urlparse(html).netloc if isinstance(html, str) else None
        # This is a rough check - in real use, we'd have the page URL

        return patterns

    def _check_iframes(self, result: SkimScanResult, html: str):
        """Check for iframe-based attacks."""
        iframe_matches = IFRAME_PATTERN.findall(html)

        for src in iframe_matches:
            # Check for hidden iframes
            iframe_pattern = re.compile(
                r'<iframe[^>]*src=["\']' + re.escape(src) + r'["\'][^>]*>',
                re.IGNORECASE
            )
            iframe_tag = iframe_pattern.search(html)
            if iframe_tag:
                iframe_html = iframe_tag.group(0)
                if 'display:none' in iframe_html.lower() or \
                   'visibility:hidden' in iframe_html.lower():
                    result.javascript.issues.append({
                        'type': 'hidden_iframe',
                        'severity': 'high',
                        'description': f'Hidden iframe: {src}',
                    })

            # Check if iframe src is on different domain
            iframe_parsed = urlparse(src)
            if iframe_parsed.netloc and iframe_parsed.netloc != urlparse(result.url).netloc:
                if src.startswith('http:') and result.url.startswith('https:'):
                    result.javascript.issues.append({
                        'type': 'mixed_content_iframe',
                        'severity': 'medium',
                        'description': f'HTTP iframe in HTTPS page: {src}',
                    })

    def _check_security_headers(self, result: SkimScanResult, html: str):
        """Check for security-related meta tags and headers."""
        # CSP meta tag
        csp_match = re.search(
            r'<meta[^>]+http-equiv=["\']Content-Security-Policy["\']+content=["\']([^"\']*)["\']',
            html,
            re.IGNORECASE
        )
        if csp_match:
            result.javascript.issues.append({
                'type': 'csp_present',
                'severity': 'info',
                'description': f'Content-Security-Policy present: {csp_match.group(1)[:200]}',
            })

        # HSTS meta (less common but check)
        hsts_match = re.search(
            r'<meta[^>]+http-equiv=["\']Strict-Transport-Security["\']',
            html,
            re.IGNORECASE
        )
        if hsts_match:
            result.javascript.issues.append({
                'type': 'hsts_present',
                'severity': 'info',
                'description': 'Strict-Transport-Security meta tag found',
            })

        # X-Frame-Options
        xfo_match = re.search(
            r'<meta[^>]+http-equiv=["\']X-Frame-Options["\']',
            html,
            re.IGNORECASE
        )
        if xfo_match:
            result.javascript.issues.append({
                'type': 'xfo_present',
                'severity': 'info',
                'description': 'X-Frame-Options meta tag found (clickjacking protection)',
            })

        # Check for missing security headers (can't check actual headers from HTML alone)
        if not csp_match:
            result.javascript.issues.append({
                'type': 'missing_csp',
                'severity': 'low',
                'description': 'No Content-Security-Policy meta tag found',
            })

    def _generate_findings(self, result: SkimScanResult) -> List[SkimFinding]:
        """Generate findings from the analysis result."""
        findings = []

        # Process form findings
        for form in result.forms:
            for issue in form.issues:
                severity = Severity(issue['severity'])
                finding = SkimFinding(
                    id=fuzz_id("F"),
                    severity=severity,
                    category=self._map_form_issue_to_category(issue['type']),
                    title=self._map_form_issue_to_title(issue['type']),
                    description=issue['description'],
                    target=result.target,
                    url=result.url,
                    element=f"Form #{form.form_index}",
                    evidence=issue['description'],
                    recommendation=self._get_recommendation(issue['type']),
                )
                findings.append(finding)

        # Process JS findings
        for issue in result.javascript.issues:
            severity = Severity(issue['severity'])
            finding = SkimFinding(
                id=fuzz_id("JS"),
                severity=severity,
                category=self._map_js_issue_to_category(issue['type']),
                title=self._map_js_issue_to_title(issue['type']),
                description=issue['description'],
                target=result.target,
                url=result.url,
                element="JavaScript",
                evidence=issue['description'],
                recommendation=self._get_js_recommendation(issue['type']),
            )
            findings.append(finding)

        # Process keylogger indicators
        for indicator in result.javascript.keylogger_indicators:
            severity = Severity(indicator.get('severity', 'high'))
            finding = SkimFinding(
                id=fuzz_id("KL"),
                severity=severity,
                category=SkimCategory.KEYLOGGER_PATTERN,
                title=f"Keylogger Indicator: {indicator.get('description', 'Unknown')}",
                description=f"Potential keylogging activity detected: {indicator.get('description', '')}",
                target=result.target,
                url=result.url,
                element=indicator.get('location', ''),
                evidence=f"Pattern: {indicator.get('type', '')}",
                recommendation=(
                    "Remove all keylogging code immediately. "
                    "Audit all JavaScript files for unauthorized data collection. "
                    "Implement Subresource Integrity (SRI) for all external scripts. "
                    "Use Content Security Policy to restrict script execution."
                ),
            )
            findings.append(finding)

        # Process suspicious DOM patterns
        for pattern in result.javascript.suspicious_patterns:
            severity = Severity(pattern.get('severity', 'medium'))
            finding = SkimFinding(
                id=fuzz_id("DOM"),
                severity=severity,
                category=SkimCategory.DOM_MANIPULATION,
                title=pattern.get('description', 'Suspicious DOM pattern'),
                description=pattern.get('description', ''),
                target=result.target,
                url=result.url,
                element=pattern.get('location', ''),
                evidence=pattern.get('type', ''),
                recommendation=(
                    "Review the purpose of this DOM element. "
                    "High z-index elements can be used to overlay forms and capture input. "
                    "Verify all dynamically created elements have legitimate purposes."
                ),
            )
            findings.append(finding)

        return findings

    def _map_form_issue_to_category(self, issue_type: str) -> SkimCategory:
        """Map form issue types to skim categories."""
        mapping = {
            'insecure_form_action': SkimCategory.INSECURE_TRANSMISSION,
            'sensitive_data_in_get': SkimCategory.INSECURE_TRANSMISSION,
            'relative_form_action': SkimCategory.INSECURE_TRANSMISSION,
        }
        return mapping.get(issue_type, SkimCategory.CREDENTIAL_HARVESTING)

    def _map_form_issue_to_title(self, issue_type: str) -> str:
        """Map form issue types to human-readable titles."""
        mapping = {
            'insecure_form_action': 'Form submits over insecure HTTP',
            'sensitive_data_in_get': 'Sensitive data exposed in URL via GET',
            'relative_form_action': 'Relative form action (could be hijacked)',
        }
        return mapping.get(issue_type, f'Form issue: {issue_type}')

    def _map_js_issue_to_category(self, issue_type: str) -> SkimCategory:
        """Map JS issue types to skim categories."""
        mapping = {
            'keylogger_pattern': SkimCategory.KEYLOGGER_PATTERN,
            'suspicious_dom_pattern': SkimCategory.DOM_MANIPULATION,
            'suspicious_external_script': SkimCategory.MAN_IN_THE_MIDDLE,
            'hidden_iframe': SkimCategory.IFRAME_INJECTION,
            'mixed_content_iframe': SkimCategory.INSECURE_TRANSMISSION,
            'missing_csp': SkimCategory.MISCONFIGURED_CSP,
            'csp_present': SkimCategory.MISCONFIGURED_CSP,
        }
        return mapping.get(issue_type, SkimCategory.DOM_MANIPULATION)

    def _map_js_issue_to_title(self, issue_type: str) -> str:
        """Map JS issue types to human-readable titles."""
        mapping = {
            'keylogger_pattern': 'Potential Keylogger Detected',
            'suspicious_dom_pattern': 'Suspicious DOM Manipulation Pattern',
            'suspicious_external_script': 'Suspicious External Script Loaded',
            'hidden_iframe': 'Hidden iframe (possible clickjacking/skimming)',
            'mixed_content_iframe': 'Insecure iframe in secure page',
            'missing_csp': 'Missing Content-Security-Policy',
            'csp_present': 'Content-Security-Policy Found',
        }
        return mapping.get(issue_type, f'JS Issue: {issue_type}')

    def _get_recommendation(self, issue_type: str) -> str:
        """Get recommendation for form issues."""
        mapping = {
            'insecure_form_action': (
                "Change form action to use HTTPS. "
                "Ensure all payment and credential forms submit over TLS. "
                "Implement HSTS to prevent downgrade attacks."
            ),
            'sensitive_data_in_get': (
                "Change form method from GET to POST for all sensitive data. "
                "Never transmit passwords, card numbers, or tokens via GET parameters."
            ),
            'relative_form_action': (
                "Use absolute URLs for form actions. "
                "Relative URLs can be manipulated via base tag injection. "
                "Always specify the full HTTPS URL."
            ),
        }
        return mapping.get(issue_type, "Review and secure this form.")

    def _get_js_recommendation(self, issue_type: str) -> str:
        """Get recommendation for JS issues."""
        mapping = {
            'keylogger_pattern': (
                "Immediately remove all keylogging code. "
                "Audit all third-party scripts and remove unauthorized data collection. "
                "Implement Subresource Integrity (SRI) for all scripts. "
                "Use a strict Content Security Policy. "
                "Monitor for unauthorized script injections regularly."
            ),
            'suspicious_dom_pattern': (
                "Review the purpose of this DOM element. "
                "High z-index overlays can capture user input. "
                "Verify all dynamic elements serve legitimate purposes."
            ),
            'suspicious_external_script': (
                "Verify the legitimacy of this external script source. "
                "Remove any unauthorized third-party scripts. "
                "Implement SRI hashes for all external scripts."
            ),
            'hidden_iframe': (
                "Remove hidden iframes unless they serve a legitimate purpose. "
                "Hidden iframes are commonly used for clickjacking and skimming attacks. "
                "Implement X-Frame-Options or CSP frame-ancestors."
            ),
            'mixed_content_iframe': (
                "Replace HTTP iframe sources with HTTPS equivalents. "
                "Mixed content undermines the security of the entire page."
            ),
            'missing_csp': (
                "Implement a strict Content-Security-Policy header. "
                "Start with report-only mode to identify breakage, then enforce. "
                "CSP prevents unauthorized script injection and skimming."
            ),
        }
        return mapping.get(issue_type, "Review and remediate this issue.")

    def _calculate_risk(self, result: SkimScanResult) -> Severity:
        """Calculate overall risk level for the scan result."""
        risk_score = 0

        # Factor in form issues
        for form in result.forms:
            for issue in form.issues:
                if issue['severity'] == 'critical':
                    risk_score += 4
                elif issue['severity'] == 'high':
                    risk_score += 3
                elif issue['severity'] == 'medium':
                    risk_score += 2
                elif issue['severity'] == 'low':
                    risk_score += 1

        # Factor in JS issues
        for issue in result.javascript.issues:
            if issue['severity'] == 'critical':
                risk_score += 4
            elif issue['severity'] == 'high':
                risk_score += 3
            elif issue['severity'] == 'medium':
                risk_score += 2
            elif issue['severity'] == 'low':
                risk_score += 1

        # Factor in keylogger indicators
        risk_score += len(result.javascript.keylogger_indicators) * 3

        # Determine severity from score
        if risk_score >= 8:
            return Severity.CRITICAL
        elif risk_score >= 5:
            return Severity.HIGH
        elif risk_score >= 3:
            return Severity.MEDIUM
        elif risk_score >= 1:
            return Severity.LOW
        else:
            return Severity.INFO

    def _generate_summary(self, result: SkimScanResult) -> str:
        """Generate a human-readable summary of the scan."""
        total_forms = len(result.forms)
        sensitive_forms = sum(
            1 for f in result.forms if f.sensitive_inputs
        )
        total_js_issues = len(result.javascript.issues)
        keylogger_count = len(result.javascript.keylogger_indicators)
        total_findings = len(result.findings)

        critical_findings = sum(1 for f in result.findings if f.severity == Severity.CRITICAL)
        high_findings = sum(1 for f in result.findings if f.severity == Severity.HIGH)

        summary = (
            f"Scan of {result.url}\n"
            f"{'='*50}\n"
            f"Forms found: {total_forms} ({sensitive_forms} with sensitive inputs)\n"
            f"JavaScript issues: {total_js_issues}\n"
            f"Keylogger indicators: {keylogger_count}\n"
            f"Total findings: {total_findings}\n"
            f"  Critical: {critical_findings}\n"
            f"  High: {high_findings}\n"
            f"Overall risk: {result.overall_risk.value.upper()}\n"
        )

        if result.findings:
            summary += "\nTop Findings:\n"
            for finding in sorted(
                result.findings,
                key=lambda f: (f.severity.value, f.category.value),
                reverse=True
            )[:5]:
                summary += f"  [{finding.severity.value.upper()}] {finding.title}\n"
                summary += f"    {finding.description[:200]}\n\n"

        return summary


# --- CLI ---

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Web Skimmer Analyzer — detect payment/credential skimming vulnerabilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python web_skimmer.py --target https://shop.example.com
      --scan full --output results/skim_report.json

  python web_skimmer.py --target https://shop.example.com/checkout
      --scan payment-forms --csp --hsts --mixed-content
        """,
    )
    parser.add_argument("--target", required=True, help="Base URL to scan")
    parser.add_argument("--scan", default="full",
                        choices=["full", "payment-forms", "credential-forms", "javascript", "csp"],
                        help="Type of scan to perform")
    parser.add_argument("--urls", nargs="+", help="Specific URLs to scan (default: target/)")
    parser.add_argument("--output", help="Output file for JSON results")
    parser.add_argument("--csp", action="store_true", help="Check Content-Security-Policy")
    parser.add_argument("--hsts", action="store_true", help="Check HSTS")
    parser.add_argument("--mixed-content", action="store_true", help="Check for mixed content")
    parser.add_argument("--js-lint", type=int, default=3, help="JS suspiciousness threshold")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    return parser


async def async_main(args: argparse.Namespace):
    """Async entry point."""
    config = SkimConfig(
        target=args.target.rstrip("/"),
        scan_type=args.scan,
        check_csp=args.csp,
        check_hsts=args.hsts,
        check_mixed_content=args.mixed_content,
        js_lint_threshold=args.js_lint,
    )

    analyzer = WebSkimmerAnalyzer(config)

    # Determine URLs to scan
    if args.urls:
        urls = args.urls
    else:
        urls = [args.target + "/", args.target + "/checkout", args.target + "/payment"]

    # Run analysis (synchronous for HTML-based scanning)
    all_results = []
    for url in urls:
        logger.info(f"Scanning: {url}")
        # In a real implementation, we'd fetch the HTML here
        # For the tool framework, we provide the analysis capability
        # that can be called with fetched HTML
        print(f"\n{'='*60}")
        print(f"WEB SKIMMING SCAN: {url}")
        print(f"{'='*60}")
        print(f"\nNote: Provide HTML content via the analyzer.analyze_page(html, url) method.")
        print(f"Tool is ready to analyze fetched HTML for skimming indicators.")
        print(f"\nAnalyzer capabilities:")
        print(f"  - Form analysis (detects insecure form actions, sensitive data in GET)")
        print(f"  - JavaScript analysis (detects keyloggers, suspicious scripts)")
        print(f"  - Iframe analysis (detects hidden/mixed-content iframes)")
        print(f"  - CSP/HSTS/XFO header checking")
        print(f"  - DOM manipulation pattern detection")
        print(f"  - Overall risk scoring")
        print(f"\nTo use: analyzer.analyze_page(html_content, url)")
        print(f"{'='*60}\n")

    # Output results
    if args.output and all_results:
        output = {
            "version": VERSION,
            "timestamp": now_iso(),
            "target": args.target,
            "results": [
                {
                    "url": r.url,
                    "overall_risk": r.overall_risk.value,
                    "forms_count": len(r.forms),
                    "js_issues_count": len(r.javascript.issues),
                    "findings_count": len(r.findings),
                    "findings": [f.__dict__ for f in r.findings],
                    "summary": r.summary,
                }
                for r in all_results
            ],
        }
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2, default=str)
        print(f"Results written to {args.output}")


def main():
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if aiohttp is None:
        print("WARNING: aiohttp not installed. HTTP fetching features limited.")
        print("Install with: pip install aiohttp")

    try:
        asyncio.run(async_main(args))
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(130)


if __name__ == "__main__":
    main()
