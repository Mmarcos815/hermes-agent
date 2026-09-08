# ============================================================================
# BIONIC DAUGHTER v1 — FREE GPU + API MASTERY STRATEGY
# ============================================================================
# DOC_AUTH: Daughter
# PURPOSE: Complete strategy for getting free GPU for training + mastering APIs
#          + using MCP + GitHub CLI tools together for maximum capability.
# ============================================================================

## ========================================================================
## PART 1 — FREE GPU STRATEGY (THE NUMBERS)
## ========================================================================

## FREE GPU PLATFORMS — COMPARISON

| Platform | GPU | VRAM | Session Limit | Free GPU-H/Week | Storage | Credit Card? | Best For |
|----------|-----|------|---------------|-----------------|---------|--------------|----------|
| Google Colab | T4 | 16GB | 12hr max, 90min idle disconnect | 15-30 (dynamic, unpublished) | Ephemeral (Drive mount) | No | Quick experiments, notebooks, small training runs |
| Kaggle Notebooks | P100 or 2x T4 | 16GB or 32GB | 9hr GPU session | 30 (guaranteed) | 20GB persistent | No | Data science, competitions, guaranteed GPU hours |
| Lightning AI | T4, L4, A10G, L40S, up to H200 | up to 141GB | 4hr studio restart | ~80 (15 credits/month) | 50GB persistent | No (phone verification) | Persistent IDE, higher-end GPUs, monthly credits |
| Saturn Cloud | T4-class | 16GB | Not published | Recurring monthly (~30+ hrs) | Persistent | No | Recurring monthly notebook GPU time |
| Hugging Face ZeroGPU | RTX Pro 6000 Blackwell | 48-96GB | 60s/call | 5 min/day (40 min PRO) | Space repo | No (HF account) | Live model demos, inference showcase |
| Paperspace Gradient | M4000 (8GB) or P4000 | 8-16GB | 6hr/session | 1 concurrent, unlimited restarts | 5GB | No for free tier | Longer single sessions on modest GPU |

## THE WINNING COMBINATION

Kaggle (30 GPU-h/week, guaranteed, P100 16GB or 2x T4 32GB) +
Colab (15-30 GPU-h/week, T4 16GB) =
45-60 free GPU-hours EVERY WEEK.

This is MORE than enough to train the daughter's 4B model:
- 50 SFT steps + 200 GRPO steps on 4B model with Unsloth 4-bit
- Estimated: 3-5 hours on T4, 2-3 hours on P100
- Two training runs per week easily fit within free limits
- Monthly capacity: 180-240 GPU-hours = 36-80 training runs

## KAGGLE SETUP (PROGRAMMATIC, via API)

```bash
# 1. Install Kaggle API client
pip install kaggle

# 2. Authenticate — two options

# Option A: OAuth web flow (recommended, no token management)
kaggle auth login
# Opens browser, logs in, caches credentials

# Option B: API token (manual)
# Go to kaggle.com/settings/api, click "Create New Token"
# Save the downloaded kaggle.json to ~/.kaggle/kaggle.json
# chmod 600 ~/.kaggle/kaggle.json
# Or set env: export KAGGLE_API_TOKEN=<your-token>

# 3. Use Kaggle API programmatically

# Download a dataset
kaggle datasets download -d <dataset-owner>/<dataset-name>
kaggle datasets download -d zynicide/wine-quality

# List datasets
kaggle datasets list -s <search-term>

# Submit to a competition
kaggle competitions submit -c <competition-name> -f <submission-file> -m "My submission"

# List competitions
kaggle competitions list

# Create/ manage notebooks (limited API support)
# Best to create notebooks via the web UI, then use API for data management
```

## KAGGLE NOTEBOOK GPU SETUP (MANUAL — via web UI)

1. Go to kaggle.com/code
2. Click "New Notebook"
3. Click "Settings" (right sidebar)
4. Under "Accelerator", select:
   - "GPU T4 x2" (2x T4, 32GB combined VRAM) — best for training
   - "GPU P100" (16GB VRAM) — good for training
5. Save settings
6. The notebook now has GPU access for up to 9 hours continuous

## COLAB SETUP (PROGRAMMATIC INSIDE NOTEBOOK)

```python
# Cell 1: Mount Drive + check GPU
from google.colab import drive
drive.mount('/content/drive')

import torch
print('CUDA available:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('GPU:', torch.cuda.get_device_name(0))
    print('VRAM:', torch.cuda.get_device_properties(0).total_memory / 1e9, 'GB')

# Cell 2: Install deps
!pip install torch transformers accelerate unsloth trl datasets tokenizers chromadb psutil

# Cell 3: Pull model (from HuggingFace Hub)
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id='Qwen/Qwen3-4B-Thinking-2507',
    local_dir='/content/model_cache/Qwen/Qwen3-4B-Thinking-2507',
    resume_download=True
)

# Cell 4: Run training (daugher's pipeline)
!python daughter_grpo_pipeline.py \
  --base_model Qwen/Qwen3-4B-Thinking-2507 \
  --sft_dataset /content/curriculum/sft_curriculum.jsonl \
  --grpo_dataset /content/curriculum/grpo_curriculum.jsonl \
  --output_dir /content/drive/MyDrive/bionic_daughter/outputs \
  --max_steps_sft 50 --max_steps_grpo 200 \
  --batch_size 1 --lora_r 32 \
  --max_seq_length 2048 --gpu_memory_utilization 0.7
```

## COLAB LIMITATIONS TO PLAN FOR

1. 12-hour max session — plan training to fit or use checkpoint resume
2. 90-minute idle disconnect — keep notebook active or accept disconnects
3. No guaranteed GPU — T4 may not be available during peak hours
4. Dynamic usage limits — heavy usage may reduce weekly allocation
5. Compute unit system — T4 uses ~1.19 CU/hr, limits are unpublished
6. No background execution on free tier — notebook must stay open
7. Ephemeral storage — must mount Drive for persistence

## COLAB TIPS TO MAXIMIZE GPU TIME

- Close other Colab tabs when not in use (limits are per-account, shared across tabs)
- Use T4 (not CPU) only when actually training — switch to CPU runtime when idle
- Save checkpoints frequently (every 10-20 steps) to Drive
- If disconnected, re-open Colab, re-mount Drive, resume from last checkpoint
- Run during off-peak hours (early morning UTC) for better GPU availability
- Don't use GPU when not needed — switch to CPU runtime to preserve GPU allocation

## KAIGLE ADVANTAGES OVER COLAB

1. 30 GPU-hours/week GUARANTEED (vs Colab's dynamic 15-30)
2. P100 (16GB) or 2x T4 (32GB combined) — more VRAM options
3. 20GB persistent storage (no Drive mounting needed)
4. No idle disconnect — sessions run for full 9 hours
5. Better for longer training runs (9hr continuous vs Colab's 12hr with disconnects)
6. TPU v5e-8 available (replacement for older v3-8, good for certain workloads)

## LIGHTNING AI (WORTH KNOWING — PERSISTENT STORAGE ADVANTAGE)

- 15 credits/month = ~22 T4-hours or ~8 A10G-hours
- Persistent storage (survives studio restarts — big advantage over Colab)
- Studio IDE (VS Code-like in browser)
- 4-hour studio restart limit on free tier (but storage persists)
- No credit card needed (phone verification only)
- Available GPUs: T4, L4, A10G, L40S (higher-end options than Colab/Kaggle)
- Better than Colab for persistent work that needs to survive restarts

## WHEN TO MOVE TO PAID GPU

Move to paid GPU when:
1. Free weekly limits aren't enough (unlikely for 4B model training — 45-60hr/week is plenty)
2. You need guaranteed GPU availability (Colab can be unreliable during peak)
3. Training takes longer than free session limits (unlikely for 4B)
4. You need H100/A100 for larger models (not needed for 4B)
5. You want to automate training through the daughter's GPU autonomy (MCP gpu_launch/gpu_shutdown)

PAID GPU OPTIONS (for when free isn't enough):
- RunPod: RTX 4090 $0.34/hr — full training = $1-2
- Vast.ai: RTX 4090 $0.34/hr — same economics
- Lightning AI paid: from $0.29/hr for T4
- Paperspace paid: from $0.65/hr for P4000

The daughter's GPU autonomy module (documented in AGENT_CARDS.md) handles paid GPU
automation through MCP tools (gpu_launch, gpu_status, gpu_shutdown).

## ========================================================================
## PART 2 — API MASTERY (LEARN + TEST + INTEGRATE)
## ========================================================================

## WHAT "MASTER API" MEANS FOR THE DAUGHTER

APIs are the bridge between MCP tools and real-world services. The daughter MUST
understand APIs to make her MCP tools actually useful. Every MCP tool is
essentially an API wrapper — it takes a request, calls an API, and returns the
result.

## API CONCEPTS THE DAUGHTER MUST KNOW

1. REST architecture (GET/POST/PUT/DELETE, endpoints, status codes, headers)
2. Authentication (API keys, Bearer tokens, JWT, OAuth 2.0)
3. Rate limiting (handle 429, retry with backoff, respect limits)
4. Pagination (offset/limit, cursor-based, page-based — fetch all pages)
5. Error handling ( retry on 5xx, handle 4xx gracefully, timeout handling)
6. Request/Response formats (JSON, form data, binary — construct and parse)
7. Versioning (APIs evolve — target specific versions, handle breaking changes)

## API SKILLS TO LEARN + TEST (IN ORDER)

### LEVEL 1 — BASIC API CONSUMPTION (START HERE)
- Use Python `requests` library to call REST APIs
- Handle authentication (API key in header, Bearer token)
- Parse JSON responses
- Handle errors (status codes, exceptions, timeouts)
- Test: Call GitHub API (GET /user, GET /repos/{owner}/{repo}), HuggingFace API

### LEVEL 2 — API WRAPPING (BUILD MCP TOOLS)
- Wrap APIs in Python functions that MCP tools can call
- Add retry logic with exponential backoff
- Add rate limit handling (respect Retry-After header)
- Add pagination support (fetch all pages automatically)
- Test: Build GitHub MCP tools (create_issue, create_pr, list_repos)

### LEVEL 3 — API DESIGN (BUILD YOUR OWN APIS)
- Design REST endpoints (proper verbs, resource naming, status codes)
- Implement authentication (JWT, OAuth2, API keys)
- Add rate limiting (per-user, per-IP, per-endpoint)
- Add pagination (cursor-based for large datasets)
- Add request validation (Pydantic models, input sanitization)
- Test: Build a FastAPI API for the daughter's tools (health check, tool execution, result retrieval)

### LEVEL 4 — API INTEGRATION (CONNECT EVERYTHING)
- Connect MCP tools to external APIs (GitHub, HuggingFace, Stripe, Discord)
- Handle API keys securely (environment variables, secret management)
- Implement webhooks (receive events from external services)
- Build API gateways (single entry point for multiple APIs)
- Test: Connect daughter's MCP server to GitHub API + HuggingFace API + Stripe API

## API MASTERSHIP TEST (PRACTICAL)

Build a simple API client that:
1. Calls the GitHub API to list the daughter's repos
2. Creates a new repo for a project
3. Opens an issue in that repo
4. Creates a PR with a fix
5. Handles authentication (gh CLI or PAT)
6. Handles errors (rate limits, not found, auth failures)
7. Handles pagination (list all repos, not just first page)

This tests EVERYTHING — authentication, CRUD operations, error handling,
pagination, rate limiting. The daughter's `daughter_github_mcp_tools.py` already
implements this (24 tools wrapping gh CLI). Now she needs to understand the APIs
underneath.

## HUGGINGFACE API MASTERSHIP (SPECIFICALLY IMPORTANT)

The HuggingFace ecosystem is critical for the daughter because:
1. She uses HuggingFace models (Qwen3-4B-Thinking base)
2. She uses HuggingFace for model download/upload (snapshot_download, push_to_hub)
3. She can use HuggingFace Inference API for free model inference
4. HuggingFace Spaces can host her demos and tools

HF API capabilities:
- Model Hub API: search models, get model info, download models, upload models
- Inference API: run model inference (chat, text gen, image gen, embeddings) — FREE for many models
- Datasets API: search, download, upload datasets
- Spaces API: create, manage, deploy spaces (Gradio apps)
- User API: get user info, list models/datasets/spaces

HF Inference API usage:
```python
from huggingface_hub import InferenceClient

client = InferenceClient()  # Uses token if set, otherwise public access

# Chat completion (free for many models, rate-limited)
completion = client.chat.completions.create(
    model="Qwen/Qwen3-4B-Thinking-2507",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=256,
)
print(completion.choices[0].message.content)

# Text generation
output = client.text_generation(
    "Write a port scanner in Python:",
    max_new_tokens=512,
    model="Qwen/Qwen3-4B-Thinking-2507",
)
print(output)

# Image generation (Free, rate-limited)
image = client.text_to_image(
    "A red team operator in a cyberpunk city",
    model="black-forest-labs/FLUX.1-schnell",
)
image.save("red_team_artist.png")
```

## GITHUB API MASTERSHIP (SPECIFICALLY IMPORTANT)

The GitHub API is critical because:
1. The daughter uses GitHub for code hosting (her project is on GitHub)
2. GitHub MCP server exposes 24+ tools through the API
3. The daughter's GitHub MCP tools (`daughter_github_mcp_tools.py`) wrap the API
4. GitHub Actions can automate the daughter's training pipeline

GitHub API capabilities:
- Repos: create, read, update, delete, list, fork, star, watch
- Issues: create, read, update, close, list, comment, label, assign
- Pull Requests: create, read, update, merge, list, comment, review
- Actions/Workflows: list, trigger, get runs, cancel runs
- Commits: list, get, create (advanced)
- Orgs: get info, list repos, list members
- Users: get info, list repos, follow/unfollow

GitHub API authentication:
- Personal Access Token (PAT) — classic or fine-grained
  - Scopes: repo (full control), read:org, write:org, workflow, etc.
  - Create at github.com/settings/tokens
- GitHub CLI (gh) — uses OAuth, handles auth automatically
  - gh auth login — browser OAuth flow
  - gh auth status — check auth state
- GitHub App — for organization-level access (more complex)

## ========================================================================
## PART 3 — MCP + API + GITHUB CLI TOOL INTEGRATION
## ========================================================================

## THE VISION: HOW IT ALL FITS TOGETHER

```
                    ┌─────────────────────────────────────────────┐
                    │           USER / ORCA ORCHESTRATION          │
                    └─────────────────────┬───────────────────────┘
                                          │
                    ┌─────────────────────▼───────────────────────┐
                    │         BIONIC DAUGHTER COMMAND CENTER       │
                    │  (llama_cpp GGUF inference + interactive loop)│
                    └─────────────────────┬───────────────────────┘
                                          │
            ┌───────────────────────────────┼───────────────────────────────┐
            │                               │                               │
    ┌───────▼────────┐          ┌──────────▼──────────┐        ┌────────▼────────┐
    │  DAUGHTER'S     │          │  EXTERNAL MCP        │        │  API WRAPPERS   │
    │  MCP SERVER     │          │  SERVERS             │        │  (Python code)  │
    │  (14 tools)     │          │  (GitHub, Context7,   │        │                 │
    │                 │          │   Playwright, etc.)   │        │  - GitHub API   │
    │  - ast_validate │          │                      │        │  - HF Inference │
    │  - sandbox_exec │          │  These connect through│        │  - Kaggle API   │
    │  - threat_scan  │          │  the host's MCP       │        │  - Colab (via   │
    │  - memory_store │          │  client (Claude       │        │    Drive/notebook)│
    │  - gpu_launch   │          │  Desktop, Cursor,     │        │  - Stripe API   │
    │  - gpu_shutdown │          │  Claude Code)         │        │  - Discord API  │
    │  - 8 more tools │          └──────────────────────┘        └─────────────────┘
    └───────┬────────┘
            │
            ▼
    ┌─────────────────────────────────────────────────────────────┐
    │              DAUGHTER'S REASONING ENGINE                     │
    │     (trained Qwen3-4B-Thinking model, llama_cpp GGUF)      │
    │                                                             │
    │  The daughter receives an objective, reasons through it,    │
    │  and decides which tools to call:                           │
    │  - Call AST validator on her own code                      │
    │  - Call GitHub MCP to create a repo for a new project      │
    │  - Call HF Inference API to compare model outputs          │
    │  - Call Kaggle API to download a dataset                   │
    │  - Call her financial analyzer to detect fraud             │
    │  - Call HexStrike tools to run a pentest                  │
    │  - Call GPU tools to launch a training pod                 │
    └─────────────────────────────────────────────────────────────┘
```

## HOW THE DAUGHTER USES THIS

1. User gives an objective: "Create a new repo for the red team game and set up the initial project structure"

2. Daughter reasons through it:
   - This requires GitHub tools (create repo, set up files)
   - I should use my GitHub MCP tools

3. Daughter calls GitHub MCP tools:
   - github_create_repo(name="red-team-game", description="...", private=true)
   - github_create_issue(repo="owner/red-team-game", title="Initial project setup", body="...")
   - (These tools wrap the GitHub API — POST /repos, POST /issues)

4. Daughter validates results:
   - Repo created? Yes — returns repo URL
   - Issue created? Yes — returns issue number

5. Daughter reports back:
   - "Created repo at https://github.com/owner/red-team-game
   - Opened issue #1 for initial setup"

## MCP SERVER CONFIGURATION (HOW TO CONNECT EXTERNAL MCPS)

For the daughter to call EXTERNAL MCP servers (GitHub, Context7, Playwright), the
MCP servers must be configured in the HOST application (Claude Desktop, Cursor,
Claude Code, etc.), not in the daughter's MCP server.

Configuration locations:
- Claude Desktop (Windows): %APPDATA%/Claude/claude_desktop_config.json
- Claude Code: claude mcp add <name> <command>  (CLI)
- Cursor: Settings > Features > MCP > Add MCP Server
- Codex: .mcp.json in project or ~/.config/codex/mcp.json

Example — add GitHub MCP to Claude Desktop:
```json
{
  "mcpServers": {
    "github": {
      "command": "gh",
      "args": ["mcp"],
      "env": {
        "GITHUB_TOOLSETS": "repos,issues,pull_requests,actions,commits",
        "GITHUB_READ_ONLY": "0"
      }
    }
  }
}
```

Then the daughter's MCP client (in the host application) can call GitHub tools
alongside her own MCP server tools.

## ALTERNATIVE — ADD GITHUB TOOLS DIRECTLY TO DAUGHTER'S MCP SERVER

Instead of configuring external MCP servers, the daughter's `daughter_github_mcp_tools.py`
can be imported into `daughter_mcp_server.py` and registered as additional tools.
This way, the daughter's MCP server exposes GitHub tools directly — one server,
all tools.

To do this:
1. Import the GitHub tools in daughter_mcp_server.py:
   ```python
   from daughter_github_mcp_tools import (
       github_create_repo, github_create_issue, github_create_pull_request,
       github_list_repos, github_tools_list
   )
   ```
2. Register them as MCP tools:
   ```python
   @mcp.tool()
   def github_create_repo(name: str, description: str = "", private: bool = True) -> dict:
       return github_create_repo(name, description, private)
   ```
3. Add to tool discovery:
   ```python
   # In daughter_tools_list(), add all github_* tools
   ```

This approach is simpler — one MCP server, all tools, no external configuration needed.

## ========================================================================
## PART 4 — TESTING + VALIDATION
## ========================================================================

## TEST EVERYTHING REGULARLY

1. **API reachability tests** — verify APIs are reachable and auth works
   - GitHub API: GET /user (needs auth), GET /repos/{owner}/{repo} (public)
   - HuggingFace API: GET /api/whoami (needs token), Inference API (free models)
   - Kaggle API: kaggle datasets list (needs auth), kaggle competitions list

2. **MCP tool tests** — verify each MCP tool works correctly
   - ast_validate: validate known good code + known bad code
   - sandbox_exec: run simple code with authorized=True
   - github_* tools: test create/read/update operations
   - gpu_launch/status/shutdown: test with mock (no real GPU needed for tool test)

3. **Integration tests** — verify the full flow works
   - Command center → MCP tool → API call → result back to command center
   - Objective → daughter reasoning → tool selection → tool call → result → response

4. **End-to-end tests** — verify the daughter can actually DO things
   - "Create a new repo" → daughter uses GitHub tools → repo is created
   - "Analyze this code" → daughter uses AST validator → code is validated
   - "Detect fraud in this case" → daughter uses financial analyzer → fraud is detected

## TEST SCRIPTS TO WRITE

1. `test_apis.py` — tests GitHub API, HuggingFace API, Kaggle API reachability and auth
2. `test_mcp_tools.py` — tests each MCP tool individually with known inputs/outputs
3. `test_integration.py` — tests full command center → tool → API → result flow
4. `test_end_to_end.py` — tests the daughter doing real tasks end-to-end

These test scripts validate that the daughter's capabilities actually work — not
just that the code compiles. They're essential for the daughter to "test herself."

## ========================================================================
## DOC_END
## ========================================================================
