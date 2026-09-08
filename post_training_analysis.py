#!/usr/bin/env python3
import json, os, re
from datetime import datetime
from pathlib import Path

class PostTrainingAnalysis:
    def __init__(self, artifacts_dir="artifacts"):
        self.artifacts_dir = Path(artifacts_dir)
        self.findings = []
    
    def analyze_training_logs(self):
        """Parse training logs for issues."""
        logs_dir = self.artifacts_dir / "logs"
        if not logs_dir.exists():
            return {"error": "No logs directory"}
        
        log_files = list(logs_dir.glob("*.log"))
        analysis = {"log_files": len(log_files), "issues": []}
        
        for log_file in log_files:
            content = log_file.read_text()
            # Check for common issues
            if "error" in content.lower():
                analysis["issues"].append(f"{log_file.name}: contains errors")
            if "warning" in content.lower():
                analysis["issues"].append(f"{log_file.name}: contains warnings")
            if "nan" in content.lower():
                analysis["issues"].append(f"{log_file.name}: contains NaN values")
        
        return analysis
    
    def analyze_reward_curves(self):
        """Extract reward data from training."""
        grpo_dir = self.artifacts_dir / "grpo" / "last"
        if not grpo_dir.exists():
            return {"error": "No GRPO artifacts"}
        
        config_file = grpo_dir / "config.json"
        if not config_file.exists():
            return {"error": "No config.json"}
        
        config = json.loads(config_file.read_text())
        return {
            "group_size": config.get("group_size"),
            "beta_kl": config.get("beta_kl"),
            "max_steps": config.get("max_steps"),
            "reward_weights": config.get("reward_weights", {}),
        }
    
    def generate_report(self):
        """Generate comprehensive training analysis report."""
        report = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "log_analysis": self.analyze_training_logs(),
            "reward_config": self.analyze_reward_curves(),
            "issues": self.findings,
        }
        return report

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", default="artifacts")
    args = parser.parse_args()
    
    analyzer = PostTrainingAnalysis(args.artifacts)
    report = analyzer.generate_report()
    print(json.dumps(report, indent=2))
