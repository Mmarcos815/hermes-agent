#!/usr/bin/env python3
"""
kerberoast_sim.py — Kerberoasting attack simulation against the AD lab.

Technique: Request a TGS for an SPN-bearing account, then crack offline.
MITRE: T1558.003 (Steal or Forge Kerberos Tickets: Kerberoasting)

This is a pure simulation. No real Kerberos traffic is generated.
Replace `request_tgs()` with impacket's GetUserTickets() for a live run.
"""

from __future__ import annotations
import hashlib
import hmac

# ── Lab user database (mirrors setup.ps1) ──────────────────────────────────
USERS: dict[str, dict] = {
    "svc_sql": {
        "password": "P@ssw0rd1!",
        "spns": ["MSSQLSvc/dc01.lab.local:1433"],
        "encryption": "rc4-hmac",          # weak = crackable fast
    },
    "svc_backup": {
        "password": "P@ssw0rd1!",
        "spns": ["bkp/dc01.lab.local"],
        "encryption": "rc4-hmac",
    },
    "jsmith": {
        "password": "UserPass1!",
        "spns": [],                          # no SPN = not kerberoastable
        "encryption": "aes256",
    },
}


def derive_ntlm(password: str) -> bytes:
    """NTLM hash (MD4 of UTF-16LE password) — used by RC4 Kerberos.

    MD4 is deprecated in modern Python/OpenSSL builds. We fall back to
    SHA-256 (usedforsecurity=False) so the simulation still works.
    The exact hash is irrelevant to the educational point here.
    """
    try:
        return hashlib.new("md4", password.encode("utf-16le")).digest()
    except ValueError:
        return hashlib.new("sha256", password.encode("utf-16le"), usedforsecurity=False).digest()


def simulate_tgs(password: str, spn: str, salt: str = "LAB.LOCALsvc_sql") -> bytes:
    """
    Simulate the AS-REP encrypted portion (RC4-HMAC).
    Real Kerberos: ticket is encrypted with the account's NTLM hash.
    We replicate that relationship so a dictionary attack succeeds.
    """
    ntlm = derive_ntlm(password)
    # RC4-HMAC: HMAC-MD5 over the SPN/salt using NTLM as key
    return hmac.new(ntlm, (salt + spn).encode(), hashlib.md5).digest()


def kerberoast(users: dict[str, dict], wordlist: list[str]) -> dict[str, str | None]:
    """Attempt offline crack of each SPN-bearing account."""
    cracked: dict[str, str | None] = {}

    for acct, info in users.items():
        if not info["spns"]:
            cracked[acct] = None            # not kerberoastable
            continue

        spn = info["spns"][0]
        ticket = simulate_tgs(info["password"], spn)

        cracked[acct] = None
        for word in wordlist:
            candidate = simulate_tgs(word, spn)
            if hmac.compare_digest(ticket, candidate):
                cracked[acct] = word
                break

    return cracked


def main() -> None:
    print("=" * 60)
    print("  Kerberoasting Simulation — Educational")
    print("=" * 60)

    print("\n[*] Identifying SPN-bearing accounts...")
    targets = {u: i for u, i in USERS.items() if i["spns"]}
    for acct, info in targets.items():
        print(f"      {acct}: {info['spns']}")

    # Simulated wordlist (in real life: rockyou.txt, etc.)
    wordlist = ["Password1", "Summer2024!", "P@ssw0rd1!", "Admin123", "Welcome1"]

    print(f"\n[*] Requesting TGS tickets for {len(targets)} account(s)...")
    print(f"[*] Running dictionary attack against {len(wordlist)} candidates...\n")

    results = kerberoast(USERS, wordlist)

    for acct, pw in results.items():
        if pw is None and not USERS[acct]["spns"]:
            print(f"  [skip] {acct} — no SPN, not kerberoastable")
        elif pw:
            print(f"  [CRACKED] {acct} : password = {pw}")
            print(f"            → Recommendation: rotate to gMSA, remove SPN")
        else:
            print(f"  [RESISTANT] {acct} — not in wordlist (use stronger password)")


if __name__ == "__main__":
    main()
