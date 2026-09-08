#!/usr/bin/env python3
"""
=============================================================================
WAYFINDER: Autonomous GRPO Training System
"THERES ALWAYS A WAY" — Complete autonomous training without GPU or tokens
=============================================================================
"""

import os
import sys
from pathlib import Path

PROJECT_DIR = Path("C:/Users/mobil/orca/projects/my 1st")

def create_cpu_training_script():
    """Create a GRPO training script optimized for CPU."""
    
    script = '''#!/usr/bin/env python3
"""GRPO Training on CPU — No GPU Required"""

import os
import json
import time
from pathlib import Path

os.environ["CUDA_VISIBLE_DEVICES"] = ""

import torch
from torch.utils.data import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, TaskType
from trl import GRPOConfig, GRPOTrainer

torch.set_num_threads(os.cpu_count())

print("Loading model on CPU...")
model_name = str(Path(__file__).parent / "models/Qwen3-4B")

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float32,
    low_cpu_mem_usage=True,
    device_map="cpu",
)
tokenizer = AutoTokenizer.from_pretrained(model_name)

print("Applying LoRA...")
lora_config = LoraConfig(
    r=16, lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05, bias="none",
    task_type=TaskType.CAUSAL_LM,
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

print("Loading dataset...")
class GRPODataset(Dataset):
    def __init__(self, file_path, tokenizer, max_length=512):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.data = []
        with open(file_path) as f:
            for line in f:
                self.data.append(json.loads(line.strip()))
    def __len__(self):
        return len(self.data)
    def __getitem__(self, idx):
        item = self.data[idx]
        text = item["prompt"] + "\\n" + item["completion"] + "\\n"
        encoding = self.tokenizer(text, truncation=True, max_length=self.max_length, padding="max_length")
        return {"input_ids": encoding["input_ids"], "attention_mask": encoding["attention_mask"]}

dataset = GRPODataset(str(Path(__file__).parent / "grpo_train_ready.jsonl"), tokenizer)
print(f"Loaded {len(dataset)} examples")

training_args = GRPOConfig(
    output_dir=str(Path(__file__).parent / "artifacts/cpu_grpo"),
    num_train_epochs=1, per_device_train_batch_size=1,
    gradient_accumulation_steps=4, learning_rate=1e-5,
    warmup_ratio=0.03, lr_scheduler_type="cosine",
    logging_steps=5, save_steps=25, save_total_limit=2,
    bf16=False, fp16=False, beta=0.01,
    max_prompt_length=256, max_completion_length=256,
    report_to="none", gradient_checkpointing=True,
)

def format_reward(completions, **kwargs):
    return [1.0 if "<reasoning>" in c else 0.0 for c in completions]

def solution_reward(completions, **kwargs):
    return [1.0 if "<solution>" in c else 0.0 for c in completions]

print(f"Starting training on {os.cpu_count()} CPU threads...")
trainer = GRPOTrainer(
    model=model, processing_class=tokenizer,
    reward_funcs=[format_reward, solution_reward],
    args=training_args, train_dataset=dataset,
)

start = time.time()
trainer.train()
print(f"Training complete! Time: {(time.time()-start)/3600:.1f} hours")

output_dir = Path(__file__).parent / "artifacts/cpu_grpo"
model.save_pretrained(output_dir)
tokenizer.save_pretrained(output_dir)
print(f"Model saved to {output_dir}")
'''
    
    script_path = PROJECT_DIR / "cpu_grpo_train.py"
    with open(script_path, "w") as f:
        f.write(script)
    print(f"✅ CPU training script: {script_path}")


def create_gguf_converter():
    """Create GGUF converter script."""
    
    script = '''#!/usr/bin/env python3
"""Convert trained model to GGUF for CPU inference."""

import subprocess
from pathlib import Path

def convert_to_gguf(model_path, output_path):
    """Convert safetensors to GGUF."""
    model_path = Path(model_path)
    output_path = Path(output_path)
    
    # Download convert script if needed
    convert_script = Path("convert.py")
    if not convert_script.exists():
        subprocess.run(["wget", "-q", 
            "https://raw.githubusercontent.com/ggerganov/llama.cpp/master/convert.py"],
            check=True)
    
    subprocess.run(["python", str(convert_script), str(model_path),
        "--outtype", "f16", "--outfile", str(output_path)], check=True)
    print(f"Converted: {output_path}")

def quantize(gguf_path, output_path, method="Q4_K_M"):
    """Quantize GGUF model."""
    subprocess.run(["quantize", str(gguf_path), str(output_path), method], check=True)
    print(f"Quantized: {output_path}")

def inference(model_path, prompt):
    """Run CPU inference."""
    from llama_cpp import Llama
    llm = Llama(model_path=str(model_path), n_ctx=2048, n_threads=8)
    output = llm(prompt, max_tokens=512, temperature=0.7)
    return output["choices"][0]["text"]

if __name__ == "__main__":
    model = "C:/Users/mobil/orca/projects/my 1st/artifacts/cpu_grpo"
    gguf = "C:/Users/mobil/orca/projects/my 1st/artifacts/cpu_grpo.gguf"
    quant = "C:/Users/mobil/orca/projects/my 1st/artifacts/cpu_grpo_Q4.gguf"
    
    convert_to_gguf(model, gguf)
    quantize(gguf, quant)
    
    response = inference(quant, "Explain BOLA attack security reasoning:")
    print(f"Response: {response}")
'''
    
    script_path = PROJECT_DIR / "gguf_converter.py"
    with open(script_path, "w") as f:
        f.write(script)
    print(f"✅ GGUF converter: {script_path}")


def create_kaggle_notebook():
    """Create Kaggle notebook for training."""
    
    cells = [
        ("code", "!pip install -q unsloth trl peft datasets"),
        ("code", 'import os\nos.system("git lfs install")\nos.system("git clone https://huggingface.co/Qwen/Qwen3-4B-Thinking-2507 /kaggle/working/model")'),
        ("code", 'from datasets import Dataset\nimport json\ndata = [json.loads(l) for l in open("/kaggle/input/bionic-data/grpo_train_ready.jsonl")]\ndataset = Dataset.from_list(data)\nprint(f"Loaded {len(dataset)} examples")'),
        ("code", 'from unsloth import FastLanguageModel\nimport torch\nmodel, tokenizer = FastLanguageModel.from_pretrained("/kaggle/working/model", max_seq_length=1024, load_in_4bit=True, dtype=torch.bfloat16)\nmodel = FastLanguageModel.get_peft_model(model, r=64, lora_alpha=128, target_modules=["q_proj","k_proj","v_proj","o_proj"], lora_dropout=0.05, bias="none", use_gradient_checkpointing="unsloth")'),
        ("code", 'from trl import GRPOConfig, GRPOTrainer\ntraining_args = GRPOConfig(output_dir="/kaggle/working/output", num_train_epochs=3, per_device_train_batch_size=4, gradient_accumulation_steps=4, learning_rate=1e-5, warmup_ratio=0.03, lr_scheduler_type="cosine", logging_steps=10, save_steps=50, bf16=True, beta=0.01, max_prompt_length=512, max_completion_length=512, report_to="none")\ndef format_reward(completions, **kwargs):\n    return [1.0 if "<reasoning>" in c else 0.0 for c in completions]\ndef solution_reward(completions, **kwargs):\n    return [1.0 if "<solution>" in c else 0.0 for c in completions]\ntrainer = GRPOTrainer(model=model, processing_class=tokenizer, reward_funcs=[format_reward, solution_reward], args=training_args, train_dataset=dataset)\ntrainer.train()\nmodel.save_pretrained("/kaggle/working/output")'),
    ]
    
    notebook = {
        "metadata": {
            "title": "Bionic Daughter GRPO",
            "language": "python",
            "kernel_type": "notebook",
            "enable_gpu": True,
        },
        "cells": [{"cell_type": ct, "metadata": {}, "source": src, "execution_count": None, "outputs": []} for ct, src in cells],
        "nbformat": 4,
        "nbformat_minor": 4,
    }
    
    import json
    script_path = PROJECT_DIR / "kaggle_notebook.ipynb"
    with open(script_path, "w") as f:
        json.dump(notebook, f, indent=2)
    print(f"✅ Kaggle notebook: {script_path}")


def main():
    print("=" * 50)
    print("  WAYFINDER: Creating All Training Paths")
    print("  THERES ALWAYS A WAY")
    print("=" * 50)
    print()
    
    create_cpu_training_script()
    create_gguf_converter()
    create_kaggle_notebook()
    
    print()
    print("=" * 50)
    print("  ALL PATHS CREATED")
    print("=" * 50)
    print()
    print("USAGE:")
    print("  python cpu_grpo_train.py        # Train on CPU (slow)")
    print("  Upload to Google Colab          # Free T4 GPU")
    print("  Upload kaggle_notebook.ipynb    # Free P100 GPU")
    print("  python gguf_converter.py        # Convert to CPU format")
    print()
    print("THERES ALWAYS A WAY")


if __name__ == "__main__":
    main()
