# ============================================================================
# BIONIC DAUGHTER v1 — NVIDIA NIM MCP SERVER
# ============================================================================
# MCP server wrapping NVIDIA NIM API (build.nvidia.com) as MCP tools.
# Gives the daughter direct access to 80-100+ free AI models for inference,
# evaluation, and training reward computation.
#
# API: https://integrate.api.nvidia.com/v1 (NVIDIA NIM endpoint)
# Models: 80-100+ free models available at https://build.nvidia.com/models
# Auth: NVIDIA API key (nvapi-... format) via NVIDIA_API_KEY env var
#
# Setup:
#   export NVIDIA_API_KEY="nvapi-..."
#   python daughter_nvidia_mcp.py  (or load via MCP host)
#
# Usage (as MCP tools):
#   nvidia_model_list() — list available models
#   nvidia_chat_complete(model, messages, max_tokens, temperature) — chat
#   nvidia_embedding(model, input_text) — embeddings
#   nvidia_status() — key status + model availability
# ============================================================================

import os
import json
from mcp.server.fastmcp import FastMCP

app = FastMCP("daughter_nvidia")

# NVIDIA NIM endpoint
NVIDIA_NIM_BASE = "https://integrate.api.nvidia.com/v1"
API_KEY = os.environ.get("NVIDIA_API_KEY", "")

# Known free models on NVIDIA NIM (subset — full list at build.nvidia.com/models)
# Model IDs use format: provider/model-name (e.g., meta/llama-3.1-70b-instruct)
# NVIDIA's own models use: nvidia/model-name
# Always verify model availability at https://build.nvidia.com/models
NVIDIA_FREE_MODELS = [
    "meta/llama-3.1-70b-instruct",      # Llama 3.1 70B — general purpose
    "meta/llama-3.1-8b-instruct",       # Llama 3.1 8B — fast, lightweight
    "minimaxai/minimax-m2.7",            # MiniMax M2.7 — reasoning
    "deepseekai/deepseek-3.2",           # DeepSeek 3.2 — code & chat
    "moonshotai/kimi-k2.5",              # Kimi K2.5 — long context
    "zai-org/glm-4.5v",                  # GLM 4.5V — multilingual
    "openai/gpt-oss-120b",               # GPT-OSS 120B — general
    "sarvamai/sarvam-m",                 # Sarvam M — Indic languages
    "nvidia/llama-3.1-nemotron-70b",    # Nemotron 70B — NVIDIA reasoning
    "nvidia/nemotron-4-340b",            # Nemotron 4 340B — NVIDIA instruct
    "microsoft/phi-3-mini-4k-instruct",  # Phi-3 Mini — lightweight
]

# ============================================================================
# HELPERS
# ============================================================================

def _check_api_key():
    """Check if NVIDIA API key is configured."""
    if not API_KEY:
        return False
    return True

def _get_client():
    """Get OpenAI-compatible client for NVIDIA NIM."""
    try:
        from openai import OpenAI
        client = OpenAI(
            base_url=NVIDIA_NIM_BASE,
            api_key=API_KEY,
        )
        return client
    except ImportError:
        return None

# ============================================================================
# STATUS
# ============================================================================

@app.tool()
def nvidia_status() -> str:
    """Show NVIDIA NIM MCP status and configuration."""
    key_status = "CONFIGURED" if _check_api_key() else "NOT CONFIGURED"
    key_display = API_KEY[:12] + "..." if API_KEY else "N/A"

    return (
        "NVIDIA NIM MCP Status — Bionic Daughter v1\n"
        "================================================\n\n"
        f"API Key: {key_status} ({key_display})\n"
        f"NIM Endpoint: {NVIDIA_NIM_BASE}\n"
        f"Client library: {'openai (available)' if _get_client() else 'NOT AVAILABLE — pip install openai'}\n\n"
        f"Free models available: {len(NVIDIA_FREE_MODELS)} known + 80-100+ total at build.nvidia.com\n\n"
        "Known free models:\n"
        + "\n".join(f"  - {m}" for m in NVIDIA_FREE_MODELS)
        + "\n\n"
        "MCP Tools:\n"
        "  nvidia_model_list() — List all known NVIDIA NIM models\n"
        "  nvidia_chat_complete(model, messages, max_tokens, temperature) — Chat inference\n"
        "  nvidia_embedding(model, input_text) — Get text embeddings\n"
        "  nvidia_status() — This status info\n\n"
        "Setup: export NVIDIA_API_KEY='your-nvapi-key'\n"
        "Get key: https://build.nvidia.com/models\n"
        "Docs: https://docs.nvidia.com/nim/\n"
    )

# ============================================================================
# MODEL LIST
# ============================================================================

@app.tool()
def nvidia_model_list() -> str:
    """List available NVIDIA NIM models (free tier)."""
    if not _check_api_key():
        return (
            "ERROR: NVIDIA API key not configured.\n"
            "Set NVIDIA_API_KEY environment variable.\n"
            "Get key at: https://build.nvidia.com/models"
        )

    return (
        f"Available NVIDIA NIM Models ({len(NVIDIA_FREE_MODELS)} known free models):\n\n"
        + "\n".join(f"  - {m}" for m in NVIDIA_FREE_MODELS)
        + "\n\n"
        f"Total available: 80-100+ free models\n"
        f"Full list: https://build.nvidia.com/models\n"
        f"NIM docs: https://docs.nvidia.com/nim/\n\n"
        "To use a model for chat: nvidia_chat_complete('model-name', [...messages], max_tokens=512)\n"
        "To use a model for embeddings: nvidia_embedding('model-name', 'text to embed')"
    )

# ============================================================================
# CHAT COMPLETION
# ============================================================================

@app.tool()
def nvidia_chat_complete(
    model: str,
    messages: str,
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> str:
    """
    Run a chat completion via NVIDIA NIM API.
    messages: JSON array of {role: "user"|"assistant"|"system", content: "..."}
    Example: [{"role": "user", "content": "Hello!"}]
    """
    if not _check_api_key():
        return (
            "ERROR: NVIDIA API key not configured.\n"
            "Set NVIDIA_API_KEY environment variable."
        )

    try:
        messages_list = json.loads(messages)
    except json.JSONDecodeError:
        return f"ERROR: Invalid messages JSON: {messages}"

    if not isinstance(messages_list, list):
        return "ERROR: messages must be a JSON array"

    client = _get_client()
    if client is None:
        return (
            "ERROR: openai library not installed.\n"
            "Run: pip install openai"
        )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages_list,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        result = response.choices[0].message.content
        return (
            f"=== NVIDIA NIM Chat Completion ===\n"
            f"Model: {model}\n"
            f"Tokens used: {response.usage.total_tokens}\n"
            f"---\\n{result}\\n"
            f"---\n\n"
            f"Full response object available for programmatic use."
        )
    except Exception as e:
        return f"ERROR calling NVIDIA NIM: {str(e)}\n\nCheck model name at https://build.nvidia.com/models"

# ============================================================================
# EMBEDDINGS
# ============================================================================

@app.tool()
def nvidia_embedding(model: str, input_text: str) -> str:
    """
    Get embeddings for text via NVIDIA NIM API.
    Returns vector representation of the input text.
    """
    if not _check_api_key():
        return (
            "ERROR: NVIDIA API key not configured.\n"
            "Set NVIDIA_API_KEY environment variable."
        )

    client = _get_client()
    if client is None:
        return "ERROR: openai library not installed. Run: pip install openai"

    try:
        response = client.embeddings.create(
            model=model,
            input=input_text,
        )
        embedding = response.data[0].embedding
        return (
            f"=== NVIDIA NIM Embedding ===\n"
            f"Model: {model}\n"
            f"Input: {input_text[:80]}...\n"
            f"Embedding dimensions: {len(embedding)}\n"
            f"Embedding (first 10 values): {embedding[:10]}\n"
            f"Full embedding available programmatically."
        )
    except Exception as e:
        return f"ERROR calling NVIDIA NIM embeddings: {str(e)}\n\nSome embedding models: nvidia/nv-embedqa-e5-v5, nvai/embedqa-e5-v5"

# ============================================================================
# MODEL TEST — quick test against a model
# ============================================================================

@app.tool()
def nvidia_model_test(model: str = "meta/llama-3.1-8b-instruct") -> str:
    """
    Quick test: send a simple prompt to verify the model works.
    Uses meta/llama-3.1-8b-instruct as default (reliable, fast).
    Returns the model's response.
    """
    if not _check_api_key():
        return "ERROR: NVIDIA API key not configured."

    client = _get_client()
    if client is None:
        return "ERROR: openai library not installed."

    test_messages = json.dumps([
        {"role": "user", "content": "Hello! Can you confirm you're working? Respond with exactly: YES, I am working."}
    ])

    try:
        response = client.chat.completions.create(
            model=model,
            messages=json.loads(test_messages),
            max_tokens=128,
            temperature=0.1,
        )
        result = response.choices[0].message.content
        return (
            f"=== Model Test: {model} ===\n"
            f"Response: {result}\n"
            f"Tokens: {response.usage.total_tokens}\n"
            f"Status: WORKING"
        )
    except Exception as e:
        return f"ERROR testing model {model}: {str(e)}"

# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    app.run()
