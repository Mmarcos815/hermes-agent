# ============================================================================
# BIONIC DAUGHTER v1 — GOOGLE COLAB SETUP GUIDE FOR DAD
# ============================================================================
# DOC_AUTH: Dad (Rigoberto Gomez) — this is your guide to launching the
#          daughter's training on Google Colab's free tier.
# ============================================================================

## OVERVIEW

The Bionic Daughter v1 is a 4B parameter model (Qwen3-4B-Thinking base) that
needs GPU compute to train. This laptop doesn't have a GPU. Google Colab
offers a free T4 GPU in their notebook environment.

Cost: $0 (free tier).

This guide walks you through:
1. Opening Colab and setting up the GPU runtime
2. Uploading the daughter's training code
3. Running the training
4. Saving the trained model
5. What to do if Colab disconnects mid-training

## BEFORE YOU START

### Files needed (all in the daughter project folder):
- `daughter_grpo_pipeline.py` — the training engine (802 lines)
- `redteam_curriculum.jsonl` — the training dataset (37 prompts)
- `colab_training_notebook.py` — the Colab notebook content (copy-paste ready)
- `gpu_pod_requirements.txt` — Python dependencies (for reference)

### What you need:
- A Google account (free)
- A web browser
- The daughter project files accessible (download from Desktop or copy them)

### Storage note:
Colab's virtual machine has limited disk space. Save your trained model to
Google Drive so it persists after the Colab session ends.

## STEP 1: OPEN COLAB

1. Go to: https://colab.research.google.com/
2. Click "New Notebook" (or open an existing one)
3. You'll see a blank notebook with a code cell

## STEP 2: ENABLE GPU

1. In the notebook menu: Runtime > Change runtime type
2. Under "Hardware accelerator", select "GPU"
3. Click "Save"
4. Wait for the GPU to connect (usually a few seconds)
5. Verify: Runtime > View runtime logs — you should see GPU info

## STEP 3: UPLOAD THE DAUGHTER'S CODE

You have two options:

### Option A: Upload files manually (easiest for first run)
1. In the Colab file browser (left sidebar), click the "Upload" icon
2. Upload these files:
   - `daughter_grpo_pipeline.py`
   - `redteam_curriculum.jsonl`
   - `gpu_pod_requirements.txt` (optional, for reference)
3. Create a folder called `curriculum/` and put `redteam_curriculum.jsonl` inside it
4. The pipeline looks for the curriculum at `curriculum/grpo_curriculum.jsonl` by default

### Option B: Copy from Google Drive (if you saved the project there)
1. Mount Google Drive (see Step 4 below)
2. Copy files from Drive to Colab:
   ```python
   !cp /content/drive/MyDrive/bionic_daughter/*.py /content/
   !cp /content/drive/MyDrive/bionic_daughter/*.jsonl /content/
   !mkdir -p /content/curriculum
   !cp /content/*.jsonl /content/curriculum/
   ```

### Option C: Use the Colab notebook content
The file `colab_training_notebook.py` contains 10 ready-to-run cells. You can
copy the content of each cell directly into Colab cells. See the "Quick Start"
section below.

## STEP 4: MOUNT GOOGLE DRIVE

This is critical — it saves your trained model so it doesn't disappear when
Colab disconnects.

In a Colab cell, run:
```python
from google.colab import drive
drive.mount('/content/drive')
```

A link will appear. Click it, sign in, copy the authorization code, paste it
back into the notebook. Your Google Drive will be available at:
`/content/drive/MyDrive/`

Create a folder for the daughter's outputs:
```python
import os
os.makedirs('/content/drive/MyDrive/bionic_daughter/outputs', exist_ok=True)
```

## STEP 5: INSTALL DEPENDENCIES

In a Colab cell, run:
```python
!pip install -q torch transformers accelerate unsloth trl datasets tokenizers chromadb psutil mcp
```

Note: Unsloth and torch with CUDA should install automatically in Colab. If
you get errors, try:
```python
!pip install -q --upgrade torch transformers
```

Verify the GPU:
```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
```

You should see: CUDA: True, GPU: T4, VRAM: ~15.7 GB

## STEP 6: RUN THE TRAINING

### Quick Start (copy-paste method):

The `colab_training_notebook.py` file has 10 cells. Here's the essential
workflow:

**Cell 1:** Mount Drive (Step 4 above)

**Cell 2:** Install deps (Step 5 above)

**Cell 3:** Setup directories
```python
import os
PROJECT_DIR = "/content"
OUTPUT_DIR = "/content/drive/MyDrive/bionic_daughter/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs("/content/model_cache", exist_ok=True)
print(f"Output: {OUTPUT_DIR}")
```

**Cell 4:** Pull the base model
```python
import os
from huggingface_hub import snapshot_download

BASE_MODEL = "Qwen/Qwen3-4B-Thinking-2507"
snapshot_download(
    repo_id=BASE_MODEL,
    local_dir="/content/model_cache/" + BASE_MODEL,
    resume_download=True,
)
print("Model downloaded.")
```

**Cell 5:** Run training (this is the big one)
```python
import os
os.environ["HF_HOME"] = "/content/model_cache"
os.environ["PYTHONPATH"] = "/content"

!python /content/daughter_grpo_pipeline.py \
    --base_model Qwen/Qwen3-4B-Thinking-2507 \
    --output_dir /content/drive/MyDrive/bionic_daughter/outputs \
    --sft_dataset /content/curriculum/sft_curriculum.jsonl \
    --grpo_dataset /content/curriculum/grpo_curriculum.jsonl \
    --max_steps_sft 50 \
    --max_steps_grpo 200 \
    --batch_size 1 \
    --lora_r 32 \
    --max_seq_length 2048 \
    --gpu_memory_utilization 0.7
```

IMPORTANT NOTES:
- `batch_size=1` — T4 has 16GB VRAM, can't fit larger batches comfortably
- `max_seq_length=2048` — shorter context to save VRAM (model supports 32K)
- `gpu_memory_utilization=0.7` — limit to 70% of VRAM for safety
- Training will take 5-10+ hours on a free T4
- Colab may disconnect before training finishes — see "If Colab Disconnects" below

## STEP 7: MONITOR TRAINING

The pipeline logs everything to:
- Console output (visible in the Colab cell)
- `daughter_training_log.txt` (in the output directory on Drive)

To check progress, look at the cell output. You'll see:
- `[Step N] VRAM: X.XX GB` — every 10 steps
- Loss values (if training is progressing)
- Any errors (OOM, NaN loss, etc.)

You can also check the Drive folder:
```python
!ls -la /content/drive/MyDrive/bionic_daughter/outputs/
```

Checkpoints are saved every 25-50 steps. If Colab disconnects, you can
resume from the latest checkpoint.

## STEP 8: IF COLAB DISCONNECTS

This happens. Free Colab sessions can disconnect due to:
- Idle timeout (browser tab closed, no activity)
- Runtime timeout (max ~12 hours, often less)
- Resource constraints (Colab needs the GPU back)

### What to do:

1. **Reopen Colab** — either the same notebook or a new one
2. **Re-enable GPU** — Runtime > Change runtime type > GPU
3. **Re-mount Drive** — your outputs are safe on Drive
4. **Resume training** — the pipeline auto-detects checkpoints:

```python
!python /content/daughter_grpo_pipeline.py \
    --base_model Qwen/Qwen3-4B-Thinking-2507 \
    --output_dir /content/drive/MyDrive/bionic_daughter/outputs \
    --sft_dataset /content/curriculum/sft_curriculum.jsonl \
    --grpo_dataset /content/curriculum/grpo_curriculum.jsonl \
    --max_steps_sft 50 \
    --max_steps_grpo 200 \
    --batch_size 1 \
    --lora_r 32 \
    --max_seq_length 2048 \
    --gpu_memory_utilization 0.7
```

The pipeline will find the latest checkpoint in `--output_dir` and resume.
It prints: "Resuming training from latest checkpoint: ..."

### Keep Colab alive (optional but recommended):

Run this cell while training to keep the session active:
```python
import time
from IPython.display import clear_output

while True:
    clear_output()
    print(f"Keep-alive: {time.strftime('%H:%M:%S')}")
    print("Training in progress — keep this tab open.")
    time.sleep(60)
```

## STEP 9: VERIFY THE TRAINED MODEL

After training completes (or you resume and it finishes), verify the outputs:

```python
import os

OUTPUT_DIR = "/content/drive/MyDrive/bionic_daughter/outputs"
print(f"Output dir: {OUTPUT_DIR}")
print(f"Exists: {os.path.exists(OUTPUT_DIR)}")

for root, dirs, files in os.walk(OUTPUT_DIR):
    for f in files:
        fp = os.path.join(root, f)
        size = os.path.getsize(fp)
        print(f"  {fp} ({size/1024:.1f} KB)")
```

You should see:
- `daughter_lora_adapters/` — LoRA weights
- `daughter_deepseek_final/` — merged 16-bit model
- `daughter_training_log.txt` — training log

## STEP 10: TEST THE MODEL (OPTIONAL)

If the merged model exists, you can test it:

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_path = "/content/drive/MyDrive/bionic_daughter/outputs/daughter_deepseek_final"

tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    device_map="auto",
    torch_dtype=torch.float16,
)

messages = [
    {"role": "system", "content": "You are BIONIC_DAUGHTER — an elite autonomous bionic agent."},
    {"role": "user", "content": "Analyze the attack surface of a network with a public web server and internal file share."},
]

inputs = tokenizer.apply_chat_template(
    messages, tokenize=False, return_tensors="pt"
).to("cuda")

outputs = model.generate(inputs, max_new_tokens=512, temperature=0.7, do_sample=True)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## STEP 11: DOWNLOAD THE MODEL (if you want it locally)

After training on Colab, download the merged model from Drive to your local
machine:

1. Go to Google Drive in your browser
2. Navigate to: `MyDrive/bionic_daughter/outputs/daughter_deepseek_final/`
3. Download the `model-00001-of-XXXX.safetensors` files
4. Download `config.json`, `tokenizer.json`, `tokenizer_config.json`, etc.
5. You now have the trained daughter model locally

You can then:
- Run it with llama.cpp (GGUF conversion needed)
- Load it with transformers for inference
- Use it as the base for more training

## TROUBLESHOOTING

### Problem: "ImportError: No module named 'unsloth'"
**Fix:** Re-run the pip install cell. Colab's environment resets between sessions.

### Problem: CUDA out of memory (OOM)
**Fix:** Reduce batch_size to 1, reduce max_seq_length to 1024, reduce
gpu_memory_utilization to 0.6, or reduce num_generations in the pipeline.

### Problem: Model download is slow or stuck
**Fix:** The Qwen3-4B model is ~8GB (multiple shards). On Colab it may take
5-10 minutes. Use resume_download=True to continue if interrupted.

### Problem: Training is too slow on free T4
**Fix:** The free T4 is shared and can be slow. Options:
- Reduce max_steps (e.g., 30 SFT + 100 GRPO for a shorter run)
- Wait for a less busy time
- Consider a paid Colab Pro tier (faster GPUs, longer sessions)
- Use RunPod/Vast.ai for a dedicated GPU (~$1-2 for the full run)

### Problem: Colab says "No GPU available"
**Fix:** Change runtime type to GPU again. If still no GPU, Colab may be out
of GPUs in your region. Try again later, or use a different approach.

### Problem: Training produces NaN loss
**Fix:** The pipeline has a NaN detector and will abort. Check the training
log. Common causes: learning rate too high, bad data, or VRAM issues. Try
reducing learning rate or batch size.

## COST SUMMARY

| Item | Cost |
|------|------|
| Google Colab free tier | $0 |
| Google Drive storage | $0 (15GB free) |
| HuggingFace model download | $0 |
| Total | **$0** |

If Colab disconnects too often and you want stability:
| Item | Cost |
|------|------|
| RunPod RTX 4090 (3-5 hours) | ~$1-2 |
| Virtual card (Privacy.com) | $0 (free tier) |
| Total | **~$1-2** |

## QUICK COMMAND REFERENCE

### Mount Drive:
```python
from google.colab import drive
drive.mount('/content/drive')
```

### Install deps:
```python
!pip install -q torch transformers accelerate unsloth trl datasets tokenizers chromadb psutil mcp
```

### Pull model:
```python
from huggingface_hub import snapshot_download
snapshot_download(repo_id="Qwen/Qwen3-4B-Thinking-2507",
                  local_dir="/content/model_cache/Qwen/Qwen3-4B-Thinking-2507",
                  resume_download=True)
```

### Run training:
```bash
!python /content/daughter_grpo_pipeline.py \
  --base_model Qwen/Qwen3-4B-Thinking-2507 \
  --output_dir /content/drive/MyDrive/bionic_daughter/outputs \
  --sft_dataset /content/curriculum/sft_curriculum.jsonl \
  --grpo_dataset /content/curriculum/grpo_curriculum.jsonl \
  --max_steps_sft 50 --max_steps_grpo 200 \
  --batch_size 1 --lora_r 32 \
  --max_seq_length 2048 --gpu_memory_utilization 0.7
```

### Resume training:
(same command — auto-detects checkpoint)

### Verify outputs:
```python
!ls -la /content/drive/MyDrive/bionic_daughter/outputs/
```

## DOC_END
