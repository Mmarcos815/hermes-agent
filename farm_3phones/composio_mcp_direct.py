#!/usr/bin/env python3
"""
composio_mcp_direct.py — Connect to Composio MCP server directly
"""
import os
import json
import requests
from pathlib import Path

COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "ak_DpeVbvplJ8zYj-VVcNYR")
MCP_URL = "https://connect.composio.dev/mcp"

print("=== Composio MCP Direct Connection ===\n")
print(f"URL: {MCP_URL}")
print(f"Key: {COMPOSIO_API_KEY[:8]}...\n")

# Try SSE connection
headers = {
    "x-consumer-api-key": COMPOSIO_API_KEY,
    "Accept": "text/event-stream"
}

try:
    response = requests.get(MCP_URL, headers=headers, timeout=30, stream=True)
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    
    # Read first few lines of SSE
    for i, line in enumerate(response.iter_lines()):
        if i >= 10:
            break
        print(f"  {line}")
except Exception as e:
    print(f"SSE Error: {e}")

# Try JSON-RPC
print("\n=== JSON-RPC Test ===")
jsonrpc_headers = {
    "x-consumer-api-key": COMPOSIO_API_KEY,
    "Content-Type": "application/json"
}

payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
}

try:
    response = requests.post(MCP_URL, headers=jsonrpc_headers, json=payload, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text[:500]}")
except Exception as e:
    print(f"JSON-RPC Error: {e}")
