# Nmap MCP Server

A [FastMCP](https://github.com/jlowin/fastmcp) server that exposes nmap
scanning capabilities as Model Context Protocol (MCP) tools.

## Tools

| Tool | Description |
|------|-------------|
| `tcp_syn_scan` | TCP SYN (stealth) scan |
| `udp_scan` | UDP scan |
| `os_detection` | OS fingerprinting via TCP/IP stack |
| `service_version` | Service/version detection |
| `script_scan` | Default NSE script scan |
| `vuln_scan` | Vulnerability scanning (NSE vuln scripts) |
| `firewall_detection` | Firewall/IDS evasion detection |
| `scan_report` | Comprehensive multi-scan report |

## Requirements

- Python 3.10+
- [Nmap](https://nmap.org/) installed and on PATH (or set `NMAP_BIN` env var)
- `fastmcp` and `mcp` packages

## Installation

```bash
pip install -r requirements.txt
```

## Running

```bash
python server.py
```

The server communicates over stdio (MCP default transport).

## Configuration

Set the environment variable `NMAP_BIN` to override the default nmap path:

```
NMAP_BIN=/usr/local/bin/nmap python server.py
```

Default path on Windows: `C:\Program Files (x86)\Nmap\nmap.exe`

## Example usage

```python
# From an MCP client
result = await call_tool("tcp_syn_scan", {
    "target": "scanme.nmap.org",
    "ports": "22,80,443",
    "timeout": 120,
})
print(result["stdout"])
```

## Security notes

- Only pre-defined nmap flag combinations are allowed — user-supplied
  flags are never passed directly to nmap.
- Targets are validated as IP addresses, CIDR blocks, or hostnames.
- Port specifications are validated against a strict regex.
- All scans respect a configurable timeout (default 300 s).
