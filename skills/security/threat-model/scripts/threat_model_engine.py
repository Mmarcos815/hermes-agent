"""Threat Modeling Engine - auto-generates threat models using STRIDE, attack trees, and DFDs.

Pure native Python (no third-party deps). Provides a programmatic API for:
  1. Data Flow Diagrams (DFDs) - external entities, processes, data stores, flows
  2. STRIDE classification - per-element and per-flow threat enumeration
  3. Attack trees - goal-oriented decomposition of threats
  4. Mitigation mapping - countermeasures per threat

Usage:
    engine = ThreatModelEngine("My Web App")
    engine.add_external_entity("User")
    engine.add_process("Auth Service", trust_level="high")
    engine.add_data_store("User DB", encrypted=True)
    engine.add_flow("User -> Auth Service", "User", "Auth Service", "credentials")
    report = engine.generate()
    print(report.to_text())
"""

from __future__ import annotations

import json
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# STRIDE
# ---------------------------------------------------------------------------

class STRIDECategory(Enum):
    """The six STRIDE threat categories."""
    SPOOFING = "Spoofing"
    TAMPERING = "Tampering"
    REPUDIATION = "Repudiation"
    INFO_DISCLOSURE = "Information Disclosure"
    DENIAL_OF_SERVICE = "Denial of Service"
    ELEVATION_OF_PRIVILEGE = "Elevation of Privilege"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class STRIDE:
    """Convenience constants for each STRIDE category."""
    S = STRIDECategory.SPOOFING
    T = STRIDECategory.TAMPERING
    R = STRIDECategory.REPUDIATION
    I = STRIDECategory.INFO_DISCLOSURE
    D = STRIDECategory.DENIAL_OF_SERVICE
    E = STRIDECategory.ELEVATION_OF_PRIVILEGE


# Map each DFD element type to the STRIDE categories that apply.
# Classic reference: Swhern / Microsoft STRIDE-per-element.
STRIDE_BY_ELEMENT: dict[str, tuple[STRIDECategory, ...]] = {
    "external_entity": (STRIDE.S, STRIDE.T, STRIDE.R, STRIDE.I, STRIDE.D, STRIDE.E),
    "process": (STRIDE.S, STRIDE.T, STRIDE.R, STRIDE.I, STRIDE.D, STRIDE.E),
    "data_store": (STRIDE.T, STRIDE.R, STRIDE.I, STRIDE.D),
    "data_flow": (STRIDE.T, STRIDE.R, STRIDE.I, STRIDE.D),
}


@dataclass
class Threat:
    """A single identified threat."""
    id: str
    name: str
    category: STRIDECategory
    target: str          # DFD element the threat applies to
    description: str
    severity: str = "Medium"   # Low | Medium | High | Critical
    likelihood: str = "Medium"  # Low | Medium | High
    mitigations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": str(self.category),
            "target": self.target,
            "description": self.description,
            "severity": self.severity,
            "likelihood": self.likelihood,
            "mitigations": self.mitigations,
        }


# Threat templates keyed by (element_type, STRIDE_category).
THREAT_TEMPLATES: dict[tuple[str, STRIDECategory], tuple[str, str]] = {
    # External entity
    ("external_entity", STRIDE.S): (
        "Spoof identity",
        "An attacker impersonates '{target}' to gain unauthorized access.",
    ),
    ("external_entity", STRIDE.T): (
        "Tamper with input",
        "Data received from '{target}' could be manipulated in transit or at rest.",
    ),
    ("external_entity", STRIDE.R): (
        "Deny actions",
        "'{target}' may deny having performed an action with no proof to the contrary.",
    ),
    ("external_entity", STRIDE.I): (
        "Information leakage",
        "Sensitive data intended for '{target}' could be intercepted.",
    ),
    ("external_entity", STRIDE.D): (
        "Denial of service",
        "An attacker could overwhelm the system via '{target}'.",
    ),
    ("external_entity", STRIDE.E): (
        "Unauthorized privilege gain",
        "'{target}' could be exploited to elevate privileges.",
    ),
    # Process
    ("process", STRIDE.S): (
        "Spoof process",
        "An attacker could spoof '{target}' to other components.",
    ),
    ("process", STRIDE.T): (
        "Tamper process",
        "The code or runtime state of '{target}' could be modified.",
    ),
    ("process", STRIDE.R): (
        "Repudiate process action",
        "Actions taken by '{target}' may be denied without non-repudiation controls.",
    ),
    ("process", STRIDE.I): (
        "Expose process data",
        "Memory, logs, or config of '{target}' could leak sensitive data.",
    ),
    ("process", STRIDE.D): (
        "Crash or exhaust process",
        "'{target}' could be crashed or starved of resources.",
    ),
    ("process", STRIDE.E): (
        "Exploit process for privilege escalation",
        "A vulnerability in '{target}' could grant elevated access.",
    ),
    # Data store
    ("data_store", STRIDE.T): (
        "Tamper stored data",
        "Data at rest in '{target}' could be modified without authorization.",
    ),
    ("data_store", STRIDE.R): (
        "Repudiate data store writes",
        "Writes to '{target}' may be denied without an audit trail.",
    ),
    ("data_store", STRIDE.I): (
        "Unauthorized data access",
        "An attacker could read data from '{target}' without authorization.",
    ),
    ("data_store", STRIDE.D): (
        "Deny access to data store",
        "'{target}' could be rendered unavailable or destroyed.",
    ),
    # Data flow
    ("data_flow", STRIDE.T): (
        "Tamper data in transit",
        "Data on flow '{target}' could be modified between endpoints.",
    ),
    ("data_flow", STRIDE.R): (
        "Repudiate data transmission",
        "A sender could deny sending data over flow '{target}'.",
    ),
    ("data_flow", STRIDE.I): (
        "Eavesdrop on flow",
        "Data on flow '{target}' could be intercepted by an attacker.",
    ),
    ("data_flow", STRIDE.D): (
        "Disrupt data flow",
        "Flow '{target}' could be interrupted or flooded.",
    ),
}


# ---------------------------------------------------------------------------
# Mitigation catalog
# ---------------------------------------------------------------------------

MITIGATIONS: dict[STRIDECategory, list[str]] = {
    STRIDE.S: [
        "Implement strong authentication (MFA, mutual TLS).",
        "Use cryptographic tokens (JWT, OAuth2) with proper validation.",
        "Enforce session management best practices.",
    ],
    STRIDE.T: [
        "Apply digital signatures / HMACs to detect tampering.",
        "Use TLS 1.3 for all data in transit.",
        "Enforce integrity checks on stored data.",
    ],
    STRIDE.R: [
        "Enable comprehensive audit logging with tamper-evident storage.",
        "Use digital signatures for critical transactions.",
        "Implement centralized log aggregation.",
    ],
    STRIDE.I: [
        "Encrypt data at rest (AES-256-GCM).",
        "Classify and label sensitive data; enforce least privilege.",
        "Apply data masking / tokenization where appropriate.",
    ],
    STRIDE.D: [
        "Implement rate limiting and throttling.",
        "Deploy auto-scaling and redundancy.",
        "Use circuit breakers and bulkhead patterns.",
    ],
    STRIDE.E: [
        "Apply principle of least privilege.",
        "Sandbox / isolate processes (containers, seccomp).",
        "Conduct regular privilege reviews and patch management.",
    ],
}


# ---------------------------------------------------------------------------
# Attack trees
# ---------------------------------------------------------------------------

class Gate(Enum):
    AND = "AND"
    OR = "OR"


@dataclass
class AttackNode:
    """A node in an attack tree."""
    description: str
    gate: Gate | None = None
    children: list["AttackNode"] = field(default_factory=list)
    is_leaf: bool = False
    mitigations: list[str] = field(default_factory=list)

    def add_child(self, node: "AttackNode") -> "AttackNode":
        self.children.append(node)
        return self

    def _render(self, indent: int = 0) -> str:
        prefix = "  " * indent
        if self.is_leaf:
            line = f"{prefix}[LEAF] {self.description}"
        elif self.gate:
            line = f"{prefix}[{self.gate.value}] {self.description}"
        else:
            line = f"{prefix}[GOAL] {self.description}"
        lines = [line]
        for child in self.children:
            lines.append(child._render(indent + 1))
        return "\n".join(lines)

    def __str__(self) -> str:
        return self._render()

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"description": self.description}
        if self.gate:
            result["gate"] = self.gate.value
        if self.is_leaf:
            result["is_leaf"] = True
        if self.mitigations:
            result["mitigations"] = self.mitigations
        if self.children:
            result["children"] = [c.to_dict() for c in self.children]
        return result


def build_attack_tree_for_threat(threat: Threat) -> AttackNode:
    """Generate an attack tree rooted at the given threat."""
    root = AttackNode(f"Attack: {threat.name}", gate=Gate.OR)

    if threat.category == STRIDE.S:
        root.add_child(
            AttackNode("Forge credentials", gate=Gate.OR)
            .add_child(AttackNode("Steal credentials via phishing", is_leaf=True))
            .add_child(AttackNode("Brute-force weak credentials", is_leaf=True))
            .add_child(AttackNode("Exploit authentication bypass", is_leaf=True))
        )
        root.add_child(
            AttackNode("Spoof network identity", gate=Gate.AND)
            .add_child(AttackNode("ARP spoof / DNS hijack", is_leaf=True))
            .add_child(AttackNode("Forge TLS certificate", is_leaf=True))
        )
    elif threat.category == STRIDE.T:
        root.add_child(
            AttackNode("Modify data in transit", gate=Gate.OR)
            .add_child(AttackNode("Man-in-the-middle attack", is_leaf=True))
            .add_child(AttackNode("Replay attack", is_leaf=True))
        )
        root.add_child(
            AttackNode("Modify stored data", gate=Gate.OR)
            .add_child(AttackNode("Exploit injection vulnerability", is_leaf=True))
            .add_child(AttackNode("Direct database access", is_leaf=True))
        )
    elif threat.category == STRIDE.R:
        root.add_child(
            AttackNode("Delete or corrupt audit logs", gate=Gate.OR)
            .add_child(AttackNode("Exploit log injection", is_leaf=True))
            .add_child(AttackNode("Compromise logging service", is_leaf=True))
        )
    elif threat.category == STRIDE.I:
        root.add_child(
            AttackNode("Exfiltrate sensitive data", gate=Gate.OR)
            .add_child(AttackNode("Exploit access control flaw", is_leaf=True))
            .add_child(AttackNode("Eavesdrop unencrypted traffic", is_leaf=True))
            .add_child(AttackNode("Read data from compromised storage", is_leaf=True))
        )
    elif threat.category == STRIDE.D:
        root.add_child(
            AttackNode("Overwhelm the target", gate=Gate.OR)
            .add_child(AttackNode("Volumetric DDoS", is_leaf=True))
            .add_child(AttackNode("Application-layer flood", is_leaf=True))
            .add_child(AttackNode("Resource exhaustion attack", is_leaf=True))
        )
    elif threat.category == STRIDE.E:
        root.add_child(
            AttackNode("Escalate privileges", gate=Gate.OR)
            .add_child(AttackNode("Exploit OS/service vulnerability", is_leaf=True))
            .add_child(AttackNode("Abuse misconfigured permissions", is_leaf=True))
            .add_child(AttackNode("Exploit SUID binary or container escape", is_leaf=True))
        )
    else:
        root.add_child(AttackNode("Unknown attack vector", is_leaf=True))

    root.mitigations = threat.mitigations
    return root


# ---------------------------------------------------------------------------
# DFD elements
# ---------------------------------------------------------------------------

@dataclass
class DFDElement:
    """Base class for a DFD element."""
    name: str
    element_type: str          # external_entity | process | data_store | data_flow
    metadata: dict[str, Any] = field(default_factory=dict)
    stride_threats: list[Threat] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.element_type,
            "metadata": self.metadata,
            "threats": [t.to_dict() for t in self.stride_threats],
        }


@dataclass
class DataFlow(DFDElement):
    """A directed data flow between two DFD elements."""
    source: str = ""
    destination: str = ""
    data_type: str = ""
    encrypted: bool = False
    protocol: str = ""

    def __post_init__(self) -> None:
        self.element_type = "data_flow"
        self.metadata.setdefault("source", self.source)
        self.metadata.setdefault("destination", self.destination)
        self.metadata.setdefault("data_type", self.data_type)
        self.metadata.setdefault("encrypted", self.encrypted)
        self.metadata.setdefault("protocol", self.protocol)


# ---------------------------------------------------------------------------
# Threat model report
# ---------------------------------------------------------------------------

@dataclass
class ThreatModelReport:
    """Aggregated threat model output."""
    system_name: str
    created_at: str
    elements: list[DFDElement]
    threats: list[Threat]
    attack_trees: list[AttackNode]
    summary: dict[str, int] = field(default_factory=dict)

    def to_text(self) -> str:
        lines: list[str] = []
        lines.append("=" * 72)
        lines.append(f" THREAT MODEL: {self.system_name}")
        lines.append(f" Generated: {self.created_at}")
        lines.append("=" * 72)

        # DFD elements
        lines.append("\n## DFD Elements")
        lines.append("-" * 40)
        for elem in self.elements:
            tag = elem.element_type.upper().replace("_", " ")
            lines.append(f"  [{tag}] {elem.name}")
            if isinstance(elem, DataFlow):
                lines.append(f"    {elem.source} --[{elem.data_type}]--> {elem.destination}")
                if elem.encrypted:
                    lines.append("    (encrypted in transit)")

        # Threats by STRIDE category
        lines.append("\n## Threats (STRIDE)")
        lines.append("-" * 40)
        by_category: dict[str, list[Threat]] = {}
        for t in self.threats:
            by_category.setdefault(str(t.category), []).append(t)
        for cat in STRIDECategory:
            items = by_category.get(str(cat), [])
            if not items:
                continue
            lines.append(f"\n  [{cat.value}] ({len(items)} threats)")
            for t in items:
                lines.append(f"    {t.id}: {t.name}")
                lines.append(f"      Target : {t.target}")
                lines.append(f"      Severity: {t.severity} | Likelihood: {t.likelihood}")
                lines.append(f"      {t.description}")
                if t.mitigations:
                    lines.append("      Mitigations:")
                    for m in t.mitigations:
                        lines.append(f"        - {m}")

        # Attack trees
        lines.append("\n## Attack Trees")
        lines.append("-" * 40)
        for i, tree in enumerate(self.attack_trees, 1):
            lines.append(f"\n  Tree #{i}:")
            for line in str(tree).split("\n"):
                lines.append(f"    {line}")

        # Summary
        lines.append("\n## Summary")
        lines.append("-" * 40)
        lines.append(f"  Total elements : {len(self.elements)}")
        lines.append(f"  Total threats  : {len(self.threats)}")
        for key, val in self.summary.items():
            lines.append(f"  {key}: {val}")

        lines.append("\n" + "=" * 72)
        return "\n".join(lines)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps({
            "system_name": self.system_name,
            "created_at": self.created_at,
            "elements": [e.to_dict() for e in self.elements],
            "threats": [t.to_dict() for t in self.threats],
            "attack_trees": [t.to_dict() for t in self.attack_trees],
            "summary": self.summary,
        }, indent=indent, default=str)


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------

class ThreatModelEngine:
    """Auto-generates threat models using STRIDE, attack trees, and DFDs."""

    def __init__(self, system_name: str) -> None:
        self.system_name = system_name
        self._elements: list[DFDElement] = []
        self._threat_counter = 0

    # -- Element registration ---------------------------------------------

    def add_external_entity(self, name: str, **meta: Any) -> DFDElement:
        elem = DFDElement(name=name, element_type="external_entity", metadata=meta)
        self._elements.append(elem)
        return elem

    def add_process(
        self, name: str, trust_level: str = "medium", **meta: Any,
    ) -> DFDElement:
        meta.setdefault("trust_level", trust_level)
        elem = DFDElement(name=name, element_type="process", metadata=meta)
        self._elements.append(elem)
        return elem

    def add_data_store(
        self, name: str, encrypted: bool = False, **meta: Any,
    ) -> DFDElement:
        meta.setdefault("encrypted", encrypted)
        elem = DFDElement(name=name, element_type="data_store", metadata=meta)
        self._elements.append(elem)
        return elem

    def add_flow(
        self,
        label: str,
        source: str,
        destination: str,
        data_type: str = "",
        encrypted: bool = False,
        protocol: str = "",
        **meta: Any,
    ) -> DataFlow:
        flow = DataFlow(
            name=label,
            element_type="data_flow",
            source=source,
            destination=destination,
            data_type=data_type,
            encrypted=encrypted,
            protocol=protocol,
            metadata=meta,
        )
        self._elements.append(flow)
        return flow

    # -- Threat generation ------------------------------------------------

    def _next_id(self) -> str:
        self._threat_counter += 1
        return f"T-{self._threat_counter:03d}"

    def _apply_context(self, threat: Threat, elem: DFDElement) -> Threat:
        """Adjust severity/likelihood and mitigations based on element metadata."""
        if elem.element_type == "data_store":
            if elem.metadata.get("encrypted"):
                if threat.category in (STRIDE.I, STRIDE.T):
                    threat.severity = _downgrade(threat.severity)
                    threat.mitigations.insert(0, "Encryption at rest is already enabled.")
            else:
                if threat.category in (STRIDE.I, STRIDE.T):
                    threat.severity = _upgrade(threat.severity)

        if elem.element_type == "data_flow":
            if elem.metadata.get("encrypted"):
                if threat.category in (STRIDE.I, STRIDE.T):
                    threat.severity = _downgrade(threat.severity)
                    threat.mitigations.insert(0, "Transport encryption (TLS) is enabled.")
            else:
                if threat.category in (STRIDE.I, STRIDE.T):
                    threat.severity = _upgrade(threat.severity)

        if elem.element_type == "process":
            tl = elem.metadata.get("trust_level", "medium")
            if tl == "high" and threat.severity in ("Low", "Medium"):
                threat.severity = _upgrade(threat.severity)

        return threat

    def _generate_threats_for_element(self, elem: DFDElement) -> list[Threat]:
        threats: list[Threat] = []
        categories = STRIDE_BY_ELEMENT.get(elem.element_type, ())
        for cat in categories:
            template = THREAT_TEMPLATES.get((elem.element_type, cat))
            if not template:
                continue
            name_tpl, desc_tpl = template
            threat = Threat(
                id=self._next_id(),
                name=name_tpl.format(target=elem.name),
                category=cat,
                target=elem.name,
                description=desc_tpl.format(target=elem.name),
                mitigations=list(MITIGATIONS.get(cat, [])),
            )
            threat = self._apply_context(threat, elem)
            threats.append(threat)
        elem.stride_threats = threats
        return threats

    def generate(self) -> ThreatModelReport:
        """Run the full threat modeling pipeline and return a report."""
        all_threats: list[Threat] = []
        for elem in self._elements:
            all_threats.extend(self._generate_threats_for_element(elem))

        attack_trees = [build_attack_tree_for_threat(t) for t in all_threats]

        summary = self._summarize(all_threats)

        return ThreatModelReport(
            system_name=self.system_name,
            created_at=datetime.now().isoformat(timespec="seconds"),
            elements=list(self._elements),
            threats=all_threats,
            attack_trees=attack_trees,
            summary=summary,
        )

    def _summarize(self, threats: list[Threat]) -> dict[str, int]:
        counts: dict[str, int] = {
            "By Category": 0,
            "Critical": 0,
            "High": 0,
            "Medium": 0,
            "Low": 0,
        }
        seen_categories: set[str] = set()
        for t in threats:
            cat = str(t.category)
            if cat not in seen_categories:
                seen_categories.add(cat)
            sev = t.severity
            if sev in counts:
                counts[sev] += 1
        counts["By Category"] = len(seen_categories)
        return counts


# ---------------------------------------------------------------------------
# Severity helpers
# ---------------------------------------------------------------------------

_SEVERITY_ORDER = ("Low", "Medium", "High", "Critical")


def _upgrade(severity: str) -> str:
    try:
        idx = _SEVERITY_ORDER.index(severity)
        return _SEVERITY_ORDER[min(idx + 1, len(_SEVERITY_ORDER) - 1)]
    except ValueError:
        return severity


def _downgrade(severity: str) -> str:
    try:
        idx = _SEVERITY_ORDER.index(severity)
        return _SEVERITY_ORDER[max(idx - 1, 0)]
    except ValueError:
        return severity


# ---------------------------------------------------------------------------
# Quick-start demo (run as __main__)
# ---------------------------------------------------------------------------

def main() -> None:
    """Demonstrate the engine on a sample web-application architecture."""
    engine = ThreatModelEngine("E-Commerce Web Application")

    # External entities
    engine.add_external_entity("Customer", role="end-user")
    engine.add_external_entity("Admin", role="privileged")
    engine.add_external_entity("Payment Gateway", role="third-party")

    # Processes
    engine.add_process("Web Frontend", trust_level="low")
    engine.add_process("API Gateway", trust_level="high")
    engine.add_process("Auth Service", trust_level="high")
    engine.add_process("Order Service", trust_level="medium")
    engine.add_process("Payment Service", trust_level="high")

    # Data stores
    engine.add_data_store("Product Catalog DB", encrypted=True)
    engine.add_data_store("Order DB", encrypted=True)
    engine.add_data_store("User DB", encrypted=True)
    engine.add_data_store("Session Cache", encrypted=False)

    # Flows
    engine.add_flow(
        "Customer -> Web Frontend",
        source="Customer", destination="Web Frontend",
        data_type="HTTP requests", encrypted=True, protocol="HTTPS",
    )
    engine.add_flow(
        "Web Frontend -> API Gateway",
        source="Web Frontend", destination="API Gateway",
        data_type="API calls", encrypted=True, protocol="HTTPS",
    )
    engine.add_flow(
        "API Gateway -> Auth Service",
        source="API Gateway", destination="Auth Service",
        data_type="auth tokens", encrypted=True, protocol="mTLS",
    )
    engine.add_flow(
        "API Gateway -> Order Service",
        source="API Gateway", destination="Order Service",
        data_type="order commands", encrypted=True, protocol="gRPC",
    )
    engine.add_flow(
        "Order Service -> Order DB",
        source="Order Service", destination="Order DB",
        data_type="SQL queries", encrypted=True,
    )
    engine.add_flow(
        "Order Service -> Payment Service",
        source="Order Service", destination="Payment Service",
        data_type="payment requests", encrypted=True, protocol="mTLS",
    )
    engine.add_flow(
        "Payment Service -> Payment Gateway",
        source="Payment Service", destination="Payment Gateway",
        data_type="card data", encrypted=True, protocol="HTTPS",
    )
    engine.add_flow(
        "Auth Service -> Session Cache",
        source="Auth Service", destination="Session Cache",
        data_type="session tokens", encrypted=False,
    )

    report = engine.generate()
    print(report.to_text())
    print()
    print("JSON export snippet:")
    print(report.to_json()[:600] + "...")


if __name__ == "__main__":
    main()
