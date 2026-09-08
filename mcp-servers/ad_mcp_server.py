#!/usr/bin/env python3
"""
AD MCP Server - Active Directory Attack Simulation Tools
=========================================================
Provides 5 AD attack simulation tools as MCP tools over stdio transport.

Tools:
  1. kerberoast    — Simulate Kerberoasting attack (TGS ticket request for SPN accounts)
  2. asrep_roast   — Simulate AS-REP roasting (accounts without preauth)
  3. golden_ticket — Simulate Golden Ticket forgery (TGT with krbtgt hash)
  4. dcsync        — Simulate DCSync attack (replication rights abuse)
  5. bloodhound    — Simulate Bloodhound data collection (attack paths)

All tools run in simulation mode and return structured JSON describing the
attack chain, required inputs, expected outputs, and detection indicators.
No real network calls are made.
"""

import hashlib
import json
import random
import re
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SERVER_NAME = "ad-mcp"
SERVER_VERSION = "1.0.0"

DEFAULT_DOMAIN = "corp.local"

# Common SPN service types
SPN_SERVICES = [
    "MSSQLSvc", "HTTP", "CIFS", "LDAP", "HOST", "RPC", "SMTP",
    "imap", "pop", "exchangeAB", "exchangeRFR", "MSClusterVirtualServer",
    "TERMSERV", "WSMAN", "RestrictedKrbHost", "DNS",
]

# Simulated user accounts with SPNs
SPN_USER_ACCOUNTS = [
    {"sam": "svc_sql_prod", "spn": "MSSQLSvc/db01.corp.local:1433", "pw_age_days": 145},
    {"sam": "svc_sql_dev", "spn": "MSSQLSvc/db02.corp.local:1433", "pw_age_days": 380},
    {"sam": "svc_web_app", "spn": "HTTP/web.corp.local", "pw_age_days": 90},
    {"sam": "svc_backup", "spn": "CIFS/backup.corp.local", "pw_age_days": 250},
    {"sam": "svc_ldap_ext", "spn": "LDAP/ldap.corp.local", "pw_age_days": 210},
    {"sam": "svc_exchange", "spn": "exchangeAB/mail.corp.local", "pw_age_days": 320},
    {"sam": "svc_batch", "spn": "HOST/batch.corp.local", "pw_age_days": 45},
    {"sam": "svc_monitor", "spn": "HTTP/mon.corp.local", "pw_age_days": 180},
]

# Accounts without pre-authentication
NO_PREAUTH_ACCOUNTS = [
    {"sam": "legacy_app", "reason": "Pre-authentication not required (admin set)"},
    {"sam": "batch_service", "reason": "Account created before 2000 domain functional level"},
    {"sam": "test_account", "reason": "Do not enable Kerberos preauthentication checked"},
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _fake_rc4_hash(password: str) -> str:
    """Simulate RC4-HMAC (NTLM) hash (md4 unavailable in this build, use sha256)."""
    return hashlib.sha256(f"ntlm:{password}".encode()).hexdigest()[:32]


def _fake_aes_hash(password: str, salt: str) -> str:
    """Simulate AES256-CTS-HMAC-SHA1-96 key."""
    return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()


def _fake_tgt_blob() -> str:
    return hashlib.sha256(str(random.getrandbits(256)).encode()).hexdigest()[:64]


def _fake_tgs_blob() -> str:
    return hashlib.sha256(str(random.getrandbits(256)).encode()).hexdigest()[:64]


def _validate_domain(domain: str) -> str:
    domain = domain.strip().lower()
    if not re.match(r"^[a-z0-9][a-z0-9\-]*(\.[a-z0-9][a-z0-9\-]*)+$", domain):
        return DEFAULT_DOMAIN
    return domain


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

app = FastMCP(SERVER_NAME)


@app.tool(
    name="kerberoast",
    description=(
        "Simulate a Kerberoasting attack: request TGS tickets for SPN-registered accounts, "
        "then crack them offline to recover plaintext passwords. "
        "Returns SPN accounts found, ticket details, and cracking simulation results."
    ),
)
def kerberoast(
    domain: str = DEFAULT_DOMAIN,
    dc_ip: str = "10.0.0.1",
    crack: bool = True,
) -> str:
    """Simulate Kerberoasting attack (TGS-REQ abuse)."""
    domain = _validate_domain(domain)
    random.seed(hash(domain + dc_ip))
    timestamp = _now_iso()

    spn_accounts = list(SPN_USER_ACCOUNTS)
    tickets: List[Dict[str, Any]] = []
    for acct in spn_accounts:
        aes_key = _fake_aes_hash(
            password=f"PwFor_{acct['sam']}!",
            salt=f"{domain.upper()}{acct['sam']}",
        )
        tickets.append({
            "sam_account_name": acct["sam"],
            "spn": acct["spn"],
            "encryption_type": "AES256-CTS-HMAC-SHA1-96",
            "ticket_flags": ["forwardable", "renewable", "canonicalize"],
            "start_time": timestamp,
            "end_time": (datetime.utcnow() + timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "ticket_blob": _fake_tgs_blob(),
            "aes_sha1_hash": aes_key,
            "password_last_set_days_ago": acct["pw_age_days"],
        })

    cracked: List[Dict[str, Any]] = []
    if crack:
        weak_passwords = {
            "svc_sql_dev": "SqlDev2023!",
            "svc_batch": "batch123",
            "svc_monitor": "monitor1",
        }
        for ticket in tickets:
            sam = ticket["sam_account_name"]
            if sam in weak_passwords:
                cracked.append({
                    "sam_account_name": sam,
                    "spn": ticket["spn"],
                    "cracked_password": weak_passwords[sam],
                    "crack_time_seconds": round(random.uniform(0.01, 2.5), 2),
                    "method": "wordlist_top10k",
                })

    detection_indicators = [
        "Event ID 4769 (TGS Request) with encryption type RC4 (0x17) — downgrade indicator",
        "High volume of TGS-REQ from single source IP in short window",
        "TGS-REQ for multiple SPNs without prior AS-REQ (ticket cache behavior)",
        "Logon event 4624 with logon type 3 from attacker host post-compromise",
    ]

    result = {
        "attack": "kerberoast",
        "simulation": True,
        "timestamp": timestamp,
        "target": {"domain": domain, "kdc_ip": dc_ip},
        "phase_1_enumeration": {
            "method": "LDAP query: (servicePrincipalName=*)",
            "total_spn_accounts": len(spn_accounts),
            "accounts": [{"sam": a["sam"], "spn": a["spn"]} for a in spn_accounts],
        },
        "phase_2_ticket_requests": {
            "tool": "Impacket GetUserSPNs / Rubeus kerberoast",
            "tickets_requested": len(tickets),
            "tickets": tickets,
        },
        "phase_3_cracking": {
            "enabled": crack,
            "tool": "hashcat -m 13100 / john --format=krb5tgs",
            "cracked_count": len(cracked),
            "cracked_accounts": cracked,
        },
        "impact": {
            "severity": "high",
            "description": "Service account plaintext passwords recovered. Lateral movement and privilege escalation likely.",
            "cracked_count": len(cracked),
            "total_accounts": len(spn_accounts),
        },
        "detection_indicators": detection_indicators,
        "mitigations": [
            "Use Group Managed Service Accounts (gMSA) — automatic password rotation",
            "Enforce AES-only Kerberos encryption, disable RC4",
            "Set long (25+ char) random passwords on all service accounts",
            "Monitor Event ID 4769 for anomalous TGS request volume",
        ],
    }
    return json.dumps(result, indent=2)


@app.tool(
    name="asrep_roast",
    description=(
        "Simulate an AS-REP roasting attack: target AD accounts that have "
        "Do not require Kerberos preauthentication enabled. Request AS-REP "
        "hashes and crack them offline without sending a single TGS request."
    ),
)
def asrep_roast(
    domain: str = DEFAULT_DOMAIN,
    dc_ip: str = "10.0.0.1",
    crack: bool = True,
) -> str:
    """Simulate AS-REP Roasting attack."""
    domain = _validate_domain(domain)
    random.seed(hash(domain + "asrep"))
    timestamp = _now_iso()

    no_preauth = list(NO_PREAUTH_ACCOUNTS)
    asrep_hashes: List[Dict[str, Any]] = []
    for acct in no_preauth:
        password = f"Asrep_{acct['sam']}123"
        asrep_hashes.append({
            "sam_account_name": acct["sam"],
            "reason": acct["reason"],
            "encryption_type": "AES256-CTS-HMAC-SHA1-96",
            "kerberos_key": _fake_aes_hash(password, f"{domain.upper()}{acct['sam']}"),
            "as_rep_blob": _fake_tgt_blob()[:48],
        })

    cracked: List[Dict[str, Any]] = []
    if crack:
        weak = {"legacy_app": "Password1", "batch_service": "batch2000"}
        for h in asrep_hashes:
            sam = h["sam_account_name"]
            if sam in weak:
                cracked.append({
                    "sam_account_name": sam,
                    "cracked_password": weak[sam],
                    "crack_time_seconds": round(random.uniform(0.01, 1.0), 2),
                })

    result = {
        "attack": "asrep_roast",
        "simulation": True,
        "timestamp": timestamp,
        "target": {"domain": domain, "kdc_ip": dc_ip},
        "phase_1_identification": {
            "method": "LDAP query: (userAccountControl:1.2.840.113556.1.4.803:=4194304)",
            "description": "Accounts with DONT_REQUIRE_PREAUTH flag set",
            "accounts_found": len(no_preauth),
            "accounts": [{"sam": a["sam"], "reason": a["reason"]} for a in no_preauth],
        },
        "phase_2_asrep_extraction": {
            "tool": "Impacket GetNPUsers / Rubeus asreproast",
            "as_rep_hashes_collected": len(asrep_hashes),
            "hashes": asrep_hashes,
        },
        "phase_3_cracking": {
            "enabled": crack,
            "tool": "hashcat -m 18200 / john --format=krb5asrep",
            "cracked_count": len(cracked),
            "cracked_accounts": cracked,
        },
        "impact": {
            "severity": "high",
            "description": "Account passwords recovered without triggering TGS-request events. Stealthier than Kerberoasting.",
        },
        "detection_indicators": [
            "Event ID 4768 (AS-REQ) with pre-authentication not performed",
            "AS-REQ volume spike from single source",
            "Account with DONT_REQUIRE_PREAUTH is actively being used",
        ],
        "mitigations": [
            "Audit all accounts with DONT_REQUIRE_PREAUTH and remove the flag",
            "Ensure all accounts require pre-authentication (default since Windows 2000)",
            "Monitor Event ID 4768 for pre-auth-not-performed anomalies",
        ],
    }
    return json.dumps(result, indent=2)


@app.tool(
    name="golden_ticket",
    description=(
        "Simulate a Golden Ticket forgery attack: using the krbtgt account NT hash "
        "to forge arbitrary TGT tickets, granting any user any privilege including "
        "Domain Admin. Persists because the krbtgt hash is never automatically changed."
    ),
)
def golden_ticket(
    domain: str = DEFAULT_DOMAIN,
    dc_ip: str = "10.0.0.1",
    impersonate_user: str = "Administrator",
    groups: Optional[List[str]] = None,
) -> str:
    """Simulate Golden Ticket forgery (krbtgt hash abuse)."""
    domain = _validate_domain(domain)
    random.seed(hash(domain + "golden"))
    timestamp = _now_iso()

    if groups is None:
        groups = [
            "S-1-5-21-0-512",
            "S-1-5-21-0-519",
            "S-1-5-21-0-544",
            "S-1-5-21-0-517",
        ]

    krbtgt_nt_hash = _fake_rc4_hash("krbtgt_password_never_changes")
    krbtgt_aes_hash = _fake_aes_hash("krbtgt_password_never_changes", f"{domain.upper()}krbtgt")

    forged_tgt = {
        "domain": domain,
        "domain_sid": "S-1-5-21-3623811015-3361044348-30300820",
        "username": impersonate_user,
        "groups": groups,
        "ticket_lifetime_hours": 1008,
        "renewable_lifetime_days": 10,
        "flags": ["forwardable", "renewable", "initial", "pre_authent"],
        "krbtgt_nt_hash_used": krbtgt_nt_hash,
        "krbtgt_aes_hash_used": krbtgt_aes_hash,
        "forged_ticket_blob": _fake_tgt_blob(),
        "pac_valid": True,
        "is_validated_by_dc": True,
    }

    result = {
        "attack": "golden_ticket",
        "simulation": True,
        "timestamp": timestamp,
        "target": {"domain": domain, "kdc_ip": dc_ip},
        "phase_1_krbtgt_hash_theft": {
            "method": "DCSync (DSGetNCReplication) or NTDS.dit offline extraction",
            "target_account": "krbtgt",
            "nt_hash": krbtgt_nt_hash,
            "aes_hash": krbtgt_aes_hash,
        },
        "phase_2_ticket_forgery": {
            "tool": "Impacket ticketer / Rubeus golden / Mimikatz kerberos::golden",
            "forged_tgt": forged_tgt,
            "capabilities": [
                f"Impersonate {impersonate_user} or any domain user",
                "Include arbitrary group SIDs (Domain Admins, etc.)",
                "Set ticket lifetime up to 10 years",
                "Bypass normal password expiry checks",
            ],
        },
        "phase_3_persistence": {
            "description": "Golden Ticket persists until krbtgt password is changed TWICE.",
            "detection_difficulty": "very_high",
            "indicators": [
                "TGT lifetime exceeds domain policy (default 10 hours)",
                "PAC validation skipped",
                "Account from unregistered logon session accesses resources",
            ],
        },
        "impact": {
            "severity": "critical",
            "description": "Full domain compromise. Attacker can impersonate any user with any group membership.",
        },
        "detection_indicators": [
            "TGT lifetime exceeds max ticket age (Event 4769 with unusual end time)",
            "PAC checksum mismatch",
            "Kerberos TGS-REQ without preceding AS-REQ in logs",
            "Accounts accessing resources from IPs they have never used before",
        ],
        "mitigations": [
            "Rotate krbtgt password TWICE (with replication delay between rotations)",
            "Enable Protected Users group for high-privilege accounts",
            "Monitor for TGT lifetimes exceeding domain maxTicketAge (default 10h)",
            "Deploy ATA / Microsoft Defender for Identity for anomaly detection",
        ],
    }
    return json.dumps(result, indent=2)


@app.tool(
    name="dcsync",
    description=(
        "Simulate a DCSync attack: abuse AD replication rights (DS-Replication-Get-Changes, "
        "DS-Replication-Get-Changes-All) to impersonate a DC and pull password hashes "
        "for any account including krbtgt, without running code on the DC itself."
    ),
)
def dcsync(
    domain: str = DEFAULT_DOMAIN,
    dc_ip: str = "10.0.0.1",
    target_accounts: Optional[List[str]] = None,
) -> str:
    """Simulate DCSync attack (replication rights abuse)."""
    domain = _validate_domain(domain)
    random.seed(hash(domain + "dcsync"))
    timestamp = _now_iso()

    if target_accounts is None:
        target_accounts = ["krbtgt", "Administrator", "admin_svc", "svc_sql_prod"]

    required_rights = [
        "DS-Replication-Get-Changes (1131F6AA-9C07-11D1-F79F-00C04FC2DCD2)",
        "DS-Replication-Get-Changes-All (1131F6AD-9C07-11D1-F79F-00C04FC2DCD2)",
        "DS-Replication-Get-Changes-In-Filtered-Set (89e95b76-444d-4c62-991a-0facbeda640c)",
    ]

    hashes: List[Dict[str, Any]] = []
    for acct in target_accounts:
        nt_hash = _fake_rc4_hash(f"password_for_{acct}")
        hashes.append({
            "sam_account_name": acct,
            "domain": domain,
            "nt_hash": nt_hash,
            "lm_hash": "aad3b435b51404eeaad3b435b51404ee",
            "distinguished_name": f"CN={acct},CN=Users,DC={domain.replace('.', ',DC=')}",
            "object_sid": f"S-1-5-21-0-{random.randint(1000, 999999)}",
            "pwd_last_set": (datetime.utcnow() - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d"),
        })

    result = {
        "attack": "dcsync",
        "simulation": True,
        "timestamp": timestamp,
        "target": {"domain": domain, "kdc_ip": dc_ip},
        "phase_1_rights_verification": {
            "required_rights": required_rights,
            "accounts_with_rights": [
                "Domain Admins",
                "Enterprise Admins",
                "Administrators",
                "DC computer accounts",
            ],
            "tool": "BloodHound / PowerView Get-ObjectAcl",
        },
        "phase_2_replication_abuse": {
            "tool": "Impacket secretsdump / Mimikatz lsadump::dcsync",
            "protocol": "DRSUAPI (MS-DRSR) — RPC over TCP 135 + dynamic ports",
            "targeted_accounts": len(target_accounts),
            "extracted_hashes": hashes,
        },
        "impact": {
            "severity": "critical",
            "description": "NTLM hashes extracted for any domain account. Enables PtH, Golden Ticket, lateral movement.",
        },
        "detection_indicators": [
            "Event ID 4662 with Properties containing replication GUIDs from non-DC source",
            "Event ID 4624 logon from non-DC machine with replication SPN",
            "Network traffic: DRSUAPI RPC from non-DC",
            "Unexpected Event 4662 with replication GUID by non-admin user",
        ],
        "mitigations": [
            "Restrict replication rights to DC computer accounts only",
            "Monitor Event 4662 for DRSUAPI access from non-DC hosts",
            "Deploy Microsoft Defender for Identity",
            "Enable Protected Users group to prevent NTLM hash caching",
        ],
    }
    return json.dumps(result, indent=2)


@app.tool(
    name="bloodhound",
    description=(
        "Simulate Bloodhound data collection: ingest AD data via SharpHound ingestor, "
        "then analyze attack paths showing how unprivileged users can reach Domain Admin "
        "through group memberships, ACL abuse, GPO control, and session chains."
    ),
)
def bloodhound(
    domain: str = DEFAULT_DOMAIN,
    collection_method: str = "default",
    include_sessions: bool = True,
) -> str:
    """Simulate BloodHound data collection and attack path analysis."""
    domain = _validate_domain(domain)
    random.seed(hash(domain + "bloodhound"))
    timestamp = _now_iso()

    collection = {
        "tool": "SharpHound.exe (BloodHound ingestor)",
        "method": collection_method,
        "options": [
            "--CollectionMethod All",
            "--Stealth (avoids DC-only paths)",
            "--Loop (continuous session collection)",
        ],
        "collected_objects": {
            "users": random.randint(80, 250),
            "groups": random.randint(40, 120),
            "computers": random.randint(50, 200),
            "ous": random.randint(10, 40),
            "gpos": random.randint(5, 25),
            "domains": 1,
            "containers": random.randint(15, 50),
        },
    }

    sessions: List[Dict[str, Any]] = []
    if include_sessions:
        for _ in range(random.randint(5, 15)):
            sessions.append({
                "user": random.choice(["jsmith", "agarcia", "dlee", "kwilsson", "admin_svc"]),
                "computer": f"WS-{random.randint(100, 999)}.corp.local",
                "logon_time": (datetime.utcnow() - timedelta(hours=random.randint(1, 48))).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "admin_rights": random.random() < 0.3,
            })

    attack_paths: List[Dict[str, Any]] = [
        {
            "path_id": 1,
            "name": "ACL Abuse to DA",
            "start": "Domain Users",
            "target": "Domain Admins",
            "steps": [
                "GenericAll on Group 'IT-Admins'",
                "IT-Admins has GenericAll on Domain Admins group",
                "Add self to IT-Admins then add self to Domain Admins",
            ],
            "hops": 2,
            "severity": "high",
        },
        {
            "path_id": 2,
            "name": "Session Chain to DA",
            "start": "User: jsmith (Domain User)",
            "target": "Domain Admins",
            "steps": [
                "jsmith has admin session on WS-205",
                "DA session (admin_svc) active on WS-205",
                "Lateral movement to WS-205 then steal admin_svc token",
            ],
            "hops": 2,
            "severity": "high",
        },
        {
            "path_id": 3,
            "name": "GPO Abuse to DA",
            "start": "GPO: 'Workstation Config'",
            "target": "Domain Admins",
            "steps": [
                "IT-Admins has WriteProperty on GPO 'Workstation Config'",
                "GPO linked to OU containing all workstations",
                "Modify GPO to run scheduled task as SYSTEM on target DA workstation",
            ],
            "hops": 3,
            "severity": "medium",
        },
        {
            "path_id": 4,
            "name": "Group Nesting to Enterprise Admins",
            "start": "HelpDesk group",
            "target": "Enterprise Admins",
            "steps": [
                "HelpDesk is nested in Local Admins on all servers",
                "Local Admins group has Domain Admin rights on DC01",
                "Enterprise Admins are Domain Admins in all domains in forest",
            ],
            "hops": 3,
            "severity": "medium",
        },
    ]

    total_users = collection["collected_objects"]["users"]
    total_computers = collection["collected_objects"]["computers"]
    da_count = random.randint(2, 8)

    result = {
        "attack": "bloodhound",
        "simulation": True,
        "timestamp": timestamp,
        "target": {"domain": domain},
        "phase_1_collection": collection,
        "phase_2_session_data": {
            "enabled": include_sessions,
            "total_sessions_collected": len(sessions),
            "sessions": sessions[:10],
        },
        "phase_3_attack_paths": {
            "tool": "BloodHound Neo4j Cypher queries / SharpHound analysis",
            "total_paths_identified": len(attack_paths),
            "shortest_path_hops": min(p["hops"] for p in attack_paths),
            "paths": attack_paths,
        },
        "phase_4_key_statistics": {
            "total_users": total_users,
            "total_computers": total_computers,
            "domain_admin_count": da_count,
            "users_with_dapaths": random.randint(10, min(50, total_users)),
            "percent_users_can_reach_da": round(random.uniform(5.0, 35.0), 1),
            "users_with_sessions_on_dacomputers": random.randint(1, 8),
        },
        "impact": {
            "severity": "informational to critical",
            "description": "BloodHound maps the attack surface, revealing paths to DA that may be invisible to defenders.",
        },
        "detection_indicators": [
            "SharpHound.exe process execution (EDR detection of known hash)",
            "Volume of LDAP queries exceeding normal admin tooling patterns",
            "Network connections from non-admin hosts to LDAP (389) and LDAPS (636)",
            "Temporary ZIP files with BloodHound JSON schema in user temp directories",
        ],
        "mitigations": [
            "Audit and remove excessive ACL permissions (BloodHound shows exact paths)",
            "Minimize group nesting and unnecessary admin sessions",
            "Use Protected Users group for DA accounts",
            "Deploy EDR rules to detect SharpHound ingestor execution",
        ],
    }
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(transport="stdio")
