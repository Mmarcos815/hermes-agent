#!/usr/bin/env python3
"""
Professional Engagement Report Generator
Generates a comprehensive, client-ready PDF engagement report from security findings.

Usage:
    python engagement_report.py findings.json -o engagement_report.py
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether, HRFlowable
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.legends import Legend
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SEVERITY_COLORS = {
    "critical": colors.HexColor("#dc2626"),
    "high": colors.HexColor("#ea580c"),
    "medium": colors.HexColor("#ca8a04"),
    "low": colors.HexColor("#16a34a"),
    "info": colors.HexColor("#2563eb"),
}

SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]

COMPLIANCE_MAPPINGS = {
    "critical": [
        ("PCI-DSS", "6.5.1 – Injection flaws"),
        ("HIPAA", "§164.312(a)(1) – Access Control"),
        ("SOC2", "CC6.1 – Logical Access Controls"),
    ],
    "high": [
        ("PCI-DSS", "6.5.7 – Broken authentication"),
        ("HIPAA", "§164.312(c)(1) – Integrity Controls"),
        ("SOC2", "CC7.1 – Security Operations"),
    ],
    "medium": [
        ("PCI-DSS", "6.5.10 – Broken authentication sessions"),
        ("HIPAA", "§164.312(b) – Audit Controls"),
        ("SOC2", "CC8.1 – Change Management"),
    ],
    "low": [
        ("PCI-DSS", "11.5 – Security headers"),
        ("HIPAA", "§164.308(a)(5)(ii)(C) – Log-in monitoring"),
        ("SOC2", "A1.2 – Availability monitoring"),
    ],
    "info": [
        ("PCI-DSS", "2.2.5 – Configuration standards"),
        ("HIPAA", "§164.308(a)(7)(ii)(E) – Info backup"),
        ("SOC2", "PI 1.4 – Privacy notices"),
    ],
}


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def load_findings(path: str) -> list[dict]:
    """Load findings from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data.get("findings", [data])
    return data


def count_by_severity(findings: list[dict]) -> dict[str, int]:
    counts = {s: 0 for s in SEVERITY_ORDER}
    for f in findings:
        sev = f.get("severity", "info").lower()
        counts[sev] = counts.get(sev, 0) + 1
    return counts


def compute_risk_rating(findings: list[dict]) -> str:
    """Calculate overall risk rating based on severity distribution."""
    counts = count_by_severity(findings)
    if counts["critical"] >= 2:
        return "CRITICAL"
    if counts["critical"] >= 1:
        return "HIGH"
    if counts["high"] >= 2:
        return "HIGH"
    if counts["high"] == 1:
        return "MEDIUM"
    if counts["medium"] >= 3:
        return "MEDIUM"
    if counts["medium"] >= 1:
        return "LOW"
    return "MINIMAL"


def average_cvss(findings: list[dict]) -> float:
    scores = [f.get("cvss", 0) for f in findings if f.get("cvss")]
    return round(sum(scores) / len(scores), 1) if scores else 0.0


# ---------------------------------------------------------------------------
# Chart builders
# ---------------------------------------------------------------------------

def build_severity_pie(findings: list[dict], width=300, height=180) -> Drawing:
    """Pie chart of severity distribution."""
    counts = count_by_severity(findings)
    drawing = Drawing(width, height)

    active = [s for s in SEVERITY_ORDER if counts[s] > 0]
    pie = Pie()
    pie.x = 70
    pie.y = 25
    pie.width = 110
    pie.height = 110
    pie.data = [counts[s] for s in active]
    pie.labels = [f"{s.capitalize()}\n({counts[s]})" for s in active]
    pie.slices.strokeWidth = 0.5
    pie.slices.fontSize = 7
    for i, sev in enumerate(active):
        pie.slices[i].fillColor = SEVERITY_COLORS[sev]
    drawing.add(pie)

    # Legend
    legend = Legend()
    legend.x = 200
    legend.y = 100
    legend.alignment = "right"
    legend.columnMaximum = 10
    legend.fontSize = 9
    legend.dx = 8
    legend.dy = 8
    legend.dxTextSpace = 4
    legend.deltay = 12
    legend.colorNamePairs = [(SEVERITY_COLORS[s], s.capitalize()) for s in active]
    drawing.add(legend)
    return drawing


def build_cvss_bar(findings: list[dict], width=400, height=180) -> Drawing:
    """Horizontal bar chart of CVSS scores per finding."""
    drawing = Drawing(width, height)
    scored = [(f.get("title", "Untitled")[:25], f.get("cvss", 0), f.get("severity", "info").lower())
              for f in findings if f.get("cvss")]

    if not scored:
        drawing.add(String(width / 2, height / 2, "No CVSS data", fontSize=12, fillColor=colors.grey))
        return drawing

    bar_h = 18
    y_start = (height - len(scored) * (bar_h + 4)) / 2 + len(scored) * (bar_h + 4)
    max_score = max(s for _, s, _ in scored) or 10

    for i, (title, score, sev) in enumerate(scored):
        y = y_start - i * (bar_h + 4)
        w = (score / 10.0) * (width - 120)
        drawing.add(Rect(110, y, w, bar_h, fillColor=SEVERITY_COLORS[sev]))
        drawing.add(String(105, y + 3, title, fontSize=7, fillColor=colors.black,
                           textAnchor="end"))
        drawing.add(String(115 + w, y + 3, str(score), fontSize=7,
                           fillColor=colors.HexColor("#334155")))

    drawing.add(String(width / 2, y_start + len(scored) * (bar_h + 4) + 8,
                       f"CVSS Scores ({len(scored)} findings)",
                       fontSize=10, fillColor=colors.black, textAnchor="middle"))
    return drawing


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def severity_badge(severity: str) -> str:
    sev = severity.lower()
    color = SEVERITY_COLORS.get(sev, colors.grey)
    hex_color = f"#{color.hexval()[2:]}"
    return f'<font color="{hex_color}"><b>{sev.upper()}</b></font>'


def build_executive_summary(findings: list[dict], styles) -> list:
    """Section 1: Executive Summary with business impact & risk rating."""
    elements = []
    counts = count_by_severity(findings)
    total = len(findings)
    risk = compute_risk_rating(findings)
    avg_cvss = average_cvss(findings)
    risk_color = {"CRITICAL": "#7f1d1d", "HIGH": "#dc2626", "MEDIUM": "#ca8a04",
                  "LOW": "#16a34a", "MINIMAL": "#2563eb"}.get(risk, "#334155")

    elements.append(Paragraph("1. Executive Summary", styles["Heading1"]))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1e293b")))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        f"This security engagement assessed the target application and identified "
        f"<b>{total} findings</b> spanning critical to informational severity. "
        f"The overall risk rating is <font color='{risk_color}'><b>{risk}</b></font>.",
        styles["Body"]
    ))
    elements.append(Spacer(1, 12))

    # Business impact table
    impact_data = [
        ["Metric", "Value"],
        ["Total Findings", str(total)],
        ["Critical / High", f"{counts['critical']} / {counts['high']}"],
        ["Average CVSS Score", str(avg_cvss)],
        ["Overall Risk Rating", risk],
        ["Estimated Remediation", "2–6 weeks"],
    ]
    table = Table(impact_data, colWidths=[200, 250])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 16))

    # Business impact narrative
    elements.append(Paragraph("Business Impact", styles["Heading2"]))
    if counts["critical"] > 0:
        elements.append(Paragraph(
            "Critical findings pose <b>immediate business risk</b>: unauthorized data access, "
            "financial fraud, and regulatory penalties are plausible. Remediation must begin "
            "<b>within 24 hours</b> for critical items.", styles["Body"]
        ))
    elif counts["high"] > 0:
        elements.append(Paragraph(
            "High-severity findings indicate <b>significant exposure</b>. While not immediately "
            "exploitable at scale, targeted attacks could lead to data loss and service disruption. "
            "Remediation should be prioritized within the next release cycle.",
            styles["Body"]
        ))
    else:
        elements.append(Paragraph(
            "Findings are primarily low-to-medium severity. Risk to business operations is "
            "<b>controlled but non-trivial</b>. Address as part of planned maintenance to reduce "
            "attack surface over time.", styles["Body"]
        ))
    elements.append(Spacer(1, 12))

    # Charts
    elements.append(build_severity_pie(findings))
    return elements


def build_technical_details(findings: list[dict], styles) -> list:
    """Section 2: Technical Details with reproduction steps & evidence."""
    elements = []
    elements.append(Paragraph("2. Technical Details", styles["Heading1"]))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1e293b")))
    elements.append(Spacer(1, 8))

    for i, f in enumerate(findings, 1):
        title = f.get("title", "Untitled")
        severity = f.get("severity", "info").lower()
        cvss = f.get("cvss", "N/A")
        affected = f.get("affected", "Unknown")

        elements.append(Paragraph(
            f"{i}. {title}  [{severity_badge(severity)}]  CVSS: {cvss}",
            styles["Heading2"]
        ))

        # Meta row
        meta = [
            ["Severity", severity.capitalize()],
            ["CVSS Score", str(cvss)],
            ["Affected Surface", affected],
            ["Discovered", f.get("date", "N/A")],
        ]
        meta_table = Table(meta, colWidths=[130, 320])
        meta_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 8))

        # Description
        if f.get("description"):
            elements.append(Paragraph("<b>Description</b>", styles["Heading3"]))
            elements.append(Paragraph(f["description"], styles["Body"]))

        # Reproduction steps
        elements.append(Paragraph("<b>Reproduction Steps</b>", styles["Heading3"]))
        affected_url = f.get("affected", "the target endpoint")
        elements.append(Paragraph(
            f"1. Navigate to <font face='Courier'>{affected_url}</font><br/>"
            f"2. Identify the injectable/input parameter<br/>"
            f"3. Submit the malicious payload documented below<br/>"
            f"4. Observe the application's response confirming the vulnerability",
            styles["Body"]
        ))

        # Evidence
        if f.get("evidence"):
            elements.append(Paragraph("<b>Evidence</b>", styles["Heading3"]))
            elements.append(Paragraph(
                f'<font face="Courier" size="9">{f["evidence"]}</font>',
                styles["Body"]
            ))

        # Remediation hint (full roadmap in Section 3)
        if f.get("remediation"):
            elements.append(Paragraph("<b>Suggested Fix</b>", styles["Heading3"]))
            elements.append(Paragraph(f["remediation"], styles["Body"]))

        elements.append(Spacer(1, 6))
        elements.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))
        elements.append(Spacer(1, 6))

    return elements


def build_remediation_roadmap(findings: list[dict], styles) -> list:
    """Section 3: Remediation Roadmap with prioritized fixes."""
    elements = []
    elements.append(Paragraph("3. Remediation Roadmap", styles["Heading1"]))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1e293b")))
    elements.append(Spacer(1, 8))

    # Priority order: critical > high > medium > low > info
    ordered = sorted(findings, key=lambda f: (
        SEVERITY_ORDER.index(f.get("severity", "info").lower())
    ))

    roadmap_data = [
        ["Priority", "Finding", "Action", "Timeline"],
    ]
    for idx, f in enumerate(ordered, 1):
        sev = f.get("severity", "info").lower()
        priority = "P0 – Critical" if sev == "critical" else \
                   "P1 – High" if sev == "high" else \
                   "P2 – Medium" if sev == "medium" else \
                   "P3 – Low" if sev == "low" else "P4 – Info"
        action = f.get("remediation", "Review and address.")
        timeline = "24 hours" if sev == "critical" else \
                   "1 week" if sev == "high" else \
                   "2 weeks" if sev == "medium" else \
                   "30 days" if sev == "low" else "Next sprint"
        roadmap_data.append([
            Paragraph(f'<b>{priority}</b>', styles["Body"]),
            Paragraph(f.get("title", "Untitled")[:35], styles["Body"]),
            Paragraph(action[:60], styles["Body"]),
            Paragraph(timeline, styles["Body"]),
        ])

    col_widths = [85, 130, 170, 65]
    table = Table(roadmap_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 16))

    # Quick wins section
    elements.append(Paragraph("Quick Wins (Address Within 48 Hours)", styles["Heading2"]))
    quick_wins = [f for f in ordered if f.get("severity", "info").lower() in ("critical", "high")]
    if quick_wins:
        for qf in quick_wins:
            elements.append(Paragraph(f"• <b>{qf.get('title', '')}</b> — {qf.get('remediation', '')}", styles["Body"]))
    else:
        elements.append(Paragraph("No critical or high findings requiring immediate action.", styles["Body"]))

    return elements


def build_compliance_mapping(findings: list[dict], styles) -> list:
    """Section 4: Compliance Mapping (PCI-DSS, HIPAA, SOC2)."""
    elements = []
    elements.append(Paragraph("4. Compliance Mapping", styles["Heading1"]))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1e293b")))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "Each finding has been mapped to relevant regulatory and framework controls. "
        "This mapping assists in prioritizing remediation based on compliance obligations.",
        styles["Body"]
    ))
    elements.append(Spacer(1, 10))

    # Build compliance table
    comp_data = [["Finding", "Severity", "PCI-DSS", "HIPAA", "SOC2"]]
    for f in findings:
        sev = f.get("severity", "info").lower()
        mappings = COMPLIANCE_MAPPINGS.get(sev, COMPLIANCE_MAPPINGS["info"])
        pci = mappings[0][1] if len(mappings) > 0 else "—"
        hipaa = mappings[1][1] if len(mappings) > 1 else "—"
        soc2 = mappings[2][1] if len(mappings) > 2 else "—"
        comp_data.append([
            Paragraph(f.get("title", "")[:30], styles["Body"]),
            Paragraph(severity_badge(sev), styles["Body"]),
            Paragraph(pci, styles["Body"]),
            Paragraph(hipaa, styles["Body"]),
            Paragraph(soc2, styles["Body"]),
        ])

    col_w = [100, 55, 120, 100, 85]
    table = Table(comp_data, colWidths=col_w, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 16))

    # Compliance summary
    elements.append(Paragraph("Framework Summary", styles["Heading2"]))
    elements.append(Paragraph(
        "<b>PCI-DSS v4.0:</b> Critical and high findings must be addressed before "
        "cardholder data handling resumes. Remediation evidence required for SAQ-D / ROC.",
        styles["Body"]
    ))
    elements.append(Paragraph(
        "<b>HIPAA:</b> Findings affecting ePHI trigger breach-risk assessment. "
        "Corrective action plans per §164.308(a)(8) are recommended.",
        styles["Body"]
    ))
    elements.append(Paragraph(
        "<b>SOC2 (2017):</b> All high/critical findings impact CC-series control "
        "effectiveness. Remediation required before next audit window.",
        styles["Body"]
    ))
    return elements


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def build_report(findings: list[dict], output_path: str):
    """Generate the full engagement report PDF."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=48,
        leftMargin=48,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ReportTitle", parent=styles["Title"],
                              fontSize=26, spaceAfter=22, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="ReportSub", parent=styles["Normal"],
                              fontSize=11, textColor=colors.HexColor("#64748b"),
                              alignment=TA_CENTER, spaceAfter=24))
    styles.add(ParagraphStyle(name="Body", parent=styles["Normal"],
                              fontSize=10, leading=14, spaceAfter=6))
    styles.add(ParagraphStyle(name="H2", parent=styles["Heading2"],
                              fontSize=14, spaceBefore=14, spaceAfter=6,
                              textColor=colors.HexColor("#1e293b")))
    styles.add(ParagraphStyle(name="H3", parent=styles["Heading3"],
                              fontSize=10, spaceBefore=8, spaceAfter=4,
                              textColor=colors.HexColor("#475569")))
    styles.add(ParagraphStyle(name="Footer", parent=styles["Normal"],
                              fontSize=8, textColor=colors.HexColor("#94a3b8"),
                              alignment=TA_CENTER))

    elements: list = []

    # ---- Cover page ----
    elements.append(Spacer(1, 100))
    elements.append(Paragraph("Engagement Report", styles["ReportTitle"]))
    elements.append(Paragraph(
        f"Security Assessment — {datetime.now().strftime('%B %Y')}",
        styles["ReportSub"]
    ))
    elements.append(Spacer(1, 20))

    counts = count_by_severity(findings)
    risk = compute_risk_rating(findings)
    risk_color = {"CRITICAL": "#7f1d1d", "HIGH": "#dc2626", "MEDIUM": "#ca8a04",
                  "LOW": "#16a34a", "MINIMAL": "#2563eb"}.get(risk, "#334155")

    cover_stats = [
        ["Total Findings", str(len(findings))],
        ["Risk Rating", f"{risk}"],
        ["Critical / High", f"{counts['critical']} / {counts['high']}"],
        ["Date", datetime.now().strftime("%Y-%m-%d")],
        ["Classification", "CONFIDENTIAL"],
    ]
    cover_table = Table(cover_stats, colWidths=[180, 180])
    cover_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TEXTCOLOR", (1, 1), (1, 1), colors.HexColor(risk_color)),
        ("FONTNAME", (1, 1), (1, 1), "Helvetica-Bold"),
    ]))
    elements.append(cover_table)

    # CVSS chart on cover
    elements.append(Spacer(1, 30))
    elements.append(build_cvss_bar(findings))

    elements.append(PageBreak())

    # ---- Table of Contents ----
    elements.append(Paragraph("Table of Contents", styles["Heading1"]))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1e293b")))
    elements.append(Spacer(1, 12))
    for idx, title in enumerate([
        "1. Executive Summary",
        "2. Technical Details",
        "3. Remediation Roadmap",
        "4. Compliance Mapping",
    ], 1):
        elements.append(Paragraph(f"{title}", styles["Body"]))
        elements.append(Spacer(1, 6))

    elements.append(PageBreak())

    # ---- Section 1: Executive Summary ----
    elements.extend(build_executive_summary(findings, styles))
    elements.append(PageBreak())

    # ---- Section 2: Technical Details ----
    elements.extend(build_technical_details(findings, styles))
    elements.append(PageBreak())

    # ---- Section 3: Remediation Roadmap ----
    elements.extend(build_remediation_roadmap(findings, styles))
    elements.append(PageBreak())

    # ---- Section 4: Compliance Mapping ----
    elements.extend(build_compliance_mapping(findings, styles))

    # ---- Footer on every page ----
    def on_page(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#94a3b8"))
        canvas.drawCentredString(
            letter[0] / 2, 30,
            f"Confidential — Security Engagement Report — Page {doc.page} — {datetime.now().strftime('%Y-%m-%d')}"
        )
        canvas.restoreState()

    doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
    print(f"Engagement report generated: {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate professional engagement report PDF")
    parser.add_argument("input", help="Path to JSON findings file")
    parser.add_argument("-o", "--output", default="engagement_report.pdf",
                        help="Output PDF path (default: engagement_report.pdf)")
    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    findings = load_findings(args.input)
    if not findings:
        print("Error: No findings found in input file", file=sys.stderr)
        sys.exit(1)

    build_report(findings, args.output)


if __name__ == "__main__":
    main()
