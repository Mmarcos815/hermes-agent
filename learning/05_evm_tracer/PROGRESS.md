# Skill 6: EVM Internals — PROGRESS.md

**Status:** ⚠️ PARTIAL — tracer built, demo ran (expected: no real tx to trace)
**Started:** 2026-09-02

## What was built
- `evm_tracer.py` — Custom Foundry tracer (Python) that flags suspicious patterns

## What it detects
- `DELEGATECALL` to non-whitelisted addresses
- `SELFDESTRUCT` calls
- `STATICCALL` violations
- Unusual gas patterns

## Evidence
```
Demo: tracing a hypothetical tx hash...
  → No findings (expected — no real tx to trace)
Live usage: connect to Anvil, run a buy/sell, then pass the tx hash
```

## Next steps
- Integrate with live Anvil node (port 8545)
- Run against SovereignBionicCurrency contract
- Add real-time flag stream during tx simulation
