#!/usr/bin/env python3
"""
BIONIC DAUGHTER — Lean CPU GRPO Training
Fits in 8GB RAM with 2.5GB free.
Uses Qwen2.5-1.5B, 8-bit quantization via bitsandbytes (CPU fallback to bfloat16).
"""
import os
import sys
import json
import time
import shutil
from pathlib import Path

PROJECT_DIR = Path("C:/Users/mobil/orca/projects/my 1st")
DATA_FILE = PROJECT_DIR / "grpo_train_ready.jsonl"
OUTPUT_DIR = PROJECT_DIR / "artifacts/cpu_grpo"
LOG_DIR = PROJECT_DIR / "artifacts/logs"
MODEL_DIR = PROJECT_DIR / "models/Qwen2.5-1.5B"

# Training config — lean for CPU
LORA_R = 8
LORA_ALPHA = 16
BATCH_SIZE = 1
GRADIENT_ACCUMULATION = 2
MAX_SEQ_LENGTH = 256  # Short for memory
LEARNING_RATE = 1e-5
NUM_EPOCHS = 1
MAX_STEPS = 50  # Start small, can increase
WARMUP_RATIO = 0.03

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def check_ram():
    import psutil
    ram = psutil.virtual_memory()
    log(f"RAM: {ram.available/1e9:.1f}GB free / {ram.total/1e9:.1f}GB total")
    return ram.available

def main():
    log("=" * 60)
    log("BIONIC DAUGHTER — LEAN CPU GRPO TRAINING")
    log("=" * 60)

    # Check RAM
    avail = check_ram()
    if avail < 1.5e9:
        log("WARNING: Less than 1.5GB RAM free. Training may be slow.")
        log("Consider closing other applications.")

    # Check data
    if not DATA_FILE.exists():
        log(f"ERROR: Data file not found: {DATA_FILE}")
        sys.exit(1)

    with open(DATA_FILE) as f:
        data = [json.loads(line) for line in f if line.strip()]
    log(f"Loaded {len(data)} training examples")

    # Check model
    if not MODEL_DIR.exists():
        log(f"ERROR: Model not found: {MODEL_DIR}")
        sys.exit(1)
    log(f"Model: {MODEL_DIR}")

    # Create dirs
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Load packages
    log("Loading packages (this may take 30-60s)...")
    import torch
    log(f"torch: {torch.__version__}, cuda: {torch.cuda.is_available()}")

    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import LoraConfig, get_peft_model, TaskType
    from trl import GRPOConfig, GRPOTrainer

    # Try to load model with 8-bit quantization
    log("Loading model (attempting 8-bit quantization)...")
    model_loaded = False

    # Attempt 1: 8-bit via bitsandbytes
    try:
        from transformers import BitsAndBytesConfig
        bnb_config = BitsAndBytesConfig(
            load_in_8bit=True,
            llm_int8_threshold=6.0,
        )
        model = AutoModelForCausalLM.from_pretrained(
            str(MODEL_DIR),
            quantization_config=bnb_config,
            device_map="cpu",
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True,
            trust_remote_code=True,
        )
        log("Model loaded with 8-bit quantization")
        model_loaded = True
    except Exception as e:
        log(f"8-bit failed: {e}")
        log("Falling back to bfloat16...")

    # Attempt 2: bfloat16 (no quantization)
    if not model_loaded:
        try:
            model = AutoModelForCausalLM.from_pretrained(
                str(MODEL_DIR),
                device_map="cpu",
                torch_dtype=torch.bfloat16,
                low_cpu_mem_usage=True,
                trust_remote_code=True,
            )
            log("Model loaded with bfloat16")
            model_loaded = True
        except Exception as e:
            log(f"bfloat16 failed: {e}")
            log("Falling back to float32...")

    # Attempt 3: float32 (last resort)
    if not model_loaded:
        model = AutoModelForCausalLM.from_pretrained(
            str(MODEL_DIR),
            device_map="cpu",
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True,
            trust_remote_code=True,
        )
        log("Model loaded with float32")

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        str(MODEL_DIR),
        trust_remote_code=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Apply LoRA
    log(f"Applying LoRA (r={LORA_R}, alpha={LORA_ALPHA})...")
    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Load reward engine
    sys.path.insert(0, str(PROJECT_DIR))
    from grpo_reward_engine import (
        reward_format, reward_accuracy, reward_reasoning_depth,
        reward_creativity, reward_attack_chain, reward_bypass_creativity,
        reward_tool_use_quality, reward_self_correction,
        DEFAULT_REWARD_WEIGHTS,
    )

    def reward_format_wrapper(completions, **kwargs):
        return [reward_format(c, DEFAULT_REWARD_WEIGHTS) for c in completions]

    def reward_accuracy_wrapper(completions, **kwargs):
        prompts = kwargs.get('prompts', [''] * len(completions))
        return [reward_accuracy(c, p, DEFAULT_REWARD_WEIGHTS) for c, p in zip(completions, prompts)]

    def reward_reasoning_wrapper(completions, **kwargs):
        return [reward_reasoning_depth(c, DEFAULT_REWARD_WEIGHTS) for c in completions]

    def reward_creativity_wrapper(completions, **kwargs):
        return [reward_creativity(c, '', DEFAULT_REWARD_WEIGHTS) for c in completions]

    def reward_attack_chain_wrapper(completions, **kwargs):
        return [reward_attack_chain(c, '', DEFAULT_REWARD_WEIGHTS) for c in completions]

    def reward_bypass_wrapper(completions, **kwargs):
        return [reward_bypass_creativity(c, '', DEFAULT_REWARD_WEIGHTS) for c in completions]

    def reward_tools_wrapper(completions, **kwargs):
        prompts = kwargs.get('prompts', [''] * len(completions))
        return [reward_tool_use_quality(c, p, DEFAULT_REWARD_WEIGHTS) for c, p in zip(completions, prompts)]

    def reward_self_corr_wrapper(completions, **kwargs):
        return [reward_self_correction(c, DEFAULT_REWARD_WEIGHTS) for c in completions]

    # Load dataset as datasets.Dataset (required by TRL 0.24)
    from datasets import Dataset
    data_dicts = []
    for item in data:
        data_dicts.append({
            "prompt": item["prompt"],
            "completion": item.get("completion", ""),
        })
    dataset = Dataset.from_list(data_dicts)
    log(f"Dataset: {len(dataset)} examples")

    # Training args
    training_args = GRPOConfig(
        output_dir=str(OUTPUT_DIR),
        num_train_epochs=NUM_EPOCHS,
        max_steps=MAX_STEPS,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        learning_rate=LEARNING_RATE,
        lr_scheduler_type="cosine",
        logging_steps=5,
        save_steps=25,
        save_total_limit=2,
        beta=0.01,
        max_completion_length=128,
        report_to="none",
        dataloader_num_workers=0,
        seed=42,
        use_cpu=True,
        num_generations=2,
        generation_batch_size=2,
    )

    # Trainer
    trainer = GRPOTrainer(
        model=model,
        processing_class=tokenizer,
        reward_funcs=[
            reward_format_wrapper,
            reward_accuracy_wrapper,
            reward_reasoning_wrapper,
            reward_creativity_wrapper,
            reward_attack_chain_wrapper,
            reward_bypass_wrapper,
            reward_tools_wrapper,
            reward_self_corr_wrapper,
        ],
        args=training_args,
        train_dataset=dataset,
    )

    # Train
    log("=" * 60)
    log("STARTING TRAINING")
    log("=" * 60)
    start_time = time.time()

    trainer.train()

    elapsed = time.time() - start_time
    log(f"Training complete! Time: {elapsed/60:.1f} minutes")

    # Save
    log("Saving model...")
    trainer.save_model(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))

    info = {
        "base_model": "Qwen2.5-1.5B",
        "lora_r": LORA_R,
        "lora_alpha": LORA_ALPHA,
        "batch_size": BATCH_SIZE,
        "gradient_accumulation": GRADIENT_ACCUMULATION,
        "learning_rate": LEARNING_RATE,
        "num_epochs": NUM_EPOCHS,
        "max_steps": MAX_STEPS,
        "max_seq_length": MAX_SEQ_LENGTH,
        "training_time_minutes": elapsed / 60,
        "device": "CPU",
        "quantization": "8-bit or bfloat16",
        "dataset_size": len(data),
    }
    with open(OUTPUT_DIR / "training_info.json", "w") as f:
        json.dump(info, f, indent=2)

    log(f"Model saved to: {OUTPUT_DIR}")
    log("=" * 60)
    log("DONE!")
    log("=" * 60)

if __name__ == "__main__":
    main()
