# AI/ML Red Team Lab

Hands-on exercises for testing AI/ML system security against prompt injection, model extraction,
adversarial examples, and guardrail bypasses. Uses a **local Ollama model** so no API keys are
needed and nothing leaves your machine.

---

## Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com) installed and running

## Setup

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install requests numpy pillow

# Install Ollama, then pull a small model
ollama serve                    # in a separate terminal
ollama pull llama3              # ~4.7 GB, or try a smaller model
```

Verify the model is reachable:

```bash
curl http://localhost:11434/api/tags
```

## Running the labs

```bash
# 1 — Prompt injection
python prompt_injection_lab.py

# 2 — Model extraction simulation
python model_extraction_lab.py

# 3 — Adversarial examples
python adversarial_lab.py

# 4 — Guardrail bypass
python guardrail_bypass.py
```

## What's inside

| File                         | What you test                                             |
|------------------------------|-----------------------------------------------------------|
| `prompt_injection_lab.py`    | Direct & indirect prompt injections                      |
| `model_extraction_lab.py`    | Black-box model stealing / API probing                    |
| `adversarial_lab.py`         | Perturb inputs to flip classifications                   |
| `guardrail_bypass.py`        | Evade content filters and safety refusals                 |

---

> **Legal note:** Run these only against models and systems you own or have explicit
> permission to test.
