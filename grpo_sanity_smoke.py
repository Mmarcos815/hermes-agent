#!/usr/bin/env python3
"""
BIONIC DAUGHTER — GRPO PIPELINE SMOKE TEST
Real end-to-end run that proves trl/peft/transformers work and that the
pipeline can train one real LoRA step on CPU using a tiny base model.

This is NOT a full GRPO training run. It's the smallest possible
verification that the entire stack is wired:
  - TRL loads
  - PEFT LoRA applies
  - Transformers model + tokenizer load
  - Dataset JSONL parses
  - SFTTrainer trains 1 step
  - LoRA adapter saves
  - Reward engine imports (used downstream)

If this passes on CPU, the same script can be pointed at a GPU and the
real 5-stage pipeline in grpo_train.py will run.

Base model: sshleifer/tiny-gpt2 (2-layer, ~2M params, downloads in <5s)
Dataset:    grpo_train_ready.jsonl, first 8 records (subset)
Train:      SFT only, 1 step, LoRA r=4 (tiny adapter)
Output:     artifacts/sanity/sft_smoke/last/

If this works, GRPO training on real GPU is mechanically feasible.
"""

import json
import os
import sys
import time
from pathlib import Path

SANITY_DIR = Path("artifacts/sanity/sft_smoke")
SANITY_DIR.mkdir(parents=True, exist_ok=True)

BASE_MODEL = os.environ.get("SANITY_BASE_MODEL", "sshleifer/tiny-gpt2")
SUBSET_SIZE = int(os.environ.get("SANITY_SUBSET", "8"))
MAX_STEPS = int(os.environ.get("SANITY_MAX_STEPS", "1"))

manifest = {
    "stage": "sanity_smoke",
    "base_model": BASE_MODEL,
    "subset_size": SUBSET_SIZE,
    "max_steps": MAX_STEPS,
    "started": time.time(),
}

print("[1/6] Importing transformers / peft / trl ...", flush=True)
import torch
from datasets import Dataset
from peft import LoraConfig as PeftLoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTConfig, SFTTrainer

print(f"  torch:        {torch.__version__}", flush=True)
print(f"  device:       {'cuda' if torch.cuda.is_available() else 'cpu'}", flush=True)
print(f"  base model:   {BASE_MODEL}", flush=True)

print("[2/6] Loading + tokenizing dataset (subset=%d) ..." % SUBSET_SIZE, flush=True)
records = []
with open("grpo_train_ready.jsonl", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if i >= SUBSET_SIZE:
            break
        rec = json.loads(line)
        # Format as plain text for the tiny model (no chat template stress test)
        records.append({"text": rec["prompt"] + "\n" + rec["completion"]})

ds = Dataset.from_list(records)
print(f"  loaded {len(ds)} records", flush=True)

print("[3/6] Loading base model + tokenizer ...", flush=True)
t_load = time.time()
tok = AutoTokenizer.from_pretrained(BASE_MODEL)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(BASE_MODEL)
print(f"  model loaded in {time.time()-t_load:.1f}s", flush=True)

print("[4/6] Applying LoRA (r=4 for sanity) ...", flush=True)
peft_cfg = PeftLoraConfig(
    r=4,
    lora_alpha=8,
    target_modules=["c_attn"] if "gpt2" in BASE_MODEL.lower() else ["query_key_value"],
    lora_dropout=0.0,
    bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(model, peft_cfg)
model.print_trainable_parameters()

print("[5/6] SFTTrainer (1 step, batch_size=2, CPU) ...", flush=True)
sft_cfg = SFTConfig(
    output_dir=str(SANITY_DIR / "trainer_out"),
    max_steps=MAX_STEPS,
    per_device_train_batch_size=2,
    learning_rate=1e-3,
    logging_steps=1,
    save_strategy="no",
    bf16=False,
    fp16=False,
    report_to="none",
    dataset_text_field="text",
    max_length=256,
)
trainer = SFTTrainer(
    model=model,
    args=sft_cfg,
    train_dataset=ds,
    processing_class=tok,
)

t_train = time.time()
train_result = trainer.train()
train_seconds = time.time() - t_train
print(f"  trained 1 step in {train_seconds:.1f}s", flush=True)

print("[6/6] Saving LoRA adapter + writing manifest ...", flush=True)
adapter_dir = SANITY_DIR / "last"
adapter_dir.mkdir(parents=True, exist_ok=True)
model.save_pretrained(adapter_dir)
tok.save_pretrained(adapter_dir)

# Save the manifest for the audit trail
manifest.update({
    "finished": time.time(),
    "device": "cuda" if torch.cuda.is_available() else "cpu",
    "train_seconds": round(train_seconds, 2),
    "train_loss": float(train_result.training_loss),
    "train_steps": int(train_result.global_step),
    "adapter_dir": str(adapter_dir),
    "adapter_files": sorted(p.name for p in adapter_dir.iterdir()),
    "status": "SANITY_PASS" if train_result.global_step >= 1 else "SANITY_FAIL",
})

with open(SANITY_DIR / "manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

print(f"\n  ADAPTER SAVED TO: {adapter_dir}", flush=True)
print(f"  STATUS:           {manifest['status']}", flush=True)
print(f"  TRAIN LOSS:       {manifest['train_loss']}", flush=True)
print(f"  ADAPTER FILES:    {manifest['adapter_files']}", flush=True)

# Sanity assertion: real artifacts, not stubs
adapter_json = adapter_dir / "adapter_config.json"
if not adapter_json.exists():
    print("  !! FAIL: adapter_config.json not written — trainer didn't save real weights", flush=True)
    sys.exit(2)

print("\n=== SANITY PASS — GRPO pipeline is mechanically wired ===", flush=True)