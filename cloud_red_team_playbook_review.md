# Security Review: cloud_red_team_playbook.py

**Date:** 2026-09-13
**Auditor:** Bionic Daughter (Hermes Agent)
**File:** `cloud_red_team_playbook.py`
**Size:** 892 lines, 43,718 bytes
**Type:** Cloud pentesting playbook generator — AWS attack scenarios, detection rules, MITRE ATT&CK mapping

---

## Executive Summary

`cloud_red_team_playbook.py` is a **Cloud Red Team Playbook Generator** — a Python tool that constructs structured, professional documentation for cloud security testing. It does **not** execute real attacks or make network connections. Instead, it uses a simulation engine with seeded random number generation to produce realistic-looking but entirely fake output, then assembles Markdown or JSON reports containing attack scenarios, detection rules, and remediation guidance.

The file contains 5 AWS-specific attack scenarios covering the cloud kill chain from initial access through data exfiltration. Each scenario maps to MITRE ATT&CK techniques and includes CloudTrail detection queries. The tool is well-structured, cleanly written, and serves a legitimate dual-use purpose: enabling authorized red team operations while simultaneously providing defensive detection guidance.

**Verdict:** Legitimate security documentation tool with moderate dual-use sensitivity. Not an exploit kit — no actual attack code, no credential processing, no network I/O. However, it consolidates attack techniques with copy-paste-ready AWS CLI commands, lowering the barrier for misuse. File-level access controls recommended.

---

## What This Tool Does

This is a **generator, not an attacker**. Its workflow:

1. **Data Model Definition** — Defines structured dataclasses for scenarios, attack steps, detection rules
2. **Simulation Engine** — Uses `random.Random(seed=42)` to generate reproducible fake output (ARNs, credentials, snapshots)
3. **Scenario Builder** — Constructs 5 complete AWS attack scenarios as in-memory objects
4. **Report Generator** — Outputs Markdown or JSON with attack steps, fake simulated output, detection rules, and remediation guidance

Key architectural points:
- **No network calls** — all "attacks" are string templates populated by the simulator
- **No credential handling** — no AWS SDK, no API calls, no key storage
- **Seeded RNG** — deterministic output (seed=42) for reproducible reports
- **Clear simulation markers** — all fake data includes `[SIM]` tags or obviously randomized values

---

## 5 Attack Scenarios Covered

### Scenario 1: AWS-001 — IAM Privilege Escalation via Policy Manipulation
| Field | Value |
|-------|-------|
| **Severity** | CRITICAL |
| **MITRE ATT&CK** | TA0004 (Privilege Escalation) — T1078.004 Valid Accounts: Cloud Accounts |
| **Steps** | 3 |
| **Detection Rules** | 3 |

**Attack Chain:**
1. Enumerate IAM permissions (`list-attached-user-policies`, `simulate-principal-policy`)
2. Attach AdministratorAccess policy to current user
3. Verify elevated access (`get-caller-identity`, `list-users`)

**What it teaches:** How over-permissive IAM roles (granting `iam:AttachUserPolicy` to non-admin users) enable trivial privilege escalation. The detection rules focus on API call patterns in CloudTrail.

### Scenario 2: AWS-002 — Metadata Service SSRF Credential Theft
| Field | Value |
|-------|-------|
| **Severity** | CRITICAL |
| **MITRE ATT&CK** | TA0006 (Credential Access) — T1552.005 Unsecured Credentials: Cloud Instance Metadata API |
| **Steps** | 4 |
| **Detection Rules** | 2 |

**Attack Chain:**
1. Confirm SSRF vulnerability by requesting `http://169.254.169.254/latest/meta-data/`
2. Enumerate IAM role name via metadata endpoint
3. Exfiltrate temporary credentials (`AccessKeyId`, `SecretAccessKey`, `Token`)
4. Configure stolen credentials in AWS CLI

**What it teaches:** The classic cloud SSRF→IMDS attack pattern. Highlights the IMDSv1 vs IMDSv2 distinction. Detection uses VPC Flow Logs to catch traffic to the metadata IP.

### Scenario 3: AWS-003 — S3 Bucket Data Exposure & Exfiltration
| Field | Value |
|-------|-------|
| **Severity** | HIGH |
| **MITRE ATT&CK** | TA0010 (Exfiltration) — T1530 Data from Cloud Storage |
| **Steps** | 3 |
| **Detection Rules** | 2 |

**Attack Chain:**
1. List all S3 buckets (`s3api list-buckets`)
2. Check ACLs for public access (`get-bucket-acl`, check for AllUsers/AuthenticatedUsers)
3. Download exposed data (`s3 sync` with `--no-sign-request`)

**What it teaches:** How S3 bucket misconfigurations (disabled Block Public Access, permissive ACLs) lead to data breaches. Detection focuses on ACL changes and anomalous download patterns.

### Scenario 4: AWS-004 — Lambda Function Backdoor & Persistence
| Field | Value |
|-------|-------|
| **Severity** | HIGH |
| **MITRE ATT&CK** | TA0008 (Lateral Movement) — T1059.006 Command and Scripting Interpreter: Python |
| **Steps** | 4 |
| **Detection Rules** | 2 |

**Attack Chain:**
1. Identify exploitable Lambda execution roles
2. Deploy backdoored Lambda function (`create-function` with disguised name)
3. Establish persistence via CloudWatch Events rule (`rate(5 minutes)`)
4. Confirm callback and persistence

**What it teaches:** Serverless persistence techniques. Lambda functions are often overlooked in incident response. Detection focuses on anomalous function creation and EventBridge rules targeting new functions.

### Scenario 5: AWS-005 — EBS Snapshot Exfiltration via Cross-Account Sharing
| Field | Value |
|-------|-------|
| **Severity** | CRITICAL |
| **MITRE ATT&CK** | TA0010 (Exfiltration) — T1537 Transfer Data to Cloud Account |
| **Steps** | 3 |
| **Detection Rules** | 2 |

**Attack Chain:**
1. Identify sensitive production volumes (`describe-volumes` with tag filters)
2. Create EBS snapshots of identified volumes
3. Modify snapshot attributes to share with external account (`modify-snapshot-attribute`)

**What it teaches:** How to bypass network controls by sharing EBS snapshots directly with attacker accounts. Detection focuses on snapshot creation outside backup windows and cross-account permission changes.

---

## Detection Rules Quality Assessment

The file contains **12 detection rules** across all scenarios. Evaluation:

### Strengths
- **Real data sources** — CloudTrail, VPC Flow Logs, S3 Server Access Logs are the correct sources for cloud detection
- **Practical query syntax** — Uses AWS CloudTrail Insights-like query syntax with `fields`, `filter`, `stats`, `bin()` that closely matches real AWS Athena/CloudTrail Insights queries
- **False positive documentation** — Each rule includes realistic false positive scenarios (compliance scanning, break-glass access, CDN warming)
- **Severity-appropriate** — Critical actions (policy attachment, snapshot sharing) get CRITICAL severity; reconnaissance gets HIGH
- **Detection coverage** — Covers all 5 scenarios with at least 1 detection rule per scenario

### Weaknesses
- **Some rules are step-specific, not behavioral** — DET-AWS-001c ("Privilege Verification After Escalation") requires knowing `escalation_time` — an external input not available in real-time detection
- **Thresholds may need tuning** — `enum_count > 10` and `downloads > 100` are arbitrary; real environments need calibration
- **No behavioral baselines** — Rules don't account for "normal" per-user API volume (a developer might legitimately make 20 IAM calls)
- **Missing encryption detection** — For EBS snapshots, doesn't detect when encrypted volumes are shared (encryption doesn't prevent cross-account sharing of the snapshot itself)

### Detection Rules Summary Table

| Rule ID | Title | Severity | Data Source |
|---------|-------|----------|-------------|
| DET-AWS-001a | IAM Policy Enumeration Detection | HIGH | CloudTrail |
| DET-AWS-001b | Admin Policy Attachment Alert | CRITICAL | CloudTrail |
| DET-AWS-001c | Privilege Verification After Escalation | HIGH | CloudTrail |
| DET-AWS-002a | SSRF to Metadata Service Detection | HIGH | VPC Flow Logs + App Logs |
| DET-AWS-002b | IMDS Credential Access from Web App | CRITICAL | CloudTrail + VPC Flow Logs |
| DET-AWS-003a | S3 Public Access Configuration Change | HIGH | CloudTrail |
| DET-AWS-003b | Mass S3 Object Download from External IP | HIGH | CloudTrail + S3 Access Logs |
| DET-AWS-004a | Suspicious Lambda Function Creation | HIGH | CloudTrail |
| DET-AWS-004b | Lambda Persistence via EventBridge Rule | HIGH | CloudTrail |
| DET-AWS-005a | EBS Snapshot Creation Alert | HIGH | CloudTrail |
| DET-AWS-005b | EBS Snapshot Shared with External Account | CRITICAL | CloudTrail |

---

## MITRE ATT&CK Mapping Accuracy

| Scenario | Technique ID | Technique Name | Tactic | Accuracy |
|----------|-------------|----------------|--------|----------|
| AWS-001 | T1078.004 | Valid Accounts: Cloud Accounts | TA0004 Privilege Escalation | ✅ Correct — privilege escalation via cloud account policy manipulation |
| AWS-002 | T1552.005 | Unsecured Credentials: Cloud Instance Metadata API | TA0006 Credential Access | ✅ Correct — classic IMDS credential theft |
| AWS-003 | T1530 | Data from Cloud Storage | TA0010 Exfiltration | ✅ Correct — S3 bucket data exfiltration |
| AWS-004 | T1059.006 | Command and Scripting Interpreter: Python | TA0008 Lateral Movement | ⚠️ Partial — Lambda is T1648 (Serverless Execution) for the technique; T1059.006 is for the runtime. Lateral movement is debatable — persistence would be more accurate (TA0003) |
| AWS-005 | T1537 | Transfer Data to Cloud Account | TA0010 Exfiltration | ✅ Correct — snapshot sharing is documented as T1537 |

**Assessment:** 4/5 accurate mappings. AWS-004's MITRE mapping is slightly off — the scenario is more about persistence (TA0003) and serverless execution (T1648) than lateral movement via Python.

---

## Defensive Utility

**High defensive value.** This file provides:

1. **Ready-to-deploy detection rules** — 12 CloudTrail/Flow Log queries that can be adapted for AWS Athena, Splunk, or Elastic
2. **Attack pattern education** — Teaches defenders what to look for
3. **Remediation guidance** — Each scenario includes 4-6 specific remediation actions:
   - SCPs to prevent IAM actions
   - IMDSv2 enforcement
   - S3 Block Public Access
   - Lambda code signing
   - EBS encryption with CMK
4. **References** — Links to authoritative sources (AWS docs, MITRE ATT&CK, Splunk research)

The detection rules alone justify the file's existence — they're practical, well-structured, and cover common cloud attack patterns.

---

## Dual-Use Concerns

### Risk Level: MODERATE

**Why it's NOT high risk:**
- No actual exploit code — all "attacks" are string templates
- No credential processing or storage
- No network connections or API calls
- No obfuscation or anti-forensics techniques
- All simulated data is clearly fake (seeded RNG, `[SIM]` markers)

**Why it IS dual-use:**
- **Copy-paste attack commands** — Real AWS CLI commands that work if you have credentials:
  ```
  aws iam attach-user-policy --user-name $USER --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
  aws ec2 modify-snapshot-attribute --snapshot-id snap-... --attribute createVolumePermission --user-ids 999888777666
  ```
- **Consolidated knowledge** — Gathers 5 attack techniques in one easy-to-reference document
- **Lowered barrier** — Provides step-by-step execution paths that a novice could follow
- **Lambda backdoor reference** — References "backdoor.zip" and reverse shell callbacks (though no actual payload is included)

### Comparison to Public Resources

This file is comparable to publicly available resources:
- [Rhino Security Labs AWS Privilege Escalation](https://rhinosecuritylabs.com/aws/aws-privilege-escalation-methods-mitigation/)
- [MITRE ATT&CK Cloud Matrix](https://attack.mitre.org/matrices/enterprise/cloud/)
- [AWS Well-Architected Security Pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/)
- Cloud penetration learning certifications (CCSP, AWS Security Specialty)

The attack commands are standard AWS CLI operations that any cloud administrator or security professional would know. The file does not contain novel exploits or zero-days.

---

## Code Quality Assessment

### Strengths
- **Clean architecture** — Data models, simulation engine, and report generators are cleanly separated
- **Type hints** — Uses `typing`, `dataclasses`, `Enum` for structured code
- **Deterministic output** — Seeded RNG ensures reproducible reports
- **No external dependencies** — Uses only Python standard library (`json`, `argparse`, `random`, `hashlib`, `textwrap`, `datetime`)
- **Error-free** — No syntax errors, clean structure

### Weaknesses
- **MITRE mapping for AWS-004** — As noted, the technique mapping is slightly off
- **Detection query syntax** — Uses a pseudo-SQL that resembles but doesn't exactly match AWS Athena or CloudTrail Insights syntax. Real deployment requires syntax adaptation.
- **No input validation** — CLI args are not validated (output path could be any string)

---

## Red Flags Checklist

| Concern | Present? | Severity |
|---------|----------|----------|
| Actual exploit code | ❌ No | — |
| Credential harvesting | ❌ No | — |
| Network connections | ❌ No | — |
| Obfuscation/encoding | ❌ No | — |
| Anti-forensics techniques | ❌ No | — |
| Malicious payload generation | ❌ No | — |
| Real AWS account IDs | ❌ No | — |
| Real credentials | ❌ No | — |
| Copy-paste attack commands | ✅ Yes | Low |
| Novel zero-day exploits | ❌ No | — |

---

## Verdict

**Classification:** Legitimate security documentation tool with moderate dual-use potential.

**Summary:** This is a well-structured, cleanly written cloud security playbook generator. It does not perform attacks, process credentials, or make network connections. Its primary function is educational and defensive — providing detection rules, remediation guidance, and MITRE ATT&CK mapping. The copy-paste AWS CLI commands pose a minor dual-use concern, but these are standard operations available in any AWS documentation.

**Recommendations:**
1. ✅ **File-level access controls** — Restrict access to authorized security team members
2. ✅ **Authorization disclaimer** — Already present in output ("For authorized security testing only")
3. ⚠️ **MITRE mapping fix** — AWS-004 should map to T1648 (Serverless Execution) and TA0003 (Persistence) instead of T1059.006 and TA0008
4. ⚠️ **Detection query adaptation** — Add comments noting that query syntax may need adjustment for specific SIEM platforms (Athena, Splunk, Elastic)

**Risk Rating:** LOW (as a tool) | MODERATE (as documentation with copy-paste commands)

**Acceptable for:** Authorized security teams, cloud penetration testers, red/blue team exercises, security training programs.

**Not recommended for:** Public distribution without access controls, environments without clear authorization frameworks.

---

*Review completed by Bionic Daughter — Hermes Agent*
*Saved to: C:\Users\mobil\orca\projects\my 1st\cloud_red_team_playbook_review.md*
*Also saved to: C:\Users\mobil\Documents\Obsidian Vault\10 AUDIT\cloud_red_team_playbook_review.md*
