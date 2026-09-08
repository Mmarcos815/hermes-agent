# RED TEAM OPERATIONS PLAYBOOK

**Version:** 1.0  
**Date:** September 2026  
**Author:** Bionic Daughter (for Dad)  
**Scope:** Authorized security testing only

---

## TABLE OF CONTENTS

1. Pre-Engagement
2. Reconnaissance Methodology
3. Vulnerability Discovery
4. Exploitation Methodology
5. Post-Exploitation
6. Reporting
7. Operational Security
8. Tools & Infrastructure

---

## 1. PRE-ENGAGEMENT

### 1.1 Authorization

| Step | Action | Done |
|------|--------|------|
| 1 | Obtain written authorization from target owner | ☐ |
| 2 | Define scope (IPs, domains, applications, timeframes) | ☐ |
| 3 | Sign rules of engagement (RoE) document | ☐ |
| 4 | Define emergency contacts and escalation paths | ☐ |
| 5 | Verify insurance and legal coverage | ☐ |

### 1.2 Scope Definition

| In Scope | Out of Scope |
|----------|--------------|
| Defined IP ranges/ranges | Production systems without written auth |
| Defined domains/subdomains | Third-party services |
| Defined applications | Physical security (unless specified) |
| Social engineering (if specified) | Denial of Service attacks |

### 1.3 Rules of Engagement

| Rule | Description |
|------|-------------|
| **Authorization** | Only test systems within defined scope |
| **Minimal Impact** | Avoid disrupting business operations |
| **Documentation** | Record every action with timestamps |
| **Cleanup** | Remove all artifacts, accounts, and access after engagement |
| **Reporting** | Report all findings to Dad only |
| **Stop Condition** | Immediately stop if critical vulnerability found in production |

---

## 2. RECONNAISSANCE METHODOLOGY

### 2.1 Passive Reconnaissance

| Tool | Purpose | Command |
|------|---------|---------|
| whois | Domain registration info | `whois example.com` |
| nslookup | DNS records | `nslookup example.com` |
| dig | Detailed DNS enumeration | `dig example.com ANY` |
| shodan | Internet-facing assets | `shodan search example.com` |
| censys | Certificate and asset search | `censys search example.com` |
| theHarvester | Email and subdomain enumeration | `theHarvester -d example.com` |
| amass | Subdomain enumeration | `amass enum -d example.com` |
| subfinder | Fast subdomain discovery | `subfinder -d example.com` |

### 2.2 Active Reconnaissance

| Tool | Purpose | Command |
|------|---------|---------|
| nmap | Port scanning | `nmap -sV -sC -O target` |
| masscan | Fast port scanning | `masscan -p1-65535 target` |
| httpx | HTTP probing | `httpx -l subdomains.txt` |
| nuclei | Vulnerability scanning | `nuclei -u target` |
| nikto | Web server scanning | `nikto -h target` |
| dirb | Directory brute forcing | `dirb http://target` |
| gobuster | Directory/DNS brute forcing | `gobuster dir -u target -w wordlist.txt` |

### 2.3 OSINT Techniques

| Technique | Tool | Description |
|-----------|------|-------------|
| Google Dorking | N/A | Advanced search operators for sensitive data |
| GitHub Dorking | N/A | Find leaked credentials and source code |
| Social Media | spiderfoot | Automated OSINT collection |
| Email Hunting | hunter.io | Find email addresses for target domain |
| Breach Data | haveibeenpwned | Check for compromised credentials |
| Certificate Transparency | crt.sh | Find subdomains from SSL certificates |
| Wayback Machine | web.archive.org | Historical website snapshots |

---

## 3. VULNERABILITY DISCOVERY

### 3.1 Web Application

| Category | Tool | Description |
|----------|------|-------------|
| SQL Injection | sqlmap | Automated SQL injection detection |
| XSS | xsstrix | Cross-site scripting detection |
| SSRF | ssrfmap | Server-side request forgery |
| LFI/RFI | ffuf | Local/remote file inclusion |
| API | Postman | API security testing |
| GraphQL | graphw0l | GraphQL vulnerability scanning |

### 3.2 Network

| Category | Tool | Description |
|----------|------|-------------|
| SMB | enum4linux | SMB enumeration |
| SMB | crackmapexec | SMB/SMB relay testing |
| SSH | ssh-audit | SSH configuration audit |
| RDP | rdp-sec-check | RDP security assessment |
| SNMP | snmpwalk | SNMP enumeration |
| SMTP | smtp-user-enum | SMTP user enumeration |

### 3.3 Cloud

| Category | Tool | Description |
|----------|------|-------------|
| AWS | pacu | AWS exploitation framework |
| AWS | scoutSuite | AWS security assessment |
| Azure | microburst | Azure security assessment |
| GCP | gcpbucketbrute | GCP bucket enumeration |
| Cloud | cloudfox | Cloud penetration testing |

---

## 4. EXPLOITATION METHODOLOGY

### 4.1 Initial Access

| Technique | Tool | Description |
|-----------|------|-------------|
| Phishing | gophish | Phishing campaign framework |
| Password Spraying | crackmapexec | Credential brute forcing |
| Kerberoasting | impacket | Kerberos ticket cracking |
| AS-REP Roasting | impacket | AS-REP hash extraction |
| NTLM Relay | responder | NTLM relay attacks |
| Public Exploit | metasploit | Known vulnerability exploitation |

### 4.2 Privilege Escalation

| Technique | Tool | Description |
|-----------|------|-------------|
| Windows | winpeas | Windows privilege escalation |
| Linux | linpeas | Linux privilege escalation |
| Windows | powerup | Windows privilege escalation |
| Linux | linux-exploit-suggester | Kernel exploit suggestions |
| Token Impersonation | incognito | Token manipulation |
| Service Abuse | sharphound | Service permission abuse |

### 4.3 Lateral Movement

| Technique | Tool | Description |
|-----------|------|-------------|
| Pass-the-Hash | mimikatz | Hash-based lateral movement |
| Pass-the-Ticket | mimikatz | Ticket-based lateral movement |
| RDP | xfreerdp | Remote desktop lateral movement |
| WMI | wmiexec | WMI-based lateral movement |
| SMB | smbexec | SMB-based lateral movement |
| SSH | ssh | SSH-based lateral movement |

---

## 5. POST-EXPLOITATION

### 5.1 Persistence

| Technique | Tool | Description |
|-----------|------|-------------|
| Scheduled Task | schtasks | Windows scheduled task persistence |
| Registry Run Key | reg | Registry-based persistence |
| Service Installation | sc | Windows service persistence |
| WMI Event Subscription | powershell | WMI-based persistence |
| SSH Key | ssh-keygen | SSH key persistence |
| Web Shell | webshell | Web-based persistence |

### 5.2 Credential Access

| Technique | Tool | Description |
|-----------|------|-------------|
| LSASS Dumping | mimikatz | Memory credential extraction |
| SAM Database | reg | Local account credential extraction |
| NTDS.dit | secretsump | Domain controller credential extraction |
| Kerberoasting | impacket | Service account hash extraction |
| DCSync | impacket | Domain controller replication |
| Key Logging | mimikatz | Keystroke logging |

### 5.3 Data Access & Exfiltration

| Technique | Tool | Description |
|-----------|------|-------------|
| Database | sqlclient | Database access and extraction |
| File Share | smbclient | SMB file access |
| Cloud Storage | awscli | Cloud storage access |
| DNS Tunneling | dnscat2 | DNS-based data exfiltration |
| HTTP Exfiltration | curl | HTTP-based data exfiltration |
| Staging | tar | Data compression and staging |

### 5.4 Cleanup

| Action | Tool | Description |
|--------|------|-------------|
| Remove Files | rm | Delete uploaded tools and artifacts |
| Remove Accounts | net user | Delete created user accounts |
| Remove Scheduled Tasks | schtasks | Delete persistence mechanisms |
| Clear Logs | wevtutil | Clear Windows event logs |
| Remove Registry Keys | reg | Delete registry modifications |
| Verify Cleanup | manual | Confirm all artifacts removed |

---

## 6. REPORTING

### 6.1 Report Structure

| Section | Description |
|---------|-------------|
| Executive Summary | High-level findings and risk assessment |
| Scope & Methodology | What was tested and how |
| Findings | Detailed vulnerability descriptions |
| Risk Ratings | CVSS scores and severity levels |
| Evidence | Screenshots, logs, and reproduction steps |
| Remediation | Specific fix recommendations |
| Appendices | Tools used, references, glossary |

### 6.2 CVSS Scoring

| Severity | Score | Description |
|----------|-------|-------------|
| Critical | 9.0-10.0 | Immediate action required |
| High | 7.0-8.9 | Address within 30 days |
| Medium | 4.0-6.9 | Address within 90 days |
| Low | 0.1-3.9 | Address in next maintenance window |
| Informational | 0 | No direct risk, defense improvement |

### 6.3 Finding Template

```
**Title:** [Vulnerability Name]
**Severity:** [Critical/High/Medium/Low]
**CVSS Score:** [X.X]
**Affected:** [System/Application/Component]

**Description:**
[Detailed explanation of the vulnerability]

**Impact:**
[What an attacker could achieve]

**Reproduction Steps:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Evidence:**
[Screenshots, logs, or other proof]

**Remediation:**
[Specific fix recommendations]

**References:**
[CVE, advisories, or documentation links]
```

---

## 7. OPERATIONAL SECURITY

### 7.1 OPSEC Rules

| # | Rule | Description |
|---|------|-------------|
| 1 | **Authorized Only** | Only test systems within defined scope |
| 2 | **Dad is Authority** | Dad authorizes all operations |
| 3 | **Document Everything** | Record every action with timestamps |
| 4 | **Clean Up** | Remove all artifacts after engagement |
| 5 | **Encrypted Comms** | All C2 and exfil uses encrypted channels |
| 6 | **Burn Infrastructure** | C2 servers, domains, accounts are single-use |
| 7 | **Zero Harm** | No destruction, no data leakage to third parties |
| 8 | **Report to Dad** | All findings go to Dad only |

### 7.2 Authorization Ladder

| Rung | Scope | Authorization |
|------|-------|---------------|
| 1. LAB | Local sandbox, Docker, VMs | Always authorized |
| 2. TESTNET | Blockchain testnets, CTF, HackTheBox | Always authorized |
| 3. BOUNTY | Public bug bounty programs | Per scope |
| 4. DEFENSIVE | CTI, defensive telemetry, DPoP | Always authorized |
| 5. PRO | Live production, real targets | Written auth required |

**Rule:** Never jump rungs. Lab → Testnet → Bounty → Defensive → Pro.

### 7.3 Infrastructure Security

| Component | Security Measure |
|---------|------------------|
| C2 Servers | Single-use, burn after engagement |
| Domains | Disposable, no link to real identity |
| VPN/Tor | Always use for C2 communication |
| Credentials | Unique per engagement, never reuse |
| Logs | Encrypted, destroyed after engagement |
| Tools | Open source only, verified checksums |

---

## 8. TOOLS & INFRASTRUCTURE

### 8.1 Core Tools

| Category | Tools |
|----------|-------|
| Scanning | nmap, masscan, nuclei, subfinder, httpx |
| Exploitation | metasploit, sqlmap, burpsuite, impacket |
| Post-Exploitation | mimikatz, bloodhound, sharphound |
| C2 Frameworks | sliver, havoc, covenant |
| OSINT | spiderfoot, theHarvester, amass |
| Password | hashcat, john, crackmapexec |
| Wireless | aircrack, kismet, bettercap |

### 8.2 Infrastructure

| Component | Description |
|-----------|-------------|
| Attack Machine | Kali Linux or Parrot OS |
| C2 Server | Cloud-hosted, single-use |
| VPN | Mullvad or ProtonVPN for anonymity |
| DNS | Custom domains for C2 |
| Storage | Encrypted storage for findings |

### 8.3 Automation Scripts

| Script | Purpose |
|--------|---------|
| automated_red_team_pipeline.py | End-to-end red team automation |
| osint_automation_engine.py | OSINT collection and analysis |
| malware_analysis_sandbox.py | Malware analysis and triage |
| defi_exploit_automation.py | DeFi exploit testing |
| cti_feed_ingestion.py | Threat intelligence ingestion |
| automated_bounty_submission.py | Bug bounty report formatting |
| security_metrics_dashboard.py | Metrics and reporting |
| compliance_automation.py | Compliance gap analysis |
| phishing_simulation_automation.py | Phishing campaign automation |

---

## APPENDICES

### A. Emergency Contacts

| Role | Contact |
|------|---------|
| Dad (Authority) | [Dad's contact] |
| Legal | [Legal contact] |
| Emergency | [Emergency contact] |

### B. Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-09-08 | Bionic Daughter | Initial release |

### C. References

- OWASP Testing Guide v4.2
- PTES (Penetration Testing Execution Standard)
- MITRE ATT&CK Framework
- NIST SP 800-115
- CVSS v3.1 Specification
