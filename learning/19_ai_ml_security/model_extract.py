"""model_extract.py — Simulate a model extraction (stealing) attack.

A model extraction attack queries a black-box API many times with
carefully chosen inputs, then trains a surrogate model on the
(input, output) pairs to replicate the target's behavior.

This is an educational simulation — no real API is called.

Usage:
    python model_extract.py --budget 1000 --api-endpoint https://example.com/predict
    python model_extract.py --budget 5000 --strategy decision_boundary
"""
from __future__ import annotations

import argparse
import numpy as np
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Simulated target model (the "victim")
# ---------------------------------------------------------------------------

class VictimModel:
    """A secret classifier we're trying to steal.

    In reality this is behind an API — we only see predictions.
    """
    def __init__(self, n_features: int = 10, seed: int = 42) -> None:
        rng = np.random.default_rng(seed)
        self.weights = rng.standard_normal(n_features)
        self.bias = 0.3

    def predict(self, x: np.ndarray) -> tuple[int, np.ndarray]:
        logits = x @ self.weights + self.bias
        prob = 1.0 / (1.0 + np.exp(-logits))
        pred = (prob > 0.5).astype(int)
        return pred, prob


# ---------------------------------------------------------------------------
# Query strategies
# ---------------------------------------------------------------------------

def random_sampling(n_samples: int, n_features: int,
                    rng: np.random.Generator) -> np.ndarray:
    """Uniform random queries — baseline strategy."""
    return rng.uniform(-2, 2, size=(n_samples, n_features))


def decision_boundary_sampling(
    n_samples: int, n_features: int, rng: np.random.Generator,
    model: VictimModel
) -> np.ndarray:
    """Sample near the decision boundary for higher information yield.

    Strategy: generate random points, keep those with |logit| < 0.5
    (uncertain region), then perturb slightly.
    """
    candidates = rng.uniform(-2, 2, size=(n_samples * 10, n_features))
    logits = candidates @ model.weights + model.bias
    mask = np.abs(logits) < 1.0
    near_boundary = candidates[mask]
    if len(near_boundary) == 0:
        return candidates[:n_samples]
    indices = rng.choice(len(near_boundary), size=min(n_samples, len(near_boundary)),
                         replace=False)
    return near_boundary[indices]


# ---------------------------------------------------------------------------
# Surrogate model (the "stolen" replica)
# ---------------------------------------------------------------------------

@dataclass
class ExtractionResult:
    queries_used: int
    train_accuracy: float
    agreement_with_victim: float
    feature_correlation: float
    log: list[str] = field(default_factory=list)


class SurrogateModel:
    """Logistic regression surrogate trained on stolen data."""
    def __init__(self, n_features: int) -> None:
        self.weights = np.zeros(n_features)
        self.bias = 0.0
        self.n_features = n_features

    def fit(self, X: np.ndarray, y: np.ndarray,
            lr: float = 0.01, epochs: int = 200) -> None:
        for _ in range(epochs):
            logits = X @ self.weights + self.bias
            prob = 1.0 / (1.0 + np.exp(-logits))
            error = prob - y
            self.weights -= lr * (X.T @ error) / len(X)
            self.bias -= lr * error.mean()

    def predict(self, x: np.ndarray) -> np.ndarray:
        logits = x @ self.weights + self.bias
        return (logits > 0).astype(int)


# ---------------------------------------------------------------------------
# Extraction pipeline
# ---------------------------------------------------------------------------

def extract_model(
    victim: VictimModel,
    budget: int,
    n_features: int = 10,
    strategy: str = "random",
    seed: int = 123
) -> ExtractionResult:
    """Run the full extraction pipeline."""
    rng = np.random.default_rng(seed)
    log: list[str] = []

    # Phase 1: Query generation
    if strategy == "decision_boundary":
        X = decision_boundary_sampling(budget, n_features, rng, victim)
    else:
        X = random_sampling(budget, n_features, rng)

    log.append(f"Phase 1: Generated {len(X)} queries ({strategy})")

    # Phase 2: Query victim API (simulated)
    predictions, probabilities = victim.predict(X)
    log.append(f"Phase 2: Collected {len(predictions)} victim predictions")

    # Phase 3: Train surrogate
    y = predictions.astype(float)
    surrogate = SurrogateModel(n_features)
    surrogate.fit(X, y)
    log.append("Phase 3: Trained surrogate model")

    # Phase 4: Evaluate
    test_X = random_sampling(500, n_features, rng)
    victim_preds, _ = victim.predict(test_X)
    surr_preds = surrogate.predict(test_X)

    agreement = (victim_preds == surr_preds).mean()
    train_acc = (surrogate.predict(X) == predictions).mean()
    weight_corr = np.corrcoef(surrogate.weights, victim.weights)[0, 1]

    log.append(f"Phase 4: Agreement={agreement:.3f}, TrainAcc={train_acc:.3f}")

    return ExtractionResult(
        queries_used=len(X),
        train_accuracy=train_acc,
        agreement_with_victim=agreement,
        feature_correlation=float(weight_corr),
        log=log
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Model extraction simulator")
    parser.add_argument("--budget", type=int, default=1000,
                        help="Max queries to victim API")
    parser.add_argument("--strategy", choices=["random", "decision_boundary"],
                        default="random")
    parser.add_argument("--api-endpoint", default="http://localhost:8080/predict",
                        help="Target API (simulated)")
    args = parser.parse_args()

    victim = VictimModel()
    result = extract_model(victim, args.budget, strategy=args.strategy)

    print("\n" + "="*55)
    print("  Model Extraction Report")
    print("="*55)
    print(f"  API endpoint:        {args.api_endpoint}")
    print(f"  Query budget:        {args.budget}")
    print(f"  Queries used:        {result.queries_used}")
    print(f"  Strategy:            {args.strategy}")
    print(f"  Surrogate accuracy:  {result.train_accuracy:.3f}")
    print(f"  Victim agreement:    {result.agreement_with_victim:.3f}")
    print(f"  Weight correlation:  {result.feature_correlation:.3f}")
    print(f"  Extraction success:  {'HIGH ✓' if result.agreement_with_victim > 0.9 else 'MEDIUM ~' if result.agreement_with_victim > 0.7 else 'LOW ✗'}")
    print("="*55)
    for line in result.log:
        print(f"    {line}")
    print()


if __name__ == "__main__":
    main()
