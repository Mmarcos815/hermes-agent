# MCPirats — Multi-Agent MCP Vulnerability Analysis Server

> **MCPirats** is a FastMCP-powered red team tool for analyzing, scanning,
> and testing Model Context Protocol (MCP) servers for security
> vulnerabilities. Part of the **Bionic Daughter** security academy project.

## What It Does

MCPirats exposes **10 security analysis tools** as an MCP server, allowing
any MCP-compatible client (Claude Desktop, Cursor, Windsurf, custom agents)
to perform automated vulnerability assessments of MCP server deployments.

The tools follow a natural pentest workflow:

1. **Reconnaissance** — Scan and enumerate the target
2. **Discovery** — Find tools, endpoints, and auth config
3. **Vulnerability Analysis** — Deep-dive into specific vuln classes
4. **Exploitation Support** — Suggest concrete exploit paths
5. **Reporting** — Generate structured audit reports

## Tools

| # | Tool | Description |
|---|------|-------------|
| 1 | `scan_mcp_server` | Connectivity check, MCP initialize handshake, header analysis |
| 2 | `discover_tools` | Enumerate all tools via `tools/list`, flag dangerous capabilities |
| 3 | `enumerate_endpoints` | Probe 23 common MCP HTTP endpoints, detect info leaks |
| 4 | `check_auth` | Analyze auth requirements, test unauthenticated access |
| 5 | `test_injection` | Send crafted injection payloads to tool parameters |
| 6 | `analyze_vulnerability` | Deep-dive into specific vuln classes (BOLA, SSRF, mass assignment, etc.) |
| 7 | `suggest_exploit` | Generate concrete exploit recommendations from scan findings |
| 8 | `generate_report` | Compile all findings into a structured JSON/Markdown audit report |
| 9 | `fuzz_tool` | Fuzz a specific tool with malformed inputs (crash/error detection) |
| 10 | `compare_schemas` | Diff tool schemas between two MCP servers (drift detection) |

## Installation

```bash
# Navigate to the MCPirats directory
cd redteam/MCP_Red_Team_Agent

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Running the Server

### Stdio Transport (for MCP clients like Claude Desktop)

```bash
python server.py
```

### HTTP Transport (for direct API access)

```bash
python server.py --transport http --port 8765
```

The server will listen on `http://127.0.0.1:8765/mcp`.

### SSE Transport

```bash
python server.py --transport sse --port 8765
```

### Development Mode (with FastMCP Inspector)

```bash
fastmcp dev server.py
```

This launches the FastMCP inspector UI for interactive tool testing.

## Configuration for MCP Clients

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mcpirats": {
      "command": "python",
      "args": ["/absolute/path/to/redteam/MCP_Red_Team_Agent/server.py"]
    }
  }
}
```

### Cursor / Windsurf

Add to your `.cursor/mcp.json` or project settings:

```json
{
  "mcpServers": {
    "mcpirats": {
      "command": "python",
      "args": ["/absolute/path/to/redteam/MCP_Red_Team_Agent/server.py"]
    }
  }
}
```

## Usage Workflow

A typical MCPirats assessment follows this sequence:

```
1. scan_mcp_server("https://target-mcp.example.com")
   → Establishes session, checks connectivity, headers, protocol version

2. discover_tools("https://target-mcp.example.com")
   → Enumerates all tools, flags dangerous capabilities

3. enumerate_endpoints("https://target-mcp.example.com")
   → Probes common endpoints for information leaks

4. check_auth("https://target-mcp.example.com")
   → Analyzes authentication configuration

5. test_injection("https://target-mcp.example.com")
   → Sends injection payloads to tool parameters

6. analyze_vulnerability("https://target-mcp.example.com", "bola")
   → Deep-dive into specific vulnerability class

7. suggest_exploit("https://target-mcp.example.com")
   → Generates exploit recommendations

8. generate_report("https://target-mcp.example.com", format="json")
   → Compiles final audit report
```

## Vulnerability Classes Covered

- **BOLA** (Broken Object Level Authorization) — CWE-639
- **Mass Assignment** — CWE-915
- **Excessive Information Disclosure** — CWE-200
- **Missing Rate Limiting** — CWE-770
- **Insecure Deserialization** — CWE-502
- **Tool Chaining** (read → execute) — CWE-78
- **Prompt Injection** — CWE-74
- **Path Traversal** — CWE-22
- **Command Injection** — CWE-78
- **SQL Injection** — CWE-89
- **SSRF** — CWE-918
- **Template Injection** — CWE-1336
- **Authentication Bypass** — CWE-306
- **Version Disclosure** — CWE-200

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Client (agent)                     │
└──────────────────────────┬──────────────────────────────┘
                           │ MCP protocol (stdio/HTTP/SSE)
┌──────────────────────────▼──────────────────────────────┐
│                    MCPirats Server                        │
│  ┌─────────────────────────────────────────────────┐    │
│  │              FastMCP (mcp.server)                │    │
│  ├─────────────────────────────────────────────────┤    │
│  │  Tools Layer                                     │    │
│  │  • scan_mcp_server    • check_auth               │    │
│  │  • discover_tools     • test_injection           │    │
│  │  • enumerate_endpoints • analyze_vulnerability   │    │
│  │  • suggest_exploit    • generate_report          │    │
│  │  • fuzz_tool          • compare_schemas          │    │
│  ├─────────────────────────────────────────────────┤    │
│  │  Protocol Layer                                  │    │
│  │  • MCP JSON-RPC (initialize, tools/list,         │    │
│  │    tools/call)                                   │    │
│  │  • HTTP probing & response analysis              │    │
│  ├─────────────────────────────────────────────────┤    │
│  │  HTTP Client (httpx)                             │    │
│  │  • Timeouts, redirects, connection pooling       │    │
│  └─────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP/JSON-RPC
┌──────────────────────────▼──────────────────────────────┐
│              Target MCP Server (under test)              │
└─────────────────────────────────────────────────────────┘
```

## Design Decisions

- **FastMCP**: Chosen for its simplicity, MCP spec compliance, and built-in transport support
- **Pydantic models**: All findings and results use validated models for type safety
- **Session-based**: Scan results are accumulated in-memory across tool calls, enabling multi-step analysis
- **httpx**: Modern HTTP client with proper timeout handling, connection pooling, and HTTP/2 support
- **Real HTTP requests**: Every tool makes actual network calls — no stubs or mocks

## Ethical Use Notice

**MCPirats is designed for authorized security testing only.**

Only use this tool against systems you own or have explicit written
permission to test. Unauthorized scanning may violate computer fraud
laws (CFAA, Computer Misuse Act, etc.). The Bionic Daughter project
is for educational purposes within controlled lab environments.

## License

Part of the Bionic Daughter security academy project.

See project root for license details.
