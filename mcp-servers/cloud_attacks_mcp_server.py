#!/usr/bin/env python3
"""
Cloud Attacks MCP Server
========================
Simulates cloud attack scenarios as MCP tools for AWS/GCP/Azure.

Tools:
  1. iam_privesc       — IAM privilege escalation simulation
  2. metadata_ssrf     — Metadata service SSRF simulation
  3. s3_exposure       — Cloud storage bucket exposure simulation
  4. lambda_backdoor   — Serverless function backdoor simulation
  5. ebs_exfil         — Disk snapshot exfiltration simulation

Each tool accepts a provider parameter (aws/gcp/azure) and returns
structured JSON with findings, severity, and remediation guidance.
"""
import json
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SERVER_NAME = "cloud-attacks-mcp"
SERVER_VERSION = "1.0.0"

VALID_PROVIDERS = {"aws", "gcp", "azure"}

# ---------------------------------------------------------------------------
# Simulation Data (condensed)
# ---------------------------------------------------------------------------

ATTACK_DATA = {
    "iam_privesc": {
        "aws": {
            "vectors": [
                {"name": "PassRole + RunInstances", "severity": "critical", "mitre": "T1098", "perms": ["iam:PassRole", "ec2:RunInstances"], "chain": "PassRole → RunInstances → curl metadata → steal creds"},
                {"name": "iam:CreatePolicyVersion", "severity": "critical", "mitre": "T1098", "perms": ["iam:CreatePolicyVersion"], "chain": "CreatePolicyVersion (Allow *) → SetDefaultPolicyVersion → admin"},
                {"name": "iam:AttachUserPolicy", "severity": "high", "mitre": "T1098", "perms": ["iam:AttachUserPolicy"], "chain": "AttachUserPolicy (AdministratorAccess) → admin"},
                {"name": "iam:CreateAccessKey", "severity": "high", "mitre": "T1098", "perms": ["iam:CreateAccessKey"], "chain": "CreateAccessKey(target) → impersonate"},
            ],
            "remediation": ["Apply least-privilege IAM; deny iam:PassRole on wildcard resources.", "Enable CloudTrail; monitor CreatePolicyVersion, AttachRolePolicy.", "Use permission boundaries and SCPs to cap privilege."],
        },
        "gcp": {
            "vectors": [
                {"name": "iam.roles.update", "severity": "critical", "mitre": "T1098", "perms": ["iam.roles.update"], "chain": "Update role → add setIamPolicy → grant owner"},
                {"name": "compute.instances.setMetadata", "severity": "high", "mitre": "T1098", "perms": ["compute.instances.setMetadata"], "chain": "setMetadata (SSH key) → SSH → access SA token"},
                {"name": "serviceAccounts.getAccessToken", "severity": "critical", "mitre": "T1078", "perms": ["iam.serviceAccounts.getAccessToken"], "chain": "getAccessToken(target_SA) → impersonate"},
            ],
            "remediation": ["Restrict iam.roles.update via deny policies.", "Use Workload Identity instead of service account keys.", "Audit IAM bindings with Asset Inventory."],
        },
        "azure": {
            "vectors": [
                {"name": "roleAssignments/write", "severity": "critical", "mitre": "T1098", "perms": ["Microsoft.Authorization/roleAssignments/write"], "chain": "Create role assignment (Owner) → full control"},
                {"name": "virtualMachines/runCommand", "severity": "high", "mitre": "T1098", "perms": ["Microsoft.Compute/virtualMachines/runCommand/action"], "chain": "RunCommand (curl IMDS) → steal token"},
                {"name": "KeyVault/secrets/read", "severity": "high", "mitre": "T1552", "perms": ["Microsoft.KeyVault/vaults/secrets/read"], "chain": "Read secrets → lateral movement"},
            ],
            "remediation": ["Use Azure PIM for just-in-time access.", "Restrict role assignment with condition scopes.", "Monitor Activity Logs for assignment changes."],
        },
    },
    "metadata_ssrf": {
        "aws": {
            "url": "http://169.254.169.254/latest/meta-data/",
            "findings": ["IMDSv1 enabled — creds via simple SSRF", "IMDSv2 not enforced — hop limit allows bypass", "X-Forwarded-For trusted — IMDSv2 bypass"],
            "exploit": "curl http://169.254.169.254/latest/meta-data/iam/security-credentials/<role>",
            "remediation": ["Enforce IMDSv2 with hop limit = 1.", "Disable IMDSv1 via instance metadata options.", "Block 169.254.169.254 at network level where unused."],
        },
        "gcp": {
            "url": "http://metadata.google.internal/computeMetadata/v1/",
            "findings": ["Metadata-Flavor header not validated", "Service account token exposed", "Recursive queries enabled — full config readable"],
            "exploit": "curl -H 'Metadata-Flavor: Google' http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
            "remediation": ["Enforce Metadata-Flavor header validation.", "Use metadata concealment feature.", "Use Workload Identity Federation."],
        },
        "azure": {
            "url": "http://169.254.169.254/metadata/instance",
            "findings": ["IMDS accessible — managed identity token exposed", "Metadata header bypassable via SSRF", "Instance metadata leaks subscription info"],
            "exploit": "curl -H 'Metadata: true' http://169.254.169.254/metadata/identity/oauth2/token",
            "remediation": ["Restrict IMDS to VM network namespace.", "Use Azure AD Workload Identity for pods.", "Block IMDS from containers via network policies."],
        },
    },
    "s3_exposure": {
        "aws": {
            "scenarios": [
                {"name": "Public Read Access", "severity": "critical", "indicator": "Principal: * in bucket policy", "data": "Customer PII, financial records"},
                {"name": "Authenticated Any-AWS-User", "severity": "high", "indicator": "Principal: { AWS: * } without OrgID condition", "data": "Internal docs, source code"},
                {"name": "Misconfigured CORS", "severity": "medium", "indicator": "AllowedOrigin: * with GET", "data": "Static assets, uploads"},
            ],
            "remediation": ["Enable S3 Block Public Access (account + bucket).", "Use aws:PrincipalOrgID condition key.", "Enable default encryption (SSE-S3/KMS)."],
        },
        "gcp": {
            "scenarios": [
                {"name": "AllUsers Read Access", "severity": "critical", "indicator": "allUsers with roles/storage.objectViewer", "data": "Customer data, secrets"},
                {"name": "Uniform Access Disabled", "severity": "high", "indicator": "uniformBucketLevelAccess = false", "data": "Objects with permissive ACLs"},
            ],
            "remediation": ["Enable Public Access Prevention.", "Migrate to Uniform Bucket-Level Access.", "Use IAM Conditions for VPC/IP restrictions."],
        },
        "azure": {
            "scenarios": [
                {"name": "Blob Anonymous Access", "severity": "critical", "indicator": "publicAccess = Blob/Container", "data": "All blobs in container"},
                {"name": "Over-Permissioned SAS", "severity": "high", "indicator": "SAS with sp=rwdlac and no expiry", "data": "Entire storage account"},
            ],
            "remediation": ["Disable anonymous public access.", "Use stored access policies with expiry.", "Restrict to specific VNets and IP ranges."],
        },
    },
    "lambda_backdoor": {
        "aws": {
            "scenarios": [
                {"name": "Code Modification", "severity": "critical", "vector": "lambda:UpdateFunctionCode → deploy backdoor", "persistence": "Until next deployment"},
                {"name": "Layer Injection", "severity": "critical", "vector": "UpdateFunctionConfiguration → add malicious layer", "persistence": "Survives code updates"},
                {"name": "Env Var Exfiltration", "severity": "high", "vector": "GetFunctionConfiguration → read plaintext creds", "persistence": "N/A — credential theft"},
            ],
            "remediation": ["Restrict UpdateFunctionCode to CI/CD roles only.", "Enable Lambda code signing.", "Encrypt env vars with KMS."],
        },
        "gcp": {
            "scenarios": [
                {"name": "Cloud Function Code Overwrite", "severity": "critical", "vector": "cloudfunctions.functions.update → backdoor", "persistence": "Until next deployment"},
                {"name": "Service Account Impersonation", "severity": "critical", "vector": "setIamPolicy → bind to privileged SA", "persistence": "Survives code updates"},
            ],
            "remediation": ["Restrict functions.update to deployment SAs.", "Use Binary Authorization.", "Use Secret Manager with audit logging."],
        },
        "azure": {
            "scenarios": [
                {"name": "Function App Code Deployment", "severity": "critical", "vector": "webApps/functions/action → deploy backdoor", "persistence": "In deployment slot"},
                {"name": "Managed Identity Token Theft", "severity": "critical", "vector": "Modify function → curl IMDS → exfiltrate", "persistence": "Until redeployment"},
            ],
            "remediation": ["Restrict deployment to CI/CD pipelines.", "Use managed identity with least-privilege RBAC.", "Use Key Vault references for secrets."],
        },
    },
    "ebs_exfil": {
        "aws": {
            "scenarios": [
                {"name": "Cross-Account Snapshot Sharing", "severity": "critical", "vector": "ModifySnapshotAttribute → share with attacker", "data": "Full disk contents"},
                {"name": "Public Snapshot Creation", "severity": "critical", "vector": "CreateSnapshot → ModifySnapshotAttribute (public)", "data": "Entire volume"},
                {"name": "Unencrypted Snapshot from Encrypted Volume", "severity": "high", "vector": "CreateSnapshot (encryption disabled)", "data": "Volume data without KMS"},
            ],
            "remediation": ["Deny ModifySnapshotAttribute via SCP unless using approved KMS.", "Enable EBS encryption by default.", "Use AWS Config to detect public snapshots."],
        },
        "gcp": {
            "scenarios": [
                {"name": "Cross-Project Snapshot Sharing", "severity": "critical", "vector": "SetIamPolicy → grant compute.storageAdmin", "data": "Full disk contents"},
                {"name": "Snapshot Export to Cloud Storage", "severity": "high", "vector": "Export to GCS → share bucket publicly", "data": "Volume data in GCS"},
            ],
            "remediation": ["Restrict snapshots.setIamPolicy to backup SAs.", "Enforce CMEK encryption via Org Policy.", "Monitor Audit Logs for IAM changes."],
        },
        "azure": {
            "scenarios": [
                {"name": "Cross-Subscription Snapshot Copy", "severity": "critical", "vector": "snapshots/copy → attacker subscription", "data": "Full disk contents"},
                {"name": "SAS URI Generation", "severity": "critical", "vector": "beginGetAccess → SAS URI → download VHD", "data": "Entire disk as VHD"},
            ],
            "remediation": ["Restrict beginGetAccess to backup roles only.", "Enforce Azure Disk Encryption.", "Use Azure Policy to deny unencrypted snapshots."],
        },
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validate_provider(provider: str) -> str:
    """Validate and normalize a cloud provider name."""
    provider = (provider or "aws").strip().lower()
    if provider not in VALID_PROVIDERS:
        raise ValueError(
            f"Invalid provider '{provider}'. Must be one of: {', '.join(sorted(VALID_PROVIDERS))}"
        )
    return provider


def _build_result(
    provider: str,
    tool: str,
    findings: List[Dict[str, Any]],
    remediation: List[str],
    summary: str,
) -> str:
    """Build a standardized JSON result."""
    return json.dumps(
        {
            "provider": provider,
            "tool": tool,
            "summary": summary,
            "findings_count": len(findings),
            "findings": findings,
            "remediation": remediation,
        },
        indent=2,
    )


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

app = FastMCP(SERVER_NAME)


@app.tool(
    name="iam_privesc",
    description=(
        "Simulate IAM privilege escalation attack scenarios for AWS, GCP, or Azure. "
        "Checks for dangerous permission combinations like PassRole + RunInstances, "
        "policy manipulation, and role chaining. Returns findings with severity, "
        "MITRE ATT&CK technique mapping, and remediation guidance."
    ),
)
def iam_privesc(provider: str = "aws") -> str:
    """
    Simulate IAM privilege escalation scenarios.

    Args:
        provider: Cloud provider — 'aws', 'gcp', or 'azure' (default: aws)
    """
    provider = _validate_provider(provider)
    data = ATTACK_DATA["iam_privesc"][provider]

    findings = []
    for v in data["vectors"]:
        findings.append({
            "name": v["name"],
            "severity": v["severity"],
            "mitre_technique": v["mitre"],
            "permissions_required": v["perms"],
            "attack_chain": v["chain"],
        })

    summary = (
        f"IAM privilege escalation for {provider.upper()}: {len(findings)} vectors. "
        f"Critical: {sum(1 for f in findings if f['severity'] == 'critical')}, "
        f"High: {sum(1 for f in findings if f['severity'] == 'high')}."
    )

    return _build_result(provider, "iam_privesc", findings, data["remediation"], summary)


@app.tool(
    name="metadata_ssrf",
    description=(
        "Simulate metadata service SSRF attacks against AWS IMDS, GCP metadata, "
        "or Azure IMDS. Covers IMDSv1 vs v2 differences, credential theft via SSRF, "
        "and header-based bypass techniques. Returns findings with exploit details "
        "and remediation steps."
    ),
)
def metadata_ssrf(provider: str = "aws") -> str:
    """
    Simulate metadata service SSRF scenarios.

    Args:
        provider: Cloud provider — 'aws', 'gcp', or 'azure' (default: aws)
    """
    provider = _validate_provider(provider)
    data = ATTACK_DATA["metadata_ssrf"][provider]

    findings = [
        {
            "metadata_url": data["url"],
            "exploit_example": data["exploit"],
            "configuration_findings": data["findings"],
        }
    ]

    summary = (
        f"Metadata SSRF for {provider.upper()}: primary risk is credential theft via SSRF. "
        f"{len(data['findings'])} configuration issue(s) identified."
    )

    return _build_result(provider, "metadata_ssrf", findings, data["remediation"], summary)


@app.tool(
    name="s3_exposure",
    description=(
        "Simulate S3/Cloud Storage/Blob Storage bucket exposure scenarios. "
        "Checks for public access, misconfigured ACLs, CORS misconfigurations, "
        "and encryption gaps. Returns findings with data-at-risk assessment "
        "and remediation guidance."
    ),
)
def s3_exposure(provider: str = "aws") -> str:
    """
    Simulate cloud storage bucket exposure scenarios.

    Args:
        provider: Cloud provider — 'aws', 'gcp', or 'azure' (default: aws)
    """
    provider = _validate_provider(provider)
    data = ATTACK_DATA["s3_exposure"][provider]

    findings = []
    for s in data["scenarios"]:
        findings.append({
            "name": s["name"],
            "severity": s["severity"],
            "indicator": s["indicator"],
            "data_at_risk": s["data"],
        })

    summary = (
        f"Storage exposure for {provider.upper()}: {len(findings)} scenario(s). "
        f"Critical: {sum(1 for f in findings if f['severity'] == 'critical')}, "
        f"High: {sum(1 for f in findings if f['severity'] == 'high')}, "
        f"Medium: {sum(1 for f in findings if f['severity'] == 'medium')}."
    )

    return _build_result(provider, "s3_exposure", findings, data["remediation"], summary)


@app.tool(
    name="lambda_backdoor",
    description=(
        "Simulate serverless function backdoor scenarios for AWS Lambda, "
        "Google Cloud Functions, or Azure Functions. Covers code modification, "
        "layer injection, environment variable theft, and event source manipulation. "
        "Returns findings with persistence mechanisms and remediation."
    ),
)
def lambda_backdoor(provider: str = "aws") -> str:
    """
    Simulate serverless function backdoor scenarios.

    Args:
        provider: Cloud provider — 'aws', 'gcp', or 'azure' (default: aws)
    """
    provider = _validate_provider(provider)
    data = ATTACK_DATA["lambda_backdoor"][provider]

    findings = []
    for s in data["scenarios"]:
        findings.append({
            "name": s["name"],
            "severity": s["severity"],
            "attack_vector": s["vector"],
            "persistence_mechanism": s["persistence"],
        })

    summary = (
        f"Serverless backdoor for {provider.upper()}: {len(findings)} scenario(s). "
        f"Critical: {sum(1 for f in findings if f['severity'] == 'critical')}, "
        f"High: {sum(1 for f in findings if f['severity'] == 'high')}."
    )

    return _build_result(provider, "lambda_backdoor", findings, data["remediation"], summary)


@app.tool(
    name="ebs_exfil",
    description=(
        "Simulate disk snapshot exfiltration scenarios for AWS EBS, "
        "GCP Persistent Disk, or Azure Managed Disks. Covers cross-account "
        "sharing, public snapshot creation, SAS URI abuse, and encryption bypass. "
        "Returns findings with data-at-risk and remediation guidance."
    ),
)
def ebs_exfil(provider: str = "aws") -> str:
    """
    Simulate disk snapshot exfiltration scenarios.

    Args:
        provider: Cloud provider — 'aws', 'gcp', or 'azure' (default: aws)
    """
    provider = _validate_provider(provider)
    data = ATTACK_DATA["ebs_exfil"][provider]

    findings = []
    for s in data["scenarios"]:
        findings.append({
            "name": s["name"],
            "severity": s["severity"],
            "attack_vector": s["vector"],
            "data_at_risk": s["data"],
        })

    summary = (
        f"Snapshot exfiltration for {provider.upper()}: {len(findings)} scenario(s). "
        f"Critical: {sum(1 for f in findings if f['severity'] == 'critical')}, "
        f"High: {sum(1 for f in findings if f['severity'] == 'high')}."
    )

    return _build_result(provider, "ebs_exfil", findings, data["remediation"], summary)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(transport="stdio")
