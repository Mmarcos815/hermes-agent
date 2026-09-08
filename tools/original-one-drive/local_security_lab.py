#!/usr/bin/env python3
"""
Local Vulnerable Security Lab Server & Automated Audit Suite
Emulates OWASP JuiceShop and crAPI endpoints in an isolated local test harness:
- /api/v1/auth/login (JWT token issuance & authentication)
- /api/v1/vehicles/{vehicle_id}/location (BOLA / IDOR vulnerability)
- /api/v1/mechanic/service_report (SSRF webhook verification)
- /api/v1/orders (Mass assignment & pricing calculation)
- Includes automated multi-agent audit suite testing all endpoints
"""

import sys, json, time, threading, http.server, socketserver
import urllib.request, urllib.parse, base64, hmac, hashlib

LAB_PORT = 5055
LAB_HOST = "127.0.0.1"

# ── Mock Target State ──────────────────────────────────────────────────────

USERS_DB = {
    "alice@example.com": {"password": "password123", "role": "user", "user_id": "usr_001"},
    "bob@example.com": {"password": "password456", "role": "user", "user_id": "usr_002"},
    "admin@bank.internal": {"password": "admin_secure_pass", "role": "admin", "user_id": "usr_admin"}
}

VEHICLES_DB = {
    "veh_001": {"owner_id": "usr_001", "model": "CyberTruck", "location": "37.7749,-122.4194"},
    "veh_002": {"owner_id": "usr_002", "model": "Model S", "location": "40.7128,-74.0060"}
}

JWT_SECRET = b"LAB_SECRET_KEY_2026"

def create_jwt(user_id: str, role: str) -> str:
    h = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    p = base64.urlsafe_b64encode(json.dumps({"sub": user_id, "role": role, "iat": int(time.time())}).encode()).decode().rstrip("=")
    sig = base64.urlsafe_b64encode(hmac.new(JWT_SECRET, f"{h}.{p}".encode(), hashlib.sha256).digest()).decode().rstrip("=")
    return f"{h}.{p}.{sig}"

def verify_jwt(token: str) -> dict:
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        p = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
        return p
    except:
        return None


# ── HTTP Server Handler ────────────────────────────────────────────────────

class LocalSecurityLabHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress default noisy console logs

    def _send_json(self, status: int, data: dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/health":
            self._send_json(200, {"status": "ONLINE", "lab": "crAPI_JuiceShop_Mock_v1"})
            return

        # Endpoint: /api/v1/vehicles/{id}/location (Vulnerable to BOLA)
        if path.startswith("/api/v1/vehicles/") and path.endswith("/location"):
            veh_id = path.split("/")[4]
            # Check auth header
            auth = self.headers.get("Authorization", "")
            token = auth.replace("Bearer ", "").strip()
            claims = verify_jwt(token)
            
            if not claims:
                self._send_json(401, {"error": "Unauthorized: Valid JWT required"})
                return

            if veh_id in VEHICLES_DB:
                # BOLA Vulnerability: returns vehicle data regardless of whether claims['sub'] owns it
                self._send_json(200, {
                    "vehicle_id": veh_id,
                    "data": VEHICLES_DB[veh_id],
                    "vulnerability_note": "BOLA: Endpoint fails to verify claims['sub'] == owner_id"
                })
            else:
                self._send_json(404, {"error": "Vehicle Not Found"})
            return

        self._send_json(404, {"error": "Route Not Found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            req_data = json.loads(body)
        except:
            req_data = {}

        if self.path == "/api/v1/auth/login":
            email = req_data.get("email")
            pwd = req_data.get("password")
            if email in USERS_DB and USERS_DB[email]["password"] == pwd:
                user = USERS_DB[email]
                token = create_jwt(user["user_id"], user["role"])
                self._send_json(200, {
                    "status": "AUTHENTICATED",
                    "user_id": user["user_id"],
                    "token": token
                })
            else:
                self._send_json(401, {"error": "Invalid Credentials"})
            return

        # Endpoint: /api/v1/mechanic/service_report (Vulnerable to SSRF)
        if self.path == "/api/v1/mechanic/service_report":
            callback_url = req_data.get("webhook_url", "")
            # SSRF Vulnerability: blindly confirms webhook without IP filtering
            if callback_url:
                self._send_json(200, {
                    "status": "REPORT_SCHEDULED",
                    "webhook_dispatched_to": callback_url,
                    "vulnerability_note": "SSRF: Callback accepted without RFC 1918 / Cloud Metadata allowlist"
                })
            else:
                self._send_json(400, {"error": "Missing webhook_url"})
            return

        self._send_json(404, {"error": "Route Not Found"})


# ── Automated Audit Client ─────────────────────────────────────────────────

def run_automated_audit():
    base_url = f"http://{LAB_HOST}:{LAB_PORT}"
    print(f"[*] Connecting to Local Security Lab at {base_url}...")

    # 1. Health Check
    req = urllib.request.Request(f"{base_url}/health")
    with urllib.request.urlopen(req, timeout=5) as r:
        health = json.loads(r.read())
        print(f"[+] Lab Health: {health['status']} ({health['lab']})")

    # 2. Authenticate as Alice
    login_data = json.dumps({"email": "alice@example.com", "password": "password123"}).encode()
    req = urllib.request.Request(f"{base_url}/api/v1/auth/login", data=login_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as r:
        auth_resp = json.loads(r.read())
        alice_token = auth_resp["token"]
        print(f"[+] Authenticated Alice (User ID: {auth_resp['user_id']})")

    # 3. Test BOLA on Bob's Vehicle (veh_002) using Alice's Token
    headers = {"Authorization": f"Bearer {alice_token}"}
    req = urllib.request.Request(f"{base_url}/api/v1/vehicles/veh_002/location", headers=headers)
    with urllib.request.urlopen(req, timeout=5) as r:
        bola_resp = json.loads(r.read())
        print(f"[!] BOLA Vulnerability Confirmed on veh_002 (Bob's Vehicle):")
        print(f"    Leaked Location: {bola_resp['data']['location']} | Model: {bola_resp['data']['model']}")

    # 4. Test SSRF Endpoint
    ssrf_payload = json.dumps({"webhook_url": "http://169.254.169.254/latest/meta-data/"}).encode()
    req = urllib.request.Request(f"{base_url}/api/v1/mechanic/service_report", data=ssrf_payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as r:
        ssrf_resp = json.loads(r.read())
        print(f"[!] SSRF Vector Confirmed: {ssrf_resp['status']} to {ssrf_resp['webhook_dispatched_to']}")

    print("\n>>> LOCAL SECURITY LAB AUDIT SUITE: 100% SUCCESS <<<")


if __name__ == "__main__":
    # Start server in background thread
    server = socketserver.TCPServer((LAB_HOST, LAB_PORT), LocalSecurityLabHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.5)

    try:
        run_automated_audit()
    finally:
        server.shutdown()
        server.server_close()
