#!/usr/bin/env python3
"""
Activate Bionic Models on Cloud (RunPod)
========================================
Deploys bionic-coder, bionic-deepseek, and bionic-hermes to a RunPod GPU pod
with Ollama, exposing an OpenAI-compatible API endpoint.

Prerequisites:
    pip install runpod paramiko scp
    export RUNPOD_API_KEY=rp_...

Usage:
    python activate_bionic_models.py
"""

import os
import sys
import time
import json
import tarfile
import tempfile
import hashlib
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OLLAMA_ROOT = Path.home() / ".ollama" / "models"
BLOBS_DIR = OLLAMA_ROOT / "blobs"
MANIFESTS_DIR = OLLAMA_ROOT / "manifests"

BIONIC_MODELS = [
    "bionic-coder",    # LoRA on qwen2.5-coder:14b (~9 GB)
    "bionic-deepseek", # LoRA on deepseek-r1:8b   (~5.2 GB)
    "bionic-hermes",   # LoRA on hermes3:8b        (~4.7 GB)
]

# GPU preference: RTX 4090 (cheapest 24 GB) first, then A100
GPU_PREFERENCES = ["NVIDIA RTX 4090", "NVIDIA A100-SXM4-40GB", "NVIDIA A100-80GB"]
OLLAMA_PORT = 11434

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def sha256sum(path: Path, chunk_size: int = 1 << 20) -> str:
    h = hashlib.sha255()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(model: str) -> dict:
    """Load the model manifest; returns dict with 'config' and 'layers'."""
    mpath = MANIFESTS_DIR / "registry.ollama.ai" / "library" / model / "latest"
    if not mpath.exists():
        # Try community namespace
        mpath = MANIFESTS_DIR / "registry.ollama.ai" / "library" / model / "latest"
    return json.loads(mpath.read_bytes())


def collect_blobs_for_model(model: str) -> list[Path]:
    """Return list of local blob Paths required by a bionic model manifest."""
    manifest = load_manifest(model)
    needed = {layer["digest"] for layer in manifest.get("layers", [])}
    needed.add(manifest["config"]["digest"])
    blobs = []
    for digest in needed:
        blob_path = BLOBS_DIR / digest
        if blob_path.exists():
            blobs.append(blob_path)
        else:
            print(f"  WARNING: blob {digest} not found locally")
    return blobs


def build_pod_startup_script() -> str:
    """Bash script that installs Ollama and prepares the container."""
    return """#!/bin/bash
set -euo pipefail

# Install Ollama (idempotent)
if ! command -v ollama &>/dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Run Ollama serve in background, expose on all interfaces
export OLLAMA_HOST=0.0.0.0:11434
export OLLAMA_ORIGINS=*

# Kill any existing instance
pkill ollama || true
sleep 2

# Start server
nohup ollama serve > /tmp/ollama.log 2>&1 &
sleep 5

# Wait for readiness
for i in $(seq 1 30); do
    if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "Ollama is ready"
        break
    fi
    sleep 2
done

echo "STARTUP_COMPLETE"
"""


# ---------------------------------------------------------------------------
# RunPod provisioning
# ---------------------------------------------------------------------------
def create_runpod():
    import runpod
    api_key = os.environ.get("RUNPOD_API_KEY", "")
    if not api_key:
        print("ERROR: RUNPOD_API_KEY not set")
        sys.exit(1)

    runpod.api_key = api_key

    # Find a suitable GPU
    gpu_id = None
    for gpu_name in GPU_PREFERENCES:
        try:
            gpus = runpod.get_gpus()
            for g in gpus:
                if gpu_name.lower() in g["displayName"].lower() and g["lowestPrice"]["minMemory"] > 0:
                    gpu_id = g["id"]
                    print(f"Selected GPU: {g['displayName']}")
                    break
        except Exception as e:
            print(f"GPU lookup failed: {e}")
        if gpu_id:
            break

    if not gpu_id:
        # Fallback: cheapest GPU with >= 24 GB
        gpus = runpod.get_gpus()
        for g in sorted(gpus, key=lambda x: x.get("lowestPrice", {}).get("stockPrice", 999999)):
            if g.get("memoryInGb", 0) >= 24:
                gpu_id = g["id"]
                print(f"Fallback GPU: {g['displayName']} ({g['memoryInGb']} GB)")
                break

    if not gpu_id:
        print("ERROR: No suitable GPU found")
        sys.exit(1)

    # Build the startup script
    startup = build_pod_startup_script()

    # Create pod
    pod = runpod.create_pod(
        name="bionic-models",
        imageName="ollama/ollama:latest",
        gpuTypeId=gpu_id,
        cloudType="SECURE",
        gpuCount=1,
        volumeInGb=50,
        containerDiskInGb=25,
        ports=f"{OLLAMA_PORT}/tcp",
        volumeMountPath="/root/.ollama",
        env={"OLLAMA_HOST": f"0.0.0.0:{OLLAMA_PORT}"},
        dockerArgs=startup,
    )

    pod_id = pod["id"]
    print(f"Pod created: {pod_id}")
    return pod_id


def wait_for_pod(pod_id: str, timeout: int = 600) -> dict:
    """Wait until pod is RUNNING and return its details."""
    import runpod
    start = time.time()
    while time.time() - start < timeout:
        pod = runpod.get_pod(pod_id)
        status = pod.get("desiredStatus", pod.get("runtime", {}).get("status", "UNKNOWN"))
        if status == "RUNNING":
            # Extract connection info
            runtime = pod.get("runtime", {})
            ports = runtime.get("ports", [])
            public_port = None
            for p in ports:
                if str(p.get("privatePort", p.get("containerPort"))) == str(OLLAMA_PORT):
                    public_port = p.get("publicPort", p.get("hostPort"))
                    break
            ip = runtime.get("ip", pod.get("ip"))
            return {
                "id": pod_id,
                "ip": ip,
                "port": public_port or OLLAMA_PORT,
                "status": "RUNNING",
            }
        if status in ("FAILED", "TERMINATED"):
            print(f"Pod entered terminal state: {status}")
            sys.exit(1)
        print(f"Pod status: {status}... waiting")
        time.sleep(10)
    print("Timeout waiting for pod")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Upload models
# ---------------------------------------------------------------------------
def upload_models_to_pod(pod_info: dict):
    """Upload bionic model blobs to the pod via tar+ssh."""
    import paramiko
    from scp import SCPClient

    ip = pod_info["ip"]
    port = pod_info.get("port", OLLAMA_PORT)

    # Collect all unique blobs across the three models
    all_blobs: dict[str, Path] = {}
    for model in BIONIC_MODELS:
        print(f"\nCollecting blobs for {model}...")
        for blob_path in collect_blobs_for_model(model):
            digest = blob_path.name
            if digest not in all_blobs:
                all_blobs[digest] = blob_path
                print(f"  + {digest} ({blob_path.stat().st_size / 1e9:.2f} GB)")

    if not all_blobs:
        print("No blobs to upload!")
        return

    total_gb = sum(p.stat().st_size for p in all_blobs.values()) / 1e9
    print(f"\nTotal upload size: {total_gb:.2f} GB across {len(all_blobs)} blobs")

    # SSH into pod (RunPod uses root + SSH key from your account)
    ssh_key_path = Path.home() / ".ssh" / "id_ed25519"
    if not ssh_key_path.exists():
        ssh_key_path = Path.home() / ".ssh" / "id_rsa"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=ip,
        port=22,
        username="root",
        key_filename=str(ssh_key_path),
        timeout=30,
    )

    # Ensure Ollama models directory exists on pod
    ssh.exec_command("mkdir -p /root/.ollama/models/blobs /root/.ollama/models/manifests/registry.ollama.ai/library")

    # Upload blobs via SCP
    with SCPClient(ssh.get_transport(), progress=lambda f, s, t: print(f"  Uploading {f}: {t}/{s} bytes")) as scp:
        for digest, blob_path in all_blobs.items():
            scp.put(str(blob_path), f"/root/.ollama/models/blobs/{digest}")

    # Upload manifests
    for model in BIONIC_MODELS:
        manifest_path = MANIFESTS_DIR / "registry.ollama.ai" / "library" / model / "latest"
        if manifest_path.exists():
            dest = f"/root/.ollama/models/manifests/registry.ollama.ai/library/{model}"
            ssh.exec_command(f"mkdir -p {dest}")
            with SCPClient(ssh.get_transport()) as scp:
                scp.put(str(manifest_path), f"{dest}/latest")

    # Restart Ollama so it picks up the new models
    ssh.exec_command("pkill ollama; sleep 2; nohup ollama serve > /tmp/ollama.log 2>&1 &")
    ssh.close()
    print("\nAll blobs and manifests uploaded successfully!")


def verify_models_on_pod(pod_info: dict):
    """Poll Ollama's /api/tags until all three models appear."""
    import urllib.request

    url = f"http://{pod_info['ip']}:{pod_info['port']}/api/tags"
    start = time.time()
    while time.time() - start < 300:
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                names = {m["name"] for m in data.get("models", [])}
                if all(f"{m}:latest" in names or m in names for m in BIONIC_MODELS):
                    print("\n✓ All bionic models are loaded!")
                    for m in data.get("models", []):
                        print(f"  - {m['name']} ({m.get('size', 0) / 1e9:.2f} GB)")
                    return True
                else:
                    missing = [m for m in BIONIC_MODELS if m not in names and f"{m}:latest" not in names]
                    print(f"  Waiting for: {', '.join(missing)}")
        except Exception as e:
            print(f"  Ollama not ready yet: {e}")
        time.sleep(10)
    print("Timeout waiting for models to load")
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("  BIONIC MODELS — CLOUD ACTIVATION")
    print("=" * 60)

    # Step 1: Create pod
    print("\n[1/4] Creating RunPod pod with GPU...")
    pod_id = create_runpod()

    # Step 2: Wait for pod
    print("\n[2/4] Waiting for pod to start...")
    pod_info = wait_for_pod(pod_id)

    # Step 3: Upload models
    print("\n[3/4] Uploading bionic model blobs...")
    upload_models_to_pod(pod_info)

    # Step 4: Verify
    print("\n[4/4] Verifying models are loaded...")
    verify_models_on_pod(pod_info)

    # Output endpoint
    endpoint = f"http://{pod_info['ip']}:{pod_info['port']}"
    print("\n" + "=" * 60)
    print(f"  🚀 BIONIC MODELS ACTIVE")
    print(f"  Endpoint: {endpoint}")
    print(f"  OpenAI-compatible API: {endpoint}/v1")
    print(f"  Models: bionic-coder, bionic-deepseek, bionic-hermes")
    print(f"  Pod ID: {pod_id}")
    print("=" * 60)

    # Save endpoint to file
    output_path = Path(__file__).parent / "bionic_endpoint.json"
    output_path.write_text(json.dumps({
        "endpoint": endpoint,
        "openai_endpoint": f"{endpoint}/v1",
        "models": BIONIC_MODELS,
        "pod_id": pod_id,
    }, indent=2))
    print(f"\nEndpoint saved to: {output_path}")


if __name__ == "__main__":
    main()
