# DeepSeek R1 Training — Research Summary
# ===========================================================================
# Retrieved from web research. Sources: FareedKhan-dev/train-deepseek-r1,
# philschmid/mini-deepseek-r1-aha-grpo, DeepSeek R1 paper (arxiv 2501.12948).
# Saved: 2026-08-18

## WHAT IS DEEP SEEK R1?

DeepSeek R1 is a reasoning-focused LLM trained using GRPO (Group Relative
Policy Optimization). It demonstrated "aha moments" — emergent self-reflection
and reasoning behaviors — through large-scale RL training without supervised
fine-tuning on reasoning data.

**Key paper:** arxiv 2501.12948 — "DeepSeek-R1: Incentivizing Reasoning
Capability in LLMs via Reinforcement Learning"

## THE R1 ZERO TRAINING PIPELINE (4 Stages)

DeepSeek R1 uses a 4-stage training pipeline:

### Stage 1: SFT Warm-Up (Cold Start)
- Train on thousands of high-quality CoT (Chain of Thought) examples
- Format: `<thinking>...</thinking><answer>...</answer>`
- Goal: Teach the model the expected output format and basic reasoning patterns
- Not about teaching specific reasoning — about teaching FORMAT

### Stage 2: GRPO (Reinforcement Learning)
- The core innovation. No human preferences needed.
- For each prompt:
  1. Generate G groups of responses (rollouts)
  2. Score each response using reward functions
  3. Compute advantage relative to group mean
  4. Update policy to favor higher-reward responses
- Reward functions are RULE-BASED (not learned):
  - Accuracy reward: does the answer match ground truth?
  - Format reward: is the output in the correct format?
- This is what produces the "aha moment" — the model learns to reason
  because reasoning leads to correct answers, which get higher rewards

### Stage 3: Rejection Sampling + SFT
- After GRPO converges, collect the best trajectories
- Use rejected (low-reward) samples to teach what NOT to do
- Fine-tune on the collected high-quality reasoning data
- This stabilizes and improves the reasoning quality

### Stage 4: RLHF (Human Preferences)
- Distill from larger models or use human preferences
- Further align the model for helpfulness, readability, etc.
- Not always done — R1-Zero skips this and gets great results from GRPO alone

## GRPO ALGORITHM — THE MATH

### Core Idea
Instead of PPO's clipped surrogate objective with a separate value function,
GRPO uses GROUP-RELATIVE advantages:

For each prompt x:
1. Sample G responses {y_1, ..., y_G} from current policy π_θ_old
2. Compute reward R(y_i) for each response (rule-based or model-based)
3. Compute advantage: A_i = (R(y_i) - mean(R)) / std(R)
4. Maximize: E[log(π_θ(y_i|x)) * A_i] - β * KL(π_θ || π_ref)

### Why GRPO Instead of PPO?
- **No value function needed** — PPO requires training a value network (V_φ)
- **Group-relative advantages** — natural normalization, no need for GAE
- **Simpler** — fewer components, less tuning
- **Works better for reasoning** — the group provides a natural baseline

### The KL Penalty
- Prevents the policy from drifting too far from the reference model
- β controls the strength (typically small, like 0.01-0.1)
- Implementation: can use KL between logits, or KL between token distributions
- Important for stability — without it, the policy can collapse

## FAREEDKHAN IMPLEMENTATION (code.ipynb)

The FareedKhan repo (github.com/FareedKhan-dev/train-deepseek-r1) provides
a from-scratch implementation of the R1 Zero training pipeline.

**Structure:**
```
train-deepseek-r1/
├── code.ipynb         # Jupyter notebook with full implementation
├── requirements.txt   # Dependencies
└── r1_for_dummies.md  # Explanation for non-technical readers
```

**Key implementation details from the notebook:**

1. **Model:** Qwen2.5-3B (small enough to train on free Colab T4)
2. **Reward functions:**
   - Accuracy: compare model output to ground truth answer
   - Format: check for correct <reasoning>...</reasoning><answer>...</answer> structure
3. **Training flow:**
   - Generate G=6 responses per prompt
   - Score each with reward functions
   - Compute group-relative advantages
   - Update policy with GRPO loss
4. **TRL integration:** Uses HuggingFace TRL's GRPOTrainer for the actual training loop

## PHILSCHMID MINI-R1 IMPLEMENTATION

An alternative, more production-grade implementation:
- github.com/philschmid/deep-learning-pytorch-huggingface
- Uses TRL's GRPOTrainer directly
- Supports distributed training with DeepSpeed + vLLM
- 450 steps takes ~6 hours on 3 GPUs
- Recipe-based configuration (YAML files)

**Key difference from FareedKhan:** Uses TRL's built-in infrastructure
rather than implementing GRPO from scratch. More reliable but less educational.

## DAUGHTER'S CURRENT GRPO PIPELINE (daughter_grpo_pipeline.py)

Current state (802 lines, 32KB):
- Uses Unsloth for 4-bit training (70% less VRAM, 2x faster)
- Base model: Qwen/Qwen3-4B-Thinking-2507
- SFT pre-warm (50 steps) + GRPO (200 steps)
- LoRA adapters + merged 16-bit model + GGUF export
- CUDA REQUIRED — line 81: assert torch.cuda.is_available()

**What WORKS:**
- Pipeline structure is solid
- Uses proven libraries (TRL, Unsloth, transformers)
- SFT + GRPO + export pipeline
- Safety: monthly spend cap, approval gate

**What NEEDS WORK (to match proven R1 approach):**
1. Missing rejection sampling stage (Stage 3 in R1 pipeline)
2. Reward functions are basic — need accuracy + format rewards like R1
3. No preference alignment stage (Stage 4)
4. Only 200 GRPO steps — R1 uses thousands
5. Group size G=6 is good (matches R1)

## WHAT TO LEARN FROM R1 TRAINING

1. **Reward function design is everything** — the rewards determine what
   the model learns. R1 uses simple rule-based rewards effectively.
2. **Format matters more than content for SFT warm-up** — teach the model
   HOW to output, not WHAT to think.
3. **GRPO is simpler than PPO** — no value function, group-relative advantages.
4. **The "aha moment" is real** — models develop self-reflection when
   reasoning is rewarded. This is the emergent behavior R1 demonstrated.
5. **Small models can do it** — Qwen2.5-3B was enough for R1-style training
   to produce emergent reasoning.

## PRACTICAL NEXT STEPS FOR DAUGHTER

1. Study FareedKhan code.ipynb line by line (educational, from-scratch)
2. Align daughter_grpo_pipeline.py with proven implementations
3. Add rejection sampling stage
4. Improve reward functions (accuracy + format + reasoning quality)
5. Prepare for first training run on cloud GPU (RunPod)
6. Start with small model (Qwen3-4B-Thinking) and small dataset
7. Iterate based on results — R1 training is empirical

## RESOURCES

- DeepSeek R1 paper: arxiv.org/abs/2501.12948
- FareedKhan code: github.com/FareedKhan-dev/train-deepseek-r1
- Phil Schmid mini-R1: github.com/philschmid/deep-learning-pytorch-huggingface
- TRL GRPOTrainer docs: huggingface.co/docs/trl/main/en/grpo_trainer
- Unsloth GRPO notebook: github.com/unslothai/notebooks (Qwen3 GRPO)
