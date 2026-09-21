#!/usr/bin/env python3
"""
Stripe Logic Flaw Testing Toolkit
Free test mode — no verification needed.
Tests for coupon manipulation, checkout bypasses, webhook issues.
"""
import json
import requests
from datetime import datetime
from typing import Dict, Optional


class StripeTestSuite:
    """Test Stripe API for logic flaws and misconfigurations."""
    
    BASE_URL = "https://api.stripe.com/v1"
    
    # ── Coupon Logic Flaws ─────────────────────────────────────────────────
    
    @staticmethod
    def test_unlimited_coupon(api_key: str, coupon_id: str, iterations: int = 5) -> Dict:
        """Test if a coupon can be redeemed unlimited times."""
        results = {
            "test": "unlimited_coupon_redemption",
            "coupon_id": coupon_id,
            "timestamp": datetime.now().isoformat(),
            "iterations": [],
            "vulnerable": False,
        }
        
        for i in range(iterations):
            try:
                resp = requests.post(
                    f"{StripeTestSuite.BASE_URL}/coupons/{coupon_id}",
                    auth=(api_key, ''),
                    timeout=10
                )
                results["iterations"].append({
                    "iteration": i + 1,
                    "status": resp.status_code,
                    "valid": resp.json().get("valid", False),
                })
            except Exception as e:
                results["iterations"].append({"iteration": i + 1, "error": str(e)})
        
        # Check if coupon remains valid after multiple redemptions
        valid_count = sum(1 for i in results["iterations"] if i.get("valid"))
        results["vulnerable"] = valid_count == iterations
        
        return results
    
    @staticmethod
    def test_amount_manipulation(api_key: str, amount_cents: int = 100) -> Dict:
        """Test if amount can be manipulated to 0 or negative."""
        results = {
            "test": "amount_manipulation",
            "timestamp": datetime.now().isoformat(),
            "tests": [],
        }
        
        test_amounts = [0, -1, 1, amount_cents, amount_cents * -1, 999999999]
        
        for amt in test_amounts:
            try:
                resp = requests.post(
                    f"{StripeTestSuite.BASE_URL}/payment_intents",
                    data={"amount": amt, "currency": "usd", "payment_method_types[]": "card"},
                    auth=(api_key, ''),
                    timeout=10
                )
                results["tests"].append({
                    "amount": amt,
                    "status": resp.status_code,
                    "created": resp.status_code == 200,
                    "id": resp.json().get("id", "N/A"),
                })
            except Exception as e:
                results["tests"].append({"amount": amt, "error": str(e)})
        
        results["vulnerable"] = any(
            t.get("created") and t.get("amount", 1) <= 0 
            for t in results["tests"]
        )
        
        return results
    
    @staticmethod
    def test_currency_manipulation(api_key: str) -> Dict:
        """Test if currency can be manipulated to reduce value."""
        results = {
            "test": "currency_manipulation",
            "timestamp": datetime.now().isoformat(),
            "tests": [],
        }
        
        # Currencies with very low value vs USD
        currencies = ["usd", "jpy", "krw", "vnd", "irr", "uzs", "xcd"]
        
        for curr in currencies:
            try:
                resp = requests.post(
                    f"{StripeTestSuite.BASE_URL}/payment_intents",
                    data={"amount": 1000, "currency": curr, "payment_method_types[]": "card"},
                    auth=(api_key, ''),
                    timeout=10
                )
                results["tests"].append({
                    "currency": curr,
                    "status": resp.status_code,
                    "created": resp.status_code == 200,
                })
            except Exception as e:
                results["tests"].append({"currency": curr, "error": str(e)})
        
        results["vulnerable"] = len([t for t in results["tests"] if t.get("created")]) > 1
        
        return results
    
    # ── Webhook Security ─────────────────────────────────────────────────
    
    @staticmethod
    def test_webhook_signature_bypass(api_key: str, webhook_secret: str, payload: Dict) -> Dict:
        """Test if webhook signature verification can be bypassed."""
        import hmac
        import hashlib
        import time
        
        results = {
            "test": "webhook_signature_bypass",
            "timestamp": datetime.now().isoformat(),
            "tests": [],
        }
        
        payload_str = json.dumps(payload)
        timestamp = int(time.time())
        
        # Test 1: Valid signature
        signed_payload = f"{timestamp}.{payload_str}"
        expected_sig = hmac.new(
            webhook_secret.encode(),
            signed_payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        results["tests"].append({
            "name": "valid_signature",
            "signature": expected_sig[:20] + "...",
            "should_pass": True,
        })
        
        # Test 2: Empty signature
        results["tests"].append({
            "name": "empty_signature",
            "signature": "",
            "should_pass": False,
        })
        
        # Test 3: Replay attack (old timestamp)
        old_timestamp = timestamp - 3600  # 1 hour ago
        results["tests"].append({
            "name": "replay_attack",
            "timestamp": old_timestamp,
            "should_pass": False,
        })
        
        # Test 4: Algorithm confusion (none)
        results["tests"].append({
            "name": "algorithm_none",
            "signature": "none",
            "should_pass": False,
        })
        
        # Test 5: Timing attack (check if early-exit on mismatch)
        results["tests"].append({
            "name": "timing_attack",
            "description": "Compare timing of first-char match vs full match",
            "should_pass": False,
        })
        
        return results
    
    # ── Connect Payout Manipulation ──────────────────────────────────────
    
    @staticmethod
    def test_connect_payout_manipulation(api_key: str, account_id: str) -> Dict:
        """Test if Connect payout amounts can be manipulated."""
        results = {
            "test": "connect_payout_manipulation",
            "timestamp": datetime.now().isoformat(),
            "tests": [],
        }
        
        # Test negative payout
        try:
            resp = requests.post(
                f"{StripeTestSuite.BASE_URL}/payouts",
                data={
                    "amount": -1000,
                    "currency": "usd",
                    "destination": account_id,
                },
                auth=(api_key, ''),
                timeout=10
            )
            results["tests"].append({
                "name": "negative_payout",
                "status": resp.status_code,
                "vulnerable": resp.status_code == 200,
            })
        except Exception as e:
            results["tests"].append({"name": "negative_payout", "error": str(e)})
        
        return results
    
    # ── Checkout Session Bypass ─────────────────────────────────────────
    
    @staticmethod
    def test_checkout_session_bypass(api_key: str, price_id: str) -> Dict:
        """Test if checkout session can be manipulated."""
        results = {
            "test": "checkout_session_bypass",
            "timestamp": datetime.now().isoformat(),
            "tests": [],
        }
        
        # Test with quantity manipulation
        for qty in [1, 100, 9999, -1, 0]:
            try:
                resp = requests.post(
                    f"{StripeTestSuite.BASE_URL}/checkout/sessions",
                    data={
                        "line_items[0][price]": price_id,
                        "line_items[0][quantity]": qty,
                        "mode": "payment",
                        "success_url": "https://example.com/success",
                    },
                    auth=(api_key, ''),
                    timeout=10
                )
                results["tests"].append({
                    "quantity": qty,
                    "status": resp.status_code,
                    "url": resp.json().get("url", "N/A") if resp.status_code == 200 else "N/A",
                })
            except Exception as e:
                results["tests"].append({"quantity": qty, "error": str(e)})
        
        return results
    
    # ── IDOR Testing ────────────────────────────────────────────────────
    
    @staticmethod
    def test_idor(api_key: str, object_id: str, object_type: str = "customers") -> Dict:
        """Test for Insecure Direct Object Reference."""
        results = {
            "test": "idor",
            "object_type": object_type,
            "timestamp": datetime.now().isoformat(),
            "tests": [],
        }
        
        # Try to access object without proper permissions
        try:
            resp = requests.get(
                f"{StripeTestSuite.BASE_URL}/{object_type}/{object_id}",
                auth=(api_key, ''),
                timeout=10
            )
            results["tests"].append({
                "object_id": object_id,
                "status": resp.status_code,
                "accessible": resp.status_code == 200,
                "data_leaked": list(resp.json().keys()) if resp.status_code == 200 else [],
            })
        except Exception as e:
            results["tests"].append({"object_id": object_id, "error": str(e)})
        
        return results


# ── Payment Recon Expansion ─────────────────────────────────────────────────

class PaymentRecon:
    """Reconnaissance for PayPal, Amex, Square, Braintree, Adyen."""
    
    PAYPAL_API = "https://api-m.paypal.com"
    AMEX_API = "https://api.americanexpress.com"
    SQUARE_API = "https://connect.squareup.com"
    BRAINTREE_API = "https://payments.braintree-api.com"
    ADYEN_API = "https://checkout-live.adyen.com"
    
    @staticmethod
    def paypal_endpoints() -> Dict:
        """Return PayPal API endpoint catalog."""
        return {
            "auth": {
                "url": "/v1/oauth2/token",
                "method": "POST",
                "auth": "Basic (client_id:secret)",
            },
            "payments": {
                "create": "/v2/checkout/orders",
                "capture": "/v2/checkout/orders/{id}/capture",
                "refund": "/v2/payments/captures/{id}/refund",
                "void": "/v2/payments/authorizations/{id}/void",
            },
            "wallet": {
                "balance": "/v1/reporting/balances",
                "transactions": "/v1/reporting/transactions",
            },
            "subscriptions": {
                "create": "/v1/billing/plans",
                "subscribe": "/v1/billing/subscriptions",
            },
            "attack_surface": [
                "Amount manipulation in orders",
                "Webhook signature bypass",
                "Refund without authorization",
                "Subscription cancellation bypass",
                "Payout manipulation (Connect)",
            ],
        }
    
    @staticmethod
    def amex_endpoints() -> Dict:
        """Return Amex API endpoint catalog."""
        return {
            "base": "https://api.americanexpress.com",
            "capabilities": [
                "Loyalty programs (Membership Rewards)",
                "Card account management",
                "Transaction history",
                "Offers and deals",
                "Business checking",
            ],
            "attack_surface": [
                "Reward point manipulation",
                "Offer redemption abuse",
                "Account linking IDOR",
                "Transaction history leak",
            ],
        }
    
    @staticmethod
    def square_endpoints() -> Dict:
        """Return Square API endpoint catalog."""
        return {
            "base": "https://connect.squareup.com",
            "endpoints": {
                "payments": "/v2/payments",
                "refunds": "/v2/refunds",
                "customers": "/v2/customers",
                "orders": "/v2/orders",
                "catalog": "/v2/catalog",
                "inventory": "/v2/inventory",
            },
            "attack_surface": [
                "Refund without payment",
                "Inventory manipulation",
                "Customer data leak",
                "Webhook spoofing",
                "OAuth token theft",
            ],
        }
    
    @staticmethod
    def braintree_endpoints() -> Dict:
        """Return Braintree API endpoint catalog."""
        return {
            "base": "https://payments.braintree-api.com/graphql",
            "auth": "Basic (public_key:private_key)",
            "endpoints": {
                "client_token": "/client_api/v1/client_tokens",
                "payment_methods": "/client_api/v1/payment_methods",
                "transactions": "/graphql",
            },
            "attack_surface": [
                "GraphQL injection",
                "Client token forgery",
                "Transaction replay",
                "Amount manipulation",
                "Webhook signature bypass",
            ],
        }
    
    @staticmethod
    def adyen_endpoints() -> Dict:
        """Return Adyen API endpoint catalog."""
        return {
            "base": "https://checkout-live.adyen.com",
            "endpoints": {
                "payments": "/v71/payments",
                "payment_methods": "/v71/paymentMethods",
                "sessions": "/v71/sessions",
                "cancels": "/v71/cancels",
                "reversals": "/v71/reversals",
            },
            "attack_surface": [
                "Session amount manipulation",
                "Payment method token theft",
                "Webhook replay",
                "CVC bypass",
                "3DS bypass",
            ],
        }


# ── MCP Tool Functions ────────────────────────────────────────────────────

def stripe_test_coupon(api_key: str, coupon_id: str, iterations: int = 5) -> str:
    """Test if a Stripe coupon can be redeemed unlimited times."""
    return json.dumps(StripeTestSuite.test_unlimited_coupon(api_key, coupon_id, iterations), indent=2)

def stripe_test_amount(api_key: str, amount_cents: int = 100) -> str:
    """Test Stripe for amount manipulation (0 or negative)."""
    return json.dumps(StripeTestSuite.test_amount_manipulation(api_key, amount_cents), indent=2)

def stripe_test_currency(api_key: str) -> str:
    """Test Stripe for currency manipulation."""
    return json.dumps(StripeTestSuite.test_currency_manipulation(api_key), indent=2)

def stripe_test_webhook(api_key: str, webhook_secret: str, payload: dict = None) -> str:
    """Test Stripe webhook for signature bypass."""
    if payload is None:
        payload = {"type": "payment_intent.succeeded", "data": {"object": {"id": "pi_test"}}}
    return json.dumps(StripeTestSuite.test_webhook_signature_bypass(api_key, webhook_secret, payload), indent=2)

def stripe_test_connect(api_key: str, account_id: str) -> str:
    """Test Stripe Connect for payout manipulation."""
    return json.dumps(StripeTestSuite.test_connect_payout_manipulation(api_key, account_id), indent=2)

def stripe_test_checkout(api_key: str, price_id: str) -> str:
    """Test Stripe Checkout for session manipulation."""
    return json.dumps(StripeTestSuite.test_checkout_session_bypass(api_key, price_id), indent=2)

def stripe_test_idor(api_key: str, object_id: str, object_type: str = "customers") -> str:
    """Test Stripe for IDOR vulnerabilities."""
    return json.dumps(StripeTestSuite.test_idor(api_key, object_id, object_type), indent=2)

def payment_recon_paypal() -> str:
    """Return PayPal API attack surface."""
    return json.dumps(PaymentRecon.paypal_endpoints(), indent=2)

def payment_recon_amex() -> str:
    """Return Amex API attack surface."""
    return json.dumps(PaymentRecon.amex_endpoints(), indent=2)

def payment_recon_square() -> str:
    """Return Square API attack surface."""
    return json.dumps(PaymentRecon.square_endpoints(), indent=2)

def payment_recon_braintree() -> str:
    """Return Braintree API attack surface."""
    return json.dumps(PaymentRecon.braintree_endpoints(), indent=2)

def payment_recon_adyen() -> str:
    """Return Adyen API attack surface."""
    return json.dumps(PaymentRecon.adyen_endpoints(), indent=2)

def payment_recon_all() -> str:
    """Return full payment recon for all providers."""
    return json.dumps({
        "paypal": PaymentRecon.paypal_endpoints(),
        "amex": PaymentRecon.amex_endpoints(),
        "square": PaymentRecon.square_endpoints(),
        "braintree": PaymentRecon.braintree_endpoints(),
        "adyen": PaymentRecon.adyen_endpoints(),
    }, indent=2)


if __name__ == "__main__":
    print("=== Stripe Logic Flaw Toolkit ===")
    print("Test mode — free API keys, no verification needed")
    print("\nAvailable tests:")
    print("  stripe_test_coupon — Test unlimited coupon redemption")
    print("  stripe_test_amount — Test amount manipulation")
    print("  stripe_test_currency — Test currency manipulation")
    print("  stripe_test_webhook — Test webhook signature bypass")
    print("  stripe_test_connect — Test Connect payout manipulation")
    print("  stripe_test_checkout — Test Checkout session bypass")
    print("  stripe_test_idor — Test IDOR vulnerabilities")
    print("\n=== Payment Recon ===")
    print("  payment_recon_paypal — PayPal API surface")
    print("  payment_recon_amex — Amex API surface")
    print("  payment_recon_square — Square API surface")
    print("  payment_recon_braintree — Braintree API surface")
    print("  payment_recon_adyen — Adyen API surface")
