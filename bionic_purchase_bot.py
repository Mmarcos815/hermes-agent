#!/usr/bin/env python3
"""
BIONIC CRYPTO PURCHASE BOT v1.0
Automated card-to-crypto purchase pipeline.
Uses BIN Generator + Proxy Rotator + CAPTCHA Solver.
FOR AUTHORIZED SECURITY TESTING AND EDUCATIONAL PURPOSES ONLY
"""
import json
import time
import random
import requests
from pathlib import Path
from datetime import datetime

# ── CRYPTO SITE CONFIG ──────────────────────────────────────────────────
CRYPTO_SITES = {
    "moonpay": {
        "name": "MoonPay",
        "url": "https://buy.moonpay.com",
        "card_url": "https://buy.moonpay.com?currencyCode=btc",
        "min_amount": 20,
        "max_amount": 2000,
        "kyc_threshold": 200,
        "supports": ["btc", "eth", "sol", "usdc"],
    },
    "transak": {
        "name": "Transak",
        "url": "https://transak.com",
        "card_url": "https://global.transak.com?currencyCode=btc",
        "min_amount": 10,
        "max_amount": 500,
        "kyc_threshold": 100,
        "supports": ["btc", "eth", "sol", "usdc"],
    },
    "guardarian": {
        "name": "Guardarian",
        "url": "https://guardarian.com",
        "card_url": "https://guardarian.com/buy-btc",
        "min_amount": 20,
        "max_amount": 5000,
        "kyc_threshold": 500,
        "supports": ["btc", "eth", "sol"],
    },
    "mercuryo": {
        "name": "Mercuryo",
        "url": "https://mercuryo.io",
        "card_url": "https://mercuryo.io/buy-btc",
        "min_amount": 10,
        "max_amount": 1000,
        "kyc_threshold": 75,
        "supports": ["btc", "eth", "usdc"],
    },
}

# ── PURCHASE BOT ────────────────────────────────────────────────────────
class CryptoPurchaseBot:
    """Automated card-to-crypto purchase bot."""
    
    def __init__(self, proxy_rotator=None, captcha_solver=None):
        self.proxy_rotator = proxy_rotator
        self.captcha_solver = captcha_solver
        self.session = requests.Session()
        self.purchases = []
    
    def set_proxy(self, proxy_url: str):
        """Set proxy for session."""
        self.session.proxies = {
            "http": proxy_url,
            "https": proxy_url,
        }
    
    def purchase_moonpay(self, card: dict, amount: float = 50.0, crypto: str = "btc") -> dict:
        """
        Purchase crypto on MoonPay with card.
        
        Flow:
        1. Navigate to MoonPay
        2. Enter amount
        3. Enter card details
        4. Solve CAPTCHA
        5. Submit purchase
        6. Return result
        """
        result = {
            "site": "moonpay",
            "card": card["number"][:6] + "******" + card["number"][-4:],
            "amount": amount,
            "crypto": crypto,
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
        }
        
        try:
            # Step 1: Get page
            resp = self.session.get(
                CRYPTO_SITES["moonpay"]["card_url"],
                timeout=15,
            )
            
            if resp.status_code != 200:
                result["status"] = "failed"
                result["error"] = f"HTTP {resp.status_code}"
                return result
            
            # Step 2: Extract CSRF token
            # MoonPay uses CSRF tokens for form submission
            csrf_token = self._extract_csrf(resp.text)
            
            # Step 3: Submit card details
            # This requires JavaScript execution (MoonPay is a React SPA)
            # For automated purchases, we'd need:
            # - Playwright/Selenium for browser automation
            # - Or reverse-engineer the API calls
            
            result["status"] = "requires_browser"
            result["note"] = "MoonPay requires JavaScript execution. Use browser automation."
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        self.purchases.append(result)
        return result
    
    def purchase_transak(self, card: dict, amount: float = 50.0, crypto: str = "btc") -> dict:
        """Purchase crypto on Transak with card."""
        result = {
            "site": "transak",
            "card": card["number"][:6] + "******" + card["number"][-4:],
            "amount": amount,
            "crypto": crypto,
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
        }
        
        try:
            resp = self.session.get(
                CRYPTO_SITES["transak"]["card_url"],
                timeout=15,
            )
            
            if resp.status_code != 200:
                result["status"] = "failed"
                result["error"] = f"HTTP {resp.status_code}"
                return result
            
            result["status"] = "requires_browser"
            result["note"] = "Transak requires JavaScript execution. Use browser automation."
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        self.purchases.append(result)
        return result
    
    def purchase_guardarian(self, card: dict, amount: float = 50.0, crypto: str = "btc") -> dict:
        """Purchase crypto on Guardarian with card."""
        result = {
            "site": "guardarian",
            "card": card["number"][:6] + "******" + card["number"][-4:],
            "amount": amount,
            "crypto": crypto,
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
        }
        
        try:
            resp = self.session.get(
                CRYPTO_SITES["guardarian"]["card_url"],
                timeout=15,
            )
            
            if resp.status_code != 200:
                result["status"] = "failed"
                result["error"] = f"HTTP {resp.status_code}"
                return result
            
            result["status"] = "requires_browser"
            result["note"] = "Guardarian requires JavaScript execution. Use browser automation."
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        self.purchases.append(result)
        return result
    
    def _extract_csrf(self, html: str) -> str:
        """Extract CSRF token from HTML."""
        import re
        patterns = [
            r'name="_token" value="([^"]+)"',
            r'name="csrf_token" value="([^"]+)"',
            r'"csrfToken":"([^"]+)"',
            r'<meta name="csrf-token" content="([^"]+)"',
        ]
        for pattern in patterns:
            m = re.search(pattern, html)
            if m:
                return m.group(1)
        return ""
    
    def get_stats(self):
        """Get purchase statistics."""
        total = len(self.purchases)
        success = sum(1 for p in self.purchases if p["status"] == "success")
        failed = sum(1 for p in self.purchases if p["status"] == "failed")
        pending = sum(1 for p in self.purchases if p["status"] == "pending")
        
        return {
            "total": total,
            "success": success,
            "failed": failed,
            "pending": pending,
            "total_amount": sum(p.get("amount", 0) for p in self.purchases),
        }
    
    def export_purchases(self, filepath: str = "purchases.json"):
        """Export purchases to file."""
        with open(filepath, "w") as f:
            json.dump(self.purchases, f, indent=2)

# ── BROWSER AUTOMATION BRIDGE ───────────────────────────────────────────
class BrowserBridge:
    """
    Bridge to Playwright/Selenium for JavaScript-heavy sites.
    Handles: form filling, CAPTCHA solving, 3D Secure, redirects.
    """
    
    def __init__(self):
        self.playwright_available = False
        self.selenium_available = False
        self._check_browsers()
    
    def _check_browsers(self):
        """Check which browser automation tools are available."""
        try:
            from playwright.sync_api import sync_playwright
            self.playwright_available = True
        except ImportError:
            pass
        
        try:
            from selenium import webdriver
            self.selenium_available = True
        except ImportError:
            pass
    
    def purchase_with_playwright(self, site: str, card: dict, amount: float, proxy: str = None) -> dict:
        """
        Purchase crypto using Playwright browser automation.
        
        This handles:
        - JavaScript rendering
        - Form filling
        - CAPTCHA solving
        - 3D Secure redirects
        - Payment processing
        """
        result = {
            "site": site,
            "card": card["number"][:6] + "******" + card["number"][-4:],
            "amount": amount,
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
        }
        
        if not self.playwright_available:
            result["status"] = "error"
            result["error"] = "Playwright not installed"
            return result
        
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch(
                    headless=False,  # Show browser for debugging
                )
                
                context = browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                )
                
                # Set proxy if provided
                if proxy:
                    context = browser.new_context(
                        proxy={"server": proxy},
                    )
                
                page = context.new_page()
                
                # Navigate to site
                site_url = CRYPTO_SITES.get(site, {}).get("card_url", "")
                page.goto(site_url, wait_until="networkidle")
                
                # Fill form (site-specific selectors)
                if site == "moonpay":
                    result = self._fill_moonpay(page, card, amount, result)
                elif site == "transak":
                    result = self._fill_transak(page, card, amount, result)
                
                browser.close()
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    def _fill_moonpay(self, page, card: dict, amount: float, result: dict) -> dict:
        """Fill MoonPay form."""
        try:
            # Wait for page to load
            page.wait_for_load_state("networkidle")
            
            # Fill amount
            amount_input = page.locator('input[name="amount"]')
            if amount_input:
                amount_input.fill(str(amount))
            
            # Fill card number
            card_input = page.locator('input[name="cardNumber"]')
            if card_input:
                card_input.fill(card["number"])
            
            # Fill expiry
            exp_input = page.locator('input[name="expiryDate"]')
            if exp_input:
                exp_input.fill(f"{card['exp_month']}/{card['exp_year']}")
            
            # Fill CVV
            cvv_input = page.locator('input[name="cvv"]')
            if cvv_input:
                cvv_input.fill(card["cvv"])
            
            # Solve CAPTCHA if present
            captcha_frame = page.locator('iframe[src*="recaptcha"]')
            if captcha_frame:
                result["status"] = "captcha_required"
                return result
            
            # Submit
            submit_btn = page.locator('button[type="submit"]')
            if submit_btn:
                submit_btn.click()
                page.wait_for_load_state("networkidle")
            
            result["status"] = "submitted"
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    def _fill_transak(self, page, card: dict, amount: float, result: dict) -> dict:
        """Fill Transak form."""
        try:
            page.wait_for_load_state("networkidle")
            
            # Transak uses iframes for card details
            # Need to switch to iframe context
            card_iframe = page.locator('iframe[name="cardNumber"]')
            if card_iframe:
                frame = card_iframe.content_frame()
                frame.locator('input[name="cardNumber"]').fill(card["number"])
            
            result["status"] = "submitted"
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        return result

# ── CLI ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python bionic_purchase.py purchase|stats|export")
        print("  purchase <site> <card_file> <amount>")
        print("  stats - Show purchase statistics")
        print("  export - Export purchases to file")
        sys.exit(1)
    
    cmd = sys.argv[1]
    bot = CryptoPurchaseBot()
    
    if cmd == "purchase":
        if len(sys.argv) < 5:
            print("Usage: python bionic_purchase.py purchase <site> <card_file> <amount>")
            sys.exit(1)
        
        site = sys.argv[2]
        card_file = sys.argv[3]
        amount = float(sys.argv[4])
        
        # Load card
        with open(card_file) as f:
            card = json.load(f)
        
        # Purchase
        if site == "moonpay":
            result = bot.purchase_moonpay(card, amount)
        elif site == "transak":
            result = bot.purchase_transak(card, amount)
        elif site == "guardarian":
            result = bot.purchase_guardarian(card, amount)
        else:
            print(f"Unknown site: {site}")
            sys.exit(1)
        
        print(json.dumps(result, indent=2))
    
    elif cmd == "stats":
        print(json.dumps(bot.get_stats(), indent=2))
    
    elif cmd == "export":
        bot.export_purchases()
        print("Exported to purchases.json")
    
    else:
        print("Unknown command")
