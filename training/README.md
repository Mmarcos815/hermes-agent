# Red Team Operations Training Platform

## Overview

This platform teaches red team operations — simulating real-world adversaries to
test organizational defenses. Covers the full attack lifecycle with emphasis on
ethical conduct and defensive feedback.

## Audience

- Security professionals learning offensive skills
- Penetration testers expanding into adversary simulation
- Blue teamers understanding attacker methodologies

## Prerequisites

- **Networking:** TCP/IP, DNS, HTTP/HTTPS, firewalls
- **OS:** Linux CLI and Windows administration basics
- **Scripting:** Basic Python or Bash
- **Security:** Familiarity with OWASP Top 10, CIA triad

## Hardware Requirements

- 16 GB RAM minimum (32 GB recommended)
- 100 GB free disk space
- Virtualization support (VT-x / AMD-V) enabled

## Required Software

- VMware Workstation or VirtualBox
- Kali Linux (attacker VM)
- Target VMs: Metasploitable, DVWA, VulnHub images

## Rules of Engagement

1. Only attack systems you own or have written authorization to test
2. All labs run in an isolated virtual network — no traffic leaves the host
3. Document every finding
4. Report any accidental out-of-scope activity immediately

## Structure

- **20 modules** covering the full red team lifecycle
- Each module: theory + hands-on lab + written report
- Duration: 8–12 weeks at 8–10 hours/week
- Final capstone: full adversary simulation

## Grading

| Component        | Weight |
|------------------|--------|
| Module labs      | 40%    |
| Module reports   | 30%    |
| Capstone         | 20%    |
| Peer review      | 10%    |
