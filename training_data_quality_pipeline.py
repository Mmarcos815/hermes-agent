#!/usr/bin/env python3
import json, hashlib, re
from pathlib import Path

class TrainingDataQualityPipeline:
    def __init__(self, input_path="grpo_train_clean.jsonl"):
        self.input_path = Path(input_path)
        self.issues = []
        self.stats = {"total": 0, "valid": 0, "invalid": 0, "duplicates": 0}
    
    def validate(self):
        """Run all validation checks."""
        records = []
        seen_hashes = set()
        
        with open(self.input_path, encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                self.stats["total"] += 1
                line = line.strip()
                if not line:
                    self.issues.append(f"Line {i}: empty")
                    self.stats["invalid"] += 1
                    continue
                
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    self.issues.append(f"Line {i}: invalid JSON")
                    self.stats["invalid"] += 1
                    continue
                
                # Check required fields
                if not rec.get("prompt", "").strip():
                    self.issues.append(f"Line {i}: empty prompt")
                    self.stats["invalid"] += 1
                    continue
                if not rec.get("completion", "").strip():
                    self.issues.append(f"Line {i}: empty completion")
                    self.stats["invalid"] += 1
                    continue
                
                # Check for duplicates
                h = hashlib.md5(rec["prompt"].encode()).hexdigest()
                if h in seen_hashes:
                    self.stats["duplicates"] += 1
                    continue
                seen_hashes.add(h)
                
                # Check encoding
                try:
                    rec["prompt"].encode("utf-8")
                    rec["completion"].encode("utf-8")
                except UnicodeError:
                    self.issues.append(f"Line {i}: encoding error")
                    self.stats["invalid"] += 1
                    continue
                
                self.stats["valid"] += 1
                records.append(rec)
        
        return records
    
    def generate_report(self):
        """Generate quality report."""
        report = {
            "stats": self.stats,
            "issues": self.issues[:50],
            "pass_rate": round(self.stats["valid"] / max(self.stats["total"], 1) * 100, 1),
            "unique_prompts": self.stats["valid"] - self.stats["duplicates"],
        }
        return report

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="grpo_train_clean.jsonl")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    
    pipeline = TrainingDataQualityPipeline(args.input)
    records = pipeline.validate()
    report = pipeline.generate_report()
    print(json.dumps(report, indent=2))
