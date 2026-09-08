"""
OSINT MCP Server
Provides Open Source Intelligence tools via the Model Context Protocol.
All tools return structured JSON for easy agent consumption.
"""

import json
import hashlib
import random
import re
from datetime import datetime, timedelta
from typing import Any

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("osint-server")


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _fake_ip(seed: str) -> str:
    h = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
    return f"{(h >> 24) & 0xff}.{(h >> 16) & 0xff}.{(h >> 8) & 0xff}.{h & 0xff}"


def _fake_subdomain(base: str, seed: str) -> str:
    prefixes = ["www", "mail", "api", "dev", "staging", "admin", "portal",
                "vpn", "cdn", "blog", "shop", "app", "secure", "test", "old"]
    h = int(hashlib.md5(seed.encode()).hexdigest()[:4], 16)
    return f"{prefixes[h % len(prefixes)]}.{base}"


@mcp.tool()
def shodan_search(query: str, limit: int = 10) -> str:
    """Simulate Shodan search for exposed services."""
    results = []
    port_map = {
        "apache": 80, "nginx": 443, "ssh": 22, "ftp": 21,
        "mysql": 3306, "rdp": 3389, "telnet": 23, "smtp": 25,
    }
    banners = {
        80: "HTTP/1.1 200 OK\r\nServer: Apache/2.4.41",
        443: "HTTP/1.1 200 OK\r\nServer: nginx/1.18.0",
        22: "SSH-2.0-OpenSSH_7.6p1",
        3389: "RDP Protocol Negotiation",
        3306: "5.7.33-0ubuntu0.18.04.1",
        21: "220 (vsFTPd 3.0.3)",
        25: "220 mail.example.com ESMTP Postfix",
        8080: "HTTP/1.1 401 Unauthorized",
        8443: "HTTP/1.1 302 Found",
    }
    countries = ["US", "DE", "CN", "RU", "GB", "FR", "BR", "IN", "JP", "AU"]
    orgs = ["Cloudflare", "AWS", "DigitalOcean", "Hetzner", "OVH",
            "Linode", "Azure", "Google Cloud"]

    for i in range(min(limit, 50)):
        port = 80
        for key, p in port_map.items():
            if key in query.lower():
                port = p
                break
        else:
            port = random.choice([80, 443, 22, 3389, 8080, 8443])

        results.append({
            "ip": _fake_ip(f"{query}-{i}"),
            "port": port,
            "hostname": f"host-{i}.{query.replace(':', '-')}.net",
            "org": random.choice(orgs),
            "country": random.choice(countries),
            "banner": banners.get(port, "Unknown"),
            "ssl": port in (443, 8443),
            "last_seen": _now_iso(),
        })

    return json.dumps({
        "tool": "shodan_search",
        "query": query,
        "total_found": len(results) + random.randint(0, 500),
        "results_returned": len(results),
        "timestamp": _now_iso(),
        "results": results,
    }, indent=2)


@mcp.tool()
def haveibeenpwned(email: str) -> str:
    """Simulate HIBP breach check for an email address."""
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return json.dumps({
            "tool": "haveibeenpwned",
            "error": "Invalid email format",
            "email": email,
        }, indent=2)

    breaches_pool = [
        {"name": "Adobe", "year": 2013, "records": 152445165,
         "data": ["Email addresses", "Passwords", "Usernames"]},
        {"name": "LinkedIn", "year": 2012, "records": 164661595,
         "data": ["Email addresses", "Passwords"]},
        {"name": "Dropbox", "year": 2012, "records": 68648009,
         "data": ["Email addresses", "Passwords"]},
        {"name": "Canva", "year": 2019, "records": 137272116,
         "data": ["Email addresses", "Passwords", "Names"]},
        {"name": "Twitter", "year": 2023, "records": 20550516,
         "data": ["Email addresses", "Usernames"]},
        {"name": "Equifax", "year": 2017, "records": 147900000,
         "data": ["Names", "SSNs", "DOBs", "Addresses"]},
    ]

    h = int(hashlib.sha1(email.lower().encode()).hexdigest()[:8], 16)
    num_breaches = (h % 4) + 1
    selected = [breaches_pool[(h + i * 7) % len(breaches_pool)] for i in range(num_breaches)]

    pastes = []
    if h % 3 == 0:
        pastes.append({
            "source": "Pastebin",
            "date": "2022-08-14",
            "title": f"Leak_{h % 10000}",
            "email_count": random.randint(1, 50),
        })

    return json.dumps({
        "tool": "haveibeenpwned",
        "email": email,
        "found": len(selected) > 0,
        "breach_count": len(selected),
        "breaches": selected,
        "pastes": pastes,
        "recommendation": "Change passwords immediately. Enable 2FA everywhere.",
        "timestamp": _now_iso(),
    }, indent=2)


@mcp.tool()
def theharvester(domain: str, sources: str = "all", limit: int = 50) -> str:
    """Simulate theHarvester email and subdomain harvesting."""
    source_list = [s.strip() for s in sources.split(",")] if sources != "all" else [
        "bing", "duckduckgo", "google", "linkedin", "virustotal", "crtsh",
    ]

    emails = []
    people = ["john", "jane", "admin", "info", "support", "sales",
              "contact", "security", "noc", "billing"]
    for i in range(min(limit, len(people))):
        emails.append(f"{people[i]}@{domain}")

    hosts = []
    for i in range(min(limit, 20)):
        sub = _fake_subdomain(domain, f"{domain}-sub-{i}")
        hosts.append({"host": sub, "ip": _fake_ip(sub)})

    urls = [
        f"https://www.{domain}", f"https://mail.{domain}",
        f"https://api.{domain}", f"https://admin.{domain}",
        f"https://blog.{domain}",
    ]

    return json.dumps({
        "tool": "theharvester",
        "domain": domain,
        "sources_used": source_list,
        "emails_found": emails,
        "hosts_found": hosts,
        "ips_found": list({h["ip"] for h in hosts}),
        "urls_found": urls,
        "total_results": len(emails) + len(hosts) + len(urls),
        "timestamp": _now_iso(),
    }, indent=2)


@mcp.tool()
def amass(domain: str, mode: str = "enum") -> str:
    """Simulate Amass subdomain enumeration."""
    prefixes = ["www", "api", "mail", "dev", "staging", "admin", "portal",
                "vpn", "cdn", "blog", "shop", "app", "secure", "test", "old",
                "internal", "git", "jenkins", "grafana", "kibana", "db",
                "redis", "mongo", "elastic", "vault", "consul", "ldap",
                "sso", "auth", "oauth", "wiki", "docs", "confluence", "jira",
                "gitlab", "ci", "build", "deploy", "registry", "k8s",
                "nagios", "splunk", "datadog", "prometheus", "alertmanager",
                "pagerduty", "slack", "zoom", "terraform", "ansible"]

    discovered = []
    seen = set()
    count = min(30, 10 + int(hashlib.md5(domain.encode()).hexdigest()[:2], 16) % 20)

    for i in range(count):
        sub = _fake_subdomain(domain, f"{domain}-amass-{i}")
        if sub not in seen:
            seen.add(sub)
            discovered.append({
                "name": sub,
                "addresses": [{"addr": _fake_ip(sub)}],
                "tag": random.choice(["api", "default", "cdn", "cloud"]),
            })

    cname_records = []
    for d in discovered[:5]:
        cname_records.append({
            "query": d["name"],
            "name": d["name"],
            "response": f"{d['name']}.cdn.cloudflare.net",
        })

    whois = {
        "domain": domain,
        "registrar": random.choice(["GoDaddy", "Namecheap", "Cloudflare", "AWS"]),
        "created": "2010-03-15",
        "expires": "2027-03-15",
        "nameservers": ["ns1.example.com", "ns2.example.com"],
    }

    return json.dumps({
        "tool": "amass",
        "domain": domain,
        "mode": mode,
        "total_found": len(discovered),
        "subdomains": discovered,
        "dns_records": {
            "cname": cname_records,
            "whois": whois,
        },
        "timestamp": _now_iso(),
    }, indent=2)


@mcp.tool()
def censys(query: str, limit: int = 25) -> str:
    """Simulate Censys certificate search."""
    results = []
    for i in range(min(limit, 50)):
        domain = f"{query.replace(' ', '-').replace('.', '-')}-{i}.com"
        ip = _fake_ip(f"censys-{query}-{i}")
        not_before = datetime(2023, 1, 1) + timedelta(days=random.randint(0, 365))
        not_after = not_before + timedelta(days=random.choice([90, 180, 365, 397]))

        results.append({
            "ip": ip,
            "services": [
                {"port": 443, "service_name": "HTTPS",
                 "certificate": f"-----BEGIN CERTIFICATE-----\nMIID{i:08x}...\n{name:=<20}\n-----END CERTIFICATE-----"},
            ],
            "certificates": {
                "parsed": {
                    "subject_dn": f"CN={domain}",
                    "issuer_dn": "CN=Let's Encrypt Authority X3",
                    "serial_number": hashlib.sha256(f"{domain}-{i}".encode()).hexdigest()[:32],
                    "validity": {
                        "start": not_before.isoformat(),
                        "end": not_after.isoformat(),
                    },
                    "names": [domain, f"*.{domain}"],
                    "signature_algorithm": "SHA256-RSA",
                },
                "fingerprint_sha256": hashlib.sha256(f"{domain}-{i}".encode()).hexdigest(),
                "fingerprint_sha1": hashlib.sha1(f"{domain}-{i}".encode()).hexdigest(),
            },
            "location": {
                "country": random.choice(["US", "DE", "JP", "GB", "FR", "CA"]),
                "continent": random.choice(["North America", "Europe", "Asia"]),
            },
            "autonomous_system": {
                "name": random.choice(["AS15169 Google", "AS16509 Amazon", "AS13335 Cloudflare",
                                      "AS14061 DigitalOcean", "AS24940 Hetzner"]),
                "asn": random.randint(10000, 60000),
            },
        })

    return json.dumps({
        "tool": "censys",
        "query": query,
        "total_hits": len(results) + random.randint(0, 10000),
        "results_returned": len(results),
        "timestamp": _now_iso(),
        "results": results,
    }, indent=2)


if __name__ == "__main__":
    mcp.run()
