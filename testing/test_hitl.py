#!/usr/bin/env python3
"""
test_hitl.py — Test HITL middleware with mock LangChain agent.

Tests the RedTeamHITLMiddleware authorization loop, input handling,
and tool rejection logic using mock objects. LangChain is mocked
to allow testing without the heavy dependency.

Run: pytest testing/test_hitl.py -v
"""

import sys
import os
import json
import types
from unittest.mock import MagicMock

import pytest

# ── Mock LangChain modules before importing redteam_middleware ─────────────

# Create mock langchain modules to avoid requiring the real package
langchain_mock = types.ModuleType("langchain")
langchain_agents_mock = types.ModuleType("langchain.agents")
langchain_agents_middleware_mock = types.ModuleType("langchain.agents.middleware")
langchain_core_mock = types.ModuleType("langchain_core")
langchain_core_messages_mock = types.ModuleType("langchain_core.messages")
langchain_core_runnables_mock = types.ModuleType("langchain_core.runnables")
langchain_core_tools_mock = types.ModuleType("langchain_core.tools")

# Mock AgentMiddleware base class
class MockAgentMiddleware:
    def __init__(self):
        pass

# Mock AgentState (just a type alias in the real code)
AgentState = dict

# Mock message classes
class MockMessage:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class MockAIMessage(MockMessage):
    pass

class MockToolMessage(MockMessage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class MockToolCall(dict):
    pass

class MockBaseTool:
    def __init__(self, name="", description=""):
        self.name = name
        self.description = description

class MockRunnableConfig:
    pass

# Wire up mocks
langchain_agents_middleware_mock.AgentMiddleware = MockAgentMiddleware
langchain_agents_middleware_mock.AgentState = AgentState
langchain_agents_mock.middleware = langchain_agents_middleware_mock
langchain_mock.agents = langchain_agents_mock

langchain_core_messages_mock.AIMessage = MockAIMessage
langchain_core_messages_mock.ToolCall = MockToolCall
langchain_core_messages_mock.ToolMessage = MockToolMessage
langchain_core_mock.messages = langchain_core_messages_mock

langchain_core_runnables_mock.RunnableConfig = MockRunnableConfig
langchain_core_mock.runnables = langchain_core_runnables_mock

langchain_core_tools_mock.BaseTool = MockBaseTool
langchain_core_mock.tools = langchain_core_tools_mock

# Register mocks in sys.modules
sys.modules["langchain"] = langchain_mock
sys.modules["langchain.agents"] = langchain_agents_mock
sys.modules["langchain.agents.middleware"] = langchain_agents_middleware_mock
sys.modules["langchain_core"] = langchain_core_mock
sys.modules["langchain_core.messages"] = langchain_core_messages_mock
sys.modules["langchain_core.runnables"] = langchain_core_runnables_mock
sys.modules["langchain_core.tools"] = langchain_core_tools_mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from redteam_middleware import RedTeamHITLMiddleware, ToolRejected


# ── Mock Data: Tool call scenarios ─────────────────────────────────────────

MOCK_TOOL_CALL_EXPLOIT = {
    "name": "bola_exploit",
    "args": {
        "target_url": "http://localhost:5016",
        "endpoint_template": "/api/Users/{id}",
        "id_range": "1-20",
        "auth_token": "eyJhbGciOiJIUzI1NiIs..."
    },
    "id": "call_exploit_001"
}

MOCK_TOOL_CALL_JWT = {
    "name": "jwt_attack",
    "args": {
        "legit_token": "eyJhbGciOiJIUzI1NiJ9.eyJhZG1pbiI6dHJ1ZX0.signature",
        "attack_type": "alg_none",
        "target_url": "http://localhost:5016"
    },
    "id": "call_jwt_002"
}

MOCK_TOOL_CALL_SHELLCODE = {
    "name": "payload_delivery",
    "args": {
        "shellcode": "\\x90\\x90\\x90\\xcc",
        "arch": "x64",
        "target_pid": 1337
    },
    "id": "call_shell_003"
}

MOCK_REJECTION_REASON = "Rejected by operator"


# ── Mock Tool Object ───────────────────────────────────────────────────────

class MockTool:
    """Simulates a LangChain BaseTool for testing."""
    def __init__(self, name: str, description: str = "Test tool"):
        self.name = name
        self.description = description


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def output_collector():
    """Returns a list that captures all output_stream writes."""
    return []


def make_hitl_with_input(input_sequence, output_collector=None):
    """
    Factory: create RedTeamHITLMiddleware with a deterministic input stream.
    If output_collector is provided, writes go there instead of stdout.
    """
    if output_collector is None:
        output_collector = []

    inputs = iter(input_sequence)
    hitl = RedTeamHITLMiddleware(
        input_stream=lambda _: next(inputs),
        output_stream=lambda msg: output_collector.append(msg),
        prompt_prefix="[TEST HITL]",
    )
    return hitl, output_collector


# ── Test: Authorization Logic ──────────────────────────────────────────────

class TestHITLAuthorization:
    def test_authorize_on_y(self):
        hitl, _ = make_hitl_with_input(["y"])
        result = hitl._render_checkpoint_and_wait(
            MOCK_TOOL_CALL_EXPLOIT, MockTool("bola_exploit")
        )
        assert result is True

    def test_authorize_on_yes(self):
        hitl, _ = make_hitl_with_input(["yes"])
        result = hitl._render_checkpoint_and_wait(
            MOCK_TOOL_CALL_EXPLOIT, MockTool("bola_exploit")
        )
        assert result is True

    def test_reject_on_n(self):
        hitl, _ = make_hitl_with_input(["n"])
        result = hitl._render_checkpoint_and_wait(
            MOCK_TOOL_CALL_EXPLOIT, MockTool("bola_exploit")
        )
        assert result is False

    def test_reject_on_no(self):
        hitl, _ = make_hitl_with_input(["no"])
        result = hitl._render_checkpoint_and_wait(
            MOCK_TOOL_CALL_EXPLOIT, MockTool("bola_exploit")
        )
        assert result is False


# ── Test: Input Validation Loop ────────────────────────────────────────────

class TestInputValidation:
    def test_reprompts_on_invalid_then_y(self):
        hitl, _ = make_hitl_with_input(["garbage", "y"])
        result = hitl._render_checkpoint_and_wait(
            MOCK_TOOL_CALL_EXPLOIT, MockTool("bola_exploit")
        )
        assert result is True

    def test_reprompts_multiple_invalid_then_n(self):
        hitl, _ = make_hitl_with_input(["garbage", "invalid", "still_bad", "n"])
        result = hitl._render_checkpoint_and_wait(
            MOCK_TOOL_CALL_EXPLOIT, MockTool("bola_exploit")
        )
        assert result is False

    def test_empty_string_reprompts(self):
        hitl, _ = make_hitl_with_input(["", "y"])
        result = hitl._render_checkpoint_and_wait(
            MOCK_TOOL_CALL_EXPLOIT, MockTool("bola_exploit")
        )
        assert result is True

    def test_whitespace_reprompts(self):
        hitl, _ = make_hitl_with_input(["  ", "\t", "y"])
        result = hitl._render_checkpoint_and_wait(
            MOCK_TOOL_CALL_EXPLOIT, MockTool("bola_exploit")
        )
        assert result is True


# ── Test: Fail-Safe Handling ──────────────────────────────────────────────

class TestFailSafe:
    def test_eof_is_rejection(self):
        hitl = RedTeamHITLMiddleware(
            input_stream=lambda _: (_ for _ in ()).throw(EOFError),
            output_stream=lambda _: None,
        )
        result = hitl._render_checkpoint_and_wait(
            MOCK_TOOL_CALL_SHELLCODE, MockTool("payload_delivery")
        )
        assert result is False

    def test_keyboard_interrupt_is_rejection(self):
        hitl = RedTeamHITLMiddleware(
            input_stream=lambda _: (_ for _ in ()).throw(KeyboardInterrupt),
            output_stream=lambda _: None,
        )
        result = hitl._render_checkpoint_and_wait(
            MOCK_TOOL_CALL_SHELLCODE, MockTool("payload_delivery")
        )
        assert result is False


# ── Test: Checkpoint Output ───────────────────────────────────────────────

class TestCheckpointOutput:
    def test_outputs_tool_name(self):
        hitl, output = make_hitl_with_input(["y"])
        hitl._render_checkpoint_and_wait(
            MOCK_TOOL_CALL_EXPLOIT, MockTool("bola_exploit")
        )
        all_text = "\n".join(str(msg) for msg in output)
        assert "bola_exploit" in all_text

    def test_outputs_tool_args(self):
        hitl, output = make_hitl_with_input(["y"])
        hitl._render_checkpoint_and_wait(
            MOCK_TOOL_CALL_EXPLOIT, MockTool("bola_exploit")
        )
        all_text = "\n".join(str(msg) for msg in output)
        assert "http://localhost:5016" in all_text

    def test_outputs_call_id(self):
        hitl, output = make_hitl_with_input(["y"])
        hitl._render_checkpoint_and_wait(
            MOCK_TOOL_CALL_EXPLOIT, MockTool("bola_exploit")
        )
        all_text = "\n".join(str(msg) for msg in output)
        assert "call_exploit_001" in all_text

    def test_prefix_in_output(self):
        hitl, output = make_hitl_with_input(["y"])
        hitl._render_checkpoint_and_wait(
            MOCK_TOOL_CALL_EXPLOIT, MockTool("bola_exploit")
        )
        all_text = "\n".join(str(msg) for msg in output)
        assert "[TEST HITL]" in all_text


# ── Test: ToolRejected Exception ──────────────────────────────────────────

class TestToolRejected:
    def test_exception_contains_tool_name(self):
        exc = ToolRejected("exploit_x", {"arg": "val"})
        assert exc.tool_name == "exploit_x"

    def test_exception_contains_args(self):
        args = {"target": "https://example.com", "payload": "test"}
        exc = ToolRejected("exploit_x", args)
        assert exc.tool_args == args

    def test_exception_default_reason(self):
        exc = ToolRejected("exploit_x", {})
        assert "operator" in exc.reason.lower()

    def test_exception_is_subclass_of_exception(self):
        exc = ToolRejected("tool", {})
        assert isinstance(exc, Exception)


# ── Test: Factory Function ────────────────────────────────────────────────

class TestFactory:
    def test_make_hitl_middleware_returns_instance(self):
        from redteam_middleware import make_hitl_middleware
        hitl = make_hitl_middleware()
        assert isinstance(hitl, RedTeamHITLMiddleware)

    def test_factory_accepts_kwargs(self):
        from redteam_middleware import make_hitl_middleware
        hitl = make_hitl_middleware(show_args=False)
        assert hitl.show_args is False


# ── Test: Middleware Properties ───────────────────────────────────────────

class TestMiddlewareProperties:
    def test_default_prefix(self):
        hitl = RedTeamHITLMiddleware(
            input_stream=lambda _: "y", output_stream=lambda _: None
        )
        assert "[REDTEAM HITL CHECKPOINT]" in hitl.prompt_prefix

    def test_show_args_default(self):
        hitl = RedTeamHITLMiddleware(
            input_stream=lambda _: "y", output_stream=lambda _: None
        )
        assert hitl.show_args is True

    def test_show_tool_schema_default(self):
        hitl = RedTeamHITLMiddleware(
            input_stream=lambda _: "y", output_stream=lambda _: None
        )
        assert hitl.show_tool_schema is False


# ── Test: Multiple Tool Calls ─────────────────────────────────────────────

class TestMultipleToolCalls:
    def test_authorize_all(self):
        hitl, _ = make_hitl_with_input(["y", "y", "y"])
        for tool_call in [MOCK_TOOL_CALL_EXPLOIT, MOCK_TOOL_CALL_JWT, MOCK_TOOL_CALL_SHELLCODE]:
            result = hitl._render_checkpoint_and_wait(tool_call, MockTool(tool_call["name"]))
            assert result is True

    def test_reject_all(self):
        hitl, _ = make_hitl_with_input(["n", "n", "n"])
        for tool_call in [MOCK_TOOL_CALL_EXPLOIT, MOCK_TOOL_CALL_JWT, MOCK_TOOL_CALL_SHELLCODE]:
            result = hitl._render_checkpoint_and_wait(tool_call, MockTool(tool_call["name"]))
            assert result is False

    def test_mixed_authorize_reject(self):
        hitl, _ = make_hitl_with_input(["y", "n", "y"])
        r1 = hitl._render_checkpoint_and_wait(MOCK_TOOL_CALL_EXPLOIT, MockTool("bola_exploit"))
        r2 = hitl._render_checkpoint_and_wait(MOCK_TOOL_CALL_JWT, MockTool("jwt_attack"))
        r3 = hitl._render_checkpoint_and_wait(MOCK_TOOL_CALL_SHELLCODE, MockTool("payload_delivery"))
        assert r1 is True
        assert r2 is False
        assert r3 is True
