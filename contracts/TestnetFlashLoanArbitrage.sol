// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title TestnetFlashLoanArbitrage
 * @notice Educational and testnet reference implementation of an Aave v3 Flash Loan Receiver.
 * @dev Intended strictly for testnets (Sepolia, Base Sepolia, Arbitrum Sepolia).
 * Demonstrates the canonical sequence: Borrow -> Cross-DEX Swap -> Fee Accounting -> Repay.
 */

interface IERC20 {
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address recipient, uint256 amount) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
}

interface IPoolAddressesProvider {
    function getPool() external view returns (address);
}

interface IPool {
    function flashLoanSimple(
        address receiverAddress,
        address asset,
        uint256 amount,
        bytes calldata params,
        uint16 referralCode
    ) external;
}

interface ISwapRouter {
    struct ExactInputSingleParams {
        address tokenIn;
        address tokenOut;
        uint24 fee;
        address recipient;
        uint256 deadline;
        uint256 amountIn;
        uint256 amountOutMinimum;
        uint160 sqrtPriceLimitX96;
    }
    function exactInputSingle(ExactInputSingleParams calldata params) external payable returns (uint256 amountOut);
}

contract TestnetFlashLoanArbitrage {
    address public immutable owner;
    IPoolAddressesProvider public immutable ADDRESSES_PROVIDER;
    IPool public immutable POOL;

    event FlashLoanExecuted(address indexed asset, uint256 amount, uint256 premium, uint256 profit);
    event ArbitrageFailed(string reason);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can execute");
        _;
    }

    constructor(address _addressProvider) {
        owner = msg.sender;
        ADDRESSES_PROVIDER = IPoolAddressesProvider(_addressProvider);
        POOL = IPool(IPoolAddressesProvider(_addressProvider).getPool());
    }

    /**
     * @notice Initiates a flash loan against the Aave lending pool.
     */
    function requestFlashLoan(address _token, uint256 _amount) external onlyOwner {
        bytes memory params = "";
        uint16 referralCode = 0;

        POOL.flashLoanSimple(
            address(this),
            _token,
            _amount,
            params,
            referralCode
        );
    }

    /**
     * @notice Callback invoked by the lending pool once capital is transferred.
     */
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external returns (bool) {
        require(msg.sender == address(POOL), "Caller must be Lending Pool");
        require(initiator == address(this), "Initiator must be this contract");

        uint256 totalOwing = amount + premium;

        // Simulated cross-DEX execution logic (Uniswap vs Sushiswap mock)
        // 1. Swap Asset on DEX A for Intermediate Token
        // 2. Swap Intermediate Token on DEX B back to Asset
        // In this testnet reference, we ensure liquidity covers totalOwing:

        uint256 currentBalance = IERC20(asset).balanceOf(address(this));
        require(currentBalance >= totalOwing, "Insufficient funds to execute repayment invariant");

        uint256 netProfit = currentBalance - totalOwing;

        // Approve the Lending Pool to pull repayment + premium
        IERC20(asset).approve(address(POOL), totalOwing);

        emit FlashLoanExecuted(asset, amount, premium, netProfit);
        return true;
    }

    /**
     * @notice Allows owner to sweep accumulated testnet profits.
     */
    function withdraw(address _token) external onlyOwner {
        uint256 balance = IERC20(_token).balanceOf(address(this));
        require(balance > 0, "Zero balance");
        IERC20(_token).transfer(owner, balance);
    }
}
