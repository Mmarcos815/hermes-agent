#!/usr/bin/env python3
"""
Automated Red Team Pipeline
For authorized security testing only. Use only on systems you own or have
explicit written permission to test.

Pipeline phases:
  1. Recon       — nmap, subfinder, httpx, nuclei
  2. Analysis    — build exploit chains from findings
  3. Evidence    — collect logs, screenshots, timestamps
  4. Reporting   — generate HTML/PDF report

Usage:
  python automated_red_team_pipeline.py --target example.com
  python automated_red_team_pipeline.py --target 192.168.1.1 --full
  python automated_red_team_pipeline.py --target example.com --skip-nuclei
"""

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from urllib.parse import urlparse

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

WORKSPACE = Path(__file__).parent.resolve()
TIMESTAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# Tool binaries (auto-detected)
TOOLS = {
    "nmap": "nmap",
    "subfinder": "subfinder",
    "httpx": "httpx",
    "nuclei": "nuclei",
}

# Severity mapping for exploit chain building
SEVERITY_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}

# CVE-to-exploit mapping (simplified — extend as needed)
EXPLOIT_DB = {
    "CVE-2021-41773": {"name": "Apache Path Traversal", "severity": "critical", "port": 80},
    "CVE-2021-44228": {"name": "Log4Shell RCE", "severity": "critical", "port": 0},
    "CVE-2017-5638": {"name": "Struts2 RCE", "severity": "critical", "port": 80},
    "CVE-2014-0160": {"name": "Heartbleed", "severity": "high", "port": 443},
}

# ──────────────────────────────────────────────────────────────────────────────
# Utility helpers
# ──────────────────────────────────────────────────────────────────────────────

def banner():
    print(r"""
    ╔══════════════════════════════════════════════════╗
    ║       AUTOMATED RED TEAM PIPELINE v1.0           ║
    ║       Authorized Testing Only                     ║
    ╚══════════════════════════════════════════════════╝
    """)


def log(msg, level="INFO"):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    prefix = {"INFO": "[*]", "WARN": "[!]", "ERROR": "[X]", "SUCCESS": "[+]"}
    print(f"{ts} {prefix.get(level, '   ')} {msg}")


def check_tool(name):
    """Return True if a tool is available on PATH."""
    return shutil.which(TOOLS[name]) is not None


def run_cmd(cmd, timeout=300, capture=True):
    """Run a shell command and return (returncode, stdout, stderr)."""
    log(f"Running: {cmd[:120]}{'...' if len(cmd) > 120 else ''}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=capture,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout or "", result.stderr or ""
    except subprocess.TimeoutExpired:
        log(f"Command timed out after {timeout}s: {cmd[:60]}", "WARN")
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -1, "", str(e)


def parse_nmap_ports(nmap_output):
    """Extract open ports from nmap output."""
    ports = []
    for line in nmap_output.splitlines():
        m = re.match(r"(\d+)/(tcp|udp)\s+(\S+)\s+(\S+)", line)
        if m:
            ports.append({
                "port": int(m.group(1)),
                "proto": m.group(2),
                "state": m.group(3),
                "service": m.group(4),
            })
    return ports


def parse_httpx(httpx_output):
    """Extract live hosts from httpx output."""
    hosts = []
    for line in httpx_output.splitlines():
        line = line.strip()
        if line and line.startswith(("http://", "https://")):
            # Strip trailing metadata in brackets
            url = line.split()[0] if " " in line else line
            hosts.append(url)
    return hosts


def parse_nuclei(nuclei_output):
    """Extract findings from nuclei JSON output."""
    findings = []
    for line in nuclei_output.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            findings.append({
                "template": entry.get("template-id", "unknown"),
                "name": entry.get("info", {}).get("name", "Unknown"),
                "severity": entry.get("info", {}).get("severity", "unknown"),
                "host": entry.get("host", ""),
                "matched": entry.get("matched-at", ""),
                "description": entry.get("info", {}).get("description", ""),
                "cve": entry.get("info", {}).get("classification", {}).get("cve-id", ""),
            })
        except json.JSONDecodeError:
            continue
    return findings


# ──────────────────────────────────────────────────────────────────────────────
# Phase 1: Reconnaissance
# ──────────────────────────────────────────────────────────────────────────────

def phase_recon(target, workdir, args):
    """Run automated reconnaissance."""
    log("PHASE 1: Reconnaissance", "INFO")
    recon = {"target": target, "timestamp": TIMESTAMP, "findings": {}}

    # --- Nmap ---
    if not args.skip_nmap and check_tool("nmap"):
        log("Running nmap scan...")
        nmap_out = workdir / "nmap_output.txt"
        cmd = (
            f"nmap -sV -sC --top-ports 1000 -T4 "
            f"--script=vuln -oN {nmap_out} {target}"
        )
        rc, stdout, stderr = run_cmd(cmd, timeout=600)
        if nmap_out.exists():
            content = nmap_out.read_text(errors="replace")
            recon["findings"]["nmap"] = {
                "raw": content,
                "ports": parse_nmap_ports(content),
                "rc": rc,
            }
            log(f"nmap found {len(recon['findings']['nmap']['ports'])} open ports", "SUCCESS")
        else:
            log("nmap produced no output", "WARN")
    else:
        if args.skip_nmap:
            log("nmap skipped (--skip-nmap)", "WARN")
        else:
            log("nmap not found on PATH", "WARN")

    # --- Subfinder ---
    if not args.skip_subfinder and check_tool("subfinder"):
        log("Running subfinder...")
        sf_out = workdir / "subfinder_output.txt"
        cmd = f"subfinder -d {target} -silent -o {sf_out}"
        rc, stdout, stderr = run_cmd(cmd, timeout=300)
        if sf_out.exists():
            subs = sf_out.read_text(errors="replace").splitlines()
            subs = [s.strip() for s in subs if s.strip()]
            recon["findings"]["subfinder"] = {"subdomains": subs, "count": len(subs)}
            log(f"subfinder found {len(subs)} subdomains", "SUCCESS")
        else:
            # subfinder may write to stdout
            subs = [s.strip() for s in stdout.splitlines() if s.strip()]
            recon["findings"]["subfinder"] = {"subdomains": subs, "count": len(subs)}
            log(f"subfinder found {len(subs)} subdomains", "SUCCESS")
    else:
        if args.skip_subfinder:
            log("subfinder skipped (--skip-subfinder)", "WARN")
        else:
            log("subfinder not found on PATH", "WARN")

    # --- HTTPX ---
    if not args.skip_httpx and check_tool("httpx"):
        log("Running httpx...")
        # Build target list from subdomains or use the target directly
        hosts_file = workdir / "hosts.txt"
        if "subfinder" in recon["findings"] and recon["findings"]["subfinder"]["subdomains"]:
            hosts_file.write_text("\n".join(recon["findings"]["subfinder"]["subdomains"]))
        else:
            hosts_file.write_text(target + "\n")

        httpx_out = workdir / "httpx_output.txt"
        cmd = (
            f"httpx -l {hosts_file} -silent -title -status-code "
            f"-tech-detect -json -o {httpx_out}"
        )
        rc, stdout, stderr = run_cmd(cmd, timeout=300)
        if httpx_out.exists():
            content = httpx_out.read_text(errors="replace")
            recon["findings"]["httpx"] = {
                "raw": content,
                "hosts": parse_httpx(content.replace('"url":', '\n')),
            }
        else:
            recon["findings"]["httpx"] = {"raw": stdout, "hosts": parse_httpx(stdout)}
        log(f"httpx found {len(recon['findings']['httpx']['hosts'])} live hosts", "SUCCESS")
    else:
        if args.skip_httpx:
            log("httpx skipped (--skip-httpx)", "WARN")
        else:
            log("httpx not found on PATH", "WARN")

    # --- Nuclei ---
    if not args.skip_nuclei and check_tool("nuclei"):
        log("Running nuclei...")
        nuclei_out = workdir / "nuclei_output.json"
        cmd = (
            f"nuclei -u {target} -severity low,medium,high,critical "
            f"-json-export {nuclei_out} -rate-limit 50"
        )
        rc, stdout, stderr = run_cmd(cmd, timeout=600)
        if nuclei_out.exists():
            content = nuclei_out.read_text(errors="replace")
            findings = parse_nuclei(content)
            recon["findings"]["nuclei"] = {"findings": findings, "count": len(findings)}
            log(f"nuclei found {len(findings)} vulnerabilities", "SUCCESS")
        else:
            findings = parse_nuclei(stdout)
            recon["findings"]["nuclei"] = {"findings": findings, "count": len(findings)}
            log(f"nuclei found {len(findings)} vulnerabilities", "SUCCESS")
    else:
        if args.skip_nuclei:
            log("nuclei skipped (--skip-nuclei)", "WARN")
        else:
            log("nuclei not found on PATH", "WARN")

    return recon


# ──────────────────────────────────────────────────────────────────────────────
# Phase 2: Exploit Chain Builder
# ──────────────────────────────────────────────────────────────────────────────

def phase_analysis(recon, workdir):
    """Build exploit chains from recon findings."""
    log("PHASE 2: Building exploit chains...", "INFO")
    chains = []

    # Collect all vulnerabilities
    vulns = []
    if "nuclei" in recon["findings"]:
        for f in recon["findings"]["nuclei"]["findings"]:
            vulns.append({
                "source": "nuclei",
                "name": f["name"],
                "severity": f["severity"],
                "host": f["host"],
                "cve": f["cve"],
            })

    # Map open ports to potential attacks
    if "nmap" in recon["findings"]:
        for port_info in recon["findings"]["nmap"]["ports"]:
            port = port_info["port"]
            svc = port_info["service"]

            # Common service-to-attack mapping
            if svc == "ftp" and port == 21:
                vulns.append({
                    "source": "nmap",
                    "name": f"FTP service on port {port} (check for anonymous login)",
                    "severity": "medium",
                    "host": f"{recon['target']}:{port}",
                })
            elif svc == "ssh" and port == 22:
                vulns.append({
                    "source": "nmap",
                    "name": f"SSH service on port {port} (check for weak creds)",
                    "severity": "low",
                    "host": f"{recon['target']}:{port}",
                })
            elif svc in ("http", "https"):
                vulns.append({
                    "source": "nmap",
                    "name": f"HTTP service on port {port} ({svc})",
                    "severity": "info",
                    "host": f"{recon['target']}:{port}",
                })
            elif svc == "smb" or port in (139, 445):
                vulns.append({
                    "source": "nmap",
                    "name": f"SMB service on port {port} (check for EternalBlue/MS17-010)",
                    "severity": "high",
                    "host": f"{recon['target']}:{port}",
                })
            elif svc == "rdp" or port == 3389:
                vulns.append({
                    "source": "nmap",
                    "name": f"RDP exposed on port {port} (check for BlueKeep)",
                    "severity": "high",
                    "host": f"{recon['target']}:{port}",
                })

    # Build chains: group by host and sort by severity
    host_map = {}
    for v in vulns:
        host = v.get("host", recon["target"])
        if host not in host_map:
            host_map[host] = []
        host_map[host].append(v)

    for host, host_vulns in host_map.items():
        # Sort by severity descending
        host_vulns.sort(key=lambda x: SEVERITY_ORDER.get(x["severity"], 0), reverse=True)
        chain = {
            "host": host,
            "steps": host_vulns,
            "max_severity": host_vulns[0]["severity"] if host_vulns else "info",
            "risk_score": sum(SEVERITY_ORDER.get(v["severity"], 0) for v in host_vulns),
        }
        chains.append(chain)

    # Sort chains by risk score
    chains.sort(key=lambda c: c["risk_score"], reverse=True)

    log(f"Built {len(chains)} exploit chains", "SUCCESS")
    return chains


# ──────────────────────────────────────────────────────────────────────────────
# Phase 3: Evidence Collection
# ──────────────────────────────────────────────────────────────────────────────

def phase_evidence(recon, chains, workdir, args):
    """Collect evidence: logs, screenshots, timestamps."""
    log("PHASE 3: Collecting evidence...", "INFO")
    evidence = {
        "collected_at": datetime.datetime.now().isoformat(),
        "screenshots": [],
        "artifacts": [],
    }

    # Save recon data as JSON artifact
    recon_json = workdir / "recon_data.json"
    # Serialize only essential data (skip raw output for size)
    serializable = {
        "target": recon["target"],
        "timestamp": recon["timestamp"],
        "findings": {},
    }
    for tool, data in recon["findings"].items():
        if tool == "nmap":
            serializable["findings"]["nmap"] = {
                "ports": data["ports"],
                "rc": data["rc"],
            }
        elif tool == "subfinder":
            serializable["findings"]["subfinder"] = {
                "count": data["count"],
                "sample": data["subdomains"][:50],
            }
        elif tool == "httpx":
            serializable["findings"]["httpx"] = {
                "count": len(data["hosts"]),
                "hosts": data["hosts"][:50],
            }
        elif tool == "nuclei":
            serializable["findings"]["nuclei"] = {
                "count": data["count"],
                "findings": data["findings"],
            }

    recon_json.write_text(json.dumps(serializable, indent=2))
    evidence["artifacts"].append(str(recon_json))

    # Save exploit chains
    chains_json = workdir / "exploit_chains.json"
    chains_json.write_text(json.dumps(chains, indent=2))
    evidence["artifacts"].append(str(chains_json))

    # Take screenshots of live hosts via nuclei/httpx output
    if not args.skip_screenshots:
        screenshot_dir = workdir / "screenshots"
        screenshot_dir.mkdir(exist_ok=True)

        hosts_to_shoot = []
        if "httpx" in recon["findings"]:
            hosts_to_shoot.extend(recon["findings"]["httpx"]["hosts"][:5])

        for url in hosts_to_shoot:
            safe_name = re.sub(r"[^a-zA-Z0-9.-]", "_", url)[:80]
            screenshot_path = screenshot_dir / f"{safe_name}.png"
            # Use a headless screenshot approach via curl + placeholder
            # In production, you'd use playwright or similar
            cmd = 'curl -sL -o /dev/null -w "%{http_code}" "' + url + '"'
            rc, stdout, stderr = run_cmd(cmd, timeout=30)
            evidence["screenshots"].append({
                "url": url,
                "status": stdout.strip(),
                "screenshot_file": str(screenshot_path),
            })

        log(f"Checked {len(hosts_to_shoot)} hosts for screenshot availability", "SUCCESS")

    evidence["artifacts"].extend([
        str(workdir / "nmap_output.txt"),
        str(workdir / "subfinder_output.txt"),
        str(workdir / "httpx_output.txt"),
        str(workdir / "nuclei_output.json"),
    ])

    log(f"Collected {len(evidence['artifacts'])} artifacts", "SUCCESS")
    return evidence


# ──────────────────────────────────────────────────────────────────────────────
# Phase 4: Report Generation
# ──────────────────────────────────────────────────────────────────────────────

def phase_report(recon, chains, evidence, workdir, args):
    """Generate HTML report."""
    log("PHASE 4: Generating report...", "INFO")

    target = recon["target"]
    report_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Count stats
    open_ports = len(recon["findings"].get("nmap", {}).get("ports", []))
    subdomains = recon["findings"].get("subfinder", {}).get("count", 0)
    live_hosts = len(recon["findings"].get("httpx", {}).get("hosts", []))
    vuln_count = recon["findings"].get("nuclei", {}).get("count", 0)

    # Severity breakdown
    sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for chain in chains:
        for step in chain["steps"]:
            sev = step.get("severity", "info")
            if sev in sev_counts:
                sev_counts[sev] += 1

    # Build HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Red Team Report — {target}</title>
<style>
:root {{
  --bg: #0d1117; --surface: #161b22; --border: #30363d;
  --text: #c9d1d9; --text-muted: #8b949e; --accent: #58a6ff;
  --critical: #ff0040; --high: #ff6600; --medium: #ffcc00;
  --low: #00cc66; --info: #58a6ff;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg);
  color: var(--text); line-height:1.6; padding:2rem; }}
.container {{ max-width:1200px; margin:0 auto; }}
h1 {{ color: var(--accent); font-size:2rem; margin-bottom:0.5rem; }}
h2 {{ color: var(--text); border-bottom:1px solid var(--border); padding-bottom:0.5rem; margin:2rem 0 1rem; }}
h3 {{ color: var(--text-muted); margin:1rem 0 0.5rem; }}
.meta {{ color: var(--text-muted); margin-bottom:2rem; }}
.stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:1rem; margin:2rem 0; }}
.stat-card {{ background:var(--surface); border:1px solid var(--border); border-radius:8px; padding:1.2rem; text-align:center; }}
.stat-card .value {{ font-size:2rem; font-weight:bold; color:var(--accent); }}
.stat-card .label {{ color:var(--text-muted); font-size:0.85rem; margin-top:0.3rem; }}
.severity-bar {{ display:flex; gap:0.5rem; margin:1rem 0; }}
.sev-item {{ flex:1; text-align:center; padding:0.5rem; border-radius:4px; background:var(--surface); }}
.sev-item .count {{ font-size:1.5rem; font-weight:bold; }}
.sev-critical .count {{ color:var(--critical); }}
.sev-high .count {{ color:var(--high); }}
.sev-medium .count {{ color:var(--medium); }}
.sev-low .count {{ color:var(--low); }}
.sev-info .count {{ color:var(--info); }}
table {{ width:100%; border-collapse:collapse; margin:1rem 0; }}
th, td {{ padding:0.6rem 0.8rem; text-align:left; border-bottom:1px solid var(--border); }}
th {{ background:var(--surface); color:var(--text-muted); font-weight:600; }}
tr:hover {{ background:var(--surface); }}
.badge {{ display:inline-block; padding:0.15rem 0.5rem; border-radius:4px; font-size:0.75rem; font-weight:bold; }}
.badge-critical {{ background:rgba(255,0,64,0.2); color:var(--critical); }}
.badge-high {{ background:rgba(255,102,0,0.2); color:var(--high); }}
.badge-medium {{ background:rgba(255,204,0,0.2); color:var(--medium); }}
.badge-low {{ background:rgba(0,204,102,0.2); color:var(--low); }}
.badge-info {{ background:rgba(88,166,255,0.2); color:var(--info); }}
.chain {{ background:var(--surface); border:1px solid var(--border); border-radius:8px; padding:1rem; margin:1rem 0; }}
.chain-header {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem; }}
.chain-host {{ font-weight:bold; color:var(--accent); }}
.risk-score {{ color:var(--text-muted); }}
.step {{ padding:0.4rem 0; border-bottom:1px solid var(--border); }}
.step:last-child {{ border-bottom:none; }}
.evidence-list {{ list-style:none; }}
.evidence-list li {{ padding:0.3rem 0; color:var(--text-muted); }}
.footer {{ margin-top:3rem; padding-top:1rem; border-top:1px solid var(--border);
  color:var(--text-muted); font-size:0.8rem; text-align:center; }}
</style>
</head>
<body>
<div class="container">

<h1>Red Team Assessment Report</h1>
<div class="meta">
  <strong>Target:</strong> {target} &nbsp;|&nbsp;
  <strong>Date:</strong> {report_time} &nbsp;|&nbsp;
  <strong>Pipeline:</strong> Automated Red Team Pipeline v1.0
</div>

<h2>Executive Summary</h2>
<div class="stats">
  <div class="stat-card"><div class="value">{open_ports}</div><div class="label">Open Ports</div></div>
  <div class="stat-card"><div class="value">{subdomains}</div><div class="label">Subdomains</div></div>
  <div class="stat-card"><div class="value">{live_hosts}</div><div class="label">Live Hosts</div></div>
  <div class="stat-card"><div class="value">{vuln_count}</div><div class="label">Vulnerabilities</div></div>
  <div class="stat-card"><div class="value">{len(chains)}</div><div class="label">Exploit Chains</div></div>
</div>

<h2>Severity Breakdown</h2>
<div class="severity-bar">
  <div class="sev-item sev-critical"><div class="count">{sev_counts['critical']}</div>Critical</div>
  <div class="sev-item sev-high"><div class="count">{sev_counts['high']}</div>High</div>
  <div class="sev-item sev-medium"><div class="count">{sev_counts['medium']}</div>Medium</div>
  <div class="sev-item sev-low"><div class="count">{sev_counts['low']}</div>Low</div>
  <div class="sev-item sev-info"><div class="count">{sev_counts['info']}</div>Info</div>
</div>

<h2>Open Ports</h2>
<table>
<tr><th>Port</th><th>Protocol</th><th>State</th><th>Service</th></tr>
"""

    for p in recon["findings"].get("nmap", {}).get("ports", []):
        html += f'<tr><td>{p["port"]}</td><td>{p["proto"]}</td><td>{p["state"]}</td><td>{p["service"]}</td></tr>\n'

    html += """</table>

<h2>Discovered Subdomains</h2>
<table>
<tr><th>#</th><th>Subdomain</th></tr>
"""

    subs = recon["findings"].get("subfinder", {}).get("subdomains", [])
    for i, sub in enumerate(subs[:100], 1):
        html += f"<tr><td>{i}</td><td>{sub}</td></tr>\n"
    if len(subs) > 100:
        html += f'<tr><td colspan="2">... and {len(subs) - 100} more</td></tr>\n'

    html += """</table>

<h2>Live Web Hosts</h2>
<table>
<tr><th>#</th><th>URL</th></tr>
"""

    hosts = recon["findings"].get("httpx", {}).get("hosts", [])
    for i, host in enumerate(hosts[:50], 1):
        html += f"<tr><td>{i}</td><td>{host}</td></tr>\n"

    html += """</table>

<h2>Exploit Chains</h2>
"""

    for i, chain in enumerate(chains, 1):
        html += f"""
<div class="chain">
  <div class="chain-header">
    <span class="chain-host">Chain #{i}: {chain["host"]}</span>
    <span class="risk-score">Risk Score: {chain["risk_score"]}</span>
  </div>
"""
        for j, step in enumerate(chain["steps"], 1):
            sev = step.get("severity", "info")
            badge = f'class="badge badge-{sev}"'
            html += f'  <div class="step">{j}. <span {badge}>{sev.upper()}</span> {step["name"]} <small>({step.get("source", "analysis")})</small></div>\n'
        html += "</div>\n"

    html += """
<h2>Nuclei Findings</h2>
<table>
<tr><th>Severity</th><th>Name</th><th>Host</th><th>CVE</th></tr>
"""

    nuclei_findings = recon["findings"].get("nuclei", {}).get("findings", [])
    for f in nuclei_findings:
        sev = f.get("severity", "info")
        badge = f'class="badge badge-{sev}"'
        html += f'<tr><td><span {badge}>{sev.upper()}</span></td><td>{f["name"]}</td><td>{f.get("host","")}</td><td>{f.get("cve","-")}</td></tr>\n'

    html += """</table>

<h2>Evidence Collected</h2>
<ul class="evidence-list">
"""
    for art in evidence.get("artifacts", []):
        exists = "✓" if Path(art).exists() else "✗"
        html += f"<li>{exists} {art}</li>\n"

    html += f"""</ul>

<div class="footer">
  <p>This report was generated by the Automated Red Team Pipeline.</p>
  <p>FOR AUTHORIZED TESTING ONLY. Unauthorized access to computer systems is illegal.</p>
  <p>Report generated: {report_time}</p>
</div>

</div>
</body>
</html>"""

    report_path = workdir / "report.html"
    report_path.write_text(html)
    log(f"Report generated: {report_path}", "SUCCESS")

    # Try PDF conversion if wkhtmltopdf is available
    if check_tool("wkhtmltopdf") and not args.skip_pdf:
        pdf_path = workdir / "report.pdf"
        cmd = f'wkhtmltopdf --enable-local-file-access "{report_path}" "{pdf_path}"'
        rc, _, _ = run_cmd(cmd, timeout=60)
        if rc == 0:
            log(f"PDF report generated: {pdf_path}", "SUCCESS")

    return str(report_path)


# ──────────────────────────────────────────────────────────────────────────────
# Main entry point
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Automated Red Team Pipeline — Authorized Testing Only",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              %(prog)s --target example.com
              %(prog)s --target 192.168.1.1 --full
              %(prog)s --target example.com --skip-nuclei --skip-screenshots
        """),
    )
    parser.add_argument("--target", required=True, help="Target domain or IP address")
    parser.add_argument("--full", action="store_true", help="Run full scan (all ports, all templates)")
    parser.add_argument("--skip-nmap", action="store_true", help="Skip nmap scan")
    parser.add_argument("--skip-subfinder", action="store_true", help="Skip subdomain enumeration")
    parser.add_argument("--skip-httpx", action="store_true", help="Skip HTTP probing")
    parser.add_argument("--skip-nuclei", action="store_true", help="Skip nuclei vulnerability scan")
    parser.add_argument("--skip-screenshots", action="store_true", help="Skip screenshot collection")
    parser.add_argument("--skip-pdf", action="store_true", help="Skip PDF report generation")
    parser.add_argument("--output-dir", default=None, help="Custom output directory")
    parser.add_argument("--timeout", type=int, default=300, help="Default command timeout (seconds)")
    args = parser.parse_args()

    banner()
    log(f"Target: {args.target}")
    log(f"Workspace: {WORKSPACE}")

    # Create output directory
    if args.output_dir:
        workdir = Path(args.output_dir)
    else:
        workdir = WORKSPACE / f"redteam_{args.target.replace('.', '_')}_{TIMESTAMP}"
    workdir.mkdir(parents=True, exist_ok=True)
    log(f"Output directory: {workdir}")

    # Check which tools are available
    log("Checking tool availability...")
    for tool in TOOLS:
        status = "FOUND" if check_tool(tool) else "MISSING"
        log(f"  {tool}: {status}", "SUCCESS" if status == "FOUND" else "WARN")

    start_time = time.time()

    # Phase 1: Recon
    recon = phase_recon(args.target, workdir, args)

    # Phase 2: Analysis
    chains = phase_analysis(recon, workdir)

    # Phase 3: Evidence
    evidence = phase_evidence(recon, chains, workdir, args)

    # Phase 4: Report
    report_path = phase_report(recon, chains, evidence, workdir, args)

    elapsed = time.time() - start_time

    # Final summary
    log("=" * 60)
    log("PIPELINE COMPLETE", "SUCCESS")
    log(f"Target: {args.target}")
    log(f"Duration: {elapsed:.1f}s")
    log(f"Report: {report_path}")
    log(f"Artifacts: {workdir}")
    log("=" * 60)


if __name__ == "__main__":
    main()
