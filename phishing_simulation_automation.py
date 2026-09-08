#!/usr/bin/env python3
"""
Phishing Simulation Automation Tool
====================================
For authorized security awareness training only.
Simulates phishing campaigns, tracks engagement, and generates compliance reports.

Usage:
    python phishing_simulation_automation.py send --config campaign.yaml
    python phishing_simulation_automation.py track --campaign-id CAMP-001
    python phishing_simulation_automation.py report --campaign-id CAMP-001
    python phishing_simulation_automation.py recommend --campaign-id CAMP-001
    python phishing_simulation_automation.py compliance --campaign-id CAMP-001
"""

import argparse
import csv
import datetime
import json
import os
import smtplib
import sys
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# --- Configuration & Data Storage ---

DEFAULT_DATA_DIR = Path(__file__).parent / "phishing_data"
DEFAULT_DATA_DIR.mkdir(exist_ok=True)

CAMPAIGNS_FILE = DEFAULT_DATA_DIR / "campaigns.json"
TRACKING_FILE = DEFAULT_DATA_DIR / "tracking.json"
REPORTS_FILE = DEFAULT_DATA_DIR / "reports.json"
COMPLIANCE_DIR = DEFAULT_DATA_DIR / "compliance"
COMPLIANCE_DIR.mkdir(exist_ok=True)


# --- Data Persistence Helpers ---

def load_json(path: Path) -> dict | list:
    """Load JSON data from file, return empty dict if not found."""
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json(path: Path, data) -> None:
    """Save data as JSON to file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def generate_campaign_id() -> str:
    """Generate a unique campaign identifier."""
    return f"CAMP-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"


# --- Campaign Management ---

def load_campaign(campaign_id: str) -> dict | None:
    """Load a specific campaign by ID."""
    campaigns = load_json(CAMPAIGNS_FILE)
    return campaigns.get(campaign_id)


def save_campaign(campaign: dict) -> None:
    """Save or update a campaign record."""
    campaigns = load_json(CAMPAIGNS_FILE)
    campaigns[campaign["id"]] = campaign
    save_json(CAMPAIGNS_FILE, campaigns)


# --- 1. Send Simulated Phishing Emails ---

def build_phishing_email(template: str, recipient: str, tracking_id: str,
                         tracking_url: str, sender: str) -> MIMEMultipart:
    """Construct a phishing simulation email with embedded tracking pixel and link."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = get_template_subject(template)
    msg["From"] = sender
    msg["To"] = recipient

    # Plain text version
    text_body = get_template_body(template, tracking_url)

    # HTML version with tracking pixel
    html_body = f"""\
<html>
<body>
{text_body.replace(chr(10), '<br>')}
<img src="{tracking_url}/pixel/{tracking_id}" width="1" height="1" alt="" />
<p style="font-size:10px;color:#999;">[SIMULATION - Security Awareness Training]</p>
</body>
</html>
"""

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))
    return msg


def get_template_subject(template: str) -> str:
    """Return subject line for a given template."""
    subjects = {
        "password_reset": "Action Required: Password Reset Needed",
        "invoice": "Overdue Invoice - Immediate Attention Required",
        "urgent_ceo": "Urgent Request - Time Sensitive",
        "package_delivery": "Package Delivery Failed - Update Address",
        "it_support": "IT Alert: Unusual Sign-in Activity Detected",
    }
    return subjects.get(template, "Important: Action Required")


def get_template_body(template: str, link: str) -> str:
    """Return email body for a given template."""
    bodies = {
        "password_reset": (
            "Your password has expired. Please reset it immediately to avoid account lockout.\n\n"
            f"Reset your password here: {link}\n\n"
            "IT Security Team"
        ),
        "invoice": (
            "You have an overdue invoice that requires immediate payment.\n\n"
            f"View and pay your invoice: {link}\n\n"
            "Accounts Payable"
        ),
        "urgent_ceo": (
            "I need you to process an urgent wire transfer. Please handle this confidentially.\n\n"
            f"Access the secure portal: {link}\n\n"
            "- Executive Office"
        ),
        "package_delivery": (
            "Your package could not be delivered. Please update your address within 24 hours.\n\n"
            f"Update delivery info: {link}\n\n"
            "Shipping Department"
        ),
        "it_support": (
            "We detected unusual sign-in activity on your account. Please verify your identity.\n\n"
            f"Verify your account: {link}\n\n"
            "IT Support"
        ),
    }
    return bodies.get(template, f"Please click the link to proceed: {link}")


def send_campaign(args) -> None:
    """Send simulated phishing emails to target recipients."""
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        sys.exit(1)

    # Parse simple config (supports JSON or key=value lines)
    config = parse_config(config_path)

    template = config.get("template", "password_reset")
    sender = config.get("sender", "security-training@company.com")
    smtp_host = config.get("smtp_host", "localhost")
    smtp_port = int(config.get("smtp_port", 587))
    smtp_user = config.get("smtp_user", "")
    smtp_pass = config.get("smtp_pass", "")
    tracking_base = config.get("tracking_base", "https://training.company.com/click")
    recipients_file = config.get("recipients", "")

    if not recipients_file or not Path(recipients_file).exists():
        print(f"ERROR: Recipients file not found: {recipients_file}")
        sys.exit(1)

    recipients = load_recipients(recipients_file)
    if not recipients:
        print("ERROR: No recipients found in file.")
        sys.exit(1)

    campaign_id = generate_campaign_id()
    campaign = {
        "id": campaign_id,
        "template": template,
        "sender": sender,
        "created_at": datetime.datetime.now().isoformat(),
        "total_recipients": len(recipients),
        "status": "sending",
        "recipients": recipients,
    }

    # Initialize tracking records
    tracking = load_json(TRACKING_FILE)
    tracking[campaign_id] = {}
    for recipient in recipients:
        tid = uuid.uuid4().hex
        tracking[campaign_id][tid] = {
            "email": recipient,
            "tracking_id": tid,
            "sent_at": datetime.datetime.now().isoformat(),
            "clicked": False,
            "clicked_at": None,
            "reported": False,
            "reported_at": None,
        }

    # Send emails
    sent_count = 0
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            if smtp_port == 587:
                server.starttls()
                server.ehlo()
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)

            for recipient in recipients:
                tid = next(
                    k for k, v in tracking[campaign_id].items()
                    if v["email"] == recipient
                )
                tracking_url = f"{tracking_base}/{campaign_id}/{tid}"
                msg = build_phishing_email(template, recipient, tid, tracking_url, sender)
                try:
                    server.sendmail(sender, [recipient], msg.as_string())
                    sent_count += 1
                except smtplib.SMTPException as e:
                    print(f"  WARN: Failed to send to {recipient}: {e}")

    except (smtplib.SMTPConnectError, ConnectionRefusedError, OSError) as e:
        print(f"  WARN: SMTP connection failed ({e}). Emails logged but not delivered.")

    campaign["sent_count"] = sent_count
    campaign["status"] = "sent"
    save_campaign(campaign)
    save_json(TRACKING_FILE, tracking)

    print(f"\nCampaign {campaign_id} created.")
    print(f"  Template:  {template}")
    print(f"  Recipients: {len(recipients)}")
    print(f"  Sent:      {sent_count}")
    print(f"  Tracking:  {tracking_base}/{campaign_id}/<tracking_id>")


# --- 2. Track Click Rates ---

def track_clicks(args) -> None:
    """Display click tracking statistics for a campaign."""
    campaign_id = args.campaign_id
    tracking = load_json(TRACKING_FILE)

    if campaign_id not in tracking:
        print(f"ERROR: Campaign {campaign_id} not found in tracking data.")
        sys.exit(1)

    campaign = load_campaign(campaign_id)
    records = tracking[campaign_id]
    total = len(records)
    clicked = sum(1 for r in records.values() if r["clicked"])
    click_rate = (clicked / total * 100) if total > 0 else 0.0

    print(f"\n=== Click Tracking: {campaign_id} ===")
    print(f"  Total emails sent:  {total}")
    print(f"  Links clicked:      {clicked}")
    print(f"  Click rate:         {click_rate:.1f}%")
    print(f"  Campaign template:  {campaign.get('template', 'unknown') if campaign else 'unknown'}")

    if args.detail:
        print(f"\n  {'Email':<35} {'Clicked':<10} {'Timestamp'}")
        print(f"  {'-'*35} {'-'*10} {'-'*25}")
        for tid, rec in records.items():
            status = "YES" if rec["clicked"] else "no"
            ts = rec["clicked_at"] or "-"
            print(f"  {rec['email']:<35} {status:<10} {ts}")

    # Save click rate to campaign record
    if campaign:
        campaign["click_rate"] = round(click_rate, 2)
        campaign["clicked_count"] = clicked
        save_campaign(campaign)


# --- 3. Measure Reporting Rates ---

def measure_reports(args) -> None:
    """Display reporting rate statistics for a campaign."""
    campaign_id = args.campaign_id
    tracking = load_json(TRACKING_FILE)

    if campaign_id not in tracking:
        print(f"ERROR: Campaign {campaign_id} not found.")
        sys.exit(1)

    campaign = load_campaign(campaign_id)
    records = tracking[campaign_id]
    total = len(records)
    reported = sum(1 for r in records.values() if r["reported"])
    report_rate = (reported / total * 100) if total > 0 else 0.0

    print(f"\n=== Reporting Rate: {campaign_id} ===")
    print(f"  Total recipients:   {total}")
    print(f"  Phishing reported:  {reported}")
    print(f"  Reporting rate:     {report_rate:.1f}%")

    if args.detail:
        print(f"\n  {'Email':<35} {'Reported':<10} {'Timestamp'}")
        print(f"  {'-'*35} {'-'*10} {'-'*25}")
        for tid, rec in records.items():
            status = "YES" if rec["reported"] else "no"
            ts = rec["reported_at"] or "-"
            print(f"  {rec['email']:<35} {status:<10} {ts}")

    # Save report rate to campaign record
    if campaign:
        campaign["report_rate"] = round(report_rate, 2)
        campaign["reported_count"] = reported
        save_campaign(campaign)


# --- 4. Generate Awareness Training Recommendations ---

def generate_recommendations(args) -> None:
    """Generate training recommendations based on campaign results."""
    campaign_id = args.campaign_id
    campaign = load_campaign(campaign_id)
    tracking = load_json(TRACKING_FILE)

    if not campaign or campaign_id not in tracking:
        print(f"ERROR: Campaign {campaign_id} not found.")
        sys.exit(1)

    records = tracking[campaign_id]
    total = len(records)
    clicked = sum(1 for r in records.values() if r["clicked"])
    reported = sum(1 for r in records.values() if r["reported"])
    click_rate = (clicked / total * 100) if total > 0 else 0.0
    report_rate = (reported / total * 100) if total > 0 else 0.0

    recommendations = []

    # Risk-level assessment
    if click_rate > 30:
        recommendations.append({
            "priority": "HIGH",
            "area": "Overall Phishing Susceptibility",
            "detail": f"Click rate of {click_rate:.1f}% exceeds 30% threshold. "
                      "Organization-wide phishing awareness training recommended.",
        })
    elif click_rate > 15:
        recommendations.append({
            "priority": "MEDIUM",
            "area": "Overall Phishing Susceptibility",
            "detail": f"Click rate of {click_rate:.1f}% indicates moderate risk. "
                      "Targeted refresher training advised.",
        })
    else:
        recommendations.append({
            "priority": "LOW",
            "area": "Overall Phishing Susceptibility",
            "detail": f"Click rate of {click_rate:.1f}% is within acceptable range. "
                      "Continue regular training cadence.",
        })

    # Template-specific recommendations
    template = campaign.get("template", "")
    template_recs = {
        "password_reset": {
            "area": "Credential Harvesting Awareness",
            "detail": "Train employees to verify password reset requests through official channels only.",
        },
        "invoice": {
            "area": "Financial Fraud Awareness",
            "detail": "Educate staff on invoice verification procedures and payment authorization workflows.",
        },
        "urgent_ceo": {
            "area": "CEO Fraud / BEC Awareness",
            "detail": "Implement verification protocols for executive requests involving financial transactions.",
        },
        "package_delivery": {
            "area": "Social Engineering Awareness",
            "detail": "Train employees to recognize delivery-themed phishing and verify through official tracking.",
        },
        "it_support": {
            "area": "IT Security Awareness",
            "detail": "Reinforce that IT will never ask for credentials via email links.",
        },
    }
    if template in template_recs:
        recommendations.append({
            "priority": "HIGH" if click_rate > 20 else "MEDIUM",
            **template_recs[template],
        })

    # Reporting rate assessment
    if report_rate < 10:
        recommendations.append({
            "priority": "HIGH",
            "area": "Incident Reporting Culture",
            "detail": f"Reporting rate of {report_rate:.1f}% is low. Promote 'see something, say something' "
                      "culture and simplify the phishing report button process.",
        })
    elif report_rate < 25:
        recommendations.append({
            "priority": "MEDIUM",
            "area": "Incident Reporting Culture",
            "detail": f"Reporting rate of {report_rate:.1f}% has room for improvement. "
                      "Consider gamification or recognition for reporters.",
        })

    # Output
    print(f"\n=== Training Recommendations: {campaign_id} ===")
    print(f"  Template: {template}")
    print(f"  Click Rate: {click_rate:.1f}% | Report Rate: {report_rate:.1f}%\n")

    for i, rec in enumerate(recommendations, 1):
        print(f"  [{rec['priority']}] {i}. {rec['area']}")
        print(f"         {rec['detail']}\n")

    # Save recommendations
    campaign["recommendations"] = recommendations
    save_campaign(campaign)

    # Export to file
    rec_path = DEFAULT_DATA_DIR / f"recommendations_{campaign_id}.json"
    save_json(rec_path, {
        "campaign_id": campaign_id,
        "generated_at": datetime.datetime.now().isoformat(),
        "metrics": {"click_rate": click_rate, "report_rate": report_rate},
        "recommendations": recommendations,
    })
    print(f"  Recommendations saved to: {rec_path}")


# --- 5. Document Results for Compliance ---

def generate_compliance_report(args) -> None:
    """Generate a compliance-ready report documenting the phishing simulation."""
    campaign_id = args.campaign_id
    campaign = load_campaign(campaign_id)
    tracking = load_json(TRACKING_FILE)

    if not campaign or campaign_id not in tracking:
        print(f"ERROR: Campaign {campaign_id} not found.")
        sys.exit(1)

    records = tracking[campaign_id]
    total = len(records)
    clicked = sum(1 for r in records.values() if r["clicked"])
    reported = sum(1 for r in records.values() if r["reported"])
    click_rate = (clicked / total * 100) if total > 0 else 0.0
    report_rate = (reported / total * 100) if total > 0 else 0.0

    report_timestamp = datetime.datetime.now().isoformat()
    report_filename = f"compliance_report_{campaign_id}.md"
    report_path = COMPLIANCE_DIR / report_filename

    report_lines = [
        f"# Phishing Simulation Compliance Report",
        f"",
        f"**Campaign ID:** {campaign_id}",
        f"**Report Generated:** {report_timestamp}",
        f"**Classification:** Internal - Security Awareness Training",
        f"",
        f"## Executive Summary",
        f"",
        f"This report documents an authorized phishing simulation conducted for security ",
        f"awareness training purposes. The simulation was performed with management approval ",
        f"in accordance with organizational security policies.",
        f"",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Campaign ID | {campaign_id} |",
        f"| Template Used | {campaign.get('template', 'N/A')} |",
        f"| Campaign Created | {campaign.get('created_at', 'N/A')} |",
        f"| Total Recipients | {total} |",
        f"| Emails Delivered | {campaign.get('sent_count', 'N/A')} |",
        f"| Links Clicked | {clicked} |",
        f"| Click Rate | {click_rate:.1f}% |",
        f"| Phishing Reported | {reported} |",
        f"| Reporting Rate | {report_rate:.1f}% |",
        f"",
        f"## Methodology",
        f"",
        f"1. **Target Selection:** Recipients were selected from authorized training participant list.",
        f"2. **Email Delivery:** Simulated phishing emails were sent using template '{campaign.get('template', 'N/A')}'.",
        f"3. **Tracking:** Click behavior was tracked via unique per-recipient tracking identifiers.",
        f"4. **Reporting:** Recipients could report suspicious emails via the designated reporting mechanism.",
        f"5. **Data Collection:** All interaction data was logged for analysis.",
        f"",
        f"## Results",
        f"",
        f"### Click Analysis",
        f"",
        f"- **{clicked}** out of **{total}** recipients clicked the simulated phishing link.",
        f"- Click rate: **{click_rate:.1f}%**",
        f"",
        f"### Reporting Analysis",
        f"",
        f"- **{reported}** out of **{total}** recipients reported the phishing email.",
        f"- Reporting rate: **{report_rate:.1f}%**",
        f"",
        f"## Risk Assessment",
        f"",
    ]

    if click_rate > 30:
        report_lines.append(f"**HIGH RISK:** Click rate exceeds 30% threshold. Immediate organization-wide training required.")
    elif click_rate > 15:
        report_lines.append(f"**MEDIUM RISK:** Click rate indicates moderate susceptibility. Targeted training recommended.")
    else:
        report_lines.append(f"**LOW RISK:** Click rate within acceptable parameters. Maintain current training schedule.")

    report_lines.extend([
        f"",
        f"## Recommendations",
        f"",
    ])

    recs = campaign.get("recommendations", [])
    if recs:
        for rec in recs:
            report_lines.append(f"- **{rec['priority']}] {rec['area']}:** {rec['detail']}")
    else:
        report_lines.append(f"- Run `recommend` command to generate training recommendations.")

    report_lines.extend([
        f"",
        f"## Compliance Notes",
        f"",
        f"- This simulation was conducted with explicit management authorization.",
        f"- No actual credentials were collected during this exercise.",
        f"- All data is stored securely and retained per organizational data retention policy.",
        f"- Individual results are confidential and used solely for training purposes.",
        f"- This exercise complies with applicable security awareness training requirements.",
        f"",
        f"## Data Retention",
        f"",
        f"- Campaign data stored at: `{CAMPAIGNS_FILE}`",
        f"- Tracking data stored at: `{TRACKING_FILE}`",
        f"- This report stored at: `{report_path}`",
        f"",
        f"---",
        f"*Report generated by Phishing Simulation Automation Tool*",
    ])

    report_content = "\n".join(report_lines)
    report_path.write_text(report_content, encoding="utf-8")

    # Also export CSV of individual results for audit
    csv_path = COMPLIANCE_DIR / f"campaign_{campaign_id}_results.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Email", "Sent At", "Clicked", "Clicked At", "Reported", "Reported At"])
        for rec in records.values():
            writer.writerow([
                rec["email"],
                rec.get("sent_at", ""),
                rec.get("clicked", False),
                rec.get("clicked_at", ""),
                rec.get("reported", False),
                rec.get("reported_at", ""),
            ])

    print(f"\n=== Compliance Report Generated ===")
    print(f"  Report:  {report_path}")
    print(f"  CSV:     {csv_path}")
    print(f"  Campaign: {campaign_id}")
    print(f"  Click Rate: {click_rate:.1f}%")
    print(f"  Report Rate: {report_rate:.1f}%")


# --- Utility Functions ---

def parse_config(path: Path) -> dict:
    """Parse a config file (JSON or key=value format)."""
    content = path.read_text(encoding="utf-8")
    # Try JSON first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    # Fall back to key=value parsing
    config = {}
    for line in content.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            config[key.strip()] = value.strip()
    return config


def load_recipients(path: str) -> list[str]:
    """Load recipient emails from a file (one per line or CSV)."""
    recipients = []
    p = Path(path)
    if not p.exists():
        return recipients
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Handle CSV: take first column
            email = line.split(",")[0].strip()
            if "@" in email:
                recipients.append(email)
    return recipients


def list_campaigns(args) -> None:
    """List all recorded campaigns."""
    campaigns = load_json(CAMPAIGNS_FILE)
    if not campaigns:
        print("No campaigns found.")
        return

    print(f"\n{'Campaign ID':<30} {'Template':<18} {'Sent':<8} {'Click%':<8} {'Report%':<8} {'Status'}")
    print("-" * 100)
    for cid, camp in campaigns.items():
        print(f"  {cid:<28} {camp.get('template','?'):<18} "
              f"{camp.get('sent_count',0):<8} "
              f"{camp.get('click_rate',0):<8} "
              f"{camp.get('report_rate',0):<8} "
              f"{camp.get('status','?')}")


# --- CLI Entry Point ---

def main():
    parser = argparse.ArgumentParser(
        description="Phishing Simulation Automation Tool - For authorized security awareness training only.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  Send campaign:    %(prog)s send --config campaign.yaml
  Track clicks:     %(prog)s track --campaign-id CAMP-20240101-ABC123
  Measure reports:  %(prog)s report --campaign-id CAMP-20240101-ABC123
  Recommendations:  %(prog)s recommend --campaign-id CAMP-20240101-ABC123
  Compliance doc:   %(prog)s compliance --campaign-id CAMP-20240101-ABC123
  List campaigns:   %(prog)s list
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # send
    send_parser = subparsers.add_parser("send", help="Send simulated phishing emails")
    send_parser.add_argument("--config", required=True, help="Path to campaign config file")

    # track
    track_parser = subparsers.add_parser("track", help="Track click rates")
    track_parser.add_argument("--campaign-id", required=True, help="Campaign ID to track")
    track_parser.add_argument("--detail", action="store_true", help="Show per-recipient detail")

    # report
    report_parser = subparsers.add_parser("report", help="Measure reporting rates")
    report_parser.add_argument("--campaign-id", required=True, help="Campaign ID to measure")
    report_parser.add_argument("--detail", action="store_true", help="Show per-recipient detail")

    # recommend
    rec_parser = subparsers.add_parser("recommend", help="Generate training recommendations")
    rec_parser.add_argument("--campaign-id", required=True, help="Campaign ID to analyze")

    # compliance
    comp_parser = subparsers.add_parser("compliance", help="Generate compliance report")
    comp_parser.add_argument("--campaign-id", required=True, help="Campaign ID to document")

    # list
    subparsers.add_parser("list", help="List all campaigns")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "send": send_campaign,
        "track": track_clicks,
        "report": measure_reports,
        "recommend": generate_recommendations,
        "compliance": generate_compliance_report,
        "list": list_campaigns,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
