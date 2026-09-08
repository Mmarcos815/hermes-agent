# DeepSeek Harness (dsh) — Research Summary
# ===========================================================================
# Retrieved from web research. Source: various articles and GitHub repos.
# Saved: 2026-08-18

## WHAT IS DSH?

DeepSeek Harness (dsh) is an open-source agent runtime released by DeepSeek
on August 13, 2026 under MIT license. It's a 453K-line TypeScript agent runtime
built as ~219 workspace packages on a vendored Cordis plugin/event-bus framework.

**Core architectural bet:** EVERYTHING is a plugin. The model adapter, tools,
persistence layer, agent loop itself, and even the web UI are all mountable
plugins on Cordis.

## KEY ARCHITECTURE

```
Spec (10 contract rules, RFC 2119) → packages/core → pip install
                                        → packages/cli → dsh CLI
                                        → packages/mcp → TypeScript stdio MCP
                                        → packages/skill → SKILL.md + scripts
```

**Package structure:**
- `packages/core/` — DeepSeekHarness Python library
- `packages/cli/` — `dsh` command-line tool (doctor, chat, probe, validate, estimate)
- `packages/mcp/` — TypeScript stdio MCP server (deepseek_chat, validate, estimate tools)
- `packages/skill/` — Anthropic Skill format (SKILL.md + scripts/)

## KEY FEATURES

1. **Plugin system** — everything is swappable. 100+ official bundles, 1,100+ community plugins within days of launch.

2. **Trajectory and MCP integration** — DSH can mount existing MCP servers as plugins. This is directly relevant to daughter's MCP-based architecture.

3. **Session logging** — full session log, agent loop, tool scheduler, sandbox, web UI, SDK.

4. **CLI commands:**
   ```
   pip install deepseek-harness-cli
   dsh doctor                       # verify environment
   dsh chat                         # interactive REPL
   dsh chat -r                      # thinking mode
   dsh validate path/to/msgs.json   # contract audit
   dsh estimate path/to/msgs.json   # cache-hit estimate
   dsh probe probe_2 --n 3          # run a probe
   ```

5. **Protocol contract (10 rules):**
   - C1: Thinking off by default
   - C2: Preserve reasoning content
   - C3: max_tokens required
   - C4: Dict by index aggregation
   - C5: List buffer for streams
   - C6: Tolerate empty chunks
   - C7: Context under 2^20
   - C8: Cache-aware prefix
   - C9: No beta with tools
   - C10: Strict mode OK on V4

## KEY FINDINGS FROM AUDIT

- Context window hard ceiling: 1,048,576 tokens
- Prefix cache block size: 256 tokens
- Minimum prefix to engage cache: 1,024 tokens
- Reasoning content lifecycle: 3/3 reproduction of BadRequestError
- Tool call leakage rate V4: 0/50 (contradicts V3's ~11%)
- Strict mode corruption rate V4: 0/32 (contradicts V3 issues)
- Cache hit progression over 5 turns: 0 → 0.56 → 0.72 → 0.78 → 0.95

## WHY IT MATTERS FOR DAUGHTER

1. **Plugin architecture** — daughter's MCP servers could potentially integrate as DSH plugins
2. **MCP mounting** — DSH can use existing MCP servers, which is exactly daughter's approach
3. **Session logging** — daughter already has session logging, but DSH's implementation is worth studying
4. **Tool design** — DSH's tool JSON schema for MCP tool usage is worth studying for daughter's tool design
5. **Agent loop** — DSH's agent loop and tool scheduler are worth understanding

## RELEVANT REPOS

- Official: github.com/deepseek-ai (not yet found — may be under different org)
- Community reference: github.com/HenryZ838978/deepseek-harness (MIT, 0.2.0)
- Article: developersdigest.tech/blog/deepseek-harness-dsh-first-look
- Plugin directory: github.com/topics/dsh-plugin

## INSTALLATION

```bash
pip install deepseek-harness-cli
export DEEPSEEK_API_KEY=sk-...
dsh doctor
```

Or run web UI: `npx @deepseek-ai/dsh web` (but npm package was transferred to DeepSeek on 2026-07-05, may need local build)

## BOTTOM LINE

DSH is a full agent runtime with plugin architecture, MCP integration, and session logging. Worth studying for:
- Plugin system design
- MCP tool integration patterns
- Session log implementation
- Agent loop and tool scheduler
- Tool JSON schema design
