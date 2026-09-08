#!/usr/bin/env python3
import json, os
from pathlib import Path
from datetime import datetime

class OperationDashboard:
    def __init__(self, artifacts_dir="artifacts"):
        self.artifacts_dir = Path(artifacts_dir)
    
    def get_training_status(self):
        grpo_dir = self.artifacts_dir / "grpo" / "last"
        if not grpo_dir.exists():
            return {"status": "not_started"}
        config = grpo_dir / "config.json"
        if config.exists():
            return {"status": "completed", "config": json.loads(config.read_text())}
        return {"status": "in_progress"}
    
    def get_scan_results(self):
        scan_dir = Path("scan_results")
        if not scan_dir.exists():
            return []
        return [f.name for f in scan_dir.glob("*.json")]
    
    def get_model_versions(self):
        perf_file = self.artifacts_dir / "model_performance.json"
        if perf_file.exists():
            data = json.loads(perf_file.read_text())
            return data.get("versions", [])
        return []
    
    def generate_dashboard(self):
        return {
            "timestamp": datetime.utcnow().isoformat()+"Z",
            "training": self.get_training_status(),
            "scans": self.get_scan_results(),
            "models": self.get_model_versions(),
        }

if __name__ == "__main__":
    dashboard = OperationDashboard()
    print(json.dumps(dashboard.generate_dashboard(), indent=2))
