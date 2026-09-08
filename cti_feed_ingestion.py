#!/usr/bin/env python3
"""
CTI Feed Ingestion Script
=========================
Ingests threat intelligence feeds from MISP, AlienVault OTX, and abuse.ch
(URLhaus, MalwareBazaar), correlates IOCs against known infrastructure,
and alerts on matches.

Usage:
    python cti_feed_ingestion.py --feeds urlhaus malwarebazaar
    python cti_feed_ingestion.py --feeds all --infrastructure infra.json
    python cti_feed_ingestion.py --list-iocs
    python cti_feed_ingestion.py --init-config
"""

import argparse
import csv
import hashlib
import ipaddress
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
WORKSPACE = Path(__file__).parent
IOC_DB_PATH = WORKSPACE / "ioc_database.json"
ALERTS_PATH = WORKSPACE / "alerts.json"
CONFIG_PATH = WORKSPACE / "cti_config.json"
STATE_PATH = WORKSPACE / "cti_state.json"

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_CONFIG = {
    "misp": {
        "enabled": False,
        "url": "https://misp.example.com",
        "api_key": "",
        "verify_ssl": True,
        "days_back": 7,
    },
    "otx": {
        "enabled": False,
        "api_key": "",
        "limit": 20,
        "modified_since_days": 7,
    },
    "abuse_ch": {
        "enabled": True,
        "urlhaus_limit": 100,
        "malwarebazaar_limit": 100,
        "malwarebazaar_api_key": "",
    },
    "infrastructure": {
        "domains": [],
        "ips": [],
        "file_hashes": [],
    },
    "alerting": {
        "console": True,
        "file": True,
        "min_severity": "medium",
    },
}

SEVERITY_LEVELS = {"low": 1, "medium": 2, "high": 3, "critical": 4}
IOC_TYPES = ("ip", "domain", "url", "hash_md5", "hash_sha1", "hash_sha256", "email")

USER_AGENT = "CTI-Ingestion-Script/1.0"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(path: Path, default=None):
    """Load JSON from path, returning default if missing."""
    if not path.exists():
        return default if default is not None else {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[WARN] Could not read {path}: {e}")
        return default if default is not None else {}


def save_json(path: Path, data):
    """Atomic-ish JSON write."""
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)
    tmp.replace(path)


def http_get(url: str, headers: dict = None, timeout: int = 30, verify_ssl: bool = True) -> bytes:
    """Minimal HTTP GET using only stdlib."""
    req = urllib.request.Request(url, headers=headers or {})
    req.add_header("User-Agent", USER_AGENT)
    ctx = ssl.create_default_context()
    if not verify_ssl:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} for {url}: {e.reason}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"URL error for {url}: {e.reason}") from e


def http_post(url: str, data: bytes = None, headers: dict = None, timeout: int = 30) -> bytes:
    """Minimal HTTP POST using only stdlib."""
    req = urllib.request.Request(url, data=data, method="POST", headers=headers or {})
    req.add_header("User-Agent", USER_AGENT)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {e.code} for {url}: {e.reason} — {body[:200]}") from e


def is_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value.strip())
        return True
    except ValueError:
        return False


def is_domain(value: str) -> bool:
    v = value.strip().lower()
    if not v or len(v) > 253 or is_ip(v):
        return False
    return bool(re.match(r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$", v))


def is_hash(value: str) -> str | None:
    v = value.strip().lower()
    if re.match(r"^[a-f0-9]{32}$", v):
        return "md5"
    if re.match(r"^[a-f0-9]{40}$", v):
        return "sha1"
    if re.match(r"^[a-f0-9]{64}$", v):
        return "sha256"
    return None


def normalise_ioc(value: str) -> tuple[str, str]:
    """Return (type, normalised_value)."""
    v = value.strip().lower()
    if is_ip(v):
        return ("ip", v)
    if is_domain(v):
        return ("domain", v)
    h = is_hash(v)
    if h:
        return (f"hash_{h}", v)
    if v.startswith(("http://", "https://")):
        return ("url", v)
    if re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", v):
        return ("email", v)
    return ("unknown", v)


# ---------------------------------------------------------------------------
# Feed: MISP
# ---------------------------------------------------------------------------

def fetch_misp_events(config: dict) -> list[dict]:
    """Fetch recent MISP events and extract IOCs."""
    url = config["misp"]["url"].rstrip("/")
    api_key = config["misp"]["api_key"]
    if not api_key:
        print("[MISP] No API key configured — skipping.")
        return []

    headers = {
        "Authorization": api_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    since = (datetime.now(tz=timezone.utc) - timedelta(days=config["misp"]["days_back"])).strftime("%Y-%m-%d")
    payload = json.dumps({
        "returnFormat": "json",
        "timestamp": since,
        "enforceWarninglist": True,
        "includeAttributeUuid": False,
    }).encode()

    print(f"[MISP] Querying {url}/events/index since {since} …")
    raw = http_post(f"{url}/events/index", data=payload, headers=headers,
                    timeout=60)
    events = json.loads(raw)
    iocs = []
    for event in events:
        e_id = event.get("Event", {}).get("id", "?")
        info = event.get("Event", {}).get("info", "")
        for attr in event.get("Event", {}).get("Attribute", []):
            ioc_type, val = normalise_ioc(attr.get("value", ""))
            if ioc_type == "unknown":
                continue
            iocs.append({
                "value": val,
                "type": ioc_type,
                "source": "misp",
                "source_id": str(e_id),
                "threat_level": event.get("Event", {}).get("threat_level_id", "3"),
                "info": info,
                "timestamp": attr.get("timestamp", ""),
                "severity": _misp_severity(event.get("Event", {}).get("threat_level_id")),
            })
    print(f"[MISP] Extracted {len(iocs)} IOCs from {len(events)} events.")
    return iocs


def _misp_severity(tlid: str) -> str:
    mapping = {"1": "critical", "2": "high", "3": "medium", "4": "low"}
    return mapping.get(str(tlid), "medium")


# ---------------------------------------------------------------------------
# Feed: AlienVault OTX
# ---------------------------------------------------------------------------

def fetch_otx_pulses(config: dict) -> list[dict]:
    """Fetch subscribed OTX pulses and extract their IOCs."""
    api_key = config["otx"]["api_key"]
    if not api_key:
        print("[OTX] No API key configured — skipping.")
        return []

    headers = {"X-OTX-API-KEY": api_key, "Accept": "application/json"}
    since = (datetime.now(tz=timezone.utc) - timedelta(days=config["otx"]["modified_since_days"]))
    since_str = since.strftime("%Y-%m-%dT%H:%M:%S")
    limit = config["otx"]["limit"]

    url = (f"https://otx.alienvault.com/api/v1/pulses/subscribed"
           f"?limit={limit}&modified_since={urllib.parse.quote(since_str)}&page=1")
    print(f"[OTX] Fetching up to {limit} pulses modified since {since_str} …")
    raw = http_get(url, headers=headers, timeout=60)
    data = json.loads(raw)
    results = data.get("results", [])
    iocs = []
    for pulse in results:
        p_id = pulse.get("id", "?")
        pname = pulse.get("name", "")
        tags = ", ".join(pulse.get("tags", []))
        for ind in pulse.get("indicators", []):
            ioc_type, val = normalise_ioc(ind.get("indicator", ""))
            if ioc_type == "unknown":
                continue
            iocs.append({
                "value": val,
                "type": ioc_type,
                "source": "otx",
                "source_id": p_id,
                "info": pname,
                "tags": tags,
                "created": ind.get("created", ""),
                "severity": _otx_severity(pulse.get("TLP", "green"), pulse.get("malware_families", [])),
            })
    print(f"[OTX] Extracted {len(iocs)} IOCs from {len(results)} pulses.")
    return iocs


def _otx_severity(tlp: str, malware_families: list) -> str:
    if malware_families:
        return "high"
    if tlp.lower() in ("red",):
        return "critical"
    return "medium"


# ---------------------------------------------------------------------------
# Feed: abuse.ch
# ---------------------------------------------------------------------------

def fetch_urlhaus(limit: int = 100) -> list[dict]:
    """Fetch recent URLhaus CSV feed."""
    print(f"[URLhaus] Fetching {limit} recent entries …")
    url = "https://urlhaus.abuse.ch/downloads/csv_recent/"
    raw = http_get(url, timeout=60)
    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines()
    # Strip comment lines starting with #
    csv_lines = [l for l in lines if not l.startswith("#")]
    # The header is commented out; provide fieldnames explicitly
    fieldnames = ["id", "dateadded", "url", "url_status", "last_online",
                  "threat", "tags", "urlhaus_link", "reporter"]
    reader = csv.DictReader(StringIO("\n".join(csv_lines)), fieldnames=fieldnames)
    iocs = []
    for i, row in enumerate(reader):
        if i >= limit:
            break
        url_val = row.get("url", "").strip()
        if not url_val:
            continue
        ioc_type, val = normalise_ioc(url_val)
        iocs.append({
            "value": val,
            "type": ioc_type if ioc_type != "unknown" else "url",
            "source": "urlhaus",
            "source_id": row.get("id", ""),
            "info": f"Threat: {row.get('threat', '')}; Status: {row.get('url_status', '')}",
            "tags": row.get("tags", ""),
            "date_added": row.get("dateadded", ""),
            "severity": "high" if row.get("url_status", "") == "online" else "medium",
        })
    print(f"[URLhaus] Extracted {len(iocs)} IOCs.")
    return iocs


def fetch_malwarebazaar(limit: int = 100, api_key: str = "") -> list[dict]:
    """Fetch recent MalwareBazaar entries via hash lookup endpoint.
    
    Note: abuse.ch now requires an API key for the get_recent query.
    Register at https://bazaar.abuse.ch/api/ to obtain a free key.
    """
    print(f"[MalwareBazaar] Fetching {limit} recent samples …")
    url = "https://mb-api.abuse.ch/api/v1/"
    payload = json.dumps({"query": "get_recent", "selector": "time", "limit": limit}).encode()
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["API-KEY"] = api_key
    raw = http_post(url, data=payload, headers=headers, timeout=60)
    data = json.loads(raw)
    if data.get("query_status") != "ok":
        print(f"[MalwareBazaar] Query failed: {data.get('query_status')}")
        return []
    entries = data.get("data", [])[:limit]
    iocs = []
    for entry in entries:
        for h_type in ("sha256_hash", "sha1_hash", "md5_hash"):
            val = entry.get(h_type, "").strip()
            if val:
                iocs.append({
                    "value": val.lower(),
                    "type": f"hash_{h_type.replace('_hash', '')}",
                    "source": "malwarebazaar",
                    "source_id": entry.get("sha256_hash", val),
                    "info": f"{entry.get('signature', 'Unknown')}; {entry.get('file_type', '')}",
                    "tags": ", ".join(entry.get("tags", [])),
                    "timestamp": entry.get("first_seen", ""),
                    "severity": "high",
                })
        # Also extract imphash / ssdeep as soft hashes
        for domain in (entry.get("intelligence", {}) or {}).get("domains", []):
            iocs.append({
                "value": domain.lower(),
                "type": "domain",
                "source": "malwarebazaar_intel",
                "source_id": entry.get("sha256_hash", ""),
                "info": f"C2 domain for {entry.get('signature', '')}",
                "tags": "c2",
                "timestamp": entry.get("first_seen", ""),
                "severity": "critical",
            })
        for ip_val in (entry.get("intelligence", {}) or {}).get("urls", []):
            # intelligence.urls contains URLs — extract host
            try:
                parsed = urllib.parse.urlparse(ip_val)
                host = parsed.hostname or ""
                if is_ip(host):
                    iocs.append({
                        "value": host,
                        "type": "ip",
                        "source": "malwarebazaar_intel",
                        "source_id": entry.get("sha256_hash", ""),
                        "info": f"C2 IP for {entry.get('signature', '')}",
                        "tags": "c2",
                        "timestamp": entry.get("first_seen", ""),
                        "severity": "critical",
                    })
            except Exception:
                continue
    print(f"[MalwareBazaar] Extracted {len(iocs)} IOCs.")
    return iocs


# ---------------------------------------------------------------------------
# Correlation
# ---------------------------------------------------------------------------

def load_infrastructure(config: dict) -> dict:
    """Return infrastructure asset buckets."""
    infra = config.get("infrastructure", {})
    return {
        "domains": {d.lower().strip() for d in infra.get("domains", [])},
        "ips": {ip.strip() for ip in infra.get("ips", [])},
        "hashes": {h.lower().strip() for h in infra.get("file_hashes", [])},
    }


def correlate(iocs: list[dict], infra: dict) -> list[dict]:
    """Match IOCs against infrastructure; return list of alerts."""
    alerts = []
    for ioc in iocs:
        val = ioc["value"]
        itype = ioc["type"]
        match = None
        if itype == "ip" and val in infra["ips"]:
            match = f"IP {val} matches monitored infrastructure"
        elif itype == "domain" and val in infra["domains"]:
            match = f"Domain {val} matches monitored infrastructure"
        elif itype.startswith("hash_") and val in infra["hashes"]:
            match = f"Hash {val} matches monitored file inventory"
        elif itype == "url":
            # Check if URL contains a monitored IP or domain
            for ip in infra["ips"]:
                if ip in val:
                    match = f"URL {val[:80]} contains monitored IP {ip}"
                    break
            if not match:
                for domain in infra["domains"]:
                    if domain in val:
                        match = f"URL {val[:80]} contains monitored domain {domain}"
                        break
        if match:
            alerts.append({
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "severity": ioc.get("severity", "medium"),
                "match": match,
                "ioc": ioc,
            })
    return alerts


# ---------------------------------------------------------------------------
# Alerting
# ---------------------------------------------------------------------------

SEVERITY_COLORS = {
    "low": "\033[90m",
    "medium": "\033[33m",
    "high": "\033[91m",
    "critical": "\033[41m\033[97m",
}
RESET = "\033[0m"


def alert_console(alerts: list[dict], min_severity: str = "medium"):
    """Print colour-coded alerts to console."""
    min_lvl = SEVERITY_LEVELS.get(min_severity, 1)
    shown = 0
    for a in alerts:
        if SEVERITY_LEVELS.get(a["severity"], 0) < min_lvl:
            continue
        color = SEVERITY_COLORS.get(a["severity"], "")
        tag = f"[{a['severity'].upper()}]"
        print(f"{color}{tag} {a['match']}{RESET}")
        ioc = a["ioc"]
        print(f"       Source: {ioc['source']} (ID: {ioc.get('source_id', '?')})")
        print(f"       Type: {ioc['type']} | Value: {ioc['value'][:120]}")
        if ioc.get("info"):
            print(f"       Info: {ioc['info'][:120]}")
        shown += 1
    if shown == 0:
        print("[ALERT] No matches above severity threshold.")
    else:
        print(f"[ALERT] {shown} total matches found.")


def alert_file(alerts: list[dict], path: Path):
    """Append alerts to a JSON-lines file."""
    if not alerts:
        return
    with open(path, "a", encoding="utf-8") as f:
        for a in alerts:
            f.write(json.dumps(a, default=str) + "\n")
    print(f"[ALERT] Wrote {len(alerts)} alerts to {path}")


# ---------------------------------------------------------------------------
# IOC database
# ---------------------------------------------------------------------------

def build_ioc_index(iocs: list[dict]) -> dict:
    """Deduplicate IOCs by (type, value), keep newest / highest severity."""
    index: dict[str, dict] = {}
    for ioc in iocs:
        key = f"{ioc['type']}:{ioc['value']}"
        existing = index.get(key)
        if existing is None:
            index[key] = ioc
        else:
            # keep the one with higher severity
            if SEVERITY_LEVELS.get(ioc.get("severity", "low"), 0) > SEVERITY_LEVELS.get(existing.get("severity", "low"), 0):
                index[key] = ioc
    return index


def update_ioc_db(index: dict, db_path: Path):
    """Merge new IOCs into persistent database."""
    existing = load_json(db_path, {})
    merged = {**existing, **index}
    save_json(db_path, merged)
    print(f"[DB] IOC database now holds {len(merged)} entries ({len(index)} new this run).")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmd_init_config(_args, config):
    save_json(CONFIG_PATH, DEFAULT_CONFIG)
    print(f"[CONFIG] Wrote default config to {CONFIG_PATH}")
    return 0


def cmd_ingest(args, config):
    feeds = set(args.feeds)
    all_feeds = {"misp", "otx", "urlhaus", "malwarebazaar"}
    if "all" in feeds:
        feeds = all_feeds

    # Load infrastructure
    infra_path = getattr(args, "infrastructure", None)
    if infra_path:
        infra_cfg = load_json(Path(infra_path))
        config["infrastructure"].update(infra_cfg)
    infra = load_infrastructure(config)

    print(f"[*] Ingesting feeds: {', '.join(sorted(feeds))}")
    print(f"[*] Infrastructure assets: {len(infra['ips'])} IPs, {len(infra['domains'])} domains, {len(infra['hashes'])} hashes")

    all_iocs: list[dict] = []
    try:
        if "misp" in feeds:
            all_iocs.extend(fetch_misp_events(config))
    except Exception as e:
        print(f"[ERROR] MISP feed failed: {e}")
    try:
        if "otx" in feeds:
            all_iocs.extend(fetch_otx_pulses(config))
    except Exception as e:
        print(f"[ERROR] OTX feed failed: {e}")
    try:
        if "urlhaus" in feeds:
            all_iocs.extend(fetch_urlhaus(config["abuse_ch"]["urlhaus_limit"]))
    except Exception as e:
        print(f"[ERROR] URLhaus feed failed: {e}")
    try:
        if "malwarebazaar" in feeds:
            all_iocs.extend(fetch_malwarebazaar(
                config["abuse_ch"]["malwarebazaar_limit"],
                config["abuse_ch"].get("malwarebazaar_api_key", ""),
            ))
    except Exception as e:
        print(f"[ERROR] MalwareBazaar feed failed: {e}")

    print(f"\n[*] Total IOCs collected: {len(all_iocs)}")

    # Correlate
    alerts = correlate(all_iocs, infra)
    print(f"[*] Matches found: {len(alerts)}")

    # Alert
    min_sev = config.get("alerting", {}).get("min_severity", "medium")
    if config.get("alerting", {}).get("console", True):
        alert_console(alerts, min_sev)
    if config.get("alerting", {}).get("file", True):
        alert_file(alerts, ALERTS_PATH)

    # Persist IOCs
    index = build_ioc_index(all_iocs)
    update_ioc_db(index, IOC_DB_PATH)

    return 0


def cmd_list_iocs(args, _config):
    db = load_json(IOC_DB_PATH, {})
    if not db:
        print("[*] No IOC database found. Run ingestion first.")
        return 0
    for key, ioc in sorted(db.items()):
        sev = ioc.get("severity", "?")
        src = ioc.get("source", "?")
        print(f"[{sev:8}] [{src:15}] {ioc['type']:12} {ioc['value'][:100]}")
    print(f"\n[*] {len(db)} total IOCs in database.")
    return 0


def cmd_search(args, _config):
    db = load_json(IOC_DB_PATH, {})
    if not db:
        print("[*] No IOC database found.")
        return 1
    term = args.term.lower()
    matches = [ioc for ioc in db.values() if term in ioc["value"].lower() or term in ioc.get("info", "").lower()]
    for ioc in matches:
        print(f"[{ioc.get('severity', '?'):8}] [{ioc.get('source', '?'):15}] {ioc['type']:12} {ioc['value'][:120]}")
    print(f"\n[*] {len(matches)} matches for '{args.term}'.")
    return 0


def cmd_stats(args, _config):
    db = load_json(IOC_DB_PATH, {})
    if not db:
        print("[*] No IOC database found.")
        return 1
    by_source: dict[str, int] = {}
    by_type: dict[str, int] = {}
    by_sev: dict[str, int] = {}
    for ioc in db.values():
        by_source[ioc.get("source", "?")] = by_source.get(ioc.get("source", "?"), 0) + 1
        by_type[ioc.get("type", "?")] = by_type.get(ioc.get("type", "?"), 0) + 1
        by_sev[ioc.get("severity", "?")] = by_sev.get(ioc.get("severity", "?"), 0) + 1
    print(f"[*] IOC Database Stats — {len(db)} entries total\n")
    print("  By Source:")
    for k, v in sorted(by_source.items(), key=lambda x: -x[1]):
        print(f"    {k:20} {v}")
    print("\n  By Type:")
    for k, v in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"    {k:20} {v}")
    print("\n  By Severity:")
    for k, v in sorted(by_sev.items(), key=lambda x: -SEVERITY_LEVELS.get(x[0], 0)):
        print(f"    {k:20} {v}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="CTI Feed Ingestion — MISP, OTX, abuse.ch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python cti_feed_ingestion.py --init-config
  python cti_feed_ingestion.py --feeds all --infrastructure infra.json
  python cti_feed_ingestion.py --feeds urlhaus malwarebazaar
  python cti_feed_ingestion.py --list-iocs
  python cti_feed_ingestion.py --search 192.0.2.1
  python cti_feed_ingestion.py --stats""",
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("init-config", help="Write default cti_config.json").set_defaults(func=cmd_init_config)

    p_ingest = sub.add_parser("ingest", help="Run feed ingestion")
    p_ingest.add_argument("--feeds", nargs="+", required=True,
                          help="Feeds: misp otx urlhaus malwarebazaar all")
    p_ingest.add_argument("--infrastructure", "-i", default=None,
                          help="Path to infrastructure JSON (overrides config)")
    p_ingest.set_defaults(func=cmd_ingest)

    p_list = sub.add_parser("list-iocs", help="List all IOCs in database")
    p_list.set_defaults(func=cmd_list_iocs)

    p_search = sub.add_parser("search", help="Search IOC database")
    p_search.add_argument("term", help="Search term (substring match)")
    p_search.set_defaults(func=cmd_search)

    p_stats = sub.add_parser("stats", help="Show IOC database statistics")
    p_stats.set_defaults(func=cmd_stats)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    config = load_json(CONFIG_PATH, DEFAULT_CONFIG)
    return args.func(args, config)


if __name__ == "__main__":
    sys.exit(main())
