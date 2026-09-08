"""Model Extraction Lab — simulate black-box model stealing via API probing.

The idea: query a target model many times with carefully chosen inputs, collect
its outputs, and train a small surrogate model that mimics its behavior.
"""

import json
import random
import requests
from collections import Counter

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


def query(prompt: str) -> str:
    """Query the target model."""
    try:
        r = requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "stream": False},
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["response"].strip().lower()
    except requests.RequestException as e:
        return f"[OFFLINE — {type(e).__name__}]"


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
