"""
Tier 4 UPGRADE: Real-Filesystem Bounty Sweeper
Scans actual .sol files on disk (crytic/not-so-smart-contracts corpus) with
regex AST heuristics and emits a severity-ranked findings report.
"""

import os
import re
import json
from datetime import datetime

CORPUS_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bounty_targets")
REPORT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bounty_sweeper_report.json")

RULES = [
    {
        "id": "RACE-COND-001",
        "name": "Race condition / call to the unknown",
        "severity": "HIGH",
        "pattern": r"\.call\.value\([^)]*\)\s*\(",
        "desc": "External call with value forwarding before state finalization enables reentrancy.",
    },
    {
        "id": "DOS-GAS-002",
        "name": "Unbounded loop over dynamic array (gas griefing DoS)",
        "severity": "MEDIUM",
        "pattern": r"for\s*\(uint\s*\w+\s*=\s*0;\s*\w+\s*<\s*(\w+)\.length",
        "desc": "Loop over dynamic array length can exceed block gas limit and brick the function.",
    },
    {
        "id": "FORCED-ETH-003",
        "name": "Strict balance equality",
        "severity": "MEDIUM",
        "pattern": r"(address\(this\)\.balance\s*==|this\.balance\s*==)",
        "desc": "Exact balance equality can be broken by selfdestruct force-feeding.",
    },
    {
        "id": "TXORIGIN-004",
        "name": "tx.origin authentication",
        "severity": "HIGH",
        "pattern": r"require\s*\(\s*tx\.origin\s*==",
        "desc": "tx.origin auth is phishable; substitute msg.sender.",
    },
    {
        "id": "TIMESTAMP-005",
        "name": "Block timestamp as randomness",
        "severity": "MEDIUM",
        "pattern": r"(block\.timestamp|now)\s*[%+]",
        "desc": "Miners can bias timestamp-derived values.",
    },
    {
        "id": "DELEGATE-006",
        "name": "Unprotected delegatecall",
        "severity": "CRITICAL",
        "pattern": r"\.delegatecall\s*\(",
        "desc": "delegatecall executes foreign code in storage context; must be tightly access-controlled.",
    },
    {
        "id": "SELFDESTRUCT-007",
        "name": "Self-destruct present",
        "severity": "LOW",
        "pattern": r"selfdestruct\s*\(",
        "desc": "Can force-feed ether and permanently alter accounting invariants.",
    },
]

EXCLUDE_DIRS = {"lib", "node_modules", "out", "broadcast", ".git"}


def scan_file(path: str):
    findings = []
    try:
        src = open(path, encoding="utf-8", errors="ignore").read()
    except OSError:
        return findings
    for rule in RULES:
        for m in re.finditer(rule["pattern"], src):
            line_no = src[: m.start()].count("\n") + 1
            findings.append({
                "rule": rule["id"],
                "severity": rule["severity"],
                "name": rule["name"],
                "file": os.path.relpath(path, CORPUS_ROOT),
                "line": line_no,
                "desc": rule["desc"],
                "snippet": src[max(0, m.start() - 40): m.end() + 40].replace("\n", " ")[:100],
            })
    return findings


def run():
    all_findings = []
    files_scanned = 0
    for root, dirs, files in os.walk(CORPUS_ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            if f.endswith(".sol"):
                files_scanned += 1
                all_findings.extend(scan_file(os.path.join(root, f)))

    sev_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    all_findings.sort(key=lambda x: (sev_rank.get(x["severity"], 9), x["file"], x["line"]))

    report = {
        "generated": datetime.utcnow().isoformat() + "Z",
        "corpus": CORPUS_ROOT,
        "files_scanned": files_scanned,
        "total_findings": len(all_findings),
        "by_severity": {
            s: sum(1 for f in all_findings if f["severity"] == s)
            for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        },
        "findings": all_findings,
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    print("=" * 72)
    print("   BOUNTY SWEEPER v2 — REAL CORPUS SCAN (crytic/not-so-smart-contracts)")
    print("=" * 72)
    print(f"Files scanned : {files_scanned}")
    print(f"Total findings: {len(all_findings)}")
    for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        print(f"  {s:9}: {report['by_severity'][s]}")
    print("-" * 72)
    shown = 0
    seen_rules = set()
    for f in all_findings:
        if f["rule"] in seen_rules:
            continue
        seen_rules.add(f["rule"])
        print(f"[{f['severity']:8}] {f['rule']}  {f['file']}:{f['line']}")
        print(f"           {f['snippet'][:90]}")
        shown += 1
        if shown >= 8:
            break
    print("-" * 72)
    print(f"[OK] Full report: {REPORT_PATH}")


if __name__ == "__main__":
    run()
