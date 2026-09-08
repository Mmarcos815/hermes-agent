#!/usr/bin/env python3
"""
Automated Engagement Pipeline
=============================
Connects all tools in the bug bounty / red-team workflow:

  1. Target input      → Recon pipeline (subdomain enum, port scan, tech detect)
  2. Vulnerability scan → Exploit tools (vuln-lab modules, CVSS scoring)
  3. Evidence capture  → PDF report (reportlab-based findings export)
  4. Scope tracking    → Monthly report (scope_manager + cron aggregation)
  5. CLI: python engagement.py target.com --full

Usage:
    python engagement.py <target> [--full] [--recon] [--vuln] [--report] [--scope]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PIPELINE_DIR.parent
BUG_BOUNTY_DIR = PROJECT_DIR / "bug-bounty"
RECON_PIPELINE = BUG_BOUNTY_DIR / "recon_pipeline.py"
SCOPE_MANAGER = BUG_BOUNTY_DIR / "scope_manager.py"
PDF_REPORT = PROJECT_DIR / "reporting" / "pdf_report.py"
VULN_LAB_DIR = PROJECT_DIR / "bionic-vuln-lab"
DEFAULT_OUTPUT_DIR = PROJECT_DIR / "engagements"

SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]
SEVERITY_WEIGHTS = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
CVSS_MAP = {"critical": 9.8, "high": 8.0, "medium": 5.5, "low": 3.0, "info": 0.0}

DANGEROUS_PORTS = {
    21: ("FTP Open", "FTP exposed — may allow anonymous access", "medium"),
    23: ("Telnet Exposed", "Telnet active — cleartext protocol", "high"),
    445: ("SMB Exposed", "SMB exposed — lateral movement risk", "high"),
    3306: ("MySQL Exposed", "MySQL directly accessible", "high"),
    3389: ("RDP Exposed", "RDP exposed — brute-force risk", "high"),
    5432: ("PostgreSQL Exposed", "PostgreSQL directly accessible", "high"),
    6379: ("Redis Exposed", "Redis exposed — unauthenticated access", "critical"),
    9200: ("Elasticsearch Exposed", "Elasticsearch API exposed", "high"),
    27017: ("MongoDB Exposed", "MongoDB directly accessible", "critical"),
}

TAKEOVER_INDICATORS = ["herokuapp.com", "s3.amazonaws.com", "cloudfront.net",
                       "github.io", "azurewebsites.net"]


def slugify(t: str) -> str:
    return re.sub(r"[^a-zA-Z0-9.-]", "_", t)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_cmd(cmd: list[str], timeout: int = 120):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError:
        return -1, "", f"Not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return -2, "", "Timeout"
    except Exception as e:
        return -3, "", str(e)


def load_json(path: Path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


# ── Stage 1: Recon ──────────────────────────────────────────────────────────

def run_recon(target: str, output_dir: Path, args: argparse.Namespace) -> dict:
    print("\n" + "=" * 60 + "\n STAGE 1: Reconnaissance\n" + "=" * 60)
    recon_output = output_dir / "recon_raw.json"
    cmd = [sys.executable, str(RECON_PIPELINE), target, "-o", str(recon_output)]
    if args.top_ports:
        cmd.extend(["--top-ports", str(args.top_ports)])
    if args.timeout:
        cmd.extend(["--timeout", str(args.timeout)])
    print(f"[*] Running recon on {target}...")
    rc, stdout, stderr = run_cmd(cmd, timeout=300)
    if rc != 0 and stderr:
        print(f"[!] Recon warning: {stderr[:200]}")
    report = load_json(recon_output) or {
        "target": target, "timestamp": now_iso(),
        "subdomains": [], "open_ports": {}, "technologies": [],
        "wayback_urls": [], "git_leaks": [],
    }
    save_json(recon_output, report)
    print(f"  Subdomains: {len(report.get('subdomains', []))}")
    print(f"  Open ports: {len(report.get('open_ports', {}))}")
    print(f"  Technologies: {len(report.get('technologies', []))}")
    print(f"  Git leaks: {len(report.get('git_leaks', []))}")
    return report


# ── Stage 2: Vulnerability Scan ─────────────────────────────────────────────

def run_vuln_scan(target: str, recon_data: dict, output_dir: Path, args: argparse.Namespace) -> list[dict]:
    print("\n" + "=" * 60 + "\n STAGE 2: Vulnerability Analysis\n" + "=" * 60)
    findings = []
    for port_str, banner in recon_data.get("open_ports", {}).items():
        port = int(port_str)
        if port in DANGEROUS_PORTS:
            title, desc, sev = DANGEROUS_PORTS[port]
            findings.append({
                "title": f"{title} (Port {port})", "severity": sev,
                "description": desc,
                "evidence": f"Port {port} open" + (f" — {banner[:80]}" if banner else ""),
                "remediation": f"Restrict port {port} via firewall",
                "cvss": CVSS_MAP[sev], "affected": f"{target}:{port}",
                "date": now_iso()[:10], "source": "port_scan",
            })
    for leak in recon_data.get("git_leaks", []):
        findings.append({
            "title": f"Git Exposure ({leak.get('type', 'unknown')})",
            "severity": "high",
            "description": leak.get("detail", "Git metadata exposed"),
            "evidence": leak.get("url", "")[:200],
            "remediation": "Block .git access in web server config",
            "cvss": 7.5, "affected": leak.get("url", target),
            "date": now_iso()[:10], "source": "git_leak",
        })
    for sub in recon_data.get("subdomains", [])[:50]:
        for ind in TAKEOVER_INDICATORS:
            if ind in sub:
                findings.append({
                    "title": f"Subdomain Takeover Risk ({sub})",
                    "severity": "medium",
                    "description": f"Subdomain references {ind} — verify resource is claimed",
                    "evidence": f"CNAME: {sub} -> {ind}",
                    "remediation": "Claim the resource or remove the CNAME",
                    "cvss": 5.3, "affected": sub,
                    "date": now_iso()[:10], "source": "subdomain_analysis",
                })
    scanner = VULN_LAB_DIR / "src" / "app.js"
    if scanner.exists():
        rc, stdout, _ = run_cmd(["node", str(scanner), target], timeout=60)
        if rc == 0 and stdout.strip().startswith("["):
            try:
                for v in json.loads(stdout):
                    findings.append({
                        "title": v.get("title", "Vuln Found"),
                        "severity": v.get("severity", "medium"),
                        "description": v.get("description", ""),
                        "evidence": v.get("evidence", ""),
                        "remediation": v.get("remediation", ""),
                        "cvss": v.get("cvss", 5.0),
                        "affected": v.get("affected", target),
                        "date": now_iso()[:10], "source": "vuln_lab",
                    })
            except json.JSONDecodeError:
                pass
    findings.sort(key=lambda f: SEVERITY_WEIGHTS.get(f.get("severity", "info"), 0), reverse=True)
    save_json(output_dir / "findings.json", findings)
    print(f"  Total findings: {len(findings)}")
    for sev in SEVERITY_ORDER:
        c = sum(1 for f in findings if f.get("severity") == sev)
        if c:
            print(f"    {sev.upper()}: {c}")
    return findings


# ── Stage 3: Evidence Capture → PDF Report ──────────────────────────────────

def generate_report(target: str, findings: list[dict], recon_data: dict,
                    output_dir: Path, args: argparse.Namespace) -> Path:
    print("\n" + "=" * 60 + "\n STAGE 3: Evidence Capture & Report Generation\n" + "=" * 60)
    fmt = args.format if args.format in ("detailed", "summary", "executive") else "detailed"
    pdf_output = output_dir / f"report_{target}_{now_iso()[:10]}.pdf"
    if PDF_REPORT.exists():
        cmd = [sys.executable, str(PDF_REPORT), str(output_dir / "findings.json"),
               "-o", str(pdf_output), "-f", fmt]
        print(f"[*] Generating {fmt} PDF report...")
        rc, _, stderr = run_cmd(cmd, timeout=60)
        if rc == 0:
            print(f"  [+] PDF: {pdf_output}")
            return pdf_output
        print(f"  [!] PDF failed: {stderr[:150]}")
    html_output = output_dir / f"report_{target}_{now_iso()[:10]}.html"
    _gen_html_report(target, findings, recon_data, html_output)
    print(f"  [+] HTML: {html_output}")
    return html_output


def _gen_html_report(target: str, findings: list[dict], recon_data: dict, output: Path) -> None:
    colors = {"critical": "#dc2626", "high": "#ea580c", "medium": "#ca8a04",
              "low": "#16a34a", "info": "#2563eb"}
    rows = ""
    for i, f in enumerate(findings, 1):
        s = f.get("severity", "info")
        c = colors.get(s, "#64748b")
        rows += f'<div style="border-left:4px solid {c};padding-left:1rem;margin-bottom:1rem;">'
        rows += f'<h3>{i}. {f.get("title","")} <span style="background:{c};padding:2px 6px;border-radius:3px;color:#fff;font-size:0.75em;">{s.upper()}</span></h3>'
        rows += f'<p><b>Description:</b> {f.get("description","")}</p>'
        rows += f'<p><b>Evidence:</b> {f.get("evidence","")}</p>'
        rows += f'<p><b>Remediation:</b> {f.get("remediation","")}</p></div>'
    counts = {s: sum(1 for f in findings if f.get("severity") == s) for s in SEVERITY_ORDER}
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Report — {target}</title></head><body style="font-family:sans-serif;max-width:900px;margin:2rem auto">
<h1>Security Engagement Report</h1>
<p>Target: <b>{target}</b> | Generated: {now_iso()[:19]} | Findings: {len(findings)}</p>
<h2>Summary</h2><p>{' '.join(f'{s.upper()}: {c} ' for s,c in counts.items() if c)}</p>
<h2>Recon</h2><ul>
<li>Subdomains: {len(recon_data.get('subdomains',[]))}</li>
<li>Open Ports: {len(recon_data.get('open_ports',{}))}</li>
<li>Technologies: {len(recon_data.get('technologies',[]))}</li></ul>
<h2>Findings</h2>{rows or '<p>No findings.</p>'}</body></html>"""
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        f.write(html)


# ── Stage 4: Scope Tracking → Monthly Report ────────────────────────────────

def update_scope(target: str, findings: list[dict], output_dir: Path, args: argparse.Namespace) -> None:
    print("\n" + "=" * 60 + "\n STAGE 4: Scope Tracking & Monthly Report\n" + "=" * 60)
    scope_db = output_dir / "scope.db"
    if SCOPE_MANAGER.exists():
        run_cmd([sys.executable, str(SCOPE_MANAGER), "--db", str(scope_db),
                 "add", "domain", target], timeout=30)
        run_cmd([sys.executable, str(SCOPE_MANAGER), "--db", str(scope_db),
                 "scan", "--type", "domain"], timeout=120)
        rc, stdout, _ = run_cmd([sys.executable, str(SCOPE_MANAGER),
                                 "--db", str(scope_db), "notify"], timeout=30)
        if stdout.strip():
            print(f"  Notifications: {stdout[:300]}")
    entry = {
        "target": target, "scan_date": now_iso(),
        "total_findings": len(findings),
        "severity_breakdown": {s: sum(1 for f in findings if f.get("severity") == s) for s in SEVERITY_ORDER},
        "top_findings": [{"title": f.get("title"), "severity": f.get("severity")} for f in findings[:5]],
    }
    save_json(output_dir / "monthly_entry.json", entry)
    month_str = datetime.now(timezone.utc).strftime("%Y-%m")
    monthly_dir = output_dir.parent / "monthly"
    monthly_dir.mkdir(parents=True, exist_ok=True)
    agg_path = monthly_dir / f"monthly_{month_str}.json"
    agg = load_json(agg_path) or {"month": month_str, "engagements": []}
    agg["engagements"].append(entry)
    agg["total_targets"] = len(agg["engagements"])
    agg["total_findings"] = sum(e.get("total_findings", 0) for e in agg["engagements"])
    save_json(agg_path, agg)
    print(f"  [+] Monthly aggregate: {agg_path}")


# ── Pipeline Orchestrator ────────────────────────────────────────────────────

def run_engagement(target: str, args: argparse.Namespace) -> dict:
    target_slug = slugify(target)
    output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR / target_slug
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n{'#' * 60}\n  AUTOMATED ENGAGEMENT PIPELINE — {target}")
    print(f"  Output: {output_dir}  Started: {now_iso()}\n{'#' * 60}")
    start = time.time()
    summary = {"target": target, "started": now_iso(), "stages_run": [], "output_dir": str(output_dir)}
    run_all = args.full or not any([args.recon, args.vuln, args.report, args.scope])
    recon_data, findings = {}, []
    if run_all or args.recon:
        recon_data = run_recon(target, output_dir, args)
        summary["stages_run"].append("recon")
        summary["recon"] = {"subdomains": len(recon_data.get("subdomains", [])),
                            "open_ports": len(recon_data.get("open_ports", {}))}
    if run_all or args.vuln:
        if not recon_data:
            recon_data = load_json(output_dir / "recon_raw.json") or {}
        findings = run_vuln_scan(target, recon_data, output_dir, args)
        summary["stages_run"].append("vuln_scan")
        summary["findings_count"] = len(findings)
    if run_all or args.report:
        if not findings:
            findings = load_json(output_dir / "findings.json") or []
        report_path = generate_report(target, findings, recon_data, output_dir, args)
        summary["stages_run"].append("report")
        summary["report_path"] = str(report_path)
    if run_all or args.scope:
        update_scope(target, findings, output_dir, args)
        summary["stages_run"].append("scope_tracking")
    summary["elapsed_seconds"] = round(time.time() - start, 1)
    summary["completed"] = now_iso()
    save_json(output_dir / "engagement_summary.json", summary)
    print(f"\n{'=' * 60}\n ENGAGEMENT COMPLETE — {target}")
    print(f"  Stages: {', '.join(summary['stages_run'])}")
    print(f"  Findings: {summary.get('findings_count', 0)}")
    print(f"  Report: {summary.get('report_path', 'N/A')}")
    print(f"  Elapsed: {summary['elapsed_seconds']}s\n{'=' * 60}\n")
    return summary


# ── CLI ──────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="engagement",
        description="Automated Engagement Pipeline — recon → vuln scan → report → scope",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  python engagement.py target.com --full\n  python engagement.py target.com --recon --vuln\n  python engagement.py target.com --report --format executive\n  python engagement.py target.com --full -o ./engagements/target_com",
    )
    p.add_argument("target", help="Target domain (e.g., example.com)")
    p.add_argument("--full", action="store_true", help="Run all stages")
    p.add_argument("--recon", action="store_true", help="Recon only")
    p.add_argument("--vuln", action="store_true", help="Vuln scan only")
    p.add_argument("--report", action="store_true", help="Report only")
    p.add_argument("--scope", action="store_true", help="Scope tracking only")
    p.add_argument("-f", "--format", choices=["detailed", "summary", "executive"], default="detailed")
    p.add_argument("-o", "--output-dir", help="Output directory")
    p.add_argument("-t", "--timeout", type=float, default=3.0, help="TCP timeout (default: 3.0)")
    p.add_argument("--top-ports", type=int, help="Limit to top N ports")
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    target = args.target.strip()
    if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9.\-]*[a-zA-Z0-9])?$', target):
        print(f"[!] Invalid target: {target}")
        sys.exit(1)
    try:
        run_engagement(target, args)
    except KeyboardInterrupt:
        print("\n[!] Interrupted"); sys.exit(130)
    except Exception as e:
        print(f"\n[!] Error: {e}"); import traceback; traceback.print_exc(); sys.exit(1)


if __name__ == "__main__":
    main()
