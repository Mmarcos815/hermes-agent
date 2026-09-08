#!/usr/bin/env python3
# ============================================================================
# BIONIC DAUGHTER v1 — HEXSTRIKE AI INTEGRATION MODULE
# ============================================================================
# Integrates the daughter with HexStrike AI — a multi-agent pentesting
# framework that connects AI (Claude, GPT, Copilot) to 150+ cybersecurity
# tools for automated penetration testing, vulnerability discovery, and
# CTF challenge solving.
#
# HexStrike AI capabilities:
#   - 150+ security tools (nmap, sqlmap, gobuster, hydra, john, gdb, etc.)
#   - Multi-agent architecture with autonomous AI agents
#   - Intelligent tool selection and attack chain construction
#   - CTF workflow manager (24x faster than manual)
#   - Bug bounty workflow automation
#   - Network recon, web app security, password cracking, binary analysis
#
# HexStrike AI MCP server:
#   github.com/b-bogus/hexstrike-ai_mcp_server
#   Exposes 150+ security tools through MCP protocol
#
# USAGE:
#   from daughter_hexstrike import HexstrikeIntegration
#   hex = HexstrikeIntegration()
#   hex.initialize()  # Check prerequisites
#   result = hex.run_recon(target="example.com")
#   result = hex.run_vuln_scan(target="example.com", tool="nuclei")
#   result = hex.run_sqlmap(target="http://example.com/vuln.php?id=1")
#   result = hex.run_ctf_workflow(challenge_name="easybox", category="web")
#
# PREREQUISITES:
#   - HexStrike AI installed (pip install hexstrike-ai or from GitHub)
#   - Security tools installed (nmap, sqlmap, gobuster, nuclei, etc.)
#   - OR: hexstrike-ai MCP server running and accessible
#   - Authorization: only run against targets you have permission to test
#
# AUTHORIZATION GATE:
#   Every HexStrike operation requires explicit target authorization.
#   The daughter will NOT run hexstrike against any target without
#   documented authorization (scope, written permission, or owned system).
# ============================================================================

import os
import sys
import json
import subprocess
import logging
import re
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DaughterHexstrike")

PROJECT_DIR = Path(__file__).parent

# Authorization tracking — every target must be authorized
AUTHORIZED_TARGETS = PROJECT_DIR / "data" / "authorized_targets.json"

# ============================================================================
# HEXSTRIKE INTEGRATION
# ============================================================================

class HexstrikeIntegration:
    """
    Integrates the Bionic Daughter with HexStrike AI for automated
    penetration testing, vulnerability discovery, and CTF challenge solving.
    """

    def __init__(self):
        self.authorized_targets = {}
        self._load_authorized_targets()
        self.hexstrike_available = False
        self.mcp_server_available = False
        self._check_prerequisites()

    # ------------------------------------------------------------------
    # INITIALIZATION & PREREQUISITES
    # ------------------------------------------------------------------

    def _load_authorized_targets(self):
        """Load authorized targets from file."""
        if AUTHORIZED_TARGETS.exists():
            try:
                with open(AUTHORIZED_TARGETS) as f:
                    self.authorized_targets = json.load(f)
                logger.info(f"Loaded {len(self.authorized_targets)} authorized targets.")
            except Exception as e:
                logger.warning(f"Failed to load authorized targets: {e}")
                self.authorized_targets = {}
        else:
            logger.info("No authorized targets file — all operations require explicit authorization.")

    def _check_prerequisites(self):
        """Check if HexStrike AI and required tools are available."""
        # Check if hexstrike-ai Python package is installed
        try:
            import hexstrike_ai
            logger.info("hexstrike-ai Python package available.")
            self.hexstrike_available = True
        except ImportError:
            logger.info("hexstrike-ai Python package not installed.")
            self.hexstrike_available = False

        # Check if hexstrike MCP server is configured
        # (look for it in MCP config or running processes)
        try:
            result = subprocess.run(
                ["pgrep", "-f", "hexstrike"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                logger.info("HexStrike MCP server process detected.")
                self.mcp_server_available = True
        except:
            pass

        # Check for common security tools
        tools_to_check = ["nmap", "sqlmap", "gobuster", "nuclei", "hydra", "masscan"]
        available_tools = []
        for tool in tools_to_check:
            try:
                result = subprocess.run(
                    ["which", tool], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    available_tools.append(tool)
            except:
                pass
        logger.info(f"Available security tools: {available_tools}")

        return {
            "hexstrike_package": self.hexstrike_available,
            "hexstrike_mcp": self.mcp_server_available,
            "available_tools": available_tools,
        }

    # ------------------------------------------------------------------
    # AUTHORIZATION
    # ------------------------------------------------------------------

    def authorize_target(self, target, justification, scope=None, owner=None, expires=None):
        """
        Authorize a target for testing.

        Args:
            target: str — hostname, IP, or range to authorize
            justification: str — reason for testing (owned system, written permission, bug bounty scope)
            scope: str (optional) — specific scope restrictions
            owner: str (optional) — owner of the target
            expires: str (optional) — ISO date when authorization expires

        Returns:
            dict with authorization record
        """
        auth_record = {
            "target": target,
            "justification": justification,
            "scope": scope or "full",
            "owner": owner or "self",
            "authorized_by": "BionicDaughter",
            "authorized_at": datetime.now().isoformat(),
            "expires": expires,
            "operations_performed": [],
        }

        self.authorized_targets[target] = auth_record
        self._save_authorized_targets()

        logger.info(f"Target authorized: {target} — {justification[:80]}")
        return auth_record

    def is_authorized(self, target):
        """Check if a target is authorized for testing."""
        # Normalize target
        target = target.lower().strip()

        # Check exact match
        if target in self.authorized_targets:
            auth = self.authorized_targets[target]
            # Check expiration
            if auth.get("expires"):
                try:
                    expire_date = datetime.fromisoformat(auth["expires"])
                    if expire_date < datetime.now():
                        logger.warning(f"Authorization expired for: {target}")
                        return False
                except:
                    pass
            return True

        # Check if target is within an authorized range
        for authorized_target, auth in self.authorized_targets.items():
            if self._target_in_scope(target, authorized_target, auth.get("scope", "full")):
                return True

        return False

    def _target_in_scope(self, target, authorized_pattern, scope):
        """Check if a target falls within an authorized scope."""
        # Simple string matching for hostnames/IPs
        if authorized_pattern in target or target in authorized_pattern:
            return True

        # CIDR or range matching would go here (simplified for now)
        return False

    def _save_authorized_targets(self):
        """Save authorized targets to file."""
        AUTHORIZED_TARGETS.parent.mkdir(parents=True, exist_ok=True)
        with open(AUTHORIZED_TARGETS, "w") as f:
            json.dump(self.authorized_targets, f, indent=2)

    # ------------------------------------------------------------------
    # HEXSTRIKE OPERATIONS
    # ------------------------------------------------------------------

    def run_recon(self, target, tool="nmap", options=None):
        """
        Run reconnaissance on an authorized target.

        Args:
            target: str — hostname or IP
            tool: str — recon tool (nmap, masscan, rustscan, amass, subfinder)
            options: str (optional) — additional tool options

        Returns:
            dict with operation result
        """
        if not self.is_authorized(target):
            return {"status": "denied", "error": f"Target not authorized: {target}"}

        logger.info(f"Running recon on {target} with {tool}")

        cmd_map = {
            "nmap": f"nmap -sV -sC -O -p- {target}",
            "masscan": f"masscan {target} -p-- --rate 1000",
            "rustscan": f"rustscan -a {target} --top-ports 1000 -- -sV -sC",
            "amass": f"amass enum -d {target}",
            "subfinder": f"subfinder -d {target}",
            "theharvester": f"theharvester -d {target} -b all",
        }

        cmd = cmd_map.get(tool, f"{tool} {target}")
        if options:
            cmd += f" {options}"

        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=300
            )
            output = result.stdout + result.stderr
            status = "success" if result.returncode == 0 else "failed"

            # Record operation
            if target in self.authorized_targets:
                self.authorized_targets[target]["operations_performed"].append({
                    "operation": "recon",
                    "tool": tool,
                    "timestamp": datetime.now().isoformat(),
                    "status": status,
                })
                self._save_authorized_targets()

            return {
                "status": status,
                "tool": tool,
                "target": target,
                "output_preview": output[:2000],
                "exit_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": "Operation timed out after 5 minutes"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def run_vuln_scan(self, target, tool="nuclei", options=None):
        """
        Run vulnerability scanning on an authorized target.

        Args:
            target: str — URL or IP
            tool: str — vuln scanner (nuclei, nikto, wpscan, dirsearch, ffuf)
            options: str (optional) — additional options

        Returns:
            dict with scan results
        """
        if not self.is_authorized(target):
            return {"status": "denied", "error": f"Target not authorized: {target}"}

        logger.info(f"Running vuln scan on {target} with {tool}")

        cmd_map = {
            "nuclei": f"nuclei -u {target} -t default -json -o /tmp/nuclei_results.json",
            "nikto": f"nikto -h {target}",
            "wpscan": f"wpscan --url {target} --enumerate vp",
            "dirsearch": f"dirsearch -u {target} -e php,html,asp,aspx,json",
            "ffuf": f"ffuf -u {target}/FUZZ -w /usr/share/wordlists/dirb/common.txt",
            "httpx": f"httpx -l targets.txt -o alive.txt -silent",
        }

        cmd = cmd_map.get(tool, f"{tool} {target}")
        if options:
            cmd += f" {options}"

        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=300
            )
            output = result.stdout + result.stderr

            return {
                "status": "success" if result.returncode == 0 else "completed",
                "tool": tool,
                "target": target,
                "output_preview": output[:2000],
                "exit_code": result.returncode,
                "findings": self._parse_vuln_findings(output, tool),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _parse_vuln_findings(self, output, tool):
        """Parse tool output for vulnerability findings."""
        findings = []

        if tool == "nuclei" and output:
            # Nuclei JSON output parsing
            try:
                for line in output.strip().split("\n"):
                    if line:
                        finding = json.loads(line)
                        findings.append({
                            "template": finding.get("template", "unknown"),
                            "severity": finding.get("info", {}).get("severity", "unknown"),
                            "url": finding.get("matched", "unknown"),
                            "description": finding.get("info", {}).get("description", "")[:200],
                        })
            except:
                pass

        if tool == "nikto" and output:
            for line in output.split("\n"):
                if "OSVDB" in line or "ni" in line.lower():
                    findings.append({"raw": line.strip()[:200]})

        return findings

    def run_sqlmap(self, url, options=None, risk=1, level=1):
        """
        Run SQLMap against an authorized target URL.

        Args:
            url: str — target URL with parameter (e.g., http://example.com/page?id=1)
            options: str (optional) — additional sqlmap options
            risk: int (1-3) — detection risk level
            level: int (1-5) — test depth level

        Returns:
            dict with SQL injection test results
        """
        if not self.is_authorized(url):
            return {"status": "denied", "error": f"Target not authorized: {url}"}

        logger.info(f"Running sqlmap on {url}")

        cmd = f"sqlmap -u '{url}' --risk={risk} --level={level} --batch"
        if options:
            cmd += f" {options}"

        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=600
            )
            output = result.stdout + result.stderr

            # Parse for injection results
            injection_found = any(kw in output.lower() for kw in [
                "sql injection", "injectable", "parameter", "back-end", "database"
            ])

            return {
                "status": "completed",
                "target": url,
                "output_preview": output[:2000],
                "injection_detected": injection_found,
                "exit_code": result.returncode,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def run_password_test(self, target, tool="hydra", service="ssh", username=None, password_file=None):
        """
        Run password testing on an authorized target.

        Args:
            target: str — hostname or IP
            tool: str — password tool (hydra, john, hashcat, medusa)
            service: str — service to test (ssh, ftp, smb, http, mysql)
            username: str (optional) — username to test
            password_file: str (optional) — path to password wordlist

        Returns:
            dict with password test results
        """
        if not self.is_authorized(target):
            return {"status": "denied", "error": f"Target not authorized: {target}"}

        logger.info(f"Running password test on {target}:{service} with {tool}")

        wordlist = password_file or "/usr/share/wordlists/rockyou.txt"

        cmd_map = {
            "hydra": f"hydra -l {username or 'admin'} -P {wordlist} {target} {service}",
            "medusa": f"medusa -h {target} -u {username or 'admin'} -P {wordlist} -M {service}",
        }

        cmd = cmd_map.get(tool, f"{tool} {target}")
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=300
            )
            output = result.stdout + result.stderr

            # Check for successful login
            success_found = any(kw in output.lower() for kw in [
                "login successful", "access granted", "password found", "accepted"
            ])

            return {
                "status": "completed",
                "target": target,
                "service": service,
                "output_preview": output[:1000],
                "credentials_found": success_found,
                "exit_code": result.returncode,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def run_ctf_workflow(self, challenge_name, category="web", approach="automated"):
        """
        Run a CTF challenge solving workflow using HexStrike AI concepts.

        Args:
            challenge_name: str — name/identifier of the CTF challenge
            category: str — CTF category (web, pwn, crypto, rev, forensics, misc)
            approach: str — "automated" (HexStrike tools) or "manual" (guided analysis)

        Returns:
            dict with workflow plan and tool recommendations
        """
        logger.info(f"CTF workflow for {challenge_name} ({category})")

        # Tool recommendations by category
        category_tools = {
            "web": ["nmap", "gobuster", "dirsearch", "ffuf", "sqlmap", "burpsuite", "nuclei"],
            "pwn": ["gdb", "pwntools", "checksec", "radare2", "retseverter", "one_gadget"],
            "crypto": ["cyberchef", "openssl", "python", "hashcat", "secrets"],
            "rev": ["ghidra", "radare2", "gdb", "strings", "binwalk", "pwntools"],
            "forensics": ["volatility3", "foremost", "strings", "exiftool", "steghide", "binwalk"],
            "misc": ["python", "cyberchef", "base64", "strings", "file"],
        }

        recommended_tools = category_tools.get(category, ["python", "cyberchef"])

        workflow = {
            "challenge": challenge_name,
            "category": category,
            "approach": approach,
            "recommended_tools": recommended_tools,
            "workflow_steps": self._generate_ctf_workflow(category, approach),
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(f"CTF workflow generated: {len(recommended_tools)} tools recommended")
        return workflow

    def _generate_ctf_workflow(self, category, approach):
        """Generate a CTF solving workflow for a category."""
        workflows = {
            "web": [
                {"step": 1, "action": "Reconnaissance", "tools": ["nmap", "gobuster", "subfinder"], "description": "Enumerate subdomains, endpoints, and technologies"},
                {"step": 2, "action": "Enumeration", "tools": ["dirsearch", "ffuf", "nikto"], "description": "Discover hidden directories, files, and parameters"},
                {"step": 3, "action": "Vulnerability Analysis", "tools": ["sqlmap", "nuclei", "burpsuite"], "description": "Test for SQLi, XSS, CSRF, misconfigurations"},
                {"step": 4, "action": "Exploitation", "tools": ["sqlmap", "custom_payloads"], "description": "Develop and test exploit for confirmed vulnerabilities"},
                {"step": 5, "action": "Flag Capture", "tools": ["python", "manual"], "description": "Extract flag from exploited system"},
            ],
            "pwn": [
                {"step": 1, "action": "Binary Analysis", "tools": ["checksec", "file", "strings"], "description": "Analyze binary properties, protections, and strings"},
                {"step": 2, "action": "Reverse Engineering", "tools": ["gdb", "radare2", "pwntools"], "description": "Understand program logic and find vulnerability"},
                {"step": 3, "action": "Exploit Development", "tools": ["pwntools", "one_gadget", "retseverter"], "description": "Develop ROP chain or buffer overflow exploit"},
                {"step": 4, "action": "Exploitation", "tools": ["pwntools", "gdb"], "description": "Execute exploit against target binary"},
                {"step": 5, "action": "Flag Capture", "tools": ["pwntools"], "description": "Read flag from exploited process memory or file system"},
            ],
            "crypto": [
                {"step": 1, "action": "Cipher Identification", "tools": ["cyberchef", "file"], "description": "Identify encryption/cipher type from ciphertext"},
                {"step": 2, "action": "Analysis", "tools": ["python", "cyberchef"], "description": "Analyze patterns, key space, and weaknesses"},
                {"step": 3, "action": "Decryption", "tools": ["python", "openssl", "hashcat"], "description": "Decrypt ciphertext using discovered weakness or key"},
                {"step": 4, "action": "Flag Capture", "tools": ["python"], "description": "Extract flag from decrypted plaintext"},
            ],
            "rev": [
                {"step": 1, "action": "Initial Analysis", "tools": ["file", "strings", "binwalk"], "description": "Identify file type, extract strings, find embedded data"},
                {"step": 2, "action": "Disassembly", "tools": ["ghidra", "radare2"], "description": "Decompile and analyze binary logic"},
                {"step": 3, "action": "Vulnerability Discovery", "tools": ["ghidra", "manual"], "description": "Find logic bugs, backdoors, weak crypto"},
                {"step": 4, "action": "Exploitation", "tools": ["python", "gdb"], "description": "Exploit discovered vulnerability"},
                {"step": 5, "action": "Flag Capture", "tools": ["python"], "description": "Extract flag"},
            ],
            "forensics": [
                {"step": 1, "action": "File Analysis", "tools": ["file", "strings", "exiftool"], "description": "Analyze file metadata and extract strings"},
                {"step": 2, "action": "Steganography Check", "tools": ["steghide", "stegsolve", "binwalk"], "description": "Check for hidden data in images/files"},
                {"step": 3, "action": "Memory/Disk Analysis", "tools": ["volatility3", "foremost"], "description": "Analyze memory dumps or disk images"},
                {"step": 4, "action": "Data Extraction", "tools": ["python", "manual"], "description": "Extract and reconstruct hidden data"},
                {"step": 5, "action": "Flag Capture", "tools": ["python"], "description": "Find and decode the flag"},
            ],
        }

        return workflows.get(category, [{"step": 1, "action": "Analyze", "tools": ["python"], "description": "Understand the challenge"}])

    # ------------------------------------------------------------------
    # BUG BOUNTY WORKFLOW
    # ------------------------------------------------------------------

    def run_bug_bounty_workflow(self, target, scope, program="hackerone"):
        """
        Run a bug bounty reconnaissance and discovery workflow.

        Args:
            target: str — target domain (must be in bug bounty scope)
            scope: str — scope description (e.g., "*.target.com")
            program: str — platform (hackerone, bugcrowd, intigriti)

        Returns:
            dict with workflow and findings
        """
        # Check authorization — bug bounty targets MUST be in scope
        if not self.is_authorized(target):
            return {"status": "denied", "error": f"Target not in authorized scope: {target}. Add to authorized_targets.json with bug bounty program justification."}

        logger.info(f"Bug bounty workflow for {target} on {program}")

        workflow = {
            "target": target,
            "program": program,
            "scope": scope,
            "timestamp": datetime.now().isoformat(),
            "steps": [
                {"step": "1. Subdomain Enumeration", "tools": ["subfinder", "amass", "assetfinder"], "description": "Find all subdomains in scope"},
                {"step": "2. Port Scanning", "tools": ["nmap", "masscan"], "description": "Identify open ports and services"},
                {"step": "3. Web Discovery", "tools": ["gobuster", "dirsearch", "waybackurls"], "description": "Discover endpoints, directories, and parameters"},
                {"step": "4. Technology Fingerprinting", "tools": ["httpx", "wappalyzer"], "description": "Identify tech stack, frameworks, CMS"},
                {"step": "5. Vulnerability Scanning", "tools": ["nuclei", "nikto"], "description": "Automated vulnerability detection"},
                {"step": "6. Manual Testing Focus Areas", "tools": ["manual"], "description": "API endpoints, auth flows, file uploads, business logic"},
                {"step": "7. Report Generation", "tools": ["python"], "description": "Document findings with PoC and risk rating"},
            ],
            "status": "ready",
        }

        return workflow

    # ------------------------------------------------------------------
    # REPORTING
    # ------------------------------------------------------------------

    def generate_report(self, operations):
        """
        Generate a summary report from multiple HexStrike operations.

        Args:
            operations: list of operation result dicts

        Returns:
            dict with summary report
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_operations": len(operations),
            "operations": [],
            "summary": {
                "successful": sum(1 for op in operations if op.get("status") in ("success", "completed")),
                "failed": sum(1 for op in operations if op.get("status") in ("failed", "error", "denied")),
                "targets": list(set(op.get("target", "unknown") for op in operations)),
            }
        }

        for op in operations:
            report["operations"].append({
                "tool": op.get("tool", "unknown"),
                "target": op.get("target", "unknown"),
                "status": op.get("status", "unknown"),
                "findings": op.get("findings", []),
                "injection_detected": op.get("injection_detected", False),
                "credentials_found": op.get("credentials_found", False),
            })

        return report

# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    hex = HexstrikeIntegration()

    print("=== HexStrike Integration Status ===")
    print(f"HexStrike package: {hex.hexstrike_available}")
    print(f"HexStrike MCP server: {hex.mcp_server_available}")
    print(f"Authorized targets: {len(hex.authorized_targets)}")

    # Test authorization flow
    print("\n=== Authorization Test ===")
    auth = hex.authorize_target(
        "192.168.1.0/24",
        "Owned home lab network for security training",
        scope="192.168.1.0/24",
        owner="self",
    )
    print(f"Authorized: {auth['target']} — {auth['justification']}")

    print(f"\nIs 192.168.1.5 authorized? {hex.is_authorized('192.168.1.5')}")
    print(f"Is 10.0.0.1 authorized? {hex.is_authorized('10.0.0.1')}")

    # Test CTF workflow generation
    print("\n=== CTF Workflow Test ===")
    ctf = hex.run_ctf_workflow("EasyWebChallenge", category="web")
    print(f"Challenge: {ctf['challenge']}")
    print(f"Category: {ctf['category']}")
    print(f"Tools: {', '.join(ctf['recommended_tools'])}")
    print(f"Steps: {len(ctf['workflow_steps'])}")

    for step in ctf["workflow_steps"]:
        print(f"  Step {step['step']}: {step['action']} — {step['description']}")
        print(f"    Tools: {', '.join(step['tools'])}")

    # Test bug bounty workflow
    print("\n=== Bug Bounty Workflow Test ===")
    # First authorize the bug bounty target
    hex.authorize_target(
        "example.com",
        "HackerOne bug bounty program — scope includes *.example.com",
        scope="*.example.com",
        program="hackerone",
    )
    bb = hex.run_bug_bounty_workflow("example.com", "*.example.com")
    print(f"Target: {bb['target']}")
    print(f"Program: {bb['program']}")
    print(f"Steps: {len(bb['steps'])}")
