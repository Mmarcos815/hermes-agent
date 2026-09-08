"""CTI (Cyber Threat Intelligence) Feed Ingestion Module.

Aggregates threat intelligence from:
  1. CVE monitoring via NVD API
  2. Threat actor (APT group) tracking
  3. Dark web monitoring (simulated)
  4. IOC feeds via STIX/TAXII
  5. Alerting on new in-scope threats

Usage:
    python intelligence/cti_feed.py --once
    python -m intelligence.cti_feed.py
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from typing import Any

NVD_API_BASE = "https://services.nvd.nist.gov/rest/json/cves/2.0"
STIX_TAXII_BASE = os.environ.get("TAXII_BASE_URL", "https://cti-taxii.com/taxii2")
TAXII_COLLECTION = os.environ.get("TAXII_COLLECTION", "91e7b038-2b5d-4f8e-9f7a-1c3d5e7f9a1b")
POLL_INTERVAL = int(os.environ.get("CTI_POLL_INTERVAL", "3600"))
STATE_FILE = os.path.join(os.path.dirname(__file__), ".cti_state.json")
IN_SCOPE_KEYWORDS = (
    "ransomware", "supply chain", "zero-day", "0day", "apt",
    "backdoor", "remote code execution", "rce", "privilege escalation",
    "credential harvesting",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("cti_feed")


# ── Data models ──────────────────────────────────────────────────────────────

@dataclass
class CVEItem:
    cve_id: str
    description: str
    cvss_score: float | None
    published: str
    references: list[str] = field(default_factory=list)

    @property
    def severity(self) -> str:
        if self.cvss_score is None:
            return "UNKNOWN"
        if self.cvss_score >= 9.0:
            return "CRITICAL"
        if self.cvss_score >= 7.0:
            return "HIGH"
        if self.cvss_score >= 4.0:
            return "MEDIUM"
        return "LOW"


@dataclass
class ThreatActor:
    name: str
    aliases: list[str]
    last_seen: str
    targets: list[str]
    ttps: list[str]


@dataclass
class DarkWebMention:
    source: str
    timestamp: str
    snippet: str
    indicators: list[str]


@dataclass
class IOC:
    type: str
    value: str
    confidence: int
    source: str
    first_seen: str


@dataclass
class ThreatAlert:
    timestamp: str
    severity: str
    title: str
    source: str
    details: dict[str, Any] = field(default_factory=dict)


# ── State persistence ────────────────────────────────────────────────────────

def load_state() -> dict[str, Any]:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            log.warning("Corrupt state file; starting fresh.")
    return {"seen_cves": [], "last_poll": None, "seen_iocs": []}


def save_state(state: dict[str, Any]) -> None:
    state["last_poll"] = datetime.now(timezone.utc).isoformat()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


# ── 1. CVE Monitoring (NVD API) ──────────────────────────────────────────────

def fetch_recent_cves(hours: int = 24) -> list[CVEItem]:
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime(
        "%Y-%m-%dT%H:%M:%S.000"
    )
    try:
        import urllib.request, urllib.parse
        url = f"{NVD_API_BASE}?{urllib.parse.urlencode({'pubStartDate': since, 'resultsPerPage': 20})}"
        req = urllib.request.Request(url, headers={"User-Agent": "CTI-Feed/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        log.error("NVD API failed: %s", exc)
        return []

    items: list[CVEItem] = []
    for vuln in data.get("vulnerabilities", []):
        cve = vuln.get("cve", {})
        desc = next((d["value"] for d in cve.get("descriptions", []) if d.get("lang") == "en"), "")
        metrics = cve.get("metrics", {})
        score = None
        for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            if key in metrics and metrics[key]:
                score = metrics[key][0].get("cvssData", {}).get("baseScore")
                if score is not None:
                    break
        items.append(CVEItem(
            cve_id=cve.get("id", "UNKNOWN"),
            description=desc,
            cvss_score=score,
            published=cve.get("published", ""),
            references=[r.get("url", "") for r in cve.get("references", [])[:5]],
        ))
    log.info("Fetched %d CVEs from NVD (last %dh)", len(items), hours)
    return items


# ── 2. Threat Actor Tracking ─────────────────────────────────────────────────

APT_GROUPS: list[dict[str, Any]] = [
    {"name": "APT28", "aliases": ["Fancy Bear", "Sednit"], "targets": ["government", "defense"], "ttps": ["T1566", "T1059"]},
    {"name": "APT29", "aliases": ["Cozy Bear", "Nobelium"], "targets": ["diplomatic", "think tanks"], "ttps": ["T1078.004", "T1566.002"]},
    {"name": "Lazarus Group", "aliases": ["Hidden Cobra"], "targets": ["financial", "cryptocurrency"], "ttps": ["T1486", "T1566"]},
]

def track_threat_actors() -> list[ThreatActor]:
    now = datetime.now(timezone.utc).isoformat()
    actors = [ThreatActor(g["name"], g["aliases"], now, g["targets"], g["ttps"]) for g in APT_GROUPS]
    log.info("Tracking %d APT groups", len(actors))
    return actors


# ── 3. Dark Web Monitoring (Simulated) ──────────────────────────────────────

def monitor_dark_web() -> list[DarkWebMention]:
    now = datetime.now(timezone.utc).isoformat()
    mentions = [
        DarkWebMention("forum_alpha", now, "New exploit kit targeting enterprise VPNs advertised", ["198.51.100.23"]),
        DarkWebMention("paste_bin", now, "Credential dump containing enterprise email addresses", ["d41d8cd98f00b204e9800998ecf8427e"]),
    ]
    log.info("Dark web: %d mentions (simulated)", len(mentions))
    return mentions


# ── 4. IOC Feeds (STIX/TAXII) ────────────────────────────────────────────────

def _extract_stix_value(pattern: str) -> str:
    import re
    m = re.search(r"=\s*'([^']+)'", pattern)
    return m.group(1) if m else pattern


def fetch_stix_iocs() -> list[IOC]:
    iocs: list[IOC] = []
    try:
        import urllib.request
        url = f"{STIX_TAXII_BASE}/collections/{TAXII_COLLECTION}/objects/"
        req = urllib.request.Request(url, headers={"Accept": "application/stix+json;version=2.1", "User-Agent": "CTI-Feed/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            bundle = json.loads(resp.read().decode("utf-8"))

        for obj in bundle.get("objects", []):
            if obj.get("type") == "indicator":
                pat = obj.get("pattern", "")
                if "MD5" in pat:
                    iocs.append(IOC("hash", _extract_stix_value(pat), 80, "taxii", obj.get("created", "")))
                elif "domain-name" in pat:
                    iocs.append(IOC("domain", _extract_stix_value(pat), 80, "taxii", obj.get("created", "")))
                elif "ipv4-addr" in pat:
                    iocs.append(IOC("ip", _extract_stix_value(pat), 80, "taxii", obj.get("created", "")))
        log.info("Fetched %d IOCs from TAXII", len(iocs))
    except Exception as exc:
        log.warning("TAXII unreachable (%s); using simulated IOCs", exc)
        now = datetime.now(timezone.utc).isoformat()
        iocs = [
            IOC("ip", "203.0.113.50", 75, "simulated", now),
            IOC("domain", "malware-c2.example", 85, "simulated", now),
            IOC("hash", "e99a18c428cb38d5f260853678922e03", 90, "simulated", now),
        ]
    return iocs


# ── 5. Alerting Engine ────────────────────────────────────────────────────────

def is_in_scope(text: str) -> bool:
    lowered = text.lower()
    return any(kw in lowered for kw in IN_SCOPE_KEYWORDS)


def generate_alerts(
    cves: list[CVEItem],
    actors: list[ThreatActor],
    dark_web: list[DarkWebMention],
    iocs: list[IOC],
    state: dict[str, Any],
) -> list[ThreatAlert]:
    alerts: list[ThreatAlert] = []
    seen = set(state.get("seen_cves", []))
    seen_iocs = set(state.get("seen_iocs", []))
    now = datetime.now(timezone.utc).isoformat()

    for cve in cves:
        if cve.cve_id in seen:
            continue
        if cve.cvss_score is not None and cve.cvss_score >= 7.0:
            alerts.append(ThreatAlert(now, cve.severity, f"{cve.cve_id} (CVSS {cve.cvss_score})", "nvd",
                                       {"description": cve.description, "refs": cve.references}))
        elif is_in_scope(cve.description):
            alerts.append(ThreatAlert(now, "MEDIUM", f"{cve.cve_id} — in-scope match", "nvd",
                                       {"description": cve.description}))
        seen.add(cve.cve_id)

    for mention in dark_web:
        if is_in_scope(mention.snippet):
            alerts.append(ThreatAlert(now, "HIGH", f"Dark web: {mention.source}", "dark_web",
                                       {"snippet": mention.snippet, "iocs": mention.indicators}))

    for ioc in iocs:
        key = f"{ioc.type}:{ioc.value}"
        if key not in seen_iocs and ioc.confidence >= 80:
            alerts.append(ThreatAlert(now, "HIGH" if ioc.confidence >= 90 else "MEDIUM",
                                       f"New {ioc.type.upper()} IOC: {ioc.value}", ioc.source,
                                       {"confidence": ioc.confidence, "first_seen": ioc.first_seen}))
            seen_iocs.add(key)

    state["seen_cves"] = list(seen)[-1000:]
    state["seen_iocs"] = list(seen_iocs)[-1000:]

    if alerts:
        log.warning("Generated %d alerts", len(alerts))
    else:
        log.info("No new alerts")
    return alerts


def dispatch_alerts(alerts: list[ThreatAlert]) -> None:
    for alert in alerts:
        log.warning("ALERT [%s] %s — source: %s", alert.severity, alert.title, alert.source)
        webhook_url = os.environ.get("CTI_WEBHOOK_URL")
        if webhook_url:
            try:
                import urllib.request
                payload = json.dumps(asdict(alert)).encode("utf-8")
                req = urllib.request.Request(webhook_url, data=payload,
                                             headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=10) as resp:
                    log.debug("Webhook %s returned %d", webhook_url, resp.status)
            except Exception as exc:
                log.error("Webhook failed: %s", exc)


# ── Main orchestration ────────────────────────────────────────────────────────

def run_once(state: dict[str, Any]) -> list[ThreatAlert]:
    log.info("CTI collection cycle starting")
    alerts = generate_alerts(
        fetch_recent_cves(24),
        track_threat_actors(),
        monitor_dark_web(),
        fetch_stix_iocs(),
        state,
    )
    dispatch_alerts(alerts)
    save_state(state)
    return alerts


def run_loop() -> None:
    log.info("CTI feed started (interval: %ds)", POLL_INTERVAL)
    state = load_state()
    while True:
        try:
            run_once(state)
        except KeyboardInterrupt:
            log.info("Shutting down")
            break
        except Exception as exc:
            log.exception("Unexpected error: %s", exc)
        time.sleep(POLL_INTERVAL)


def main() -> None:
    parser = argparse.ArgumentParser(description="CTI Feed Ingestion")
    parser.add_argument("--once", action="store_true", help="Run one cycle and exit")
    args = parser.parse_args()
    if args.once:
        alerts = run_once(load_state())
        print(json.dumps([asdict(a) for a in alerts], indent=2))
    else:
        run_loop()


if __name__ == "__main__":
    main()
