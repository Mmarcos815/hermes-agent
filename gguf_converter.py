#!/usr/bin/env python3
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
