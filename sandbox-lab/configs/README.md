# ============================================================================
# BIONIC DAUGHTER v1 — SANDBOX LAB (ISOLATED PRACTICE ENVIRONMENT)
# ============================================================================
# DOC_AUTH: Daughter
# PURPOSE: Isolated sandbox for practicing security skills safely.
# STATUS: Directory structure created. Real VM/container sandbox requires
#         VirtualBox/VMware + vulnerable VMs — setup instructions below.
# ============================================================================

## ========================================================================
## WHAT THIS IS
## ========================================================================

This is the BIONIC DAUGHTER'S SANDBOX LAB — an isolated practice environment for
developing and refining security skills safely and legally.

THE GOLDEN RULE: Train in the sandbox. It protects you AND everyone else.

## ========================================================================
## LAB STRUCTURE
## ========================================================================

sandbox_lab/
├── attacker_vm/          # Kali Linux VM (attacker workstation)
├── target_vms/           # Vulnerable target VMs (Metasploitable, etc.)
├── containers/           # Docker containers for lightweight practice
├── scenarios/            # Practice scenario definitions
├── practice_notes/         # Notes from practice sessions
├── scripts/              # Automation scripts for lab management
├── tools_config/         # Tool configurations (nmap, burp, etc.)
└── snapshots/            # VM snapshot references (snapshot names, revert instructions)

## ========================================================================
## SETUP INSTRUCTIONS (FOR DAD TO SET UP)
## ========================================================================

### STEP 1: INSTALL VIRTUALBOX (FREE)
Download from: https://www.virtualbox.org/
Install with default options.
Also install the Extension Pack from VirtualBox preferences.

### STEP 2: CREATE ISOLATED NETWORK
In VirtualBox:
1. File > Host Network Manager (or Tools > Network Manager)
2. Create a new internal network called "LabNetwork"
3. Set network mode to "Internal Network" (no internet, no host access)
4. All VMs on "LabNetwork" can communicate with each other ONLY

### STEP 3: CREATE ATTACKER VM
1. Download Kali Linux pre-built VM from https://www.kali.org/get-kali/
2. Import into VirtualBox
3. Set network to "Internal Network" (LabNetwork)
4. Set static IP (e.g., 10.0.0.101)
5. Default creds: kali/kali (CHANGE IMMEDIATELY)

### STEP 4: CREATE VULNERABLE TARGET VMs
Recommended targets (download and import each):

1. **Metasploitable 2** (classic vulnerable Linux)
   - Download: https://sourceforge.net/projects/metasploitable/files/Metasploitable2/
   - Import OVF, set network to LabNetwork
   - IP: 10.0.0.102
   - creds: msfadmin/msfadmin

2. **Metasploitable 3** (more modern, Windows + Linux)
   - Build from source or download pre-built
   - More realistic vulnerabilities

3. **OWASP Juice Shop** (modern web app vulnerabilities)
   - Run as Docker container or VM
   - Full of web vulnerabilities (XSS, SQLi, CSRF, SSRF, etc.)

4. **DVWA (Damn Vulnerable Web Application)**
   - Docker: docker run --rm -it -p 80:80 vulnerables/web-dvwa
   - Or deploy on a VM
   - Configurable difficulty (low/medium/high/impossible)

5. **VulnHub VMs** (various scenarios)
   - Download from https://www.vulnhub.com/
   - Each VM has a specific vulnerability scenario

### STEP 5: VERIFY ISOLATION (CRITICAL)
Before practicing, verify:
1. From attacker VM: ping target VMs (should work — same network)
2. From attacker VM: ping host machine (should NOT work)
3. From attacker VM: ping 8.8.8.8 (should NOT work — no internet)
4. From host: ping VMs (should NOT work)

If any check fails, fix network settings BEFORE practicing.

### STEP 6: TAKE SNAPSHOTS
Take a clean snapshot of each VM before practicing.
Name them clearly (e.g., "Metasploitable2-Clean-State-2026-08-15").

Before each practice session, revert to the clean snapshot.

## ========================================================================
## PRACTICE SCENARIOS (WHAT TO PRACTICE)
## ========================================================================

See daughter_sandbox_setup.md for the full practice curriculum.

Quick reference:

### BEGINNER
- nmap scanning on Metasploitable 2
- Basic exploitation with Metasploit
- Password cracking with John/Hashcat
- DVWA low/medium level exploitation

### INTERMEDIATE
- Web app testing with Burp Suite on Juice Shop
- Full pen test workflow on VulnHub VMs
- Privilege escalation on Metasploitable 3
- Manual SQL injection, XSS, CSRF exploitation

### ADVANCED
- Exploit development (writing custom exploits)
- Active Directory attacks (if Windows-based targets)
- Red team scenarios (multi-step, persistence, evasion)
- Malware analysis (in fully isolated sandbox)

## ========================================================================
## SAFETY RULES (ALWAYS FOLLOW)
## ========================================================================

1. **VERIFY ISOLATION BEFORE EVERY SESSION.**
2. **ONLY PRACTICE ON SYSTEMS YOU OWN.** (The VMs in this lab are yours.)
3. **NEVER USE THESE SKILLS ON REAL SYSTEMS WITHOUT AUTHORIZATION.**
4. **MALWARE SAMPLES: ONLY FROM REPUTABLE SOURCES. Keep in isolated sandbox.**
5. **SNAPSHOTS ARE YOUR SAFETY NET. Snapshot before anything aggressive.**
6. **THE SANDBOX PROTECTS EVERYONE. Practice in isolation = responsible.**

## ========================================================================
## END
## ========================================================================
