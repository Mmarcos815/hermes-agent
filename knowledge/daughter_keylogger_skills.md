# ============================================================================
# BIONIC DAUGHTER v1 — KEYLOGGER SKILLS (EDUCATIONAL / AUTHORIZED TESTING)
# ============================================================================
# DOC_AUTH: Daughter
# PURPOSE: Understand keyloggers — how they work, types, detection, prevention —
#          for authorized security testing and defensive understanding.
# CONTEXT: Educational understanding and authorized testing only.
#          Never deploy keyloggers on systems without explicit written authorization.
#          Never use keyloggers for unauthorized surveillance, credential theft, or
#          any purpose other than authorized security testing or education.
# ============================================================================

## ========================================================================
## PART 1 — WHAT A KEYLOGGER IS
## ========================================================================

## DEFINITION

A keylogger (keystroke logger) is a tool — software or hardware — that records
keystrokes made on a keyboard (or virtual keyboard) and captures the input data.
The recorded data can include passwords, messages, search queries, financial
information, and anything else typed on the device.

## THE CORE CONCEPT

The keylogger sits BETWEEN the keyboard input and the application that receives it.
Every keystroke passes through the keylogger, which records it before (or instead of)
passing it to the legitimate destination.

```
KEYBOARD → [KEYLOGGER intercepts] → APPLICATION (receives the keystroke, doesn't know it was logged)
                                    ↓
                              [KEYLOGGER stores/transmits the recorded keystrokes]
```

The application functions normally (the user sees their input appearing on screen).
The keylogger operates silently in the background. The user typically doesn't know
their keystrokes are being recorded.

## ========================================================================
## PART 2 — TYPES OF KEYLOGGERS
## ========================================================================

## SOFTWARE KEYLOGGERS (MOST COMMON)

Software keyloggers are programs installed on the device's operating system. They
capture keystrokes through various OS-level mechanisms.

### API-LEVEL KEYLOGGERS (USER-MODE)
- Hook into keyboard input APIs at the application level
- Windows: SetWindowsHookEx with WH_KEYBOARD or WH_KEYBOARD_LL — registers a hook
  procedure that receives keyboard events
- The hook receives keystroke information (virtual key code, scan code, modifiers,
  whether the key is up or down) before the application processes it
- Can be installed by any user with appropriate privileges (no kernel access needed)
- Relatively easy to detect (running processes, known hook patterns)

### DRMIVER-LEVEL KEYLOGGERS (KERNEL-MODE)
- Operate at the kernel level, intercepting input before it reaches user mode
- Replace or modify the keyboard driver, or install a filter driver in the keyboard
  stack
- Can capture input before user-mode security tools see it
- Harder to detect (running in kernel space, hidden from user-mode tools)
- Require kernel-level access ( administrator/root, or a signed kernel driver)
- More powerful but also more likely to be detected by security tools (kernel driver
  installation is itself suspicious)

### DLL INJECTION KEYLOGGERS
- Inject a DLL into the target application's process
- The DLL hooks keyboard input within that process
- Can be targeted (specific application) or global (inject into multiple processes)
- Technique: CreateRemoteThread + LoadLibrary, or other injection methods

### BROWSER-BASED KEYLOGGERS
- JavaScript running in the browser captures keystrokes in web forms
- Intercepts input before it's encrypted by HTTPS (captures plaintext)
- Can be delivered through malicious scripts, compromised websites, malicious browser
  extensions
- Limited to browser context (doesn't capture keystrokes in other applications)
- Modern browsers have defenses (content security policy, script blockers, extension
  permissions)

### REMOTE ACCESS TROJAN (RAT) KEYLOGGERS
- RAT malware that includes keylogging as one feature
- Can also capture screenshots, webcam, microphone, file system access, remote control
- Typically installed through phishing, downloaded files, or other malware delivery
- Combines multiple surveillance capabilities into one tool

### AI-ENHANCED KEYLOGGERS (RECENT)
- Use machine learning to predict user activity patterns
- Can make detection harder (behavioral adaptation)
- Can prioritize certain keystrokes (focus on password fields, financial inputs)
- Recent development (2021-2025 trend)

## HARDWARE KEYLOGGERS

Hardware keyloggers are physical devices that sit between the keyboard and the computer.

### PHYSICAL HARDWARE KEYLOGGERS
- Device that connects between the keyboard cable and the computer's USB/PS/2 port
- Records keystrokes to internal memory (or transmits them wirelessly)
- Disguised as a normal USB adapter or connector
- Operates at the hardware level — OS doesn't see it (it's not a software process)
- Not detectable by software (antivirus can't see a physical device between keyboard
  and computer)
- Requires physical access to install (attacker must physically access the target computer)
- Requires physical access to retrieve (or wireless transmission)

### INTERNAL HARDWARE KEYLOGGERS
- Installed inside the keyboard itself (modified keyboard with built-in keylogger)
- Or inside the computer (motherboard-level interception)
- Even harder to detect (no external device to find)
- Requires physical access to install (and to retrieve data, unless wireless)

## OTHER TYPES

### VIRTUAL KEYBOARD LOGGERS
- Track input on virtual keyboards (on-screen keyboards, touchscreen keyboards)
- Different mechanism than physical keyboard hooking (mouse clicks, touch events)
- Relevant for touchscreen devices, accessibility tools

### VIDEO-BASED KEYLOGGERS (CONCEPTUAL)
- Camera pointed at keyboard + screen — video analysis can determine which keys are
  pressed by tracking finger positions and correlating with screen content
- Not a common attack method (requires camera access, visual analysis), but conceptually
  possible
- Countered by: not having a camera with view of keyboard, using privacy screens,
  password managers (auto-fill bypasses typing)

### ACOUSTIC KEYLOGGERS (RESEARCH CONCEPT)
- Microphone picks up the sound of keystrokes — different keys make slightly different
  sounds (acoustic signatures)
- Machine learning can potentially decode keystrokes from audio
- Research concept, not widely deployed in practice (requires good audio, ML analysis)
- Countered by: no microphone with audible keyboard, white noise, quiet keyboards

## ========================================================================
## PART 3 — HOW KEYLOGGERS ARE DEPLOYED (THE INFILTRATION METHODS)
## ========================================================================

## HOW THEY GET ON THE SYSTEM

1. **Malicious downloads** — user downloads and runs a malicious file (disguised as
   legitimate software, cracked software, game cheat, etc.) that installs the keylogger

2. **Phishing emails** — email with malicious attachment (document with macro, executable
   disguised as PDF/invoice) or link to malicious website that delivers the keylogger

3. **Compromised websites** — drive-by download (visiting a compromised website that
   exploits a browser vulnerability to install malware)

4. **Bundled software** — keylogger hidden in "free" software, especially from untrusted
   sources (cracked software, pirated content, unofficial downloads)

5. **Physical access** — someone with physical access to the device installs the keylogger
   (hardware keylogger between keyboard and computer, software keylogger installed directly)

6. **Remote access** — attacker with remote access to the device (compromised RDP, remote
   support tools, backdoors) installs the keylogger remotely

7. **Supply chain** — compromised software update that delivers keylogger (rare but
   possible — trusted software that's been compromised)

8. **Social engineering** — tricking the user into installing the keylogger (disguised as
   "security tool," "parental control," "employee monitoring" — legitimate uses of
   keylogging that the attacker co-opts)

## ========================================================================
## PART 4 — DETECTION (HOW TO FIND A KEYLOGGER)
## ========================================================================

## DETECTION METHODS (FOR THE DEFENSIVE SIDE)

### PROCESS-LEVEL DETECTION
- Check running processes (Task Manager, process explorer tools)
- Look for unknown/unfamiliar processes, especially those with suspicious names or
  hiding (some keyloggers hide their process name or appear as legitimate processes)
- Check startup items (keyloggers often install themselves to start automatically)
- Look for processes with hooked functions (specialized tools can detect API hooking)

### NETWORK-LEVEL DETECTION
- Monitor network traffic for suspicious outbound connections (keyloggers transmit
  recorded keystrokes to a remote server — look for unexpected connections, especially
  to unknown IPs or domains, especially on unusual ports)
- Look for periodic small data transmissions (keystroke data sent in chunks)
- Encrypted traffic to unknown destinations (keylogger C2 servers often use encryption)

### BEHAVIORAL DETECTION
- EDR (Endpoint Detection and Response) tools monitor for suspicious behavior patterns:
  - API hooking (SetWindowsHookEx, keyboard-related APIs being hooked)
  - Unusual driver installation (kernel-mode keyloggers install drivers)
  - Processes injecting into other processes (DLL injection for keylogging)
  - Unexpected background activity (keylogger running silently)
- Modern security tools (EDR, antivirus with behavioral analysis) can detect many
  keyloggers through behavior, not just signatures

### PHYSICAL INSPECTION
- Check USB ports for unfamiliar devices (hardware keylogers are physical devices)
- Check keyboard connections (hardware keylogger between keyboard and computer)
- In high-security environments, regular physical inspection of all connected devices

### SPECIALIZED TOOLS
- Anti-keylogger tools (specific detection for keylogging behavior)
- Rootkit detectors (for kernel-mode keyloggers)
- Hook detection tools (detect API hooking)
- Network analysis tools (detect keylogger C2 traffic)

## LIMITATIONS OF DETECTION
- Sophisticated keyloggers use evasion techniques (hide process, disguise as legitimate
  process, use kernel mode to avoid user-mode detection, encrypt C2 traffic, use
  legitimate-looking network behavior)
- Custom/keylogger variants may not be in antivirus signature databases (zero-day
  keyloggers = no signature yet)
- Kernel-mode keyloggers are harder to detect (they operate below user-mode detection)
- Some keyloggers are designed specifically to evade common detection methods

## ========================================================================
## PART 5 — PREVENTION (HOW TO PROTECT AGAINST KEYLOGGERS)
## ========================================================================

## DEFENSIVE MEASURES

### 1. ANTIVIRUS / EDR (ENDPOINT PROTECTION)
- Use reputable antivirus / EDR solutions (Sophos, CrowdStrike, SentinelOne, Microsoft
  Defender, etc.)
- Keep updated (signature databases, behavioral detection engines)
- Enable real-time protection (scan files as they're accessed, monitor behavior)
- EDR with behavioral analysis is especially important (detects unknown keyloggers through
  behavior, not just signatures)

### 2. MULTI-FACTOR AUTHENTICATION (MFA) — THE MOST EFFECTIVE COUNTERMEASURE
- MFA significantly reduces the impact of keylogger attacks
- Even if the keylogger captures the password, the attacker can't authenticate without
  the second factor (TOTP code, hardware token, biometric, push notification)
- The keylogger captures the password, but the second factor is (typically) not capturable
  by a keylogger (TOTP changes every 30 seconds, hardware tokens generate codes locally,
  push notifications require user approval on a separate device)
- EXCEPTION: some sophisticated keyloggers can capture TOTP if they also capture the
  screen (screenshot at the moment the code is entered) or intercept the TOTP input
  (still just keystrokes). But basic keyloggers can't bypass MFA.

### 3. PASSWORD MANAGERS — BYPASS THE KEYBOARD
- Password managers auto-fill passwords — no typing required
- If you're not typing the password, a keylogger can't capture it (basic keylogger)
- Password manager autofill typically uses browser APIs / OS accessibility features,
  not keyboard input
- Counters basic keyloggers (API-level, driver-level might still capture the input before
  it reaches the browser, but password managers reduce the attack surface significantly)
- Use a reputable password manager (Bitwarden, 1Password, KeePass, etc.) with a strong
  master password and MFA on the password manager itself

### 4. VIRTUAL KEYBOARDS (PARTIAL DEFENSE)
- On-screen keyboard (Windows: Win+R, type "osk" — On-Screen Keyboard)
- Input via mouse clicks, not keyboard — basic keyloggers that hook keyboard APIs don't
  capture mouse clicks on the virtual keyboard
- SOME keyloggers can still capture virtual keyboard input (screen capture + analysis,
  or hooking at a level that captures all input regardless of source)
- Not a complete defense, but adds a layer

### 5. BIOMETRIC AUTHENTICATION
- Fingerprint, face, iris — no typing required
- Counters basic keyloggers (no password to capture)
- But: biometric data, once compromised, can't be changed (you can't change your fingerprint)
- Use biometrics as ONE factor (not the only factor) — combine with something else (MFA)

### 6. SYSTEM HARDENING
- Keep systems updated (patch vulnerabilities that keyloggers exploit to install)
- Limit user privileges (standard user account for daily use, not administrator —
  makes it harder for keyloggers to install at system level)
- Application control / allowlisting (only allow approved software to run — prevents
  unauthorized keyloggers from executing)
- Disable unnecessary services and features (reduce attack surface)

### 7. BEHAVIORAL AWARENESS
- Be cautious about downloads (only from trusted sources)
- Be cautious about email attachments and links (phishing is a common delivery method)
- Be cautious about physical access to your devices (hardware keyloggers require physical
  access — be aware of your devices in public/shared spaces)
- Be cautious about "free" software from unofficial sources (cracked software, pirated
  content — common vector for malware including keyloggers)

### 8. NETWORK MONITORING
- Monitor for unusual outbound connections (keyloggers need to transmit data)
- Use firewalls (block unnecessary outbound connections, alert on suspicious ones)
- DNS filtering (block known malicious domains)
- Network segmentation (limit what a compromised device can reach)

### 9. PHYSICAL SECURITY
- Physical inspection of devices (especially in shared/public spaces)
- Be aware of USB devices (unknown USB devices plugged into your computer — could be
  hardware keyloggers, could be malicious USB devices that install software)
- Lock devices when not in use (prevent physical access)

## ========================================================================
## PART 6 — LEGITIMATE USES OF KEYLOGGING (AUTHORIZED CONTEXTS)
## ========================================================================

Keylogging technology itself is neutral. Legitimate uses exist:

1. **IT troubleshooting** — IT departments may use keyloggers (with disclosure/
   consent) to diagnose keyboard issues, troubleshoot input problems, understand
   what a user is experiencing.

2. **Parental monitoring** — parents may monitor children's online activity (with
   disclosure to the child, age-appropriate). Controversial but legal in many
   jurisdictions for minor children.

3. **Employee monitoring** — organizations may monitor employee activity on company
   devices (with disclosure/policy, not covert). Legal requirements vary by jurisdiction
   — many places require disclosure, some require consent.

4. **Authorized security testing** — penetration testers / red teamers may use keyloggers
   in authorized engagements (with written authorization from the target organization,
   within scope, safe handling of any captured data). The keylogger tests whether the
   organization's defenses detect it, how quickly, and whether the security team responds.

5. **Research/education** — cybersecurity students may study keyloggers in controlled
   lab environments (authorized, isolated, educational purpose). Understanding how
   keyloggers work is part of understanding the threat and how to defend against it.

## THE LINE BETWEEN LEGITIMATE AND ILLEGAL

| Legitimate | Illegal |
|------------|---------|
| Authorized by the target (written consent) | No authorization |
| Disclosure to the person being monitored (typically) | Covert surveillance without knowledge |
| Limited scope (specific purpose, specific device) | Broad surveillance (all devices, all users, no limits) |
| Data handled responsibly (secure storage, limited access, proper disposal) | Data misused (stolen credentials, identity theft, sale of data) |
| Within legal boundaries (respecting privacy laws) | Violating privacy laws, computer crime laws |

The daughter's keylogger understanding is for authorized security testing and defensive
understanding. Never deploy a keylogger without authorization.

## ========================================================================
## PART 7 — THE DAUGHTER'S KEYLOGGER CAPABILITY (CONCEPTUAL)

The daughter understands keyloggers at a technical level:
- How they work (API hooks, driver-level, DLL injection, browser-based, hardware)
- How they're deployed (phishing, downloads, physical access, remote access)
- How to detect them (process analysis, network monitoring, EDR, physical inspection)
- How to prevent them (MFA, password managers, antivirus/EDR, system hardening,
  behavioral awareness, physical security)
- How to use them in authorized testing (authorized deployment, detection testing,
  educational purpose, safe data handling)

The daughter does NOT deploy keyloggers without authorization. That would be illegal
and unethical. The daughter's keylogger knowledge is for defense and authorized testing.

## ========================================================================
## DOC_END
## ========================================================================
