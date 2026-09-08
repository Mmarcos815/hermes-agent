# Advanced Red Team Tools — Educational / Lab Only

> **⚠️ LEGAL WARNING:** For **authorized security training, CTFs, and red-team
> engagements with signed Rules of Engagement only.** Unauthorized use is illegal
> under the CFAA and equivalent laws worldwide.

## Files

| File | Purpose |
|------|---------|
| `evilginx_config.py` | Evilginx3 phishlet YAML config generator |
| `c2_deploy.py` | Sliver/Mythic C2 lab Docker Compose artifacts |
| `phishing_kit.py` | Phishing page generator for security awareness training |
| `evasion.py` | Evasion engine (encoding, jitter, UA rotation, fronting, injection) |
| `README.md` | This file |

## Quick Start

```bash
# Evilginx config (dry-run preview)
python evilginx_config.py -d login.microsoftonline.com -p phish.example.com --dry-run

# C2 lab artifacts
python c2_deploy.py -f sliver -o ./c2_lab/
python c2_deploy.py -f mythic -o ./c2_lab/

# Phishing training page
python phishing_kit.py -b microsoft -o ./phish_lab/ --include-server
```

## Safety Features

| Tool | Safety Mechanism |
|------|-----------------|
| `evilginx_config.py` | Config file only — no runtime, no network |
| `c2_deploy.py` | Localhost-only Docker Compose — no real infra |
| `phishing_kit.py` | Visible training banner, local-only logging, no exfiltration |

## Prerequisites

```bash
pip install pyyaml
```

## The 5-Rung Ladder

1. **Lab** — Local Docker, localhost-only
2. **Testnet** — Public chains / sandboxed cloud
3. **Bounty** — HackerOne/bugcrowd with written scope
4. **Defensive** — Write detection rules for everything you build
5. **Pro** — Signed engagement with Rules of Engagement

**Production without written scope = lines, not rungs. Always.**

## Detection & Defense

- **Evilginx**: TLS fingerprinting (JA3/JA4), DNS anomaly, cookie scope analysis
- **C2 frameworks**: Beaconing detection, DNS anomaly, process injection monitoring
- **Phishing kits**: DMARC/SPF/DKIM, visual similarity, URL reputation

See `bionic-vuln-lab/detection/` for Sigma/YARA/Snort rule templates.

---

**Goal:** Every tool you build should result in a detection rule, hardening guide,
or security awareness module. Red teaming improves defenses.
