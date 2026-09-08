# Sovereign Bionic Currency — Real Foundry Project

Production Solidity implementation of our sovereign settlement stack:
- ERC-20 with sovereign mint authority
- Real EIP-2612 `permit` (gasless approvals via EIP-712 signatures)
- Bonding curve AMM (constant product with virtual reserves)
- Foundry invariant fuzz tests (10k runs)

## Build & Test

```bash
forge build
forge test -vv --fuzz-runs 10000
anvil  # local chain for deployments
forge script script/Deploy.s.sol --broadcast
```
