"""
Nmap MCP Server — FastMCP server exposing nmap scanning tools.
"""

import ipaddress
import re
import subprocess
import time
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Path to nmap binary (Windows default)
NMAP_BIN = r"C:\Program Files (x86)\Nmap\nmap.exe"

# Whitelist of safe nmap flags per tool – we never pass user-supplied flags
# directly to nmap.
SAFE_FLAGS: dict[str, list[str]] = {
    "tcp_syn_scan": ["-sS", "-T4"],
    "udp_scan": ["-sU", "-T4"],
    "os_detection": ["-O", "--osscan-guess", "-T4"],
    "service_version": ["-sV", "--version-intensity", "5", "-T4"],
    "script_scan": ["-sC", "-T4"],
    "vuln_scan": ["--script=vuln", "-T4"],
    "firewall_detection": ["-sA", "--script=firewall-bypass", "-T4"],
}

_HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)"
    r"(\.[A-Za-z0-9-]{1,63})*\.?$"
)


def _validate_target(target: str) -> str:
    """Validate a target (IP or hostname). Raise ValueError on bad input."""
    target = target.strip()
    if not target:
        raise ValueError("Target must not be empty")

    # Try as an IP address (IPv4 or IPv6)
    try:
        ipaddress.ip_address(target)
        return target
    except ValueError:
        pass

    # Try as a CIDR network
    try:
        ipaddress.ip_network(target, strict=False)
        return target
    except ValueError:
        pass

    # Try as a hostname
    if _HOSTNAME_RE.match(target):
        return target

    raise ValueError(
        f"Invalid target '{target}': must be a valid IP, CIDR, or hostname"
    )


def _run_nmap(args: list[str], timeout: int = 300) -> dict[str, Any]:
    """Run nmap with the given args and return a structured result."""
    cmd = [NMAP_BIN] + args
    start = time.time()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return {
            "success": False,
            "error": f"nmap binary not found at '{NMAP_BIN}'. "
            "Install nmap or adjust NMAP_BIN.",
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"nmap timed out after {timeout}s",
            "command": " ".join(cmd),
        }

    elapsed = round(time.time() - start, 2)

    # nmap returns 0 on success, 1 when no hosts are up (still useful)
    if proc.returncode not in (0, 1):
        return {
            "success": False,
            "error": f"nmap exited with code {proc.returncode}",
            "stderr": proc.stderr.strip(),
            "stdout": proc.stdout.strip(),
            "command": " ".join(cmd),
            "elapsed_seconds": elapsed,
        }

    return {
        "success": True,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "command": " ".join(cmd),
        "elapsed_seconds": elapsed,
    }


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp = FastMCP("nmap-scanner")


@mcp.tool()
def tcp_syn_scan(target: str, ports: str = "1-1024", timeout: int = 300) -> dict[str, Any]:
    """Run a TCP SYN (stealth) scan against a target.

    Args:
        target: IP address, CIDR, or hostname to scan.
        ports: Port range (e.g. "80", "20-80", "80,443,8080"). Default 1-1024.
        timeout: Maximum seconds to wait. Default 300.
    """
    target = _validate_target(target)
    # Validate ports string: only digits, commas, hyphens
    if not re.match(r"^[0-9,\- ]+$", ports):
        return {"success": False, "error": f"Invalid ports specification: '{ports}'"}
    args = SAFE_FLAGS["tcp_syn_scan"] + ["-p", ports, target]
    return _run_nmap(args, timeout)


@mcp.tool()
def udp_scan(target: str, ports: str = "53,67,68,69,123,137,138,161,162,500,514,520,631,1434,1900,4500,5353,49152", timeout: int = 300) -> dict[str, Any]:
    """Run a UDP scan against a target.

    Args:
        target: IP address, CIDR, or hostname to scan.
        ports: UDP ports to scan. Common UDP ports by default.
        timeout: Maximum seconds to wait. Default 300.
    """
    target = _validate_target(target)
    if not re.match(r"^[0-9,\- ]+$", ports):
        return {"success": False, "error": f"Invalid ports specification: '{ports}'"}
    args = SAFE_FLAGS["udp_scan"] + ["-p", ports, target]
    return _run_nmap(args, timeout)


@mcp.tool()
def os_detection(target: str, timeout: int = 300) -> dict[str, Any]:
    """Attempt OS detection via TCP/IP fingerprinting.

    Args:
        target: IP address, CIDR, or hostname to scan.
        timeout: Maximum seconds to wait. Default 300.
    """
    target = _validate_target(target)
    args = SAFE_FLAGS["os_detection"] + [target]
    return _run_nmap(args, timeout)


@mcp.tool()
def service_version(target: str, ports: str = "1-1024", timeout: int = 300) -> dict[str, Any]:
    """Probe open ports for service/version information.

    Args:
        target: IP address, CIDR, or hostname to scan.
        ports: Port range to probe. Default 1-1024.
        timeout: Maximum seconds to wait. Default 300.
    """
    target = _validate_target(target)
    if not re.match(r"^[0-9,\- ]+$", ports):
        return {"success": False, "error": f"Invalid ports specification: '{ports}'"}
    args = SAFE_FLAGS["service_version"] + ["-p", ports, target]
    return _run_nmap(args, timeout)


@mcp.tool()
def script_scan(target: str, ports: str = "1-1024", timeout: int = 300) -> dict[str, Any]:
    """Run NSE default scripts against a target.

    Args:
        target: IP address, CIDR, or hostname to scan.
        ports: Port range to scan. Default 1-1024.
        timeout: Maximum seconds to wait. Default 300.
    """
    target = _validate_target(target)
    if not re.match(r"^[0-9,\- ]+$", ports):
        return {"success": False, "error": f"Invalid ports specification: '{ports}'"}
    args = SAFE_FLAGS["script_scan"] + ["-p", ports, target]
    return _run_nmap(args, timeout)


@mcp.tool()
def vuln_scan(target: str, ports: str = "1-1024", timeout: int = 300) -> dict[str, Any]:
    """Run NSE vuln scripts against a target.

    Args:
        target: IP address, CIDR, or hostname to scan.
        ports: Port range to scan. Default 1-1024.
        timeout: Maximum seconds to wait. Default 300.
    """
    target = _validate_target(target)
    if not re.match(r"^[0-9,\- ]+$", ports):
        return {"success": False, "error": f"Invalid ports specification: '{ports}'"}
    args = SAFE_FLAGS["vuln_scan"] + ["-p", ports, target]
    return _run_nmap(args, timeout)


@mcp.tool()
def firewall_detection(target: str, ports: str = "80,443,22,25,53", timeout: int = 300) -> dict[str, Any]:
    """Detect firewall rules using ACK scan and NSE firewall scripts.

    Args:
        target: IP address, CIDR, or hostname to scan.
        ports: Port range to probe. Default common ports.
        timeout: Maximum seconds to wait. Default 300.
    """
    target = _validate_target(target)
    if not re.match(r"^[0-9,\- ]+$", ports):
        return {"success": False, "error": f"Invalid ports specification: '{ports}'"}
    args = SAFE_FLAGS["firewall_detection"] + ["-p", ports, target]
    return _run_nmap(args, timeout)


@mcp.tool()
def scan_report(target: str, scan_type: str = "comprehensive", timeout: int = 600) -> dict[str, Any]:
    """Generate a comprehensive scan report combining multiple scan types.

    Args:
        target: IP address, CIDR, or hostname to scan.
        scan_type: One of "quick", "standard", "comprehensive".
        timeout: Maximum seconds to wait. Default 600.
    """
    target = _validate_target(target)

    scan_profiles = {
        "quick": ["-sS", "-T4", "-F"],
        "standard": ["-sS", "-sV", "-sC", "-O", "--osscan-guess", "-T4", "-p", "1-1024"],
        "comprehensive": [
            "-sS", "-sU", "-sV", "--version-intensity", "5",
            "-O", "--osscan-guess", "-sC", "--script=vuln,firewall-bypass",
            "-T4", "-p", "1-65535",
        ],
    }

    if scan_type not in scan_profiles:
        return {
            "success": False,
            "error": f"Invalid scan_type '{scan_type}'. Choose from: {list(scan_profiles.keys())}",
        }

    args = scan_profiles[scan_type] + [target]
    return _run_nmap(args, timeout)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
