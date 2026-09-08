#!/usr/bin/env python3
import json, csv, os
from datetime import datetime
from pathlib import Path

class ModelPerformanceTracker:
    def __init__(self, db_path="artifacts/model_performance.json"):
        self.db_path = Path(db_path)
        self.data = {"versions": [], "evaluations": []}
        if self.db_path.exists():
            self.data = json.loads(self.db_path.read_text())
    
    def add_version(self, name, path, notes=""):
        version = {"name": name, "path": path, "notes": notes, "added": datetime.utcnow().isoformat()+"Z"}
        self.data["versions"].append(version)
        self._save()
        return version
    
    def add_evaluation(self, version_name, metrics, notes=""):
        eval = {"version": version_name, "metrics": metrics, "notes": notes, "date": datetime.utcnow().isoformat()+"Z"}
        self.data["evaluations"].append(eval)
        self._save()
        return eval
    
    def compare(self, v1, v2):
        e1 = [e for e in self.data["evaluations"] if e["version"] == v1]
        e2 = [e for e in self.data["evaluations"] if e["version"] == v2]
        if not e1 or not e2:
            return None
        m1 = e1[-1]["metrics"]
        m2 = e2[-1]["metrics"]
        diff = {}
        for k in set(list(m1.keys()) + list(m2.keys())):
            diff[k] = {"v1": m1.get(k), "v2": m2.get(k), "delta": round(m2.get(k,0) - m1.get(k,0), 3) if isinstance(m2.get(k), (int,float)) and isinstance(m1.get(k), (int,float)) else None}
        return diff
    
    def export_csv(self, output="artifacts/performance_export.csv"):
        evals = self.data["evaluations"]
        if not evals:
            return
        keys = set()
        for e in evals:
            keys.update(e["metrics"].keys())
        with open(output, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["version", "date"] + sorted(keys))
            for e in evals:
                row = [e["version"], e["date"]]
                for k in sorted(keys):
                    row.append(e["metrics"].get(k, ""))
                writer.writerow(row)
        return output
    
    def _save(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path.write_text(json.dumps(self.data, indent=2))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("add-version")
    p.add_argument("name")
    p.add_argument("path")
    p.add_argument("--notes", default="")
    p = sub.add_parser("add-eval")
    p.add_argument("version")
    p.add_argument("--metrics", type=json.loads, default="{}")
    p.add_argument("--notes", default="")
    p = sub.add_parser("compare")
    p.add_argument("v1")
    p.add_argument("v2")
    p = sub.add_parser("export")
    p.add_argument("--output", default="artifacts/performance_export.csv")
    args = parser.parse_args()
    t = ModelPerformanceTracker()
    if args.cmd == "add-version":
        print(json.dumps(t.add_version(args.name, args.path, args.notes), indent=2))
    elif args.cmd == "add-eval":
        print(json.dumps(t.add_evaluation(args.version, args.metrics, args.notes), indent=2))
    elif args.cmd == "compare":
        print(json.dumps(t.compare(args.v1, args.v2), indent=2))
    elif args.cmd == "export":
        out = t.export_csv(args.output)
        print(f"Exported: {out}")
