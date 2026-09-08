#!/usr/bin/env python3
"""Analyze package dependencies for supply-chain risks.

Parses manifests (requirements.txt, package.json), queries OSV for vulns,
and flags recently-published or suspicious packages.
"""
import argparse, json, sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

OSV = "https://api.osv.dev/v1/query"
PYPI = "https://pypi.org/pypi/{}/json"

def parse_reqs(p):
    pkgs = []
    for line in Path(p).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "-")): continue
        name = line.split("==",1)[0].split(">=",1)[0].split("<=",1)[0].split("[",1)[0].strip()
        if name: pkgs.append(name.lower())
    return pkgs

def parse_pkg_json(p):
    d = json.loads(Path(p).read_text())
    return list({**d.get("dependencies",{}), **d.get("devDependencies",{})}.keys())

def osv_query(pkg, eco):
    try:
        r = Request(OSV, json.dumps({"package":{"name":pkg,"ecosystem":eco}}).encode(),
                     headers={"Content-Type":"application/json"})
        return json.loads(urlopen(r, timeout=15).read()).get("vulns", [])
    except: return []

def pypi_age(pkg):
    try:
        r = Request(PYPI.format(pkg), headers={"User-Agent":"analyzer/1.0"})
        d = json.loads(urlopen(r, timeout=10).read())
        t = d.get("urls",[{}])[0].get("upload_time","")
        if t: return (datetime.now() - datetime.fromisoformat(t.replace("Z",""))).days
    except: pass
    return None

def analyze(pkg, eco):
    score, risks = 0, []
    vulns = osv_query(pkg, eco)
    if vulns: score += len(vulns)*20; risks.append(f"{len(vulns)} CVE(s)")
    if eco == "pypi":
        age = pypi_age(pkg)
        if age is not None and age < 30: score += 30; risks.append(f"recent ({age}d)")
    level = "HIGH" if score>=40 else "MEDIUM" if score>=15 else "LOW"
    return {"pkg":pkg,"eco":eco,"score":score,"level":level,"risks":risks}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("project")
    args = p.parse_args()
    found = list(Path(args.project).rglob("requirements.txt")) + list(Path(args.project).rglob("package.json"))
    for m in found:
        print(f"\n{m}")
        pkgs = parse_reqs(m) if m.name=="requirements.txt" else parse_pkg_json(m)
        for pkg in pkgs[:20]:
            r = analyze(pkg, "PyPI" if m.name=="requirements.txt" else "npm")
            flag = "⚠️" if r["level"]!="LOW" else "✓"
            print(f"  {flag} {pkg}: {r['level']} ({r['score']}) {'; '.join(r['risks'])}")

if __name__=="__main__": main()
