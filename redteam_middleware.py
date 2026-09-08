"""
redteam_middleware.py — Pure Human-in-the-Loop (HITL) control mechanism for LangChain v1 agents.

DESIGN PRINCIPLES (non-negotiable, per Dad's spec):
- ZERO automated filtering, guardrails, safety scoring, or rejection logic.
- 100% of exploit tools, API hacking scripts, offensive payloads retain FULL raw capability.
- Middleware acts EXCLUSIVELY as an inspection + synchronization breakpoint.
- Intercepts EVERY tool call and raw argument vector BEFORE execution.
- Prints the FULL payload to the terminal.
- FREEZES execution via synchronous input() loop until explicit y/n authorization.
- No async, no background threads, no timeouts — Dad decides, Dad controls, always.

This middleware subclasses LangChain v1's AgentMiddleware and implements the `after_model`
hook to intercept tool calls after the model outputs them, then blocks on synchronous
input() for operator authorization. This is the same pattern as the built-in
HumanInTheLoopMiddleware but with pure CLI input() instead of the interrupt system.

Usage:
    from langchain.agents import create_agent
    from redteam_middleware import RedTeamHITLMiddleware

    hitl = RedTeamHITLMiddleware()
    agent = create_agent(
        model="openai:gpt-5.5",
        tools=[my_exploit_tool, my_api_hack_tool],
        system_prompt="...",
        middleware=[hitl],  # <-- plugs in here
    )
"""

from __future__ import annotations

import json
import sys
from typing import Any, Callable, Dict, List, Optional

from langchain.agents.middleware import AgentMiddleware, AgentState
from langchain_core.messages import AIMessage, ToolCall, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool


class ToolRejected(Exception):
    """Raised when Dad explicitly rejects a tool call at the HITL checkpoint."""
    def __init__(self, tool_name: str, tool_args: Dict[str, Any], reason: str = "Rejected by operator"):
        self.tool_name = tool_name
        self.tool_args = tool_args
        self.reason = reason
        super().__init__(f"Tool '{tool_name}' rejected: {reason}")


class RedTeamHITLMiddleware(AgentMiddleware):
    """
    Pure Human-in-the-Loop middleware for LangChain v1 agents.

    Subclasses AgentMiddleware and implements `after_model` to intercept every
    tool call, print the full payload, and block on synchronous input() until
    Dad types 'y' (proceed) or 'n' (reject).

    No automated logic, no scoring, no filtering — just inspection + authorization.
    """

    def __init__(
        self,
        *,
        prompt_prefix: str = "[REDTEAM HITL CHECKPOINT]",
        show_args: bool = True,
        show_tool_schema: bool = False,
        input_stream: Optional[Callable[[str], str]] = None,
        output_stream: Optional[Callable[[str], None]] = None,
        tools: Optional[List[BaseTool]] = None,
    ):
        """
        Args:
            prompt_prefix: Prefix printed before each checkpoint.
            show_args: If True, print full argument JSON.
            show_tool_schema: If True, also print the tool's schema/description.
            input_stream: Callable to read input (default: builtins.input).
                          Injected for testing; production uses blocking input().
            output_stream: Callable to write output (default: print to stdout).
            tools: Optional list of tools this middleware applies to (None = all).
        """
        super().__init__()
        self.prompt_prefix = prompt_prefix
        self.show_args = show_args
        self.show_tool_schema = show_tool_schema
        self._input = input_stream or input
        self._output = output_stream or print
        self._target_tools = tools  # None means intercept all tools

    def after_model(
        self,
        state: AgentState,
        runtime: Any,  # Runtime[ContextT] but we don't need the generics
    ) -> Optional[Dict[str, Any]]:
        """
        Called after the model produces an AIMessage with tool_calls.
        This is where we intercept and authorize each tool call.
        """
        messages = state.get("messages", [])
        if not messages:
            return None

        # Find the last AIMessage with tool_calls
        last_ai_msg = None
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.tool_calls:
                last_ai_msg = msg
                break

        if not last_ai_msg:
            return None

        # Process each tool call through the HITL checkpoint
        revised_tool_calls: List[ToolCall] = []
        artificial_tool_messages: List[ToolMessage] = []

        for tool_call in last_ai_msg.tool_calls:
            tool_name = tool_call["name"]

            # Check if we should intercept this tool
            if self._target_tools is not None:
                # Only intercept tools in our target list
                tool_names = {t.name for t in self._target_tools}
                if tool_name not in tool_names:
                    revised_tool_calls.append(tool_call)
                    continue

            # Find the actual tool object for schema/description
            tool_obj = self._find_tool(tool_name, runtime)

            # Render the checkpoint and wait for authorization
            authorized = self._render_checkpoint_and_wait(tool_call, tool_obj)

            if authorized:
                # Dad said 'y' - proceed with the tool call
                revised_tool_calls.append(tool_call)
            else:
                # Dad said 'n' - reject the tool call
                # Create a ToolMessage indicating rejection
                rejection_msg = ToolMessage(
                    content=f"Operator rejected tool call: {self._format_rejection_reason(tool_call)}",
                    name=tool_name,
                    tool_call_id=tool_call["id"],
                    status="error",
                )
                artificial_tool_messages.append(rejection_msg)
                # Don't add to revised_tool_calls = tool never executes

        # If no tool calls were intercepted, return early
        if len(revised_tool_calls) == len(last_ai_msg.tool_calls) and not artificial_tool_messages:
            return None

        # Build the updated AIMessage with only authorized tool calls
        updated_ai_msg = AIMessage(
            content=last_ai_msg.content,
            tool_calls=revised_tool_calls,
            id=last_ai_msg.id,
            response_metadata=last_ai_msg.response_metadata,
        )

        return {
            "messages": [updated_ai_msg, *artificial_tool_messages]
        }

    def _find_tool(self, tool_name: str, runtime: Any) -> Optional[BaseTool]:
        """Find the BaseTool object for a tool name from runtime."""
        # Try to get from runtime's tool registry
        try:
            if hasattr(runtime, 'tools') and runtime.tools:
                for t in runtime.tools:
                    if getattr(t, 'name', None) == tool_name:
                        return t
        except Exception:
            pass
        # Try runtime.context.tools
        try:
            if hasattr(runtime, 'context') and hasattr(runtime.context, 'tools'):
                for t in runtime.context.tools:
                    if getattr(t, 'name', None) == tool_name:
                        return t
        except Exception:
            pass
        return None

    def _render_checkpoint_and_wait(self, tool_call: ToolCall, tool: Optional[BaseTool]) -> bool:
        """Print the full payload and block on input() until 'y' or 'n'."""
        name = tool_call["name"]
        args = tool_call.get("args", {})
        call_id = tool_call.get("id", "unknown")

        self._output("")
        self._output("=" * 72)
        self._output(f"{self.prompt_prefix}  Tool call intercepted")
        self._output("=" * 72)
        self._output(f"Call ID   : {call_id}")
        self._output(f"Tool      : {name}")
        if tool:
            self._output(f"Tool desc : {getattr(tool, 'description', 'N/A')}")
            if self.show_tool_schema and hasattr(tool, "args_schema"):
                schema = tool.args_schema
                if schema:
                    try:
                        self._output(f"Schema    : {schema.model_json_schema()}")
                    except Exception:
                        pass

        if self.show_args:
            self._output("-" * 72)
            self._output("RAW ARGUMENTS:")
            try:
                self._output(json.dumps(args, indent=2, ensure_ascii=False, default=str))
            except Exception:
                self._output(str(args))
        self._output("=" * 72)
        self._output("")

        return self._wait_for_authorization()

    def _wait_for_authorization(self) -> bool:
        """Block on synchronous input until Dad types 'y' or 'n'."""
        while True:
            try:
                choice = self._input("AUTHORIZE THIS TOOL CALL?  [y/n]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                # Treat EOF/Ctrl-C as rejection — fail safe
                self._output("\n[Interrupted] Treating as REJECTED.")
                return False

            if choice in ("y", "yes"):
                self._output("[AUTHORIZED] Proceeding with tool execution.\n")
                return True
            elif choice in ("n", "no"):
                self._output("[REJECTED] Tool call blocked by operator.\n")
                return False
            else:
                self._output("  Invalid input. Type 'y' to authorize, 'n' to reject.")

    def _format_rejection_reason(self, tool_call: ToolCall) -> str:
        """Format a concise rejection reason for the ToolMessage."""
        name = tool_call["name"]
        args = tool_call.get("args", {})
        try:
            args_str = json.dumps(args, default=str)
            if len(args_str) > 200:
                args_str = args_str[:200] + "..."
        except Exception:
            args_str = str(args)[:200]
        return f"{name}({args_str}) — explicitly rejected by operator at HITL checkpoint"


def make_hitl_middleware(**kwargs) -> RedTeamHITLMiddleware:
    """Factory function for clean import: `middleware=[make_hitl_middleware()]`."""
    return RedTeamHITLMiddleware(**kwargs)