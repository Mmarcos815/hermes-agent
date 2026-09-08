# Pentest Engagement Package

A reusable kit for planning, executing, and reporting a penetration test.
All documents are templates — fill in per-engagement details before kickoff.

## Files

| File | Purpose |
|------|---------|
| `README.md` | This file — methodology overview |
| `scope_template.md` | Define in-scope / out-of-scope targets |
| `rules_of_engagement.md` | ROE — boundaries, contacts, escalation |
| `report_template.md` | Final deliverable (exec summary + tech findings) |
| `finding_template.md` | Per-finding write-up |
| `evidence_tracker.py` | Chain-of-custody log for screenshots, packets, notes |

## Methodology

Follows the **Penetration Testing Execution Standard (PTES)** with a
slight bias toward speed on time-boxed engagements.

### 1. Pre-engagement
- Sign ROE and NDA. Confirm emergency contacts and "stop" triggers.
- Fill `scope_template.md`. Get written authorization (email is fine).
- Agree on comms channel (Signal, email, ticket system) and cadence.

### 2. Reconnaissance
- **Passive** — OSINT, DNS, WHOIS, Shodan, Google dorks, LinkedIn recon.
- **Active** — port scan (`nmap`), service enumeration, tech fingerprinting.
- Recon findings feed directly into the attack surface table in the scope doc.

### 3. Threat Modeling
- Map attacker goals to high-value assets.
- Rank attack vectors: external vs internal, authenticated vs unauthenticated.
- Prioritize: internet-facing services > internal pivoting > social engineering.

### 4. Vulnerability Analysis
- Cross-reference found services with CVE/NVD, exploit-db, vendor advisories.
- Manual verification of scanner results — never ship unverified Nessus hits.
- Use `finding_template.md` to draft findings as you go.

### 5. Exploitation
- Attempt to confirm high-value vulns with safe, non-destructive exploits.
- Stay within ROE — no DoS, no production data exfil without approval.
- Log every command with timestamps in `evidence_tracker.py`.

### 6. Post-Exploitation (if in scope)
- Demonstrate impact: read a file, dump creds, lateral-move one hop.
- **Do not** persist, pivot to third parties, or modify production data.
- Document access level gained and business impact.

### 7. Reporting
- Fill `report_template.md` — executive summary first, then technical findings.
- Each finding gets a CVSS score, evidence reference, and remediation step.
- Deliver draft → client review → final report → retest.

## Evidence Handling

- Screenshots, packet captures, and logs are immutable artifacts.
- `evidence_tracker.py` timestamps and hashes each piece at collection time.
- Store originals in a read-only directory; work on copies only.

## Tools (common)

- `nmap` — port scanning
- `nikto` / `nuclei` — vuln scanning
- `burpsuite` — web proxy
- `metasploit` — exploitation framework
- `bloodhound` / `python bloodhound` — AD enumeration
- `impacket` — Windows protocol toolkit
- `sqlmap` — SQL injection (auth only)
- `gobuster` / `ffuf` — directory brute-force
- `john` / `hashcat` — password cracking (offline only)

## Disclaimer

These templates are for **authorized testing only**. Unauthorized access
to computer systems is a crime in most jurisdictions. Always get written
permission before you touch a target.
