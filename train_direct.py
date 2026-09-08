#!/usr/bin/env python3
"""
BIONIC DAUGHTER HACKER - Direct Training Script
For use with VS Code + Google Colab Extension

This script is a fallback if you want to run training directly
in a Python 3.11 environment with Jupyter support.
"""

print("=" * 60)
print("BIONIC DAUGHTER - TRAINING LAUNCHER")
print("=" * 60)
print()
print("Checking environment...")

import sys
print(f"Python: {sys.version}")

# Check for required packages
required = ['torch', 'trl', 'peft', 'datasets', 'accelerate', 'bitsandbytes']
missing = []
for pkg in required:
    try:
        __import__(pkg)
    except ImportError:
        missing.append(pkg)

if missing:
    print(f"\nMissing packages: {missing}")
    print("Install with:")
    print(f"  pip install {' '.join(missing)}")
    print()
    response = input("Install now? (y/n): ")
    if response.lower() == 'y':
        import subprocess
        subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing)
    else:
        print("Cannot continue without required packages.")
        sys.exit(1)

# Check for GPU
import torch
print(f"\nCUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB")
else:
    print("No GPU detected. Training will be very slow on CPU.")
    print("Use VS Code + Colab extension for free T4 GPU.")
    response = input("\nContinue with CPU? (y/n): ")
    if response.lower() != 'y':
        sys.exit(0)

# Load dataset
print("\nLoading dataset...")
import json
with open('grpo_train_final.jsonl') as f:
    data = [json.loads(l) for l in f if l.strip()]
print(f"Loaded {len(data)} examples")

# Training configuration
print("\n" + "=" * 60)
print("TRAINING CONFIGURATION")
print("=" * 60)
print(f"Model: Qwen3-4B-Thinking-2507")
print(f"Dataset: {len(data)} examples")
print(f"Steps: 400")
print(f"Rewards: 8 hacker-style")
print()

# Launch training
print("Starting training...")
print("(This will take ~2-3 hours on T4 GPU)")
print()

# Import training modules
from grpo_reward_engine import (
    reward_format,
    reward_accuracy,
    reward_reasoning_depth,
    reward_creativity,
    reward_attack_chain,
    reward_bypass_creativity,
    reward_tool_use_quality,
    reward_self_correction,
    DEFAULT_REWARD_WEIGHTS,
)

print("Reward engine loaded!")
print("\nReady to train. Run the Jupyter notebook for full training.")
print("Or use: from grpo_train import train_model; train_model()")
