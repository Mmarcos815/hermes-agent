#!/usr/bin/env python3
"""Audit CI/CD workflows for supply-chain risks.

Flags: pull_request_target, unpinned actions, missing permissions,
script injection via untrusted contexts.
"""
import argparse, re, sys
from pathlib import Path

PATTERNS = [
    (r"pull_request_target","CRITICAL","untrusted PRs get secrets"),
    (r"uses:\s*[\w-]+/[\w-]+@(main|master|latest|v\d+)\s*$","HIGH","action pinned to tag, not SHA"),
    (r"github\.event\.pull_request\.head\.sha","MEDIUM","PR head checkout without fork validation"),
    (r"github\.event\.issue\.body","MEDIUM","script injection risk"),
]
PERMS = re.compile(r"^permissions\s*:", re.MULTILINE)

def find_wf(root):
    wf = Path(root)/".github"/"workflows"
    return list(wf.glob("*.yml"))+list(wf.glob("*.yaml")) if wf.exists() else []

def audit(path):
    findings = []
    try: lines = Path(path).read_text().splitlines()
    except: return findings
    for pat, sev, desc in PATTERNS:
        for i, line in enumerate(lines, 1):
            if re.search(pat, line, re.IGNORECASE):
                findings.append((sev, i, line.strip(), desc))
    if not PERMS.search("\n".join(lines)):
        findings.append(("MEDIUM", 0, "", "no permissions block"))
    return findings

def main():
    p = argparse.ArgumentParser()
    p.add_argument("dir")
    a = p.parse_args()
    wfs = find_wf(a.dir)
    if not wfs: print("No workflows found"); sys.exit(1)
    all_f = []
    for wf in wfs:
        print(f"\n{wf.name}")
        f = audit(wf)
        all_f.extend(f)
        for sev, ln, match, desc in sorted(f, key=lambda x:["CRITICAL","HIGH","MEDIUM","LOW"].index(x[0])):
            flag = {"CRITICAL":"🚨","HIGH":"⚠️","MEDIUM":"⚡"}.get(sev,"ℹ️")
            print(f"  {flag} [{sev}] L{ln}: {desc}")
            if match: print(f"      → {match}")
    c = sum(1 for x in all_f if x[0]=="CRITICAL")
    h = sum(1 for x in all_f if x[0]=="HIGH")
    print(f"\nSummary: {c} critical, {h} high, {len(all_f)} total")

if __name__=="__main__": main()
