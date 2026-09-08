#!/usr/bin/env python3
"""Monitor for supply-chain-relevant CVEs via OSV.

Queries OSV for vulns affecting watched packages and filters by
supply-chain keywords and optional severity level.
"""
import argparse, json, sys
from urllib.request import Request, urlopen

OSV = "https://api.osv.dev/v1/query"
KEYWORDS = ["supply chain","typosquat","dependency confusion","malicious package",
            "package substitution","provenance","build integrity"]

def query(eco, pkg):
    try:
        r = Request(OSV, json.dumps({"package":{"name":pkg,"ecosystem":eco}}).encode(),
                     headers={"Content-Type":"application/json"})
        return json.loads(urlopen(r, timeout=20).read()).get("vulns",[])
    except Exception as e: print(f"  Error: {e}", file=sys.stderr); return []

def is_sc(vuln):
    text = (vuln.get("summary","")+" "+vuln.get("details","")).lower()
    return any(k in text for k in KEYWORDS)

def severity(vuln):
    for s in vuln.get("severity",[]):
        if s.get("type")=="CVSS_V3": return s.get("score","?")
    return "?"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--packages", nargs="+", required=True)
    p.add_argument("--ecosystem", choices=["PyPI","npm","Go","crates.io","RubyGems"], default="PyPI")
    p.add_argument("--severity", choices=["LOW","MEDIUM","HIGH","CRITICAL"])
    a = p.parse_args()
    alerts = []
    for pkg in a.packages:
        print(f"Checking {pkg}...")
        for v in query(a.ecosystem, pkg):
            sev = severity(v)
            if a.severity and sev.upper()!=a.severity.upper(): continue
            if is_sc(v):
                alerts.append(v["id"])
                print(f"  🚨 {v['id']}: {v.get('summary','')[:80]}")
    print(f"\n{'='*40}")
    print(f"{len(alerts)} supply-chain CVE(s) found" if alerts else "No issues")

if __name__=="__main__": main()
