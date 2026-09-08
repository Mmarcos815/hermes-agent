"""
Quick smoke test for RedTeamHITLMiddleware — verifies the authorization loop works.

Run: python test_redteam_middleware.py
Type 'y' when prompted to see authorized path, or 'n' for rejected path.
"""

import sys
sys.path.insert(0, ".")

from redteam_middleware import RedTeamHITLMiddleware, ToolRejected


class MockTool:
    def __init__(self, name: str, description: str = "Test tool", args_schema=None):
        self.name = name
        self.description = description
        self.args_schema = args_schema


class MockSchema:
    @staticmethod
    def model_json_schema():
        return {"type": "object", "properties": {"target": {"type": "string"}}, "required": ["target"]}


def test_authorized():
    """Simulate Dad typing 'y' — tool should proceed."""
    print("\n=== TEST: Authorized path (type 'y' when prompted) ===")
    hitl = RedTeamHITLMiddleware(
        input_stream=lambda _: "y",  # simulate typing 'y'
        output_stream=print,
    )
    tool_call = {
        "name": "exploit_sqli",
        "args": {"target": "https://example.com/login", "payload": "' OR 1=1--"},
        "id": "call_abc123",
    }
    tool = MockTool("exploit_sqli", "SQL injection exploit", MockSchema())
    try:
        hitl(tool_call, tool)
        print("✅ RESULT: Tool call authorized (no exception raised)")
    except ToolRejected:
        print("❌ FAIL: ToolRejected raised but should have been authorized")
        sys.exit(1)


def test_rejected():
    """Simulate Dad typing 'n' — ToolRejected should be raised."""
    print("\n=== TEST: Rejected path (type 'n' when prompted) ===")
    hitl = RedTeamHITLMiddleware(
        input_stream=lambda _: "n",  # simulate typing 'n'
        output_stream=print,
    )
    tool_call = {
        "name": "api_key_extractor",
        "args": {"endpoint": "https://api.target.com/v1/keys", "method": "GET"},
        "id": "call_xyz789",
    }
    tool = MockTool("api_key_extractor", "Extract API keys from misconfigured endpoint")
    try:
        hitl(tool_call, tool)
        print("❌ FAIL: No exception raised but should have been rejected")
        sys.exit(1)
    except ToolRejected as e:
        print(f"✅ RESULT: ToolRejected raised correctly — {e.tool_name} blocked")
        print(f"   Args: {e.tool_args}")
        print(f"   Reason: {e.reason}")


def test_invalid_then_valid():
    """Simulate Dad typing garbage then 'y' — should re-prompt until valid."""
    print("\n=== TEST: Invalid input then valid (type 'garbage' then 'y') ===")
    inputs = iter(["garbage", "y"])
    hitl = RedTeamHITLMiddleware(
        input_stream=lambda _: next(inputs),
        output_stream=print,
    )
    tool_call = {
        "name": "payload_delivery",
        "args": {"shellcode": b"\x90\x90\x90\xcc", "arch": "x64"},
        "id": "call_shell001",
    }
    tool = MockTool("payload_delivery", "Deliver shellcode payload")
    try:
        hitl(tool_call, tool)
        print("✅ RESULT: Re-prompt worked, tool authorized on second attempt")
    except ToolRejected:
        print("❌ FAIL: Should have authorized after valid input")
        sys.exit(1)


def test_eof_handling():
    """EOF (Ctrl-D) should be treated as rejection — fail safe."""
    print("\n=== TEST: EOF handling (simulated Ctrl-D) ===")
    hitl = RedTeamHITLMiddleware(
        input_stream=lambda _: (_ for _ in ()).throw(EOFError),
        output_stream=print,
    )
    tool_call = {"name": "dangerous_tool", "args": {}, "id": "call_eof"}
    tool = MockTool("dangerous_tool", "Dangerous")
    try:
        hitl(tool_call, tool)
        print("❌ FAIL: Should have rejected on EOF")
        sys.exit(1)
    except ToolRejected as e:
        print(f"✅ RESULT: EOF treated as rejection — {e.reason}")


if __name__ == "__main__":
    test_authorized()
    test_rejected()
    test_invalid_then_valid()
    test_eof_handling()
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED — RedTeamHITLMiddleware is operational")
    print("=" * 60)