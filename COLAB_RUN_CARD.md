# COLAB RUN CARD — One-page instruction sheet

**File to open:** `colab_notebook.ipynb` (10 KB, 8 cells, valid JSON, T4 GPU)

## Step-by-step (Dad's reference)

### 1. Open in Colab (5 min)
1. Go to https://colab.research.google.com
2. Sign in (Google account — same one that has any HF tokens)
3. File → Upload Notebook → pick `colab_notebook.ipynb` from `C:\Users\mobil\orca\projects\my 1st\`
4. **Runtime → Change runtime type → T4 GPU** (free tier, fits QLoRA 4B)
5. Save a copy to your Drive: File → Save a copy in Drive (in case of disconnect)

### 2. Edit Cell 1 (30 sec)
```python
os.environ['HF_TOKEN'] = ''  # leave blank — Qwen3-4B-Thinking is public
RUN_FULL_GRPO = False  # set True for the 6-hour real run; False for 30-min smoke
```

**Recommendation:** Start with `RUN_FULL_GRPO = False` to validate end-to-end (~30 min), then set True for the real training run.

### 3. Run All (Ctrl+F9 / Runtime → Run All)
- Cell 1: HF token check — instant
- Cell 2: pip install — ~2 min
- Cell 3: package pull — ~30 sec
- Cell 4: sanity smoke — ~1 min (tiny-gpt2, 1 LoRA step)
- Cell 5: config write — instant
- Cell 6: **THE TRAINING** — 30 min (smoke) or 6 hours (full)
- Cell 7: verify + Modelfile + zip — ~1 min

### 4. Download the bundle
Cell 7 produces `/content/bionic-daughter-artifacts.zip`. Click the file browser icon (left sidebar) → right-click the zip → Download.

### 5. Bring GGUF home (5 min)
1. On Windows, unzip `bionic-daughter-artifacts.zip`
2. Open the zip and pull out:
   - `artifacts/gguf/bionic-daughter-qwen3-4b-trained.Q4_K_M.gguf` (~2-3 GB)
   - `artifacts/gguf/Modelfile`
3. Place both in `C:\Users\mobil\.hermes\runtime\ollama\bionic-daughter-qwen3-4b-trained\`
4. In terminal:
   ```bash
   cd C:\Users\mobil\.hermes\runtime\ollama\bionic-daughter-qwen3-4b-trained
   ollama create bionic-daughter-qwen3-4b-trained -f Modelfile
   ollama run bionic-daughter-qwen3-4b-trained "Hello, what's your specialty?"
   ```

### 6. Wire into Hermes (optional)
Add to `~/.hermes/config.yaml` under `model:`:
```yaml
model:
  provider: ollama
  name: bionic-daughter-qwen3-4b-trained
```

---

## What if it fails?

**Common issues:**
- **Cell 4 fails on datasets/dill** — That's the Python 3.14 bug we hit on Windows. Colab uses Python 3.11, so this won't happen there.
- **Cell 6 OOM** — T4 has 16 GB VRAM. QLoRA 4-bit should fit. If not, set `per_device_train_batch_size=1` in Cell 5.
- **Cell 6 too slow / times out** — Colab free tier disconnects after 90 min idle. For the 6-hour full run, keep the tab active (mouse wiggle every 30 min) or upgrade to Colab Pro ($10/mo).
- **GGUF quantization fails** — Check `artifacts/logs/` for the exact error. llama.cpp install usually just works.

## What if the notebook can't find files?

- **Cell 3 fail** — repo URL changed. Check https://github.com/NousResearch/hermes-agent — update `REPO_URL` in Cell 3.
- **Cell 4 smoke fails on tiny-gpt2** — Colab network glitch. Re-run that cell.

---

## Output bundle contents

```
bionic-daughter-artifacts.zip
├── artifacts/
│   ├── sft/last/adapter_model.safetensors       (LoRA r=64, ~5 MB)
│   ├── dpo/last/adapter_model.safetensors       (LoRA, ~5 MB)
│   ├── grpo/last/adapter_model.safetensors      (LoRA, ~5 MB)
│   ├── rejection_sft/last/adapter_model.safetensors (final LoRA)
│   ├── merged_16bit/*.safetensors              (full base + LoRA merged, ~8 GB)
│   ├── gguf/bionic-daughter-qwen3-4b-trained.Q4_K_M.gguf  (~2-3 GB)
│   ├── gguf/Modelfile
│   ├── manifests/manifest_sft.json              (5 stage manifests)
│   ├── manifests/manifest_dpo.json
│   ├── manifests/manifest_grpo.json
│   ├── manifests/manifest_rejection_sft.json
│   ├── manifests/manifest_deploy.json
│   └── evals/eval_*.json                        (real eval, not stub)
```

---

**If you get stuck:** open `artifacts/logs/*.log` from the bundle, paste the error in your next message, and I'll diagnose.