#!/usr/bin/env python3
"""
Orca ADE Multi-Agent Swarm Orchestrator
Executes parallel task lanes mapped to Orca worktree roles:
1. Lane 1: 3D Secure 2.2 Protocol Simulator (three_ds_simulator.py)
2. Lane 2: Unified ISO 8583 / EMV Payment Gateway (unified_payment_gateway.py)
3. Lane 3: API Vulnerability & Defense Verification Lab (api_defense_lab.py)
4. Lane 4: Native Rust Packet Engine & Dissector (bionic_packet_engine.exe)
5. Lane 5: Financial Statement Table Extractor (statement_extractor_cli.py)
"""

import sys, os, time, json, subprocess, concurrent.futures

ROOT_DIR = r"C:\Users\mobil\orca\projects\my 1st"

SWARM_JOBS = [
    {
        "lane_id": "lane-3ds2",
        "name": "3D Secure 2.2 Protocol Engine",
        "worktree": "task/payment-rails",
        "command": [sys.executable, os.path.join(ROOT_DIR, "three_ds_simulator.py")],
        "expected_marker": "ALL TESTS PASSED"
    },
    {
        "lane_id": "lane-payment-gw",
        "name": "ISO 8583 & EMV Field 55 Gateway",
        "worktree": "task/payment-rails",
        "command": [sys.executable, os.path.join(ROOT_DIR, "unified_payment_gateway.py")],
        "expected_marker": "ALL TESTS PASSED"
    },
    {
        "lane_id": "lane-api-defense",
        "name": "API Vulnerability & Defense Lab",
        "worktree": "task/api-fuzzing",
        "command": [sys.executable, os.path.join(ROOT_DIR, "api_defense_lab.py")],
        "expected_marker": "ALL TESTS PASSED"
    },
    {
        "lane_id": "lane-rust-dissector",
        "name": "Native Rust FastMCP Dissector",
        "worktree": "task/binary-protocol",
        "command": [os.path.join(ROOT_DIR, "rust_tools", "target", "release", "bionic_packet_engine.exe"), "--test"],
        "expected_marker": "100% PASS"
    },
    {
        "lane_id": "lane-ocr-extractor",
        "name": "Statement OCR & Ledger Extractor",
        "worktree": "task/statement-ocr",
        "command": [sys.executable, os.path.join(ROOT_DIR, "statement_extractor_cli.py")],
        "expected_marker": "total_extracted_rows"
    },
    {
        "lane_id": "lane-arbitrage-monitor",
        "name": "Testnet DEX Arbitrage & Fee Calculator",
        "worktree": "task/web3-arbitrage",
        "command": [sys.executable, os.path.join(ROOT_DIR, "testnet_arbitrage_monitor.py")],
        "expected_marker": "100% PASS"
    },
    {
        "lane_id": "lane-iso20022",
        "name": "ISO 20022 Financial Messaging Engine",
        "worktree": "task/payment-rails",
        "command": [sys.executable, os.path.join(ROOT_DIR, "iso20022_engine.py")],
        "expected_marker": "100% PASS"
    },
    {
        "lane_id": "lane-mobile-framework",
        "name": "Mobile Banking MASVS Security Lab",
        "worktree": "task/mobile-security",
        "command": [sys.executable, os.path.join(ROOT_DIR, "mobile_api_framework.py")],
        "expected_marker": "100% PASS"
    },
    {
        "lane_id": "lane-cloud-vps",
        "name": "Private Cloud VPS & High-RAM Engine",
        "worktree": "task/cloud-infrastructure",
        "command": [sys.executable, os.path.join(ROOT_DIR, "bionic_cloud_vps_engine.py")],
        "expected_marker": "100% PASS"
    }
]

def execute_lane(job: dict) -> dict:
    start = time.time()
    try:
        res = subprocess.run(job["command"], cwd=ROOT_DIR, capture_output=True, text=True, timeout=60)
        elapsed = time.time() - start
        combined_output = res.stdout + res.stderr
        passed = res.returncode == 0 and job["expected_marker"] in combined_output
        return {
            "lane_id": job["lane_id"],
            "name": job["name"],
            "worktree": job["worktree"],
            "elapsed_sec": round(elapsed, 3),
            "exit_code": res.returncode,
            "status": "PASS" if passed else "FAIL",
            "summary": "100% Verified" if passed else "Execution Failed",
            "log_sample": res.stdout.strip().split("\n")[-1] if res.stdout else res.stderr
        }
    except Exception as e:
        return {
            "lane_id": job["lane_id"],
            "name": job["name"],
            "worktree": job["worktree"],
            "elapsed_sec": 0.0,
            "status": "FAIL",
            "summary": str(e),
            "log_sample": str(e)
        }

def run_orca_swarm_orchestrator():
    print("================================================================================")
    print("★ ORCA ADE MULTI-AGENT SWARM ORCHESTRATOR — LIVE SANDBOX RUN ★")
    print("================================================================================")
    print(f"Project Workspace: {ROOT_DIR}")
    print(f"Active Parallel Workers: {len(SWARM_JOBS)}\n")

    start_total = time.time()
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(SWARM_JOBS)) as executor:
        futures = [executor.submit(execute_lane, job) for job in SWARM_JOBS]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    total_time = time.time() - start_total
    all_green = all(r["status"] == "PASS" for r in results)

    # Sort results by lane_id for clean presentation
    results.sort(key=lambda r: r["lane_id"])

    print("┌────────────────────────────────────┬──────────────────────┬──────────┬───────────┐")
    print("│ Agent Worktree Task Lane           │ Orca Worktree Lane   │ Duration │ Status    │")
    print("├────────────────────────────────────┼──────────────────────┼──────────┼───────────┤")
    for r in results:
        status_colored = "✅ PASS" if r["status"] == "PASS" else "❌ FAIL"
        print(f"│ {r['name']:<34} │ {r['worktree']:<20} │ {r['elapsed_sec']:>6.3f}s │ {status_colored:<9} │")
    print("└────────────────────────────────────┴──────────────────────┴──────────┴───────────┘")

    print(f"\nSwarm Completed in: {round(total_time, 3)}s")
    print(f"Final Swarm Verdict: {'ALL AGENT LANES GREEN (100% FLAWLESS)' if all_green else 'FAILURES DETECTED'}")
    
    return all_green

if __name__ == "__main__":
    success = run_orca_swarm_orchestrator()
    sys.exit(0 if success else 1)
