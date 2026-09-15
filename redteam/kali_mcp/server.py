"""
Kali MCP Server - FastMCP server wrapping Kali Linux security tools.

Provides tools for nmap, sqlmap, gobuster, nikto, hydra, john, aircrack-ng, and metasploit.
Each tool calls the underlying Kali binary via subprocess with argument validation,
timeout enforcement, and structured error handling.
"""

import re
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Server instance
# ---------------------------------------------------------------------------

mcp = FastMCP("kali-mcp")

# Default timeout for subprocess calls (seconds)
DEFAULT_TIMEOUT = 300

# Allowed base commands (must exist on PATH)
ALLOWED_BINARIES = {
    "nmap": "/usr/bin/nmap",
    "sqlmap": "/usr/bin/sqlmap",
    "gobuster": "/usr/bin/gobuster",
    "nikto": "/usr/bin/nikto",
    "hydra": "/usr/bin/hydra",
    "john": "/usr/bin/john",
    "aircrack-ng": "/usr/bin/aircrack-ng",
    "msfconsole": "/usr/bin/msfconsole",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Strict hostname / IP / domain validation patterns
_IPV4_RE = re.compile(
    r"^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$"
)
_HOSTNAME_RE = re.compile(
    r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*\.[A-Za-z]{2,}$"
)
# A safe target is either an IPv4 literal or a valid hostname / FQDN
_TARGET_RE = re.compile(
    r"^(?:"
    r"(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)"
    r"|"
    r"(?!-)[A-Za-z0-9.-]{1,253}(?<!\-)"
    r")$"
)

# Safe filename pattern (no path traversal)
_SAFE_FILE_RE = re.compile(r"^[A-Za-z0-9._-]{1,255}$")


def _validate_target(target: str) -> str:
    """Validate an IP / hostname target. Returns cleaned target or raises."""
    target = target.strip()
    if not target or len(target) > 253:
        raise ValueError(f"Invalid target: empty or too long")
    if not _TARGET_RE.match(target):
        raise ValueError(
            f"Invalid target '{target}': must be a valid IPv4 address or hostname"
        )
    return target


def _validate_port(port: int) -> int:
    """Validate a TCP/UDP port number."""
    if not isinstance(port, int) or not (1 <= port <= 65535):
        raise ValueError(f"Invalid port {port}: must be integer 1-65535")
    return port


def _validate_filepath(path_str: str, must_exist: bool = False) -> Path:
    """Validate a file path string, preventing traversal."""
    path_str = path_str.strip()
    if not _SAFE_FILE_RE.match(Path(path_str).name):
        raise ValueError(f"Invalid filename: contains unsafe characters")
    p = Path(path_str)
    if must_exist and not p.exists():
        raise FileNotFoundError(f"File not found: {p}")
    return p


def _run_subprocess(cmd: list[str], timeout: int = DEFAULT_TIMEOUT) -> dict:
    """
    Run a command via subprocess with timeout and structured output.
    Returns a dict with returncode, stdout, stderr, and success flag.
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s",
        }
    except FileNotFoundError as e:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": f"Binary not found: {e}",
        }
    except Exception as e:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": f"Unexpected error: {e}",
        }


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def nmap_scan(
    target: str,
    ports: Optional[str] = None,
    scan_type: str = "-sV",
    timing: str = "-T4",
    output_file: Optional[str] = None,
    timeout: int = 300,
) -> dict:
    """
    Run an nmap scan against a target.

    Args:
        target: IP address or hostname to scan.
        ports: Port range (e.g. "80,443" or "1-1024"). Defaults to top 1000.
        scan_type: nmap scan type flag (e.g. "-sV", "-sC", "-A", "-sS").
        timing: Timing template (e.g. "-T1" through "-T5").
        output_file: Optional path to save XML output.
        timeout: Maximum seconds to wait for completion.

    Returns:
        dict with success, returncode, stdout, stderr.
    """
    target = _validate_target(target)

    # Validate scan_type and timing are safe flags
    safe_flags = {"-sS", "-sT", "-sU", "-sV", "-sC", "-A", "-O", "-sN", "-sF", "-sX"}
    if scan_type not in safe_flags:
        raise ValueError(f"Invalid scan_type '{scan_type}': must be one of {safe_flags}")

    safe_timing = {"-T0", "-T1", "-T2", "-T3", "-T4", "-T5"}
    if timing not in safe_timing:
        raise ValueError(f"Invalid timing '{timing}': must be one of {safe_timing}")

    cmd = ["nmap", scan_type, timing]

    if ports:
        # Validate port string: digits, commas, hyphens only
        if not re.match(r"^[\d,\-]+$", ports):
            raise ValueError(f"Invalid ports specification: '{ports}'")
        cmd.extend(["-p", ports])

    if output_file:
        output_path = _validate_filepath(output_file)
        cmd.extend(["-oX", str(output_path)])

    cmd.append(target)

    return _run_subprocess(cmd, timeout=timeout)


@mcp.tool()
def sqlmap_run(
    url: str,
    risk: int = 3,
    level: int = 5,
    batch: bool = True,
    dump: bool = False,
    timeout: int = 300,
) -> dict:
    """
    Run sqlmap against a target URL to detect and exploit SQL injection.

    Args:
        url: Target URL with parameter (e.g. "http://target.com/page?id=1").
        risk: Risk level (1-3).
        level: Level of tests (1-5).
        batch: Use batch mode (no interactive prompts).
        dump: Dump table entries after detection.
        timeout: Maximum seconds to wait.

    Returns:
        dict with success, returncode, stdout, stderr.
    """
    # Basic URL validation
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"URL must start with http:// or https://")
    if len(url) > 2048:
        raise ValueError("URL too long")

    if not (1 <= risk <= 3):
        raise ValueError(f"risk must be 1-3, got {risk}")
    if not (1 <= level <= 5):
        raise ValueError(f"level must be 1-5, got {level}")

    cmd = [
        "sqlmap",
        "-u", url,
        "--risk", str(risk),
        "--level", str(level),
        "--timeout", "30",
        "--retries", "2",
    ]
    if batch:
        cmd.append("--batch")
    if dump:
        cmd.append("--dump")

    return _run_subprocess(cmd, timeout=timeout)


@mcp.tool()
def gobuster_dir(
    target: str,
    wordlist: str = "/usr/share/wordlists/dirb/common.txt",
    extensions: Optional[str] = None,
    threads: int = 10,
    timeout: int = 300,
) -> dict:
    """
    Run gobuster directory brute-force against a web target.

    Args:
        target: Base URL (e.g. "http://target.com").
        wordlist: Path to wordlist file.
        extensions: Comma-separated extensions to check (e.g. "php,html,txt").
        threads: Number of concurrent threads.
        timeout: Maximum seconds to wait.

    Returns:
        dict with success, returncode, stdout, stderr.
    """
    target = target.strip()
    if not target.startswith(("http://", "https://")):
        raise ValueError(f"Target must start with http:// or https://")

    wordlist_path = _validate_filepath(wordlist, must_exist=True)

    if not (1 <= threads <= 100):
        raise ValueError(f"threads must be 1-100, got {threads}")

    cmd = [
        "gobuster", "dir",
        "-u", target,
        "-w", str(wordlist_path),
        "-t", str(threads),
    ]

    if extensions:
        if not re.match(r"^[A-Za-z0-9]+(,[A-Za-z0-9]+)*$", extensions):
            raise ValueError(f"Invalid extensions: '{extensions}'")
        cmd.extend(["-x", extensions])

    return _run_subprocess(cmd, timeout=timeout)


@mcp.tool()
def nikto_scan(
    target: str,
    port: int = 80,
    ssl: bool = False,
    timeout: int = 300,
) -> dict:
    """
    Run nikto web server scanner against a target.

    Args:
        target: Hostname or IP to scan.
        port: Target port.
        ssl: Use HTTPS.
        timeout: Maximum seconds to wait.

    Returns:
        dict with success, returncode, stdout, stderr.
    """
    target = _validate_target(target)
    port = _validate_port(port)

    cmd = ["nikto", "-h", target, "-p", str(port)]
    if ssl:
        cmd.append("-ssl")

    return _run_subprocess(cmd, timeout=timeout)


@mcp.tool()
def hydra_brute(
    target: str,
    service: str = "ssh",
    username: str = "root",
    password_file: str = "/usr/share/wordlists/rockyou.txt",
    port: Optional[int] = None,
    threads: int = 4,
    timeout: int = 300,
) -> dict:
    """
    Run hydra brute-force against a network service.

    Args:
        target: Target IP or hostname.
        service: Service to attack (e.g. "ssh", "ftp", "http-form-post").
        username: Username to target.
        password_file: Path to password wordlist.
        port: Override default service port.
        threads: Number of parallel threads (max 16).
        timeout: Maximum seconds to wait.

    Returns:
        dict with success, returncode, stdout, stderr.
    """
    target = _validate_target(target)

    # Whitelist of allowed services
    allowed_services = {
        "ssh", "ftp", "ftps", "telnet", "smb", "smtp", "pop3", "imap",
        "http-get", "http-post", "http-form-get", "http-form-post",
        "https-get", "https-post", "mysql", "mssql", "postgres", "rdp",
    }
    if service not in allowed_services:
        raise ValueError(f"Invalid service '{service}': must be one of {allowed_services}")

    # Validate username (no shell metacharacters)
    if not re.match(r"^[A-Za-z0-9._-]{1,64}$", username):
        raise ValueError(f"Invalid username: '{username}'")

    pw_path = _validate_filepath(password_file, must_exist=True)

    if not (1 <= threads <= 16):
        raise ValueError(f"threads must be 1-16, got {threads}")

    cmd = [
        "hydra",
        "-l", username,
        "-P", str(pw_path),
        "-t", str(threads),
        "-f",  # stop on first found
    ]

    if port:
        port = _validate_port(port)
        cmd.extend(["-s", str(port)])

    cmd.extend([target, service])

    return _run_subprocess(cmd, timeout=timeout)


@mcp.tool()
def john_hash(
    hash_file: str,
    wordlist: str = "/usr/share/wordlists/rockyou.txt",
    hash_format: Optional[str] = None,
    rules: Optional[str] = None,
    timeout: int = 300,
) -> dict:
    """
    Run John the Ripper against a file of password hashes.

    Args:
        hash_file: Path to file containing hashes (one per line).
        wordlist: Path to wordlist for dictionary attack.
        hash_format: Force hash format (e.g. "raw-md5", "sha512crypt").
        rules: Wordlist rules to apply (e.g. "Wordlist", "Single").
        timeout: Maximum seconds to wait.

    Returns:
        dict with success, returncode, stdout, stderr.
    """
    hash_path = _validate_filepath(hash_file, must_exist=True)
    wl_path = _validate_filepath(wordlist, must_exist=True)

    cmd = ["john", "--wordlist", str(wl_path)]

    if hash_format:
        # Validate format string (alphanumeric + hyphens)
        if not re.match(r"^[A-Za-z0-9_-]{1,64}$", hash_format):
            raise ValueError(f"Invalid hash_format: '{hash_format}'")
        cmd.extend(["--format", hash_format])

    if rules:
        allowed_rules = {"Wordlist", "Single", "KoreLogic", "All"}
        if rules not in allowed_rules:
            raise ValueError(f"Invalid rules '{rules}': must be one of {allowed_rules}")
        cmd.extend(["--rules", rules])

    cmd.append(str(hash_path))

    return _run_subprocess(cmd, timeout=timeout)


@mcp.tool()
def aircrack_suite(
    capture_file: str,
    wordlist: str = "/usr/share/wordlists/rockyou.txt",
    bssid: Optional[str] = None,
    essid: Optional[str] = None,
    timeout: int = 300,
) -> dict:
    """
    Run aircrack-ng against a WPA/WPA2 capture file.

    Args:
        capture_file: Path to .cap capture file.
        wordlist: Path to wordlist for cracking.
        bssid: Target BSSID (MAC address).
        essid: Target ESSID (network name).
        timeout: Maximum seconds to wait.

    Returns:
        dict with success, returncode, stdout, stderr.
    """
    cap_path = _validate_filepath(capture_file, must_exist=True)
    wl_path = _validate_filepath(wordlist, must_exist=True)

    cmd = ["aircrack-ng", "-w", str(wl_path)]

    if bssid:
        # Validate MAC address format
        if not re.match(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$", bssid):
            raise ValueError(f"Invalid BSSID MAC format: '{bssid}'")
        cmd.extend(["-b", bssid])

    if essid:
        if not re.match(r"^[A-Za-z0-9._ -]{1,32}$", essid):
            raise ValueError(f"Invalid ESSID: '{essid}'")
        cmd.extend(["-e", essid])

    cmd.append(str(cap_path))

    return _run_subprocess(cmd, timeout=timeout)


@mcp.tool()
def metasploit_console(
    module: str,
    options: Optional[dict] = None,
    action: str = "run",
    timeout: int = 300,
) -> dict:
    """
    Execute a Metasploit module via msfconsole in non-interactive mode.

    Args:
        module: Full module path (e.g. "exploit/multi/handler", "auxiliary/scanner/portscan/tcp").
        options: Dict of module options (e.g. {"RHOSTS": "10.0.0.1", "LHOST": "10.0.0.2"}).
        action: Action to perform ("run" or "exploit").
        timeout: Maximum seconds to wait.

    Returns:
        dict with success, returncode, stdout, stderr.
    """
    # Validate module path format
    if not re.match(r"^[A-Za-z0-9/._-]{1,128}$", module):
        raise ValueError(f"Invalid module path: '{module}'")

    if action not in ("run", "exploit"):
        raise ValueError(f"Invalid action '{action}': must be 'run' or 'exploit'")

    # Build msfconsole resource script commands
    lines = [f"use {module}"]
    if options:
        for key, value in options.items():
            # Validate option key (alphanumeric + underscore)
            if not re.match(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$", key):
                raise ValueError(f"Invalid option key: '{key}'")
            # Escape value for msfconsole
            escaped_value = str(value).replace('"', '\\"')
            lines.append(f'set {key} "{escaped_value}"')
    lines.append(action)
    lines.append("exit")

    cmd_input = "\n".join(lines)
    cmd = ["msfconsole", "-q", "-x", cmd_input]

    return _run_subprocess(cmd, timeout=timeout)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
