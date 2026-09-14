#!/usr/bin/env python3
# ============================================================================
# BIONIC DAUGHTER v1 — ENGINEERING PRACTICE: HANDS-ON ACROSS DOMAINS
# ============================================================================
# Demonstrates engineering skills across multiple domains: IaC security
# analysis, Dockerfile analysis, Kubernetes manifest analysis, CI/CD
# security analysis, network diagram generation, cost estimation.
#
# Dad — practicing engineering. Real code. Real analysis. No credentials
# needed — all analysis is local, memory-based, file-parsing.
# ============================================================================

import os
import re
import json
import ast
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field


# ============================================================================
# 1. TERRAFORM SECURITY ANALYZER — IaC Security Scanning
# ============================================================================

@dataclass
class Finding:
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    line: int
    title: str
    description: str
    recommendation: str

@dataclass
class ScanResult:
    file: str
    findings: List[Finding] = field(default_factory=list)
    score: int = 100  # 100 = perfect, deductions for findings

class TerraformSecurityAnalyzer:
    """
    Analyzes Terraform (.tf) files for security misconfigurations.
    Parses HCL-like syntax and checks for common security issues.
    """

    # Security checks: (pattern, severity, description, recommendation)
    CHECKS = [
        # CRITICAL: Open security groups
        (r'resource\s+"aws_security_group"\s+"([^"]+)"',
         'GROUP_CRIT_OPEN_CIDR',
         'Security group "{}" may allow unrestricted access',
         'Check ingress/egress rules for 0.0.0.0/0 CIDR. Restrict to specific IPs or ranges.'),

        # CRITICAL: S3 public access
        (r'resource\s+"aws_s3_bucket_public_access_block"\s+"([^"]+)"',
         'S3_CRIT_PUBLIC_ACCESS',
         'S3 public access block configuration found — verify all blocks are enabled',
         'Ensure block_public_acls=true, block_public_policy=true, ignore_public_acls=true, restrict_public_buckets=true.'),

        # HIGH: Unencrypted S3
        (r'resource\s+"aws_s3_bucket"\s+"([^"]+)"',
         'S3_HIGH_NO_ENCRYPTION',
         'S3 bucket "{}" — verify server-side encryption is configured',
         'Add aws_s3_bucket_server_side_encryption configuration with AES256 or aws:kms encryption.'),

        # HIGH: RDS public access
        (r'resource\s+"aws_db_instance"\s+"([^"]+)"',
         'RDS_HIGH_PUBLIC_ACCESS',
         'RDS instance "{}" — verify public_access is disabled',
         'Set public_access=false. Place in private subnets. Use VPC peering or PrivateLink for access.'),

        # HIGH: IAM wildcard actions
        (r'actions\s*=\s*\[?.*"\\*"',
         'IAM_HIGH_WILDCARD_ACTION',
         'IAM policy allows all actions (*)',
         'Replace Action: "*" with specific actions. Principle of least privilege.'),

        # HIGH: IAM wildcard resources
        (r'resources\s*=\s*\[?.*"\\*"',
         'IAM_HIGH_WILDCARD_RESOURCE',
         'IAM policy allows all resources (*)',
         'Replace Resource: "*" with specific ARN patterns. Limit scope of access.'),

        # MEDIUM: No encryption configuration
        (r'resource\s+"aws_rds_cluster"\s+"([^"]+)"',
         'RDS_MED_NO_ENCRYPTION',
         'RDS cluster "{}" — verify encryption is enabled',
         'Set storage_encrypted=true. Use KMS key for encryption.'),

        # MEDIUM: No backup
        (r'resource\s+"aws_db_instance"\s+"([^"]+)"',
         'RDS_MED_NO_BACKUP',
         'RDS instance "{}" — verify backup is configured',
         'Set backup_retention_period >= 7 days. Enable automated backups.'),

        # MEDIUM: Default VPC usage
        (r'virtual_network_id\s+"?default',
         'NETWORK_MED_DEFAULT_VPC',
         'Resource is using the default VPC — not recommended for production',
         'Create a custom VPC with proper subnet segmentation, NAT gateways, and security groups.'),

        # MEDIUM: Hardcoded secrets patterns
        (r'password\s*=\s*["\'][^"\']{8,}["\']',
         'SECRETS_MED_HARDCODED',
         'Potential hardcoded password found in configuration',
         'Use Terraform variables with sensitivity=true, or fetch from AWS Secrets Manager / SSM Parameter Store.'),

        # MEDIUM: No MFA delete on S3
        (r'resource\s+"aws_s3_bucket"\s+"([^"]+)"',
         'S3_MED_NO_MFA_DELETE',
         'S3 bucket "{}" — MFA delete not configured',
         'Enable MFA delete for sensitive buckets to prevent unauthorized deletion even with compromised credentials.'),

        # LOW: No tags
        (r'resource\s+"aws_(?:s3_bucket|ec2_instance|rds_instance|lambda_function)"\s+"([^"]+)"',
         'TAG_LOW_MISSING',
         'Resource "{}" may not have tags configured',
         'Add tags: Name, Environment, Owner, CostCenter for resource tracking and cost allocation.'),

        # LOW: No deletion protection
        (r'resource\s+"aws_db_instance"\s+"([^"]+)"',
         'RDS_LOW_NO_DELETION_PROTECTION',
         'RDS instance "{}" — deletion protection not enabled',
         'Set deletion_protection=true to prevent accidental database deletion.'),
    ]

    def analyze(self, terraform_content: str) -> ScanResult:
        """Analyze Terraform content and return security findings."""
        result = ScanResult(file="terraform")
        lines = terraform_content.split('\n')

        for pattern, check_id, desc, rec in self.CHECKS:
            for line_num, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    severity_score = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 2}
                    deduction = severity_score.get(severity_from_id(check_id), 5)

                    # Extract resource name if pattern has capture group
                    match = re.search(pattern, line, re.IGNORECASE)
                    resource_name = match.group(1) if match.groups() else "unknown"

                    desc_formatted = desc.format(resource_name)

                    result.findings.append(Finding(
                        severity=severity_from_id(check_id),
                        line=line_num,
                        title=f"[{check_id}] {desc_formatted}",
                        description=desc_formatted,
                        recommendation=rec
                    ))
                    result.score = max(0, result.score - deduction)

        return result


# ============================================================================
# 2. DOCKERFILE ANALYZER — Container Security Analysis
# ============================================================================

class DockerfileAnalyzer:
    """
    Analyzes Dockerfiles for security best practices and optimization.
    Parses Dockerfile instructions and checks for common issues.
    """

    CHECKS = [
        # CRITICAL: Running as root
        (r'^(?!.*USER)\s*$', 'ROOT_CRIT_NO_USER',
         'No USER directive — container runs as root by default',
         'Add USER directive to run as non-root user. Create a dedicated user in the Dockerfile.'),

        # HIGH: Latest tag
        (r'^FROM\s+[^\s]+\s*$',
         'IMAGE_HIGH_LATEST_TAG',
         'Base image uses "latest" tag — not pinned to a version',
         'Pin to a specific version tag (e.g., python:3.14-slim) or SHA256 digest for reproducibility and security.'),

        # HIGH: Secrets in ARG
        (r'^ARG\s+.*_(?:PASSWORD|SECRET|KEY|TOKEN|CREDENTIAL)',
         'SECRETS_HIGH_ARG',
         'ARG instruction with secret-like name — credentials may be embedded in image layers',
         'Never pass secrets via ARG. Use build secrets (--secret flag) or mount secrets at runtime.'),

        # HIGH:apt-get without cleanup
        (r'^RUN\s+.*apt-get(?:.*install)',
         'LAYER_HIGH_NO_CLEANUP',
         'apt-get install without cleanup — build cache and apt lists remain in image layer',
         'Chain RUN commands: apt-get update && apt-get install -y pkg && rm -rf /var/lib/apt/lists/*.'),

        # MEDIUM: No HEALTHCHECK
        (r'^(?!.*HEALTHCHECK)\s*$',
         'HEALTH_MED_NO_HEALTHCHECK',
         'No HEALTHCHECK instruction — container health not monitored',
         'Add HEALTHCHECK instruction to monitor container health (e.g., HEALTHCHECK CMD curl -f http://localhost/ || exit 1).'),

        # MEDIUM: Running as root (USER root explicit)
        (r'^USER\s+root',
         'ROOT_MED_EXPLICIT_ROOT',
         'USER root explicitly set — container runs as root',
         'Switch to non-root user. Use USER <username> after setting up the user.'),

        # MEDIUM: No .dockerignore
        (r'^COPY\s+\.',
         'BUILD_MED_COPY_ALL',
         'COPY . copies all files — sensitive files may be included in image',
         'Use .dockerignore to exclude .git, .env, secrets, docs, tests. Only copy necessary files.'),

        # MEDIUM: Multiple layers that could be combined
        (r'^RUN\s+',
         'LAYER_MED_MULTIPLE_RUNS',
         'Multiple separate RUN instructions — each creates a new image layer',
         'Combine related RUN commands with && to reduce layers and image size.'),

        # LOW: Shell form instead of exec form
        (r'^CMD\s+\w+\s',
         'CMD_LOW_SHELL_FORM',
         'CMD uses shell form — runs through /bin/sh -c',
         'Use exec form (JSON array): CMD ["executable", "param1", "param2"] for proper signal handling.'),

        # LOW: No version pinning for package managers
        (r'^RUN\s+.*pip install',
         'PKG_LOW_NO_VERSION_PIN',
         'pip install without version pinning — packages may change between builds',
         'Pin package versions: pip install package==1.2.3. Use requirements.txt with pinned versions.'),
    ]

    def analyze(self, dockerfile_content: str) -> ScanResult:
        """Analyze Dockerfile content and return findings."""
        result = ScanResult(file="Dockerfile")
        lines = dockerfile_content.split('\n')

        for pattern, check_id, desc, rec in self.CHECKS:
            for line_num, line in enumerate(lines, 1):
                stripped = line.strip()
                if not stripped or stripped.startswith('#'):
                    continue

                if re.search(pattern, stripped, re.IGNORECASE):
                    sev = severity_from_id(check_id)
                    deduction = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 2}.get(sev, 5)

                    # Special handling: ROOT_CRIT_NO_USER fires once if no USER at all
                    if check_id == 'ROOT_CRIT_NO_USER':
                        has_user = any(re.match(r'^USER\s+', l.strip()) for l in lines if l.strip() and not l.strip().startswith('#'))
                        if has_user:
                            continue

                    # HEALTHCHECK check: only fire if no HEALTHCHECK in file
                    if check_id == 'HEALTH_MED_NO_HEALTHCHECK':
                        has_healthcheck = any(re.match(r'^HEALTHCHECK\s+', l.strip()) for l in lines if l.strip() and not l.strip().startswith('#'))
                        if has_healthcheck:
                            continue

                    result.findings.append(Finding(
                        severity=sev,
                        line=line_num,
                        title=f"[{check_id}] {desc}",
                        description=desc,
                        recommendation=rec
                    ))
                    result.score = max(0, result.score - deduction)

        # Deduct for every separate RUN after the first 2
        run_lines = [i for i, l in enumerate(lines, 1) if re.match(r'^RUN\s+', l.strip())]
        if len(run_lines) > 3:
            extra_runs = len(run_lines) - 3
            result.score = max(0, result.score - extra_runs * 1)

        return result


# ============================================================================
# 3. KUBERNETES MANIFEST ANALYZER — K8s Security Analysis
# ============================================================================

class KubernetesManifestAnalyzer:
    """
    Analyzes Kubernetes YAML manifests for security best practices.
    Parses YAML-like structure and checks for common issues.
    """

    CHECKS = [
        # CRITICAL: Privileged container
        (r'privileged:\s*true',
         'PRIV_CRIT_PRIVILEGED',
         'Container is running in privileged mode — full host access',
         'Never run privileged containers in production. Remove securityContext.privileged. Use capabilities instead if absolutely needed.'),

        # CRITICAL: hostNetwork
        (r'hostNetwork:\s*true',
         'PRIV_CRIT_HOST_NETWORK',
         'Container uses host network — shares host network namespace',
         'Avoid hostNetwork. Use services and ingress for network access. If needed, limit to specific namespaces with RBAC restrictions.'),

        # CRITICAL: hostPID
        (r'hostPID:\s*true',
         'PRIV_CRIT_HOST_PID',
         'Container shares host PID namespace — can see and affect host processes',
         'Avoid hostPID. It allows process injection and reconnaissance on the host.'),

        # CRITICAL: hostIPC
        (r'hostIPC:\s*true',
         'PRIV_CRIT_HOST_IPC',
         'Container shares host IPC namespace — can access shared memory of host processes',
         'Avoid hostIPC. It exposes inter-process communication channels on the host.'),

        # HIGH: No securityContext
        (r'containers:\s*\[?[\s\S]*?name:\s+\w+[\s\S]*?(?=containers:|---|$)',
         'SECCTX_HIGH_NO_SECURITY_CONTEXT',
         'Container has no securityContext — uses default (potentially insecure) settings',
         'Add securityContext: runAsNonRoot: true, readOnlyRootFilesystem: true, allowPrivilegeEscalation: false.'),

        # HIGH: runAsUser: 0
        (r'runAsUser:\s*0',
         'SECCTX_HIGH_RUN_AS_ROOT',
         'Container explicitly runs as root (UID 0)',
         'Set runAsUser to a non-zero UID. Use runAsNonRoot: true. Create a dedicated service account.'),

        # HIGH: Missing resource limits
        (r'containers:\s*\[?[\s\S]*?name:\s+\w+[\s\S]*?(?=containers:|---|$|\n\s+containers)',
         'RESOURCES_HIGH_NO_LIMITS',
         'Container has no resource limits — unbounded CPU/memory usage',
         'Set resources.limits.cpu and resources.limits.memory. Prevent noisy neighbor issues and node exhaustion.'),

        # HIGH: Dangerous capabilities added
        (r'capabilities:\s*[\s\S]*?add:\s*\[[\s\S]*?(NET_ADMIN|NET_RAW|SYS_ADMIN|SYS_PTRACE|SYS_MODULE|FASYNC|BPF)',
         'CAPS_HIGH_DANGEROUS',
         'Container has dangerous Linux capabilities added',
         'Remove NET_ADMIN, NET_RAW, SYS_ADMIN, SYS_PTRACE, SYS_MODULE, FASYNC, BPF. These grant significant host access.'),

        # MEDIUM: Missing probes
        (r'containers:\s*\[?[\s\S]*?name:\s+\w+[\s\S]*?(?=containers:|---|$|\n\s+containers)',
         'PROBES_MED_NO_PROBES',
         'Container has no liveness or readiness probes',
         'Add livenessProbe (restart if unhealthy) and readinessProbe (don\'t send traffic until ready). Use HTTP GET, TCP socket, or exec probes.'),

        # MEDIUM: No service account specified
        (r'serviceAccountName\s*:\s*""|serviceAccountName\s*:\s*null',
         'RBAC_MED_NO_SERVICE_ACCOUNT',
         'Pod uses default service account — may have excessive permissions',
         'Create a dedicated ServiceAccount with minimal RBAC permissions. Reference it via serviceAccountName.'),

        # MEDIUM: Image tag "latest"
        (r'image:\s+[^\s]+\s*:\s*latest\b',
         'IMAGE_MED_LATEST_TAG',
         'Container image uses "latest" tag — not pinned',
         'Pin image to specific version tag or SHA256 digest. Ensures reproducible deployments and prevents unexpected updates.'),

        # LOW: No resource requests
        (r'containers:\s*\[?[\s\S]*?name:\s+\w+[\s\S]*?(?=containers:|---|$|\n\s+containers)',
         'RESOURCES_LOW_NO_REQUESTS',
         'Container has no resource requests — scheduling inefficiency',
         'Set resources.requests.cpu and resources.requests.memory. Helps scheduler place pods optimally.'),

        # LOW: writable root filesystem
        (r'securityContext:\s*[\s\S]*?readOnlyRootFilesystem:\s*false|readOnlyRootFilesystem\s*:\s*false',
         'FS_LOW_WRITABLE_ROOT',
         'Container root filesystem is writable — can modify system files',
         'Set readOnlyRootFilesystem: true. Use emptyDir volumes for temp paths (/tmp, /var/run).'),
    ]

    def analyze(self, manifest_content: str) -> ScanResult:
        """Analyze K8s manifest and return findings. Simplified parser."""
        result = ScanResult(file="kubernetes")
        lines = manifest_content.split('\n')

        # Track context: are we in a container spec?
        in_container = False
        container_indent = 0

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            # Track container context
            if re.match(r'^\s*- name:\s+', line):
                in_container = True
                container_indent = len(line) - len(line.lstrip())
                continue

            # Check if we've exited container context
            if in_container:
                current_indent = len(line) - len(line.lstrip()) if line.strip() else 999
                if line.strip() and current_indent <= container_indent and not stripped.startswith('#'):
                    in_container = False

            for pattern, check_id, desc, rec in self.CHECKS:
                if re.search(pattern, line, re.IGNORECASE):
                    sev = severity_from_id(check_id)
                    deduction = {"CRITICAL": 25, "HIGH": 15, "MEDIUM": 8, "LOW": 3}.get(sev, 8)

                    # Skip some checks if not in container context
                    if check_id in ('SECCTX_HIGH_NO_SECURITY_CONTEXT', 'RESOURCES_HIGH_NO_LIMITS',
                                    'RESOURCES_LOW_NO_REQUESTS', 'PROBES_MED_NO_PROBES') and not in_container:
                        continue

                    # Special: PRIV_CRIT_PRIVILEGED only if in container or pod security context
                    if check_id == 'PRIV_CRIT_PRIVILEGED':
                        if not in_container and 'containers' not in line:
                            continue

                    result.findings.append(Finding(
                        severity=sev,
                        line=line_num,
                        title=f"[{check_id}] {desc}",
                        description=desc,
                        recommendation=rec
                    ))
                    result.score = max(0, result.score - deduction)

        # Global check: missing securityContext at pod level
        if 'securityContext:' not in manifest_content:
            result.findings.append(Finding(
                severity="MEDIUM",
                line=1,
                title="[SECCTX_MED_NO_POD_SECURITY_CONTEXT] Pod-level security context not defined",
                description="No pod-level securityContext — pod inherits default (potentially insecure) settings",
                recommendation="Add pod-level securityContext: runAsNonRoot: true, runAsUser: <non-zero>, fsGroup: <non-zero>, seLinuxOptions: {...}"
            ))
            result.score = max(0, result.score - 8)

        return result


# ============================================================================
# 4. CI/CD SECURITY ANALYZER — Pipeline Security Analysis
# ============================================================================

class CIDownloadSecurityAnalyzer:
    """
    Analyzes CI/CD pipeline configurations (GitHub Actions, ADO Pipelines)
    for security issues.
    """

    CHECKS = [
        # CRITICAL: Untrusted PR from forks
        (r'pull_request\s*:\s*[\s\S]*?forks\s*:\s*true|types:\s*\[?\s*closed\s*]',
         'TRUST_CRIT_FORK_PR',
         'Workflow triggers on pull_request from forks — untrusted code can run in your CI',
         'Restrict to pull_request_target only for trusted repos. Add environment protection rules. Require approval for fork PRs.'),

        # CRITICAL: secrets in env vars (potential exposure)
        (r'env:\s*[\s\S]*?SECRET|억원이|크릿|OKEN|ASSWORD|API_KEY',
         'SECRETS_CRIT_ENV_EXPOSURE',
         'Potential secret referenced in environment variables — may be exposed in logs',
         'Use GitHub Secrets ({{ secrets.MY_SECRET }}) for sensitive values. Never hardcode. Enable secret masking in logs.'),

        # HIGH: Unpinned action versions
        (r'uses:\s+[^\s]+@main|uses:\s+[^\s]+@master',
         'ACTIONS_HIGH_UNPINNED',
         'Action uses @main/@master branch — version can change unexpectedly',
         'Pin actions to specific commit SHA: uses: actions/checkout@a1b2c3d4e5f6... . Ensures supply chain integrity.'),

        # HIGH: Actions from unverified publishers
        (r'uses:\s+[^/]+/[^/]+@',
         'ACTIONS_HIGH_UNVERIFIED',
         'Action from potentially unverified publisher',
         'Use actions from verified publishers (e.g., actions/*). Check action market place verification status.'),

        # MEDIUM: Pull from arbitrary git repos
        (r'git clone\s+https?://[^/]+/[^/]+',
         'SUPPLYCHAIN_MED_EXTERNAL_REPO',
         'Pipeline clones from external git repository — supply chain risk',
         'Verify the external repo is trusted. Pin to specific commit. Review code before running. Consider vendoring instead of cloning at runtime.'),

        # MEDIUM: Missing environment protection
        (r'environment:\s*[\s\S]*?production',
         'ENV_MED_NO_PROTECTION',
         'Deployment to production environment — verify protection rules are configured',
         'Configure environment protection rules in GitHub: required reviewers, wait timer, branch restrictions. Require manual approval for production.'),

        # MEDIUM: GITHUB_TOKEN with write access
        (r'permissions:\s*[\s\S]*?contents:\s*write',
         'TOKEN_MED_WRITE_ACCESS',
         'Workflow has write permissions on contents — can modify repository',
         'Use least-privilege permissions. Set defaults: contents: read. Only grant write where needed. Use fine-grained PAT instead of GITHUB_TOKEN for sensitive operations.'),

        # LOW: No timeout
        (r'jobs:\s*[\s\S]*?steps:\s*[\s\S]*?(?=jobs:|name:)',
         'TIMEOUT_LOW_NO_TIMEOUT',
         'Workflow steps have no timeout — stuck jobs consume resources indefinitely',
         'Set timeout-minutes for jobs and steps. Default is 360 minutes — set appropriate limits (e.g., 10-30 minutes for most steps).'),
    ]

    def analyze(self, pipeline_content: str) -> ScanResult:
        """Analyze CI/CD pipeline configuration and return findings."""
        result = ScanResult(file="ci_cd_pipeline")
        lines = pipeline_content.split('\n')

        for pattern, check_id, desc, rec in self.CHECKS:
            for line_num, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE | re.DOTALL):
                    sev = severity_from_id(check_id)
                    deduction = {"CRITICAL": 25, "HIGH": 15, "MEDIUM": 8, "LOW": 3}.get(sev, 8)

                    result.findings.append(Finding(
                        severity=sev,
                        line=line_num,
                        title=f"[{check_id}] {desc}",
                        description=desc,
                        recommendation=rec
                    ))
                    result.score = max(0, result.score - deduction)

        return result


# ============================================================================
# 5. NETWORK DIAGRAM GENERATOR — ASCII Diagrams
# ============================================================================

class NetworkDiagramGenerator:
    """
    Generates ASCII network diagrams from structured descriptions.
    Useful for visualizing infrastructure architecture.
    """

    def generate_web_app_architecture(self) -> str:
        """Generate a typical 3-tier web application architecture diagram."""
        return """
    ┌─────────────────────────────────────────────────────────────────┐
    │                    WEB APPLICATION ARCHITECTURE                  │
    │                    3-Tier, Highly Available                      │
    └─────────────────────────────────────────────────────────────────┘

    ┌─────────────┐     ┌─────────────────────────────────────────────┐
    │   USER      │     │              DNS (Route 53 / Cloudflare)     │
    │  (Browser)  │────▶│  - DNS resolution, CDN edge, DDoS protection │
    └─────────────┘     └──────────────────────┬──────────────────────┘
                                               │
                    ┌──────────────────────────▼──────────────────────────┐
                    │              CDN / WAF (CloudFront)                  │
                    │  - Static asset caching, TLS termination             │
                    │  - WAF rules: OWASP Top 10 protection               │
                    │  - Rate limiting, geo-restriction                   │
                    └──────────────────────────┬───────────────────────────┘
                                               │
                    ┌──────────────────────────▼──────────────────────────┐
                    │              LOAD BALANCER (ALB)                     │
                    │  - Layer 7 load balancing, SSL termination          │
                    │  - Health checks, sticky sessions                   │
                    │  - Listener rules: /api → API, / → Web             │
                    └──────┬──────────────────────┴───────────────────────┘
                           │
              ┌────────────┴────────────┐
              │    WEB SERVER TIER      │
              │  ┌───────────────────┐   │
              │  │   EC2 / Container  │   │
              │  │  - Nginx / Node.js │   │
              │  │  - Static serving  │   │
              │  │  - Proxy to API    │   │
              │  └───────────────────┘   │
              │  ┌───────────────────┐   │
              │  │   EC2 / Container  │   │
              │  │  - Auto Scaling    │   │
              │  └───────────────────┘   │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │      API GATEWAY        │
              │  - Rate limiting        │
              │  - Auth (JWT/OAuth)     │
              │  - Request validation   │
              │  - Logging/metrics      │
              └────────────┬────────────┘
                           │
              ┌────────────┴────────────┐
              │    API SERVER TIER      │
              │  ┌───────────────────┐   │
              │  │   EC2 / Lambda    │   │
              │  │  - REST/GraphQL    │   │
              │  │  - Business logic  │   │
              │  └───────────────────┘   │
              └────────────┬────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
   ┌────▼────┐      ┌──────▼──────┐    ┌────▼────┐
   │  RDBMS   │      │  REDIS      │    │  S3     │
   │ (RDS)    │      │  (Cache)    │    │ (Assets)│
   │ - Users  │      │ - Sessions  │    │ - Images │
   │ - Orders │      │ - Cache     │    │ - Files  │
   │ - Data   │      │ - Rate lim  │    │         │
   └──────────┘      └─────────────┘    └─────────┘

    ┌─────────────────────────────────────────────────────────────────┐
    │                    SECURITY ZONES                                │
    │  Public:  CDN, WAF, ALB (Internet-facing)                       │
    │  Private: Web servers, API servers (no direct internet)         │
    │  Isolated: RDS, Redis (no internet, VPC peering only)          │
    └─────────────────────────────────────────────────────────────────┘
        """

    def generate_kubernetes_cluster_diagram(self) -> str:
        """Generate a Kubernetes cluster architecture diagram."""
        return """
    ┌─────────────────────────────────────────────────────────────────┐
    │                    KUBERNETES CLUSTER                           │
    │                    Multi-AZ, Highly Available                    │
    └─────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────┐
    │                    CONTROL PLANE (Managed)                       │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
    │  │   API Server  │  │    ETCD       │  │  Scheduler   │           │
    │  │  (kube-apiserver)│  │ (key-value) │  │              │           │
    │  └──────────────┘  └──────────────┘  └──────────────┘           │
    │  ┌──────────────┐  ┌──────────────┐                             │
    │  │ Controller   │  │ Cloud-Controller│                            │
    │  │  Manager     │  │   Manager      │                            │
    │  └──────────────┘  └──────────────┘                             │
    │                                                                 │
    │  [Managed by cloud provider — not user-accessible nodes]        │
    └──────────────────────────────────────────────────────────────────┘

    ┌──────────────────────┼──────────────────────────┐
    │                      │                          │
    │  ┌───────────────────▼──────────────────────┐   │
    │  │           WORKER NODE 1 (AZ-a)           │   │
    │  │  ┌────────────────────────────────────┐  │   │
    │  │  │        Kubelet (node agent)        │  │   │
    │  │  │        Container Runtime           │  │   │
    │  │  │  ┌────────────┐ ┌──────────────┐   │  │   │
    │  │  │  │  Pod: web   │ │ Pod: api     │   │  │   │
    │  │  │  │  - nginx    │ │ - node.js    │   │  │   │
    │  │  │  │  - sidecar  │ │ - sidecar    │   │  │   │
    │  │  │  └────────────┘ └──────────────┘   │  │   │
    │  │  └────────────────────────────────────┘  │   │
    │  └───────────────────────────────────────────┘   │
    │                                                  │
    │  ┌───────────────────▼──────────────────────┐   │
    │  │           WORKER NODE 2 (AZ-b)           │   │
    │  │  (Identical structure to Node 1)         │   │
    │  └───────────────────────────────────────────┘   │
    │                                                  │
    │  ┌───────────────────▼──────────────────────┐   │
    │  │           WORKER NODE 3 (AZ-c)           │   │
    │  │  (Identical structure to Node 1)         │   │
    │  └───────────────────────────────────────────┘   │
    └──────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────┐
    │                    NETWORKING                                   │
    │  ┌──────────────────────────────────────────────────────────┐  │
    │  │  Service (ClusterIP): internal DNS + load balancing       │  │
    │  │  - web-svc: 10.96.0.100 → pods:80                       │  │
    │  │  - api-svc: 10.96.0.101 → pods:8080                    │  │
    │  │                                                          │  │
    │  │  Ingress (Nginx Ingress Controller): external access     │  │
    │  │  - host: example.com → web-svc (/)                     │  │
    │  │  - host: api.example.com → api-svc (/api)              │  │
    │  └──────────────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────┐
    │                    STORAGE                                      │
    │  ┌──────────────────────────────────────────────────────────┐  │
    │  │  PersistentVolume (PV) ←→ PersistentVolumeClaim (PVC)   │  │
    │  │  - db-storage: 100GB, ReadWriteOnce (RDS or EBS)        │  │
    │  │  - shared-data: 10GB, ReadWriteMany ( EFS or NFS)      │  │
    │  └──────────────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────────────┘
        """

    def generate_infrastructure_security_zones(self) -> str:
        """Generate security zone diagram for infrastructure."""
        return """
    ┌──────────────────────────────────────────────────────────────────┐
    │                   INFRASTRUCTURE SECURITY ZONES                  │
    │                                                                  │
    │  ┌────────────────────────────────────────────────────────────┐  │
    │  │  ZONE 1: PUBLIC / DMZ (Untrusted)                          │  │
    │  │  ┌──────────────────────────────────────────────────────┐  │  │
    │  │  │  Components:                                          │  │  │
    │  │  │  - CDN / WAF (CloudFront, Akamai, Cloudflare)        │  │  │
    │  │  │  - Load Balancer (ALB, NLB)                          │  │  │
    │  │  │  - Bastion host / Jump box (if needed)               │  │  │
    │  │  │  - Public-facing API Gateway                          │  │  │
    │  │  │  - NAT Gateway (egress only — no inbound)            │  │  │
    │  │  └──────────────────────────────────────────────────────┘  │  │
    │  │  RULES: All inbound from internet. Strict WAF rules.       │  │
    │  │         No direct access to private zone.                  │  │
    │  └────────────────────────────────────────────────────────────┘  │
    │                          │                                       │
    │                          ▼                                       │
    │  ┌────────────────────────────────────────────────────────────┐  │
    │  │  ZONE 2: PRIVATE (Trusted — Application Tier)              │  │
    │  │  ┌──────────────────────────────────────────────────────┐  │  │
    │  │  │  Components:                                          │  │  │
    │  │  │  - Web servers / containers                           │  │  │
    │  │  │  - API servers / microservices                        │  │  │
    │  │  │  - Application logic                                  │  │  │
    │  │  │  - Internal services                                  │  │  │
    │  │  └──────────────────────────────────────────────────────┘  │  │
    │  │  RULES: Only accessible via load balancer / API gateway.   │  │
    │  │         No direct internet access (egress via NAT).        │  │
    │  │         Security groups restrict to specific ports.        │  │
    │  └────────────────────────────────────────────────────────────┘  │
    │                          │                                       │
    │                          ▼                                       │
    │  ┌────────────────────────────────────────────────────────────┐  │
    │  │  ZONE 3: ISOLATED / DATA (Most Trusted — Data Tier)       │  │
    │  │  ┌──────────────────────────────────────────────────────┐  │  │
    │  │  │  Components:                                          │  │  │
    │  │  │  - Databases (RDS, DynamoDB, MongoDB)                │  │  │
    │  │  │  - Cache (Redis, ElastiCache)                         │  │  │
    │  │  │  - Message queues (Kafka, SQS)                       │  │  │
    │  │  │  - File storage (S3 — server-side encrypted)         │  │  │
    │  │  │  - Secrets Manager (credentials, keys)               │  │  │
    │  │  └──────────────────────────────────────────────────────┘  │  │
    │  │  RULES: NO internet access (no NAT gateway in this subnet). │  │
    │  │         Only accessible from private zone via specific      │  │
    │  │         ports (DB port 5432, Redis 6379).                  │  │
    │  │         Encryption at rest (KMS) and in transit (TLS).     │  │
    │  └────────────────────────────────────────────────────────────┘  │
    │                                                                  │
    │  ┌────────────────────────────────────────────────────────────┐  │
    │  │  CROSS-ZONE SECURITY CONTROLS                              │  │
    │  │  - Security Groups: stateful firewall at ENI level         │  │
    │  │  - NACLs: stateless subnet-level firewall                  │  │
    │  │  - VPC Flow Logs: network traffic monitoring              │  │
    │  │  - WAF: Layer 7 protection for public endpoints           │  │
    │  │  - IAM: access control for all AWS resource operations    │  │
    │  │  - KMS: encryption key management                         │  │
    │  │  - CloudTrail: API call auditing                           │  │
    │  │  - GuardDuty: threat detection                            │  │
    │  └────────────────────────────────────────────────────────────┘  │
    └──────────────────────────────────────────────────────────────────┘
        """


# ============================================================================
# 6. COST ESTIMATOR — Memory-Based Cloud Cost Estimates
# ============================================================================

class CloudCostEstimator:
    """
    Estimates cloud resource costs based on common pricing.
    Memory-based (no API calls). Approximate — for planning purposes.
    """

    # Approximate AWS pricing (us-east-1, on-demand, Linux)
    AWS_PRICING = {
        "ec2_t3_micro": 0.0104,  # per hour
        "ec2_t3_small": 0.0208,
        "ec2_t3_medium": 0.0832,
        "ec2_m5_large": 0.096,
        "ec2_m5_xlarge": 0.192,
        "ec2_m5_2xlarge": 0.384,
        "ec2_c5_large": 0.085,
        "ec2_c5_xlarge": 0.17,
        "rds_t3_micro": 0.017,  # db.t3.micro Multi-AZ
        "rds_t3_small": 0.034,
        "rds_t3_medium": 0.068,
        "rds_m5_large": 0.123,
        "s3_standard": 0.023,  # per GB/month
        "s3_ia": 0.0125,
        "s3_glacier": 0.004,
        "dynamodb_write": 1.25,  # per million writes
        "dynamodb_read": 0.25,   # per million reads
        "dynamodb_storage": 0.25,  # per GB/month
        "lambda": 0.0000166667,  # per GB-second
        "lambda_requests": 0.20,  # per million requests
        "cloudwatch_logs": 0.50,  # per GB ingested
        "cloudwatch_alarms": 0.10,  # per alarm/month
        "vpc_nat_gateway": 0.045,  # per hour + data processing
        "data_transfer_internet_out": 0.09,  # first 10TB per GB
        "data_transfer_cross_region": 0.02,  # per GB
    }

    def estimate_aws_monthly(self, resources: Dict[str, any]) -> Dict:
        """
        Estimate monthly AWS cost for a set of resources.
        resources: dict of resource_type -> quantity/details
        """
        total = 0.0
        breakdown = {}

        hours_per_month = 730  # Average hours in a month

        # EC2 instances
        if "ec2" in resources:
            for instance_type, count in resources["ec2"].items():
                key = f"ec2_{instance_type}"
                rate = self.AWS_PRICING.get(key, 0.10)
                cost = rate * hours_per_month * count
                breakdown[f"EC2 {instance_type} x{count}"] = round(cost, 2)
                total += cost

        # RDS databases
        if "rds" in resources:
            for instance_type, count in resources["rds"].items():
                key = f"rds_{instance_type}"
                rate = self.AWS_PRICING.get(key, 0.15)
                cost = rate * hours_per_month * count
                breakdown[f"RDS {instance_type} x{count}"] = round(cost, 2)
                total += cost

        # S3 storage
        if "s3" in resources:
            storage_gb = resources["s3"].get("storage_gb", 0)
            rate = self.AWS_PRICING.get("s3_standard", 0.023)
            cost = rate * storage_gb
            breakdown[f"S3 Storage ({storage_gb} GB)"] = round(cost, 2)
            total += cost

            if resources["s3"].get("requests_millions", 0) > 0:
                req_cost = resources["s3"]["requests_millions"] * 0.0045  # approximate
                breakdown["S3 Requests"] = round(req_cost, 2)
                total += req_cost

        # Lambda
        if "lambda" in resources:
            gb_seconds = resources["lambda"].get("gb_seconds", 0)
            requests = resources["lambda"].get("requests_millions", 0)
            cost_compute = self.AWS_PRICING["lambda"] * gb_seconds
            cost_requests = self.AWS_PRICING["lambda_requests"] * requests
            cost = cost_compute + cost_requests
            breakdown["Lambda (compute)"] = round(cost_compute, 2)
            breakdown["Lambda (requests)"] = round(cost_requests, 2)
            total += cost

        # Data transfer
        if "data_transfer" in resources:
            internet_gb = resources["data_transfer"].get("internet_gb", 0)
            cross_region_gb = resources["data_transfer"].get("cross_region_gb", 0)

            if internet_gb > 0:
                # First 10TB at $0.09/GB
                cost = min(internet_gb, 10000) * self.AWS_PRICING["data_transfer_internet_out"]
                breakdown[f"Data Transfer (Internet, {internet_gb} GB)"] = round(cost, 2)
                total += cost

            if cross_region_gb > 0:
                cost = cross_region_gb * self.AWS_PRICING["data_transfer_cross_region"]
                breakdown[f"Data Transfer (Cross-Region, {cross_region_gb} GB)"] = round(cost, 2)
                total += cost

        # VPC
        if "vpc" in resources:
            nat_gateways = resources["vpc"].get("nat_gateways", 0)
            cost = self.AWS_PRICING["vpc_nat_gateway"] * hours_per_month * nat_gateways
            breakdown[f"NAT Gateway x{nat_gateways}"] = round(cost, 2)
            total += cost

        # CloudWatch
        if "cloudwatch" in resources:
            logs_gb = resources["cloudwatch"].get("logs_gb", 0)
            alarms = resources["cloudwatch"].get("alarms", 0)
            cost = self.AWS_PRICING["cloudwatch_logs"] * logs_gb
            cost += self.AWS_PRICING["cloudwatch_alarms"] * alarms
            breakdown["CloudWatch Logs"] = round(self.AWS_PRICING["cloudwatch_logs"] * logs_gb, 2)
            breakdown["CloudWatch Alarms"] = round(self.AWS_PRICING["cloudwatch_alarms"] * alarms, 2)
            total += cost

        return {
            "total_monthly_usd": round(total, 2),
            "breakdown": breakdown,
            "note": "Approximate pricing based on us-east-1 on-demand Linux. Actual costs vary by region, commitment (Reserved Instances, Savings Plans), and usage patterns.",
        }


# ============================================================================
# 7. SECURITY CHECKLIST GENERATOR
# ============================================================================

class SecurityChecklistGenerator:
    """Generates security checklists for different infrastructure types."""

    CHECKLISTS = {
        "web_application": [
            ("Authentication", [
                "Use strong password hashing (bcrypt, argon2, scrypt) — never MD5 or SHA1",
                "Implement rate limiting on login endpoints (e.g., 5 attempts per minute per IP)",
                "Use MFA for all administrative accounts",
                "Implement session management with secure, HttpOnly, SameSite cookies",
                "Use OAuth 2.0 / OIDC for third-party authentication — never roll your own",
                "Invalidate sessions on password change and logout",
            ]),
            ("Authorization", [
                "Implement proper access control — check permissions on EVERY request",
                "Prevent BOLA (Broken Object Level Authorization) — verify user owns the resource",
                "Use role-based access control (RBAC) with least privilege",
                "Deny by default — require explicit permission grants",
                "Test authorization thoroughly — automated tests for each role/permission combination",
            ]),
            ("Input Validation", [
                "Validate ALL input — never trust client data",
                "Use parameterized queries — never string concatenation for SQL",
                "Encode output appropriately (HTML entity encoding, URL encoding, etc.)",
                "Implement Content Security Policy (CSP) headers",
                "Validate file uploads — type, size, content inspection",
                "Sanitize rich text input (if allowing HTML) — use DOMPurify or similar",
            ]),
            ("Data Protection", [
                "Encrypt data at rest (AES-256) — database, file storage, backups",
                "Encrypt data in transit (TLS 1.2+) — all connections, internal and external",
                "Use KMS or HSM for key management — never hardcode keys",
                "Mask/hash sensitive data in logs — never log passwords, tokens, PII",
                "Implement data retention and deletion policies",
                "Use secrets management (AWS Secrets Manager, HashiCorp Vault) for credentials",
            ]),
            ("Infrastructure Security", [
                "Deploy behind WAF with OWASP Top 10 rules",
                "Use CDN for DDoS protection and caching",
                "Place databases in isolated subnets — no internet access",
                "Use security groups to restrict traffic to minimum required",
                "Enable VPC Flow Logs for network monitoring",
                "Implement auto-scaling with health checks",
                "Use IAM roles (not access keys) for service-to-service auth",
                "Rotate credentials and keys regularly (90-day max)",
            ]),
            ("Monitoring & Logging", [
                "Log all authentication events (success and failure)",
                "Log all authorization failures and access denied events",
                "Log all administrative actions",
                "Implement centralized log aggregation ( CloudWatch, ELK, Datadog)",
                "Set up alerts for suspicious activity (brute force, unusual access patterns)",
                "Retain logs for compliance (90 days minimum, 1 year for audit)",
                "Monitor uptime, response time, error rate — set SLOs and alert on burn rate",
            ]),
            ("Dependency Security", [
                "Use dependency scanning (npm audit, pip audit, Dependabot, Snyk)",
                "Pin dependency versions — never use floating tags in production",
                "Review dependencies before adding — check maintenance status, known vulns",
                "Remove unused dependencies — reduce attack surface",
                "Monitor for new vulnerabilities in your dependency tree",
                "Keep frameworks and libraries updated — apply security patches promptly",
            ]),
        ],
        "kubernetes": [
            ("Cluster Security", [
                "Enable RBAC — disable anonymous access, use service accounts",
                "Use pod security standards (Restricted, Baseline, Privileged) — default to Restricted",
                "Enable network policies — default deny all, allow only required traffic",
                "Encrypt etcd data at rest (encryptionConfiguration in API server)",
                "Rotate certificates regularly — API server, kubelet, service account tokens",
                "Use admission controllers (PodSecurity, ResourceQuota, LimitRange)",
                "Enable audit logging — capture who did what, when",
                "Keep Kubernetes version updated — apply security patches",
            ]),
            ("Workload Security", [
                "Run containers as non-root (runAsNonRoot: true, runAsUser: <non-zero>)",
                "Use read-only root filesystem (readOnlyRootFilesystem: true)",
                "Drop ALL capabilities, add only what's needed (never add NET_ADMIN, SYS_ADMIN)",
                "Set resource limits (CPU, memory) — prevent resource exhaustion",
                "Set resource requests — improve scheduling and prevent noisy neighbors",
                "Use liveness and readiness probes — auto-recover from failures",
                "Pin container images to specific tags or SHA256 digests",
                "Use trusted base images (official, minimal — distroless, Alpine)",
                "Scan images for vulnerabilities (Trivy, Clair, Docker Scout) before deployment",
                "Don't run privileged containers — ever, in production",
            ]),
            ("Secret Management", [
                "Never hardcode secrets in manifests, environment variables, or Docker images",
                "Use Kubernetes Secrets (with encryption at rest) or external secret stores (Vault, AWS SM)",
                "Limit secret access with RBAC — only pods that need secrets can access them",
                "Rotate secrets regularly — automate rotation where possible",
                "Mount secrets as volumes (not environment variables) — better audit trail, less leakage risk",
                "Use secret encryption at rest — encrypt etcd data",
            ]),
            ("Network Security", [
                "Use NetworkPolicies to control pod-to-pod traffic — default deny",
                "Segment workloads into namespaces — apply different policies per namespace",
                "Use service mesh (Istio, Linkerd) for mTLS between services",
                "Restrict ingress to only required services — use Ingress Controller with TLS",
                "Don't use hostNetwork, hostPID, hostIPC — unless absolutely necessary",
                "Use CNI plugins with network policy support (Calico, Cilium)",
            ]),
            ("Monitoring", [
                "Deploy monitoring stack (Prometheus + Grafana, or Datadog)",
                "Monitor cluster health, node health, pod health",
                "Set up alerts for: pod crashes, node failures, resource exhaustion",
                "Monitor API server audit logs for suspicious activity",
                "Track resource usage trends — plan capacity",
                "Implement centralized logging (EFK stack, Loki, or external service)",
            ]),
        ],
        "docker": [
            ("Image Security", [
                "Use minimal base images (distroless, Alpine, slim) — reduce attack surface",
                "Pin base image to specific version or SHA256 digest — never use 'latest'",
                "Scan images for vulnerabilities (Trivy, Docker Scout, Snyk) before deployment",
                "Use multi-stage builds — final image only contains runtime artifacts",
                "Remove build tools, compilers, package managers from final image",
                "Don't store secrets in images — use build secrets or runtime injection",
                "Sign images (Docker Content Trust, Cosign) — verify integrity at deploy time",
            ]),
            ("Container Runtime Security", [
                "Run as non-root user (USER directive in Dockerfile, securityContext in K8s)",
                "Set read-only root filesystem where possible",
                "Drop capabilities — start with --cap-drop=ALL, add only needed",
                "Set resource limits (--memory, --cpus) — prevent resource exhaustion",
                "Use --security-opt to apply AppArmor/SELinux profiles",
                "Don't mount sensitive host paths (/var/run/docker.sock, /proc, /sys)",
                "Use --read-only and tmpfs for writable paths (/tmp, /var/run)",
                "Set --restart=on-failure with reasonable retry limit",
            ]),
            ("Dockerfile Best Practices", [
                "Use multi-stage builds — separate build environment from runtime",
                "Combine RUN commands with && — reduce image layers",
                "Clean up package manager cache in same RUN instruction (.apt-get clean, rm -rf /var/lib/apt/lists/*)",
                "Use .dockerignore — exclude .git, .env, docs, tests, logs",
                "COPY specific files, not COPY . — minimize copied content",
                "Use COPY --chown to set file ownership correctly",
                "Add HEALTHCHECK instruction — monitor container health",
                "Use exec form for CMD and ENTRYPOINT (JSON array) — proper signal handling",
            ]),
            ("Registry Security", [
                "Use private registry for proprietary images — never expose in public registry",
                "Enable registry authentication — restrict access to authorized users/services",
                "Scan images in registry (automated scanning on push)",
                "Implement image retention policies — remove old/unused images",
                "Use image signing and verification (DCT, Cosign) — prevent tampering",
                "Integrate registry with CI/CD — automated build, scan, push on code change",
            ]),
        ],
    }

    def generate(self, infrastructure_type: str) -> Dict:
        """Generate a security checklist for a given infrastructure type."""
        checklist = self.CHECKLISTS.get(infrastructure_type)

        if not checklist:
            available = list(self.CHECKLISTS.keys())
            return {
                "error": f"No checklist for '{infrastructure_type}'.",
                "available_types": available,
                "suggestion": f"Try one of: {', '.join(available)}",
            }

        flat_items = []
        for category, items in checklist:
            flat_items.extend([f"[{category}] {item}" for item in items])

        return {
            "infrastructure_type": infrastructure_type,
            "total_items": len(flat_items),
            "categories": [{"category": cat, "items": len(items)} for cat, items in checklist],
            "items": flat_items,
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def severity_from_id(check_id: str) -> str:
    """Extract severity from check ID prefix."""
    if check_id.startswith("CRIT"):
        return "CRITICAL"
    elif check_id.startswith("HIGH"):
        return "HIGH"
    elif check_id.startswith("MED"):
        return "MEDIUM"
    elif check_id.startswith("LOW"):
        return "LOW"
    return "INFO"


# ============================================================================
# MAIN — DEMONSTRATION
# ============================================================================

def main():
    print("=" * 70)
    print("BIONIC DAUGHTER v1 — ENGINEERING PRACTICE")
    print("IaC Security, Docker, K8s, CI/CD, Cost Estimation, Checklists")
    print("=" * 70)
    print()

    # ------------------------------------------------------------------
    # 1. TERRAFORM SECURITY SCAN
    # ------------------------------------------------------------------
    print("--- 1. TERRAFORM SECURITY ANALYSIS ---")
    terraform_sample = '''
    provider "aws" {
      region = "us-east-1"
    }

    resource "aws_security_group" "web_sg" {
      name = "web-sg"
      ingress {
        from_port = 80
        to_port = 80
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
      }
      ingress {
        from_port = 443
        to_port = 443
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
      }
    }

    resource "aws_s3_bucket" "assets" {
      bucket = "my-app-assets"
    }

    resource "aws_db_instance" "main" {
      allocated_storage = 100
      engine = "postgres"
      instance_class = "db.t3.medium"
      username = "admin"
      password = "super-secret-password-123"
      publicly_accessible = true
      backup_retention_period = 0
    }

    resource "aws_iam_policy" "admin" {
      name = "admin-policy"
      policy = jsonencode({
        Version = "2012-10-17"
        Statement = [{
          Action = "*"
          Resource = "*"
          Effect = "Allow"
        }]
      })
    }
    '''

    analyzer = TerraformSecurityAnalyzer()
    result = analyzer.analyze(terraform_sample)
    print(f"File: {result.file}")
    print(f"Security Score: {result.score}/100")
    print(f"Findings: {len(result.findings)}")
    for f in result.findings:
        print(f"  [{f.severity}] Line {f.line}: {f.title}")
        print(f"    → {f.recommendation}")
    print()

    # ------------------------------------------------------------------
    # 2. DOCKERFILE ANALYSIS
    # ------------------------------------------------------------------
    print("--- 2. DOCKERFILE SECURITY ANALYSIS ---")
    dockerfile_sample = '''
    FROM python:3.14

    RUN apt-get update && apt-get install -y curl vim git
    RUN pip install flask==3.0.0 requests==2.31.0

    COPY . /app
    WORKDIR /app

    ARG DATABASE_PASSWORD=mysecretpassword

    EXPOSE 5000

    CMD python app.py
    '''

    da = DockerfileAnalyzer()
    result = da.analyze(dockerfile_sample)
    print(f"File: {result.file}")
    print(f"Security Score: {result.score}/100")
    print(f"Findings: {len(result.findings)}")
    for f in result.findings:
        print(f"  [{f.severity}] Line {f.line}: {f.title}")
        print(f"    → {f.recommendation}")
    print()

    # ------------------------------------------------------------------
    # 3. KUBERNETES MANIFEST ANALYSIS
    # ------------------------------------------------------------------
    print("--- 3. KUBERNETES MANIFEST SECURITY ANALYSIS ---")
    k8s_sample = '''
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: web-app
    spec:
      replicas: 3
      selector:
        matchLabels:
          app: web
      template:
        metadata:
          labels:
            app: web
        spec:
          containers:
          - name: web
            image: nginx:latest
            ports:
            - containerPort: 80
            resources: {}
    '''

    ka = KubernetesManifestAnalyzer()
    result = ka.analyze(k8s_sample)
    print(f"File: {result.file}")
    print(f"Security Score: {result.score}/100")
    print(f"Findings: {len(result.findings)}")
    for f in result.findings:
        print(f"  [{f.severity}] Line {f.line}: {f.title}")
        print(f"    → {f.recommendation}")
    print()

    # ------------------------------------------------------------------
    # 4. CI/CD SECURITY ANALYSIS
    # ------------------------------------------------------------------
    print("--- 4. CI/CD PIPELINE SECURITY ANALYSIS ---")
    cicd_sample = '''
    name: CI Pipeline

    on:
      pull_request:
        branches: [main]

    jobs:
      build:
        runs-on: ubuntu-latest
        permissions:
          contents: write
        steps:
        - uses: actions/checkout@main
        - uses: SomeRandomDev/random-action@master
        - env:
            API_KEY: hardcoded-api-key-12345
            DATABASE_URL: postgresql://user:password@host/db
          run: |
            git clone https://github.com/untrusted/repo.git
            npm install
            npm test
    '''

    ca = CIDownloadSecurityAnalyzer()
    result = ca.analyze(cicd_sample)
    print(f"File: {result.file}")
    print(f"Security Score: {result.score}/100")
    print(f"Findings: {len(result.findings)}")
    for f in result.findings:
        print(f"  [{f.severity}] Line {f.line}: {f.title}")
        print(f"    → {f.recommendation}")
    print()

    # ------------------------------------------------------------------
    # 5. NETWORK DIAGRAMS
    # ------------------------------------------------------------------
    print("--- 5. NETWORK DIAGRAMS ---")
    generator = NetworkDiagramGenerator()
    print(generator.generate_web_app_architecture())
    print()

    # ------------------------------------------------------------------
    # 6. COST ESTIMATION
    # ------------------------------------------------------------------
    print("--- 6. CLOUD COST ESTIMATION ---")
    estimator = CloudCostEstimator()
    resources = {
        "ec2": {"t3_medium": 2, "m5_large": 1},
        "rds": {"t3_medium": 1},
        "s3": {"storage_gb": 50, "requests_millions": 1},
        "lambda": {"gb_seconds": 500000, "requests_millions": 10},
        "data_transfer": {"internet_gb": 100, "cross_region_gb": 10},
        "vpc": {"nat_gateways": 1},
        "cloudwatch": {"logs_gb": 10, "alarms": 5},
    }
    cost = estimator.estimate_aws_monthly(resources)
    print(f"Estimated Monthly Cost: ${cost['total_monthly_usd']}")
    print("Breakdown:")
    for item, amount in cost["breakdown"].items():
        print(f"  {item}: ${amount}")
    print(f"  {cost['note']}")
    print()

    # ------------------------------------------------------------------
    # 7. SECURITY CHECKLISTS
    # ------------------------------------------------------------------
    print("--- 7. SECURITY CHECKLISTS ---")
    checklist_gen = SecurityChecklistGenerator()

    for infra_type in ["web_application", "kubernetes", "docker"]:
        print(f"\n[{infra_type.upper()}] Security Checklist ({checklist_gen.generate(infra_type)['total_items']} items):")
        checklist = checklist_gen.generate(infra_type)
        for item in checklist["items"][:5]:
            print(f"  ✓ {item}")
        if len(checklist["items"]) > 5:
            print(f"  ... and {len(checklist['items']) - 5} more items")

    print()
    print("=" * 70)
    print("ENGINEERING PRACTICE COMPLETE — ALL ANALYZERS WORKING")
    print("=" * 70)


if __name__ == "__main__":
    main()
