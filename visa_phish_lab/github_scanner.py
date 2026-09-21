#!/usr/bin/env python3
"""
GitHub Credential Scanner
Searches for leaked Visa/Mastercard API credentials in public repos.
FOR AUTHORIZED SECURITY TESTING ONLY - EDUCATIONAL PURPOSES ONLY
"""

import subprocess
import json
import re
import sys
import os

SEARCH_PATTERNS = [
    # Visa patterns
    "VISA_USER_ID",
    "VISA_PASSWORD",
    "VISA_KEY_PATH",
    "VISA_CERT_PATH",
    "VISA_BASE_URL",
    "sandbox.api.visa.com",
    "visa_api_key",
    "visa_user_id",
    "visa_password",
    "visa_cert",
    "visa_key",
    
    # Mastercard patterns
    "MASTERCARD_API_KEY",
    "MASTERCARD_SECRET",
    "MASTERCARD_CONSUMER_KEY",
    "sandbox.mastercard.com",
    "mastercard_api",
    "mastercard_key",
    "mastercard_secret",
    
    # Generic payment patterns
    "payment_gateway_api",
    "stripe_secret",
    "braintree_token",
    "cybersource_api",
]

def search_github():
    results = []
    
    for pattern in SEARCH_PATTERNS:
        print(f"[*] Searching for: {pattern}")
        
        try:
            result = subprocess.run(
                ["gh", "search", "code", pattern, "--limit", "20", "--json", "repository,path,textMatches"],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                for item in data:
                    repo = item.get('repository', {}).get('fullName', 'unknown')
                    path = item.get('path', 'unknown')
                    
                    # Extract actual credential values
                    for match in item.get('textMatches', []):
                        text = match.get('fragment', '')
                        
                        # Look for actual values (not just variable names)
                        if any(x in text for x in ['=V', '=AKC', 'apikey=', 'Bearer ', 'Basic ']):
                            results.append({
                                'pattern': pattern,
                                'repo': repo,
                                'path': path,
                                'match': text[:200],
                            })
                            print(f"  [!] FOUND: {repo}/{path}")
                            print(f"      Match: {text[:100]}...")
        
        except subprocess.TimeoutExpired:
            print(f"  [-] Timeout for pattern: {pattern}")
        except Exception as e:
            print(f"  [-] Error: {e}")
    
    return results

def scan_repo_for_certs(repo_name):
    """Scan a specific repo for certificate files"""
    print(f"\n[*] Scanning repo: {repo_name}")
    
    cert_patterns = [
        "*.pem",
        "*.key",
        "*.crt",
        "*.p12",
        "*.pfx",
        ".env",
        "*.env",
    ]
    
    found_certs = []
    
    for pattern in cert_patterns:
        try:
            result = subprocess.run(
                ["gh", "api", f"repos/{repo_name}/git/trees/main?recursive=1", "--jq", ".[].path"],
                capture_output=True, text=True, timeout=15
            )
            
            if result.returncode == 0:
                paths = result.stdout.strip().split('\n')
                for path in paths:
                    if any(path.endswith(ext) for ext in ['.pem', '.key', '.crt', '.p12', '.pfx']):
                        print(f"  [!] Certificate file found: {path}")
                        found_certs.append({
                            'repo': repo_name,
                            'file': path,
                            'type': 'certificate'
                        })
                    elif '.env' in path:
                        print(f"  [!] Env file found: {path}")
                        found_certs.append({
                            'repo': repo_name,
                            'file': path,
                            'type': 'env_file'
                        })
        
        except Exception as e:
            print(f"  [-] Error scanning {pattern}: {e}")
    
    return found_certs

if __name__ == '__main__':
    print("="*60)
    print("GitHub Credential Scanner - Visa/Mastercard")
    print("="*60)
    print()
    
    # Search for leaked credentials
    results = search_github()
    
    # Scan specific repos known to have Visa/Mastercard integration
    target_repos = [
        "silverlogic/CircleCredit---Backend---Django",
        "visahackathon2020/Backend",
        "norbertm09/hello_VisaDirect",
        "EdsonHs94/visa-api-java",
    ]
    
    cert_results = []
    for repo in target_repos:
        certs = scan_repo_for_certs(repo)
        cert_results.extend(certs)
    
    # Summary
    print("\n" + "="*60)
    print("SCAN SUMMARY")
    print("="*60)
    print(f"Credential matches found: {len(results)}")
    print(f"Certificate/env files found: {len(cert_results)}")
    
    # Save results
    output = {
        'credentials': results,
        'certificates': cert_results,
    }
    
    with open('github_scan_results.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nResults saved to: github_scan_results.json")
