#!/usr/bin/env python3
"""
Cloud MCP Server
================
Simulates AWS/GCP/Azure cloud attack scenarios as MCP tools.

Tools:
  1. iam_privesc       — IAM privilege escalation simulation
  2. metadata_ssrf     — Metadata service SSRF simulation
  3. s3_exposure       — S3 bucket exposure simulation
  4. lambda_backdoor   — Lambda function backdoor simulation
  5. ebs_exfil         — EBS snapshot exfiltration simulation

Each tool accepts a provider parameter (aws/gcp/azure) and returns
structured JSON with findings, severity, and remediation guidance.
"""
import json
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SERVER_NAME = "cloud-mcp"
SERVER_VERSION = "1.0.0"

VALID_PROVIDERS = {"aws", "gcp", "azure"}

# ---------------------------------------------------------------------------
# Simulation Data
# ---------------------------------------------------------------------------

# IAM privilege escalation vectors per provider
IAM_VECTORS = {
    "aws": {
        "vectors": [
            {
                "name": "PassRole + RunInstances",
                "description": "iam:PassRole combined with ec2:RunInstances allows launching an instance with an admin role, then accessing its instance profile credentials via the metadata service.",
                "severity": "critical",
                "mitre_technique": "T1098",
                "permissions_required": ["iam:PassRole", "ec2:RunInstances"],
                "chain": "PassRole → RunInstances → curl http://169.254.169.254/latest/meta-data/iam/security-credentials/ → steal creds",
            },
            {
                "name": "iam:CreatePolicyVersion",
                "description": "Creating a new policy version with full-admin permissions and setting it as default escalates privileges without triggering CloudTrail alarms for role assumption.",
                "severity": "critical",
                "mitre_technique": "T1098",
                "permissions_required": ["iam:CreatePolicyVersion", "iam:SetDefaultPolicyVersion"],
                "chain": "CreatePolicyVersion (Allow *) → SetDefaultPolicyVersion → full admin",
            },
            {
                "name": "iam:AttachUserPolicy",
                "description": "Attaching an admin policy to the current user grants immediate elevated access.",
                "severity": "high",
                "mitre_technique": "T1098",
                "permissions_required": ["iam:AttachUserPolicy"],
                "chain": "AttachUserPolicy (AdministratorAccess) → immediate admin",
            },
            {
                "name": "iam:CreateAccessKey",
                "description": "Creating a new access key for another user allows impersonation.",
                "severity": "high",
                "mitre_technique": "T1098",
                "permissions_required": ["iam:CreateAccessKey"],
                "chain": "CreateAccessKey(target_user) → use new creds",
            },
            {
                "name": "iam:UpdateLoginProfile",
                "description": "Updating another user's login password grants console access.",
                "severity": "high",
                "mitre_technique": "T1098",
                "permissions_required": ["iam:UpdateLoginProfile"],
                "chain": "UpdateLoginProfile(target_user, new_pass) → console login",
            },
        ],
        "remediation": [
            "Apply least-privilege IAM policies; deny iam:PassRole on wildcard resources.",
            "Use aws:RequestedRegion and aws:PrincipalArn condition keys.",
            "Enable AWS CloudTrail and monitor for CreatePolicyVersion, AttachRolePolicy.",
            "Use permission boundaries to cap maximum privilege.",
            "Implement SCPs at the organization level to deny dangerous IAM actions.",
        ],
    },
    "gcp": {
        "vectors": [
            {
                "name": "iam.roles.update (Custom Role Escalation)",
                "description": "Updating a custom role to add *.setIamPolicy permissions allows granting oneself the Project Owner role.",
                "severity": "critical",
                "mitre_technique": "T1098",
                "permissions_required": ["iam.roles.update"],
                "chain": "Update role → add roles/resourcemanager.projectSetIamPolicy → grant owner",
            },
            {
                "name": "compute.instances.setMetadata",
                "description": "Setting instance metadata to add an SSH key grants OS-level access to the service account, which may have elevated GCP IAM bindings.",
                "severity": "high",
                "mitre_technique": "T1098",
                "permissions_required": ["compute.instances.setMetadata"],
                "chain": "setMetadata (add SSH key) → SSH → access SA token from metadata",
            },
            {
                "name": "serviceAccounts.getAccessToken",
                "description": "Impersonating a service account with broader permissions via iam.serviceAccounts.getAccessToken.",
                "severity": "critical",
                "mitre_technique": "T1078",
                "permissions_required": ["iam.serviceAccounts.getAccessToken"],
                "chain": "getAccessToken(target_SA) → use token as target SA",
            },
            {
                "name": "deploymentmanager.deployments.create",
                "description": "Creating a deployment that adds an IAM binding grants persistent elevated access.",
                "severity": "high",
                "mitre_technique": "T1098",
                "permissions_required": ["deploymentmanager.deployments.create"],
                "chain": "Create deployment with IAM binding → persistent backdoor",
            },
        ],
        "remediation": [
            "Restrict iam.roles.update and resourcemanager.projectSetIamPolicy via deny policies.",
            "Enable VPC Service Controls to limit metadata access.",
            "Use Workload Identity instead of service account keys.",
            "Audit IAM bindings regularly with Asset Inventory.",
            "Implement Organization Policy constraints.",
        ],
    },
    "azure": {
        "vectors": [
            {
                "name": "Microsoft.Authorization/roleAssignments/write",
                "description": "Creating a role assignment at subscription scope grants Owner access, enabling full control of all resources.",
                "severity": "critical",
                "mitre_technique": "T1098",
                "permissions_required": ["Microsoft.Authorization/roleAssignments/write"],
                "chain": "Create role assignment (Owner) → full subscription control",
            },
            {
                "name": "Microsoft.Compute/virtualMachines/runCommand/action",
                "description": "Running a command on a VM to fetch the managed identity token from the IMDS endpoint.",
                "severity": "high",
                "mitre_technique": "T1098",
                "permissions_required": ["Microsoft.Compute/virtualMachines/runCommand/action"],
                "chain": "RunCommand (curl IMDS) → steal managed identity token",
            },
            {
                "name": "Microsoft.KeyVault/vaults/secrets/read",
                "description": "Reading Key Vault secrets may expose service credentials, API keys, and certificates that enable lateral movement.",
                "severity": "high",
                "mitre_technique": "T1552",
                "permissions_required": ["Microsoft.KeyVault/vaults/secrets/read"],
                "chain": "Read Key Vault secrets → use credentials for lateral movement",
            },
            {
                "name": "Microsoft.Authorization/policyAssignments/write",
                "description": "Modifying Azure Policy assignments to exclude critical resources from compliance checks.",
                "severity": "medium",
                "mitre_technique": "T1098",
                "permissions_required": ["Microsoft.Authorization/policyAssignments/write"],
                "chain": "Modify policy → exclude resources → bypass guardrails",
            },
        ],
        "remediation": [
            "Use Azure Privileged Identity Management (PIM) for just-in-time access.",
            "Restrict role assignment permissions with condition scopes.",
            "Enable Azure Policy to enforce least-privilege and audit assignments.",
            "Use managed identities with scoped permissions instead of shared credentials.",
            "Monitor Azure Activity Logs for role assignment changes.",
        ],
    },
}

# Metadata SSRF vectors per provider
METADATA_SSRF = {
    "aws": {
        "metadata_url": "http://169.254.169.254/latest/meta-data/",
        "versions": {
            "IMDSv1": {
                "description": "Unauthenticated GET request returns credentials. No session token required.",
                "severity": "critical",
                "exploit": "curl http://169.254.169.254/latest/meta-data/iam/security-credentials/<role-name>",
            },
            "IMDSv2": {
                "description": "Requires session token via PUT request first. Adds defense-in-depth but bypassable via X-Forwarded-For header smuggling.",
                "severity": "medium",
                "exploit": "PUT x-aws-ec2-metadata-token-ttl-seconds: 21600 → GET with X-Aws-Ec2-Metadata-Token header",
            },
        },
        "findings": [
            "IMDSv1 enabled — credentials accessible via simple SSRF",
            "IMDSv2 not enforced — hop limit of 1 allows container escape",
            "X-Forwarded-For header trusted — allows IMDSv2 bypass via HTTP header injection",
        ],
        "remediation": [
            "Enforce IMDSv2 with hop limit = 1 across all instances.",
            "Disable IMDSv1 via instance metadata options.",
            "Block 169.254.169.254 at the network level where IMDS is not needed.",
            "Use VPC endpoints and private subnets to limit metadata exposure.",
        ],
    },
    "gcp": {
        "metadata_url": "http://metadata.google.internal/computeMetadata/v1/",
        "versions": {
            "v1": {
                "description": "Requires Metadata-Flavor: Google header. Older tooling may skip this check.",
                "severity": "high",
                "exploit": "curl -H 'Metadata-Flavor: Google' http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
            },
        },
        "findings": [
            "Metadata-Flavor header not validated — allows unauthenticated access",
            "Service account token exposed via metadata endpoint",
            "Recursive metadata queries enabled — full instance config readable",
        ],
        "remediation": [
            "Enforce Metadata-Flavor: Google header validation.",
            "Use the metadata concealment feature to restrict access.",
            "Implement VPC Service Controls around the metadata server.",
            "Use Workload Identity Federation instead of instance metadata.",
        ],
    },
    "azure": {
        "metadata_url": "http://169.254.169.254/metadata/instance",
        "versions": {
            "v1": {
                "description": "Requires Metadata: true header. IMDS is the only way to access managed identity tokens.",
                "severity": "high",
                "exploit": "curl -H 'Metadata: true' http://169.254.169.254/metadata/identity/oauth2/token",
            },
        },
        "findings": [
            "IMDS accessible from within the VM — managed identity token exposed",
            "Metadata header validation may be bypassed via SSRF in web apps",
            "Instance metadata leaks full subscription and resource group info",
        ],
        "remediation": [
            "Restrict IMDS access to the VM's own network namespace.",
            "Use Azure AD Workload Identity for Kubernetes pods.",
            "Block IMDS access from containers via network policies.",
            "Monitor for unexpected IMDS token requests in diagnostic logs.",
        ],
    },
}

# S3 bucket exposure scenarios
S3_EXPOSURE = {
    "aws": {
        "scenarios": [
            {
                "name": "Public Read Access",
                "description": "Bucket ACL or policy allows s3:GetObject for Principal: *",
                "severity": "critical",
                "indicator": "BucketPolicy contains 'Effect: Allow' with 'Principal: \"*\"'",
                "data_at_risk": "Customer PII, financial records, credentials",
            },
            {
                "name": "Authenticated User Access",
                "description": "Bucket allows access to any authenticated AWS user (not just your account).",
                "severity": "high",
                "indicator": "Principal: { AWS: \"*\" } without condition restricting aws:PrincipalOrgID",
                "data_at_risk": "Internal documents, source code, backups",
            },
            {
                "name": "Misconfigured CORS",
                "description": "CORS policy allows any origin to read bucket contents via JavaScript.",
                "severity": "medium",
                "indicator": "AllowedOrigin: * with AllowedMethod: GET",
                "data_at_risk": "Static assets, user-uploaded content",
            },
            {
                "name": "Unencrypted Bucket",
                "description": "Bucket lacks default encryption, allowing data to be read in plaintext if accessed.",
                "severity": "medium",
                "indicator": "No ServerSideEncryptionConfiguration on bucket",
                "data_at_risk": "All stored objects",
            },
        ],
        "remediation": [
            "Enable S3 Block Public Access at the account and bucket level.",
            "Use aws:PrincipalOrgID condition key to restrict access to your organization.",
            "Enable default encryption (SSE-S3 or SSE-KMS) on all buckets.",
            "Use S3 Access Analyzer to identify public and cross-account access.",
            "Enable CloudTrail data events for S3 object-level logging.",
        ],
    },
    "gcp": {
        "scenarios": [
            {
                "name": "AllUsers Read Access",
                "description": "Bucket IAM allows allUsers or allAuthenticatedUsers to read objects.",
                "severity": "critical",
                "indicator": "Binding includes allUsers with roles/storage.objectViewer",
                "data_at_risk": "Customer data, application secrets, backups",
            },
            {
                "name": "Uniform Bucket-Level Access Disabled",
                "description": "Fine-grained ACLs coexist with IAM, creating conflicting permissions that may allow unintended access.",
                "severity": "high",
                "indicator": "uniformBucketLevelAccess = false",
                "data_at_risk": "Objects with permissive ACLs",
            },
            {
                "name": "Public Logging Bucket",
                "description": "Access logs bucket is publicly readable, exposing request patterns and object names.",
                "severity": "medium",
                "indicator": "Logging bucket has allUsers binding",
                "data_at_risk": "Access patterns, object names, requester info",
            },
        ],
        "remediation": [
            "Enable 'Public access prevention' at the bucket or organization level.",
            "Migrate to Uniform Bucket-Level Access.",
            "Use IAM Conditions to restrict access by VPC or IP range.",
            "Enable Cloud Audit Logs for Cloud Storage.",
            "Use VPC Service Controls to limit data exfiltration.",
        ],
    },
    "azure": {
        "scenarios": [
            {
                "name": "Blob Anonymous Access",
                "description": "Container public access level set to Blob or Container allows unauthenticated reads.",
                "severity": "critical",
                "indicator": "publicAccess = 'Blob' or 'Container'",
                "data_at_risk": "All blobs in the container",
            },
            {
                "name": "Shared Access Signature (SAS) Over-Permissioned",
                "description": "SAS token grants read, write, delete, and list permissions with no expiry.",
                "severity": "high",
                "indicator": "SAS token with sp=rwdlac and no se (expiry) parameter",
                "data_at_risk": "Entire storage account contents",
            },
            {
                "name": "Storage Account Firewall Bypass",
                "description": 'Storage account allows "trusted Microsoft services" access, which can be abused via Azure services.',
                "severity": "medium",
                "indicator": "networkAcls.bypass = 'AzureServices'",
                "data_at_risk": "Data accessible via compromised Azure service",
            },
        ],
        "remediation": [
            "Disable anonymous public access at the storage account level.",
            "Use stored access policies with expiry for SAS tokens.",
            "Restrict storage account access to specific VNets and IP ranges.",
            "Enable storage analytics logging and monitor for anonymous access.",
            "Use Azure Policy to enforce secure transfer and firewall rules.",
        ],
    },
}

# Lambda backdoor scenarios
LAMBDA_BACKDOOR = {
    "aws": {
        "scenarios": [
            {
                "name": "Code Modification via update-function-code",
                "description": "An attacker with lambda:UpdateFunctionCode can replace the function with a malicious version that exfiltrates data or maintains persistence.",
                "severity": "critical",
                "attack_vector": "lambda:UpdateFunctionCode → deploy backdoored zip → trigger via existing event source",
                "persistence": "Function code persists until next legitimate deployment",
            },
            {
                "name": "Layer Injection",
                "description": "Adding a malicious Lambda layer that overrides a library function (e.g., requests.get) to exfiltrate data.",
                "severity": "critical",
                "attack_vector": "lambda:UpdateFunctionConfiguration → add malicious layer ARN",
                "persistence": "Layer persists across code updates",
            },
            {
                "name": "Environment Variable Exfiltration",
                "description": "Reading lambda:GetFunctionConfiguration to steal database credentials, API keys from environment variables.",
                "severity": "high",
                "attack_vector": "lambda:GetFunctionConfiguration → read plaintext env vars",
                "persistence": "N/A — credential theft, not persistence",
            },
            {
                "name": "Event Source Manipulation",
                "description": "Adding a malicious event source mapping (e.g., SQS queue) to trigger the function with attacker-controlled input.",
                "severity": "high",
                "attack_vector": "lambda:CreateEventSourceMapping → attacker-controlled SQS queue",
                "persistence": "Event source mapping persists until deleted",
            },
        ],
        "remediation": [
            "Restrict lambda:UpdateFunctionCode to CI/CD service roles only.",
            "Enable Lambda code signing to verify code integrity.",
            "Encrypt environment variables with KMS and restrict kms:Decrypt.",
            "Use Lambda function URLs with auth, not public endpoints.",
            "Monitor CloudTrail for unexpected UpdateFunctionCode events.",
        ],
    },
    "gcp": {
        "scenarios": [
            {
                "name": "Cloud Function Code Overwrite",
                "description": "Using cloudfunctions.functions.update to replace function code with a backdoor.",
                "severity": "critical",
                "attack_vector": "cloudfunctions.functions.update → upload malicious source",
                "persistence": "Function code persists until next deployment",
            },
            {
                "name": "Service Account Impersonation",
                "description": "Modifying the runtime service account to one with broader permissions.",
                "severity": "critical",
                "attack_vector": "cloudfunctions.functions.setIamPolicy → bind to privileged SA",
                "persistence": "IAM binding persists across code updates",
            },
            {
                "name": "Secret Reference Theft",
                "description": "Reading secret environment variables via functions.get to steal referenced secrets.",
                "severity": "high",
                "attack_vector": "cloudfunctions.functions.get → read secret env var references",
                "persistence": "N/A — credential theft",
            },
        ],
        "remediation": [
            "Restrict cloudfunctions.functions.update to deployment service accounts.",
            "Use Binary Authorization for Cloud Functions.",
            "Use Secret Manager with versioned secrets and audit access.",
            "Implement VPC Service Controls around Cloud Functions.",
            "Monitor Audit Logs for function configuration changes.",
        ],
    },
    "azure": {
        "scenarios": [
            {
                "name": "Function App Code Deployment",
                "description": "Using webApps/functions or deployment slots to push malicious code to a Function App.",
                "severity": "critical",
                "attack_vector": "Microsoft.Web/sites/functions/action → deploy backdoor",
                "persistence": "Code persists in deployment slot",
            },
            {
                "name": "Managed Identity Token Theft",
                "description": "Modifying function code to fetch and exfiltrate the managed identity token via IMDS.",
                "severity": "critical",
                "attack_vector": "Modify function → curl IMDS token endpoint → exfiltrate",
                "persistence": "Code persists until redeployment",
            },
            {
                "name": "App Settings Modification",
                "description": "Modifying app settings to redirect function output to attacker-controlled storage.",
                "severity": "high",
                "attack_vector": "Microsoft.Web/sites/config/write → change connection strings",
                "persistence": "Config persists across restarts",
            },
        ],
        "remediation": [
            "Restrict deployment permissions to CI/CD pipelines.",
            "Use deployment slots with swap approval workflows.",
            "Enable managed identity with least-privilege RBAC assignments.",
            "Use Azure Key Vault references for secrets, not plaintext app settings.",
            "Monitor Activity Logs for function app configuration changes.",
        ],
    },
}

# EBS snapshot exfiltration scenarios
EBS_EXFIL = {
    "aws": {
        "scenarios": [
            {
                "name": "Cross-Account Snapshot Sharing",
                "description": "Sharing an EBS snapshot with an external AWS account allows the attacker to create a volume and extract data.",
                "severity": "critical",
                "attack_vector": "ModifySnapshotAttribute (createVolumePermission) → share with attacker account → copy snapshot → create volume",
                "data_at_risk": "Full disk contents including deleted files, credentials, application data",
            },
            {
                "name": "Public Snapshot Creation",
                "description": "Creating a public snapshot makes it accessible to all AWS users globally.",
                "severity": "critical",
                "attack_vector": "CreateSnapshot → ModifySnapshotAttribute (public) → anyone can copy",
                "data_at_risk": "Entire volume data",
            },
            {
                "name": "Snapshot Copy to Attacker Region",
                "description": "Copying a snapshot to a region the attacker controls, then sharing from there.",
                "severity": "high",
                "attack_vector": "CopySnapshot (encrypted=false, different region) → share from attacker region",
                "data_at_risk": "Volume data accessible in attacker-controlled region",
            },
            {
                "name": "Unencrypted Snapshot from Encrypted Volume",
                "description": "Creating an unencrypted snapshot of an encrypted volume bypasses KMS key policies.",
                "severity": "high",
                "attack_vector": "CreateSnapshot with encryption disabled → snapshot readable without KMS key",
                "data_at_risk": "Volume data without KMS protection",
            },
        ],
        "remediation": [
            "Deny ModifySnapshotAttribute and CreateSnapshot via SCP unless using approved KMS keys.",
            "Enable EBS encryption by default at the account level.",
            "Use AWS Config rules to detect public or cross-account snapshots.",
            "Monitor CloudTrail for CreateSnapshot and ModifySnapshotAttribute events.",
            "Restrict snapshot operations to specific IAM roles used by backup services.",
        ],
    },
    "gcp": {
        "scenarios": [
            {
                "name": "Cross-Project Snapshot Sharing",
                "description": "Sharing a snapshot with another project allows the attacker to create a disk and access data.",
                "severity": "critical",
                "attack_vector": "SetIamPolicy on snapshot → grant roles/compute.storageAdmin to attacker → create disk from snapshot",
                "data_at_risk": "Full disk contents",
            },
            {
                "name": "Snapshot Export to Cloud Storage",
                "description": "Exporting a snapshot to a Cloud Storage bucket, then sharing the bucket publicly.",
                "severity": "high",
                "attack_vector": "Create snapshot → export to GCS → share bucket publicly",
                "data_at_risk": "Volume data in GCS bucket",
            },
            {
                "name": "Unencrypted Snapshot",
                "description": "Creating a snapshot without CMEK encryption, making it accessible without key permissions.",
                "severity": "medium",
                "attack_vector": "Create snapshot without kmsKey parameter → accessible without CMEK key",
                "data_at_risk": "Volume data without CMEK protection",
            },
        ],
        "remediation": [
            "Restrict compute.snapshots.setIamPolicy to backup service accounts.",
            "Enforce CMEK encryption on all snapshots via Organization Policy.",
            "Use Cloud DLP to scan exported snapshots for sensitive data.",
            "Monitor Audit Logs for snapshot IAM policy changes.",
            "Implement VPC Service Controls to limit snapshot export paths.",
        ],
    },
    "azure": {
        "scenarios": [
            {
                "name": "Cross-Subscription Snapshot Copy",
                "description": "Copying a snapshot to another subscription grants access to the disk data.",
                "severity": "critical",
                "attack_vector": "Microsoft.Compute/snapshots/copy → create in attacker subscription → attach to VM",
                "data_at_risk": "Full disk contents",
            },
            {
                "name": "SAS URI Generation",
                "description": "Generating a SAS URI for a snapshot allows time-limited but full access to download the disk.",
                "severity": "critical",
                "attack_vector": "Microsoft.Compute/snapshots/beginGetAccess action → SAS URI → download VHD",
                "data_at_risk": "Entire disk as downloadable VHD",
            },
            {
                "name": "Snapshot with Managed Disk Key Export",
                "description": "Exporting a snapshot that uses a different encryption key, bypassing Azure Key Vault access controls.",
                "severity": "high",
                "attack_vector": "Create snapshot with different encryption settings → access without original key",
                "data_at_risk": "Disk data accessible with different key",
            },
        ],
        "remediation": [
            "Restrict Microsoft.Compute/snapshots/beginGetAccess to backup roles only.",
            "Enforce Azure Disk Encryption on all managed disks and snapshots.",
            "Use Azure Policy to deny snapshot creation without encryption.",
            "Monitor Activity Logs for snapshot access operations.",
            "Implement RBAC with deny assignments on snapshot resources.",
        ],
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
    data = IAM_VECTORS[provider]

    findings = []
    for v in data["vectors"]:
        findings.append({
            "name": v["name"],
            "description": v["description"],
            "severity": v["severity"],
            "mitre_technique": v["mitre_technique"],
            "permissions_required": v["permissions_required"],
            "attack_chain": v["chain"],
        })

    summary = (
        f"Identified {len(findings)} IAM privilege escalation vectors for {provider.upper()}. "
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
    data = METADATA_SSRF[provider]

    findings = []
    for version_name, version_data in data["versions"].items():
        findings.append({
            "metadata_service": version_name,
            "url": data["metadata_url"],
            "description": version_data["description"],
            "severity": version_data["severity"],
            "exploit_example": version_data["exploit"],
        })

    # Add provider-specific findings
    for finding in data["findings"]:
        findings.append({
            "name": finding,
            "severity": "high",
            "type": "configuration_finding",
        })

    summary = (
        f"Metadata SSRF analysis for {provider.upper()}: {len(data['versions'])} service version(s), "
        f"{len(data['findings'])} configuration finding(s). "
        f"Primary risk: credential theft via SSRF."
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
    data = S3_EXPOSURE[provider]

    findings = []
    for s in data["scenarios"]:
        findings.append({
            "name": s["name"],
            "description": s["description"],
            "severity": s["severity"],
            "indicator": s["indicator"],
            "data_at_risk": s["data_at_risk"],
        })

    summary = (
        f"Storage exposure analysis for {provider.upper()}: {len(findings)} scenario(s) identified. "
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
    data = LAMBDA_BACKDOOR[provider]

    findings = []
    for s in data["scenarios"]:
        findings.append({
            "name": s["name"],
            "description": s["description"],
            "severity": s["severity"],
            "attack_vector": s["attack_vector"],
            "persistence_mechanism": s["persistence"],
        })

    summary = (
        f"Serverless backdoor analysis for {provider.upper()}: {len(findings)} scenario(s). "
        f"Critical: {sum(1 for f in findings if f['severity'] == 'critical')}, "
        f"High: {sum(1 for f in findings if f['severity'] == 'high')}. "
        f"Persistence via code/config modification is the primary concern."
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
    data = EBS_EXFIL[provider]

    findings = []
    for s in data["scenarios"]:
        findings.append({
            "name": s["name"],
            "description": s["description"],
            "severity": s["severity"],
            "attack_vector": s["attack_vector"],
            "data_at_risk": s["data_at_risk"],
        })

    summary = (
        f"Snapshot exfiltration analysis for {provider.upper()}: {len(findings)} scenario(s). "
        f"Critical: {sum(1 for f in findings if f['severity'] == 'critical')}, "
        f"High: {sum(1 for f in findings if f['severity'] == 'high')}. "
        f"Cross-account sharing and public access are the top risks."
    )

    return _build_result(provider, "ebs_exfil", findings, data["remediation"], summary)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(transport="stdio")
