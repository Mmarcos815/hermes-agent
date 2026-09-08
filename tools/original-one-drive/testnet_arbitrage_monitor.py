#!/usr/bin/env python3
"""
Testnet DEX Arbitrage Engine & Liquidity Monitor
Monitors simulated DEX price spreads (Uniswap v3 vs Sushiswap) across testnet pairs,
calculates flash loan premium + gas costs, and evaluates transaction profitability.
"""

import sys, time, json

class TestnetArbitrageMonitor:
    def __init__(self, gas_price_gwei: float = 25.0, eth_price_usd: float = 3000.0):
        self.gas_price_gwei = gas_price_gwei
        self.eth_price_usd = eth_price_usd
        self.estimated_gas_units = 350000 # Typical multi-hop flash loan gas cost

    def calculate_gas_cost_usd(self) -> float:
        eth_cost = (self.estimated_gas_units * (self.gas_price_gwei * 1e-9))
        return eth_cost * self.eth_price_usd

    def evaluate_opportunity(self, token_symbol: str, borrow_amount: float, dex_a_price: float, dex_b_price: float, flash_loan_fee_bps: int = 9) -> dict:
        """
        Evaluates whether a cross-DEX spread covers flash loan premium + L1 gas costs.
        """
        gas_cost_usd = self.calculate_gas_cost_usd()
        loan_fee_usd = (borrow_amount * flash_loan_fee_bps) / 10000.0

        # Buy on DEX A (lower price), Sell on DEX B (higher price)
        if dex_b_price > dex_a_price:
            tokens_bought = borrow_amount / dex_a_price
            gross_revenue = tokens_bought * dex_b_price
            gross_profit = gross_revenue - borrow_amount
            direction = f"Buy on DEX A (${dex_a_price:.2f}) -> Sell on DEX B (${dex_b_price:.2f})"
        else:
            tokens_bought = borrow_amount / dex_b_price
            gross_revenue = tokens_bought * dex_a_price
            gross_profit = gross_revenue - borrow_amount
            direction = f"Buy on DEX B (${dex_b_price:.2f}) -> Sell on DEX A (${dex_a_price:.2f})"

        total_overhead = loan_fee_usd + gas_cost_usd
        net_profit_usd = gross_profit - total_overhead
        profitable = net_profit_usd > 0

        return {
            "token": token_symbol,
            "borrow_amount_usd": borrow_amount,
            "direction": direction,
            "gross_profit_usd": round(gross_profit, 2),
            "flash_loan_fee_usd": round(loan_fee_usd, 2),
            "gas_cost_usd": round(gas_cost_usd, 2),
            "total_overhead_usd": round(total_overhead, 2),
            "net_profit_usd": round(net_profit_usd, 2),
            "is_profitable": profitable,
            "verdict": "EXECUTE_TESTNET_ARBITRAGE" if profitable else "SKIP_UNPROFITABLE_SPREAD"
        }


def run_monitor_demo():
    print("=== TESTNET DEX ARBITRAGE & LIQUIDITY MONITOR ===")
    monitor = TestnetArbitrageMonitor(gas_price_gwei=20.0, eth_price_usd=3000.0)
    
    print(f"Base Gas Cost Estimate: ${monitor.calculate_gas_cost_usd():.2f} (at 20 Gwei)")

    # Scenario 1: Tiny spread (0.05%) on $100k borrow -> Swallowed by gas + loan fee
    print("\n--- Scenario 1: 0.05% Spread on $100,000 Borrow ---")
    res1 = monitor.evaluate_opportunity(
        token_symbol="WETH",
        borrow_amount=100000.0,
        dex_a_price=3000.00,
        dex_b_price=3001.50, # 0.05% difference
        flash_loan_fee_bps=9
    )
    print(json.dumps(res1, indent=2))
    assert res1["is_profitable"] is False

    # Scenario 2: Sizable testnet spread (0.35%) on $100k borrow -> Profitable
    print("\n--- Scenario 2: 0.35% Spread on $100,000 Borrow ---")
    res2 = monitor.evaluate_opportunity(
        token_symbol="WETH",
        borrow_amount=100000.0,
        dex_a_price=3000.00,
        dex_b_price=3010.50, # 0.35% difference
        flash_loan_fee_bps=9
    )
    print(json.dumps(res2, indent=2))
    assert res2["is_profitable"] is True

    print("\n>>> TESTNET ARBITRAGE MONITOR: 100% PASS <<<")


if __name__ == "__main__":
    run_monitor_demo()
