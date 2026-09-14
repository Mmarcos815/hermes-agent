---
name: unsloth
description: 2-5x faster LoRA/QLoRA fine-tuning for LLMs with reduced VRAM.
version: 1.1.0
author: Orchestra Research
license: MIT
dependencies: [unsloth, torch, transformers, trl, datasets, peft]
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Fine-Tuning, Unsloth, Fast Training, LoRA, QLoRA, Memory-Efficient, Optimization, Llama, Mistral, Gemma, Qwen, GRPO, RLHF]

---

# Unsloth — Fast LLM Fine-Tuning

Unsloth speeds up LoRA/QLoRA fine-tuning 2-5x while cutting VRAM usage by ~70%. It works by optimizing the forward/backward pass with custom CUDA kernels and efficient gradient accumulation. Supports Llama, Mistral, Gemma, Qwen, DeepSeek, Phi, and 20+ other architectures.

## When to Use Unsloth

**Use Unsloth when:**
- Fine-tuning on a single GPU with limited VRAM (even 8GB works for 7B QLoRA)
- You want faster training iterations (hours → minutes for small datasets)
- Training Llama 3/4, Mistral, Gemma, Qwen, Phi, DeepSeek, or IBM Granite
- Need GRPO/RLHF on consumer hardware
- Running on Colab, Kaggle, or local workstation

**Use alternatives when:**
- **Axolotl**: You want YAML-based config and broad framework support
- **TRL**: You want native HuggingFace trainer integration
- **torchtitan**: You're pretraining from scratch at scale
- **Full fine-tuning**: You have enough VRAM for non-LoRA training

## Installation

```bash
pip install unsloth

# With extra deps for specific providers
pip install "unsloth[colab]"       # Google Colab
pip install "unsloth[local]""      # Local install
```

### Verify

```python
import unsloth
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Llama-3.1-8B-Instruct",
    max_seq_length=2048,
    load_in_4bit=True,  # QLoRA — dramatically reduces VRAM
)
```

## Quick start: LoRA fine-tuning

### 1. Prepare data

```python
from datasets import Dataset

data = [
    {"instruction": "Explain quantum computing", "response": "Quantum computing uses qubits..."},
    {"instruction": "What is Python?", "response": "Python is a programming language..."},
]
dataset = Dataset.from_list(data)
```

### 2. Tokenize

```python
def tokenize(example):
    prompt = f"### Instruction:\n{example['instruction']}\n\n### Response:\n{example['response']}"
    return tokenizer(prompt, truncation=True, max_length=2048)

tokenized = dataset.map(tokenize)
```

### 3. Train with SFTTrainer (TRL integration)

```python
from unsloth import FastLanguageModel
from trl import SFTTrainer, SFTConfig
from datasets import Dataset

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Llama-3.1-8B-Instruct",
    max_seq_length=2048,
    load_in_4bit=True,
    dtype=torch.bfloat16,
)

model = FastLanguageModel.get_peft_model(
    model,
    r=16,                    # LoRA rank
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",  # Unsloth's optimized checkpointing
    random_state=3407,
)

trainer = SFTTrainer(
    model=model,
    train_dataset=tokenized,
    dataset_text_field="text",
    max_seq_length=2048,
    args=SFTConfig(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        num_train_epochs=3,
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=10,
        output_dir="outputs",
        optim="adamw_8bit",  # 8-bit optimizer — saves memory
        lr_scheduler_type="linear",
    ),
)

trainer.train()
```

### 4. Save and use

```python
# Save full model (merged with LoRA weights)
FastLanguageModel.save_model(model, "outputs")

# Or save just LoRA weights
model.save_pretrained("lora-weights")

# Load and use
from unsloth import FastLanguageModel
model, tokenizer = FastLanguageModel.from_pretrained(
    "outputs", max_seq_length=2048, load_in_4bit=True
)
FastLanguageModel.for_inference(model)  # enable fast inference

inputs = tokenizer("### Instruction:\nExplain quantum computing\n\n### Response:\n", return_tensors="pt").to("cuda")
outputs = model.generate(**inputs, max_new_tokens=256, temperature=0.7)
print(tokenizer.decode(outputs[0]))
```

## GRPO / RL fine-tuning

Unsloth supports GRPO training for building reasoning models:

```python
from unsloth import FastLanguageModel
from unsloth.trainer import UnslothGRPO

model, tokenizer = FastLanguageModel.from_pretrained(
    "unsloth/Llama-3.1-8B-Instruct",
    max_seq_length=2048,
    load_in_4bit=True,
)

grpo_trainer = UnslothGRPO(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    reward_funcs=[my_reward_function],
    args=GRPOConfig(
        learning_rate=1e-5,
        per_device_train_batch_size=4,
        num_generations=4,
        max_new_tokens=256,
    ),
)

grpo_trainer.train()
```

## Key features

### Dynamic quantization (Unsloth GGUFs)

Unsloth's Dynamic GGUFs recover accuracy lost in standard quantization:

```python
# Download a Dynamic GGUF
from huggingface_hub import snapshot_download
snapshot_download("unsloth/Llama-3.1-8B-Instruct-Dynamic-GGUF",
                 allow_patterns=["*Q4_K_M*"])
```

### Model support

Unsloth supports fine-tuning for: Llama 3/3.1/3.2/4, Mistral, Mixtral, Gemma 2/3, Qwen 2/2.5/3, Phi-3/4, DeepSeek-V2/V3/R1, IBM Granite, GLM-4.5/4.6, Magistral, Kimi K2, Devstral, QwQ, and 20+ more.

### Memory optimization

| Technique | VRAM savings | Notes |
|-----------|-------------|-------|
| QLoRA (4-bit) | ~70% vs full | Load model in 4-bit, train LoRA params in FP16 |
| 8-bit optimizers | ~50% optimizer state | `optim="adamw_8bit"` |
| Gradient checkpointing | ~60% activations | Unsloth's custom implementation |
| Flash Attention | ~30% attention memory | Auto-enabled where supported |

## Common issues

### OOM during training

```python
# Reduce: batch size, seq length, LoRA rank
model = FastLanguageModel.get_peft_model(
    model,
    r=8,                      # Reduce from 16
    max_seq_length=1024,      # Reduce from 2048
)
# Increase gradient accumulation to compensate
# Use 8-bit optimizer
```

### Slow training (not 2-5x faster)

- Ensure `load_in_4bit=True` (QLoRA)
- Use `use_gradient_checkpointing="unsloth"` (not "true")
- Verify CUDA version ≥ 12.1
- Check that Unsloth kernels are loaded: `unsloth.__version__`

### Colab-specific issues

```python
# Enable HF transfer for faster downloads
import os
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
```

### Model not in support list

Unsloth supports most Llama-derived architectures. For unsupported models, you can still use standard PEFT + transformers but won't get the speed boost.

## Resources

- Docs: https://docs.unsloth.ai/
- GitHub: https://github.com/unslothai/unsloth
- Colab notebooks: https://docs.unsloth.ai/get-started/unsloth-notebooks
- Model zoo: https://docs.unsloth.ai/get-started/all-our-models
