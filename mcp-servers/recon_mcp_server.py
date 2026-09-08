#!/usr/bin/env python3
"""
Recon MCP Server - Reconnaissance tools for MCP clients.

Provides simulated reconnaissance tools (subdomain enumeration, port scanning,
technology detection, Wayback Machine checks, and git leak detection).
All tools run in simulation mode by default; pass --live to enable real network calls.
"""

import argparse
import asyncio
import json
import random
import sys
from datetime import datetime, timedelta
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Common TCP ports for scanning
COMMON_PORTS = [21, 22, 25, 53, 80, 110, 143, 443, 993, 995, 3306, 5432, 8080, 8443]

# Common web technologies and their signatures
WEB_TECHS = {
    "nginx": {"header": "Server", "value": "nginx"},
    "apache": {"header": "Server", "value": "Apache"},
    "cloudflare": {"header": "Server", "value": "cloudflare"},
    "php": {"header": "X-Powered-By", "value": "PHP"},
    "express": {"header": "X-Powered-By", "value": "Express"},
    "django": {"header": "X-Frame-Options", "value": "DENY"},
    "wordpress": {"header": "Link", "value": "wp-json"},
    "react": {"header": "X-React", "value": "true"},
    "nextjs": {"header": "X-Powered-By", "value": "Next.js"},
}

# Simulated subdomain wordlist
SUBDOMAIN_WORDS = [
    "www", "mail", "ftp", "localhost", "webmail", "smtp", "pop", "ns1", "ns2",
    "admin", "blog", "dev", "test", "stage", "api", "secure", "vpn", "m",
    "mobile", "shop", "store", "support", "portal", "forum", "wiki", "docs",
    "status", "monitor", "git", "gitlab", "jenkins", "ci", "cdn", "static",
    "assets", "img", "media", "files", "upload", "download", "backup", "old",
]


class ReconServer:
    """Reconnaissance MCP server with simulated and live tool modes."""

    def __init__(self, live: bool = False):
        self.live = live
        self.server = Server("recon-mcp-server")
        self._register_tools()

    def _register_tools(self):
        """Register all reconnaissance tools with the MCP server."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="subdomain_enum",
                    description="Enumerate subdomains using certificate transparency logs",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "domain": {"type": "string", "description": "Target domain to enumerate"},
                            "max_results": {"type": "integer", "description": "Maximum results to return (default 20)"},
                        },
                        "required": ["domain"],
                    },
                ),
                Tool(
                    name="port_scan",
                    description="TCP port scan on common ports",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "host": {"type": "string", "description": "Target host (domain or IP)"},
                            "ports": {"type": "array", "items": {"type": "integer"}, "description": "Custom ports to scan (default: common ports)"},
                        },
                        "required": ["host"],
                    },
                ),
                Tool(
                    name="tech_detect",
                    description="Detect web technologies from HTTP response headers",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "URL to analyze"},
                        },
                        "required": ["url"],
                    },
                ),
                Tool(
                    name="wayback_check",
                    description="Check Wayback Machine for historical URLs",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "URL to look up in Wayback Machine"},
                            "limit": {"type": "integer", "description": "Number of results (default 10)"},
                        },
                        "required": ["url"],
                    },
                ),
                Tool(
                    name="git_leaks",
                    description="Check for exposed .git directories on a web server",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "Base URL to check for .git exposure"},
                        },
                        "required": ["url"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            try:
                if name == "subdomain_enum":
                    result = await self._subdomain_enum(arguments)
                elif name == "port_scan":
                    result = await self._port_scan(arguments)
                elif name == "tech_detect":
                    result = await self._tech_detect(arguments)
                elif name == "wayback_check":
                    result = await self._wayback_check(arguments)
                elif name == "git_leaks":
                    result = await self._git_leaks(arguments)
                else:
                    result = {"error": f"Unknown tool: {name}"}

                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]

    async def _subdomain_enum(self, args: dict[str, Any]) -> dict[str, Any]:
        """Enumerate subdomains using certificate transparency logs (simulated)."""
        domain = args["domain"]
        max_results = args.get("max_results", 20)

        if self.live:
            # In live mode, this would query crt.sh or similar CT log APIs
            return {
                "domain": domain,
                "mode": "live",
                "note": "Live mode not yet implemented - requires HTTP client setup",
                "subdomains": [],
            }

        # Simulation: generate plausible subdomains
        random.seed(hash(domain))
        count = random.randint(3, min(max_results, len(SUBDOMAIN_WORDS)))
        found = random.sample(SUBDOMAIN_WORDS, count)
        subdomains = sorted([f"{word}.{domain}" for word in found])

        return {
            "domain": domain,
            "mode": "simulated",
            "source": "certificate_transparency_logs",
            "total_found": len(subdomains),
            "subdomains": subdomains[:max_results],
        }

    async def _port_scan(self, args: dict[str, Any]) -> dict[str, Any]:
        """TCP port scan on common ports (simulated)."""
        host = args["host"]
        ports = args.get("ports", COMMON_PORTS)

        if self.live:
            return {
                "host": host,
                "mode": "live",
                "note": "Live mode not yet implemented - requires raw socket/connection setup",
                "open_ports": [],
            }

        # Simulation: randomly open some common ports
        random.seed(hash(host))
        open_ports = []
        common_open = {80, 443, 22}  # Almost always "open"
        for port in ports:
            if port in common_open or random.random() < 0.2:
                service = self._guess_service(port)
                open_ports.append({"port": port, "service": service, "state": "open"})

        return {
            "host": host,
            "mode": "simulated",
            "ports_scanned": len(ports),
            "open_ports": sorted(open_ports, key=lambda x: x["port"]),
            "scan_time": f"{random.uniform(0.5, 5.0):.2f}s",
        }

    def _guess_service(self, port: int) -> str:
        """Map common ports to service names."""
        services = {
            21: "ftp", 22: "ssh", 25: "smtp", 53: "dns", 80: "http",
            110: "pop3", 143: "imap", 443: "https", 993: "imaps",
            995: "pop3s", 3306: "mysql", 5432: "postgresql",
            8080: "http-proxy", 8443: "https-alt",
        }
        return services.get(port, "unknown")

    async def _tech_detect(self, args: dict[str, Any]) -> dict[str, Any]:
        """Detect web technologies from HTTP response headers (simulated)."""
        url = args["url"]

        if self.live:
            return {
                "url": url,
                "mode": "live",
                "note": "Live mode not yet implemented - requires HTTP request",
                "technologies": [],
            }

        # Simulation: pick random technologies
        random.seed(hash(url))
        tech_count = random.randint(1, 4)
        chosen = random.sample(list(WEB_TECHS.items()), tech_count)
        technologies = [
            {"name": name, "header": info["header"], "value": info["value"]}
            for name, info in chosen
        ]

        headers = {
            "Server": "nginx/1.24.0",
            "Content-Type": "text/html; charset=UTF-8",
            "X-Frame-Options": "SAMEORIGIN",
        }
        # Add detected tech headers
        for tech in technologies:
            headers[tech["header"]] = tech["value"]

        return {
            "url": url,
            "mode": "simulated",
            "status_code": 200,
            "headers": headers,
            "technologies": technologies,
        }

    async def _wayback_check(self, args: dict[str, Any]) -> dict[str, Any]:
        """Check Wayback Machine for historical URLs (simulated)."""
        url = args["url"]
        limit = args.get("limit", 10)

        if self.live:
            return {
                "url": url,
                "mode": "live",
                "note": "Live mode not yet implemented - requires Wayback CDX API call",
                "snapshots": [],
            }

        # Simulation: generate fake snapshot history
        random.seed(hash(url))
        snapshots = []
        base_date = datetime.now() - timedelta(days=365 * 2)
        paths = ["/", "/about", "/contact", "/login", "/api/v1", "/robots.txt", "/sitemap.xml"]

        for i in range(min(limit, len(paths))):
            snap_date = base_date + timedelta(days=random.randint(0, 730))
            snapshots.append({
                "url": f"{url.rstrip('/')}{paths[i]}",
                "timestamp": snap_date.strftime("%Y%m%d%H%M%S"),
                "status": random.choice(["200", "301", "302", "404"]),
                "digest": f"{random.getrandbits(128):032x}",
            })

        return {
            "url": url,
            "mode": "simulated",
            "source": "wayback_machine_cdx",
            "total_snapshots": len(snapshots),
            "snapshots": sorted(snapshots, key=lambda x: x["timestamp"], reverse=True),
        }

    async def _git_leaks(self, args: dict[str, Any]) -> dict[str, Any]:
        """Check for exposed .git directories (simulated)."""
        url = args["url"].rstrip("/")

        if self.live:
            return {
                "url": url,
                "mode": "live",
                "note": "Live mode not yet implemented - requires HTTP requests to /.git/ paths",
                "exposures": [],
            }

        # Simulation: small chance of exposure
        random.seed(hash(url))
        is_exposed = random.random() < 0.15  # 15% chance

        exposures = []
        if is_exposed:
            git_paths = [
                "/.git/HEAD",
                "/.git/config",
                "/.git/index",
                "/.git/refs/heads/main",
                "/.git/logs/HEAD",
            ]
            exposures = [
                {"path": f"{url}{p}", "status": "200", "risk": "high"}
                for p in random.sample(git_paths, random.randint(2, len(git_paths)))
            ]

        return {
            "url": url,
            "mode": "simulated",
            "is_exposed": is_exposed,
            "checked_paths": ["/.git/HEAD", "/.git/config", "/.git/index", "/.git/description"],
            "exposures": exposures,
            "recommendation": "Restrict access to .git directory via web server configuration" if is_exposed else "No .git exposure detected",
        }

    async def run(self):
        """Run the MCP server over stdio."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, write_stream, self.server.create_initialization_options()
            )


def main():
    parser = argparse.ArgumentParser(description="Recon MCP Server")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Enable live network calls (default: simulation mode)",
    )
    args = parser.parse_args()

    server = ReconServer(live=args.live)
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
