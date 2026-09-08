// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {SovereignBionicCurrency} from "../src/SovereignBionicCurrency.sol";
import {BondingCurveAMM} from "../src/BondingCurveAMM.sol";

/// @notice Sovereign token + bonding curve: unit, fuzz, and gasless-permit tests.
contract SovereignBionicTest is Test {
    SovereignBionicCurrency token;
    BondingCurveAMM curve;

    // DAD's identity is always derived FROM the key: vm.addr(DAD_PRIV_KEY)
    uint256 constant DAD_PRIV_KEY = 0xA11CE;

    address DAUGHTER = makeAddr("DaughterAgent");
    address RELAYER = makeAddr("RelayerNode");

    function setUp() public {
        // Derive the real address for the test key
        address dad = vm.addr(DAD_PRIV_KEY);

        token = new SovereignBionicCurrency(dad);
        curve = new BondingCurveAMM(
            address(token),
            10_000_000e18,          // initial virtual token reserve
            500_000e18              // initial base reserve (18-dec)
        );
        // Hand sovereign mint authority to the curve so `buy()` can mint
        vm.prank(dad);
        token.transferAuthority(address(curve));
    }

    function _dad() internal view returns (address) {
        return vm.addr(DAD_PRIV_KEY);
    }

    // ---------- Genesis & authority ----------

    function test_GenesisMintToOneBillion() public view {
        assertEq(token.balanceOf(_dad()), 1_000_000_000e18);
        assertEq(token.totalSupply(), 1_000_000_000e18);
    }

    function test_SovereignMintOnlyAuthority() public {
        // After setup, authority = curve. DAUGHTER must not mint.
        vm.prank(DAUGHTER);
        vm.expectRevert();
        token.sovereignMint(DAUGHTER, 1e18, bytes32("X"));

        // The curve CAN mint (it holds authority)
        vm.prank(address(curve));
        token.sovereignMint(DAUGHTER, 5_000e18, bytes32("CURVE_REF"));
        assertEq(token.balanceOf(DAUGHTER), 5_000e18);
    }

    // ---------- Bonding curve ----------

    function test_BuyIncreasesReserveAndMints() public {
        uint256 baseIn = 50_000e18;
        deal(_dad(), baseIn);

        vm.prank(_dad());
        uint256 out = curve.buy{value: baseIn}(baseIn);

        assertGt(out, 0);
        assertEq(token.balanceOf(_dad()), 1_000_000_000e18 + out);
    }

    function test_SpotPriceScalesWithReserve() public {
        uint256 p0 = curve.spotPrice();
        uint256 baseIn = 50_000e18;
        deal(_dad(), baseIn);
        vm.prank(_dad());
        curve.buy{value: baseIn}(baseIn);
        uint256 p1 = curve.spotPrice();
        assertGt(p1, p0, "price must rise after buys");
    }

    function test_BuyRejectsOversizedBaseIn() public {
        // uint128.max + 1 should revert with AmountTooLarge (input validation).
        // baseIn is uint256, so the overflow doesn't happen at constant time.
        uint256 oversizedBaseIn = uint256(type(uint128).max) + 1;
        vm.prank(_dad());
        try curve.buy{value: 0}(oversizedBaseIn) {
            revert("buy() should have reverted");
        } catch (bytes memory reason) {
            bytes4 expected = BondingCurveAMM.AmountTooLarge.selector;
            require(reason.length >= 4, "revert reason too short");
            bytes4 actual;
            assembly { actual := mload(add(reason, 0x20)) }
            require(actual == expected, "wrong revert reason");
        }
    }

    function test_BuyRejectsMsgValueMismatch() public {
        vm.deal(_dad(), 10 ether);
        vm.prank(_dad());
        vm.expectRevert(BondingCurveAMM.AmountTooLarge.selector);
        curve.buy{value: 10 ether}(1 ether);  // value != baseIn
    }

    // ---------- REAL EIP-2612 gasless settlement ----------

    /// @notice Builds the exact EIP-712 digest, signs with DAD's key,
    ///         and relays the settlement (relayer pays gas, DAD pays zero).
    function test_GaslessSettlementViaPermit() public {
        // Fund DAD's permit via the authority path first
        vm.prank(address(curve));
        token.sovereignMint(_dad(), 1_000e18, bytes32("SEED"));

        address dad = _dad();
        uint256 amount = 250_000e18;
        uint256 deadline = block.timestamp + 1 hours;

        bytes32 structHash = keccak256(
            // spender MUST be the token contract itself — that's what
            // executeGaslessSettlement passes into permit() internally
            abi.encode(token.PERMIT_TYPEHASH(), dad, address(token), amount, token.nonces(dad), deadline)
        );
        bytes32 digest = keccak256(abi.encodePacked("\x19\x01", token.DOMAIN_SEPARATOR(), structHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(DAD_PRIV_KEY, digest);

        uint256 dadBefore = token.balanceOf(dad);
        vm.prank(RELAYER);
        token.executeGaslessSettlement(dad, DAUGHTER, amount, deadline, v, r, s);

        assertEq(token.balanceOf(DAUGHTER), amount);
        assertEq(token.balanceOf(dad), dadBefore - amount);
        assertEq(token.nonces(dad), 1);
    }

    function test_PermitRejectsBadSignature() public {
        uint256 deadline = block.timestamp + 1 hours;
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(DAD_PRIV_KEY, keccak256("garbage"));

        vm.prank(RELAYER);
        vm.expectRevert(SovereignBionicCurrency.BadSignature.selector);
        token.executeGaslessSettlement(_dad(), DAUGHTER, 1e18, deadline, v, r, s);
    }

    function test_PermitRejectsExpired() public {
        address dad = _dad();
        uint256 deadline = block.timestamp - 1;
        bytes32 structHash = keccak256(
            abi.encode(token.PERMIT_TYPEHASH(), dad, DAUGHTER, 1e18, token.nonces(dad), deadline)
        );
        bytes32 digest = keccak256(abi.encodePacked("\x19\x01", token.DOMAIN_SEPARATOR(), structHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(DAD_PRIV_KEY, digest);

        vm.prank(RELAYER);
        vm.expectRevert(SovereignBionicCurrency.PermitExpired.selector);
        token.executeGaslessSettlement(dad, DAUGHTER, 1e18, deadline, v, r, s);
    }

    // ---------- FUZZ: k must never decrease ----------

    function test_Fuzz_BuySellRoundTripConservesK(uint128 baseIn) public {
        vm.assume(baseIn > 1e12 && baseIn < 100_000e18);

        uint256 kBefore = uint256(curve.reserveBase()) * curve.virtualTokenReserve();
        deal(_dad(), baseIn);  // give the test contract ETH to send

        vm.prank(_dad());
        uint256 out = curve.buy{value: baseIn}(baseIn);

        uint256 kAfterBuy = uint256(curve.reserveBase()) * curve.virtualTokenReserve();
        assertGe(kAfterBuy, kBefore, "k must never decrease on buy");

        // Real user flow: approve the curve, then sell half back
        vm.startPrank(_dad());
        token.approve(address(curve), out / 2);
        curve.sell(out / 2);
        vm.stopPrank();

        uint256 kAfterSell = uint256(curve.reserveBase()) * curve.virtualTokenReserve();
        assertGe(kAfterSell, kAfterBuy, "k must never decrease on sell");
    }
}
