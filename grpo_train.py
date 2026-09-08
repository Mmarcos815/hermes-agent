# ============================================================================
# BIONIC DAUGHTER — GRPO TRAINING RUNNER
# Wires the 5-stage pipeline together:
#   SFT -> DPO/ORPO -> GRPO -> Rejection Sampling + SFT -> Quantize + Eval
#
# This is the orchestration layer. Each stage is a function that reads the
# config and runs the real training code via HuggingFace TRL / PEFT / Unsloth
# (where available) or stubs when the libraries aren't wired yet.
#
# Design principles (from the training guide + R1 study):
#   - reward design is everything; the pipeline is simple, the rewards steer
#   - format first, quality second (SFT teaches format, GRPO refines quality)
#   - evals before/after every stage so we know what changed
#   - artifacts are reproducible: config hash + dataset hash + seed in every
#     manifest
# ============================================================================

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# ---------------------------------------------------------------------------
# Paths — everything lives under artifacts/
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

# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_config(path: str = "grpo_training_config.yaml") -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    # Validate required sections exist
    required = ["base_model", "dataset", "sft", "grpo", "eval", "training"]
    for section in required:
        if section not in cfg:
            raise ValueError(f"Missing required config section: {section}")
    return cfg


def hash_file(path: str) -> str:
    """SHA256 of a file, first 16 hex chars — for manifest integrity."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def hash_dict(d: Dict) -> str:
    """Stable hash of a dict (sorted keys, JSON-serialized)."""
    return hashlib.sha256(
        json.dumps(d, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Stage manifests — one per stage, capturing what ran
# ---------------------------------------------------------------------------

def write_stage_manifest(
    stage: str,
    config_hash: str,
    dataset_hash: str,
    base_model_hash: str,
    hyperparameters: Dict[str, Any],
    start_time: str,
    end_time: str,
    eval_result: Optional[Dict] = None,
    status: str = "completed",
    notes: str = "",
) -> Path:
    manifest = {
        "stage": stage,
        "timestamp_start": start_time,
        "timestamp_end": end_time,
        "status": status,
        "config_hash": config_hash,
        "dataset_hash": dataset_hash,
        "base_model_hash": base_model_hash,
        "hyperparameters": hyperparameters,
        "eval_result": eval_result,
        "notes": notes,
    }
    path = MANIFESTS_DIR / f"manifest_{stage}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=str)
    return path


# ---------------------------------------------------------------------------
# EVAL HOOK — run evals at the right points
# ---------------------------------------------------------------------------

def run_eval_hook(
    label: str,
    eval_path: str,
    generations_per_prompt: int = 4,
    weights: Dict = None,
) -> Dict:
    """
    Run the eval suite and return the result dict.
    In a real run, generate_fn is the trainer's model.generate().
    Here we use the stored completions for baseline validation.
    """
    # Import lazily so the runner can load without the eval module present
    # until we actually run evals (avoids import errors in stubs).
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from grpo_eval import run_eval

    result = run_eval(
        eval_path=eval_path,
        generations_per_prompt=generations_per_prompt,
        weights=weights,
    )

    # Print the report
    from grpo_eval import print_report
    print_report(result, label=label)

    # Save the report
    safe_label = label.replace(" ", "_").lower()
    report_path = EVALS_DIR / f"eval_{safe_label}.json"
    EVALS_DIR.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)

    return result


# ---------------------------------------------------------------------------
# STAGE 1 — SFT
# ---------------------------------------------------------------------------

def run_sft(cfg: Dict) -> Dict:
    """
    Stage 1: Supervised Fine-Tuning.
    Teaches format + specialist reasoning on our 1,005 traces.
    In a real run, this calls TRL/SFT trainer with LoRA.
    Here we validate the config and emit the manifest + stub artifact.
    """
    start = datetime.now(timezone.utc).isoformat()
    print("\n" + "=" * 70)
    print("  STAGE 1 — SFT (Supervised Fine-Tuning)")
    print("=" * 70)

    sft_cfg = cfg["sft"]
    dataset_cfg = cfg["dataset"]
    training_cfg = cfg["training"]

    print(f"  Dataset           : {dataset_cfg['train_path']}")
    print(f"  Base model        : {cfg['base_model']['name']}")
    print(f"  Device            : {training_cfg.get('device', 'cuda')}")
    print(f"  Max steps         : {sft_cfg['max_steps']}")
    print(f"  LR                : {sft_cfg['learning_rate']}")
    print(f"  Scheduler         : {sft_cfg['lr_scheduler']}")
    print(f"  Warmup ratio      : {sft_cfg['warmup_ratio']}")
    print(f"  Effective batch   : {sft_cfg['effective_batch_size']}")
    print(f"  LoRA r/α          : {sft_cfg['lora']['r']} / {sft_cfg['lora']['alpha']}")
    print(f"  Target modules    : {', '.join(sft_cfg['lora']['target_modules'])}")
    print(f"  Max seq length    : {sft_cfg['max_seq_length']}")
    print(f"  Save dir          : {sft_cfg['save_dir']}")
    print()

    # Validate LoRA target modules against the model
    # (In a real run we'd load the model and check named_modules.
    #  Here we trust the config + assert the expected modules for Qwen3 4B.)
    expected_modules = {
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    }
    configured = set(sft_cfg["lora"]["target_modules"])
    missing = expected_modules - configured
    if missing:
        print(f"  [WARN] LoRA target modules missing expected: {missing}")
    print(f"  LoRA target modules validated: {configured}")

    # Validate dataset exists
    dataset_path = Path(dataset_cfg["train_path"])
    if not dataset_path.exists():
        raise FileNotFoundError(f"Training dataset not found: {dataset_path}")
    print(f"  Dataset validated: {dataset_path} ({dataset_cfg.get('format')})")

    # Simulate the training run (real run calls TRL SFTTrainer)
    print("  [SIM] Loading base model...")
    time.sleep(0.2)
    print("  [SIM] Applying LoRA config...")
    time.sleep(0.1)
    print("  [SIM] Running SFT trainer for {} steps...".format(sft_cfg["max_steps"]))
    time.sleep(0.3)
    print("  [SIM] SFT complete — saving artifacts to", sft_cfg["save_dir"])

    # Emit stub artifact + manifest
    SFT_DIR.mkdir(parents=True, exist_ok=True)
    stub_path = SFT_DIR / "last"
    stub_path.mkdir(parents=True, exist_ok=True)
    with open(stub_path / "config.json", "w", encoding="utf-8") as f:
        json.dump({
            "stage": "sft",
            "base_model": cfg["base_model"]["name"],
            "lora_config": sft_cfg["lora"],
            "model_type": cfg["base_model"].get("dtype", "bfloat16"),
        }, f, indent=2)
    # Placeholder adapter weights (stub — real run writes real LoRA weights)
    with open(stub_path / "adapter_weights.stub", "w", encoding="utf-8") as f:
        f.write("STUB — real LoRA adapter weights written by trainer\n")

    end = datetime.now(timezone.utc).isoformat()
    config_hash = hash_dict(cfg)
    dataset_hash = hash_file(str(dataset_path))
    base_model_hash = hash_dict(cfg["base_model"])

    write_stage_manifest(
        stage="sft",
        config_hash=config_hash,
        dataset_hash=dataset_hash,
        base_model_hash=base_model_hash,
        hyperparameters={
            "max_steps": sft_cfg["max_steps"],
            "learning_rate": sft_cfg["learning_rate"],
            "lr_scheduler": sft_cfg["lr_scheduler"],
            "warmup_ratio": sft_cfg["warmup_ratio"],
            "effective_batch_size": sft_cfg["effective_batch_size"],
            "lora_r": sft_cfg["lora"]["r"],
            "lora_alpha": sft_cfg["lora"]["alpha"],
            "target_modules": sft_cfg["lora"]["target_modules"],
            "max_seq_length": sft_cfg["max_seq_length"],
            "packing": sft_cfg["packing"],
            "save_dir": sft_cfg["save_dir"],
        },
        start_time=start,
        end_time=end,
        status="completed",
        notes="SFT stage complete. Stub artifacts written — real run writes LoRA weights via TRL.",
    )

    print(f"  Manifest written: {MANIFESTS_DIR / 'manifest_sft.json'}")
    return {"status": "completed", "save_dir": sft_cfg["save_dir"]}


# ---------------------------------------------------------------------------
# STAGE 2 — DPO / ORPO
# ---------------------------------------------------------------------------

def run_dpo(cfg: Dict) -> Dict:
    """
    Stage 2: Preference Optimization (DPO).
    Teaches precision over fluff + refusal calibration.
    In a real run, this calls TRL DPOTrainer with paired (chosen, rejected) data.
    Here we build the paired dataset stub + emit manifest.
    """
    start = datetime.now(timezone.utc).isoformat()
    print("\n" + "=" * 70)
    print("  STAGE 2 — DPO (Preference Optimization)")
    print("=" * 70)

    dpo_cfg = cfg["dpo"]
    dataset_cfg = cfg["dataset"]

    print(f"  Base (SFT) model  : {dpo_cfg['reference_model_path']}")
    print(f"  Max steps         : {dpo_cfg['max_steps']}")
    print(f"  LR                : {dpo_cfg['learning_rate']}")
    print(f"  Beta (KL penalty) : {dpo_cfg['beta']}")
    print(f"  Save dir          : {dpo_cfg['save_dir']}")
    print()

    # Build paired dataset stub (chosen = good traces, rejected = weakened)
    print("  [SIM] Building paired dataset (chosen / rejected)...")
    time.sleep(0.2)
    print("  [SIM] Running DPO trainer for {} steps...".format(dpo_cfg["max_steps"]))
    time.sleep(0.3)
    print("  [SIM] DPO complete — saving artifacts to", dpo_cfg["save_dir"])

    DPO_DIR.mkdir(parents=True, exist_ok=True)
    stub_path = DPO_DIR / "last"
    stub_path.mkdir(parents=True, exist_ok=True)
    with open(stub_path / "config.json", "w", encoding="utf-8") as f:
        json.dump({
            "stage": "dpo",
            "reference_model": dpo_cfg["reference_model_path"],
            "beta": dpo_cfg["beta"],
            "max_steps": dpo_cfg["max_steps"],
        }, f, indent=2)

    end = datetime.now(timezone.utc).isoformat()
    config_hash = hash_dict(cfg)

    write_stage_manifest(
        stage="dpo",
        config_hash=config_hash,
        dataset_hash="see_sft_manifest",
        base_model_hash="see_sft_manifest",
        hyperparameters={
            "max_steps": dpo_cfg["max_steps"],
            "learning_rate": dpo_cfg["learning_rate"],
            "beta": dpo_cfg["beta"],
            "effective_batch_size": dpo_cfg["per_device_train_batch_size"] *
                dpo_cfg["gradient_accumulation_steps"],
            "save_dir": dpo_cfg["save_dir"],
        },
        start_time=start,
        end_time=end,
        status="completed",
        notes="DPO stage complete. Stub artifacts — real run writes via TRL DPOTrainer.",
    )

    print(f"  Manifest written: {MANIFESTS_DIR / 'manifest_dpo.json'}")
    return {"status": "completed", "save_dir": dpo_cfg["save_dir"]}


# ---------------------------------------------------------------------------
# STAGE 3 — GRPO (THE CORE)
# ---------------------------------------------------------------------------

def run_grpo(cfg: Dict) -> Dict:
    """
    Stage 3: Group Relative Policy Optimization.
    The core training stage — R1-style, no separate critic model.
    In a real run, this calls TRL GRPOTrainer with the reward engine.
    Here we validate the reward config + emit manifest + stub.
    """
    start = datetime.now(timezone.utc).isoformat()
    print("\n" + "=" * 70)
    print("  STAGE 3 — GRPO (Group Relative Policy Optimization)")
    print("=" * 70)

    grpo_cfg = cfg["grpo"]
    dataset_cfg = cfg["dataset"]
    eval_cfg = cfg["eval"]

    print(f"  Policy base        : {grpo_cfg['policy_model_path']}")
    print(f"  Reference          : {grpo_cfg['reference_model_path']}")
    print(f"  Max steps          : {grpo_cfg['max_steps']}")
    print(f"  Group size (G)     : {grpo_cfg['group_size']}")
    print(f"  LR                 : {grpo_cfg['learning_rate']}")
    print(f"  KL beta            : {grpo_cfg['beta_kl']}")
    print(f"  Clip epsilon       : {grpo_cfg['clip_epsilon']}")
    print(f"  Entropy bonus      : {grpo_cfg['entropy_bonus']}")
    print(f"  Save dir           : {grpo_cfg['save_dir']}")
    print()
    print("  Reward functions enabled:")
    for r in grpo_cfg["rewards"]:
        w = grpo_cfg["reward_weights"].get(r, 0.0)
        print(f"    - {r:20s}  weight={w}")
    print()
    print("  Generation config (for rollouts):")
    gen = grpo_cfg["generation"]
    print(f"    temperature       : {gen['temperature']}")
    print(f"    top_p             : {gen['top_p']}")
    print(f"    top_k             : {gen['top_k']}")
    print(f"    max_new_tokens    : {gen['max_new_tokens']}")
    print(f"    eos_tokens        : {gen['eos_tokens']}")
    print()

    # Validate reward engine imports
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from grpo_reward_engine import compute_reward, DEFAULT_REWARD_WEIGHTS
        print("  [OK] Reward engine imports cleanly")
    except Exception as e:
        print(f"  [FAIL] Reward engine import failed: {e}")
        raise

    # Validate dataset + eval set exist
    dataset_path = Path(dataset_cfg["train_path"])
    eval_path = Path(eval_cfg["path"])
    if not dataset_path.exists():
        raise FileNotFoundError(f"Training dataset not found: {dataset_path}")
    if not eval_path.exists():
        print(f"  [WARN] Eval set not found at {eval_path} — build with: python grpo_eval.py --build-eval")
    else:
        print(f"  [OK] Eval set found: {eval_path}")

    # Baseline eval (before GRPO starts)
    print("\n  --- BASELINE EVAL (before GRPO) ---")
    if eval_path.exists():
        try:
            run_eval_hook(
                label="pre_grpo_baseline",
                eval_path=str(eval_path),
                generations_per_prompt=eval_cfg.get("generations_per_prompt", 4),
                weights=grpo_cfg["reward_weights"],
            )
        except Exception as e:
            print(f"  [WARN] Baseline eval failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("  [SKIP] No eval set — skipping baseline eval")

    # Simulate GRPO training loop
    print(f"\n  [SIM] Running GRPO for {grpo_cfg['max_steps']} steps "
          f"(G={grpo_cfg['group_size']}, beta_kl={grpo_cfg['beta_kl']})...")
    for step in range(0, grpo_cfg["max_steps"] + 1, grpo_cfg["save_steps"]):
        if step == 0:
            continue
        print(f"    Step {step:>4d} / {grpo_cfg['max_steps']}: "
              f"[SIM] composite_reward ~ {0.5 + 0.01 * step:.3f}")
        time.sleep(0.02)

    print("  [SIM] GRPO complete — saving artifacts to", grpo_cfg["save_dir"])

    GRPO_DIR.mkdir(parents=True, exist_ok=True)
    stub_path = GRPO_DIR / "last"
    stub_path.mkdir(parents=True, exist_ok=True)
    with open(stub_path / "config.json", "w", encoding="utf-8") as f:
        json.dump({
            "stage": "grpo",
            "policy_model": grpo_cfg["policy_model_path"],
            "reference_model": grpo_cfg["reference_model_path"],
            "group_size": grpo_cfg["group_size"],
            "beta_kl": grpo_cfg["beta_kl"],
            "max_steps": grpo_cfg["max_steps"],
            "rewards": grpo_cfg["rewards"],
            "reward_weights": grpo_cfg["reward_weights"],
        }, f, indent=2)
    with open(stub_path / "checkpoint.stub", "w", encoding="utf-8") as f:
        f.write("STUB — real GRPO checkpoint written by trainer\n")

    # Post-GRP0 eval
    print("\n  --- POST-GRPO EVAL (step {}) ---".format(grpo_cfg["max_steps"]))
    if eval_path.exists():
        try:
            run_eval_hook(
                label=f"post_grpo_step_{grpo_cfg['max_steps']}",
                eval_path=str(eval_path),
                generations_per_prompt=eval_cfg.get("generations_per_prompt", 4),
                weights=grpo_cfg["reward_weights"],
            )
        except Exception as e:
            print(f"  [WARN] Post-GRPO eval failed: {e}")

    end = datetime.now(timezone.utc).isoformat()
    config_hash = hash_dict(cfg)

    write_stage_manifest(
        stage="grpo",
        config_hash=config_hash,
        dataset_hash="see_sft_manifest",
        base_model_hash="see_sft_manifest",
        hyperparameters={
            "max_steps": grpo_cfg["max_steps"],
            "group_size": grpo_cfg["group_size"],
            "learning_rate": grpo_cfg["learning_rate"],
            "beta_kl": grpo_cfg["beta_kl"],
            "clip_epsilon": grpo_cfg["clip_epsilon"],
            "entropy_bonus": grpo_cfg["entropy_bonus"],
            "rewards": grpo_cfg["rewards"],
            "reward_weights": grpo_cfg["reward_weights"],
            "generation": grpo_cfg["generation"],
            "save_dir": grpo_cfg["save_dir"],
        },
        start_time=start,
        end_time=end,
        status="completed",
        notes="GRPO stage complete. Stub artifacts — real run writes via TRL GRPOTrainer.",
    )

    print(f"  Manifest written: {MANIFESTS_DIR / 'manifest_grpo.json'}")
    return {"status": "completed", "save_dir": grpo_cfg["save_dir"]}


# ---------------------------------------------------------------------------
# STAGE 4 — REJECTION SAMPLING + SFT
# ---------------------------------------------------------------------------

def run_rejection_sampling(cfg: Dict) -> Dict:
    """
    Stage 4: Rejection Sampling + SFT.
    After GRPO, collect best trajectories, retrain on high-quality reasoning.
    """
    start = datetime.now(timezone.utc).isoformat()
    print("\n" + "=" * 70)
    print("  STAGE 4 — Rejection Sampling + SFT")
    print("=" * 70)

    rs_cfg = cfg["rejection_sampling"]
    grpo_cfg = cfg["grpo"]

    print(f"  Generations/prompt : {rs_cfg['generations_per_prompt']}")
    print(f"  Keep top-K         : {rs_cfg['keep_top_k']}")
    print(f"  Keep bottom-K      : {rs_cfg['keep_bottom_k']}")
    print(f"  Mix with original  : {rs_cfg['mix_with_original']} "
          f"(ratio={rs_cfg['mix_ratio_original']})")
    print(f"  Fresh SFT steps    : {rs_cfg['sft_steps']}")
    print(f"  Save dir           : {rs_cfg['save_dir']}")
    print()

    print("  [SIM] Generating rollout completions per eval prompt...")
    time.sleep(0.2)
    print("  [SIM] Scoring + selecting top-K / bottom-K...")
    time.sleep(0.1)
    print("  [SIM] Retraining on curated dataset for {} steps...".format(rs_cfg['sft_steps']))
    time.sleep(0.3)
    print("  [SIM] Rejection+SFT complete — saving to", rs_cfg['save_dir'])

    REJECTION_SFT_DIR.mkdir(parents=True, exist_ok=True)
    stub_path = REJECTION_SFT_DIR / "last"
    stub_path.mkdir(parents=True, exist_ok=True)
    with open(stub_path / "config.json", "w", encoding="utf-8") as f:
        json.dump({
            "stage": "rejection_sft",
            "grpo_base": grpo_cfg["policy_model_path"],
            "generations_per_prompt": rs_cfg["generations_per_prompt"],
            "keep_top_k": rs_cfg["keep_top_k"],
            "keep_bottom_k": rs_cfg["keep_bottom_k"],
            "sft_steps": rs_cfg["sft_steps"],
        }, f, indent=2)

    end = datetime.now(timezone.utc).isoformat()
    config_hash = hash_dict(cfg)

    write_stage_manifest(
        stage="rejection_sft",
        config_hash=config_hash,
        dataset_hash="see_sft_manifest",
        base_model_hash="see_sft_manifest",
        hyperparameters={
            "generations_per_prompt": rs_cfg["generations_per_prompt"],
            "keep_top_k": rs_cfg["keep_top_k"],
            "keep_bottom_k": rs_cfg["keep_bottom_k"],
            "mix_with_original": rs_cfg["mix_with_original"],
            "mix_ratio_original": rs_cfg["mix_ratio_original"],
            "sft_steps": rs_cfg["sft_steps"],
            "sft_learning_rate": rs_cfg["sft_learning_rate"],
            "save_dir": rs_cfg["save_dir"],
        },
        start_time=start,
        end_time=end,
        status="completed",
        notes="Rejection sampling + SFT stage complete. Stub artifacts.",
    )

    print(f"  Manifest written: {MANIFESTS_DIR / 'manifest_rejection_sft.json'}")
    return {"status": "completed", "save_dir": rs_cfg["save_dir"]}


# ---------------------------------------------------------------------------
# STAGE 5 — QUANTIZE + DEPLOY
# ---------------------------------------------------------------------------

def run_deploy(cfg: Dict) -> Dict:
    """
    Stage 5: Merge LoRA into base, quantize to GGUF, emit deploy artifacts.
    """
    start = datetime.now(timezone.utc).isoformat()
    print("\n" + "=" * 70)
    print("  STAGE 5 — Quantize + Deploy")
    print("=" * 70)

    deploy_cfg = cfg["deploy"]

    print(f"  Merge LoRA         : {deploy_cfg['merge_lora']}")
    print(f"  Merged output      : {deploy_cfg['merged_output_dir']}")
    print(f"  Quant format       : {deploy_cfg['quantize']['format']}")
    print(f"  Target quant       : {deploy_cfg['quantize']['target_quant']}")
    print(f"  GGUF output        : {deploy_cfg['quantize']['output_dir']}")
    print(f"  Local runtime      : {deploy_cfg['local_runtime']['base_url']} "
          f"({deploy_cfg['local_runtime']['model_name']})")
    print()

    print("  [SIM] Merging LoRA adapter into base model...")
    time.sleep(0.2)
    print("  [SIM] Saving merged 16-bit model to", deploy_cfg["merged_output_dir"])
    time.sleep(0.1)

    MERGED_DIR.mkdir(parents=True, exist_ok=True)
    with open(MERGED_DIR / "merged_model.stub", "w", encoding="utf-8") as f:
        f.write("STUB — real merged 16-bit model written by merge script\n")

    print("  [SIM] Quantizing to GGUF {} ...".format(deploy_cfg["quantize"]["target_quant"]))
    time.sleep(0.2)
    print("  [SIM] Saving GGUF to", deploy_cfg["quantize"]["output_dir"])

    GGUF_DIR.mkdir(parents=True, exist_ok=True)
    q = deploy_cfg["quantize"]["target_quant"]
    with open(GGUF_DIR / f"bionic_daughter_qwen3_4b_{q.lower()}.stub", "w", encoding="utf-8") as f:
        f.write(f"STUB — real GGUF {q} written by llama-quantize\n")

    print("  [SIM] Local runtime config ready — Hermes points here after deploy:")
    lr = deploy_cfg["local_runtime"]
    print(f"    base_url: {lr['base_url']}")
    print(f"    model   : {lr['model_name']}")

    end = datetime.now(timezone.utc).isoformat()
    config_hash = hash_dict(cfg)

    write_stage_manifest(
        stage="deploy",
        config_hash=config_hash,
        dataset_hash="see_sft_manifest",
        base_model_hash="see_sft_manifest",
        hyperparameters={
            "merge_lora": deploy_cfg["merge_lora"],
            "merged_output_dir": deploy_cfg["merged_output_dir"],
            "quant_format": deploy_cfg["quantize"]["format"],
            "target_quant": deploy_cfg["quantize"]["target_quant"],
            "gguf_output_dir": deploy_cfg["quantize"]["output_dir"],
            "local_runtime": deploy_cfg["local_runtime"],
        },
        start_time=start,
        end_time=end,
        status="completed",
        notes="Deploy stage complete. Stub artifacts — real run writes merged + quantized models.",
    )

    print(f"  Manifest written: {MANIFESTS_DIR / 'manifest_deploy.json'}")
    return {"status": "completed"}


# ---------------------------------------------------------------------------
# MAIN — run the full pipeline
# ---------------------------------------------------------------------------

def run_full_pipeline(cfg_path: str = "grpo_training_config.yaml", stages: str = "all"):
    """
    Run the full 5-stage pipeline.
    stages: "all" | "sft" | "dpo" | "grpo" | "rejection" | "deploy" | comma-separated subset
    """
    cfg = load_config(cfg_path)
    print("\n" + "#" * 70)
    print("#  BIONIC DAUGHTER — GRPO TRAINING PIPELINE")
    print(f"#  Config   : {cfg_path}")
    print(f"#  Base     : {cfg['base_model']['name']}")
    print(f"#  Dataset  : {cfg['dataset']['train_path']}")
    print(f"#  Eval     : {cfg['eval']['path']}")
    print("#" * 70)

    # Validate dataset
    dataset_path = Path(cfg["dataset"]["train_path"])
    if not dataset_path.exists():
        print(f"\n[FATAL] Training dataset not found: {dataset_path}")
        print("Build it: run grpo_packager.py first (it reads the canonical OneDrive source).")
        sys.exit(1)
    print(f"\n[DATA] Training corpus: {dataset_path}  "
          f"({cfg['dataset'].get('format')}, {cfg['eval'].get('path', 'see eval section')} for eval)")

    # Validate eval set exists or offer to build it
    eval_path = Path(cfg["eval"]["path"])
    if not eval_path.exists():
        print(f"\n[DATA] Eval set not found: {eval_path}")
        print("Build it now? (y/n): ", end="")
        import sys as _sys
        if _sys.stdin.isatty():
            resp = input().strip().lower()
        else:
            print("auto-building eval set (non-interactive)...")
            resp = "y"
        if resp == "y":
            from grpo_eval import build_held_out_eval_set
            stats = build_held_out_eval_set(
                train_path=str(dataset_path),
                eval_path=str(eval_path),
                samples_per_domain=cfg["eval"].get("samples_per_domain", 10),
            )
            print(f"\n[OK] Eval set built: {stats['eval_records']} records across "
                  f"{len(stats['eval_domains'])} domains")
            print(f"     Training corpus now: {stats['train_records_after']} records (leak-free)")
        else:
            print("[SKIP] Eval set not built — eval hooks will be skipped.")
            cfg["eval"]["path"] = None

    # Stage selection
    if stages == "all":
        stage_order = ["sft", "dpo", "grpo", "rejection", "deploy"]
    else:
        stage_order = [s.strip() for s in stages.split(",")]

    stage_funcs = {
        "sft": run_sft,
        "dpo": run_dpo,
        "grpo": run_grpo,
        "rejection": run_rejection_sampling,
        "deploy": run_deploy,
    }

    results = {}
    for stage_name in stage_order:
        if stage_name not in stage_funcs:
            print(f"\n[SKIP] Unknown stage: {stage_name}")
            continue
        try:
            results[stage_name] = stage_funcs[stage_name](cfg)
        except Exception as e:
            print(f"\n[FAIL] Stage {stage_name} failed: {e}")
            import traceback
            traceback.print_exc()
            results[stage_name] = {"status": "failed", "error": str(e)}
            # Halt the pipeline on failure — don't run downstream stages with
            # missing artifacts.
            print(f"\n[HALT] Pipeline halted after failed stage: {stage_name}")
            break

    # Summary
    print("\n" + "=" * 70)
    print("  PIPELINE SUMMARY")
    print("=" * 70)
    for stage, result in results.items():
        status = result.get("status", "unknown")
        print(f"  {stage:15s}: {status}")
    print("=" * 70)

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Bionic Daughter GRPO Training Pipeline"
    )
    parser.add_argument(
        "--config", default="grpo_training_config.yaml",
        help="Path to training config YAML",
    )
    parser.add_argument(
        "--stages", default="all",
        help="Comma-separated stage subset: all,sft,dpo,grpo,rejection,deploy",
    )
    args = parser.parse_args()

    run_full_pipeline(cfg_path=args.config, stages=args.stages)
