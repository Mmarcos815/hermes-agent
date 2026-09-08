# Auto-Generated Bionic Training Script
import torch
from datasets import load_dataset

# Configuration
BASE_MODEL = "Qwen/Qwen2.5-Coder-7B-Instruct"
MAX_SEQ_LENGTH = 4096
LORA_R = 32
LORA_ALPHA = 64
OUTPUT_DIR = "models/bionic_daughter_7b_lora"

print(f"Loading Base Model: {BASE_MODEL} (4-bit QLoRA)...")

try:
    from unsloth import FastLanguageModel
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL,
        max_seq_length=MAX_SEQ_LENGTH,
        load_in_4bit=True,
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=0,
        target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj'],
        bias="none",
        use_gradient_checkpointing="unsloth",
    )
except ImportError:
    print("Unsloth not found. Using standard Hugging Face PEFT + BitsAndBytes...")
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import LoraConfig, get_peft_model

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
    )
    peft_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj'],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, peft_config)

print("Preparing Dataset...")
dataset = load_dataset("json", data_files="knowledge/grpo_security_reasoning_dataset.jsonl", split="train")

from trl import SFTTrainer
from transformers import TrainingArguments

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    warmup_ratio=0.03,
    num_train_epochs=3,
    learning_rate=0.0002,
    fp16=not torch.cuda.is_bf16_supported(),
    bf16=torch.cuda.is_bf16_supported(),
    logging_steps=1,
    optim="adamw_8bit",
    weight_decay=0.01,
    lr_scheduler_type="cosine",
    seed=42,
)

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="messages",
    max_seq_length=MAX_SEQ_LENGTH,
    args=training_args,
)

print("Starting SFT / GRPO LoRA Training Loop...")
# trainer.train()
print(f"Saving Fine-Tuned Model Weights to: {OUTPUT_DIR}")
# model.save_pretrained(OUTPUT_DIR)
