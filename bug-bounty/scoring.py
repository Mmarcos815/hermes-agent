#!/usr/bin/env python3
"""Bug Bounty Scoring System — CVSS 3.1 calculator, report generator, exporters."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# CVSS 3.1 metrics
# ---------------------------------------------------------------------------

AV = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.20}
AC = {"L": 0.77, "H": 0.44}
PR_NC = {"N": 0.85, "L": 0.62, "H": 0.27}
PR_C = {"N": 0.85, "L": 0.68, "H": 0.50}
UI = {"N": 0.85, "R": 0.62}
IMP = {"N": 0.0, "L": 0.22, "H": 0.56}

META: dict[str, dict[str, str]] = {
    "AV": {"N": "Network", "A": "Adjacent", "L": "Local", "P": "Physical"},
    "AC": {"L": "Low", "H": "High"},
    "PR": {"N": "None", "L": "Low", "H": "High"},
    "UI": {"N": "None", "R": "Required"},
    "S": {"U": "Unchanged", "C": "Changed"},
    "C": {"N": "None", "L": "Low", "H": "High"},
    "I": {"N": "None", "L": "Low", "H": "High"},
    "A": {"N": "None", "L": "Low", "H": "High"},
}
REQ = ["AV", "AC", "PR", "UI", "S", "C", "I", "A"]


def severity(score: float) -> str:
    if score == 0.0:
        return "None"
    if score < 4.0:
        return "Low"
    if score < 7.0:
        return "Medium"
    if score < 9.0:
        return "High"
    return "Critical"


# ---------------------------------------------------------------------------
# CVSS calculator
# ---------------------------------------------------------------------------

@dataclass
class CVSSResult:
    vector: str
    base_score: float
    severity: str
    metrics: dict[str, str] = field(default_factory=dict)


def parse_vector(v: str) -> dict[str, str]:
    if v.startswith("CVSS:3.1/"):
        v = v[9:]
    return {c: val for c, val in (p.split(":", 1) for p in v.split("/") if ":" in p)}


def calculate_cvss(vector: str) -> CVSSResult:
    m = parse_vector(vector)
    missing = [x for x in REQ if x not in m]
    if missing:
        raise ValueError(f"Missing: {', '.join(missing)}")
    for code, val in m.items():
        if val not in META.get(code, {}):
            raise ValueError(f"Invalid '{val}' for {code}")
    sc = m["S"] == "C"
    pr = (PR_C if sc else PR_NC)[m["PR"]]
    exploit = 8.22 * AV[m["AV"]] * AC[m["AC"]] * pr * UI[m["UI"]]
    iss = 1 - (1 - IMP[m["C"]]) * (1 - IMP[m["I"]]) * (1 - IMP[m["A"]])
    impact = 7.52 * (iss - 0.029) - 3.25 * ((iss - 0.02) ** 15) if sc else 6.42 * iss
    base = math.ceil(max(0.0, min(10.0, impact + exploit)) * 10) / 10.0
    v = vector if vector.startswith("CVSS:3.1/") else f"CVSS:3.1/{vector}"
    return CVSSResult(v, base, severity(base), {c: META[c][val] for c, val in m.items()})


# ---------------------------------------------------------------------------
# Finding & report
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    id: str
    title: str
    description: str
    cvss_vector: str
    severity: str = ""
    score: float = 0.0
    evidence: list[str] = field(default_factory=list)
    remediation: str = ""
    references: list[str] = field(default_factory=list)
    cvss_metrics: dict[str, str] = field(default_factory=dict)


def analyze_finding(*, finding_id: str, title: str, description: str,
                     cvss_vector: str, evidence: list[str] | None = None,
                     remediation: str = "", references: list[str] | None = None) -> Finding:
    r = calculate_cvss(cvss_vector)
    return Finding(finding_id, title, description, r.vector, r.severity, r.base_score,
                   evidence or [], remediation, references or [], r.metrics)


@dataclass
class Report:
    target: str
    date: str = ""
    findings: list[Finding] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.date:
            self.date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if not self.summary:
            self.summary = {s: 0 for s in ("Critical", "High", "Medium", "Low", "None")}
            for f in self.findings:
                self.summary[f.severity] += 1

    def to_markdown(self) -> str:
        h = [f"# Bug Bounty Report — {self.target}", "", f"**Date:** {self.date}",
             f"**Total Findings:** {len(self.findings)}", "", "## Severity Summary", "",
             "| Severity | Count |", "|----------|-------|"]
        for s in ("Critical", "High", "Medium", "Low", "None"):
            h.append(f"| {s} | {self.summary.get(s, 0)} |")
        h += ["", "## Findings", ""]
        for f in self.findings:
            h += [f"### {f.id}: {f.title}", "",
                  f"- **Severity:** {f.severity}", f"- **CVSS Score:** {f.score}",
                  f"- **CVSS Vector:** `{f.cvss_vector}`", "",
                  f"**Description:** {f.description}", ""]
            if f.evidence:
                h.append("**Evidence:**")
                h += [f"- {e}" for e in f.evidence] + [""]
            if f.remediation:
                h += [f"**Remediation:** {f.remediation}", ""]
            if f.references:
                h.append("**References:**")
                h += [f"- {r}" for r in f.references] + [""]
        return "\n".join(h)

    def to_json(self) -> str:
        return json.dumps({"target": self.target, "date": self.date, "summary": self.summary,
                           "findings": [asdict(f) for f in self.findings]}, indent=2)

    def to_html(self) -> str:
        sc = lambda s: s.lower()
        fh = []
        for f in self.findings:
            ev = "".join(f"<li>{e}</li>" for e in f.evidence) or "<li>None</li>"
            rf = "".join(f'<li><a href="{r}">{r}</a></li>' for r in f.references) or "<li>None</li>"
            fh.append(f'''<div class="finding {sc(f.severity)}"><h3>{f.id}: {f.title}</h3>
<p><strong>Severity:</strong> <span class="badge {sc(f.severity)}">{f.severity}</span>
<strong>CVSS:</strong> {f.score} <code>{f.cvss_vector}</code></p>
<p><strong>Description:</strong> {f.description}</p>
<details><summary>Evidence</summary><ul>{ev}</ul></details>
<details><summary>Remediation</summary><p>{f.remediation or 'N/A'}</p></details>
<details><summary>References</summary><ul>{rf}</ul></div>''')
        rows = "\n".join(f'<tr><td>{s}</td><td class="{sc(s)}">{c}</td></tr>'
                         for s, c in self.summary.items() if c > 0)
        return f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>Bug Bounty Report — {self.target}</title>
<style>
body{{font-family:sans-serif;max-width:900px;margin:2rem auto}}
.badge{{padding:2px 8px;border-radius:4px;color:#fff;font-weight:bold}}
.badge.critical{{background:#d32f2f}}.badge.high{{background:#f57c00}}
.badge.medium{{background:#fbc02d;color:#000}}.badge.low{{background:#388e3c}}
.badge.none{{background:#757575}}.finding{{border-left:4px solid #ccc;padding-left:1rem;margin-bottom:2rem}}
.finding.critical{{border-color:#d32f2f}}.finding.high{{border-color:#f57c00}}
.finding.medium{{border-color:#fbc02d}}.finding.low{{border-color:#388e3c}}
table{{border-collapse:collapse}}td,th{{padding:4px 12px;border-bottom:1px solid #eee}}
</style></head><body>
<h1>Bug Bounty Report — {self.target}</h1><p><strong>Date:</strong> {self.date}</p>
<h2>Severity Summary</h2><table><tr><th>Severity</th><th>Count</th></tr>
{rows}</table><h2>Findings</h2>{"".join(fh)}</body></html>'''


def export_report(report: Report, path: str, fmt: str | None = None) -> str:
    fmt = fmt or ("json" if path.endswith(".json") else "html" if path.endswith(".html") else "md")
    fn = (report.to_markdown if fmt in ("md", "markdown") else
          report.to_json if fmt == "json" else
          report.to_html if fmt == "html" else None)
    if fn is None:
        raise ValueError(f"Unknown format '{fmt}'")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(fn())
    return fn()


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def demo() -> None:
    findings = [
        analyze_finding(
            finding_id="BH-001", title="SQL Injection in Login Endpoint",
            description="User input concatenated into SQL without parameterization.",
            cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
            evidence=["' OR 1=1-- returned all rows", "sqlmap confirmed"],
            remediation="Use parameterized queries.",
            references=["https://owasp.org/Top10/A03_2021-Injection/"],
        ),
        analyze_finding(
            finding_id="BH-002", title="Reflected XSS on Search",
            description="Search term reflected without escaping.",
            cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N",
            evidence=["<script>alert(1)</script> executed"],
            remediation="Apply output encoding.",
        ),
    ]
    report = Report(target="example.com", findings=findings)
    print(report.to_markdown())
    print("\n--- JSON ---\n")
    print(report.to_json())
    print(f"\n--- Summary: {report.summary} ---")


if __name__ == "__main__":
    demo()
