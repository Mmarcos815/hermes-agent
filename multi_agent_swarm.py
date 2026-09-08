#!/usr/bin/env python3
import json, time, threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

class Agent:
    def __init__(self, name: str, capabilities: List[str]):
        self.name = name
        self.capabilities = capabilities
        self.status = "idle"
        self.results = []
    
    def execute(self, task: dict) -> dict:
        self.status = "working"
        result = {
            "agent": self.name,
            "task": task["type"],
            "status": "completed",
            "output": f"{self.name} completed {task['type']}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        self.results.append(result)
        self.status = "idle"
        return result

class MultiAgentSwarm:
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.tasks = []
        self.results = []
    
    def register_agent(self, name: str, capabilities: List[str]):
        self.agents[name] = Agent(name, capabilities)
    
    def assign_task(self, task: dict) -> Optional[str]:
        task_type = task.get("type", "")
        for name, agent in self.agents.items():
            if agent.status == "idle" and task_type in agent.capabilities:
                return name
        return None
    
    def run_task(self, task: dict) -> dict:
        agent_name = self.assign_task(task)
        if not agent_name:
            return {"error": "No available agent", "task": task}
        return self.agents[agent_name].execute(task)
    
    def run_swarm(self, tasks: List[dict]) -> List[dict]:
        results = []
        for task in tasks:
            result = self.run_task(task)
            results.append(result)
        self.results.extend(results)
        return results
    
    def get_status(self) -> dict:
        return {
            "agents": {name: {"status": a.status, "capabilities": a.capabilities} for name, a in self.agents.items()},
            "total_tasks": len(self.tasks),
            "completed": len([r for r in self.results if r.get("status") == "completed"]),
        }
    
    def export_results(self, path: str):
        Path(path).write_text(json.dumps(self.results, indent=2))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--tasks", help="Tasks JSON file")
    args = parser.parse_args()
    swarm = MultiAgentSwarm()
    swarm.register_agent("recon", ["recon", "osint", "scan"])
    swarm.register_agent("exploit", ["exploit", "attack", "pivot"])
    swarm.register_agent("report", ["report", "write", "summarize"])
    if args.demo:
        tasks = [
            {"type": "recon", "target": "example.com"},
            {"type": "scan", "target": "example.com"},
            {"type": "exploit", "target": "example.com"},
            {"type": "report", "target": "example.com"},
        ]
        results = swarm.run_swarm(tasks)
        print(json.dumps(swarm.get_status(), indent=2))
    elif args.tasks:
        tasks = json.loads(Path(args.tasks).read_text())
        swarm.run_swarm(tasks)
        swarm.export_results("swarm_results.json")
        print("Results: swarm_results.json")
