# Tier 6 Active Directory — Progress Tracking

## Status: COMPLETED

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `SKILL.md` | ~85 | Skill definition with attack chain, concepts, safety |
| `ad_attack.py` | ~205 | AD attack simulation (5 attacks) |
| `PROGRESS.md` | This file | Progress tracking |

## Skills Covered

- [x] **Kerberoasting** — TGS ticket request + RC4 offline cracking concept
- [x] **AS-REP Roasting** — Preauth bypass + encrypted timestamp extraction
- [x] **Golden Ticket** — TGT forgery with krbtgt hash simulation
- [x] **DCShadow** — Rogue DC registration + malicious object push
- [x] **DCSync** — Replication rights abuse + hash extraction

## Verification

```bash
cd "C:/Users/mobil/orca/projects/my 1st/learning/17_active_directory"
python ad_attack.py --kerberoasting --users svc_sql,svc_ftp
python ad_attack.py --asrep-roast --users user1
python ad_attack.py --golden-ticket --user admin
python ad_attack.py --dcshadow --target-dc DC01.corp.local
python ad_attack.py --dcsync --user admin
```

## Notes

- All attack classes use simulation only (no live network/auth operations)
- Educational focus: demonstrates attack mechanics for red team training
- Mutually exclusive CLI flags prevent accidental multi-attack runs
- Consistent with Tier 5 skill patterns (SKILL.md frontmatter + Python tool)
