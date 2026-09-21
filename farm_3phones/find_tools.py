#!/usr/bin/env python3
"""Find correct Composio tool slugs"""
from composio import Composio

client = Composio()

# List tools properly
print("=== Finding Tools ===\n")

# Try different methods
try:
    # Method 1: get_raw_composio_tools with search
    tools = client.tools.get_raw_composio_tools(
        search="search",
        limit=20
    )
    print(f"Search tools: {tools}")
except Exception as e:
    print(f"Method 1 error: {e}")

try:
    # Method 2: with toolkit
    tools = client.tools.get_raw_composio_tools(
        toolkits=["COMPOSIOSEARCH"],
        limit=20
    )
    print(f"ComposioSearch: {tools}")
except Exception as e:
    print(f"Method 2 error: {e}")

try:
    # Method 3: list all toolkits
    toolkits = client.tools.get_raw_tool_router_meta_tools(limit=50)
    print(f"Toolkits: {toolkits}")
except Exception as e:
    print(f"Method 3 error: {e}")
