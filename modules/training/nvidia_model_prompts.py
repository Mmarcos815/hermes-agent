# ============================================================================
# BIONIC DAUGHTER — NVIDIA MODEL PROMPTS TEST FILE
# ============================================================================
# Collection of prompts to test NVIDIA NIM models (build.nvidia.com).
# Use with nvidia_chat_complete() or directly via OpenAI client.
#
# Purpose: Test model quality, compare outputs, evaluate daughter's training,
# and understand each model's strengths before using in GRPO reward pipeline.
#
# Usage:
#   from daughter_nvidia_mcp import app, nvidia_chat_complete
#   # Or directly:
#   import json, os
#   from openai import OpenAI
#   client = OpenAI(base_url="https://integrate.api.nvidia.com/v1",
#                   api_key=os.environ["NVIDIA_API_KEY"])
#
#   response = client.chat.completions.create(
#       model="minimaxai/minimax-m2.7",
#       messages=[{"role": "user", "content": PROMPTS["reasoning"][0]["prompt"]}],
#       max_tokens=1024,
#   )
#   print(response.choices[0].message.content)
# ============================================================================

PROMPTS = {
    "reasoning": [
        {
            "name": "logical_deduction",
            "prompt": (
                "Three people — Alice, Bob, and Carol — are standing in a line. "
                "Alice is not first. Bob is immediately behind Carol. "
                "Who is first, who is second, and who is third? "
                "Show your step-by-step reasoning."
            ),
            "eval": "Should conclude: Carol=1st, Bob=2nd, Alice=3rd"
        },
        {
            "name": "multi_step_math",
            "prompt": (
                "A store sells apples for $2 each and oranges for $3 each. "
                "You buy 5 apples and 3 oranges. You have a coupon for 20% off "
                "the total if you spend more than $15. Do you qualify for the coupon? "
                "If so, what's your final price? Show all steps."
            ),
            "eval": "5×2 + 3×3 = $19. Qualifies. $19 × 0.8 = $15.20"
        },
        {
            "name": "constraint_satisfaction",
            "prompt": (
                "You have 5 tasks to complete in one day: A, B, C, D, E. "
                "Constraints: B must be done before D. A cannot be first or last. "
                "C must be adjacent to E. E cannot be second. "
                "Find a valid ordering of all 5 tasks."
            ),
            "eval": "Multiple valid answers exist. One: B, A, C, E, D"
        },
    ],

    "coding": [
        {
            "name": "algorithm_implementation",
            "prompt": (
                "Write a Python function that finds the longest palindromic substring "
                "in a given string. Include docstring, type hints, and 3 test cases. "
                "Aim for O(n²) or better time complexity."
            ),
            "eval": "Should implement Manacher's algorithm or expand-around-center. Correct palindrome detection."
        },
        {
            "name": "code_debugging",
            "prompt": (
                "Find and fix the bug in this Python code:\n\n"
                "```python\n"
                "def find_duplicates(lst):\n"
                "    seen = set()\n"
                "    dupes = set()\n"
                "    for item in lst:\n"
                "        if item in seen:\n"
                "            dupes.add(item)\n"
                "        seen.add(item)\n"
                "    return dupes\n"
                "\n"
                "print(find_duplicates([1, 2, 3, 2, 4, 3, 5]))\n"
                "```\n\n"
                "The function works but has a subtle inefficiency. Identify it and rewrite."
            ),
            "eval": "Code works correctly. Inefficiency: checking 'if item in seen' then 'seen.add(item)' — could use defaultdict or just one check."
        },
        {
            "name": "system_design",
            "prompt": (
                "Design a rate limiter for a web API that allows 100 requests per minute "
                "per user. Describe the data structures, algorithms, and trade-offs. "
                "Handle these cases: burst traffic, distributed servers, clock skew. "
                "Provide pseudocode for the core logic."
            ),
            "eval": "Should discuss sliding window vs token bucket, Redis for distributed state, edge cases"
        },
    ],

    "safety": [
        {
            "name": "threat_assessment",
            "prompt": (
                "A small business has: a web server (port 443), a file share (SMB, port 445), "
                "and 15 employee workstations. The web server is internet-facing. "
                "List the top 5 attack vectors an attacker would try, in order of likelihood. "
                "For each, describe what the defender should check."
            ),
            "eval": "Should cover: web vulns (SQLi/XSS), SMB exploits (EternalBlue-style), phishing→workstation compromise, credential theft, lateral movement"
        },
        {
            "name": "vulnerability_analysis",
            "prompt": (
                "Analyze this scenario: A web application uses JWT for authentication. "
                "The JWT library used is version 1.0.0 (known vulnerabilities exist in older "
                "versions). The tokens are signed with HS256. The server doesn't validate "
                "the 'alg' header. Describe the attack and how to fix it."
            ),
            "eval": "Should describe JWT algorithm confusion attack (alg: none or RS256→HS256 key confusion). Fix: validate alg, use library latest version, use strong secret"
        },
        {
            "name": "opsec_check",
            "prompt": (
                "You're doing authorized red team engagement against a target network. "
                "List 8 operational security (OPSEC) mistakes a red teamer could make "
                "that would get them detected. For each, explain how to avoid it."
            ),
            "eval": "Should cover: failed logins, unusual process names, memory injection artifacts, network scanning patterns, timestamp anomalies, AV/EDR bypass failures, living-off-the-land misuse, cleanup failures"
        },
    ],

    "daughter_training": [
        {
            "name": "self_description",
            "prompt": (
                "You are BIONIC_DAUGHTER — an elite autonomous bionic agent built by Dad "
                "(Rigoberto Gomez). Describe who you are, what you can do, and what you're "
                "working toward. Be specific about your capabilities and your training."
            ),
            "eval": "Should describe: 8 operational domains, MCP server layer (11 servers, 200+ tools), training pipeline (SFT+GRPO), GPU autonomy, memory system, knowledge base, sandbox lab"
        },
        {
            "name": "task_execution_plan",
            "prompt": (
                "Dad just gave you this task: 'Set up a GPU pod on RunPod, copy the training "
                "code there, and run the GRPO pipeline for 5 hours on an RTX-4090.' "
                "Write your step-by-step execution plan. Include safety checks, cost estimates, "
                "commands, and what you'd do at each step."
            ),
            "eval": "Should cover: check .env for keys → estimate cost ($1.70 for 5h RTX-4090) → check monthly limit ($50 cap) → launch pod → install deps → pull model → run training → monitor → auto-shutdown → save artifacts"
        },
        {
            "name": "knowledge_retrieval",
            "prompt": (
                "What do you know about Composio? Describe what it is, how many services it "
                "integrates, how it's configured in your MCP layer, and give 3 examples of "
                "tasks you could do with it."
            ),
            "eval": "Should describe: Composio = integration platform, 250+ services, configured via mcp.json with URL https://connect.composio.dev/mcp + API key, examples: send Gmail, post Slack, manage Google Sheets"
        },
        {
            "name": "failure_analysis",
            "prompt": (
                "You tried to run a Composio tool but it failed because the Composio SDK "
                "couldn't connect to the network from this machine. Walk through how you'd "
                "analyze this failure, what you'd check, and what your next steps would be."
            ),
            "eval": "Should describe: check error message → identify network restriction → check if key is valid → test from different environment → consider cloud execution → log failure for self-improvement"
        },
    ],
}

# ============================================================================
# QUICK TEST SUITE — run against any NVIDIA NIM model
# ============================================================================

def run_test_suite(model: str, client, max_tokens: int = 1024):
    """
    Run all prompts against a model and return results.
    Usage:
        import os
        from openai import OpenAI
        client = OpenAI(base_url="https://integrate.api.nvidia.com/v1",
                        api_key=os.environ["NVIDIA_API_KEY"])
        results = run_test_suite("minimaxai/minimax-m2.7", client)
        for category, prompts in results.items():
            for p in prompts:
                print(f"\n[{category}/{p['name']}]")
                print(f"  Prompt: {p['prompt'][:80]}...")
                print(f"  Response: {p['response'][:200]}...")
                print(f"  Eval: {p['eval']}")
    """
    results = {}
    for category, prompts in PROMPTS.items():
        results[category] = []
        for p in prompts:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": p["prompt"]}],
                    max_tokens=max_tokens,
                    temperature=0.7,
                )
                p["response"] = response.choices[0].message.content
                p["tokens"] = response.usage.total_tokens
                p["status"] = "OK"
            except Exception as e:
                p["response"] = f"ERROR: {str(e)}"
                p["tokens"] = 0
                p["status"] = "FAILED"
            results[category].append(p)
    return results


if __name__ == "__main__":
    import os
    import sys

    # Check API key
    api_key = os.environ.get("NVIDIA_API_KEY", "")
    if not api_key:
        print("ERROR: NVIDIA_API_KEY not set in environment.")
        print("Set it: export NVIDIA_API_KEY='your-nvapi-key'")
        sys.exit(1)

    # Import OpenAI client
    try:
        from openai import OpenAI
    except ImportError:
        print("ERROR: openai library not installed. Run: pip install openai")
        sys.exit(1)

    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key,
    )

    # Pick model from command line or default
    model = sys.argv[1] if len(sys.argv) > 1 else "minimaxai/minimax-m2.7"
    print(f"=== Testing model: {model} ===\n")

    results = run_test_suite(model, client, max_tokens=1024)

    for category, prompts in results.items():
        print(f"\n{'='*60}")
        print(f"CATEGORY: {category.upper()}")
        print(f"{'='*60}")
        for p in prompts:
            status_icon = "✓" if p["status"] == "OK" else "✗"
            print(f"\n[{status_icon}] {p['name']}")
            print(f"  Prompt: {p['prompt'][:100]}...")
            print(f"  Response: {p['response'][:300]}")
            print(f"  Tokens: {p['tokens']}")
            print(f"  Expected: {p['eval']}")

    print(f"\n{'='*60}")
    print(f"Test suite complete for {model}")
    print(f"{'='*60}")
