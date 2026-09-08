#!/usr/bin/env python3
import json, os, time, subprocess
from datetime import datetime
from pathlib import Path

class ContinuousTrainingPipeline:
    def __init__(self, config_path="training/pipeline_config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self):
        if self.config_path.exists():
            return json.loads(self.config_path.read_text())
        return {
            "data_dir": "training/data",
            "output_dir": "training/output",
            "schedule": "weekly",
            "min_new_examples": 100,
            "auto_train": False,
            "notify_on_complete": True
        }
    
    def watch_for_new_data(self):
        """Watch for new JSONL files in data directory."""
        data_dir = Path(self.config["data_dir"])
        if not data_dir.exists():
            return []
        new_files = []
        for f in data_dir.glob("*.jsonl"):
            if f.name not in self.config.get("processed_files", []):
                new_files.append(f)
        return new_files
    
    def validate_new_data(self, filepath):
        """Validate new training data."""
        issues = []
        valid = 0
        invalid = 0
        with open(filepath) as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if not rec.get("prompt", "").strip():
                        issues.append(f"Line {i}: empty prompt")
                        invalid += 1
                    elif not rec.get("completion", "").strip():
                        issues.append(f"Line {i}: empty completion")
                        invalid += 1
                    else:
                        valid += 1
                except json.JSONDecodeError:
                    issues.append(f"Line {i}: invalid JSON")
                    invalid += 1
        return {"valid": valid, "invalid": invalid, "issues": issues}
    
    def merge_datasets(self, new_files, output_path="training/merged_data.jsonl"):
        """Merge new files with existing dataset."""
        all_records = []
        # Load existing
        if Path(output_path).exists():
            with open(output_path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            all_records.append(json.loads(line))
                        except:
                            pass
        # Add new
        for f in new_files:
            with open(f) as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        try:
                            all_records.append(json.loads(line))
                        except:
                            pass
        # Deduplicate by prompt hash
        seen = set()
        unique = []
        for rec in all_records:
            h = hashlib.md5(rec.get("prompt", "").encode()).hexdigest()
            if h not in seen:
                seen.add(h)
                unique.append(rec)
        # Write
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            for rec in unique:
                f.write(json.dumps(rec, ensure_ascii=False) + "
")
        return len(unique)
    
    def trigger_training(self, data_path, output_dir="training/output"):
        """Trigger training run."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        cmd = [
            "python3", "colab_train.py",
            "--data", data_path,
            "--output", output_dir,
            "--steps", str(self.config.get("steps", 400))
        ]
        # In production, this would run the training
        # For now, just log the command
        print(f"Would run: {' '.join(cmd)}")
        return {"status": "triggered", "command": " ".join(cmd)}
    
    def run(self):
        """Main pipeline loop."""
        print(f"Pipeline started at {datetime.utcnow().isoformat()}Z")
        
        # Check for new data
        new_files = self.watch_for_new_data()
        if not new_files:
            print("No new data found.")
            return
        
        print(f"Found {len(new_files)} new file(s)")
        
        # Validate
        for f in new_files:
            result = self.validate_new_data(f)
            print(f"  {f.name}: {result['valid']} valid, {result['invalid']} invalid")
            if result["issues"][:5]:
                for issue in result["issues"][:5]:
                    print(f"    - {issue}")
        
        # Merge
        total = self.merge_datasets(new_files)
        print(f"Merged dataset: {total} unique examples")
        
        # Train if auto_train enabled
        if self.config.get("auto_train"):
            self.trigger_training("training/merged_data.jsonl")
        
        # Update config
        self.config.setdefault("processed_files", []).extend([f.name for f in new_files])
        self.config_path.write_text(json.dumps(self.config, indent=2))
        print("Pipeline complete.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true", help="Watch for new data")
    parser.add_argument("--validate", help="Validate a file")
    parser.add_argument("--merge", nargs="+", help="Merge files")
    parser.add_argument("--run", action="store_true", help="Run full pipeline")
    args = parser.parse_args()
    
    pipeline = ContinuousTrainingPipeline()
    if args.watch:
        files = pipeline.watch_for_new_data()
        print(f"New files: {[f.name for f in files]}")
    elif args.validate:
        result = pipeline.validate_new_data(args.validate)
        print(json.dumps(result, indent=2))
    elif args.merge:
        total = pipeline.merge_datasets([Path(f) for f in args.merge])
        print(f"Merged: {total} examples")
    elif args.run:
        pipeline.run()
