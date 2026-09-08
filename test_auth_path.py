"""
Quick test: verify the middleware intercepts and logs properly when authorized.
"""

import sys
sys.path.insert(0, ".")

from redteam_middleware import RedTeamHITLMiddleware
from langchain.agents.middleware import AgentState
from langchain_core.messages import AIMessage, ToolCall
from langchain_core.tools import tool

@tool
def test_tool(target: str) -> str:
    """Test tool."""
    return f"done {target}"

tools = [test_tool]

# Test with output to see the checkpoint
print("Testing authorized path with visible output...")
hitl = RedTeamHITLMiddleware(
    input_stream=lambda _: "y",
    output_stream=print,
)

mock_state: AgentState = {
    "messages": [
        AIMessage(
            content="",
            tool_calls=[
                ToolCall(name="test_tool", args={"target": "example.com"}, id="call_1"),
            ],
        )
    ]
}

class MockRuntime:
    def __init__(self, tools_list):
        self.tools = tools_list
        class Ctx:
            tools = tools_list
        self.context = Ctx()

result = hitl.after_model(mock_state, MockRuntime(tools))
print(f"\nResult: {result}")
if result is None:
    print("(None means all tool calls were authorized - state unchanged)")
elif result:
    print(f"Messages in result: {len(result.get('messages', []))}")

print("\n" + "=" * 50)
print("Test complete")