# Kali MCP Server

A FastMCP server that wraps popular Kali Linux penetration testing tools as
callable MCP (Model Context Protocol) tools. Designed for the **Bionic Daughter
security academy** — each tool invokes the real Kali binary via `subprocess` with
argument validation, timeouts, and structured error handling.

## Tools

| Tool | Description |
|---|---|
| `nmap_scan` | Network port/service scanning with nmap. |
| `sqlmap_run` | Automated SQL injection detection and exploitation. |
| `gobuster_dir` | Directory and file brute-forcing against web servers. |
| `nikto_scan` | Web server vulnerability scanning. |
| `hydra_brute` | Brute-force attacks against network services (SSH, FTP, HTTP, …). |
| `john_hash` | Password hash cracking with John the Ripper. |
| `aircrack_suite` | WPA/WPA2 Wi-Fi handshake cracking. |
| `metasploit_console` | Run any Metasploit module through `msfconsole`. |

## Layout

```
kali_mcp/
├── server.py            # FastMCP server + all tool definitions
├── requirements.txt     # fastmcp, mcp
├── README.md            # this file
└── assets/              # reference screenshots from Kali tools
    ├── cherry.png
    ├── kali_cmd.png
    ├── kali_nmap.png
    ├── kali_sqlmap.png
    └── kali_subdomain.png
```

## Installation

```bash
pip install -r requirements.txt
```

Or, if you already have the project venv:

```bash
source ../venv/Scripts/activate   # Windows / MSYS
pip install fastmcp mcp
```

## Running the server

### STDIO transport (default, for MCP hosts / Cursor / Claude Desktop)

```bash
python server.py
```

### HTTP / SSE transport

```bash
python server.py --transport http --port 8765
```

### With `mcp` CLI

```bash
mcp run server.py
```

## Configuration

| Setting | Default | Description |
|---|---|---|
| `DEFAULT_TIMEOUT` | `300` | Max seconds before a tool call is killed. |
| `ALLOWED_BINARIES` | (see source) | Maps tool name → expected binary path on Kali. |

Override per-call via the `timeout` parameter on every tool.

## Security notes

- **Targets are validated** — only IPv4 literals and valid hostnames/FQDNs are accepted; path traversal and shell metacharacters are rejected.
- **Shell is never invoked** — all subprocess calls use `list[str]` args (no `shell=True`).
- **Service/module whitelists** — `hydra_brute` and `metasploit_console` restrict inputs to known-good values.
- Run inside an isolated Kali VM or container. Never expose this server to an untrusted network.

## Example: call via MCP client

```python
from mcp.client.streamable_http import streamablehttp_client
import asyncio

async with streamablehttp_client("http://localhost:8765") as (read, write, _):
    result = await session.call_tool("nmap_scan", {"target": "10.0.0.1"})
    print(result)
```
