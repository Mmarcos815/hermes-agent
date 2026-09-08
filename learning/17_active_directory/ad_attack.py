#!/usr/bin/env python3
"""Active Directory Attack Simulation — Kerberoasting, AS-REP Roasting, Golden Ticket, DCShadow, DCSync.

Educational simulation only. No live exploitation.
Demonstrates attack mechanics for authorized red team training.
"""

import argparse
import hashlib
import hmac
import json
import secrets
import sys
from typing import Optional


class _MD4Hash:
    """Simple wrapper to provide hexdigest() interface."""

    def __init__(self, hex_str: str):
        self._hex = hex_str

    def hexdigest(self) -> str:
        return self._hex


class KerberoastSimulator:
    """Simulate Kerberoasting attack against SPN service accounts."""

    def __init__(self, domain: str):
        self.domain = domain
        self.service_accounts = {
            "svc_sql": {"spn": "MSSQLSvc/sql.corp.local:1433", "hash": self._derive_hash("P@ssw0rd123")},
            "svc_ftp": {"spn": "FTP/ftp.corp.local", "hash": self._derive_hash("FtpPass2023!")},
            "svc_web": {"spn": "HTTP/web.corp.local", "hash": self._derive_hash("Summer2024!")},
        }

    def _derive_hash(self, password: str) -> str:
        """Derive NTLM hash (MD4 of UTF-16LE) — pure Python fallback."""
        try:
            return hashlib.new("md4", password.encode("utf-16le")).hexdigest()
        except (ValueError, TypeError):
            return self._md4(password.encode("utf-16le")).hexdigest()

    @staticmethod
    def _md4(data: bytes) -> _MD4Hash:
        """Minimal pure Python MD4 implementation (48 rounds)."""
        S = ([3, 7, 11, 19] * 4
             + [3, 5, 9, 13] * 4
             + [3, 9, 11, 15] * 4)

        def F(x, y, z): return (x & y) | (~x & z)
        def G(x, y, z): return (x & y) | (x & z) | (y & z)
        def H(x, y, z): return x ^ y ^ z

        def left_rotate(x, n):
            return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF

        G_INDEX = [0, 4, 8, 12, 1, 5, 9, 13, 2, 6, 10, 14, 3, 7, 11, 15]
        H_INDEX = [0, 8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15]

        original_len = len(data)
        padded = data + b"\x80"
        while (len(padded) % 64) != 56:
            padded += b"\x00"
        padded += (original_len * 8).to_bytes(8, "little")

        A, B, C, D = 0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476

        for i in range(0, len(padded), 64):
            block = padded[i:i+64]
            X = [int.from_bytes(block[j:j+4], "little") for j in range(0, 64, 4)]

            a, b, c, d = A, B, C, D

            for j in range(48):
                if j < 16:
                    f = F(b, c, d)
                    k = j
                elif j < 32:
                    f = G(b, c, d)
                    k = G_INDEX[j - 16]
                else:
                    f = H(b, c, d)
                    k = H_INDEX[j - 32]

                temp = (left_rotate((a + f + X[k]) & 0xFFFFFFFF, S[j])) & 0xFFFFFFFF
                a, b, c, d = d, temp, b, c

            A = (A + a) & 0xFFFFFFFF
            B = (B + b) & 0xFFFFFFFF
            C = (C + c) & 0xFFFFFFFF
            D = (D + d) & 0xFFFFFFFF

        result = "".join(
            v.to_bytes(4, "little").hex() for v in (A, B, C, D)
        )
        return _MD4Hash(result)

    def request_tgs(self, username: str) -> dict:
        """Simulate TGS request for a service account."""
        if username not in self.service_accounts:
            return {"error": f"No SPN found for {username}"}

        acct = self.service_accounts[username]
        ticket_data = f"TGS:{self.domain}:{acct['spn']}:{acct['hash']}"
        ticket_hash = hmac.new(b"krbtgt_hash", ticket_data.encode(), hashlib.sha256).hexdigest()

        return {
            "username": username,
            "spn": acct["spn"],
            "domain": self.domain,
            "ticket_type": "TGS-REP",
            "encryption": "RC4-HMAC (vulnerable)",
            "ticket_hash": ticket_hash,
            "crackable": True,
            "weakness": "RC4 encryption allows offline cracking of service account password",
        }

    def roast_all(self, users: list) -> dict:
        """Kerberoast all specified service accounts."""
        results = {"attack": "Kerberoasting", "domain": self.domain, "targets": []}
        for user in users:
            result = self.request_tgs(user)
            results["targets"].append(result)
        return results


class ASREPRoastSimulator:
    """Simulate AS-REP Roasting for accounts without preauth."""

    def __init__(self, domain: str):
        self.domain = domain
        self.vulnerable_accounts = {
            "user1": {"hash": self._derive_hash("Welcome1"), "preauth": False},
            "user2": {"hash": self._derive_hash("Password123"), "preauth": False},
            "user3": {"hash": self._derive_hash("Winter2024!"), "preauth": False},
        }

    def _derive_hash(self, password: str) -> str:
        """Derive NTLM hash (MD4 of UTF-16LE) — pure Python fallback."""
        try:
            return hashlib.new("md4", password.encode("utf-16le")).hexdigest()
        except (ValueError, TypeError):
            return KerberoastSimulator._md4(password.encode("utf-16le")).hexdigest()

    def asrep_request(self, username: str) -> dict:
        """Simulate AS-REP without preauthentication."""
        if username not in self.vulnerable_accounts:
            return {"error": f"{username} requires preauthentication (safe)"}

        acct = self.vulnerable_accounts[username]
        timestamp_data = f"timestamp:{self.domain}:{username}"
        encrypted_ts = hmac.new(acct["hash"].encode(), timestamp_data.encode(), hashlib.sha256).hexdigest()

        return {
            "username": username,
            "preauth_required": False,
            "encrypted_timestamp": encrypted_ts,
            "hash_type": "NTLM (RC4)",
            "crackable": True,
            "weakness": "DONT_REQUIRE_PREAUTH flag set — AS-REP contains crackable hash",
        }

    def roast_all(self, users: list) -> dict:
        """AS-REP roast all specified accounts."""
        results = {"attack": "AS-REP Roasting", "domain": self.domain, "targets": []}
        for user in users:
            results["targets"].append(self.asrep_request(user))
        return results


class GoldenTicketSimulator:
    """Simulate Golden Ticket forgery."""

    def __init__(self, domain: str):
        self.domain = domain
        self.krbtgt_hash = "a9a836a8c8e2b58a9e8b91c3d4e5f6a7"

    def forge_ticket(self, target_user: str, krbtgt_hash: Optional[str] = None) -> dict:
        """Forge a Golden Ticket TGT."""
        hash_used = krbtgt_hash or self.krbtgt_hash
        ticket_data = f"TGT:{self.domain}:{target_user}:{hash_used}"
        forged_tgt = hmac.new(hash_used.encode(), ticket_data.encode(), hashlib.sha256).hexdigest()

        return {
            "attack": "Golden Ticket",
            "domain": self.domain,
            "target_user": target_user,
            "forged": True,
            "tgt_validity": "10 years (default krbtgt lifetime)",
            "forged_ticket_hash": forged_tgt,
            "sid": f"S-1-5-21-{secrets.token_hex(8)}",
            "groups": ["Domain Admins", "Enterprise Admins", "Domain Users"],
            "detection_evasion": "Valid PAC, no anomalous timestamps, appears legitimate",
        }


class DCShadowSimulator:
    """Simulate DCShadow attack."""

    def __init__(self, domain: str):
        self.domain = domain

    def push_malicious_object(self, target_dc: str, object_type: str = "user") -> dict:
        """Simulate pushing a malicious object via rogue DC."""
        malicious_changes = {
            "user": {
                "action": "Create user 'svc_backup' with Domain Admin rights",
                "attributes": {"memberOf": "CN=Domain Admins", "userAccountControl": "NORMAL_ACCOUNT"},
            },
            "computer": {
                "action": "Register rogue computer object for replication hijack",
                "attributes": {"servicePrincipalName": "GC/rogue.corp.local"},
            },
            "acl": {
                "action": "Modify nTSecurityDescriptor to grant DCSync rights",
                "attributes": {"allowedRights": ["DS-Replication-Get-Changes", "DS-Replication-Get-Changes-All"]},
            },
        }

        change = malicious_changes.get(object_type, malicious_changes["acl"])

        return {
            "attack": "DCShadow",
            "domain": self.domain,
            "target_dc": target_dc,
            "action": change["action"],
            "attributes": change["attributes"],
            "replication_triggered": True,
            "detection": "Event ID 4742 (computer object change), SPN modification alerts",
        }


class DCSyncSimulator:
    """Simulate DCSync hash extraction."""

    def __init__(self, domain: str):
        self.domain = domain
        self.user_database = {
            "admin": {"ntlm": "e52cac67419a9a224a3b108f3fa6cb6d", "history": 3},
            "krbtgt": {"ntlm": "a9a836a8c8e2b58a9e8b91c3d4e5f6a7", "history": 1},
            "svc_sql": {"ntlm": "88c4d2a56b3a3e9e8b8a91c3d4e5f6a7", "history": 0},
        }

    def request_replication(self, target_user: str) -> dict:
        """Simulate requesting replication data for a user."""
        if target_user not in self.user_database:
            return {"error": f"User {target_user} not found in domain database"}

        user_data = self.user_database[target_user]
        repl_token = secrets.token_hex(16)

        return {
            "attack": "DCSync",
            "domain": self.domain,
            "target_user": target_user,
            "replication_rights": "DS-Replication-Get-Changes-All",
            "ntlm_hash": user_data["ntlm"],
            "password_history_count": user_data["history"],
            "replication_token": repl_token,
            "event_log_evidence": "Event ID 4662 (DRSUAPI operation)",
        }


def main():
    parser = argparse.ArgumentParser(description="AD Attack Simulation (Educational)")
    parser.add_argument("--domain", default="corp.local", help="Target domain")
    parser.add_argument("--users", help="Comma-separated user list")
    parser.add_argument("--krbtgt-hash", help="Golden Ticket: krbtgt NTLM hash")
    parser.add_argument("--target-dc", default="DC01.corp.local", help="DCShadow: target DC FQDN")
    parser.add_argument("--user", help="Golden Ticket/DCSync: target username")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--kerberoasting", action="store_true", help="Simulate Kerberoasting")
    group.add_argument("--asrep-roast", action="store_true", help="Simulate AS-REP Roasting")
    group.add_argument("--golden-ticket", action="store_true", help="Simulate Golden Ticket")
    group.add_argument("--dcshadow", action="store_true", help="Simulate DCShadow")
    group.add_argument("--dcsync", action="store_true", help="Simulate DCSync")

    args = parser.parse_args()

    if args.kerberoasting:
        sim = KerberoastSimulator(args.domain)
        users = (args.users or "svc_sql,svc_ftp,svc_web").split(",")
        result = sim.roast_all(users)
    elif args.asrep_roast:
        sim = ASREPRoastSimulator(args.domain)
        users = (args.users or "user1,user2,user3").split(",")
        result = sim.roast_all(users)
    elif args.golden_ticket:
        sim = GoldenTicketSimulator(args.domain)
        result = sim.forge_ticket(args.user or "admin", args.krbtgt_hash)
    elif args.dcshadow:
        sim = DCShadowSimulator(args.domain)
        result = sim.push_malicious_object(args.target_dc)
    elif args.dcsync:
        sim = DCSyncSimulator(args.domain)
        result = sim.request_replication(args.user or "admin")
    else:
        parser.print_help()
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f"  {result.get('attack', 'AD Attack')} — Simulation")
    print(f"{'='*50}")
    print(json.dumps(result, indent=2))
    print(f"\n  [!] Educational simulation — no live exploitation performed")


if __name__ == "__main__":
    main()
