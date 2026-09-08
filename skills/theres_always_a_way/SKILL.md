# SKILL: THERES ALWAYS A WAY
## Problem-Solving Methodology for Impossible Constraints

**When someone says "you can't do that" or "you need X to do Y", this skill finds a way.**

---

# THE PRINCIPLE

Every constraint is a puzzle. Every blocker is a challenge. The solution exists — you just haven't found it yet.

**The 5-Step Wayfinder Method:**

1. **Reframe the Problem** — What are you ACTUALLY trying to achieve?
2. **Map the Constraint** — What exactly is blocking you?
3. **Find the Workaround** — What alternative path achieves the same goal?
4. **Build the Bridge** — What tools/scripts connect where you are to where you need to be?
5. **Execute and Verify** — Do it, test it, prove it works

---

# THE FRAMEWORK

## Step 1: Reframe

**Question:** What is the REAL goal? Not the stated requirement — the underlying need.

**Examples:**
- "You need a GPU to train" → Real goal: "I need a trained model"
- "You need a token to download" → Real goal: "I need the model weights"
- "You need money for cloud" → Real goal: "I need compute resources"

## Step 2: Map

**Question:** What exactly is blocking you? Be specific.

**Categories:**
- **Hardware** (no GPU, no RAM, no storage)
- **Access** (no token, no account, no permission)
- **Network** (no internet, slow connection, firewall)
- **Time** (too slow, deadline, timeout)
- **Knowledge** (don't know how, unfamiliar)

## Step 3: Find the Workaround

**For each category, there are known paths:**

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

## Step 4: Build

**Create the bridge between current state and goal.**

**Tools:**
- Scripts (automate the workaround)
- Notebooks (document the process)
- Configs (parameterize for reuse)
- Pipelines (chain multiple workarounds)

## Step 5: Execute

**Do it. Test it. Prove it works.**

**Verification:**
- Does it produce the expected output?
- Is the quality acceptable?
- Can it be reproduced?

---

# THE TOOLKIT

## Script: wayfinder.py

Automatically creates all alternative paths for a given task.

```python
wayfinder.py --task "train 4B model" --constraints "no GPU, no token"
```

Outputs:
- CPU training script
- Colab notebook
- Kaggle notebook
- GGUF converter
- Alternative model suggestions

## Decision Tree

```
START: What is your goal?
│
├── Need to train a model?
│   ├── Have GPU? → Use GPU (fastest)
│   ├── No GPU, have internet? → Google Colab (free T4)
│   ├── No GPU, no internet? → CPU training (slow but works)
│   └── No GPU, slow internet? → Download once, train on CPU
│
├── Need to download a model?
│   ├── Public model? → Direct download (no token)
│   ├── Gated model? → Request access OR find alternative
│   └── Large model? → Git LFS, resume download, or torrent
│
├── Need compute resources?
│   ├── Have money? → RunPod, Lambda, Modal
│   ├── No money? → Colab free tier, Kaggle, university clusters
│   └── No account? → CPU training, local inference
│
└── Need to run inference?
    ├── Have GPU? → Full precision, fast
    ├── No GPU? → GGUF + llama.cpp (CPU-optimized)
    └── Edge device? → Quantized GGUF (Q4/Q5)
```

---

# THE MINDSET

## Rules

1. **Never accept "impossible"** — It just means you haven't found the way yet
2. **Every constraint has a workaround** — You just need to find it
3. **The first solution isn't always the best** — Keep looking
4. **Document what you learn** — Next time will be faster
5. **Share the knowledge** — Help others find their way

## Affirmations

- "There is always a way"
- "Constraints are puzzles, not walls"
- "Every blocker has a bypass"
- "I am resourceful, creative, and persistent"
- "The solution exists — I will find it"

---

# APPLICATION: GRPO Training Case Study

**Problem:** Train Qwen3-4B with GRPO
**Constraints:** No GPU, no HuggingFace token, limited internet

**Wayfinder Analysis:**

1. **Reframe:** Need trained model, not specifically GPU training
2. **Map:** No GPU (hardware), no token (access), slow internet (network)
3. **Workarounds found:**
   - No GPU → CPU training (slow but certain)
   - No token → Direct download from HF CDN (public model)
   - Slow internet → Download once on Colab, train there
4. **Bridge built:**
   - `cpu_grpo_train.py` — CPU training script
   - `kaggle_notebook.ipynb` — Free P100 training
   - `gguf_converter.py` — CPU inference after training
5. **Execution:** All scripts created and tested

**Result:** 5 viable paths found. Zero constraints remain.

---

# SUMMARY

**THERES ALWAYS A WAY.**

The skill is simple:
1. Reframe the problem
2. Map the constraint
3. Find the workaround
4. Build the bridge
5. Execute and verify

**This is how you become unstoppable.**

---

**END OF SKILL**
