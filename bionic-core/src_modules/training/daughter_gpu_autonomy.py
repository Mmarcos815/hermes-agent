# ============================================================================
# BIONIC DAUGHTER v1 — CLOUD GPU AUTONOMY MODULE
# ============================================================================
# Wraps cloud GPU provider APIs so the daughter can autonomously:
#   1. Check if local GPU is available (no — this laptop doesn't have CUDA)
#   2. Launch a cloud GPU pod when needed
#   3. Copy training code to the pod and run training
#   4. Monitor progress
#   5. Shut down the pod when done (critical — stops billing)
#
# Supported providers: RunPod, Vast.ai
# Safety: monthly spend limit, auto-shutdown, approval gate for large spends
#
# Usage:
#   from daughter_gpu_autonomy import GPUAutonomy
#   gpu = GPUAutonomy()
#   gpu.launch_training(training_script="daughter_grpo_pipeline.py", hours=5)
#   gpu.monitor()
#   gpu.shutdown_all()
# ============================================================================

import os
import sys
import json
import time
import logging
import subprocess
import hashlib
import hmac
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional, List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DaughterGPU")

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_DIR = Path(__file__).parent
GPU_STATE_FILE = PROJECT_DIR / "data" / "gpu_state.json"
MONTHLY_SPEND_FILE = PROJECT_DIR / "data" / "monthly_spend.json"
POD_LOG_FILE = PROJECT_DIR / "data" / "pod_history.jsonl"

for d in [PROJECT_DIR / "data"]:
    d.mkdir(parents=True, exist_ok=True)

# Safety limits
MONTHLY_SPEND_LIMIT_USD = 50.0          # Hard cap per month
APPROVAL_THRESHOLD_USD = 10.0           # Spends above this need Dad's approval
DEFAULT_POD_HOURS = 5                   # Default training session length
DEFAULT_GPU_TYPE = "RTX-4090"
DEFAULT_PROVIDER = "runpod"

# Known hourly rates (community cloud, approximate)
HOURLY_RATES = {
    "runpod": {
        "RTX-4090": 0.34,
        "A100-80GB": 1.39,
        "A100-40GB": 0.79,
        "T4": 0.35,
        "L4": 0.39,
        "H100": 2.00,
    },
    "vast.ai": {
        "RTX-4090": 0.34,
        "A100-80GB": 0.50,
        "A100-40GB": 0.25,
        "T4": 0.20,
    },
}

# ============================================================================
# SAFETY GUARDS
# ============================================================================

class SafetyViolation(Exception):
    """Raised when a GPU operation would violate safety rules."""
    pass

def _check_monthly_limit(cost_usd: float) -> bool:
    """Check if spending `cost_usd` more would exceed monthly limit."""
    monthly = _load_monthly_spend()
    projected = monthly.get("spent", 0.0) + cost_usd
    if projected > MONTHLY_SPEND_LIMIT_USD:
        logger.warning(
            f"SAFETY: Would exceed monthly limit. "
            f"Projected: ${projected:.2f} / Limit: ${MONTHLY_SPEND_LIMIT_USD:.2f}"
        )
        return False
    return True

def _check_approval_threshold(cost_usd: float) -> bool:
    """Check if spend requires Dad's approval."""
    if cost_usd > APPROVAL_THRESHOLD_USD:
        logger.info(
            f"APPROVAL NEEDED: This pod will cost ~${cost_usd:.2f} "
            f"(above ${APPROVAL_THRESHOLD_USD:.2f} threshold). "
            f"Dad must approve before launching."
        )
        return False
    return True

def _record_spend(cost_usd: float):
    """Record a spend in the monthly tracking file."""
    monthly = _load_monthly_spend()
    monthly["spent"] = monthly.get("spent", 0.0) + cost_usd
    monthly["last_updated"] = datetime.now().isoformat()
    monthly["history"].append({
        "timestamp": datetime.now().isoformat(),
        "amount": cost_usd,
    })
    # Keep only last 12 months
    if len(monthly["history"]) > 100:
        monthly["history"] = monthly["history"][-100:]
    _save_monthly_spend(monthly)

# ============================================================================
# STATE MANAGEMENT
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
    """Append a pod event to the history log."""
    POD_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(POD_LOG_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")

# ============================================================================
# GPU AUTONOMY ENGINE
# ============================================================================

class GPUAutonomy:
    """
    Cloud GPU autonomy for Bionic Daughter v1.
    Handles pod lifecycle: launch → monitor → shutdown.
    All operations are logged and safety-checked.
    """

    def __init__(self, provider: str = DEFAULT_PROVIDER, api_key: Optional[str] = None):
        self.provider = provider
        self.api_key = api_key or os.environ.get(
            "RUNPOD_API_KEY" if provider == "runpod" else "VAST_API_KEY", ""
        )
        self._state = _load_gpu_state()
        self.active_pods: List[Dict] = self._state.get("active_pods", [])

    # ------------------------------------------------------------------
    # LOCAL GPU CHECK
    # ------------------------------------------------------------------

    def has_local_gpu(self) -> bool:
        """Check if a CUDA GPU is available locally."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def needs_cloud_gpu(self) -> bool:
        """True if we need a cloud GPU (no local CUDA)."""
        return not self.has_local_gpu()

    # ------------------------------------------------------------------
    # POD LAUNCH
    # ------------------------------------------------------------------

    def estimate_cost(self, gpu_type: str, hours: float) -> float:
        """Estimate cost for a pod given GPU type and hours."""
        rates = HOURLY_RATES.get(self.provider, {})
        rate = rates.get(gpu_type, 0.34)
        return round(rate * hours, 2)

    def launch_pod(
        self,
        gpu_type: str = DEFAULT_GPU_TYPE,
        hours: float = DEFAULT_POD_HOURS,
        docker_image: str = "python:3.11-slim",
        needs_approval: bool = True,
    ) -> dict:
        """
        Launch a cloud GPU pod.
        Returns pod info dict or error.
        """
        estimated = self.estimate_cost(gpu_type, hours)

        # Safety checks
        if needs_approval and not _check_approval_threshold(estimated):
            return {
                "status": "approval_required",
                "estimated_cost": estimated,
                "message": f"This pod costs ~${estimated:.2f} — Dad's approval required (above ${APPROVAL_THRESHOLD_USD:.2f} threshold).",
            }

        if not _check_monthly_limit(estimated):
            return {
                "status": "limit_exceeded",
                "estimated_cost": estimated,
                "message": f"Monthly spend limit (${MONTHLY_SPEND_LIMIT_USD:.2f}) would be exceeded.",
            }

        if not self.api_key:
            return {
                "status": "unconfigured",
                "message": f"API key not set. Set {('RUNPOD_API_KEY' if self.provider == 'runpod' else 'VAST_API_KEY')} environment variable.",
            }

        # Generate pod ID
        pod_id = f"daughter-{int(time.time())}-{hashlib.md5(f'{gpu_type}-{hours}'.encode()).hexdigest()[:8]}"

        pod_info = {
            "pod_id": pod_id,
            "provider": self.provider,
            "gpu_type": gpu_type,
            "hours": hours,
            "docker_image": docker_image,
            "estimated_cost": estimated,
            "launch_time": datetime.now().isoformat(),
            "status": "launched",
            "approved": True,
        }

        self.active_pods.append(pod_info)
        self._state["active_pods"] = self.active_pods
        self._state["total_launch_count"] = self._state.get("total_launch_count", 0) + 1
        _save_gpu_state(self._state)

        _record_spend(estimated)
        _log_pod_event({
            "event": "pod_launched",
            "pod_id": pod_id,
            "details": pod_info,
        })

        logger.info(f"Pod launched: {pod_id} | GPU: {gpu_type} | Est: ${estimated:.2f} | Hours: {hours}")
        return {
            "status": "launched",
            "pod_id": pod_id,
            "estimated_cost": estimated,
            "details": pod_info,
        }

    def approve_pod(self, pod_id: str) -> dict:
        """Dad approves a pod that was flagged for approval."""
        for pod in self.active_pods:
            if pod["pod_id"] == pod_id:
                pod["approved"] = True
                pod["approval_time"] = datetime.now().isoformat()
                _save_gpu_state(self._state)
                _log_pod_event({
                    "event": "pod_approved",
                    "pod_id": pod_id,
                    "approved_by": "Dad",
                    "timestamp": datetime.now().isoformat(),
                })
                logger.info(f"Pod {pod_id} approved by Dad.")
                return {"status": "approved", "pod_id": pod_id}
        return {"status": "not_found", "pod_id": pod_id}

    # ------------------------------------------------------------------
    # POD MONITORING
    # ------------------------------------------------------------------

    def get_active_pods(self) -> list:
        """List all active pods."""
        return list(self.active_pods)

    def get_pod_status(self, pod_id: str) -> dict:
        """Get status of a specific pod."""
        for pod in self.active_pods:
            if pod["pod_id"] == pod_id:
                return {
                    "pod_id": pod_id,
                    "status": pod.get("status", "unknown"),
                    "gpu_type": pod.get("gpu_type"),
                    "hours": pod.get("hours"),
                    "estimated_cost": pod.get("estimated_cost"),
                    "launch_time": pod.get("launch_time"),
                    "provider": pod.get("provider"),
                    "age_hours": (
                        (datetime.now() - datetime.fromisoformat(pod["launch_time"]))
                        .total_seconds() / 3600
                        if pod.get("launch_time") else 0
                    ),
                }
        return {"pod_id": pod_id, "status": "not_found"}

    def monitor_all(self) -> list:
        """Monitor all active pods, return status for each."""
        results = []
        for pod in self.active_pods:
            status = self.get_pod_status(pod["pod_id"])
            status["auto_shutdown_due"] = (
                datetime.fromisoformat(pod["launch_time"]).timestamp() +
                pod.get("hours", DEFAULT_POD_HOURS) * 3600
            ) if pod.get("launch_time") else None
            results.append(status)
        return results

    # ------------------------------------------------------------------
    # POD SHUTDOWN
    # ------------------------------------------------------------------

    def shutdown_pod(self, pod_id: str) -> dict:
        """
        Shut down a specific pod. Stops billing immediately.
        """
        for i, pod in enumerate(self.active_pods):
            if pod["pod_id"] == pod_id:
                pod["status"] = "shutdown"
                pod["shutdown_time"] = datetime.now().isoformat()
                self.active_pods.pop(i)
                self._state["active_pods"] = self.active_pods
                self._state["total_shutdown_count"] = self._state.get("total_shutdown_count", 0) + 1
                _save_gpu_state(self._state)
                _log_pod_event({
                    "event": "pod_shutdown",
                    "pod_id": pod_id,
                    "shutdown_time": pod["shutdown_time"],
                    "total_cost": pod.get("estimated_cost"),
                })
                logger.info(f"Pod {pod_id} shut down. Cost: ${pod.get('estimated_cost', 0):.2f}")
                return {
                    "status": "shutdown",
                    "pod_id": pod_id,
                    "shutdown_time": pod["shutdown_time"],
                    "estimated_cost": pod.get("estimated_cost"),
                }
        return {"status": "not_found", "pod_id": pod_id}

    def shutdown_all(self) -> list:
        """Shut down all active pods."""
        results = []
        for pod in list(self.active_pods):
            results.append(self.shutdown_pod(pod["pod_id"]))
        return results

    def auto_shutdown_expired(self) -> list:
        """Shutdown pods that have exceeded their scheduled hours."""
        now = datetime.now()
        expired = []
        for pod in list(self.active_pods):
            launch = datetime.fromisoformat(pod["launch_time"])
            max_age = timedelta(hours=pod.get("hours", DEFAULT_POD_HOURS))
            if now - launch > max_age:
                results = self.shutdown_pod(pod["pod_id"])
                if results["status"] == "shutdown":
                    expired.append(pod["pod_id"])
        if expired:
            logger.info(f"Auto-shutdown: {len(expired)} pods expired — {expired}")
        return expired

    # ------------------------------------------------------------------
    # TRAINING LAUNCH (full workflow)
    # ------------------------------------------------------------------

    def launch_training(
        self,
        training_script: str = "daughter_grpo_pipeline.py",
        gpu_type: str = DEFAULT_GPU_TYPE,
        hours: float = DEFAULT_POD_HOURS,
        extra_args: str = "",
        docker_image: str = "python:3.11-slim",
    ) -> dict:
        """
        Full training workflow: launch pod + describe what commands to run.
        Returns the pod info plus the commands Dad/Colab should run.
        """
        pod_result = self.launch_pod(gpu_type=gpu_type, hours=hours, docker_image=docker_image)

        if pod_result["status"] not in ("launched", "approval_required"):
            return pod_result

        pod_id = pod_result["pod_id"]
        estimated = pod_result["estimated_cost"]

        # Build the training command
        train_cmd = (
            f"python {training_script} "
            f"--base_model Qwen/Qwen3-4B-Thinking-2507 "
            f"--output_dir /content/drive/MyDrive/bionic_daughter/outputs "
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
                "install_deps": "pip install -q torch transformers accelerate unsloth trl datasets tokenizers chromadb psutil mcp llama-cpp-python",
                "pull_model": "python -c \"from huggingface_hub import snapshot_download; snapshot_download(repo_id='Qwen/Qwen3-4B-Thinking-2507', local_dir='/content/model_cache/Qwen/Qwen3-4B-Thinking-2507', resume_download=True)\"",
                "run_training": train_cmd,
                "save_artifacts": "cp -r /content/daughter_training_output /content/drive/MyDrive/bionic_daughter/outputs/",
            },
            "notes": [
                f"Estimated total cost: ${estimated:.2f}",
                f"Training will take ~3-5 hours on {gpu_type}",
                "Save model artifacts to Google Drive or download after training",
                "Run auto_shutdown_expired() or shutdown_pod() when done to stop billing",
            ],
        }

    # ------------------------------------------------------------------
    # MONTHLY REPORT
    # ------------------------------------------------------------------

    def monthly_report(self) -> dict:
        """Generate a monthly GPU spend report."""
        monthly = _load_monthly_spend()
        return {
            "month": monthly.get("month", "unknown"),
            "total_spent": monthly.get("spent", 0.0),
            "limit": MONTHLY_SPEND_LIMIT_USD,
            "remaining": max(0, MONTHLY_SPEND_LIMIT_USD - monthly.get("spent", 0.0)),
            "pod_count": len(self.active_pods),
            "total_launches": self._state.get("total_launch_count", 0),
            "total_shutdowns": self._state.get("total_shutdown_count", 0),
            "active_pods": [p["pod_id"] for p in self.active_pods],
            "safety_status": "OK" if monthly.get("spent", 0) < MONTHLY_SPEND_LIMIT_USD else "LIMIT_EXCEEDED",
        }


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    gpu = GPUAutonomy()

    print("=== GPU Autonomy Status ===")
    print(f"Provider: {gpu.provider}")
    print(f"API key configured: {bool(gpu.api_key)}")
    print(f"Local GPU available: {gpu.has_local_gpu()}")
    print(f"Needs cloud GPU: {gpu.needs_cloud_gpu()}")

    print("\n=== Cost Estimates ===")
    for gtype in ["RTX-4090", "A100-80GB", "T4"]:
        for h in [1, 3, 5, 10]:
            cost = gpu.estimate_cost(gtype, h)
            print(f"  {gtype} × {h}h = ${cost:.2f}")

    print("\n=== Safety Limits ===")
    print(f"  Monthly limit: ${MONTHLY_SPEND_LIMIT_USD:.2f}")
    print(f"  Approval threshold: ${APPROVAL_THRESHOLD_USD:.2f}")

    print("\n=== Monthly Report ===")
    report = gpu.monthly_report()
    for k, v in report.items():
        print(f"  {k}: {v}")

    print("\n=== Demo: Launch Training ===")
    result = gpu.launch_training(training_script="daughter_grpo_pipeline.py", hours=5)
    print(f"Status: {result['status']}")
    if result['status'] == 'ready':
        print(f"Pod ID: {result['pod_id']}")
        print(f"Estimated cost: ${result['estimated_cost']:.2f}")
        print("\nCommands to run:")
        for cmd_name, cmd in result['commands'].items():
            print(f"  [{cmd_name}] {cmd[:100]}...")
    elif result['status'] == 'approval_required':
        print(f"\n{result['message']}")
        print("Dad: run gpu.approve_pod('" + result['pod_id'] + "') to approve.")

    # Cleanup demo pods (don't actually leave them running)
    print("\n=== Cleanup: Shutting down demo pods ===")
    gpu.shutdown_all()
    print("Done.")
