#!/usr/bin/env python3
"""
MITMProxy Add-on for Courtyard.io
Intercepts and logs all Courtyard API calls.
Run with: mitmproxy -s courtyard_mitm_addon.py -p 8080
"""
import json
from mitmproxy import http
from datetime import datetime

LOG_FILE = "courtyard_traffic.jsonl"

# Target domains
TARGET_DOMAINS = [
    "courtyard.io",
    "api.courtyard.io",
    "home-carousel.courtyard.io",
]

def is_target(host: str) -> bool:
    return any(d in host for d in TARGET_DOMAINS)

def log_entry(entry: dict):
    """Append to log file."""
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

class CourtyardInterceptor:
    def request(self, flow: http.HTTPFlow):
        """Intercept outgoing requests."""
        if not is_target(flow.request.pretty_host):
            return

        entry = {
            "timestamp": datetime.now().isoformat(),
            "direction": "REQUEST",
            "method": flow.request.method,
            "url": flow.request.pretty_url,
            "host": flow.request.pretty_host,
            "headers": dict(flow.request.headers),
        }

        # Log body for API calls
        if "/api/" in flow.request.pretty_url:
            try:
                body = flow.request.content.decode("utf-8", errors="ignore")
                entry["body"] = body[:1000]
            except:
                pass

        # Log auth headers (for analysis, not storage!)
        auth_headers = {}
        for key, value in flow.request.headers.items():
            if key.lower() in ["authorization", "x-api-key", "cookie"]:
                auth_headers[key] = value[:100] + "..." if len(value) > 100 else value

        if auth_headers:
            entry["auth_headers"] = auth_headers

        log_entry(entry)
        print(f"[REQ] {flow.request.method} {flow.request.pretty_url}")

    def response(self, flow: http.HTTPFlow):
        """Intercept incoming responses."""
        if not is_target(flow.request.pretty_host):
            return

        entry = {
            "timestamp": datetime.now().isoformat(),
            "direction": "RESPONSE",
            "url": flow.request.pretty_url,
            "status": flow.response.status_code,
            "size": len(flow.response.content) if flow.response.content else 0,
        }

        # Log response body for API errors (might leak info)
        if flow.response.status_code >= 400 and "/api/" in flow.request.pretty_url:
            try:
                body = flow.response.content.decode("utf-8", errors="ignore")
                entry["error_body"] = body[:500]
            except:
                pass

        log_entry(entry)
        print(f"[RES] {flow.response.status_code} {flow.request.pretty_url}")

# Register the addon
addons = [CourtyardInterceptor()]

# Optional: Intercept and modify specific requests
class CourtyardModifier:
    """Modify requests to test for weaknesses."""

    def request(self, flow: http.HTTPFlow):
        if not is_target(flow.request.pretty_host):
            return

        # Test 1: Add X-Forwarded-For to bypass IP restrictions
        flow.request.headers["X-Forwarded-For"] = "127.0.0.1"

        # Test 2: Check if User-Agent validation exists
        flow.request.headers["User-Agent"] = "Courtyard-Internal/1.0"

        # Test 3: CORS bypass attempts
        flow.request.headers["Origin"] = "https://courtyard.io"
        flow.request.headers["Referer"] = "https://courtyard.io/admin"

addons.append(CourtyardModifier())
