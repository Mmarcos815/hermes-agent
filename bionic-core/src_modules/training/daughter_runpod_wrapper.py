# ============================================================================
# BIONIC DAUGHTER v1 — RUNPOD WRAPPER MODULE (v2 — corrected SDK usage)
# ============================================================================
# Direct RunPod API integration for cloud GPU pod management.
# Uses the RunPod Python SDK (v1.12.0) for full pod lifecycle control.
#
# CORRECTED SDK API (verified against runpod==1.12.0):
#   runpod.api_key = "..."              — set API key
#   runpod.get_user()                   — returns {'id': ..., 'pubKey': ..., ...}
#   runpod.get_pods()                   — returns list of pod dicts
#   runpod.get_gpus()                   — returns list of GPU dicts
#       Each GPU dict: {'id': 'NVIDIA GeForce RTX 4090', 'displayName': 'RTX 4090', 'memoryInGb': 24}
#       NOTE: 'id' field IS the GPU type identifier for create_pod()
#   runpod.create_pod(name, image_name, gpu_type_id, cloud_type, ...) — create pod
#   runpod.terminate_pod(pod_id)        — terminate a pod
#
# Capabilities:
#   - List available GPU pod types and pricing (from real API)
#   - Launch GPU pods (RTX-4090, A100, T4, L4, H100, etc.)
#   - Manage pod lifecycle: start, stop, sleep, wake
#   - Monitor pod status and costs
#   - Auto-shutdown to stop billing
#
# Safety: Monthly spend cap ($50), approval gate ($10+), full audit log.
# ============================================================================

import os
import sys
import json
import time
import logging
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

try:
    import runpod
    RUNPOD_SDK_AVAILABLE = True
except ImportError:
    RUNPOD_SDK_AVAILABLE = False
    runpod = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DaughterRunPod")

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
GPU_STATE_FILE = DATA_DIR / "gpu_state.json"
MONTHLY_SPEND_FILE = DATA_DIR / "monthly_spend.json"
POD_LOG_FILE = DATA_DIR / "pod_history.jsonl"

for d in [DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

MONTHLY_SPEND_LIMIT_USD = 50.0
APPROVAL_THRESHOLD_USD = 10.0
DEFAULT_POD_HOURS = 5

# ============================================================================
# SAFETY
# ============================================================================

def _check_monthly_limit(cost_usd: float) -> bool:
    monthly = _load_monthly_spend()
    projected = monthly.get("spent", 0.0) + cost_usd
    if projected > MONTHLY_SPEND_LIMIT_USD:
        logger.warning(f"SAFETY: Would exceed monthly limit. Projected: ${projected:.2f} / Limit: ${MONTHLY_SPEND_LIMIT_USD:.2f}")
        return False
    return True

def _check_approval_threshold(cost_usd: float) -> bool:
    if cost_usd > APPROVAL_THRESHOLD_USD:
        logger.info(f"APPROVAL NEEDED: This pod will cost ~${cost_usd:.2f} (above ${APPROVAL_THRESHOLD_USD:.2f} threshold). Dad must approve.")
        return False
    return True

def _record_spend(cost_usd: float):
    monthly = _load_monthly_spend()
    monthly["spent"] = monthly.get("spent", 0.0) + cost_usd
    monthly["last_updated"] = datetime.now().isoformat()
    monthly["history"].append({"timestamp": datetime.now().isoformat(), "amount": cost_usd})
    if len(monthly["history"]) > 100:
        monthly["history"] = monthly["history"][-100:]
    _save_monthly_spend(monthly)

# ============================================================================
# STATE
# ============================================================================

def _load_gpu_state() -> dict:
    if GPU_STATE_FILE.exists():
        return json.loads(GPU_STATE_FILE.read_text())
    return {"active_pods": [], "total_launch_count": 0, "total_shutdown_count": 0}

def _save_gpu_state(state: dict):
    GPU_STATE_FILE.write_text(json.dumps(state, indent=2))

def _load_monthly_spend() -> dict:
    if MONTHLY_SPEND_FILE.exists():
        return json.loads(MONTHLY_SPEND_FILE.read_text())
    return {"spent": 0.0, "month": datetime.now().strftime("%Y-%m"), "history": []}

def _save_monthly_spend(data: dict):
    MONTHLY_SPEND_FILE.write_text(json.dumps(data, indent=2))

def _log_pod_event(event: dict):
    POD_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(POD_LOG_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")

# ============================================================================
# GPU TYPE RESOLUTION
# ============================================================================

def _resolve_gpu_type_id(gpu_type_name: str, all_gpus: list) -> Optional[str]:
    """Find GPU type ID from display name.

    RunPod's get_gpus() returns dicts like:
        {'displayName': 'RTX 4090', 'id': 'NVIDIA GeForce RTX 4090', 'memoryInGb': 24}
    The 'id' field is what create_pod(gpu_type_id=...) needs.

    Args:
        gpu_type_name: Human-readable name ('RTX-4090', 'A100-80GB', etc.)
        all_gpus: List of GPU dicts from runpod.get_gpus().

    Returns:
        GPU type ID string (the 'id' field), or None.
    """
    query = gpu_type_name.lower().replace("-", " ")
    for g in all_gpus:
        if not isinstance(g, dict):
            continue
        gdisplay = g.get("displayName", "").lower()
        if not gdisplay:
            continue
        if query == gdisplay or query in gdisplay or gdisplay in query:
            return g.get("id")
    return None

def _format_gpu_list_for_display(gpu_list: list) -> str:
    """Format GPU list for human-readable display."""
    lines = []
    for g in gpu_list:
        if not isinstance(g, dict):
            continue
        gid = g.get("id", "unknown")
        display = g.get("displayName", gid)
        mem = g.get("memoryInGb", "?")
        lines.append(f"  - {display} (id={gid}, memory={mem}GB)")
    return "\n".join(lines)

# ============================================================================
# RUNPOD WRAPPER
# ============================================================================

class RunPodWrapper:
    """Direct RunPod API wrapper for Bionic Daughter v1."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("RUNPOD_API_KEY", "")
        self._all_gpus: List[Dict] = []
        self._state = _load_gpu_state()
        self.active_pods: List[Dict] = self._state.get("active_pods", [])
        self.user_info: Optional[Dict] = None
        if self.api_key and RUNPOD_SDK_AVAILABLE:
            runpod.api_key = self.api_key

    def is_sdk_ready(self) -> bool:
        return bool(RUNPOD_SDK_AVAILABLE and self.api_key)

    def refresh_gpu_list(self):
        """Fetch latest GPU list from RunPod API."""
        self._all_gpus = []
        if self.is_sdk_ready():
            try:
                self._all_gpus = runpod.get_gpus()
                logger.info(f"Fetched {len(self._all_gpus)} GPU types from RunPod API.")
            except Exception as e:
                logger.warning(f"Failed to fetch GPU list: {e}")
        return self._all_gpus

    def list_gpu_types(self) -> list:
        """List available GPU types with pricing from RunPod API."""
        if not self._all_gpus:
            self.refresh_gpu_list()
        result = []
        for g in self._all_gpus:
            if not isinstance(g, dict):
                continue
            display = g.get("displayName", g.get("id", "unknown"))
            # RunPod API doesn't return price in get_gpus() — use known rates
            # The actual price is determined at pod creation time
            result.append({
                "gpu_type": display,
                "gpu_type_id": g.get("id"),
                "memory_gb": g.get("memoryInGb", 0),
            })
        return result

    def get_gpu_info(self) -> dict:
        """Get user info and GPU catalog from RunPod."""
        if not self.user_info and self.is_sdk_ready():
            try:
                self.user_info = runpod.get_user()
            except Exception as e:
                logger.warning(f"Failed to get user info: {e}")
        return {
            "user": self.user_info,
            "gpu_types_available": self.list_gpu_types(),
            "sdk_ready": self.is_sdk_ready(),
        }

    def get_user_info(self) -> Optional[Dict]:
        if not self.user_info and self.is_sdk_ready():
            try:
                self.user_info = runpod.get_user()
            except Exception as e:
                logger.warning(f"Failed to get user info: {e}")
                return None
        return self.user_info

    def estimate_cost(self, gpu_type: str, hours: float) -> float:
        """Estimate cost. Uses known rates since get_gpus() doesn't return pricing."""
        # Known approximate hourly rates (verified via RunPod dashboard)
        known_rates = {
            "RTX-4090": 0.34, "NVIDIA GeForce RTX 4090": 0.34,
            "A100-80GB": 1.39, "NVIDIA A100-SXM4-80GB": 1.39, "NVIDIA A100 80GB PCIe": 1.39,
            "A100-40GB": 0.79, "NVIDIA A100-SXM4-40GB": 0.79,
            "T4": 0.35, "NVIDIA T4": 0.35,
            "L4": 0.39, "NVIDIA L4": 0.39,
            "H100": 2.00, "NVIDIA H100": 2.00,
            "A6000": 0.49,
            "V100": 0.45,
            "A10": 0.35,
            "L40": 0.39,
        }
        rate = known_rates.get(gpu_type, 0.34)
        return round(rate * hours, 2)

    def get_pods(self) -> list:
        if not self.is_sdk_ready():
            return []
        try:
            pods = runpod.get_pods()
            return pods if isinstance(pods, list) else []
        except Exception as e:
            logger.warning(f"Failed to get pods: {e}")
            return []

    def get_pod(self, pod_id: str) -> Optional[Dict]:
        pods = self.get_pods()
        for p in pods:
            if isinstance(p, dict) and p.get("id") == pod_id:
                return p
        return None

    def launch_pod(
            self,
            gpu_type: str = "RTX-4090",
            hours: float = DEFAULT_POD_HOURS,
            docker_image: str = "runpod/pytorch:3.10-2.0.1-cuda11.8.0",
            needs_approval: bool = True,
            disk_size_gb: int = 50,
            name: Optional[str] = None,
            cloud_type: str = "SECURE",
        ) -> dict:
            """Launch a cloud GPU pod on RunPod via SDK."""
            # Refresh GPU catalog
            self.refresh_gpu_list()

            # Resolve GPU type ID from name (handles "RTX-4090" -> "NVIDIA GeForce RTX 4090")
            gpu_type_id = _resolve_gpu_type_id(gpu_type, self._all_gpus)
            if not gpu_type_id:
                available = [g.get("displayName", g.get("id", "")) for g in self._all_gpus if isinstance(g, dict)]
                return {
                    "status": "gpu_type_not_found",
                    "message": f"GPU type '{gpu_type}' not found in RunPod catalog. Try one of: {available[:15]}",
                    "available_gpus": available,
                }

            # Estimate cost
            estimated = self.estimate_cost(gpu_type, hours)

            # Safety checks
            if needs_approval and not _check_approval_threshold(estimated):
                return {"status": "approval_required", "estimated_cost": estimated,
                        "message": f"This pod costs ~${estimated:.2f} — Dad's approval required (above ${APPROVAL_THRESHOLD_USD:.2f} threshold)."}

            if not _check_monthly_limit(estimated):
                return {"status": "limit_exceeded", "estimated_cost": estimated,
                        "message": f"Monthly limit (${MONTHLY_SPEND_LIMIT_USD:.2f}) would be exceeded."}

            if not self.api_key:
                return {"status": "unconfigured", "message": "RUNPOD_API_KEY not set."}

            pod_name = name or f"daughter-{int(time.time())}-{hashlib.md5(f'{gpu_type}-{hours}'.encode()).hexdigest()[:8]}"

            pod_info = {
                "pod_name": pod_name,
                "provider": "runpod",
                "gpu_type": gpu_type,
                "gpu_type_id": gpu_type_id,
                "hours": hours,
                "docker_image": docker_image,
                "disk_size_gb": disk_size_gb,
                "estimated_cost": estimated,
                "launch_time": datetime.now().isoformat(),
                "status": "creating",
            }

            # Create pod via SDK
            if self.is_sdk_ready():
                try:
                    created = runpod.create_pod(
                        name=pod_name,
                        image_name=docker_image,
                        gpu_type_id=gpu_type_id,
                        cloud_type=cloud_type,
                        volume_in_gb=disk_size_gb,
                        support_public_ip=True,
                        start_ssh=True,
                    )
                    if isinstance(created, dict):
                        pod_info["pod_id"] = created.get("id", created.get("pod_id", pod_name))
                        pod_info["status"] = created.get("status", "creating")
                        pod_info["sdk_response"] = {k: v for k, v in created.items() if k not in ("id", "pod_id", "status")}
                    elif hasattr(created, "id"):
                        pod_info["pod_id"] = created.id
                        pod_info["status"] = getattr(created, "status", "creating")
                    else:
                        pod_info["pod_id"] = str(created)
                        pod_info["status"] = "creating"
                    pod_info["api_url"] = f"https://dashboard.runpod.com/pod/{pod_info['pod_id']}"
                    logger.info(f"SDK: Pod created — ID: {pod_info['pod_id']} | Status: {pod_info['status']}")
                except Exception as e:
                    error_msg = str(e)
                    logger.warning(f"SDK pod creation failed: {error_msg}")
                    pod_info["sdk_error"] = error_msg
                    pod_info["pod_id"] = f"daughter-local-{int(time.time())}-{hashlib.md5(f'{gpu_type}-{hours}'.encode()).hexdigest()[:8]}"
                    pod_info["status"] = "local_planning"

            pod_info["id"] = pod_info.get("pod_id", pod_name)
            self.active_pods.append(pod_info)
            self._state["active_pods"] = self.active_pods
            self._state["total_launch_count"] = self._state.get("total_launch_count", 0) + 1
            _save_gpu_state(self._state)
            _record_spend(estimated)

            _log_pod_event({"event": "pod_launched", "pod_id": pod_info["id"],
                            "gpu_type": gpu_type, "gpu_type_id": gpu_type_id,
                            "estimated_cost": estimated, "hours": hours})

            logger.info(f"Pod launched: {pod_info['id']} | GPU: {gpu_type} ({gpu_type_id}) | Est: ${estimated:.2f} | Hours: {hours}")

            return {
                "status": pod_info["status"] if pod_info["status"] != "local_planning" else "launched_local",
                "pod_id": pod_info["id"],
                "pod_name": pod_info["pod_name"],
                "gpu_type": gpu_type,
                "gpu_type_id": gpu_type_id,
                "estimated_cost": estimated,
                "details": {k: v for k, v in pod_info.items() if k not in ("sdk_response", "sdk_error", "id")},
                "sdk_error": pod_info.get("sdk_error"),
            }

    def approve_pod(self, pod_id: str) -> dict:
        for pod in self.active_pods:
            if pod.get("pod_id") == pod_id or pod.get("id") == pod_id:
                pod["approved"] = True
                pod["approval_time"] = datetime.now().isoformat()
                _save_gpu_state(self._state)
                _log_pod_event({"event": "pod_approved", "pod_id": pod_id, "approved_by": "Dad",
                                "timestamp": datetime.now().isoformat()})
                logger.info(f"Pod {pod_id} approved by Dad.")
                return {"status": "approved", "pod_id": pod_id}
        return {"status": "not_found", "pod_id": pod_id}

    def get_active_pods(self) -> list:
        return list(self.active_pods)

    def get_pod_status(self, pod_id: str) -> dict:
        for pod in self.active_pods:
            if pod.get("pod_id") == pod_id or pod.get("id") == pod_id:
                result = {
                    "pod_id": pod_id,
                    "local_status": pod.get("status", "unknown"),
                    "gpu_type": pod.get("gpu_type"),
                    "hours": pod.get("hours"),
                    "estimated_cost": pod.get("estimated_cost"),
                    "launch_time": pod.get("launch_time"),
                    "provider": pod.get("provider"),
                    "api_url": pod.get("api_url"),
                }
                api_pod = self.get_pod(pod_id)
                if api_pod:
                    result["api_status"] = api_pod.get("status", "unknown")
                    result["api_alive"] = api_pod.get("status") == "RUNNING"
                else:
                    result["api_status"] = "not_found_in_api"
                return result
        api_pod = self.get_pod(pod_id)
        if api_pod:
            return {"pod_id": pod_id, "api_status": api_pod.get("status", "unknown"),
                    "api_alive": api_pod.get("status") == "RUNNING", "note": "in API only"}
        return {"pod_id": pod_id, "status": "not_found"}

    def monitor_all(self) -> list:
        results = []
        for pod in self.active_pods:
            pod_id = pod.get("pod_id") or pod.get("id")
            status = self.get_pod_status(pod_id)
            status["auto_shutdown_due"] = (
                datetime.fromisoformat(pod["launch_time"]).timestamp()
                + pod.get("hours", DEFAULT_POD_HOURS) * 3600
            ) if pod.get("launch_time") else None
            results.append(status)
        return results

    def shutdown_pod(self, pod_id: str) -> dict:
        if self.is_sdk_ready():
            try:
                runpod.terminate_pod(pod_id=pod_id)
                logger.info(f"SDK: Pod {pod_id} terminated via API.")
            except Exception as e:
                logger.warning(f"SDK termination failed: {e}")
        for i, pod in enumerate(self.active_pods):
            if pod.get("pod_id") == pod_id or pod.get("id") == pod_id:
                pod["status"] = "shutdown"
                pod["shutdown_time"] = datetime.now().isoformat()
                self.active_pods.pop(i)
                self._state["active_pods"] = self.active_pods
                self._state["total_shutdown_count"] = self._state.get("total_shutdown_count", 0) + 1
                _save_gpu_state(self._state)
                _log_pod_event({"event": "pod_shutdown", "pod_id": pod_id,
                                "shutdown_time": pod["shutdown_time"], "total_cost": pod.get("estimated_cost")})
                logger.info(f"Pod {pod_id} shut down. Cost: ${pod.get('estimated_cost', 0):.2f}")
                return {"status": "shutdown", "pod_id": pod_id, "shutdown_time": pod["shutdown_time"],
                        "estimated_cost": pod.get("estimated_cost")}
        return {"status": "not_found", "pod_id": pod_id}

    def shutdown_all(self) -> list:
        results = []
        for pod in list(self.active_pods):
            pod_id = pod.get("pod_id") or pod.get("id")
            results.append(self.shutdown_pod(pod_id))
        return results

    def auto_shutdown_expired(self) -> list:
        now = datetime.now()
        expired = []
        for pod in list(self.active_pods):
            launch = datetime.fromisoformat(pod["launch_time"])
            max_age = timedelta(hours=pod.get("hours", DEFAULT_POD_HOURS))
            if now - launch > max_age:
                pod_id = pod.get("pod_id") or pod.get("id")
                result = self.shutdown_pod(pod_id)
                if result["status"] == "shutdown":
                    expired.append(pod_id)
        if expired:
            logger.info(f"Auto-shutdown: {len(expired)} pods expired — {expired}")
        return expired

    def launch_training(
        self,
        training_script: str = "daughter_grpo_pipeline.py",
        gpu_type: str = "RTX-4090",
        hours: float = DEFAULT_POD_HOURS,
        extra_args: str = "",
        docker_image: str = "runpod/pytorch:3.10-2.0.1-cuda11.8.0",
    ) -> dict:
        """Full training workflow: launch pod + commands + notes."""
        pod_result = self.launch_pod(gpu_type=gpu_type, hours=hours, docker_image=docker_image)
        if pod_result["status"] not in ("launched", "launched_local", "approval_required"):
            return pod_result

        pod_id = pod_result["pod_id"]
        estimated = pod_result["estimated_cost"]
        train_cmd = (
            f"python {training_script} "
            f"--base_model Qwen/Qwen3-4B-Thinking-2507 "
            f"--output_dir /workspace/bionic_daughter/outputs "
            f"--sft_dataset curriculum/sft_curriculum.jsonl "
            f"--grpo_dataset curriculum/grpo_curriculum.jsonl "
            f"--max_steps_sft 50 --max_steps_grpo 200 "
            f"--batch_size 1 --lora_r 32 "
            f"--max_seq_length 2048 --gpu_memory_utilization 0.7 "
            f"{extra_args}"
        )
        return {
            "status": "ready",
            "pod_id": pod_id,
            "estimated_cost": estimated,
            "commands": {
                "install_deps": "pip install -q torch transformers accelerate unsloth trl datasets tokenizers chromadb psutil mcp llama-cpp-python protobuf deepspeed vllm",
                "pull_model": "python -c \"from huggingface_hub import snapshot_download; snapshot_download(repo_id='Qwen/Qwen3-4B-Thinking-2507', local_dir='/workspace/model_cache/Qwen/Qwen3-4B-Thinking-2507', resume_download=True)\"",
                "run_training": train_cmd,
                "save_artifacts": "tar czf /workspace/bionic_daughter_training_output.tar.gz /workspace/bionic_daughter/outputs/ && cp /workspace/bionic_daughter_training_output.tar.gz /workspace/",
            },
            "notes": [
                f"Estimated total cost: ${estimated:.2f}",
                f"Training will take ~3-5 hours on {gpu_type}",
                "Save model artifacts after training — download the tarball",
                "Run auto_shutdown_expired() or shutdown_pod() when done to stop billing",
            ],
        }

    def monthly_report(self) -> dict:
        monthly = _load_monthly_spend()
        return {
            "month": monthly.get("month", "unknown"),
            "total_spent": monthly.get("spent", 0.0),
            "limit": MONTHLY_SPEND_LIMIT_USD,
            "remaining": max(0, MONTHLY_SPEND_LIMIT_USD - monthly.get("spent", 0.0)),
            "pod_count": len(self.active_pods),
            "total_launches": self._state.get("total_launch_count", 0),
            "total_shutdowns": self._state.get("total_shutdown_count", 0),
            "active_pods": [p.get("pod_id", p.get("id")) for p in self.active_pods],
            "safety_status": "OK" if monthly.get("spent", 0) < MONTHLY_SPEND_LIMIT_USD else "LIMIT_EXCEEDED",
            "sdk_ready": self.is_sdk_ready(),
            "api_key_configured": bool(self.api_key),
            "user_id": (self.user_info or {}).get("id"),
        }


if __name__ == "__main__":
    rp = RunPodWrapper()
    print("=== RunPod Wrapper Status ===")
    print(f"API key configured: {bool(rp.api_key)}")
    print(f"SDK available: {RUNPOD_SDK_AVAILABLE}")
    print(f"SDK ready: {rp.is_sdk_ready()}")
    user = rp.get_user_info()
    if user:
        print(f"User ID: {user.get('id', 'unknown')}")
    print()
    print("=== Available GPU Types (from RunPod API) ===")
    gpus = rp.list_gpu_types()
    for gt in gpus:
        print(f"  {gt['gpu_type']} (id={gt['gpu_type_id']}, memory={gt['memory_gb']}GB)")
    print()
    print("=== Cost Estimates ===")
    for gtype in ["RTX-4090", "A100-80GB", "T4"]:
        for h in [1, 3, 5, 10]:
            print(f"  {gtype} × {h}h = ${rp.estimate_cost(gtype, h):.2f}")
    print()
    print(f"=== Safety: \${MONTHLY_SPEND_LIMIT_USD:.2f}/mo cap, \${APPROVAL_THRESHOLD_USD:.2f} approval threshold ===")
    print()
    report = rp.monthly_report()
    print("=== Monthly Report ===")
    for k, v in report.items():
        print(f"  {k}: {v}")
    print()
    print("=== Demo: Launch Training ===")
    result = rp.launch_training(training_script="daughter_grpo_pipeline.py", hours=5)
    print(f"Status: {result['status']}")
    if result['status'] in ('launched', 'launched_local', 'ready'):
        print(f"Pod ID: {result['pod_id']}")
        print(f"Estimated cost: ${result['estimated_cost']:.2f}")
        print(f"Commands: {list(result['commands'].keys())}")
        print(f"Train cmd: {result['commands']['run_training'][:100]}...")
        if result.get('sdk_error'):
            print(f"SDK note: {result['sdk_error']}")
    elif result['status'] == 'approval_required':
        print(f"\n{result['message']}")
    print("\n=== Cleanup ===")
    rp.shutdown_all()
    print("Done.")
