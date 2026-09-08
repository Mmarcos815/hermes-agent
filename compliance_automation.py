#!/usr/bin/env python3
"""
Compliance Automation Tool
===========================
Performs PCI-DSS gap analysis, SOC 2 control mapping,
automated evidence collection, and audit trail generation.

For authorized defensive security and compliance work only.
Self-contained: uses only Python 3.10+ standard library.

Usage:
    python compliance_automation.py pci-gap --output report.json
    python compliance_automation.py soc2-map --output mapping.csv
    python compliance_automation.py collect-evidence --dir ./evidence --output evidence.json
    python compliance_automation.py audit-trail --action "review" --resource "PCI-1.1"
    python compliance_automation.py full-audit --evidence-dir ./evidence --output-dir ./reports
"""

import argparse
import csv
import datetime
import hashlib
import json
import os
import sys
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


# ──────────────────────────────────────────────────────────────────────────────
# Data Models
# ──────────────────────────────────────────────────────────────────────────────

class Status(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    NOT_ASSESSED = "not_assessed"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Control:
    control_id: str
    name: str
    description: str
    framework: str
    sub_requirements: List[str] = field(default_factory=list)


@dataclass
class GapFinding:
    control_id: str
    framework: str
    severity: str
    description: str
    recommendation: str
    status: str = Status.NOT_ASSESSED.value
    evidence_refs: List[str] = field(default_factory=list)


@dataclass
class EvidenceItem:
    evidence_id: str
    control_id: str
    evidence_type: str
    source_path: str
    sha256: str
    size_bytes: int
    collected_at: str
    description: str = ""


@dataclass
class AuditEvent:
    event_id: str
    timestamp: str
    event_type: str
    actor: str
    action: str
    resource: str
    result: str
    details: str = ""
    prev_hash: str = ""
    event_hash: str = ""


# ──────────────────────────────────────────────────────────────────────────────
# Control Framework Definitions (PCI-DSS v4.0 & SOC 2 2017 TSC)
# ──────────────────────────────────────────────────────────────────────────────

PCI_DSS_CONTROLS: List[Control] = [
    Control("PCI-1.1", "Network Security Controls",
            "Processes and mechanisms for network security controls are defined and understood.",
            "PCI-DSS", ["Document all network security control rules", "Review semi-annually"]),
    Control("PCI-1.2", "Network Configuration",
            "Network security controls (NSCs) are configured and maintained.",
            "PCI-DSS", ["Restrict traffic to/from cardholder data environment", "Deny all traffic by default"]),
    Control("PCI-2.1", "Vendor Default Settings",
            "All vendor-supplied defaults are changed before system installation.",
            "PCI-DSS", ["Change default passwords", "Disable unnecessary default accounts"]),
    Control("PCI-3.1", "Stored Account Data",
            "Storage of account data is kept to a minimum.",
            "PCI-DSS", ["Retain only what business requires", "Implement data retention policy"]),
    Control("PCI-3.2", "Sensitive Authentication Data",
            "Sensitive authentication data is not stored after authorization.",
            "PCI-DSS", ["Do not store full track data", "Do not store CVV2/CVC2", "Do not store PINs"]),
    Control("PCI-4.1", "Encrypt Transmission",
            "Account data is protected with strong cryptography during transmission.",
            "PCI-DSS", ["Use TLS 1.2 or higher", "Disable SSL/early TLS", "Enforce strong cipher suites"]),
    Control("PCI-5.1", "Malware Protection",
            "Anti-malware mechanisms are deployed and maintained.",
            "PCI-DSS", ["Deploy on all systems commonly affected", "Keep signatures current"]),
    Control("PCI-6.1", "Secure Development",
            "Security vulnerabilities are identified and addressed.",
            "PCI-DSS", ["Maintain vulnerability management program", "Apply critical patches within 30 days"]),
    Control("PCI-6.2", "Secure Software",
            "Software is developed securely following SDLC practices.",
            "PCI-DSS", ["Code reviews before release", "Separate development/test/production"]),
    Control("PCI-7.1", "Access Control System",
            "Access is limited to system components with need-to-know.",
            "PCI-DSS", ["Define access needs by role", "Restrict based on job classification"]),
    Control("PCI-8.1", "User Identification",
            "All users are authenticated before accessing system components.",
            "PCI-DSS", ["Unique ID for each user", "Implement multi-factor authentication"]),
    Control("PCI-9.1", "Physical Access",
            "Physical access to systems with cardholder data is controlled.",
            "PCI-DSS", ["Use badges/cameras for facility entry", "Visitor management procedures"]),
    Control("PCI-10.1", "Audit Logging",
            "Audit trails link access to individual users.",
            "PCI-DSS", ["Log all access to cardholder data", "Log root/admin actions", "Include timestamps"]),
    Control("PCI-11.1", "Security Testing",
            "Vulnerabilities are regularly tested.",
            "PCI-DSS", ["Quarterly internal vulnerability scans", "Annual penetration test"]),
    Control("PCI-12.1", "Security Policy",
            "Security policy addresses all PCI-DSS requirements.",
            "PCI-DSS", ["Publish and maintain policy", "Annual review cycle", "Assign ownership"]),
]

SOC2_CONTROLS: List[Control] = [
    Control("CC6.1", "Logical Access Controls",
            "Logical access to system components is restricted via policies.",
            "SOC2", ["User access provisioning", "Role-based access control", "Periodic access review"]),
    Control("CC6.2", "Authentication",
            "Prior to access, users and devices are identified and authenticated.",
            "SOC2", ["Multi-factor authentication", "Password complexity enforcement", "Session timeout"]),
    Control("CC6.3", "Access Removal",
            "Access is removed or changed upon role change or termination.",
            "SOC2", ["Automated deprovisioning within 24h", "Quarterly access recertification"]),
    Control("CC6.6", "Encryption",
            "Data is encrypted in transit and at rest.",
            "SOC2", ["TLS 1.2+ for transit", "AES-256 for data at rest", "Key management process"]),
    Control("CC6.7", "Network Controls",
            "Network perimeter controls restrict unauthorized inbound/outbound traffic.",
            "SOC2", ["Firewall rule review", "IDS/IPS deployment", "Network segmentation"]),
    Control("CC6.8", "Monitoring",
            "System components are monitored for anomalies and policy violations.",
            "SOC2", ["Centralized log collection", "Alerting on critical events", "Log retention 12+ months"]),
    Control("CC7.1", "Change Management",
            "Changes are authorized, tested, and approved before production.",
            "SOC2", ["Change advisory board", "Rollback procedures", "Segregation of duties"]),
    Control("CC7.2", "Incident Response",
            "Incident response capability is prepared and maintained.",
            "SOC2", ["Documented IR plan", "Annual tabletop exercise", "Defined escalation paths"]),
    Control("CC8.1", "Risk Assessment",
            "Risks are identified, assessed, and mitigated.",
            "SOC2", ["Annual risk assessment", "Risk register maintenance", "Treatment plans"]),
]

# Cross-mapping: PCI-DSS control -> SOC 2 controls
PCI_TO_SOC2_MAPPING: Dict[str, List[str]] = {
    "PCI-1.1": ["CC6.7"],
    "PCI-1.2": ["CC6.7"],
    "PCI-2.1": ["CC6.1", "CC7.1"],
    "PCI-3.1": ["CC6.1"],
    "PCI-3.2": ["CC6.1", "CC6.6"],
    "PCI-4.1": ["CC6.6"],
    "PCI-5.1": ["CC6.8"],
    "PCI-6.1": ["CC6.8", "CC8.1"],
    "PCI-6.2": ["CC7.1"],
    "PCI-7.1": ["CC6.1", "CC6.3"],
    "PCI-8.1": ["CC6.2", "CC6.3"],
    "PCI-9.1": ["CC6.1"],
    "PCI-10.1": ["CC6.8"],
    "PCI-11.1": ["CC6.8", "CC8.1"],
    "PCI-12.1": ["CC8.1"],
}


# ──────────────────────────────────────────────────────────────────────────────
# 1. PCI-DSS Gap Analysis
# ──────────────────────────────────────────────────────────────────────────────

def run_pci_gap_analysis(assessment_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Perform PCI-DSS gap analysis. If assessment_file is provided (JSON),
    load existing assessment results; otherwise generate a template.
    Returns findings and summary.
    """
    findings: List[GapFinding] = []
    assessment: Dict[str, str] = {}

    if assessment_file and Path(assessment_file).exists():
        with open(assessment_file, "r", encoding="utf-8") as f:
            assessment = json.load(f)

    for control in PCI_DSS_CONTROLS:
        status = assessment.get(control.control_id, Status.NOT_ASSESSED.value)
        if status == Status.NOT_ASSESSED.value:
            severity = Severity.HIGH.value
            desc = f"Control {control.control_id} ({control.name}) has not been assessed."
            rec = f"Conduct assessment: {control.sub_requirements[0] if control.sub_requirements else 'Review control requirements'}"
        elif status == Status.NON_COMPLIANT.value:
            severity = Severity.CRITICAL.value
            desc = f"Control {control.control_id} ({control.name}) is non-compliant."
            rec = f"Remediate: {control.sub_requirements[0] if control.sub_requirements else 'Address gaps per control description'}"
        elif status == Status.PARTIAL.value:
            severity = Severity.MEDIUM.value
            desc = f"Control {control.control_id} ({control.name}) is partially compliant."
            rec = f"Complete remaining requirements: {'; '.join(control.sub_requirements)}"
        else:
            continue  # Compliant — no gap

        findings.append(GapFinding(
            control_id=control.control_id,
            framework="PCI-DSS",
            severity=severity,
            description=desc,
            recommendation=rec,
            status=status,
        ))

    summary = {
        "total_controls": len(PCI_DSS_CONTROLS),
        "gaps_found": len(findings),
        "critical": sum(1 for f in findings if f.severity == Severity.CRITICAL.value),
        "high": sum(1 for f in findings if f.severity == Severity.HIGH.value),
        "medium": sum(1 for f in findings if f.severity == Severity.MEDIUM.value),
        "low": sum(1 for f in findings if f.severity == Severity.LOW.value),
    }

    return {
        "framework": "PCI-DSS v4.0",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "summary": summary,
        "findings": [asdict(f) for f in findings],
    }


def generate_assessment_template(output_path: str) -> None:
    """Generate a blank assessment template for manual completion."""
    template = {c.control_id: Status.NOT_ASSESSED.value for c in PCI_DSS_CONTROLS}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2)
    print(f"Assessment template written to: {output_path}")


# ──────────────────────────────────────────────────────────────────────────────
# 2. SOC 2 Control Mapping
# ──────────────────────────────────────────────────────────────────────────────

def run_soc2_mapping(output_format: str = "json") -> Dict[str, Any]:
    """
    Generate SOC 2 control mapping with PCI-DSS cross-references.
    Returns mapping data structure.
    """
    mapping = []
    for soc_control in SOC2_CONTROLS:
        # Find which PCI-DSS controls map to this SOC 2 control
        linked_pci = []
        for pci_id, soc_ids in PCI_TO_SOC2_MAPPING.items():
            if soc_control.control_id in soc_ids:
                linked_pci.append(pci_id)

        mapping.append({
            "soc2_control": soc_control.control_id,
            "soc2_name": soc_control.name,
            "soc2_description": soc_control.description,
            "soc2_requirements": soc_control.sub_requirements,
            "mapped_pci_dss_controls": linked_pci,
            "coverage": "mapped" if linked_pci else "no_pci_overlap",
        })

    # Also include PCI-DSS controls with no SOC 2 mapping
    for pci_control in PCI_DSS_CONTROLS:
        if pci_control.control_id not in PCI_TO_SOC2_MAPPING:
            mapping.append({
                "soc2_control": "N/A",
                "soc2_name": "No SOC 2 mapping",
                "soc2_description": "",
                "soc2_requirements": [],
                "mapped_pci_dss_controls": [pci_control.control_id],
                "coverage": "pci_only",
            })

    return {
        "mapping_type": "PCI-DSS <-> SOC 2 Cross-Reference",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "total_mappings": len(mapping),
        "mappings": mapping,
    }


def write_mapping_csv(mapping_data: Dict[str, Any], output_path: str) -> None:
    """Write control mapping to CSV format."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "SOC2 Control", "SOC2 Name", "PCI-DSS Controls",
            "Coverage", "SOC2 Requirements"
        ])
        for item in mapping_data["mappings"]:
            writer.writerow([
                item["soc2_control"],
                item["soc2_name"],
                "; ".join(item["mapped_pci_dss_controls"]),
                item["coverage"],
                "; ".join(item["soc2_requirements"]),
            ])
    print(f"Mapping CSV written to: {output_path}")


# ──────────────────────────────────────────────────────────────────────────────
# 3. Automated Evidence Collection
# ──────────────────────────────────────────────────────────────────────────────

EVIDENCE_EXTENSIONS = {
    ".pdf": "document",
    ".docx": "document",
    ".doc": "document",
    ".xlsx": "spreadsheet",
    ".csv": "data",
    ".json": "data",
    ".log": "log",
    ".txt": "text",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".pcap": "network_capture",
    ".conf": "configuration",
    ".yaml": "configuration",
    ".yml": "configuration",
    ".xml": "configuration",
    ".sh": "script",
    ".py": "script",
    ".ps1": "script",
}

# Map file patterns to control IDs (heuristic matching)
CONTROL_PATTERN_MAP = {
    "firewall": "PCI-1.1",
    "password": "PCI-2.1",
    "encryption": "PCI-4.1",
    "encrypt": "PCI-4.1",
    "malware": "PCI-5.1",
    "antivirus": "PCI-5.1",
    "vulnerability": "PCI-6.1",
    "patch": "PCI-6.1",
    "access": "PCI-7.1",
    "mfa": "PCI-8.1",
    "authentication": "PCI-8.1",
    "physical": "PCI-9.1",
    "log": "PCI-10.1",
    "audit": "PCI-10.1",
    "scan": "PCI-11.1",
    "pentest": "PCI-11.1",
    "policy": "PCI-12.1",
    "soc2": "CC6.1",
    "incident": "CC7.2",
    "risk": "CC8.1",
    "change": "CC7.1",
}


def _infer_control_id(file_path: str) -> str:
    """Heuristically infer which control a piece of evidence relates to."""
    lower = file_path.lower()
    for pattern, control_id in CONTROL_PATTERN_MAP.items():
        if pattern in lower:
            return control_id
    return "UNMAPPED"


def _compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_evidence(evidence_dir: str, output_path: str) -> Dict[str, Any]:
    """
    Walk evidence_dir, catalog all files with hashes, sizes, types,
    and inferred control mappings. Write catalog to output_path.
    """
    evidence_items: List[EvidenceItem] = []
    base_path = Path(evidence_dir)

    if not base_path.exists():
        print(f"Warning: evidence directory '{evidence_dir}' does not exist. Creating template.")
        base_path.mkdir(parents=True, exist_ok=True)
        return {"evidence_dir": evidence_dir, "items": [], "total_size": 0, "count": 0}

    for file_path in base_path.rglob("*"):
        if not file_path.is_file():
            continue
        ext = file_path.suffix.lower()
        ev_type = EVIDENCE_EXTENSIONS.get(ext, "unknown")
        sha = _compute_sha256(str(file_path))
        size = file_path.stat().st_size
        rel_path = str(file_path.relative_to(base_path))
        control_id = _infer_control_id(rel_path)

        evidence_items.append(EvidenceItem(
            evidence_id=str(uuid.uuid4())[:8],
            control_id=control_id,
            evidence_type=ev_type,
            source_path=rel_path,
            sha256=sha,
            size_bytes=size,
            collected_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            description=f"Auto-collected {ev_type} evidence",
        ))

    total_size = sum(e.size_bytes for e in evidence_items)
    catalog = {
        "collection_id": str(uuid.uuid4())[:12],
        "evidence_dir": str(base_path.resolve()),
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "count": len(evidence_items),
        "total_size_bytes": total_size,
        "items": [asdict(e) for e in evidence_items],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)

    print(f"Evidence catalog: {len(evidence_items)} files, {total_size:,} bytes")
    print(f"Catalog written to: {output_path}")
    return catalog


# ──────────────────────────────────────────────────────────────────────────────
# 4. Audit Trail Generation
# ──────────────────────────────────────────────────────────────────────────────

AUDIT_LOG_FILE = "compliance_audit_log.jsonl"


def _compute_event_hash(event: AuditEvent) -> str:
    """Compute chained hash for tamper evidence (simple hash chain)."""
    payload = f"{event.event_id}|{event.timestamp}|{event.event_type}|{event.actor}|{event.action}|{event.resource}|{event.result}|{event.prev_hash}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _get_last_hash(log_file: str) -> str:
    """Read the last event's hash from the log file for chaining."""
    if not Path(log_file).exists():
        return "GENESIS"
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if not lines:
                return "GENESIS"
            last = json.loads(lines[-1])
            return last.get("event_hash", "GENESIS")
    except (json.JSONDecodeError, KeyError):
        return "GENESIS"


def log_audit_event(
    event_type: str,
    actor: str,
    action: str,
    resource: str,
    result: str,
    details: str = "",
    log_file: str = AUDIT_LOG_FILE,
) -> AuditEvent:
    """
    Append a tamper-evident audit event to the log file.
    Each event includes a hash chained to the previous event.
    """
    prev_hash = _get_last_hash(log_file)
    event = AuditEvent(
        event_id=str(uuid.uuid4())[:12],
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        event_type=event_type,
        actor=actor,
        action=action,
        resource=resource,
        result=result,
        details=details,
        prev_hash=prev_hash,
    )
    event.event_hash = _compute_event_hash(event)

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(event)) + "\n")

    print(f"Audit event logged: [{event.event_id}] {event_type} | {action} on {resource} -> {result}")
    return event


def verify_audit_trail(log_file: str = AUDIT_LOG_FILE) -> Dict[str, Any]:
    """
    Verify the integrity of the audit trail by checking hash chain.
    Returns verification report.
    """
    if not Path(log_file).exists():
        return {"status": "no_log", "message": f"Audit log '{log_file}' not found."}

    events: List[Dict[str, Any]] = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))

    broken_at = []
    prev_hash = "GENESIS"
    for i, event in enumerate(events):
        # Verify chain link
        if event.get("prev_hash") != prev_hash:
            broken_at.append({
                "index": i,
                "event_id": event.get("event_id"),
                "expected_prev": prev_hash,
                "actual_prev": event.get("prev_hash"),
            })
        # Recompute hash
        recomputed = hashlib.sha256(
            f"{event['event_id']}|{event['timestamp']}|{event['event_type']}|{event['actor']}|{event['action']}|{event['resource']}|{event['result']}|{event['prev_hash']}".encode()
        ).hexdigest()
        if recomputed != event.get("event_hash"):
            broken_at.append({
                "index": i,
                "event_id": event.get("event_id"),
                "issue": "hash_mismatch",
            })
        prev_hash = event.get("event_hash", prev_hash)

    return {
        "status": "valid" if not broken_at else "tampered",
        "total_events": len(events),
        "broken_links": broken_at,
        "verified_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Full Audit Orchestrator
# ──────────────────────────────────────────────────────────────────────────────

def run_full_audit(evidence_dir: str, output_dir: str) -> Dict[str, Any]:
    """Run all four compliance functions and produce consolidated output."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    log_audit_event("audit_start", "compliance_tool", "full_audit", output_dir, "started")

    # 1. PCI Gap Analysis
    pci_result = run_pci_gap_analysis()
    pci_file = out_path / "pci_gap_analysis.json"
    with open(pci_file, "w", encoding="utf-8") as f:
        json.dump(pci_result, f, indent=2)
    log_audit_event("gap_analysis", "compliance_tool", "pci_gap_analysis", str(pci_file), "completed",
                    f"Found {pci_result['summary']['gaps_found']} gaps")

    # 2. SOC 2 Mapping
    mapping_result = run_soc2_mapping()
    mapping_file = out_path / "soc2_control_mapping.json"
    with open(mapping_file, "w", encoding="utf-8") as f:
        json.dump(mapping_result, f, indent=2)
    mapping_csv = out_path / "soc2_control_mapping.csv"
    write_mapping_csv(mapping_result, str(mapping_csv))
    log_audit_event("control_mapping", "compliance_tool", "soc2_mapping", str(mapping_file), "completed",
                    f"{mapping_result['total_mappings']} mappings generated")

    # 3. Evidence Collection
    evidence_file = out_path / "evidence_catalog.json"
    evidence_result = collect_evidence(evidence_dir, str(evidence_file))
    log_audit_event("evidence_collection", "compliance_tool", "collect_evidence", str(evidence_file), "completed",
                    f"{evidence_result['count']} items cataloged")

    # 4. Verify audit trail
    audit_report = verify_audit_trail()
    audit_file = out_path / "audit_trail_verification.json"
    with open(audit_file, "w", encoding="utf-8") as f:
        json.dump(audit_report, f, indent=2)

    consolidated = {
        "audit_run_id": str(uuid.uuid4())[:12],
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "reports": {
            "pci_gap_analysis": str(pci_file),
            "soc2_mapping_json": str(mapping_file),
            "soc2_mapping_csv": str(mapping_csv),
            "evidence_catalog": str(evidence_file),
            "audit_verification": str(audit_file),
        },
        "summary": {
            "pci_gaps": pci_result["summary"]["gaps_found"],
            "soc2_mappings": mapping_result["total_mappings"],
            "evidence_items": evidence_result["count"],
            "audit_status": audit_report["status"],
        },
    }

    consolidated_file = out_path / "consolidated_report.json"
    with open(consolidated_file, "w", encoding="utf-8") as f:
        json.dump(consolidated, f, indent=2)

    log_audit_event("audit_complete", "compliance_tool", "full_audit", str(consolidated_file), "completed")
    print(f"\n{'='*60}")
    print(f"Full audit complete. Reports in: {out_path.resolve()}")
    print(f"  PCI gaps: {consolidated['summary']['pci_gaps']}")
    print(f"  SOC2 mappings: {consolidated['summary']['soc2_mappings']}")
    print(f"  Evidence items: {consolidated['summary']['evidence_items']}")
    print(f"  Audit trail: {consolidated['summary']['audit_status']}")
    return consolidated


# ──────────────────────────────────────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="compliance_automation",
        description="Compliance automation: PCI-DSS gap analysis, SOC 2 mapping, evidence collection, audit trails.",
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # --- pci-gap ---
    p_pci = sub.add_parser("pci-gap", help="Run PCI-DSS gap analysis")
    p_pci.add_argument("--assessment", "-a", default=None,
                       help="Path to existing assessment JSON (optional)")
    p_pci.add_argument("--output", "-o", default="pci_gap_report.json",
                       help="Output file path (default: pci_gap_report.json)")
    p_pci.add_argument("--template", "-t", default=None,
                       help="Generate blank assessment template and exit")

    # --- soc2-map ---
    p_soc2 = sub.add_parser("soc2-map", help="Generate SOC 2 control mapping")
    p_soc2.add_argument("--output", "-o", default="soc2_mapping.json",
                        help="Output JSON file path (default: soc2_mapping.json)")
    p_soc2.add_argument("--csv", default=None,
                        help="Also write CSV mapping to this path")

    # --- collect-evidence ---
    p_ev = sub.add_parser("collect-evidence", help="Catalog evidence files with hashes")
    p_ev.add_argument("--dir", "-d", default="./evidence",
                      help="Evidence directory to scan (default: ./evidence)")
    p_ev.add_argument("--output", "-o", default="evidence_catalog.json",
                      help="Output catalog path (default: evidence_catalog.json)")

    # --- audit-trail ---
    p_audit = sub.add_parser("audit-trail", help="Log or verify audit trail events")
    p_audit.add_argument("--action", default=None,
                         help="Action performed (logs an event)")
    p_audit.add_argument("--resource", default="system",
                         help="Resource affected (default: system)")
    p_audit.add_argument("--actor", default=os.getenv("USER", "unknown"),
                         help="Actor performing the action")
    p_audit.add_argument("--result", default="success",
                         choices=["success", "failure", "denied", "error"],
                         help="Result of the action")
    p_audit.add_argument("--details", default="",
                         help="Additional details")
    p_audit.add_argument("--verify", action="store_true",
                         help="Verify audit trail integrity instead of logging")
    p_audit.add_argument("--log-file", default=AUDIT_LOG_FILE,
                         help=f"Audit log file path (default: {AUDIT_LOG_FILE})")

    # --- full-audit ---
    p_full = sub.add_parser("full-audit", help="Run all compliance checks")
    p_full.add_argument("--evidence-dir", "-e", default="./evidence",
                        help="Evidence directory (default: ./evidence)")
    p_full.add_argument("--output-dir", "-o", default="./reports",
                        help="Output directory for all reports (default: ./reports)")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "pci-gap":
        if args.template:
            generate_assessment_template(args.template)
            return 0
        result = run_pci_gap_analysis(args.assessment)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"PCI-DSS gap analysis written to: {args.output}")
        print(f"  Gaps found: {result['summary']['gaps_found']}")
        print(f"  Critical: {result['summary']['critical']}")
        print(f"  High: {result['summary']['high']}")

    elif args.command == "soc2-map":
        result = run_soc2_mapping()
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"SOC 2 mapping written to: {args.output}")
        if args.csv:
            write_mapping_csv(result, args.csv)

    elif args.command == "collect-evidence":
        collect_evidence(args.dir, args.output)

    elif args.command == "audit-trail":
        if args.verify:
            report = verify_audit_trail(args.log_file)
            print(json.dumps(report, indent=2))
            return 0 if report["status"] == "valid" else 2
        if not args.action:
            print("Error: --action required when logging (or use --verify)")
            return 1
        log_audit_event(
            event_type="manual_event",
            actor=args.actor,
            action=args.action,
            resource=args.resource,
            result=args.result,
            details=args.details,
            log_file=args.log_file,
        )

    elif args.command == "full-audit":
        run_full_audit(args.evidence_dir, args.output_dir)

    return 0


if __name__ == "__main__":
    sys.exit(main())
