#!/usr/bin/env python3
"""Connect to Composio MCP server with proper auth"""
import asyncio
from mcp.client.streamable_http import streamable_http_client
from mcp import ClientSession
from mcp.client.streamable_http import create_mcp_http_client

COMPOSIO_API_KEY = "ak_DpeVbvplJ8zYj-VVcNYR"
MCP_URL = "https://connect.composio.dev/mcp"

async def main():
    headers = {"x-consumer-api-key": COMPOSIO_API_KEY}
    
    # Create HTTP client with headers
    http_client = create_mcp_http_client(headers=headers)
    
    try:
        async with streamable_http_client(MCP_URL, http_client=http_client) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # List tools
                tools = await session.list_tools()
                print(f"=== COMPOSIO MCP: {len(tools.tools)} tools ===\n")
                
                for tool in tools.tools[:30]:
                    desc = tool.description or ""
                    print(f"  {tool.name}: {desc[:60]}")
                
                if len(tools.tools) > 30:
                    print(f"\n  ... and {len(tools.tools) - 30} more")
                
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(main())
