"""AD Attacks MCP Server — Simulated Active Directory attack primitives.

Educational/defensive simulation only. Each tool models what an attacker
observes at each stage and returns structured JSON describing the technique
without performing any real network action.
"""

from __future__ import annotations

import json
import random
import string
from datetime import datetime, timezone
from typing import Any

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ad-attacks")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hex(n: int, length: int = 16) -> str:
    return "".join(random.choices("0123456789abcdef", k=length))


def _nthash(password: str) -> str:
    """Return a deterministic-looking NT hash stub from a password."""
    h = 0
    for ch in password.encode("utf-16-le"):
        h = (h * 31 + ch) & 0xFFFFFFFF
    return f"{h:08x}{_hex(24)}"


def _krbtgt_hash(domain: str) -> str:
    return f"{_hex(16)}-{_hex(16)}-{_hex(8)}"


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def kerberoast(
    target_spn: str = "MSSQLSvc/sql01.corp.local:1433",
    domain: str = "corp.local",
    username: str = "svc_sql",
) -> dict[str, Any]:
    """Simulate a Kerberoasting attack — request a TGS ticket for an SPN,
    then extract a hashcat-crackable Kerberos ticket hash.

    Returns the SPN enumerated, the fake ticket blob, the crackable hash
    line, and the technique's MITRE ATT&CK reference.
    """
    ticket_blob = f"krb5_tgs@{_hex(32)}"
    crackable_hash = (
        f"$krb5tgs$23$*{username}${domain}${target_spn}"
        f"*${_hex(32)}${_hex(64)}"
    )
    return {
        "technique": "Kerberoasting",
        "mitre_attack": "T1558.003",
        "timestamp": _timestamp(),
        "target_spn": target_spn,
        "domain": domain,
        "service_account": username,
        "ticket_type": "RC4-HMAC (type 23) — crackable",
        "ticket_blob": ticket_blob,
        "crackable_hash": crackable_hash,
        "defensive_notes": [
            "Monitor 4769 events for RC4 ticket requests on service accounts.",
            "Use gMSAs with long, random passwords for all service accounts.",
            "Set SPN accounts to AES-only and audit for downgrade.",
        ],
    }


@mcp.tool()
def asrep_roast(
    domain: str = "corp.local",
    username: str = "jdoe",
) -> dict[str, Any]:
    """Simulate AS-REP roasting — find accounts with 'Do not require
    Kerberos preauthentication' enabled, request an AS-REP, and extract
    a crackable hash (no password needed to request it).

    Returns the enumerated account flag, the crackable hash, and refs.
    """
    crackable_hash = (
        f"$krb5asrep$23${username}@{domain}"
        f":${_hex(32)}${_hex(64)}"
    )
    return {
        "technique": "AS-REP Roasting",
        "mitre_attack": "T1558.004",
        "timestamp": _timestamp(),
        "domain": domain,
        "target_account": username,
        "preauth_enabled": False,
        "crackable_hash": crackable_hash,
        "defensive_notes": [
            "Audit accounts with DONT_REQUIRE_PREAUTH (UAC 0x400000).",
            "All accounts should require Kerberos preauthentication by default.",
        ],
    }


@mcp.tool()
def golden_ticket(
    domain: str = "corp.local",
    domain_sid: str = "S-1-5-21-3623811015-3361044348-30300820",
    target_user: str = "Administrator",
) -> dict[str, Any]:
    """Simulate Golden Ticket forgery — with the krbtgt NT hash, forge a
    TGT granting arbitrary domain access. Returns ticket parameters and
    detection guidance.
    """
    krbtgt = _krbtgt_hash(domain)
    forged_tgt = {
        "domain": domain,
        "domain_sid": domain_sid,
        "user": target_user,
        "user_rid": "500",
        "groups": ["512", "513", "519"],  # Domain Admins, Domain Users, Enterprise Admins
        "start_time": _timestamp(),
        "lifetime_hours": 10,
        "ticket_flags": ["forwardable", "renewable"],
        "session_key": _hex(16),
    }
    return {
        "technique": "Golden Ticket",
        "mitre_attack": "T1558.001",
        "timestamp": _timestamp(),
        "krbtgt_nt_hash": krbtgt,
        "forged_tgt": forged_tgt,
        "defensive_notes": [
            "Rotate the krbtgt password twice (invalidates existing TGTs).",
            "Monitor 4769 for TGT lifetimes exceeding domain policy.",
            "Detect anomalous TGTs with PAC validation gaps.",
        ],
    }


@mcp.tool()
def dcsync(
    domain: str = "corp.local",
    target_dn: str = "CN=krbtgt,CN=Users,DC=corp,DC=local",
) -> dict[str, Any]:
    """Simulate a DCSync attack — abuse AD replication permissions to
    request password hashes from a domain controller.

    Returns the replicated objects and detection guidance.
    """
    return {
        "technique": "DCSync",
        "mitre_attack": "T1003.006",
        "timestamp": _timestamp(),
        "domain": domain,
        "replicated_objects": [
            {
                "dn": "CN=krbtgt,CN=Users,DC=corp,DC=local",
                "object_class": "user",
                "nt_hash": _nthash("krbtgt_placeholder"),
                "supplementary_credentials": _hex(200),
            },
            {
                "dn": target_dn,
                "object_class": "user",
                "nt_hash": _nthash("target_placeholder"),
                "supplementary_credentials": _hex(200),
            },
        ],
        "defensive_notes": [
            "Monitor 4662 for DS-Replication-Get-Changes-All on domain NC.",
            "Restrict replication rights to legitimate DCs only.",
            "Alert on 5136 for replication permission modifications.",
        ],
    }


@mcp.tool()
def bloodhound(
    domain: str = "corp.local",
    collection_methods: list[str] = ["Session", "LocalAdmin", "Trusts", "ACL", "Container"],
) -> dict[str, Any]:
    """Simulate BloodHound data collection — enumerate AD objects to
    build attack-path graphs (sessions, group memberships, ACLs, etc.).

    Returns the graph nodes/edges discovered and defensive mitigations.
    """
    nodes = [
        {"type": "User", "name": "admin@corp.local", "props": {"domain": domain}},
        {"type": "Group", "name": "Domain Admins@corp.local"},
        {"type": "Computer", "name": "DC01.corp.local", "os": "Windows Server 2022"},
        {"type": "Computer", "name": "WORKSTATION01.corp.local", "os": "Windows 11"},
        {"type": "OU", "name": "Sales@corp.local"},
    ]
    edges = [
        {"source": "admin@corp.local", "target": "Domain Admins@corp.local", "kind": "MemberOf"},
        {"source": "Domain Admins@corp.local", "target": "DC01.corp.local", "kind": "AdminTo"},
        {"source": "WORKSTATION01.corp.local", "target": "admin@corp.local", "kind": "HasSession"},
        {"source": "Sales@corp.local", "target": "Domain Admins@corp.local", "kind": "GenericAll"},
    ]
    return {
        "technique": "BloodHound Collection",
        "mitre_attack": "T1087 / T1069 / T1484 (reconnaissance)",
        "timestamp": _timestamp(),
        "domain": domain,
        "collection_methods_used": collection_methods,
        "objects_enumerated": len(nodes) + len(edges),
        "nodes": nodes,
        "edges": edges,
        "attack_paths": [
            {
                "start": "admin@corp.local",
                "end": "DC01.corp.local",
                "path": ["MemberOf", "AdminTo"],
                "risk": "Critical",
            }
        ],
        "defensive_notes": [
            "Audit LDAP searches and restrict anonymous directory queries.",
            "Remove unnecessary GenericAll/WriteDacl ACEs.",
            "Tier admin accounts and enforce PAW (Privileged Access Workstations).",
        ],
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
