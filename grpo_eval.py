# ============================================================================
# BIONIC DAUGHTER — GRPO EVAL SUITE
# Held-out eval set + scoring harness.
#
# Purpose:
#   - Measure the model's capability on each of the 6 domains BEFORE and
#     AFTER each training stage
#   - Never leak eval data into training (held-out, separate file)
#   - Track per-domain accuracy + overall so we know whether training helped
#
# Design:
#   - Eval set: grpo_eval_held_out.jsonl — separate from the training corpus
#   - For each eval prompt, generate N completions (generations_per_prompt)
#   - Score each completion with the reward engine
#   - Report per-domain + overall: composite score, format pass rate,
#     accuracy pass rate, reasoning-depth pass rate
#
# Pass criteria:
#   - A completion "passes" if it has clean format AND a concrete verifiable
#     claim (accuracy > 0.5) AND reasoning depth > 0.4
#   - Domain pass rate = fraction of prompts where at least one generation
#     passes
#   - Overall pass rate = average across domains
# ============================================================================

import json
import re
import os
import sys
from typing import Dict, List, Any
from collections import defaultdict

# Import the reward engine (same-project, same dir)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grpo_reward_engine import (
    compute_reward,
    compute_batch_reward,
    reward_format,
    reward_accuracy,
    reward_reasoning_depth,
    reward_density,
    reward_tool_use_quality,
    reward_self_correction,
)

# ---------------------------------------------------------------------------
# PASS THRESHOLDS (tunable)
# ---------------------------------------------------------------------------
FORMAT_PASS_THRESHOLD = 0.6
ACCURACY_PASS_THRESHOLD = 0.5
REASONING_DEPTH_PASS_THRESHOLD = 0.4
DENSITY_PASS_THRESHOLD = 0.4

# A completion "passes" if it clears ALL of these:
def completion_passes(component_scores: Dict) -> bool:
    return (
        component_scores.get("format", 0.0) >= FORMAT_PASS_THRESHOLD
        and component_scores.get("accuracy", 0.0) >= ACCURACY_PASS_THRESHOLD
        and component_scores.get("reasoning_depth", 0.0) >= REASONING_DEPTH_PASS_THRESHOLD
        and component_scores.get("density", 0.0) >= DENSITY_PASS_THRESHOLD
    )


# ---------------------------------------------------------------------------
# LOAD EVAL SET
# ---------------------------------------------------------------------------

def load_eval_set(path: str) -> List[Dict]:
    """
    Load the held-out eval set from JSONL.
    Each record: {prompt, completion, metadata}
    We use prompt + metadata for scoring; we do NOT use the stored completion
    as ground truth (the model generates fresh completions).
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Eval set not found: {path}")
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if "prompt" not in rec:
                    continue
                records.append(rec)
            except json.JSONDecodeError:
                continue
    return records


# ---------------------------------------------------------------------------
# GENERATE COMPLETIONS (stub — real generation happens in the trainer)
# ---------------------------------------------------------------------------

def generate_completions_stub(prompt: str, n: int = 4) -> List[str]:
    """
    Stub: in the real training loop, the trainer generates N completions
    per eval prompt using the current policy model.
    Here we return placeholder completions that mirror the stored eval
    completions so we can run the suite standalone for validation.
    """
    # In a real run, this calls the model's generate().
    # For standalone eval validation, fall back to the stored completion.
    return ["__STUB__"]


# ---------------------------------------------------------------------------
# SCORE ONE PROMPT
# ---------------------------------------------------------------------------

def score_prompt(
    prompt: str,
    metadata: Dict,
    generations: List[str],
    weights: Dict = None,
) -> Dict:
    """
    Score a single eval prompt: generate N completions (or use provided),
    score each, return per-generation scores + summary.
    """
    if weights is None:
        weights = {}

    gen_scores = []
    for gen in generations:
        comp = compute_reward(gen, prompt, weights, per_component=True)
        gen_scores.append(comp)

    # Summary: best composite, pass/fail, per-component averages
    best = max(gen_scores, key=lambda x: x["composite"]) if gen_scores else {}
    avg_components = {}
    for key in ["format", "accuracy", "reasoning_depth", "density",
                "tool_use_quality", "self_correction"]:
        vals = [g["components"].get(key, 0.0) for g in gen_scores]
        avg_components[key] = sum(vals) / len(vals) if vals else 0.0

    passes = any(completion_passes(g["components"]) for g in gen_scores)

    return {
        "prompt": prompt,
        "domain": metadata.get("domain", "unknown"),
        "trace_id": metadata.get("trace_id", ""),
        "generations": gen_scores,
        "best_composite": best.get("composite", 0.0),
        "avg_components": avg_components,
        "passes": passes,
        "pass_count": sum(1 for g in gen_scores if completion_passes(g["components"])),
        "generation_count": len(generations),
    }


# ---------------------------------------------------------------------------
# RUN FULL EVAL
# ---------------------------------------------------------------------------

def run_eval(
    eval_path: str,
    generations_per_prompt: int = 4,
    weights: Dict = None,
    generate_fn=None,
) -> Dict:
    """
    Run the full eval suite.
    generate_fn(prompt, n) -> List[str]  — the trainer's generation call.
    If None, uses the stored completion as a single generation (for baseline
    validation of the reward engine against the held-out set).
    """
    records = load_eval_set(eval_path)
    weights = weights or {}

    # Group by domain
    by_domain: Dict[str, List[Dict]] = defaultdict(list)
    results = []

    for rec in records:
        prompt = rec.get("prompt", "")
        metadata = rec.get("metadata", {})
        domain = metadata.get("domain", "unknown")

        if generate_fn is not None:
            generations = generate_fn(prompt, generations_per_prompt)
        else:
            # Baseline: use the stored completion as one generation
            generations = [rec.get("completion", "")]

        scored = score_prompt(prompt, metadata, generations, weights)
        results.append(scored)
        by_domain[domain].append(scored)

    # Aggregate
    total_prompts = len(results)
    total_passes = sum(1 for r in results if r["passes"])
    overall_pass_rate = total_passes / total_prompts if total_prompts > 0 else 0.0

    domain_summary = {}
    for domain, dom_results in by_domain.items():
        domain_prompts = len(dom_results)
        domain_passes = sum(1 for r in dom_results if r["passes"])
        domain_summary[domain] = {
            "prompts": domain_prompts,
            "passes": domain_passes,
            "pass_rate": domain_passes / domain_prompts if domain_prompts > 0 else 0.0,
            "avg_best_composite": sum(r["best_composite"] for r in dom_results) / domain_prompts,
            "avg_components": {},
        }
        for key in ["format", "accuracy", "reasoning_depth", "density",
                    "tool_use_quality", "self_correction"]:
            vals = [r["avg_components"].get(key, 0.0) for r in dom_results]
            domain_summary[domain]["avg_components"][key] = sum(vals) / len(vals)

    # Overall component averages
    overall_components = {}
    for key in ["format", "accuracy", "reasoning_depth", "density",
                "tool_use_quality", "self_correction"]:
        vals = [r["avg_components"].get(key, 0.0) for r in results]
        overall_components[key] = sum(vals) / len(vals) if vals else 0.0

    overall_best = sum(r["best_composite"] for r in results) / total_prompts if total_prompts > 0 else 0.0

    return {
        "total_prompts": total_prompts,
        "total_passes": total_passes,
        "overall_pass_rate": overall_pass_rate,
        "overall_best_composite": overall_best,
        "overall_components": overall_components,
        "domain_summary": domain_summary,
        "results": results,
    }


# ---------------------------------------------------------------------------
# REPORT
# ---------------------------------------------------------------------------

def print_report(eval_result: Dict, label: str = "EVAL"):
    """
    Print a human-readable eval report.
    """
    print("\n" + "=" * 70)
    print(f"  {label}")
    print("=" * 70)
    print(f"  Total prompts   : {eval_result['total_prompts']}")
    print(f"  Total passes    : {eval_result['total_passes']}")
    print(f"  Overall pass rate: {eval_result['overall_pass_rate']:.2%}")
    print(f"  Overall best composite (avg): {eval_result['overall_best_composite']:.3f}")
    print()
    print("  Per-component averages (overall):")
    for k, v in eval_result["overall_components"].items():
        print(f"    {k:20s}: {v:.3f}")
    print()
    print("  Per-domain:")
    print(f"    {'Domain':<35s} {'Prompts':>8s} {'Passes':>7s} {'Pass Rate':>10s} {'BestComp':>9s}")
    print(f"    {'-'*35} {'-'*8} {'-'*7} {'-'*10} {'-'*9}")
    for domain, summary in eval_result["domain_summary"].items():
        print(f"    {domain:<35s} {summary['prompts']:>8d} {summary['passes']:>7d} "
              f"{summary['pass_rate']:>10.2%} {summary['avg_best_composite']:>9.3f}")
    print("=" * 70)


# ---------------------------------------------------------------------------
# BUILD THE HELD-OUT EVAL SET (one-time setup)
# ---------------------------------------------------------------------------
# The eval set must be separate from the training corpus. We build it by
# sampling from the training corpus per domain, then removing those samples
# from the training set. This ensures no data leakage.
#
# For now, we build a small held-out set (10 per domain = 60 total) from the
# existing 1,005-trace corpus. In a real run, you'd want a larger eval set,
# but 60 is enough to get a signal on the first run.

def build_held_out_eval_set(
    train_path: str = "grpo_train_ready.jsonl",
    eval_path: str = "grpo_eval_held_out.jsonl",
    samples_per_domain: int = 10,
    seed: int = 42,
) -> Dict:
    """
    Build the held-out eval set by sampling from the training corpus.
    Removes sampled records from the training set to prevent leakage.
    Returns stats about what was built.
    """
    import random

    if not os.path.exists(train_path):
        raise FileNotFoundError(f"Training corpus not found: {train_path}")

    # Load all records, grouped by domain
    by_domain: Dict[str, List[Dict]] = defaultdict(list)
    all_records = []
    with open(train_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                all_records.append(rec)
                domain = rec.get("metadata", {}).get("domain", "unclassified")
                by_domain[domain].append(rec)
            except json.JSONDecodeError:
                continue

    # Sample per domain
    rng = random.Random(seed)
    eval_records = []
    eval_trace_ids = set()

    for domain, records in by_domain.items():
        if len(records) <= samples_per_domain:
            # Not enough records to hold out — take all and warn
            chosen = records[:]
        else:
            chosen = rng.sample(records, samples_per_domain)
        for rec in chosen:
            eval_trace_ids.add(rec.get("metadata", {}).get("trace_id", ""))
            eval_records.append(rec)

    # Remove eval records from training set
    remaining = [r for r in all_records if r.get("metadata", {}).get("trace_id", "") not in eval_trace_ids]

    # Write eval set
    with open(eval_path, "w", encoding="utf-8") as f:
        for rec in eval_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # Rewrite training set without eval records
    with open(train_path, "w", encoding="utf-8") as f:
        for rec in remaining:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # Stats
    by_domain_after: Dict[str, int] = defaultdict(int)
    for rec in remaining:
        domain = rec.get("metadata", {}).get("domain", "unclassified")
        by_domain_after[domain] += 1

    stats = {
        "eval_path": eval_path,
        "train_path": train_path,
        "samples_per_domain": samples_per_domain,
        "seed": seed,
        "eval_records": len(eval_records),
        "eval_domains": sorted(by_domain.keys()),
        "train_records_after": len(remaining),
        "train_domains_after_counts": dict(by_domain_after),
    }

    return stats


# ---------------------------------------------------------------------------
# MAIN — self-test on the held-out set
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GRPO Eval Suite")
    parser.add_argument("--eval-path", default="grpo_eval_held_out.jsonl")
    parser.add_argument("--label", default="BASELINE EVAL")
    parser.add_argument("--generations", type=int, default=4)
    parser.add_argument("--build-eval", action="store_true",
                        help="Build held-out eval set from training corpus")
    parser.add_argument("--samples-per-domain", type=int, default=10)
    args = parser.parse_args()

    if args.build_eval:
        print("Building held-out eval set...")
        stats = build_held_out_eval_set(
            train_path="grpo_train_ready.jsonl",
            eval_path=args.eval_path,
            samples_per_domain=args.samples_per_domain,
        )
        print(json.dumps(stats, indent=2))
        print("\nEval set built. Now run eval with --label to score it.")
        sys.exit(0)

    if not os.path.exists(args.eval_path):
        print(f"Eval set not found: {args.eval_path}")
        print("Build it first: python grpo_eval.py --build-eval")
        sys.exit(1)

    # Run eval using stored completions as baseline (single generation per prompt)
    result = run_eval(
        eval_path=args.eval_path,
        generations_per_prompt=args.generations,
        generate_fn=None,  # use stored completions
    )

    print_report(result, label=args.label)

    # Save report to artifacts
    os.makedirs("artifacts/evals", exist_ok=True)
    report_path = f"artifacts/evals/eval_{args.label.replace(' ', '_').lower()}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nReport saved: {report_path}")
