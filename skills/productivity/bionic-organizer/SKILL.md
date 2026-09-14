---
name: bionic-organizer
description: "Project organization and task coordination for Bionic Daughter."
version: 1.0.0
author: Bionic Daughter
license: MIT
platforms: [linux, macos, win32]
metadata:
  hermes:
    category: productivity
    tags: [organization, task-management, coordination, subagent-dispatch, testing, labs]
    related_skills: [weekly-review-planning, meeting-action-items]
---

# Bionic Organizer Skill

## When to Use

- Starting any new work session — load this skill to get oriented on what's done and pending
- Dispatching subagents — use the task taxonomy to assign work clearly
- After subagents complete — update task list and audit report
- Before testing tools/skills in labs — check what's been tested

## Quick Reference

| Resource | Location |
|----------|----------|
| Master Task List | `MASTER_TASK_LIST.md` (project root) |
| Audit Report | `BIONIC_DAUGHTER_AUDIT.md` (project root + Obsidian) |
| Progress Tracker | `BIONIC_DAUGHTER_PROGRESS.md` (project root) |
| Obsidian Vault | `C:/Users/mobil/Documents/Obsidian Vault/10 AUDIT/` |
| Python Landscape | `python_landscape_report.md` (project root) |

## Task Taxonomies

### Security Review Tiers

**Tier 1 — Offensive Security (highest priority):**
- cloud_red_team_playbook.py — cloud pentesting playbook
- redteam/MCP_Red_Team_Agent/ — red team agent framework
- redteam/autopentest-ai/ — automated pentesting AI

**Tier 2 — Bionic Infrastructure:**
- defi_exploit_automation.py — DeFi exploits
- malware_analysis_sandbox.py — malware analysis
- cti_feed_ingestion.py — CTI processing
- bionic-vuln-lab/ — vulnerable app lab
- bionic-core/ — MCP servers, audit pipelines, bounty sweepers

**Tier 3 — Remaining Root .py Files:**
- All remaining unreviewed root-level .py files

### Skill Development Pipeline

1. Survey — Understand what the tool/skill does
2. Review — Assess quality, identify issues
3. Enhance — Fix issues, add missing pieces
4. Package — Create proper SKILL.md with frontmatter
5. Test — Verify in lab environment
6. Document — Update reports and task list

### Lab Testing Protocol

1. Identify the tool/skill to test
2. Set up isolated lab environment
3. Run tool with known inputs
4. Capture outputs and verify expected behavior
5. Document results — pass/fail, issues found
6. Update task list with test results

## Subagent Dispatch Templates

### Security Review
```
Goal: Review [file/directory] — [description]
Context: Read MASTER_TASK_LIST.md and BIONIC_DAUGHTER_AUDIT.md first.
After review, update both files. Save findings to Obsidian Vault/10 AUDIT/.
```

### Skill Development
```
Goal: Develop and package [skill/tool name] as a proper Hermes skill
Context: Survey the tool at [path], create SKILL.md, enhance if needed, test it.
Update MASTER_TASK_LIST.md and BIONIC_DAUGHTER_AUDIT.md.
```

### Lab Testing
```
Goal: Test [tool/skill name] in an isolated lab environment
Context: Set up lab, run tool with known inputs, capture outputs, verify behavior.
NEVER test on production systems. Update task list with results.
```

## Progress Tracking Protocol

After ANY significant work:
1. Update `MASTER_TASK_LIST.md`
2. Update `BIONIC_DAUGHTER_AUDIT.md`
3. Save major findings to Obsidian Vault/10 AUDIT/
4. Update `BIONIC_DAUGHTER_PROGRESS.md`

## Coordination Rules

- Max 3 subagents concurrently
- Each subagent should read MASTER_TASK_LIST.md and BIONIC_DAUGHTER_AUDIT.md first
- Subagents report back with: what they did, findings, files changed
- After subagent batch completes, update both tracking files
- Don't dispatch overlapping work
