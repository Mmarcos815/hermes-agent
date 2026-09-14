# Module 17: Mobile Device Security

## Objectives
- Understand mobile attack surfaces (Android and iOS)
- Perform mobile application security testing
- Exploit mobile-specific vulnerabilities
- Understand mobile device management (MDM) and containerization
- Defend mobile devices and applications

---

## 17.1 Mobile Security Fundamentals

Mobile devices are ubiquitous and contain enormous amounts of sensitive data — emails, messages, photos, credentials, location history, and access to corporate systems. They're also harder to secure than traditional computers due to the diversity of devices, the prevalence of third-party apps, and the physical nature of the device.

### Mobile Threat Landscape

| Threat Category | Description | Examples |
|----------------|-------------|----------|
| **Malicious apps** | Apps that steal data, spy, or defraud | Fake apps, trojanized apps, spyware |
| **Network attacks** | Intercepting or modifying mobile traffic | Public Wi-Fi MitM, evil twin, SSL stripping |
| **Physical access** | Gaining access to a lost/stolen/unlocked device | data extraction, credential harvesting |
| **Phishing/smishing** | SMS or app-based phishing | Fake login pages, credential harvesting via SMS |
| **App vulnerabilities** | Vulnerabilities in legitimate apps | Insecure storage, weak SSL, intent injection |
| **OS vulnerabilities** | Exploits targeting mobile OS or components | Kernel exploits, sandbox escapes, privilege escalation |
| **Supply chain** | Compromised SDKs, libraries, or developer tools | Malicious SDKs, compromised build pipelines |

### Android vs. iOS Security Model

| Aspect | Android | iOS |
|--------|---------|-----|
| **App sandboxing** | Each app runs in its own sandbox | Each app runs in its own sandbox |
| **App distribution** | Google Play + sideloading (APKs from anywhere) | App Store primarily; sideloading limited ( enterprise certs, jailbreak, EU DMA changes) |
| **Permission model** | Runtime permissions (user grants/revokes) | Runtime permissions (user grants/revokes) |
| **Root/jailbreak** | Relatively accessible (magisk, etc.) | Harder, but possible (checkra1n, etc. for older devices) |
| **Encryption** | File-based encryption (modern Android) | Full-disk encryption / file-based encryption (iOS) |
| **Security updates** | Fragmented — depends on manufacturer/ carrier | More centralized — Apple pushes updates to all supported devices |
| **App review** | Google Play Protect + manual review (less strict than Apple) | Apple App Store review (more strict, but not perfect) |

---

## 17.2 Mobile Application Security Testing

### Static Analysis

Analyzing the app without running it — examining the binary, resources, and code.

#### Android Static Analysis

```bash
# Obtain the APK (from device, app store, or test build)
# Analyze the APK

# Use apktool to decompile
apktool d app.apk -o app_decompiled

# Examine the manifest (AndroidManifest.xml)
cat app_decompiled/AndroidManifest.xml | grep -i "permission\|activity\|service\|receiver\|provider"

# Look for:
# - Exported components (activities, services, broadcast receivers, content providers)
# - Permissions requested and used
# - Debuggable flag (android:debuggable="true" — huge security risk)
# - Backup allowed (android:allowBackup="true" — can extract app data)
# - Uses-permission for sensitive permissions

# Inspect the decompiled code (smali or Java if decompiled with jadx)
jadx-gui app.apk   # Or jadx -d app_decompiled app.apk

# Search for sensitive data in the code
grep -r "password\|secret\|key\|token\|api_key\|Authorization" app_decompiled/

# Check for hard-coded credentials, API keys, encryption keys
# Check for insecure cryptographic implementations
# Check for WebView vulnerabilities (JavaScript enabled, loadURL from untrusted source)
# Check for intent vulnerabilities (exported components, intent filtering)
```

**Key Android manifest checks:**
- `android:exported="true"` on activities, services, providers — accessible by other apps
- `android:debuggable="true"` — app can be debugged, data extracted
- `android:allowBackup="true"` — data can be backed up and extracted
- Permissions requested — does the app ask for more than it needs?
- Content providers — are they accessible? Do they properly validate inputs?

#### iOS Static Analysis

```bash
# Obtain the IPA or app binary
# Analyze

# Use objection (runtime exploration, also does some static)
objection explore com.example.app

# Use MobSF (Mobile Security Framework) — automated static and dynamic analysis
# MobSF can analyze both Android and iOS apps

# For iOS specifically:
# Check Info.plist for permissions, URL schemes, etc.
# Check for hardcoded secrets in the binary
strings app_binary | grep -i "password\|secret\|key\|token\|api"

# Check for SSL pinning bypass needs
# Check for jailbreak detection
# Check for debugging detection
```

### Dynamic Analysis

Analyzing the app while it's running — monitoring behavior, network traffic, file system changes, etc.

#### Android Dynamic Analysis

```bash
# Connect device via USB (or use emulator)
adb devices

# Monitor app behavior
adb logcat | grep -i "<package_name>"

# Use Frida for runtime instrumentation
frida -U -l script.js com.example.app

# Common Frida scripts:
# - Bypass SSL pinning
# - Bypass root/jailbreak detection
# - Hook cryptographic functions
# - Intercept and modify function calls

# Use MobSF for dynamic analysis (connected to the device)
# Use mitmproxy or Burp Suite to intercept traffic (requires installing CA cert on device/emulator)

# Check file system for sensitive data
adb shell
cd /data/data/com.example.app/
ls -la
cat shared_prefs/*.xml    # SharedPreferences — often contain tokens, settings
cat databases/*.db         # SQLite databases — may contain sensitive data
ls -la files/             # App's file storage

# Check for Copilot/Clipboard data leakage
adb shell "dumpsys clipboard"
```

#### iOS Dynamic Analysis

```bash
# Use Frida with iOS device (requires jailbreak or using a simulator)
frida -U -l script.js com.example.app

# Use objection
objection explore com.example.app
# Inside objection:
# - ios sslpinning disable
# - ios checkra1n disable
# - env
# -Crashlog
# - ls
# - filesystem

# Use Burp Suite or mitmproxy with iOS (requires installing custom CA — harder on iOS without jailbreak)
# Use Charles Proxy (paid, but popular for iOS traffic interception)

# Check app's App Container
# /var/mobile/Containers/Data/Application/<UUID>/
# Look for:
# - Plist files (settings, tokens)
# - Databases (SQLite)
# - Logs
# - Cached data
```

### Network Traffic Analysis

```bash
# Intercept mobile app traffic with Burp Suite or mitmproxy
# 1. Install custom CA certificate on device/emulator
#    - Android: Settings > Security > Install from storage (user CA store)
#    - iOS: Settings > General > Profile > Install (then enable in Settings > General > About > Certificate Trust Settings)
# 2. Configure device to use proxy (Wi-Fi settings > proxy)
# 3. Intercept and analyze traffic

# Common mobile network issues:
# - SSL/TLS misconfigurations (weak ciphers, missing cert validation)
# - SSL pinning (app pins to specific certificate — bypass with Frida/objection)
# - Cleartext traffic (HTTP instead of HTTPS — common in older apps)
# - Sensitive data in URLs (tokens, credentials in query parameters)
# - Improper certificate validation (accepting any certificate)

# Test for:
# - Missing certificate validation
# - Weak cipher suites
# - Session management issues
# - Sensitive data exposure in traffic
# - API vulnerabilities (same as web apps — IDOR, injection, etc.)
```

---

## 17.3 Mobile Vulnerability Categories

### OWASP Mobile Top 10 (2016)

| Rank | Vulnerability | Description |
|------|--------------|-------------|
| **M1** | Improper Credential Usage | Hardcoded credentials, improper token handling |
| **M2** | Inadequate Supply Chain Security | Malicious SDKs, compromised libraries |
| **M3** | Insecure Authentication/Authorization | Weak auth, missing auth, improper session management |
| **M4** | Insufficient Cryptography | Weak encryption, hardcoded keys, improper use of crypto |
| **M5** | Insecure Communication | Cleartext traffic, weak TLS, SSL pinning bypassable |
| **M6** | Inadequate Privacy Controls | Excessive data collection, insecure data storage, lack of user consent |
| **M7** | Insufficient Binary Protections | Lack of obfuscation, easy to reverse engineer, no anti-tampering |
| **M8** | Security Misconfiguration | Debuggable builds, default configs, overly permissive settings |
| **M9** | Side-Channel Data Leakage | Clipboard, logs, screenshots, analytics leaks |
| **M10** | Weak Server Side Controls | Same as web app vulnerabilities — API security, injection, etc. |

### Common Mobile Vulnerabilities

```bash
# 1. Insecure data storage
# Check SharedPreferences (Android), plist files (iOS), databases, files
# Look for: passwords, tokens, credit card numbers, PII, API keys

# 2. Weak server-side controls (same as web apps)
# Test APIs for IDOR, injection, broken auth, etc.

# 3. SSL pinning bypass
# Use Frida scripts to bypass common SSL pinning implementations
# objection ios sslpinning disable / android sslpinning disable

# 4. Intent/URL scheme abuse (Android)
# If an activity is exported and accepts intents, it may be exploitable
# adb shell am start -n com.example.app/.Activity -d "scheme://command"
# Check for intent injection — can you make the app do something unintended?

# 5. Deep link / universal link abuse (iOS/Android)
# Apps register URL schemes — if not properly validated, can be abused
# Test with different inputs, check for command injection, data leakage

# 6. Side-channel data leakage
# - Clipboard: sensitive data copied to clipboard may be accessible to other apps
# - Screenshots: app may display sensitive data in screenshots (Android: windowIsSecure flag)
# - Logs: app may log sensitive data to logcat/console
# - Analytics: sensitive data sent to analytics services
# - Keyboard cache: typed data may be cached by the keyboard app

# 7. Root/jailbreak detection bypass
# Many apps check for root/jailbreak and refuse to run
# Bypass with Frida scripts that hook the detection functions and return false
# objection ios jailbreak disable / android root disable

# 8. Component hijacking
# - Android: exported components can be started by other apps
# - iOS: URL schemes, app extensions, WidgetKit, etc. can be abused
```

---

## 17.4 Mobile Device Management (MDM) and Containerization

### MDM (Mobile Device Management)
MDM allows organizations to manage and secure mobile devices — enforce policies, remotely wipe, enforce encryption, etc.

**MDM attack considerations:**
- MDM profiles can be installed by users (if not restricted by Apple/Google)
- MDM can enforce device compliance — but bypass is possible with root/jailbreak and tools
- MDM data is typically in a container separate from personal data
- MDM can track device location, install apps, enforce passwords, etc.

### Mobile Application Management (MAM) / Containerization
MAM manages specific apps rather than the whole device. Common in BYOD (Bring Your Own Device) scenarios.

- App-level policies (copy/paste restrictions, data sharing restrictions)
- Encrypted containers for corporate data
- Remote wipe of corporate data only (not personal data)

**Red team perspective:** MDM/MAM can be a target — if you can bypass the container, you can access corporate data. But these are also a defense — they limit the impact of a compromised personal device.

---

## 17.5 Mobile Forensics Basics

Understanding what data is on a mobile device and how to extract it is important for both red teamers (understanding what an attacker can get) and forensics (investigating mobile incidents).

### Data Sources on Mobile Devices

| Source | What's There |
|--------|-------------|
| **File system** | Apps, data, media, configs, logs |
| **Databases** | SQLite databases with app data, messages, contacts, etc. |
| **Keychain/Keystore** | Stored credentials, keys, tokens (iOS Keychain, Android Keystore) |
| **Cloud backups** | iCloud backup, Google Drive backup — may contain device data |
| **Memory (RAM)** | Runtime data, decryption keys, session tokens (requires physical access and specialized tools) |
| **Logs** | System logs, app logs — may contain sensitive info |

### Extraction Methods

| Method | Description | Feasibility |
|--------|-------------|-------------|
| **Logical extraction** | Via backup APIs, ADB, iTunes backup | Easy to moderate; may not get everything |
| **File system extraction** | Full file system access via ADB, jailbreak, exploit | Moderate; requires some access |
| **Physical extraction** | Bit-by-bit copy of storage | Hard; requires hardware tools or exploits |
| **Cloud extraction** | Access iCloud/Google account to get backup data | Depends on cloud account security |
| **Manual extraction** | Looking at the device screen, taking photos, copying data | Only gets what's visible on screen |

**Note:** Mobile forensics is a specialized field. The above is a high-level overview for red teamers to understand what data is potentially accessible.

---

## 17.6 Lab: Mobile Device Security

### Setup
- Android emulator (Android Studio AVD, Genymotion) or a rooted test device
- iOS simulator (macOS only) or a jailbroken test device (optional)
- A test mobile app with intentional vulnerabilities (e.g., OWASP MSTG test apps, InsecureBankv2, DIVA, etc.)
- Burp Suite or mitmproxy for traffic interception
- Frida and objection for runtime analysis
- apktool, jadx for static analysis

### Tasks

**Task 1: Static Analysis of an Android App**
1. Obtain a test APK (OWASP MSTG InsecureBankv2, DIVA, or similar)
2. Decompile with apktool:
   ```bash
   apktool d insecureapp.apk -o insecure_decompiled
   ```
3. Examine AndroidManifest.xml:
   - List all components (activities, services, receivers, providers)
   - Identify which are exported
   - Check for debuggable flag, backup flag
   - List requested permissions
4. Decompile with jadx and browse the code:
   - Search for hardcoded strings (passwords, API keys, tokens)
   - Look for cryptographic implementations
   - Check for WebView usage
   - Check for intent handling
5. Document all findings — what security issues did you find in the static analysis?

**Task 2: Dynamic Analysis with Runtime Instrumentation**
1. Install the test app on an emulator or rooted device
2. Install Frida server on the device:
   ```bash
   adb push frida-server /data/local/tmp/
   adb shell chmod 755 /data/local/tmp/frida-server
   adb shell /data/local/tmp/frida-server &
   ```
3. Use Frida to:
   - Bypass SSL pinning (if the app uses it)
   - Bypass root detection (if the app checks for root)
   - Hook interesting functions (login, crypto, network calls)
4. Use objection to explore the app:
   ```bash
   objection explore com.insecure.app
   # - env, ls, filesystem, etc.
   # - android intent resolve, android intent send
   # - android sslpinning disable
   ```
5. Document what you found through dynamic analysis — what did Frida/objection reveal that static analysis didn't?

**Task 3: Network Traffic Interception**
1. Set up Burp Suite or mitmproxy as a proxy
2. Install the proxy's CA certificate on the emulator/device
3. Configure the emulator/device to use the proxy
4. Use the app and observe traffic:
   - What endpoints does it call?
   - What data is sent and received?
   - Is traffic encrypted (HTTPS) or cleartext (HTTP)?
   - Are there any obvious security issues in the API calls?
5. Test API endpoints for vulnerabilities (IDOR, injection, broken auth, etc.)
6. Document the traffic analysis and any vulnerabilities found

**Task 4: Insecure Data Storage Analysis**
1. After using the app, examine its data on the device:
   ```bash
   adb shell
   cd /data/data/<package_name>/
   ls -la
   ls -la shared_prefs/
   cat shared_prefs/*.xml
   ls -la databases/
   sqlite3 databases/<database>.db ".dump"
   ls -la files/
   cat files/*
   ```
2. Check for:
   - Passwords, tokens, or keys stored in SharedPreferences or plist files
   - Sensitive data in SQLite databases
   - Sensitive files in the app's file storage
   - Logs that contain sensitive data (adb logcat | grep <package>)
3. Document what sensitive data was stored insecurely and where

**Task 5: Component Exploitation (Android)**
1. Identify exported activities, services, or content providers from the manifest
2. Test exported activities:
   ```bash
   adb shell am start -n com.example.app/.ExportedActivity
   adb shell am start -n com.example.app/.ExportedActivity -d "scheme://data"
   ```
3. Test exported content providers:
   ```bash
   adb shell content query --uri content://com.example.app.provider/...
   ```
4. Test for intent injection or privilege escalation through exported components
5. Document which components are exploitable and what they allow

**Task 6: iOS Analysis (If iOS Environment Available)**
1. On iOS simulator or jailbroken device, install the test app
2. Use objection or Frida to:
   - Bypass SSL pinning
   - Bypass jailbreak detection
   - Explore the app's data and environment
3. Check the app's container for sensitive data
4. Examine network traffic (using Charles Proxy or similar)
5. Document findings — compare with Android findings (what's similar, what's different?)

**Task 7: Mobile Defense Assessment**
1. Review the vulnerabilities found in the test app
2. For each vulnerability, recommend a fix:
   - How should the data be stored securely?
   - How should the network communication be protected?
   - How should the components be protected?
   - What runtime checks should the app perform?
   - How should the app handle authentication and sessions?
3. Prioritize recommendations by risk and implementation effort
4. Document the defense recommendations

---

## 17.7 Expected Outcomes

By the end of this module, you should be able to:
- Perform static analysis of Android and iOS applications
- Perform dynamic analysis using Frida and objection
- Intercept and analyze mobile app network traffic
- Identify common mobile vulnerabilities (insecure storage, weak auth, SSL issues, component hijacking)
- Understand mobile forensics data sources
- Understand MDM/MAM security implications
- Recommend mobile security improvements

---

## 17.8 Assessment Criteria

| Criteria | Points | Description |
|----------|--------|-------------|
| Static analysis | 10 | Conducts thorough static analysis of test app, documents findings |
| Dynamic analysis (Frida/objection) | 10 | Uses runtime instrumentation to bypass protections and analyze behavior |
| Network analysis | 10 | Intercepts and analyzes app traffic, identifies API issues |
| Data storage analysis | 10 | Identifies insecure data storage in the app |
| Component testing | 5 | Tests exported components for exploitation |
| iOS analysis (if available) | 5 | Performs iOS-specific analysis (or documents iOS concepts) |
| Defense recommendations | 10 | Specific, actionable mobile security recommendations |
| Report quality | 10 | Professional documentation of methodology, findings, recommendations |
| **Total** | **70** | |

**Pass threshold:** 49/70 (70%)

### Report Requirements (4–5 pages)
1. Target app overview — platform, version, purpose, permissions
2. Static analysis findings — manifest issues, hardcoded secrets, code analysis
3. Dynamic analysis findings — SSL pinning bypass, root detection bypass, runtime behavior
4. Network analysis — endpoints, traffic issues, API vulnerabilities
5. Data storage findings — where sensitive data was found, how it was stored
6. Component exploitation — exported components, what they allow, exploitation results
7. Defense recommendations — specific fixes for each vulnerability, prioritized
