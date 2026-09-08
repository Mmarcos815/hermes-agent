#!/usr/bin/env python3
# GOOGLE COLAB GRPO TRAINING NOTEBOOK
# Ready to copy-paste into https://colab.research.google.com

# ===== CELL 1: Install Dependencies =====
!pip install unsloth trl peft datasets accelerate bitsandbytes huggingface_hub

# ===== CELL 2: Download Model (NO HF TOKEN NEEDED) =====
# Qwen3-4B-Thinking is Apache 2.0 — public access

import os
os.system("git lfs install")
os.system("git clone https://huggingface.co/Qwen/Qwen3-4B-Thinking-2507 /content/model")

# ===== CELL 3: Load Training Data =====
from google.colab import drive
drive.mount('/content/drive')

# Copy your grpo_train_ready.jsonl to Google Drive first!
import shutil
shutil.copy('/content/drive/MyDrive/grpo_train_ready.jsonl', '/content/data.jsonl')

# ===== CELL 4: Prepare Dataset =====
from datasets import Dataset
import json

data = []
with open('/content/data.jsonl') as f:
    for line in f:
        data.append(json.loads(line))

dataset = Dataset.from_list(data)
print(f"Loaded {len(dataset)} training examples")

# ===== CELL 5: Load Model with Unsloth =====
from unsloth import FastLanguageModel
import torch

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="/content/model",
    max_seq_length=2048,
    load_in_4bit=True,  # 4-bit quantization for T4 GPU
    dtype=torch.bfloat16,
)

# ===== CELL 6: Apply LoRA =====
model = FastLanguageModel.get_peft_model(
    model,
    r=64,
    lora_alpha=128,
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    lora_dropout=0.05,
    bias="none",
    use_gradient_checkpointing="unsloth",
)

# ===== CELL 7: GRPO Training Config =====
from trl import GRPOConfig

training_args = GRPOConfig(
    output_dir="/content/output",
    num_train_epochs=3,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    learning_rate=1e-5,
    warmup_ratio=0.03,
    lr_scheduler_type="cosine",
    logging_steps=10,
    save_steps=50,
    save_total_limit=3,
    bf16=True,
    beta=0.01,
    max_prompt_length=512,
    max_completion_length=512,
    report_to="none",
)

# ===== CELL 8: Load Reward Functions =====
def format_reward(completions, **kwargs):
    """Reward proper XML format"""
    rewards = []
    for completion in completions:
        if "<reasoning>" in completion and "</reasoning>" in completion:
            rewards.append(1.0)
        else:
            rewards.append(0.0)
    return rewards

def accuracy_reward(completions, **kwargs):
    """Reward correct answers (simplified)"""
    rewards = []
    for completion in completions:
        if "<solution>" in completion and "</solution>" in completion:
            rewards.append(2.0)
        else:
            rewards.append(0.0)
    return rewards

# ===== CELL 9: Train =====
from trl import GRPOTrainer

trainer = GRPOTrainer(
    model=model,
    processing_class=tokenizer,
    reward_funcs=[format_reward, accuracy_reward],
    args=training_args,
    train_dataset=dataset,
)

trainer.train()

# ===== CELL 10: Save to Drive =====
model.save_pretrained("/content/drive/MyDrive/bionic-daughter-grpo")
tokenizer.save_pretrained("/content/drive/MyDrive/bionic-daughter-grpo")
print("Training complete! Model saved to Google Drive.")
