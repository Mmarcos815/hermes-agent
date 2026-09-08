#!/usr/bin/env python3
import json, os, re
from pathlib import Path
from datetime import datetime

class SecurityKnowledgeBase:
    def __init__(self, db_path="knowledge/security_kb.json"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.data = {"findings": [], "ttps": [], "lessons": [], "tools": []}
        if self.db_path.exists():
            self.data = json.loads(self.db_path.read_text())
    
    def add_finding(self, title, domain, severity, description, ttp_ids=None):
        finding = {
            "id": f"FIND-{len(self.data['findings'])+1:04d}",
            "title": title,
            "domain": domain,
            "severity": severity,
            "description": description,
            "ttp_ids": ttp_ids or [],
            "date": datetime.utcnow().isoformat()+"Z",
        }
        self.data["findings"].append(finding)
        self._save()
        return finding
    
    def add_ttp(self, technique_id, name, tactic, description):
        ttp = {
            "technique_id": technique_id,
            "name": name,
            "tactic": tactic,
            "description": description,
        }
        self.data["ttps"].append(ttp)
        self._save()
        return ttp
    
    def search(self, query):
        results = []
        query_lower = query.lower()
        for finding in self.data["findings"]:
            if query_lower in finding["title"].lower() or query_lower in finding["description"].lower():
                results.append(finding)
        for ttp in self.data["ttps"]:
            if query_lower in ttp["name"].lower() or query_lower in ttp["description"].lower():
                results.append(ttp)
        return results
    
    def get_by_severity(self, severity):
        return [f for f in self.data["findings"] if f["severity"] == severity]
    
    def get_by_tactic(self, tactic):
        return [t for t in self.data["ttps"] if t["tactic"] == tactic]
    
    def export_json(self, output="knowledge/kb_export.json"):
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(json.dumps(self.data, indent=2))
        return output
    
    def _save(self):
        self.db_path.write_text(json.dumps(self.data, indent=2))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("add-finding")
    p.add_argument("title")
    p.add_argument("domain")
    p.add_argument("severity")
    p.add_argument("description")
    p = sub.add_parser("search")
    p.add_argument("query")
    p = sub.add_parser("export")
    args = parser.parse_args()
    kb = SecurityKnowledgeBase()
    if args.cmd == "add-finding":
        print(json.dumps(kb.add_finding(args.title, args.domain, args.severity, args.description), indent=2))
    elif args.cmd == "search":
        print(json.dumps(kb.search(args.query), indent=2))
    elif args.cmd == "export":
        print(kb.export_json())
