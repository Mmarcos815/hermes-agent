#!/usr/bin/env python3
"""
web_analyzer.py — Web Checkout Analyzer subagent.

Given a URL, analyzes:
- Login form fields
- CSRF tokens
- Payment gateways
- API endpoints
- Session cookies
- Known vulnerabilities

Usage:
    python web_analyzer.py https://www.tcgplayer.com/login
"""

import sys
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("playwright not installed")
    sys.exit(1)


class WebAnalyzer:
    """Analyze web checkout pages."""
    
    def __init__(self, url: str, headless: bool = True):
        self.url = url
        self.headless = headless
        self.results = {}
    
    def analyze(self) -> Dict:
        """Full analysis of the target URL."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context()
            page = context.new_page()
            
            # Navigate
            try:
                page.goto(self.url, wait_until="networkidle", timeout=30000)
            except Exception as e:
                return {"error": str(e), "url": self.url}
            
            self.results["title"] = page.title()
            self.results["url"] = page.url
            self.results["content_length"] = len(page.content())
            
            # Analyze forms
            self.results["forms"] = self._analyze_forms(page)
            
            # Analyze CSRF
            self.results["csrf_tokens"] = self._find_csrf(page)
            
            # Analyze payment gateways
            self.results["payment_gateways"] = self._detect_payments(page)
            
            # Analyze cookies
            self.results["cookies"] = self._analyze_cookies(context)
            
            # Analyze API endpoints
            self.results["api_endpoints"] = self._find_api_endpoints(page)
            
            # Analyze JavaScript
            self.results["scripts"] = self._analyze_scripts(page)
            
            browser.close()
        
        return self.results
    
    def _analyze_forms(self, page) -> List[Dict]:
        """Analyze all forms on the page."""
        forms = page.locator("form")
        form_data = []
        for i in range(forms.count()):
            inputs = forms.nth(i).locator("input")
            inp_list = []
            for j in range(inputs.count()):
                name = inputs.nth(j).get_attribute("name") or ""
                inp_type = inputs.nth(j).get_attribute("type") or ""
                placeholder = inputs.nth(j).get_attribute("placeholder") or ""
                inp_list.append({
                    "name": name,
                    "type": inp_type,
                    "placeholder": placeholder
                })
            if inp_list:
                form_data.append({
                    "form_index": i,
                    "action": forms.nth(i).get_attribute("action") or "",
                    "method": forms.nth(i).get_attribute("method") or "GET",
                    "inputs": inp_list
                })
        return form_data
    
    def _find_csrf(self, page) -> List[Dict]:
        """Find CSRF tokens on the page."""
        csrf = page.locator("input[name*='csrf'], input[name*='_token'], input[name*='authenticity_token']")
        tokens = []
        for i in range(csrf.count()):
            name = csrf.nth(i).get_attribute("name") or ""
            value = csrf.nth(i).get_attribute("value") or ""
            tokens.append({"name": name, "value": value[:50]})
        return tokens
    
    def _detect_payments(self, page) -> List[str]:
        """Detect payment gateways."""
        content = page.content().lower()
        gateways = []
        for gw in ["stripe", "paypal", "braintree", "square", "authorize", "adyen", "shopify", "klarna", "affirm"]:
            if gw in content:
                gateways.append(gw)
        return gateways
    
    def _analyze_cookies(self, context) -> List[Dict]:
        """Analyze cookies."""
        cookies = context.cookies()
        return [{"name": c["name"], "domain": c["domain"], "value": c["value"][:50]} for c in cookies]
    
    def _find_api_endpoints(self, page) -> List[str]:
        """Find API endpoints in page source."""
        content = page.content()
        # Find fetch/XMLHttpRequest URLs
        endpoints = set()
        patterns = [
            r'fetch\(["\']([^"\']+)["\']',
            r'\.ajax\(\{[^}]*url:\s*["\']([^"\']+)["\']',
            r'axios\([\'"]([^\'"]+)[\'"]',
            r'url:\s*["\']([^"\']+/api/[^"\']+)["\']',
            r'url:\s*["\']([^"\']+/v[0-9]+/[^"\']+)["\']',
        ]
        for pat in patterns:
            for m in re.finditer(pat, content):
                endpoints.add(m.group(1))
        return sorted(endpoints)
    
    def _analyze_scripts(self, page) -> List[str]:
        """Analyze script sources."""
        scripts = page.locator("script")
        srcs = []
        for i in range(scripts.count()):
            src = scripts.nth(i).get_attribute("src") or ""
            if src:
                srcs.append(src)
        return srcs
    
    def summary(self) -> str:
        """Get a summary of findings."""
        if not self.results:
            self.analyze()
        
        lines = [
            "=" * 60,
            f"WEB ANALYZER: {self.url}",
            "=" * 60,
            f"Title: {self.results.get('title', 'N/A')}",
            f"Content length: {self.results.get('content_length', 0):,} bytes",
            "",
            f"FORMS: {len(self.results.get('forms', []))}",
        ]
        for f in self.results.get("forms", []):
            lines.append(f"  [{f.get('method', 'GET')}] {f.get('action', '/')}")
            for inp in f.get("inputs", []):
                lines.append(f"    - {inp['name']} ({inp['type']})")
        
        lines.extend([
            "",
            f"CSRF TOKENS: {len(self.results.get('csrf_tokens', []))}",
        ])
        for t in self.results.get("csrf_tokens", []):
            lines.append(f"  - {t['name']}: {t['value'][:30]}...")
        
        lines.extend([
            "",
            f"PAYMENT GATEWAYS: {', '.join(self.results.get('payment_gateways', [])) or 'None detected'}",
        ])
        
        lines.extend([
            "",
            f"COOKIES: {len(self.results.get('cookies', []))}",
        ])
        for c in self.results.get("cookies", [])[:10]:
            lines.append(f"  - {c['name']} (domain: {c['domain']})")
        
        lines.extend([
            "",
            f"API ENDPOINTS: {len(self.results.get('api_endpoints', []))}",
        ])
        for e in self.results.get("api_endpoints", [])[:10]:
            lines.append(f"  - {e}")
        
        lines.append("=" * 60)
        return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python web_analyzer.py <url>")
        print("Example: python web_analyzer.py https://www.tcgplayer.com/login")
        sys.exit(1)
    
    url = sys.argv[1]
    analyzer = WebAnalyzer(url, headless=True)
    analyzer.analyze()
    print(analyzer.summary())
