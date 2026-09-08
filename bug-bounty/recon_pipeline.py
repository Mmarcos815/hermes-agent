#!/usr/bin/env python3
"""
Bug Bounty Recon Pipeline

Automated reconnaissance for bug bounty hunting.
Accepts a target domain, runs all recon modules, outputs structured JSON.

Modules:
    1. subdomain_enum   - Certificate transparency logs (crt.sh)
    2. port_scan        - TCP connect scan on common ports
    3. tech_detect      - HTTP header analysis
    4. wayback           - Wayback Machine historical URLs
    5. git_leaks         - Exposed .git directories

Usage:
    python recon_pipeline.py <domain> [--timeout PORT_TIMEOUT] [--top-ports N] [--output FILE]

Example:
    python recon_pipeline.py example.com --output report.json

Only uses Python standard library (urllib, socket, ssl, json, etc.).
"""

import argparse
import json
import re
import socket
import ssl
import sys
import time
import urllib.parse
import urllib.request
from collections import OrderedDict

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMMON_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 111, 135, 139,
    143, 443, 445, 465, 587, 993, 995, 1433, 1521,
    2000, 3000, 3306, 3389, 5000, 5060, 5432, 5601,
    5900, 6379, 7001, 8000, 8008, 8080, 8081, 8443,
    8888, 9000, 9090, 9200, 9300, 10000, 11211, 27017,
]

USER_AGENT = "ReconPipeline/1.0 (Bug Bounty Scanner)"
REQUEST_TIMEOUT = 10  # seconds for HTTP requests
CONNECT_TIMEOUT = 3    # seconds for TCP connect

# ---------------------------------------------------------------------------
# HTTP helpers (no requests library — pure urllib)
# ---------------------------------------------------------------------------

def http_request(url, follow_redirects=False, headers=None):
    """Make an HTTP request and return (status_code, headers_dict, body_str)."""
    if headers is None:
        headers = {}
    headers.setdefault("User-Agent", USER_AGENT)
    headers.setdefault("Accept", "*/*")

    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        if follow_redirects:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            response = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=context)
            return response.getcode(), dict(response.headers), response.read().decode("utf-8", errors="replace")
        else:
            # Don't follow redirects manually
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            response = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=context)
            return response.getcode(), dict(response.headers), response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), ""
    except Exception:
        return None, {}, ""


def https_request(host, path="/"):
    """Simple HTTPS GET returning (status, headers_dict, body_str)."""
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        conn = urllib.request.HTTPSConnection(host, timeout=REQUEST_TIMEOUT, context=context)
        conn.request("GET", path, headers={"User-Agent": USER_AGENT, "Host": host})
        resp = conn.getresponse()
        body = resp.read().decode("utf-8", errors="replace")
        return resp.status, dict(resp.getheaders()), body
    except Exception:
        return None, {}, ""

# ---------------------------------------------------------------------------
# 1. Subdomain Enumeration — crt.sh (Certificate Transparency)
# ---------------------------------------------------------------------------

def subdomain_enum(domain, max_results=500):
    """
    Query crt.sh for certificate transparency logs to find subdomains.
    Returns sorted list of unique subdomain strings.
    """
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    print(f"  [*] Querying crt.sh for subdomains of {domain}...")

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, timeout=30, context=context) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [!] crt.sh query failed: {e}")
        return []

    subdomains = set()
    for entry in data:
        names = entry.get("name_value", "").split("\n")
        for name in names:
            name = name.strip().lower()
            # Remove wildcard prefix
            if name.startswith("*."):
                name = name[2:]
            if name.endswith(domain) and "." in name:
                subdomains.add(name)

    result = sorted(subdomains)[:max_results]
    print(f"  [+] Found {len(result)} subdomains")
    return result

# ---------------------------------------------------------------------------
# 2. Port Scan — TCP Connect
# ---------------------------------------------------------------------------

def port_scan(target, ports=None):
    """
    TCP connect scan on common ports.
    Returns dict of {port: banner_or_empty_string}.
    """
    if ports is None:
        ports = COMMON_PORTS

    print(f"  [*] Scanning {target} on {len(ports)} ports...")
    open_ports = {}

    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(CONNECT_TIMEOUT)
        try:
            result = sock.connect_ex((target, port))
            if result == 0:
                # Try to grab a short banner
                banner = ""
                try:
                    sock.settimeout(1)
                    banner = sock.recv(128).decode("utf-8", errors="replace").strip()
                except Exception:
                    pass
                open_ports[port] = banner
                print(f"  [+] Port {port} open" + (f" — {banner[:60]}" if banner else ""))
        except Exception:
            pass
        finally:
            sock.close()

    print(f"  [+] {len(open_ports)} open ports found")
    return open_ports

# ---------------------------------------------------------------------------
# 3. Technology Detection — HTTP Header Analysis
# ---------------------------------------------------------------------------

# Mapping of header patterns to technology names
TECH_PATTERNS = [
    (r"cloudflare", "Cloudflare"),
    (r"akamai", "Akamai CDN"),
    (r"amazon\s*cloudfront", "Amazon CloudFront"),
    (r"fastly", "Fastly CDN"),
    (r"nginx", "Nginx"),
    (r"apache", "Apache"),
    (r"iis", "Microsoft IIS"),
    (r"litespeed", "LiteSpeed"),
    (r"express", "Express.js"),
    (r"php", "PHP"),
    (r"asp\.net", "ASP.NET"),
    (r"ruby", "Ruby"),
    (r"python", "Python"),
    (r"wix", "Wix"),
    (r"shopify", "Shopify"),
    (r"wordpress", "WordPress"),
    (r"drupal", "Drupal"),
    (r"joomla", "Joomla"),
    (r"squarespace", "Squarespace"),
    (r"webflow", "Webflow"),
    (r"vercel", "Vercel"),
    (r"netlify", "Netlify"),
    (r"heroku", "Heroku"),
    (r"google\s*cloud\s*load\s*balancing", "Google Cloud LB"),
    (r"awselb|elb", "AWS ELB"),
    (r"hsts|strict-transport-security", "HSTS Enabled"),
    (r"x-frame-options", "X-Frame-Options"),
    (r"x-content-type-options", "X-Content-Type-Options"),
    (r"content-security-policy", "Content Security Policy"),
    (r"x-powered-by:\s*([^\s,;]+)", None),  # special handling below
]

# Headers known to reveal tech
TECH_HEADERS = [
    "server", "x-powered-by", "x-aspnet-version", "x-aspnetmvc-version",
    "x-generator", "via", "x-served-by", "x-backend-server",
    "x-amz-cf-id", "x-amz-request-id", "cf-ray",
]

def tech_detect(target):
    """
    Analyze HTTP headers for technology detection.
    Returns list of detected technologies.
    """
    print(f"  [*] Detecting technologies on {target}...")
    technologies = []

    # Try both HTTP and HTTPS
    for scheme in ["https", "http"]:
        url = f"{scheme}://{target}/"
        status, headers, body = http_request(url)
        if status is None:
            continue

        # Combine all header values into one string for pattern matching
        header_text = ""
        tech_header_values = OrderedDict()
        for h_name, h_val in headers.items():
            header_text += f"{h_name}: {h_val}\n"
            lower = h_name.lower()
            if lower in TECH_HEADERS:
                tech_header_values[h_name] = h_val

        # Pattern matching on combined header text
        found_techs = set()
        for pattern, tech_name in TECH_PATTERNS:
            match = re.search(pattern, header_text, re.IGNORECASE)
            if match:
                if tech_name is None:
                    # x-powered-by special case
                    val = match.group(1) if match.groups() else match.group(0)
                    found_techs.add(f"X-Powered-By: {val}")
                else:
                    found_techs.add(tech_name)

        # Also check body for framework signatures
        body_signatures = [
            (r"react", "React"),
            (r"angular", "Angular"),
            (r"vue\.js|vue\.min\.js", "Vue.js"),
            (r"jquery", "jQuery"),
            (r"bootstrap", "Bootstrap"),
            (r"next\.js", "Next.js"),
            (r"nuxt", "Nuxt.js"),
            (r"gatsby", "Gatsby"),
            (r"__NEXT_DATA__", "Next.js (data)"),
            (r"nuxt-", "Nuxt.js (data)"),
            (r"csrfmiddlewaretoken", "Django CSRF"),
            (r"django", "Django"),
            (r"laravel", "Laravel"),
            (r"rails", "Ruby on Rails"),
            (r"__cfduid|__cflb", "Cloudflare Cookie"),
            (r"wp-content|wp-includes", "WordPress (body)"),
        ]
        for pattern, tech_name in body_signatures:
            if re.search(pattern, body, re.IGNORECASE):
                found_techs.add(tech_name)

        # Check for specific cookies
        cookies = headers.get("set-cookie", "") + headers.get("Set-Cookie", "")
        cookie_techs = [
            (r"JSESSIONID", "Java EE"),
            (r"PHPSESSID", "PHP Session"),
            (r"ASP\.NET_SessionId", "ASP.NET Session"),
            (r"connect\.sid", "Express/Connect Session"),
            (r"laravel_session", "Laravel Session"),
            (r"_rails", "Rails"),
            (r"XSRF-TOKEN", "Laravel/Angular CSRF"),
            (r"csrftoken", "Django CSRF Cookie"),
            (r"__Host-", "Cookie Prefix (secure)"),
        ]
        for pattern, tech_name in cookie_techs:
            if re.search(pattern, cookies, re.IGNORECASE):
                found_techs.add(tech_name)

        if found_techs:
            technologies = sorted(found_techs)
            break  # Got results, no need to try other scheme

    if technologies:
        print(f"  [+] Detected {len(technologies)} technologies: {', '.join(technologies[:10])}")
    else:
        print(f"  [-] No technologies detected")

    return technologies

# ---------------------------------------------------------------------------
# 4. Wayback Machine — Historical URLs
# ---------------------------------------------------------------------------

def wayback(target, max_urls=50):
    """
    Query Wayback Machine CDX API for historical URLs.
    Returns list of unique URL strings.
    """
    print(f"  [*] Querying Wayback Machine for historical URLs of {target}...")

    # Use the CDX API
    domain_wildcard = f"*.{target}"
    cdx_url = (
        f"https://web.archive.org/cdx/search/cdx"
        f"?url={urllib.parse.quote(domain_wildcard)}"
        f"&output=json&fl=original&collapse=urlkey"
        f"&limit={max_urls * 3}"
    )

    req = urllib.request.Request(cdx_url, headers={"User-Agent": USER_AGENT})
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, timeout=30, context=context) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [!] Wayback Machine query failed: {e}")
        return []

    # First row is header
    if not data or len(data) < 2:
        print(f"  [-] No historical URLs found")
        return []

    urls = []
    seen = set()
    for row in data[1:]:  # skip header
        if row and row[0] not in seen:
            seen.add(row[0])
            urls.append(row[0])

    urls = urls[:max_urls]
    print(f"  [+] Found {len(urls)} historical URLs")
    return urls

# ---------------------------------------------------------------------------
# 5. Git Leaks — Exposed .git directories
# ---------------------------------------------------------------------------

GIT_PATHS = [
    ".git/HEAD",
    ".git/config",
    ".git/index",
    ".git/description",
    ".git/COMMIT_EDITMSG",
    ".git/logs/HEAD",
    ".git/refs/heads/main",
    ".git/refs/heads/master",
    ".git/objects/info/packs",
    ".git/FETCH_HEAD",
]

def git_leaks(target):
    """
    Check for exposed .git directories and sensitive files.
    Returns list of findings dicts.
    """
    print(f"  [*] Checking for exposed .git on {target}...")
    findings = []

    for scheme in ["https", "http"]:
        base_url = f"{scheme}://{target}"

        # First check if .git/HEAD exists (quick indicator)
        head_url = f"{base_url}/.git/HEAD"
        status, headers, body = http_request(head_url)

        if status == 200 and ("ref:" in body or len(body) > 0):
            findings.append({
                "url": head_url,
                "type": "git_head_exposed",
                "status": status,
                "detail": "Git HEAD file accessible",
                "snippet": body[:200],
            })

        # Check .git/config
        config_url = f"{base_url}/.git/config"
        status, headers, body = http_request(config_url)
        if status == 200 and ("repositoryformatversion" in body or "url =" in body):
            findings.append({
                "url": config_url,
                "type": "git_config_exposed",
                "status": status,
                "detail": "Git config file accessible — may contain remote URLs/credentials",
                "snippet": body[:200],
            })

        # Check for .git/index
        index_url = f"{base_url}/.git/index"
        status, headers, body = http_request(index_url)
        if status == 200 and body:
            # Check magic bytes for git index
            if len(body) >= 4 and body[:4] == "DIRC":
                findings.append({
                    "url": index_url,
                    "type": "git_index_exposed",
                    "status": status,
                    "detail": "Git index file accessible — may leak file names and hashes",
                    "snippet": "(binary git index)",
                })

        # Check for directory listing
        dir_url = f"{base_url}/.git/"
        status, headers, body = http_request(dir_url)
        if status == 200 and ("Index of" in body or "HEAD" in body):
            findings.append({
                "url": dir_url,
                "type": "git_directory_listing",
                "status": status,
                "detail": "Git directory listing enabled",
                "snippet": body[:200],
            })

        # Check .gitignore (low severity but useful)
        gitignore_url = f"{base_url}/.gitignore"
        status, headers, body = http_request(gitignore_url)
        if status == 200 and body.strip():
            findings.append({
                "url": gitignore_url,
                "type": "gitignore_exposed",
                "status": status,
                "detail": "Gitignore file accessible — may reveal internal paths",
                "snippet": body[:200],
            })

        # Check for common backup files that indicate git exposure
        backup_files = [
            (".git/refs/heads/", "git_refs"),
            (".git/logs/HEAD", "git_log"),
            (".git/info/refs", "git_info_refs"),
            (".git/packed-refs", "git_packed_refs"),
        ]
        for path, leak_type in backup_files:
            url = f"{base_url}/{path}"
            status, headers, body = http_request(url)
            if status == 200 and body.strip():
                findings.append({
                    "url": url,
                    "type": leak_type,
                    "status": status,
                    "detail": f"Git file accessible: {path}",
                    "snippet": body[:200],
                })

        # If we found anything with this scheme, don't try the other
        if findings:
            break

    if findings:
        print(f"  [!] Found {len(findings)} git exposure issues")
    else:
        print(f"  [+] No .git exposures detected")

    return findings

# ---------------------------------------------------------------------------
# Main pipeline orchestrator
# ---------------------------------------------------------------------------

def run_pipeline(domain, port_timeout=None, top_ports=None, verbose=False):
    """Run all recon modules and return structured report."""
    print(f"\n{'='*60}")
    print(f" Bug Bounty Recon Pipeline")
    print(f" Target: {domain}")
    print(f" Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    report = OrderedDict()
    report["target"] = domain
    report["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    report["pipeline_version"] = "1.0.0"

    # Determine scan target (use domain directly, may resolve or not)
    scan_target = domain

    # --- Module 1: Subdomain Enumeration ---
    print("[Module 1/5] Subdomain Enumeration")
    report["subdomains"] = subdomain_enum(domain)

    # --- Module 2: Port Scan ---
    print("\n[Module 2/5] Port Scan")
    ports_to_scan = COMMON_PORTS[:top_ports] if top_ports else COMMON_PORTS
    if port_timeout:
        global CONNECT_TIMEOUT
        CONNECT_TIMEOUT = port_timeout
    report["open_ports"] = port_scan(scan_target, ports=ports_to_scan)

    # --- Module 3: Technology Detection ---
    print("\n[Module 3/5] Technology Detection")
    report["technologies"] = tech_detect(scan_target)

    # --- Module 4: Wayback Machine ---
    print("\n[Module 4/5] Wayback Machine")
    report["wayback_urls"] = wayback(domain)

    # --- Module 5: Git Leaks ---
    print("\n[Module 5/5] Git Leak Detection")
    report["git_leaks"] = git_leaks(scan_target)

    # --- Summary ---
    print(f"\n{'='*60}")
    print(" SUMMARY")
    print(f"{'='*60}")
    print(f"  Subdomains found:    {len(report['subdomains'])}")
    print(f"  Open ports:          {len(report['open_ports'])}")
    print(f"  Technologies:        {len(report['technologies'])}")
    print(f"  Wayback URLs:        {len(report['wayback_urls'])}")
    print(f"  Git exposures:       {len(report['git_leaks'])}")
    print(f"{'='*60}\n")

    return report

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Bug Bounty Recon Pipeline — automated reconnaissance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python recon_pipeline.py example.com
  python recon_pipeline.py example.com --output report.json
  python recon_pipeline.py example.com --top-ports 50 --timeout 2
  python recon_pipeline.py example.com -o report.json -t 2 --top-ports 100
        """,
    )
    parser.add_argument("domain", help="Target domain (e.g., example.com)")
    parser.add_argument("-o", "--output", help="Output JSON report file path")
    parser.add_argument("-t", "--timeout", type=float, default=CONNECT_TIMEOUT,
                        help=f"TCP connect timeout in seconds (default: {CONNECT_TIMEOUT})")
    parser.add_argument("--top-ports", type=int, default=None,
                        help="Limit port scan to top N common ports")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Basic domain validation
    if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?$', args.domain):
        print(f"[!] Invalid domain format: {args.domain}")
        sys.exit(1)

    try:
        report = run_pipeline(
            domain=args.domain,
            port_timeout=args.timeout,
            top_ports=args.top_ports,
            verbose=args.verbose,
        )
    except KeyboardInterrupt:
        print("\n[!] Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[!] Pipeline error: {e}")
        sys.exit(1)

    # Output
    json_output = json.dumps(report, indent=2)

    if args.output:
        try:
            with open(args.output, "w") as f:
                f.write(json_output)
            print(f"[+] Report saved to: {args.output}")
        except Exception as e:
            print(f"[!] Could not write output file: {e}")
            print(json_output)
    else:
        print(json_output)

if __name__ == "__main__":
    main()
