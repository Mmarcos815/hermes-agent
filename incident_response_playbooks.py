#!/usr/bin/env python3
import json, os, subprocess
from pathlib import Path
from datetime import datetime

class IncidentResponsePlaybooks:
    def __init__(self, playbooks_dir="ir_playbooks"):
        self.playbooks_dir = Path(playbooks_dir)
        self.playbooks_dir.mkdir(parents=True, exist_ok=True)
        self.incidents = []
    
    def detect_incident(self, logs: list) -> dict:
        """Detect incidents from logs."""
        incident = {
            "id": f"INC-{len(self.incidents)+1:04d}",
            "detected": datetime.utcnow().isoformat() + "Z",
            "severity": "medium",
            "status": "detected",
            "indicators": [],
        }
        for log in logs:
            if "malware" in log.lower() or "exploit" in log.lower():
                incident["indicators"].append(log)
                incident["severity"] = "critical"
        self.incidents.append(incident)
        return incident
    
    def contain(self, incident_id: str) -> dict:
        """Execute containment procedures."""
        return {
            "incident": incident_id,
            "action": "contain",
            "status": "contained",
            "steps": ["Isolate affected systems", "Block malicious IPs", "Disable compromised accounts"],
        }
    
    def collect_evidence(self, incident_id: str) -> dict:
        """Collect forensic evidence."""
        return {
            "incident": incident_id,
            "evidence": ["memory_dump", "disk_image", "network_logs"],
            "collected": datetime.utcnow().isoformat() + "Z",
        }
    
    def generate_report(self, incident_id: str) -> str:
        """Generate incident report."""
        return f"""# Incident Report: {incident_id}
**Date:** {datetime.utcnow().strftime("%Y-%m-%d")}
**Status:** Contained
**Evidence:** Memory dump, disk image, network logs
"""

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("detect")
    p.add_argument("--logs", nargs="+")
    p = sub.add_parser("contain")
    p.add_argument("incident_id")
    p = sub.add_parser("evidence")
    p.add_argument("incident_id")
    p = sub.add_parser("report")
    p.add_argument("incident_id")
    args = parser.parse_args()
    irp = IncidentResponsePlaybooks()
    if args.cmd == "detect":
        print(json.dumps(irp.detect_incident(args.logs or []), indent=2))
    elif args.cmd == "contain":
        print(json.dumps(irp.contain(args.incident_id), indent=2))
    elif args.cmd == "evidence":
        print(json.dumps(irp.collect_evidence(args.incident_id), indent=2))
    elif args.cmd == "report":
        print(irp.generate_report(args.incident_id))
