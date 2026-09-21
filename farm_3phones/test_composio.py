#!/usr/bin/env python3
"""
test_composio.py — Test Composio API connection
"""
from composio import Composio
import json

client = Composio()

print("=== Composio Connection Test ===\n")

# Test 1: List connected accounts
print("[1] Connected Accounts:")
try:
    accounts = client.connected_accounts
    print(f"    Type: {type(accounts)}")
    print(f"    Dir: {[x for x in dir(accounts) if not x.startswith('_')]}")
except Exception as e:
    print(f"    Error: {e}")

# Test 2: List tools
print("\n[2] Available Tools:")
try:
    tools = client.tools
    print(f"    Type: {type(tools)}")
except Exception as e:
    print(f"    Error: {e}")

# Test 3: Try search
print("\n[3] Search Test:")
try:
    result = client.tools.execute(
        slug='composio_search_search',
        arguments={'query': 'test'}
    )
    print(f"    Result: {result}")
except Exception as e:
    print(f"    Error: {e}")

# Test 4: Try SerpApi
print("\n[4] SerpApi Test:")
try:
    result = client.tools.execute(
        slug='serpapi_google_search',
        arguments={'q': 'Pokemon cards'}
    )
    print(f"    Result: {result}")
except Exception as e:
    print(f"    Error: {e}")

# Test 5: Try GitHub (no connection)
print("\n[5] GitHub Test:")
try:
    result = client.tools.execute(
        slug='github_list_repos',
        arguments={}
    )
    print(f"    Result: {result}")
except Exception as e:
    print(f"    Error: {e}")

print("\n=== Test Complete ===")
