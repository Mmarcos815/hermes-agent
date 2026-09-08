"""
Multi-Agent Swarm — Coordinated Security Assessment Framework

A simulation of coordinated agents performing security assessment tasks.
Educational/demonstration purposes only — runs against authorized targets
with explicit scope boundaries enforced by the orchestrator.

Architecture:
  - ReconAgent: enumerates attack surface (ports, services, endpoints)
  - ExploitAgent: validates vulnerabilities against in-scope targets
  - PostExploitAgent: maps persistence/credential-access paths (dry-run)
  - ReportingAgent: aggregates findings into structured reports
  - Orchestrator: enforces scope, serializes access, and coordinates agents
"""

from __future__ import annotations

import json
import queue
import threading
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


# ---------------------------------------------------------------------------
# Shared data model
# ---------------------------------------------------------------------------

class Severity(Enum):
    INFO = auto()
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()

    def __str__(self) -> str:
        return self.name


class FindingKind(Enum):
    PORT_OPEN = "port_open"
    SERVICE_VER = "service_version"
    VULN = "vulnerability"
    CREDENTIAL = "credential_exposure"
    PERSISTENCE = "persistence_path"
    RECOMMENDATION = "remediation"


@dataclass
class Finding:
    """Immutable record produced by any agent."""
    kind: FindingKind
    severity: Severity
    title: str
    detail: str
    source_agent: str
    target: str
    finding_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.finding_id,
            "kind": self.kind.value,
            "severity": str(self.severity),
            "title": self.title,
            "detail": self.detail,
            "agent": self.source_agent,
            "target": self.target,
            "ts": self.timestamp,
        }


@dataclass
class Scope:
    """Targets explicitly authorized for testing. Orchestrator enforces this."""
    allowed_hosts: set[str]
    allowed_ports: set[int] | None = None  # None = all ports allowed
    max_severity: Severity = Severity.HIGH  # stop above this during dry-run

    def is_host_allowed(self, host: str) -> bool:
        return host in self.allowed_hosts

    def is_port_allowed(self, port: int) -> bool:
        if self.allowed_ports is None:
            return True
        return port in self.allowed_ports


@dataclass
class TaskMessage:
    """Inter-agent message passed through the orchestrator's bus."""
    sender: str
    recipient: str
    payload: Any
    msg_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])


# ---------------------------------------------------------------------------
# Base agent
# ---------------------------------------------------------------------------

class Agent(ABC):
    """Thread-safe agent base with a mailbox for inter-agent messages."""

    def __init__(self, name: str, scope: Scope) -> None:
        self.name = name
        self.scope = scope
        self.mailbox: queue.Queue[TaskMessage] = queue.Queue()
        self.findings: list[Finding] = []
        self._running = threading.Event()

    # ---- lifecycle ----
    def start(self) -> None:
        self._running.set()
        self._thread = threading.Thread(target=self._run, name=self.name, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running.clear()
        self.mailbox.put(TaskMessage(sender="orchestrator", recipient=self.name, payload=None))

    def join(self, timeout: float = 5.0) -> None:
        if hasattr(self, "_thread"):
            self._thread.join(timeout=timeout)

    def _run(self) -> None:
        """Main loop: receive messages, dispatch to handle()."""
        self.on_start()
        while self._running.is_set():
            try:
                msg = self.mailbox.get(timeout=0.5)
            except queue.Empty:
                continue
            if msg.payload is None:  # poison pill
                break
            try:
                self.handle(msg)
            except Exception as exc:  # never let one message kill the agent
                self.log(f"error handling {msg.msg_id}: {exc!r}")
        self.on_stop()

    # ---- messaging ----
    def send(self, orchestrator: "Orchestrator", recipient: str, payload: Any) -> None:
        orchestrator.route(TaskMessage(sender=self.name, recipient=recipient, payload=payload))

    def emit(self, finding: Finding) -> None:
        self.findings.append(finding)

    # ---- subclass hooks ----
    def log(self, msg: str) -> None:
        print(f"[{self.name}] {msg}")

    def on_start(self) -> None: ...
    def on_stop(self) -> None: ...

    @abstractmethod
    def handle(self, msg: TaskMessage) -> None: ...


# ---------------------------------------------------------------------------
# Concrete agents
# ---------------------------------------------------------------------------

class ReconAgent(Agent):
    """Phase 1 — enumerate hosts, ports, services within scope."""

    def on_start(self) -> None:
        self.log("reconnaissance phase starting")

    def handle(self, msg: TaskMessage) -> None:
        if not isinstance(msg.payload, list):
            return
        for host in msg.payload:
            if not self.scope.is_host_allowed(host):
                self.log(f"SKIP out-of-scope host: {host}")
                continue
            self._enumerate_host(host)

    def _enumerate_host(self, host: str) -> None:
        """Simulated port/service scan. Replace with real scanner in production."""
        common_ports = [21, 22, 80, 443, 3306, 8080, 8443]
        for port in common_ports:
            if not self.scope.is_port_allowed(port):
                continue
            # Simulation: only "open" even ports for demo
            if port % 2 == 0:
                self.emit(Finding(
                    kind=FindingKind.PORT_OPEN,
                    severity=Severity.INFO,
                    title=f"Open port {port}",
                    detail=f"TCP port {port} accepting connections on {host}",
                    source_agent=self.name,
                    target=host,
                ))
                # Service banner grab simulation
                service = {22: "SSH", 80: "HTTP", 443: "HTTPS", 8080: "HTTP-Proxy"}.get(port, "unknown")
                if service != "unknown":
                    self.emit(Finding(
                        kind=FindingKind.SERVICE_VER,
                        severity=Severity.INFO,
                        title=f"{service} detected on {port}",
                        detail=f"Banner: {service}/2.4.5 (simulated)",
                        source_agent=self.name,
                        target=host,
                    ))

    def on_stop(self) -> None:
        self.log(f"recon complete — {len(self.findings)} findings")


class ExploitAgent(Agent):
    """Phase 2 — validate vulnerabilities discovered by recon."""

    def on_start(self) -> None:
        self.log("exploitation phase armed (dry-run mode)")

    def handle(self, msg: TaskMessage) -> None:
        """Receives a list of Findings from recon to validate."""
        if not isinstance(msg.payload, list):
            return
        for finding in msg.payload:
            if not isinstance(finding, Finding):
                continue
            if not self.scope.is_host_allowed(finding.target):
                self.log(f"SKIP out-of-scope: {finding.target}")
                continue
            self._validate(finding)

    def _validate(self, finding: Finding) -> None:
        """Simulated vulnerability validation — no real exploitation."""
        if finding.kind == FindingKind.PORT_OPEN:
            port = self._extract_port(finding.title)
            # Simulated logic: flag well-known risky ports
            if port in {21, 23, 3306}:
                self.emit(Finding(
                    kind=FindingKind.VULN,
                    severity=Severity.MEDIUM,
                    title=f"Potentially exposed service on port {port}",
                    detail=(
                        f"Port {port} on {finding.target} is exposed. "
                        f"Recommended: restrict access, enforce auth."
                    ),
                    source_agent=self.name,
                    target=finding.target,
                ))

    @staticmethod
    def _extract_port(title: str) -> int:
        """Naive port extraction from finding title."""
        for token in title.split():
            if token.isdigit():
                return int(token)
        return 0

    def on_stop(self) -> None:
        self.log(f"exploitation complete — {len(self.findings)} findings")


class PostExploitAgent(Agent):
    """Phase 3 — dry-run persistence / lateral-movement path mapping."""

    def on_start(self) -> None:
        self.log("post-exploit analysis starting (dry-run only)")

    def handle(self, msg: TaskMessage) -> None:
        if not isinstance(msg.payload, list):
            return
        for finding in msg.payload:
            if not isinstance(finding, Finding):
                continue
            if finding.kind == FindingKind.VULN and finding.severity.value >= Severity.MEDIUM.value:
                # Simulate: check if this vuln could lead to persistence
                self.emit(Finding(
                    kind=FindingKind.PERSISTENCE,
                    severity=Severity.LOW,
                    title=f"Persistence path via {finding.title}",
                    detail=(
                        f"DRY-RUN: {finding.title} on {finding.target} could allow "
                        f"cron/job persistence. Verify patching priority."
                    ),
                    source_agent=self.name,
                    target=finding.target,
                ))

    def on_stop(self) -> None:
        self.log(f"post-exploit analysis complete — {len(self.findings)} findings")


class ReportingAgent(Agent):
    """Phase 4 — aggregate all findings into a structured report."""

    def __init__(self, name: str, scope: Scope) -> None:
        super().__init__(name, scope)
        self.collected: list[Finding] = []

    def on_start(self) -> None:
        self.log("report agent ready — awaiting findings")

    def handle(self, msg: TaskMessage) -> None:
        if isinstance(msg.payload, list):
            for item in msg.payload:
                if isinstance(item, Finding):
                    self.collected.append(item)
            self.log(f"received {len(msg.payload)} findings (total: {len(self.collected)})")
        elif msg.payload == "GENERATE":
            self._generate_report()

    def _generate_report(self) -> None:
        severity_counts: dict[str, int] = {}
        for f in self.collected:
            severity_counts[str(f.severity)] = severity_counts.get(str(f.severity), 0) + 1

        report = {
            "report_id": uuid.uuid4().hex[:12],
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_findings": len(self.collected),
            "severity_breakdown": severity_counts,
            "findings": [f.to_dict() for f in self.collected],
        }
        self.log("=== REPORT ===")
        self.log(json.dumps(report, indent=2))
        self.log("=== END REPORT ===")
        self.last_report = report

    def on_stop(self) -> None:
        self.log(f"reporting complete — {len(self.collected)} findings captured")


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class Orchestrator:
    """Central coordinator — enforces scope, routes messages, drives phases."""

    def __init__(self, scope: Scope) -> None:
        self.scope = scope
        self.agents: dict[str, Agent] = {}
        self.phase = 0
        self._lock = threading.Lock()

    def register(self, agent: Agent) -> None:
        self.agents[agent.name] = agent

    def route(self, msg: TaskMessage) -> None:
        """Thread-safe message routing with scope check on target names."""
        with self._lock:
            if msg.recipient == "broadcast":
                for name, agent in self.agents.items():
                    if name != msg.sender:
                        agent.mailbox.put(msg)
            elif msg.recipient in self.agents:
                self.agents[msg.recipient].mailbox.put(msg)

    def run_swarm(self, targets: list[str], timeout: float = 30.0) -> dict:
        """Execute all phases against targets and return the final report."""
        # Validate targets against scope
        valid_targets = [t for t in targets if self.scope.is_host_allowed(t)]
        if not valid_targets:
            print("[orchestrator] no in-scope targets to process")
            return {}

        # Start all agents
        for agent in self.agents.values():
            agent.start()

        try:
            # Phase 1: Recon
            self._advance_phase(1, "Reconnaissance")
            self.route(TaskMessage(
                sender="orchestrator",
                recipient="recon",
                payload=valid_targets,
            ))
            time.sleep(1)  # allow recon to finish

            # Phase 2: Exploit (fed by recon findings)
            self._advance_phase(2, "Vulnerability Validation")
            recon_findings = self.agents["recon"].findings
            self.route(TaskMessage(
                sender="orchestrator",
                recipient="exploit",
                payload=recon_findings,
            ))
            time.sleep(1)

            # Phase 3: Post-exploit analysis
            self._advance_phase(3, "Post-Exploit Analysis")
            exploit_findings = self.agents["exploit"].findings
            self.route(TaskMessage(
                sender="orchestrator",
                recipient="postexploit",
                payload=exploit_findings,
            ))
            time.sleep(1)

            # Phase 4: Aggregate & report
            self._advance_phase(4, "Reporting")
            all_findings: list[Finding] = []
            for name, agent in self.agents.items():
                if name != "reporter":
                    all_findings.extend(agent.findings)
            self.route(TaskMessage(
                sender="orchestrator",
                recipient="reporter",
                payload=all_findings,
            ))
            time.sleep(0.5)
            self.route(TaskMessage(
                sender="orchestrator",
                recipient="reporter",
                payload="GENERATE",
            ))
            time.sleep(1)

        finally:
            for agent in self.agents.values():
                agent.stop()
            for agent in self.agents.values():
                agent.join()

        reporter = self.agents["reporter"]
        return getattr(reporter, "last_report", {})

    def _advance_phase(self, n: int, label: str) -> None:
        self.phase = n
        print(f"\n[orchestrator] ═══ Phase {n}: {label} ═══")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Demonstrate the multi-agent swarm against example targets."""
    scope = Scope(
        allowed_hosts={"10.0.0.1", "10.0.0.2", "192.168.1.100"},
        allowed_ports={22, 80, 443, 8080},
        max_severity=Severity.HIGH,
    )

    orch = Orchestrator(scope)
    orch.register(ReconAgent("recon", scope))
    orch.register(ExploitAgent("exploit", scope))
    orch.register(PostExploitAgent("postexploit", scope))
    orch.register(ReportingAgent("reporter", scope))

    targets = ["10.0.0.1", "10.0.0.2", "10.0.0.99"]  # .99 is out-of-scope
    report = orch.run_swarm(targets)

    print(f"\n[main] swarm complete — report has {report.get('total_findings', 0)} findings")
    if report.get("severity_breakdown"):
        print(f"[main] severity breakdown: {report['severity_breakdown']}")


if __name__ == "__main__":
    main()
