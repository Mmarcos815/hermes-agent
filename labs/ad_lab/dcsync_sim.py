#!/usr/bin/env python3
"""
dcsync_sim.py — DCSync attack simulation against the AD lab.

Technique: Abuse DS-Replication-Get-Changes to pull password data from the DC.
MITRE: T1003.006 (OS Credential Dumping: DCSync)

This is a simulation. No real replication traffic is sent.
Replace `dcsync()` with impacket's secretsdump for a live lab run.
"""

from __future__ import annotations
import hashlib


def derive_ntlm(password: str) -> str:
    """NTLM hash with fallback for builds that lack MD4."""
    try:
        return hashlib.new("md4", password.encode("utf-16le")).hexdigest()
    except ValueError:
        return hashlib.new("sha256", password.encode("utf-16le"),
                          usedforsecurity=False).hexdigest()


# ── Lab credential store (simulates the AD DS ntds.dit / replication) ──────
# Using derive_ntlm so the simulation works regardless of hash backend.
REPLICATION_DB: dict[str, dict] = {
    "Administrator": {
        "ntlm": derive_ntlm("LabPass123!"),
        "pwd_last_set": "2026-01-15",
        "admin_count": 1,
    },
    "krbtgt": {
        "ntlm": derive_ntlm("KrbtgtP@ss!"),
        "pwd_last_set": "2025-06-01",
        "admin_count": 1,
    },
    "svc_sql": {
        "ntlm": derive_ntlm("P@ssw0rd1!"),
        "pwd_last_set": "2026-02-01",
        "admin_count": 0,
    },
    "jsmith": {
        "ntlm": derive_ntlm("UserPass1!"),
        "pwd_last_set": "2026-03-10",
        "admin_count": 0,
    },
}


# ── Permission check (simulated) ───────────────────────────────────────────
DCSYNC_PRIVILEGES = {"Domain Admins", "Enterprise Admins", "Administrators"}


def can_dsync(user_groups: set[str]) -> bool:
    """DCSync requires DS-Replication-Get-Changes on the domain object."""
    return bool(user_groups & DCSYNC_PRIVILEGES)


# ── Simulated DCSync ───────────────────────────────────────────────────────
def dcsync(user_groups: set[str]) -> dict[str, dict] | None:
    """Return replication data if caller has the required privilege."""
    if not can_dsync(user_groups):
        return None
    return REPLICATION_DB


def attempt_crack(ntlm_hash: str, wordlist: list[str]) -> str | None:
    for word in wordlist:
        if derive_ntlm(word) == ntlm_hash:
            return word
    return None


def main() -> None:
    print("=" * 60)
    print("  DCSync Attack Simulation — Educational")
    print("=" * 60)

    # Scenario 1: attacker with Domain Admin-equivalent rights
    attacker_groups = {"Domain Admins"}
    print(f"\n[*] Attacker group membership: {attacker_groups}")
    print(f"[*] DCSync privilege check:   {can_dsync(attacker_groups)}")

    data = dcsync(attacker_groups)
    if not data:
        print("[!] Access denied — cannot perform DCSync.")
        return

    print(f"\n[*] Retrieved {len(data)} credential record(s):\n")
    for acct, info in data.items():
        print(f"      {acct:<20} NTLM={info['ntlm']}  last_set={info['pwd_last_set']}")

    # Scenario 2: offline cracking of pulled hashes
    print("\n[*] Offline cracking with wordlist...")
    wordlist = ["LabPass123!", "P@ssw0rd1!", "UserPass1!", "Admin123"]
    for acct, info in data.items():
        pw = attempt_crack(info["ntlm"], wordlist)
        status = f"CRACKED -> {pw}" if pw else "not in wordlist"
        print(f"      {acct:<20} {status}")

    # Scenario 3: low-privilege user attempt
    print(f"\n[*] Scenario 2: low-privilege user tries DCSync...")
    lowpriv = {"IT_Admins"}
    print(f"    Groups: {lowpriv}")
    print(f"    Privilege check: {can_dsync(lowpriv)}")
    if dcsync(lowpriv) is None:
        print("    DENIED — DCSync requires Domain/Enterprise Admin.")

    print("\n[*] Mitigations:")
    print("      - Monitor DS-Replication-Get-Changes calls (Event ID 4662)")
    print("      - Rotate krbtgt twice to invalidate golden tickets")
    print("      - Tier admin accounts — no credential overlap between tiers")


if __name__ == "__main__":
    main()
