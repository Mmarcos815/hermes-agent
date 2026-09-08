# Skill 11: Formal Verification — PROGRESS.md

**Status:** ⚠️ PARTIAL — Certora-style spec file exists
**Started:** 2026-09-02

## What was built
- `certora_spec.sol` — Certora CVL spec for SovereignBionicCurrency

## What's in the spec
- `k_invariant` — proves `reserve * supply == k` ALWAYS
- `no_drain_possible` — proves vault cannot be drained
- `permit_replay_blocked` — proves permit signatures cannot be replayed

## Next steps
- Run actual Certora verification (requires Certora CLI)
- Add more invariants to the spec
- Integrate with CI pipeline
