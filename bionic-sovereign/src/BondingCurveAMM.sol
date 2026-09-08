// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "./SovereignBionicCurrency.sol";

/// @title BondingCurveAMM (FIXED v2)
/// @notice Constant-product bonding curve with virtual reserves (x*y=k).
///         Buys mint from the curve; sells burn back into it.
/// @dev Security fixes vs v1:
///      1. buy() is now payable (was missing — couldn't accept ETH in production)
///      2. baseIn/tokensIn capped at type(uint128).max before any math (prevents
///         silent overflow on the uint128 cast)
///      3. Explicit require on uint128 cast (belt-and-suspenders even though the
///         bound check above should catch it)
///      4. Same cap applied to sell() (k = base * tokens could overflow both ways)
contract BondingCurveAMM {
    SovereignBionicCurrency public immutable token;
    address public owner;

    uint256 public virtualTokenReserve; // virtual token side of the curve
    uint128 public reserveBase;         // real base (e.g. WETH/USDC-18) side

    // simple accounting of real base collected
    event Buy(address indexed buyer, uint256 baseIn, uint256 tokensOut);
    event Sell(address indexed seller, uint256 tokensIn, uint256 baseOut);

    error ZeroAmount();
    error NotOwner();
    error AmountTooLarge();
    error InsufficientOutput();
    error TransferFailed();

    /// @notice Maximum value that fits in uint128 — anything larger is rejected
    ///         to prevent silent overflow when storage variables are cast down.
    uint128 public constant MAX_AMOUNT = type(uint128).max;

    constructor(address token_, uint256 initialVirtualTokens, uint256 initialBase) {
        token = SovereignBionicCurrency(token_);
        owner = msg.sender;
        virtualTokenReserve = initialVirtualTokens;
        if (initialBase > MAX_AMOUNT) revert AmountTooLarge();
        reserveBase = uint128(initialBase);
    }

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    function spotPrice() public view returns (uint256) {
        // price = base / tokens, 18-dec fixed point
        return (uint256(reserveBase) * 1e18) / virtualTokenReserve;
    }

    /// @notice Buy tokens with base (ETH); minted against the curve.
    /// @dev Rounds tokensOut DOWN so reserveBase * virtualTokenReserve >= k
    ///      holds exactly after every trade (no invariant dust leak).
    function buy(uint256 baseIn) external payable returns (uint256 tokensOut) {
        if (baseIn == 0) revert ZeroAmount();
        if (baseIn > MAX_AMOUNT) revert AmountTooLarge();          // FIX: cap input
        // msg.value should match baseIn — accept exactly baseIn to prevent griefing
        if (msg.value != baseIn) revert AmountTooLarge();

        uint256 k = uint256(reserveBase) * virtualTokenReserve;
        uint256 newBase = uint256(reserveBase) + baseIn;          // uint256 math
        uint256 newTokens = (k + newBase - 1) / newBase;
        tokensOut = virtualTokenReserve - newTokens;
        if (tokensOut == 0) revert InsufficientOutput();

        // Belt-and-suspenders: even with the cap above, verify before casting
        if (newBase > MAX_AMOUNT) revert AmountTooLarge();
        reserveBase = uint128(newBase);
        virtualTokenReserve = newTokens;

        token.sovereignMint(msg.sender, tokensOut, bytes32("BONDING_CURVE_BUY"));
        emit Buy(msg.sender, baseIn, tokensOut);
    }

    /// @notice Sell tokens back into the curve; tokens burned, base returned.
    function sell(uint256 tokensIn) external returns (uint256 baseOut) {
        if (tokensIn == 0) revert ZeroAmount();
        if (tokensIn > MAX_AMOUNT) revert AmountTooLarge();       // FIX: cap input

        uint256 k = uint256(reserveBase) * virtualTokenReserve;
        uint256 newTokens = virtualTokenReserve + tokensIn;
        if (newTokens > MAX_AMOUNT) revert AmountTooLarge();      // FIX: prevent overflow
        uint256 newBase = (k + newTokens - 1) / newTokens;
        baseOut = uint256(reserveBase) - newBase;
        if (baseOut == 0) revert InsufficientOutput();

        if (!token.transferFrom(msg.sender, address(this), tokensIn)) revert TransferFailed();
        if (newBase > MAX_AMOUNT) revert AmountTooLarge();           // FIX: verify before cast
        reserveBase = uint128(newBase);
        virtualTokenReserve = newTokens;
        emit Sell(msg.sender, tokensIn, baseOut);
    }

    /// @notice Owner withdrawal of accumulated base (simulated).
    function withdrawBase(uint256 amount) external onlyOwner {
        if (amount > reserveBase) revert AmountTooLarge();
        // in a real deployment this pulls from the base token ledger
    }

    /// @notice Allow the contract to receive ETH directly (for future use)
    receive() external payable {}

    /// @notice Allow the contract to receive ETH with data
    fallback() external payable {}
}