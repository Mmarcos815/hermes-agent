#!/usr/bin/env python3
"""
Minimal MCP Server — Phase 3A learning project.

This MCP server exposes:
- Tools: echo, math_add, system_info
- Resources: hello://greeting, config://version
- Prompts: hello_world

Purpose: Learn the MCP protocol from the inside. Not a toy — actually works.
Transport: stdio (the simplest transport, the one to start with).

Reference: MCP specification — tool, resource, prompt primitives.
"""

import json
import os
import sys
import platform
from datetime import datetime

# ---------------------------------------------------------------------------
# MCP protocol helpers — these are the primitives the spec defines.
# Every MCP server needs to understand these message shapes.
# ---------------------------------------------------------------------------

def send(text: str) -> None:
    """Write a JSON-RPC message to stdout (the client reads stdin/stdout)."""
    sys.stdout.write(text + "\n")
    sys.stdout.flush()

def receive() -> dict:
    """Read one JSON-RPC message from stdin."""
    line = sys.stdin.readline()
    if not line:
        raise EOFError("MCP client disconnected")
    return json.loads(line)


# ---------------------------------------------------------------------------
# Tool definitions — what this server can DO.
# Each tool has: name, description, inputSchema (JSON Schema subset).
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "echo",
        "description": "Echo back a message. Useful for testing the MCP connection.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The message to echo back."
                }
            },
            "required": ["message"],
        },
    },
    {
        "name": "math_add",
        "description": "Add two numbers together. Simple but proves structured input/output works.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number."},
                "b": {"type": "number", "description": "Second number."},
            },
            "required": ["a", "b"],
        },
    },
    {
        "name": "system_info",
        "description": "Return basic system information. Shows how a tool can expose real data.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]


# ---------------------------------------------------------------------------
# Resource definitions — what this server can READ (read-only data).
# Resources are exposed as URIs with MIME types.
# ---------------------------------------------------------------------------

RESOURCES = [
    {
        "name": "hello",
        "description": "A friendly greeting resource.",
        "uriTemplate": "hello://greeting",
        "mimeType": "text/plain",
    },
    {
        "name": "config",
        "description": "Server version information.",
        "uriTemplate": "config://version",
        "mimeType": "application/json",
    },
]


# ---------------------------------------------------------------------------
# Prompt definitions — what this server can contribute to the system prompt.
# Prompts are template-based and can include variables.
# ---------------------------------------------------------------------------

PROMPTS = [
    {
        "name": "hello_world",
        "description": "A simple hello world prompt template.",
        "template": "Say hello to ${name} in a friendly way. Today is ${date}.",
        "arguments": [
            {
                "name": "name",
                "description": "Who to greet.",
                "required": True,
            },
            {
                "name": "date",
                "description": "What date to mention.",
                "required": False,
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# Tool handlers — the actual implementation of each tool.
# These are called when the client invokes a tool.
# ---------------------------------------------------------------------------

async def handle_echo(args: dict) -> dict:
    """Echo a message back."""
    return {"content": [{"type": "text", "text": args["message"]}]}


async def handle_math_add(args: dict) -> dict:
    """Add two numbers."""
    a = args["a"]
    b = args["b"]
    result = a + b
    return {
        "content": [
            {"type": "text", "text": f"{a} + {b} = {result}"}
        ]
    }


async def handle_system_info(args: dict) -> dict:
    """Return system information."""
    info = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "node": platform.node(),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    return {
        "content": [
            {"type": "text", "text": json.dumps(info, indent=2)}
        ]
    }


TOOL_HANDLERS = {
    "echo": handle_echo,
    "math_add": handle_math_add,
    "system_info": handle_system_info,
}


# ---------------------------------------------------------------------------
# Resource read — called when the client wants to read a resource.
# ---------------------------------------------------------------------------

async def read_resource(uri: str) -> dict:
    """Read a resource by URI and return its contents."""
    if uri == "hello://greeting":
        return {
            "contents": [
                {
                    "uri": "hello://greeting",
                    "mimeType": "text/plain",
                    "text": "Hello from the minimal MCP server! This server is built as a learning project to understand the MCP protocol from the inside."
                }
            ]
        }
    elif uri == "config://version":
        return {
            "contents": [
                {
                    "uri": "config://version",
                    "mimeType": "application/json",
                    "text": json.dumps({
                        "server": "minimal-mcp-server",
                        "version": "0.1.0",
                        "purpose": "MCP protocol learning project",
                        "transport": "stdio",
                        "capabilities": {
                            "tools": [t["name"] for t in TOOLS],
                            "resources": [r["name"] for r in RESOURCES],
                            "prompts": [p["name"] for p in PROMPTS],
                        },
                    }, indent=2)
                }
            ]
        }
    else:
        raise ValueError(f"Unknown resource URI: {uri}")


# ---------------------------------------------------------------------------
# Prompt template rendering — called when the client wants to use a prompt.
# ---------------------------------------------------------------------------

async def get_prompt(name: str, arguments: dict) -> dict:
    """Render a prompt template with the given arguments."""
    if name == "hello_world":
        template = "Say hello to ${name} in a friendly way. Today is ${date}."
        name_arg = arguments.get("name", "World")
        date_arg = arguments.get("date", datetime.utcnow().strftime("%Y-%m-%d"))
        rendered = template.replace("${name}", name_arg).replace("${date}", date_arg)
        return {
            "description": "A friendly greeting prompt",
            "messages": [
                {
                    "role": "user",
                    "content": {"type": "text", "text": rendered},
                }
            ],
        }
    else:
        raise ValueError(f"Unknown prompt: {name}")


# ---------------------------------------------------------------------------
# JSON-RPC dispatch — the MCP protocol is JSON-RPC over stdio.
# This is the core protocol logic: receive a request, dispatch to the
# right handler, return a response or error.
# ---------------------------------------------------------------------------

async def dispatch(request: dict) -> dict | None:
    """Dispatch a JSON-RPC request to the right handler.
    
    Args:
        request: The full JSON-RPC request dict (includes 'method', 'params',
                 'id', etc.)
    
    Returns:
        Response dict, or None for notifications (no response needed).
    """
    method = request.get("method", "")
    params = request.get("params", {})
    request_id = request.get("id")

    # --- Notifications (no id) need no response ---
    if request_id is None:
        return None

    # --- Tool calls ---
    if method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})
        if tool_name not in TOOL_HANDLERS:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Tool not found: {tool_name}",
                },
            }
        handler = TOOL_HANDLERS[tool_name]
        try:
            result = await handler(tool_args)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result,
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Tool execution error: {str(e)}",
                },
            }

    # --- Resources list ---
    elif method == "resources/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "resources": RESOURCES,
            },
        }

    # --- Resources read ---
    elif method == "resources/read":
        uri = params.get("uri")
        try:
            result = await read_resource(uri)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result,
            }
        except ValueError as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": str(e),
                },
            }

    # --- Resources subscribe (not implemented — return empty) ---
    elif method == "resources/subscribe":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {},
        }

    # --- Prompts list ---
    elif method == "prompts/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "prompts": PROMPTS,
            },
        }

    # --- Prompts get ---
    elif method == "prompts/get":
        name = params.get("name")
        arguments = params.get("arguments", {})
        try:
            result = await get_prompt(name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result,
            }
        except ValueError as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": str(e),
                },
            }

    # --- Tools list ---
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": TOOLS,
            },
        }

    # --- Tools call (already handled above, but keep for clarity) ---
    elif method == "tools/call":
        # Handled above
        pass

    # --- Initialize ---
    elif method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"list": {"tools": TOOLS}},
                    "resources": {"list": {"resources": RESOURCES}},
                    "prompts": {"list": {"prompts": PROMPTS}},
                },
                "serverInfo": {
                    "name": "minimal-mcp-server",
                    "version": "0.1.0",
                },
            },
        }

    # --- Notifications: initialized ---
    elif method == "notifications/initialized":
        # Client notifies server that it's initialized. No response needed.
        return None

    # --- Sampling — not implemented ---
    elif method == "sampling/create":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": "Sampling not supported by this server.",
            },
        }

    else:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}",
            },
        }


# ---------------------------------------------------------------------------
# Main loop — the server runs forever, processing one JSON-RPC message at
# a time. This is the stdio transport: one message in, one message out.
# ---------------------------------------------------------------------------

async def main():
    """Main server loop — process JSON-RPC messages from stdin.

    The MCP stdio transport: client sends JSON-RPC requests on stdin,
    server responds on stdout. Notifications (no 'id' field) are handled
    but generate no response.
    """
    while True:
        try:
            request = receive()
        except EOFError:
            break

        response = await dispatch(request)
        if response is not None:
            send(json.dumps(response))


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
