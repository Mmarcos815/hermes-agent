---
name: axolotl
description: YAML-configured LLM fine-tuning with LoRA, QLoRA, DPO, KTO, ORPO, GRPO.
version: 1.1.0
author: Orchestra Research
license: MIT
dependencies: [axolotl, torch, transformers, datasets, peft, accelerate, deepspeed]
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Fine-Tuning, Axolotl, LLM, LoRA, QLoRA, DPO, KTO, ORPO, GRPO, YAML, HuggingFace, DeepSpeed, Multimodal, FSDP]

---

# Axolotl — YAML LLM Fine-Tuning

Axolotl is a fine-tuning framework that uses declarative YAML configs to train LLMs with LoRA, QLoRA, DPO, KTO, ORPO, GRPO, and full fine-tuning. Supports 100+ models via HuggingFace. Handles single-GPU, multi-GPU (FSDP/DeepSpeed), and cloud (Modal) training.

## When to Use Axolotl

**Use Axolotl when:**
- You want YAML-based configs (not Python scripts) for reproducible training
- Fine-tuning Llama, Mistral, Qwen, DeepSeek, Phi, Gemma, or 100+ other HF models
- Need LoRA/QLoRA for memory-efficient training
- Running preference optimization (DPO, KTO, ORPO, GRPO)
- Using DeepSpeed or FSDP for multi-GPU training
- Training on Modal cloud or locally

**Use alternatives when:**
- **TRL**: You want programmatic trainer control and RL pipelines (RLOO, GRPO)
- **Unsloth**: You need maximum speed on a single GPU
- **torchtitan**: You're pretraining from scratch
- **LitGPT**: You want minimal, educational fine-tuning

## Installation

```bash
pip install axolotl[deepspeed]      # With DeepSpeed
pip install axolotl[accelerate]     # With Accelerate
pip install axolotl[all]            # Everything

# Or from source for latest features
git clone https://github.com/axolotl-ai-cloud/axolotl
cd axolotl
pip install -e ".[dev]"
```

## Quick start

### Minimal YAML config (LoRA, single GPU)

```yaml
# config.yaml
base_model: meta-llama/Llama-3.1-8B-Instruct
sequence_len: 2048
gradient_accumulation_steps: 4
micro_batch_size: 2
epoch_training: false
steps: 500
optimizer: pagedadamw8bit
lr_scheduler: cosine
learning_rate: 2e-4
warmup_steps: 10
mixed_precision: bf16
lora:
  r: 16
  lora_alpha: 16
  target_modules:
    - q_proj
    - k_proj
    - v_proj
    - o_proj
    - gate_proj
    - up_proj
    - down_proj
  lora_dropout: 0.0
adapter: lora
wandb: true
```

```bash
axolotl train config.yaml
```

### Dataset formats

Axolotl accepts several dataset formats. The most common is the `sharegpt` format:

```json
{
  "conversations": [
    {"from": "human", "value": "Explain quantum computing"},
    {"from": "gpt", "value": "Quantum computing uses qubits..."}
  ]
}
```

Or instruction-response pairs:

```json
{
  "instruction": "Explain quantum computing",
  "input": "",
  "output": "Quantum computing uses qubits..."
}
```

```bash
# Train with a HuggingFace dataset
axolotl train config.yaml \
  --dataset.locations=trl-lib/Capybara \
  --dataset.subset=sharegpt \
  --dataset.format=sharegpt
```

### DPO config (preference alignment)

```yaml
base_model: meta-llama/Llama-3.1-8B-Instruct
sequence_len: 2048
gradient_accumulation_steps: 4
micro_batch_size: 2
optimizer: pagedadamw8bit
lr_scheduler: cosine
learning_rate: 5e-7
warmup_steps: 10
mixed_precision: bf16
lora:
  r: 16
  target_modules: [q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]
adapter: lora

# DPO-specific
dpo:
  beta: 0.1
  label_smoothing: 0.0
  max_prompt_length: 1024
  max_completion_length: 1024

dataset:
  - path: trl-lib/ultrafeedback_binarized
    type: dpo
    split: train
```

```bash
axolotl train dpo_config.yaml
```

### GRPO config (reinforcement learning)

```yaml
base_model: meta-llama/Llama-3.1-8B-Instruct
sequence_len: 2048
micro_batch_size: 1
gradient_accumulation_steps: 8
optimizer: adamw8bit
lr_scheduler: cosine
learning_rate: 1e-5
mixed_precision: bf16
lora:
  r: 16
  target_modules: [q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]

grpo:
  num_generations: 4
  max_new_tokens: 256
  temperature: 0.7
  top_p: 0.9
  reward_functions:
    - name: length
    - name: custom
      function: my_reward_fn

dataset:
  - path: /path/to/grpo_data.jsonl
    type: grpo
    split: train
```

### FSDP config (multi-GPU)

```yaml
base_model: meta-llama/Llama-3.1-70B-Instruct
sequence_len: 4096
gradient_accumulation_steps: 8
micro_batch_size: 1
optimizer: pagedadamw8bit
lr_scheduler: cosine
learning_rate: 2e-5
mixed_precision: bf16
lora:
  r: 16
  target_modules: [q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]

fsdp:
  version: 2
  min_num_params: 1e8
  xla: false
  fsdp_config:
    offload_params: true
    state_dict_type: FULL_STATE_DICT
    auto_wrap_policy: TRANSFORMER_BASED_WRAP
    transformer_layer_cls_to_wrap: LlamaDecoderLayer
    reshard_after_forward: true
```

```bash
accelerate launch --num_processes=8 --num_machines=2 \
  --rdzv_backend=c10d --rdzv_endpoint=$MASTER_ADDR:29500 \
  -m axolotl.cli train fsdp_config.yaml
```

### DeepSpeed config

```yaml
base_model: meta-llama/Llama-3.1-70B-Instruct
sequence_len: 4096
gradient_accumulation_steps: 8
micro_batch_size: 1
optimizer: pagedadamw8bit
lr_scheduler: cosine
learning_rate: 2e-5
mixed_precision: bf16
lora:
  r: 16
  target_modules: [q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]

deepspeed:
  stage: 3
  offload: true            # ZeRO-3 Offload
  xuna: false
```

```bash
deepspeed --num_gpus=8 train.py ds_config.yaml
```

## Common workflows

### Workflow 1: Fine-tune Llama 3.1 8B on custom data

```bash
# 1. Write config (see minimal YAML above)
# 2. Prepare dataset as JSONL
# 3. Train
axolotl train config.yaml

# 4. Merge LoRA weights into base model
axolotl merge config.yaml --merge-path merges/llama3-8b-custom

# 5. Test merged model
python -c "
from transformers import AutoModelForCausalLM, AutoTokenizer
model = AutoModelForCausalLM.from_pretrained('merges/llama3-8b-custom')
tokenizer = AutoTokenizer.from_pretrained('merges/llama3-8b-custom')
inputs = tokenizer('Explain quantum computing', return_tensors='pt').to('cuda')
print(tokenizer.decode(model.generate(**inputs, max_new_tokens=200)[0]))
"
```

### Workflow 2: DPO alignment with preference data

```bash
axolotl train dpo_config.yaml \
  --dataset.locations=trl-lib/ultrafeedback_binarized \
  --dataset.format=dpo
```

### Workflow 3: QLoRA on single GPU (24GB)

```yaml
base_model: meta-llama/Llama-3.1-70B-Instruct  # Yes, 70B on 24GB with QLoRA!
sequence_len: 2048
micro_batch_size: 1
gradient_accumulation_steps: 16
load_in_4bit: true              # QLoRA
bnb_config:
  load_in_4bit: true
  bnb_4bit_compute_dtype: bf16
  bnb_4bit_quant_type: nf4
  bnb_4bit_use_double_quant: true
lora:
  r: 16
  target_modules: [q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]
```

### Workflow 4: Cloud training on Modal

Axolotl has built-in Modal cloud support:

```yaml
# In your config
cloud:
  provider: modal
  image: ghcr.io/axolotl-ai-cloud/axolotl:latest
  gpu: H100
  timeout_min: 60
```

```bash
axolotl train config.yaml   # Automatically launches on Modal
```

## Advanced features

### Multimodal (vision + text)

Axolotl supports LLaVA-style multimodal fine-tuning:

```yaml
base_model: liuhaotian/llava-v1.5-7b
sequence_len: 2048
lora:
  r: 16
  target_modules: [q_proj, v_proj, k_proj, o_proj]

multimodal:
  vision_encoder: openai/clip-vit-large-patch14-336
  image_token_index: 249000  # <image> token id
```

### Custom hooks and callbacks

```yaml
callbacks:
  - name: custom_callback
    kwargs:
      my_param: value
```

### Evaluation during training

```yaml
eval:
  enabled: true
  dataset:
    - path: /path/to/eval.jsonl
      type: completion
  eval_every_n_steps: 50
```

### Save compressed models

```yaml
save_compressed: true   # ~40% smaller, vLLM-compatible
```

## Configuration reference

### Top-level keys

| Key | Description |
|-----|-------------|
| `base_model` | HuggingFace model ID |
| `sequence_len` | Max sequence length |
| `micro_batch_size` | Per-GPU batch size |
| `gradient_accumulation_steps` | Effective batch = micro × accum × GPUs |
| `optimizer` | `pagedadamw8bit`, `adamw8bit`, `sgd`, etc. |
| `lr_scheduler` | `cosine`, `linear`, `constant`, etc. |
| `learning_rate` | Peak LR |
| `warmup_steps` | LR warmup steps |
| `mixed_precision` | `bf16`, `fp16`, `none` |
| `steps` | Total training steps (if `epoch_training: false`) |
| `epoch_training` | Train for N epochs instead of N steps |
| `load_in_4bit` | Enable QLoRA |

### LoRA config

| Key | Description |
|-----|-------------|
| `lora.r` | LoRA rank (8, 16, 32, 64) |
| `lora.lora_alpha` | Scaling factor (typically = r) |
| `lora.target_modules` | Modules to apply LoRA to |
| `lora.lora_dropout` | LoRA dropout (0-0.1) |
| `lora.bias` | `none`, `all`, `lora_only` |

### FSDP config

| Key | Description |
|-----|-------------|
| `fsdp.version` | `1` or `2` |
| `fsdp.min_num_params` | Min params to wrap as FSDP unit |
| `fsdp.offload_params` | Offload params to CPU |

## Tips

1. **Start small**: Test with `sequence_len=512`, `micro_batch_size=1`, 10 steps
2. **BF16 over FP16**: More stable on A100/H100/B200
3. **QLoRA for large models**: 70B on 24GB is possible
4. **Watch VRAM**: Use `max_memory` in Accelerate config if needed
5. **Dataset quality > quantity**: 1000 good examples beats 100k noisy ones
6. **Use `save_compressed`** for deployment — saves space, vLLM-compatible

## Common issues

### NCCL timeout on multi-GPU

```bash
export NCCL_TIMEOUT=3600  # 1 hour timeout
export NCCL_DEBUG=INFO    # Debug comms
```

### OOM during training

- Reduce `sequence_len` and `micro_batch_size`
- Enable `load_in_4bit: true` (QLoRA)
- Use `gradient_accumulation_steps` to keep effective batch size
- Enable `fsdp.offload_params: true` or `deepspeed.stage: 3` with offload

### DataLoader is slow

- Use `--dataset.num_workers=4` to parallelize data loading
- Set `HF_HUB_ENABLE_HF_TRANSFER=1` for faster HF downloads

### Tips not applying

- Check `lora.target_modules` — must match model architecture
- Verify LoRA is enabled: `adapter: lora` (not `full` or missing)

## Resources

- Docs: https://docs.axolotl.ai/
- GitHub: https://github.com/axolotl-ai-cloud/axolotl
- Config examples: https://github.com/axolotl-ai-cloud/axolotl/tree/main/examples
- Discord: https://discord.gg/axolotl
