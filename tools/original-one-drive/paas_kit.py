#!/usr/bin/env python3
"""
paas_kit.py — Phishing-as-a-Service Campaign Orchestration Kit v1.0.0
======================================================================
Coordinates phishing page hosting, lure generation, and capture analysis
for authorized red team engagements and security awareness training.

FOR AUTHORIZED PENETRATION TESTING AND SECURITY AWARENESS TRAINING
AGAINST OWNED OR EXPLICITLY AUTHORIZED TARGETS ONLY.

Usage:
  python paas_kit.py campaign-create "Q4 Security Awareness Training"
  python paas_kit.py campaign-list
  python paas_kit.py campaign-start "Q4 Security Awareness Training"
  python paas_kit.py campaign-report "Q4 Security Awareness Training" \\
      --output-format markdown --output-dir results/reports
  python paas_kit.py campaign-export "Q4 Security Awareness Training" \\
      --output-file results/export/campaign.json
  python paas_kit.py campaign-import results/import/campaign.json

Author: bionic daughter (trained by Dad/Rigoberto Gomez)
"""

import argparse
import json
import logging
import os
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VERSION = "1.0.0"
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
DEFAULT_CAMPAIGN_DIR = "results/phishing_campaigns"
DEFAULT_REPORT_DIR = "results/reports"
DEFAULT_CONFIG_PATH = "tools/phishing_config.yaml"

STATUS_DRAFT = "draft"
STATUS_ACTIVE = "active"
STATUS_PAUSED = "paused"
STATUS_COMPLETED = "completed"
STATUS_DELETED = "deleted"

VALID_STATUSES = (STATUS_DRAFT, STATUS_ACTIVE, STATUS_PAUSED,
                   STATUS_COMPLETED, STATUS_DELETED)


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT)

def random_hex(n: int = 16) -> str:
    return uuid.uuid4().hex[:n]

def generate_campaign_id() -> str:
    return f"CMP-{random_hex(10).upper()}"

def truncate(s: str, max_len: int = 500) -> str:
    if len(s) <= max_len:
        return s
    half = max_len // 2
    return s[:half] + "\n...[truncated]...\n" + s[-half:]

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
        json.dump(obj, f, indent=2, default=str)

def load_yaml(path: str) -> dict:
    if yaml is None:
        raise RuntimeError("PyYAML not installed")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def save_yaml(path: str, obj: Any) -> None:
    if yaml is None:
        raise RuntimeError("PyYAML not installed")
    ensure_dir(Path(path).parent)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(obj, f, default_flow_style=False, sort_keys=False)

def slugify(name: str) -> str:
    return re.sub(r'[^\w\-]', '_', name.lower())

def sanitize_id(raw: str) -> str:
    """Turn a campaign name into a safe filename component."""
    return slugify(raw)[:80]


# ---------------------------------------------------------------------------
# Campaign data model
# ---------------------------------------------------------------------------

class Campaign:
    """Represents a phishing campaign."""

    def __init__(self, data: Optional[dict] = None):
        if data:
            self._data = data
        else:
            self._data = {
                "id": generate_campaign_id(),
                "name": "",
                "description": "",
                "status": STATUS_DRAFT,
                "created_at": now_iso(),
                "updated_at": now_iso(),
                "started_at": None,
                "paused_at": None,
                "completed_at": None,
                "target_group": "",
                "target_count": 0,
                "lure_template": "",
                "phishing_template": "",
                "phishing_page_url": "",
                "lure_count": 0,
                "send_schedule": {},
                "metrics": {
                    "emails_sent": 0,
                    "emails_delivered": 0,
                    "opens": 0,
                    "clicks": 0,
                    "captures": 0,
                    "unique_captures": 0,
                    "first_capture_at": None,
                    "last_capture_at": None,
                    "capture_categories": {},
                    "top_lures": [],
                },
                "metadata": {},
            }

    @property
    def id(self) -> str:
        return self._data["id"]

    @property
    def name(self) -> str:
        return self._data["name"]

    @name.setter
    def name(self, value: str):
        self._data["name"] = value
        self._data["updated_at"] = now_iso()

    @property
    def status(self) -> str:
        return self._data["status"]

    @status.setter
    def status(self, value: str):
        if value not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {value}")
        self._data["status"] = value
        self._data["updated_at"] = now_iso()
        if value == STATUS_ACTIVE:
            self._data["started_at"] = self._data["started_at"] or now_iso()
        elif value == STATUS_PAUSED:
            self._data["paused_at"] = now_iso()
        elif value == STATUS_COMPLETED:
            self._data["completed_at"] = now_iso()

    def to_dict(self) -> dict:
        return dict(self._data)

    def to_json(self, path: str):
        save_json(path, self._data)

    @classmethod
    def from_json(cls, path: str) -> "Campaign":
        data = load_json(path)
        return cls(data)

    def update_metrics(self, emails_sent: int = 0, emails_delivered: int = 0,
                       opens: int = 0, clicks: int = 0, captures: int = 0,
                       unique_captures: int = 0,
                       capture_categories: Optional[Dict[str, int]] = None,
                       first_capture_at: Optional[str] = None,
                       last_capture_at: Optional[str] = None,
                       top_lures: Optional[List[dict]] = None):
        self._data["metrics"]["emails_sent"] = emails_sent
        self._data["metrics"]["emails_delivered"] = emails_delivered
        self._data["metrics"]["opens"] = opens
        self._data["metrics"]["clicks"] = clicks
        self._data["metrics"]["captures"] = captures
        self._data["metrics"]["unique_captures"] = unique_captures
        if capture_categories:
            self._data["metrics"]["capture_categories"] = capture_categories
        if first_capture_at:
            self._data["metrics"]["first_capture_at"] = first_capture_at
        if last_capture_at:
            self._data["metrics"]["last_capture_at"] = last_capture_at
        if top_lures:
            self._data["metrics"]["top_lures"] = top_lures
        self._data["updated_at"] = now_iso()


# ---------------------------------------------------------------------------
# Campaign store
# ---------------------------------------------------------------------------

class CampaignStore:
    """Manages persistence of campaigns to disk."""

    def __init__(self, campaign_dir: str):
        self.campaign_dir = Path(campaign_dir)
        ensure_dir(self.campaign_dir)
        self._index: Dict[str, str] = {}  # id -> file path

    def _resolve_path(self, campaign_id: str) -> Path:
        return self.campaign_dir / f"{campaign_id}.json"

    def list(self) -> List[Campaign]:
        """List all campaigns (excluding deleted ones)."""
        campaigns = []
        for json_file in sorted(self.campaign_dir.glob("*.json")):
            try:
                c = Campaign.from_json(str(json_file))
                if c.status != STATUS_DELETED:
                    campaigns.append(c)
            except Exception as e:
                logging.warning("Skipping corrupt campaign file %s: %s",
                                json_file, e)
        return campaigns

    def get(self, campaign_id: str) -> Optional[Campaign]:
        """Get a campaign by ID."""
        path = self._resolve_path(campaign_id)
        if not path.exists():
            return None
        try:
            return Campaign.from_json(str(path))
        except Exception as e:
            logging.error("Failed to load campaign %s: %s", campaign_id, e)
            return None

    def save(self, campaign: Campaign) -> str:
        """Save a campaign to disk."""
        path = self._resolve_path(campaign.id)
        campaign.to_json(str(path))
        return str(path)

    def delete(self, campaign_id: str) -> bool:
        """Mark a campaign as deleted (soft delete)."""
        campaign = self.get(campaign_id)
        if campaign is None:
            return False
        campaign.status = STATUS_DELETED
        self.save(campaign)
        return True

    def get_by_name(self, name: str) -> Optional[Campaign]:
        """Find a campaign by name (case-insensitive)."""
        name_lower = name.lower()
        for c in self.list():
            if c.name.lower() == name_lower:
                return c
        return None

    def import_campaign(self, source_path: str) -> Campaign:
        """Import a campaign from a JSON file."""
        data = load_json(source_path)
        campaign = Campaign(data)
        self.save(campaign)
        return campaign

    def export_campaign(self, campaign: Campaign, target_path: str) -> str:
        """Export a campaign to a JSON file."""
        campaign.to_json(target_path)
        return target_path


# ---------------------------------------------------------------------------
# Report generator
# ---------------------------------------------------------------------------

class ReportGenerator:
    """Generates campaign reports in various formats."""

    def __init__(self, campaign: Campaign):
        self.campaign = campaign

    def generate_summary(self) -> dict:
        """Generate a summary stats dict."""
        m = self.campaign._data["metrics"]
        total_sent = m["emails_sent"] or 1
        return {
            "campaign_id": self.campaign.id,
            "campaign_name": self.campaign.name,
            "status": self.campaign.status,
            "created_at": self.campaign._data["created_at"],
            "started_at": self.campaign._data["started_at"],
            "completed_at": self.campaign._data["completed_at"],
            "target_group": self.campaign._data["target_group"],
            "target_count": self.campaign._data["target_count"],
            "lure_template": self.campaign._data["lure_template"],
            "phishing_template": self.campaign._data["phishing_template"],
            "lure_count": self.campaign._data["lure_count"],
            "total_sent": m["emails_sent"],
            "delivered": m["emails_delivered"],
            "delivery_rate": f"{(m['emails_delivered'] / total_sent * 100):.1f}%" if total_sent else "N/A",
            "opens": m["opens"],
            "open_rate": f"{(m['opens'] / total_sent * 100):.1f}%" if total_sent else "N/A",
            "clicks": m["clicks"],
            "click_rate": f"{(m['clicks'] / total_sent * 100):.1f}%" if total_sent else "N/A",
            "click_to_open_rate": f"{(m['clicks'] / max(m['opens'], 1) * 100):.1f}%" if m['opens'] else "N/A",
            "captures": m["captures"],
            "capture_rate": f"{(m['captures'] / total_sent * 100):.1f}%" if total_sent else "N/A",
            "capture_to_click_rate": f"{(m['captures'] / max(m['clicks'], 1) * 100):.1f}%" if m['clicks'] else "N/A",
            "unique_captures": m["unique_captures"],
            "capture_categories": m.get("capture_categories", {}),
            "first_capture_at": m.get("first_capture_at"),
            "last_capture_at": m.get("last_capture_at"),
            "top_lures": m.get("top_lures", []),
        }

    def generate_markdown(self, summary: Optional[dict] = None) -> str:
        """Generate a Markdown report."""
        s = summary or self.generate_summary()
        md = []
        md.append(f"# Phishing Campaign Report")
        md.append("")
        md.append(f"**Campaign:** {s['campaign_name']}")
        md.append(f"**ID:** `{s['campaign_id']}`")
        md.append(f"**Status:** {s['status']}")
        md.append(f"**Created:** {s['created_at']}")
        if s['started_at']:
            md.append(f"**Started:** {s['started_at']}")
        if s['completed_at']:
            md.append(f"**Completed:** {s['completed_at']}")
        md.append("")
        md.append("## Target Information")
        md.append("")
        md.append(f"- **Target Group:** {s['target_group'] or 'Not specified'}")
        md.append(f"- **Target Count:** {s['target_count']}")
        md.append(f"- **Lure Template:** {s['lure_template'] or 'Not set'}")
        md.append(f"- **Phishing Template:** {s['phishing_template'] or 'Not set'}")
        md.append(f"- **Lure Count:** {s['lure_count']}")
        md.append("")
        md.append("## Campaign Metrics")
        md.append("")
        md.append(f"| Metric | Count | Rate |")
        md.append(f"|--------|-------|------|")
        md.append(f"| Emails Sent | {s['total_sent']} | — |")
        md.append(f"| Delivered | {s['delivered']} | {s['delivery_rate']} |")
        md.append(f"| Opens | {s['opens']} | {s['open_rate']} |")
        md.append(f"| Clicks | {s['clicks']} | {s['click_rate']} |")
        md.append(f"| Clicks / Opens | — | {s['click_to_open_rate']} |")
        md.append(f"| Captures | {s['captures']} | {s['capture_rate']} |")
        md.append(f"| Captures / Clicks | — | {s['capture_to_click_rate']} |")
        md.append(f"| Unique Captures | {s['unique_captures']} | — |")
        md.append("")
        md.append("## Capture Categories")
        md.append("")
        cats = s.get("capture_categories", {})
        if cats:
            for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
                md.append(f"- **{cat}:** {count}")
        else:
            md.append("_No captures recorded._")
        md.append("")
        md.append("## Timeline")
        md.append("")
        if s['first_capture_at']:
            md.append(f"- **First capture:** {s['first_capture_at']}")
        if s['last_capture_at']:
            md.append(f"- **Last capture:** {s['last_capture_at']}")
        md.append("")
        md.append("## Top Performing Lures")
        md.append("")
        top = s.get("top_lures", [])
        if top:
            for i, lure in enumerate(top[:5], 1):
                md.append(f"{i}. **{lure.get('name', 'Unknown')}** — "
                          f"{lure.get('captures', 0)} captures, "
                          f"{lure.get('click_rate', 'N/A')} click rate")
        else:
            md.append("_No lure performance data._")
        md.append("")
        md.append("---")
        md.append(f"*Report generated: {now_iso()}*")
        md.append(f"*Campaign Orchestration Kit v{VERSION}*")
        return "\n".join(md)

    def generate_json(self, summary: Optional[dict] = None) -> dict:
        """Generate a JSON report dict."""
        return summary or self.generate_summary()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(
        description="Phishing-as-a-Service Campaign Orchestration Kit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python paas_kit.py campaign-create "Q4 Security Awareness Training"
      --target-group "Finance Department" --target-count 45
      --lure-template fake_invoice --phishing-template corporate_login
  python paas_kit.py campaign-list
  python paas_kit.py campaign-start "Q4 Security Awareness Training"
  python paas_kit.py campaign-report "Q4 Security Awareness Training" \\
      --output-format markdown --output-dir results/reports
  python paas_kit.py campaign-export "Q4 Security Awareness Training" \\
      --output-file results/import/q4_campaign.json
  python paas_kit.py campaign-import results/import/q4_campaign.json
  python paas_kit.py metrics fake_invoice --capture-dir results/phishing_captures
""",
    )
    sub = parser.add_subparsers(dest="command")

    # campaign-create
    cc = sub.add_parser("campaign-create", help="Create a new campaign")
    cc.add_argument("name", help="Campaign name")
    cc.add_argument("--description", "-d", help="Campaign description")
    cc.add_argument("--target-group", "-g", help="Target group description")
    cc.add_argument("--target-count", "-n", type=int, help="Number of targets")
    cc.add_argument("--lure-template", "-l", help="Lure template name")
    cc.add_argument("--phishing-template", "-p", help="Phishing page template name")
    cc.add_argument("--phishing-url", "-u", help="Phishing page URL")
    cc.add_argument("--campaign-dir", default=DEFAULT_CAMPAIGN_DIR,
                     help="Campaign storage directory")

    # campaign-list
    cl = sub.add_parser("campaign-list", help="List all campaigns")
    cl.add_argument("--campaign-dir", default=DEFAULT_CAMPAIGN_DIR,
                    help="Campaign storage directory")

    # campaign-start / -stop / -pause / -resume / -complete
    for cmd, help_text in [
        ("campaign-start", "Start a campaign"),
        ("campaign-stop", "Stop a campaign"),
        ("campaign-pause", "Pause a campaign"),
        ("campaign-resume", "Resume a paused campaign"),
        ("campaign-complete", "Mark a campaign as completed"),
    ]:
        s = sub.add_parser(cmd, help=help_text)
        s.add_argument("name", help="Campaign name or ID")
        s.add_argument("--campaign-dir", default=DEFAULT_CAMPAIGN_DIR,
                       help="Campaign storage directory")

    # campaign-report
    cr = sub.add_parser("campaign-report", help="Generate a campaign report")
    cr.add_argument("name", help="Campaign name or ID")
    cr.add_argument("--output-format", choices=("json", "markdown"), default="markdown",
                    help="Report format (default: markdown)")
    cr.add_argument("--output-dir", default=DEFAULT_REPORT_DIR,
                    help="Report output directory")
    cr.add_argument("--output-file", help="Specific output filename")
    cr.add_argument("--campaign-dir", default=DEFAULT_CAMPAIGN_DIR,
                    help="Campaign storage directory")

    # campaign-export / -import
    for cmd, help_text in [
        ("campaign-export", "Export a campaign to JSON"),
        ("campaign-import", "Import a campaign from JSON"),
    ]:
        e = sub.add_parser(cmd, help=help_text)
        e.add_argument("name", nargs="?", help="Campaign name or ID (export only)")
        e.add_argument("--output-file", "-o", help="Output file path (export)")
        e.add_argument("--input-file", "-i", help="Input file path (import)")
        e.add_argument("--campaign-dir", default=DEFAULT_CAMPAIGN_DIR,
                       help="Campaign storage directory")

    # metrics (reads capture files directly)
    m = sub.add_parser("metrics", help="Analyze capture files for a template")
    m.add_argument("template", help="Template name to analyze")
    m.add_argument("--capture-dir", help="Capture directory")
    m.add_argument("--campaign-dir", default=DEFAULT_CAMPAIGN_DIR,
                   help="Campaign storage directory")

    # init-config
    ic = sub.add_parser("init-config", help="Create a default config file")
    ic.add_argument("--config-path", default=DEFAULT_CONFIG_PATH,
                    help="Where to create the config file")

    return parser


def find_campaign(store: CampaignStore, name_or_id: str) -> Campaign:
    """Find a campaign by name or ID. Exits on failure."""
    c = store.get(name_or_id)
    if c is None:
        c = store.get_by_name(name_or_id)
    if c is None:
        logging.error("Campaign not found: %s", name_or_id)
        sys.exit(1)
    return c


def cmd_campaign_create(args):
    """Create a new campaign."""
    store = CampaignStore(args.campaign_dir)
    existing = store.get_by_name(args.name)
    if existing:
        logging.warning("A campaign with this name already exists: %s (%s)",
                        args.name, existing.id)
        sys.exit(1)

    campaign = Campaign()
    campaign.name = args.name
    if args.description:
        campaign._data["description"] = args.description
    if args.target_group:
        campaign._data["target_group"] = args.target_group
    if args.target_count:
        campaign._data["target_count"] = args.target_count
    if args.lure_template:
        campaign._data["lure_template"] = args.lure_template
    if args.phishing_template:
        campaign._data["phishing_template"] = args.phishing_template
    if args.phishing_url:
        campaign._data["phishing_page_url"] = args.phishing_url

    path = store.save(campaign)
    print(f"Created campaign: {campaign.name}")
    print(f"  ID: {campaign.id}")
    print(f"  Status: {campaign.status}")
    print(f"  Stored: {path}")


def cmd_campaign_list(args):
    """List all campaigns."""
    store = CampaignStore(args.campaign_dir)
    campaigns = store.list()
    if not campaigns:
        print("No campaigns found.")
        return

    print(f"Campaigns ({len(campaigns)}):")
    print()
    for c in campaigns:
        print(f"  [{c.status.upper()}] {c.id} — {c.name}")
        if c._data["target_group"]:
            print(f"         Target: {c._data['target_group']} ({c._data['target_count']})")
        if c._data["lure_template"]:
            print(f"         Lure: {c._data['lure_template']} → {c._data['phishing_template']}")
        if c._data["started_at"]:
            print(f"         Started: {c._data['started_at']}")
        if c._data["metrics"]["captures"] > 0:
            print(f"         Captures: {c._data['metrics']['captures']}")
        print()


def cmd_campaign_lifecycle(args, target_status: str):
    """Generic lifecycle command (start/stop/pause/resume/complete)."""
    store = CampaignStore(args.campaign_dir)
    campaign = find_campaign(store, args.name)
    campaign.status = target_status
    store.save(campaign)
    status_labels = {
        STATUS_ACTIVE: "started",
        STATUS_PAUSED: "paused",
        STATUS_COMPLETED: "completed",
        STATUS_STOP: "stopped",
    }
    action = status_labels.get(target_status, target_status)
    print(f"Campaign '{campaign.name}' ({campaign.id}) {action}.")
    print(f"  Status: {campaign.status}")
    if target_status == STATUS_ACTIVE:
        print(f"  Started at: {campaign._data['started_at']}")
    elif target_status == STATUS_PAUSED:
        print(f"  Paused at: {campaign._data['paused_at']}")


def cmd_campaign_report(args):
    """Generate a campaign report."""
    store = CampaignStore(args.campaign_dir)
    campaign = find_campaign(store, args.name)

    generator = ReportGenerator(campaign)

    if args.output_format == "markdown":
        report = generator.generate_markdown()
    else:
        report = generator.generate_json()

    if args.output_file:
        out_path = args.output_file
    else:
        safe_name = sanitize_id(campaign.name)
        ext = "md" if args.output_format == "markdown" else "json"
        out_path = os.path.join(args.output_dir,
                                f"report_{safe_name}_{campaign.id}.{ext}")

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    if args.output_format == "markdown":
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(report)
    else:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)

    print(f"Report generated: {out_path}")
    print(f"  Campaign: {campaign.name}")
    print(f"  Status: {campaign.status}")
    m = campaign._data["metrics"]
    if m["captures"] > 0:
        print(f"  Captures: {m['captures']}")


def cmd_campaign_export(args):
    """Export a campaign to a JSON file."""
    store = CampaignStore(args.campaign_dir)

    if args.input_file:
        # Import mode
        campaign = store.import_campaign(args.input_file)
        print(f"Imported campaign: {campaign.name}")
        print(f"  ID: {campaign.id}")
        print(f"  Status: {campaign.status}")
        print(f"  From: {args.input_file}")
        print(f"  Stored: {store.campaign_dir / (campaign.id + '.json')}")
    elif args.name:
        campaign = find_campaign(store, args.name)
        if args.output_file:
            out_path = args.output_file
        else:
            safe_name = sanitize_id(campaign.name)
            out_path = os.path.join(args.campaign_dir,
                                    f"export_{safe_name}_{campaign.id}.json")
        store.export_campaign(campaign, out_path)
        print(f"Exported campaign: {campaign.name}")
        print(f"  ID: {campaign.id}")
        print(f"  To: {out_path}")
    else:
        logging.error("Specify a campaign name (export) or --input-file (import)")
        sys.exit(1)


def cmd_metrics(args):
    """Analyze capture files for a given template."""
    capture_dir = args.capture_dir or "results/phishing_captures"
    store = CampaignStore(args.campaign_dir)

    # Scan capture files for the template
    capture_dir_p = Path(capture_dir)
    captures = []
    if capture_dir_p.exists():
        for cf in capture_dir_p.glob("*.json"):
            try:
                data = load_json(str(cf))
                if data.get("template") == args.template:
                    captures.append(data)
            except Exception:
                pass

    print(f"Template: {args.template}")
    print(f"Captures found: {len(captures)}")
    print()
    if captures:
        categories = {}
        for c in captures:
            cat = c.get("template_category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
        print("By category:")
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count}")
        print()
        ips = set(c.get("client_ip", "?") for c in captures)
        print(f"Unique IPs: {len(ips)}")
        print(f"Time range: {captures[0].get('timestamp', '?')} — "
              f"{captures[-1].get('timestamp', '?')}")
    else:
        print("No captures found for this template.")


def cmd_init_config(args):
    """Create a default config file."""
    config = {
        "campaign_dir": DEFAULT_CAMPAIGN_DIR,
        "report_dir": DEFAULT_REPORT_DIR,
        "capture_dir": "results/phishing_captures",
        "log_level": "INFO",
        "default_lure_template": "",
        "default_phishing_template": "",
    }
    save_yaml(args.config_path, config)
    print(f"Config written to: {args.config_path}")


def main():
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Configure logging
    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    if args.command == "campaign-create":
        cmd_campaign_create(args)
    elif args.command == "campaign-list":
        cmd_campaign_list(args)
    elif args.command == "campaign-start":
        cmd_campaign_lifecycle(args, STATUS_ACTIVE)
    elif args.command == "campaign-stop":
        cmd_campaign_lifecycle(args, STATUS_DRAFT)
    elif args.command == "campaign-pause":
        cmd_campaign_lifecycle(args, STATUS_PAUSED)
    elif args.command == "campaign-resume":
        cmd_campaign_lifecycle(args, STATUS_ACTIVE)
    elif args.command == "campaign-complete":
        cmd_campaign_lifecycle(args, STATUS_COMPLETED)
    elif args.command == "campaign-report":
        cmd_campaign_report(args)
    elif args.command in ("campaign-export", "campaign-import"):
        cmd_campaign_export(args)
    elif args.command == "metrics":
        cmd_metrics(args)
    elif args.command == "init-config":
        cmd_init_config(args)


if __name__ == "__main__":
    main()
