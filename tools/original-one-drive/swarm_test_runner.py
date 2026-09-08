#!/usr/bin/env python3
"""
Multi-Agent Sandbox Swarm Runner
Coordinates parallel worker lanes to execute, test, and stress-test
all built tools and engines in our workspace.
"""

import sys, os, time, json, concurrent.futures
import subprocess

ROOT_DIR = r"C:\Users\mobil\orca\projects\my 1st"

def run_lane_payment():
    """Worker Lane 1: Payment Rails Switch (ISO 8583 + EMV + Token Vault)"""
    start = time.time()
    script_path = os.path.join(ROOT_DIR, "unified_payment_gateway.py")
    res = subprocess.run([sys.executable, script_path], cwd=ROOT_DIR, capture_output=True, text=True)
    elapsed = time.time() - start
    return {
        "lane": "Payment Rails Engine",
        "command": "unified_payment_gateway.py",
        "exit_code": res.returncode,
        "elapsed_sec": round(elapsed, 3),
        "status": "PASS" if res.returncode == 0 and "ALL TESTS PASSED" in res.stdout else "FAIL",
        "output_tail": res.stdout.strip().split("\n")[-1] if res.stdout else res.stderr
    }

def run_lane_rust():
    """Worker Lane 2: Native Rust FastMCP Packet Engine"""
    start = time.time()
    rust_bin = os.path.join(ROOT_DIR, "rust_tools", "target", "release", "bionic_packet_engine.exe")
    if not os.path.exists(rust_bin):
        return {"lane": "Rust Native Engine", "status": "FAIL", "elapsed_sec": 0.0, "output_tail": f"Binary not found: {rust_bin}"}
    
    res = subprocess.run([rust_bin, "--test"], cwd=ROOT_DIR, capture_output=True, text=True)
    elapsed = time.time() - start
    return {
        "lane": "Rust Native Engine",
        "command": "bionic_packet_engine.exe --test",
        "exit_code": res.returncode,
        "elapsed_sec": round(elapsed, 3),
        "status": "PASS" if res.returncode == 0 and "100% PASS" in res.stdout else "FAIL",
        "output_tail": res.stdout.strip().split("\n")[-1] if res.stdout else res.stderr
    }

def run_lane_security_audit():
    """Worker Lane 3: HexStrike Live Port & Security Header Auditor"""
    start = time.time()
    script = (
        "import sys\n"
        "sys.path.insert(0, r'C:\\Users\\mobil\\orca\\projects\\my 1st')\n"
        "from hexstrike_live_server import live_http_audit, live_port_scan\n"
        "res1 = live_port_scan('127.0.0.1', ports='80,443,8080')\n"
        "res2 = live_http_audit('https://example.com')\n"
        "print('PORT_SCAN_OK' if 'scanned_ports_count' in res1 else 'FAIL')\n"
        "print('HTTP_AUDIT_OK' if 'security_headers' in res2 else 'FAIL')\n"
    )
    res = subprocess.run([sys.executable, "-c", script], cwd=ROOT_DIR, capture_output=True, text=True)
    elapsed = time.time() - start
    passed = res.returncode == 0 and "PORT_SCAN_OK" in res.stdout and "HTTP_AUDIT_OK" in res.stdout
    return {
        "lane": "HexStrike Security Prober",
        "command": "hexstrike_live_server.py",
        "exit_code": res.returncode,
        "elapsed_sec": round(elapsed, 3),
        "status": "PASS" if passed else "FAIL",
        "output_tail": "Both Port Scan & HTTP Audit Validated" if passed else res.stderr
    }

def run_lane_ocr():
    """Worker Lane 4: Financial Table Extraction & Ledger Reconciler"""
    start = time.time()
    script_path = os.path.join(ROOT_DIR, "financial_table_extractor.py")
    res = subprocess.run([sys.executable, script_path], cwd=ROOT_DIR, capture_output=True, text=True)
    elapsed = time.time() - start
    passed = res.returncode == 0 and "parsed_transactions_count" in res.stdout
    return {
        "lane": "Document & Financial OCR",
        "command": "financial_table_extractor.py",
        "exit_code": res.returncode,
        "elapsed_sec": round(elapsed, 3),
        "status": "PASS" if passed else "FAIL",
        "output_tail": "Reconstruction & Transaction Parser Validated" if passed else res.stderr
    }

def run_swarm():
    print("=== STARTING MULTI-AGENT SANDBOX SWARM TEST SUITE ===")
    start_total = time.time()
    
    tasks = [run_lane_payment, run_lane_rust, run_lane_security_audit, run_lane_ocr]
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(t) for t in tasks]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    total_time = time.time() - start_total
    all_pass = all(r["status"] == "PASS" for r in results)

    print("\n--- SWARM EXECUTION RESULTS ---")
    for r in results:
        icon = "✅" if r["status"] == "PASS" else "❌"
        print(f"{icon} Lane: {r['lane']:<28} | Time: {r['elapsed_sec']}s | Status: {r['status']}")
        print(f"   Detail: {r['output_tail']}")

    print(f"\nTotal Swarm Execution Time: {round(total_time, 3)}s")
    print(f"Overall Swarm Status: {'ALL LANES PASSING (100% GREEN)' if all_pass else 'SOME LANES FAILED'}")
    return all_pass

if __name__ == "__main__":
    success = run_swarm()
    sys.exit(0 if success else 1)
