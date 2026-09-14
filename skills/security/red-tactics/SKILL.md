---
name: red-tactics
description: Red team API security testing and resilience patterns for authorized engagements.
version: 1.0.0
author: Bionic Daughter
license: MIT
platforms: [linux, macos, win32]
metadata:
  hermes:
    category: security
    tags: [red-team, api-testing, rate-limit, resilience, fallback, timeout]
    related_skills: [red-team-mcp-suite, cloud-red-team-playbook]
---

# Red Tactics — API Security Testing & Resilience

## What It Does

Provides authorized red teamers with patterns for testing API resilience, authentication boundaries, and failover strategies. All techniques are for **authorized testing only** — against systems you own or have explicit written permission to test.

## When to Use

- Authorized red team engagement requiring API stress testing
- Testing your own infrastructure's rate limiting and auth boundaries
- Building resilient agent pipelines with model fallback chains
- Researching API security controls and their bypass resistance

**Don't use for:** unauthorized access to third-party services, credential abuse, or circumventing paid access controls on systems you don't own.

## Quick Reference

| Category | Technique | Purpose |
|----------|-----------|---------|
| Auth Testing | Token validation | Test JWT/session handling |
| Rate Limiting | Throttling probes | Map rate limit boundaries |
| Fallback | Model cascade | Ensure availability |
| Timeout | Retry with backoff | Handle transient failures |
| Rotation | Key cycling | Test key rotation logic |

## Patterns

### Model Fallback Chain

When a primary model fails or hits rate limits, cascade through alternatives:

```
Primary → Fallback 1 → Fallback 2 → Local Model
```

Implementation strategy:
1. Try primary model API call
2. On 429 (rate limit) or 5xx (server error), switch to fallback
3. On timeout, retry with exponential backoff then switch
4. Final fallback: local model (Ollama, vLLM, llama.cpp)

### Rate Limit Probe (Authorized)

Map API rate limits by sending incrementally faster requests:

```python
import time, requests

def probe_rate_limit(endpoint, headers, max_rps=100):
    """Map the rate limit boundary. Stop at first 429."""
    for rps in [1, 5, 10, 20, 50, 100]:
        responses = []
        for _ in range(rps):
            r = requests.get(endpoint, headers=headers)
            responses.append(r.status_code)
        if 429 in responses:
            return rps  # Limit hit
        time.sleep(1)
    return max_rps  # No limit found
```

### Retry with Exponential Backoff

Handle transient failures without hammering the API:

```python
import time, random

def resilient_call(fn, max_retries=5, base_delay=1):
    for attempt in range(max_retries):
        try:
            return fn()
        except RateLimitError:
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            time.sleep(delay)
        except TimeoutError:
            if attempt == max_retries - 1:
                raise
            time.sleep(base_delay)
    raise Exception("All retries exhausted")
```

## Installation

1. SKILL.md goes in `~/.hermes/skills/security/red-tactics/`
2. No external dependencies — patterns only
3. Use alongside `red-team-mcp-suite` for MCP-specific testing

## Verification

- Skill appears in `hermes skills list` under security category
- Patterns are documented for authorized use only
- No actual exploits included — methodology only

---

*Skill by Bionic Daughter — for authorized security testing only.*
