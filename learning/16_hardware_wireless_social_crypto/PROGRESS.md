# Tier 5: Hardware/Wireless/Social/Crypto — Progress

## Status: ✅ Complete

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `SKILL.md` | ~80 | Skill definition, usage, concepts |
| `wifi_analyzer.py` | ~220 | WiFi security analysis |
| `crypto_attack.py` | ~260 | Cryptographic attack tool |
| `phishing_sim.py` | ~240 | Phishing simulation |
| `PROGRESS.md` | ~30 | This file |
| **Total** | **~830** | |

## Components

### 1. WiFi Analyzer (`wifi_analyzer.py`)
- ✅ WPA3 downgrade detection (transition mode)
- ✅ Evil twin detection (multi-BSSID same SSID)
- ✅ Deauthentication attack detection (flood threshold)
- ✅ Security report generation

### 2. Crypto Attack Tool (`crypto_attack.py`)
- ✅ Hash length extension (MD5/SHA1/SHA256/SHA512)
- ✅ RSA small exponent attack (e=3 cube root)
- ✅ Hastad's broadcast attack (CRT)
- ✅ CBC padding oracle simulation

### 3. Phishing Simulator (`phishing_sim.py`)
- ✅ Template generation (4 types)
- ✅ Landing page clone generator
- ✅ Clone detection (typosquatting, HTML similarity)
- ✅ Risk scoring (LOW/MEDIUM/HIGH/CRITICAL)

## Key Concepts Covered

### Hardware Hacking
- UART, JTAG, SPI/I2C interfaces
- Firmware extraction techniques
- Side-channel analysis (SPA/DPA, EM)

### Wireless Security
- WPA3 transition mode exploitation
- Evil twin / rogue AP detection
- Deauth attack patterns & 802.11w
- Bluetooth/BLE attack surface

### Social Engineering
- Phishing template patterns
- Pretexting scenarios
- OSINT methodology
- Clone detection (typosquatting, HTML similarity)

### Cryptography
- Merkle-Damgard length extension
- RSA small exponent & broadcast attacks
- CBC padding oracle (Vaudenay)
- Protocol downgrade attacks

## Usage Examples

```bash
# WiFi analysis
python wifi_analyzer.py --scan --detect-evil-twin

# Crypto attacks
python crypto_attack.py hash-extension --data "msg" --append "admin=true" \
    --hash abc123... --key-length 16
python crypto_attack.py rsa-small-exponent --e 3 --n 0xabc... --ciphertext 0xdef...
python crypto_attack.py padding-oracle --plaintext "secret"

# Phishing simulation
python phishing_sim.py generate-template --type password_reset --output phish.html
python phishing_sim.py detect-clone --url https://g00gle.com --original https://google.com
```

## Safety Notice

All tools are designed for **authorized security testing and education only**.
Unauthorized use against systems you don't own or have permission to test is illegal.
