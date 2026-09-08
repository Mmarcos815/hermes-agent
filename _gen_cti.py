#!/usr/bin/env python3
"""
Automated CTI Monitoring System
==============================
Ingests threat intel feeds (MISP, OTX, abuse.ch), correlates IOCs against
infrastructure, alerts on matches, generates reports, tracks IOC aging,
and serves a read-only dashboard.

Native Python only. Run:
    python automated_cti_monitoring.py            # ingest + correlate once
    python automated_cti_monitoring.py --daemon    # loop every 300s
    python automated_cti_monitoring.py --dashboard # serve dashboard on :8080
"""

import argparse
import datetime as dt
import hashlib
import http.server
import ipaddress
import json
import os
import re
import socketserver
import time
import urllib.request
import urllib.error
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"C:\Users\mobil\orca\projects\my 1st")
IOC_DB_FILE = ROOT / "ioc_database.json"
ALERTS_FILE = ROOT / "alerts.json"
REPORTS_DIR = ROOT / "cti_reports"
INFRA_FILE = ROOT / "infra.json"
REPORTS_DIR.mkdir(exist_ok=True)

FEEDS = {
    "otx": "https://otx.alienvault.com/api/v1/indicators/IPv4/general/?limit=50&page=1",
    "urlhaus": "https://urlhaus-api.abuse.ch/v1/host/",
}

DEFAULT_INFRA = {
    "cidrs": ["10.0.0.0/8", "172.16.0.0/12", "192.168.1.0/24"],
    "domains": ["internal.example.com", "vpn.corp.local", "git.internal"],
    "hosts": ["10.0.1.1", "10.0.1.2", "192.168.1.100"],
    "hashes": [],
}

IOC_MAX_AGE_DAYS = 90
IOC_RELEVANCE_DECAY = 0.95
SEVERITY_HIGH = 3
SEVERITY_MED = 2
SEVERITY_LOW = 1


def load_infrastructure():
    try:
        with open(INFRA_FILE, encoding="utf-8") as f:
            data = json.load(f)
        for k, v in DEFAULT_INFRA.items():
            data.setdefault(k, v)
        return data
    except (FileNotFoundError, json.JSONDecodeError):
        return DEFAULT_INFRA.copy()


def ioc_matches_infra(value, ioc_type, infra):
    if ioc_type == "ip":
        try:
            ip = ipaddress.ip_address(value)
            for cidr in infra.get("cidrs", []):
                if ip in ipaddress.ip_network(cidr, strict=False):
                    return True
            return value in infra.get("hosts", [])
        except ValueError:
            return False
    if ioc_type == "domain":
        return value in infra.get("domains", [])
    if ioc_type == "hash":
        return value in infra.get("hashes", [])
    return False


def http_get_json(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CTI-Monitor/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return None


def fetch_otx():
    data = http_get_json(FEEDS["otx"])
    iocs = []
    if not data:
        return iocs
    for pulse in data.get("pulse_info", {}).get("pulses", []):
        tags = pulse.get("tags", [])
        sev = SEVERITY_HIGH if ("malware" in tags or "cve" in tags) else SEVERITY_MED
        for ind in pulse.get("indicators", []):
            t = ind.get("type", "")
            if t in ("IPv4", "domain", "hostname"):
                iocs.append({"value": ind["indicator"], "type": "ip" if t == "IPv4" else "domain",
                              "source": "otx", "tags": tags, "severity": sev})
    return iocs


def fetch_urlhaus():
    try:
        req = urllib.request.Request(FEEDS["urlhaus"], data=b"recent=urls",
                                      headers={"User-Agent": "CTI-Monitor/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return []
    iocs = []
    if data.get("query_status") != "ok":
        return iocs
    for entry in data.get("urls", [])[:50]:
        host = entry.get("host", "")
        if host:
            iocs.append({"value": host,
                          "type": "domain" if not re.match(r"^\d", host) else "ip",
                          "source": "urlhaus", "tags": [entry.get("threat", "malware")],
                          "severity": SEVERITY_HIGH})
    return iocs


def generate_demo_feed():
    return [
        {"value": "192.168.1.50", "type": "ip", "source": "demo_misp",
         "tags": ["apt28", "spearphishing"], "severity": SEVERITY_HIGH},
        {"value": "evil-update.example.com", "type": "domain", "source": "demo_misp",
         "tags": ["c2", "trojan"], "severity": SEVERITY_HIGH},
        {"value": "10.0.1.42", "type": "ip", "source": "demo_otx",
         "tags": ["scanner", "bruteforce"], "severity": SEVERITY_MED},
        {"value": "a]b]c]d]e]f]a]b]c]d]e]f]a]b]c]d]e]f]a]b]c]d]e]f",
         "type": "hash", "source": "demo_bazaar", "tags": ["ransomware"],
         "severity": SEVERITY_HIGH},
        {"value": "192.168.1.100", "type": "ip", "source": "demo_otx",
         "tags": ["lateral-movement"], "severity": SEVERITY_MED},
    ]


def ingest_all_feeds():
    all_iocs = []
    for name, fetcher in [("otx", fetch_otx), ("urlhaus", fetch_urlhaus)]:
        try:
            result = fetcher()
            all_iocs.extend(result)
            print(f"  [{name}] fetched {len(result)} IOCs")
        except Exception as e:
            print(f"  [{name}] error: {e}")
    if not all_iocs:
        print("  [demo] no live data, using synthetic IOCs")
        all_iocs = generate_demo_feed()
    return all_iocs


def load_ioc_database():
    try:
        with open(IOC_DB_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"iocs": {}, "last_updated": None, "stats": {"total": 0, "active": 0, "expired": 0}}


def save_ioc_database(db):
    tmp = IOC_DB_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False, default=str)
    tmp.replace(IOC_DB_FILE)


def make_ioc_key(value, ioc_type):
    return hashlib.sha1(f"{ioc_type}:{value}".encode()).hexdigest()[:16]


def merge_iocs(db, new_iocs):
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    added = updated = 0
    for ioc in new_iocs:
        key = make_ioc_key(ioc["value"], ioc["type"])
        if key in db["iocs"]:
            ex = db["iocs"][key]
            ex["sightings"] = ex.get("sightings", 1) + 1
            ex["last_seen"] = now
            ex["relevance"] = min(1.0, ex.get("relevance", 0.5) + 0.05)
            ex["tags"] = list(set(ex.get("tags", []) + ioc.get("tags", [])))
            ex["severity"] = max(ex.get("severity", 0), ioc.get("severity", 0))
            updated += 1
        else:
            db["iocs"][key] = {
                "value": ioc["value"], "type": ioc["type"],
                "source": ioc.get("source", "unknown"),
                "tags": ioc.get("tags", []), "severity": ioc.get("severity", SEVERITY_LOW),
                "first_seen": now, "last_seen": now, "sightings": 1,
                "relevance": 0.5, "active": True,
            }
            added += 1
    db["last_updated"] = now
    return added, updated


def apply_aging(db):
    now = dt.datetime.now(dt.timezone.utc)
    for key, ioc in db["iocs"].items():
        if not ioc.get("active", True):
            continue
        last = dt.datetime.fromisoformat(ioc["last_seen"])
        age_days = (now - last).days
        ioc["relevance"] = round(ioc.get("relevance", 0.5) * (IOC_RELEVANCE_DECAY ** age_days), 3)
        if age_days > IOC_MAX_AGE_DAYS or ioc["relevance"] < 0.05:
            ioc["active"] = False
    db["stats"] = {
        "total": len(db["iocs"]),
        "active": sum(1 for i in db["iocs"].values() if i.get("active", True)),
        "expired": sum(1 for i in db["iocs"].values() if not i.get("active", True)),
    }


def correlate_iocs(db, infra):
    alerts = []
    for key, ioc in db["iocs"].items():
        if not ioc.get("active", True):
            continue
        if ioc_matches_infra(ioc["value"], ioc["type"], infra):
            alerts.append({
                "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                "ioc_key": key, "ioc_value": ioc["value"], "ioc_type": ioc["type"],
                "severity": ioc["severity"], "source": ioc["source"],
                "tags": ioc["tags"], "action": "INVESTIGATE",
            })
    return alerts


def save_alerts(new_alerts):
    existing = []
    if ALERTS_FILE.exists():
        try:
            with open(ALERTS_FILE, encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []
    existing.extend(new_alerts)
    with open(ALERTS_FILE, "w", encoding="utf-8") as f:
        json.dump(existing[-1000:], f, indent=2, ensure_ascii=False, default=str)


def generate_threat_report(db, alerts):
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report_path = REPORTS_DIR / f"threat_report_{dt.date.today().isoformat()}.md"
    active = [i for i in db["iocs"].values() if i.get("active", True)]
    high = [i for i in active if i.get("severity", 0) >= SEVERITY_HIGH]

    tag_counts = defaultdict(int)
    for ioc in active:
        for t in ioc.get("tags", []):
            tag_counts[t] += 1
    top_tags = sorted(tag_counts.items(), key=lambda x: -x[1])[:10]

    lines = []
    lines.append("# Threat Intelligence Report")
    lines.append(f"**Generated:** {now}")
    lines.append(f"**IOC Database:** {db['stats']['total']} total / {db['stats']['active']} active")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append(f"- **{len(high)}** high-severity IOCs active")
    lines.append(f"- **{len(alerts)}** infrastructure matches this cycle")
    top_tags_str = ", ".join(f"{t}({c})" for t, c in top_tags[:5]) or "N/A"
    lines.append(f"- Top tags: {top_tags_str}")
    lines.append("")
    lines.append("## High-Severity Active IOCs")
    for ioc in high:
        tags_str = ",".join(ioc.get("tags", []))
        lines.append(f"- `{ioc['value']}` [{ioc['type']}] src={ioc['source']} "
                      f"rel={ioc.get('relevance',0)} tags={tags_str}")

    lines += ["", "## Infrastructure Alerts"]
    if alerts:
        lines.append("| Timestamp | IOC | Type | Severity | Action |")
        lines.append("|-----------|-----|------|----------|--------|")
        for a in alerts:
            lbl = {3: "HIGH", 2: "MED", 1: "LOW"}.get(a["severity"], "INFO")
            lines.append(f"| {a['timestamp'][:19]} | {a['ioc_value']} | {a['ioc_type']} "
                          f"| {lbl} | {a['action']} |")
    else:
        lines.append("_No infrastructure matches this cycle._")

    lines += ["", "## Active IOCs by Source"]
    by_src = defaultdict(list)
    for ioc in active:
        by_src[ioc.get("source", "unknown")].append(ioc)
    for src, items in sorted(by_src.items()):
        lines.append(f"### {src} ({len(items)})")
        for ioc in sorted(items, key=lambda x: -x.get("severity", 0))[:20]:
            tags_str = ",".join(ioc.get("tags", []))
            lines.append(f"- `{ioc['value']}` [{ioc['type']}] rel={ioc.get('relevance',0)} "
                          f"seen={ioc.get('sightings',1)}x")
        if len(items) > 20:
            lines.append(f"- ...and {len(items)-20} more")
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return str(report_path)


def run_pipeline():
    print("=" * 50)
    print(" CTI Monitoring Pipeline")
    print("=" * 50)

    infra = load_infrastructure()
    print(f"[infra] {len(infra.get('cidrs',[]))} CIDRs, {len(infra.get('domains',[]))} domains")

    print("[ingest] Fetching feeds...")
    new_iocs = ingest_all_feeds()
    print(f"[ingest] {len(new_iocs)} IOCs ingested")

    db = load_ioc_database()
    added, updated = merge_iocs(db, new_iocs)
    print(f"[merge] Added={added} Updated={updated}")

    apply_aging(db)
    print(f"[aging] Active={db['stats']['active']} Expired={db['stats']['expired']}")

    print("[correlate] Checking IOCs vs infrastructure...")
    alerts = correlate_iocs(db, infra)
    print(f"[correlate] {len(alerts)} alert(s)")
    if alerts:
        save_alerts(alerts)
        for a in alerts:
            sev = {3: "HIGH", 2: "MED", 1: "LOW"}.get(a["severity"], "?")
            print(f"  !! [{sev}] {a['ioc_value']} ({a['ioc_type']})")

    save_ioc_database(db)
    report_path = generate_threat_report(db, alerts)
    print(f"[report] {report_path}")

    return {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "iocs_ingested": len(new_iocs), "added": added, "updated": updated,
        "alerts": len(alerts), "active": db["stats"]["active"],
        "expired": db["stats"]["expired"], "report": report_path,
    }


DASH_HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>CTI Dashboard</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#0d1117;color:#c9d1d9;padding:20px}
h1{color:#58a6ff}
h2{color:#bc8cff;margin:18px 0 8px;border-bottom:1px solid #30363d}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px}
.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:14px;text-align:center}
.card .val{font-size:2em;font-weight:700;color:#58a6ff}
.card .lbl{color:#8b949e;font-size:.82em}
.card.alert .val{color:#f85149}
.card.ok .val{color:#3fb950}
table{width:100%;border-collapse:collapse;margin:10px 0;background:#161b22}
th,td{padding:6px 10px;text-align:left;border-bottom:1px solid #21262d;font-size:.85em}
th{background:#21262d;color:#8b949e}
.sev-high{color:#f85149}.sev-med{color:#d29922}.sev-low{color:#8b949e}
.ts{color:#8b949e;font-size:.82em}
.btn{background:#21262d;color:#c9d1d9;border:1px solid #30363d;padding:6px 14px;border-radius:6px;cursor:pointer}
pre{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px}
</style></head>
<body>
<h1>CTI Monitoring Dashboard</h1>
<p class="ts" id="ts">Loading...</p>
<div class="grid">
  <div class="card"><div class="val" id="s-total">&ndash;</div><div class="lbl">Total IOCs</div></div>
  <div class="card ok"><div class="val" id="s-active">&ndash;</div><div class="lbl">Active</div></div>
  <div class="card alert"><div class="val" id="s-alerts">&ndash;</div><div class="lbl">Alerts</div></div>
</div>
<h2>Infrastructure Alerts</h2>
<table><thead><tr><th>Time</th><th>IOC</th><th>Type</th><th>Sev</th><th>Source</th><th>Tags</th></tr></thead>
<tbody id="alerts-tbody"><tr><td colspan="6">Loading...</td></tr></tbody></table>
<h2>Top Active IOCs</h2>
<table><thead><tr><th>Value</th><th>Type</th><th>Source</th><th>Sev</th><th>Rel</th><th>Tags</th></tr></thead>
<tbody id="iocs-tbody"><tr><td colspan="6">Loading...</td></tr></tbody></table>
<h2>Pipeline</h2>
<button class="btn" onclick="runPipe()">Run Now</button>
<pre id="log">Click Run Now.</pre>
<script>
async function refresh(){
  try{
    const db=await fetch('/api/db').then(r=>r.json());
    const a=await fetch('/api/alerts').then(r=>r.json());
    document.getElementById('ts').textContent='Updated: '+new Date().toLocaleTimeString();
    document.getElementById('s-total').textContent=db.stats?.total||0;
    document.getElementById('s-active').textContent=db.stats?.active||0;
    document.getElementById('s-alerts').textContent=a.length;
  }catch(e){console.error(e);}
}
async function runPipe(){
  const l=document.getElementById('log');l.textContent='Running...';
  try{const r=await fetch('/api/run',{method:'POST'});l.textContent=JSON.stringify(await r.json(),null,2);refresh();}
  catch(e){l.textContent='Error: '+e;}
}
refresh();setInterval(refresh,30000);
</script></body></html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/dashboard"):
            self.send_response(200); self.send_header("Content-Type","text/html;charset=utf-8"); self.end_headers()
            self.wfile.write(DASH_HTML.encode())
        elif self.path == "/api/db":
            self._json(load_ioc_database())
        elif self.path == "/api/alerts":
            a = []
            if ALERTS_FILE.exists():
                try:
                    with open(ALERTS_FILE,encoding="utf-8") as f: a=json.load(f)
                except: pass
            self._json(a)
        elif self.path == "/api/health":
            self._json({"status":"ok","ts":time.time()})
        else: self.send_error(404)

    def do_POST(self):
        if self.path == "/api/run":
            self._json(run_pipeline())
        else: self.send_error(404)

    def _json(self, data):
        b = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(200); self.send_header("Content-Type","application/json;charset=utf-8")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def log_message(self, *a): pass


def start_dashboard(port=8080):
    with socketserver.TCPServer(("", port), Handler) as h:
        print(f"CTI Dashboard -> http://127.0.0.1:{port}")
        try: h.serve_forever()
        except KeyboardInterrupt: print("\nStopped.")


def main():
    p = argparse.ArgumentParser(description="CTI Monitoring")
    p.add_argument("--daemon", action="store_true")
    p.add_argument("--dashboard", action="store_true")
    p.add_argument("--interval", type=int, default=300)
    p.add_argument("--port", type=int, default=8080)
    p.add_argument("--report-only", action="store_true")
    args = p.parse_args()

    if args.dashboard:
        start_dashboard(args.port); return

    if args.report_only:
        db = load_ioc_database(); apply_aging(db)
        db["stats"] = {"total":len(db["iocs"]),"active":sum(1 for i in db["iocs"].values() if i.get("active",True)),"expired":sum(1 for i in db["iocs"].values() if not i.get("active",True))}
        a = []
        if ALERTS_FILE.exists():
            with open(ALERTS_FILE,encoding="utf-8") as f: a=json.load(f)
        print("Report:", generate_threat_report(db, a)); return

    s = run_pipeline()
    print("SUMMARY:", json.dumps(s, indent=2, default=str))

    if args.daemon:
        print(f"[daemon] loop every {args.interval}s")
        try:
            while True: time.sleep(args.interval); run_pipeline()
        except KeyboardInterrupt: print("\nStopped.")


if __name__ == "__main__":
    main()
