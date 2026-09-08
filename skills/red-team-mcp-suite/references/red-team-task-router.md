# Red Team Task Router — Task → Server/Tool Mapping

Use this table to route a security task to the right MCP server and tool. When multiple servers offer the same capability, pick the one with the best stars + the cleanest tool surface.

## Network recon

| Task | Primary server | Tool(s) | Fallback |
|------|----------------|---------|----------|
| Port scan, service detection, OS fingerprint | `nmap-mcp-server` (PhialsBasement, 49★) | `nmapScan` | `pentest-mcp` → `nmapScan`, `kali_mcp` → nmap |
| Subdomain enumeration | `pentest-mcp` (DMontgomery40, 143★) | `subfinderEnum` | `kali_mcp` → subfinder |
| HTTP probing / alive check | `pentest-mcp` | `httpxProbe` | `kali_mcp` → curl |
| Network traffic capture | `pentest-mcp` | `trafficCapture` | `kali_mcp` → tcpdump/tshark |
| Nmap advanced scanning | `Anthropic-Cybersecurity-Skills` → `scanning-network-with-nmap-advanced` | manual nmap CLI | any nmap MCP |

## Web application security

| Task | Primary server | Tool(s) | Fallback |
|------|----------------|---------|----------|
| Web server vuln scan | `pentest-mcp` | `nikto` | `web-vuln-scanner-mcp` |
| Directory/file brute-force | `pentest-mcp` | `ffufScan`, `gobuster` | `kali_mcp` → gobuster, `pentester-mcp` |
| Template-based vuln scanning | `pentest-mcp` | `nucleiScan` | standalone nuclei CLI |
| SQL injection detection/exploitation | `pentest-mcp` + `sqli-web3-mastery` skill | sqlmap (via tool or CLI) | `kali_mcp` → sqlmap |
| XSS testing | `web-vuln-scanner-mcp` (marc-shade) | XSS detection | `pentest-mcp` → manual Burp |
| CSRF testing | `Anthropic-Cybersecurity-Skills` → `performing-csrf-attack-simulation` | manual | `pentest-mcp` |
| SSRF exploitation | `Anthropic-Cybersecurity-Skills` → `exploiting-server-side-request-forgery` + `performing-blind-ssrf-exploitation` | manual | `pentest-mcp` |
| API security testing | `Anthropic-Cybersecurity-Skills` → `conducting-api-security-testing` + `performing-api-security-testing-with-postman` | Postman/manual | `pentest-mcp` |
| GraphQL security | `Anthropic-Cybersecurity-Skills` → `performing-graphql-security-assessment` + `performing-graphql-introspection-attack` | manual | `pentest-mcp` |
| Web cache poisoning/deception | `Anthropic-Cybersecurity-Skills` → `performing-web-cache-poisoning-attack` + `performing-web-cache-deception-attack` | manual | — |

## Vulnerability management

| Task | Primary server | Tool(s) | Fallback |
|------|----------------|---------|----------|
| CVE lookup + details | `vulnicheck` (andrasfe, 11★) | CVE detail, CVSS, remediation | `exploitdb-mcp-server` |
| Exploit lookup | `exploitdb-mcp-server` (Cyreslab-AI, 29★) | ExploitDB search | standalone searchsploit |
| Dependency/vuln scan on code | `vulnicheck` | OSV/NVD/GitHub Advisory DBs | `trivy`, `grype` |
| Container image vuln scan | `Anthropic-Cybersecurity-Skills` → `scanning-container-images-with-grype` + `scanning-docker-images-with-trivy` | trivy/grype CLI | `pentest-mcp` |
| Vuln prioritization | `Anthropic-Cybersecurity-Skills` → `prioritizing-vulnerabilities-with-cvss-scoring` + `performing-cve-prioritization-with-kev-catalog` | manual | `vulnicheck` |
| Vuln scanning workflow | `Anthropic-Cybersecurity-Skills` → `building-vulnerability-scanning-workflow` + `performing-authenticated-vulnerability-scan` | Nessus/OpenVAS | `pentest-mcp` → `extractionSweep` |
| Authenticated scan | `Anthropic-Cybersecurity-Skills` → `performing-authenticated-scan-with-openvas` | OpenVAS | `kali_mcp` → OpenVAS |

## Credential + auth testing

| Task | Primary server | Tool(s) | Fallback |
|------|----------------|---------|----------|
| Brute-force / password testing | `pentest-mcp` | `hydraBruteforce` | `kali_mcp` → hydra, `pentester-mcp` |
| Hash cracking | `pentest-mcp` | `runHashcat`, `runJohnTheRipper` | `kali_mcp` → hashcat/john |
| Credential dumping (authorized lab) | `Anthropic-Cybersecurity-Skills` → `performing-credential-access-with-lazagne` + `extracting-credentials-from-memory-dump` | LaZagne/volatility | `kali_mcp` |
| Kerberos testing (AD lab) | `Anthropic-Cybersecurity-Skills` → `exploiting-kerberoasting-with-impacket` + `performing-kerberoasting-attack` | impacket | — |
| OAuth token testing | `Anthropic-Cybersecurity-Skills` → `exploiting-oauth-misconfiguration` + `performing-oauth-scope-minimization-review` | manual | — |
| JWT testing | `Anthropic-Cybersecurity-Skills` → `testing-jwt-token-security` + `exploiting-jwt-algorithm-confusion-attack` + `performing-jwt-none-algorithm-attack` | manual/jwt CLI | — |

## MCP server attack surface (red-team the agent layer)

| Task | Primary server | Tool(s) | Fallback |
|------|----------------|---------|----------|
| Enumerate MCP server tools/resources/prompts | `mcploit` (Heisenbergg4) | connect + enumerate | `MCP-client` (IntegSec) |
| Passive MCP vuln scan | `mcploit` | passive scan | manual |
| Active MCP exploit | `mcploit` | 99-payload exploit library | `MCP_Red_Team_Agent` (SoelMgd) |
| Multi-agent MCP analysis | `MCP_Red_Team_Agent` | 5-agent pipeline: manager + API auditor + code reader + code auditor + exploitation | `mcploit` |
| MCP server audit (tool poisoning) | `Anthropic-Cybersecurity-Skills` → `auditing-mcp-servers-for-tool-poisoning` | manual + `mcploit` | — |
| Pentest MCP servers checklist | `pentesting-mcp-servers-checklist` (Appsecco, 40★) | methodology | — |
| Interactive MCP pentest CLI | `MCP-client` (IntegSec, 6★) | JSON-RPC 2.0, Burp/SOCKS5, Bearer/Basic/mTLS | `mcploit` |

## LLM red teaming

| Task | Primary resource | Tool/skill | Fallback |
|------|------------------|------------|----------|
| LLM jailbreak (Parseltongue/GODMODE/ULTRAPLINIAN) | `godmode` skill (already installed) | godmode skill | — |
| Continuous LLM red teaming | `Anthropic-Cybersecurity-Skills` → `continuous-llm-red-teaming-with-promptfoo` | promptfoo evals | `red-teaming-llms-with-garak` |
| LLM red teaming with GARAK | `Anthropic-Cybersecurity-Skills` → `red-teaming-llms-with-garak` | GARAK | `continuous-llm-red-teaming-with-promptfoo` |
| Prompt injection detection | `community-rules` (declawedai) + `Anthropic-Cybersecurity-Skills` → `detecting-indirect-prompt-injection` + `detecting-ai-model-prompt-injection-attacks` | detection rules | manual |
| Prompt injection in RAG pipelines | `Anthropic-Cybersecurity-Skills` → `testing-prompt-injection-in-rag-pipelines` | manual + `community-rules` | — |
| LLM guardrails / defense | `Anthropic-Cybersecurity-Skills` → `defending-llms-with-guardrails` + `implementing-llm-guardrails-for-security` + `implementing-llm-guardrails-for-security` | manual | — |
| Orchestrating LLM attacks | `Anthropic-Cybersecurity-Skills` → `orchestrating-llm-attacks-with-pyrit` | PyRIT | — |
| Data/model poisoning detection | `Anthropic-Cybersecurity-Skills` → `detecting-data-and-model-poisoning` | manual | — |
| Model extraction attacks | `Anthropic-Cybersecurity-Skills` → `detecting-model-extraction-attacks` | manual | — |
| System prompt leakage testing | `Anthropic-Cybersecurity-Skills` → `testing-for-system-prompt-leakage` | manual | — |

## Smart contract / Web3 security

| Task | Primary server/skill | Tool/skill | Fallback |
|------|---------------------|------------|----------|
| Foundry smart contract audit | `foundry-smart-contract-labs` skill (already installed) + `Anthropic-Cybersecurity-Skills` → `auditing-foundry-smart-contract-security` | Foundry + forge fuzz | — |
| Ethereum smart contract vuln analysis | `Anthropic-Cybersecurity-Skills` → `analyzing-ethereum-smart-contract-vulnerabilities` | manual + Slither/Mythril | — |
| Smart contract fuzz testing | `foundry-smart-contract-labs` skill | forge test --fuzz | `Anthropic-Cybersecurity-Skills` → `performing-fuzzing-with-aflplusplus` |
| Blockchain/CTI | `Anthropic-Cybersecurity-Skills` → `analyzing-certificate-transparency-for-phishing` + `analyzing-tls-certificate-transparency-logs` | manual | — |

## Bug bounty discovery

| Task | Primary server | Tool(s) | Fallback |
|------|----------------|---------|----------|
| HackerOne programs/scope/reports | `hackerone-mcp-server` (Sicks3c, 41★) | programs, scope, reports, hacktivity, earnings | HackerOne web UI |
| Bug bounty program discovery | `hackerone-mcp-server` | list programs | `awesome-cyber-security-mcp` → `conducting-external-reconnaissance-with-osint` |
| Scope lookup | `hackerone-mcp-server` | get program scope | web UI |

## Full engagement planning

| Task | Primary resource | Tool/skill | Fallback |
|------|------------------|------------|----------|
| Full-scope red team engagement | `Anthropic-Cybersecurity-Skills` → `conducting-full-scope-red-team-engagement` + `executing-red-team-engagement-planning` + `executing-red-team-exercise` | manual planning | — |
| Red team phishing | `Anthropic-Cybersecurity-Skills` → `performing-red-team-phishing-with-gophish` + `conducting-spearphishing-simulation-campaign` | Gophish | — |
| Purple team exercise | `Anthropic-Cybersecurity-Skills` → `performing-purple-team-exercise` + `performing-purple-team-atomic-testing` | Atomic Red Team | — |
| C2 infrastructure | `Anthropic-Cybersecurity-Skills` → `building-c2-infrastructure-with-sliver-framework` + `building-c2-redirector-infrastructure` + `building-red-team-c2-infrastructure-with-havoc` + `operating-havoc-c2` + `operating-sliver-c2` | Sliver/Havoc | — |
| Social engineering | `Anthropic-Cybersecurity-Skills` → `conducting-social-engineering-penetration-test` + `conducting-social-engineering-pretext-call` + `performing-red-team-phishing-with-gophish` | manual + Gophish | — |

## Forensics + incident response

| Task | Primary resource | Tool/skill | Fallback |
|------|------------------|------------|----------|
| Disk image acquisition | `Anthropic-Cybersecurity-Skills` → `acquiring-disk-image-with-dd-and-dcfldd` + `analyzing-disk-image-with-autopsy` | dd/dcfldd/Autopsy | — |
| Memory forensics | `Anthropic-Cybersecurity-Skills` → `analyzing-memory-dumps-with-volatility` + `conducting-memory-forensics-with-volatility` + `performing-memory-forensics-with-volatility3` + `extracting-memory-artifacts-with-rekall` | Volatility/Rekall | — |
| Malware triage | `Anthropic-Cybersecurity-Skills` → `performing-malware-triage-with-yara` + `analyzing-malware-behavior-with-cuckoo-sandbox` + `performing-malware-hash-enrichment-with-virustotal` | YARA/Cuckoo/VirusTotal | — |
| Windows artifact analysis | `Anthropic-Cybersecurity-Skills` → `analyzing-windows-event-logs-in-splunk` + `analyzing-windows-registry-for-artifacts` + `analyzing-windows-shellbag-artifacts` + `analyzing-windows-lnk-files-for-artifacts` + `performing-windows-artifact-analysis-with-eric-zimmerman-tools` | Eric Zimmerman tools/Splunk | — |
| Linux forensics | `Anthropic-Cybersecurity-Skills` → `analyzing-linux-system-artifacts` + `analyzing-linux-audit-logs-for-intrusion` + `performing-linux-log-forensics-investigation` | manual | — |
| Network forensics | `Anthropic-Cybersecurity-Skills` → `analyzing-network-packets-with-scapy` + `analyzing-network-traffic-with-wireshark` + `performing-network-forensics-with-wireshark` + `performing-network-traffic-analysis-with-zeek` | Wireshark/Scapy/Zeek | — |
| Ransomware response | `Anthropic-Cybersecurity-Skills` → `performing-ransomware-response` + `recovering-from-ransomware-attack` + `building-ransomware-playbook-with-cisa-framework` + `building-soc-playbook-for-ransomware` | manual + CISA framework | — |
| Incident response | `Anthropic-Cybersecurity-Skills` → `conducting-malware-incident-response` + `triaging-security-incident` + `triaging-security-incident-with-ir-playbook` + `building-incident-response-playbook` + `building-incident-response-dashboard` | manual + SIEM | — |

## Unauthenticated / quick lookup

| Task | Primary server | Tool(s) |
|------|----------------|---------|
| Vulnerability scan + CVE report (Python) | `Vulnerability-Scanner-MCP-Server` (aryanrangapur) | Nmap + CVE intelligence |
| Vulnerability scan + CVE report (JS) | `Vulnerability-Scanner-MCP-Server` (surendra-bishnoi29) | automated vuln scan + HTML/PDF report |
| Web vuln scan (SQLi/XSS/CSRF/auth) | `web-vuln-scanner-mcp` (marc-shade, 0★) | OWASP Top 10 detection |
| Vuln scan + LLM risk assessment | `vulnicheck` (andrasfe, 11★) | OSV/NVD/GitHub Advisory + LLM risk |
| ExploitDB lookup | `exploitdb-mcp-server` (Cyreslab-AI, 29★) | ExploitDB search |
