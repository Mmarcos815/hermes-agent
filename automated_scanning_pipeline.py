#!/usr/bin/env python3
import json, os, subprocess
from pathlib import Path
from datetime import datetime

class ScanningPipeline:
    def __init__(self, target, output_dir="scan_results"):
        self.target = target
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = {"target": target, "start": datetime.utcnow().isoformat()+"Z", "phases": []}
    
    def phase1_recon(self):
        findings = []
        try:
            r = subprocess.run(["whois", self.target], capture_output=True, text=True, timeout=30)
            findings.append({"tool": "whois", "output": r.stdout[:1000]})
        except: pass
        try:
            r = subprocess.run(["nmap", "-sV", "-sC", self.target], capture_output=True, text=True, timeout=120)
            findings.append({"tool": "nmap", "output": r.stdout[:2000]})
        except: pass
        self.results["phases"].append({"phase": "recon", "findings": findings})
        return findings
    
    def phase2_vuln_scan(self):
        findings = []
        try:
            r = subprocess.run(["nuclei", "-u", self.target, "-json"], capture_output=True, text=True, timeout=120)
            findings.append({"tool": "nuclei", "output": r.stdout[:2000]})
        except: pass
        self.results["phases"].append({"phase": "vuln_scan", "findings": findings})
        return findings
    
    def phase3_correlation(self):
        correlated = []
        for phase in self.results["phases"]:
            for finding in phase.get("findings", []):
                output = finding.get("output", "")
                if "vulnerable" in output.lower() or "cve" in output.lower():
                    correlated.append({"source": finding["tool"], "finding": output[:500]})
        self.results["phases"].append({"phase": "correlation", "findings": correlated})
        return correlated
    
    def phase4_report(self):
        report_path = self.output_dir / f"scan_report_{self.target}.json"
        report_path.write_text(json.dumps(self.results, indent=2))
        return str(report_path)
    
    def run(self):
        self.phase1_recon()
        self.phase2_vuln_scan()
        self.phase3_correlation()
        report = self.phase4_report()
        self.results["end"] = datetime.utcnow().isoformat()+"Z"
        return self.results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("target")
    parser.add_argument("--output", default="scan_results")
    args = parser.parse_args()
    pipeline = ScanningPipeline(args.target, args.output)
    results = pipeline.run()
    print(json.dumps({"status": "complete", "phases": len(results["phases"]), "report": f"scan_results/scan_report_{args.target}.json"}, indent=2))
