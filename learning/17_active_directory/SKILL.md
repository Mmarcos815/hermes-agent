---
name: active-directory-tier6
version: 1.0.0
description: Tier 6 Active Directory Attacks — Kerberoasting, AS-REP Roasting, Golden Ticket, DCShadow, DCSync simulation. For authorized red team operations and CTF labs only.
tags: [active-directory, kerberos, kerberoasting, golden-ticket, dcsync, dcshadow, red-team]
category: red-teaming
---

# Tier 6: Active Directory Attacks

## Overview

Active Directory attack simulation covering the five pillars of AD credential abuse and domain dominance:

1. **Kerberoasting** — Offline cracking of service account passwords via TGS tickets
2. **AS-REP Roasting** — Extract crackable hashes from accounts with "Do not require Kerberos preauthentication"
3. **Golden Ticket** — Forge TGT tickets using the krbtgt hash for persistent domain access
4. **DCShadow** — Spoof a DC to push malicious changes to AD replication
5. **DCSync** — Simulate DC replication to extract password hashes without admin rights

> **Scope:** Authorized red team operations, lab environments, and CTF challenges only. All techniques require explicit written permission against target systems.

---

## Attack Chain

```
[Initial Access] → [Kerberoasting] → [Credential Theft] → [Lateral Movement]
                                                                    ↓
[Persistence] ← [Golden Ticket] ← [DCSync/Hash Dump] ← [Privilege Escalation]
```

---

## Key Concepts

### Kerberoasting
- Request TGS tickets for SPN-registered service accounts
- Tickets are encrypted with the service account's NTLM hash
- Offline brute-force reveals weak service account passwords
- **Mitigation:** Managed Service Accounts (MSA/gMSA), strong passwords (>25 chars), AES-only enforcement

### AS-REP Roasting
- Target accounts with `DONT_REQUIRE_PREAUTH` flag set
- Request AS-REP without authenticating — contains encrypted timestamp
- Crack offline to reveal account password hash
- **Mitigation:** Audit and remove `DONT_REQUIRE_PREAUTH`, enable AES, monitor AS-REP requests

### Golden Ticket
- Requires the krbtgt account's NTLM hash (obtained via DCSync or Mimikatz)
- Forge any TGT for any user — including non-existent accounts
- Valid for 10 years by default (krbtgt password rarely changed)
- **Mitigation:** Rotate krbtgt password twice, monitor TGT lifetime anomalies, enable PAC validation

### DCShadow
- Register a rogue "DC" via SPN manipulation + AD replication rights
- Push malicious changes (SID History, ACL backdoors) that replicate to real DCs
- No traditional DC required — user-mode attack
- **Mitigation:** Monitor SPN changes, restrict `Replicating Directory Changes`, audit replication traffic

### DCSync
- Use `DS-Replication-Get-Changes` rights to request replication data
- Extract NTLM hashes of any domain user without code execution on DC
- Requires `Domain Admin`, `Enterprise Admin`, or delegated replication rights
- **Mitigation:** Audit replication permissions, monitor DRSUAPI traffic, enable PAC validation

---

## Tool Reference

```bash
# Kerberoasting simulation
python ad_attack.py --kerberoasting --domain corp.local --users svc_sql,svc_ftp

# AS-REP Roasting simulation
python ad_attack.py --asrep-roast --domain corp.local --users user1,user2

# Golden Ticket forging (educational)
python ad_attack.py --golden-ticket --domain corp.local --user admin --krbtgt-hash <hash>

# DCShadow simulation
python ad_attack.py --dcshadow --domain corp.local --target-dc DC01.corp.local

# DCSync simulation
python ad_attack.py --dcsync --domain corp.local --user admin
```

---

## Safety & Ethics

- **Authorized testing only** — Written permission required against any target
- **Simulation mode** — This skill simulates attacks for learning; does not exploit live systems
- **Responsible disclosure** — Report findings through proper channels
- **Legal compliance** — Unauthorized access to AD environments violates CFAA, Computer Misuse Act, and similar laws
