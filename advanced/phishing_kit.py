#!/usr/bin/env python3
"""
phishing_kit.py — Phishing page generator (EDUCATIONAL / LAB ONLY).

Generates static HTML phishing pages for security awareness training.
Includes visible training banner and local-only credential logging.

Usage:
    python phishing_kit.py -b microsoft -o ./phish_lab/
    python phishing_kit.py -b google -o ./phish_lab/ --include-server

Safety: Static HTML only. No exfiltration. Training banner on by default.
"""

import argparse, html, sys
from pathlib import Path

BRANDS = {
    "microsoft": {"title": "Sign in to your account", "logo": "Microsoft",
                  "user_ph": "Email, phone, or Skype", "color": "#0078d4"},
    "google": {"title": "Sign in — Google Accounts", "logo": "Google",
               "user_ph": "Email or phone", "color": "#1a73e8"},
    "okta": {"title": "Sign In", "logo": "Okta",
             "user_ph": "Username", "color": "#00297a"},
    "generic": {"title": "Sign in", "logo": "Company",
                "user_ph": "Username", "color": "#2563eb"},
}


def gen_html(brand, banner=True):
    b = BRANDS.get(brand, BRANDS["generic"])
    t = {k: html.escape(v) for k, v in b.items()}
    banner_html = ('<div style="background:#dc2626;color:#fff;text-align:center;'
                   'padding:8px;font:bold 14px sans-serif;">'
                   '⚠️ SECURITY TRAINING — DO NOT ENTER REAL CREDENTIALS ⚠️</div>') if banner else ""

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{t["title"]}</title>
<style>
body{{font-family:sans-serif;background:#f2f2f2;display:flex;justify-content:center;align-items:center;min-height:100vh}}
.box{{background:#fff;padding:44px;width:440px;box-shadow:0 2px 6px rgba(0,0,0,.2)}}
h1{{font-size:24px;margin-bottom:16px}}
label{{display:block;font-size:14px;margin-bottom:4px;font-weight:500}}
input{{width:100%;padding:8px 12px;margin-bottom:16px;border:1px solid #ccc;border-radius:4px}}
button{{width:100%;padding:10px;background:{t["color"]};color:#fff;border:none;border-radius:4px;font-weight:600;cursor:pointer}}
.warn{{background:#fef3c7;border:1px solid #f59e0b;padding:12px;border-radius:4px;margin-bottom:16px;font-size:13px;color:#92400e}}
</style></head><body>
{banner_html}
<div class="box">
<div style="font-size:24px;font-weight:600;margin-bottom:16px">{t["logo"]}</div>
<h1>{t["title"]}</h1>
<div class="warn"><strong>Training simulation.</strong> Credentials logged locally only.</div>
<form action="/capture" method="POST">
<label>Username</label><input name="username" placeholder="{t["user_ph"]}" required>
<label>Password</label><input type="password" name="password" required>
<button type="submit">Sign In</button>
</form></div></body></html>"""


def gen_server():
    return '''#!/usr/bin/env python3
"""Training capture server — logs to local file only."""
import http.server, urllib.parse, json
from datetime import datetime

class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length",0)))
        data = urllib.parse.parse_qs(body.decode())
        entry = {"time": datetime.now().isoformat(), "ip": self.client_address[0],
                 "user": data.get("username",[""])[0],
                 "pw_len": len(data.get("password",[""])[0])}
        open("captured.log","a").write(json.dumps(entry)+"\\n")
        self.send_response(200); self.end_headers()
        self.wfile.write(b"Captured for training.")

if __name__ == "__main__":
    http.server.HTTPServer(("127.0.0.1",8080),H).serve_forever()
'''


def main(argv=None):
    p = argparse.ArgumentParser(description="Phishing kit generator (training only)")
    p.add_argument("-b", "--brand", default="generic", choices=list(BRANDS))
    p.add_argument("-o", "--output", default="./phish_lab")
    p.add_argument("--no-banner", action="store_true")
    p.add_argument("--include-server", action="store_true")
    a = p.parse_args(argv)

    out = Path(a.output)
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(gen_html(a.brand, not a.no_banner))
    print(f"[+] Page: {out / 'index.html'}")

    if a.include_server:
        (out / "capture_server.py").write_text(gen_server())
        print(f"[+] Server: {out / 'capture_server.py'}")

    print(f"    Brand: {a.brand}  |  Banner: {'OFF' if a.no_banner else 'ON'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
