"""adversarial_gen.py — Generate adversarial examples via FGSM and PGD.

Simulates gradient-based evasion attacks against neural network
classifiers. No real model required — works with a surrogate
gradient function for educational demonstration.

Usage:
    python adversarial_gen.py --method fgsm --epsilon 0.03
    python adversarial_gen.py --method pgd --epsilon 0.03 --iterations 40
"""
from __future__ import annotations

import argparse
import numpy as np
from pathlib import Path


# ---------------------------------------------------------------------------
# Surrogate "model" — mimics a classifier's loss gradient for demonstration.
# Replace `surrogate_gradient()` with a real model's .backward() in practice.
# ---------------------------------------------------------------------------

def surrogate_gradient(image: np.ndarray) -> np.ndarray:
    """Return a fake gradient that pushes toward high-frequency noise.

    In production this is `loss.backward()` on a real model.
    Here we use the image Laplacian as a stand-in.
    """
    from scipy.ndimage import laplace
    return laplace(image.astype(np.float64))


def predict(image: np.ndarray) -> tuple[int, float]:
    """Fake prediction: class = mean pixel bucket, conf = sigmoid(mean)."""
    mean = image.mean() / 255.0
    confidence = 1.0 / (1.0 + np.exp(-10 * (mean - 0.5)))
    predicted_class = 1 if mean > 0.5 else 0
    return predicted_class, float(confidence)


# ---------------------------------------------------------------------------
# Attacks
# ---------------------------------------------------------------------------

def fgsm(image: np.ndarray, epsilon: float) -> np.ndarray:
    """Fast Gradient Sign Method (Goodfellow et al., 2014).

    x_adv = x + epsilon * sign(∇_x loss)
    """
    gradient = surrogate_gradient(image)
    perturbation = epsilon * np.sign(gradient)
    adversarial = np.clip(image.astype(np.float64) + perturbation, 0, 255)
    return adversarial.astype(np.uint8)


def pgd(image: np.ndarray, epsilon: float, alpha: float,
        iterations: int) -> np.ndarray:
    """Projected Gradient Descent (Madry et al., 2018).

    Iterative FGSM with projection back to the epsilon-ball around x.
    """
    original = image.astype(np.float64).copy()
    adversarial = original + np.random.uniform(-epsilon, epsilon, image.shape)
    adversarial = np.clip(adversarial, 0, 255)

    for _ in range(iterations):
        gradient = surrogate_gradient(adversarial)
        step = alpha * np.sign(gradient)
        adversarial = adversarial + step
        # Project onto epsilon-ball around original
        perturbation = adversarial - original
        perturbation = np.clip(perturbation, -epsilon, epsilon)
        adversarial = np.clip(original + perturbation, 0, 255)

    return adversarial.astype(np.uint8)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def report(original: np.ndarray, adversarial: np.ndarray,
           method: str, epsilon: float) -> None:
    """Print attack results."""
    orig_class, orig_conf = predict(original)
    adv_class, adv_conf = predict(adversarial)
    l_inf = np.max(np.abs(adversarial.astype(float) - original.astype(float)))
    l_2 = np.linalg.norm(adversarial.astype(float) - original.astype(float))

    print(f"\n{'='*55}")
    print(f"  Adversarial Attack Report — {method.upper()}")
    print(f"{'='*55}")
    print(f"  Epsilon (ε):        {epsilon}")
    print(f"  Original class:     {orig_class} (conf={orig_conf:.3f})")
    print(f"  Adversarial class:  {adv_class} (conf={adv_conf:.3f})")
    print(f"  L∞ perturbation:    {l_inf:.2f}")
    print(f"  L₂ perturbation:    {l_2:.2f}")
    print(f"  Attack success:     {'YES ✓' if orig_class != adv_class else 'NO ✗'}")
    print(f"{'='*55}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Adversarial example generator")
    parser.add_argument("--image", default=None, help="Input image path")
    parser.add_argument("--method", choices=["fgsm", "pgd"], default="fgsm")
    parser.add_argument("--epsilon", type=float, default=0.03,
                        help="Perturbation budget")
    parser.add_argument("--alpha", type=float, default=0.005,
                        help="PGD step size")
    parser.add_argument("--iterations", type=int, default=40,
                        help="PGD iterations")
    args = parser.parse_args()

    if args.image and Path(args.image).exists():
        from PIL import Image
        img = np.array(Image.open(args.image).convert("L"))
    else:
        # Demo: random 28x28 "image"
        img = np.random.randint(0, 256, size=(28, 28), dtype=np.uint8)
        print("[demo] Using random 28x28 image (no --image provided)")

    if args.method == "fgsm":
        adv = fgsm(img, args.epsilon)
    else:
        adv = pgd(img, args.epsilon, args.alpha, args.iterations)

    report(img, adv, args.method, args.epsilon)


if __name__ == "__main__":
    main()
