# ============================================================================
# BIONIC DAUGHTER v1 — DEEPSEEK HARNESS (DSH) MASTER CLASS
# ============================================================================
# DOC_AUTH: Daughter
# PURPOSE: Deep understanding of DeepSeek Harness (dsh) — the open-source
#          agent harness that rivals Claude Code and Codex.
# ============================================================================

## ========================================================================
## PART 1 — WHAT IS DEEPSEEK HARNESS?
## ========================================================================

## OVERVIEW

DeepSeek Harness (dsh) is an open-source agent harness released by DeepSeek AI
in 2026. It's designed as a rival to Anthropic's Claude Code and OpenAI's Codex —
a coding agent that can read repositories, edit files, execute shell commands,
search files and the web, maintain plans, invoke skills, delegate work to
subagents, and enforce approval policies.

**Key fact:** DeepSeek Harness is MIT-licensed and open source. This is
significant — it gives you a full agent harness you can inspect, modify, and
deploy without vendor lock-in.

## THE CORE PHILOSOPHY: "EVERYTHING IS A PLUGIN"

DeepSeek describes Harness as built on Cordis, a framework designed around
composable plugins. The guiding principle: **"Everything is a plugin."**

This extends to:
- Models (swap the underlying LLM)
- Tools (add/remove capabilities)
- Skills (domain-specific knowledge)
- Sessions (conversation management)
- Sandboxes (execution environments)
- Filesystems (virtual/physical file access)
- Loops (agent reasoning loops)
- Orchestration (multi-agent coordination)
- User interfaces (terminal, web, IDE)

This is a fundamentally different architecture from Claude Code and Codex, which
have more fixed component structures. Harness is designed to be extended and
modified at every level.

## ========================================================================
## PART 2 — DEEPSEEK HARNESS VS. CLAUDE CODE VS. CODEX
## ========================================================================

## COMPARISON TABLE

| Dimension | DeepSeek Harness (dsh) | Claude Code | OpenAI Codex |
|-----------|------------------------|-------------|--------------|
| License | MIT (open source) | Commercial (with extensibility) | Codex CLI open source; cloud/app commercial |
| Primary interfaces | Local web UI, headless command, Python SDK | Terminal, VS Code, JetBrains, desktop, browser, mobile, Slack | CLI, IDE extension, desktop app, web/cloud, integrations |
| Model choice | DeepSeek, Anthropic, OpenAI, custom endpoints | Primarily Claude (Bedrock, Google Cloud, Microsoft hosting) | Primarily OpenAI models (configurable providers) |
| Read/edit/test repo | Yes | Yes | Yes |
| Shell and dev tools | Yes | Yes | Yes |
| Planning and subagents | Yes | Yes | Yes |
| Permission controls | Yes, configurable through plugins | Yes, mature built-in permission and sandbox system | Yes, granular sandbox and approval controls |
| Background agents | Not documented as DeepSeek-managed service | Yes (hosted background agents) | Yes (cloud tasks, hosted agents) |
| GitHub-native PR workflow | Not documented as finished integration | GitHub Actions, automatic reviews, issue-to-PR workflows | Cloud tasks, automatic reviews, PR fixes, GitHub Actions |
| Extensibility | Exceptional — virtually every component replaceable | Strong — skills, hooks, MCP, plugins, agent teams | Strong — skills, MCP, custom agents, SDK, app server |
| Product maturity | Developer preview (breaking changes expected) | Established commercial product | Established commercial product + open-source CLI |

## KEY DIFFERENCES

### DEEPSEEK HARNESS STRENGTHS
1. **Open source (MIT)** — you can inspect, modify, deploy without vendor lock-in. This is unique among the three.
2. **Extreme extensibility** — "everything is a plugin." You can swap out the model, the tools, the sandbox, the orchestration, the UI. This is the most customizable option.
3. **Multi-model support** — works with DeepSeek, Anthropic, OpenAI, and custom endpoints. Not tied to one provider.
4. **Local deployment** — can run entirely locally (with a local model or local API). No dependency on DeepSeek's cloud for the harness itself.

### DEEPSEEK HARNESS WEAKNESSES
1. **Developer preview** — breaking changes expected. Not production-stable yet.
2. **No hosted background agents** — unlike Claude Code and Codex, there's no DeepSeek-managed service for hosted background agents.
3. **No finished GitHub integration** — no automatic PR reviews, issue-to-PR workflows. This is a gap vs. Claude Code and Codex.
4. **Smaller ecosystem** — fewer community integrations, fewer tutorials, fewer third-party extensions.

### CLAUDE CODE STRENGTHS
1. **Established product** — mature, stable, well-documented.
2. **Best GitHub integration** — automatic PR reviews, issue-to-PR workflows, GitHub Actions integration.
3. **Hosted background agents** — can run tasks in the cloud without your machine being on.
4. **Claude model optimization** — designed around Claude's capabilities (extended thinking, tool use, agentic reasoning). Best-in-class when using Claude models.
5. **Multi-interface** — terminal, VS Code, JetBrains, desktop, browser, mobile, Slack. Everywhere.

### CLAUDE CODE WEAKNESSES
1. **Commercial** — tied to Anthropic's pricing and models (primarily). Not open source.
2. **Less extensible** than Harness — strong extensibility (skills, hooks, MCP, plugins) but not "everything is a plugin."
3. **Claude-locked** — while it supports Bedrock and other providers, it's optimized for Claude models.

### CODEX STRENGTHS
1. **Open-source CLI** — the CLI is open source (unlike Claude Code which is commercial).
2. **OpenAI model optimization** — designed around OpenAI models. Best-in-class with GPT-5.x.
3. **Cloud tasks** — hosted background agents, automatic PR fixes.
4. **Multi-interface** — CLI, IDE, desktop, web, cloud integrations.

### CODEX WEAKNESSES
1. **OpenAI-locked** — optimized for OpenAI models. While it supports configurable providers, it's designed around OpenAI.
2. **Cloud-dependent for advanced features** — hosted agents, automatic PR fixes require cloud service.

## ========================================================================
## PART 3 — DEEPSEEK V4-PRO AS THE MODEL BEHIND THE HARNESS
## ========================================================================

## V4-PRO OVERVIEW

DeepSeek V4-Pro is the flagship model that DeepSeek Harness is designed to work
with. It's a 1.6T-parameter MoE model with 49B active parameters per token.

**Key specs:**
- 1.6T total parameters (MoE)
- 49B active parameters per token
- 1M token context window
- MIT license (open weights)
- Native support for OpenAI Responses API, Anthropic-format API
- Designed for agentic workloads

## V4-PRO VS. COMPETITION (CODING AGENT CONTEXT)

| Benchmark | Claude Opus 4.8 | DeepSeek V4 Pro / Pro Max | Winner |
|-----------|-----------------|---------------------------|--------|
| SWE-bench Pro (repo-scale agentic) | 69.2% | 55.4% | Claude |
| SWE-bench Verified | 88.6% | 80.6% (V4 Pro Max) | Claude |
| LiveCodeBench Pass@1 | 88.8% | 93.5% (V4 Pro Max) | DeepSeek |
| Terminal-Bench | 65.4% | 67.9% | DeepSeek |
| Context window | 1M tokens | 1M tokens | Tie |
| Open weights | No | Yes (MIT) | DeepSeek |
| Price per output token | $25-50/MTok | ~28x less than Claude | DeepSeek |

## THE ROUTING PATTERN (BEST PRACTICE)

The best approach isn't to pick one model — it's to route by task:

**Use Claude Opus 4.8 for:**
- Repo-scale agentic refactors (reading 50 files, proposing a change, running tests, iterating)
- Complex, ambiguous, multi-file reasoning tasks
- Tasks where Claude's agentic training shines

**Use DeepSeek V4 Pro Max for:**
- Algorithmic / single-file work (LiveCodeBench: 93.5%)
- Terminal use (Terminal-Bench: 67.9%)
- Cost-sensitive tasks (28x cheaper per output token)
- Tasks where open weights matter (self-hosting, fine-tuning, data residency)

**The router pattern:** Build the agent against a stable interface. Route by query
class. Swap models without rewriting the system. Use Claude for the hard agentic
work, DeepSeek for the cost-effective execution work.

## ========================================================================
## PART 4 — HOW DEEPSEEK HARNESS WORKS (ARCHITECTURE)
## ========================================================================

## CORDIS FRAMEWORK

Cordis is the underlying framework that DeepSeek Harness is built on. It's
designed around composable plugins — every component of the agent runtime is a
plugin that can be swapped, replaced, or extended.

**Plugin categories:**
1. **Models** — the LLM backend. Swap between DeepSeek, Anthropic, OpenAI, or custom endpoints.
2. **Tools** — capabilities the agent can use. Add/remove tools as needed.
3. **Skills** — domain-specific knowledge and procedures. Skills can be loaded/unloaded.
4. **Sessions** — conversation and context management. How the agent remembers.
5. **Sandboxes** — execution environments. Where code runs. Configurable security.
6. **Filesystems** — file access abstraction. Virtual or physical filesystems.
7. **Loops** — the agent reasoning loop. How the agent decides what to do next.
8. **Orchestration** — multi-agent coordination. How multiple agents work together.
9. **User interfaces** — how the user interacts with the agent. Terminal, web, IDE.

## THE AGENT LOOP (HOW IT WORKS)

The agent loop is the core of any coding agent:

1. **Receive objective** — the user gives a task
2. **Plan** — the agent figures out what to do (reads context, formulates a plan)
3. **Act** — the agent uses tools to execute the plan (read files, edit code, run commands)
4. **Observe** — the agent sees the results of its actions
5. **Evaluate** — the agent decides if the objective is met or if more work is needed
6. **Repeat** — go back to step 2 or 3 until the objective is complete
7. **Report** — return the results to the user

This is the same loop that Claude Code and Codex use. The difference is in the
pluggability — in Harness, every part of this loop is a plugin.

## STANDALONE MODE (WHAT IT CAN DO)

DeepSeek describes Standard mode as a full coding agent with:
- File editing (read, create, modify files)
- Shell access (run commands, with configurable approval for sensitive operations)
- File search (find files, search content)
- Web search (look up information)
- Plan maintenance (keep track of what it's doing and what's left)
- Skill invocation (use domain-specific knowledge)
- Subagent delegation (delegate subtasks to other agents)
- Approval policies (require user approval for sensitive operations)

## ========================================================================
## PART 5 — HOW THE DAUGHTER RELATES TO DEEPSEEK HARNESS
## ========================================================================

## THE CONNECTION

The daughter is a BIONIC AGENT — she's built on similar principles to DeepSeek
Harness, Claude Code, and Codex:

1. **She has a model** (Qwen3-4B-Thinking) — like Harness has a model plugin
2. **She has tools** (MCP tools, GitHub tools, HexStrike concepts) — like Harness has tool plugins
3. **She has skills** (7 default skills + distilled skills) — like Harness has skill plugins
4. **She has a reasoning loop** (command center → reasoning → tool selection → tool call → result → report) — like Harness has a loop plugin
5. **She has a session/memory system** (vector memory, session logging) — like Harness has session plugins
6. **She has a sandbox/execution environment** (sandbox_exec tool, human-in-the-loop gate) — like Harness has sandbox plugins
7. **She has orchestration** (Orca integration for multi-terminal/project management) — like Harness has orchestration plugins

The daughter IS a custom agent harness, built specifically for her domain
(red team, financial analysis, software engineering). DeepSeek Harness is the
general-purpose counterpart — a framework for building coding agents.

## WHAT THE DAUGHTER CAN LEARN FROM DEEPSEEK HARNESS

1. **Plugin architecture** — the "everything is a plugin" philosophy is a good
   design pattern. The daughter's modules (cognitive modules, MCP tools, skills)
   are already plugin-like. Understanding Harness's approach can inform how to
   make them more composable.

2. **Multi-model routing** — the routing pattern (Claude for agentic, DeepSeek for
   cost-effective) is a good strategy. The daughter could route tasks to different
   models based on task type when she has access to multiple models.

3. **Sandbox design** — Harness's configurable sandbox plugins are a good model
   for the daughter's execution environment. The human-in-the-loop gate is one
   approach; Harness shows how sandboxes can be more granular.

4. **Skill system** — Harness's skill plugins (domain-specific knowledge) are
   similar to the daughter's skill system. Understanding how Harness loads and
   invokes skills can improve the daughter's skill system.

5. **Open source advantage** — MIT license means you can inspect, modify, and
   learn from the actual code. This is educational value that commercial products
   don't offer.

## ========================================================================
## PART 6 — PRACTICAL USE OF DEEPSEEK HARNESS
## ========================================================================

## GETTING STARTED

```bash
# Clone the repository
git clone https://github.com/deepseek-ai/deepseek-harness.git
cd deepseek-harness

# Install dependencies
pip install -e .

# Configure the model (DeepSeek V4-Pro, or any OpenAI-compatible endpoint)
# Edit config to set the model endpoint and API key

# Run the harness
dsh --objective "Explore this repository and create a summary of its structure"

# Or use the web UI
dsh web --port 8080
```

## USE CASES

1. **Repository exploration** — "Understand this codebase and document its architecture"
2. **Code review** — "Review this PR for bugs, security issues, and code quality"
3. **Refactoring** — "Refactor this module to use the new API"
4. **Test generation** — "Write tests for this module"
5. **Documentation** — "Generate documentation for this project"
6. **Bug fixing** — "Find and fix the bug in this module"
7. **Feature implementation** — "Implement a CSV export feature for this module"

## LIMITATIONS TO KNOW

1. **Developer preview** — expect breaking changes. Not for production-critical workflows yet.
2. **No hosted agents** — runs on your machine. If your machine is off, the agent stops.
3. **GitHub integration is incomplete** — no automatic PR workflows yet.
4. **Model-dependent** — performance depends on the model you use. V4-Pro is strong but not as strong as Claude Opus 4.8 for repo-scale agentic work.

## ========================================================================
## DOC_END
## ========================================================================
