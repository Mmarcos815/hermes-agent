"""
Compliance Scanner
==================
Scans for compliance issues across PCI-DSS, HIPAA, SOC 2, and GDPR frameworks.
Maps findings to specific compliance requirements and generates actionable reports.

Usage:
    python compliance_scanner.py [--target PATH] [--framework FRAMEWORK] [--output REPORT]
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class Severity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class Finding:
    """A single compliance finding."""
    framework: str
    control_id: str
    title: str
    description: str
    severity: Severity
    evidence: str
    remediation: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "framework": self.framework,
            "control_id": self.control_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "evidence": self.evidence,
            "remediation": self.remediation,
            "file_path": self.file_path,
            "line_number": self.line_number,
        }


@dataclass
class ComplianceFramework:
    """Defines a compliance framework and its controls."""
    name: str
    description: str
    controls: dict[str, str]  # control_id -> description


# Framework definitions
FRAMEWORKS = {
    "PCI-DSS": ComplianceFramework(
        name="PCI-DSS v4.0",
        description="Payment Card Industry Data Security Standard",
        controls={
            "REQ-1": "Install and maintain network security controls",
            "REQ-2": "Apply secure configurations to all system components",
            "REQ-3": "Protect stored account data",
            "REQ-4": "Protect cardholder data with strong cryptography",
            "REQ-5": "Protect systems and networks from malicious software",
            "REQ-6": "Develop and maintain secure systems and software",
            "REQ-7": "Restrict access to system components",
            "REQ-8": "Identify users and authenticate access",
            "REQ-9": "Restrict physical access to cardholder data",
            "REQ-10": "Log and monitor all access to system components",
            "REQ-11": "Test security of systems and networks regularly",
            "REQ-12": "Support security with organizational policies",
        },
    ),
    "HIPAA": ComplianceFramework(
        name="HIPAA Security Rule",
        description="Health Insurance Portability and Accountability Act",
        controls={
            "164.312(a)(1)": "Access Control - Unique User Identification",
            "164.312(a)(2)(i)": "Access Control - Emergency Access Procedure",
            "164.312(a)(2)(ii)": "Access Control - Automatic Logoff",
            "164.312(a)(2)(iv)": "Access Control - Encryption and Decryption",
            "164.312(b)": "Audit Controls",
            "164.312(c)(1)": "Integrity - Mechanism to Authenticate ePHI",
            "164.312(d)": "Person or Entity Authentication",
            "164.312(e)(1)": "Transmission Security - Integrity Controls",
            "164.312(e)(2)(ii)": "Transmission Security - Encryption",
            "164.308(a)(1)(ii)(D)": "Information System Activity Review",
        },
    ),
    "SOC-2": ComplianceFramework(
        name="SOC 2 Type II",
        description="Service Organization Control - Trust Services Criteria",
        controls={
            "CC6.1": "Logical and physical access controls",
            "CC6.2": "User authentication and authorization",
            "CC6.3": "Role-based access control",
            "CC6.4": "Encryption of data at rest",
            "CC6.5": "Encryption of data in transit",
            "CC6.6": "Network security controls",
            "CC6.7": "Monitoring of system components",
            "CC6.8": "Vulnerability detection and remediation",
            "CC7.1": "Security event detection",
            "CC7.2": "Incident response and recovery",
            "CC7.3": "Security event logging and monitoring",
            "CC8.1": "Change management procedures",
        },
    ),
    "GDPR": ComplianceFramework(
        name="GDPR",
        description="General Data Protection Regulation (EU 2016/679)",
        controls={
            "ART-5": "Principles relating to processing of personal data",
            "ART-6": "Lawfulness of processing",
            "ART-13": "Information to be provided (transparency)",
            "ART-15": "Right of access by the data subject",
            "ART-17": "Right to erasure (right to be forgotten)",
            "ART-20": "Right to data portability",
            "ART-25": "Data protection by design and by default",
            "ART-30": "Records of processing activities",
            "ART-32": "Security of processing",
            "ART-33": "Notification of personal data breach",
            "ART-35": "Data protection impact assessment",
        },
    ),
}


class ComplianceScanner:
    """Scans code and configurations for compliance issues."""

    # Patterns that indicate potential compliance violations
    PATTERNS = {
        "hardcoded_secret": {
            "patterns": [
                r'(?i)(password|passwd|pwd|secret|token|api_key|apikey)\s*[=:]\s*["\'][^"\']{4,}["\']',
                r'(?i)(aws_access_key_id|aws_secret_access_key)\s*[=:]\s*["\'][^"\']+["\']',
                r'(?i)private[_-]?key\s*[=:]\s*["\'][^"\']+["\']',
            ],
            "frameworks": {
                "PCI-DSS": ("REQ-3", Severity.CRITICAL),
                "HIPAA": ("164.312(a)(2)(iv)", Severity.CRITICAL),
                "SOC-2": ("CC6.1", Severity.HIGH),
                "GDPR": ("ART-32", Severity.CRITICAL),
            },
            "title": "Hardcoded Secret Detected",
            "description": "A hardcoded secret (password, API key, or token) was found in source code.",
            "remediation": "Move secrets to environment variables or a secrets manager (e.g., AWS Secrets Manager, HashiCorp Vault).",
        },
        "weak_crypto": {
            "patterns": [
                r'(?i)md5\s*\(',
                r'(?i)sha1\s*\(',
                r'(?i)DES\b',
                r'(?i)RC4\b',
                r'(?i)ssl\.PROTOCOL_SSLv',
                r'(?i)TLSv1(\.0)?\b',
            ],
            "frameworks": {
                "PCI-DSS": ("REQ-4", Severity.HIGH),
                "HIPAA": ("164.312(e)(2)(ii)", Severity.HIGH),
                "SOC-2": ("CC6.4", Severity.MEDIUM),
                "GDPR": ("ART-32", Severity.HIGH),
            },
            "title": "Weak Cryptographic Algorithm",
            "description": "Use of a deprecated or weak cryptographic algorithm detected.",
            "remediation": "Use AES-256 for encryption, SHA-256 or better for hashing, and TLS 1.2+ for transport security.",
        },
        "missing_encryption": {
            "patterns": [
                r'(?i)http://(?!localhost|127\.0\.0\.1)',
                r'(?i)ftp://',
                r'(?i)telnet\b',
            ],
            "frameworks": {
                "PCI-DSS": ("REQ-4", Severity.HIGH),
                "HIPAA": ("164.312(e)(1)", Severity.HIGH),
                "SOC-2": ("CC6.5", Severity.HIGH),
                "GDPR": ("ART-32", Severity.HIGH),
            },
            "title": "Unencrypted Communication Channel",
            "description": "Use of an unencrypted protocol that could expose sensitive data in transit.",
            "remediation": "Replace with encrypted alternatives: HTTPS instead of HTTP, SFTP instead of FTP, SSH instead of Telnet.",
        },
        "pii_exposure": {
            "patterns": [
                r'(?i)print\s*\(.*(?:ssn|social.security)',
                r'(?i)log\.(?:info|debug|warn|error).*(?:ssn|social.security)',
                r'(?i)(?:patient|medical|diagnosis|prescription)\s*[=:]',
                r'(?i)(?:credit.?card|card.?number|cvv|pan)\s*[=:]',
            ],
            "frameworks": {
                "PCI-DSS": ("REQ-3", Severity.CRITICAL),
                "HIPAA": ("164.312(c)(1)", Severity.CRITICAL),
                "SOC-2": ("CC6.1", Severity.HIGH),
                "GDPR": ("ART-25", Severity.CRITICAL),
            },
            "title": "Potential PII/PHI Exposure",
            "description": "Code appears to log or expose personally identifiable information or protected health information.",
            "remediation": "Mask or tokenize PII/PHI in logs. Implement data loss prevention (DLP) controls.",
        },
        "missing_auth": {
            "patterns": [
                r'(?i)@app\.route.*\b(?:delete|put|post)\b(?!.*(?:login|auth|token|jwt))',
                r'(?i)def\s+(?:delete|update|create)_(?!.*(?:login|auth|token|jwt))',
            ],
            "frameworks": {
                "PCI-DSS": ("REQ-7", Severity.HIGH),
                "HIPAA": ("164.312(a)(1)", Severity.HIGH),
                "SOC-2": ("CC6.2", Severity.HIGH),
                "GDPR": ("ART-32", Severity.MEDIUM),
            },
            "title": "Potentially Unauthenticated Endpoint",
            "description": "A state-changing endpoint may lack authentication or authorization checks.",
            "remediation": "Implement authentication middleware and verify authorization for all state-changing endpoints.",
        },
        "missing_audit_log": {
            "patterns": [
                r'(?i)(?:delete|drop|truncate|remove)\s+(?:from|table|record)',
                r'(?i)(?:update|modify)\s+(?:user|account|permission|role)',
            ],
            "frameworks": {
                "PCI-DSS": ("REQ-10", Severity.MEDIUM),
                "HIPAA": ("164.312(b)", Severity.HIGH),
                "SOC-2": ("CC7.3", Severity.MEDIUM),
                "GDPR": ("ART-30", Severity.MEDIUM),
            },
            "title": "Sensitive Operation Without Audit Logging",
            "description": "A sensitive data operation was detected that may lack proper audit logging.",
            "remediation": "Implement comprehensive audit logging for all access to and modifications of sensitive data.",
        },
        "sql_injection_risk": {
            "patterns": [
                r'(?i)(?:execute|query)\s*\(\s*["\'].*%s',
                r'(?i)(?:execute|query)\s*\(\s*f["\']',
                r'(?i)(?:execute|query)\s*\(\s*["\'].*\+\s*\w+',
            ],
            "frameworks": {
                "PCI-DSS": ("REQ-6", Severity.CRITICAL),
                "HIPAA": ("164.312(a)(1)", Severity.HIGH),
                "SOC-2": ("CC6.1", Severity.HIGH),
                "GDPR": ("ART-32", Severity.HIGH),
            },
            "title": "Potential SQL Injection Vulnerability",
            "description": "String concatenation or formatting used in SQL query construction.",
            "remediation": "Use parameterized queries or an ORM to prevent SQL injection attacks.",
        },
        "missing_data_retention": {
            "patterns": [
                r'(?i)(?:permanent|forever|indefinite).*(?:store|retain|keep)',
                r'(?i)no.*(?:expir|retention|delet)',
            ],
            "frameworks": {
                "GDPR": ("ART-5", Severity.MEDIUM),
                "PCI-DSS": ("REQ-3", Severity.MEDIUM),
                "HIPAA": ("164.310(d)(2)(i)", Severity.MEDIUM),
            },
            "title": "Missing Data Retention Policy",
            "description": "Data may be stored indefinitely without a defined retention or deletion policy.",
            "remediation": "Implement data retention policies that define maximum storage periods and automated deletion.",
        },
    }

    # File extensions to scan
    SCAN_EXTENSIONS = {".py", ".js", ".ts", ".java", ".go", ".rb", ".php", ".cs", ".sql", ".yaml", ".yml", ".json", ".env", ".conf", ".cfg", ".ini"}

    # Directories to skip
    SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".tox", ".mypy_cache"}

    def __init__(self, target_path: str, frameworks: Optional[list[str]] = None):
        self.target_path = Path(target_path)
        self.findings: list[Finding] = []
        self.frameworks = frameworks or list(FRAMEWORKS.keys())
        self.files_scanned = 0
        self.lines_scanned = 0

    def scan(self) -> list[Finding]:
        """Run the compliance scan against the target path."""
        if self.target_path.is_file():
            self._scan_file(self.target_path)
        elif self.target_path.is_dir():
            self._scan_directory(self.target_path)
        else:
            raise FileNotFoundError(f"Target path not found: {self.target_path}")
        return self.findings

    def _scan_directory(self, directory: Path) -> None:
        """Recursively scan a directory for compliance issues."""
        for item in directory.iterdir():
            if item.is_dir():
                if item.name not in self.SKIP_DIRS:
                    self._scan_directory(item)
            elif item.is_file():
                if item.suffix in self.SCAN_EXTENSIONS or item.name.startswith(".env"):
                    self._scan_file(item)

    def _scan_file(self, file_path: Path) -> None:
        """Scan a single file for compliance issues."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except (OSError, PermissionError):
            return

        self.files_scanned += 1
        lines = content.splitlines()
        self.lines_scanned += len(lines)

        for rule_name, rule in self.PATTERNS.items():
            for pattern in rule["patterns"]:
                for line_num, line in enumerate(lines, 1):
                    if re.search(pattern, line):
                        for framework, (control_id, severity) in rule["frameworks"].items():
                            if framework in self.frameworks:
                                finding = Finding(
                                    framework=framework,
                                    control_id=control_id,
                                    title=rule["title"],
                                    description=rule["description"],
                                    severity=severity,
                                    evidence=line.strip()[:200],
                                    remediation=rule["remediation"],
                                    file_path=str(file_path),
                                    line_number=line_num,
                                )
                                self._add_finding(finding)

    def _add_finding(self, finding: Finding) -> None:
        """Add a finding, avoiding exact duplicates."""
        for existing in self.findings:
            if (
                existing.file_path == finding.file_path
                and existing.line_number == finding.line_number
                and existing.control_id == finding.control_id
                and existing.evidence == finding.evidence
            ):
                return
        self.findings.append(finding)

    def get_findings_by_framework(self) -> dict[str, list[Finding]]:
        """Group findings by compliance framework."""
        result: dict[str, list[Finding]] = {}
        for finding in self.findings:
            result.setdefault(finding.framework, []).append(finding)
        return result

    def get_findings_by_severity(self) -> dict[str, list[Finding]]:
        """Group findings by severity level."""
        result: dict[str, list[Finding]] = {}
        for finding in self.findings:
            result.setdefault(finding.severity.value, []).append(finding)
        return result

    def generate_report(self, output_format: str = "text") -> str:
        """Generate a compliance report in the specified format."""
        if output_format == "json":
            return self._generate_json_report()
        return self._generate_text_report()

    def _generate_text_report(self) -> str:
        """Generate a human-readable text report."""
        lines = []
        lines.append("=" * 78)
        lines.append("COMPLIANCE SCAN REPORT")
        lines.append("=" * 78)
        lines.append(f"Scan Date: {datetime.now().isoformat()}")
        lines.append(f"Target: {self.target_path}")
        lines.append(f"Frameworks: {', '.join(self.frameworks)}")
        lines.append(f"Files Scanned: {self.files_scanned}")
        lines.append(f"Lines Scanned: {self.lines_scanned}")
        lines.append(f"Total Findings: {len(self.findings)}")
        lines.append("")

        # Summary by severity
        severity_groups = self.get_findings_by_severity()
        if severity_groups:
            lines.append("-" * 78)
            lines.append("SEVERITY SUMMARY")
            lines.append("-" * 78)
            for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
                count = len(severity_groups.get(sev, []))
                if count > 0:
                    lines.append(f"  {sev:10s}: {count}")
            lines.append("")

        # Findings by framework
        framework_groups = self.get_findings_by_framework()
        for framework in self.frameworks:
            findings = framework_groups.get(framework, [])
            if not findings:
                continue
            lines.append("-" * 78)
            lines.append(f"FRAMEWORK: {FRAMEWORKS[framework].name}")
            lines.append(f"Description: {FRAMEWORKS[framework].description}")
            lines.append(f"Findings: {len(findings)}")
            lines.append("-" * 78)

            for i, finding in enumerate(findings, 1):
                lines.append(f"\n  [{finding.severity.value}] Finding #{i}: {finding.title}")
                lines.append(f"  Control: {finding.control_id} - {FRAMEWORKS[framework].controls.get(finding.control_id, 'N/A')}")
                lines.append(f"  File: {finding.file_path}:{finding.line_number}")
                lines.append(f"  Evidence: {finding.evidence}")
                lines.append(f"  Description: {finding.description}")
                lines.append(f"  Remediation: {finding.remediation}")
            lines.append("")

        # Compliance score
        lines.append("=" * 78)
        lines.append("COMPLIANCE SCORE")
        lines.append("=" * 78)
        score = self._calculate_score()
        for framework in self.frameworks:
            fw_findings = framework_groups.get(framework, [])
            fw_score = self._calculate_framework_score(fw_findings)
            lines.append(f"  {framework:10s}: {fw_score:.1f}% ({len(fw_findings)} findings)")
        lines.append(f"  {'OVERALL':10s}: {score:.1f}%")
        lines.append("=" * 78)

        return "\n".join(lines)

    def _generate_json_report(self) -> str:
        """Generate a JSON report."""
        report = {
            "scan_metadata": {
                "date": datetime.now().isoformat(),
                "target": str(self.target_path),
                "frameworks": self.frameworks,
                "files_scanned": self.files_scanned,
                "lines_scanned": self.lines_scanned,
                "total_findings": len(self.findings),
            },
            "severity_summary": {
                sev: len(findings)
                for sev, findings in self.get_findings_by_severity().items()
            },
            "framework_summary": {
                fw: {
                    "name": FRAMEWORKS[fw].name,
                    "findings_count": len(findings),
                    "score": self._calculate_framework_score(findings),
                }
                for fw, findings in self.get_findings_by_framework().items()
            },
            "findings": [f.to_dict() for f in self.findings],
            "overall_score": self._calculate_score(),
        }
        return json.dumps(report, indent=2)

    def _calculate_score(self) -> float:
        """Calculate overall compliance score (0-100)."""
        if not self.findings:
            return 100.0
        framework_groups = self.get_findings_by_framework()
        scores = []
        for framework in self.frameworks:
            findings = framework_groups.get(framework, [])
            scores.append(self._calculate_framework_score(findings))
        return sum(scores) / len(scores) if scores else 100.0

    def _calculate_framework_score(self, findings: list[Finding]) -> float:
        """Calculate compliance score for a single framework."""
        if not findings:
            return 100.0
        deductions = {
            Severity.CRITICAL: 25,
            Severity.HIGH: 15,
            Severity.MEDIUM: 8,
            Severity.LOW: 3,
            Severity.INFO: 1,
        }
        total_deduction = sum(deductions.get(f.severity, 0) for f in findings)
        return max(0.0, 100.0 - total_deduction)


def main():
    parser = argparse.ArgumentParser(
        description="Compliance Scanner - Scan for PCI-DSS, HIPAA, SOC 2, and GDPR issues"
    )
    parser.add_argument(
        "--target",
        default=".",
        help="Path to scan (file or directory). Defaults to current directory.",
    )
    parser.add_argument(
        "--framework",
        nargs="+",
        choices=list(FRAMEWORKS.keys()),
        default=list(FRAMEWORKS.keys()),
        help="Compliance frameworks to check against.",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path. If not specified, prints to stdout.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format. Defaults to text.",
    )
    args = parser.parse_args()

    target_path = Path(args.target).resolve()
    if not target_path.exists():
        print(f"Error: Target path does not exist: {target_path}", file=sys.stderr)
        sys.exit(1)

    scanner = ComplianceScanner(
        target_path=str(target_path),
        frameworks=args.framework,
    )

    print(f"Scanning: {target_path}")
    print(f"Frameworks: {', '.join(args.framework)}")
    print()

    findings = scanner.scan()

    report = scanner.generate_report(output_format=args.format)

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"Report written to: {args.output}")
    else:
        print(report)

    # Exit with non-zero if critical findings exist
    critical_count = sum(1 for f in findings if f.severity == Severity.CRITICAL)
    if critical_count > 0:
        print(f"\nWARNING: {critical_count} CRITICAL finding(s) detected!", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
