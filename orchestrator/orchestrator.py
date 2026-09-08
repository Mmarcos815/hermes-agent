#!/usr/bin/env python3
"""
Multi-Agent Orchestrator
========================
Coordinates Recon, Exploit, Code, and Report agents via an internal message
queue. Each agent runs with its own bionic model, publishes results, and the
orchestrator consolidates the final report.

Usage:
    python orchestrator.py --target <ip|domain>
    python orchestrator.py --dry-run
    python orchestrator.py --list-models
"""

import argparse, json, queue, threading, time
from dataclasses import dataclass, field, asdict
from typing import Any

# Agent -> Bionic model assignment
AGENT_MODELS: dict[str, str] = {
    "recon":  "meituan/longcat-2.0:free",
    "exploit": "meituan/longcat-2.0:free",
    "code":   "meituan/longcat-2.0:free",
    "report": "meituan/longcat-2.0:free",
}

@dataclass
class AgentMessage:
    sender: str; receiver: str; msg_type: str
    payload: Any = None
    timestamp: float = field(default_factory=time.time)

@dataclass
class AgentResult:
    agent: str; model: str; status: str
    output: Any = None
    elapsed_sec: float = 0.0
    error: str | None = None

class BaseAgent(threading.Thread):
    """Abstract base handling queue I/O and lifecycle."""
    def __init__(self, name: str, model: str, task_q: queue.Queue, result_q: queue.Queue, target: str):
        super().__init__(name=name, daemon=True)
        self.agent_name, self.model, self.task_q, self.result_q, self.target = name, model, task_q, result_q, target
        self.result = AgentResult(agent=name, model=model, status="pending")

    def run(self) -> None:
        self.result.status = "running"
        start = time.time()
        try:
            self.result.output = self.execute()
            self.result.status = "completed"
        except Exception as exc:
            self.result.status, self.result.error = "error", str(exc)
        finally:
            self.result.elapsed_sec = round(time.time() - start, 3)
            self.result_q.put(AgentMessage(self.agent_name, "orchestrator", "done", asdict(self.result)))

    def execute(self) -> Any:
        raise NotImplementedError

    def _wait_for(self, sender: str, msg_type: str, timeout: float = 30.0) -> Any:
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                msg = self.task_q.get(timeout=1.0)
                if msg.sender == sender and msg.receiver == self.agent_name and msg.msg_type == msg_type:
                    return msg.payload
                self.task_q.put(msg)  # not for requeue
            except queue.Empty: continue
        raise TimeoutError(f"Timed out waiting for {msg_type} from {sender}")


class ReconAgent(BaseAgent):
    """Phase 1 — reconnaissance & enumeration."""
    def execute(self) -> dict:
        findings = {"target": self.target, "ports_open": [22, 80, 443],
                    "services": {"22": "OpenSSH 8.9", "80": "nginx 1.24", "443": "nginx 1.24"},
                    "technologies": ["PHP 8.2", "WordPress 6.3"]}
        self.task_q.put(AgentMessage(self.agent_name, "exploit", "findings", findings))
        self.task_q.put(AgentMessage(self.agent_name, "code", "findings", findings))
        return findings


class ExploitAgent(BaseAgent):
    """Phase 2 — exploitation based on recon findings."""
    def execute(self) -> dict:
        findings = self._wait_for("recon", "findings")
        result = {"findings": findings,
                  "exploits": [{"id": "CVE-2024-1234", "port": 80, "description": "WordPress RCE", "severity": "critical"}]}
        self.task_q.put(AgentMessage(self.agent_name, "report", "exploit_result", result))
        return result


class CodeAgent(BaseAgent):
    """Phase 3 — generate helper scripts / payloads."""
    def execute(self) -> dict:
        findings = self._wait_for("recon", "findings")
        scripts = {"scanner": f"nmap -sV -p 1-65535 {findings['target']}",
                   "exploit_template": f"#!/bin/bash\n# Auto-generated for {findings['target']}\necho 'pwned'"}
        self.task_q.put(AgentMessage(self.agent_name, "report", "code", scripts))
        return scripts


class ReportAgent(BaseAgent):
    """Phase 4 — collect all results and build the consolidated report."""
    def execute(self) -> dict:
        exploit_data = self._wait_for("exploit", "exploit_result")
        code_data = self._wait_for("code", "code")
        report = {"title": f"Assessment Report for {self.target}",
                  "recon": exploit_data.get("findings"),
                  "exploits": exploit_data.get("exploits"),
                  "generated_scripts": code_data,
                  "risk_score": self._score(exploit_data.get("exploits", []))}
        self.task_q.put(AgentMessage(self.agent_name, "orchestrator", "report", report))
        return report

    @staticmethod
    def _score(exploits: list[dict]) -> str:
        return "CRITICAL" if any(e.get("severity") == "critical" for e in exploits) else "LOW"


class Orchestrator:
    """Spawns agents, coordinates execution, and returns consolidated results."""
    AGENT_CLASSES = {"recon": ReconAgent, "exploit": ExploitAgent, "code": CodeAgent, "report": ReportAgent}

    def __init__(self, target: str, models: dict[str, str] | None = None):
        self.target, self.models = target, models or AGENT_MODELS
        self.task_q, self.result_q = queue.Queue(), queue.Queue()
        self.agents, self.results = [], {}

    def list_agents(self) -> None:
        print("\nAgent-to-Model Mapping:\n" + "-" * 46)
        for name, model in self.models.items():
            print(f"  {name:<10} → {model}")
        print()

    def run(self) -> dict:
        print(f"\n{'='*60}\n MULTI-AGENT ORCHESTRATOR  |  target: {self.target}\n{'='*60}\n")
        self._spawn_agents()
        self._start_agents()
        self._collect_results()
        return self._consolidate()

    def _spawn_agents(self) -> None:
        for name, cls in self.AGENT_CLASSES.items():
            agent = cls(name, self.models[name], self.task_q, self.result_q, self.target)
            self.agents.append(agent)
            self.results[name] = agent.result

    def _start_agents(self) -> None:
        for agent in self.agents:
            print(f"  ▶ Starting {agent.agent_name} ({agent.model})")
            agent.start()

    def _collect_results(self) -> None:
        received, expected = 0, len(self.agents)
        while received < expected:
            try:
                msg = self.result_q.get(timeout=120)
                if msg.msg_type == "done":
                    self.results[msg.sender] = AgentResult(**msg.payload)
                    received += 1
                    print(f"  ◀ {msg.sender} finished — {msg.payload['status']} ({msg.payload['elapsed_sec']}s)")
            except queue.Empty:
                print("  ⚠ Timeout waiting for agent results; proceeding with partial data.")
                break

    def _consolidate(self) -> dict:
        consolidated = {"target": self.target, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "agents": {n: asdict(r) for n, r in self.results.items()},
                        "summary": {"total_agents": len(self.agents),
                                    "completed": sum(1 for r in self.results.values() if r.status == "completed"),
                                    "failed": sum(1 for r in self.results.values() if r.status == "error"),
                                    "total_time_sec": round(sum(r.elapsed_sec for r in self.results.values()), 3)}}
        if self.results.get("report") and self.results["report"].output:
            consolidated["report"] = self.results["report"].output
        return consolidated

    @staticmethod
    def display(results: dict) -> None:
        print(f"\n{'='*60}\n CONSOLIDATED RESULTS\n{'='*60}")
        s = results["summary"]
        print(f"\n  Target: {results['target']}  |  Completed: {s['completed']}/{s['total_agents']}  |  Failed: {s['failed']}  |  Time: {s['total_time_sec']}s")
        if "report" in results:
            r = results["report"]
            print(f"  Risk Score: {r.get('risk_score', 'N/A')}")
            for e in r.get("exploits", []):
                print(f"    • [{e.get('severity','?').upper()}] {e.get('id')} — {e.get('description')}")
        print(f"\n{'='*60}\n")

    @staticmethod
    def export_json(results: dict, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"  📄 Results exported to {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-Agent Orchestrator — Recon, Exploit, Code, Report.")
    parser.add_argument("--target", "-t", default="example.com", help="Target IP or domain")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list-models", action="store_true")
    parser.add_argument("--json-out", "-o", help="Export results as JSON")
    args = parser.parse_args()

    orch = Orchestrator(target=args.target)
    if args.list_models: return orch.list_agents()
    if args.dry_run: return orch.list_agents()

    results = orch.run()
    Orchestrator.display(results)
    if args.json_out: Orchestrator.export_json(results, args.json_out)


if __name__ == "__main__":
    main()
