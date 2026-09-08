"""
SE Campaign Framework
Social Engineering simulation toolkit for authorized security awareness testing.
All modules require explicit authorization scope before execution.
"""

import json
import hashlib
import time
import re
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional
from pathlib import Path


# ---------------------------------------------------------------------------
# 1. Vishing Scripts — AI-generated voice call scripts
# ---------------------------------------------------------------------------

VISHING_TEMPLATES = {
    "it_support": {
        "greeting": "Hi {target_name}, this is {caller_name} from {org_name} IT support.",
        "hook": "We've detected unusual login activity on your account from {location}.",
        "urgency": "To prevent account lockout, I need to verify your identity within the next 10 minutes.",
        "ask": "Can you confirm your employee ID and the password you currently use?",
        "fallback": "If you can't provide that now, I can send a verification link to {email}.",
        "closing": "Thanks for your cooperation. You'll see a ticket reference {ticket_id} in your email."
    },
    "vendor_invoice": {
        "greeting": "Hello {target_name}, this is {caller_name} from {vendor_name} accounts receivable.",
        "hook": "Invoice #{invoice_id} for {amount} is past due and scheduled for collections.",
        "urgency": "We need payment details updated today to avoid service interruption on your account.",
        "ask": "Can you confirm the credit card on file, or provide an updated one?",
        "fallback": "I can also take a wire transfer if you prefer — I'll need your banking details.",
        "closing": "I'll email a receipt to {email} once the payment processes."
    },
    "executive_impersonation": {
        "greeting": "{target_name}, this is {caller_name}. I'm in a meeting and need your help.",
        "hook": "We're closing an acquisition and I need a wire transfer processed immediately.",
        "urgency": "This is time-sensitive and confidential — don't discuss with the team yet.",
        "ask": "Can you initiate a wire for {amount} to the account I'm texting you?",
        "fallback": "If you can't do wires, can you buy {gift_card_amount} in gift cards and text me the codes?",
        "closing": "Great work. I'll brief the board next week. Delete this thread after."
    }
}

def generate_vishing_script(
    template: str,
    target_name: str,
    caller_name: str = "Alex Morgan",
    org_name: str = "Acme Corp",
    **kwargs
) -> str:
    """Generate a vishing call script from a template with variable substitution."""
    if template not in VISHING_TEMPLATES:
        raise ValueError(f"Unknown template: {template}. Available: {list(VISHING_TEMPLATES.keys())}")

    tmpl = VISHING_TEMPLATES[template]
    variables = {
        "target_name": target_name,
        "caller_name": caller_name,
        "org_name": org_name,
        "ticket_id": f"TKT-{hashlib.md5(target_name.encode()).hexdigest()[:8].upper()}",
        "location": kwargs.get("location", "Moscow, Russia"),
        "email": kwargs.get("email", "user@company.com"),
        "vendor_name": kwargs.get("vendor_name", "TechSupply Inc"),
        "invoice_id": kwargs.get("invoice_id", f"INV-{int(time.time()) % 10000}"),
        "amount": kwargs.get("amount", "$4,250.00"),
        "gift_card_amount": kwargs.get("gift_card_amount", "$2,000"),
    }
    variables.update(kwargs)

    script_lines = []
    for key in ["greeting", "hook", "urgency", "ask", "fallback", "closing"]:
        line = tmpl.get(key, "")
        try:
            script_lines.append(line.format(**variables))
        except KeyError as e:
            script_lines.append(f"[MISSING VAR {e}] {line}")

    return "\n\n".join(script_lines)


# ---------------------------------------------------------------------------
# 2. Pretexting Scenarios — customizable SE scripts
# ---------------------------------------------------------------------------

@dataclass
class PretextScenario:
    """A reusable pretexting scenario with role, backstory, and dialogue beats."""
    name: str
    role: str
    backstory: str
    entry_vector: str
    objectives: list[str]
    dialogue_beats: list[str]
    risk_level: str = "medium"  # low, medium, high
    detection_flags: list[str] = field(default_factory=list)

    def to_script(self) -> str:
        lines = [
            f"=== PRETEXT: {self.name} ===",
            f"Role: {self.role}",
            f"Risk Level: {self.risk_level.upper()}",
            f"Entry Vector: {self.entry_vector}",
            "",
            "--- Backstory ---",
            self.backstory,
            "",
            "--- Objectives ---",
        ]
        for i, obj in enumerate(self.objectives, 1):
            lines.append(f"  {i}. {obj}")
        lines.extend(["", "--- Dialogue Beats ---"])
        for i, beat in enumerate(self.dialogue_beats, 1):
            lines.append(f"  [{i}] {beat}")
        if self.detection_flags:
            lines.extend(["", "--- Detection Flags ---"])
            for flag in self.detection_flags:
                lines.append(f"  ⚠ {flag}")
        return "\n".join(lines)


PRETEXT_LIBRARY = {
    "new_employee": PretextScenario(
        name="New Employee Onboarding",
        role="New hire in Finance department",
        backstory="Claiming to be a remote employee on their first day, unfamiliar with internal processes.",
        entry_vector="Tailgating through badge-access doors; calling help desk for credentials.",
        objectives=["Gain physical access to office areas", "Obtain VPN credentials", "Map internal systems"],
        dialogue_beats=[
            "Hi, I'm new and my badge isn't working yet — can you let me in?",
            "I haven't received my laptop setup instructions. Who do I contact?",
            "My manager said to ask you about the shared drive login.",
        ],
        risk_level="medium",
        detection_flags=["No HR record found", "Badge not provisioned", "Manager unverified"]
    ),
    "auditor": PretextScenario(
        name="External Auditor",
        role="Third-party compliance auditor",
        backstory="Claiming to conduct a surprise SOX/ISO audit with a forged engagement letter.",
        entry_vector="Email from lookalike domain; phone calls to executive assistants.",
        objectives=["Access financial records", "Obtain org charts", "Identify control weaknesses"],
        dialogue_beats=[
            "We're conducting the annual compliance review — I need read access to the GL system.",
            "My engagement letter was sent to your CFO last week. Let me forward it again.",
            "I'll need a quiet room with network access for the next two days.",
        ],
        risk_level="high",
        detection_flags=["No audit scheduled", "Domain registered recently", "Letter lacks partner signature"]
    ),
    "facilities": PretextScenario(
        name="HVAC Vendor Technician",
        role="Air conditioning repair technician",
        backstory="Claiming a refrigerant leak requires immediate access to the server room for sensor checks.",
        entry_vector="Phone call to reception; arrives in uniform with fake work order.",
        objectives=["Physical access to server room", "Visual survey of rack layout", "Plant rogue device"],
        dialogue_beats=[
            "We got an automated alert about a refrigerant leak in your building.",
            "I need to check the sensors — they're usually in the server room.",
            "This'll take 15 minutes. You don't need to escort me; I know the way.",
        ],
        risk_level="high",
        detection_flags=["No vendor ticket", "No uniform logo", "Refuses escort"]
    )
}


# ---------------------------------------------------------------------------
# 3. OSINT Profiling — gather info from public sources
# ---------------------------------------------------------------------------

@dataclass
class OSINTProfile:
    """Aggregated open-source intelligence on a target individual or organization."""
    target: str
    emails: list[str] = field(default_factory=list)
    social_handles: dict[str, str] = field(default_factory=dict)
    job_title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    interests: list[str] = field(default_factory=list)
    data_breaches: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    collected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


def osint_from_email(email: str) -> OSINTProfile:
    """Generate an OSINT profile skeleton from an email address (public data only)."""
    local_part, domain = email.rsplit("@", 1)
    profile = OSINTProfile(target=email, emails=[email])

    # Derive likely name patterns
    name_variants = []
    if "." in local_part:
        first, last = local_part.split(".", 1)
        name_variants.append(f"{first.capitalize()} {last.capitalize()}")
    if "_" in local_part:
        first, last = local_part.split("_", 1)
        name_variants.append(f"{first.capitalize()} {last.capitalize()}")
    profile.metadata["name_variants"] = name_variants

    # Common social handle patterns
    profile.social_handles = {
        "linkedin": f"linkedin.com/in/{local_part}",
        "twitter": f"twitter.com/{local_part}",
        "github": f"github.com.{local_part}",
    }

    profile.metadata["domain"] = domain
    profile.metadata["domain_hash"] = hashlib.sha256(domain.encode()).hexdigest()[:16]

    return profile


def search_haveibeenpwned(email: str) -> list[str]:
    """
    Check HIBP for breach data. Returns list of breach names.
    NOTE: Requires API key for production use. This is a stub showing the interface.
    """
    # In production: call https://haveibeenpwned.com/api/v3/breachedaccount/{email}
    # with hibp-api-key header. Returns 404 if no breaches, 201 if found.
    return ["[HIBP check requires API key — stub response]"]


# ---------------------------------------------------------------------------
# 4. Campaign Tracking — click rates, capture rates
# ---------------------------------------------------------------------------

@dataclass
class CampaignMetrics:
    """Tracks engagement metrics for an SE campaign."""
    campaign_id: str
    campaign_name: str
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    total_targets: int = 0
    emails_sent: int = 0
    emails_delivered: int = 0
    emails_opened: int = 0
    links_clicked: int = 0
    credentials_captured: int = 0
    calls_made: int = 0
    calls_completed: int = 0
    vishing_success: int = 0
    reported_suspicious: int = 0

    @property
    def delivery_rate(self) -> float:
        return (self.emails_delivered / self.emails_sent * 100) if self.emails_sent else 0.0

    @property
    def open_rate(self) -> float:
        return (self.emails_opened / self.emails_delivered * 100) if self.emails_delivered else 0.0

    @property
    def click_rate(self) -> float:
        return (self.links_clicked / self.emails_delivered * 100) if self.emails_delivered else 0.0

    @property
    def capture_rate(self) -> float:
        return (self.credentials_captured / self.links_clicked * 100) if self.links_clicked else 0.0

    @property
    def vishing_success_rate(self) -> float:
        return (self.vishing_success / self.calls_completed * 100) if self.calls_completed else 0.0

    @property
    def reporting_rate(self) -> float:
        return (self.reported_suspicious / self.total_targets * 100) if self.total_targets else 0.0

    def summary(self) -> str:
        return (
            f"Campaign: {self.campaign_name} [{self.campaign_id}]\n"
            f"  Targets: {self.total_targets}\n"
            f"  Delivery Rate: {self.delivery_rate:.1f}%\n"
            f"  Open Rate: {self.open_rate:.1f}%\n"
            f"  Click Rate: {self.click_rate:.1f}%\n"
            f"  Capture Rate: {self.capture_rate:.1f}%\n"
            f"  Vishing Success: {self.vishing_success_rate:.1f}%\n"
            f"  Reporting Rate: {self.reporting_rate:.1f}%"
        )


class CampaignTracker:
    """Manages multiple SE campaigns with persistent JSON storage."""

    def __init__(self, storage_path: str = "campaigns.json"):
        self.storage_path = Path(storage_path)
        self.campaigns: dict[str, CampaignMetrics] = {}
        self._load()

    def _load(self):
        if self.storage_path.exists():
            data = json.loads(self.storage_path.read_text())
            for cid, cdata in data.items():
                self.campaigns[cid] = CampaignMetrics(**cdata)

    def _save(self):
        data = {cid: asdict(cm) for cid, cm in self.campaigns.items()}
        self.storage_path.write_text(json.dumps(data, indent=2, default=str))

    def create(self, name: str, total_targets: int) -> CampaignMetrics:
        cid = f"CMP-{hashlib.md5(f'{name}{time.time()}'.encode()).hexdigest()[:8].upper()}"
        cm = CampaignMetrics(campaign_id=cid, campaign_name=name, total_targets=total_targets)
        self.campaigns[cid] = cm
        self._save()
        return cm

    def get(self, campaign_id: str) -> Optional[CampaignMetrics]:
        return self.campaigns.get(campaign_id)

    def record_event(self, campaign_id: str, event: str, count: int = 1):
        cm = self.campaigns.get(campaign_id)
        if not cm:
            raise ValueError(f"Unknown campaign: {campaign_id}")
        valid_events = [
            "emails_sent", "emails_delivered", "emails_opened",
            "links_clicked", "credentials_captured", "calls_made",
            "calls_completed", "vishing_success", "reported_suspicious"
        ]
        if event not in valid_events:
            raise ValueError(f"Unknown event: {event}. Valid: {valid_events}")
        setattr(cm, event, getattr(cm, event) + count)
        self._save()

    def list_campaigns(self) -> list[CampaignMetrics]:
        return list(self.campaigns.values())


# ---------------------------------------------------------------------------
# 5. Phishing Email Templates
# ---------------------------------------------------------------------------

PHISHING_TEMPLATES = {
    "password_reset": {
        "subject": "Action Required: Password reset for your {service} account",
        "sender": "security@{domain}",
        "body": """Dear {name},

We detected a sign-in attempt to your {service} account from an unrecognized device.

Location: {location}
Time: {timestamp}
Device: {device}

If this wasn't you, your account may be compromised. Reset your password immediately:

[RESET PASSWORD →]{reset_link}

If you do not reset your password within 24 hours, your account will be suspended.

— {service} Security Team
"""
    },
    "shared_document": {
        "subject": "{sender_name} shared \"{doc_name}\" with you",
        "sender": "noreply@{domain}",
"body": """Hi {name},

{sender_name} ({sender_email}) has shared a document with you on {service}:

  📄 {doc_name}

Click below to view the document:

[VIEW DOCUMENT →]{doc_link}

This link expires in 48 hours.

— {service} Notifications
"""
    },
    "shipping_delivery": {
        "subject": "Your package delivery failed — action needed",
        "sender": "no-reply@{domain}",
        "body": """Hello {name},

We attempted to deliver your package but no one was available.

Tracking: {tracking_number}
Delivery Date: {delivery_date}

Reschedule your delivery by confirming your address:

[RESCHEDULE DELIVERY →]{reschedule_link}

A second failed delivery will return the package to sender.

— {carrier} Shipping
"""
    },
    "ceo_fraud": {
        "subject": "Urgent wire transfer needed",
        "sender": "{ceo_email}",
        "body": """{name},

I'm in back-to-back meetings and need your help with something urgent.

We need to process a wire transfer for an acquisition that hasn't been announced yet.
Please keep this confidential until the public announcement.

Amount: {amount}
Beneficiary: {beneficiary}
Reference: {reference}

Can you process this today? Just reply with confirmation.

Thanks,
{ceo_name}
"""
    }
}

def generate_phishing_email(
    template: str,
    target_name: str,
    target_email: str,
    **kwargs
) -> dict:
    """Generate a phishing email from a template with variable substitution."""
    if template not in PHISHING_TEMPLATES:
        raise ValueError(f"Unknown template: {template}. Available: {list(PHISHING_TEMPLATES.keys())}")

    tmpl = PHISHING_TEMPLATES[template]
    variables = {
        "name": target_name,
        "email": target_email,
        "service": kwargs.get("service", "Microsoft 365"),
        "domain": kwargs.get("domain", "security-alerts.com"),
        "location": kwargs.get("location", "Lagos, Nigeria"),
        "timestamp": kwargs.get("timestamp", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")),
        "device": kwargs.get("device", "Windows PC — Chrome"),
        "reset_link": kwargs.get("reset_link", "https://bit.ly/reset-now"),
        "sender_name": kwargs.get("sender_name", "Sarah Chen"),
        "sender_email": kwargs.get("sender_email", "s.chen@company.com"),
        "doc_name": kwargs.get("doc_name", "Q3_Financial_Projections.xlsx"),
        "doc_link": kwargs.get("doc_link", "https://bit.ly/doc-view"),
        "tracking_number": kwargs.get("tracking_number", f"1Z{hashlib.md5(target_email.encode()).hexdigest()[:16].upper()}"),
        "delivery_date": kwargs.get("delivery_date", (datetime.utcnow() + timedelta(days=1)).strftime("%B %d, %Y")),
        "reschedule_link": kwargs.get("reschedule_link", "https://bit.ly/reschedule"),
        "carrier": kwargs.get("carrier", "UPS"),
        "ceo_name": kwargs.get("ceo_name", "James Wilson"),
        "ceo_email": kwargs.get("ceo_email", "jwilson@company.com"),
        "amount": kwargs.get("amount", "$47,500.00"),
        "beneficiary": kwargs.get("beneficiary", "Meridian Holdings LLC"),
        "reference": kwargs.get("reference", "ACQ-2024-CONFIDENTIAL"),
    }
    variables.update(kwargs)

    try:
        subject = tmpl["subject"].format(**variables)
        sender = tmpl["sender"].format(**variables)
        body = tmpl["body"].format(**variables)
    except KeyError as e:
        raise ValueError(f"Missing template variable: {e}")

    return {
        "subject": subject,
        "sender": sender,
        "body": body,
        "recipient": target_email,
        "template_used": template,
        "generated_at": datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# Demo / CLI entry point
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("SE Campaign Framework — Demo Output")
    print("=" * 60)

    # 1. Vishing demo
    print("\n--- Vishing Script (IT Support) ---")
    print(generate_vishing_script("it_support", target_name="John Smith"))

    # 2. Pretexting demo
    print("\n--- Pretexting Scenario ---")
    pretext = PRETEXT_LIBRARY["auditor"]
    print(pretext.to_script())

    # 3. OSINT demo
    print("\n--- OSINT Profile ---")
    profile = osint_from_email("john.smith@acme.com")
    print(profile.to_json())

    # 4. Campaign tracking demo
    print("\n--- Campaign Tracking ---")
    tracker = CampaignTracker(storage_path="demo_campaigns.json")
    campaign = tracker.create("Q3 Security Awareness Test", total_targets=100)
    tracker.record_event(campaign.campaign_id, "emails_sent", 100)
    tracker.record_event(campaign.campaign_id, "emails_delivered", 95)
    tracker.record_event(campaign.campaign_id, "emails_opened", 42)
    tracker.record_event(campaign.campaign_id, "links_clicked", 18)
    tracker.record_event(campaign.campaign_id, "credentials_captured", 7)
    tracker.record_event(campaign.campaign_id, "reported_suspicious", 12)
    print(tracker.get(campaign.campaign_id).summary())

    # 5. Phishing email demo
    print("\n--- Phishing Email (Password Reset) ---")
    email = generate_phishing_email("password_reset", "John Smith", "john.smith@acme.com")
    print(f"From: {email['sender']}")
    print(f"To: {email['recipient']}")
    print(f"Subject: {email['subject']}")
    print(f"\n{email['body']}")

    # Cleanup demo file
    demo_path = Path("demo_campaigns.json")
    if demo_path.exists():
        demo_path.unlink()

    print("\n" + "=" * 60)
    print("Demo complete. Framework ready for authorized testing.")
    print("=" * 60)


if __name__ == "__main__":
    main()
