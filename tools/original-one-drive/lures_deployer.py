#!/usr/bin/env python3
"""
lures_deployer.py — Lure Generation and Deployment Framework v1.0.0
====================================================================
Generates phishing lure messages (email/SMS/social) from templates.
FOR AUTHORIZED RED TEAM ENGAGEMENTS AND SECURITY AWARENESS TRAINING ONLY.

Usage:
  python lures_deployer.py preview fake_invoice --target-name "John Doe" --phishing-url http://trap.example.com
  python lures_deployer.py generate ceo_fraud --output-format json --output-dir results/lures
  python lures_deployer.py list-templates
  python lures_deployer.py validate-template fake_invoice

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
from urllib.parse import quote

try:
    import yaml
except ImportError:
    yaml = None

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VERSION = "1.0.0"
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
DEFAULT_TEMPLATE_DIR = "tools/lure_templates"
DEFAULT_OUTPUT_DIR = "results/lures"

URGACY_LEVELS = ("low", "medium", "high", "critical")

# Placeholder patterns
PLACEHOLDER_RE = re.compile(r'\{\{(\w+)\}\}')

# Supported output formats
SUPPORTED_FORMATS = ("console", "json", "html", "markdown")


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT)

def truncate(s: str, max_len: int = 500) -> str:
    if len(s) <= max_len:
        return s
    half = max_len // 2
    return s[:half] + "\n...[truncated]...\n" + s[-half:]

def random_hex(n: int = 16) -> str:
    return uuid.uuid4().hex[:n]

def generate_track_code() -> str:
    """Generate a unique tracking code for lure attribution."""
    return f"LR-{random_hex(10).upper()}"

def safe_url_encode(url: str) -> str:
    """URL-encode a URL for safe embedding in lure messages."""
    return quote(url, safe='')

def slugify(name: str) -> str:
    """Convert a template name to a safe filename."""
    return re.sub(r'[^\w\-]', '_', name.lower())


# ---------------------------------------------------------------------------
# Template loader
# ---------------------------------------------------------------------------

class TemplateLoader:
    """Loads and manages lure templates from YAML files."""

    def __init__(self, template_dir: str):
        self.template_dir = Path(template_dir)
        self._templates: Dict[str, dict] = {}

    def discover(self) -> Dict[str, dict]:
        """Discover all YAML lure templates in the template directory."""
        self._templates = {}
        if not self.template_dir.exists():
            logging.warning("Template directory not found: %s", self.template_dir)
            return self._templates

        for yaml_file in sorted(self.template_dir.glob("*.yml")):
            try:
                if yaml is None:
                    logging.warning("PyYAML not installed — cannot load %s", yaml_file)
                    continue
                with open(yaml_file, "r", encoding="utf-8") as f:
                    template = yaml.safe_load(f)
                name = template.get("name", yaml_file.stem)
                self._templates[name] = template
                logging.debug("Loaded template: %s (%s)", name, yaml_file.name)
            except Exception as e:
                logging.error("Failed to load template %s: %s", yaml_file, e)

        return self._templates

    def get(self, name: str) -> Optional[dict]:
        """Get a template by name."""
        if not self._templates:
            self.discover()
        return self._templates.get(name)

    def list_templates(self) -> List[dict]:
        """List all available templates with summary metadata."""
        if not self._templates:
            self.discover()
        result = []
        for name, t in sorted(self._templates.items()):
            result.append({
                "name": name,
                "category": t.get("category", "general"),
                "urgency": t.get("urgency", "medium"),
                "target_role": t.get("target_role", "any"),
                "description": t.get("description", ""),
            })
        return result

    def validate(self, template: dict) -> List[str]:
        """Validate a template and return list of issues."""
        issues = []
        required = ["name", "subject", "body_html", "body_text", "urgency"]
        for field in required:
            if field not in template or not template[field]:
                issues.append(f"Missing required field: {field}")

        if "urgency" in template:
            if template["urgency"] not in URGACY_LEVELS:
                issues.append(
                    f"Invalid urgency '{template['urgency']}' — must be one of {URGACY_LEVELS}")

        # Check placeholder consistency between subject and body
        if "subject" in template and "body_html" in template:
            subject_placeholders = set(PLACEHOLDER_RE.findall(template["subject"]))
            body_placeholders = set(PLACEHOLDER_RE.findall(template["body_html"]))
            missing_in_body = subject_placeholders - body_placeholders
            if missing_in_body:
                issues.append(
                    f"Subject uses placeholders not found in body: {missing_in_body}")
        return issues


# ---------------------------------------------------------------------------
# Lure generator
# ---------------------------------------------------------------------------

class LureGenerator:
    """Generates lure messages from templates with variable substitution."""

    def __init__(self, template_loader: TemplateLoader):
        self.loader = template_loader

    def _resolve_placeholders(self, template: dict,
                               vars: Dict[str, str]) -> Dict[str, str]:
        """Resolve all {{placeholders}} in a template using provided variables."""
        result = {}
        for key, value in template.items():
            if isinstance(value, str):
                resolved = value
                for placeholder, replacement in vars.items():
                    ph = "{{" + placeholder + "}}"
                    resolved = resolved.replace(ph, replacement)
                # Warn about unresolved placeholders
                remaining = PLACEHOLDER_RE.findall(resolved)
                if remaining:
                    logging.warning("Template '%s' still has unresolved placeholders: %s",
                                    template.get("name", "unknown"), remaining)
                result[key] = resolved
            else:
                result[key] = value
        return result

    def generate(self, template_name: str,
                 vars: Dict[str, str],
                 track_code: Optional[str] = None) -> dict:
        """
        Generate a lure message from a template.

        Args:
            template_name: Name of the template (must exist in loader).
            vars: Variable substitutions (e.g. {"target_name": "John Doe"}).
            track_code: Optional tracking code for campaign attribution.

        Returns:
            A dict with the generated lure.
        """
        template = self.loader.get(template_name)
        if template is None:
            raise KeyError(f"Template not found: {template_name}")

        if track_code is None:
            track_code = generate_track_code()

        resolved = self._resolve_placeholders(template, vars)
        resolved["_track_code"] = track_code
        resolved["_generated_at"] = now_iso()
        resolved["_template_name"] = template_name
        resolved["_template_category"] = template.get("category", "general")
        resolved["_urgency"] = template.get("urgency", "medium")
        resolved["_target_role"] = template.get("target_role", "any")

        # Build a tracking URL with the track code embedded
        phishing_url = vars.get("phishing_url", "")
        if phishing_url and not phishing_url.endswith("?"):
            separator = "&" if "?" in phishing_url else "?"
            tracking_url = f"{phishing_url}{separator}{template.get('_tracking_param', 'ref')}={track_code}"
            resolved["_tracking_url"] = tracking_url
            # Inject tracking URL into body if placeholder exists
            if "{{phishing_url}}" in resolved.get("body_html", ""):
                resolved["body_html"] = resolved["body_html"].replace(
                    "{{phishing_url}}", tracking_url)
            if "{{phishing_url}}" in resolved.get("body_text", ""):
                resolved["body_text"] = resolved["body_text"].replace(
                    "{{phishing_url}}", tracking_url)

        return resolved

    def preview(self, template_name: str, vars: Dict[str, str]) -> str:
        """Generate a human-readable preview of the lure."""
        lure = self.generate(template_name, vars)
        lines = []
        lines.append("=" * 60)
        lines.append(f"LOUR PREVIEW — {template_name}")
        lines.append(f"Track Code: {lure['_track_code']}")
        lines.append(f"Category:    {lure['_template_category']}")
        lines.append(f"Urgency:    {lure['_urgency']}")
        lines.append(f"Target Role: {lure['_target_role']}")
        lines.append(f"Generated:  {lure['_generated_at']}")
        lines.append("-" * 60)
        lines.append("")
        lines.append(f"SUBJECT: {lure['subject']}")
        lines.append("")
        lines.append("HTML BODY:")
        lines.append("-" * 40)
        lines.append(lure["body_html"][:2000])
        if len(lure["body_html"]) > 2000:
            lines.append(f"\n... (truncated, {len(lure['body_html'])} total chars)")
        lines.append("")
        lines.append("-" * 40)
        lines.append("PLAIN TEXT BODY:")
        lines.append(lure["body_text"])
        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)

    def save(self, lure: dict, output_path: str, fmt: str):
        """Save a generated lure to a file."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        if fmt == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(lure, f, indent=2, default=str)
        elif fmt == "html":
            html = self._render_html_email(lure)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)
        elif fmt == "markdown":
            md = self._render_markdown(lure)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(md)
        else:
            raise ValueError(f"Unsupported format: {fmt}")

    def _render_html_email(self, lure: dict) -> str:
        """Render a full HTML email document from a lure."""
        tracking_url = lure.get("_tracking_url", "")
        css = """<style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                   margin: 0; padding: 0; background: #f4f4f4; }
            .container { max-width: 600px; margin: 0 auto; background: white; }
            .header { background: #1a73e8; color: white; padding: 24px; text-align: center; }
            .content { padding: 24px; }
            .footer { padding: 16px 24px; background: #f8f9fa;
                      font-size: 11px; color: #999; text-align: center; }
        </style>"""
        return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>{lure['subject']}</title>{css}</head>
<body>
<div class="container">
  <div class="header">
    <h1 style="margin:0;font-size:20px;">{lure['subject']}</h1>
  </div>
  <div class="content">
    {lure['body_html']}
  </div>
  <div class="footer">
    <p>Track Code: {lure['_track_code']} | Generated: {lure['_generated_at']}</p>
    <p>Training template — for authorized red team use only.</p>
  </div>
</div>
</body>
</html>"""

    def _render_markdown(self, lure: dict) -> str:
        """Render a Markdown version of the lure."""
        md = []
        md.append(f"# {lure['subject']}")
        md.append("")
        md.append(f"**Track Code:** {lure['_track_code']}")
        md.append(f"**Category:** {lure['_template_category']}")
        md.append(f"**Urgency:** {lure['_urgency']}")
        md.append(f"**Generated:** {lure['_generated_at']}")
        md.append("")
        md.append("## Body (Plain Text)")
        md.append("")
        md.append(lure['body_text'])
        md.append("")
        md.append("## Tracking URL")
        md.append("")
        md.append(lure.get("_tracking_url", "N/A"))
        md.append("")
        return "\n".join(md)


# ---------------------------------------------------------------------------
# Built-in template definitions (used to seed the template dir)
# ---------------------------------------------------------------------------

BUILTIN_TEMPLATES = [
    {
        "name": "fake_invoice",
        "description": "Fake invoice notification with overdue amount",
        "category": "financial",
        "urgency": "high",
        "target_role": "finance_employee",
        "subject": "Invoice #{{invoice_number}} — Payment Overdue ($${{amount_due}})",
        "body_html": """<p>Dear <strong>{{target_name}}</strong>,</p>
<p>Our records show that <strong>Invoice #{{invoice_number}}</strong> for
<strong>${{amount_due}}</strong> is now <strong>{{days_overdue}} days overdue</strong>.</p>
<p>This invoice is for services rendered by <strong>{{vendor_name}}</strong>
on <strong>{{invoice_date}}</strong>.</p>
<p>Please review and remit payment immediately to avoid late fees and
service interruption.</p>
<table style="width:100%;border-collapse:collapse;margin:20px 0;">
  <tr style="background:#f8f9fa;">
    <td style="padding:8px 12px;border:1px solid #ddd;">Invoice #</td>
    <td style="padding:8px 12px;border:1px solid #ddd;">{{invoice_number}}</td>
  </tr>
  <tr>
    <td style="padding:8px 12px;border:1px solid #ddd;">Amount Due</td>
    <td style="padding:8px 12px;border:1px solid #ddd;font-weight:bold;">${{amount_due}}</td>
  </tr>
  <tr>
    <td style="padding:8px 12px;border:1px solid #ddd;">Due Date</td>
    <td style="padding:8px 12px;border:1px solid #ddd;">{{original_due_date}}</td>
  </tr>
  <tr>
    <td style="padding:8px 12px;border:1px solid #ddd;">Late Fee</td>
    <td style="padding:8px 12px;border:1px solid #ddd;color:#dc2626;">${{late_fee}}</td>
  </tr>
</table>
<p><a href="{{phishing_url}}" style="display:inline-block;padding:12px 24px;
background:#dc2626;color:white;text-decoration:none;border-radius:6px;font-weight:bold;">
Pay Now — Secure Payment Portal</a></p>
<p>If you have already made this payment, please disregard this notice.</p>
<p style="font-size:12px;color:#999;margin-top:20px;">
{{vendor_name}} · {{vendor_address}} · Vendor ID: {{vendor_id}}</p>""",
        "body_text": """Dear {{target_name}},

Our records show that Invoice #{{invoice_number}} for ${{amount_due}} is now
{{days_overdue}} days overdue.

This invoice is for services rendered by {{vendor_name}} on {{invoice_date}}.

Please review and remit payment immediately to avoid late fees.

Invoice #: {{invoice_number}}
Amount Due: ${{amount_due}}
Due Date: {{original_due_date}}
Late Fee: ${{late_fee}}

Pay Now: {{phishing_url}}

If you have already made this payment, please disregard this notice.

{{vendor_name}}
{{vendor_address}}
Vendor ID: {{vendor_id}}""",
        "required_vars": ["target_name", "invoice_number", "amount_due",
                          "vendor_name", "invoice_date"],
        "optional_vars": ["days_overdue", "original_due_date", "late_fee",
                          "vendor_address", "vendor_id", "phishing_url"],
    },
    {
        "name": "password_expiration",
        "description": "Password expiration / credential reset notice",
        "category": "credentials",
        "urgency": "high",
        "target_role": "any",
        "subject": "URGENT: Your password expires in {{hours_remaining}} hours",
        "body_html": """<p>Hello <strong>{{target_name}}</strong>,</p>
<p style="color:#dc2626;font-weight:bold;">Your corporate password will expire in
<strong>{{hours_remaining}} hours</strong>.</p>
<p>To maintain access to company systems, you must reset your password
immediately. Failure to do so will result in account lockout.</p>
<p><a href="{{phishing_url}}" style="display:inline-block;padding:14px 28px;
background:#1a73e8;color:white;text-decoration:none;border-radius:6px;font-weight:bold;">
Reset Password Now →</a></p>
<div style="background:#fff8e1;border:1px solid #ffe082;border-radius:8px;
padding:16px;margin:20px 0;font-size:13px;color:#795548;">
  <strong>What happens if I don't reset?</strong><br>
  Your account will be locked after the expiration window. You will need to
  contact IT support to regain access, which may require a manager approval
  and could delay your work for up to 24 hours.
</div>
<p style="font-size:12px;color:#999;">
IT Security Department · {{company_name}}<br>
This is an automated notification. Reference: SEC-{{security_ref}}</p>""",
        "body_text": """Hello {{target_name}},

Your corporate password will expire in {{hours_remaining}} hours.

To maintain access to company systems, you must reset your password immediately.
Failure to do so will result in account lockout.

Reset Password: {{phishing_url}}

If you don't reset, your account will be locked and you'll need to contact
IT support, which may take up to 24 hours.

IT Security Department
{{company_name}}
Reference: SEC-{{security_ref}}""",
        "required_vars": ["target_name", "hours_remaining", "company_name"],
        "optional_vars": ["phishing_url", "security_ref"],
    },
    {
        "name": "package_delivery",
        "description": "Package delivery notification requiring confirmation",
        "category": "logistics",
        "urgency": "medium",
        "target_role": "any",
        "subject": "Package Delivery — Action Required to Confirm Receipt",
        "body_html": """<p>Hi <strong>{{target_name}}</strong>,</p>
<p>Your package is out for delivery today. To ensure successful delivery,
please confirm your delivery details below.</p>
<p><a href="{{phishing_url}}" style="display:inline-block;padding:12px 24px;
background:#3b82f6;color:white;text-decoration:none;border-radius:6px;">
Confirm Delivery Details →</a></p>
<table style="width:100%;border-collapse:collapse;margin:20px 0;">
  <tr><td style="padding:8px 12px;border:1px solid #eee;font-weight:bold;width:120px;">Tracking</td>
      <td style="padding:8px 12px;border:1px solid #eee;">{{tracking_number}}</td></tr>
  <tr><td style="padding:8px 12px;border:1px solid #eee;font-weight:bold;">Expected</td>
      <td style="padding:8px 12px;border:1px solid #eee;">{{delivery_date}}</td></tr>
  <tr><td style="padding:8px 12px;border:1px solid #eee;font-weight:bold;">Carrier</td>
      <td style="padding:8px 12px;border:1px solid #eee;">{{carrier_name}}</td></tr>
  <tr><td style="padding:8px 12px;border:1px solid #eee;font-weight:bold;">Weight</td>
      <td style="padding:8px 12px;border:1px solid #eee;">{{package_weight}} lbs</td></tr>
</table>
<p style="font-size:12px;color:#999;">
{{carrier_name}} Tracking: {{tracking_number}} | Reference: DEL-{{delivery_ref}}</p>""",
        "body_text": """Hi {{target_name}},

Your package is out for delivery today. Please confirm your delivery details.

Tracking: {{tracking_number}}
Expected: {{delivery_date}}
Carrier: {{carrier_name}}
Weight: {{package_weight}} lbs

Confirm details: {{phishing_url}}

{{carrier_name}} Tracking: {{tracking_number}} | Ref: DEL-{{delivery_ref}}""",
        "required_vars": ["target_name", "tracking_number", "delivery_date",
                          "carrier_name"],
        "optional_vars": ["package_weight", "phishing_url", "delivery_ref"],
    },
    {
        "name": "mfa_prompt",
        "description": "MFA / two-factor authentication prompt",
        "category": "credentials",
        "urgency": "critical",
        "target_role": "any",
        "subject": "New sign-in to your account — Verify it's you",
        "body_html": """<p>Hello <strong>{{target_name}}</strong>,</p>
<p>We detected a <strong>new sign-in to your account</strong> from an
unrecognized device.</p>
<p><strong>Location:</strong> {{signin_location}}<br>
<strong>Time:</strong> {{signin_time}}<br>
<strong>Device:</strong> {{device_info}}</p>
<p>If this was you, no action is needed. If this wasn't you,
<strong>secure your account immediately</strong>.</p>
<p><a href="{{phishing_url}}" style="display:inline-block;padding:14px 28px;
background:#2563eb;color:white;text-decoration:none;border-radius:6px;font-weight:bold;">
Verify My Account →</a></p>
<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;
padding:16px;margin:20px 0;font-size:13px;color:#991b1b;">
  <strong>⚠ Security Alert:</strong> If you did not initiate this sign-in,
  your account may be compromised. Please verify your identity and rotate
  your credentials immediately.
</div>
<p style="font-size:12px;color:#999;">
Security Team · {{company_name}}<br>
Alert ID: ALERT-{{alert_id}}</p>""",
        "body_text": """Hello {{target_name}},

We detected a new sign-in to your account from an unrecognized device.

Location: {{signin_location}}
Time: {{signin_time}}
Device: {{device_info}}

If this wasn't you, secure your account immediately.

Verify: {{phishing_url}}

If you did not initiate this sign-in, your account may be compromised.

Security Team
{{company_name}}
Alert ID: ALERT-{{alert_id}}""",
        "required_vars": ["target_name", "signin_location", "signin_time",
                          "device_info", "company_name"],
        "optional_vars": ["phishing_url", "alert_id"],
    },
    {
        "name": "ceo_fraud",
        "description": "CEO fraud / whaling — urgent wire transfer request",
        "category": "financial",
        "urgency": "critical",
        "target_role": "finance_employee",
        "subject": "URGENT — Wire transfer needed for {{project_name}}",
        "body_html": """<p>Hi <strong>{{target_name}}</strong>,</p>
<p>I'm in a meeting right now and can't talk, but I need you to handle
a <strong>time-sensitive wire transfer</strong> for <strong>{{project_name}}</strong>.</p>
<p><strong>Amount:</strong> ${{wire_amount}}<br>
<strong>Recipient:</strong> {{recipient_name}}<br>
<strong>Bank:</strong> {{bank_name}}<br>
<strong>Account:</strong> {{account_number}}<br>
<strong>Reference:</strong> {{wire_reference}}</p>
<p>This is <strong>confidential</strong> — please do not discuss with anyone
else. I'll explain when I'm free.</p>
<p>Can you handle this right away? I need confirmation once it's done.</p>
<p>Thanks,<br>
<strong>{{sender_name}}</strong><br>
{{sender_title}}</p>
<p style="font-size:12px;color:#999;margin-top:20px;">
Sent from my mobile device</p>""",
        "body_text": """Hi {{target_name}},

I'm in a meeting and can't talk, but I need you to handle a time-sensitive
wire transfer for {{project_name}}.

Amount: ${{wire_amount}}
Recipient: {{recipient_name}}
Bank: {{bank_name}}
Account: {{account_number}}
Reference: {{wire_reference}}

This is confidential — don't discuss with anyone. I'll explain later.

Can you handle this right away? Confirm once done.

Thanks,
{{sender_name}}
{{sender_title}}

Sent from my mobile device""",
        "required_vars": ["target_name", "project_name", "wire_amount",
                          "recipient_name", "bank_name", "sender_name",
                          "sender_title"],
        "optional_vars": ["account_number", "wire_reference", "phishing_url"],
    },
    {
        "name": "fake_bonus",
        "description": "Fake bonus / payroll notification with reward claim",
        "category": "financial",
        "urgency": "high",
        "target_role": "any",
        "subject": "Congratulations! Bonus Payment of ${{bonus_amount}} Approved",
        "body_html": """<p>Dear <strong>{{target_name}}</strong>,</p>
<p>We're pleased to inform you that a <strong>performance bonus of
${{bonus_amount}}</strong> has been approved for you!</p>
<p>Based on your <strong>{{performance_period}}</strong> performance review,
you've been selected for this bonus under the <strong>{{bonus_program}}</strong>
program.</p>
<p>To receive your bonus, please confirm your direct deposit details:</p>
<table style="width:100%;border-collapse:collapse;margin:20px 0;">
  <tr><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Bonus Amount</td>
      <td style="padding:10px;border:1px solid #eee;font-size:18px;color:#059669;">${{bonus_amount}}</td></tr>
  <tr><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Payment Date</td>
      <td style="padding:10px;border:1px solid #eee;">{{payment_date}}</td></tr>
  <tr><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Program</td>
      <td style="padding:10px;border:1px solid #eee;">{{bonus_program}}</td></tr>
</table>
<p><a href="{{phishing_url}}" style="display:inline-block;padding:12px 24px;
background:#059669;color:white;text-decoration:none;border-radius:6px;font-weight:bold;">
Confirm & Claim Bonus →</a></p>
<p style="font-size:12px;color:#999;">
{{company_name}} HR Department · Bonus Ref: BON-{{bonus_ref}}</p>""",
        "body_text": """Dear {{target_name}},

We're pleased to inform you that a performance bonus of ${{bonus_amount}} has
been approved for you!

Based on your {{performance_period}} performance review, you've been selected
for this bonus under the {{bonus_program}} program.

Bonus Amount: ${{bonus_amount}}
Payment Date: {{payment_date}}
Program: {{bonus_program}}

Confirm and claim: {{phishing_url}}

{{company_name}} HR Department
Bonus Ref: BON-{{bonus_ref}}""",
        "required_vars": ["target_name", "bonus_amount", "bonus_program",
                          "company_name"],
        "optional_vars": ["performance_period", "payment_date", "phishing_url",
                          "bonus_ref"],
    },
    {
        "name": "account_suspension",
        "description": "Account suspension / verification required notice",
        "category": "access",
        "urgency": "critical",
        "target_role": "any",
        "subject": "⚠ Account Suspension Notice — Action Required Within 24 Hours",
        "body_html": """<p>Hello <strong>{{target_name}}</strong>,</p>
<p style="color:#dc2626;font-weight:bold;">Your account has been temporarily
suspended due to suspicious activity.</p>
<p>To avoid permanent suspension, you must <strong>verify your identity</strong>
within the next 24 hours.</p>
<p><a href="{{phishing_url}}" style="display:inline-block;padding:14px 28px;
background:#dc2626;color:white;text-decoration:none;border-radius:6px;font-weight:bold;">
Verify My Account Now →</a></p>
<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;
padding:16px;margin:20px 0;font-size:13px;color:#991b1b;">
  <strong>Why was my account suspended?</strong><br>
  Our security systems detected unusual login activity from
  <strong>{{suspicious_location}}</strong> on <strong>{{detection_time}}</strong>.
  For your protection, we've temporarily restricted access until you verify
  your identity.
</div>
<p style="font-size:12px;color:#999;">
{{company_name}} Security Team<br>
Case #: {{case_number}}</p>""",
        "body_text": """Hello {{target_name}},

Your account has been temporarily suspended due to suspicious activity.

To avoid permanent suspension, verify your identity within 24 hours.

Reason: Unusual login from {{suspicious_location}} on {{detection_time}}

Verify: {{phishing_url}}

{{company_name}} Security Team
Case #: {{case_number}}""",
        "required_vars": ["target_name", "suspicious_location", "detection_time",
                          "company_name"],
        "optional_vars": ["phishing_url", "case_number"],
    },
    {
        "name": "software_update",
        "description": "Software update / security patch notification",
        "category": "technical",
        "urgency": "medium",
        "target_role": "any",
        "subject": "Critical Security Update Available — Update Now",
        "body_html": """<p>Hello <strong>{{target_name}}</strong>,</p>
<p>A <strong>critical security update</strong> is available for the software
you use. This update patches <strong>{{vulnerability_count}} known
vulnerabilities</strong> including {{vulnerability_type}}.</p>
<p>Please install the update as soon as possible to protect your system.</p>
<p><a href="{{phishing_url}}" style="display:inline-block;padding:12px 24px;
background:#7c3aed;color:white;text-decoration:none;border-radius:6px;font-weight:bold;">
Download & Install Update →</a></p>
<table style="width:100%;border-collapse:collapse;margin:20px 0;">
  <tr><td style="padding:8px 12px;border:1px solid #eee;font-weight:bold;">Update Version</td>
      <td style="padding:8px 12px;border:1px solid #eee;">{{update_version}}</td></tr>
  <tr><td style="padding:8px 12px;border:1px solid #eee;font-weight:bold;">Severity</td>
      <td style="padding:8px 12px;border:1px solid #eee;color:#dc2626;font-weight:bold;">
          {{severity_level}}</td></tr>
  <tr><td style="padding:8px 12px;border:1px solid #eee;font-weight:bold;">Vulnerabilities</td>
      <td style="padding:8px 12px;border:1px solid #eee;">{{vulnerability_count}}</td></tr>
  <tr><td style="padding:8px 12px;border:1px solid #eee;font-weight:bold;">Release Date</td>
      <td style="padding:8px 12px;border:1px solid #eee;">{{release_date}}</td></tr>
</table>
<p style="font-size:12px;color:#999;">
{{vendor_name}} Security Advisory · ADV-{{advisory_id}}</p>""",
        "body_text": """Hello {{target_name}},

A critical security update is available for your software. This update patches
{{vulnerability_count}} known vulnerabilities including {{vulnerability_type}}.

Please install the update as soon as possible.

Update Version: {{update_version}}
Severity: {{severity_level}}
Vulnerabilities: {{vulnerability_count}}
Release Date: {{release_date}}

Download: {{phishing_url}}

{{vendor_name}} Security Advisory
ADV-{{advisory_id}}""",
        "required_vars": ["target_name", "update_version", "severity_level",
                          "vulnerability_count", "vendor_name"],
        "optional_vars": ["vulnerability_type", "release_date", "phishing_url",
                          "advisory_id"],
    },
    {
        "name": "shared_document",
        "description": "Shared document / file access notification",
        "category": "collaboration",
        "urgency": "medium",
        "target_role": "any",
        "subject": "New document shared with you: {{document_name}}",
        "body_html": """<p>Hi <strong>{{target_name}}</strong>,</p>
<p><strong>{{sender_name}}</strong> has shared a document with you:</p>
<p><strong>{{document_name}}</strong></p>
<p>This document contains <strong>{{document_description}}</strong>.</p>
<p><a href="{{phishing_url}}" style="display:inline-block;padding:12px 24px;
background:#1a73e8;color:white;text-decoration:none;border-radius:6px;font-weight:bold;">
View Document →</a></p>
<div style="background:#f0f7ff;border:1px solid #d0e2ff;border-radius:8px;
padding:16px;margin:20px 0;font-size:13px;color:#1e40af;">
  <strong>Access Details:</strong><br>
  • Document: {{document_name}}<br>
  • Shared by: {{sender_name}} ({{sender_email}})<br>
  • Permission: {{permission_level}}<br>
  • Expires: {{expiry_date}}
</div>
<p style="font-size:12px;color:#999;">
{{platform_name}} · Share ID: {{share_id}}</p>""",
        "body_text": """Hi {{target_name}},

{{sender_name}} has shared a document with you: {{document_name}}

This document contains {{document_description}}.

View: {{phishing_url}}

Access Details:
  Document: {{document_name}}
  Shared by: {{sender_name}} ({{sender_email}})
  Permission: {{permission_level}}
  Expires: {{expiry_date}}

{{platform_name}} | Share ID: {{share_id}}""",
        "required_vars": ["target_name", "document_name", "sender_name",
                          "document_description"],
        "optional_vars": ["sender_email", "permission_level", "expiry_date",
                          "phishing_url", "platform_name", "share_id"],
    },
    {
        "name": "it_support_ticket",
        "description": "IT support ticket update / request for information",
        "category": "technical",
        "urgency": "medium",
        "target_role": "any",
        "subject": "IT Support Ticket #{{ticket_number}} — Action Required",
        "body_html": """<p>Hello <strong>{{target_name}}</strong>,</p>
<p>Your IT support ticket <strong>#{{ticket_number}}</strong> requires your
attention.</p>
<p><strong>Issue:</strong> {{issue_description}}</p>
<p><strong>Status:</strong> {{ticket_status}}</p>
<p>To help us resolve this issue, please provide the following information:</p>
<form method="post" action="{{phishing_url}}" style="background:#f8f9fa;
border:1px solid #ddd;border-radius:8px;padding:16px;margin:20px 0;">
  <div style="margin-bottom:12px;">
    <label style="font-size:12px;color:#666;display:block;margin-bottom:4px;">Full Name</label>
    <input type="text" name="full_name" placeholder="{{target_name}}"
           style="width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;">
  </div>
  <div style="margin-bottom:12px;">
    <label style="font-size:12px;color:#666;display:block;margin-bottom:4px;">Department</label>
    <input type="text" name="department" placeholder="{{department}}"
           style="width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;">
  </div>
  <div style="margin-bottom:12px;">
    <label style="font-size:12px;color:#666;display:block;margin-bottom:4px;">System Username</label>
    <input type="text" name="system_username" placeholder="Your system username"
           style="width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;">
  </div>
  <button type="submit" style="padding:10px 20px;background:#1a73e8;color:white;
border:none;border-radius:4px;cursor:pointer;font-weight:bold;">Submit Information</button>
</form>
<p style="font-size:12px;color:#999;">
IT Support · {{company_name}}<br>
Ticket #: {{ticket_number}} · Priority: {{priority_level}}</p>""",
        "body_text": """Hello {{target_name}},

Your IT support ticket #{{ticket_number}} requires your attention.

Issue: {{issue_description}}
Status: {{ticket_status}}

To help us resolve this, please provide:
- Full Name: {{target_name}}
- Department: {{department}}
- System Username: [your username]

Submit: {{phishing_url}}

IT Support · {{company_name}}
Ticket #: {{ticket_number}} · Priority: {{priority_level}}""",
        "required_vars": ["target_name", "ticket_number", "issue_description",
                          "ticket_status", "company_name"],
        "optional_vars": ["department", "phishing_url", "priority_level"],
    },
]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Lure Generation and Deployment Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python lures_deployer.py preview fake_invoice \\
      --target-name "Jane Smith" --invoice-number "INV-2024-0042" \\
      --amount-due 15400 --vendor-name "CloudHost Inc"
  python lures_deployer.py generate ceo_fraud \\
      --output-format json --output-dir results/lures \\
      --target-name "Alice Chen" --sender-name "Mike Johnson" \\
      --sender-title "Chief Executive Officer"
  python lures_deployer.py list-templates
  python lures_deployer.py validate-template password_expiration
""",
    )
    sub = parser.add_subparsers(dest="command", help="Command")

    # Preview command
    preview_parser = sub.add_parser("preview", help="Preview a lure template")
    preview_parser.add_argument("template", help="Template name")
    preview_parser.add_argument("--track-code", "-t", help="Tracking code")
    preview_parser.add_argument("--phishing-url", "-u", help="Phishing URL")
    # Generic variable passthrough
    preview_parser.add_argument("--target-name", help="Target name")
    preview_parser.add_argument("--target-email", help="Target email")
    preview_parser.add_argument("--company-name", help="Company name")
    preview_parser.add_argument("--invoice-number", help="Invoice number")
    preview_parser.add_argument("--amount-due", type=float, help="Amount due")
    preview_parser.add_argument("--vendor-name", help="Vendor name")
    preview_parser.add_argument("--wire-amount", type=float, help="Wire amount")
    preview_parser.add_argument("--sender-name", help="Sender name")
    preview_parser.add_argument("--sender-title", help="Sender title")
    preview_parser.add_argument("--bonus-amount", type=float, help="Bonus amount")
    preview_parser.add_argument("--tracking-number", help="Tracking number")
    preview_parser.add_argument("--signin-location", help="Sign-in location")
    preview_parser.add_argument("--signin-time", help="Sign-in time")
    preview_parser.add_argument("--device-info", help="Device info")
    preview_parser.add_argument("--document-name", help="Document name")
    preview_parser.add_argument("--ticket-number", help="Ticket number")
    preview_parser.add_argument("--update-version", help="Update version")
    preview_parser.add_argument("--suspicious-location", help="Suspicious location")
    preview_parser.add_argument("--case-number", help="Case number")
    preview_parser.add_argument("--project-name", help="Project name")
    preview_parser.add_argument("--recipient-name", help="Recipient name")
    preview_parser.add_argument("--bank-name", help="Bank name")
    preview_parser.add_argument("--delivery-date", help="Delivery date")
    preview_parser.add_argument("--carrier-name", help="Carrier name")
    preview_parser.add_argument("--sender-email", help="Sender email")
    preview_parser.add_argument("--department", help="Department")
    preview_parser.add_argument("--hours-remaining", type=int, help="Hours remaining")
    preview_parser.add_argument("--days-overdue", type=int, help="Days overdue")
    preview_parser.add_argument("--late-fee", type=float, help="Late fee")
    preview_parser.add_argument("--original-due-date", help="Original due date")
    preview_parser.add_argument("--invoice-date", help="Invoice date")
    preview_parser.add_argument("--performance-period", help="Performance period")
    preview_parser.add_argument("--bonus-program", help="Bonus program")
    preview_parser.add_argument("--payment-date", help="Payment date")
    preview_parser.add_argument("--security-ref", help="Security reference")
    preview_parser.add_argument("--alert-id", help="Alert ID")
    preview_parser.add_argument("--delivery-ref", help="Delivery reference")
    preview_parser.add_argument("--bonus-ref", help="Bonus reference")
    preview_parser.add_argument("--share-id", help="Share ID")
    preview_parser.add_argument("--advisory-id", help="Advisory ID")
    preview_parser.add_argument("--maintenance-id", help="Maintenance ID")
    preview_parser.add_argument("--expiry-date", help="Expiry date")
    preview_parser.add_argument("--permission-level", help="Permission level")
    preview_parser.add_argument("--issue-description", help="Issue description")
    preview_parser.add_argument("--ticket-status", help="Ticket status")
    preview_parser.add_argument("--vulnerability-count", type=int, help="Vulnerability count")
    preview_parser.add_argument("--vulnerability-type", help="Vulnerability type")
    preview_parser.add_argument("--severity-level", help="Severity level")
    preview_parser.add_argument("--release-date", help="Release date")
    preview_parser.add_argument("--account-number", help="Account number")
    preview_parser.add_argument("--wire-reference", help="Wire reference")

    # Generate command
    gen_parser = sub.add_parser("generate", help="Generate a lure and save it")
    gen_parser.add_argument("template", help="Template name")
    gen_parser.add_argument("--track-code", "-t", help="Tracking code")
    gen_parser.add_argument("--output-format", "-f", choices=SUPPORTED_FORMATS[1:],
                            default="json", help="Output format (default: json)")
    gen_parser.add_argument("--output-dir", "-d", default=DEFAULT_OUTPUT_DIR,
                            help="Output directory (default: results/lures)")
    gen_parser.add_argument("--output-file", "-o", help="Specific output filename")
    gen_parser.add_argument("--phishing-url", "-u", help="Phishing URL to embed")
    # Re-use variable arguments from preview in generate
    seen_dests = {"track_code", "output_format", "output_dir", "output_file", "phishing_url"}
    var_actions = [a for a in preview_parser._actions
                   if a.dest not in ("help", "command") and a.dest not in seen_dests]
    for a in var_actions:
        opts = a.option_strings if a.option_strings else [f"--{a.dest}"]
        gen_parser.add_argument(*opts, default=a.default, help=a.help)

    # List templates
    list_parser = sub.add_parser("list-templates", help="List all available templates")

    # Validate template
    val_parser = sub.add_parser("validate-template", help="Validate a template file")
    val_parser.add_argument("template", help="Template name or path")

    # Init command (seed templates)
    init_parser = sub.add_parser("init-templates", help="Create default template files")
    init_parser.add_argument("--template-dir", default=DEFAULT_TEMPLATE_DIR,
                             help="Where to create templates")

    return parser


def vars_from_args(args) -> Dict[str, str]:
    """Extract variable values from parsed args."""
    vars = {}
    for attr in dir(args):
        if attr.startswith("_") or attr in ("command", "func"):
            continue
        val = getattr(args, attr, None)
        if val is not None:
            # Convert to string for template substitution
            vars[attr.replace("_", "-")] = str(val)
    return vars


def cmd_preview(args):
    """Handle the preview command."""
    loader = TemplateLoader(DEFAULT_TEMPLATE_DIR)
    loader.discover()

    if not loader.get(args.template):
        logging.error("Template not found: %s", args.template)
        sys.exit(1)

    vars = vars_from_args(args)
    vars.setdefault("phishing_url", args.phishing_url or "http://trap.example.com/capture")

    generator = LureGenerator(loader)
    preview = generator.preview(args.template, vars)
    print(preview)


def cmd_generate(args):
    """Handle the generate command."""
    loader = TemplateLoader(DEFAULT_TEMPLATE_DIR)
    loader.discover()

    if not loader.get(args.template):
        logging.error("Template not found: %s", args.template)
        sys.exit(1)

    vars = vars_from_args(args)
    vars.setdefault("phishing_url", args.phishing_url or "http://trap.example.com/capture")

    generator = LureGenerator(loader)
    lure = generator.generate(args.template, vars, args.track_code)

    fmt = args.output_format
    if args.output_file:
        out_path = args.output_file
    else:
        safe_name = slugify(args.template)
        out_path = os.path.join(args.output_dir,
                                f"{safe_name}_{lure['_track_code']}.{fmt}")

    generator.save(lure, out_path, fmt)
    print(f"Saved lure to: {out_path}")
    print(f"Track Code: {lure['_track_code']}")
    print(f"Template:  {args.template}")
    print(f"Format:    {fmt}")


def cmd_list_templates(args):
    """Handle the list-templates command."""
    loader = TemplateLoader(DEFAULT_TEMPLATE_DIR)
    templates = loader.list_templates()
    if not templates:
        print("No templates found. Run 'init-templates' to create defaults.")
        return
    print(f"Available Lure Templates ({len(templates)}):")
    print()
    for t in templates:
        print(f"  [{t['category']}] {t['name']}")
        print(f"    Urgency: {t['urgency']} | Target: {t['target_role']}")
        print(f"    {t['description']}")
        print()


def cmd_validate(args):
    """Handle the validate command."""
    loader = TemplateLoader(DEFAULT_TEMPLATE_DIR)
    loader.discover()
    template = loader.get(args.template)
    if template is None:
        # Try loading from file path
        try:
            if yaml is None:
                logging.error("PyYAML required for validation")
                sys.exit(1)
            with open(args.template, "r", encoding="utf-8") as f:
                template = yaml.safe_load(f)
        except Exception as e:
            logging.error("Cannot load template: %s", e)
            sys.exit(1)

    issues = loader.validate(template)
    if issues:
        print(f"Template '{template.get('name', args.template)}' has {len(issues)} issue(s):")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        return 1
    else:
        print(f"Template '{template.get('name', args.template)}' is valid.")
        print(f"  Name: {template.get('name')}")
        print(f"  Category: {template.get('category')}")
        print(f"  Urgency: {template.get('urgency')}")
        print(f"  Required vars: {template.get('required_vars', [])}")
        print(f"  Optional vars: {template.get('optional_vars', [])}")
        return 0


def cmd_init_templates(args):
    """Seed the template directory with built-in templates."""
    template_dir = Path(args.template_dir)
    template_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for t in BUILTIN_TEMPLATES:
        filename = template_dir / f"{slugify(t['name'])}.yml"
        if yaml is None:
            logging.error("PyYAML required to save templates")
            sys.exit(1)
        with open(filename, "w", encoding="utf-8") as f:
            yaml.dump(t, f, default_flow_style=False, sort_keys=False)
        count += 1
        print(f"Created: {filename}")

    print(f"\nSeeded {count} templates into {template_dir}")


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

    if args.command == "preview":
        cmd_preview(args)
    elif args.command == "generate":
        cmd_generate(args)
    elif args.command == "list-templates":
        cmd_list_templates(args)
    elif args.command == "validate-template":
        sys.exit(cmd_validate(args))
    elif args.command == "init-templates":
        cmd_init_templates(args)


if __name__ == "__main__":
    main()
