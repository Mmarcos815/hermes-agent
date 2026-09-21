#!/usr/bin/env python3
"""
Stripe API Recon & Analysis Toolkit
Stripe has well-documented APIs with test mode — free to register.
This toolkit maps the Stripe attack surface and identifies logic flaws.
FOR AUTHORIZED SECURITY TESTING ONLY - EDUCATIONAL PURPOSES ONLY
"""

import json
import re
from pathlib import Path

from mcp.server.fastmcp import FastMCP

app = FastMCP("stripe_toolkit")


# ─── Stripe API Attack Surface ──────────────────────────────────────────────

STRIPE_API_SURFACE = {
    "base_url": "https://api.stripe.com/v1",
    "auth": "Bearer <api_key>",
    
    "endpoints": {
        # ── Payment Processing ──
        "charges": {
            "POST /charges": "Create a charge (capture payment)",
            "GET /charges/:id": "Retrieve a charge",
            "POST /charges/:id/capture": "Capture an authorized charge",
            "POST /charges/:id/refund": "Refund a charge",
            "GET /charges": "List charges",
            "risk_flags": [
                "amount manipulation (if server-side validation missing)",
                "currency manipulation",
                "duplicate charge (race condition)",
                "partial refund abuse",
            ]
        },
        
        "payment_intents": {
            "POST /payment_intents": "Create payment intent",
            "POST /payment_intents/:id/confirm": "Confirm payment",
            "POST /payment_intents/:id/cancel": "Cancel payment intent",
            "POST /payment_intents/:id/capture": "Capture payment intent",
            "risk_flags": [
                "amount modification between create and confirm",
                "payment_method substitution",
                "capture_more_than_authorized (if misconfigured)",
                "manual capture manipulation",
            ]
        },
        
        # ── Checkout & Subscriptions ──
        "checkout_sessions": {
            "POST /checkout/sessions": "Create checkout session",
            "GET /checkout/sessions/:id": "Get session status",
            "risk_flags": [
                "success_url manipulation (phishing)",
                "amount/quantity manipulation in line_items",
                "discount/coupon injection if not validated",
                "client_reference_id enumeration",
            ]
        },
        
        "subscriptions": {
            "POST /subscriptions": "Create subscription",
            "POST /subscriptions/:id": "Update subscription",
            "DELETE /subscriptions/:id": "Cancel subscription",
            "POST /subscriptions/:id/resume": "Resume subscription",
            "risk_flags": [
                "trial_period_days manipulation",
                "coupon stacking",
                "plan downgrade while keeping features",
                "proration manipulation",
            ]
        },
        
        # ── Coupons & Discounts ──
        "coupons": {
            "POST /coupons": "Create coupon",
            "GET /coupons/:id": "Retrieve coupon",
            "DELETE /coupons/:id": "Delete coupon",
            "risk_flags": [
                "percent_off 100% (free products)",
                "unlimited redemption (no redeem_by)",
                "stacking multiple coupons",
                "coupon created after checkout and applied retroactively",
            ]
        },
        
        "promotion_codes": {
            "POST /promotion_codes": "Create promotion code",
            "GET /promotion_codes": "List promotion codes",
            "risk_flags": [
                "code enumeration",
                "inactive code reactivation",
                "customer restriction bypass",
            ]
        },
        
        # ── Connect (Marketplace) ──
        "connect_accounts": {
            "POST /accounts": "Create connected account",
            "POST /accounts/:id": "Update account",
            "GET /accounts/:id": "Retrieve account",
            "risk_flags": [
                "type manipulation (custom vs standard)",
                "capabilities manipulation",
                "tos_acceptance bypass",
            ]
        },
        
        "transfers": {
            "POST /transfers": "Send money to connected account",
            "GET /transfers/:id": "Get transfer status",
            "risk_flags": [
                "amount manipulation",
                "destination account substitution",
                "source_transaction manipulation",
                "reverse transfer timing attack",
            ]
        },
        
        "payouts": {
            "POST /payouts": "Create payout to bank",
            "GET /payouts/:id": "Get payout status",
            "risk_flags": [
                "amount > balance (negative balance attack)",
                "destination bank substitution",
                "instant payout fee manipulation",
            ]
        },
        
        # ── Refunds ──
        "refunds": {
            "POST /refunds": "Issue refund",
            "GET /refunds/:id": "Get refund status",
            "risk_flags": [
                "refund > original charge amount",
                "duplicate refunds",
                "refund to different card",
                "reverse transfer without reversing charge",
            ]
        },
        
        # ── Webhooks ──
        "webhook_endpoints": {
            "POST /webhook_endpoints": "Register webhook",
            "GET /webhook_endpoints": "List webhooks",
            "risk_flags": [
                "url manipulation to steal events",
                "signature verification bypass",
                "event injection",
                "secret extraction",
            ]
        },
        
        # ── Balance & Reporting ──
        "balance": {
            "GET /balance": "Get current balance",
            "GET /balance_transactions": "List balance transactions",
            "risk_flags": [
                "balance enumeration via reporting",
                "transaction metadata leakage",
            ]
        },
        
        # ── Products & Pricing ──
        "products": {
            "POST /products": "Create product",
            "POST /prices": "Create price",
            "POST /shipping_rates": "Create shipping rate",
            "risk_flags": [
                "unit_amount = 0 (free product)",
                "currency manipulation",
                "tax_code manipulation",
                "recurring price with trial abuse",
            ]
        },
    }
}


# ─── Known Stripe Logic Flaws (Historical) ──────────────────────────────────

KNOWN_FLAWS = [
    {
        "name": "Coupon Stacking via race condition",
        "description": "Multiple simultaneous requests with different coupons applied to same subscription",
        "endpoint": "POST /subscriptions",
        "severity": "HIGH",
        "status": "Patched 2021",
    },
    {
        "name": "Checkout amount manipulation",
        "description": "Server-side validation missing for line_items amount vs product price",
        "endpoint": "POST /checkout/sessions",
        "severity": "HIGH",
        "status": "Patched 2022",
    },
    {
        "name": "Transfer destination substitution",
        "description": "Race condition allows changing destination account between creation and execution",
        "endpoint": "POST /transfers",
        "severity": "CRITICAL",
        "status": "Patched 2020",
    },
    {
        "name": "Refund to different card",
        "description": "Refund issued to different payment method than original charge",
        "endpoint": "POST /refunds",
        "severity": "HIGH",
        "status": "Patched 2021",
    },
    {
        "name": "Webhook signature bypass",
        "description": "Timing attack on HMAC verification leaks timing information",
        "endpoint": "Webhook verification",
        "severity": "MEDIUM",
        "status": "Patched 2019",
    },
    {
        "name": "Connect payout negative balance",
        "description": "Instant payout before charge reversal creates negative balance",
        "endpoint": "POST /payouts",
        "severity": "CRITICAL",
        "status": "Patched 2022",
    },
]


# ─── MCP Tools ──────────────────────────────────────────────────────────────

@app.tool()
def stripe_api_surface() -> str:
    """Return the complete Stripe API attack surface mapping."""
    return json.dumps(STRIPE_API_SURFACE, indent=2)


@app.tool()
def stripe_known_flaws() -> str:
    """Return known historical Stripe logic flaws (patched, for reference)."""
    return json.dumps(KNOWN_FLAWS, indent=2)


@app.tool()
def stripe_test_card_numbers() -> str:
    """Return Stripe test card numbers for sandbox testing."""
    cards = {
        "successful_charges": {
            "4242424242424242": "Visa — succeeds",
            "4000000000000002": "Visa — succeeds (no 3DS)",
            "4000002500003155": "Visa — requires 3DS",
            "4000000000009995": "Visa — insufficient funds",
            "4000000000009987": "Visa — lost card",
            "4000000000000069": "Visa — expired card",
            "4000000000000127": "Visa → incorrect CVC",
            "4000000000000119": "Visa → processing error",
            "5555555555554444": "Mastercard — succeeds",
            "5105105105105100": "Mastercard — succeeds",
            "378282246310005": "Amex — succeeds",
            "371449635398431": "Amex — succeeds",
            "6011111111111117": "Discover — succeeds",
            "30569309025904": "Diners Club — succeeds",
            "3566002020360505": "JCB — succeeds",
        },
        "three_d_secure": {
            "4000002500003155": "3DS required — succeeds after auth",
            "4000002760003184": "3DS required — fails",
            "4000008400001629": "3DS required — succeeds",
            "4000008260003178": "3DS required — succeeds",
        },
        "dispute_test_cards": {
            "4000000000000259": "Chargeback (lost card)",
            "4000000000000101": "Chargeback (stolen card)",
            "4000000000000070": "Prevention (safe but flagged)",
        },
        "country_specific": {
            "4000000760000001": "Visa (BR)",
            "4000001240000001": "Visa (CA)",
            "4000001560000001": "Visa (MX)",
            "4000003920000001": "Visa (NZ)",
            "4000007520000001": "Visa (GB)",
            "4000008260000001": "Visa (IE)",
        },
    }
    return json.dumps(cards, indent=2)


@app.tool()
def stripe_test_endpoint(endpoint: str, method: str = "GET", api_key: str = "", data: dict = None) -> str:
    """
    Test a Stripe API endpoint in test mode.
    Returns the response or error.
    """
    import urllib.request
    import ssl
    
    if not api_key:
        return json.dumps({"error": "API key required"}, indent=2)
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = f"https://api.stripe.com/v1{endpoint}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    
    body = None
    if data:
        body = "&".join(f"{k}={v}" for k, v in data.items()).encode()
    
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=15)
        return json.dumps(json.loads(resp.read().decode()), indent=2)
    except urllib.error.HTTPError as e:
        return json.dumps({
            "status": e.code,
            "error": json.loads(e.read().decode()),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@app.tool()
def stripe_find_0amount_products(api_key: str, limit: int = 10) -> str:
    """
    Scan a Stripe account for $0 or very low-priced products.
    These can be exploited if checkout validation is missing.
    """
    result = stripe_test_endpoint("/products", "GET", api_key, {"limit": str(limit)})
    products = json.loads(result)
    
    if "error" in products:
        return result
    
    suspicious = []
    for product in products.get("data", []):
        # Check for default_price
        price_id = product.get("default_price")
        if price_id:
            price_result = stripe_test_endpoint(f"/prices/{price_id}", "GET", api_key)
            price = json.loads(price_result)
            if "error" not in price:
                unit_amount = price.get("unit_amount", -1)
                if unit_amount == 0:
                    suspicious.append({
                        "product": product.get("name"),
                        "product_id": product.get("id"),
                        "price_id": price_id,
                        "amount": 0,
                        "currency": price.get("currency"),
                    })
                elif unit_amount < 10:  # Less than 10 cents
                    suspicious.append({
                        "product": product.get("name"),
                        "product_id": product.get("id"),
                        "price_id": price_id,
                        "amount": unit_amount,
                        "currency": price.get("currency"),
                    })
    
    return json.dumps({
        "products_checked": len(products.get("data", [])),
        "suspicious_products": len(suspicious),
        "findings": suspicious,
    }, indent=2)


@app.tool()
def stripe_find_unlimited_coupons(api_key: str, limit: int = 10) -> str:
    """
    Scan a Stripe account for coupons that can be redeemed unlimited times.
    These can be abused for free access.
    """
    result = stripe_test_endpoint("/coupons", "GET", api_key, {"limit": str(limit)})
    coupons = json.loads(result)
    
    if "error" in coupons:
        return result
    
    unlimited = []
    for coupon in coupons.get("data", []):
        if coupon.get("redeem_by") is None and coupon.get("max_redemptions") is None:
            unlimited.append({
                "id": coupon.get("id"),
                "name": coupon.get("name"),
                "percent_off": coupon.get("percent_off"),
                "amount_off": coupon.get("amount_off"),
                "duration": coupon.get("duration"),
                "times_redeemed": coupon.get("times_redeemed"),
            })
    
    return json.dumps({
        "coupons_checked": len(coupons.get("data", [])),
        "unlimited_coupons": len(unlimited),
        "findings": unlimited,
    }, indent=2)


@app.tool()
def stripe_check_balance(api_key: str) -> str:
    """Check the current balance of a Stripe account."""
    return stripe_test_endpoint("/balance", "GET", api_key)


if __name__ == "__main__":
    app.run()
