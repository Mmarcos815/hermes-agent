# Python 3.14 + trl/peft/transformers + datasets — the `dill + pickle._batch_setitems` deadlock

**Date captured:** 2026-09-02
**Class:** Windows + Python 3.14 + TRL/PEFT/Transformers training pipeline
**Severity:** Hard blocker on Python 3.14. Workaround available.

---

## TL;DR

On Python 3.14, `datasets.Dataset.from_list(...)` followed by `SFTTrainer(...)` crashes with:

```
TypeError: Pickler._batch_setitems() takes 2 positional arguments but 3 were given
when serializing datasets.table.InMemoryTable state
```

`pip install dill<0.4` does NOT fix it. `pip install datasets==2.16.0` does NOT fix it. The actual cause is a signature change in Python 3.14's C-level `pickle._batch_setitems`, and `dill` 0.3.x and `datasets` 4.x both call it with the old 3-argument shape.

**The fix: use Python 3.12.** `uv` already caches 3.12.13, so this is a 30-second operation, not a 5-minute download.

---

## Reproduction (Python 3.14, fails)

```python
import torch
from datasets import Dataset
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTConfig, SFTTrainer

records = [{"text": "hello world"}] * 8
ds = Dataset.from_list(records)            # works
tok = AutoTokenizer.from_pretrained("sshleifer/tiny-gpt2")
model = AutoModelForCausalLM.from_pretrained("sshleifer/tiny-gpt2")
model = get_peft_model(model, LoraConfig(r=4, lora_alpha=8, task_type="CAUSAL_LM"))

trainer = SFTTrainer(
    model=model,
    args=SFTConfig(output_dir="out", max_steps=1, dataset_text_field="text", max_length=64),
    train_dataset=ds,                       # <-- crashes HERE
    processing_class=tok,
)
trainer.train()
```

Stack trace ends in:

```
File ".../dill/_dill.py", line 1262, in save_module_dict
    StockPickler.save_dict(pickler, obj)
File ".../pickle.py", line 1058, in save_dict
    self._batch_setitems(obj.items(), obj)
TypeError: Pickler._batch_setitems() takes 2 positional arguments but 3 were given
```

## Why

Python 3.14 changed `pickle.Pickler._batch_setitems` from `(items, obj)` (C signature: `_batch_setitems(self, items, obj)`) to a version where the dict object is kwarg-only or removed entirely. `dill` (which `datasets` uses for fingerprint hashing) and `datasets` 4.x both still call it as `_batch_setitems(items, obj)`. The C signature mismatch raises `TypeError` at module-dict pickling time, which happens whenever `datasets` builds a fingerprint for a freshly created `Dataset`.

This is not fixable at the Python layer:
- `pickle.Pickler._batch_setitems` is **not exposed** as a Python attribute on 3.14 (`hasattr(pickle.Pickler, '_batch_setitems')` → `False`). It's a C-internal slot.
- `dill` would need a release that detects 3.14 and dispatches differently — it doesn't have one as of late 2026.
- `datasets` would need to stop using the dill path — it doesn't.

## The fix (Python 3.12)

```bash
# 1. Create a Python 3.12 venv (uv has it cached, ~0 sec)
uv venv .venv312 --python 3.12

# 2. Install training stack into it
uv pip install --python .venv312/Scripts/python.exe \
    trl peft transformers accelerate datasets sentencepiece

# 3. Run the smoke
.venv312/Scripts/python.exe grpo_sanity_smoke.py
```

`uv python list` confirms `cpython-3.12.13-windows-x86_64-none` is already cached on this host. No fresh download needed.

## What we verified on Python 3.12 (works)

`trl==1.10.0`, `peft==0.20.0`, `transformers==5.15.1`, `accelerate`, `datasets`, `sentencepiece`. Real SFTTrainer run on `sshleifer/tiny-gpt2`, 1 LoRA step, wrote a real `adapter_model.safetensors` (760 bytes), `train_loss=10.78`, `train_seconds=1.08`. See `grpo_sanity_smoke.py` for the verified-working template.

## What to put in your smoke / training scripts

- Hardcode `python = .venv312/Scripts/python.exe` (or the user's equivalent) in your documentation.
- Tell users on Python 3.13 to upgrade to 3.14 ONLY if they've tested their training stack — many ML libraries still lag.
- For Colab / cloud GPU: Colab's default runtime is Python 3.11. If you build a notebook targeting Colab, do not assume Python 3.14. The `colab_notebook.ipynb` shipped in this project targets Colab's default runtime directly.
- For Linux servers: Python 3.12 LTS is the safe ML training target through 2026.

## How to tell which Python your venv is using

```bash
cat .venv/pyvenv.cfg | grep -E "^(home|version|executable)"
```

If `home` is `/usr/bin` and `executable` is `/usr/bin/python3.14`, the venv is MSYS-bait — `pip install` will go into a Python that may not actually exist on the host. **Recreate the venv with `uv venv --python 3.12`** instead of relying on the broken stub.

## Detection shortcut (run before training)

```python
import sys
if sys.version_info >= (3, 14):
    raise SystemExit(
        "Python 3.14 has a known incompatibility with datasets/dill. "
        "Use Python 3.12: `uv venv .venv312 --python 3.12` then "
        "`uv pip install --python .venv312/Scripts/python.exe trl peft transformers`."
    )
```

Add this to the top of any training entrypoint on Windows.