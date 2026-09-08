#!/usr/bin/env python3
"""
HexStrike AI — Hermes MCP Proxy
Registers 81 security tool schemas in Hermes without requiring
the backend Kali tools to be installed.

Purpose: Dad can see and call mcp_hexstrike_* tools for planning
and orchestration. Actual tool execution needs the HexStrike server
running at localhost:8888 with Kali tools installed.

Transport: stdio — Hermes launches this as a subprocess.
"""

import json, sys, os
from mcp.server.fastmcp import FastMCP

app = FastMCP("hexstrike-hermes-proxy")

# ── Tool catalog (81 tools, 7 categories) ──────────────────────────────────

TOOLS = {
    # Network Security (12)
    "nmap_scan":            ("network", "Advanced Nmap scanning — host discovery, port scan, service/version detection, OS fingerprinting"),
    "rustscan_scan":        ("network", "Ultra-fast port scanning with Rust — prioritizes speed, pipes results to Nmap for service detection"),
    "masscan_scan":         ("network", "High-speed Internet-scale port scanning — can scan the entire Internet in under 6 minutes"),
    "autorecon_scan":       ("network", "Comprehensive automated reconnaissance — combines multiple tools into a single workflow"),
    "amass_enum":           ("network", "Subdomain enumeration + OSINT — passive and active sources, DNS mapping, IntelX integration"),
    "subfinder":            ("network", "Passive subdomain discovery — 30+ sources, fast, reliable"),
    "fierce":               ("network", "DNS reconnaissance + zone transfer attempts — targeted at discovering misconfigured DNS"),
    "dnsenum":              ("network", "DNS enumeration — brute force, reverse lookup, zone transfer, Google scraping"),
    "theharvester":         ("network", "OSINT email/subdomain harvesting — searches search engines, PGP, LinkedIn, GitHub"),
    "responder":            ("network", "LLMNR/NBT-NS poisoner — captures credential hashes on the local network"),
    "netexec":              ("network", "Network pentesting toolkit — formerly CrackMapExec, SMB/WinRM/SSH/LDAP enumeration and execution"),
    "enum4linux_ng":       ("network", "SMB/Windows enumeration — user list, share enumeration, policy analysis, RID cycling"),

    # Web Application (25)
    "gobuster_scan":        ("web", "Directory/file/DNS enumeration — fast, wordlist-driven, Go-based"),
    "feroxbuster_scan":     ("web", "Recursive content discovery — brute forces paths, handles size filters, concurrent"),
    "ffuf_scan":            ("web", "Fast web fuzzing — directory, parameter, vhost, parameter keyword, and header fuzzing"),
    "dirsearch":            ("web", "Web content scanner — recursive directory/b file discovery, robots.txt handling"),
    "dirb":                ("web", "Web content scanner — older but still used, dictionary-based brute force"),
    "httpx":               ("web", "Multi-purpose HTTP toolkit — probes URLs, gets status codes, titles, tech fingerprints"),
    "katana":              ("web", "URL crawler — headless and non-headless, parameter discovery, JS parsing"),
    "nikto":               ("web", "Web server vulnerability scanner — 6700+ checks, outdated servers, dangerous files"),
    "sqlmap_scan":         ("web", "SQL injection testing — automatic detection and exploitation of SQL injection flaws"),
    "wpscan_scan":         ("web", "WordPress security scanner — core, plugin, theme vulnerability enumeration"),
    "arjun":               ("web", "HTTP parameter discovery — finds hidden parameters in web applications"),
    "paramspider":         ("web", "Parameter mining — extracts parameters from URLs, JS files, HTML forms"),
    "dalfox":              ("web", "XSS scanner — parameter analysis, payload generation, DOM-based XSS detection"),
    "wafw00f":             ("web", "WAF fingerprinting — identifies which WAF is protecting a target"),
    "hakrawler":           ("web", "Web endpoint discovery — fast, extracts URLs, JS files, forms from pages"),
    "gau":                 ("web", "URL fetching from archive.org — gets all URLs for a domain from Wayback Machine"),
    "waybackurls":         ("web", "Wayback Machine URL extraction — historical URLs for a domain"),
    "xsser":               ("web", "XSS detection/exploitation — auto-generates and tests Cross-Site Scripting payloads"),
    "wfuzz":               ("web", "Web application fuzzer — flexible payload filtering, multi-threaded"),
    "dotdotpwn":           ("web", "Directory traversal fuzzer — tests for path traversal vulnerabilities"),
    "burp_suite":          ("web", "Professional web security platform — intercepting proxy, scanner, intruder"),
    "owasp_zap":           ("web", "Web app security scanner — OWASP Zed Attack Proxy, open source"),
    "aquatone":            ("web", "Visual website inspection — screenshots, tech detection, status collection"),
    "subjack":             ("web", "Subdomain takeover checker — scans for subdomains pointing to unclaimed services"),
    "nuclei_scan":         ("web", "Vuln scanning with 4000+ templates — CVE detection, misconfiguration, default credentials"),

    # Authentication / Password (9)
    "hydra":               ("auth", "Login cracker — 50+ protocols (SSH, FTP, HTTP, SMB, Telnet, etc.), parallel"),
    "john":                ("auth", "Password hash cracking — John the Ripper, supports 100+ hash types"),
    "hashcat":             ("auth", "Password recovery — GPU-accelerated, world's fastest, 300+ hash types"),
    "medusa":              ("auth", "Parallel brute-forcer — thread-based, modular, supports many protocols"),
    "patator":             ("auth", "Multi-purpose brute-forcer — modular, Python-based, more flexible than Hydra"),
    "crackmapexec":        ("auth", "Pentesting Swiss army knife — network authentication testing, now netexec"),
    "evil_winrm":          ("auth", "Windows RM shell — PowerShell over WinRM, post-exploitation"),
    "hash_identifier":     ("auth", "Hash type identification — analyzes hash format and suggests type"),
    "ophcrack":            ("auth", "Windows password cracker — rainbow table-based, live CD"),

    # Binary / Reverse Engineering (17)
    "ghidra_analyze":      ("binary", "NSA reverse engineering suite — decompiler, disassembler, scripting"),
    "radare2_analyze":     ("binary", "Advanced RE framework — cross-platform, scripting, large plugin ecosystem"),
    "gdb_debug":           ("binary", "GNU debugger — source-level debugging, reverse debugging, remote targets"),
    "pwntools_exploit":    ("binary", "CTF exploit framework — Python library for exploit development"),
    "angr_analyze":        ("binary", "Symbolic execution — path exploration, constraint solving, vulnerability discovery"),
    "binwalk":             ("binary", "Firmware analysis — extracts embedded files, identifies signatures"),
    "ropgadget":           ("binary", "ROP/JOP gadget finder — extracts return-oriented programming gadgets"),
    "checksec":            ("binary", "Binary security checker — RELRO, stack canary, NX, PIE, ASLR status"),
    "strings":             ("binary", "String extraction — pulls printable strings from binary files"),
    "objdump":             ("binary", "Object file info — displays sections, headers, disassembly"),
    "xxd":                 ("binary", "Hex dump — makes a hexdump or converts hex to binary"),
    "volatility3":         ("binary", "Memory forensics — analyzes RAM dumps, process lists, network connections"),
    "foremost":            ("binary", "File carving — recovers embedded files from raw data"),
    "steghide":            ("binary", "Steganography detection — embeds/hides data in images and audio"),
    "exiftool":            ("binary", "Metadata reader/writer — reads/writes metadata in 100+ file formats"),
    "autopsy":             ("binary", "Digital forensics platform — disk imaging, file recovery, timeline analysis"),
    "sleuthkit":           ("binary", "Forensics tools — file system analysis, media management, timeline"),

    # Cloud Security (8)
    "prowler_assess":      ("cloud", "AWS/Azure/GCP security assessment — CIS benchmarks, compliance checking"),
    "scout_suite_audit":   ("cloud", "Multi-cloud auditing — AWS, Azure, GCP, OAuth-based, HTML/JSON report"),
    "trivy_scan":          ("cloud", "Container vulnerability scanning — OS packages, language libraries, IaC"),
    "kube_hunter_scan":    ("cloud", "Kubernetes pentesting — probes for misconfigurations, security issues"),
    "kube_bench_check":    ("cloud", "CIS K8s benchmark — checks if Kubernetes is deployed securely"),
    "docker_bench_security": ("cloud", "Docker CIS benchmark — container host, daemon, image security checks"),
    "checkov":             ("cloud", "IaC security scanning — Terraform, CloudFormation, Kubernetes, Dockerfiles"),
    "terrascan":           ("cloud", "Policy enforcement — scans IaC for security misconfigurations and compliance"),

    # OSINT (5)
    "sherlock":            ("osint", "Find social media accounts — searches 300+ sites for a username"),
    "social_analyzer":     ("osint", "Social media analysis — 300+ sites, email, phone, domain lookups"),
    "recon_ng":            ("osint", "Recon framework — modular,  reconnaissance for target information gathering"),
    "shodan_cli":          ("osint", "Shodan CLI — Internet-connected device search, host enumeration"),
    "censys_cli":          ("osint", "Censys CLI — Internet-wide host and certificate search"),

    # Payload Generation (5)
    "xss_payload":         ("payload", "XSS payload generator — context-aware, bypasses, polyglots"),
    "sql_injection_payload": ("payload", "SQLi payload generator — union-based, blind, timed, error-based"),
    "command_injection_payload": ("payload", "Cmd injection generator — Unix/Windows, chained, obfuscated"),
    "lfi_rfi_payload":     ("payload", "LFI/RFI payload generator — path traversal, wrapper, filter bypass"),
    "ssti_payload":        ("payload", "SSTI payload generator — template engine detection, exploitation"),
}

TOTAL = len(TOOLS)
CATEGORIES = {}
for name, (cat, desc) in TOOLS.items():
    CATEGORIES[cat] = CATEGORIES.get(cat, 0) + 1


# ── MCP Tools ──────────────────────────────────────────────────────────────

@app.tool()
def hexstrike_tool_list() -> str:
    """List all 81 HexStrike tools grouped by category with descriptions."""
    tools_list = []
    for name, (cat, desc) in sorted(TOOLS.items()):
        tools_list.append({
            "name": name,
            "description": desc,
            "category": cat,
        })
    return json.dumps({
        "total_tools": TOTAL,
        "categories": CATEGORIES,
        "tools": tools_list,
    }, indent=2)


@app.tool()
def hexstrike_health() -> str:
    """Check HexStrike proxy health status."""
    return json.dumps({
        "status": "proxy_ready",
        "tools_registered": TOTAL,
        "server_required": "localhost:8888 for actual execution",
        "message": "Schemas registered. Call hexstrike_tool_list() to see all tools.",
    })


@app.tool()
def hexstrike_command(target: str, tool: str, args: str = "") -> str:
    """Request execution of a HexStrike tool against a target.

    Returns tool_not_available unless the HexStrike server is running
    at localhost:8888 with the requested Kali tool installed.
    """
    if tool not in TOOLS:
        return json.dumps({"error": f"Unknown tool: {tool}", "available": sorted(TOOLS.keys())})
    cat, desc = TOOLS[tool]
    return json.dumps({
        "error": "tool_not_available",
        "tool": tool,
        "target": target,
        "category": cat,
        "description": desc,
        "message": f"'{tool}' requires HexStrike server at localhost:8888 with the tool installed.",
    })


# Dynamic tool registration — factory with attribute-baked values.
# FastMCP rejects params starting with '_', so we store tool metadata
# on the function object and read it inside the body.

_tool_counter = 0

def make_hexstrike_tool(tool_name: str, description: str, category: str):
    """Factory that creates a standalone MCP tool for one HexStrike tool."""
    global _tool_counter
    _tool_counter += 1

    def hexstrike_tool(target: str = "", **kw) -> str:
        tn = hexstrike_tool._tool_name
        desc = hexstrike_tool._description
        cat = hexstrike_tool._category
        return json.dumps({
            "error": "tool_not_available",
            "tool": tn,
            "target": target,
            "description": desc,
            "category": cat,
            "message": f"'{tn}' requires HexStrike server at localhost:8888. Start it with: python hexstrike_server.py",
        })

    hexstrike_tool._tool_name = tool_name
    hexstrike_tool._description = description
    hexstrike_tool._category = category
    hexstrike_tool.__name__ = f"hexstrike_{tool_name.replace('-', '_')}"
    hexstrike_tool.__doc__ = f"HexStrike {tool_name} — {description}"

    app.add_tool(hexstrike_tool)
    return hexstrike_tool


for tool_name, (cat, desc) in TOOLS.items():
    make_hexstrike_tool(tool_name, desc, cat)


if __name__ == "__main__":
    print(f"HexStrike AI - Hermes MCP Proxy | {TOTAL} tools registered across {len(CATEGORIES)} categories")
    print(f"Categories: {', '.join(f'{k}({v})' for k, v in sorted(CATEGORIES.items()))}")
    print("")
    print("Add to ~/.hermes/config.yaml under mcp_servers:")
    print("  hexstrike:")
    print("    command: \"python\"")
    script_path = os.path.abspath(__file__)
    print(f"    args: [\"{script_path}\"]")
    print("    timeout: 300")
    print("    connect_timeout: 60")
    print("")
    print("Restart Hermes. Tools appear as mcp_hexstrike_<tool_name>.")
    print(f"Test: call mcp_hexstrike_hexstrike_tool_list() -> {TOTAL} tools.")
    sys.exit(app.run())
