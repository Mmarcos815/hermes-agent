# MCPloit — Exploit Enumeration & SAST MCP Server

A FastMCP server providing tools for exploit enumeration, CVE lookups,
vulnerability scanning, static code analysis, and report generation.
Designed for the **Bionic Daughter** security academy project.

## Features

- **11 MCP tools** for offensive and defensive security work
- **Real API calls** to NIST NVD, Exploit-DB, CVE.circl.lu, HackerTarget
- **Pattern-based SAST** covering OWASP Top 10 categories
- **Modular architecture** — easy to add new tools or detection rules
- **Async** throughout for concurrent operation

## Installation

```bash
# From the project root
cd "my 1st"
source venv/Scripts/activate        # or: venv\Scripts\activate on cmd.exe
cd redteam/mcploit

pip install -r requirements.txt
```

## Usage

### Stdio mode (default — for MCP clients)

```bash
python server.py
```

### HTTP mode (for testing / MCP Inspector)

```bash
python server.py --http
# Server listens on http://127.0.0.1:8000/mcp
```

### SSE mode (legacy)

```bash
python server.py --sse
```

## Configuring in an MCP client

Add to your `mcp.json` / `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mcploit": {
      "command": "C:/Users/mobil/orca/projects/my 1st/venv/Scripts/python.exe",
      "args": ["C:/Users/mobil/orca/projects/my 1st/redteam/mcploit/server.py"]
    }
  }
}
```

For HTTP transport:

```json
{
  "mcpServers": {
    "mcploit": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

## Tools

| Tool | Description | APIs Used |
|------|-------------|-----------|
| `search_exploits` | Search Exploit-DB by keyword | exploit-db.com, cve.circl.lu |
| `lookup_cve` | Get CVE details by ID | NIST NVD 2.0, cve.circl.lu |
| `scan_vulnerabilities` | Scan a target (nmap/web/passive) | nmap, hackertarget.com |
| `analyze_code` | Static code analysis (SAST) | Local regex patterns |
| `check_misconfig` | Check web target for misconfigurations | Direct HTTP checks |
| `enumerate_services` | Service enumeration on a host | nmap, hackertarget.com |
| `test_credentials` | Test for weak/default credentials | paramiko, ftplib, httpx |
| `generate_report` | Generate structured assessment reports | Local |
| `get_exploit_details` | Get exploit code and metadata | exploit-db.com |
| `check_patch` | Check CVEs for a product/version | NIST NVD 2.0 |
| `cve_timeline` | Recent CVEs for a product | NIST NVD 2.0 |

### Tool Details

#### `search_exploits(query, platform?, exploit_type?, limit=20)`
Search Exploit-DB for exploits matching a keyword. Supports platform and type filters.

```json
{
  "query": "apache 2.4",
  "platform": "linux",
  "limit": 10
}
```

#### `lookup_cve(cve_id)`
Look up a CVE by its identifier (e.g., "CVE-2024-1234").

```json
{ "cve_id": "CVE-2023-44487" }
```

#### `scan_vulnerabilities(target, scan_type='nmap', ports?, aggressive?)`
Run a vulnerability scan. Supports `nmap`, `web`, and `passive` scan types.

```json
{
  "target": "example.com",
  "scan_type": "web"
}
```

#### `analyze_code(code, language='auto', check_xss=true, check_sqli=true, ...)`
Perform static analysis on source code for security vulnerabilities.

```json
{
  "code": "import os; os.system(user_input)",
  "language": "python"
}
```

#### `check_misconfig(target, checks?)`
Check for missing security headers, permissive CORS, exposed files, dangerous HTTP methods.

```json
{
  "target": "https://example.com",
  "checks": "headers,cors,files"
}
```

#### `enumerate_services(target, scan_ports='top100', include_version=true)`
Enumerate running services on a host.

```json
{
  "target": "192.168.1.1",
  "scan_ports": "top100"
}
```

#### `test_credentials(target, service='ssh', username='admin', wordlist?, max_attempts=5)`
Test for weak/default credentials using a built-in wordlist or custom file.

> ⚠️ **Only use against systems you own or have authorization to test.**

```json
{
  "target": "192.168.1.1",
  "service": "ssh",
  "username": "root,admin",
  "max_attempts": 10
}
```

#### `generate_report(findings?, target, title, format='json', include_remediation=true)`
Generate a structured report from findings data.

```json
{
  "findings": {"vulnerulnerabilities": [...]},
  "target": "example.com",
  "format": "markdown"
}
```

#### `get_exploit_details(exploit_id)`
Get detailed exploit information and code from Exploit-DB.

```json
{ "exploit_id": "48522" }
```

#### `check_patch(product, version, include_eol=true)`
Check NVD for CVEs affecting a specific product version.

```json
{
  "product": "Apache httpd",
  "version": "2.4.41"
}
```

#### `cve_timeline(product, days=30)`
Get recent CVEs published for a product.

```json
{
  "product": "openssl",
  "days": 30
}
```

## Architecture

```
mcploit/
├── server.py          # FastMCP server with all tools
├── requirements.txt   # Dependencies
└── README.md          # This file
```

The server is a single FastMCP instance (`mcp`) with tools registered via the
`@mcp.tool()` decorator. All external HTTP calls go through a shared
`httpx.AsyncClient` for connection pooling and consistent headers.

### Error Handling

Every tool returns a structured JSON response:
- Success: `{"status": "ok", "timestamp": "...", "data": {...}}`
- Error: `{"status": "error", "timestamp": "...", "error": "...", "detail": "..."}`

Tools **never raise** — errors are caught and returned as structured data so
the MCP client always gets a valid response.

## Testing

Quick smoke test with curl (HTTP mode):

```bash
# Start server
python server.py --http &

# List tools
curl http://127.0.0.1:8000/mcp/tools/list

# Call a tool
curl -X POST http://127.0.0.1:8000/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "lookup_cve", "arguments": {"cve_id": "CVE-2023-44487"}}'
```

## License & Disclaimer

This tool is for **authorized security testing and education only**.
Unauthorized access to computer systems is illegal. The authors accept no
responsibility for misuse.
