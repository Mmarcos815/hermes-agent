# MCP Server Registration — config.yaml Blocks

Each MCP server is registered under `mcp.servers` in `config.yaml`. Hermes discovers the tools at startup and they appear in the agent's toolset.

## Common pattern

```yaml
mcp:
  servers:
    <server_name>:
      command: <executable>
      args: [<arg1>, <arg2>, ...]
      transport: stdio
      env: {}            # optional — API keys, tokens
      timeout: 300      # optional — seconds before Hermes kills the subprocess
```

## Registered servers

### nmap-mcp-server (PhialsBasement, 49★)

```
~/mcp-redteam/nmap-mcp-server/
```

Node.js. Entrypoint: check `package.json` → `main` or `bin`.

```yaml
mcp:
  servers:
    nmap:
      command: node
      args: ["/home/user/mcp-redteam/nmap-mcp-server/build/index.js"]
      transport: stdio
```

Or run from the clone with npx:
```yaml
mcp:
  servers:
    nmap:
      command: npx
      args: ["-y", "@phialsbasement/nmap-mcp-server"]
      transport: stdio
```

### mcploit (Heisenbergg4, 2★)

```
~/mcp-redteam/mcploit/
```

Python. Install: `cd mcploit && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.

```yaml
mcp:
  servers:
    mcploit:
      command: /home/user/mcp-redteam/mcploit/.venv/bin/python
      args: ["-m", "mcploit"]
      transport: stdio
      env:
        ANTHROPIC_API_KEY: "${ANTHROPIC_API_KEY}"   # optional, for --ai flag
```

### vulnicheck (andrasfe, 11★)

```
~/mcp-redteam/vulnicheck/
```

Python. Install deps per `requirements.txt`. Entrypoint: check repo for the MCP server file (likely `vulnicheck_mcp_server.py` or similar — verify by reading the repo).

```yaml
mcp:
  servers:
    vulnicheck:
      command: /home/user/mcp-redteam/vulnicheck/.venv/bin/python
      args: ["/home/user/mcp-redteam/vulnicheck/<entrypoint>.py"]
      transport: stdio
```

### exploitdb-mcp-server (Cyreslab-AI, 29★)

```
~/mcp-redteam/exploitdb-mcp-server/
```

Python/JS — check `package.json` / `requirements.txt` to determine runtime.

```yaml
mcp:
  servers:
    exploitdb:
      command: <python-or-node>
      args: ["<entrypoint>"]
      transport: stdio
```

### Vulnerability-Scanner-MCP-Server (aryanrangapur)

```
~/mcp-redteam/Vulnerability-Scanner-MCP-Server/
```

Python.

```yaml
mcp:
  servers:
    vulnscanner:
      command: /home/user/mcp-redteam/Vulnerability-Scanner-MCP-Server/.venv/bin/python
      args: ["<entrypoint>"]
      transport: stdio
```

### hackerone-mcp-server (Sicks3c, 41★)

```
~/mcp-redteam/hackerone-mcp-server/
```

TypeScript. Needs a HackerOne API token.

```yaml
mcp:
  servers:
    hackerone:
      command: node
      args: ["/home/user/mcp-redteam/hackerone-mcp-server/build/index.js"]
      transport: stdio
      env:
        HACKERONE_API_TOKEN: "${HACKERONE_API_TOKEN}"
```

### pentest-mcp (DMontgomery40, 143★)

```
~/mcp-redteam/pentest-mcp/
```

JavaScript/Node. Docker-based toolchain (nmap, john, hashcat, gobuster, nikto, etc.) — install the Kali toolchain in the Docker container or on the host.

```yaml
mcp:
  servers:
    pentest:
      command: node
      args: ["/home/user/mcp-redteam/pentest-mcp/build/index.js"]
      transport: stdio
```

Set `MCP_TRANSPORT=http` for HTTP mode (Streamable HTTP) if stdio doesn't work.

### pentester-mcp (halilkirazkaya, 52★)

```
~/mcp-redteam/pentester-mcp/
```

Python + Docker sandbox with 200+ tools.

```yaml
mcp:
  servers:
    pentester:
      command: /home/user/mcp-redteam/pentester-mcp/.venv/bin/python
      args: ["<entrypoint>"]
      transport: stdio
```

### kali_mcp (0x7556, 64★)

```
~/mcp-redteam/kali_mcp/
```

Python. Needs Kali toolchain on host (nmap, sqlmap, subfinder, nikto, metasploit, aircrack-ng, tshark, john, openvas, gobuster, wget, curl, ssh, tcpdump, theHarvester, searchsploit).

```yaml
mcp:
  servers:
    kali:
      command: /home/user/mcp-redteam/kali_mcp/.venv/bin/python
      args: ["<entrypoint>"]
      transport: stdio
```

### CyberSecurity-MCPs (secmate-ai, 16★)

```
~/mcp-redteam/CyberSecurity-MCPs/
```

JavaScript.

```yaml
mcp:
  servers:
    cybersec:
      command: node
      args: ["/home/user/mcp-redteam/CyberSecurity-MCPs/build/index.js"]
      transport: stdio
```

### autopentest-ai (bhavsec, 223★)

```
~/mcp-redteam/autopentest-ai/
```

Python. Agentic pentest: discover + exploit + report.

```yaml
mcp:
  servers:
    autopentest:
      command: /home/user/mcp-redteam/autopentest-ai/.venv/bin/python
      args: ["<entrypoint>"]
      transport: stdio
```

### MCP_Red_Team_Agent (SoelMgd, 1★)

```
~/mcp-redteam/MCP_Red_Team_Agent/
```

Python. Multi-agent MCP vuln analysis. Needs Anthropic API key.

```yaml
mcp:
  servers:
    mcpredteam:
      command: /home/user/mcp-redteam/MCP_Red_Team_Agent/.venv/bin/python
      args: ["<entrypoint>"]
      transport: stdio
      env:
        ANTHROPIC_API_KEY: "${ANTHROPIC_API_KEY}"
```

## Anthropic Cybersecurity Skills corpus

Not an MCP server — 819 SKILL.md files mounted as a skill directory.

```yaml
skills:
  paths:
    - /home/user/mcp-redteam/Anthropic-Cybersecurity-Skills/skills/
```

Or load on demand:
```
skill_view(name="Anthropic-Cybersecurity-Skills:<domain>")
```

## Notes

- Replace `/home/user/` with the actual home path on the host (`C:\Users\mobil\` on Windows, but MCP servers run better with POSIX paths; use the MSYS path `/c/Users/mobil/` for Node/Python subprocesses).
- Verify each server's actual entrypoint before registering — read `package.json` (Node) or the repo's main `.py` file (Python).
- Some servers require host-level tool installation (Kali toolchain for pentest-mcp/kali_mcp). Install those separately — the MCP server is just the bridge.
- `mcp` section name is illustrative — use the actual Hermes config key for MCP servers (check `hermes_cli/config.py` DEFAULT_CONFIG for the current key).
