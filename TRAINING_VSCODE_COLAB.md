# BIONIC DAUGHTER — VS Code + Colab Training Guide

## Quick Start (5 minutes)

### Step 1: Install VS Code Colab Extension

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "Colab"
4. Install **Google Colab** extension (publisher: google.com)
5. Restart VS Code

### Step 2: Configure Colab Kernel

1. Open Command Palette (Ctrl+Shift+P)
2. Type "Colab: New Colab Server"
3. Select **TPU V4-8** or **T4 GPU** (free tier)
4. Wait for kernel to connect

### Step 3: Clone Training Data

```powershell
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
```

### Step 4: Open Training Notebook

1. Open `grpo_colab_vscode.ipynb` in VS Code
2. Click "Select Kernel" in top right
3. Choose "Google Colab" → Your server name
4. Run cells 1-11 sequentially

### Step 5: Monitor Training

Training takes ~2-3 hours on T4 GPU. Progress:
- 400 GRPO steps
- ~6 minutes per step (with 6 generations per prompt)
- Check logs every 50 steps

### Step 6: Download Model

After training completes:
1. Model saved to `/content/bionic-daughter-hacker`
2. Download via Google Drive or direct download
3. Load into Ollama: `ollama create bionic-daughter-hacker -f Modelfile`

---

## Training Configuration

| Parameter | Value |
|---|---|
| Base model | Qwen3-4B-Thinking-2507 |
| Dataset | 4,750 examples (33 domains) |
| LoRA rank | 64 |
| Batch size | 2 (x4 gradient accumulation) |
| Learning rate | 1e-5 |
| GRPO steps | 400 |
| Group size | 6 generations/prompt |
| Rewards | 8 hacker-style |
| Hardware | Free T4 GPU (16GB VRAM) |
| Estimated time | 2-3 hours |

---

## Reward Functions

| Reward | Weight | Purpose |
|---|---|---|
| format | 1.0 | Proper `<reasoning>` and `<solution>` tags |
| accuracy | 2.0 | Correct answers |
| reasoning_depth | 1.5 | Step-by-step analysis |
| creativity | 1.5 | Unconventional/lateral thinking |
| attack_chain | 1.5 | Realistic multi-step attacks |
| bypass_creativity | 1.0 | Defense evasion techniques |
| tool_use_quality | 1.0 | Proper tool selection and usage |
| self_correction | 1.5 | Catching and fixing own mistakes |

---

## Alternative: Google Colab Browser

If you prefer the browser-based Colab:

1. Open https://colab.research.google.com
2. Upload `grpo_colab_vscode.ipynb`
3. Select T4 GPU runtime
4. Run all cells

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Out of memory | Reduce batch_size to 1, max_seq_length to 1024 |
| Slow training | Use T4 not TPU; reduce max_completion_length |
| Kernel disconnects | Reconnect via VS Code Colab extension |
| Git clone fails | Download data manually from GitHub |

---

## After Training

1. **Evaluate:** `python evaluate_model.py --model bionic-daughter-hacker --use-persona`
2. **Deploy:** `python deploy_model.py --full`
3. **Use:** Chat via Ollama or Hermes
