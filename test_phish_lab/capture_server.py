#!/usr/bin/env python3
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
        open("captured.log","a").write(json.dumps(entry)+"\n")
        self.send_response(200); self.end_headers()
        self.wfile.write(b"Captured for training.")

if __name__ == "__main__":
    http.server.HTTPServer(("127.0.0.1",8080),H).serve_forever()
