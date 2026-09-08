# ============================================================================
# BIONIC DAUGHTER — COLAB SETUP GUIDE
# "THERES ALWAYS A WAY" — Run GRPO training on Google Colab
#
# PREREQUISITES:
#   - Google account (for Colab access)
#   - Hugging Face account + token (for Qwen3-4B download, if gated)
#   - The training package files (see COLAB_PACKAGE_INDEX.md)
#
# ============================================================================
# QUICKSTART — ONE-CELL NOTEBOOK (preferred path, recommended)
# ============================================================================
#
# 1. Open `colab_notebook.ipynb` in Google Colab (File -> Upload Notebook)
# 2. Set runtime: Runtime -> Change runtime type -> T4 GPU
# 3. Cell 1: paste your HF_TOKEN if Qwen3-4B-Thinking is gated
#    (leave blank if not gated -- it isn't as of Sept 2026)
# 4. Cell 1: set RUN_FULL_GRPO = True for the real 6-hour run
#    (or False for a 30-minute smoke that still produces a model)
# 5. Run All. Walk away. Come back to a trained GGUF + manifest bundle.
# 6. Download `/content/bionic-daughter-artifacts.zip` -> drop GGUF into
#    ~/.hermes/runtime/ollama/ -> `ollama create bionic-daughter-qwen3-4b-trained`
#
# The notebook handles: dep install, package pull, sanity smoke,
# QLoRA-tuned config write, full 5-stage run, GGUF quantize, Modelfile
# write, and zip bundling. One cell per stage, all chained.
#
# ============================================================================
# STEP 1: UPLOAD FILES TO COLAB (manual path)
# ============================================================================
#
# In Colab, upload these files to the working directory:
#
#   Required files:
#     - colab_train.py              (this package's training entry point)
#     - grpo_reward_engine.py       (reward functions)
#     - grpo_eval.py                (eval harness)
#     - grpo_training_config.yaml   (config)
#     - grpo_train_ready.jsonl      (1,005 training records, 6 domains)
#     - grpo_eval_held_out.jsonl    (60 eval prompts)
#     - grpo_meta.json              (corpus manifest)
#     - grpo_sanity_smoke.py        (CPU smoke test, validates pipeline wires)
#
#   Optional:
#     - bionic-sovereign/          (if you want Foundry verification hooks)
#
# Upload methods:
#   a) Colab file browser: click the folder icon -> Upload
#   b) Google Drive mount:
#        from google.colab import drive
#        drive.mount('/content/drive')
#      Then copy files from Drive to working dir.
#   c) Direct from GitHub (if repo is public):
#        !git clone <repo-url>
#        %cd <repo-dir>
#
# ============================================================================
# STEP 2: SET UP HUGGING FACE TOKEN
# ============================================================================
#
# If Qwen3-4B-Thinking-2507 requires authentication:
#
#   Option A -- Colab secrets (recommended):
#     1. Click the "Secrets" icon (key icon) in Colab sidebar
#     2. Add a secret named HF_TOKEN with your Hugging Face token
#     3. Enable "Notebook access"
#
#   Option B -- Environment variable:
#     import os
#     os.environ["HF_TOKEN"] = "your_token_here"
#
#   Get a token at: https://huggingface.co/settings/tokens
#   Needs "read" permission at minimum.
#
# ============================================================================
# STEP 3: VERIFY GPU AVAILABILITY
# ============================================================================
#
# Run this in a cell:
#
#   import torch
#   print("CUDA available:", torch.cuda.is_available())
#
# If False: Runtime -> Change runtime type -> T4 GPU (free) or A100 (paid).
#
# T4 has 16GB VRAM. Qwen3-4B in 4-bit (QLoRA) fits comfortably at batch 2.
# Use the colab-tuned config written by Cell 5 of the notebook:
#   grpo_training_config_colab.yaml
#
# ============================================================================
# STEP 4: LAUNCH TRAINING
# ============================================================================
#
#   !python colab_train.py --config grpo_training_config.yaml
#
# Wall time estimates on T4 free tier:
#   SFT (50 steps):   ~20 min
#   DPO (30 steps):   ~25 min
#   GRPO (200 steps): ~5 hours  (the bottleneck)
#   Rejection + SFT:  ~30 min
#   Merge + GGUF:     ~5 min
#   -------------------------------
#   TOTAL:            ~6 hours
#
# For a smoke run (RUN_FULL_GRPO=False), total is ~30 min and still
# produces a deployable adapter.
#
# ============================================================================
# STEP 5: COLLECT + DOWNLOAD OUTPUTS
# ============================================================================
#
# Artifacts live in `artifacts/` under the working dir. Copy to Drive:
#
#   !cp -r artifacts /content/drive/MyDrive/bionic-daughter-training/
#
# Or download individually:
#
#   from google.colab import files
#   files.download("artifacts/manifests/run_XXXX.json")
#
# TIP: For long runs, use Colab's "Save a copy in Drive" feature
#      to preserve the environment in case of disconnection.
#
# ============================================================================
# STEP 6: BRING GGUF BACK TO YOUR BOX
# ============================================================================
#
# 1. From the notebook artifacts, download:
#      artifacts/gguf/bionic-daughter-qwen3-4b-trained.Q4_K_M.gguf
#      artifacts/gguf/Modelfile
# 2. On the Windows box:
#      mkdir ~/.hermes/runtime/ollama/bionic-daughter-qwen3-4b-trained/
#      cp *.gguf Modelfile ~/.hermes/runtime/ollama/bionic-daughter-qwen3-4b-trained/
#      cd ~/.hermes/runtime/ollama/bionic-daughter-qwen3-4b-trained/
#      ollama create bionic-daughter-qwen3-4b-trained -f Modelfile
# 3. Verify:
#      ollama list
#      ollama run bionic-daughter-qwen3-4b-trained "Hello"
# 4. Wire into Hermes:
#      Add to ~/.hermes/config.yaml under model:
#        model:
#          provider: ollama
#          name: bionic-daughter-qwen3-4b-trained
#
# ============================================================================
# PLATFORM ALTERNATIVES
# ============================================================================
#
# RunPod (paid, faster):
#   1. Spin up a pod with H100 or A100 (80GB VRAM ideal for 4B)
#   2. SSH in, git clone the repo
#   3. Same commands as Colab, but use the full (non-colab-tuned) config
#
# Modal (paid, serverless):
#   modal_training.py in the project root provides a ready wrapper.
#   Set MODAL_TOKEN_ID + MODAL_TOKEN_SECRET, then:
#     modal run modal_training.py
#
# Local with HF model on disk (if you already have Qwen3-4B-Thinking cached):
#   - Use grpo_train.py directly (the local 5-stage runner)
#   - GPU required; CPU training is a 1000x slowdown
#
# ============================================================================
# VERIFICATION CHECKLIST
# ============================================================================
#
# After a successful run you should see:
#   - artifacts/sft/last/adapter_model.safetensors   (~1-10 MB)
#   - artifacts/dpo/last/adapter_model.safetensors   (~1-10 MB)
#   - artifacts/grpo/last/adapter_model.safetensors  (~1-10 MB)
#   - artifacts/merged_16bit/*.safetensors           (~8 GB for bf16)
#   - artifacts/gguf/bionic-daughter_qwen3_4b_q4_k_m.gguf  (~2-3 GB)
#   - artifacts/manifests/manifest_*.json            (5 files)
#   - artifacts/evals/eval_*.json                    (one per stage)
#
# If any are missing, the corresponding stage stubbed. See grpo_train.py
# for the failure mode of each stage.
# ============================================================================