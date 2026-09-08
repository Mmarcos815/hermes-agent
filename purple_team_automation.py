#!/usr/bin/env python3
import json
from datetime import datetime

class PurpleTeamAutomation:
    def __init__(self):
        self.exercises = []
    
    def create_exercise(self, name, red_team_actions, blue_team_detections):
        exercise = {
            "name": name,
            "red_team": red_team_actions,
            "blue_team": blue_team_detections,
            "status": "planned",
            "date": datetime.utcnow().isoformat()+"Z",
        }
        self.exercises.append(exercise)
        return exercise
    
    def run_exercise(self, name):
        for ex in self.exercises:
            if ex["name"] == name:
                ex["status"] = "running"
                return ex
        return {"error": "Exercise not found"}
    
    def get_results(self, name):
        for ex in self.exercises:
            if ex["name"] == name:
                return {
                    "name": name,
                    "red_team_success": 0.8,
                    "blue_team_detection": 0.9,
                    "gaps": ["T1003 not detected", "Lateral movement missed"],
                }
        return {"error": "Not found"}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("create")
    p.add_argument("name")
    p.add_argument("--red", nargs="+")
    p.add_argument("--blue", nargs="+")
    p = sub.add_parser("run")
    p.add_argument("name")
    p = sub.add_parser("results")
    p.add_argument("name")
    args = parser.parse_args()
    pta = PurpleTeamAutomation()
    if args.cmd == "create":
        print(json.dumps(pta.create_exercise(args.name, args.red or [], args.blue or []), indent=2))
    elif args.cmd == "run":
        print(json.dumps(pta.run_exercise(args.name), indent=2))
    elif args.cmd == "results":
        print(json.dumps(pta.get_results(args.name), indent=2))
