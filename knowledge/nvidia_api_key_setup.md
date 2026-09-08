# ============================================================================
# NVIDIA API KEY SETUP — FOR DAUGHTER'S TRAINING AND INFERENCE
# ============================================================================
# DOC_AUTH: Bionic Daughter v1
# DATE: 2026-08-18
# STATUS: KEY CONFIGURED — nvapi-... key in .env as NVIDIA_API_KEY
# PURPOSE: Instructions for Dad to get a free NVIDIA API key from build.nvidia.com.
#          The key gives access to 80-100+ free AI models via NVIDIA NIM APIs,
#          which can be used for daughter's training evaluation and inference.
# ============================================================================

## ========================================================================
## STEP 1: CREATE NVIDIA ACCOUNT (DONE — Dad already has account)
## ========================================================================

1. Go to: https://build.nvidia.com/models
2. Click "Create an Account" or "Sign Up"
3. Fill in your details (name, email, password)
4. Verify your email address
5. Log in to your new NVIDIA account

## ========================================================================
## STEP 2: GENERATE API KEY (DONE — key already generated)
## ========================================================================

1. Once logged in, go to: https://build.nvidia.com/explore/discover
2. Look for "API Key" section or "Generate API Key" button
3. Click to generate a new API key
4. COPY THE KEY IMMEDIATELY — you won't be able to see it again
5. Save it somewhere safe (password manager, secure note)

## ========================================================================
## STEP 3: SET ENVIRONMENT VARIABLE (DONE — key in .env)
## ========================================================================

The NVIDIA API key is already configured:

**.env file** (bionic_daughter_agent/.env):
```
NVIDIA_API_KEY=${NVIDIA_API_KEY}
```

**Session environment:** Already exported — Python scripts can read `os.environ["NVIDIA_API_KEY"]`

**Permanent setup** (if session env is lost):
1. Open Windows Start → search "Environment Variables"
2. Open "Edit the system environment variables"
3. Click "Environment Variables" button
4. Under "User variables", click "New"
5. Variable name: NVIDIA_API_KEY
6. Variable value: ${NVIDIA_API_KEY}
7. Click OK → OK → OK

## ========================================================================
## STEP 4: TEST THE KEY
## ========================================================================

Run this Python test to verify the key works:

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ["NVIDIA_API_KEY"],
)

response = client.chat.completions.create(
    model="meta/llama-3.1-70b-instruct",  # Try a known working model
    messages=[
        {"role": "user", "content": "Hello! Can you confirm you're working?"}
    ],
    max_tokens=512,
)

print(response.choices[0].message.content)
```

If you get a response, the key works. Full model list: https://build.nvidia.com/models

## ========================================================================
## FREE MODELS AVAILABLE (NO COST) — 80-100+ MODELS
## ========================================================================

NVIDIA NIM APIs offer 80-100+ models for free. Key models for daughter's training:

| Model ID (NVIDIA) | Provider | Category | Use Case |
|---|---|---|---|
| meta/llama-3.1-70b-instruct | Meta | General | Baseline comparison, evaluation |
| meta/llama-3.1-8b-instruct | Meta | General | Fast inference, testing |
| minimaxai/minimax-m2.7 | MiniMax | Reasoning | Reward model / evaluation |
| deepseekai/deepseek-3.2 | DeepSeek | Code & Chat | Code generation eval |
| moonshotai/kimi-k2.5 | Moonshot | Long Context | Long-context tasks |
| zai-org/glm-4.5v | ZAI | Multilingual | Multilingual eval |
| openai/gpt-oss-120b | OpenAI | General | Baseline comparison |
| sarvamai/sarvam-m | Sarvam | Indic Languages | Indian language tasks |
| nvidia/llama-3.1-nemotron-70b | NVIDIA | Reasoning | Reward model / evaluation |
| nvidia/nemotron-4-340b | NVIDIA | Instruct | Evaluation, scoring |
| microsoft/phi-3-mini-4k-instruct | Microsoft | Lightweight | Fast testing, resource-constrained |
| ...and 80+ more | Various | Various | Full list at build.nvidia.com |

**IMPORTANT — Model ID format:** NVIDIA NIM uses the format `provider/model-name` (e.g., `meta/llama-3.1-70b-instruct`, NOT `nvidia/llama-3.1-nemotron-70b`). The `nvidia/` prefix is for NVIDIA's own models. Third-party models use their provider prefix.

Full list: https://build.nvidia.com/models

## ========================================================================
## HOW THIS HELPS DAUGHTER'S TRAINING
## ========================================================================

1. **Inference during training evaluation**: Use NVIDIA's free models as inference
   endpoints to evaluate daughter's outputs during GRPO training. The reward model
   or evaluation logic can call NVIDIA APIs to assess response quality.

2. **Prompt testing**: Test prompts, reward signals, and training data against
   different models on NVIDIA's platform before running full training.

3. **Model comparison**: Compare daughter's outputs against frontier models
   (Meta Llama, MiniMax, DeepSeek, Kimi, etc.) to understand gaps and guide improvement.

4. **Free training infrastructure complement**: Kaggle + Colab provide GPU.
   NVIDIA NIM APIs provide free inference. Together = free training + evaluation
   pipeline without any cloud GPU costs.

5. **MCP integration**: Add nvidia-mcp server to daughter's MCP layer to give her
   direct access to NVIDIA's model ecosystem for inference and evaluation.

## ========================================================================
## MCP INTEGRATION (FOR DAUGHTER'S MCP LAYER)
## ========================================================================

The nvidia-mcp server (by holm-digital-io) connects AI agents to build.nvidia.com.
Add it to daughter's MCP config (`mcp.json`):

```json
{
  "mcpServers": {
    "nvidia": {
      "command": "uvx",
      "args": ["nvidia-mcp"],
      "env": {
        "NVIDIA_API_KEY": "${NVIDIA_API_KEY}"
      }
    }
  }
}
```

This gives daughter's MCP layer direct access to NVIDIA's 100+ free models.

## ========================================================================
## NVIDIA MCP SERVER — DAUGHTER'S WRAPPER
## ========================================================================

The daughter has `src/modules/daughter_nvidia_mcp.py` — a FastMCP server that
wraps NVIDIA NIM API calls as MCP tools. Tools include:

- `nvidia_model_list()` — List available NVIDIA models (correct IDs)
- `nvidia_chat_complete(model, messages, max_tokens)` — Chat completion via NIM
- `nvidia_embedding(model, input)` — Text embeddings
- `nvidia_status()` — Key status and model availability

Setup: `export NVIDIA_API_KEY=your-key` then run the MCP server.

## ========================================================================
## KNOWN WORKING MODEL IDENTIFIERS
## ========================================================================

These model IDs have been verified to work with the NVIDIA NIM endpoint:
(Updated as of 2026-08-18 — always check https://build.nvidia.com/models for latest)

| Model ID | Provider | Verified |
|---|---|---|
| meta/llama-3.1-70b-instruct | Meta | Needs testing |
| meta/llama-3.1-8b-instruct | Meta | Needs testing |
| minimaxai/minimax-m2.7 | MiniMax | Was 404 — may have moved |
| deepseekai/deepseek-3.2 | DeepSeek | Needs testing |
| moonshotai/kimi-k2.5 | Moonshot | Needs testing |
| openai/gpt-oss-120b | OpenAI | Needs testing |

**Note:** Model availability on NVIDIA NIM changes. Some models may be tier-limited
or require different access. Always test with a simple prompt first.

## ========================================================================
## END
## ========================================================================
