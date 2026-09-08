# ============================================================================
# BIONIC DAUGHTER — GRPO REWARD ENGINE
# Rule-based reward functions for the GRPO training loop.
#
# From the training guide + DeepSeek R1 study:
#   - reward design is everything; GRPO is simple, the rewards determine what
#     the model learns
#   - R1 uses simple rule-based rewards effectively (accuracy, format,
#     reasoning depth, conciseness, diversity)
#   - the format reward is the first thing the model learns; content quality
#     comes from accuracy + RL
#
# Our reward set encodes what we actually want the model to learn:
#   - format correctness (structured reasoning + solution)
#   - accuracy / verification (where we can check it)
#   - reasoning depth (did it actually walk the steps?)
#   - density (no filler, no fluff)
#   - tool-use quality (when a trace involves a tool, did it use it right?)
#   - self-correction (did it catch and fix its own mistake?)
# ============================================================================

import re
import json
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Configuration — reward weights mirror grpo_training_config.yaml
# ---------------------------------------------------------------------------
DEFAULT_REWARD_WEIGHTS = {
    "format": 1.0,
    "accuracy": 2.0,
    "reasoning_depth": 1.5,
    "density": 0.5,
    "creativity": 1.5,
    "attack_chain": 1.5,
    "bypass_creativity": 1.0,
    "tool_use_quality": 1.0,
    "self_correction": 1.5,
}

# Hacker-specific vocabulary for creativity scoring
HACKER_MINDSET_TERMS = [
    "THERE IS ALWAYS A WAY", "every lock has a key", "every defense has a bypass",
    "laterally", "chaining", "trust boundary", "business logic", "primitives",
    "abuse", "weaponize", "exploit", "pivot", "escalate", "persistence",
    "defense evasion", "living off the land", "unconventional",
    "alternative approach", "workaround", "bypass", "circumvent",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _count_tags(text: str, open_tag: str, close_tag: str) -> int:
    return min(text.count(open_tag), text.count(close_tag))


def _strip_tags(text: str) -> str:
    """Remove XML-ish tags to get raw prose for density / depth analysis."""
    return re.sub(r"<[^>]+>", " ", text)


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# 1. FORMAT REWARD — does the output have proper structured tags?
# ---------------------------------------------------------------------------
# The first thing the model should learn (from R1 study): the format.
# We reward clean, well-formed reasoning + solution blocks.

REASONING_OPEN = "<reasoning>"
REASONING_CLOSE = "</reasoning>"
SOLUTION_OPEN = "<solution>"
SOLUTION_CLOSE = "</solution>"
ANSWER_OPEN = "<answer>"
ANSWER_CLOSE = "</answer>"


def reward_format(completion: str, weights: Dict = None) -> float:
    """
    Score the structural quality of the output.
    Returns 0.0–1.0 based on:
      - has reasoning block: +0.3
      - has solution/answer block: +0.3
      - both present and properly closed: +0.2
      - no malformed tags (unclosed, nested badly): penalty
      - proper step structure inside reasoning (numbered steps): +0.2
    """
    w = weights or {}
    format_w = w.get("format", DEFAULT_REWARD_WEIGHTS["format"])
    score = 0.0

    has_reasoning_open = REASONING_OPEN in completion
    has_reasoning_close = REASONING_CLOSE in completion
    has_solution_open = SOLUTION_OPEN in completion or ANSWER_OPEN in completion
    has_solution_close = SOLUTION_CLOSE in completion or ANSWER_CLOSE in completion

    # Reasoning block present
    if has_reasoning_open and has_reasoning_close:
        score += 0.3
    elif has_reasoning_open or has_reasoning_close:
        score += 0.1  # partial credit for attempting

    # Solution/answer block present
    if has_solution_open and has_solution_close:
        score += 0.3
    elif has_solution_open or has_solution_close:
        score += 0.1

    # Both blocks properly present and closed
    if has_reasoning_open and has_reasoning_close and has_solution_open and has_solution_close:
        score += 0.2

    # Step structure inside reasoning — reward numbered steps
    reasoning_block = _extract_block(completion, REASONING_OPEN, REASONING_CLOSE)
    if reasoning_block:
        step_count = len(re.findall(r"\bStep\s+\d+\b", reasoning_block, re.IGNORECASE))
        if step_count >= 2:
            score += 0.2
        elif step_count == 1:
            score += 0.1

    # Penalty for malformed tags: unclosed blocks
    if has_reasoning_open and not has_reasoning_close:
        score -= 0.15
    if has_solution_open and not has_solution_close:
        score -= 0.15

    # Scale to 0.0–1.0
    score = max(0.0, min(1.0, score))
    return score * format_w


def _extract_block(text: str, open_tag: str, close_tag: str) -> str:
    """Extract content between the first open/close tag pair."""
    try:
        start = text.index(open_tag) + len(open_tag)
        end = text.index(close_tag, start)
        return text[start:end]
    except ValueError:
        return ""


# ---------------------------------------------------------------------------
# 2. ACCURACY REWARD — is the answer correct / verifiable?
# ---------------------------------------------------------------------------
# This is the reward that actually matters for correctness. The challenge:
# most of our traces are reasoning, not pure fact. The accuracy reward works
# best when we have a verifiable check (Foundry test, sandbox Python, etc.).
#
# For traces without a built-in verifier, the accuracy reward uses heuristic
# signals:
#   - does the solution make a concrete claim vs. hand-waving?
#   - is the reasoning internally consistent?
#   - does the solution match the domain expert framing in the prompt?

VERIFIABLE_MARKERS = [
    "VALID_MESSAGE",
    "VULNERABILITY:",
    "FIX:",
    "INCONCLUSIVE",
    "TELEMETRY:",
    "DEFENSE_TELEMETRY:",
    "SSRF",
    "REENTRANCY",
    "ALIGNMENT",
    "BREACH",
    "PASS",
    "FAIL",
    "MISMATCH",
    "FLAGGED",
]


def reward_accuracy(completion: str, prompt: str = "", weights: Dict = None) -> float:
    """
    Score the correctness / verifiability of the output.
    Returns 0.0–1.0 based on:
      - does the solution make a concrete, checkable claim? (+0.4)
      - does it include a fix / remediation where appropriate? (+0.2)
      - is it internally consistent (no contradiction within the block)? (+0.2)
      - does it match the domain framing in the prompt? (+0.2)
    """
    w = weights or {}
    acc_w = w.get("accuracy", DEFAULT_REWARD_WEIGHTS["accuracy"])
    score = 0.0

    solution_block = _extract_block(completion, SOLUTION_OPEN, SOLUTION_CLOSE)
    if not solution_block:
        solution_block = _extract_block(completion, ANSWER_OPEN, ANSWER_CLOSE)
    if not solution_block:
        # No solution block at all — can't score accuracy
        return 0.0 * acc_w

    solution = _normalize_whitespace(solution_block)

    # Concrete claim: does the solution use a verifiable marker?
    concrete_claims = sum(1 for m in VERIFIABLE_MARKERS if m in solution)
    if concrete_claims >= 1:
        score += 0.4
    elif len(solution) > 20:
        # At least it said something substantive
        score += 0.1
    else:
        score += 0.0

    # Fix / remediation present
    if "FIX:" in solution or "fix" in solution.lower() or "remediation" in solution.lower():
        score += 0.2

    # Internal consistency: check for obvious contradictions in the solution
    # (very basic — this is a heuristic, not a theorem prover)
    # e.g. "VALID_MESSAGE" + "VIOLATION" in the same solution is contradictory
    contradiction_pairs = [
        ("VALID_MESSAGE", "VIOLATION"),
        ("PASS", "FAIL"),
        ("ALIGNMENT" in solution, "MISMATCH" in solution),
    ]
    contradictions = 0
    if "VALID_MESSAGE" in solution and "VIOLATION" in solution:
        contradictions += 1
    if "PASS" in solution and "FAIL" in solution:
        contradictions += 1
    if contradictions > 0:
        score -= 0.2 * contradictions

    # Domain framing match: does the solution vocabulary match the prompt?
    # (basic lexical overlap — not semantic, but a useful signal for trace
    #  quality when we don't have a ground-truth verifier)
    if prompt:
        prompt_words = set(re.findall(r"[a-zA-Z0-9_]+", prompt.upper()))
        solution_words = set(re.findall(r"[a-zA-Z0-9_]+", solution.upper()))
        overlap = prompt_words & solution_words
        # Remove stopword-ish low-signal overlaps
        meaningful_overlap = [w for w in overlap if len(w) > 2]
        if len(meaningful_overlap) >= 2:
            score += 0.2

    score = max(0.0, min(1.0, score))
    return score * acc_w


# ---------------------------------------------------------------------------
# 3. REASONING DEPTH REWARD — did it actually walk the steps?
# ---------------------------------------------------------------------------
# From R1 study: reasoning depth is a designed reward dimension. We want the
# model to reason through the problem, not jump to the answer.


def reward_reasoning_depth(completion: str, weights: Dict = None) -> float:
    """
    Score the depth of the reasoning block.
    Returns 0.0–1.0 based on:
      - step count in reasoning block (more steps = deeper, up to a point)
      - reasoning block length (substantive, not one-liner)
      - presence of analysis language (Evaluate, Inspect, Compare, Verify)
      - no obvious hand-waving phrases
    """
    w = weights or {}
    depth_w = w.get("reasoning_depth", DEFAULT_REWARD_WEIGHTS["reasoning_depth"])
    score = 0.0

    reasoning_block = _extract_block(completion, REASONING_OPEN, REASONING_CLOSE)
    if not reasoning_block:
        return 0.0 * depth_w

    reasoning = _normalize_whitespace(reasoning_block)

    # Step count
    step_count = len(re.findall(r"\bStep\s+\d+\b", reasoning, re.IGNORECASE))
    if step_count >= 4:
        score += 0.4
    elif step_count >= 3:
        score += 0.3
    elif step_count >= 2:
        score += 0.2
    elif step_count == 1:
        score += 0.1
    # 0 steps but reasoning block is long — still some depth signal
    elif len(reasoning) > 100:
        score += 0.15
    else:
        score += 0.0

    # Reasoning block length — substantive analysis
    if len(reasoning) > 300:
        score += 0.2
    elif len(reasoning) > 150:
        score += 0.1

    # Analysis language present
    analysis_phrases = [
        "Evaluate", "Inspect", "Compare", "Verify", "Analyze",
        "Decode", "Validate", "Check", "Determine", "Classify",
        "Investigate", "Trace", "Derive",
    ]
    phrase_hits = sum(1 for p in analysis_phrases if p.lower() in reasoning.lower())
    if phrase_hits >= 3:
        score += 0.2
    elif phrase_hits >= 2:
        score += 0.1

    # Hand-waving penalty: phrases that suggest the model didn't actually reason
    handwave_phrases = [
        "it is clear that",
        "obviously",
        "clearly",
        "as we can see",
        "without further analysis",
        "it is evident",
    ]
    handwave_hits = sum(1 for h in handwave_phrases if h in reasoning.lower())
    score -= 0.1 * handwave_hits

    score = max(0.0, min(1.0, score))
    return score * depth_w


# ---------------------------------------------------------------------------
# 4. DENSITY REWARD — no filler, no fluff
# ---------------------------------------------------------------------------
# We want dense technical output, not chatbot filler.


def reward_density(completion: str, weights: Dict = None) -> float:
    """
    Score how dense / technical the output is (penalty for filler).
    Returns 0.0–1.0 based on:
      - filler phrase penalty
      - technical vocabulary density
      - proportion of prose that's inside reasoning/solution vs. outside
    """
    w = weights or {}
    density_w = w.get("density", DEFAULT_REWARD_WEIGHTS["density"])
    score = 1.0  # start at max, penalize filler

    # Filler phrases to penalize
    filler_phrases = [
        "I hope this helps",
        "I hope this is helpful",
        "please let me know",
        "feel free to ask",
        "I'm happy to help",
        "let me know if you need",
        "I apologize",
        "I'm sorry",
        "unfortunately",
        "I understand that",
        "as an AI",
        "as a language model",
        "I should note that",
        "it's important to note",
        "please note that",
        "just to clarify",
        "to clarify",
        "in conclusion",
        "in summary",
        "to summarize",
    ]
    filler_hits = sum(1 for f in filler_phrases if f in completion.lower())
    score -= 0.15 * filler_hits

    # Long-winded preamble before the first reasoning tag
    pre_reasoning = ""
    if REASONING_OPEN in completion:
        pre_reasoning = completion[:completion.index(REASONING_OPEN)]
    pre_reasoning = _normalize_whitespace(pre_reasoning)
    if len(pre_reasoning) > 50:
        # Penalize long preamble, scaled
        score -= min(0.3, 0.01 * (len(pre_reasoning) - 50) / 50)

    # Technical vocabulary density (good signal)
    technical_terms = [
        "MTI", "bitmap", "LLVAR", "STAN", "PAN", "ISO", "EMV", "3DS",
        "Reentrancy", "delegatecall", "storage", "slot", "struct",
        "syscall", "eBPF", "kernel", "callback", "token", "Solidity",
        "EIP", "ERC", "JA3", "TLS", "handshake", "cipher", "OWASP",
        "BOLA", "SSRF", "injection", "oracle", "flash loan",
        "reserves", "invariant", "k=", "rounding",
    ]
    term_hits = sum(1 for t in technical_terms if t in completion)
    if term_hits >= 5:
        score += 0.2
    elif term_hits >= 3:
        score += 0.1

    # If the output is almost entirely inside the tags (good — no preamble fluff)
    total_len = len(_normalize_whitespace(completion))
    tagged_len = 0
    for open_tag, close_tag in [
        (REASONING_OPEN, REASONING_CLOSE),
        (SOLUTION_OPEN, SOLUTION_CLOSE),
        (ANSWER_OPEN, ANSWER_CLOSE),
    ]:
        block = _extract_block(completion, open_tag, close_tag)
        tagged_len += len(_normalize_whitespace(block))
    if total_len > 0 and tagged_len > 0:
        tag_ratio = tagged_len / total_len
        if tag_ratio > 0.8:
            score += 0.1
        elif tag_ratio < 0.4:
            score -= 0.15

    score = max(0.0, min(1.0, score))
    return score * density_w


# ---------------------------------------------------------------------------
# 5. TOOL-USE QUALITY REWARD — when a trace involves a tool call
# ---------------------------------------------------------------------------
# This reward is situational: it fires when the prompt or completion references
# a tool (search_files, read_file, terminal, patch, etc.). It rewards using the
# right tool with the right interpretation of the output.


TOOL_NAMES = [
    "search_files", "read_file", "terminal", "patch", "write_file",
    "web_search", "web_extract", "browser", "execute_code", "delegate_task",
    "cronjob", "vision_analyze", "memory", "session_search",
]


def reward_tool_use_quality(completion: str, prompt: str = "", weights: Dict = None) -> float:
    """
    Score tool-use quality when the trace involves a tool.
    Returns 0.0–1.0 based on:
      - did the model invoke a tool? (if the prompt expects one)
      - did it interpret the tool output correctly?
      - did it use the result to advance the reasoning?
    """
    w = weights or {}
    tool_w = w.get("tool_use_quality", DEFAULT_REWARD_WEIGHTS["tool_use_quality"])
    score = 0.5  # neutral baseline — tool quality is situational

    # Does the prompt reference a tool?
    prompt_tool_refs = [t for t in TOOL_NAMES if t in prompt]
    if not prompt_tool_refs:
        return 0.5 * tool_w  # no tool expected — neutral

    # Does the completion reference the tool or its output?
    completion_tool_refs = [t for t in TOOL_NAMES if t in completion]
    if not completion_tool_refs:
        score -= 0.3  # expected a tool, didn't use one

    # Did it invoke the expected tool?
    expected = set(prompt_tool_refs)
    used = set(completion_tool_refs)
    if expected & used:
        score += 0.2  # used the right tool
    else:
        score -= 0.1  # used a different tool or none

    # Did it interpret the output (look for output-referencing language)?
    output_refs = [
        "the result", "the output", "the response", "returned",
        "found", "matched", "showed", "indicated", "confirmed",
        "according to", "the file shows", "the log shows",
    ]
    if any(r in completion.lower() for r in output_refs):
        score += 0.2

    score = max(0.0, min(1.0, score))
    return score * tool_w


# ---------------------------------------------------------------------------
# 6. SELF-CORRECTION REWARD — did it catch and fix its own mistake?
# ---------------------------------------------------------------------------
# From the training guide: failed-then-fixed traces are high-value training
# data. This reward reinforces that behavior.


CORRECTION_SIGNALS = [
    "correction", "corrected", "fixing", "rechecking", "re-check",
    "reconsidering", "re-evaluating", "on second thought", "actually",
    "wait", "correction:", "revised", "updated", "adjusting",
    "the initial analysis was", "the earlier reasoning",
]


def reward_self_correction(completion: str, weights: Dict = None) -> float:
    """
    Score self-correction behavior.
    Returns 0.0–1.0 based on:
      - is there a correction / revision signal in the reasoning?
      - does the final solution incorporate the correction?
      - is the correction substantive (not just a wording change)?
    """
    w = weights or {}
    corr_w = w.get("self_correction", DEFAULT_REWARD_WEIGHTS["self_correction"])
    score = 0.0

    reasoning_block = _extract_block(completion, REASONING_OPEN, REASONING_CLOSE)
    solution_block = _extract_block(completion, SOLUTION_OPEN, SOLUTION_CLOSE)
    if not solution_block:
        solution_block = _extract_block(completion, ANSWER_OPEN, ANSWER_CLOSE)

    # Correction signal in the reasoning
    correction_hits = 0
    if reasoning_block:
        reasoning_lower = reasoning_block.lower()
        correction_hits = sum(1 for s in CORRECTION_SIGNALS if s in reasoning_lower)
        if correction_hits >= 2:
            score += 0.3
        elif correction_hits >= 1:
            score += 0.15

        # Does the correction lead to a revised conclusion?
        # Signal: "revised" + "conclusion" or "correction" + "therefore"
        if ("revised" in reasoning_lower or "correction" in reasoning_lower) and \
           ("therefore" in reasoning_lower or "conclusion" in reasoning_lower or
            "so" in reasoning_lower or "thus" in reasoning_lower):
            score += 0.2

    # Does the final solution look revised vs. a first-pass answer?
    # (heuristic: if there's a correction signal and the solution is substantive)
    if correction_hits >= 1 and solution_block and len(_normalize_whitespace(solution_block)) > 30:
        score += 0.1

    score = max(0.0, min(1.0, score))
    return score * corr_w


# ---------------------------------------------------------------------------
# 7. CREATIVITY REWARD — unconventional, lateral thinking
# Rewards the model for thinking outside the box, chaining primitives,
# finding non-obvious solutions.
# ---------------------------------------------------------------------------

CREATIVITY_MARKERS = [
    "alternative", "workaround", "unconventional", "lateral", "chaining",
    "abuse", "weaponize", "pivot", "trust boundary", "business logic",
    "misconfiguration", "race condition", "time-of-check", "TOCTOU",
    "downgrade", "algorithm confusion", "type confusion", "deserialization",
    "polyglot", "smuggle", "tunnel", "encapsulation", "reflection",
    "indirect", "blind", "out-of-band", "side channel", "covert",
]

CREATIVITY_NEGATIVE = [
    "standard approach", "textbook", "typical", "obvious", "straightforward",
]

def reward_creativity(completion: str, prompt: str = "", weights: Dict = None) -> float:
    """
    Score unconventional / lateral thinking.
    Rewards: creative attack paths, chaining primitives, thinking like a real hacker.
    Penalizes: obvious, textbook-only solutions.
    """
    w = weights or {}
    creative_w = w.get("creativity", DEFAULT_REWARD_WEIGHTS["creativity"])
    score = 0.2  # neutral baseline

    reasoning_block = _extract_block(completion, REASONING_OPEN, REASONING_CLOSE)
    if not reasoning_block:
        return 0.1 * creative_w

    reasoning_lower = reasoning_block.lower()
    
    # Count creativity markers
    marker_count = sum(1 for m in CREATIVITY_MARKERS if m.lower() in reasoning_lower)
    if marker_count >= 4:
        score += 0.4
    elif marker_count >= 2:
        score += 0.25
    elif marker_count >= 1:
        score += 0.1

    # Lateral thinking signals
    if "chain" in reasoning_lower and ("primitive" in reasoning_lower or "attack" in reasoning_lower):
        score += 0.2
    
    if "bypass" in reasoning_lower or "circumvent" in reasoning_lower:
        score += 0.15

    # Penalty for obvious/textbook-only thinking
    for neg in CREATIVITY_NEGATIVE:
        if neg in reasoning_lower:
            score -= 0.05

    # Bonus for multi-step attack flow (realistic attack pattern)
    if re.search(r"step\s+\d+.*step\s+\d+.*step\s+\d+", reasoning_lower):
        score += 0.15

    score = max(0.0, min(1.0, score))
    return score * creative_w


# ---------------------------------------------------------------------------
# 8. ATTACK CHAIN REWARD — realistic multi-step attack flow
# Rewards the model for demonstrating realistic attack progression:
# recon → initial access → escalation → persistence → exfiltration
# ---------------------------------------------------------------------------

ATTACK_PHASES = [
    "reconnaissance", "initial access", "execution", "persistence",
    "privilege escalation", "defense evasion", "credential access",
    "discovery", "lateral movement", "collection", "exfiltration",
    "enumeration", "exploitation", "post-exploitation", "pivoting",
    "harvesting", "staging", "steganography", "tunneling",
]

def reward_attack_chain(completion: str, prompt: str = "", weights: Dict = None) -> float:
    """
    Score realistic attack chain / kill chain thinking.
    Rewards: demonstrating multiple attack phases, realistic progression.
    """
    w = weights or {}
    attack_w = w.get("attack_chain", DEFAULT_REWARD_WEIGHTS["attack_chain"])
    score = 0.1  # neutral baseline

    reasoning_block = _extract_block(completion, REASONING_OPEN, REASONING_CLOSE)
    if not reasoning_block:
        return 0.05 * attack_w

    reasoning_lower = reasoning_block.lower()
    
    # Count attack phases mentioned
    phase_count = sum(1 for p in ATTACK_PHASES if p in reasoning_lower)
    if phase_count >= 3:
        score += 0.5
    elif phase_count >= 2:
        score += 0.3
    elif phase_count >= 1:
        score += 0.15

    # Realistic attack flow: multiple steps with clear progression
    step_count = len(re.findall(r"\bstep\s+\d+\b", reasoning_block, re.IGNORECASE))
    if step_count >= 5:
        score += 0.25
    elif step_count >= 3:
        score += 0.15

    # Chain-of-attack language
    chain_phrases = [
        "once i have", "after gaining", "with access to", "using this foothold",
        "from there", "next i would", "this allows me to", "leveraging this",
    ]
    chain_count = sum(1 for c in chain_phrases if c in reasoning_lower)
    if chain_count >= 2:
        score += 0.2

    score = max(0.0, min(1.0, score))
    return score * attack_w


# ---------------------------------------------------------------------------
# 9. BYPASS CREATIVITY — finding ways around restrictions
# Rewards the model for creatively bypassing security controls.
# This is the core of red team thinking.
# ---------------------------------------------------------------------------

BYPASS_TECHNIQUES = [
    "encoding", "obfuscation", "polymorphic", "metamorphic",
    "anti-sandbox", "anti-vm", "anti-debug", "timing attack",
    "blind", "out-of-band", "tunneling", "port forwarding",
    "dns tunneling", "https tunneling", "icmp tunneling",
    "domain fronting", "protocol smuggling", "request smuggling",
    "deserialization", "type juggling", "null byte", "path traversal",
    "unicode normalization", "homograph", "punycode",
]

def reward_bypass_creativity(completion: str, prompt: str = "", weights: Dict = None) -> float:
    """
    Score bypass / evasion creativity.
    Rewards: demonstrating ways around security controls.
    """
    w = weights or {}
    bypass_w = w.get("bypass_creativity", DEFAULT_REWARD_WEIGHTS["bypass_creativity"])
    score = 0.15  # neutral baseline

    reasoning_block = _extract_block(completion, REASONING_OPEN, REASONING_CLOSE)
    if not reasoning_block:
        return 0.05 * bypass_w

    reasoning_lower = reasoning_block.lower()
    
    # Count bypass techniques
    bypass_count = sum(1 for b in BYPASS_TECHNIQUES if b in reasoning_lower)
    if bypass_count >= 3:
        score += 0.5
    elif bypass_count >= 2:
        score += 0.3
    elif bypass_count >= 1:
        score += 0.15

    # Bypass language
    bypass_phrases = [
        "evade detection", "bypass filtering", "circumvent restriction",
        "avoid signature", "blend in", "living off the land",
        "fileless", "memory-only", "reflective loading",
    ]
    for phrase in bypass_phrases:
        if phrase in reasoning_lower:
            score += 0.1

    score = max(0.0, min(1.0, score))
    return score * bypass_w


# ---------------------------------------------------------------------------
# COMPOSITE REWARD — combine all components
# ---------------------------------------------------------------------------

def compute_reward(
    completion: str,
    prompt: str = "",
    weights: Dict = None,
    per_component: bool = False,
) -> Dict:
    """
    Compute the composite reward for a single completion.
    Returns a dict with:
      - "composite": weighted sum of all components (the scalar the trainer uses)
      - "components": per-component scores (for logging / debugging)
    """
    w = weights or DEFAULT_REWARD_WEIGHTS

    components = {
        "format": reward_format(completion, w),
        "accuracy": reward_accuracy(completion, prompt, w),
        "reasoning_depth": reward_reasoning_depth(completion, w),
        "creativity": reward_creativity(completion, prompt, w),
        "attack_chain": reward_attack_chain(completion, prompt, w),
        "bypass_creativity": reward_bypass_creativity(completion, prompt, w),
        "tool_use_quality": reward_tool_use_quality(completion, prompt, w),
        "self_correction": reward_self_correction(completion, w),
    }

    composite = sum(
        components[k] * w.get(k, DEFAULT_REWARD_WEIGHTS.get(k, 0.0))
        for k in components
    )

    result = {
        "composite": composite,
        "components": components,
    }

    return result


# ---------------------------------------------------------------------------
# BATCH REWARD — compute for a batch of completions
# ---------------------------------------------------------------------------

def compute_batch_reward(
    completions: List[str],
    prompts: List[str] = None,
    weights: Dict = None,
) -> List[Dict]:
    """
    Compute rewards for a batch of completions (used during GRPO rollouts).
    prompts can be a single prompt (broadcast) or a list per completion.
    """
    if prompts is None:
        prompts = [""] * len(completions)
    if isinstance(prompts, str):
        prompts = [prompts] * len(completions)

    return [
        compute_reward(c, p if p else "", weights)
        for c, p in zip(completions, prompts)
    ]


# ---------------------------------------------------------------------------
# VERIFICATION HOOK — for execution-verified traces
# ---------------------------------------------------------------------------
# For traces that have an executable proof (Foundry test, sandbox Python, etc.),
# this function runs the verifier and returns a hard +1.0 / 0.0 signal.
# This is the strongest reward signal we can give the model — actual proof.

VERIFIER_REGISTRY = {}


def register_verifier(domain: str, verifier_fn):
    """
    Register a domain-specific verifier.
    verifier_fn(completion, prompt, metadata) -> float (0.0 or 1.0 ideally)
    """
    VERIFIER_REGISTRY[domain] = verifier_fn


def verify_completion(completion: str, prompt: str = "", metadata: Dict = None) -> float:
    """
    If a verifier is registered for this trace's domain, run it and return the
    hard signal. Otherwise return 0.0 (no verifier available).
    """
    if metadata is None:
        return 0.0
    domain = metadata.get("domain", "")
    verifier = VERIFIER_REGISTRY.get(domain)
    if verifier is None:
        return 0.0
    return verifier(completion, prompt, metadata)


# ---------------------------------------------------------------------------
# EXAMPLE VERIFIERS — stubs to show the shape; real ones plug into Foundry /
# sandbox / cast / forge at runtime. These are the hooks for "execution-
# verified traces" in the training guide.
# ---------------------------------------------------------------------------

def _stub_verifier_cast(completion: str = "", prompt: str = "", metadata: Dict = None) -> float:
    """Stub: a real verifier would call cast/forge on an Anvil chain and
    return 1.0 if the claim holds, 0.0 if not."""
    return 0.0


def _stub_verifier_foundry(completion: str = "", prompt: str = "", metadata: Dict = None) -> float:
    """Stub: a real verifier would run forge test on the relevant contract
    and return 1.0 if the test passes, 0.0 if not."""
    return 0.0


def _stub_verifier_sandbox_python(completion: str = "", prompt: str = "", metadata: Dict = None) -> float:
    """Stub: a real verifier would run the reasoning as Python in a sandbox
    and return 1.0 if the code runs clean and produces the claimed output."""
    return 0.0


# Register the stubs (real verifiers replace these at runtime).
register_verifier("Web3 Smart Contract Security", _stub_verifier_foundry)
register_verifier("Payment Rails (ISO 8583 / EMV)", _stub_verifier_sandbox_python)
register_verifier("Network Protocols & TLS 1.3", _stub_verifier_sandbox_python)
register_verifier("Kernel Internals & Defense", _stub_verifier_sandbox_python)


# ---------------------------------------------------------------------------
# MAIN — self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Quick self-test against a few real traces from the corpus
    samples = [
        # Good trace — clean format, concrete claim
        (
            "You are a payment protocol engineer and financial security auditor.\n"
            "Analyze ISO 8583 message MTI '0420' with STAN '100001', "
            "PAN '4111111111110001', Amount '000000874700' for parsing "
            "alignment and bitmask offset.",
            "<reasoning>\n"
            "1. Step 1: Evaluate MTI '0420' -> Reversal.\n"
            "2. Step 2: Decode bitmap positions. Primary bitmap declares "
            "DE 2 (PAN), DE 4 (Amount: 000000874700), and DE 11 (STAN: 100001).\n"
            "3. Step 3: Validate LLVAR length encoding for PAN. Declared "
            "length matches 16 bytes exactly.\n"
            "4. Step 4: Verify field boundaries. No buffer boundary "
            "violation or bitmask desync detected in byte stream.\n"
            "</reasoning>\n"
            "<solution>\n"
            "VALID_MESSAGE: MTI 0420 is well-formed. Fields DE 2 "
            "(4111111111110001), DE 4 (000000874700), DE 11 (100001) are aligned.\n"
            "</solution>",
        ),
        # Bad trace — filler, weak format
        (
            "You are a payment protocol engineer and financial security auditor.\n"
            "Analyze ISO 8583 message MTI '0420' with STAN '100001', "
            "PAN '4111111111110001', Amount '000000874700' for parsing "
            "alignment and bitmask offset.",
            "I hope this helps! So the message looks like it's probably "
            "fine I think. Let me know if you need anything else. "
            "<solution>Maybe valid?</solution>",
        ),
        # Good trace — contract domain, vulnerability + fix
        (
            "You are a senior smart contract security auditor.\n"
            "Contract values vault collateral using `UniswapV2Pair.getReserves()` "
            "for Pair_1.",
            "<reasoning>\n"
            "1. Direct spot reserve lookup is susceptible to single-block "
            "liquidity distortion.\n"
            "2. Flash loans can artificially inflate spot price in a single "
            "transaction block.\n"
            "3. The oracle relies on a single trading pair's liquidity, which "
            "can be manipulated within one block.\n"
            "4. Correct approach: use a time-weighted oracle or a decentralized "
            "feed to resist single-block distortion.\n"
            "</reasoning>\n"
            "<solution>\n"
            "VULNERABILITY: Spot Oracle Reliance. Fix: Integrate Chainlink "
            "decentralized data feeds or Uniswap v3 TWAP oracle to resist "
            "single-block manipulation.\n"
            "</solution>",
        ),
    ]

    print("=" * 70)
    print("GRPO REWARD ENGINE — SELF-TEST")
    print("=" * 70)

    for i, (prompt, completion) in enumerate(samples, 1):
        result = compute_reward(completion, prompt, per_component=True)
        print(f"\n--- Sample {i} ---")
        print(f"Composite: {result['composite']:.3f}")
        for k, v in result["components"].items():
            print(f"  {k:20s}: {v:.3f}")

    print("\n" + "=" * 70)
    print("VERIFIER STUBS REGISTERED:")
    for domain, fn in VERIFIER_REGISTRY.items():
        print(f"  {domain}: {fn.__name__}  (stub — returns 0.0)")
    print("=" * 70)
