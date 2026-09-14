---
name: three-ds
description: "3D Secure 2.2.0 authentication protocol simulator — models ACS, DS, 3DS Server entities with frictionless/challenge flows, risk scoring, and CAVV generation."
version: 1.0.0
author: Rigoberto Gomez, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [financial, 3ds, emvco, authentication, payments, fintech, card-processing]
    related_skills: [iso8583]
---

# 3D Secure 2.2.0 Authentication Protocol Simulator

A pure-Python (stdlib only) implementation of the EMVCo 3D Secure Protocol v2.2.0. Models the full 3DS ecosystem: 3DS Requestor/Merchant, 3DS Server (3DSS), Directory Server (DS), and Access Control Server (ACS). Simulates the complete authentication choreography — device profiling, AReq/ARes risk evaluation, frictionless vs. challenge flow decisions, CReq/CRes OTP verification, and CAVV minting. Includes a risk-scoring engine with configurable rules for high-risk MCCs, amount thresholds, and known-card profiles.

## When to Use

- Understanding how 3D Secure 2.x authentication works end-to-end
- Testing payment flows that require 3DS challenge/frictionless decisions
- Training on EMVCo 3DS protocol message formats and state transitions
- Simulating issuer ACS behavior for payment integration testing

Don't use for:
- Real payment authentication (no real HMAC keys, no real cardholder data, no network I/O)
- Production 3DS Server deployment (simulation only)

## Prerequisites

- Python 3.8+ (uses `json`, `hashlib`, `hmac`, `uuid`, `time` — all stdlib)
- No external dependencies
- The script `scripts/three_ds_simulator.py` in this skill directory

## How to Run

```bash
cp ~/.hermes/skills/financial/three-ds/scripts/three_ds_simulator.py ./
python three_ds_simulator.py
```

This runs the built-in test suite that:
1. Tests frictionless flow ($25.00 grocery purchase → TransStatus Y, ECI 05)
2. Tests challenge flow ($750.00 crypto purchase → TransStatus C, challenge required)
3. Tests challenge completion (valid OTP → TransStatus Y, ECI 05)

## Quick Reference

| Entity | Class | Role |
|--------|-------|------|
| ACS | `AccessControlServer` | Risk scoring, challenge decision, CAVV minting |
| DS | `DirectoryServer` | Routes AReq between 3DSS and ACS |
| 3DSS | `ThreeDSServer` | Initiates authentication, formats AReq |

| Action | Code |
|--------|------|
| Initiate auth | `three_ds_server.initiate_authentication(merchant_id, pan, amount_cents, currency, mcc)` |
| Evaluate risk | `acs.evaluate_areq(areq_dict)` |
| Process challenge | `acs.process_creq(creq_dict)` |
| Generate CAVV | `acs._generate_cavv(pan, amount, trans_id)` |

## Procedure

### 1. Initialize the 3DS Ecosystem

```python
from three_ds_simulator import AccessControlServer, DirectoryServer, ThreeDSServer

acs = AccessControlServer()
ds = DirectoryServer(acs)
three_ds_server = ThreeDSServer(ds)
```

### 2. Initiate Authentication (Frictionless)

```python
ares = three_ds_server.initiate_authentication(
    merchant_id="MERCH-001",
    pan="4111111111111111",
    amount_cents=2500,       # $25.00
    currency="840",          # USD
    mcc="5411"               # Grocery (low risk)
)
# ares["transStatus"] == "Y" (Frictionless Approved)
# ares["eci"] == "05" (Fully Authenticated)
# ares["authenticationValue"] == CAVV hex
```

### 3. Initiate Authentication (Challenge Required)

```python
ares = three_ds_server.initiate_authentication(
    merchant_id="MERCH-001",
    pan="5500000000000004",
    amount_cents=75000,      # $750.00
    currency="840",
    mcc="6051"               # Crypto (high risk)
)
# ares["transStatus"] == "C" (Challenge Required)
# ares["acsURL"] == challenge endpoint
# ares["challengeWindowSize"] == "05" (Full Screen)
```

### 4. Complete Challenge (OTP Verification)

```python
creq = {
    "threeDSServerTransID": ares["threeDSServerTransID"],
    "acsTransID": ares["acsTransID"],
    "acctNumber": "5500000000000004",
    "challengeDataEntry": "123456",  # OTP from cardholder
    "messageType": "CReq",
    "messageVersion": "2.2.0"
}
cres = acs.process_creq(creq)
# cres["transStatus"] == "Y" (Challenge Passed)
# cres["eci"] == "05"
```

### 5. Risk Scoring Rules

The ACS evaluates risk based on:

| Rule | Trigger | Result |
|------|---------|--------|
| High-risk card | PAN in known_cards with risk_level=HIGH | Challenge |
| High amount | purchaseAmount >= 50000 ($500.00) | Challenge |
| High-risk MCC | mcc in [7995, 6051, 6012] | Challenge |
| Default | None of the above | Frictionless |

### 6. Message Flow

```
3DS Requestor → 3DSS → DS → ACS (AReq → ARes)
                  ↓
          Frictionless (Y) → Done
          Challenge (C) → CReq → CRes → Done
```

### 7. Key Fields

| Field | Description |
|-------|-------------|
| threeDSServerTransID | Unique transaction ID (UUID) |
| acsTransID | ACS-generated transaction ID |
| transStatus | Y=Success, C=Challenge, N=Failed |
| eci | Electronic Commerce Indicator (05=Full, 07=None) |
| authenticationValue | CAVV (Cardholder Auth Verification Value) |
| challengeWindowSize | 01-05 (05 = full screen) |

## Pitfalls

- **Simulation only.** No real HMAC keys, no real cardholder data, no network I/O.
- **Hardcoded test cards.** Only 4111111111111111 and 5500000000000004 are known to the ACS.
- **Static OTP secrets.** OTP values are hardcoded (774920, 123456). Not for production.
- **ACS secret key is hardcoded.** `ACS_SECRET_KEY_2026` is a placeholder. Replace with real key for production.
- **No real CAVV.** CAVV is HMAC-SHA256 truncated to 20 bytes, but uses a static key.
- **No 3DS Method.** Device fingerprinting step is not implemented (assumes browser channel).
- **No RReq/RRes.** Results Request/Response flow (post-auth) is not implemented.
- **EMVCo compliance.** This is a learning tool, not a certified EMVCo implementation.

## Verification

- Frictionless flow returns TransStatus "Y" and ECI "05"
- Challenge flow returns TransStatus "C" with acsURL
- Valid OTP returns TransStatus "Y" and ECI "05"
- Invalid OTP returns TransStatus "N" and ECI "07"
- All test cases in `run_3ds_suite()` pass with assertions
- CAVV is 40 hex chars (20 bytes HMAC-SHA256 truncated)
