---
name: hardware-wireless-social-crypto
description: Tier 5 Hardware Hacking + Wireless Security + Social Engineering + Cryptography skill set. Use when analyzing WiFi security, cryptographic attacks, phishing simulations, or hardware/wireless attack vectors.
---

# Tier 5: Hardware Hacking + Wireless Security + Social Engineering + Cryptography

## Overview

This skill covers four advanced security domains:

1. **Hardware Hacking** — UART, JTAG, SPI/I2C, firmware extraction, side-channel analysis
2. **Wireless Security** — WiFi (WPA2/3), Bluetooth, RF/sub-GHz, Zigbee, SDR
3. **Social Engineering** — Phishing, pretexting, OSINT, physical security
4. **Cryptography** — Hash extension, RSA attacks, padding oracle, protocol analysis

## Tools

| Tool | Purpose |
|------|---------|
| `wifi_analyzer.py` | WiFi security analysis (WPA3 downgrade, evil twin, deauth detection) |
| `crypto_attack.py` | Cryptographic attacks (hash extension, RSA small exponent, padding oracle) |
| `phishing_sim.py` | Phishing simulation (template generation, landing page clone detector) |

## Usage

```bash
# WiFi analysis
python wifi_analyzer.py --scan --interface wlan0mon
python wifi_analyzer.py --detect-evil-twin --bssid AA:BB:CC:DD:EE:FF
python wifi_analyzer.py --detect-deauth --pcap capture.pcap

# Crypto attacks
python crypto_attack.py --hash-extension --data "original" --append "malicious" --hash <sha256> --key-length 16
python crypto_attack.py --rsa-small-exponent --e 3 --n <n> --ciphertext <c>
python crypto_attack.py --padding-oracle --url https://target.com/decrypt --block-size 16

# Phishing simulation
python phishing_sim.py --generate-template --target "corp-login" --output phish.html
python phishing_sim.py --detect-clone --url https://suspicious-site.com --original https://legit.com
```

## Key Concepts

### Hardware Hacking
- **UART**: Serial debug interface — identify TX/RX/GND, baud rate detection
- **JTAG**: Boundary scan — TDI/TDO/TMS/TCK/TRST pinout identification
- **SPI/I2C**: Flash memory extraction, EEPROM dumping
- **Side-Channel**: Power analysis (SPA/DPA), timing attacks, EM emissions

### Wireless Security
- **WPA3 Downgrade**: Transition mode exploitation, PMF bypass
- **Evil Twin**: Rogue AP detection via BSSID/SSID/channel analysis
- **Deauth Attack**: Management frame analysis, 802.11w protection
- **Bluetooth**: BLE sniffing, pairing bypass, GATT enumeration

### Social Engineering
- **Phishing**: Template generation, payload delivery, credential harvesting
- **Pretexting**: Scenario building, identity fabrication
- **OSINT**: Reconnaissance, data aggregation, attack surface mapping

### Cryptography
- **Hash Extension**: Length extension attacks on MD5/SHA1/SHA256
- **RSA Attacks**: Small exponent, Coppersman's, Wiener's attack
- **Padding Oracle**: CBC padding oracle, Vaudenay's attack
- **Protocol Analysis**: Downgrade attacks, cipher suite manipulation

## Safety & Ethics

All tools are for **authorized testing and educational purposes only**. Unauthorized access to computer systems is illegal. Always obtain proper authorization before testing.
