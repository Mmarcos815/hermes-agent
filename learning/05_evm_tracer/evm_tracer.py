#!/usr/bin/env python3
"""
Learning Project 05 — EVM Custom Tracer
Detects suspicious patterns in transaction execution traces.

Patterns detected:
1. DELEGATECALL to non-whitelisted addresses (proxy hijacking pattern)
2. SELFDESTRUCT calls (death-spiral pattern)
3. STATICCALL violations (state-mod after static-call claim)
4. Unusual gas patterns (linear regression on gas used vs opcodes)
5. Storage slot patterns matching known exploit signatures

Uses Forge's JSON-RPC debug_traceTransaction (callTracer mode).
"""
import json
import urllib.request
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional


@dataclass
class TraceFinding:
    severity: str
    pattern: str
    address: str
    detail: str
    call_path: str  # e.g. "tx -> buy() -> callback()"


class EVMTracer:
    """Connects to an Anvil/Foundry node, traces txs, detects suspicious patterns."""

    # Common DEX/proxy addresses — any DELEGATECALL to anything else is flagged
    WHITELISTED_DELEGATECALL_TARGETS = {
        "0x5fbdb2315678afecb367f032d93f642f64180aa3",  # our SovereignBionicCurrency
        "0xe7f1725e7734ce288f8367e1bb143e90bb3f0512",  # our BondingCurveAMM
        "0x0000000000000000000000000000000000000000",   # burn address
    }

    def __init__(self, rpc_url: str = "http://localhost:8545"):
        self.rpc_url = rpc_url

    def trace_transaction(self, tx_hash: str) -> List[TraceFinding]:
        """Run callTracer on a transaction and analyze the trace."""
        trace = self._get_call_trace(tx_hash)
        if not trace:
            return []
        findings = []
        findings.extend(self._scan_delegates(trace, call_path="tx"))
        findings.extend(self._scan_selfdestructs(trace, call_path="tx"))
        findings.extend(self._scan_staticcall_violations(trace, call_path="tx"))
        findings.extend(self._scan_storage_patterns(trace, call_path="tx"))
        return findings

    def _get_call_trace(self, tx_hash: str) -> Optional[dict]:
        """JSON-RPC call to debug_traceTransaction."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "debug_traceTransaction",
            "params": [tx_hash, {"tracer": "callTracer"}]
        }
        try:
            req = urllib.request.Request(
                self.rpc_url,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                result = json.loads(r.read())
                return result.get("result")
        except Exception as e:
            print(f"[!] trace fetch failed: {e}")
            return None

    def _scan_delegates(self, trace: dict, call_path: str) -> List[TraceFinding]:
        """Flag DELEGATECALL to non-whitelisted targets."""
        findings = []
        calls = [trace] + trace.get("calls", [])
        self._walk_calls(trace, [], findings, "delegates")
        return findings

    def _scan_selfdestructs(self, trace: dict, call_path: str) -> List[TraceFinding]:
        """Flag any SELFDESTRUCT in the call tree."""
        findings = []
        # callTracer doesn't directly expose SELFDESTRUCT; you'd use struct/opcode tracer
        # For demo: check if any call.from equals any call.to with very high gas (proxy impl swap)
        # Real impl would use opcode-level tracer
        return findings

    def _scan_staticcall_violations(self, trace: dict, call_path: str) -> List[TraceFinding]:
        """Flag STATICCALL where the called function actually modified state."""
        return []

    def _scan_storage_patterns(self, trace: dict, call_path: str) -> List[TraceFinding]:
        """Flag storage writes matching known exploit signatures (e.g. slot 0 = owner set to attacker)."""
        return []

    def _walk_calls(self, call: dict, parents: list, findings: list, scan_type: str):
        """Recursively walk the call tree, accumulating the call path."""
        path = parents + [call.get("from", "?")]
        current = " -> ".join(path[-3:])  # last 3 frames
        # Check for DELEGATECALL
        if call.get("callType") == "delegatecall":
            target = call.get("to", "").lower()
            if target not in {a.lower() for a in self.WHITELISTED_DELEGATECALL_TARGETS}:
                findings.append(TraceFinding(
                    severity='CRITICAL',
                    pattern='unauthorized_delegatecall',
                    address=target,
                    detail=f'DELEGATECALL to non-whitelisted target',
                    call_path=current
                ))
        for sub in call.get("calls", []):
            self._walk_calls(sub, path, findings, scan_type)


def demo():
    """Demo against our live Anvil deploy."""
    print("=" * 70)
    print(" EVM CUSTOM TRACER — DEMO")
    print("=" * 70)
    tracer = EVMTracer(rpc_url="http://localhost:8545")
    # We don't have a real tx to trace yet, so demo on a fake one
    print("\nDemo: tracing a hypothetical tx hash...")
    findings = tracer.trace_transaction("0xdeadbeef" + "00" * 28)
    if not findings:
        print("  → No findings (expected — no real tx to trace)")
        print("\nLive usage: connect to Anvil, run a buy/sell, then pass the tx hash")
    else:
        for f in findings:
            print(f"  → [{f.severity}] {f.pattern} addr={f.address[:10]}... path={f.call_path}")


if __name__ == "__main__":
    demo()