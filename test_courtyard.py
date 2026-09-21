#!/usr/bin/env python3
"""Deep research on Courtyard.io API"""
import requests
from pathlib import Path

url = "https://courtyard.io"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

results = []

# Test homepage
try:
    r = requests.get(url, headers=headers, timeout=15)
    results.append(("Homepage", r.status_code, r.text[:500]))
except Exception as e:
    results.append(("Homepage", "Error", str(e)))

# Test common API paths
api_paths = ["/api", "/api/v1", "/api/v1/status", "/docs", "/api-docs", "/graphql", "/health", "/status"]
for path in api_paths:
    try:
        r = requests.get(f"{url}{path}", headers=headers, timeout=10)
        results.append((path, r.status_code, r.text[:200]))
    except Exception as e:
        results.append((path, "Error", str(e)))

# Print results
for name, status, body in results:
    print(f"\n=== {name} ({status}) ===")
    print(body)
