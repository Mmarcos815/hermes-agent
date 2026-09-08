# Skill 2: Solidity Invariants — PROGRESS.md

**Status:** ⚠️ PARTIAL
**Started:** 2026-09-02

## What exists
- `SECURITY_FINDING_UINT128_OVERFLOW.md` — uint128 overflow bug found in BondingCurveAMM
- Foundry fuzz artifacts show 10k fuzz runs passing

## What's missing
- `SovereignBionicInvariants.t.sol` — 3 new invariant tests:
  1. `invariant_k_preserved()` — `reserve * supply == k` ALWAYS
  2. `invariant_no_drain()` — vault can never be drained below initial_reserve
  3. `invariant_sequential_consistency()` — multiple users + multiple ops preserve solvency

## Next steps
- Write the 3 invariant tests
- Run: `forge test --match-contract SovereignBionicInvariants -vv --invariant-runs 256 --invariant-depth 64`
