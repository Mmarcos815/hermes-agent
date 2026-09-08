#!/usr/bin/env python3
"""
OSINT Automation Engine
=======================
A unified reconnaissance tool for authorized security research.
Modules: domain recon, email hunting, social media, dark web, CTI feeds.

Usage:
    python osint_automation_engine.py --help
    python osint_automation_engine.py domain --target example.com
    python osint_automation_engine.py email --target user@example.com
    python osint_automation_engine.py social --target username
    python osint_automation_engine.py darkweb --query "breach"
    python osint_automation_engine.py cti --target example.com
    python osint_automation_engine.py full --target example.com
"""

import argparse
import json
import re
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
DEFAULT_TIMEOUT = 15
OUTPUT_DIR = "."

COMMON_SUBDOMAINS = [
    "www", "mail", "api", "dev", "staging", "test", "admin",
    "portal", "secure", "vpn", "remote", "blog", "shop",
    "app", "mobile", "cdn", "static", "assets", "support",
    "docs", "wiki", "forum", "community", "status", "monitor",
    "git", "gitlab", "jenkins", "ci", "stage", "uat",
    "internal", "intranet", "extranet", "dashboard", "kibana",
    "grafana", "prometheus", "logs", "metrics", "db", "mysql",
    "postgres", "redis", "cache", "smtp", "imap", "pop",
    "owa", "exchange", "lync", "sip", "voip", "proxy",
    "gateway", "lb", "load", "edge", "origin", "media",
    "files", "storage", "backup", "archive", "research",
]

SOCIAL_PLATFORMS = {
    "twitter": "https://twitter.com/{username}",
    "github": "https://github.com/{username}",
    "linkedin": "https://www.linkedin.com/in/{username}",
    "reddit": "https://www.reddit.com/user/{username}",
    "instagram": "https://www.instagram.com/{username}",
    "tiktok": "https://www.tiktok.com/@{username}",
    "youtube": "https://www.youtube.com/@{username}",
    "medium": "https://medium.com/@{username}",
    "pinterest": "https://www.pinterest.com/{username}",
    "twitch": "https://www.twitch.tv/{username}",
    "tumblr": "https://{username}.tumblr.com",
    "flickr": "https://www.flickr.com/people/{username}",
    "vimeo": "https://vimeo.com/{username}",
    "soundcloud": "https://soundcloud.com/{username}",
    "spotify": "https://open.spotify.com/user/{username}",
}

PASTE_SITES = {
    "pastebin": "https://pastebin.com/search?q={query}",
    "ghostbin": "https://ghostbin.com/search?q={query}",
    "throwbin": "https://throwbin.io/search?q={query}",
    "controlc": "https://controlc.com/search?q={query}",
}

CTI_FEEDS = {
    "alienvault_otx": "https://otx.alienvault.com/api/v1/indicators/domain/{target}/general",
    "urlhaus": "https://urlhaus-api.abuse.ch/v1/host/",
    "threatfox": "https://threatfox-api.abuse.ch/api/",
    "phishtank": "https://www.phishtank.com/phish_search.php?page=1&valid=y&active=All&Search=Search&page={target}",
}

# ──────────────────────────────────────────────────────────────────────────────
# Utility Helpers
# ──────────────────────────────────────────────────────────────────────────────

def http_get(url, headers=None, timeout=DEFAULT_TIMEOUT):
    """Perform an HTTP GET request and return (status, body, headers_dict)."""
    hdrs = {"User-Agent": USER_AGENT}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, body, dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace"), {}
    except (urllib.error.URLError, socket.timeout, ConnectionError) as e:
        return 0, str(e), {}


def http_post(url, data=None, headers=None, timeout=DEFAULT_TIMEOUT):
    """Perform an HTTP POST request."""
    hdrs = {"User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"}
    if headers:
        hdrs.update(headers)
    body_data = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body_data, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, body, dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace"), {}
    except (urllib.error.URLError, socket.timeout, ConnectionError) as e:
        return 0, str(e), {}


def run_command(cmd, timeout=DEFAULT_TIMEOUT):
    """Run a shell command and return stdout or None."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip() if result.stdout else None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def extract_emails(text):
    """Extract email addresses from text."""
    return list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)))


def extract_ips(text):
    """Extract IPv4 addresses from text."""
    return list(set(re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', text)))


def extract_urls(text):
    """Extract URLs from text."""
    return list(set(re.findall(r'https?://[^\s<>"\')\]]+', text)))


def safe_print(data, label=""):
    """Pretty-print a dict/list to stdout."""
    if label:
        print(f"\n{'='*60}\n{label}\n{'='*60}")
    print(json.dumps(data, indent=2, default=str))


def now_iso():
    return datetime.now().isoformat() + "Z"


# ──────────────────────────────────────────────────────────────────────────────
# Module 1: Domain Recon
# ──────────────────────────────────────────────────────────────────────────────

def whois_lookup(domain):
    """Query WHOIS for domain registration info."""
    result = run_command(f"whois {domain}", timeout=20)
    if result:
        return {"raw": result, "source": "whois"}
    # Fallback: use Python's socket for basic info
    try:
        ip = socket.gethostbyname(domain)
        return {"ip": ip, "note": "whois CLI not available, used socket lookup", "source": "socket"}
    except socket.gaierror:
        return {"error": "Could not resolve domain"}


def dns_lookup(domain):
    """Perform DNS lookups for common record types."""
    records = {}
    record_types = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA", "SRV"]
    for rtype in record_types:
        out = run_command(f"nslookup -type={rtype} {domain}")
        if out and "No answer" not in out and "NXDOMAIN" not in out:
            records[rtype] = out
    return records


def subdomain_enumeration(domain):
    """Enumerate common subdomains via DNS resolution."""
    found = []
    for sub in COMMON_SUBDOMAINS:
        fqdn = f"{sub}.{domain}"
        try:
            ip = socket.gethostbyname(fqdn)
            found.append({"subdomain": fqdn, "ip": ip})
        except socket.gaierror:
            continue
    return found


def ssl_cert_info(domain):
    """Retrieve SSL certificate information."""
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=DEFAULT_TIMEOUT) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                return cert
    except Exception as e:
        return {"error": str(e)}


def domain_recon(target):
    """Full domain reconnaissance."""
    print(f"[*] Starting domain recon for: {target}")
    results = {
        "target": target,
        "timestamp": now_iso(),
        "whois": whois_lookup(target),
        "dns": dns_lookup(target),
        "subdomains": subdomain_enumeration(target),
        "ssl_cert": ssl_cert_info(target),
    }
    safe_print(results, "DOMAIN RECON RESULTS")
    return results


# ──────────────────────────────────────────────────────────────────────────────
# Module 2: Email Hunting
# ──────────────────────────────────────────────────────────────────────────────

def hunter_io_search(domain):
    """Search hunter.io for emails associated with a domain (public endpoint)."""
    url = f"https://hunter.io/api/v2/domains-search?domain={domain}"
    status, body, _ = http_get(url)
    if status == 200:
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"raw": body[:500]}
    return {"error": f"HTTP {status}", "note": "May require API key"}


def haveibeenpwned_check(email):
    """Check if email appears in known breaches via HIBP API."""
    url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{urllib.parse.quote(email)}"
    status, body, _ = http_get(url, headers={"User-Agent": "OSINT-Engine"})
    if status == 200:
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"raw": body[:500]}
    elif status == 404:
        return {"breaches": [], "status": "not_found"}
    return {"error": f"HTTP {status}"}


def skype_email_search(email):
    """Search for Skype profile info from email (public info)."""
    url = f"https://api.skype.com/users/{urllib.parse.quote(email)}/profile"
    status, body, _ = http_get(url)
    if status == 200:
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"raw": body[:300]}
    return {"error": f"HTTP {status}"}


def email_hunting(target):
    """Full email reconnaissance."""
    print(f"[*] Starting email hunting for: {target}")
    # Extract domain if email provided
    domain = target.split("@")[-1] if "@" in target else target
    results = {
        "target": target,
        "timestamp": now_iso(),
        "hunter_io": hunter_io_search(domain),
        "pwned": haveibeenpwned_check(target) if "@" in target else {"skipped": "provide an email"},
        "skype": skype_email_search(target) if "@" in target else {"skipped": "provide an email"},
    }
    safe_print(results, "EMAIL HUNTING RESULTS")
    return results


# ──────────────────────────────────────────────────────────────────────────────
# Module 3: Social Media Scraping
# ──────────────────────────────────────────────────────────────────────────────

def probe_social_platform(platform, username):
    """Probe a single social platform for a username."""
    url = SOCIAL_PLATFORMS[platform].format(username=username)
    status, body, headers = http_get(url)
    if status == 200:
        # Extract title and meta description
        title = re.search(r'<title>(.*?)</title>', body, re.IGNORECASE)
        meta_desc = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)', body, re.IGNORECASE)
        return {
            "url": url,
            "exists": True,
            "status": status,
            "title": title.group(1).strip() if title else None,
            "description": meta_desc.group(1).strip() if meta_desc else None,
        }
    elif status == 404:
        return {"url": url, "exists": False, "status": 404}
    else:
        return {"url": url, "status": status, "note": "may require auth"}


def social_media_search(target):
    """Search across social platforms for a username."""
    print(f"[*] Starting social media search for: {target}")
    results = {
        "target": target,
        "timestamp": now_iso(),
        "profiles": {},
    }
    for platform, url_template in SOCIAL_PLATFORMS.items():
        try:
            result = probe_social_platform(platform, target)
            results["profiles"][platform] = result
            if result.get("exists"):
                print(f"    [+] Found on {platform}: {result.get('title', 'N/A')}")
            time.sleep(0.5)  # Rate limiting
        except Exception as e:
            results["profiles"][platform] = {"error": str(e)}
    safe_print(results, "SOCIAL MEDIA RESULTS")
    return results


# ──────────────────────────────────────────────────────────────────────────────
# Module 4: Dark Web Monitoring
# ──────────────────────────────────────────────────────────────────────────────

def search_paste_sites(query):
    """Search public paste sites for a query."""
    results = {}
    for site, url_template in PASTE_SITES.items():
        url = url_template.format(query=urllib.parse.quote(query))
        status, body, _ = http_get(url)
        results[site] = {
            "url": url,
            "status": status,
            "note": "Public endpoint - full results may require parsing" if status == 200 else f"HTTP {status}",
        }
    return results


def check_ddark_web_forums(query):
    """Check indexed dark web forum references via clearnet search proxies."""
    # Use public search engines that index .onion references
    results = {"query": query, "sources": []}
    # Search via clearnet for .onion references
    search_url = f"https://ahmia.fi/search/?q={urllib.parse.quote(query)}"
    status, body, _ = http_get(search_url)
    if status == 200:
        onions = re.search(r'<cite>(.*?)</cite>', body)
        if onions:
            results["sources"].append({"ahmia.fi": onions.group(1)})
        else:
            results["sources"].append({"ahmia.fi": "No direct .onion results parsed"})
    return results


def pastebin_recent_check(query):
    """Check Pastebin's public recent pastes for a query."""
    url = f"https://pastebin.com/archive"
    status, body, _ = http_get(url)
    matches = []
    if status == 200:
        # Look for matching text in paste titles
        paste_titles = re.findall(r'<td\s+class="icon"\s*>.*?href="/([^"]+)"[^>]*></td>\s*<td[^>]*>(.*?)</td>', body, re.DOTALL)
        for paste_id, title_block in paste_titles:
            if query.lower() in title_block.lower():
                matches.append({"id": paste_id, "url": f"https://pastebin.com/{paste_id}"})
    return matches


def darkweb_monitor(query):
    """Dark web and paste site monitoring."""
    print(f"[*] Starting dark web monitoring for: {query}")
    results = {
        "query": query,
        "timestamp": now_iso(),
        "paste_sites": search_paste_sites(query),
        "ddark_web_forums": check_ddark_web_forums(query),
        "pastebin_matches": pastebin_recent_check(query),
    }
    safe_print(results, "DARK WEB MONITORING RESULTS")
    return results


# ──────────────────────────────────────────────────────────────────────────────
# Module 5: CTI Feed Ingestion
# ──────────────────────────────────────────────────────────────────────────────

def alienvault_otx_lookup(target):
    """Query AlienVault OTX for threat intelligence on a target."""
    url = CTI_FEEDS["alienvault_otx"].format(target=urllib.parse.quote(target))
    status, body, _ = http_get(url)
    if status == 200:
        try:
            data = json.loads(body)
            # Extract pulse info
            pulses = data.get("pulse_info", {}).get("pulses", [])
            malware_families = []
            for p in pulses:
                for m in p.get("malware_families", []):
                    if isinstance(m, str) and m not in malware_families:
                        malware_families.append(m)
            return {
                "pulse_count": len(pulses),
                "reputation": data.get("reputation"),
                "pulses": [{"name": p.get("name"), "tags": p.get("tags", []), "created": p.get("created")} for p in pulses[:5]],
                "malware_families": malware_families[:10],
            }
        except json.JSONDecodeError:
            return {"raw": body[:500]}
    return {"error": f"HTTP {status}"}


def urlhaus_lookup(target):
    """Query URLhaus (abuse.ch) for malware URLs associated with a host."""
    data = {"host": target}
    status, body, _ = http_post(CTI_FEEDS["urlhaus"], data=data)
    if status == 200:
        try:
            result = json.loads(body)
            return {
                "query_status": result.get("query_status"),
                "url_count": len(result.get("urls", [])),
                "urls": result.get("urls", [])[:5],
                "blacklist": result.get("blacklists", {}),
            }
        except json.JSONDecodeError:
            return {"raw": body[:500]}
    return {"error": f"HTTP {status}"}


def threatfox_lookup(target):
    """Query ThreatFox (abuse.ch) for threat intelligence on a target."""
    payload = {"query": "search_ioc", "search_term": target}
    status, body, _ = http_post(CTI_FEEDS["threatfox"], data=payload)
    if status == 200:
        try:
            result = json.loads(body)
            data = json.loads(result.get("data", "[]"))
            return {
                "query_status": result.get("query_status"),
                "ioc_count": len(data),
                "iocs": data[:5],
            }
        except (json.JSONDecodeError, TypeError):
            return {"raw": body[:500]}
    return {"error": f"HTTP {status}"}


def abuse_ipdb_lookup(target):
    """Query AbuseIPDB-style public feed (using ip-api.com as public proxy)."""
    # Use ip-api.com as a public IP reputation source
    url = f"http://ip-api.com/json/{target}?fields=status,country,regionName,city,isp,org,as,proxy,hosting,query"
    status, body, _ = http_get(url)
    if status == 200:
        try:
            data = json.loads(body)
            return {
                "source": "ip-api.com",
                "ip": data.get("query"),
                "country": data.get("country"),
                "isp": data.get("isp"),
                "org": data.get("org"),
                "is_proxy": data.get("proxy"),
                "is_hosting": data.get("hosting"),
            }
        except json.JSONDecodeError:
            return {"raw": body[:500]}
    return {"error": f"HTTP {status}"}


def phishtank_search(query):
    """Search PhishTank for phishing URLs."""
    url = CTI_FEEDS["phishtank"].format(target=urllib.parse.quote(query))
    status, body, _ = http_get(url)
    if status == 200:
        entries = re.findall(r'<div\s+class="url">\s*<a[^>]*>(.*?)</a>', body)
        return {"url_count": len(entries), "urls": entries[:10]}
    return {"error": f"HTTP {status}"}


def cti_ingestion(target):
    """Full CTI feed ingestion."""
    print(f"[*] Starting CTI feed ingestion for: {target}")
    results = {
        "target": target,
        "timestamp": now_iso(),
        "alienvault_otx": alienvault_otx_lookup(target),
        "urlhaus": urlhaus_lookup(target),
        "threatfox": threatfox_lookup(target),
        "ip_reputation": abuse_ipdb_lookup(target),
        "phishtank": phishtank_search(target),
    }
    safe_print(results, "CTI INGESTION RESULTS")
    return results


# ──────────────────────────────────────────────────────────────────────────────
# Full Recon Pipeline
# ──────────────────────────────────────────────────────────────────────────────

def full_recon(target):
    """Run all modules for comprehensive OSINT."""
    print(f"\n{'#'*60}")
    print(f"# FULL OSINT RECON: {target}")
    print(f"# Started: {now_iso()}")
    print(f"{'#'*60}\n")

    results = {
        "target": target,
        "timestamp": now_iso(),
        "domain": domain_recon(target),
        "social": social_media_search(target),
        "darkweb": darkweb_monitor(target),
        "cti": cti_ingestion(target),
    }

    # Try email hunting with common prefixes
    email_domain = target
    for prefix in ["admin", "info", "contact", "hello", "support"]:
        email_target = f"{prefix}@{email_domain}"
        results[f"email_{prefix}"] = haveibeenpwned_check(email_target)

    print(f"\n{'#'*60}")
    print(f"# RECON COMPLETE: {target}")
    print(f"{'#'*60}\n")
    return results


# ──────────────────────────────────────────────────────────────────────────────
# CLI Argument Parser
# ──────────────────────────────────────────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(
        description="OSINT Automation Engine - Authorized Reconnaissance Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python osint_automation_engine.py --timeout 20 domain --target example.com
  python osint_automation_engine.py email --target user@example.com
  python osint_automation_engine.py social --target johndoe
  python osint_automation_engine.py darkweb --query "example.com"
  python osint_automation_engine.py cti --target example.com
  python osint_automation_engine.py full --target example.com

Note: This tool is intended for authorized security research only.
        """,
    )
    # Global options must come BEFORE the subcommand
    parser.add_argument("--output", "-o", help="Save results to JSON file")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress intermediate output")

    subparsers = parser.add_subparsers(dest="module", help="Module to run")

    # Domain recon
    p_domain = subparsers.add_parser("domain", help="Domain reconnaissance")
    p_domain.add_argument("--target", "-t", required=True, help="Target domain")

    # Email hunting
    p_email = subparsers.add_parser("email", help="Email hunting")
    p_email.add_argument("--target", "-t", required=True, help="Target email or domain")

    # Social media
    p_social = subparsers.add_parser("social", help="Social media scraping")
    p_social.add_argument("--target", "-t", required=True, help="Username to search")

    # Dark web
    p_dark = subparsers.add_parser("darkweb", help="Dark web monitoring")
    p_dark.add_argument("--query", "-q", required=True, help="Search query")

    # CTI feeds
    p_cti = subparsers.add_parser("cti", help="CTI feed ingestion")
    p_cti.add_argument("--target", "-t", required=True, help="Target domain/IP")

    # Full recon
    p_full = subparsers.add_parser("full", help="Full OSINT reconnaissance")
    p_full.add_argument("--target", "-t", required=True, help="Target domain")

    return parser


# ──────────────────────────────────────────────────────────────────────────────
# Main Entry Point
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.module:
        parser.print_help()
        sys.exit(1)

    # Set global timeout
    global DEFAULT_TIMEOUT
    DEFAULT_TIMEOUT = args.timeout

    # Route to the correct module
    results = {}
    try:
        if args.module == "domain":
            results = domain_recon(args.target)
        elif args.module == "email":
            results = email_hunting(args.target)
        elif args.module == "social":
            results = social_media_search(args.target)
        elif args.module == "darkweb":
            results = darkweb_monitor(args.query)
        elif args.module == "cti":
            results = cti_ingestion(args.target)
        elif args.module == "full":
            results = full_recon(args.target)
        else:
            parser.print_help()
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[!] Fatal error: {e}")
        sys.exit(1)

    # Save to file if requested
    if args.output and results:
        output_path = args.output
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str, ensure_ascii=False)
        print(f"\n[+] Results saved to: {output_path}")
    elif results:
        # Default: save to timestamped file
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_val = getattr(args, 'target', None) or getattr(args, 'query', None) or 'unknown'
        safe_name = re.sub(r'[^\w.-]', '_', str(target_val))
        output_path = f"osint_{args.module}_{safe_name}_{ts}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str, ensure_ascii=False)
        print(f"\n[+] Results saved to: {output_path}")

    return results


if __name__ == "__main__":
    main()
