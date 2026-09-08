# ADVANCED AI MODEL STEERING, LOCAL INFERENCE & CUSTOMIZATION GUIDE
**Authors:** Bionic Daughter & Dad (Rigoberto Gomez)  
**Domain:** Open-Weights Inference (Ollama / llama.cpp), Activation Steering, System Prompt Engineering, and LoRA Customization  
**Date:** August 2026  

---

## 1. Running Frontier & Open Models with Zero API Keys

Using local inference engines allows us to run state-of-the-art open-weight models (Qwen 2.5 Coder, DeepSeek R1 Distill, Llama 3.3) completely offline without API rate limits or recurring costs.

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Local Runtime Engine (Ollama / llama-server / vLLM)      │
│    - Loads quantized GGUF weights (Q4_K_M, Q8_0)            │
│    - Manages GPU VRAM offloading and KV-cache               │
└──────────────────────────────┬──────────────────────────────┘
                               │ OpenAI-Compatible HTTP / stdio
┌──────────────────────────────▼──────────────────────────────┐
│ 2. Hermes / Orca ADE Orchestration Layer                    │
│    - Points base_url: "http://localhost:11434/v1"           │
│    - Zero API key required (api_key: "local")               │
└──────────────────────────────┬──────────────────────────────┘
                               │ Structured Tool Calling
┌──────────────────────────────▼──────────────────────────────┐
│ 3. Custom Steering & LoRA Adapter Layers                     │
│    - Injects system prompts, XML reasoning formatters       │
│    - Hot-swaps fine-tuned domain LoRA adapters              │
└─────────────────────────────────────────────────────────────┘
```

### Supported Local Runtimes:
1. **Ollama:** `ollama run qwen2.5-coder:7b` (Provides instant local OpenAI-compatible endpoint at `http://localhost:11434/v1`).
2. **llama.cpp / llama-server:** `llama-server -m model.gguf -c 8192 --n-gpu-layers 99` (Bare-metal high throughput).
3. **vLLM:** Optimized for batched parallel subagent execution.

---

## 2. Advanced Model Steering & Prompt Architecture

Steering a model to output precise technical artifacts without conversational filler relies on structured prompt engineering and inference constraints:

### A. Pre-Fill Invariant Injection
In models supporting assistant pre-fills (or via chat templates), priming the assistant turn forces strict formatting:
```json
{
  "role": "assistant",
  "content": "<reasoning>\n1. Step 1: Analyze protocol bitmask...\n"
}
```
*The model is mathematically forced to continue within the designated reasoning block rather than generating conversational preambles.*

### B. Representation Engineering & System Roles
Explicit role-conditioning anchors the model's latent representations to specialized technical domains:
* **Security Auditor:** Focuses attention weights on boundary conditions, integer overflow edge cases, and missing authorization checks.
* **Systems Engineer:** Emphasizes memory safety, zero-allocation data structures, and deterministic error propagation.

---

## 3. Customizing Models to Your Exact Specification (The LoRA/GRPO Recipe)

To turn any general-purpose base model into a customized domain expert:

```
[ Base Open Model (e.g., Qwen 2.5 Coder 7B) ]
                     │
                     ▼
[ 1. Ingest Synthetic Reasoning Data (grpo_security_reasoning_dataset.jsonl) ]
                     │
                     ▼
[ 2. 4-bit QLoRA Parameter-Efficient Fine-Tuning ]
     - Target: All Linear Attention Projections (q, k, v, o, gate, up, down)
     - Rank r=64, Alpha=128
                     │
                     ▼
[ 3. Merge Weights & Quantize to GGUF (llama.cpp) ]
                     │
                     ▼
[ 4. Local Deployment in Orca / Hermes ]
```

---

## 4. Summary & Best Practices
1. **Zero API Key Independence:** Open weights run locally via Ollama / llama.cpp give us total autonomy and privacy.
2. **Deterministic Formatting:** XML tags (``, `<solution>`) enforce verifiable reasoning.
3. **Continuous Data Distillation:** Every sandbox tool run generates real execution traces that feed directly into our next fine-tuning cycle.
