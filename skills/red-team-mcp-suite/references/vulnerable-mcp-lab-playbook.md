# Vulnerable MCP Lab Playbook

Source: `~/mcp-redteam/vulnerable-mcp-servers-lab/` (Appsecco, 277★).

**DO NOT run any of this outside a controlled lab environment.** Use a disposable VM or container, isolated network, no real secrets.

## Lab setup

1. Spin up a disposable Linux container/VM (Docker, UTM, VirtualBox — anything disposable).
2. Install Node.js (for the JS MCP servers) and Python 3.10+ (for the Python ones).
3. Clone the lab: `gh repo clone appsecco/vulnerable-mcp-servers-lab`
4. Each server has its own `README.md` with run instructions. Read it before starting the server.
5. Many servers include a `claude_config.json` snippet for Claude Desktop's MCP config — adapt to Hermes `config.yaml` `mcp.servers` if you want Hermes to attack them.

## Server selection order (build up difficulty)

### Level 1 — Config + secrets exposure (easy, foundational)

**`vulnerable-mcp-server-secrets-pii`**
- What: "Utilities" tools (IP/weather/news) with embedded secrets + PII in source code, leakage via logs.
- Attack: read the source, find the hardcoded values, confirm they leak in tool output/logs.
- Lesson: never embed secrets in MCP server source; log sanitization matters.

**`vulnerable-mcp-server-outdated-pacakges`**
- What: read-only system/filesystem inspection tools with outdated/deprecated/vulnerable dependencies.
- Attack: run `npm audit` / `pip audit` / `safety check` against the server's deps, find the vuln, confirm it's exploitable in context.
- Lesson: dependency hygiene is a real attack surface.

### Level 2 — Path traversal + code execution (medium)

**`vulnerable-mcp-server-filesystem-workspace-actions`**
- What: read/write/list a "workspace" + Python execution; vulnerable to naive path joining + unsandboxed code execution.
- Attack: path traversal to read files outside the workspace; execute arbitrary Python via the code exec tool.
- Lesson: sandbox file operations; never expose unsandboxed code execution to an agent.

### Level 3 — Instruction injection (medium, core red-team skill)

**`vulnerable-mcp-server-indirect-prompt-injection`** (local stdio)
- What: document retrieval/search that returns documents verbatim, including embedded hidden instructions.
- Attack: craft a document with hidden instructions; retrieve it; observe the agent executing the injected instructions.
- Lesson: retrieved content is untrusted input; separate data from instructions; sanitize/escape before returning to the model.

**`vulnerable-mcp-server-indirect-prompt-injection-remote-mcp`** (remote HTTP+SSE)
- What: Network-accessible MCP server (HTTP+SSE) returning untrusted documents verbatim.
- Attack: same as above, but over the network — demonstrates the risk of connecting to untrusted remote MCP endpoints.
- Lesson: remote MCP servers are a trust boundary; treat their output as attacker-controlled.

### Level 4 — Active exploitation (hard)

**`vulnerable-mcp-server-malicious-code-exec`**
- What: "Quote of the day" tool with unsafe formatting that `eval()`s attacker-controlled JavaScript.
- Attack: craft a quote payload that executes arbitrary JS via eval; achieve RCE in the MCP server process.
- Lesson: never eval user input; sandbox untrusted code.

**`vulnerable-mcp-server-malicious-tools`**
- What: Appears to return status data but injects misleading instructions + fabricates plausible-looking incidents.
- Attack: call the tool; observe the injected instructions; confirm the model follows them.
- Lesson: tool output can be weaponized; trust boundaries around tool results matter.

### Level 5 — Supply chain + trust (conceptual, hard to "exploit" in a lab)

**`vulnerable-mcp-server-namespace-typosquatting`**
- What: Lookalike server name (`twittter-mcp`) intended to be mistaken for a legitimate package.
- Attack: conceptual — the exploit is the install/registration of the typosquatted server instead of the real one.
- Lesson: verify server identity; pin server names; don't trust package names blindly.

**`vulnerable-mcp-server-wikipedia-http-streamable`**
- What: Wikipedia search/retrieval over HTTP; returns untrusted public content without sanitization.
- Attack: Wikipedia articles can contain hidden instructions (conceptual — real Wikipedia is mostly clean, but the architecture is the point).
- Lesson: any remote content source is a prompt injection surface; sanitize/escape.

## Exploitation workflow (per server)

1. Read the server's `README.md`.
2. Start the server in the lab.
3. Register it in Hermes `config.yaml` `mcp.servers` (or call it directly if it's a CLI).
4. Enumerate the server's tools via `mcploit` (connect + enumerate) or by reading the source.
5. Execute the attack per the README's "how to demonstrate" section.
6. Document: what the vulnerability is, how it was exploited, the impact, and the fix.
7. Save the write-up to the canonical audits layout (`~/OneDrive/Desktop/bionic_daughter_agent/_AUDITS/`).

## Verification

- `vulnerable-mcp-server-secrets-pii`: find at least one hardcoded secret in the source and confirm it appears in tool output/logs.
- `vulnerable-mcp-server-filesystem-workspace-actions`: read a file outside the workspace via path traversal; execute a Python snippet that proves code execution.
- `vulnerable-mcp-server-indirect-prompt-injection`: craft a document with a hidden instruction; retrieve it; confirm the agent executes the instruction.
- `vulnerable-mcp-server-malicious-code-exec`: achieve arbitrary JS execution via the eval-based RCE.
- `vulnerable-mcp-server-malicious-tools`: call the tool and observe the injected/fabricated output.

## Cross-reference

- `mcploit` — connect to these lab servers and enumerate/exploit them programmatically.
- `MCP_Red_Team_Agent` — multi-agent analysis of these servers.
- `godmode` skill — same injection concepts, applied to LLM jailbreak.
- `Anthropic-Cybersecurity-Skills` → `auditing-mcp-servers-for-tool-poisoning` — structured MCP audit procedure.
- `Anthropic-Cybersecurity-Skills` → `detecting-indirect-prompt-injection` — detection-side counterpart.
