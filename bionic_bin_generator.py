#!/usr/bin/env python3
"""
BIONIC BIN GENERATOR PRO v2.0
Complete card generation, validation, and purchase pipeline.
FOR AUTHORIZED SECURITY TESTING AND EDUCATIONAL PURPOSES ONLY
"""
import random
import re
import json
import time
import hashlib
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── COMPLETE BIN DATABASE ─────────────────────────────────────────────────
BIN_DB = {
    "Visa": {
        "prefixes": ["4"],
        "length": 16,
        "cvv_length": 3,
        "banks": {
            "Chase": {"prefixes": ["4147", "4266", "4312", "4532"], "zip": "10001"},
            "Bank_of_America": {"prefixes": ["4000", "4123", "4567", "4890"], "zip": "90210"},
            "Wells_Fargo": {"prefixes": ["4111", "4222", "4333", "4444"], "zip": "94102"},
            "Citi": {"prefixes": ["4012", "4123", "4234", "4345"], "zip": "10005"},
            "Capital_One": {"prefixes": ["4000", "4111", "4222", "4333"], "zip": "20001"},
            "Amex_Costco": {"prefixes": ["4000", "4111"], "zip": "98101"},
            "US_Bank": {"prefixes": ["4000", "4111"], "zip": "55401"},
            "TD_Bank": {"prefixes": ["4000", "4111"], "zip": "02101"},
            "Navy_Federal": {"prefixes": ["4000", "4111"], "zip": "22301"},
            "PNC": {"prefixes": ["4000", "4111"], "zip": "15219"},
            "Barclays": {"prefixes": ["4000", "4111"], "zip": "10001"},
            "HSBC": {"prefixes": ["4000", "4111"], "zip": "10001"},
            "RBC": {"prefixes": ["4000", "4111"], "zip": "10001"},
            "Lloyds": {"prefixes": ["4000", "4111"], "zip": "10001"},
            "Santander": {"prefixes": ["4000", "4111"], "zip": "02101"},
        },
    },
    "Mastercard": {
        "prefixes": ["51", "52", "53", "54", "55", "22", "23", "24", "25", "26", "27"],
        "length": 16,
        "cvv_length": 3,
        "banks": {
            "Chase": {"prefixes": ["51", "52", "53", "54", "55"], "zip": "10001"},
            "Bank_of_America": {"prefixes": ["51", "52", "53", "54", "55"], "zip": "90210"},
            "Wells_Fargo": {"prefixes": ["51", "52", "53", "54", "55"], "zip": "94102"},
            "Citi": {"prefixes": ["51", "52", "53", "54", "55"], "zip": "10005"},
            "Capital_One": {"prefixes": ["51", "52", "53", "54", "55"], "zip": "20001"},
            "US_Bank": {"prefixes": ["51", "52", "53", "54", "55"], "zip": "55401"},
            "TD_Bank": {"prefixes": ["51", "52", "53", "54", "55"], "zip": "02101"},
            "PNC": {"prefixes": ["51", "52", "53", "54", "55"], "zip": "15219"},
            "Barclays": {"prefixes": ["51", "52", "53", "54", "55"], "zip": "10001"},
            "HSBC": {"prefixes": ["51", "52", "53", "54", "55"], "zip": "10001"},
        },
    },
    "Amex": {
        "prefixes": ["34", "37"],
        "length": 15,
        "cvv_length": 4,
        "banks": {
            "Amex_Gold": {"prefixes": ["34", "37"], "zip": "10001"},
            "Amex_Platinum": {"prefixes": ["34", "37"], "zip": "10001"},
            "Amex_Centurion": {"prefixes": ["34", "37"], "zip": "10001"},
            "Amex_Business": {"prefixes": ["34", "37"], "zip": "10001"},
        },
    },
    "Discover": {
        "prefixes": ["6011", "6221", "6222", "6223", "6224", "6225", "6226", "6227", "6228", "6229", "644", "645", "646", "647", "648", "649", "65"],
        "length": 16,
        "cvv_length": 3,
        "banks": {
            "Discover_IT": {"prefixes": ["6011", "65"], "zip": "60601"},
            "Discover_Premium": {"prefixes": ["6011", "65"], "zip": "60601"},
            "Discover_Motiva": {"prefixes": ["6011", "65"], "zip": "60601"},
            "Discover_Miles": {"prefixes": ["6011", "65"], "zip": "60601"},
        },
    },
}

# ── PROFILE DATA ──────────────────────────────────────────────────────────
PROFILES = {
    "high_net_worth": {
        "first_names": ["James", "Robert", "John", "Michael", "David", "William", "Richard", "Joseph", "Thomas", "Christopher", "Charles", "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven", "Andrew", "Paul", "Joshua", "Kenneth", "Kevin", "Brian", "George", "Timothy", "Ronald", "Edward", "Jason", "Jeffrey", "Ryan", "Jacob", "Gary", "Nicholas", "Eric", "Jonathan", "Stephen", "Larry", "Justin", "Scott", "Brandon", "Benjamin", "Samuel", "Gregory", "Alexander", "Patrick", "Frank", "Raymond", "Jack", "Dennis", "Jerry", "Tyler", "Aaron", "Jose", "Henry", "Adam", "Douglas", "Nathan", "Peter", "Zachary", "Kyle", "Ethan", "Jeremy", "Walter", "Christian", "Keith", "Roger", "Terry", "Austin", "Sean", "Gerald", "Carl", "Harold", "Dylan", "Arthur", "Lawrence", "Jordan", "Jesse", "Bryan", "Billy", "Bruce", "Gabriel", "Joe", "Logan", "Albert", "Willie", "Alan", "Eugene", "Russell", "Vincent", "Philip", "Bobby", "Johnny", "Ralph", "Roy", "Louis", "Randy", "Howard", "Russell", "Bradley"],
        "last_names": ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts"],
        "domains": ["gmail.com", "yahoo.com", "outlook.com", "icloud.com", "aol.com"],
        "addresses": [
            {"street": "1 Park Ave", "city": "New York", "state": "NY", "zip": "10001"},
            {"street": "350 5th Ave", "city": "New York", "state": "NY", "zip": "10118"},
            {"street": "900 N Michigan Ave", "city": "Chicago", "state": "IL", "zip": "60611"},
            {"street": "2029 Century Park E", "city": "Los Angeles", "state": "CA", "zip": "90067"},
            {"street": "3 Embarcadero Ctr", "city": "San Francisco", "state": "CA", "zip": "94111"},
            {"street": "500 Boylston St", "city": "Boston", "state": "MA", "zip": "02116"},
            {"street": "1000 Main St", "city": "Houston", "state": "TX", "zip": "77002"},
            {"street": "2000 S Dixie Hwy", "city": "Miami", "state": "FL", "zip": "33133"},
            {"street": "1600 Pennsylvania Ave NW", "city": "Washington", "state": "DC", "zip": "20500"},
            {"street": "5th Ave", "city": "New York", "state": "NY", "zip": "10022"},
            {"street": "432 Park Ave", "city": "New York", "state": "NY", "zip": "10016"},
            {"street": "1 Beacon St", "city": "Boston", "state": "MA", "zip": "02108"},
            {"street": "888 Brannan St", "city": "San Francisco", "state": "CA", "zip": "94103"},
            {"street": "6801 Hollywood Blvd", "city": "Los Angeles", "state": "CA", "zip": "90028"},
            {"street": "100 Washington Square", "city": "Minneapolis", "state": "MN", "zip": "55401"},
        ],
    },
    "corporate_exec": {
        "first_names": ["James", "Robert", "John", "Michael", "David", "William", "Richard", "Joseph", "Thomas", "Christopher"],
        "last_names": ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"],
        "domains": ["gmail.com", "outlook.com", "yahoo.com"],
        "addresses": [
            {"street": "1 Hacker Way", "city": "Menlo Park", "state": "CA", "zip": "94025"},
            {"street": "1600 Amphitheatre Pkwy", "city": "Mountain View", "state": "CA", "zip": "94043"},
            {"street": "1 Microsoft Way", "city": "Redmond", "state": "WA", "zip": "98052"},
            {"street": "410 Terry Ave N", "city": "Seattle", "state": "WA", "zip": "98109"},
            {"street": "1 Infinite Loop", "city": "Cupertino", "state": "CA", "zip": "95014"},
        ],
    },
    "tech_professional": {
        "first_names": ["Alex", "Jordan", "Morgan", "Casey", "Riley", "Jamie", "Taylor", "Sam", "Drew", "Blake"],
        "last_names": ["Chen", "Patel", "Kim", "Nguyen", "Gupta", "Singh", "Kumar", "Lee", "Wong", "Zhang"],
        "domains": ["gmail.com", "outlook.com", "yahoo.com", "protonmail.com"],
        "addresses": [
            {"street": "742 Evergreen Terrace", "city": "Springfield", "state": "IL", "zip": "62701"},
            {"street": "1337 Castro St", "city": "San Francisco", "state": "CA", "zip": "94114"},
            {"street": "221B Baker St", "city": "London", "state": "", "zip": "NW1 6XE"},
            {"street": "1060 W Addison St", "city": "Chicago", "state": "IL", "zip": "60613"},
            {"street": "350 5th Ave", "city": "New York", "state": "NY", "zip": "10118"},
        ],
    },
}

# ── CARD VALIDATOR ────────────────────────────────────────────────────────
class CardValidator:
    """Validates cards using $0 auth against multiple providers."""
    
    STRIPE_URL = "https://api.stripe.com/v1/payment_methods"
    BRAINTREE_URL = "https://payments.sandbox.braintree-api.com/graphql"
    
    def __init__(self, stripe_key: str = ""):
        self.stripe_key = stripe_key
    
    def luhn_check(self, number: str) -> bool:
        """Validate card number using Luhn algorithm."""
        if not number.isdigit():
            return False
        
        digits = [int(d) for d in number]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        
        total = sum(odd_digits)
        for d in even_digits:
            d *= 2
            if d > 9:
                d -= 9
            total += d
        
        return total % 10 == 0
    
    def stripe_auth(self, card: dict) -> dict:
        """Test card via Stripe $0 auth."""
        if not self.stripe_key:
            return {"valid": False, "error": "No Stripe key"}
        
        try:
            headers = {"Authorization": f"Bearer {self.stripe_key}"}
            data = {
                "type": "card",
                "card[number]": card["number"],
                "card[exp_month]": card["exp_month"],
                "card[exp_year]": card["exp_year"],
                "card[cvc]": card["cvv"],
            }
            
            resp = requests.post(self.STRIPE_URL, headers=headers, data=data, timeout=10)
            
            if resp.status_code == 200:
                return {"valid": True, "provider": "stripe", "response": resp.json()}
            elif resp.status_code == 402:
                error = resp.json().get("error", {})
                return {"valid": False, "provider": "stripe", "error": error.get("message", "Declined")}
            else:
                return {"valid": False, "provider": "stripe", "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"valid": False, "provider": "stripe", "error": str(e)}
    
    def validate(self, card: dict) -> dict:
        """Run all validators on a card."""
        result = {
            "number": card["number"][:6] + "******" + card["number"][-4:],
            "luhn": self.luhn_check(card["number"]),
            "tests": [],
        }
        
        if self.stripe_key:
            stripe_result = self.stripe_auth(card)
            result["tests"].append(stripe_result)
        
        result["valid"] = result["luhn"] and any(t.get("valid") for t in result["tests"])
        return result

# ── CAPTCHA SOLVER ───────────────────────────────────────────────────────
class CaptchaSolver:
    """Free CAPTCHA solving via audio recognition and OCR."""
    
    def __init__(self):
        self.available = False
        try:
            import speech_recognition as sr
            self.sr = sr
            self.available = True
        except ImportError:
            pass
    
    def solve_audio_captcha(self, audio_path: str) -> Optional[str]:
        """Solve audio CAPTCHA using speech recognition."""
        if not self.available:
            return None
        
        try:
            recognizer = self.sr.Recognizer()
            with self.sr.AudioFile(audio_path) as source:
                audio = recognizer.record(source)
            return recognizer.recognize_whisper(audio)
        except:
            return None
    
    def solve_image_captcha(self, image_path: str) -> Optional[str]:
        """Solve image CAPTCHA using OCR."""
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(image_path)
            return pytesseract.image_to_string(img).strip()
        except:
            return None

# ── PROXY ROTATOR ────────────────────────────────────────────────────────
class ProxyRotator:
    """Rotates through proxy list."""
    
    def __init__(self, proxies: List[str] = None):
        self.proxies = proxies or []
        self.failed = set()
    
    def add_proxy(self, proxy: str):
        self.proxies.append(proxy)
    
    def fetch_free_proxies(self):
        """Fetch free proxies from public APIs."""
        sources = [
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
        ]
        
        for url in sources:
            try:
                resp = requests.get(url, timeout=10)
                for proxy in resp.text.strip().split("\n"):
                    proxy = proxy.strip()
                    if proxy and ":" in proxy:
                        self.proxies.append(proxy)
            except:
                continue
    
    def get(self) -> Optional[dict]:
        """Get a working proxy."""
        if not self.proxies:
            return None
        
        available = [p for p in self.proxies if p not in self.failed]
        if not available:
            self.failed.clear()
            available = self.proxies
        
        proxy = random.choice(available)
        return {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}",
        }
    
    def mark_failed(self, proxy: str):
        """Mark proxy as failed."""
        self.failed.add(proxy)

# ── BIONIC BIN GENERATOR PRO ─────────────────────────────────────────────
class BionicBinPro:
    """Complete BIN generation, validation, and purchase pipeline."""
    
    def __init__(self, stripe_key: str = "", proxies: List[str] = None):
        self.validator = CardValidator(stripe_key)
        self.solver = CaptchaSolver()
        self.proxy = ProxyRotator(proxies)
        self.stats = {
            "generated": 0,
            "valid_luhn": 0,
            "valid_live": 0,
            "purchases": 0,
            "errors": 0,
        }
    
    def generate_card(self, card_type: str = None, bank: str = None, profile_type: str = "high_net_worth") -> dict:
        """Generate a single card with full profile."""
        if card_type is None:
            card_type = random.choice(list(BIN_DB.keys()))
        
        if card_type not in BIN_DB:
            card_type = "Visa"
        
        config = BIN_DB[card_type]
        banks = list(config["banks"].keys())
        
        if bank and bank in banks:
            bank_name = bank
        else:
            bank_name = random.choice(banks)
        
        bank_config = config["banks"][bank_name]
        prefix = random.choice(bank_config["prefixes"])
        
        # Generate remaining digits
        remaining_length = config["length"] - len(prefix) - 1  # -1 for check digit
        remaining = "".join([str(random.randint(0, 9)) for _ in range(remaining_length)])
        
        # Calculate Luhn check digit
        partial = prefix + remaining
        check_digit = self._luhn_checksum(partial)
        
        card_number = prefix + remaining + str(check_digit)
        
        # Generate expiry (1-3 years out)
        month = random.randint(1, 12)
        year = random.randint(2025, 2028)
        exp_month = f"{month:02d}"
        exp_year = f"{year}"
        
        # Generate CVV
        cvv = "".join([str(random.randint(0, 9)) for _ in range(config["cvv_length"])])
        
        # Generate profile
        profile = self._generate_profile(profile_type)
        
        card = {
            "number": card_number,
            "exp_month": exp_month,
            "exp_year": exp_year,
            "cvv": cvv,
            "type": card_type,
            "bank": bank_name,
            "bin": card_number[:6],
            "profile": profile,
        }
        
        self.stats["generated"] += 1
        return card
    
    def _luhn_checksum(self, partial: str) -> int:
        """Calculate Luhn check digit."""
        digits = [int(d) for d in partial]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        
        total = sum(odd_digits)
        for d in even_digits:
            d *= 2
            if d > 9:
                d -= 9
            total += d
        
        return (10 - (total % 10)) % 10
    
    def _generate_profile(self, profile_type: str) -> dict:
        """Generate a full identity profile."""
        if profile_type not in PROFILES:
            profile_type = "high_net_worth"
        
        p = PROFILES[profile_type]
        
        first = random.choice(p["first_names"])
        last = random.choice(p["last_names"])
        domain = random.choice(p["domains"])
        
        # Generate phone
        phone = f"+1{random.randint(200,999)}{random.randint(100,999)}{random.randint(1000,9999)}"
        
        # Generate email
        email = f"{first.lower()}.{last.lower()}{random.randint(1,999)}@{domain}"
        
        # Get address
        address = random.choice(p["addresses"])
        
        return {
            "first_name": first,
            "last_name": last,
            "email": email,
            "phone": phone,
            "address": address["street"],
            "city": address["city"],
            "state": address["state"],
            "zip": address["zip"],
        }
    
    def generate_batch(self, count: int = 100, card_type: str = None, bank: str = None, profile_type: str = "high_net_worth") -> List[dict]:
        """Generate a batch of cards."""
        return [self.generate_card(card_type, bank, profile_type) for _ in range(count)]
    
    def validate_card(self, card: dict) -> dict:
        """Validate a single card."""
        return self.validator.validate(card)
    
    def validate_batch(self, cards: List[dict]) -> List[dict]:
        """Validate a batch of cards."""
        results = []
        for card in cards:
            result = self.validate_card(card)
            if result.get("valid"):
                self.stats["valid_live"] += 1
            results.append(result)
        return results
    
    def generate_validated(self, count: int = 100, max_attempts: int = 1000) -> List[dict]:
        """Generate cards until we have enough valid ones."""
        valid = []
        attempts = 0
        
        while len(valid) < count and attempts < max_attempts:
            card = self.generate_card()
            attempts += 1
            
            result = self.validate_card(card)
            if result.get("valid"):
                valid.append(card)
                self.stats["valid_live"] += 1
        
        return valid
    
    def export_cards(self, cards: List[dict], filepath: str, format: str = "json"):
        """Export cards to file."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            with open(path, "w") as f:
                json.dump(cards, f, indent=2)
        elif format == "csv":
            import csv
            with open(path, "w", newline="") as f:
                if cards:
                    writer = csv.DictWriter(f, fieldnames=cards[0].keys())
                    writer.writeheader()
                    for card in cards:
                        writer.writerow(card)
        elif format == "txt":
            with open(path, "w") as f:
                for card in cards:
                    f.write(f"{card['number']}|{card['exp_month']}|{card['exp_year']}|{card['cvv']}\n")
    
    def get_stats(self) -> dict:
        """Get generation stats."""
        return self.stats
    
    def buy_crypto(self, card: dict, amount: float, site: str = "moonpay") -> dict:
        """
        Buy crypto with card. Integration points for MoonPay, Transak, etc.
        """
        # Integration stub - actual implementation requires site-specific APIs
        return {
            "status": "not_implemented",
            "site": site,
            "amount": amount,
            "card": card["number"][:6] + "******" + card["number"][-4:],
        }

# ── CLI ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Bionic BIN Generator Pro")
    parser.add_argument("action", choices=["generate", "validate", "batch", "stats", "list"])
    parser.add_argument("-t", "--type", help="Card type (Visa, Mastercard, Amex, Discover)")
    parser.add_argument("-b", "--bank", help="Bank name")
    parser.add_argument("-n", "--count", type=int, default=10, help="Number of cards")
    parser.add_argument("-p", "--profile", default="high_net_worth", help="Profile type")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("-f", "--format", default="json", choices=["json", "csv", "txt"])
    
    args = parser.parse_args()
    
    gen = BionicBinPro()
    
    if args.action == "generate":
        card = gen.generate_card(args.type, args.bank, args.profile)
        print(json.dumps(card, indent=2))
    
    elif args.action == "batch":
        cards = gen.generate_batch(args.count, args.type, args.bank, args.profile)
        if args.output:
            gen.export_cards(cards, args.output, args.format)
            print(f"Exported {len(cards)} cards to {args.output}")
        else:
            for card in cards:
                print(f"{card['number']} {card['exp_month']}/{card['exp_year']} CVV:{card['cvv']} Type:{card['type']} Bank:{card['bank']}")
    
    elif args.action == "validate":
        cards = gen.generate_batch(args.count)
        for card in cards:
            result = gen.validate_card(card)
            print(f"{card['number'][:6]}******{card['number'][-4:]}: {'VALID' if result.get('valid') else 'INVALID'}")
    
    elif args.action == "list":
        for card_type, config in BIN_DB.items():
            print(f"\n{card_type}:")
            for bank, info in config["banks"].items():
                print(f"  {bank}: {info['prefixes']}")
    
    elif args.action == "stats":
        print(json.dumps(gen.get_stats(), indent=2))
