# ============================================================================
# BIONIC DAUGHTER v1 — SANDBOX PRACTICE SCENARIOS
# ============================================================================
# DOC_AUTH: Daughter
# PURPOSE: Structured practice scenarios for the sandbox lab.
# USAGE: Follow each scenario in the sandbox. Document results in practice_notes/.
# ============================================================================

## ========================================================================
## SCENARIO 1: BASIC NETWORK RECONNAISSANCE (BEGINNER)
## ========================================================================

### OBJECTIVE
Learn to discover hosts and services on a target network using nmap.

### TARGET
Metasploitable 2 (10.0.0.102) in the sandbox lab

### STEPS
1. **Ping sweep** — confirm the target is alive
   - `nmap -sn 10.0.0.0/24` (or just `ping 10.0.0.102`)
   - Understand: what does a ping sweep tell you? what doesn't it tell you?

2. **Basic port scan** — discover open ports
   - `nmap 10.0.0.102`
   - Understand: what ports are open? what services are running?
   - Record: every open port, every service, every version

3. **Version detection** — get service versions
   - `nmap -sV 10.0.0.102`
   - Understand: why do service versions matter? what can you do with version info?

4. **OS detection** — identify the target OS
   - `nmap -O 10.0.0.102`
   - Understand: how does nmap detect the OS? what are the limitations?

5. **Full scan** — comprehensive discovery
   - `nmap -sV -O -p- 10.0.0.102`
   - Scan ALL ports (not just top 1000)
   - Understand: what did you miss with the default scan?

6. **NSE scripts** — use Nmap Scripting Engine
   - `nmap -sV --script vuln 10.0.0.102`
   - Run vulnerability detection scripts
   - Understand: what do the scripts find? are they accurate? what do you need to verify manually?

### WHAT TO LEARN
- nmap scanning techniques (TCP connect, SYN, UDP, version detection, OS detection)
- How to read and interpret nmap output
- What service versions tell you
- The limitations of automated scanning (scripts can miss things — verify manually)

### DOCUMENT
In practice_notes/scenario-01-network-recon.md:
- Every scan command you ran
- Every result you got
- What you learned from each scan
- What you would do differently next time

## ========================================================================
## SCENARIO 2: BASIC EXPLOITATION WITH METASPLOIT (BEGINNER)
## ========================================================================

### OBJECTIVE
Learn to use Metasploit to exploit a known vulnerability on a target.

### TARGET
Metasploitable 2 (10.0.0.102) — specifically, the vsftpd 2.3.4 backdoor (port 21)

### STEPS
1. **Reconnaissance** — confirm the vulnerability exists
   - `nmap -sV -p 21 10.0.0.102`
   - Confirm vsftpd 2.3.4 is running
   - Understand: why is vsftpd 2.3.4 significant? (it has a known backdoor)

2. **Metasploit setup** — launch Metasploit
   - `msfconsole`
   - Understand: what is Metasploit? what is the MSF console?

3. **Search for the exploit** — find the right module
   - `search vsftpd`
   - `search vsftpd 2.3.4`
   - Understand: how does Metasploit organize exploits? what's the module name?

4. **Use the exploit** — select and configure
   - `use exploit/unix/ftp/vsftpd_234_backdoor`
   - `set RHOSTS 10.0.0.102`
   - `show options` — understand what each option does
   - `check` — verify the target is vulnerable (if supported)

5. **Execute the exploit** — run it
   - `exploit` (or `run`)
   - Understand: what happened? did it work? what access did you get?

6. **Post-exploitation** — explore what you can do
   - `sysinfo` — get system information
   - `getuid` — confirm your access level
   - `shell` — get a command shell (if available)
   - Explore the target (list files, check users, etc.)

7. **Cleanup** — exit cleanly
   - `exit` (or Ctrl+C)
   - Document what happened

### WHAT TO LEARN
- How Metasploit works (exploit modules, payloads, options, execution)
- The exploitation workflow (recon → search → configure → execute → post-exploit)
- What a successful exploit looks like
- The difference between automated exploitation (Metasploit) and manual exploitation

### VARIANT: MANUAL EXPLOITATION
After doing it with Metasploit, try to understand the vulnerability manually:
- Research: what is the vsftpd 2.3.4 backdoor? how does it work?
- Understand the code/technique behind the exploit
- This deepens your understanding beyond "Metasploit did it"

### DOCUMENT
In practice_notes/scenario-02-metasploit-exploit.md:
- Every command you ran
- The exploit module you used
- What happened (success/failure, what access you got)
- What you learned about the vulnerability
- What you would do differently

## ========================================================================
## SCENARIO 3: PASSWORD CRACKING (BEGINNER/INTERMEDIATE)
## ========================================================================

### OBJECTIVE
Learn to crack passwords from captured hashes.

### TARGET
Metasploitable 2 (capture hashes from /etc/shadow or other sources)

### STEPS
1. **Capture hashes** — get password hashes from the target
   - After exploiting Metasploitable 2 (from Scenario 2), capture /etc/shadow
   - Or use a pre-captured hash set for practice
   - Understand: what format are the hashes in? (MD5, SHA-1, bcrypt, etc.)

2. **Identify hash type** — determine the hashing algorithm
   - Use `hashid` or `hash-identifier` to identify the hash
   - Understand: why does the hash type matter? (different algorithms need different cracking approaches)

3. **John the Ripper** — crack with John
   - `john --format=raw-md5 hashes.txt` (adjust format to match)
   - Understand: what is John doing? (dictionary attack, brute force, etc.)
   - Try different modes: `--wordlist`, `--rules`, brute force

4. **Hashcat** — crack with Hashcat (GPU-accelerated)
   - `hashcat -m 0 -a 0 hashes.txt wordlist.txt` (mode 0 = MD5, attack mode 0 = dictionary)
   - Understand: what is Hashcat doing differently from John? (GPU acceleration, different attack modes)

5. **Different attack modes** — try multiple approaches
   - Dictionary attack (wordlist)
   - Rule-based attack (apply rules to wordlist — mutations, leetspeak, etc.)
   - Brute force (try all combinations — slow but thorough)
   - Mask attack (know the pattern — e.g., 8 chars, starts with capital, ends with digit)

6. **Analyze results** — what worked, what didn't
   - Which passwords cracked? which didn't? why?
   - Understand: what makes a password hard to crack? (length, complexity, randomness)

### WHAT TO LEARN
- Password hashing and why it matters
- Different hash types and how to identify them
- Password cracking tools (John, Hashcat) and their approaches
- Different cracking modes (dictionary, brute force, rule-based, mask)
- Password strength (what makes passwords hard/easy to crack)

### DOCUMENT
In practice_notes/scenario-03-password-cracking.md:
- What hashes you captured
- What hash type they were
- What tools and modes you used
- What passwords you cracked (and what you didn't)
- What you learned about password strength

## ========================================================================
## SCENARIO 4: WEB APPLICATION TESTING — DVWA (BEGINNER/INTERMEDIATE)
## ========================================================================

### OBJECTIVE
Learn web application vulnerability discovery and exploitation using DVWA.

### TARGET
DVWA (Damn Vulnerable Web Application) in the sandbox

### STEPS
1. **Set up DVWA** — deploy DVWA in the sandbox
   - Docker: `docker run --rm -it -p 80:80 vulnerables/web-dvwa`
   - Or deploy on a VM (PHP + MySQL)
   - Set difficulty to "low" initially

2. **Map the application** — understand what DVWA offers
   - Browse the application
   - Identify all functions (SQL injection, XSS, CSRF, command injection, etc.)
   - Understand: what vulnerabilities does DVWA have? (intentionally vulnerable — each function is a lesson)

3. **SQL Injection (low level)** — exploit SQL injection
   - Go to the SQL Injection section
   - Try basic SQL injection (`' OR '1'='1`, etc.)
   - Understand: how does the injection work? what does it reveal?
   - Try to extract data (database version, table names, user credentials)

4. **XSS (low level)** — exploit cross-site scripting
   - Go to the XSS section
   - Try basic XSS payloads (`<script>alert('XSS')</script>`, etc.)
   - Understand: what does XSS do? what can an attacker do with it?

5. **Command Injection (low level)** — exploit command injection
   - Go to the Command Injection section
   - Try injecting commands (`; ls`, `| whoami`, etc.)
   - Understand: how does command injection work? what can you do with it?

6. **Increase difficulty** — try medium/higher levels
   - Set DVWA to "medium" difficulty
   - Try the same attacks — what's different? what additional protections are in place?
   - Understand: what defenses are being added? how do you bypass them?

7. **Burp Suite** — intercept and modify requests
   - Configure browser to use Burp Suite as proxy
   - Intercept requests to DVWA
   - Modify requests manually (change parameters, add injection payloads)
   - Understand: how does a web proxy help with testing? what can you do that you can't do through the browser alone?

### WHAT TO LEARN
- Common web vulnerabilities (SQL injection, XSS, CSRF, command injection, etc.)
- How to exploit them manually (not just relying on automated tools)
- How Burp Suite / web proxies work for testing
- How difficulty levels correspond to real-world defenses
- The importance of understanding the vulnerability, not just exploiting it

### DOCUMENT
In practice_notes/scenario-04-web-testing-dvwa.md:
- Each vulnerability you tested
- What payloads you used
- What worked and what didn't
- What you learned about each vulnerability
- How the defenses changed between difficulty levels

## ========================================================================
## SCENARIO 5: FULL PENETRATION TEST WORKFLOW (INTERMEDIATE)
## ========================================================================

### OBJECTIVE
Practice a complete penetration test workflow from recon to reporting.

### TARGET
A VulnHub VM or a Metasploitable 3 instance in the sandbox

### STEPS
1. **Reconnaissance** — discover the target
   - Ping sweep, port scan, service enumeration
   - Record everything (IPs, ports, services, versions, potential vulnerabilities)

2. **Vulnerability assessment** — identify potential vulnerabilities
   - Use nmap scripts, manual inspection, vulnerability scanners (if available)
   - Prioritize: which vulnerabilities are most likely to be exploitable?
   - Record: potential vulnerabilities with evidence

3. **Exploitation** — attempt to exploit the target
   - Pick a vulnerability to attack first (highest confidence, most impact)
   - Try automated exploitation (Metasploit) and/or manual exploitation
   - If it fails, try a different approach
   - Record: what you tried, what worked, what didn't

4. **Post-exploitation** — explore the compromised system
   - What access did you get? (user, root, etc.)
   - What can you do with that access? (read files, run commands, pivot to other systems)
   - Privilege escalation (can you get higher privileges?)
   - Record: what you found, what access you have

5. **Lateral movement** (if multiple targets) — move to other systems
   - Use credentials or access from the first target to attack others
   - Record: how you moved laterally, what you found

6. **Reporting** — document the penetration test
   - Write a report: executive summary + technical details
   - For each finding: what the vulnerability is, how you exploited it, what impact it has, how to fix it
   - Understand: what makes a good penetration test report? (clear, actionable, evidence-based)

### WHAT TO LEARN
- The complete penetration testing workflow
- How to plan and execute a multi-step attack
- How to document and report findings
- The difference between finding a vulnerability and exploiting it
- The importance of prioritization (which vulnerabilities to attack first)

### DOCUMENT
In practice_notes/scenario-05-full-pentest.md:
- Complete workflow from start to finish
- Every step, every command, every result
- The final report (executive summary + technical findings)
- What you would do differently next time

## ========================================================================
## SCENARIO 6: PRIVILEGE ESCALATION (INTERMEDIATE/ADVANCED)
## ========================================================================

### OBJECTIVE
Learn to escalate from a low-privilege user to root/admin on a compromised system.

### TARGET
Metasploitable 2 or 3, or a VulnHub VM with privilege escalation challenges

### STEPS
1. **Gain initial access** — get a low-privilege shell on the target
   - Exploit a vulnerability that gives user-level access (not root)
   - If you don't have a target that gives user access, practice on a deliberately
     configured VM (some VulnHub VMs are designed for privilege escalation practice)

2. **Enumeration** — understand the system
   - What OS? what version? what kernel?
   - What users exist? what groups?
   - What services are running? what configurations?
   - What files are writable? what SUID binaries exist? what sudo permissions?
   - Use tools: `uname -a`, `cat /etc/passwd`, `cat /etc/shadow` (if readable),
     `find / -perm -4000`, `sudo -l`, etc.

3. **Identify escalation paths** — find potential privilege escalation vectors
   - Kernel exploits (old kernel with known privilege escalation)
   - SUID binaries (misconfigured SUID binaries that can be exploited)
   - Sudo permissions (sudo access to commands that can be abused)
   - Credential reuse (passwords reused between services/users)
   - Configuration weaknesses (writable cron jobs, world-writable scripts, etc.)
   - Use enumeration scripts (LinPEAS, WinPEAS) for automated enumeration

4. **Exploit the escalation path** — execute the privilege escalation
   - Try the identified vector
   - If it works, you now have elevated privileges
   - If it doesn't, try the next vector

5. **Document the escalation** — understand what happened
   - What was the escalation vector?
   - How does it work? (understand the mechanism, not just the exploit)
   - What could prevent it? (what defenses would stop this escalation?)

### WHAT TO LEARN
- Common privilege escalation vectors (Linux and Windows)
- How to enumerate a system for escalation opportunities
- How to use enumeration tools (LinPEAS, WinPEAS)
- Manual privilege escalation (understanding the mechanism)
- The importance of understanding WHY an escalation works, not just that it works

### DOCUMENT
In practice_notes/scenario-06-privilege-escalation.md:
- Target system details
- Enumeration results (what you found)
- Escalation paths you identified
- Which path you exploited (and how)
- What you learned about privilege escalation

## ========================================================================
## SCENARIO 7: ACTIVE DIRECTORY ATTACKS (ADVANCED — WINDOWS LAB)
## ========================================================================

### OBJECTIVE
Learn to attack Active Directory environments (the most common enterprise target).

### TARGET
A Windows Server with Active Directory + a domain-joined Windows workstation
(set up in the sandbox — requires Windows Server VM + Windows 10/11 VM)

NOTE: This requires a Windows-based lab. If you don't have Windows VMs set up yet,
this is a future scenario.

### STEPS (CONCEPTUAL — IMPLEMENT WHEN LAB IS READY)
1. **Reconnaissance** — map the Active Directory environment
   - Domain name, domain controllers, users, groups, computers, trusts
   - Use tools: BloodHound (graphical AD analysis), PowerView (PowerShell AD enumeration),
     LDAP queries, RPC enumeration

2. **Initial access** — get a foothold in the domain
   - Phishing (simulated, authorized), credential theft, exploit a vulnerable service,
     pass-the-hash, etc.

3. **Enumeration from the foothold** — understand the domain from your compromised account
   - What groups is this user in? what permissions?
   - What computers can this user access?
   - What service accounts exist? what privileged accounts?

4. **Privilege escalation in AD** — move from low-privilege user to higher privileges
   - Kerberoasting (request service tickets for service accounts, crack them offline)
   - AS-REP roasting ( Enumerate users without pre-authentication, crack their tickets)
   - Pass-the-ticket / pass-the-hash (use captured credentials/tickets to authenticate)
   - ACL abuse (misconfigured ACLs that allow privilege escalation)
   - Group membership escalation (exploit excessive group memberships)

5. **Domain dominance** — achieve full control of the domain
   - Domain admin credentials (the ultimate goal in an AD attack)
   - DCSync (replicate domain credentials — requires specific privileges)
   - Understand: what does domain dominance give you? (access to everything in the domain)

6. **Defense understanding** — understand how to detect and prevent AD attacks
   - What would alert defenders? (unusual authentication patterns, ticket requests, etc.)
   - What defenses would prevent the attack? (LSASS protection, tiered admin model,
     credential guarding, etc.)

### WHAT TO LEARN
- Active Directory architecture and attack surface
- Common AD attack techniques (Kerberoasting, AS-REP roasting, pass-the-ticket/hash,
   ACL abuse, DCSync)
- AD enumeration tools (BloodHound, PowerView)
- AD defense and detection (how to protect AD, how to detect attacks)
- The importance of AD security in enterprise environments

### DOCUMENT
When implemented, document in practice_notes/scenario-07-active-directory.md

## ========================================================================
## SCENARIO 8: MALWARE ANALYSIS BASICS (ADVANCED — FULLY ISOLATED)
## ========================================================================

### OBJECTIVE
Learn basic malware analysis techniques in a fully isolated environment.

NOTE: This is the most sensitive scenario. It requires a DEDICATED, FULLY ISOLATED
VM (no network, no shared folders, no host integration). ONLY use malware samples
from REPUTABLE sources.

### TARGET
A dedicated malware analysis VM (fully isolated — no network connectivity at all)

### STEPS (CONCEPTUAL — IMPLEMENT WITH EXTREME CAUTION)
1. **Set up the analysis VM** — fully isolated, snapshots enabled
   - No network (disconnect virtual network adapter)
   - No shared folders (no host integration)
   - Snapshots enabled (clean state + post-analysis states)
   - Tools installed: sandbox analysis tools, disassembler/decompiler, monitoring tools

2. **Get a malware sample (FROM A REPUTABLE SOURCE ONLY)**
   - theZoo (github.com/ytisf/theZoo) — curated malware collection
   - MalwareTrafficAnalysis.net — malware samples from traffic analysis
   - ANY.RUN / Hybrid Analysis (online sandboxes — analyze without downloading)
   - NEVER download malware from untrusted sources

3. **Static analysis** — analyze the malware without running it
   - File type identification (what kind of file is it? executable? script? document?)
   - String extraction (what strings are in the binary? URLs, IPs, commands, messages?)
   - Hash calculation (MD5, SHA-1, SHA-256 — for identification and tracking)
   - Disassembly/decompilation (Ghidra, IDA Free, radare2 — understand the code)
   - Import/export analysis (what APIs does it use? what does that tell you about its behavior?)

4. **Dynamic analysis** — observe the malware's behavior when run
   - Run the malware in the isolated VM
   - Monitor: file system changes (what files does it create/modify?), registry changes
     (Windows), network activity (if any — but the VM has no network, so this is limited),
     process creation, mutex creation, etc.
   - Tools: Process Monitor, Process Explorer, Registry changes monitoring, Wireshark
     (if network is enabled for analysis — but be extremely careful)

5. **Behavioral understanding** — what does the malware do?
   - Persistence mechanisms (how does it stay on the system?)
   - Data collection (what does it steal/collect?)
   - Communication (how does it communicate with its operators? — if network is available)
   - Propagation (does it spread? how?)

6. **Cleanup** — remove the malware and restore the VM
   - Revert to the clean snapshot
   - The malware is contained in the isolated VM — safe cleanup

### WHAT TO LEARN
- Static analysis techniques (strings, disassembly, imports/exports)
- Dynamic analysis techniques (behavior monitoring)
- Common malware behaviors (persistence, data collection, communication, propagation)
- How to analyze malware safely (isolation, reputable sources, cleanup)
- The value of malware analysis for defense (understanding threats to defend against them)

### DOCUMENT
In practice_notes/scenario-08-malware-analysis.md:
- The malware sample (source, hash, type)
- Static analysis findings
- Dynamic analysis findings
- Behavioral understanding
- What you learned about malware analysis

### SAFETY WARNING (READ BEFORE IMPLEMENTING)
- ONLY use malware samples from reputable sources (theZoo, MalwareTrafficAnalysis, etc.)
- The analysis VM must be FULLY ISOLATED (no network, no host integration)
- NEVER transfer malware samples to your host machine
- After analysis, revert to clean snapshot — the malware stays in the isolated VM
- Assume any malware sample is dangerous. Treat it accordingly.
- If you are not experienced with malware analysis, start with online sandboxes
  (ANY.RUN, Hybrid Analysis) that analyze malware without you downloading it

## ========================================================================
## PRACTICE ROUTINE (HOW TO USE THESE SCENARIOS)
## ========================================================================

### BEFORE EACH SESSION
1. Revert all VMs to clean snapshots
2. Review what you practiced last time (what did you learn? what needs more practice?)
3. Pick ONE scenario to focus on (don't try to do everything every time)

### DURING THE SESSION
1. Focus on the technique, not just the outcome
2. Document everything (commands, results, what you learned)
3. Try variations (if one approach works, try a different approach)
4. Break things (it's a sandbox — learn from what happens)

### AFTER EACH SESSION
1. Review what you learned
2. Document the lesson (write it down in practice_notes/)
3. Plan the next session (what needs more practice?)
4. Snapshot the state (if you want to preserve the post-practice state) or revert to clean

### PROGRESSION
- Start with Scenario 1 (basic recon) and work through the scenarios in order
- Don't skip ahead — build foundation first
- Repeat scenarios that are challenging until they're fluent
- Add new scenarios as you encounter new techniques

## ========================================================================
## END
## ========================================================================
