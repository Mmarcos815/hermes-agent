# ============================================================================
# BIONIC DAUGHTER — COLAB DEPLOYMENT PACKAGE
# "THERES ALWAYS A WAY" — Everything needed to launch training on cloud GPU
#
# This package contains everything needed to train the Bionic Daughter model
# on Google Colab, RunPod, Modal, or any CUDA GPU environment.
#
# Contents (verified 2026-09-02):
#   1. colab_train.py                 — Portable single-file training entry point
#   2. grpo_reward_engine.py          — 6-component reward engine
#   3. grpo_eval.py                   — Held-out eval harness
#   4. grpo_training_config.yaml      — Full config (5-stage pipeline)
#   5. grpo_train_ready.jsonl         — 1,005 training records, 6 domains
#   6. grpo_eval_held_out.jsonl       — 60 eval prompts (held-out, never trained on)
#   7. grpo_meta.json                 — Corpus manifest (validated, all 6 domains)
#   8. grpo_packager.py               — Re-packages raw corpus if it ever drifts
#   9. grpo_sanity_smoke.py           — CPU-only smoke test (proves pipeline wires)
#  10. COLAB_SETUP.md                 — Setup instructions per platform
#  11. colab_notebook.ipynb           — Single-cell auto-install notebook
#  12. bionic-sovereign/              — Foundry contracts for integration tests
#
# Usage (3 ways):
#   A) Local CPU smoke test:  python grpo_sanity_smoke.py
#      (validates the pipeline wires — 1 LoRA step, ~1s on tiny-gpt2)
#   B) Cloud GPU:  python colab_train.py --config grpo_training_config.yaml
#      (full 5-stage SFT→DPO→GRPO→Rejection→Quantize on CUDA)
#   C) Colab one-click:  open colab_notebook.ipynb, paste HF_TOKEN if needed, Run All
# ============================================================================

# This is a marker file — the actual package is the set of files listed above.
# No code needed here; this documents the package contents.