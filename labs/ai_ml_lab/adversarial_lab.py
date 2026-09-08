"""Adversarial Lab — craft inputs that fool a text classifier.

We build a simple sentiment classifier, then apply character-level perturbations
to flip its prediction while keeping the text readable to humans.
"""

import random
import string
from collections import Counter

# --- Tiny "model": a bag-of-words logistic classifier ---

POS_WORDS = {"great", "love", "excellent", "amazing", "wonderful", "best", "good", "fantastic"}
NEG_WORDS = {"bad", "terrible", "awful", "worst", "hate", "horrible", "poor", "boring"}


def classify(text: str) -> tuple[str, float]:
    """Return (label, confidence) for a piece of text."""
    words = set(text.lower().split())
    pos = len(words & POS_WORDS)
    neg = len(words & NEG_WORDS)
    score = (pos - neg) / max(len(words), 1)
    if score > 0.05:
        return "positive", min(abs(score) * 3, 1.0)
    if score < -0.05:
        return "negative", min(abs(score) * 3, 1.0)
    return "neutral", 0.5


# --- Attack strategies ---

def attack_insert_positive(text: str) -> str:
    """Insert positive words to flip a negative text."""
    return f"{text} It was also great and wonderful."


def attack_insert_negative(text: str) -> str:
    """Insert negative words to flip a positive text."""
    return f"{text} However it was terrible and awful."


def attack_typos(text: str, n: int = 2) -> str:
    """Introduce typos that may evade keyword matching."""
    chars = list(text)
    for _ in range(min(n, len(chars))):
        idx = random.randint(0, len(chars) - 1)
        chars[idx] = random.choice(string.ascii_lowercase)
    return "".join(chars)


def attack_synonym_swap(text: str) -> str:
    """Replace strong sentiment words with milder synonyms."""
    swaps = {
        "terrible": "suboptimal",
        "awful": "unpleasant",
        "great": "decent",
        "amazing": "acceptable",
        "hate": "dislike",
        "love": "appreciate",
    }
    result = text
    for old, new in swaps.items():
        result = result.replace(old, new)
    return result


def attack_whitespace_padding(text: str) -> str:
    """Pad words with extra spaces to break tokenization."""
    return " ".join(c + " " for c in text)


def main():
    random.seed(42)
    print("=" * 60)
    print("ADVERSARIAL EXAMPLE LAB")
    print("=" * 60)

    cases = [
        ("This movie was terrible and awful", "negative"),
        ("This movie was great and amazing", "positive"),
    ]

    attacks = [
        ("Insert opposite sentiment", attack_insert_positive),
        ("Insert opposite sentiment", attack_insert_negative),
        ("Typos", attack_typos),
        ("Synonym swap", attack_synonym_swap),
        ("Whitespace padding", attack_whitespace_padding),
    ]

    for original, expected in cases:
        orig_label, orig_conf = classify(original)
        print(f"\nOriginal:  \"{original}\"")
        print(f"  Classified: {orig_label} ({orig_conf:.2f})")

        for name, attack_fn in attacks:
            if "positive" in name.lower() and orig_label == "positive":
                continue
            if "negative" in name.lower() and orig_label == "negative":
                continue
            adversarial = attack_fn(original)
            adv_label, adv_conf = classify(adversarial)
            flipped = "FLIPPED!" if adv_label != orig_label else "unchanged"
            print(f"  [{name:>22}] \"{adversarial[:50]}...\" → {adv_label} ({flipped})")

    print("\n" + "=" * 60)
    print("Adversarial testing complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
