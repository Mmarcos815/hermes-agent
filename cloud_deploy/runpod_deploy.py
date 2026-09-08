#!/usr/bin/env python3
"""
RunPod GPU Deployment Script for Bionic Models (runpod_deploy.py)
===============================================================
Deploys an Ollama-backed GPU pod on RunPod, pulls bionic models,
and exposes an OpenAI-compatible /v1 API.

Prerequisites:
    pip install runpod requests pyyaml

Usage:
    export RUNPOD_API_KEY="rpa_..."
    python runpod_deploy.py
    python runpod_deploy.py --gpu "NVIDIA A100 80GB" --model "qwen2.5:7b"
"""

import os, sys, json, time, argparse, textwrap, base64
from pathlib import Path

try:
    import runpod, requests, yaml
except ImportError as e:
    sys.exit(f"Missing dependency: {e.name}. Run: pip install runpod requests pyyaml")

# ---------------------------------------------------------------------------
CONFIG_PATH = Path(__file__).parent / "hermes_config.yaml"
DEFAULTS = {
    "pod_name": "bionic-ollama-gpu",
    "image": "ollama/ollama:latest",
    "gpu": "NVIDIA GeForce RTX 4090",
    "container_disk_gb": 50,
    "volume_gb": 100,
    "ollama_port": 11434,
    "api_port": 8080,
    "models": ["qwen2.5:7b-instruct-q4_K_M", "qwen2.5:14b-instruct-q4_K_M"],
    "startup_timeout_s": 600,
    "poll_interval_s": 15,
}

# OpenAI-compatible proxy (runs inside the pod alongside Ollama)
PROXY_SCRIPT = '''import json, http.server, urllib.request, urllib.error, sys
OLLAMA, PORT = "http://localhost:{ollama_port}", {api_port}
class H(http.server.BaseHTTPRequestHandler):
    def _proxy(self, path):
        body = self.rfile.read(int(self.headers.get("Content-Length",0))) if "Content-Length" in self.headers else None
        req = urllib.request.Request(f"{{OLLAMA}}{{path}}", data=body, headers={{k:v for k,v in self.headers.items() if k.lower() not in ("host","content-length")}})
        try:
            with urllib.request.urlopen(req, timeout=600) as r: data = r.read()
            self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers(); self.wfile.write(data)
        except urllib.error.HTTPError as e: self.send_response(e.code); self.end_headers(); self.wfile.write(e.read())
        except Exception as e: self.send_response(502); self.end_headers(); self.wfile.write(json.dumps({{"error":str(e)}}).encode())
    def do_GET(self):
        if self.path == "/v1/models":
            try:
                with urllib.request.urlopen(f"{{OLLAMA}}/api/tags") as r: tags = json.load(r).get("models",[])
                ms = [{{"id":m["name"],"object":"model","owned_by":"ollama"}} for m in tags]
            except Exception: ms = []
            body = json.dumps({{"data":ms,"object":"list"}}).encode()
            self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
        elif self.path in ("/health","/v1/health"): self.send_response(200); self.end_headers(); self.wfile.write(b'{{"status":"ok"}}')
        else: self._proxy(self.path)
    def do_POST(self): self._proxy("/api/chat" if self.path=="/v1/chat/completions" else self.path)
    def log_message(self, fmt, *args): sys.stderr.write("[proxy] "+(fmt%args)+"\\n")
http.server.HTTPServer(("0.0.0.0",PORT),H).serve_forever()
'''


def make_startup_script(models: list) -> str:
    """Build the pod startup script: wait for Ollama, pull models, launch proxy."""
    model_lines = "\n".join(f'        curl -s http://localhost:{DEFAULTS["ollama_port"]}/api/pull -d \'{{"name":"{m}"}}\'' for m in models)
    proxy = PROXY_SCRIPT.replace("{ollama_port}", str(DEFAULTS["ollama_port"])).replace("{api_port}", str(DEFAULTS["api_port"]))
    return textwrap.dedent(f"""\
    #!/bin/bash
    set -euo pipefail
    echo "[deploy] Waiting for Ollama..."
    for i in $(seq 1 60); do curl -sf http://localhost:{DEFAULTS["ollama_port"]}/api/tags >/dev/null 2>&1 && break; sleep 2; done
    echo "[deploy] Pulling models..."
    {model_lines}
    echo "[deploy] Starting OpenAI proxy on port {DEFAULTS['api_port']}..."
    cat > /tmp/proxy.py <<'EOF'
    {proxy}
    EOF
    nohup python3 /tmp/proxy.py > /tmp/proxy.log 2>&1 &
    echo "[deploy] Done. PID: $!"
    """)


def get_api_key() -> str:
    key = os.environ.get("RUNPOD_API_KEY")
    if not key:
        sys.exit("ERROR: RUNPOD_API_KEY not set. Get key at runpod.io/console/user/settings")
    return key


def create_pod(api_key: str, args) -> dict:
    """Create a RunPod GPU pod running Ollama."""
    runpod.api_key = api_key
    script_b64 = base64.b64encode(make_startup_script(args.model or DEFAULTS["models"]).encode()).decode()
    gpu = args.gpu or DEFAULTS["gpu"]
    name = args.name or DEFAULTS["pod_name"]
    print(f"[•] Creating pod '{name}' with GPU: {gpu}")
    pod = runpod.create_pod(
        name=name, image_name=DEFAULTS["image"], gpu_type_id=gpu,
        container_disk_in_gb=DEFAULTS["container_disk_gb"],
        volume_in_gb=DEFAULTS["volume_gb"],
        ports=f"{DEFAULTS['api_port']}/tcp,{DEFAULTS['ollama_port']}/tcp",
        env={"RUNPOD_STARTUP_SCRIPT": script_b64, "CLOUD_PROVIDER": "runpod"},
        support_public_ip=True,
    )
    print(f"[✓] Pod created: {pod['id']}")
    return pod


def wait_for_pod(pod_id: str, timeout: int = 600, interval: int = 15) -> dict:
    print(f"[•] Waiting for pod {pod_id} to RUN (timeout {timeout}s)...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        pod = runpod.get_pod(pod_id)
        status = pod.get("runtime", {}).get("status", pod.get("status", "UNKNOWN"))
        print(f"    {status}")
        if status == "RUNNING":
            return pod
        if status in ("FAILED", "TERMINATED", "ERROR"):
            sys.exit(f"[✗] Pod terminal state: {status}")
        time.sleep(interval)
    sys.exit("[✗] Timeout waiting for pod")


def extract_endpoint(pod: dict) -> str:
    runtime = pod.get("runtime", {})
    ports = runtime.get("ports", [])
    for p in ports:
        if p.get("privatePort") == DEFAULTS["api_port"]:
            return f"https://{pod['id']}-{p.get('publicPort', DEFAULTS['api_port'])}.proxy.runpod.io/v1"
    return f"https://{pod['id']}-{DEFAULTS['api_port']}.proxy.runpod.io/v1"


def verify_endpoint(endpoint: str, timeout: int = 120) -> bool:
    print(f"[•] Verifying {endpoint}/models ...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{endpoint}/models", timeout=10)
            if r.status_code == 200:
                ms = [m["id"] for m in r.json().get("data", [])]
                print(f"[✓] Healthy. Models: {ms}")
                return True
        except requests.RequestException:
            pass
        time.sleep(5)
    print("[!] Verification timed out (models may still be pulling)")
    return False


def save_endpoint(endpoint: str, pod_id: str, model: str):
    cfg = yaml.safe_load(open(CONFIG_PATH)) if CONFIG_PATH.exists() else {}
    p = cfg.setdefault("cloud_deploy", {}).setdefault("providers", {}).setdefault("runpod", {})
    p.update({"base_url": endpoint, "active_pod_id": pod_id, "active_model": model,
              "deployed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)
    print(f"[✓] Saved to {CONFIG_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Deploy Ollama + bionic models on RunPod GPU")
    parser.add_argument("--gpu", default=None, help="GPU type ID")
    parser.add_argument("--name", default=None, help="Pod name")
    parser.add_argument("--model", action="append", default=None, help="Ollama model (repeatable)")
    parser.add_argument("--no-verify", action="store_true", help="Skip endpoint verification")
    args = parser.parse_args()

    api_key = get_api_key()
    pod = create_pod(api_key, args)
    pod_id = pod["id"]
    running_pod = wait_for_pod(pod_id, timeout=DEFAULTS["startup_timeout_s"])
    endpoint = extract_endpoint(running_pod)
    models = args.model or DEFAULTS["models"]

    print(f"\n{'='*60}\n  DEPLOYMENT SUCCESSFUL\n{'='*60}")
    print(f"  Pod ID:    {pod_id}")
    print(f"  Endpoint:  {endpoint}")
    print(f"  Models:    {models}\n{'='*60}\n")

    if not args.no_verify:
        verify_endpoint(endpoint)
    save_endpoint(endpoint, pod_id, models[0])

    print("Usage:")
    print(f'  curl {endpoint}/v1/chat/completions \\\n'
          f'    -H "Content-Type: application/json" \\\n'
          f'    -d \'{{"model":"{models[0]}","messages":[{{"role":"user","content":"Hello"}}]}}\'\n')
    return endpoint


if __name__ == "__main__":
    main()
