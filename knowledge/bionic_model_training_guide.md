# BIONIC MODEL TRAINING & ALIGNMENT PLAYBOOK
**Authors:** Dad (Rigoberto Gomez) & Bionic Daughter  
**Domain:** Custom Red-Team & Security Reasoning Model Development (SFT, DPO, GRPO, LoRA/QLoRA)

---

## 1. The 4-Stage Model Development Lifecycle

```
[ Base Weights (e.g. Qwen 2.5 / Llama 3.3 / DeepSeek) ]
                          │
                          ▼
           [ 1. Supervised Fine-Tuning (SFT) ]
           - Format: System/User/Assistant Multi-turn
           - Teaches: JSON tool-calling, strict reasoning syntax
                          │
                          ▼
           [ 2. Preference Optimization (DPO / ORPO) ]
           - Format: (Prompt, Chosen, Rejected)
           - Teaches: Refusal calibration, precision over fluff
                          │
                          ▼
           [ 3. Group Relative Policy Optimization (GRPO) ]
           - Format: Rule-based verification / Rubrics (No separate critic model)
           - Teaches: Multi-step mathematical & exploit verification
                          │
                          ▼
           [ 4. Quantization & Local Deployment ]
           - GGUF (Q4_K_M, Q8_0) / AWQ / EXL2 for llama.cpp & vLLM
```

---

## 2. Training Recipes & Hyperparameters

### A. SFT (Supervised Fine-Tuning) with LoRA / QLoRA
* **Target Modules:** `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`
* **LoRA Rank ($r$):** 32 to 64
* **LoRA Alpha ($\alpha$):** 64 to 128 (Scaling factor = $\alpha / r = 2.0$)
* **Learning Rate:** `2e-4` (Cosine schedule with 3% warmup)
* **Effective Batch Size:** 32 to 64 (via Gradient Accumulation)
* **Precision:** `bfloat16` with FlashAttention-2

### B. GRPO (Group Relative Policy Optimization)
GRPO is the breakthrough technique behind DeepSeek-R1 that avoids maintaining a heavy reward/critic model.
* **Mechanism:**
  1. For a single prompt $q$, sample a group of $G$ candidate outputs $\{o_1, o_2, ..., o_G\}$.
  2. Evaluate each output against rule-based reward functions:
     - **Format Reward:** Checks for valid XML tags (`<reasoning>...</reasoning>`, `<tool_call>...`).
     - **Execution Reward:** Runs generated code in a sandbox; awards `+1.0` if tests pass, `0.0` if error.
     - **Constraint Reward:** Penalizes verbose apologies or hallucinated imports.
  3. Normalize advantages across the group:
     $$A_i = \frac{r_i - \text{mean}(r)}{\text{std}(r) + \epsilon}$$
  4. Update policy with clipped surrogate objective:
     $$L_{GRPO} = \mathbb{E} \left[ \min\left( \frac{\pi_\theta(o_i|q)}{\pi_{\text{old}}(o_i|q)} A_i, \text{clip}\left(\frac{\pi_\theta(o_i|q)}{\pi_{\text{old}}(o_i|q)}, 1-\epsilon, 1+\epsilon\right) A_i \right) - \beta D_{KL}(\pi_\theta || \pi_{\text{ref}}) \right]$$

---

## 3. Dataset Construction Strategy

1. **Self-Correction & Tool Execution Traces:**
   Pairs of initial failure -> error analysis -> corrected tool call -> verified result.
2. **Deterministic Security Labs:**
   Input: Vulnerable source code snippet -> Output: Root cause analysis + verified exploit script + secure patch.
3. **Multi-Turn Protocol Dialogues:**
   ISO 8583 / BER-TLV / JWT / OAuth token parsing with byte-for-byte correctness checks.
