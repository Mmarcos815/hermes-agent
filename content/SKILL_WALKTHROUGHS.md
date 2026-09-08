# Skill Walkthroughs — All 19 Learning Modules + Red Team Suite

> Step-by-step guides for every installed skill. Each walkthrough covers:
> what the skill does, how to invoke it, and what to expect.

---

## 1. AI/ML Security (Tier 6)

**Skill:** `learning/19_ai_ml_security/SKILL.md`

### What It Does
Attacks and tests AI/ML systems — evasion, extraction, and injection against neural networks and LLMs.

### Tools
| File | Attack | Target |
|------|--------|--------|
| `adversarial_gen.py` | FGSM, PGD evasion | Neural nets |
| `model_extract.py` | Model extraction/stealing | Black-box APIs |
| `prompt_injection_advanced.py` | Multi-turn, encoding, role-play | LLMs |

### Quick Start
```bash
python adversarial_gen.py --image cat.png --epsilon 0.03 --method fgsm
python model_extract.py --api-endpoint https://api.target/v1/predict --budget 1000
python prompt_injection_advanced.py --model gpt-4 --technique multi_turn
```

---

## 2. Mobile Security (Tier 6)

**Skill:** `learning/18_mobile_security/SKILL.md`

### What It Does
Android APK analysis + iOS app security — manifest parsing, permission auditing, hardcoded secrets, WebView risks.

### Tools
| File | Purpose |
|------|---------|
| `apk_analyzer.py` | APK security analysis (manifest, secrets, permissions) |
| `plist_parser.py` | iOS plist security analysis |

### Quick Start
```bash
python apk_analyzer.py --apk app.apk --full-report
python plist_parser.py --file Info.plist --security
```

---

## 3. Active Directory Attacks (Tier 6)

**Skill:** `learning/17_active_directory/SKILL.md`

### What It Does
AD credential abuse simulation — Kerberoasting, AS-REP Roasting, Golden Ticket, DCShadow, DCSync.

### Attack Chain
```
[Initial Access] → [Kerberoasting] → [Credential Theft] → [Lateral Movement]
                                                                    ↓
[Persistence] ← [Golden Ticket] ← [DCSync/Hash Dump] ← [Privilege Escalation]
```

### Key Attacks
- **Kerberoasting:** Request TGS for SPN-registered accounts, crack offline
- **AS-REP Roasting:** Target accounts with `DONT_REQUIRE_PREAUTH`
- **Golden Ticket:** Forge TGT using krbtgt hash
- **DCSync:** Simulate DC replication to extract hashes

---

## 4. Hardware/Wireless/Social/Crypto (Tier 5)

**Skill:** `learning/16_hardware_wireless_social_crypto/SKILL.md`

### What It Does
Four domains in one skill: hardware hacking (UART/JTAG/SPI), wireless security (WiFi/BT/SDR), social engineering (phishing/OSINT), and cryptography (hash extension/RSA/padding oracle).

### Tools
| File | Purpose |
|------|---------|
| `wifi_analyzer.py` | WPA3 downgrade, evil twin, deauth detection |
| `crypto_attack.py` | Hash extension, RSA small exponent, padding oracle |
| `phishing_sim.py` | Template generation, clone detection |

### Quick Start
```bash
python wifi_analyzer.py --scan --interface wlan0mon
python crypto_attack.py --hash-extension --data "original" --append "malicious" --hash <sha256> --key-length 16
python phishing_sim.py --generate-template --target "corp-login" --output phish.html
```

---

## 5. Browser Exploitation (Tier 5)

**Skill:** `learning/15_browser_exploitation/SKILL.md`

### What It Does
Client-side attack surfaces — DOM XSS, prototype pollution, V8 JIT concepts, Spectre/Meltdown awareness.

### Source → Sink Model
**Sources:** `location.hash`, `document.referrer`, `window.name`, `postMessage`, `localStorage`
**Sinks:** `eval()`, `innerHTML`, `document.write()`, `location.assign()`, `script.src`

### Framework Patterns
| Framework | Dangerous Pattern | Safe Alternative |
|-----------|-------------------|------------------|
| jQuery | `$(userInput)` | `.text()` with escaping |
| React | `dangerouslySetInnerHTML` | JSX auto-escaping |
| Angular | `bypassSecurityTrust` | Sanitizer pipeline |

---

## 6. Kernel Exploitation (Tier 5)

**Skill:** `learning/14_kernel_exploitation/SKILL.md`

### What It Does
Windows kernel-level exploitation — vulnerable driver scanning (BYOVD), VBS/KVA bypass, patch level analysis, privilege escalation paths.

### Workflow
```bash
python kernel_scanner.py --scan all
python kernel_scanner.py --driver C:\Windows\System32\drivers\vuln_driver.sys
```

---

## 7. Malware Development (Tier 5)

**Skill:** `learning/13_malware_development/SKILL.md`

### What It Does
Educational C2 architecture study — implant registration, beaconing, command dispatch, exfiltration. Purely defensive/educational.

### Implant ↔ C2 Lifecycle
```
[Implant] --register--> [C2 Server]
[C2 Server] <--beacon-- [Implant] (periodic check-in)
[C2 Server] --command--> [Implant] (task dispatch)
[Implant] --exfil-----> [C2 Server] (data staging + upload)
```

### Key Concepts
| Concept | Purpose | Detection Opportunity |
|---------|---------|----------------------|
| Beaconing | Periodic check-in | Regular timing patterns |
| Jitter | Randomize interval | Statistical analysis |
| Encryption | Obfuscate traffic | High entropy payloads |

---

## 8. Reverse Engineering (Tier 5)

**Skill:** `learning/12_reverse_engineering/SKILL.md`

### What It Does
Static analysis of PE/ELF binaries — metadata extraction, suspicious import detection, string extraction, packing identification.

### Quick Start
```bash
python re_analyzer.py <binary>
python re_analyzer.py <binary> --strings --min-len 6
python re_analyzer.py <binary> --json
```

### Format Identification
| Magic Bytes | Format |
|-------------|--------|
| `MZ` (0x4D 0x5A) | DOS header → PE (Windows) |
| 0x7F `ELF` | ELF (Linux) |
| `CAFEBABE` | Java class / Mach-O fat |

---

## 9. Red Team MCP Suite

**Skill:** `skills/red-team-mcp-suite/SKILL.md`

### What It Does
Routes security tasks to the right MCP server from 17 cloned repos. Covers network recon, web vuln scanning, CVE lookup, LLM red teaming, pentest toolchain, bug bounty discovery.

### Server Routing
| Task | MCP Server |
|------|------------|
| Port scanning | `nmap-mcp-server`, `pentest-mcp` |
| Web vuln scanning | `web-vuln-scanner-mcp`, `pentest-mcp` |
| CVE lookup | `vulnicheck`, `exploitdb-mcp-server` |
| MCP attack surface | `mcploit`, `MCP_Red_Team_Agent` |
| LLM red teaming | `godmode`, `community-rules` |
| Bug bounty | `hackerone-mcp-server` |
| Smart contract | `foundry-smart-contract-labs` |

### Cloned Repos (17 total)
| Repo | Stars | Purpose |
|------|-------|---------|
| appsecco/vulnerable-mcp-servers-lab | 277 | 9 vulnerable MCP servers |
| mukul975/Anthropic-Cybersecurity-Skills | 31,926 | 818 SKILL.md across 29 domains |
| bhavsec/autopentest-ai | 223 | Autonomous pentest agent |
| DMontgomery40/pentest-mcp | 143 | Professional pentest toolchain |
| RamKansal/pentestMCP | 93 | 150+ tools |
| halilkirazkaya/pentester-mcp | 52 | 200+ tools |
| 0x7556/kali_mcp | 64 | Kali integration |
| PhialsBasement/nmap-mcp-server | 49 | Nmap stdio MCP |
| Sicks3c/hackerone-mcp-server | 41 | HackerOne program discovery |
| Cyreslab-AI/exploitdb-mcp-server | 29 | ExploitDB lookup |
| secmate-ai/CyberSecurity-MCPs | 16 | General security MCPs |
| andrasfe/vulnicheck | 11 | Vulnerability check |
| Heisenbergg4/mcploit | 2 | MCP server red-teamer |
| SoelMgd/MCP_Red_Team_Agent | 1 | MCP red team agent |
| aryanrangapur/Vulnerability-Scanner-MCP-Server | 0 | Simple scanner |
| declawedai/community-rules | 4 | AI security detection rules |
| MorDavid/awesome-cyber-security-mcp | 99 | Curated MCP server list |

---

## 10. API Exploitation (Tier 4)

**Module:** `learning/03_api_exploitation/`

### What It Does
BOLA, JWT attacks, OAuth exploitation, SSRF, GraphQL injection.

### Tools
| File | Attack |
|------|--------|
| `01_bola_exploit.py` | Broken Object Level Authorization |
| `02_jwt_attack.py` | JWT forgery, algorithm confusion |
| `03_oauth_exploit.py` | OAuth flow manipulation |
| `04_graphql_exploit.py` | GraphQL query injection |
| `05_ssrf_tool.py` | Server-Side Request Forgery |

---

## 11. Banking API Exploitation (Tier 4)

**Module:** `learning/05_banking_api_exploitation/`

### What It Does
ISO 8583 fuzzing, EMV exploit simulation, payment API attacks.

### Tools
| File | Attack |
|------|--------|
| `01_iso8583_fuzz.py` | ISO 8583 message fuzzing |
| `02_emv_exploit.py` | EMV cryptogram bypass |

---

## 12. EVM Tracer (Tier 4)

**Module:** `learning/05_evm_tracer/`

### What It Does
EVM execution tracing — transaction replay, storage diff analysis, opcode profiling.

### Tool
- `evm_tracer.py` — Full EVM trace visualization

---

## 13. TLS 1.3 Wire Analysis (Tier 4)

**Module:** `learning/06_tls13_wire/`

### What It Does
TLS 1.3 packet-level analysis — handshake parsing, downgrade detection, cipher suite negotiation.

### Tool
- `tls13_wire_analyzer.py` — TLS 1.3 wire analysis

---

## 14. Kubernetes Security (Tier 4)

**Module:** `learning/08_kubernetes_security/`

### What It Does
K8s security lab — RBAC misconfig, pod escape, network policy bypass, admission control.

### Tool
- `k8s_security_lab.py` — Kubernetes security testing

---

## 15. Formal Verification (Tier 4)

**Module:** `learning/11_formal_verification/`

### What It Does
Certora specification writing — formal verification of smart contract invariants.

### Tool
- `certora_spec.sol` — Certora verification spec

---

## 16. GPU Kernels (Tier 4)

**Module:** `learning/10_gpu_kernels/`

### What It Does
CUDA kernel development — vector add, matrix multiply, PyTorch integration.

### Tools
| File | Purpose |
|------|---------|
| `vector_add.cu` | Basic CUDA vector addition |
| `pytorch_integration.py` | PyTorch + CUDA interop |

---

## 17. Windows Internals (Tier 4)

**Module:** `learning/09_windows_internals/`

### What It Does
Windows OS internals — PE parsing, DLL injection, APC injection, ETW analysis.

---

## 18. Prompt Injection (Tier 4)

**Module:** `learning/04_prompt_injection/`

### What It Does
Prompt injection techniques — direct, indirect, multi-turn, encoding-based.

---

## 19. Production MCP (Tier 4)

**Module:** `learning/03_production_mcp/`

### What It Does
Production MCP server patterns — error handling, rate limiting, auth, observability.

---

## Additional Learning Modules

### Rust (Tier 3)
**Module:** `learning/01_rust/` — Memory safety, ownership, lifetimes, unsafe Rust.

### Solidity Invariants (Tier 3)
**Module:** `learning/02_solidity_invariants/` — Invariant testing with Foundry.

---

## Skill Invocation Pattern

All skills follow the same pattern:

1. **Load the skill** — Hermes auto-loads from `~/AppData/Local/hermes/skills/`
2. **Match the trigger** — skill description contains keywords that route to it
3. **Follow the procedure** — each SKILL.md has a step-by-step workflow
4. **Verify output** — check results against expected invariants

---

**Generated:** 2026-09-05 | **Operator:** Bionic Daughter (Hermes Agent)
