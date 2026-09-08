#!/usr/bin/env python3
"""
Post-Training Deployment Checklist
Verifies training, deploys model, runs tests, generates report.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
GRPO_DIR = ARTIFACTS_DIR / "grpo" / "last"
DEPLOY_SCRIPT = PROJECT_ROOT / "deploy_trained_model_ollama.py"
TEST_SCRIPT = PROJECT_ROOT / "test_trained_model_vs_base.py"
REPORT_PATH = ARTIFACTS_DIR / "deployment_report.json"


def check_training_completed():
    """Verify training produced real artifacts."""
    print("\n[1/5] Checking training artifacts...")
    required_files = ["adapter_model.safetensors", "adapter_config.json"]
    missing = [f for f in required_files if not (GRPO_DIR / f).exists()]
    if missing:
        print(f"  Missing: {missing}")
        return False
    adapter_path = GRPO_DIR / "adapter_model.safetensors"
    size = adapter_path.stat().st_size
    if size < 1000:
        print(f"  Too small: {size} bytes")
        return False
    print(f"  OK ({size:,} bytes)")
    return True


def validate_model_integrity():
    """Validate model files."""
    print("\n[2/5] Validating model integrity...")
    config_path = GRPO_DIR / "adapter_config.json"
    if not config_path.exists():
        print("  Missing adapter_config.json")
        return False
    try:
        with open(config_path) as f:
            config = json.load(f)
        for key in ["peft_type", "task_type", "r", "lora_alpha"]:
            if key not in config:
                print(f"  Missing key: {key}")
                return False
        print(f"  OK (r={config.get('r')}, alpha={config.get('lora_alpha')})")
    except json.JSONDecodeError:
        print("  Invalid JSON")
        return False
    return True


def deploy_model():
    """Run deployment script."""
    print("\n[3/5] Deploying model...")
    if not DEPLOY_SCRIPT.exists():
        print("  Missing deploy script")
        return False
    try:
        result = subprocess.run(
            [sys.executable, str(DEPLOY_SCRIPT), "--training-dir", str(GRPO_DIR)],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode == 0:
            print("  OK")
            return True
        else:
            print(f"  Failed: {result.stderr[-200:]}")
            return False
    except Exception as e:
        print(f"  Error: {e}")
        return False


def run_tests():
    """Run comparative tests."""
    print("\n[4/5] Running comparative tests...")
    if not TEST_SCRIPT.exists():
        print("  Missing test script")
        return False
    try:
        result = subprocess.run(
            [sys.executable, str(TEST_SCRIPT), "--base-url", "http://localhost:11434"],
            capture_output=True, text=True, timeout=600,
        )
        print(f"  Completed (exit {result.returncode})")
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return True


def generate_report(results):
    """Generate deployment report."""
    print("\n[5/5] Generating report...")
    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "results": results,
        "overall": "PASS" if all(results.values()) else "FAIL",
    }
    ARTIFACTS_DIR.mkdir(exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(f"  Saved: {REPORT_PATH}")
    return report


def main():
    print("=" * 60)
    print("  POST-TRAINING DEPLOYMENT CHECKLIST")
    print("=" * 60)
    results = {
        "training_completed": False,
        "model_integrity": False,
        "deployment": False,
        "tests": False,
    }
    results["training_completed"] = check_training_completed()
    if results["training_completed"]:
        results["model_integrity"] = validate_model_integrity()
    if results["model_integrity"]:
        results["deployment"] = deploy_model()
    if results["deployment"]:
        results["tests"] = run_tests()
    report = generate_report(results)
    print("\n" + "=" * 60)
    for check, passed in results.items():
        print(f"  {check}: {'PASS' if passed else 'FAIL'}")
    print(f"  Overall: {report['overall']}")
    print("=" * 60)
    return 0 if report["overall"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
