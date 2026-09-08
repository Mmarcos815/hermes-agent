# ═══════════════════════════════════════════════════════════════════════════════════
# BIONIC DAUGHTER — GRPO TRAINING (Google Colab)
# Free T4 GPU • 2-4 hours • No token needed
# ═══════════════════════════════════════════════════════════════════════════════════

# =============================================================================
# CELL 1: Install Dependencies
# =============================================================================
!pip install -q unsloth trl peft datasets accelerate bitsandbytes

# =============================================================================
# CELL 2: Download Base Model (NO TOKEN NEEDED)
# =============================================================================
# Qwen2.5-1.5B is Apache 2.0 — public access
!git lfs install
!git clone https://huggingface.co/Qwen/Qwen2.5-1.5B /content/model

# =============================================================================
# CELL 3: Mount Google Drive & Load Training Data
# =============================================================================
from google.colab import drive
drive.mount('/content/drive')

# Upload grpo_train_ready.jsonl to /content/drive/MyDrive/ first!
import shutil
shutil.copy('/content/drive/MyDrive/grpo_train_ready.jsonl', '/content/data.jsonl')

# =============================================================================
# CELL 4: Load Dataset
# =============================================================================
from datasets import Dataset
import json

data = []
with open('/content/data.jsonl') as f:
    for line in f:
        data.append(json.loads(line.strip()))

dataset = Dataset.from_list(data)
split = dataset.train_test_split(test_size=0.1, seed=42)
train_dataset = split["train"]
eval_dataset = split["test"]
print(f"Train: {len(train_dataset)}, Eval: {len(eval_dataset)}")

# =============================================================================
# CELL 5: Load Model with LoRA (4-bit for T4)
# =============================================================================
from unsloth import FastLanguageModel
import torch

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="/content/model",
    max_seq_length=1024,
    load_in_4bit=True,
    dtype=torch.bfloat16,
)

model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    use_gradient_checkpointing="unsloth",
)

# =============================================================================
# CELL 6: Define Reward Functions
# =============================================================================
def format_reward(completions, **kwargs):
    rewards = []
    for c in completions:
        score = 0.0
        if "<reasoning>" in c: score += 0.5
        if "</reasoning>" in c: score += 0.5
        if "<solution>" in c: score += 0.5
        if "</solution>" in c: score += 0.5
        rewards.append(score)
    return rewards

def accuracy_reward(completions, **kwargs):
    rewards = []
    for c in completions:
        score = 0.0
        keywords = ["vulnerability", "exploit", "attack", "security", "risk", "impact", "CVE"]
        for kw in keywords:
            if kw.lower() in c.lower(): score += 0.2
        rewards.append(min(score, 3.0))
    return rewards

# =============================================================================
# CELL 7: Configure GRPO Training
# =============================================================================
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
    max_prompt_length=256,
    max_completion_length=256,
    report_to="none",
)

# =============================================================================
# CELL 8: TRAIN!
# =============================================================================
from trl import GRPOTrainer

trainer = GRPOTrainer(
    model=model,
    processing_class=tokenizer,
    reward_funcs=[format_reward, accuracy_reward],
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
)

trainer.train()

# =============================================================================
# CELL 9: Save Trained Model to Drive
# =============================================================================
model.save_pretrained("/content/drive/MyDrive/bionic-daughter-grpo")
tokenizer.save_pretrained("/content/drive/MyDrive/bionic-daughter-grpo")
print("TRAINING COMPLETE! Model saved to Google Drive.")
