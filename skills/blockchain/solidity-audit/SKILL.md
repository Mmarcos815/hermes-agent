---
name: solidity-audit
description: "Smart contract security audit scanner — detects reentrancy, oracle manipulation, unchecked calls, selfdestruct, and other DeFi/Immunefi bug bounty vectors in Solidity source."
version: 1.0.0
author: Rigoberto Gomez, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [blockchain, solidity, smart-contract, audit, defi, security, bug-bounty]
    related_skills: [iso8583]
---

# Solidity Smart Contract Security Audit Scanner

A pure-Python (stdlib only) static analyzer that scans Solidity (.sol) source files for 10 critical DeFi/Immunefi bug bounty vectors. Uses regex-based pattern matching to detect reentrancy risks, spot-price oracle reliance, missing return-value checks, unprotected functions, timestamp dependence, integer overflow, selfdestruct calls, unprotected admin functions, and delegatecall to untrusted contracts. Outputs structured JSON findings with rule IDs, severity, line numbers, code snippets, and remediation guidance.

## When to Use

- Auditing Solidity smart contracts for common vulnerability patterns
- Pre-submission checks before deploying to testnet/mainnet
- Bug bounty reconnaissance on DeFi protocols
- Security training and education on smart contract vulnerabilities
- CI/CD pipeline integration for automated contract scanning

Don't use for:
- Guaranteeing contract security (regex-based, will miss novel or obfuscated vulnerabilities)
- Replacing professional audits (Trail of Bits, OpenZeppelin, etc.)
- Analyzing compiled bytecode (works on source code only)

## Prerequisites

- Python 3.8+ (uses `re`, `os`, `json`, `sys` — all stdlib)
- No external dependencies
- The script `scripts/solidity_audit_scanner.py` in this skill directory
- Solidity source files (.sol) to scan

## How to Run

```bash
cp ~/.hermes/skills/blockchain/solidity-audit/scripts/solidity_audit_scanner.py ./
python solidity_audit_scanner.py
```

This runs the built-in demo that scans `contracts/TestnetFlashLoanArbitrage.sol` and prints findings.

### Scan a Custom Contract

```python
from solidity_audit_scanner import SolidityAuditScanner

scanner = SolidityAuditScanner()
result = scanner.scan_source("path/to/YourContract.sol")
print(f"Verdict: {result['audit_verdict']}")
for f in result['findings']:
    print(f"  [{f['severity']}] {f['rule_id']}: {f['title']} (line {f['line']})")
```

## Quick Reference

| Rule ID | Title | Severity | Pattern |
|---------|-------|----------|---------|
| SEC-SOL-001 | State Update After External Call (Reentrancy) | HIGH | `.call{value:...}` followed by state update |
| SEC-SOL-002 | Spot Price AMM Oracle Dependency | CRITICAL | `getReserves()`, `reserve0`, `reserve1` |
| SEC-SOL-003 | Low-Level Call Invocation | MEDIUM | `.send`, `.delegatecall`, `.call{` |
| SEC-SOL-004 | State-Modifying Withdrawal Function | LOW | `function withdraw/redeem/claim` external |
| SEC-SOL-005 | Timestamp Dependence (Front-running) | HIGH | `block.number`, `now`, `timestamp` |
| SEC-SOL-006 | Integer Overflow / Underflow | HIGH | `uint++`, `-- uint`, `value + value` |
| SEC-SOL-007 | Self-Destruct (Suicide) | CRITICAL | `selfdestruct(` |
| SEC-SOL-008 | Unprotected Owner / Admin Functions | HIGH | `onlyowner`, `onlyadmin`, `owner()` |
| SEC-SOL-009 | Delegate Call to Untrusted Contract | CRITICAL | `delegatecall(` |
| SEC-SOL-010 | Timestamp Manipulation via Mineable Blocks | HIGH | `block.timestamp`, `block.coinbase` |

## Procedure

### 1. Initialize the Scanner

```python
from solidity_audit_scanner import SolidityAuditScanner

scanner = SolidityAuditScanner()
```

### 2. Scan a Contract

```python
result = scanner.scan_source("contracts/MyToken.sol")
```

### 3. Interpret Results

```python
print(f"File: {result['target_file']}")
print(f"Total findings: {result['total_findings']}")
print(f"Verdict: {result['audit_verdict']}")
# "CLEAN" = no findings
# "SECURITY_ADVISORIES_IDENTIFIED" = findings present

for finding in result['findings']:
    print(f"  [{finding['severity']}] {finding['rule_id']}")
    print(f"    Title: {finding['title']}")
    print(f"    Line: {finding['line']}")
    print(f"    Snippet: {finding['snippet']}")
    print(f"    Description: {finding['description']}")
    print(f"    Remediation: {finding['remediation']}")
```

### 4. Output Structure

```json
{
  "target_file": "path/to/contract.sol",
  "total_findings": 3,
  "audit_verdict": "SECURITY_ADVISORIES_IDENTIFIED",
  "findings": [
    {
      "rule_id": "SEC-SOL-002",
      "title": "Spot Price AMM Oracle Dependency",
      "severity": "CRITICAL",
      "line": 42,
      "snippet": "getReserves()",
      "description": "Querying spot DEX reserves directly...",
      "remediation": "Use Chainlink decentralized price feeds..."
    }
  ]
}
```

## Pitfalls

- **Regex-based detection.** Will produce false positives and false negatives. Not a substitute for manual review or formal verification.
- **No AST parsing.** Patterns match text, not semantic structure. May miss vulnerabilities in complex expressions.
- **No cross-file analysis.** Scans one file at a time. Inherited contracts and imports are not followed.
- **No Solidity version detection.** Rules assume modern Solidity (^0.8+). Older version patterns may not apply.
- **Severity is static.** Severity levels are hardcoded per rule and do not account for context (e.g., a `selfdestruct` in a test contract vs. a mainnet contract).
- **No taint analysis.** Cannot track data flows from untrusted sources to sensitive sinks.
- **Pattern limitations.** SEC-SOL-001 (reentrancy) uses a simple regex that may miss complex multi-line patterns.
- **No EVM semantics.** Does not understand storage vs. memory, function visibility, or access control beyond pattern matching.

## Verification

- Scanner returns `audit_verdict: "CLEAN"` for contracts with no matches
- Each finding includes `rule_id`, `severity`, `line`, `snippet`, `description`, `remediation`
- Demo scan of `TestnetFlashLoanArbitrage.sol` produces valid JSON output
- All 10 rules are defined in the `RULES` list at module level
- `scan_source()` raises `FileNotFoundError` for missing files
