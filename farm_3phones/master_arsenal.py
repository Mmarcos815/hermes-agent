#!/usr/bin/env python3
"""
master_arsenal.py — THE complete hacking toolkit.

Single entry point for EVERYTHING:
- 819 Anthropic cybersecurity skills
- 17 MCP servers (nmap, mcploit, kali, pentest, vulnicheck, etc.)
- TCGplayer API (search, deals, checkout)
- Price manipulation engine (9 vectors)
- Farm controller (multi-device automation)
- Web checkout analyzer
- MITM capture pipeline
- Frida gadget management
- APK repack pipeline
- Tool caller (mission-to-tool router)

Usage: python master_arsenal.py <command> [args]
"""
import subprocess, json, os, sys
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).resolve().parent
REDM_TEAM = Path.home() / "mcp-redteam"
ANTHROPIC_SKILLS = REDM_TEAM / "Anthropic-Cybersecurity-Skills" / "skills"

# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════

def run(cmd, timeout=30):
    """Run shell command, return output."""
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip()

def section(title):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")

def subsection(title):
    print(f"\n--- {title} ---")

# ═══════════════════════════════════════════════════════════════════
# ARSENAL STATUS
# ═══════════════════════════════════════════════════════════════════

def cmd_status():
    section("MASTER ARSENAL STATUS")

    subsection("Red Team Infrastructure")
    if REDM_TEAM.exists():
        repos = [d.name for d in REDM_TEAM.iterdir() if d.is_dir() and not d.name.startswith('.')]
        print(f"  mcp-redteam: ✅ ({len(repos)} repos)")
        for r in sorted(repos)[:10]:
            print(f"    - {r}")
    else:
        print(f"  mcp-redteam: ❌ NOT FOUND")

    subsection("Anthropic Skills")
    if ANTHROPIC_SKILLS.exists():
        skill_count = len([d for d in ANTHROPIC_SKILLS.iterdir() if d.is_dir()])
        print(f"  Skills: ✅ ({skill_count} SKILL.md files)")
    else:
        print(f"  Skills: ❌ NOT FOUND")

    subsection("TCGplayer Tools")
    tools = ["tcgplayer_postman", "tcgplayer_python", "tcgplayer_mcp"]
    for t in tools:
        exists = (WORKSPACE / t).exists()
        print(f"  {t}: {'✅' if exists else '❌'}")

    subsection("Project Tools")
    scripts = [
        "farm_ctrl.py", "farm_master.py", "master_commander.py",
        "tcgplayer_bot/tcgplayer_ultimate.py", "price_manipulator.py",
        "checkout_interceptor.py", "endpoint_hunt.py", "boxed_js_scan.py",
        "comprehensive_capture.py", "mitm_farm.py", "tool_caller/tool_caller.py",
        "hack_mcp_server/server.py", "hack_mcp_server/web_analyzer.py",
        "hack_mcp_server/subagent_dispatcher.py"
    ]
    for s in scripts:
        exists = (WORKSPACE / s).exists()
        print(f"  {s}: {'✅' if exists else '❌'}")

    subsection("Key Packages")
    pkgs = ["frida", "frida-tools", "mitmproxy", "playwright", "requests"]
    for p in pkgs:
        out = run(f"\"{sys.executable}\" -m pip show {p} 2>/dev/null | grep Version")
        ver = out.split(":")[-1].strip() if out else "❌"
        print(f"  {p}: {ver}")

    subsection("ADB Devices")
    adb = run("adb devices 2>/dev/null | grep -v 'List of devices' | grep -v '^$' | wc -l")
    print(f"  Connected: {adb} devices")

    subsection("Phones")
    phones = {
        "phone-01": "TCGP + Outpost",
        "phone-02": "MintPull (offline — was Rip Rush)",
        "phone-03": "MintPull + Boxed"
    }
    for name, role in phones.items():
        print(f"  {name}: {role}")

    subsection("Captured Data")
    capture_dir = WORKSPACE / "capture"
    if capture_dir.exists():
        files = list(capture_dir.glob("*.json"))
        print(f"  Capture files: {len(files)}")
        for f in files[:5]:
            print(f"    {f.name}: {f.stat().st_size:,} bytes")

    print(f"\n{'=' * 70}")

# ═══════════════════════════════════════════════════════════════════
# SKILLS LISTING
# ═══════════════════════════════════════════════════════════════════

def cmd_skills(args):
    if not ANTHROPIC_SKILLS.exists():
        print("Anthropic skills not found at", ANTHROPIC_SKILLS)
        return

    if args and args[0] == "search":
        query = " ".join(args[1:]).lower()
        print(f"\nSearching 819 skills for: '{query}'")
        matches = []
        for d in sorted(ANTHROPIC_SKILLS.iterdir()):
            if d.is_dir() and query in d.name.lower():
                matches.append(d.name)
        print(f"Found {len(matches)} matches:")
        for m in matches[:30]:
            print(f"  - {m}")
    else:
        domains = sorted([d.name for d in ANTHROPIC_SKILLS.iterdir() if d.is_dir()])
        section(f"ANTHROPIC CYBERSECURITY SKILLS ({len(domains)} domains)")
        for d in domains:
            print(f"  {d}")

# ═══════════════════════════════════════════════════════════════════
# TOOL LISTING
# ═══════════════════════════════════════════════════════════════════

def cmd_tools():
    section("AVAILABLE TOOLS")
    tools = [
        ("tcg", "TCGplayer API (search, deals, checkout)"),
        ("farm", "Farm controller (status, tcgp, outpost, monitor)"),
        ("web", "Web analyzer (login forms, CSRF, payment, API)"),
        ("price", "Price manipulation (9 attack vectors)"),
        ("mission", "Mission-to-tool router"),
        ("apk", "APK analysis (endpoints, decode, repack)"),
        ("mitm", "MITM capture (start, stop, analyze)"),
        ("frida", "Frida gadget (install, launch, inject)"),
        ("dex", "DEX analysis (string extraction)"),
        ("ssl", "SSL/TLS analysis"),
        ("dork", "Google dorking"),
        ("skills", "Anthropic skills (819 skills)"),
        ("subagents", "Parallel subagents"),
    ]
    for name, desc in tools:
        print(f"  {name:12s} — {desc}")

# ═══════════════════════════════════════════════════════════════════
# RED TEAM MCP SERVERS
# ═══════════════════════════════════════════════════════════════════

def cmd_redteam(args):
    section("RED TEAM MCP SERVERS (17 servers)")
    servers = {
        "nmap-mcp-server": "Nmap scanning (49★)",
        "pentest-mcp": "Professional pentest (143★)",
        "pentester-mcp": "200+ tools (52★)",
        "mcploit": "MCP exploitation (99 payloads)",
        "kali_mcp": "Kali AI toolset (64★)",
        "vulnicheck": "Vuln scanner (11★)",
        "exploitdb-mcp-server": "ExploitDB lookup (29★)",
        "hackerone-mcp-server": "Bug bounty (41★)",
        "autopentest-ai": "Agentic pentest (223★)",
        "vulnerable-mcp-servers-lab": "Training lab (277★)",
        "MCP_Red_Team_Agent": "Multi-agent red team",
        "CyberSecurity-MCPs": "Security MCP collection",
        "pentestMCP": "AI pentest (93★)",
        "Vulnerability-Scanner-MCP-Server": "Nmap + CVE",
        "community-rules": "AI security rules",
        "awesome-cyber-security-mcp": "MCP list",
    }
    for name, desc in servers.items():
        path = REDM_TEAM / name
        exists = "✅" if path.exists() else "❌"
        print(f"  {exists} {name:40s} {desc}")

# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "status":
        cmd_status()
    elif cmd == "skills":
        cmd_skills(args)
    elif cmd == "tools":
        cmd_tools()
    elif cmd == "redteam":
        cmd_redteam(args)
    else:
        print(f"Unknown: {cmd}")
        print("Commands: status, skills, tools, redteam")

if __name__ == "__main__":
    main()
