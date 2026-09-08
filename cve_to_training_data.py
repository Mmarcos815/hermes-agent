#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

class CVEtoTrainingData:
    def __init__(self, output_path="training/cve_examples.jsonl"):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
    
    def convert(self, cve_id, description, severity):
        examples = [
            {
                "prompt": f"Explain the exploitation of {cve_id}: {description}",
                "completion": f"<reasoning>{cve_id} is a {severity} vulnerability. {description} The attack involves understanding the root cause, identifying affected systems, and developing a proof-of-concept.</reasoning><solution>**Finding:** {cve_id}\n**Severity:** {severity}\n**Remediation:** Apply vendor patch</solution>",
                "metadata": {"domain": "Vulnerability Analysis", "cve": cve_id, "severity": severity, "generated": True, "timestamp": datetime.utcnow().isoformat()+"Z"}
            },
            {
                "prompt": f"Walk through the attack chain for {cve_id}",
                "completion": f"<reasoning>The attack chain for {cve_id} begins with initial access via the vulnerability, followed by escalation and lateral movement.</reasoning><solution>**Attack Chain:** Initial Access → Escalation → Lateral Movement → Objective</solution>",
                "metadata": {"domain": "Attack Chains", "cve": cve_id, "generated": True, "timestamp": datetime.utcnow().isoformat()+"Z"}
            },
        ]
        with open(self.output_path, "a") as f:
            for ex in examples:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")
        return examples
    
    def bulk_convert(self, cves):
        all_examples = []
        for cve in cves:
            all_examples.extend(self.convert(cve["id"], cve["description"], cve["severity"]))
        return all_examples

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--cve", help="CVE ID")
    parser.add_argument("--description", default="")
    parser.add_argument("--severity", default="high")
    args = parser.parse_args()
    converter = CVEtoTrainingData()
    examples = converter.convert(args.cve, args.description, args.severity)
    print(json.dumps({"converted": len(examples), "output": str(converter.output_path)}, indent=2))
