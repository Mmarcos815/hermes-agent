#!/usr/bin/env python3
"""Security Metrics Dashboard for Bionic Daughter Project.

Reads training artifacts, evals, vulnerability scans, and bounty data from the
artifacts/ directory and generates an interactive HTML dashboard.

Usage:
    python security_metrics_dashboard.py [--artifacts DIR] [--output HTML] [--open]
"""

import argparse
import json
import os
import sys
import webbrowser
from datetime import datetime
from html import escape

DEFAULT_ARTIFACTS = "artifacts"
DEFAULT_OUTPUT = "security_dashboard.html"


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def discover_scans(d):
    scans = []
    for fn in os.listdir(d):
        if fn.endswith(".json") and any(k in fn for k in ["juiceshop", "fuzz", "audit", "smoke", "e2e"]):
            data = load_json(os.path.join(d, fn))
            if not data:
                continue
            date = ""
            for p in fn.replace(".json", "").split("_"):
                if len(p) == 10 and p[4] == "-" and p[7] == "-":
                    date = p
            scans.append({"file": fn, "date": date or "?", "data": data})
    return sorted(scans, key=lambda s: s["date"], reverse=True)


def discover_evals(d):
    ed = os.path.join(d, "evals")
    if not os.path.isdir(ed):
        return []
    evals = []
    for fn in sorted(os.listdir(ed)):
        if fn.endswith(".json"):
            data = load_json(os.path.join(ed, fn))
            if data:
                evals.append({"file": fn, "data": data})
    return evals


def discover_configs(d):
    cfgs = {}
    for stage in ["grpo", "dpo", "sft", "rejection_sft"]:
        p = os.path.join(d, stage, "last", "config.json")
        if os.path.isfile(p):
            cfgs[stage] = load_json(p)
    return cfgs


def scan_summary(scans):
    by_class, by_date, total = {}, {}, 0
    for s in scans:
        d = s["data"]
        vc = d.get("vuln_class", "Unknown")
        cnt = d.get("findings_count", len(d.get("findings", [])))
        total += cnt
        by_class[vc] = by_class.get(vc, 0) + cnt
        by_date[s["date"]] = by_date.get(s["date"], 0) + cnt
    return {"total": total, "count": len(scans), "by_class": by_class, "by_date": by_date}


def bounty_status(scans):
    sub, conf, est = 0, 0, 0
    for s in scans:
        d = s["data"]
        vc = d.get("vuln_class", "")
        for f in d.get("findings", []):
            if f.get("status") == 200:
                sub += 1
                if "BOLA" in vc:
                    conf += 1; est += 500
                elif "OAuth" in vc:
                    conf += 1; est += 300
                else:
                    est += 100
    return {"submitted": sub, "confirmed": conf, "estimate": est}


def compare_models(evals):
    baseline = next((e["data"] for e in evals if "baseline" in e["file"] or "pre_grpo" in e["file"]), None)
    if not baseline and evals:
        baseline = evals[0]["data"]
    comps = [{"label": e["file"].replace("eval_", "").replace(".json", ""), "data": e["data"]}
             for e in evals if "step_" in e["file"] or "post_grpo" in e["file"]]
    return {"baseline": baseline, "comparisons": comps}


def reward_curve(evals):
    return [{"step": e["file"].replace("eval_", "").replace(".json", ""),
             "score": round(d, 4)} for e in evals
            if (d := e["data"].get("overall_best_composite", e["data"].get("weighted_overall_score"))) is not None]


def tbl(rows):
    return "".join(f"<tr>{''.join(f'<td>{c}</td>' for c in r)}</tr>" for r in rows)


def generate_html(args, scans, evals, configs, summary, bounty, cmp_data, curve):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    baseline = cmp_data.get("baseline", {})
    bs = baseline.get("overall_best_composite", baseline.get("weighted_overall_score", 0))
    br = baseline.get("overall_pass_rate", 0) * 100

    scan_rows = tbl([[escape(s["date"]), escape(s["data"].get("vuln_class", "?")),
                      s["data"].get("findings_count", len(s["data"].get("findings", []))),
                      escape(s["data"].get("target", s["data"].get("endpoint", "-")))] for s in scans])

    dom_rows = tbl([[escape(dom), i.get("prompts", 0),
                     f'{i.get("pass_rate", 0) * 100:.1f}%',
                     f'{i.get("avg_best_composite", i.get("avg_composite", 0)):.3f}']
                    for dom, i in (baseline.get("domain_summary") or {}).items()])

    cmp_rows = tbl([[escape(c["label"]),
                     f'{c["data"].get("overall_best_composite", c["data"].get("weighted_overall_score", 0)):.3f}',
                     f'{c["data"].get("overall_pass_rate", 0) * 100:.1f}%',
                     f'{c["data"].get("overall_best_composite", c["data"].get("weighted_overall_score", 0)) - bs:+.3f}']
                    for c in cmp_data["comparisons"]])

    cl_html = "".join(f'<div class="card"><h4>{s.upper()}</h4>'
                      f'<p>Status: <span class="ok">{configs[s].get("status", "?")}</span></p>'
                      f'<p>Steps: {configs[s].get("hyperparameters", {}).get("max_steps", "?")}</p></div>'
                      for s in configs)

    cl_labels = json.dumps(list(summary["by_class"].keys()))
    cl_counts = json.dumps(list(summary["by_class"].values()))
    cu_labels = json.dumps([c["step"] for c in curve])
    cu_scores = json.dumps([c["score"] for c in curve])

    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<title>Bionic Daughter - Security Dashboard</title>
<style>
:root{{--bg:#0d1117;--card:#161b22;--brd:#30363d;--txt:#c9d1d9;--acc:#58a6ff;--grn:#3fb950;--red:#f85149;--pur:#bc8cff}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:var(--bg);color:var(--txt);padding:2rem;line-height:1.6}}
h1{{color:var(--acc);font-size:1.7rem;margin-bottom:.3rem}}
h2{{color:var(--pur);font-size:1.2rem;margin:1.5rem 0 .5rem;border-bottom:1px solid var(--brd);padding-bottom:.3rem}}
.ts{{color:#8b949e;font-size:.85rem;margin-bottom:1.5rem}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem;margin-bottom:1.5rem}}
.card{{background:var(--card);border:1px solid var(--brd);border-radius:8px;padding:1rem;text-align:center}}
.card h3{{color:var(--txt);font-size:.8rem;text-transform:uppercase;letter-spacing:.05em}}
.val{{font-size:1.8rem;font-weight:700;color:var(--acc);margin-top:.3rem}}
.card.ok .val{{color:var(--grn)}}
table{{width:100%;border-collapse:collapse;background:var(--card);border-radius:8px;overflow:hidden;margin:1rem 0}}
th,td{{padding:.5rem .8rem;text-align:left;border-bottom:1px solid var(--brd);font-size:.88rem}}
th{{background:#21262d}}
tr:hover{{background:#1c2128}}
.ok{{color:var(--grn);font-weight:600}}
.pos{{color:var(--grn)}}.neg{{color:var(--red)}}
.chart{{background:var(--card);border:1px solid var(--brd);border-radius:8px;padding:1rem;margin:1rem 0}}
.cfg{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1rem}}
.cfg .card h4{{color:var(--acc);margin-bottom:.3rem}}
.foot{{margin-top:2rem;padding-top:1rem;border-top:1px solid var(--brd);color:#8b949e;font-size:.78rem;text-align:center}}
</style></head><body>
<h1>Bionic Daughter — Security Metrics Dashboard</h1>
<p class="timestamp">Generated: {now} | Artifacts: {escape(args.artifacts)}</p>

<div class="grid">
  <div class="card"><h3>Total Findings</h3><div class="val">{summary["total"]}</div></div>
  <div class="card"><h3>Scans Run</h3><div class="val">{summary["count"]}</div></div>
  <div class="card"><h3>Eval Reports</h3><div class="val">{len(evals)}</div></div>
  <div class="card"><h3>Train Stages</h3><div class="val">{len(configs)}</div></div>
  <div class="card ok"><h3>Bounty Submitted</h3><div class="val">{bounty["submitted"]}</div></div>
  <div class="card ok"><h3>Est. Value</h3><div class="val">${bounty["estimate"]:,}</div></div>
</div>

<h2>Training Progress</h2>
<div class="cfg">{cl_html}</div>

<h2>Reward Curve Progression</h2>
<div class="chart"><canvas id="rc" height="90"></canvas></div>

<h2>Model Comparison (Base vs Trained)</h2>
<table><thead><tr><th>Variant</th><th>Score</th><th>Pass Rate</th><th>Delta</th></tr></thead>
<tbody>
<tr><td><strong>Baseline</strong></td><td>{bs:.3f}</td><td>{br:.1f}%</td><td>—</td></tr>
{cmp_rows}</tbody></table>

<h2>Domain Performance (Baseline)</h2>
<table><thead><tr><th>Domain</th><th>Prompts</th><th>Pass Rate</th><th>Avg Composite</th></tr></thead>
<tbody>{dom_rows}</tbody></table>

<h2>Vulnerability Scans</h2>
<table><thead><tr><th>Date</th><th>Class</th><th>Findings</th><th>Target</th></tr></thead>
<tbody>{scan_rows}</tbody></table>

<h2>Findings by Class</h2>
<div class="chart"><canvas id="sc" height="70"></canvas></div>

<div class="foot">Bionic Daughter Project — security_metrics_dashboard.py</div>

<script>
function lineChart(id,labels,scores){{
  const c=document.getElementById(id).getContext('2d'),W=c.canvas.parentElement.clientWidth-30,H=180;
  c.canvas.width=W;c.canvas.height=H;const p=35,xS=labels.length>1?(W-p*2)/(labels.length-1):0;
  const mn=Math.min(...scores,0),mx=Math.max(...scores,1),rng=mx-mn||1;
  c.strokeStyle='#30363d';c.lineWidth=1;
  for(let i=0;i<=4;i++){{const y=p+(H-p*2)*i/4;c.beginPath();c.moveTo(p,y);c.lineTo(W-p,y);c.stroke();
    c.fillStyle='#8b949e';c.font='10px sans-serif';c.fillText((mx-rng*i/4).toFixed(2),2,y+3)}}
  c.strokeStyle='#58a6ff';c.lineWidth=2;c.beginPath();
  scores.forEach((s,i)=>{{const x=p+i*xS,y=p+(H-p*2)*(1-(s-mn)/rng);i?c.lineTo(x,y):c.moveTo(x,y)}});c.stroke();
  c.fillStyle='#58a6ff';scores.forEach((s,i)=>{{const x=p+i*xS,y=p+(H-p*2)*(1-(s-mn)/rng);
    c.beginPath();c.arc(x,y,3,0,6.28);c.fill()}});
  c.fillStyle='#8b949e';c.font='9px sans-serif';labels.forEach((l,i)=>{{
    const x=p+i*xS;c.save();c.translate(x,H-4);c.rotate(-0.4);c.fillText(l.substring(0,12),0,0);c.restore()}})
}}
function barChart(id,labels,counts){{
  const c=document.getElementById(id).getContext('2d'),W=c.canvas.parentElement.clientWidth-30,H=140;
  c.canvas.width=W;c.canvas.height=H;const p=35,mx=Math.max(...counts,1);
  const bw=labels.length>0?(W-p*2)/labels.length*.7:0,gp=labels.length>0?(W-p*2)/labels.length*.3:0;
  const clr=['#f85149','#d29922','#58a6ff','#bc8cff','#3fb950','#db61a2'];
  counts.forEach((n,i)=>{{const x=p+i*(bw+gp),h=(H-p*2)*(n/mx),y=H-p-h;
    c.fillStyle=clr[i%clr.length];c.fillRect(x,y,bw,h);
    c.fillStyle='#c9d1d9';c.font='10px sans-serif';c.fillText(n,x+bw/2-3,y-4)}});
  c.fillStyle='#8b949e';c.font='9px sans-serif';labels.forEach((l,i)=>{{
    const x=p+i*(bw+gp)+bw/2;c.save();c.translate(x,H-4);c.rotate(-0.4);c.fillText(l.substring(0,18),0,0);c.restore()}})
}}
lineChart('rc',{cu_labels},{cu_scores});
barChart('sc',{cl_labels},{cl_counts});
</script></body></html>'''


def main():
    ap = argparse.ArgumentParser(description="Security metrics dashboard for Bionic Daughter")
    ap.add_argument("--artifacts", default=DEFAULT_ARTIFACTS, help="Artifacts directory")
    ap.add_argument("--output", default=DEFAULT_OUTPUT, help="Output HTML file")
    ap.add_argument("--open", action="store_true", help="Open in browser")
    args = ap.parse_args()

    if not os.path.isdir(args.artifacts):
        print(f"Error: directory not found: {args.artifacts}", file=sys.stderr)
        sys.exit(1)

    scans = discover_scans(args.artifacts)
    evals = discover_evals(args.artifacts)
    configs = discover_configs(args.artifacts)
    summary = scan_summary(scans)
    bounty = bounty_status(scans)
    cmp_data = compare_models(evals)
    curve = reward_curve(evals)

    html = generate_html(args, scans, evals, configs, summary, bounty, cmp_data, curve)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Dashboard: {args.output}")
    print(f"  Scans: {len(scans)} | Evals: {len(evals)} | Stages: {len(configs)}")
    print(f"  Findings: {summary['total']} | Bounty: {bounty['submitted']}/${bounty['estimate']:,}")

    if args.open:
        webbrowser.open(f"file://{os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
