---
name: iso8583
description: "ISO 8583 financial transaction message engine — pack/unpack wire format, simulate payment switch authorization, parse MTI/bitmaps/data elements."
version: 1.0.0
author: Rigoberto Gomez, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [financial, iso8583, payments, parser, fintech, card-processing]
    related_skills: [cloud-red-team-playbook]
---

# ISO 8583 Financial Transaction Message Engine

A pure-Python (stdlib only) implementation of the ISO 8583:1987/1993/2003 financial transaction message standard. Packs and unpacks wire-format messages, parses MTI (Message Type Indicator), primary/secondary bitmaps, and 20+ data elements (PAN, amounts, timestamps, auth codes, etc.). Includes a `PaymentSwitchSimulator` that processes authorization (0100→0110) and financial (0200→0210) transactions against a mock account ledger with balance, PIN, and status checks.

## When to Use

- Building or testing payment-processing systems that speak ISO 8583
- Parsing captured ISO 8583 wire messages (e.g., from PCAP logs or payment middleware)
- Simulating authorization/financial transactions for testing or training
- Understanding how card payment networks encode transaction data

Don't use for:
- Real production payment processing (no PCI-DSS compliance, no encryption, no real network I/O)
- Handling live cardholder data (uses mock/test accounts only)

## Prerequisites

- Python 3.8+ (uses `struct`, `binascii`, `json` — all stdlib)
- No external dependencies
- The script `scripts/iso8583_engine.py` in this skill directory

## How to Run

```bash
cp ~/.hermes/skills/financial/iso8583/scripts/iso8583_engine.py ./
python iso8583_engine.py
```

This runs the built-in demo that:
1. Builds an authorization request (0100) with PAN, amount, timestamp, STAN, terminal ID
2. Packs it into wire format and prints hex
3. Simulates payment-switch processing (balance check, auth approval)
4. Unpacks and displays the response (0110) with response code, auth code, updated balance

## Quick Reference

| Action | Code |
|--------|------|
| Create message | `msg = ISO8583Message(mti="0100")` |
| Set field | `msg.set_field(2, "4111111111111111")` |
| Get field | `msg.get_field(2)` |
| Pack to bytes | `raw = msg.pack()` |
| Unpack from bytes | `msg = ISO8583Message.unpack(raw)` |
| To dict | `msg.to_dict()` |
| Simulate switch | `switch = PaymentSwitchSimulator(); resp = switch.process(raw)` |

## Procedure

### 1. Build a Message

```python
from iso8583_engine import ISO8583Message

msg = ISO8583Message(mti="0100")  # Authorization Request
msg.set_field(2, "4111111111111111")   # PAN
msg.set_field(3, "000000")             # Processing Code (Purchase)
msg.set_field(4, "000000015000")       # Amount: $150.00 (cents)
msg.set_field(7, "0828063000")         # Transmission Date/Time
msg.set_field(11, "123456")            # STAN
msg.set_field(18, "5411")              # MCC (Grocery)
msg.set_field(41, "TERM0001")          # Terminal ID
msg.set_field(49, "840")               # Currency (USD)
```

### 2. Pack to Wire Format

```python
raw_bytes = msg.pack()
print(raw_bytes.hex())  # Hex-encoded wire message
```

### 3. Parse a Wire Message

```python
parsed = ISO8583Message.unpack(raw_bytes)
print(parsed.mti)          # "0100"
print(parsed.get_field(2)) # PAN
print(parsed.to_dict())    # Full structured dict
```

### 4. Simulate Payment Processing

```python
from iso8583_engine import PaymentSwitchSimulator

switch = PaymentSwitchSimulator()
response_bytes = switch.process(raw_bytes)
response = ISO8583Message.unpack(response_bytes)
print(response.get_field(39))  # "00" = Approved, "51" = Insufficient Funds
```

### 5. Supported Data Elements

| Field | Type | Max | Description |
|-------|------|-----|-------------|
| 1 | b | 8 | Secondary Bitmap |
| 2 | LLVAR | 19 | PAN |
| 3 | n | 6 | Processing Code |
| 4 | n | 12 | Amount (cents) |
| 7 | n | 10 | Transmission Date/Time |
| 11 | n | 6 | STAN |
| 12 | n | 6 | Local Time |
| 13 | n | 4 | Local Date |
| 14 | n | 4 | Expiration (YYMM) |
| 18 | n | 4 | MCC |
| 22 | n | 3 | POS Entry Mode |
| 32 | LLVAR | 11 | Acquirer ID |
| 37 | an | 12 | RRN |
| 38 | an | 6 | Auth ID Response |
| 39 | an | 2 | Response Code |
| 41 | ans | 8 | Terminal ID |
| 42 | ans | 15 | Merchant ID |
| 43 | ans | 40 | Merchant Name/Location |
| 48 | LLLVAR | 999 | Private Data |
| 49 | n | 3 | Currency Code |
| 54 | LLLVAR | 120 | Additional Amounts |
| 102 | LLVAR | 28 | Source Account |
| 103 | LLVAR | 28 | Destination Account |

### 6. MTI Transitions

| Request | Response | Meaning |
|---------|----------|---------|
| 0100 | 0110 | Authorization |
| 0200 | 0210 | Financial Transaction |
| 0400 | 0410 | Reversal |
| 0420 | 0430 | Reversal Advice |

### 7. Response Codes

| Code | Meaning |
|------|---------|
| 00 | Approved |
| 05 | Do Not Honor |
| 14 | Invalid Card Number |
| 51 | Insufficient Funds |

## Pitfalls

- **No encryption.** Wire messages are plaintext ASCII/hex. Never use with real cardholder data.
- **No network I/O.** The engine only packs/unpacks bytes. You must handle socket communication separately.
- **Mock accounts only.** `PaymentSwitchSimulator` uses hardcoded test accounts (4111..., 5500...). Not for production.
- **Fixed-length fields.** `n`, `an`, `ans` types are zero-padded or space-padded to max length. Truncation may occur if values exceed max.
- **LLVAR/LLLVAR length encoding.** Length headers are ASCII digits (2 or 3 chars), not binary.
- **Secondary bitmap.** Automatically enabled when any field > 64 is set, or field 1 is present.
- **No Luhn validation.** PANs are not validated for checksum correctness.
- **No MAC/encryption fields.** Fields 64/128 (MAC) are defined but not computed/verified.

## Verification

- Packed message starts with 4-byte MTI, followed by 8 or 16 bitmap bytes
- Bitmap first bit (bit 1) is set when secondary bitmap is present
- Response MTI = Request MTI + 10 (e.g., 0100 → 0110)
- `to_dict()` returns all set fields with names from DATA_ELEMENTS
- Demo output shows hex wire format, parsed response, and JSON field dump
