#!/usr/bin/env python3
"""Lightweight findings dashboard — Flask + Chart.js."""

import argparse
import json
import os
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

FINDINGS_FILE = Path(__file__).parent / "findings.json"
findings: list[dict] = []


def load_findings() -> list[dict]:
    """Load findings from JSON file, tolerate missing/empty."""
    if not FINDINGS_FILE.exists():
        return []
    try:
        data = json.loads(FINDINGS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else [data]
    except (json.JSONDecodeError, OSError):
        return []


# ---------------------------------------------------------------------------
# HTML template (Chart.js via CDN)
# ---------------------------------------------------------------------------
INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Findings Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
  body{font-family:system-ui,sans-serif;margin:0;padding:1rem;background:#1a1a2e;color:#e0e0e0}
  h1{margin-top:0}
  .cards{display:flex;gap:1rem;margin-bottom:1.5rem;flex-wrap:wrap}
  .card{background:#16213e;border-radius:8px;padding:1rem;flex:1;min-width:140px;text-align:center}
  .card .num{font-size:2rem;font-weight:700}
  .card .label{font-size:.8rem;opacity:.7;text-transform:uppercase}
  table{width:100%;border-collapse:collapse;margin-top:1rem;background:#16213e;border-radius:8px;overflow:hidden}
  th,td{padding:.6rem 1rem;text-align:left;border-bottom:1px solid #0f3460}
  th{background:#0f3460;font-size:.8rem;text-transform:uppercase;opacity:.8}
  tr:hover{background:#1a1a40}
  .chart-wrap{background:#16213e;border-radius:8px;padding:1rem;margin-top:1.5rem;max-width:500px}
</style>
</head>
<body>
<h1>Findings Dashboard</h1>
<div class="cards">
  <div class="card"><div class="num" id="total">0</div><div class="label">Total</div></div>
  <div class="card"><div class="num" id="critical">0</div><div class="label">Critical</div></div>
  <div class="card"><div class="num" id="high">0</div><div class="label">High</div></div>
  <div class="card"><div class="num" id="medium">0</div><div class="label">Medium</div></div>
  <div class="card"><div class="num" id="low">0</div><div class="label">Low</div></div>
</div>
<div class="chart-wrap"><canvas id="severityChart"></canvas></div>
<table>
  <thead><tr><th>ID</th><th>Title</th><th>Severity</th><th>Category</th><th>Description</th></tr></thead>
  <tbody id="rows"></tbody>
</table>
<script>
async function refresh() {
  const [findings, stats] = await Promise.all([
    fetch('/api/findings').then(r => r.json()),
    fetch('/api/stats').then(r => r.json()),
  ]);
  document.getElementById('total').textContent = stats.total;
  document.getElementById('critical').textContent = stats.severity_counts.Critical || 0;
  document.getElementById('high').textContent     = stats.severity_counts.High     || 0;
  document.getElementById('medium').textContent   = stats.severity_counts.Medium   || 0;
  document.getElementById('low').textContent      = stats.severity_counts.Low      || 0;
  const tbody = document.getElementById('rows');
  tbody.innerHTML = findings.map(f =>
    `<tr><td>${f.id||''}</td><td>${f.title||''}</td><td>${f.severity||''}</td><td>${f.category||''}</td><td>${(f.description||'').slice(0,120)}</td></tr>`
  ).join('');
  const ctx = document.getElementById('severityChart');
  const labels = Object.keys(stats.severity_counts);
  const values = Object.values(stats.severity_counts);
  const colors = {'Critical':'#e74c3c','High':'#e67e22','Medium':'#f1c40f','Low':'#2ecc71'};
  if (window._chart) window._chart.destroy();
  window._chart = new Chart(ctx, {
    type: 'doughnut',
    data: { labels, datasets: [{ data: values, backgroundColor: labels.map(l=>colors[l]||'#888') }] },
    options: { plugins: { legend: { labels: { color: '#e0e0e0' } } } }
  });
}
refresh();
setInterval(refresh, 10000);
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(INDEX_HTML)


@app.route("/api/findings")
def api_findings():
    return jsonify(findings)


@app.route("/api/stats")
def api_stats():
    severity_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    for f in findings:
        sev = f.get("severity", "Unknown")
        cat = f.get("category", "Uncategorized")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
        category_counts[cat] = category_counts.get(cat, 0) + 1
    return jsonify({
        "total": len(findings),
        "severity_counts": severity_counts,
        "category_counts": category_counts,
    })


@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "count": len(findings)})


def main():
    parser = argparse.ArgumentParser(description="Findings Dashboard")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    global findings
    findings = load_findings()
    print(f"Loaded {len(findings)} findings from {FINDINGS_FILE}")
    print(f"Dashboard running at http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
