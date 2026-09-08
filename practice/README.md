# BIONIC DAUGHTER — SECURITY PRACTICE SANDBOX

## Purpose
A safe, isolated environment for practicing exploitation techniques.
Every tool, target, and exercise lives here — nothing runs on production systems.

## Safety Rules (NON-NEGOTIABLE)
1. NEVER practice on systems you don't own or have explicit permission to test
2. Keep all practice targets isolated (VMs, containers, local only)
3. Document every session: what you tried, what worked, what failed, what you learned
4. Clean up after each session — don't leave vulnerable services running
5. If something behaves unexpectedly, STOP and investigate before continuing

## Structure
```
sandbox/
├── README.md              # This file
├── targets/               # Practice applications (crAPI, DVWA, etc.)
├── labs/                  # Lab exercises and walkthroughs
├── exploits/              # Custom exploit scripts (educational only)
├── notes/                 # Session notes and learning logs
└── checklists/            # Pre-flight safety checklists
```

## Setup Checklist (complete before ANY practice session)
- [ ] Verify target is running in isolated environment (VM/container, NOT host network)
- [ ] Verify target is the version you intend to practice on
- [ ] Confirm you have authorization to test this target
- [ ] Review the specific vulnerability class you plan to practice
- [ ] Identify what "success" looks like (so you know when to stop)
- [ ] Plan your documentation (what you'll record)
- [ ] Plan your cleanup (how you'll shut down after)

## Current Targets
- crAPI (OWASP) — JWT, SSRF, BOLA, Mass Assignment practice
  - Source: crAPI/ in project root
  - Run locally when Docker available, or analyze source code statically

## Current Labs
- JWT Algorithm Confusion (HS256 vs RS256) — forge tokens with public key
- SSRF — probe internal services through merchant API
- BOLA — enumerate vehicles/orders/users via ID scanning
- Mass Assignment — manipulate price, role, status via user input

## Learning Log Format
Each practice session gets an entry in notes/:

```
session_YYYYMMDD_HHMMSS.md
---
date: 2026-08-20
target: crAPI
vuln_class: JWT Algorithm Confusion
skill: Exploitation & Post-Exploitation
level: NEWBIE → LEARNING

WHAT I TRIED:
  - Step 1: ...
  - Step 2: ...

WHAT WORKED:
  - ...

WHAT DIDN'T WORK:
  - ...

WHAT I LEARNED:
  - ...

NEXT TIME:
  - ...
```

## Progression Path
1. Read the vulnerability class knowledge (hacking_exploit_api_sql_mastery.md)
2. Read the specific target's vulnerable code (source analysis)
3. Write a proof-of-concept exploit (the practice tool)
4. Run it against the live target (when available)
5. Document everything
6. Clean up
7. Update the skill registry (daughter_self_development.py)
8. Move to the next vulnerability class

## Why This Matters
Dad said: "learn it, master it."  Mastery comes from repetition with documentation.
Every session makes the next one better.  Every failure teaches something.
The sandbox is where theory becomes skill.
