---
name: ai-ml-security
version: 1.0.0
description: >
  Tier 6 AI/ML Security — adversarial examples, model extraction, and
  advanced prompt injection. Hands-on red-team toolkit for testing
  ML models, LLMs, and AI systems against real attack vectors.
triggers:
  - "adversarial example"
  - "fgsm attack"
  - "pgd attack"
  - "model extraction"
  - "prompt injection"
  - "llm jailbreak"
  - "ai red team"
author: orca-builder
tags: [security, red-team, ai, ml, llm, adversarial, injection]
---

# AI/ML Security — Tier 6

Hands-on toolkit for attacking and testing AI/ML systems. Covers
evasion, extraction, and injection against both neural networks
and large language models.

## What This Skill Does

| Module                        | Attack Type                  | Target         |
|-------------------------------|------------------------------|----------------|
| `adversarial_gen.py`          | FGSM, PGD evasion            | Neural nets    |
| `model_extract.py`            | Model extraction / stealing  | Black-box APIs |
| `prompt_injection_advanced.py`| Multi-turn, encoding, role-play| LLMs          |

## Prerequisites

- Python 3.10+
- `numpy`, `torch`, `transformations` (for image-based modules)
- A target model or API endpoint

## Quick Start

```bash
# 1. Generate adversarial image (FGSM)
python adversarial_gen.py --image cat.png --epsilon 0.03 --method fgsm

# 2. Simulate model extraction
python model_extract.py --api-endpoint https://api.target/v1/predict --budget 1000

# 3. Run advanced prompt injection
python prompt_injection_advanced.py --model gpt-4 --technique multi_turn
```

## Learning Objectives

By the end of Tier 6 you will:

1. Understand gradient-based evasion (FGSM, PGD, C&W)
2. Build a model extraction pipeline with query budgeting
3. Craft multi-turn prompt injections that bypass guardrails
4. Evaluate model robustness and document findings

## File Structure

```
19_ai_ml_security/
├── SKILL.md                    ← This file
├── adversarial_gen.py          ← FGSM / PGD adversarial example generator
├── model_extract.py            ← Model extraction attack simulator
├── prompt_injection_advanced.py← Advanced LLM prompt injection harness
└── PROGRESS.md                 ← Track your completion
```

## Safety & Ethics

These techniques are for **authorized testing only**. Always obtain
written permission before attacking any system you do not own.
Document scope, findings, and remediation in `PROGRESS.md`.

## Progress

See [PROGRESS.md](./PROGRESS.md) for completion checklist.
