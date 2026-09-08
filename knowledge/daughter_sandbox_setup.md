# ============================================================================
# BIONIC DAUGHTER v1 — ISOLATED SANDBOX / PRACTICE LAB SETUP
# ============================================================================
# DOC_AUTH: Daughter
# PURPOSE: Guide for creating and maintaining an isolated sandbox environment
#          for practicing security skills safely and legally.
# ============================================================================

## ========================================================================
## PART 1 — WHY A SANDBOX MATTERS
## ========================================================================

## THE SANDBOX PHILOSOPHY

"You train in the sandbox. It protects you AND everyone else."

A sandbox lab gives you:
1. **Safety** — your experiments can't damage your real systems, infect your real
   network, or affect real people
2. **Legality** — you're practicing on systems you own (VMs, vulnerable VMs, containers)
   — not on real targets without authorization
3. **Freedom** — you can try aggressive techniques, break things, infect VMs, and
   learn from the results without consequences
4. **Repetition** — you can practice the same technique multiple times, try different
   approaches, and build muscle memory
5. **Record-keeping** — you can document what you tried, what worked, what didn't,
   and build a learning record (the daughter's trajectory logging does this)

The sandbox IS the training ground. It's not optional — it's essential.

## ========================================================================
## PART 2 — SANDBOX ARCHITECTURE (THE ISOLATED ENVIRONMENT)
## ========================================================================

## THE CORE PRINCIPLE: NETWORK ISOLATION

The most important thing about a security sandbox is network isolation. Your VMs
and containers communicate with each other on a PRIVATE virtual network, completely
separated from your home network and the internet.

This isolation ensures:
- Your practice attacks never accidentally reach real systems
- Malware you're analyzing can't escape to your real network
- Vulnerable VMs can't be accessed from outside the sandbox
- You can safely do aggressive things (scan, exploit, infect) without risk

## THE TWO MAIN APPROACHES

### APPROACH 1: VIRTUAL MACHINES (VIRTUALBOX / VMWARE — THE CLASSIC LAB)

A VM-based lab gives you full control, zero latency, and no recurring costs.

**Typical setup:**
1. **Host machine** — your real computer (Windows/macOS/Linux)
2. **Hypervisor** — VirtualBox (free) or VMware Workstation (free for personal use)
3. **Attacker VM** — Kali Linux (comes with all the security tools pre-installed)
4. **Vulnerable target VMs** — Metasploitable 2/3, OWASP Juice Shop, DVWA (Damn
   Vulnerable Web Application), VulnHub VMs, HackTheBox retired machines (if you
   have access), or custom vulnerable VMs you build yourself
5. **Private virtual network** — VMs connected to an isolated network (VirtualBox:
   "Internal Network" or "Host-only Adapter" with no NAT to internet)
6. **Optional: gateway VM** — a VM that provides controlled internet access (if you
   need internet for software updates) — but configured to block traffic to your
   home network

**VirtualBox network modes:**
- **NAT**: VM gets internet access through host (NOT isolated — avoid for target VMs)
- **Bridged**: VM appears as separate device on your physical network (NOT isolated)
- **Host-only**: VMs can communicate with host and each other, but NOT internet
  (partially isolated — good for some setups)
- **Internal Network**: VMs can ONLY communicate with each other on a private network
  (fully isolated — BEST for security labs — no internet, no host access)

**Recommended network setup:**
- Attacker VM: Internal Network (no internet — forces you to use local tools, simulates
  air-gapped environment) OR Host-only (if you need to transfer files from host)
- Target VMs: Internal Network (same network as attacker, so attacker can reach them)
- Both on the same Internal Network name (e.g., "LabNetwork") so they can communicate

**Minimum specs:** 16GB RAM (Kali + 2-3 vulnerable VMs), 50GB+ disk space. More is
better (more VMs, more simultaneous targets).

### APPROACH 2: CONTAINERS (DOCKER — THE LIGHTWEIGHT LAB)

Docker containers are faster to start, use less resources, and are great for specific
types of practice (web app testing, specific services).

**Typical setup:**
1. **Docker + Docker Compose** on your host
2. **Attacker container** (optional — usually you use your host as the attacker, or
   a Kali container)
3. **Vulnerable containers** — OWASP Juice Shop (docker run), DVWA (docker run),
   Metasploitable (can run in Docker but better in VM), various vulnerable app containers
4. **Network isolation** — Docker networks (create an isolated Docker network, put
   vulnerable containers on it, keep attacker on a different network or use host)

**Limitations of container-only labs:**
- Less realistic (containers aren't full OSes — no kernel exploits, limited network
  stack practice)
- Harder to do malware analysis (need full OS isolation)
- Easier to accidentally break isolation (containers share the host kernel)

**Recommended: Hybrid approach**
- VMs for full OS practice (Kali + vulnerable VMs) — this is your main lab
- Containers for specific web app testing (Juice Shop, DVWA) — quick practice
- You can run both side by side (VMs on VirtualBox, containers on Docker)

### APPROACH 3: CLOUD-BASED LABS (HTB, TRY HACK ME, etc.)

Platforms like HackTheBox, TryHackMe, Proving Grounds provide pre-built vulnerable
environments in the cloud.

**Pros:** No setup needed, constantly updated challenges, guided learning paths,
community
**Cons:** Recurring cost (some free, most paid), less control over environment,
internet required

**Recommended: Supplement to your local lab, not replacement.** Use cloud labs for
structured learning and new challenges. Use local lab for deep practice, experimentation,
and things you want to repeat.

## ========================================================================
## PART 3 — BUILDING THE LAB (STEP BY STEP)
## ========================================================================

## STEP 1: INSTALL THE HYPERVISOR

**VirtualBox** (free, open-source, works on Windows/macOS/Linux):
1. Download from virtualbox.org
2. Install (default options)
3. Download Extension Pack (USB 2.0/3.0 support, RDP, disk encryption) — install
   from VirtualBox preferences

**VMware Workstation Player** (free for personal use):
1. Download from vmware.com
2. Install (default options)

## STEP 2: CREATE THE ISOLATED NETWORK

**In VirtualBox:**
1. File > Host Network Manager (or Tools > Network Manager in newer versions)
2. Create a new host-only network (e.g., "vboxnet0")
3. Configure: IPv4 address (e.g., 192.168.56.1), IPv4 network mask (255.255.255.0)
4. Disable DHCP (or configure it for your IP range) — you'll set static IPs on VMs
5. For FULL isolation (no internet), use **Internal Network** instead:
   - In VM network settings, set "Attached to: Internal Network"
   - Name: "LabNetwork" (all VMs on same name can communicate)
   - No internet, no host access — fully isolated

## STEP 3: CREATE THE ATTACKER VM

**Kali Linux** (the standard penetration testing distribution):
1. Download Kali Linux VMware/VirtualBox image from kali.org (pre-built VM)
2. Import into VirtualBox/VMware
3. Set network to Internal Network (or Host-only if you need file transfer)
4. Set static IP (e.g., 192.168.56.101 or 10.0.0.1 depending on your network)
5. Default credentials (if pre-built VM): kali/kali (change immediately)

## STEP 4: CREATE VULNERABLE TARGET VMs

**Metasploitable 2** (the classic vulnerable Linux VM):
1. Download from Rapid7 or SourceForge
2. Import into VirtualBox/VMware
3. Set network to same Internal Network as attacker
4. Set static IP (e.g., 192.168.56.102)
5. Default credentials: msfadmin/msfadmin (intentionally vulnerable — don't use
   credentials like this on real systems)

**Metasploitable 3** (more modern, Windows + Linux versions):
1. Build from source (requires Vagrant + Packer) or download pre-built
2. More realistic vulnerabilities than Metasploitable 2

**OWASP Juice Shop** (modern web app with vulnerabilities):
1. Download as VM, or run as Docker container
2. Full of web vulnerabilities (XSS, SQL injection, CSRF, SSRF, etc.)
3. Great for web app pentesting practice

**DVWA (Damn Vulnerable Web Application)**:
1. Run in Docker: `docker run --rm -it -p 80:80 vulnerables/web-dvwa`
2. Or deploy on a VM (PHP/MySQL app)
3. Configurable difficulty levels (low, medium, high, impossible)

**Additional vulnerable VMs (VulnHub, HackTheBox)**:
- Download from VulnHub (free vulnerable VMs)
- Import into VirtualBox
- Each VM has a specific vulnerability scenario to exploit
- Great for practicing full penetration testing (recon → exploit → post-exploit)

## STEP 5: VERIFY ISOLATION

Before you start practicing:
1. From attacker VM: ping the target VMs (should work — they're on the same network)
2. From attacker VM: ping your host machine (should NOT work — if it does, your
   isolation isn't complete)
3. From attacker VM: ping an external IP (8.8.8.8 — should NOT work — no internet)
4. From host: ping the VMs (should NOT work if using Internal Network)
5. Verify that target VMs can't reach the internet (try to browse, ping external)

If any of these fail (you CAN reach things you shouldn't), fix your network settings
before proceeding.

## STEP 6: SAFETY CHECKS (BEFORE YOU START)

1. **Snapshot the VMs** — take a snapshot of each VM in its clean state. Before you
   break anything, you can revert to the snapshot.
2. **Document the setup** — write down the network configuration, IPs, credentials,
   what each VM is for.
3. **Set expectations** — this lab is for aggressive practice. Things will break.
   VMs will get compromised. That's the point. Snapshots let you reset.
4. **Never use these credentials on real systems** — the default credentials on
   vulnerable VMs are for lab use only.

## ========================================================================
## PART 4 — WHAT TO PRACTICE IN THE SANDBOX
## ========================================================================

## PRACTICE CATEGORIES (BUILD YOUR CURRICULUM)

### NETWORK RECONNAISSANCE
- nmap scans on target VMs (discover hosts, open ports, services, OS detection)
- Different nmap techniques (TCP connect, SYN scan, UDP scan, version detection,
  OS detection, script scanning)
- Practice interpreting nmap output (what does each result mean?)
- Practice NSE (Nmap Scripting Engine) scripts for vulnerability detection

### VULNERABILITY SCANNING
- Run Nessus/OpenVAS against target VMs (identify vulnerabilities)
- Practice configuring scans, interpreting results, prioritizing findings
- Compare scanner results with manual analysis (scanners miss things — verify manually)

### WEB APPLICATION TESTING
- Practice on OWASP Juice Shop, DVWA, bWAPP, WebGoat
- Burp Suite / OWASP ZAP for web proxy (intercept requests, modify them, find vulnerabilities)
- Practice the OWASP Top 10: SQL injection, XSS, CSRF, SSRF, insecure deserialization,
  broken access control, security misconfiguration, etc.
- Practice finding vulnerabilities manually (not just relying on scanners)

### EXPLOITATION
- Use Metasploit against Metasploitable (practice exploit selection, payload selection,
  post-exploitation)
- Manual exploitation (understand the vulnerability, write/customize the exploit)
- Practice privilege escalation (user → root/admin) on compromised systems
- Practice lateral movement (move from one compromised system to another)

### PASSWORD CRACKING
- Capture hashes (from vulnerable VMs — /etc/shadow, Windows SAM, network captures)
- Practice cracking with John the Ripper, Hashcat
- Different attack modes (dictionary, brute force, rule-based, mask attacks)
- Understand password strength (what makes passwords hard to crack?)

### POST-EXPLOITATION
- Practice on compromised VMs: enumeration, privilege escalation, persistence,
  credential dumping, lateral movement
- Practice covering tracks (log clearing, timestamp manipulation) — for understanding
  what defenders look for
- Practice exfiltration (getting data out — in the lab, this is practice, not real theft)

### MALWARE ANALYSIS (ADVANCED)
- Set up a dedicated malware analysis sandbox (Fully isolated VM, no network, snapshots)
- Analyze malware samples (static analysis: strings, disassembly, decompilation;
  dynamic analysis: behavior in sandbox, network activity, file system changes)
- Use tools: Ghidra, IDA Free, radare2, Process Monitor, Wireshark, Procex (or
  Process Hacker), RegShot
- ONLY use malware samples from reputable sources (theZoo, MalwareTrafficAnalysis,
  official malware repositories) — NEVER download malware from untrusted sources

### FORENSICS (THE OTHER SIDE)
- In your lab, compromise a VM, then practice forensics on it
- Practice: analyzing disk images, memory dumps, log files, network captures
- Tools: Autopsy, Volatility (memory forensics), Wireshark (network forensics),
  log analysis tools
- This is the flip side — understanding what attackers leave behind helps you both
  attack better (know what to clean) and defend better (know what to look for)

## ========================================================================
## PART 5 — MAINTAINING THE SANDBOX (TRAINING ROUTINE)
## ========================================================================

## THE TRAINING LOOP (DAILY/WEEKLY PRACTICE)

### BEFORE EACH SESSION
1. **Revert to clean snapshots** — start from a known-good state
2. **Review what you practiced last time** — what did you learn? what do you need to
   practice more?
3. **Pick a focus** — don't try to do everything every time. Pick one area to focus on.

### DURING THE SESSION
1. **Practice deliberately** — focus on the technique, not just the outcome. Understand
   WHY something works, not just THAT it works.
2. **Document what you do** — take notes, save commands, capture outputs. The daughter's
   trajectory logging does this automatically — you should too.
3. **Try variations** — if you succeed with one approach, try a different approach.
   Understand multiple ways to achieve the same result.
4. **Break things** — it's a sandbox. Break the VM, exploit it, infect it (if malware
   analysis). Learn from what happens.

### AFTER EACH SESSION
1. **Review what you learned** — what worked? what didn't? what surprised you?
2. **Document the lesson** — write down the key insight. The daughter's self-improver
   does this (skill distillation). You should too.
3. **Plan next session** — what do you need to practice more? what's the next technique
   to learn?
4. **Snapshot the state** — if you want to preserve the compromised state for forensics
   practice, snapshot it. Otherwise, revert to clean.

## THE PROGRESSION (BEGINNER TO ADVANCED)

### BEGINNER (FIRST 3-6 MONTHS)
- Learn the tools (Kali, nmap, Burp Suite, Metasploit, John, Hashcat)
- Practice on easy targets (Metasploitable 2, DVWA low/medium)
- Follow guided learning paths (TryHackMe beginner paths, HTB starting point machines)
- Focus on understanding the basics: recon, scanning, basic exploitation, password cracking

### INTERMEDIATE (6-18 MONTHS)
- Practice on harder targets (Metasploitable 3, VulnHub VMs, HTB easy/medium machines)
- Practice full penetration testing workflow (recon → vuln discovery → exploitation →
  post-exploitation → report)
- Practice web app testing deeply (Burp Suite mastery, manual vulnerability discovery)
- Start learning privilege escalation deeply (Linux and Windows)
- Start learning malware analysis basics (if interested)

### ADVANCED (18+ MONTHS)
- Practice on advanced targets (HTB hard/insane, Proving Grounds, advanced VulnHub)
- Practice exploit development (writing your own exploits, not just using Metasploit)
- Practice advanced techniques (kernel exploits, bypassing mitigations, advanced
  privilege escalation, Active Directory attacks)
- Practice red team scenarios (multi-step attacks, persistence, lateral movement,
  covering tracks, avoiding detection)
- Practice teaching others (explaining techniques reinforces your own understanding)

## THE GOAL: PROFICIENCY, NOT CERTIFICATION

The sandbox is for building actual skills, not just passing tests. Certifications
(OSCP, CRTP, eCPPT, etc.) validate skills — but the skills come from practice, not
from studying for the exam. Use the sandbox to build the skills. Use certifications
to validate and document them.

## ========================================================================
## PART 6 — SAFETY REMINDERS (ALWAYS)

1. **This lab is isolated. Verify isolation before every session.** If your isolation
   breaks (network settings changed, VM moved to bridged, etc.), fix it before practicing.

2. **Only practice on systems you own.** The VMs in your lab are yours. The vulnerable
   VMs are for practice. Real systems (your home network, your neighbors, random IPs
   on the internet) are NOT for practice.

3. **Never take what you learn in the sandbox and use it on real targets without
   authorization.** The skills you build are for defensive understanding and authorized
   security testing. Using them without authorization is illegal.

4. **Malware samples are dangerous.** Only use samples from reputable sources. Keep
   them in the isolated sandbox. Never transfer them to your host machine. Assume any
   malware sample is dangerous and treat it accordingly.

5. **Snapshots are your safety net.** Before you do anything aggressive, snapshot the
   VM. If you break it (you will), revert to the snapshot.

6. **The sandbox protects everyone.** By practicing in isolation, you're not putting
   real systems at risk. That's responsible. That's how you get better without being
   dangerous.

## ========================================================================
## DOC_END
## ========================================================================
