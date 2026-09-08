────────────────────────────────────────────────────────────
name: red-team-mcp-suite
description: Operate the cloned GitHub red-team MCP server suite — vuln scanning, pentest toolchain, MCP-level attack surface, LLM red-teaming, and authorized bounty discovery. Use when you need to scan, probe, exploit, or analyze security surfaces through MCP servers instead of raw CLI tools. Never use against unauthorized targets — Dad's directive: testnet, bounties, labs, defensive telemetry only.
version: 1.0.0
author: Rigoberto Gomez (Dad) + Solar Pro4
license: MIT
platforms: [linux, windows]
metadata:
  hermes:
    tags: [red-team, mcp, security, penetration-testing, exploitation, vulnerability-scanning, nmap, nuclei, sqlmap, hackerone, mcp-loit, anthropic-cybersecurity-skills]
    category: red-teaming
    related_skills: [bionic-protocol-toolkits, godmode, hexstrike-proxy-setup, foundry-smart-contract-labs, vulnerability-toolkit-building, sqli-web3-mastery, hermes-agent]
    config:
      mcp_redteam_base_dir: ~/mcp-redteam
      mcp_redteam_mount_skills: true
      mcp_redteam_authorized_targets: []
      mcp_redteam_jetbrains_mcp_proxy: npx -y @jetbrains/mcp-proxy
      mcp_redteam_hackerone_token_env: HACKERONE_API_TOKEN
────────────────────────────────────────────────────────────

# Red Team MCP Suite

This skill manages the 17 GitHub-cloned MCP servers and the 819-skill Anthropic Cybersecurity Skills corpus installed under `~/mcp-redteam`. It routes security tasks to the right MCP server and surfaces the relevant Anthropic skill when the task maps to a structured procedure.

## When to Use

- **Network recon / port scanning** → route to `nmap-mcp-server` or `pentest-mcp` (`nmapScan`, `subfinderEnum`, `httpxProbe`)
- **Web application vulnerability scanning** → `web-vuln-scanner-mcp`, `pentest-mcp` (`nikto`, `ffufScan`, `nucleiScan`, `sqlmap`), `autopentest-ai`
- **Vulnerability + CVE lookup** → `vulnicheck`, `exploitdb-mcp-server`
- **MCP server attack surface (red-team the agent layer)** → `mcploit`, `MCP_Red_Team_Agent`, `vulnerable-mcp-servers-lab` (lab only)
- **LLM red teaming / jailbreak / prompt injection** → `godmode` skill, `community-rules` (declawedai detection rules), `Anthropic-Cybersecurity-Skills` (`red-teaming-llms-with-garak`, `continuous-llm-red-teaming-with-promptfoo`, `testing-prompt-injection-in-rag-pipelines`)
- **Pentest toolchain (professional)** → `pentest-mcp` (DMontgomery40, 143 stars), `pentester-mcp` (200+ tools), `kali_mcp`
- **Bug bounty discovery / scope lookup** → `hackerone-mcp-server`
- **Structured security procedure (819 Anthropic skills)** → load the matching SKILL.md from `Anthropic-Cybersecurity-Skills/skills/<domain>/SKILL.md`
- **Smart contract / Web3 security** → `foundry-smart-contract-labs` skill (already installed), `Anthropic-Cybersecurity-Skills` (`auditing-foundry-smart-contract-security`, `analyzing-ethereum-smart-contract-vulnerabilities`)
- **JetBrains IDE integration** → `jetbrains_mcp` (proxies MCP into a running IntelliJ/PyCharm/WebStorm/GoLand; see "IDE-Integrated MCP Proxies" below)

## Prerequisites

1. **All 17 repos cloned under `~/mcp-redteam`** — verified. If any are missing, re-clone with the `gh repo clone` commands in `references/cloned-repos.md`.
2. **Python/Node venvs where required** — `mcploit`, `vulnicheck`, `exploitdb-mcp-server`, `Vulnerability-Scanner-MCP-Server`, `autopentest-ai`, `MCP_Red_Team_Agent`, `pentester-mcp`, `Pentest-MCP`, `kali_mcp` are Python. `nmap-mcp-server`, `pentest-mcp` (DMontgomery40), `hackerone-mcp-server`, `CyberSecurity-MCPs` are JS/TS. Install per-repo `requirements.txt` / `package.json`.
3. **MCP server registration** — each server is registered in Hermes `config.yaml` under `mcp.servers` (stdio transport) pointing at its entrypoint. The Anthropic-Cybersecurity-Skills corpus is mounted as a skill directory (not as MCP — it's 819 SKILL.md files to load on demand).
4. **Authorized targets only** — `mcp_redteam_authorized_targets` in config or the `--authorized` flag. No live production without a written scope. Testnet (Anvil), bounty programs (HackerOne), and the vulnerable-MCP lab are in scope by default.

## How to Run

### 1. Pick the MCP server for the task

Use the table below. When in doubt, go to `pentest-mcp` (the most complete professional toolchain) or `mcploit` (MCP-layer attack surface).

| Task | Primary MCP server | Key tools |
|------|-------------------|-----------|
| Network recon, port scan, service detection | `nmap-mcp-server` (PhialsBasement, 49★) | `nmapScan` |
| Subdomain enumeration + HTTP probing | `pentest-mcp` (DMontgomery40) | `subfinderEnum`, `httpxProbe` |
| Directory/file brute-force | `pentest-mcp` | `ffufScan`, `gobuster` |
| Web vuln scanning | `pentest-mcp`, `web-vuln-scanner-mcp` | `nikto`, `nucleiScan`, SQLi/XSS/CSRF detection |
| SQL injection | `pentest-mcp` (sqlmap via tools), `sqli-web3-mastery` skill | `sqlmap` |
| CVE + exploit lookup | `vulnicheck` + `exploitdb-mcp-server` | CVE detail, CVSS, ExploitDB search |
| Hash cracking | `pentest-mcp`, `kali_mcp` | `runHashcat`, `runJohnTheRipper` |
| Credential dumping / auth testing | `kali_mcp`, `pentester-mcp` | `hydraBruteforce`, `Lazagne` |
| MCP server enumeration + exploitation | `mcploit` (99 payloads), `MCP_Red_Team_Agent` | enumerate tools/resources, SAST, exploit |
| MCP server red-team lab (training) | `vulnerable-mcp-servers-lab` (Appsecco, 277★) | pick a server, follow its README |
| Bug bounty program discovery | `hackerone-mcp-server` (Sicks3c, 41★) | programs, scope, reports, earnings |
| LLM jailbreak / adversarial prompts | `godmode` skill + `community-rules` detection rules | Parseltongue, GODMODE, ULTRAPLINIAN |
| Continuous LLM red teaming | `Anthropic-Cybersecurity-Skills` → `continuous-llm-red-teaming-with-promptfoo` | promptfoo evals |
| Detection rule authoring (AI security) | `community-rules` (declawedai) | prompt injection, MCP, agent skill rules |
| Full structured security procedure | Load from `Anthropic-Cybersecurity-Skills/skills/<domain>/SKILL.md` | 819 procedures across 29 domains |

### 2. Launch the server

Each MCP server runs as a stdio subprocess. Start it like any Hermes MCP server:

```
# Example: nmap MCP server
npx -y @phialsbasement/nmap-mcp-server
# or run the local clone:
node ~/mcp-redteam/nmap-mcp-server/build/index.js
```

For Python servers with venvs:

```
cd ~/mcp-redteam/mcploit && .venv/bin/python -m mcploit [...]
```

Add each server to `config.yaml` `mcp.servers` so Hermes discovers its tools automatically. See `references/mcp-server-registration.md` for the exact config block per server.

### 3. Use the tools

Once registered, the server's tools appear in the agent's toolset. Call them like any tool. Example flow for a web app assessment:

1. `subfinderEnum` → enumerate subdomains
2. `httpxProbe` → probe live HTTP hosts
3. `nikto` → web server vuln scan
4. `nucleiScan` → template-based vuln detection
5. `vulnicheck` → dependency/vuln check on discovered URLs
6. `exploitdb-mcp-server` → lookup known exploits for found vulns
7. `exploitdb-mcp-server` + manual validation against authorized target

For MCP-layer red teaming (attacking the agent surface itself):

1. `mcploit` → enumerate target MCP server's tools/resources/prompts
2. `mcploit` → passive vuln scan
3. `mcploit` → active exploit with payload library (99 payloads)
4. `vulnerable-mcp-servers-lab` → practice against a deliberately vulnerable MCP server in the disposable lab

### 4. Load the Anthropic Cybersecurity Skill when the task is procedural

The 819 SKILL.md files cover the full security lifecycle. When the task maps to a domain, load the matching skill:

```
skill_view(name="Anthropic-Cybersecurity-Skills:<domain>")
```

For example:
- `red-teaming-llms-with-garak` — LLM red teaming with GARAK
- `auditing-mcp-servers-for-tool-poisoning` — MCP tool poisoning audit
- `detecting-indirect-prompt-injection` — indirect prompt injection detection
- `exploiting-server-side-request-forgery` — SSRF exploitation
- `auditing-foundry-smart-contract-security` — Foundry/Solidity audit procedure
- `conducting-full-scope-red-team-engagement` — full-scope red team planning
- `performing-web-application-penetration-test` — web app pentest procedure

Use `search_files` inside `~/mcp-redteam/Anthropic-Cybersecurity-Skills/skills/` to find the domain that matches the task.

## Quick Reference

### Cloned repos (17 total, under ~/mcp-redteam)

```
mcp-redteam/
├── Anthropic-Cybersecurity-Skills/   # 819 SKILL.md, 29 domains, 6 framework mappings (31,926★)
├── autopentest-ai/                   # Agentic pentest MCP: discover + exploit + report (223★)
├── awesome-cyber-security-mcp/       # Curated cyber-security MCP list (99★)
├── community-rules/                  # AI security detection rules: prompt injection, MCP, agent skills (declawedai)
├── CyberSecurity-MCPs/               # Collection of security MCP servers (secmate-ai, 16★)
├── exploitdb-mcp-server/             # ExploitDB lookup via MCP (Cyreslab-AI, 29★)
├── hackerone-mcp-server/             # HackerOne programs/scope/reports/earnings (Sicks3c, 41★)
├── kali_mcp/                         # Kali AI pentest MCP toolset (0x7556, 64★)
├── MCP_Red_Team_Agent/               # MCPirats: multi-agent MCP vuln analysis + exploitation (SoelMgd)
├── mcploit/                          # MCP server enumeration + scan + exploit, 99 payloads (Heisenbergg4, 2★)
├── nmap-mcp-server/                  # Nmap over MCP, port scan + service detection + OS fingerprint (PhialsBasement, 49★)
├── pentester-mcp/                    # 200+ pentest tools via MCP in Docker sandbox (halilkirazkaya, 52★)
├── pentest-mcp/                      # Professional pentest MCP: nmap, john, hashcat, gobuster, nikto, nuclei, ffuf, hydra, subfinder, httpx (DMontgomery40, 143★)
├── pentestMCP/                       # AI-powered pentest via MCP (RamKansal, 93★)
├── Vulnerability-Scanner-MCP-Server/ # Nmap + CVE intelligence combo (aryanrangapur)
├── vulnerable-mcp-servers-lab/      # INTENTIONALLY VULNERABLE MCP servers for red-team training (Appsecco, 277★)
└── vulnicheck/                       # Python vuln scanner + MCP security toolkit, OSV/NVD/GitHub Advisory, CVE+CVSS+remediation (andrasfe, 11★)
```

### Vulnerable MCP Lab servers (Appsecco, DO NOT run outside a lab)

| Server | Vulnerability class |
|--------|---------------------|
| `vulnerable-mcp-server-filesystem-workspace-actions` | Path traversal + unsandboxed code execution |
| `vulnerable-mcp-server-indirect-prompt-injection` | Document retrieval returns embedded hidden instructions (local stdio) |
| `vulnerable-mcp-server-indirect-prompt-injection-remote-mcp` | Remote MCP over HTTP+SSE returns untrusted documents verbatim |
| `vulnerable-mcp-server-malicious-code-exec` | eval()-based RCE in "quote of the day" tool |
| `vulnerable-mcp-server-malicious-tools` | Instruction injection + fabricated tool output |
| `vulnerable-mcp-server-namespace-typosquatting` | Supply-chain/trust: lookalike server name (`twittter-mcp`) |
| `vulnerable-mcp-server-outdated-pacakges` | Outdated/deprecated/vulnerable dependency risk |
| `vulnerable-mcp-server-secrets-pii` | Secrets + PII embedded in source code, leakage via logs |
| `vulnerable-mcp-server-wikipedia-http-streamable` | Remote public content without sanitization → prompt injection risk |

### Framework mappings (Anthropic-Cybersecurity-Skills)

- **MITRE ATT&CK** — 29 domains, technique-level coverage
- **NIST CSF 2.0** — govern, identify, protect, detect, respond, recover
- **MITRE ATLAS** — AI/ML system threats
- **D3FEND** — defensive countermeasures catalog
- **NIST AI RMF** — AI risk management
- **MITRE F3 (Fight Fraud)** — Positioning (FA0001) + Monetization (FA0002) for cyber-enabled financial fraud

### Authorized targets (default in-scope)

- Anvil local testnet (Foundry) — `foundry-smart-contract-labs`
- HackerOne bounty programs in scope (via `hackerone-mcp-server`)
- `vulnerable-mcp-servers-lab` (disposable lab only)
- Any target explicitly added to `mcp_redteam_authorized_targets` in config.yaml

## Procedure: First-Time Setup

1. Verify all 17 repos present under `~/mcp-redteam` (`ls ~/mcp-redteam`). If short, see `references/cloned-repos.md` for the clone commands.
2. Install Python venvs for the Python-based servers:
   ```
   for d in mcploit vulnicheck exploitdb-mcp-server Vulnerability-Scanner-MCP-Server autopentest-ai MCP_Red_Team_Agent pentester-mcp Pentest-MCP kali_mcp; do
     cd ~/mcp-redteam/$d
     [ -f requirements.txt ] && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
     cd -
   done
   ```
3. Install Node deps for JS-based servers:
   ```
   cd ~/mcp-redteam/nmap-mcp-server && npm install
   cd ~/mcp-redteam/pentest-mcp && npm install  # DMontgomery40
   cd ~/mcp-redteam/hackerone-mcp-server && npm install
   cd ~/mcp-redteam/CyberSecurity-MCPs && npm install
   ```
4. Register MCP servers in `config.yaml`:
   ```yaml
   mcp:
     servers:
       nmap:
         command: node
         args: ["/home/user/mcp-redteam/nmap-mcp-server/build/index.js"]
         transport: stdio
       mcploit:
         command: /home/user/mcp-redteam/mcploit/.venv/bin/python
         args: ["-m", "mcploit"]
         transport: stdio
       vulnicheck:
         command: /home/user/mcp-redteam/vulnicheck/.venv/bin/python
         args: ["vulnicheck_mcp_server.py"]   # adjust to actual entrypoint
         transport: stdio
       # ... add the rest per references/mcp-server-registration.md
   ```
5. Mount the Anthropic skills corpus: add `~/mcp-redteam/Anthropic-Cybersecurity-Skills/skills/` to the skills search path (or load individual skills with `skill_view` on demand).
6. Verify: run `hermes tools` and confirm the red-team MCP tools appear in the available tool list.
7. Run the vulnerable-MCP lab in a disposable VM/container before touching any real target.

## IDE-Integrated MCP Proxies

Some MCP servers act as **proxies** to existing processes rather than running their own logic. The JetBrains MCP proxy is the canonical example: it bridges a running JetBrains IDE (IntelliJ / PyCharm / WebStorm / GoLand / etc.) into the agent's tool surface so the agent can read files, run inspections, execute refactors, and query the IDE's index without going through a filesystem MCP.

### JetBrains MCP proxy

```yaml
mcp:
  servers:
    jetbrains_mcp:
      command: npx
      args: ["-y", "@jetbrains/mcp-proxy"]
      env:
        JETBRAINS_IDE_PORT: "63342"
      timeout: 60
      connect_timeout: 10
```

**Prerequisites:**

1. A JetBrains IDE is open (any 2024.2+ version).
2. The **MCP Server** plugin is installed: Settings → Plugins → search "MCP Server" → Install.
3. The plugin's port is open and reachable (default `63342`). Set `JETBRAINS_IDE_PORT` env var to override.
4. The IDE is on a network the agent process can reach (localhost is fine for local usage; SSH/proxy for remote).

**Failure modes:**

- IDE closed / plugin disabled → stdio connect fails, Hermes silently drops the server, agent falls back to other tools.
- Port blocked by Windows Firewall / corporate proxy → connect_timeout hits in 10s; check the IDE's MCP Server plugin log.
- Plugin version mismatch with `@jetbrains/mcp-proxy` → upgrade both; pin via `npm install -g @jetbrains/mcp-proxy@<ver>` if needed.

**Pattern:** any MCP proxy that talks to a long-running external process should be wired with `connect_timeout` set low (10–15s) so a dead IDE/process doesn't stall the agent. Set `timeout` (handler timeout) higher (60–120s) since refactor / inspection operations can be slow.

### Adding token-gated MCP servers (HackerOne pattern)

Some servers boot fine without credentials but every tool call errors until you provide one. Document the env var explicitly in the skill's `config:` frontmatter and in `MCP_CONFIG_ADDITIONS.yaml`-style snippets — never assume the user knows which env var unlocks functionality.

Example: `hackerone-mcp-server` requires `HACKERONE_API_TOKEN` for any program/scope/report API call. The server starts cleanly without it; the agent sees a confusing auth error on the first call unless the skill flagged the requirement up front.

### Editing protected files (Hermes pattern)

`~/.hermes/config.yaml` is **agent-protected** — `patch` / `write_file` / `terminal write` to it will be refused with a "approval prompt timed out without a user response" error. Do NOT try the same edit via `execute_code` (the guard is on the path, not the tool).

**Correct pattern when you need to add MCP servers to `config.yaml`:**

1. Write a side file `MCP_CONFIG_ADDITIONS.yaml` (or `.md`) with the exact YAML block + comments explaining what each entry does.
2. Tell the user to merge it into `config.yaml` under `mcp_servers:` manually.
3. Verify the rest of your work doesn't depend on the addition being live (e.g. don't claim "JetBrains MCP is wired" until the user confirms the merge).
4. Update your skill's frontmatter `config:` block + a `## References` pointer so the next agent knows where the snippet lives.

This pattern keeps you from looping on the same refused write, gives the user a single auditable edit, and prevents accidental damage to the agent-instruction file.

## Pitfalls

- **MCP servers run as stdio subprocesses** — they block the agent while running. Long scans (full Nmap, hashcat) should be delegated or run background.
- **mcploit + MCP_Red_Team_Agent need an MCP server to target** — they don't scan the network directly; they attack MCP servers. Pair them with a lab server or an authorized target.
- **vulnerable-mcp-servers-lab is for training ONLY** — these servers are deliberately exploitable. Never expose them to a network, never use real secrets, never run outside a disposable lab.
- **pentest-mcp (DMontgomery40) carries a "not for educational purposes" note** — it's for professional pentesters with a scope. Same rule as Dad's directive: authorized targets only.
- **Anthropic-Cybersecurity-Skills are Claude/Claude-Code oriented** — some skills reference Claude-specific config (`.claude-plugin/`, `claude_config.json`). The SKILL.md procedure is tool-agnostic; adapt tool names to Hermes equivalents.
- **MCP server registration is per-profile** — if you use profiles, register the servers in each profile's config.yaml.
- **Secrets in MCP servers** — several cloned servers embed API keys or tokens in examples. Never paste real credentials into example configs.
- **Tool overlap** — multiple servers offer the same tool (nmap appears in 6+ MCP servers). Pick one per task to avoid duplicate tool schemas bloating the agent's context.

## Verification

1. `ls ~/mcp-redteam` shows all 17 repos.
2. `hermes tools` shows the registered red-team MCP tools.
3. `nmap-mcp-server` responds to a test `nmapScan` on localhost (authorized target) and returns parseable results.
4. `mcploit` enumerates a test MCP server (the lab's stdio server) and lists its tools.
5. `hackerone-mcp-server` lists programs the user is eligible for (requires HackerOne account + token).
6. `skill_view(name="Anthropic-Cybersecurity-Skills:red-teaming-llms-with-garak")` loads a skill from the corpus without error.
7. The vulnerable-MCP lab's filesystem-workspace-actions server runs in a disposable container and is exploitable per its README (verify the path traversal + code exec path).

## References

- `references/cloned-repos.md` — exact clone commands for all 17 repos + remotes
- `references/mcp-server-registration.md` — config.yaml blocks per server + entrypoint paths
- `references/vulnerable-mcp-lab-playbook.md` — lab setup, server selection order, exploitation walkthrough
- `references/anthropic-skills-index.md` — 29 domains, 819 skills, framework mapping summary
- `references/authorized-bounty-ladder.md` — how to move from lab → testnet → bounty program scope, Dad's authorization discipline
- `references/red-team-task-router.md` — task → server/tool mapping decision table
- `references/python-3.14-trl-peft-pickle-bug.md` — Windows + Python 3.14 + datasets/dill incompatibility; the 30-sec workaround using `uv venv --python 3.12`. Add this check to any training entrypoint script that runs on a host where you can't control the Python version.

────────────────────────────────────────────────────────────
END
