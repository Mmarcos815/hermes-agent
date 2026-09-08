#!/usr/bin/env python3
"""
Automated Reporting System
Generates professional security reports from findings.
"""

import json
import os
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent
REPORTS_DIR = PROJECT_ROOT / "reports"

# ---------------------------------------------------------------------------
# CVSS Calculator
# ---------------------------------------------------------------------------

def cvss_calculator(
    av: str = "N",  # Attack Vector: N/A/L/P
    ac: str = "L",  # Attack Complexity: L/H
    pr: str = "N",  # Privileges Required: N/L/H
    ui: str = "N",  # User Interaction: N/R
    s: str = "U",   # Scope: U/C
    c: str = "H",   # Confidentiality: N/L/H
    i: str = "H",   # Integrity: N/L/H
    a: str = "H",   # Availability: N/L/H
) -> Dict:
    """Calculate CVSS v3.1 base score."""
    
    # Metric values
    av_values = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.20}
    ac_values = {"L": 0.77, "H": 0.44}
    pr_values = {"N": 0.85, "L": 0.62, "H": 0.27}  # Scope unchanged
    pr_values_c = {"N": 0.85, "L": 0.68, "H": 0.50}  # Scope changed
    ui_values = {"N": 0.85, "R": 0.62}
    cia_values = {"N": 0.0, "L": 0.22, "H": 0.56}
    
    # Get values
    av_val = av_values.get(av, 0.85)
    ac_val = ac_values.get(ac, 0.77)
    if s == "C":
        pr_val = pr_values_c.get(pr, 0.85)
    else:
        pr_val = pr_values.get(pr, 0.85)
    ui_val = ui_values.get(ui, 0.85)
    c_val = cia_values.get(c, 0.56)
    i_val = cia_values.get(i, 0.56)
    a_val = cia_values.get(a, 0.56)
    
    # Calculate Impact Sub Score (ISS)
    iss = 1 - ((1 - c_val) * (1 - i_val) * (1 - a_val))
    
    # Calculate Impact
    if s == "U":
        impact = 6.42 * iss
    else:
        impact = 7.52 * (iss - 0.029) - 3.25 * ((iss - 0.02) ** 15)
    
    # Calculate Exploitability
    exploitability = 8.22 * av_val * ac_val * pr_val * ui_val
    
    # Calculate Base Score
    if impact <= 0:
        base_score = 0.0
    elif s == "U":
        base_score = min(impact + exploitability, 10.0)
    else:
        base_score = min(1.08 * (impact + exploitability), 10.0)
    
    # Round up to nearest 0.1
    base_score = round(base_score * 10) / 10
    if base_score == int(base_score):
        base_score = int(base_score)
    
    # Severity
    if base_score >= 9.0:
        severity = "Critical"
    elif base_score >= 7.0:
        severity = "High"
    elif base_score >= 4.0:
        severity = "Medium"
    elif base_score > 0:
        severity = "Low"
    else:
        severity = "Informational"
    
    # Vector string
    vector = f"CVSS:3.1/AV:{av}/AC:{ac}/PR:{pr}/UI:{ui}/S:{s}/C:{c}/I:{i}/A:{a}"
    
    return {
        "score": base_score,
        "severity": severity,
        "vector": vector,
        "impact": round(impact, 1),
        "exploitability": round(exploitability, 1),
    }


# ---------------------------------------------------------------------------
# Report Generator
# ---------------------------------------------------------------------------

class ReportGenerator:
    """Generate security reports from findings."""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.findings = []
        self.metadata = {
            "title": "Security Assessment Report",
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "version": "1.0",
        }
    
    def set_metadata(self, title: str = None, **kwargs):
        """Set report metadata."""
        if title:
            self.metadata["title"] = title
        self.metadata.update(kwargs)
    
    def add_finding(
        self,
        title: str,
        description: str,
        severity: str = None,
        cvss_score: float = None,
        cvss_vector: str = None,
        affected: str = None,
        evidence: str = None,
        remediation: str = None,
        references: List[str] = None,
        **kwargs,
    ):
        """Add a finding to the report."""
        finding = {
            "id": f"FIND-{len(self.findings) + 1:03d}",
            "title": title,
            "description": description,
            "severity": severity or "Informational",
            "cvss_score": cvss_score or 0.0,
            "cvss_vector": cvss_vector or "N/A",
            "affected": affected or "Unknown",
            "evidence": evidence or "N/A",
            "remediation": remediation or "N/A",
            "references": references or [],
        }
        finding.update(kwargs)
        self.findings.append(finding)
    
    def add_finding_from_dict(self, finding: Dict):
        """Add a finding from a dictionary."""
        self.add_finding(**finding)
    
    def load_findings_json(self, filepath: str):
        """Load findings from a JSON file."""
        with open(filepath) as f:
            data = json.load(f)
            if isinstance(data, list):
                for finding in data:
                    self.add_finding_from_dict(finding)
            elif isinstance(data, dict) and "findings" in data:
                for finding in data["findings"]:
                    self.add_finding_from_dict(finding)
    
    def generate_markdown(self, output_file: str = None) -> str:
        """Generate a Markdown report."""
        lines = []
        lines.append(f"# {self.metadata['title']}")
        lines.append("")
        lines.append(f"**Date:** {self.metadata['date']}")
        lines.append(f"**Version:** {self.metadata['version']}")
        lines.append(f"**Total Findings:** {len(self.findings)}")
        lines.append("")
        
        # Executive Summary
        lines.append("## Executive Summary")
        lines.append("")
        severity_counts = {}
        for f in self.findings:
            sev = f["severity"]
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        lines.append("| Severity | Count |")
        lines.append("|----------|-------|")
        for sev in ["Critical", "High", "Medium", "Low", "Informational"]:
            count = severity_counts.get(sev, 0)
            if count > 0:
                lines.append(f"| {sev} | {count} |")
        lines.append("")
        
        # Findings
        lines.append("## Findings")
        lines.append("")
        
        # Sort by severity then score
        severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Informational": 4}
        sorted_findings = sorted(
            self.findings,
            key=lambda x: (severity_order.get(x["severity"], 5), -x["cvss_score"])
        )
        
        for finding in sorted_findings:
            lines.append(f"### {finding['id']}: {finding['title']}")
            lines.append("")
            lines.append(f"- **Severity:** {finding['severity']}")
            lines.append(f"- **CVSS Score:** {finding['cvss_score']} ({finding['cvss_vector']})")
            lines.append(f"- **Affected:** {finding['affected']}")
            lines.append("")
            lines.append("**Description:**")
            lines.append("")
            lines.append(finding["description"])
            lines.append("")
            
            if finding.get("evidence") != "N/A":
                lines.append("**Evidence:**")
                lines.append("")
                lines.append(finding["evidence"])
                lines.append("")
            
            if finding.get("remediation") != "N/A":
                lines.append("**Remediation:**")
                lines.append("")
                lines.append(finding["remediation"])
                lines.append("")
            
            if finding.get("references"):
                lines.append("**References:**")
                lines.append("")
                for ref in finding["references"]:
                    lines.append(f"- {ref}")
                lines.append("")
        
        # Appendices
        lines.append("## Appendices")
        lines.append("")
        lines.append("### CVSS Scoring Methodology")
        lines.append("")
        lines.append("CVSS v3.1 was used to score findings. Scores range from 0.0 to 10.0:")
        lines.append("- Critical: 9.0-10.0")
        lines.append("- High: 7.0-8.9")
        lines.append("- Medium: 4.0-6.9")
        lines.append("- Low: 0.1-3.9")
        lines.append("- Informational: 0.0")
        
        report = "\n".join(lines)
        
        if output_file:
            output_path = self.output_dir / output_file
            output_path.write_text(report, encoding="utf-8")
            print(f"Report saved: {output_path}")
        
        return report
    
    def generate_html(self, output_file: str = None) -> str:
        """Generate an HTML report."""
        md_report = self.generate_markdown()
        
        # Simple markdown to HTML conversion
        html_parts = []
        html_parts.append("""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Security Report</title>
<style>
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }
h1 { color: #1a1a1a; border-bottom: 2px solid #e74c3c; padding-bottom: 10px; }
h2 { color: #2c3e50; margin-top: 40px; }
h3 { color: #34495e; }
table { border-collapse: collapse; width: 100%; margin: 20px 0; }
th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
th { background: #f5f5f5; }
.critical { color: #e74c3c; font-weight: bold; }
.high { color: #e67e22; font-weight: bold; }
.medium { color: #f39c12; }
.low { color: #3498db; }
.informational { color: #95a5a6; }
code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }
pre { background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }
</style>
</head>
<body>""")
        
        # Convert markdown to basic HTML
        lines = md_report.split("\n")
        in_table = False
        in_code = False
        in_list = False
        
        for line in lines:
            if line.startswith("```"):
                if in_code:
                    html_parts.append("</code></pre>")
                    in_code = False
                else:
                    html_parts.append("<pre><code>")
                    in_code = True
                continue
            
            if in_code:
                html_parts.append(line.replace("<", "&lt;").replace(">", "&gt;"))
                continue
            
            if line.startswith("# "):
                html_parts.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("## "):
                html_parts.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("### "):
                html_parts.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith("| ") and "|" in line[1:]:
                cells = [c.strip() for c in line.split("|")[1:-1]]
                if all(set(c) <= set("-: ") for c in cells):
                    continue
                if not in_table:
                    html_parts.append("<table><thead><tr>")
                    for cell in cells:
                        html_parts.append(f"<th>{cell}</th>")
                    html_parts.append("</tr></thead><tbody>")
                    in_table = True
                else:
                    html_parts.append("<tr>")
                    for cell in cells:
                        html_parts.append(f"<td>{cell}</td>")
                    html_parts.append("</tr>")
            else:
                if in_table:
                    html_parts.append("</tbody></table>")
                    in_table = False
                
                if line.startswith("- "):
                    if not in_list:
                        html_parts.append("<ul>")
                        in_list = True
                    html_parts.append(f"<li>{line[2:]}</li>")
                elif line.startswith("**") and "**:" in line:
                    if in_list:
                        html_parts.append("</ul>")
                        in_list = False
                    parts = line.split(":", 1)
                    html_parts.append(f"<p><strong>{parts[0].strip('* ')}</strong>: {parts[1] if len(parts) > 1 else ''}</p>")
                elif line.strip() == "":
                    if in_list:
                        html_parts.append("</ul>")
                        in_list = False
                    html_parts.append("<br>")
                else:
                    if in_list:
                        html_parts.append("</ul>")
                        in_list = False
                    html_parts.append(f"<p>{line}</p>")
        
        if in_table:
            html_parts.append("</tbody></table>")
        if in_list:
            html_parts.append("</ul>")
        
        html_parts.append("</body></html>")
        report = "\n".join(html_parts)
        
        if output_file:
            output_path = self.output_dir / output_file
            output_path.write_text(report, encoding="utf-8")
            print(f"HTML report saved: {output_path}")
        
        return report
    
    def generate_csv(self, output_file: str = None) -> str:
        """Generate a CSV summary."""
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(["ID", "Title", "Severity", "CVSS Score", "Vector", "Affected"])
        
        # Findings
        for finding in self.findings:
            writer.writerow([
                finding["id"],
                finding["title"],
                finding["severity"],
                finding["cvss_score"],
                finding["cvss_vector"],
                finding["affected"],
            ])
        
        csv_content = output.getvalue()
        
        if output_file:
            output_path = self.output_dir / output_file
            output_path.write_text(csv_content, encoding="utf-8")
            print(f"CSV saved: {output_path}")
        
        return csv_content
    
    def generate_json(self, output_file: str = None) -> str:
        """Generate a JSON report."""
        report = {
            "metadata": self.metadata,
            "findings": self.findings,
            "summary": {
                "total": len(self.findings),
                "by_severity": {},
            },
        }
        
        for finding in self.findings:
            sev = finding["severity"]
            report["summary"]["by_severity"][sev] = report["summary"]["by_severity"].get(sev, 0) + 1
        
        json_content = json.dumps(report, indent=2)
        
        if output_file:
            output_path = self.output_dir / output_file
            output_path.write_text(json_content, encoding="utf-8")
            print(f"JSON report saved: {output_path}")
        
        return json_content


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated Reporting System")
    subparsers = parser.add_subparsers(dest="command")
    
    # CVSS calculator
    cvss_parser = subparsers.add_parser("cvss", help="Calculate CVSS score")
    cvss_parser.add_argument("--vector", help="CVSS vector string")
    cvss_parser.add_argument("--av", default="N")
    cvss_parser.add_argument("--ac", default="L")
    cvss_parser.add_argument("--pr", default="N")
    cvss_parser.add_argument("--ui", default="N")
    cvss_parser.add_argument("--s", default="U")
    cvss_parser.add_argument("--c", default="H")
    cvss_parser.add_argument("--i", default="H")
    cvss_parser.add_argument("--a", default="H")
    
    # Generate report
    report_parser = subparsers.add_parser("generate", help="Generate report")
    report_parser.add_argument("--findings", help="Path to findings JSON file")
    report_parser.add_argument("--format", choices=["markdown", "html", "csv", "json", "all"], default="all")
    report_parser.add_argument("--output", default="report")
    
    args = parser.parse_args()
    
    if args.command == "cvss":
        if args.vector:
            print(f"Vector: {args.vector}")
            print("Use individual flags (--av, --ac, etc.) for calculation")
        else:
            result = cvss_calculator(
                av=args.av, ac=args.ac, pr=args.pr, ui=args.ui,
                s=args.s, c=args.c, i=args.i, a=args.a
            )
            print(f"CVSS Score: {result['score']} ({result['severity']})")
            print(f"Vector: {result['vector']}")
            print(f"Impact: {result['impact']}")
            print(f"Exploitability: {result['exploitability']}")
    
    elif args.command == "generate":
        reporter = ReportGenerator()
        
        if args.findings:
            reporter.load_findings_json(args.findings)
        
        if args.format in ["markdown", "all"]:
            reporter.generate_markdown(f"{args.output}.md")
        if args.format in ["html", "all"]:
            reporter.generate_html(f"{args.output}.html")
        if args.format in ["csv", "all"]:
            reporter.generate_csv(f"{args.output}.csv")
        if args.format in ["json", "all"]:
            reporter.generate_json(f"{args.output}.json")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
