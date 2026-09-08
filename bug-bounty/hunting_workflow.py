#!/usr/bin/env python3
"""Bug Bounty Hunting Workflow — automated recon → vuln scan → report → track."""

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── paths ────────────────────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent
WORKSPACE = BASE / "workspace"
REPORTS = BASE / "reports"
TRACKER_CSV = BASE / "submissions.csv"
CVSS_ENV = {"CRITICAL": (9.0, 10.0), "HIGH": (7.0, 8.9), "MEDIUM": (4.0, 6.9),
            "LOW": (0.1, 3.9), "INFO": (0.0, 0.0)}

# ── helpers ──────────────────────────────────────────────────────────────────
def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def ymd():
    return datetime.now(timezone.utc).strftime("%Y%m%d")

def which(tool):
    return shutil.which(tool)

def run_cmd(cmd, timeout=120):
    """Run a shell command, return (stdout, returncode).  Non-zero → ('', rc)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.returncode
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return str(e), -1

def severity(score):
    for sev, (lo, hi) in CVSS_ENV.items():
        if lo <= score <= hi:
            return sev
    return "INFO"

def ensure_dirs(*dirs):
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# ── 1. target intake ────────────────────────────────────────────────────────
def intake(target, scope_in=None, scope_out=None, program=None):
    """Register a target, write scope.json, return the target workdir."""
    safe = re.sub(r"[^A-Za-z0-9.\-]", "_", target)
    tdir = WORKSPACE / safe
    ensure_dirs(tdir)
    scope = {
        "target": target,
        "program": program,
        "scope_in": scope_in or [],
        "scope_out": scope_out or [],
        "created": now(),
        "status": "active",
    }
    (tdir / "scope.json").write_text(json.dumps(scope, indent=2))
    print(f"[+] Target registered: {target}  ({tdir})")
    return tdir

# ── 2. automated recon ──────────────────────────────────────────────────────
def recon(tdir, aggressive=False):
    """Subdomain enum → port scan → tech detect.  Write recon.json."""
    scope = json.loads((tdir / "scope.json").read_text())
    target = scope["target"]
    out = {"target": target, "started": now(), "subdomains": [], "ports": [], "tech": []}

    # -- subdomain enumeration --
    print(f"[*] Enumerating subdomains for {target} …")
    if which("subfinder"):
        so, _ = run_cmd(["subfinder", "-d", target, "-silent"], timeout=180)
        out["subdomains"] = [s for s in so.splitlines() if s.strip()]
    elif which("amass"):
        so, _ = run_cmd(["amass", "enum", "-passive", "-d", target], timeout=300)
        out["subdomains"] = [s for s in so.splitlines() if s.strip() and target in s]
    else:
        # fallback: basic DNS brute with common prefixes
        prefixes = ["www", "mail", "api", "dev", "staging", "admin", "portal",
                    "vpn", "git", "shop", "blog", "cdn"]
        for p in prefixes:
            fqdn = f"{p}.{target}"
            so, rc = run_cmd(["nslookup", "-q=A", fqdn], timeout=10)
            if rc == 0 and "Address" in so:
                out["subdomains"].append(fqdn)
        if not out["subdomains"]:
            out["subdomains"] = [target]

    # -- port scan --
    print(f"[*] Scanning ports on {len(out['subdomains'])} host(s) …")
    if which("nmap"):
        for host in out["subdomains"]:
            so, _ = run_cmd(["nmap", "-T4", "--top-ports", "1000", "-Pn", host], timeout=240)
            for line in so.splitlines():
                m = re.match(r"(\d+)/(tcp|udp)\s+(\S+)\s+(.*)", line)
                if m:
                    out["ports"].append({
                        "host": host, "port": int(m.group(1)),
                        "proto": m.group(2), "state": m.group(3), "service": m.group(4).strip()
                    })
    else:
        for host in out["subdomains"]:
            for port in [80, 443, 8080, 8443]:
                so, rc = run_cmd(["nslookup", "-q=A", host], timeout=5)
                if rc == 0 and "Address" in so:
                    out["ports"].append({"host": host, "port": port, "proto": "tcp",
                                         "state": "open", "service": "http" if port in (80, 8080) else "https"})

    # -- tech detection --
    print(f"[*] Detecting technologies …")
    if which("whatweb"):
        for host in out["subdomains"]:
            so, _ = run_cmd(["whatweb", "--no-errors", f"https://{host}"], timeout=60)
            if so:
                out["tech"].append({"host": host, "raw": so})
    else:
        for host in out["subdomains"]:
            out["tech"].append({"host": host, "note": "whatweb not installed — skipping tech detect"})

    out["finished"] = now()
    (tdir / "recon.json").write_text(json.dumps(out, indent=2))
    print(f"[+] Recon complete: {len(out['subdomains'])} subdomains, "
          f"{len(out['ports'])} open ports, {len(out['tech'])} tech fingerprints")
    return out

# ── 3. vulnerability scanning ───────────────────────────────────────────────
def vulnscan(tdir, recon_data):
    """Run nuclei / nikto against live hosts, parse findings into findings.json."""
    findings = []
    hosts = [s for s in recon_data.get("subdomains", [])]
    if not hosts:
        hosts = [recon_data["target"]]

    for host in hosts:
        base = f"https://{host}" if which("nuclei") else f"http://{host}"
        print(f"[*] Scanning {host} …")

        # nuclei (templates-based)
        if which("nuclei"):
            so, _ = run_cmd(["nuclei", "-u", base, "-silent", "-severity",
                             "critical,high,medium", "-json", "-timeout", "5"], timeout=300)
            for line in so.splitlines():
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                    findings.append({
                        "host": host,
                        "template": item.get("template-id", "?"),
                        "name": item.get("info", {}).get("name", "?"),
                        "severity": item.get("info", {}).get("severity", "unknown").upper(),
                        "matched": item.get("matched-at", ""),
                        "evidence": item.get("extracted-results", []),
                        "cpe": item.get("matcher-name", ""),
                        "cvss": item.get("info", {}).get("classification", {}).get("cvss-score", 0),
                    })
                except json.JSONDecodeError:
                    continue

        # nikto (web server scan)
        if which("nikto"):
            so, _ = run_cmd(["nikto", "-h", host, "-Format", "txt"], timeout=300)
            for line in so.splitlines():
                if any(kw in line.lower() for kw in ["vulnerab", "xss", "sql",
                                                      "injection", "rce", "include"]):
                    findings.append({
                        "host": host, "template": "nikto",
                        "name": line.strip()[:120],
                        "severity": "MEDIUM",
                        "matched": base, "evidence": [line.strip()],
                        "cpe": "", "cvss": 5.0,
                    })

    if not findings:
        print("[-] No tools available (nuclei, nikto) — no automated vuln scan performed.")

    (tdir / "findings.json").write_text(json.dumps(findings, indent=2))
    print(f"[+] Vuln scan complete: {len(findings)} finding(s)")
    return findings

# ── 4. finding documentation ────────────────────────────────────────────────
def document(findings):
    """Enrich findings with CVSS vector + evidence, deduplicate, sort by severity."""
    seen = set()
    unique = []
    for f in findings:
        key = (f.get("host"), f.get("name"), f.get("matched"))
        if key in seen:
            continue
        seen.add(key)
        score = f.get("cvss", 0) or 0
        if isinstance(score, (int, float)):
            pass
        else:
            try:
                score = float(score)
            except (ValueError, TypeError):
                score = 0.0
        f["cvss_score"] = round(score, 1)
        f["severity"] = severity(score)
        f["evidence_file"] = None
        unique.append(f)

    sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
    unique.sort(key=lambda x: sev_order.get(x["severity"], 5))
    return unique

# ── 5. report generation ────────────────────────────────────────────────────
def gen_markdown(tdir, scope, findings):
    """Write report.md with executive summary + detailed findings."""
    lines = []
    lines.append(f"# Bug Bounty Report — {scope['target']}")
    lines.append(f"\n**Program:** {scope.get('program', 'N/A')}  ")
    lines.append(f"**Date:** {now()}  ")
    lines.append(f"**Status:** {scope.get('status', 'draft')}\n")

    # summary table
    sev_counts = {}
    for f in findings:
        sev_counts[f["severity"]] = sev_counts.get(f["severity"], 0) + 1
    lines.append("## Summary\n")
    lines.append("| Severity | Count |")
    lines.append("|----------|-------|")
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
        lines.append(f"| {sev} | {sev_counts.get(sev, 0)} |")
    lines.append("")

    # findings
    lines.append("## Findings\n")
    for i, f in enumerate(findings, 1):
        lines.append(f"### {i}. [{f['severity']}] {f['name']}")
        lines.append(f"- **Host:** {f['host']}")
        lines.append(f"- **CVSS:** {f['cvss_score']} ({f['severity']})")
        lines.append(f"- **Matched:** {f.get('matched', 'N/A')}")
        if f.get("evidence"):
            lines.append("- **Evidence:**")
            for e in f["evidence"][:10]:
                lines.append(f"  - `{e}`")
        lines.append(f"- **Template:** `{f.get('template', 'N/A')}`")
        lines.append("")

    report = "\n".join(lines)
    (tdir / "report.md").write_text(report)
    print(f"[+] Markdown report: {tdir / 'report.md'}")
    return report

def gen_pdf(tdir):
    """Convert report.md → report.md.pdf via pandoc or wkhtmltopdf."""
    md = tdir / "report.md"
    pdf = tdir / "report.md.pdf"
    if not md.exists():
        return None
    if which("pandoc"):
        run_cmd(["pandoc", str(md), "-o", str(pdf), "--pdf-engine=xelatex"], timeout=60)
    elif which("wkhtmltopdf"):
        # markdown → html → pdf
        html = tdir / "report.html"
        if which("glow"):
            so, _ = run_cmd(["glow", str(md)], timeout=30)
            html.write_text(f"<html><body><pre>{so}</pre></body></html>")
        else:
            html.write_text(f"<html><body><pre>{md.read_text()}</pre></body></html>")
        run_cmd(["wkhtmltopdf", str(html), str(pdf)], timeout=60)
    if pdf.exists():
        print(f"[+] PDF report: {pdf}")
        return pdf
    print("[-] PDF generation skipped (install pandoc or wkhtmltopdf + glow)")
    return None

# ── 6. submission tracker ───────────────────────────────────────────────────
CSV_FIELDS = ["id", "date", "platform", "target", "program", "title",
              "severity", "cvss", "bounty", "status", "report_pdf", "notes"]

def tracker_init():
    if not TRACKER_CSV.exists():
        with open(TRACKER_CSV, "w", newline="") as f:
            csv.DictWriter(f, fieldnames=CSV_FIELDS).writeheader()

def tracker_add(platform, target, program, title, severity, cvss, bounty,
                status, report_pdf, notes):
    tracker_init()
    rows = []
    if TRACKER_CSV.exists():
        with open(TRACKER_CSV, newline="") as f:
            rows = list(csv.DictReader(f))
    new_id = f"BB-{len(rows) + 1:04d}"
    row = {
        "id": new_id, "date": now(), "platform": platform, "target": target,
        "program": program, "title": title, "severity": severity, "cvss": str(cvss),
        "bounty": bounty, "status": status, "report_pdf": str(report_pdf or ""),
        "notes": notes,
    }
    with open(TRACKER_CSV, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writerow(row)
    print(f"[+] Submission logged: {new_id} ({platform})")
    return new_id

def tracker_list(status_filter=None):
    if not TRACKER_CSV.exists():
        print("No submissions yet.")
        return
    with open(TRACKER_CSV, newline="") as f:
        rows = list(csv.DictReader(f))
    if status_filter:
        rows = [r for r in rows if r["status"].lower() == status_filter.lower()]
    if not rows:
        print("No matching submissions.")
        return
    print(f"\n{'ID':<10}{'Date':<22}{'Platform':<12}{'Target':<25}{'Severity':<10}{'Status':<12}{'Bounty'}")
    print("-" * 110)
    for r in rows:
        print(f"{r['id']:<10}{r['date']:<22}{r['platform']:<12}{r['target']:<25}"
              f"{r['severity']:<10}{r['status']:<12}${r['bounty']}")
    print()

# ── CLI ──────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="Bug Bounty Hunting Workflow")
    p.add_argument("target", nargs="?", help="e.g. example.com")
    p.add_argument("--program", help="Program name (HackerOne / Bugcrowd handle)")
    p.add_argument("--scope-in", nargs="*", help="In-scope assets (wildcards ok)")
    p.add_argument("--scope-out", nargs="*", help="Out-of-scope assets")
    p.add_argument("--full", action="store_true", help="Run all phases end-to-end")
    p.add_argument("--recon-only", action="store_true", help="Recon phase only")
    p.add_argument("--scan-only", action="store_true", help="Vuln scan only (needs recon)")
    p.add_argument("--report-only", action="store_true", help="Generate report from findings")
    p.add_argument("--submit", choices=["hackone", "bugcrowd"],
                   help="Log submission after report generation")
    p.add_argument("--bounty", default="0", help="Bounty amount in USD")
    p.add_argument("--notes", default="", help="Submission notes")
    p.add_argument("--list", action="store_true", help="List all tracked submissions")
    p.add_argument("--list-status", help="Filter submissions by status")
    args = p.parse_args()

    if args.list or args.list_status:
        tracker_list(args.list_status)
        return

    if not args.target:
        p.error("target is required (unless using --list)")

    # phase 1 — intake
    tdir = intake(args.target, args.scope_in, args.scope_out, args.program)

    # phase 2 — recon
    if args.full or args.recon_only:
        recon_data = recon(tdir, aggressive=args.full)
    else:
        recon_file = tdir / "recon.json"
        if recon_file.exists():
            recon_data = json.loads(recon_file.read_text())
        else:
            print("[-] No recon.json found — run with --full or --recon-only first")
            sys.exit(1)

    if args.recon_only:
        return

    # phase 3 — vuln scan
    if args.full or args.scan_only:
        findings = vulnscan(tdir, recon_data)
    else:
        findings_file = tdir / "findings.json"
        if findings_file.exists():
            findings = json.loads(findings_file.read_text())
        else:
            print("[-] No findings.json found — run with --full or --scan-only first")
            sys.exit(1)

    if args.scan_only:
        return

    # phase 4 — document
    findings = document(findings)
    (tdir / "findings.json").write_text(json.dumps(findings, indent=2))

    # phase 5 — report
    scope = json.loads((tdir / "scope.json").read_text())
    gen_markdown(tdir, scope, findings)
    pdf_path = gen_pdf(tdir)

    # phase 6 — submit
    if args.submit or args.full:
        top = findings[0] if findings else {"name": "Recon only", "severity": "INFO",
                                             "cvss_score": 0.0}
        tracker_add(
            platform="hackone" if args.submit == "hackone" else "bugcrowd",
            target=args.target,
            program=args.program or "",
            title=top["name"],
            severity=top["severity"],
            cvss=top.get("cvss_score", 0),
            bounty=args.bounty,
            status="submitted",
            report_pdf=pdf_path,
            notes=args.notes,
        )

    print(f"\n[✓] Workflow complete for {args.target}.  Artifacts in {tdir}")

if __name__ == "__main__":
    main()
