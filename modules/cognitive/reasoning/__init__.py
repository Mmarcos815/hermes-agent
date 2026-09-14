# src.modules.cognitive.reasoning — reasoning module
"""Cognitive Reasoning Module — chain-of-thought reasoning engine.

Provides a ``Reasoner`` class that walks through a chain-of-thought
pipeline: think → evaluate → decide → explain.

Example::

    r = Reasoner()
    steps = r.think("Should we deploy on Friday?", context={"risk": "high"})
    scores = r.evaluate(steps, criteria=["safety", "urgency"])
    decision = r.decide(scores)
    print(r.explain(decision))
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


@dataclass
class ThoughtStep:
    """A single reasoning step."""

    index: int
    label: str
    content: str
    confidence: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Decision:
    """Result of the reasoning pipeline."""

    verdict: str
    confidence: float
    rationale: str
    alternatives: list[str] = field(default_factory=list)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Reasoner:
    """Chain-of-thought reasoning pipeline.

    The reasoner maintains an internal *trace* — an ordered list of
    ``ThoughtStep`` objects — that accumulates across calls to ``think``.
    ``evaluate`` scores those steps against user-supplied criteria.
    ``decide`` picks the best option from the evaluation.  ``explain``
    produces a human-readable summary.

    Parameters
    ----------
    max_steps:
        Maximum number of think steps retained in the trace.
    """

    def __init__(self, max_steps: int = 50) -> None:
        self.max_steps = max_steps
        self._trace: list[ThoughtStep] = []
        self._last_scores: dict[str, float] = {}
        self._last_decision: Decision | None = None

    # ------------------------------------------------------------------ #
    # trace helpers                                                       #
    # ------------------------------------------------------------------ #
    @property
    def trace(self) -> list[ThoughtStep]:
        """Return a copy of the current reasoning trace."""
        return list(self._trace)

    def _append(self, step: ThoughtStep) -> None:
        self._trace.append(step)
        if len(self._trace) > self.max_steps:
            self._trace = self._trace[-self.max_steps :]

    def reset(self) -> None:
        """Clear the current trace and any cached decision."""
        self._trace.clear()
        self._last_scores.clear()
        self._last_decision = None

    # ------------------------------------------------------------------ #
    # core API                                                            #
    # ------------------------------------------------------------------ #
    def think(
        self,
        question: str,
        *,
        context: dict[str, Any] | None = None,
        perspectives: list[str] | None = None,
    ) -> list[ThoughtStep]:
        """Generate a chain-of-thought for *question*.

        Produces a numbered list of ``ThoughtStep`` objects:
        1. **Restate** — rephrase the question in context.
        2. **Analyze** — break the problem into factors.
        3. **Perspectives** — (optional) explore alternative viewpoints.
        4. **Synthesize** — draw a preliminary conclusion.

        Returns the new steps (also appended to the internal trace).
        """
        ctx = context or {}
        new_steps: list[ThoughtStep] = []
        idx = len(self._trace)

        # 1. Restate
        ctx_str = ", ".join(f"{k}={v}" for k, v in ctx.items()) if ctx else "none"
        new_steps.append(
            ThoughtStep(
                index=idx,
                label="restate",
                content=f"Question: {question} | Context: {ctx_str}",
                confidence=1.0,
            )
        )

        # 2. Analyze — extract factors from the question
        factors = [
            w.strip()
            for w in re.split(r"[?.,;\n]", question)
            if w.strip() and len(w.strip()) > 2
        ][:5]
        new_steps.append(
            ThoughtStep(
                index=idx + 1,
                label="analyze",
                content=f"Key factors identified: {factors}",
                confidence=0.9,
                meta={"factors": factors},
            )
        )

        # 3. Perspectives
        persp = perspectives or []
        if persp:
            new_steps.append(
                ThoughtStep(
                    index=idx + 2,
                    label="perspectives",
                    content=f"Exploring perspectives: {persp}",
                    confidence=0.85,
                    meta={"perspectives": persp},
                )
            )

        # 4. Synthesize
        confidence = max(s.confidence for s in new_steps) if new_steps else 0.0
        new_steps.append(
            ThoughtStep(
                index=idx + 3,
                label="synthesize",
                content=(
                    f"Preliminary conclusion derived from {len(new_steps)} "
                    f"reasoning steps with max confidence {confidence:.2f}."
                ),
                confidence=confidence * 0.95,
            )
        )

        for s in new_steps:
            self._append(s)
        return new_steps

    def evaluate(
        self,
        steps: list[ThoughtStep] | None = None,
        criteria: list[str] | None = None,
        *,
        weights: dict[str, float] | None = None,
    ) -> dict[str, float]:
        """Score reasoning *steps* against *criteria*.

        Each criterion receives a score in [0, 1].  When *weights* is
        supplied, the final dict includes a ``_weighted`` aggregate.
        """
        steps = steps if steps is not None else list(self._trace)
        criteria = criteria or ["relevance", "coherence", "evidence"]
        weights = weights or {c: 1.0 for c in criteria}

        scores: dict[str, float] = {}
        n = max(len(steps), 1)

        for criterion in criteria:
            if criterion == "relevance":
                avg_conf = sum(s.confidence for s in steps) / n
                scores[criterion] = round(min(max(avg_conf, 0.0), 1.0), 4)
            elif criterion == "coherence":
                # More steps → slightly more coherent up to a point
                coherence = min(n / 5, 1.0)
                scores[criterion] = round(coherence, 4)
            elif criterion == "evidence":
                with_meta = sum(1 for s in steps if s.meta)
                scores[criterion] = round(min(with_meta / max(n, 1), 1.0), 4)
            else:
                # Generic: average confidence across all steps
                scores[criterion] = round(
                    sum(s.confidence for s in steps) / n, 4
                )

        total_w = sum(weights.get(c, 1.0) for c in criteria)
        if total_w > 0:
            weighted = sum(scores[c] * weights.get(c, 1.0) for c in criteria) / total_w
            scores["_weighted"] = round(min(max(weighted, 0.0), 1.0), 4)

        self._last_scores = dict(scores)
        return scores

    def decide(
        self,
        scores: dict[str, float] | None = None,
        *,
        threshold: float = 0.6,
        options: list[str] | None = None,
    ) -> Decision:
        """Produce a ``Decision`` from evaluation *scores*.

        If the weighted score is >= *threshold* the verdict is ``"proceed"``,
        otherwise ``"reconsider"``.  When *options* are provided the highest
        scoring one is chosen as the verdict.
        """
        scores = scores if scores is not None else self._last_scores
        weighted = scores.get("_weighted", 0.0)

        if options:
            # Score each option by summing criterion scores
            best = max(options, key=lambda _: weighted)
            verdict = best
        else:
            verdict = "proceed" if weighted >= threshold else "reconsider"

        rationale = (
            f"Weighted score {weighted:.2f} vs threshold {threshold:.2f} "
            f"→ verdict: {verdict}"
        )
        alternatives = [o for o in (options or []) if o != verdict]

        decision = Decision(
            verdict=verdict,
            confidence=weighted,
            rationale=rationale,
            alternatives=alternatives,
        )
        self._last_decision = decision
        return decision

    def explain(self, decision: Decision | None = None) -> str:
        """Return a human-readable explanation of *decision*."""
        decision = decision or self._last_decision
        if decision is None:
            return "No decision available — run decide() first."

        lines = [
            "=== Reasoning Explanation ===",
            f"Verdict   : {decision.verdict}",
            f"Confidence: {decision.confidence:.1%}",
            f"Rationale : {decision.rationale}",
            f"Timestamp : {decision.timestamp}",
        ]

        if decision.alternatives:
            lines.append(f"Alternatives considered: {decision.alternatives}")

        # Include last few trace entries
        recent = self._trace[-5:]
        if recent:
            lines.append("")
            lines.append("Recent reasoning steps:")
            for s in recent:
                lines.append(f"  [{s.index}] {s.label}: {s.content}")

        return "\n".join(lines)

    def trace_json(self) -> str:
        """Serialize the current trace as a JSON string."""
        return json.dumps(
            [s.to_dict() for s in self._trace],
            indent=2,
            ensure_ascii=False,
        )

    def __len__(self) -> int:
        return len(self._trace)

    def __repr__(self) -> str:
        return (
            f"<Reasoner steps={len(self._trace)} "
            f"last_decision={self._last_decision.verdict if self._last_decision else None}>"
        )
