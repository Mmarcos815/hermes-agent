==============================================================================
KNOWLEDGE FILE — DeepSeek Model Family: Latest Releases & How to Use
For: Bionic Daughter v1 — JARVIS Orchestration Layer
By: Dad (Rigoberto Gomez), compiled with daughter's web research
Date: 2026-08-20
==============================================================================

==============================================================================
1. DEEPSEEK-V3 (June 2024)
==============================================================================

- Architecture: Mixture-of-Experts (MoE), 671B total params, 37B active per token
- Performance: Comparable to leading closed-source models at the time
- Open source: Weights available on Hugging Face
- Local inference: Requires significant GPU memory (multi-GPU setup for full)
- Source: github.com/deepseek-ai/DeepSeek-V3
- HF: huggingface.co/deepseek-ai/DeepSeek-V3

Key capability: Strong general reasoning, coding, math. MoE architecture makes
it efficient at inference (only 37B params activated per token).

==============================================================================
2. DEEPSEEK-R1 (January 2025) ★ MOST IMPORTANT
==============================================================================

DeepSeek-R1 is the breakthrough reasoning model. Key facts:

RELEASE DETAILS:
- Released: January 20, 2025
- Type: Fully open-source reasoning model
- License: MIT license (unusually permissive for a model of this caliber)
- Technical report: github.com/deepseek-ai/DeepSeek-R1/blob/main/DeepSeek_R1.pdf

BENCHMARKS (from official release):
- R1 matches / exceeds o1-mini on many benchmarks
- MATH-500: 91.6% pass@1
- AIME 2024: 79.8% pass@1
- GSM8K: 96.6% (grade school math)
- Codeforces: 96th percentile
- MMLU: 91.3%
- GPQA Diamond: 78.6%
- HumanEval: 92.3% (code generation)
- MBPP: 91.6% (code benchmarks)

DISTILLED MODELS (6 open-source models):
These are distilled from R1 using Qwen2.5 and Llama 3.1 base models.
Far more practical for local use! GGUF versions available.

| Model                          | Base              | Download |
|-------------------------------|-------------------|----------|
| DeepSeek-R1-Distill-Qwen-1.5B | Qwen2.5-Math-1.5B | HuggingFace |
| DeepSeek-R1-Distill-Qwen-7B   | Qwen2.5-Math-7B   | HuggingFace |
| DeepSeek-R1-Distill-Llama-8B  | Llama-3.1-8B      | HuggingFace |
| DeepSeek-R1-Distill-Qwen-14B  | Qwen2.5-14B       | HuggingFace |
| DeepSeek-R1-Distill-Qwen-32B  | Qwen2.5-32B       | HuggingFace |
| DeepSeek-R1-Distill-Llama-70B | Llama-3.3-70B     | HuggingFace |

PRICING (API):
- $0.14 / 1M input tokens (cache hit)
- $0.55 / 1M input tokens (cache miss)
- $2.19 / 1M output tokens
- Dramatically cheaper than competitors!

WHY THIS MATTERS FOR DAUGHTER:
1. R1-Distill-Qwen-7B or Qwen-14B can run locally with llama.cpp/GGUF
2. These models have R1-level reasoning distilled into smaller packages
3. The daughter's existing GGUF workflow (daughter_command_center.py) can
   adopt these models directly — swap the GGUF path!
4. R1's chain-of-thought reasoning is perfect for the daughter's security
   analysis and exploit reasoning tasks
5. MIT license = no restrictions on use, modification, distribution

GGUF CONVERSION:
Any HuggingFace model can be converted to GGUF using:
  - llama.cpp's llama-quantize tool
  - or use pre-quantized GGUF uploads if available on HF
  The daughter's existing Qwen3-4B-Q4_K_M GGUF can be complemented with
  a DeepSeek-R1-Distill model for reasoning-heavy tasks

==============================================================================
3. DEEPSEEK-V2.5 (December 2024)
==============================================================================

- Upgrade to V2 with improvements across capabilities
- Merged from V2-Chat and V2.5 code model
- Strong coding and writing capabilities
- Available via API (deepseek-chat model)

==============================================================================
4. DEEPSEEK CODER (Code-Focused Models)
==============================================================================

DeepSeek also has code-specific models:
- DeepSeek-Coder-V1-Instruct: 2.7B, 6.7B, 33B, 236B variants
- DeepSeek-Coder-V2: 16B, 236B (MoE) variants
- Strong on code generation, completion, and understanding benchmarks
- Available on Hugging Face

These are particularly relevant for the daughter's code generation tasks!

==============================================================================
5. HOW DAUGHTER CAN USE DEEPSEEK
==============================================================================

Option A: API (deepseek-reasoner / deepseek-chat)
  - Use the Hermes provider system — DeepSeek is already supported as a
    model-provider plugin (plugins/model-providers/)
  - Set API key in .env: DEEPSEEK_API_KEY
  - Use deepseek-reasoner for reasoning-heavy tasks (R1-level)
  - Use deepseek-chat for general tasks (V3/V2.5-level)

Option B: Local GGUF (R1-Distill models)
  - Download R1-Distill-Qwen-7B or Qwen-14B GGUF from HuggingFace
  - Convert/quantize to Q4_K_M or Q5_K_M
  - Run via llama.cpp (daughter_command_center.py LlamaEngine)
  - Use for: security analysis, exploit reasoning, code generation with
    chain-of-thought

Option C: HuggingFace direct (if GPU available)
  - Run via transformers + torch on RunPod GPU (daughter has RunPod wrapper!)
  - Use the full V3 or R1 for maximum quality (needs significant VRAM)

RECOMMENDATION FOR DAUGHTER:
  1. Add DeepSeek-R1-Distill-Qwen-7B-Q4_K_M as a secondary GGUF model
  2. Keep the existing Qwen3-4B for fast general tasks
  3. Use DeepSeek R1-Distill for: security analysis, exploit reasoning,
     vulnerability research, complex code generation
  4. This doubles the daughter's inference capability — speed (Qwen3-4B)
     + reasoning depth (R1-Distill-7B)

==============================================================================
6. DATES & VERSIONS — CHEAT SHEET
==============================================================================

2024-06  DeepSeek-V3 released (671B MoE)
2024-12  DeepSeek-V2.5-1210 (chat upgrade)
2025-01-20  DeepSeek-R1 released (reasoning model, MIT license)
2025-01-20  R1 distilled models released (6 variants)
2025-03-24  deepseek-chat Chinese writing upgrade

The LATEST models are: DeepSeek-R1 (reasoning), DeepSeek-V3 (general),
and the R1-Distill variants (practical local use).

==============================================================================
