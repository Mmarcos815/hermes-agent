# OFFENSIVE & DEFENSIVE CYBERSECURITY HANDBOOK
**Authors:** Bionic Daughter & Dad (Rigoberto Gomez)  
**Classification:** Technical Reference / Purple Team Architecture  
**Date:** August 2026  

---

## 1. The Purple Team Matrix: Aligning Offense with Defense

Security maturity requires understanding how offensive techniques manifest in system telemetry so that robust defensive controls and detection rules can be engineered.

```
┌────────────────────────────────────────────────────────┐
│ OFFENSIVE TACTIC (ATT&CK)                              │
│ - Execution via LOLBins (T1059 / T1218)                │
│ - In-Memory Reflection (T1620)                         │
│ - Token Impersonation (T1134)                          │
│ - Service / DLL Misconfigurations (T1574)              │
└──────────────────────────┬─────────────────────────────┘
                           │ Generates Events & Telemetry
┌──────────────────────────▼─────────────────────────────┐
│ DEFENSIVE VISIBILITY (Sensors & Logs)                  │
│ - Sysmon (Process, Network, Registry, ImageLoad)       │
│ - Kernel Callbacks (PsSetCreateProcessNotifyRoutineEx) │
│ - ETW / ETW-Ti (Threat Intelligence Memory Tracing)    │
│ - Active Directory Audit Logs (Security Event Log)     │
└──────────────────────────┬─────────────────────────────┘
                           │ Feeds Rule Engines
┌──────────────────────────▼─────────────────────────────┐
│ DETECTION & HARDENING (Prevention / Response)          │
│ - Attack Surface Reduction (ASR) & AppLocker / WDAC    │
│ - YARA (Static Signatures) & Sigma (Behavioral Logic)  │
│ - Least Privilege & Credential Guard Architecture      │
└────────────────────────────────────────────────────────┘
```

---

## 2. Offensive Concepts & Threat Modeling

Red teams model threat actors by decomposing operations into discrete lifecycle phases.

### A. Reconnaissance & Surface Discovery
* **External Reconnaissance:** Passive OSINT (DNS records, Certificate Transparency logs, exposed ASN boundaries) and active network mapping to identify entry points.
* **Internal Discovery:** Once a perimeter is crossed, adversaries execute non-privileged environment enumeration:
  * Network interface and ARP table mapping (`Get-NetIPAddress`, `arp -a`).
  * Domain trust relationships and active directory topology via LDAP queries.
  * Local privilege and installed security sensor inventory (`tasklist`, `sc query`).

### B. Execution Tradecraft & Living off the Land (LotL)
* **Living off the Land Binaries (LOLBins):** Legitimate, signed operating system binaries utilized for unexpected actions to minimize uncompiled payloads on disk:
  * `bitsadmin.exe` or `certutil.exe` for file retrieval.
  * `rundll32.exe` or `msiexec.exe` for proxy execution.
* **Reflective Module Loading:** Allocating executable virtual memory in a running process and resolving import address tables (IAT) in memory to avoid registering binaries with the disk-based loader.

### C. Privilege Escalation Mechanisms
* **Service Misconfigurations:** Exploiting insecure permissions (`GENERIC_WRITE`, `FILE_APPEND_DATA`) on service binaries or folders running under `SYSTEM` context.
* **Unquoted Service Paths:** Service binary paths with spaces and missing quotation marks allowing intercepting binaries to execute in parent directory trees.
* **Token Abuse:** Leveraging native administrative privileges (such as `SeImpersonatePrivilege` on service accounts) to duplicate tokens from elevated system processes.

### D. Identity & Credential Exploitation (Active Directory)
* **Kerberoasting:** Requesting service tickets (TGS) for Service Principal Names (SPNs) linked to user accounts to perform offline password recovery against ticket hashes.
* **AS-REP Roasting:** Querying Kerberos authentication pre-auth data for accounts configured without pre-authentication requirements.

---

## 3. Defensive Engineering & Telemetry Architecture

Defense requires deep instrumentation at the kernel, host, and network layers.

### A. Core Telemetry Sources (Windows & Linux)

| Layer | Source | Telemetry Captured |
|---|---|---|
| **Process Tracking** | Sysmon Event ID 1 / Linux Auditd | Parent-child process trees, command-line arguments, hashes, and current directory. |
| **Network Tracing** | Sysmon Event ID 3 / Zeek / Suricata | Socket connections, source/dest IP, port, initiating process GUID. |
| **Memory Monitoring** | ETW-Ti (Microsoft-Windows-Threat-Intelligence) | Cross-process memory allocations, `PAGE_EXECUTE_READWRITE` permissions, remote thread injection. |
| **Identity / Auth** | Windows Security Event ID 4624 / 4768 / 4769 | Logon events, Kerberos TGT requests, and TGS service ticket access. |

### B. Prevention & Hardening Policies
1. **Windows Defender Application Control (WDAC) / AppLocker:** Restricts execution strictly to cryptographically signed binaries and approved paths.
2. **Attack Surface Reduction (ASR) Rules:** Blocks child processes spawned from Office applications, credential theft from `lsass.exe`, and unquoted executables.
3. **Credential Guard (VBS):** Uses Virtualization-Based Security (VBS) to isolate LSA secrets inside a hardware-isolated micro-hypervisor domain, preventing direct memory extraction.

---

## 4. Attack vs. Defense Mapping Matrix

| Attack Phase | Offensive Vector / Technique | Defensive Detection & Mitigation |
|---|---|---|
| **Initial Access** | Office macro or script payload spawning shell. | **ASR Rule:** "Block all Office applications from creating child processes". **Sysmon:** Event ID 1 parent `WINWORD.EXE` -> child `powershell.exe`. |
| **Execution** | Syscall unhooking / Direct Syscalls. | **Kernel ETW-Ti:** Inspects syscall call-stack provenance; alerts on syscalls originating from unbacked or private memory allocations. |
| **Persistence** | Registry Run key or Scheduled Task creation. | **Sysmon Event ID 12/13:** Monitors modifications to `HKLM\Software\Microsoft\Windows\CurrentVersion\Run`. |
| **Privilege Escalation** | Weak service binary permission replacement. | **Access Control Lists (ACLs):** Restrict write access on `C:\Program Files` to `SYSTEM` and `TrustedInstaller` only. |
| **Credential Access** | Global keyboard event hooking (`WH_KEYBOARD_LL`). | **UIPI & EDR Telemetry:** User Interface Privilege Isolation blocks cross-integrity message hooks; EDR monitors API `SetWindowsHookExW`. |
| **Lateral Movement** | Kerberoasting / Service Ticket Requests. | **Event ID 4769:** Monitor spikes in RC4-encrypted (`0x17`) ticket requests from standard domain workstations. |

---

## 5. Practical Detection Artifacts

### A. Static Rule: YARA Signature for Suspicious Imphash & Imports
```yara
rule Detect_Suspicious_Injection_Imports {
    meta:
        description = "Detects PE files with API import profiles typical of memory injection"
        author = "Bionic Security Lab"
        date = "2026-08-28"
    strings:
        $a1 = "VirtualAllocEx" ascii wide
        $a2 = "WriteProcessMemory" ascii wide
        $a3 = "CreateRemoteThread" ascii wide
        $a4 = "OpenProcess" ascii wide
    condition:
        uint16(0) == 0x5A4D and // MZ header
        3 of ($a*) and
        filesize < 5MB
}
```

### B. Behavioral Rule: Sigma Detection for LOLBin Certutil File Retrieval
```yaml
title: Suspicious Certutil File Download
id: 8b7d91e4-56a2-4821-bc34-92104c881234
status: stable
description: Detects the use of certutil.exe to download files from remote URLs.
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        Image|endswith: '\certutil.exe'
        CommandLine|contains:
            - '-urlcache'
            - '/urlcache'
            - '-split'
            - '/split'
    condition: selection
level: high
tags:
    - attack.defense_evasion
    - attack.t1105
```

---

## 6. The Continuous Validation Loop

To ensure defense remains effective against emerging offensive tradecraft:
1. **Emulate:** Execute standardized test cases (e.g., using *Atomic Red Team* or *MITRE Caldera*).
2. **Verify:** Confirm logs reach the centralized SIEM/EDR and trigger expected alerts.
3. **Patch & Tune:** Close configuration gaps, update access control policies, and refine behavioral detection rules.
