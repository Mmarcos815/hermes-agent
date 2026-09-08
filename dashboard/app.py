#!/usr/bin/env python3
"""Unified Bionic Dashboard — Flask web app, ~300 lines."""

from flask import Flask, jsonify, render_template_string
import json, os, glob, time
from datetime import datetime

ROOT = r"C:\Users\mobil\orca\projects\my 1st"
app = Flask(__name__)

# ── Data loaders ──────────────────────────────────────────────────────

def load_mcp_tools():
    """Read unified_mcp_server.py to discover the 35 tools."""
    srv = os.path.join(ROOT, "mcp-servers", "unified_mcp_server.py")
    tools = []
    try:
        for line in open(srv, encoding="utf-8"):
            if "@app.tool(name=" in line:
                name = line.split('"')[1]
                tools.append({"name": name})
    except FileNotFoundError:
        pass
    return tools

def load_bionic_models():
    """List bionic model files found in the workspace (fast, depth-limited)."""
    models = []
    # Check only ROOT and one level deep to avoid scanning node_modules etc.
    for ext in ("*.gguf", "*.bin", "*.safetensors"):
        for p in glob.glob(os.path.join(ROOT, ext)):
            sz = os.path.getsize(p) / 1e9
            models.append({"name": os.path.basename(p), "path": p, "size_gb": round(sz, 2)})
        for p in glob.glob(os.path.join(ROOT, "*", ext)):
            sz = os.path.getsize(p) / 1e9
            models.append({"name": os.path.basename(p), "path": p, "size_gb": round(sz, 2)})
    # Also check for training configs
    for cfg in ("grpo_training_config.yaml",):
        fp = os.path.join(ROOT, cfg)
        if os.path.exists(fp):
            models.append({"name": cfg, "path": fp, "size_gb": 0})
    return models

def load_training_runs():
    """Scan for batch output files and training checkpoints (fast, no deep recursion)."""
    runs = []
    for jl in glob.glob(os.path.join(ROOT, "batch_*.jsonl")):
        try:
            lines = sum(1 for _ in open(jl, encoding="utf-8"))
            runs.append({
                "file": os.path.basename(jl),
                "path": jl,
                "samples": lines,
                "modified": datetime.fromtimestamp(os.path.getmtime(jl)).strftime("%Y-%m-%d %H:%M"),
            })
        except (OSError, UnicodeDecodeError):
            pass
    for ck in glob.glob(os.path.join(ROOT, "checkpoint-*")):
        runs.append({
            "file": os.path.basename(ck),
            "path": ck,
            "samples": "checkpoint",
            "modified": datetime.fromtimestamp(os.path.getmtime(ck)).strftime("%Y-%m-%d %H:%M"),
        })
    # Also scan grpo output dirs
    for ck in glob.glob(os.path.join(ROOT, "*", "checkpoint-*"))[:10]:
        runs.append({
            "file": os.path.basename(os.path.basename(ck)),
            "path": ck,
            "samples": "checkpoint",
            "modified": datetime.fromtimestamp(os.path.getmtime(ck)).strftime("%Y-%m-%d %H:%M"),
        })
    return runs[:20]

def load_deploy_status():
    """Check cloud deploy configs."""
    status = []
    cfg_path = os.path.join(ROOT, "cloud_deploy", "hermes_config.yaml")
    if os.path.exists(cfg_path):
        status.append({"provider": "runpod", "config": cfg_path})
    modal = os.path.join(ROOT, "cloud_deploy", "modal_deploy.py")
    if os.path.exists(modal):
        status.append({"provider": "modal", "config": modal})
    local = os.path.join(ROOT, "cloud_deploy", "local_proxy.py")
    if os.path.exists(local):
        status.append({"provider": "local", "config": local})
    return status

# ── HTML template ─────────────────────────────────────────────────────

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bionic Unified Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',sans-serif;background:#0d1117;color:#c9d1d9;padding:20px}
header{text-align:center;padding:20px 0;border-bottom:1px solid #21262d;margin-bottom:24px}
header h1{color:#58a6ff;font-size:1.8em}
header p{color:#8b949e;margin-top:6px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:20px}
.card{background:#161b22;border:1px solid #21262d;border-radius:8px;padding:20px}
.card h2{color:#58a6ff;margin-bottom:12px;font-size:1.15em}
table{width:100%;border-collapse:collapse;font-size:.85em}
th,td{padding:6px 10px;text-align:left;border-bottom:1px solid #21262e}
th{color:#8b949e;font-weight:600}
tr:hover{background:#1c2128}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:.75em}
.ok{background:#1a3a2a;color:#3fb950}.warn{background:#3a2a1a;color:#d29922}.off{background:#3a1a1a;color:#f85149}
canvas{background:#0d1117;border-radius:6px}
.stats{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:24px}
.stat{background:#161b22;border:1px solid #21262d;border-radius:8px;padding:16px;flex:1;min-width:140px;text-align:center}
.stat .num{font-size:2em;color:#58a6ff}
.stat .lbl{color:#8b949e;font-size:.85em;margin-top:4px}
</style>
</head>
<body>
<header>
<h1>⚡ Bionic Unified Dashboard</h1>
<p>MCP Servers · Models · Training · Deployments</p>
</header>

<div class="stats">
  <div class="stat"><div class="num" id="s-tools">–</div><div class="lbl">MCP Tools</div></div>
  <div class="stat"><div class="num" id="s-models">–</div><div class="lbl">Models</div></div>
  <div class="stat"><div class="num" id="s-runs">–</div><div class="lbl">Training Runs</div></div>
  <div class="stat"><div class="num" id="s-deploys">–</div><div class="lbl">Deployments</div></div>
</div>

<div class="grid">
  <div class="card">
    <h2>🔧 MCP Tools (35)</h2>
    <table><thead><tr><th>#</th><th>Tool Name</th><th>Category</th></tr></thead>
    <tbody id="tools-tbody"></tbody></table>
  </div>
  <div class="card">
    <h2>🧠 Bionic Models</h2>
    <table><thead><tr><th>Name</th><th>Size</th></tr></thead>
    <tbody id="models-tbody"></tbody></table>
  </div>
  <div class="card">
    <h2>📈 Training Runs</h2>
    <table><thead><tr><th>File</th><th>Samples</th><th>Modified</th></tr></thead>
    <tbody id="runs-tbody"></tbody></table>
  </div>
  <div class="card">
    <h2>☁️ Cloud Deployments</h2>
    <table><thead><tr><th>Provider</th><th>Config</th></tr></thead>
    <tbody id="deploys-tbody"></tbody></table>
  </div>
  <div class="card" style="grid-column:1/-1">
    <h2>📊 Tool Category Distribution</h2>
    <canvas id="chart-tools" height="80"></canvas>
  </div>
</div>

<script>
async function fetchJSON(r){return (await fetch(r)).json()}
function cat(name){
  if(name.startsWith("redteam_"))return"Red Team";
  if(name.startsWith("banking_"))return"Banking";
  if(name.startsWith("recon_"))return"Recon";
  if(name.startsWith("cloud_"))return"Cloud";
  if(name.startsWith("ad_"))return"Active Dir.";
  if(name.startsWith("mobile_"))return"Mobile";
  if(name.startsWith("osint_"))return"OSINT";
  return"Other";
}
function catColor(c){return{redteam:"#f85149",banking:"#d29922",recon:"#3fb950",cloud:"#58a6ff",ad:"#bc8cff",mobile:"#ff7b72",osint:"#a371f7"}[c]||"#8b949e"}

(async()=>{
  const [tools,models,runs,deploys]=await Promise.all([
    fetchJSON("/api/tools"),fetchJSON("/api/models"),fetchJSON("/api/train"),fetchJSON("/api/deploy")
  ]);
  document.getElementById("s-tools").textContent=tools.length;
  document.getElementById("s-models").textContent=models.length;
  document.getElementById("s-runs").textContent=runs.length;
  document.getElementById("s-deploys").textContent=deploys.length;

  const tb=document.getElementById("tools-tbody");
  tools.forEach((t,i)=>{
    const tr=document.createElement("tr");
    tr.innerHTML=`<td>${i+1}</td><td>${t.name}</td><td><span class="badge" style="background:${catColor(cat(t.name).toLowerCase().replace(' ','').replace('.','').replace('active dir','ad'))}20;color:${catColor(cat(t.name).toLowerCase().replace(' ','').replace('.','').replace('active dir','ad'))}">${cat(t.name)}</span></td>`;
    tb.appendChild(tr);
  });

  const mb=document.getElementById("models-tbody");
  models.forEach(m=>{
    const tr=document.createElement("tr");
    tr.innerHTML=`<td>${m.name}</td><td>${m.size_gb?m.size_gb+' GB':'config'}</td>`;
    mb.appendChild(tr);
  });

  const rb=document.getElementById("runs-tbody");
  runs.forEach(r=>{
    const tr=document.createElement("tr");
    tr.innerHTML=`<td>${r.file}</td><td>${r.samples}</td><td>${r.modified}</td>`;
    rb.appendChild(tr);
  });

  const db=document.getElementById("deploys-tbody");
  deploys.forEach(d=>{
    const tr=document.createElement("tr");
    tr.innerHTML=`<td><span class="badge ok">${d.provider}</span></td><td>${d.config}</td>`;
    db.appendChild(tr);
  });

  // Chart
  const counts={};tools.forEach(t=>{const c=cat(t.name);counts[c]=(counts[c]||0)+1});
  new Chart(document.getElementById("chart-tools"),{
    type:"doughnut",
    data:{labels:Object.keys(counts),datasets:[{data:Object.values(counts),backgroundColor:Object.keys(counts).map(c=>catColor(c.toLowerCase().replace(' ','').replace('.','').replace('active dir','ad')))}]},
    options:{plugins:{legend:{position:"right",labels:{color:"#c9d1d9"}}}}
  });
})();
</script>
</body>
</html>
"""

# ── Routes ────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(TEMPLATE)

@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "ts": time.time(), "host": "windows"})

@app.route("/api/tools")
def api_tools():
    return jsonify(load_mcp_tools())

@app.route("/api/models")
def api_models():
    return jsonify(load_bionic_models())

@app.route("/api/train")
def api_train():
    return jsonify(load_training_runs())

@app.route("/api/deploy")
def api_deploy():
    return jsonify(load_deploy_status())

# ── Main ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Bionic Unified Dashboard → http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
