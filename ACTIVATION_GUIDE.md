# ⚡ Quick-Start Activation Guide
### Bionic Models + Hermes + Jarvis — Up and Running in 5 Minutes

> **For Dad.** No fluff. Copy-paste the blocks that match your setup.

---

## 1. Prerequisites

| What | Why | Already have? |
|------|-----|---------------|
| **Python 3.11+** | Everything here is Python | `python --version` |
| **Ollama** | Runs models locally | `ollama --version` |
| **GPU (optional but recommended)** | 8 GB+ VRAM for 7B/8B models | Check Task Manager → Performance → GPU |
| **RAM (no GPU)** | 16 GB+ for small models | Close Chrome tabs |

### Install Ollama (if you don't have it)

```powershell
# Windows (PowerShell)
winget run OLLAMA.OLLAMA

# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh
```

### Verify Python

```powershell
python --version
# Should say 3.11 or higher. If not: winget install Python.Python.3.11
```

---

## 2. Load Your First Model

### Step A — Pull a model

```powershell
# Small model (fast, good for testing, 1.5B params, ~1 GB VRAM)
ollama pull qwen2.5:1.5b

# OR medium model (better quality, 7B params, ~6 GB VRAM)
ollama pull qwen2.5:7b-instruct-q4_K_M
```

> **Tip:** The `:q4_K_M` suffix means "4-bit quantized" — smaller, faster, barely any quality loss. Always grab the quantized version for local use.

### Step B — Verify it works

```powershell
ollama run qwen2.5:1.5b "Say hello in one line"
```

If it talks back, you're good. Type `/bye` to exit.

### Step C — List installed models

```powershell
ollama list
```

---

## 3. First Test Prompts

Open an Ollama chat and try these (they confirm different capabilities):

```powershell
ollama run qwen2.5:1.5b
```

| Prompt | What it tests |
|--------|---------------|
| `Write a haiku about debugging` | Language / creativity |
| `What is 2^10 + 17? Show your work.` | Math / reasoning |
| `List 3 differences between Python lists and tuples` | Factual recall |
| `Read this logic: All cats hate water. Fluffy is a cat. What follows?` | Logical inference |

Exit with `/bye`.

---

## 4. Use with Hermes (the AI Agent)

### Install Hermes (first time only)

```powershell
iex (irm https://hermes-agent.nousresearch.com/install.ps1)
```

### Point Hermes at your local Ollama

```powershell
hermes model ollama-local
```

Or during setup:

```powershell
hermes setup
# → choose "Ollama" as provider
# → pick your model (e.g., qwen2.5:1.5b)
```

### Talk to Hermes

```powershell
hermes
```

Try inside Hermes:

```
/model ollama-local/qwen2.5:1.5b
> What tools do you have?
> Search the web for "latest AI news"
> Write a script that lists all files in this folder
```

### Key Hermes commands

| Command | Does |
|---------|------|
| `hermes` | Start interactive chat |
| `hermes model` | Switch model |
| `hermes gateway setup` | Connect Telegram/Discord |
| `hermes setup` | Full setup wizard |
| `hermes doctor` | Fix problems |

---

## 5. Use with Jarvis (local assistant)

### Run Jarvis

```powershell
cd "C:\Users\mobil\orca\projects\my 1st"
python jarvis\jarvis.py
```

### Run with a single command

```powershell
python jarvis\jarvis.py "Summarize today's news"
```

### Run in autonomous mode

```powershell
python jarvis\jarvis.py --auto "Research bionic implants and write a report"
```

### Jarvis config

Edit `jarvis\jarvis_config.json`:

```json
{
  "preferred_model": "meituan/longcat-2.0:free",
  "auto_mode": false,
  "voice_enabled": false,
  "safety_confirm": true
}
```

Change `"preferred_model"` to match your Ollama model name for local inference.

---

## 6. Cloud Deployment (RunPod / Modal / Colab)

### Option A — RunPod GPU pod (recommended for production)

```powershell
pip install runpod paramiko scp
set RUNPOD_API_KEY=rp_your_key_here
python cloud_deploy\activate_bionic_models.py
```

This will:
1. Spin up a GPU pod (RTX 4090 or A100)
2. Install Ollama on the pod
3. Upload your bionic models
4. Return an OpenAI-compatible API URL you can plug into Hermes

### Option B — Google Colab (free T4 GPU)

Open `cloud_deploy_colab.ipynb` in Colab and run all cells. You get a public URL at the end.

### Option C — Modal (pay-per-use)

```powershell
pip install modal
python cloud_deploy\modal_deploy.py
```

### Option D — Local cloud proxy

Run Ollama in the cloud, connect locally:

```powershell
python cloud_deploy\local_proxy.py --port 8080
# Now point Hermes at http://localhost:8080/v1
```

---

## 7. Troubleshooting

| Problem | Fix |
|---------|-----|
| `ollama: command not found` | Reinstall Ollama, then restart your terminal |
| `CUDA out of memory` | Use a smaller model (e.g., `qwen2.5:1.5b` instead of `7b`) |
| Hermes won't start | Run `hermes doctor` — it finds and fixes most issues |
| Hermes can't reach Ollama | Verify Ollama is running: `ollama serve` in a separate terminal |
| Model responds slowly | Quantize: pull the `:q4_K_M` variant. Or upgrade GPU. |
| `Permission denied` (Windows) | Run terminal as Administrator |
| Antivirus blocks `uv.exe` | Whitelist `%LOCALAPPDATA%\hermes\bin` (it's a false positive) |
| `RUNPOD_API_KEY not set` | Get key at runpod.io → Settings → API Keys → export it |
| Jarvis crashes on start | Check `jarvis\jarvis_config.json` is valid JSON |
| Model gibberish output | The model file may be corrupted — `ollama rm <model>` and re-pull |

---

## 8. Next Steps

1. **Try a bigger model** — once `1.5b` works, try `7b` or `14b` for much better reasoning
2. **Enable voice** — set `"voice_enabled": true` in jarvis_config.json
3. **Connect Telegram** — run `hermes gateway setup` and link your bot
4. **Fine-tune on your data** — check `GRPO_TRAINING_COLAB.md` for training your own bionic model
5. **Deploy to RunPod** — your agent runs 24/7 in the cloud, costs ~$0.40/hr idle
6. **Join the community** — [Nous Research Discord](https://discord.gg/NousResearch)

---

> **Quick recap:** Install Ollama → pull a model → verify with `ollama run` → install Hermes with `hermes setup` → chat. Done in 5 minutes.
