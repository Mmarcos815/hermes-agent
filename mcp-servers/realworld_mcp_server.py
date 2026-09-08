#!/usr/bin/env python3
"""Real-World Task MCP Server — Security & Analysis Tools.

Provides analysis tools for phishing emails, files, URLs, domains, IPs, and
file hashes. Uses real APIs (DNS, HTTP, VirusTotal) where possible, with
built-in heuristics as fallback.

Run with:  python realworld_mcp_server.py
"""

from __future__ import annotations

import asyncio
import base64
import dns.resolver
import email
import email.policy
import hashlib
import ipaddress
import json
import math
import os
import re
import socket
import ssl
import string
import time
from collections import Counter
from datetime import datetime, timezone
from email.utils import parseaddr, parsedate_to_datetime
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

import requests
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

mcp = FastMCP("realworld")

VT_API_KEY = os.environ.get("VT_API_KEY", "")
ABUSEIPDB_API_KEY = os.environ.get("ABUSEIPDB_API_KEY", "")

# Known-suspicious TLDs often used in phishing campaigns
SUSPICIOUS_TLDS = {
    "tk", "ml", "ga", "cf", "gq", "xyz", "top", "pw", "cc", "work",
    "date", "racing", "stream", "download", "bid", "loan", "trade",
}

# Suspicious keywords in URLs
URL_SUSPICIOUS_KEYWORDS = [
    "login", "signin", "verify", "update", "secure", "account",
    "banking", "confirm", "password", "suspend", "alert", "notify",
    "unusual", "activity", "restricted", "locked", "expire",
]

# Known-bad hash prefixes (simplified local blocklist for demo)
# In production, load from a real threat-intel feed
KNOWN_BAD_HASHES = {
    "e99a18c428cb38d5f260853678922e03",  # MD5: "abc123"
    "44d88612fea8a8f36de82e1278abb02f",  # MD5: "ei"
}

# File magic bytes for common types
FILE_SIGNATURES = {
    b"\x89PNG": "PNG image",
    b"\xff\xd8\xff": "JPEG image",
    b"GIF87a": "GIF image",
    b"GIF89a": "GIF image",
    b"PK\x03\x04": "ZIP/Office archive",
    b"MZ": "Windows executable",
    b"\x7fELF": "ELF executable",
    b"%PDF": "PDF document",
    b"\x1f\x8b": "GZIP compressed",
    b"BM": "BMP image",
    b"RIFF": "RIFF container (WEBP/WAV/AVI)",
    b"\x00\x00\x00\x1cftyp": "MP4 video",
    b"\x00\x00\x00\x20ftyp": "MP4 video",
    b"ID3": "MP3 audio",
    b"OggS": "OGG media",
    b"fLaC": "FLAC audio",
    b"\x00\x01\x00\x00": "TrueType font",
    b"SQLite format 3\x00": "SQLite database",
}

# Regex patterns for phishing detection
PHISHING_PATTERNS = {
    "urgency": re.compile(
        r"\b(urgent|immediately|right away|act now|limited time|expire|expir)\b",
        re.I,
    ),
    "threat": re.compile(
        r"\b(suspend|disable|close|terminate|block|restricted|locked)\b",
        re.I,
    ),
    "credential": re.compile(
        r"\b(password|login|credential|username|verify your)\b",
        re.I,
    ),
    "financial": re.compile(
        r"\b(refund|payment|invoice|transaction|wire transfer|bank)\b",
        re.I,
    ),
}


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def compute_entropy(data: bytes) -> float:
    """Shannon entropy of byte sequence."""
    if not data:
        return 0.0
    counts = Counter(data)
    length = len(data)
    return -sum((c / length) * math.log2(c / length) for c in counts.values())


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def md5_of(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def describe_file_signature(head: bytes) -> Optional[str]:
    """Match magic bytes to a known file type."""
    for sig, desc in FILE_SIGNATURES.items():
        if head[: len(sig)] == sig:
            return desc
    return None


def _safe_get(url: str, **kwargs: Any) -> Optional[requests.Response]:
    try:
        return requests.get(url, timeout=10, **kwargs)
    except requests.RequestException:
        return None


# ---------------------------------------------------------------------------
# Tool 1: Email header analysis
# ---------------------------------------------------------------------------


@mcp.tool()
def email_analysis(raw_email: str) -> str:
    """Analyze an email's headers and body for phishing indicators.

    Pass the full RFC-822 email text (headers + body). Returns a JSON string
    summarizing: parsing result, authentication results (SPF/DKIM/DMARC
    mentions in Received/Authentication-Results), suspicious header patterns,
    body phishing-keyword hits, and a risk verdict.
    """
    try:
        msg = email.message_from_string(raw_email, policy=email.policy.compat32)
    except Exception as e:
        return json.dumps({"error": f"Failed to parse email: {e}"})

    headers: dict[str, Any] = {}
    for key in ("From", "To", "Subject", "Date", "Reply-To", "Return-Path",
                "Received", "Authentication-Results", "DKIM-Signature",
                "X-Mailer", "Message-ID", "MIME-Version"):
        val = msg.get(key)
        if val:
            headers[key] = str(val)

    # --- From / Reply-To mismatch ---
    from_name, from_addr = parseaddr(str(msg.get("From", "")))
    reply_name, reply_addr = parseaddr(str(msg.get("Reply-To", "")))
    from_mismatch = bool(reply_addr and reply_addr.lower() != from_addr.lower())

    # --- SPF / DKIM / DMARC results ---
    auth_results = str(msg.get("Authentication-Results", ""))
    spf = None
    dkim = None
    dmarc = None
    if auth_results:
        for token in auth_results.replace("\n", " ").split(";"):
            token = token.strip()
            if token.lower().startswith("spf="):
                spf = token.split("=", 1)[1].strip().lower()
            elif token.lower().startswith("dkim="):
                dkim = token.split("=", 1)[1].strip().lower()
            elif token.lower().startswith("dmarc="):
                dmarc = token.split("=", 1)[1].strip().lower()

    # --- Body analysis ---
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() in ("text/plain", "text/html"):
                try:
                    body += part.get_content()
                except Exception:
                    body += str(part.get_payload(decode=True) or "")
    else:
        try:
            body = msg.get_content()
        except Exception:
            body = str(msg.get_payload(decode=True) or "")

    body_lower = body.lower()
    keyword_hits: dict[str, list[str]] = {}
    for name, pattern in PHISHING_PATTERNS.items():
        matches = pattern.findall(body)
        if matches:
            keyword_hits[name] = list(set(matches))

    # --- Suspicious links (href with mismatched display text) ---
    href_pattern = re.compile(r'href=["\']([^"\']+)["\']', re.I)
    display_pattern = re.compile(r'>([^<]+)</a>', re.I)
    mismatched_links: list[dict[str, str]] = []
    for href_match, disp_match in zip(href_pattern.finditer(body),
                                      display_pattern.finditer(body)):
        url = href_match.group(1)
        disp = disp_match.group(1).strip()
        if disp.startswith("http") and url != disp:
            mismatched_links.append({"display": disp, "href": url})

    # --- Risk scoring ---
    risk_score = 0
    reasons: list[str] = []
    if from_mismatch:
        risk_score += 2
        reasons.append("From/Reply-To mismatch")
    if spf in ("fail", "softfail"):
        risk_score += 2
        reasons.append(f"SPF {spf}")
    if spf == "none":
        risk_score += 1
        reasons.append("No SPF record")
    if dkim == "fail":
        risk_score += 2
        reasons.append(f"DKIM {dkim}")
    if dkim == "none":
        risk_score += 1
        reasons.append("No DKIM signature")
    if dmarc == "fail":
        risk_score += 2
        reasons.append("DMARC fail")
    if keyword_hits:
        risk_score += len(keyword_hits)
        reasons.append(f"Phishing keywords: {', '.join(keyword_hits.keys())}")
    if mismatched_links:
        risk_score += 2
        reasons.append(f"{len(mismatched_links)} mismatched links in body")

    verdict = "low"
    if risk_score >= 4:
        verdict = "high"
    elif risk_score >= 2:
        verdict = "medium"

    result = {
        "parsed": bool(headers),
        "headers": headers,
        "from_mismatch": from_mismatch,
        "authentication": {
            "spf": spf,
            "dkim": dkim,
            "dmarc": dmarc,
            "raw": auth_results or None,
        },
        "body_keyword_hits": keyword_hits,
        "suspicious_links": mismatched_links,
        "risk_score": risk_score,
        "risk_reasons": reasons,
        "verdict": verdict,
    }
    return json.dumps(result, indent=2, default=str)


# ---------------------------------------------------------------------------
# Tool 2: File analysis
# ---------------------------------------------------------------------------


@mcp.tool()
def file_analysis(file_path: str) -> str:
    """Analyze a file on disk for metadata, hashes, and suspicious indicators.

    Returns: size, MIME type (from magic bytes), SHA-256/MD5 hashes, entropy,
    whether it is executable, and a risk verdict based on heuristics.
    """
    path = Path(file_path)
    if not path.exists():
        return json.dumps({"error": f"File not found: {file_path}"})
    if not path.is_file():
        return json.dumps({"error": f"Not a regular file: {file_path}"})

    stat = path.stat()
    data = path.read_bytes()
    size = stat.st_size

    head = data[:64]
    file_type = describe_file_signature(head)
    entropy = compute_entropy(data)

    hashes = {
        "md5": md5_of(data),
        "sha256": sha256_of(data),
    }

    # Check against known-bad hashes
    known_bad = hashes["md5"] in KNOWN_BAD_HASHES or hashes["sha256"] in KNOWN_BAD_HASHES

    # Entropy heuristic: packed/encrypted files often > 7.5
    high_entropy = entropy > 7.5

    # Is it an executable?
    is_executable = file_type in ("Windows executable", "ELF executable") or (
        os.name == "nt" and path.suffix.lower() in (".exe", ".dll", ".scr", ".bat", ".cmd", ".ps1")
    )

    # Double-extension trick (e.g., "invoice.pdf.exe")
    name = path.name
    parts = name.split(".")
    double_ext = len(parts) > 2 and parts[-1].lower() in (
        "exe", "dll", "scr", "bat", "cmd", "ps1", "vbs", "js", "wsf", "msi"
    )

    # --- Risk verdict ---
    risk_score = 0
    reasons: list[str] = []
    if known_bad:
        risk_score += 5
        reasons.append("Hash matches known-malware list")
    if high_entropy:
        risk_score += 2
        reasons.append(f"High entropy ({entropy:.2f}) — possibly packed/encrypted")
    if is_executable:
        risk_score += 1
        reasons.append("Executable file type")
    if double_ext:
        risk_score += 3
        reasons.append("Double file extension (evasion technique)")

    verdict = "low"
    if risk_score >= 4:
        verdict = "high"
    elif risk_score >= 2:
        verdict = "medium"

    result = {
        "file_path": str(path),
        "file_name": name,
        "size_bytes": size,
        "file_type": file_type,
        "extension": path.suffix.lower(),
        "entropy": round(entropy, 4),
        "hashes": hashes,
        "indicators": {
            "known_bad_hash": known_bad,
            "high_entropy": high_entropy,
            "is_executable": is_executable,
            "double_extension": double_ext,
        },
        "risk_score": risk_score,
        "risk_reasons": reasons,
        "verdict": verdict,
    }
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Tool 3: URL analysis
# ---------------------------------------------------------------------------


@mcp.tool()
def url_analysis(url: str) -> str:
    """Analyze a URL for phishing / malware indicators.

    Checks: scheme, punycode, IP literal, suspicious keywords, URL length,
    redirect chains, known-suspicious TLD, and DNS resolution status.
    Returns a JSON risk report.
    """
    if not re.match(r"^https?://", url, re.I):
        url = "http://" + url

    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    scheme = parsed.scheme.lower()

    indicators: dict[str, Any] = {}

    # Punycode detection
    indicators["is_punycode"] = "xn--" in hostname.lower()

    # IP literal in URL
    is_ip = False
    try:
        ipaddress.ip_address(hostname)
        is_ip = True
    except ValueError:
        pass
    indicators["ip_literal"] = is_ip

    # HTTPS?
    indicators["uses_https"] = scheme == "https"

    # URL length heuristic
    indicators["long_url"] = len(url) > 75

    # Suspicious TLD
    tld = hostname.rsplit(".", 1)[-1].lower() if "." in hostname else ""
    indicators["suspicious_tld"] = tld in SUSPICIOUS_TLDS

    # Count subparts
    indicators["subdomain_count"] = hostname.count(".")

    # Suspicious keywords in URL
    url_lower = url.lower()
    found_keywords = [kw for kw in URL_SUSPICIOUS_KEYWORDS if kw in url_lower]
    indicators["suspicious_keywords"] = found_keywords

    # @ sign trick (username in URL)
    indicators["has_at_sign"] = "@" in parsed.path or "@" in parsed.netloc

    # Multiple redirects (follow up to 3 hops)
    redirect_count = 0
    final_url = url
    try:
        resp = requests.get(url, allow_redirects=True, timeout=10)
        redirect_count = len(resp.history)
        final_url = resp.url
    except requests.RequestException:
        pass
    indicators["redirect_count"] = redirect_count
    indicators["final_url"] = final_url

    # DNS resolution check
    dns_resolvable = False
    try:
        if not is_ip:
            socket.getaddrinfo(hostname, None)
            dns_resolvable = True
    except socket.gaierror:
        pass
    indicators["dns_resolvable"] = dns_resolvable

    # --- Risk scoring ---
    risk_score = 0
    reasons: list[str] = []
    if indicators["is_punycode"]:
        risk_score += 3
        reasons.append("Punycode domain (possible homograph attack)")
    if indicators["ip_literal"]:
        risk_score += 2
        reasons.append("IP address used instead of domain name")
    if not indicators["uses_https"]:
        risk_score += 1
        reasons.append("Not using HTTPS")
    if indicators["suspicious_tld"]:
        risk_score += 2
        reasons.append(f"Suspicious TLD: .{tld}")
    if indicators["long_url"]:
        risk_score += 1
        reasons.append("Unusually long URL")
    if indicators["has_at_sign"]:
        risk_score += 3
        reasons.append("@ sign in URL (credential-in-URL trick)")
    if found_keywords:
        risk_score += min(len(found_keywords), 3)
        reasons.append(f"Suspicious keywords: {', '.join(found_keywords)}")
    if redirect_count > 2:
        risk_score += 2
        reasons.append(f"Excessive redirects ({redirect_count})")
    if not dns_resolvable:
        risk_score += 2
        reasons.append("Domain does not resolve (NXDOMAIN)")

    verdict = "low"
    if risk_score >= 5:
        verdict = "high"
    elif risk_score >= 3:
        verdict = "medium"

    result = {
        "input_url": url,
        "normalized_url": final_url,
        "hostname": hostname,
        "scheme": scheme,
        "tld": tld,
        "indicators": indicators,
        "risk_score": risk_score,
        "risk_reasons": reasons,
        "verdict": verdict,
    }
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Tool 4: Domain analysis
# ---------------------------------------------------------------------------


@mcp.tool()
def domain_analysis(domain: str) -> str:
    """Analyze a domain for security posture and potential issues.

    Queries: DNS A/AAAA/MX/NS/TXT records, extracts SPF & DMARC policies,
    checks DNSSEC (via DNSKEY), domain age heuristic (via RDAP if available),
    and reverse DNS. Returns a JSON report.
    """
    domain = domain.strip().lower()
    # Strip scheme if included
    domain = re.sub(r"^https?://", "", domain).split("/")[0]

    records: dict[str, Any] = {}

    # --- DNS record collection ---
    for rtype in ("A", "AAAA", "MX", "NS", "TXT", "SOA", "DNSKEY"):
        try:
            answers = dns.resolver.resolve(domain, rtype, lifetime=5)
            records[rtype] = [str(r) for r in answers]
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN,
                dns.resolver.NoNameservers, dns.exception.Timeout):
            records[rtype] = []
        except Exception as e:
            records[rtype] = [f"error: {e}"]

    # --- SPF extraction ---
    spf_record = None
    for txt in records.get("TXT", []):
        if "v=spf1" in txt:
            spf_record = txt
            break

    # --- DMARC lookup ---
    dmarc_record = None
    try:
        dmarc_answers = dns.resolver.resolve(f"_dmarc.{domain}", "TXT", lifetime=5)
        for r in dmarc_answers:
            txt = str(r)
            if "v=DMARC1" in txt:
                dmarc_record = txt
                break
    except Exception:
        pass

    # --- Reverse DNS on first A record ---
    rdns: list[str] = []
    for a in records.get("A", [])[:3]:
        try:
            rdns.append(socket.gethostbyaddr(a)[0])
        except (socket.herror, socket.gaierror):
            pass

    # --- Domain age via RDAP (ICANN) ---
    domain_age_days: Optional[int] = None
    registrar: Optional[str] = None
    rdap_url = f"https://rdap.org/domain/{domain}"
    resp = _safe_get(rdap_url, headers={"Accept": "application/json"})
    if resp and resp.status_code == 200:
        try:
            rdap_data = resp.json()
            registrar = rdap_data.get("entities", [{}])[0].get("vcardArray", [[], []])[1][0][3] if rdap_data.get("entities") else None
            for event in rdap_data.get("events", []):
                if event.get("eventAction") == "registration":
                    created = event.get("eventDate", "")
                    if created:
                        created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                        domain_age_days = (datetime.now(timezone.utc) - created_dt).days
                    break
        except (KeyError, IndexError, ValueError):
            pass

    # --- Indicator assessment ---
    indicators: dict[str, Any] = {
        "has_spf": spf_record is not None,
        "has_dmarc": dmarc_record is not None,
        "has_dnssec": bool(records.get("DNSKEY")),
        "has_mx": bool(records.get("MX")),
        "reverse_dns_matches": rdns,
    }

    # DMARC policy check
    dmarc_policy = None
    if dmarc_record:
        m = re.search(r"p=(\w+)", dmarc_record)
        if m:
            dmarc_policy = m.group(1).lower()
    indicators["dmarc_policy"] = dmarc_policy

    # --- Risk scoring ---
    risk_score = 0
    reasons: list[str] = []
    if not indicators["has_spf"]:
        risk_score += 2
        reasons.append("No SPF record")
    if not indicators["has_dmarc"]:
        risk_score += 2
        reasons.append("No DMARC record")
    elif dmarc_policy in ("none", "p=none"):
        risk_score += 1
        reasons.append("DMARC policy is 'none' (monitoring only)")
    if not indicators["has_dnssec"]:
        risk_score += 1
        reasons.append("DNSSEC not enabled")
    if domain_age_days is not None and domain_age_days < 30:
        risk_score += 3
        reasons.append(f"Very recently registered ({domain_age_days} days old)")
    elif domain_age_days is not None and domain_age_days < 90:
        risk_score += 1
        reasons.append(f"Recently registered ({domain_age_days} days old)")
    if not records.get("A"):
        risk_score += 1
        reasons.append("No A record (domain may be parked or sinkholed)")

    verdict = "low"
    if risk_score >= 5:
        verdict = "high"
    elif risk_score >= 3:
        verdict = "medium"

    result = {
        "domain": domain,
        "dns_records": records,
        "spf_record": spf_record,
        "dmarc_record": dmarc_record,
        "dmarc_policy": dmarc_policy,
        "registrar": registrar,
        "domain_age_days": domain_age_days,
        "reverse_dns": rdns,
        "indicators": indicators,
        "risk_score": risk_score,
        "risk_reasons": reasons,
        "verdict": verdict,
    }
    return json.dumps(result, indent=2, default=str)


# ---------------------------------------------------------------------------
# Tool 5: IP reputation analysis
# ---------------------------------------------------------------------------


@mcp.tool()
def ip_analysis(ip: str) -> str:
    """Analyze an IP address for reputation and threat indicators.

    Queries: AbuseIPDB (if API key set), RDAP for network/geolocation,
    reverse DNS, and checks common blacklists via DNSBL. Returns a JSON report.
    """
    try:
        addr = ipaddress.ip_address(ip.strip())
    except ValueError:
        return json.dumps({"error": f"Invalid IP address: {ip}"})

    result: dict[str, Any] = {"ip": str(addr), "version": addr.version}

    # --- RDAP lookup ---
    rdap_info: dict[str, Any] = {}
    resp = _safe_get(f"https://rdap.org/ip/{addr}", headers={"Accept": "application/json"})
    if resp and resp.status_code == 200:
        try:
            rdap_data = resp.json()
            rdap_info["network"] = rdap_data.get("name")
            rdap_info["country"] = rdap_data.get("country")
            rdap_info["cidr"] = rdap_data.get("cidr0_cidrs", [{}])[0].get("v4prefix") if rdap_data.get("cidr0_cidrs") else None
            # Events
            for event in rdap_data.get("events", []):
                if event.get("eventAction") == "registration":
                    rdap_info["last_changed"] = event.get("eventDate")
            # Entities
            entities = rdap_data.get("entities", [])
            if entities:
                vcard = entities[0].get("vcardArray", [[], []])[1]
                for item in vcard:
                    if item[0] == "fn":
                        rdap_info["org"] = item[3]
        except (KeyError, IndexError, ValueError):
            pass
    result["rdap"] = rdap_info

    # --- Reverse DNS ---
    try:
        result["reverse_dns"] = socket.gethostbyaddr(str(addr))[0]
    except (socket.herror, socket.gaierror):
        result["reverse_dns"] = None

    # --- AbuseIPDB (optional) ---
    abuse_score = None
    abuse_reports = None
    abuse_country = None
    if ABUSEIPDB_API_KEY and addr.version == 4:
        headers = {"Key": ABUSEIPDB_API_KEY, "Accept": "application/json"}
        params = {"ipAddress": str(addr), "maxAgeInDays": 90}
        resp = _safe_get("https://api.abuseipdb.com/api/v2/check",
                         headers=headers, params=params)
        if resp and resp.status_code == 200:
            try:
                data = resp.json().get("data", {})
                abuse_score = data.get("abuseConfidenceScore")
                abuse_reports = data.get("totalReports")
                abuse_country = data.get("countryCode")
            except (KeyError, ValueError):
                pass
    result["abuseipdb"] = {
        "abuse_score": abuse_score,
        "total_reports": abuse_reports,
        "country": abuse_country,
    }

    # --- DNSBL check (Spamhaus Zen) ---
    is_blacklisted = False
    if addr.version == 4:
        reversed_ip = ".".join(str(addr).split(".")[::-1])
        try:
            socket.gethostbyname(f"{reversed_ip}.zen.spamhaus.org")
            is_blacklisted = True
        except socket.gaierror:
            pass
    result["dnsbl_blacklisted"] = is_blacklisted

    # --- Risk scoring ---
    risk_score = 0
    reasons: list[str] = []
    if addr.is_private:
        reasons.append("Private/RFC1918 address")
    if is_blacklisted:
        risk_score += 5
        reasons.append("Listed in Spamhaus Zen DNSBL")
    if abuse_score is not None:
        if abuse_score >= 75:
            risk_score += 4
            reasons.append(f"High abuse confidence: {abuse_score}")
        elif abuse_score >= 50:
            risk_score += 2
            reasons.append(f"Moderate abuse confidence: {abuse_score}")
    if abuse_reports and abuse_reports > 10:
        risk_score += 2
        reasons.append(f"Reported {abuse_reports} times")

    verdict = "low"
    if risk_score >= 5:
        verdict = "high"
    elif risk_score >= 3:
        verdict = "medium"

    result["risk_score"] = risk_score
    result["risk_reasons"] = reasons
    result["verdict"] = verdict
    return json.dumps(result, indent=2, default=str)


# ---------------------------------------------------------------------------
# Tool 6: Hash analysis
# ---------------------------------------------------------------------------


@mcp.tool()
def hash_analysis(hash_value: str) -> str:
    """Analyze a file hash against known-malware databases.

    Queries: VirusTotal (if VT_API_KEY set), local blocklist, and computes
    what kind of hash it is by length. Returns a JSON report with detections.
    """
    hash_clean = hash_value.strip().lower()
    hash_len = len(hash_clean)

    # Determine hash type by length
    hash_type: Optional[str] = None
    if hash_len == 32:
        hash_type = "md5"
    elif hash_len == 40:
        hash_type = "sha1"
    elif hash_len == 64:
        hash_type = "sha256"
    elif hash_len == 128:
        hash_type = "sha512"

    result: dict[str, Any] = {
        "input_hash": hash_clean,
        "hash_type": hash_type,
        "hash_length": hash_len,
    }

    # --- Local blocklist check ---
    is_known_bad = hash_clean in KNOWN_BAD_HASHES
    result["local_blocklist_match"] = is_known_bad

    # --- VirusTotal lookup ---
    vt_data: dict[str, Any] = {}
    if VT_API_KEY:
        headers = {"x-apikey": VT_API_KEY}
        resp = _safe_get(f"https://www.virustotal.com/api/v3/files/{hash_clean}",
                         headers=headers)
        if resp and resp.status_code == 200:
            try:
                attr = resp.json().get("data", {}).get("attributes", {})
                stats = attr.get("last_analysis_stats", {})
                vt_data["malicious"] = stats.get("malicious", 0)
                vt_data["suspicious"] = stats.get("suspicious", 0)
                vt_data["undetected"] = stats.get("undetected", 0)
                vt_data["harmless"] = stats.get("harmless", 0)
                vt_data["names"] = attr.get("names", [])[:5]
                vt_data["type_description"] = attr.get("type_description")
                vt_data["size"] = attr.get("size")
                vt_data["first_submission"] = attr.get("first_submission_date")
                vt_data["popular_threat_label"] = attr.get("popular_threat_label")
            except (KeyError, ValueError):
                pass
        elif resp and resp.status_code == 404:
            vt_data["found"] = False
        elif resp:
            vt_data["error"] = f"HTTP {resp.status_code}"
    else:
        vt_data["note"] = "VT_API_KEY not set — skipping VirusTotal lookup"
    result["virustotal"] = vt_data

    # --- Risk scoring ---
    risk_score = 0
    reasons: list[str] = []
    if is_known_bad:
        risk_score += 5
        reasons.append("Matches known-malware hash in local blocklist")
    if vt_data.get("malicious", 0) > 0:
        risk_score += min(vt_data["malicious"], 5)
        reasons.append(f"VirusTotal: {vt_data['malicious']} engines flagged as malicious")
    if vt_data.get("suspicious", 0) > 0:
        risk_score += 1
        reasons.append(f"VirusTotal: {vt_data['suspicious']} engines flagged as suspicious")

    verdict = "low"
    if risk_score >= 4:
        verdict = "high"
    elif risk_score >= 2:
        verdict = "medium"

    result["risk_score"] = risk_score
    result["risk_reasons"] = reasons
    result["verdict"] = verdict
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
