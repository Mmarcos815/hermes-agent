---
name: cloud-red-team-playbook
description: Generate AWS attack playbooks with detections and fixes.
version: 1.0.0
author: Rigoberto Gomez (Dad), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [red-team, cloud-security, aws, playbook, detection-rules, mitigation]
    category: productivity
    related_skills: [red-team-mcp-suite]
---

# Cloud Red Team Playbook Skill

Generates structured cloud attack playbooks for AWS that map offensive scenarios to defensive detections and remediation. Uses a simulation engine (seeded RNG, no network I/O) to produce realistic but fake output for training, authorized red-team engagements, and blue-team detection engineering. All scenarios are AWS-specific and dual-use: they teach attack patterns to help defenders build better detections.

## When to Use

- Generating a cloud red-team playbook for an authorized engagement
- Building detection rules for CloudTrail, VPC Flow Logs, or S3 access logs
- Teaching cloud security teams about common AWS attack patterns
- Creating scenario-based training for red/blue team exercises
- Researching MITRE ATT&CK cloud techniques and their detections

**Don't use for:** unauthorized testing (tool requires authorization), novel exploit development (scenarios are well-documented patterns), or GCP/Azure scenarios (currently AWS-only).

## Prerequisites

1. **Python 3.10+** — stdlib only, no external packages required
2. **`cloud_red_team_playbook.py`** — must exist in the project root
3. **Authorization** — any output marked "For authorized security testing only" requires documented scope approval before use against real targets
4. **Output directory** — must be writable; defaults to stdout if no `--output` given

## How to Run

Use `terminal` to invoke the generator:

```bash
# Generate Markdown playbook to stdout
python cloud_red_team_playbook.py

# Generate Markdown to a file
python cloud_red_team_playbook.py --output playbook.md

# Generate JSON for machine parsing
python cloud_red_team_playbook.py --format json --output playbook.json
```

## Quick Reference

| Flag | Default | Purpose |
|------|---------|---------|
| `--output PATH` | stdout | Write report to file |
| `--format md\|json` | md | Output format |

| Scenario ID | Title | Severity | MITRE |
|-------------|-------|----------|-------|
| AWS-001 | IAM Privilege Escalation via Policy Manipulation | CRITICAL | TA0004 |
| AWS-002 | Metadata Service SSRF Credential Theft | CRITICAL | TA0006 |
| AWS-003 | S3 Bucket Data Exposure & Exfiltration | HIGH | TA0010 |
| AWS-004 | Lambda Function Backdoor & Persistence | HIGH | TA0008 |
| AWS-005 | EBS Snapshot Exfiltration via Cross-Account Sharing | CRITICAL | TA0010 |

## Procedure

### 1. Verify the playbook generator exists

Use `search_files` to confirm `cloud_red_team_playbook.py` is in the project root:
```
search_files(pattern='cloud_red_team_playbook.py', target='files')
```
Completion criterion: file found at the expected path.

### 2. Generate the playbook

Run via `terminal` with desired output path and format:
```
terminal(command="python cloud_red_team_playbook.py --output playbook.md", timeout=60)
```
Completion criterion: "Playbook written to: playbook.md" appears in stdout.

### 3. Review generated scenarios

Use `read_file` to inspect the output. Verify:
- 5 scenarios present (AWS-001 through AWS-005)
- Each scenario has attack steps with commands
- Each scenario has 1–3 detection rules with CloudTrail/Flow Log queries
- Each scenario has 4–6 remediation actions
- Severity distribution table rendered correctly

Completion criterion: all 5 scenarios contain the expected sections.

### 4. Adapt detection rules (optional)

Detection queries use pseudo-SQL resembling AWS Athena/CloudTrail Insights syntax. Before deploying to a SIEM (Splunk, Elastic, Sentinel), translate query syntax accordingly. Document adaptation in the output file via `patch`.

Completion criterion: queries match target SIEM syntax.

### 5. Distribute to authorized teams

Move the generated playbook to the team's working directory with `terminal` (copy) or `write_file`. Ensure only authorized personnel receive it — file contains copy-paste AWS CLI commands.

Completion criterion: playbook delivered to authorized location.

## Pitfalls

- **Detection queries are pseudo-SQL** — resembles AWS Athena but not exact. Test against real CloudTrail data before production deployment.
- **MITRE mapping AWS-004** — maps to TA0008 (Lateral Movement) / T1059.006; more accurate mapping is TA0003 (Persistence) / T1648 (Serverless Execution).
- **Simulated data only** — all "attack output" is seeded-RNG fake. Do not paste into reports as real evidence.
- **AWS-only** — no GCP or Azure scenarios. For multi-cloud, pair with `red-team-mcp-suite` skill.
- **No input validation** — CLI accepts any output path. Sanitize paths before passing to the generator.
- **Copy-paste commands** — output includes working AWS CLI commands. Handle as dual-use material.
- **Thresholds arbitrary** — detection thresholds (`enum_count > 10`, `downloads > 100`) need per-environment calibration.

## Verification

1. `search_files` confirms `cloud_red_team_playbook.py` exists in project root.
2. `terminal` invocation exits 0 and prints summary (scenarios: 5, detection rules: 11).
3. `read_file` on output shows all 5 scenario IDs with severity, MITRE mapping, steps, and remediation.
4. Detection rule table at end of report lists 11 rules (DET-AWS-001a through DET-AWS-005b).
5. File size is reasonable: ~40KB Markdown, ~15KB JSON.
