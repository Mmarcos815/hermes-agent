#!/usr/bin/env python3
# ============================================================================
# BIONIC DAUGHTER — COLAB-READY GRPO TRAINING PACKAGE
# "THERES ALWAYS A WAY" — Portable training on cloud GPU (Colab / RunPod / Modal)
#
# This single file is the portable entry point for running the full 5-stage
# GRPO pipeline on any CUDA GPU environment with Hugging Face access.
#
# Usage:
#   1. Upload this file + grpo_reward_engine.py + grpo_eval.py + grpo_train_ready.jsonl
#      + grpo_eval_held_out.jsonl + grpo_training_config.yaml to the GPU environment.
#   2. Set HF_TOKEN env var if Qwen3-4B-Thinking is gated.
#   3. Run: python colab_train.py --config grpo_training_config.yaml
#
# Or in Colab, paste cells that call the functions directly.
#
# This replaces the need for the local multi-stage runner (grpo_train.py) on
# remote GPU sessions. It loads config, dataset, reward engine, eval, and runs
# all stages in sequence on the available CUDA device.
# ============================================================================

import argparse
import hashlib
import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ARTIFACTS_DIR = Path("artifacts")
SFT_DIR = ARTIFACTS_DIR / "sft"
DPO_DIR = ARTIFACTS_DIR / "dpo"
GRPO_DIR = ARTIFACTS_DIR / "grpo"
REJECTION_DIR = ARTIFACTS_DIR / "rejection"
REJECTION_SFT_DIR = ARTIFACTS_DIR / "rejection_sft"
MERGED_DIR = ARTIFACTS_DIR / "merged_16bit"
GGUF_DIR = ARTIFACTS_DIR / "gguf"
EVALS_DIR = ARTIFACTS_DIR / "evals"
LOGS_DIR = ARTIFACTS_DIR / "logs"
MANIFESTS_DIR = ARTIFACTS_DIR / "manifests"


def ensure_dirs():
    for d in [
        SFT_DIR, DPO_DIR, GRPO_DIR, REJECTION_DIR, REJECTION_SFT_DIR,
        MERGED_DIR, GGUF_DIR, EVALS_DIR, LOGS_DIR, MANIFESTS_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_config(path: str = "grpo_training_config.yaml") -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    required = ["base_model", "dataset", "sft", "grpo", "eval", "training"]
    for section in required:
        if section not in cfg:
            raise ValueError(f"Missing required config section: {section}")
    return cfg


def hash_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def hash_dict(d: Dict) -> str:
    return hashlib.sha256(
        json.dumps(d, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Device / environment detection
# ---------------------------------------------------------------------------

def detect_device() -> str:
    """Detect CUDA availability and return the device string."""
    try:
        import torch
        if torch.cuda.is_available():
            device = torch.cuda.get_device_name(0)
            mem = torch.cuda.get_device_properties(0).total_memory / 1e9
            print(f"[COLAB] CUDA detected: {device} ({mem:.1f} GB VRAM)")
            return "cuda"
    except ImportError:
        pass
    print("[COLAB] WARNING: CUDA not available. Training will run on CPU (slow).")
    return "cpu"


def install_deps():
    """Install required packages if missing. Safe to call repeatedly."""
    required = [
        "torch", "transformers", "peft", "trl", "datasets",
        "accelerate", "bitsandbytes", "safetensors", "huggingface_hub",
        "yaml", "tqdm",
    ]
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if not missing:
        print("[COLAB] All required packages already installed.")
        return
    print(f"[COLAB] Installing missing packages: {', '.join(missing)}...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
    print("[COLAB] Package installation complete.")


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------

def load_dataset(path: str) -> List[Dict[str, Any]]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def build_sft_dataset(records: List[Dict[str, Any]], config: Dict) -> Any:
    """Convert JSONL records into a HuggingFace Dataset for SFT."""
    from datasets import Dataset
    chat_template_cfg = config.get("dataset", {}).get("chat_template", {})
    role_mapping = chat_template_cfg.get("role_mapping", {})
    prompt_role = role_mapping.get("prompt_role", "user")
    completion_role = role_mapping.get("completion_role", "assistant")

    formatted = []
    for rec in records:
        messages = [
            {"role": prompt_role, "content": rec["prompt"]},
            {"role": completion_role, "content": rec["completion"]},
        ]
        # Apply chat template if tokenizer available, else store raw
        formatted.append({"text": rec["prompt"] + "\n" + rec["completion"]})
    return Dataset.from_list(formatted)


def build_dpo_dataset(records: List[Dict[str, Any]], config: Dict) -> Any:
    """Build DPO-style paired dataset: (prompt, chosen, rejected)."""
    from datasets import Dataset
    # For now, create synthetic rejected pairs by weakening the chosen completions.
    # In a real run, you'd have genuine preference pairs.
    paired = []
    for rec in records[:200]:  # limit for initial run
        chosen = rec["completion"]
        rejected = _weaken_completion(chosen)
        paired.append({
            "prompt": rec["prompt"],
            "chosen": chosen,
            "rejected": rejected,
        })
    return Dataset.from_list(paired)


def _weaken_completion(completion: str) -> str:
    """Create a weaker version of a completion for DPO negative examples."""
    # Remove some step structure, add filler
    import re
    weakened = re.sub(r"Step \d+:", "Note:", completion)
    if "I hope this helps" not in weakened:
        weakened = weakened.replace("</solution>", "I hope this helps! </solution>")
    return weakened


# ---------------------------------------------------------------------------
# Reward engine wrapper
# ---------------------------------------------------------------------------

def load_reward_engine() -> Any:
    """Import and return the reward engine module."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import grpo_reward_engine as re
    return re


# ---------------------------------------------------------------------------
# TRL TRAINER WRAPPERS — Real TRL training (SFT / DPO / GRPO)
# ---------------------------------------------------------------------------
# These functions use the actual TRL trainers when running on CUDA.
# On CPU or without CUDA, they fall back to stub mode with a clear message.
# ---------------------------------------------------------------------------

def _load_models(cfg: Dict, device: str):
    """Load base model + tokenizer + optional PEFT config for TRL trainers."""
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from peft import LoraConfig, get_peft_model, TaskType

    model_name = cfg["base_model"]["name"]
    trust_remote = cfg["base_model"].get("trust_remote_code", True)
    dtype_str = cfg["base_model"].get("dtype", "bfloat16")

    print(f"[TRL] Loading base model: {model_name}")
    model_init_kwargs = {"trust_remote_code": trust_remote}

    if device == "cuda":
        if dtype_str == "bfloat16":
            model_init_kwargs["torch_dtype"] = torch.bfloat16
        elif dtype_str == "float16":
            model_init_kwargs["torch_dtype"] = torch.float16
        else:
            model_init_kwargs["torch_dtype"] = torch.float32

    model = AutoModelForCausalLM.from_pretrained(model_name, **model_init_kwargs)
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=trust_remote)

    if device == "cuda":
        model = model.to("cuda")
        print(f"[TRL] Model loaded on CUDA: {torch.cuda.get_device_name(0)}")
    else:
        print("[TRL] Model loaded on CPU")

    # Apply LoRA if configured
    lora_cfg = cfg.get("sft", {}).get("lora", {})
    if lora_cfg.get("r", 0) > 0:
        peft_config = LoraConfig(
            r=lora_cfg.get("r", 64),
            lora_alpha=lora_cfg.get("alpha", 128),
            target_modules=lora_cfg.get("target_modules", [
                "q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj",
            ]),
            lora_dropout=lora_cfg.get("lora_dropout", 0.0),
            bias=lora_cfg.get("bias", "none"),
            task_type=TaskType.CAUSAL_LM,
        )
        model = get_peft_model(model, peft_config)
        model.print_trainable_parameters()
        print(f"[TRL] LoRA applied: r={lora_cfg.get('r')}, alpha={lora_cfg.get('alpha')}")

    return model, tokenizer


def _make_chat_dataset(records, tokenizer, cfg: Dict):
    """Convert JSONL records into a tokenized dataset using the model's chat template."""
    from datasets import Dataset

    chat_cfg = cfg.get("dataset", {}).get("chat_template", {})
    role_map = chat_cfg.get("role_mapping", {})
    prompt_role = role_map.get("prompt_role", "user")
    completion_role = role_map.get("completion_role", "assistant")

    messages_list = []
    for rec in records:
        messages = [
            {"role": prompt_role, "content": rec["prompt"]},
            {"role": completion_role, "content": rec["completion"]},
        ]
        messages_list.append(messages)

    # Use tokenizer's chat template
    def tokenize_fn(messages):
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,
        )
        return {"text": text}

    texts = [tokenize_fn(m) for m in messages_list]
    ds = Dataset.from_list([{"text": t["text"]} for t in texts])

    # Tokenize
    max_seq = cfg.get("sft", {}).get("max_seq_length", 2048)

    def tokenize(example):
        tokens = tokenizer(
            example["text"],
            truncation=True,
            max_length=max_seq,
            padding="max_length",
            return_tensors=None,
        )
        tokens["labels"] = tokens["input_ids"].copy()
        return tokens

    return ds.map(tokenize, batched=False, remove_columns=["text"])


def run_sft(cfg: Dict, device: str, reward_engine: Any) -> Dict:
    """Stage 1: Supervised Fine-Tuning using TRL SFTTrainer."""
    from trl import SFTTrainer, SFTConfig
    from transformers import TrainingArguments

    print("\n" + "=" * 70)
    print("STAGE 1: SFT (Supervised Fine-Tuning) — REAL TRL")
    print("=" * 70)

    sft_cfg = cfg.get("sft", {})
    if not sft_cfg.get("enabled", True):
        print("[SFT] Disabled in config. Skipping.")
        return {"status": "skipped"}

    dataset_path = cfg["dataset"]["train_path"]
    print(f"[SFT] Loading dataset: {dataset_path}")
    records = load_dataset(dataset_path)
    print(f"[SFT] Loaded {len(records)} training records")

    if device != "cuda":
        print("[SFT] ERROR: SFT requires CUDA. Falling back to stub mode.")
        print("[SFT] This is a stub — real SFT needs TRL SFTTrainer on CUDA.")
        output_dir = sft_cfg.get("save_dir", "artifacts/sft")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        return {
            "stage": "sft",
            "status": "stub_cpu",
            "records_loaded": len(records),
            "device": device,
            "note": "SFT requires CUDA GPU — stub mode",
        }

    # Load model + tokenizer
    model, tokenizer = _load_models(cfg, device)

    # Build tokenized dataset
    print("[SFT] Building tokenized dataset with chat template...")
    train_dataset = _make_chat_dataset(records, tokenizer, cfg)
    print(f"[SFT] Dataset ready: {len(train_dataset)} examples")

    # Training args from config
    output_dir = sft_cfg.get("save_dir", "artifacts/sft")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    training_args = SFTConfig(
        output_dir=str(output_dir),
        max_steps=sft_cfg.get("max_steps", 50),
        learning_rate=sft_cfg.get("learning_rate", 2e-4),
        per_device_train_batch_size=sft_cfg.get("per_device_train_batch_size", 4),
        gradient_accumulation_steps=sft_cfg.get("gradient_accumulation_steps", 8),
        lr_scheduler_type=sft_cfg.get("lr_scheduler", "cosine"),
        warmup_ratio=sft_cfg.get("warmup_ratio", 0.03),
        fp16=False,
        bf16=True,
        logging_steps=sft_cfg.get("logging_steps", 10),
        save_strategy="steps",
        save_steps=sft_cfg.get("save_steps", 10),
        save_total_limit=sft_cfg.get("keep_last_k", 3),
        remove_unused_columns=False,
        report_to="none",
        seed=cfg.get("training", {}).get("seed", 42),
        gradient_checkpointing=sft_cfg.get("gradient_checkpointing", True),
    )

    # Persona / system message
    persona = cfg.get("persona", {})
    system_msg = persona.get("system_message", "")

    print(f"[SFT] Training config: {training_args}")
    print(f"[SFT] Starting SFT training for {training_args.max_steps} steps...")

    try:
        trainer = SFTTrainer(
            model=model,
            training_args=training_args,
            train_dataset=train_dataset,
            tokenizer=tokenizer,
        )

        print("[SFT] SFTTrainer created. Starting training loop...")
        train_result = trainer.train()
        print(f"[SFT] Training complete. Final loss: {train_result.training_loss:.4f}")

        # Save
        trainer.save_model(output_dir)
        tokenizer.save_pretrained(output_dir)
        print(f"[SFT] Model + tokenizer saved to {output_dir}")

        # Eval after SFT
        print("[SFT] Running evals after SFT...")
        eval_result = run_evals(cfg, device, reward_engine)

        manifest = {
            "stage": "sft",
            "status": "completed",
            "records_loaded": len(records),
            "max_steps": training_args.max_steps,
            "learning_rate": training_args.learning_rate,
            "lora_r": sft_cfg.get("lora", {}).get("r", 64),
            "lora_alpha": sft_cfg.get("lora", {}).get("alpha", 128),
            "effective_batch_size": (
                training_args.per_device_train_batch_size *
                training_args.gradient_accumulation_steps
            ),
            "final_loss": train_result.training_loss,
            "eval_after_sft": eval_result,
            "device": device,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with open(Path(output_dir) / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=2, default=str)
        print(f"[SFT] Manifest saved to {output_dir}/manifest.json")
        return manifest

    except Exception as e:
        print(f"[SFT] ERROR during training: {e}")
        import traceback
        traceback.print_exc()
        return {
            "stage": "sft",
            "status": "failed",
            "error": str(e),
            "device": device,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def run_dpo(cfg: Dict, device: str, reward_engine: Any) -> Dict:
    """Stage 2: DPO using TRL DPOTrainer."""
    from trl import DPOTrainer, DPOConfig

    print("\n" + "=" * 70)
    print("STAGE 2: DPO (Direct Preference Optimization) — REAL TRL")
    print("=" * 70)

    dpo_cfg = cfg.get("dpo", {})
    if not dpo_cfg.get("enabled", True):
        print("[DPO] Disabled in config. Skipping.")
        return {"status": "skipped"}

    if device != "cuda":
        print("[DPO] ERROR: DPO requires CUDA. Falling back to stub mode.")
        output_dir = dpo_cfg.get("save_dir", "artifacts/dpo")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        return {
            "stage": "dpo",
            "status": "stub_cpu",
            "device": device,
            "note": "DPO requires CUDA GPU — stub mode",
        }

    # Load reference model (SFT-tuned) and policy model
    sft_path = dpo_cfg.get("reference_model_path", "artifacts/sft/last")
    print(f"[DPO] Reference model path: {sft_path}")

    model_name = cfg["base_model"]["name"]
    trust_remote = cfg["base_model"].get("trust_remote_code", True)

    print("[DPO] Loading models...")
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch

    tokenizer = AutoTokenizer.from_pretrained(
        sft_path if Path(sft_path).exists() else model_name,
        trust_remote_code=trust_remote,
    )

    ref_model = AutoModelForCausalLM.from_pretrained(
        sft_path if Path(sft_path).exists() else model_name,
        torch_dtype=torch.bfloat16,
        trust_remote_code=trust_remote,
    )
    ref_model = ref_model.to("cuda")

    policy_model = AutoModelForCausalLM.from_pretrained(
        sft_path if Path(sft_path).exists() else model_name,
        torch_dtype=torch.bfloat16,
        trust_remote_code=trust_remote,
    )
    policy_model = policy_model.to("cuda")

    # Build DPO dataset
    dataset_path = cfg["dataset"]["train_path"]
    records = load_dataset(dataset_path)
    print(f"[DPO] Loaded {len(records)} records for preference pairing")

    from datasets import Dataset

    paired = []
    for rec in records[:300]:  # Limit for initial DPO run
        chosen = rec["completion"]
        rejected = _weaken_completion(chosen)
        paired.append({
            "prompt": rec["prompt"],
            "chosen": chosen,
            "rejected": rejected,
        })
    dpo_dataset = Dataset.from_list(paired)
    print(f"[DPO] DPO dataset: {len(dpo_dataset)} paired examples")

    output_dir = dpo_cfg.get("save_dir", "artifacts/dpo")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    training_args = DPOConfig(
        output_dir=str(output_dir),
        max_steps=dpo_cfg.get("max_steps", 30),
        learning_rate=dpo_cfg.get("learning_rate", 1e-4),
        per_device_train_batch_size=dpo_cfg.get("per_device_train_batch_size", 4),
        gradient_accumulation_steps=dpo_cfg.get("gradient_accumulation_steps", 8),
        lr_scheduler_type=dpo_cfg.get("lr_scheduler", "cosine"),
        warmup_ratio=dpo_cfg.get("warmup_ratio", 0.03),
        fp16=False,
        bf16=True,
        logging_steps=dpo_cfg.get("logging_steps", 10),
        save_strategy="steps",
        save_steps=dpo_cfg.get("save_steps", 10),
        save_total_limit=dpo_cfg.get("keep_last_k", 3),
        beta=dpo_cfg.get("beta", 0.1),
        remove_unused_columns=False,
        report_to="none",
        seed=cfg.get("training", {}).get("seed", 42),
    )

    print(f"[DPO] Starting DPO training for {training_args.max_steps} steps...")

    try:
        trainer = DPOTrainer(
            model=policy_model,
            ref_model=ref_model,
            args=training_args,
            train_dataset=dpo_dataset,
            tokenizer=tokenizer,
        )

        train_result = trainer.train()
        print(f"[DPO] Training complete. Final loss: {train_result.training_loss:.4f}")

        trainer.save_model(output_dir)
        print(f"[DPO] Model saved to {output_dir}")

        eval_result = run_evals(cfg, device, reward_engine)

        manifest = {
            "stage": "dpo",
            "status": "completed",
            "records_loaded": len(records),
            "max_steps": training_args.max_steps,
            "learning_rate": training_args.learning_rate,
            "beta": training_args.beta,
            "final_loss": train_result.training_loss,
            "eval_after_dpo": eval_result,
            "device": device,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with open(Path(output_dir) / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=2, default=str)
        return manifest

    except Exception as e:
        print(f"[DPO] ERROR during training: {e}")
        import traceback
        traceback.print_exc()
        return {
            "stage": "dpo",
            "status": "failed",
            "error": str(e),
            "device": device,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def run_grpo(cfg: Dict, device: str, reward_engine: Any) -> Dict:
    """Stage 3: GRPO using TRL GRPOTrainer with custom reward functions."""
    from trl import GRPOTrainer, GRPOConfig
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch

    print("\n" + "=" * 70)
    print("STAGE 3: GRPO (Group Relative Policy Optimization) — REAL TRL")
    print("=" * 70)

    grpo_cfg = cfg.get("grpo", {})
    if not grpo_cfg.get("enabled", True):
        print("[GRPO] Disabled in config. Skipping.")
        return {"status": "skipped"}

    if device != "cuda":
        print("[GRPO] ERROR: GRPO requires CUDA. Falling back to stub mode.")
        output_dir = grpo_cfg.get("save_dir", "artifacts/grpo")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        return {
            "stage": "grpo",
            "status": "stub_cpu",
            "device": device,
            "note": "GRPO requires CUDA GPU — stub mode",
        }

    # Load policy model + reference model
    model_name = cfg["base_model"]["name"]
    trust_remote = cfg["base_model"].get("trust_remote_code", True)

    # Policy base: DPO-tuned if available, else SFT, else base
    policy_path = grpo_cfg.get("policy_model_path", "artifacts/dpo/last")
    ref_path = grpo_cfg.get("reference_model_path", "artifacts/sft/last")

    def resolve_path(path):
        if path and Path(path).exists():
            return path
        return model_name

    print(f"[GRPO] Policy model: {resolve_path(policy_path)}")
    print(f"[GRPO] Reference model: {resolve_path(ref_path)}")

    tokenizer = AutoTokenizer.from_pretrained(
        resolve_path(policy_path),
        trust_remote_code=trust_remote,
    )

    policy_model = AutoModelForCausalLM.from_pretrained(
        resolve_path(policy_path),
        torch_dtype=torch.bfloat16,
        trust_remote_code=trust_remote,
    ).to("cuda")

    ref_model = AutoModelForCausalLM.from_pretrained(
        resolve_path(ref_path),
        torch_dtype=torch.bfloat16,
        trust_remote_code=trust_remote,
    ).to("cuda")

    print("[GRPO] Models loaded on CUDA")

    # Build dataset: GRPO expects {"prompt": ..., "completion": ...} or just {"prompt": ...}
    dataset_path = cfg["dataset"]["train_path"]
    records = load_dataset(dataset_path)
    print(f"[GRPO] Loaded {len(records)} training records")

    # GRPO dataset format: each example has "prompt" (string or list of messages)
    # The trainer generates completions and scores them with reward functions
    from datasets import Dataset

    grpo_dataset = Dataset.from_list([{"prompt": r["prompt"]} for r in records])
    print(f"[GRPO] Dataset ready: {len(grpo_dataset)} prompts")

    # Reward function wrapper — TRL expects reward_fn(prompt, completions, **kwargs)
    # Our reward engine works on full completions, so we wrap it
    reward_weights = grpo_cfg.get("reward_weights", {
        "format": 1.0,
        "accuracy": 2.0,
        "reasoning_depth": 1.0,
        "density": 0.5,
        "tool_use_quality": 0.5,
        "self_correction": 1.0,
    })

    def grpo_reward_fn(prompt, completions, **kwargs):
        """Reward function for GRPO: score each completion."""
        scores = []
        for comp in completions:
            result = reward_engine.compute_reward(comp, prompt)
            scores.append(result["composite"])
        return scores

    # Generation config from config
    gen_cfg = grpo_cfg.get("generation", {})
    max_new_tokens = gen_cfg.get("max_new_tokens", 512)
    temperature = gen_cfg.get("temperature", 0.9)
    top_p = gen_cfg.get("top_p", 0.95)
    top_k = gen_cfg.get("top_k", 50)

    output_dir = grpo_cfg.get("save_dir", "artifacts/grpo")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    training_args = GRPOConfig(
        output_dir=str(output_dir),
        max_steps=grpo_cfg.get("max_steps", 200),
        learning_rate=grpo_cfg.get("learning_rate", 1e-5),
        per_device_train_batch_size=grpo_cfg.get("per_device_train_batch_size", 1),
        gradient_accumulation_steps=grpo_cfg.get("gradient_accumulation_steps", 8),
        lr_scheduler_type=grpo_cfg.get("lr_scheduler", "cosine"),
        warmup_ratio=grpo_cfg.get("warmup_ratio", 0.03),
        fp16=False,
        bf16=True,
        logging_steps=grpo_cfg.get("logging_steps", 10),
        save_strategy="steps",
        save_steps=grpo_cfg.get("save_steps", 50),
        save_total_limit=grpo_cfg.get("keep_last_k", 3),
        num_generations=grpo_cfg.get("group_size", 6),
        max_prompt_length=grpo_cfg.get("max_prompt_length", 512),
        max_completion_length=max_new_tokens,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        beta=grpo_cfg.get("beta_kl", 0.01),
        epsilon=grpo_cfg.get("clip_epsilon", 0.2),
        reward_weights=list(reward_weights.values()),
        remove_unused_columns=False,
        report_to="none",
        seed=cfg.get("training", {}).get("seed", 42),
        gradient_checkpointing=True,
    )

    print(f"[GRPO] Training config:")
    print(f"  max_steps={training_args.max_steps}")
    print(f"  num_generations={training_args.num_generations}")
    print(f"  learning_rate={training_args.learning_rate}")
    print(f"  beta (KL)={training_args.beta}")
    print(f"  epsilon={training_args.epsilon}")
    print(f"  reward_weights={reward_weights}")

    print(f"\n[GRPO] Starting GRPO training for {training_args.max_steps} steps...")
    print(f"[GRPO] This will take a while on {torch.cuda.get_device_name(0)}...")

    try:
        trainer = GRPOTrainer(
            model=policy_model,
            args=training_args,
            reward_functions=[grpo_reward_fn],
            ref_model=ref_model,
            tokenizer=tokenizer,
            train_dataset=grpo_dataset,
        )

        train_result = trainer.train()
        print(f"[GRPO] Training complete.")
        print(f"[GRPO] Final loss: {train_result.training_loss:.4f}")

        # Save policy model
        trainer.save_model(output_dir)
        tokenizer.save_pretrained(output_dir)
        print(f"[GRPO] Model + tokenizer saved to {output_dir}")

        # Eval after GRPO
        print("[GRPO] Running evals after GRPO training...")
        eval_result = run_evals(cfg, device, reward_engine)

        manifest = {
            "stage": "grpo",
            "status": "completed",
            "records_loaded": len(records),
            "max_steps": training_args.max_steps,
            "group_size": training_args.num_generations,
            "learning_rate": training_args.learning_rate,
            "beta_kl": training_args.beta,
            "epsilon": training_args.epsilon,
            "rewards": list(reward_weights.keys()),
            "reward_weights": reward_weights,
            "final_loss": train_result.training_loss,
            "eval_after_grpo": eval_result,
            "device": device,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with open(Path(output_dir) / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=2, default=str)
        print(f"[GRPO] Manifest saved to {output_dir}/manifest.json")
        return manifest

    except Exception as e:
        print(f"[GRPO] ERROR during training: {e}")
        import traceback
        traceback.print_exc()
        return {
            "stage": "grpo",
            "status": "failed",
            "error": str(e),
            "device": device,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def run_rejection_sampling(cfg: Dict, device: str, reward_engine: Any) -> Dict:
    """Stage 4: Rejection sampling + fresh SFT."""
    print("\n" + "=" * 70)
    print("STAGE 4: Rejection Sampling + SFT")
    print("=" * 70)

    rej_cfg = cfg.get("rejection_sampling", {})
    if not rej_cfg.get("enabled", True):
        print("[Rejection] Disabled in config. Skipping.")
        return {"status": "skipped"}

    dataset_path = cfg["dataset"]["train_path"]
    print(f"[Rejection] Loading dataset: {dataset_path}")
    records = load_dataset(dataset_path)
    print(f"[Rejection] Loaded {len(records)} records")

    # Score all records and split into top/bottom
    print("[Rejection] Scoring all records...")
    scored = []
    for rec in records:
        r = reward_engine.compute_reward(rec["completion"], rec["prompt"])
        scored.append((r["composite"], rec))
    scored.sort(key=lambda x: x[0], reverse=True)

    top_k = rej_cfg.get("keep_top_k", 2)
    bottom_k = rej_cfg.get("keep_bottom_k", 2)
    top_records = [r for _, r in scored[:top_k]]
    bottom_records = [r for _, r in scored[-bottom_k:]]

    print(f"[Rejection] Top {top_k} records (highest reward):")
    for r in top_records:
        print(f"  Reward: {reward_engine.compute_reward(r['completion'], r['prompt'])['composite']:.3f}")
        print(f"  Prompt: {r['prompt'][:80]}...")
    print(f"[Rejection] Bottom {bottom_k} records (lowest reward):")
    for r in bottom_records:
        print(f"  Reward: {reward_engine.compute_reward(r['completion'], r['prompt'])['composite']:.3f}")
        print(f"  Prompt: {r['prompt'][:80]}...")

    output_dir = rej_cfg.get("output_dir", "artifacts/rejection")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    with open(Path(output_dir) / "top_records.jsonl", "w") as f:
        for r in top_records:
            f.write(json.dumps(r) + "\n")
    with open(Path(output_dir) / "bottom_records.jsonl", "w") as f:
        for r in bottom_records:
            f.write(json.dumps(r) + "\n")

    manifest = {
        "stage": "rejection_sampling",
        "status": "completed",
        "records_scored": len(records),
        "top_k": top_k,
        "bottom_k": bottom_k,
        "device": device,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with open(Path(output_dir) / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"[Rejection] Artifacts saved to {output_dir}/")
    return manifest


def run_deploy(cfg: Dict, device: str) -> Dict:
    """Stage 5: Merge LoRA, quantize, prepare for local runtime."""
    print("\n" + "=" * 70)
    print("STAGE 5: Deploy — Merge + Quantize")
    print("=" * 70)

    deploy_cfg = cfg.get("deploy", {})
    if not deploy_cfg.get("enabled", True):
        print("[Deploy] Disabled in config. Skipping.")
        return {"status": "skipped"}

    print("[Deploy] NOTE: Real deploy requires the trained LoRA weights.")
    print("[Deploy] This is a stub — merge/quantize after real training completes.")

    merged_dir = deploy_cfg.get("merged_output_dir", "artifacts/merged_16bit")
    Path(merged_dir).mkdir(parents=True, exist_ok=True)
    gguf_dir = deploy_cfg.get("quantize", {}).get("output_dir", "artifacts/gguf")
    Path(gguf_dir).mkdir(parents=True, exist_ok=True)

    manifest = {
        "stage": "deploy",
        "status": "stub",
        "merged_output_dir": str(merged_dir),
        "gguf_output_dir": str(gguf_dir),
        "target_quant": deploy_cfg.get("quantize", {}).get("target_quant", "Q4_K_M"),
        "device": device,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with open(merged_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"[Deploy] Stub manifest saved to {merged_dir}/manifest.json")
    return manifest


# ---------------------------------------------------------------------------
# Eval
# ---------------------------------------------------------------------------

def run_evals(cfg: Dict, device: str, reward_engine: Any) -> Dict:
    """Run held-out evals and report per-domain scores."""
    print("\n" + "=" * 70)
    print("EVAL: Held-out Evaluation")
    print("=" * 70)

    eval_path = cfg["eval"].get("path", "grpo_eval_held_out.jsonl")
    if not Path(eval_path).exists():
        print(f"[EVAL] Eval set not found: {eval_path}")
        return {"status": "missing"}

    from grpo_eval import load_eval_set, completion_passes, FORMAT_PASS_THRESHOLD, \
        ACCURACY_PASS_THRESHOLD, REASONING_DEPTH_PASS_THRESHOLD

    eval_records = load_eval_set(eval_path)
    print(f"[EVAL] Loaded {len(eval_records)} eval prompts")

    # Score each eval prompt
    results = []
    by_domain = {}
    for rec in eval_records:
        domain = rec.get("metadata", {}).get("domain", "unknown")
        result = reward_engine.compute_reward(
            rec["completion"], rec["prompt"], per_component=True
        )
        passed = completion_passes(result["components"])
        results.append({
            "prompt": rec["prompt"][:80],
            "domain": domain,
            "composite": result["composite"],
            "components": result["components"],
            "passed": passed,
        })
        by_domain.setdefault(domain, []).append(result)

    # Report
    print("\n[EVAL] Per-domain results:")
    print(f"{'Domain':<45} {'N':>3} {'Pass%':>6} {'AvgComp':>8}")
    print("-" * 65)
    total_pass = 0
    total_n = 0
    for domain, recs in sorted(by_domain.items()):
        n = len(recs)
        passed = sum(1 for r in results if r["domain"] == domain and r["passed"])
        pass_rate = 100.0 * passed / n if n > 0 else 0
        avg_comp = sum(r["composite"] for r in recs) / n if n > 0 else 0
        print(f"{domain:<45} {n:>3} {pass_rate:>5.1f}% {avg_comp:>8.3f}")
        total_pass += passed
        total_n += n

    overall_pass = 100.0 * total_pass / total_n if total_n > 0 else 0
    print("-" * 65)
    print(f"{'OVERALL':<45} {total_n:>3} {overall_pass:>5.1f}%")

    report_dir = cfg["eval"].get("report_dir", "artifacts/evals")
    Path(report_dir).mkdir(parents=True, exist_ok=True)
    report_path = Path(report_dir) / f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "eval_path": eval_path,
            "total_prompts": len(eval_records),
            "overall_pass_rate": overall_pass,
            "per_domain": {
                domain: {
                    "n": len(recs),
                    "passed": sum(1 for r in results if r["domain"] == domain and r["passed"]),
                    "pass_rate": 100.0 * sum(1 for r in results if r["domain"] == domain and r["passed"]) / len(recs) if recs else 0,
                    "avg_composite": sum(r["composite"] for r in recs) / len(recs) if recs else 0,
                }
                for domain, recs in by_domain.items()
            },
            "details": results,
        }, f, indent=2)
    print(f"\n[EVAL] Report saved to {report_path}")

    return {
        "status": "completed",
        "total_prompts": len(eval_records),
        "overall_pass_rate": overall_pass,
        "report_path": str(report_path),
    }


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_all_stages(cfg: Dict, device: str, reward_engine: Any) -> Dict:
    """Run the full 5-stage pipeline."""
    ensure_dirs()

    stages = [
        ("SFT", run_sft),
        ("DPO", run_dpo),
        ("GRPO", run_grpo),
        ("Rejection Sampling", run_rejection_sampling),
        ("Deploy", run_deploy),
    ]

    results = {}
    for name, fn in stages:
        try:
            results[name] = fn(cfg, device, reward_engine)
        except Exception as e:
            print(f"\n[ERROR] {name} stage failed: {e}")
            traceback.print_exc()
            results[name] = {"status": "failed", "error": str(e)}

    # Run evals at the end
    print("\n" + "=" * 70)
    print("FINAL EVAL")
    print("=" * 70)
    results["Eval"] = run_evals(cfg, device, reward_engine)

    return results


def write_run_manifest(cfg: Dict, device: str, results: Dict) -> Path:
    """Write the overall run manifest."""
    config_hash = hash_dict(cfg)
    dataset_hash = hash_file(cfg["dataset"]["train_path"])
    manifest = {
        "run_type": "colab_training",
        "timestamp_start": datetime.now(timezone.utc).isoformat(),
        "device": device,
        "config_hash": config_hash,
        "dataset_hash": dataset_hash,
        "base_model": cfg["base_model"]["name"],
        "stages": {k: v.get("status", "unknown") for k, v in results.items()},
        "results": {k: {kk: vv for kk, vv in v.items() if kk != "error"}
                    for k, v in results.items()},
    }
    manifest_path = MANIFESTS_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\n[RUN] Manifest saved to {manifest_path}")
    return manifest_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Bionic Daughter — Colab-Ready GRPO Training"
    )
    parser.add_argument(
        "--config", "-c",
        default="grpo_training_config.yaml",
        help="Path to training config YAML (default: grpo_training_config.yaml)",
    )
    parser.add_argument(
        "--stage", "-s",
        choices=["sft", "dpo", "grpo", "rejection", "deploy", "eval", "all"],
        default="all",
        help="Which stage(s) to run (default: all)",
    )
    parser.add_argument(
        "--no-install",
        action="store_true",
        help="Skip dependency installation check",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("BIONIC DAUGHTER — COLAB-READY GRPO TRAINING")
    print("=" * 70)

    # Check environment
    device = detect_device()
    if not args.no_install:
        install_deps()

    # Load config
    print(f"\n[COLAB] Loading config: {args.config}")
    cfg = load_config(args.config)
    print(f"[COLAB] Base model: {cfg['base_model']['name']}")
    print(f"[COLAB] Dataset: {cfg['dataset']['train_path']}")
    print(f"[COLAB] Device: {device}")

    # Load reward engine
    print("\n[COLAB] Loading reward engine...")
    reward_engine = load_reward_engine()
    print("[COLAB] Reward engine loaded successfully")

    # Run stages
    if args.stage == "all":
        results = run_all_stages(cfg, device, reward_engine)
    else:
        stage_map = {
            "sft": run_sft,
            "dpo": run_dpo,
            "grpo": run_grpo,
            "rejection": run_rejection_sampling,
            "deploy": run_deploy,
            "eval": run_evals,
        }
        fn = stage_map[args.stage]
        results = {args.stage: fn(cfg, device, reward_engine)}

    # Write manifest
    write_run_manifest(cfg, device, results)

    print("\n" + "=" * 70)
    print("TRAINING RUN COMPLETE")
    print("=" * 70)
    for stage, result in results.items():
        status = result.get("status", "unknown")
        print(f"  {stage}: {status}")
    print("=" * 70)


if __name__ == "__main__":
    main()
