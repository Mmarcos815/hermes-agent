# Module 4: Network Scanning

## Objectives
- Perform comprehensive network discovery using Nmap
- Identify live hosts, open ports, services, and OS fingerprints
- Conduct safe and efficient scan strategies
- Interpret scan results to inform exploitation decisions

---

## 4.1 Network Scanning Fundamentals

Network scanning is the process of systematically probing a network to discover hosts, services, and potential entry points. It bridges reconnaissance and exploitation — you can't attack what you don't know exists.

|| Scan Type | Purpose | Intensity |
|----------|----------|---------|-----------|
| Host Discovery | Find live hosts | Low |
| Port Scanning | Identify open ports | Low–Medium |
| Service Enumeration | Determine running services | Medium |
| OS Fingerprinting | Identify target OS | Medium |
| Version Detection | Identify service versions | Medium–High |
| Script Scanning | Run NSE scripts for deeper info | High |

**Rules of Engagement Reminder:** Only scan systems you are authorized to test. Excessive scanning can trigger IDS/IPS, cause denial of service on fragile systems, or alert defenders.

---

## 4.2 Nmap Essentials

Nmap is the industry-standard network scanner. Its flexibility makes it both a recon tool and an exploitation precursor.

### Host Discovery
```bash
# Ping sweep — find live hosts quickly
nmap -sn 10.10.1.0/24

# ARP scan on local network (faster, more reliable)
nmap -sn -PR 10.10.1.0/24

# Discover hosts even with ICMP blocked
nmap -sn -PS22 -PS80 -PA80 10.10.1.0/24
```

### Port Scanning Techniques
```bash
# TCP connect scan (completes full 3-way handshake)
nmap -sT 10.10.1.20

# SYN scan (half-open, stealthier) — requires root
sudo nmap -sS 10.10.1.20

# UDP scan (slow, often overlooked by defenders)
sudo nmap -sU 10.10.1.20

# Top 1000 ports (default)
nmap 10.10.1.20

# All 65535 ports
nmap -p- 10.10.1.20

# Specific ports
nmap -p 22,80,135,139,445,3389 10.10.1.20
```

### Service and Version Detection
```bash
# Determine service versions
nmap -sV 10.10.1.20

# Determine OS (requires at least one open port)
sudo nmap -O 10.10.1.20

# Aggressive scan: OS, version, script, traceroute
nmap -A 10.10.1.20

# Combine with fast mode: top 100 ports, version detection
nmap -F -sV 10.10.1.20
```

### Nmap Scripting Engine (NSE)
NSE extends Nmap with Lua scripts for vulnerability detection, brute-forcing, and discovery.

```bash
# Default scripts, safe category
nmap --script safe 10.10.1.20

# Vulnerability detection scripts
nmap --script vuln 10.10.1.20

# SMB enumeration
nmap --script smb-enum-shares,smb-enum-users -p 445 10.10.1.100

# SNMP enumeration
nmap --script snmp-brute,snmpsim-brute -p 161 10.10.1.20

# LDAP enumeration
nmap --script ldap-rootdse,ldap-search -p 389 10.10.1.100

# Run a specific script with arguments
nmap --script http-enum --script-args http-enum.path=/dvwa 10.10.1.50
```

### Scan Optimization
```bash
# Timing templates: T0 (paranoid) to T5 (insane)
nmap -T4 10.10.1.0/24

# Scan multiple hosts in parallel
nmap --min-parallelism 10 --max-parallelism 100 10.10.1.0/24

# Resume an interrupted scan
nmap --resume log.xml

# Save output in multiple formats
nmap -oA scan_results 10.10.1.20
```

---

## 4.3 Service Enumeration Deep Dive

### SMB (Ports 135, 139, 445)
SMB is critical in Windows environments. Enumeration reveals shares, users, policies, and OS details.

```bash
# Nmap SMB enumeration
nmap -sV --script "smb-*" -p 135,139,445 10.10.1.100

# smbclient — list shares (null session if allowed)
smbclient -L //10.10.1.100 -N

# smbclient — interact with a specific share
smbclient //10.10.1.100/IPC$ -N
smbclient //10.10.1.100/restricted -U guest%

# nmap scripts for detailed SMB info
nmap --script smb-os-discovery,smb-security-mode,smb-enum-shares,smb-enum-users -p 445 10.10.1.100
```

### SNMP (Port 161)
Misconfigured SNMP services expose network device information with default community strings.

```bash
# SNMP community string brute-force
nmap --script snmp-brute -p 161 10.10.1.20

# SNMP walk with common community strings
snmpwalk -v2c -c public 10.10.1.20
snmpwalk -v2c -c private 10.10.1.20

# Extract useful info from SNMP
snmpwalk -v2c -c public 10.10.1.20 .1.3.6.1.2.1.1  # System info
snmpwalk -v2c -c public 10.10.1.20 .1.3.6.1.2.1.25 # Host resources
```

### LDAP (Port 389/636)
Active Directory environments expose LDAP for directory queries.

```bash
# LDAP root DSE enumeration
nmap --script ldap-rootdse -p 389 10.10.1.100

# LDAP search (anonymous if allowed)
ldapsearch -x -H ldap://10.10.1.100 -b "dc=corp,dc=local"

# Extract users, groups, computers
ldapsearch -x -H ldap://10.10.1.100 -b "dc=corp,dc=local" "(objectClass=user)" sAMAccountName
ldapsearch -x -H ldap://10.10.1.100 -b "dc=corp,dc=local" "(objectClass=group)" cn
```

### RPC / MSRPC (Port 135)
Windows RPC endpoint mapper reveals available services.

```bash
# Nmap RPC enumeration
nmap --script msrpc-enum -p 135 10.10.1.100

# rpcdump (Impacket) — enumerate RPC endpoints
rpcdump.py 10.10.1.100
```

### FTP (Port 21)
FTP is frequently misconfigured with anonymous access.

```bash
# Anonymous login check
ftp 10.10.1.20
# login: anonymous, password: anonymous
nmap --script ftp-anon -p 21 10.10.1.20

# FTP bounce scan (deprecated but educational)
nmap -b anonymous:anonymous@10.10.1.20 10.10.1.0/24
```

### SSH (Port 22)
SSH provides remote access but also leaks version info.

```bash
# Banner grabbing
nc -v 10.10.1.20 22

# SSH version detection
nmap -sV -p 22 10.10.1.20

# SSH enumeration scripts
nmap --script ssh2-enum-algos -p 22 10.10.1.20
```

---

## 4.4 Scan Planning and Stealth

Effective scanning balances speed, coverage, and detectability.

### Scan Strategy by Phase
1. **Passive reconnaissance first** — use OSINT, don't scan yet.
2. **Host discovery** — narrow the scope to live targets.
3. **Port scanning** — find open ports on live hosts.
4. **Service/version detection** — identify what's running.
5. **Targeted NSE scripts** — gather deeper intelligence on specific services.

### Avoiding Detection
- Use `T2` or `T3` timing instead of `T4`/`T5`
- Scan non-peak hours if RoE allows
- Fragment packets: `nmap -f` (may bypass some IDS)
- Decoy scanning: `nmap -D RND:10` (spoofs source IPs)
- Slow scanning with `--scan-delay` and `--max-rate`

### Legal and Ethical Boundaries
- Written authorization must define allowed targets and techniques
- Some scan types (SYN, UDP, ACK) may be interpreted differently across jurisdictions
- Document everything — you may need to prove what you scanned and why

---

## 4.5 Lab: Network Scanning

### Setup
- Target network: 10.10.1.0/24 (Kali = 10.10.1.10)
- Targets: Metasploitable (10.10.1.20), Windows Server (10.10.1.100), Windows 10 (10.10.1.101), DVWA (10.10.1.50)

### Tasks
1. **Host Discovery:** Run a ping sweep of the entire /24. Document all live hosts. Verify with `arp -a` on the Kali host. Time the scan with `time nmap -sn 10.10.1.0/24`.

2. **Port Scan Comparison:** For each live host, run:
   - A default scan (`nmap <host>`)
   - A SYN scan (`sudo nmap -sS <host>`)
   - A full port scan (`nmap -p- <host>`)
   Compare results: which ports are missed by the default scan? Which scan takes longest?

3. **Service Enumeration:** On each target with open ports, run `-sV` and `-A`. Document:
   - Service name and version for each port
   - OS fingerprint result
   - Any NSE script output

4. **SMB Enumeration:** Target 10.10.1.100 (Windows Server DC). Use:
   - `smbclient -L` with and without credentials
   - Nmap SMB scripts
   - `rpcdump.py` from Impacket
   Document all discovered shares, users, and policies.

5. **SNMP Enumeration:** If Metasploitable has SNMP open (port 161), run:
   - `nmap --script snmp-brute`
   - `snmpwalk` with public/private community strings
   Document what information is exposed.

6. **Scan Output Management:** Save results in all three formats (normal, XML, grepable):
   ```bash
   nmap -oA network_scan 10.10.1.0/24
   ```
   Parse the grepable output: `cat network_scan.gnmap | grep "Open"`.

### Bonus: Stealth Scan
Run the same scan with `-T2` and `-T4`. Compare scan duration and any differences in detected ports. Observe if your IDS/security tools alert (check DVWA logs or Windows Event Viewer if available).

---

## 4.6 Expected Outcomes

By the end of this module, you should be able to:
- Run Nmap scans appropriate to each phase of reconnaissance
- Enumerate SMB, SNMP, LDAP, FTP, and SSH services
- Interpret Nmap output and identify potential targets
- Select appropriate scan types based on objectives and stealth requirements
- Save and parse scan results for reporting

---

## 4.7 Assessment Criteria

| Criteria | Points | Description |
|----------|--------|-------------|
| Host discovery | 5 | Correctly identifies all live hosts in the lab network |
| Port scanning | 10 | Completes port scans on all targets; identifies at least 80% of open ports |
| Service enumeration | 10 | Accurately documents services and versions for each open port |
| SMB/SNMP/LDAP enumeration | 10 | Discovers shares, users, community strings, or directory entries |
| Scan comparison | 5 | Compares scan types and explains differences |
| Output management | 5 | Saves results in all formats, parses grepable output |
| Report quality | 10 | Clear methodology, organized findings, scan commands documented |
| **Total** | **55** | |

**Pass threshold:** 40/55 (73%)

### Report Requirements (2–3 pages)
1. Scan methodology — what you scanned, how, and why
2. Host discovery results table (IP, hostname if available, status)
3. Port/service table for each target (port, protocol, service, version, notes)
4. SMB/SNMP/LDAP findings with raw output snippets
5. Scan comparison observations
6. Defensive recommendations: what network-level controls would reduce attack surface visibility
