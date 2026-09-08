#!/usr/bin/env python3
"""
PDF Report Generator
Generates professional PDF reports from security findings in JSON format.

Usage:
    python pdf_report.py findings.json -o report.pdf [--format detailed|summary|executive]
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
    PageBreak, Image, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.legends import Legend
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


SEVERITY_COLORS = {
    "critical": colors.HexColor("#dc2626"),
    "high": colors.HexColor("#ea580c"),
    "medium": colors.HexColor("#ca8a04"),
    "low": colors.HexColor("#16a34a"),
    "info": colors.HexColor("#2563eb"),
}

SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]


def load_findings(path: str) -> list[dict]:
    """Load findings from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data.get("findings", [data])
    return data


def count_by_severity(findings: list[dict]) -> dict[str, int]:
    """Count findings grouped by severity."""
    counts = {s: 0 for s in SEVERITY_ORDER}
    for f in findings:
        sev = f.get("severity", "info").lower()
        counts[sev] = counts.get(sev, 0) + 1
    return counts


def build_severity_chart(findings: list[dict], width=400, height=200) -> Drawing:
    """Build a bar chart of severity distribution."""
    counts = count_by_severity(findings)
    drawing = Drawing(width, height)

    chart = VerticalBarChart()
    chart.x = 50
    chart.y = 50
    chart.width = width - 100
    chart.height = height - 80
    chart.data = [[counts[s] for s in SEVERITY_ORDER]]
    chart.categoryAxis.categoryNames = [s.capitalize() for s in SEVERITY_ORDER]
    chart.categoryAxis.labels.fontSize = 9
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = max(counts.values()) + 1 if counts.values() else 5
    chart.valueAxis.valueStep = 1
    chart.bars[0].fillColor = colors.HexColor("#3b82f6")
    chart.barWidth = 30

    # Color each bar by severity
    for i, sev in enumerate(SEVERITY_ORDER):
        chart.bars[0].fillColor = SEVERITY_COLORS.get(sev, colors.grey)

    drawing.add(chart)
    return drawing


def build_pie_chart(findings: list[dict], width=300, height=200) -> Drawing:
    """Build a pie chart of severity distribution."""
    counts = count_by_severity(findings)
    drawing = Drawing(width, height)

    pie = Pie()
    pie.x = 65
    pie.y = 35
    pie.width = 120
    pie.height = 120
    pie.data = [counts[s] for s in SEVERITY_ORDER if counts[s] > 0]
    pie.labels = [s.capitalize() for s in SEVERITY_ORDER if counts[s] > 0]
    pie.slices.strokeWidth = 0.5
    pie.slices.fontSize = 8

    active_sevs = [s for s in SEVERITY_ORDER if counts[s] > 0]
    for i, sev in enumerate(active_sevs):
        pie.slices[i].fillColor = SEVERITY_COLORS.get(sev, colors.grey)

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
    legend.colorNamePairs = [
        (SEVERITY_COLORS.get(s, colors.grey), s.capitalize())
        for s in active_sevs
    ]
    drawing.add(legend)

    return drawing


def build_timeline_chart(findings: list[dict], width=450, height=150) -> Drawing:
    """Build a simple timeline visualization."""
    drawing = Drawing(width, height)

    # Sort findings by date if available
    dated = []
    for f in findings:
        date_str = f.get("date") or f.get("discovered") or f.get("timestamp")
        if date_str:
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                dated.append((dt, f.get("severity", "info").lower()))
            except (ValueError, TypeError):
                pass

    if not dated:
        drawing.add(String(width / 2, height / 2, "No timeline data available",
                           fontSize=12, fillColor=colors.grey))
        return drawing

    dated.sort(key=lambda x: x[0])
    min_dt = dated[0][0]
    max_dt = dated[-1][0]
    span = max((max_dt - min_dt).total_seconds(), 1)

    # Draw timeline axis
    axis_y = 40
    drawing.add(Line(50, axis_y, width - 30, axis_y, strokeColor=colors.black, strokeWidth=1))

    # Plot points
    for i, (dt, sev) in enumerate(dated):
        x = 50 + int(((dt - min_dt).total_seconds() / span) * (width - 100))
        color = SEVERITY_COLORS.get(sev, colors.grey)
        drawing.add(Rect(x - 3, axis_y - 3, 6, 6, fillColor=color, strokeColor=color))

    # Labels
    drawing.add(String(50, 15, min_dt.strftime("%Y-%m-%d"), fontSize=8, fillColor=colors.black))
    drawing.add(String(width - 80, 15, max_dt.strftime("%Y-%m-%d"), fontSize=8, fillColor=colors.black))
    drawing.add(String(width / 2, height - 15, f"Timeline: {len(dated)} findings",
                       fontSize=10, fillColor=colors.black))

    return drawing


def severity_badge(severity: str) -> str:
    """Return a styled severity badge string."""
    sev = severity.lower()
    color = SEVERITY_COLORS.get(sev, colors.grey)
    hex_color = f"#{color.hexval()[2:]}"
    return f'<font color="{hex_color}"><b>{sev.upper()}</b></font>'


def build_executive_summary(findings: list[dict], styles) -> list:
    """Build executive summary section."""
    elements = []
    counts = count_by_severity(findings)
    total = len(findings)

    elements.append(Paragraph("Executive Summary", styles["Heading1"]))

    summary_text = (
        f"This report contains <b>{total}</b> security findings. "
        f"Critical: <b>{counts['critical']}</b>, "
        f"High: <b>{counts['high']}</b>, "
        f"Medium: <b>{counts['medium']}</b>, "
        f"Low: <b>{counts['low']}</b>, "
        f"Info: <b>{counts['info']}</b>."
    )
    elements.append(Paragraph(summary_text, styles["Body"]))
    elements.append(Spacer(1, 12))

    # Risk assessment
    risk = "HIGH" if counts["critical"] > 0 else "MEDIUM" if counts["high"] > 0 else "LOW"
    risk_color = "#dc2626" if risk == "HIGH" else "#ca8a04" if risk == "MEDIUM" else "#16a34a"
    elements.append(Paragraph(
        f'Overall Risk Rating: <font color="{risk_color}"><b>{risk}</b></font>',
        styles["Body"]
    ))
    elements.append(Spacer(1, 20))

    # Charts
    elements.append(build_pie_chart(findings))
    elements.append(Spacer(1, 12))

    return elements


def build_summary_table(findings: list[dict], styles) -> list:
    """Build a summary table of all findings."""
    elements = []
    elements.append(Paragraph("Findings Summary", styles["Heading1"]))

    table_data = [["#", "Title", "Severity"]]
    for i, f in enumerate(findings, 1):
        table_data.append([
            str(i),
            f.get("title", "Untitled")[:50],
            severity_badge(f.get("severity", "info"))
        ])

    table = Table(table_data, colWidths=[30, 350, 80])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    return elements


def build_detailed_findings(findings: list[dict], styles) -> list:
    """Build detailed findings section."""
    elements = []
    elements.append(Paragraph("Detailed Findings", styles["Heading1"]))

    for i, f in enumerate(findings, 1):
        title = f.get("title", "Untitled Finding")
        severity = f.get("severity", "info")

        elements.append(Paragraph(
            f'{i}. {title} [{severity_badge(severity)}]',
            styles["Heading2"]
        ))

        if f.get("description"):
            elements.append(Paragraph(f"<b>Description:</b> {f['description']}", styles["Body"]))

        if f.get("evidence"):
            elements.append(Paragraph(f"<b>Evidence:</b> {f['evidence']}", styles["Body"]))

        if f.get("remediation"):
            elements.append(Paragraph(f"<b>Remediation:</b> {f['remediation']}", styles["Body"]))

        if f.get("cvss"):
            elements.append(Paragraph(f"<b>CVSS Score:</b> {f['cvss']}", styles["Body"]))

        if f.get("affected"):
            elements.append(Paragraph(f"<b>Affected:</b> {f['affected']}", styles["Body"]))

        elements.append(Spacer(1, 12))

    return elements


def build_report(findings: list[dict], output_path: str, fmt: str = "detailed"):
    """Generate the PDF report."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=50,
        leftMargin=50,
        topMargin=60,
        bottomMargin=50,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontSize=24,
        spaceAfter=20,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="Body",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="ReportSub",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#64748b"),
        alignment=TA_CENTER,
        spaceAfter=30,
    ))

    elements = []

    # Title page
    elements.append(Spacer(1, 80))
    elements.append(Paragraph("Security Assessment Report", styles["ReportTitle"]))
    elements.append(Paragraph(
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Format: {fmt.capitalize()}",
        styles["ReportSub"]
    ))
    elements.append(Spacer(1, 40))

    # Severity overview chart
    elements.append(build_severity_chart(findings))
    elements.append(Spacer(1, 20))

    # Format-specific content
    if fmt == "executive":
        elements.extend(build_executive_summary(findings, styles))
        elements.append(PageBreak())
        elements.extend(build_summary_table(findings, styles))

    elif fmt == "summary":
        elements.append(PageBreak())
        elements.extend(build_summary_table(findings, styles))
        elements.append(Spacer(1, 20))
        elements.append(build_timeline_chart(findings))

    else:  # detailed
        elements.extend(build_executive_summary(findings, styles))
        elements.append(PageBreak())
        elements.extend(build_summary_table(findings, styles))
        elements.append(PageBreak())
        elements.extend(build_detailed_findings(findings, styles))
        elements.append(Spacer(1, 20))
        elements.append(build_timeline_chart(findings))

    # Build PDF
    doc.build(elements)
    print(f"Report generated: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate PDF reports from security findings")
    parser.add_argument("input", help="Path to JSON findings file")
    parser.add_argument("-o", "--output", default="report.pdf", help="Output PDF path")
    parser.add_argument(
        "-f", "--format",
        choices=["detailed", "summary", "executive"],
        default="detailed",
        help="Report format (default: detailed)"
    )
    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    findings = load_findings(args.input)
    if not findings:
        print("Error: No findings found in input file", file=sys.stderr)
        sys.exit(1)

    build_report(findings, args.output, args.format)


if __name__ == "__main__":
    main()
