/*
Learning Project 11 — Formal Verification Spec for SovereignBionicCurrency
Certora Verification Language (CVL) — analogous to Certora Prover specs.

This file documents the invariants we want to prove mathematically.
Cannot be run without Certora Prover (paid SaaS), but the rules
translate to property tests in Foundry / Scribble / SMTChecker.
*/

rule k_invariant_preserved(method) {
    // For every method (except initial constructor), the constant-product
    // invariant must hold: reserveBase * virtualTokenReserve == k_initial
    // OR greater (due to rounding-up ceil in the implementation).
    env e;
    require e.msg.value == 0;  // methods are payable but we pass no value here

    mathint reserveBefore = reserveBase();
    mathint supplyBefore = virtualTokenReserve();
    mathint k_initial = 500_000e18 * 10_000_000e18;

    method();  // any method on the contract
    // (skip the constructor, which sets initial k)

    mathint reserveAfter = reserveBase();
    mathint supplyAfter = virtualTokenReserve();
    assert reserveAfter * supplyAfter >= k_initial, "k-invariant violated";
}

rule no_drain_via_buy_sell_sequence {
    // No sequence of buy/sell can withdraw more base than was deposited.
    // The reserve can never decrease via user actions (only owner can withdrawBase).
    env e;
    mathint reserveInitial = reserveBase();

    // User does a sequence of operations
    method();
    method();
    method();

    mathint reserveFinal = reserveBase();
    // Reserve can decrease only via withdrawBase (owner only)
    // OR the user's buy with insufficient virtual reserve (revert).
    // For any sequence of public user methods, reserve should not decrease
    // UNLESS the caller is the owner calling withdrawBase.
    if (e.msg.sender != owner) {
        assert reserveFinal >= reserveInitial, "non-owner drained reserve";
    }
}

rule permit_replay_blocked {
    // A used permit nonce cannot be reused.
    address holder;
    uint256 v; bytes32 r; bytes32 s; uint256 deadline;
    uint256 ownerNonceBefore = nonces(holder);

    env e;
    require e.msg.sender == holder;
    permit(holder, address(this), 1e18, deadline, v, r, s);

    uint256 ownerNonceAfter = nonces(holder);
    assert ownerNonceAfter == ownerNonceBefore + 1, "nonce not incremented";
}

rule only_authority_can_mint {
    // Only the sovereign authority (set in constructor) can call sovereignMint.
    // After transferAuthority(curve), only the curve contract can mint.
    address nonAuthority;
    require nonAuthority != authority();

    env e;
    require e.msg.sender == nonAuthority;
    sovereignMint@withrevert(nonAuthority, 1, "x");
    assert lastReverted, "non-authority minted";
}

invariant totalSupply_matches_curve_mints() {
    // token.totalSupply() == genesis_mint + sum of all curve-minted - sum of all burned
    mathint curveMinted = 10_000_000e18 - virtualTokenReserve();
    assert totalSupply() == 1_000_000_000e18 + curveMinted;
}

/*
Notes on running this:
- Certora Prover requires a paid license
- Alternative: write equivalent Solidity property tests using
  forge-std's StatefulFuzz / Scribble annotations
- Even simpler: convert to SMT-LIB2 and run with Z3 / cvc5 directly

Our equivalent in solidity:
    function invariant_k_preserved() public view {
        uint256 reserve = curve.reserveBase();
        uint256 supply = curve.virtualTokenReserve();
        assertGe(reserve * supply, k_initial);
    }

is already in /bionic-sovereign/test/SovereignBionicInvariants.t.sol.
*/