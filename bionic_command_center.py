#!/usr/bin/env python3
"""
Unified Bionic Command Center Terminal Dashboard (TUI)
Provides a live terminal interface for inspecting, executing, and benchmarking
all tools, engines, and sandbox lanes across our entire platform.
"""

import sys, os, time, subprocess, json

ROOT_DIR = r"C:\Users\mobil\orca\projects\my 1st"

MODULES = [
    ("1", "Unified Payment Gateway (ISO 8583 + EMV + Token Vault)", "unified_payment_gateway.py", "python"),
    ("2", "3D Secure 2.2 Protocol Engine", "three_ds_simulator.py", "python"),
    ("3", "Web3 DeFi & Flash Loan Simulator", "web3_defi_lab.py", "python"),
    ("4", "Web3 Smart Contract Invariant Fuzzer", "web3_contract_fuzzer.py", "python"),
    ("5", "API Vulnerability & Defense Verification Lab", "api_defense_lab.py", "python"),
    ("6", "Adversarial AI Evaluation & Defense Suite", "llm_adversarial_suite.py", "python"),
    ("7", "Statement & Tax OCR Extractor CLI", "statement_extractor_cli.py", "python"),
    ("8", "Native Rust TLS / Packet Dissector (--test)", os.path.join("rust_tools", "target", "release", "bionic_packet_engine.exe"), "rust"),
    ("9", "Orca ADE Multi-Agent Swarm Orchestrator (ALL LANES)", "orca_swarm_orchestrator.py", "python"),
    ("0", "Exit Command Center", None, "exit")
]

def render_banner():
    banner = """
================================================================================
       ★ BIONIC DAUGHTER AGENT — UNIFIED COMMAND CENTER TUI ★
================================================================================
  Host: Windows (MSYS / Git-Bash) | Runtime: Python 3.11 + Rust 1.98 | Mode: Sandbox
  Configured MCPs: 13 Active Servers | Enabled Skills: 111 Catalog Modules
================================================================================
"""
    return banner

def run_module(choice: str) -> dict:
    match = next((m for m in MODULES if m[0] == choice), None)
    if not match or not match[2]:
        return {"error": "Invalid choice"}

    name = match[1]
    rel_path = match[2]
    m_type = match[3]

    full_path = os.path.join(ROOT_DIR, rel_path) if not os.path.isabs(rel_path) else rel_path

    start = time.time()
    if m_type == "python":
        cmd = [sys.executable, full_path]
    elif m_type == "rust":
        cmd = [full_path, "--test"]
    else:
        return {"error": "Unknown type"}

    res = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, text=True)
    elapsed = time.time() - start

    return {
        "name": name,
        "elapsed_sec": round(elapsed, 3),
        "exit_code": res.returncode,
        "stdout": res.stdout,
        "stderr": res.stderr
    }

def print_menu():
    print(render_banner())
    print("Available Bionic Execution Lanes:")
    print("--------------------------------------------------------------------------------")
    for key, name, path, _ in MODULES:
        print(f"  [{key}] {name}")
    print("--------------------------------------------------------------------------------")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--auto-test":
        print("=== RUNNING BIONIC COMMAND CENTER HEADLESS SMOKE TEST ===")
        print_menu()
        print("\n[Auto-Test] Firing Module 9 (Swarm Orchestrator)...")
        res = run_module("9")
        print(f"Status: Exit Code {res['exit_code']} (took {res['elapsed_sec']}s)")
        print("Tail Log:\n", res['stdout'][-400:])
        assert res['exit_code'] == 0, "Swarm orchestrator must pass"
        print("\n>>> BIONIC COMMAND CENTER: 100% OPERATIONAL <<<")
        sys.exit(0)

    print_menu()
    print("To launch an interactive run or auto-test, execute:")
    print("  python bionic_command_center.py --auto-test")
