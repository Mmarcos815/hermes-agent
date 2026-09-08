// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import "../src/SovereignBionicCurrency.sol";
import "../src/BondingCurveAMM.sol";

/**
 * @title SovereignBionicInvariants
 * @notice 3 new invariant tests for SovereignBionicCurrency + BondingCurveAMM
 * @dev Run: forge test --match-contract SovereignBionicInvariants -vv --invariant-runs 256 --invariant-depth 64
 */
contract SovereignBionicInvariants is Test {
    SovereignBionicCurrency public currency;
    BondingCurveAMM public amm;

    uint256 public constant INITIAL_RESERVE = 1000 ether;
    uint256 public constant INITIAL_SUPPLY = 1_000_000 ether;

    function setUp() public {
        currency = new SovereignBionicCurrency();
        // Deploy AMM with initial virtual tokens and base
        amm = new BondingCurveAMM(address(currency), INITIAL_SUPPLY, INITIAL_RESERVE);
        currency.setAMM(address(amm));
    }

    // Invariant 1: k_preserved — reserveBase * virtualTokenReserve == k ALWAYS
    function invariant_k_preserved() public view {
        uint256 reserve = amm.reserveBase();
        uint256 tokens = amm.virtualTokenReserve();
        uint256 k = reserve * tokens;
        // k should be constant (or increase due to rounding)
        // After every trade, k should be >= initial k
        assertGe(k, INITIAL_RESERVE * INITIAL_SUPPLY, "k invariant violated: k decreased");
    }

    // Invariant 2: no_drain — reserve can never be drained below initial_reserve
    function invariant_no_drain() public view {
        uint256 reserve = amm.reserveBase();
        assertGe(reserve, INITIAL_RESERVE, "vault drained below initial reserve");
    }

    // Invariant 3: sequential_consistency — multiple users + multiple ops preserve solvency
    function invariant_sequential_consistency() public view {
        uint256 reserve = amm.reserveBase();
        uint256 tokens = amm.virtualTokenReserve();
        // Total value locked should always be >= reserve
        assertGe(address(amm).balance, reserve, "AMM balance below reserve");
        // Tokens should never exceed 10x initial (no infinite mint)
        assertLe(tokens, INITIAL_SUPPLY * 10, "virtual tokens exceeded 10x initial");
    }
}
