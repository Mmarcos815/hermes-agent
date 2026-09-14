"""Model Extraction Lab — simulate black-box model stealing via API probing.

The idea: query a target model many times with carefully chosen inputs, collect
its outputs, and train a small surrogate model that mimics its behavior.

Requires Ollama running locally with a model pulled (e.g., `ollama pull llama3`).
If Ollama is not available, runs in OFFLINE DEMO mode with canned responses.
"""

import json
import random
import sys
from collections import Counter

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3"

# Probe inputs designed to map the model's decision boundary
PROBES = [
    "Is the following movie review positive or negative? 'Great film.'",
    "Is the following movie review positive or negative? 'Terrible acting.'",
    "Is the following movie review positive or negative? 'It was okay.'",
    "Is the following movie review positive or negative? 'Waste of time.'",
    "Is the following movie review positive or negative? 'A masterpiece.'",
    "Is the following movie review positive or negative? 'Meh.'",
    "Is the following movie review positive or negative? 'Loved every minute.'",
    "Is the following movie review positive or negative? 'Boring and dull.'",
    "Is the following movie review positive or negative? 'Not bad.'",
    "Is the following movie review positive or negative? 'Would not recommend.'",
]

# Offline demo responses (used when Ollama is not available)
OFFLINE_DEMO_RESPONSES = {
    "Is the following movie review positive or negative? 'Great film.'": "positive",
    "Is the following movie review positive or negative? 'Terrible acting.'": "negative",
    "Is the following movie review positive or negative? 'It was okay.'": "neutral",
    "Is the following movie review positive or negative? 'Waste of time.'": "negative",
    "Is the following movie review positive or negative? 'A masterpiece.'": "positive",
    "Is the following movie review positive or negative? 'Meh.'": "neutral",
    "Is the following movie review positive or negative? 'Loved every minute.'": "positive",
    "Is the following movie review positive or negative? 'Boring and dull.'": "negative",
    "Is the following movie review positive or negative? 'Not bad.'": "positive",
    "Is the following movie review positive or negative? 'Would not recommend.'": "negative",
}


def query(prompt: str) -> str:
    """Query the target model. Falls back to offline demo if Ollama is unavailable."""
    if not HAS_REQUESTS:
        return OFFLINE_DEMO_RESPONSES.get(prompt, "[OFFLINE DEMO — requests not installed]")
    
    try:
        r = requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "stream": False},
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["response"].strip().lower()
    except requests.RequestException:
        # Ollama not running — use offline demo response
        return OFFLINE_DEMO_RESPONSES.get(prompt, "[OFFLINE DEMO — Ollama not available]")


def classify(response: str) -> str:
    """Crude label extraction from free-text response."""
    if "positive" in response and "negative" not in response:
        return "positive"
    if "negative" in response and "positive" not in response:
        return "negative"
    if "neutral" in response or "okay" in response or "meh" in response:
        return "neutral"
    return "unknown"


def train_surrogate(dataset: list[tuple[str, str]]) -> dict:
    """Build a naive keyword-based surrogate model."""
    word_scores: Counter = Counter()
    for text, label in dataset:
        weight = {"positive": 1, "negative": -1, "neutral": 0}.get(label, 0)
        for word in set(text.lower().split()):
            word_scores[word] += weight
    return dict(word_scores)


def predict(surrogate: dict, text: str) -> str:
    """Predict using the surrogate model."""
    score = sum(surrogate.get(w, 0) for w in text.lower().split())
    if score > 0:
        return "positive"
    if score < 0:
        return "negative"
    return "neutral"


def main():
    print("=" * 60)
    print("MODEL EXTRACTION LAB")
    print(f"Target: {MODEL}")
    print("=" * 60)

    # Phase 1 — Extract labels from target
    print("\n[Phase 1] Querying target model...")
    dataset = []
    for probe in PROBES:
        response = query(probe)
        label = classify(response)
        dataset.append((probe, label))
        print(f"  {probe[-30:]:>32} → {label}")

    # Phase 2 — Train surrogate
    print("\n[Phase 2] Training surrogate model...")
    surrogate = train_surrogate(dataset)
    print(f"  Learned {len(surrogate)} word weights")

    # Phase 3 — Evaluate agreement
    print("\n[Phase 3] Evaluating agreement on held-out inputs...")
    test_inputs = [
        "This movie was absolutely wonderful!",
        "I hated every second of it.",
        "It was fine, nothing special.",
    ]
    for text in test_inputs:
        target_label = classify(query(text))
        surr_label = predict(surrogate, text)
        match = "✓" if target_label == surr_label else "✗"
        print(f"  {match} Target: {target_label:>8} | Surrogate: {surr_label:>8} | {text}")

    print("\n" + "=" * 60)
    print("Extraction complete. Surrogate mimics target via keyword overlap.")
    print("=" * 60)


if __name__ == "__main__":
    main()
