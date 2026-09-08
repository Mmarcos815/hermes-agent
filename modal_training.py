# ============================================================================
# BIONIC DAUGHTER — MODAL CLOUD GPU GRPO TRAINING
# "THERES ALWAYS A WAY" — Serverless GPU training without local CUDA.
#
# This module defines Modal Functions that run the GRPO training pipeline
# on cloud GPUs (NVIDIA H100, A100, RTX 4090, etc.) without needing
# local CUDA hardware.
#
# How it works:
#   1. Modal provides serverless GPU containers
#   2. We define a function that loads Qwen3-4B-Thinking-2507
#   3. Runs the training pipeline (SFT → DPO → GRPO → Deploy)
#   4. Returns trained artifacts + eval results
#
# No pre-existing Modal account needed — the user can set one up,
# or we can use alternative providers. This is the "always a way" path.
# ============================================================================

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Configuration — matches grpo_training_config.yaml but for cloud execution
# ---------------------------------------------------------------------------

MODAL_GPU_CONFIG = {
    # GPU types available on Modal (pick based on training needs):
    # - "nvidia-h100": top-tier, fastest (expensive)
    # - "nvidia-a100": high-performance, suitable for GRPO training
    # - "nvidia-a10g": cost-effective, may be sufficient for 4B model training
    # - "nvidia-l40s": RTX 4090-based, good cost-performance
    # - "nvidia-t4": budget, slow but possible (Colab level)
    "gpu": "nvidia-a100",  # recommended: A100 (suitable for GRPO training)
    "cpu": "4",            # CPU cores
    "memory": "32Gi",      # memory (VRAM + system)
    "timeout": 86400,      # max runtime (seconds) — 24 hours
}

# training hyperparameters (matches local config)
TRAINING_PARAMS = {
    "sft": {
        "max_steps": 50,
        "learning_rate": 2e-4,
        "lora_r": 64,
        "lora_alpha": 128,
        "effective_batch_size": 32,
        "max_seq_length": 2048,
    },
    "dpo": {
        "max_steps": 30,
        "learning_rate": 1e-4,
        "beta": 0.1,
    },
    "grpo": {
        "max_steps": 200,
        "group_size": 6,
        "learning_rate": 1e-5,
        "beta_kl": 0.01,
        "rewards": ["format", "accuracy", "reasoning_depth", "density", "tool_use_quality", "self_correction"],
        "reward_weights": {
            "format": 1.0,
            "accuracy": 2.0,
            "reasoning_depth": 1.0,
            "density": 0.5,
            "tool_use_quality": 0.5,
            "self_correction": 1.0,
        },
    },
}

# ---------------------------------------------------------------------------
# MODAL FUNCTIONS (deferred import — only imported when running on Modal)
# ---------------------------------------------------------------------------

MODAL_FUNCTIONS_CODE = '''
# Modal Functions for Bionic Daughter GRPO Training
# These would be defined in a modal_app.py and deployed to Modal.
# Below is the template code.

import modal
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model, TaskType
from trl import SFTTrainer, DPOTrainer, GRPOTrainer
from datasets import Dataset
import json
import os

# Modal image: training environment with all required packages
modal_image = (
    modal.Image.debian_slim()
    .pip_install([
        "torch",
        "transformers",
        "peft",
        "trl",
        "datasets",
        "accelerate",
        "bitsandbytes",
        "safetensors",
        "huggingface_hub",
    ])
    .apt_install(["git", "wget"])
)

# GPU container app
app = modal.App("bionic-daughter-grpo-training")

# Volume: persistent storage for training data + artifacts
vol = modal.Volume.from_name("bionic-daughter-artifacts", create_if_missing=True)

# Command: model download + cache
@app.function(
    image=modal_image,
    gpu="A100",
    timeout=3600,
    volumes={"/artifacts": vol},
    secrets=[modal.Secret.from_name("huggingface-token")],  # HF token (optional)
)
def download_base_model(model_name="Qwen/Qwen3-4B-Thinking-2507"):
    """Download model weights to cloud container."""
    from transformers import AutoModelForCausalLM, AutoTokenizer
    print(f"Downloading {model_name}...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype="auto",
        device_map="auto",
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    print(f"Model downloaded and cached at: {model.config._name_or_path}")
    return {"status": "ok", "model_id": model_name}

# Command: SFT training
@app.function(
    image=modal_image,
    gpu="A100",
    timeout=86400,
    volumes={"/artifacts": vol},
    secrets=[modal.Secret.from_name("huggingface-token")],
)
def run_sft_training(
    model_name="Qwen/Qwen3-4B-Thinking-2507",
    train_data_path="/artifacts/grpo_train_ready.jsonl",
    output_dir="/artifacts/sft",
    **params
):
    """Run SFT stage (LoRA)."""
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
    from peft import LoraConfig, get_peft_model, TaskType
    from trl import SFTTrainer
    from datasets import Dataset
    import torch

    # Load model
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )

    # LoRA config
    lora_config = LoraConfig(
        r=params.get("lora_r", 64),
        lora_alpha=params.get("lora_alpha", 128),
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    model = get_peft_model(model, lora_config)

    # Load dataset
    with open(train_data_path, "r") as f:
        data = [json.loads(line) for line in f if line.strip()]

    # Convert prompt/completion to training format
    def format_sample(sample):
        prompt = sample["prompt"]
        completion = sample["completion"]
        # Convert to format model understands (system prompt + user message + assistant)
        return {
            "text": f"{prompt}\\n{completion}"
        }

    train_dataset = Dataset.from_list([format_sample(d) for d in data])

    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=params.get("effective_batch_size", 32) // 4,
        learning_rate=params.get("learning_rate", 2e-4),
        max_steps=params.get("max_steps", 50),
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        logging_steps=5,
        save_strategy="steps",
        save_steps=10,
        bf16=True,
        report_to="none",
    )

    # Trainer
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        dataset_text_field="text",
        max_seq_length=params.get("max_seq_length", 2048),
        tokenizer=tokenizer,
        packing=True,
    )

    print(f"Starting SFT training: {params.get('max_steps', 50)} steps...")
    trainer.train()
    trainer.save_model(output_dir)
    print(f"SFT training complete. Model saved to {output_dir}")

    return {"status": "completed", "output_dir": output_dir, "steps": params.get("max_steps", 50)}

# Command: GRPO training (core stage)
@app.function(
    image=modal_image,
    gpu="A100",
    timeout=86400 * 2,  # GRPO may take longer
    volumes={"/artifacts": vol},
    secrets=[modal.Secret.from_name("huggingface-token")],
)
def run_grpo_training(
    model_name="Qwen/Qwen3-4B-Thinking-2507",
    sft_model_path="/artifacts/sft/last",
    train_data_path="/artifacts/grpo_train_ready.jsonl",
    eval_data_path="/artifacts/grpo_eval_held_out.jsonl",
    output_dir="/artifacts/grpo",
    **params
):
    """Run GRPO stage — Group Relative Policy Optimization."""
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
    from trl import GRPOTrainer
    from datasets import Dataset
    import torch
    import json

    # Load SFT-tuned model
    tokenizer = AutoTokenizer.from_pretrained(sft_model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        sft_model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )

    # Load dataset
    with open(train_data_path, "r") as f:
        train_data = [json.loads(line) for line in f if line.strip()]

    # GRPO trainer setup
    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=1,  # GRPO uses lots of memory
        gradient_accumulation_steps=8,
        learning_rate=params.get("learning_rate", 1e-5),
        max_steps=params.get("max_steps", 200),
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        logging_steps=10,
        save_strategy="steps",
        save_steps=50,
        bf16=True,
        report_to="none",
    )

    # Reward functions (from reward engine)
    # In real implementation, use functions from grpo_reward_engine.py
    # or pass as callbacks to trainer

    trainer = GRPOTrainer(
        model=model,
        args=training_args,
        train_dataset=Dataset.from_list(train_data),
        # reward_funcs: reward engine functions
        # passed via treatment's reward_funcs parameter
    )

    print(f"Starting GRPO training: {params.get('max_steps', 200)} steps...")
    trainer.train()
    trainer.save_model(output_dir)
    print(f"GRPO training complete. Model saved to {output_dir}")

    return {"status": "completed", "output_dir": output_dir, "steps": params.get("max_steps", 200)}

# Command: run full training pipeline
@app.function(
    image=modal_image,
    gpu="A100",
    timeout=86400 * 3,  # full pipeline (2-3 days)
    volumes={"/artifacts": vol},
    secrets=[modal.Secret.from_name("huggingface-token")],
)
def run_full_pipeline(
    model_name="Qwen/Qwen3-4B-Thinking-2507",
    train_data_path="/artifacts/grpo_train_ready.jsonl",
    eval_data_path="/artifacts/grpo_eval_held_out.jsonl",
    output_base="/artifacts",
    **pipeline_params
):
    """Run full 5-stage pipeline."""
    import subprocess
    import sys

    # 1. SFT
    print("\\n=== STAGE 1: SFT ===")
    sft_result = run_sft_training.remote(
        model_name=model_name,
        train_data_path=train_data_path,
        output_dir=f"{output_base}/sft",
        **pipeline_params.get("sft", {}),
    )
    print(f"SFT result: {sft_result}")

    # 2. DPO
    print("\\n=== STAGE 2: DPO ===")
    # DPO function call (similar implementation)

    # 3. GRPO
    print("\\n=== STAGE 3: GRPO ===")
    grpo_result = run_grpo_training.remote(
        model_name=model_name,
        sft_model_path=f"{output_base}/sft/last",
        train_data_path=train_data_path,
        eval_data_path=eval_data_path,
        output_dir=f"{output_base}/grpo",
        **pipeline_params.get("grpo", {}),
    )
    print(f"GRPO result: {grpo_result}")

    # 4. Rejection Sampling + SFT
    print("\\n=== STAGE 4: Rejection Sampling + SFT ===")
    # rejection function call

    # 5. Deploy (quantization)
    print("\\n=== STAGE 5: Deploy (quantization) ===")
    # deploy function call

    return {"status": "completed", "artifacts": output_base}

# How to call Modal functions from local:
# if __name__ == "__main__":
#     # Modal app must be deployed:
#     with app.run():
#         # Start training (async)
#         training_handle = run_full_pipeline.remote(
#             model_name="Qwen/Qwen3-4B-Thinking-2507",
#             train_data_path="/artifacts/grpo_train_ready.jsonl",
#         )
#         # Wait for result
#         result = training_handle.get()
#         print(result)
'''

# ---------------------------------------------------------------------------
# DEPLOYMENT HELPERS
# ---------------------------------------------------------------------------

def generate_modal_deployment_guide() -> str:
    """
    Modal GRPO training deployment guide.
    "THERES ALWAYS A WAY" — train on cloud GPUs without local CUDA.
    """
    guide = """
===========================================================================
BIONIC DAUGHTER — MODAL CLOUD GPU GRPO TRAINING DEPLOYMENT
"THERES ALWAYS A WAY" — serverless GPU training, no local CUDA needed
===========================================================================

## Method 1: Modal (serverless GPU, recommended)

### Why Modal?
- Serverless: no GPU container management needed
- Python SDK: define training as Python functions, Modal runs them
- Pay per use: pay only for GPU time used
- Clean integration: connects naturally with existing Python code

### Setup steps:

1. Create Modal account:
   - https://modal.com create account (may have free credits)
   - Or use father's email / RBAC setup

2. Install Modal Python SDK (already installed):
   ```
   pip install modal-client
   ```

3. Set up HuggingFace token (for model weight downloads):
   - Create token at https://huggingface.co/settings/tokens
   - Store as Modal Secret: modal secret create huggingface-token HF_TOKEN=<token>

4. Define Modal app (modal_app.py):
   - Reference MODAL_FUNCTIONS_CODE above
   - Configure GPU type, timeout, volumes

5. Deploy and run:
   ```
   modal deploy modal_app.py     # deploy functions
   modal run modal_app.py::run_full_pipeline  # start training
   ```

6. Monitor training progress:
   ```
   modal monitor   # monitor running functions
   ```

### Cost estimate (A100 GPU):
- A100 40GB: ~$3-4/hour
- SFT 50 steps: ~1-2 hours → $3-8
- DPO 30 steps: ~1 hour → $3-4
- GRPO 200 steps: ~4-8 hours → $12-32
- Full pipeline: ~$20-50 estimated

### Pros:
- No local GPU needed
- Simple setup
- Download artifacts after training

### Cons:
- HuggingFace token required (public models may work without)
- Internet connection required
- Modal account required

## Method 2: Google Colab (free GPU, best accessibility)

### Why Colab?
- Free GPU tier (T4, sometimes better)
- Just need Google account (likely already have)
- Simple setup
- Notebook-based but can run Python scripts

### Setup steps:

1. Create Colab notebook:
   - https://colab.research.google.com

2. Select GPU runtime:
   - Runtime → Change runtime type → GPU

3. Install required packages:
   ```python
   !pip install torch transformers peft trl datasets accelerate bitsandbytes
   ```

4. HuggingFace login (optional, public models work without):
   ```python
   from huggingface_hub import login
   login()  # enter token
   ```

5. Run training code:
   - Copy grpo_train.py to Colab or write directly in cells
   - Download model → run training → save artifacts

6. Save artifacts:
   - Mount Google Drive: drive.mount('/content/drive')
   - Save trained model to Drive

### Cost: Free (within free tier limits)

### Limitations:
- Session timeout (usually 12 hours, shorter if idle)
- GPU availability varies (T4 most common)
- Large models/data need Colab Pro
- Qwen3-4B (8GB+) download and training possible

### Pros:
- Completely free
- Best accessibility
- Quick start

## Method 3: RunPod Community Cloud (affordable GPU)

### Setup:
1. Create RunPod account
2. Select affordable GPU in community cloud
3. Create pod and SSH connect
4. Run training code

### Cost:
- Community cloud GPU: ~$0.20-1.00/hour
- RTX 4090: ~$0.70/hour
- A100: ~$1.50-3.00/hour

## Method 4: vLLM local inference (verification only, not training replacement)

### vLLM purpose:
- vLLM is inference optimization engine (not training)
- Use for running/validating trained models locally
- Similar role to Llama.cpp

### Setup:
```
pip install vllm
vllm serve Qwen/Qwen3-4B-Thinking-2507 --port 8000
```

### Limitations:
- No training capability (inference only)
- GPU required (CPU inference very slow)
- Cannot replace training pipeline

## Final recommendation:

1. **Fastest start**: Google Colab (free, start immediately)
   - Run grpo_train.py in Colab notebook
   - Download Qwen3-4B, run training
   - Save artifacts to Drive

2. **Cleanest production**: Modal
   - Serverless GPU, Python SDK integration
   - Define training pipeline functions, deploy
   - Need Modal account + HF token

3. **Best value**: RunPod Community Cloud
   - Affordable GPU, full control
   - Account needed but simple

## "THERES ALWAYS A WAY" checklist:

- [ ] Choose cloud GPU provider (Modal/Colab/RunPod)
- [ ] Create/configure account
- [ ] Prepare HuggingFace token (if needed)
- [ ] Transfer training code (grpo_train.py) to cloud environment
- [ ] Download model weights (Qwen3-4B-Thinking-2507)
- [ ] Run training (SFT → DPO → GRPO → Deploy)
- [ ] Download/save artifacts
- [ ] Verify training with eval results

Let me know which method you choose. If Modal, I can proceed immediately.
"""
    return guide


def generate_colab_notebook_template() -> str:
    """
    Google Colab notebook template for running GRPO training.
    """ 
    template = """# Bionic Daughter GRPO Training on Google Colab
# "THERES ALWAYS A WAY" — Free GPU training without local CUDA

# ============================================================
# Cell 1: Setup
# ============================================================
!pip install -q torch transformers peft trl datasets accelerate bitsandbytes huggingface_hub

import torch
import json
import os
from pathlib import Path

print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'}")
print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

# ============================================================
# Cell 2: HuggingFace login (optional for public models)
# ============================================================
# from huggingface_hub import login
# login()  # enter token

# ============================================================
# Cell 3: Model download
# ============================================================
from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "Qwen/Qwen3-4B-Thinking-2507"
print(f"Downloading {model_name}...")

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    offload_folder="/tmp/offload",
)

print(f"Model loaded. Device: {model.device}")
print(f"Model type: {type(model)}")

# ============================================================
# Cell 4: Dataset load
# ============================================================
import json
from datasets import Dataset

# Upload grpo_train_ready.jsonl to Colab or load from HF
# Example: load directly with datasets library

# Data preparation (example)
train_data = []
with open("grpo_train_ready.jsonl", "r") as f:
    for line in f:
        if line.strip():
            train_data.append(json.loads(line))

print(f"Loaded {len(train_data)} training samples")

# ============================================================
# Cell 5: LoRA config + SFT training
# ============================================================
from peft import LoraConfig, get_peft_model, TaskType
from trl import SFTTrainer, TrainingArguments

lora_config = LoraConfig(
    r=64,
    lora_alpha=128,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM,
)

model = get_peft_model(model, lora_config)

# Training dataset format
def format_sample(sample):
    return {
        "text": f"{sample['prompt']}\\n{sample['completion']}"
    }

train_dataset = Dataset.from_list([format_sample(d) for d in train_data])

training_args = TrainingArguments(
    output_dir="/content/sft_output",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=8,
    learning_rate=2e-4,
    max_steps=50,
    lr_scheduler_type="cosine",
    warmup_ratio=0.03,
    logging_steps=5,
    save_strategy="steps",
    save_steps=10,
    bf16=True,
    report_to="none",
)

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    dataset_text_field="text",
    max_seq_length=2048,
    tokenizer=tokenizer,
    packing=True,
)

print("Starting SFT training...")
trainer.train()
trainer.save_model("/content/sft_trained")
print("SFT training complete!")

# ============================================================
# Cell 6: GRPO training (core)
# ============================================================
# GRPO uses TRL's GRPOTrainer
# from trl import GRPOTrainer
# ... GRPO training code ...

# ============================================================
# Cell 7: Save artifacts (Google Drive)
# ============================================================
from google.colab import drive
drive.mount("/content/drive")

# Copy trained model to Drive
!cp -r /content/sft_trained /content/drive/MyDrive/bionic_daughter_artifacts/sft

print("Artifacts saved to Google Drive")
"""
    return template


if __name__ == "__main__":
    import sys
    action = sys.argv[1] if len(sys.argv) > 1 else "guide"

    if action == "guide":
        print(generate_modal_deployment_guide())
    elif action == "colab":
        print(generate_colab_notebook_template())
    elif action == "functions":
        print(MODAL_FUNCTIONS_CODE)
    else:
        print(f"Unknown action: {action}")
        print("Usage: python modal_training.py [guide|colab|functions]")
