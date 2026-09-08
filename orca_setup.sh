#!/bin/bash
# BIONIC DAUGHTER - Orca ADE Training Script
# Run this in Orca ADE terminal to set up and start training

echo "============================================"
echo "BIONIC DAUGHTER - Orca ADE Setup"
echo "============================================"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python: $PYTHON_VERSION"

# Check for GPU
GPU_CHECK=$(python3 -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')" 2>/dev/null || echo "torch not installed")

if [[ "$GPU_CHECK" == *"torch not installed"* ]]; then
    echo "Installing PyTorch..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
fi

# Install dependencies
echo "Installing training dependencies..."
pip install unsloth trl peft datasets accelerate bitsandbytes jsonlines

# Clone repo
echo "Cloning training data..."
git clone https://github.com/NousResearch/hermes-agent.git /tmp/bionic-repo 2>/dev/null || true
cp /tmp/bionic-repo/grpo_train_final.jsonl /tmp/data.jsonl 2>/dev/null || true
cp /tmp/bionic-repo/grpo_reward_engine.py /tmp/reward_engine.py 2>/dev/null || true

# Check GPU again
python3 -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'VRAM: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB')
else:
    print('No GPU detected. Use Google Colab Extension in VS Code.')
"

echo ""
echo "Ready to train! Open VS Code, install Google Colab extension, and run:"
echo "  python3 -c \"import torch; print(f'CUDA: {torch.cuda.isavailable()}')\""
echo "  jupyter notebook grpo_colab_vscode.ipynb"
echo ""
echo "Or use the Colab extension to connect to free T4 GPU."
