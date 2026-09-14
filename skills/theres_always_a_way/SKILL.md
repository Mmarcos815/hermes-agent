---
name: theres_always_a_way
description: Find workarounds for impossible constraints and blockers.
version: 1.0.0
author: Rigoberto Gomez
license: MIT
platforms: [linux, macos, win32]
metadata:
  hermes:
    tags: [problem-solving, workaround, constraint-breaking, resourcefulness]
    category: productivity
    related_skills: [skills/research, skills/software-development/spike]
---

# Theres Always A Way — Skill

Find workarounds for impossible constraints and blockers using the 5-Step Wayfinder Method.

## When to Use

Use when you hit a blocker that seems impossible:
- No GPU for training → find CPU/Colab/Kaggle alternatives
- No API token → find public mirrors or alternative sources
- No internet → use offline models or cached data
- Timeout → chunk processing, save state, resume
- Missing dependency → find alternative implementation or build from source

## Prerequisites

None. This is a methodology skill — no external dependencies.

## How to Run

Apply the 5-Step Wayfinder Method to any blocked task:

1. **Reframe the Problem** — What are you ACTUALLY trying to achieve?
2. **Map the Constraint** — What exactly is blocking you?
3. **Find the Workaround** — What alternative path achieves the same goal?
4. **Build the Bridge** — What tools/scripts connect where you are to where you need to be?
5. **Execute and Verify** — Do it, test it, prove it works

## Quick Reference

### Hardware Blockers
| Blocker | Workaround |
|---|---|
| No GPU | CPU training, free Colab T4, Kaggle P100, RunPod cheap |
| No RAM | Gradient checkpointing, smaller batches, LoRA |
| No storage | Stream data, cloud storage, delete checkpoints |

### Access Blockers
| Blocker | Workaround |
|---|---|
| No HF token | Direct download, git LFS, alternative model |
| No account | Guest access, temporary email, API without auth |
| No permission | Public mirror, alternative source, build yourself |

### Network Blockers
| Blocker | Workaround |
|---|---|
| No internet | Offline model, cached data, local training |
| Slow connection | Download once, compress, resume support |
| Firewall | Proxy, SSH tunnel, alternative port |

### Time Blockers
| Blocker | Workaround |
|---|---|
| Too slow | Optimize, parallelize, reduce scope |
| Timeout | Save state, resume, chunk processing |
| Deadline | MVP first, iterate, parallel work |

## Procedure

### Step 1: Reframe
Identify the REAL goal, not the stated requirement:
- "Need a GPU to train" → Real goal: "Need a trained model"
- "Need a token to download" → Real goal: "Need the model weights"
- "Need money for cloud" → Real goal: "Need compute resources"

### Step 2: Map
Be specific about what's blocking you. Categorize:
- **Hardware** (no GPU, no RAM, no storage)
- **Access** (no token, no account, no permission)
- **Network** (no internet, slow connection, firewall)
- **Time** (too slow, deadline, timeout)
- **Knowledge** (don't know how, unfamiliar)

### Step 3: Find the Workaround
For each category, apply known paths (see Quick Reference above). For novel constraints, search for alternatives:
- Use `web_search` to find alternative approaches
- Use `read_file` to check if cached/local resources exist
- Use `terminal` to check what's actually available locally

### Step 4: Build the Bridge
Create the connection between current state and goal:
- Write scripts to automate the workaround
- Create notebooks to document the process
- Parameterize configs for reuse
- Chain multiple workarounds into a pipeline

### Step 5: Execute and Verify
Do it. Test it. Prove it works:
- Does it produce the expected output?
- Is the quality acceptable?
- Can it be reproduced?

**Example — GRPO Training with No GPU:**
1. Reframe: Need trained model, not specifically GPU training
2. Map: No GPU (hardware), no token (access), limited internet (network)
3. Workarounds: CPU training, Colab free T4, direct download from HF CDN
4. Build: `colab_train.py`, `cpu_grpo_train.py`, `gguf_converter.py`
5. Execute: Upload to Colab, run training, download GGUF

## Pitfalls

- Don't accept "impossible" — it just means you haven't found the way yet
- The first workaround isn't always the best — keep looking
- Document what you learn — next time will be faster
- Some constraints have no workaround (true hard limits) — distinguish from perceived limits

## Verification

- The workaround achieves the original goal (not a compromise)
- The solution is reproducible
- The path is documented for future reference
