#!/usr/bin/env python3
"""Google Colab GRPO Training Notebook — Ready to copy-paste into https://colab.research.google.com

If running as a script (not in Colab), use subprocess for installs.
In Colab, just copy each cell.
"""
import subprocess
import sys

def run_cell(code):
    """Execute a code cell (Colab-style)."""
    if code.startswith('!'):
        subprocess.run(code[1:], shell=True)
    else:
        exec(code)

# ===== CELL 1: Install Dependencies =====
def cell_1():
    subprocess.run([sys.executable, '-m', 'pip', 'install', 
                   'unsloth', 'trl', 'peft', 'datasets', 
                   'accelerate', 'bitsandbytes', 'huggingface_hub',
                   'transformers', 'torch'])

# ===== CELL 2: Download Model (NO HF TOKEN NEEDED) =====
def cell_2():
    from transformers import AutoModelForCausalLM
    model = AutoModelForCausalLM.from_pretrained(
        "Qwen/Qwen3-4B-Thinking-2507",
        device_map="auto",
        torch_dtype="auto"
    )
    return model

# ===== CELL 3: Prepare Dataset =====
def cell_3():
    from datasets import load_dataset
    ds = load_dataset("openai/gsm8k", "main", split="train[:100]")
    print(f"Dataset loaded: {len(ds)} samples")
    return ds

if __name__ == "__main__":
    cell_1()
    print("Dependencies installed")
