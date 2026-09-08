#!/usr/bin/env python3
import json, os, re
from pathlib import Path
from datetime import datetime

class BountyTargetFinder:
    def __init__(self, db_path="intelligence/bounty_targets.json"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.data = {"targets": [], "programs": []}
        if self.db_path.exists():
            self.data = json.loads(self.db_path.read_text())
    
    def add_program(self, name, platform, url, scope, min_bounty, max_bounty):
        program = {
            "name": name,
            "platform": platform,
            "url": url,
            "scope": scope,
            "min_bounty": min_bounty,
            "max_bounty": max_bounty,
            "added": datetime.utcnow().isoformat()+"Z",
        }
        self.data["programs"].append(program)
        self._save()
        return program
    
    def find_matching(self, skills):
        """Find programs matching our skills."""
        matches = []
        for program in self.data["programs"]:
            for skill in skills:
                if skill.lower() in program.get("scope", "").lower():
                    matches.append(program)
                    break
        return matches
    
    def get_top_paying(self, limit=10):
        """Get top paying programs."""
        programs = sorted(self.data["programs"], key=lambda x: x.get("max_bounty", 0), reverse=True)
        return programs[:limit]
    
    def export_json(self, output="intelligence/bounty_targets_export.json"):
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(json.dumps(self.data, indent=2))
        return output
    
    def _save(self):
        self.db_path.write_text(json.dumps(self.data, indent=2))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("add-program")
    p.add_argument("name")
    p.add_argument("platform")
    p.add_argument("url")
    p.add_argument("scope")
    p.add_argument("min_bounty", type=int)
    p.add_argument("max_bounty", type=int)
    p = sub.add_parser("match")
    p.add_argument("skills", nargs="+")
    p = sub.add_parser("top")
    args = parser.parse_args()
    finder = BountyTargetFinder()
    if args.cmd == "add-program":
        print(json.dumps(finder.add_program(args.name, args.platform, args.url, args.scope, args.min_bounty, args.max_bounty), indent=2))
    elif args.cmd == "match":
        print(json.dumps(finder.find_matching(args.skills), indent=2))
    elif args.cmd == "top":
        print(json.dumps(finder.get_top_paying(), indent=2))
