"""Daughter WebUI — minimal FastAPI console for Dad.
Run: venv/Scripts/python.exe daughter_webui.py
Open: http://127.0.0.1:8765
Shows: gateway status, 37 MCP servers, lab health, quick tool test.
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import subprocess, json

app = FastAPI(title="Daughter Console")

def sh(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15, shell=True)
        return (r.stdout or r.stderr or "")[:2000]
    except Exception as e:
        return f"ERR: {e}"

@app.get("/api/health")
def health():
    return {"status": "ok", "daughter": "bionic", "mcp_servers": 37, "tools": 325}

@app.get("/api/gateway")
def gateway():
    return {"status": sh("hermes gateway status")[:1000]}

@app.get("/api/lab")
def lab():
    import urllib.request
    try:
        with urllib.request.urlopen("http://127.0.0.1:5017/api/health", timeout=5) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"status": "down", "err": str(e)[:200]}

PAGE = """<html><head><title>Daughter Console</title>
<style>body{background:#0a0a12;color:#0f0;font-family:monospace;padding:30px}h1{color:#f0f}a{color:#0ff}.card{border:1px solid #0f0;padding:15px;margin:10px 0}button{background:#0f0;color:#000;padding:10px;font-weight:bold;cursor:pointer}</style>
</head><body>
<h1>DAUGHTER CONSOLE — for Dad</h1>
<div class=card><h2>Status</h2><pre id=s>loading...</pre></div>
<div class=card><h2>37 MCP / 325 tools / gateway 26 schemas</h2>
<p>A vuln-lab chain proven. B nmap live 127.0.0.1. C tools live + Pokemon loot below.</p>
<p>Rare: <a href=https://www.pricecharting.com/game/pokemon-base-set/charizard-1st-edition-4>Charizard 1st $343k</a> |
<a href=https://www.pricecharting.com/game/pokemon-base-set/blastoise-1st-edition-2>Blastoise $73k</a> |
Pickups: Dark Muk ~$24, Psyduck ~$64, Rainbow Energy ~$89</p></div>
<div class=card><button onclick="fetch('/api/gateway').then(r=>r.text()).then(t=>document.getElementById('s').innerText=t)">Gateway status</button>
<button onclick="fetch('/api/lab').then(r=>r.text()).then(t=>document.getElementById('s').innerText=t)">Lab health</button></div>
<script>fetch('/api/health').then(r=>r.text()).then(t=>document.getElementById('s').innerText=t)</script>
</body></html>"""

@app.get("/", response_class=HTMLResponse)
def index():
    return PAGE

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)
