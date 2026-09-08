#!/usr/bin/env python3
import json, subprocess
from pathlib import Path
from datetime import datetime

class AttackSurfaceManager:
    def __init__(self, output_dir="asm_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def discover_subdomains(self, domain):
        try:
            r = subprocess.run(["subfinder", "-d", domain, "-silent"], capture_output=True, text=True, timeout=60)
            return r.stdout.strip().split("\n")
        except:
            return []
    
    def check_ports(self, target):
        try:
            r = subprocess.run(["nmap", "-p1-1000", target], capture_output=True, text=True, timeout=60)
            return r.stdout[:1000]
        except:
            return ""
    
    def scan(self, domains):
        results = {}
        for domain in domains:
            results[domain] = {
                "subdomains": self.discover_subdomains(domain),
                "ports": self.check_ports(domain),
                "date": datetime.utcnow().isoformat()+"Z",
            }
        return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--domains", nargs="+", required=True)
    args = parser.parse_args()
    manager = AttackSurfaceManager()
    results = manager.scan(args.domains)
    print(json.dumps(results, indent=2))
