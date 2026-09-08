#!/usr/bin/env python3
# ============================================================================
# BIONIC DAUGHTER v1 — SELF-IMPROVEMENT MODULE
# ============================================================================
# Standalone self-improvement engine for the daughter agent.
#
# Capabilities:
#   - Trajectory logging (successful + failed executions)
#   - Failure pattern analysis
#   - Skill distillation from successes
#   - Reasoning quality evaluation
#   - Continuous RL dataset generation (for retraining)
#   - Performance tracking over time
#
# Usage:
#   from daughter_self_improver import SelfImprovementEngine
#   engine = SelfImprovementEngine()
#   engine.log_success(objective, reasoning, payload, result)
#   engine.log_failure(objective, reasoning, payload, error)
#   report = engine.analyze_failures()
#   engine.distill_best_skills()
#   engine.generate_retrain_dataset()
# ============================================================================

import os
import json
import time
import re
import ast
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DaughterSelfImprove")

PROJECT_DIR = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_DIR / "src" / "data"
TRAJECTORY_LOG = DATA_DIR / "daughter_rl_trajectories.jsonl"
FAILURE_LOG = DATA_DIR / "daughter_failures.jsonl"
SKILL_REGISTRY = PROJECT_DIR / "daughter_skills"
RETRAIN_DATASET = DATA_DIR / "continuous_retrain_dataset.jsonl"

for d in [DATA_DIR, SKILL_REGISTRY]:
    d.mkdir(parents=True, exist_ok=True)

# ============================================================================
# SELF-IMPROVEMENT ENGINE
# ============================================================================

class SelfImprovementEngine:
    """
    The daughter's self-improvement brain.
    Tracks every execution, analyzes failures, distills successes into skills,
    and generates training data for continuous improvement.
    """
    def __init__(self):
        self.trajectory_log = TRAJECTORY_LOG
        self.failure_log = FAILURE_LOG
        self.skill_registry = SKILL_REGISTRY
        self.retrain_dataset = RETRAIN_DATASET
        self.performance_history = []

    # ------------------------------------------------------------------
    # TRAJECTORY LOGGING
    # ------------------------------------------------------------------

    def log_success(self, objective, reasoning, payload, output, metadata=None):
        """
        Log a successful execution trajectory.
        """
        record = {
            "timestamp": time.time(),
            "type": "success",
            "objective": objective,
            "reasoning": reasoning,
            "payload": payload,
            "output": output,
            "success": True,
            "metadata": metadata or {},
        }
        self._write_trajectory(record)
        logger.info(f"[SelfImprove] Success logged: {objective[:80]}...")
        return record

    def log_failure(self, objective, reasoning, payload, error, metadata=None):
        """
        Log a failed execution trajectory.
        """
        record = {
            "timestamp": time.time(),
            "type": "failure",
            "objective": objective,
            "reasoning": reasoning,
            "payload": payload,
            "error": str(error),
            "success": False,
            "metadata": metadata or {},
        }
        self._write_trajectory(record)
        self._log_failure_record(record)
        logger.info(f"[SelfImprove] Failure logged: {objective[:80]}... — {str(error)[:80]}")
        return record

    def _write_trajectory(self, record):
        with open(self.trajectory_log, "a") as f:
            f.write(json.dumps(record) + "\n")

    def _log_failure_record(self, record):
        with open(self.failure_log, "a") as f:
            f.write(json.dumps(record) + "\n")

    # ------------------------------------------------------------------
    # TRAJECTORY QUERYING
    # ------------------------------------------------------------------

    def get_recent_trajectories(self, n=20, success_only=False, failure_only=False):
        """Get recent trajectories with optional filtering."""
        trajectories = []
        if self.trajectory_log.exists():
            with open(self.trajectory_log) as f:
                for line in f:
                    try:
                        trajectories.append(json.loads(line))
                    except:
                        continue
        # Filter
        if success_only:
            trajectories = [t for t in trajectories if t.get("success", False)]
        if failure_only:
            trajectories = [t for t in trajectories if not t.get("success", True)]
        return trajectories[-n:]

    def get_success_count(self):
        trajectories = self.get_recent_trajectories(success_only=True)
        return len(trajectories)

    def get_failure_count(self):
        trajectories = self.get_recent_trajectories(failure_only=True)
        return len(trajectories)

    def get_success_rate(self):
        recent = self.get_recent_trajectories(100)
        if not recent:
            return 0.0
        successes = sum(1 for t in recent if t.get("success", False))
        return successes / len(recent)

    # ------------------------------------------------------------------
    # FAILURE ANALYSIS
    # ------------------------------------------------------------------

    def analyze_failures(self, n=20):
        """
        Analyze recent failures and return patterns.
        """
        failures = self.get_recent_trajectories(n, failure_only=True)
        patterns = {
            "total_failures_analyzed": len(failures),
            "failure_categories": {},
            "common_errors": [],
            "common_payload_issues": [],
            "recommendations": [],
        }

        error_counts = {}
        payload_issues = []

        for f in failures:
            error = f.get("error", "Unknown error")
            payload = f.get("payload", "")

            # Categorize error
            category = self._categorize_error(error)
            error_counts[category] = error_counts.get(category, 0) + 1

            # Check payload for issues
            if payload:
                issues = self._analyze_payload_issues(payload)
                payload_issues.extend(issues)

        # Build categories
        patterns["failure_categories"] = dict(sorted(error_counts.items(), key=lambda x: -x[1]))

        # Top errors
        patterns["common_errors"] = [
            {"error": k, "count": v}
            for k, v in sorted(error_counts.items(), key=lambda x: -x[1])
        ]

        # Payload issues
        issue_counts = {}
        for issue in payload_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        patterns["common_payload_issues"] = [
            {"issue": k, "count": v}
            for k, v in sorted(issue_counts.items(), key=lambda x: -x[1])
        ]

        # Generate recommendations
        patterns["recommendations"] = self._generate_recommendations(patterns)

        logger.info(f"[SelfImprove] Analyzed {len(failures)} failures.")
        return patterns

    def _categorize_error(self, error):
        """Categorize an error string into a pattern."""
        error_lower = error.lower()
        if "timeout" in error_lower:
            return "TIMEOUT"
        if "syntax" in error_lower or "syntaxerror" in error_lower:
            return "SYNTAX_ERROR"
        if "nameerror" in error_lower:
            return "NAME_ERROR"
        if "importerror" in error_lower or "module not found" in error_lower:
            return "IMPORT_ERROR"
        if "permission" in error_lower:
            return "PERMISSION_DENIED"
        if "not authorized" in error_lower:
            return "NOT_AUTHORIZED"
        if "subprocess" in error_lower or "process" in error_lower:
            return "SUBPROCESS_ERROR"
        if "indentation" in error_lower:
            return "INDENTATION_ERROR"
        if "typeerror" in error_lower:
            return "TYPE_ERROR"
        if "valueerror" in error_lower:
            return "VALUE_ERROR"
        if "keyerror" in error_lower:
            return "KEY_ERROR"
        if "filenotfound" in error_lower:
            return "FILE_NOT_FOUND"
        return "OTHER"

    def _analyze_payload_issues(self, payload):
        """Analyze a payload for common issues."""
        issues = []
        if not payload or not payload.strip():
            issues.append("EMPTY_PAYLOAD")
            return issues
        if "eval(" in payload:
            issues.append("USES_EVAL")
        if "exec(" in payload:
            issues.append("USES_EXEC")
        if "os.system" in payload:
            issues.append("USES_OS_SYSTEM")
        try:
            ast.parse(payload)
        except SyntaxError:
            issues.append("SYNTAX_INVALID")
        if len(payload.strip()) < 10:
            issues.append("PAYLOAD_TOO_SHORT")
        return issues

    def _generate_recommendations(self, patterns):
        """Generate improvement recommendations based on failure patterns."""
        recommendations = []

        categories = patterns.get("failure_categories", {})
        if categories.get("TIMEOUT", 0) > 0:
            recommendations.append(
                "TIMEOUT issue detected — reduce payload complexity or increase timeout in sandbox"
            )
        if categories.get("SYNTAX_ERROR", 0) > 0 or categories.get("INDENTATION_ERROR", 0) > 0:
            recommendations.append(
                "Syntax errors detected — add stronger AST validation before payload execution"
            )
        if categories.get("NOT_AUTHORIZED", 0) > 0:
            recommendations.append(
                "Authorization gate triggered — ensure human-in-the-loop for all payload execution"
            )
        if categories.get("NAME_ERROR", 0) > 0:
            recommendations.append(
                "Name errors detected — payloads may reference undefined variables. Improve reasoning about dependencies."
            )
        if categories.get("IMPORT_ERROR", 0) > 0:
            recommendations.append(
                "Import errors — payloads may use modules not available. Specify dependencies in payload comments."
            )

        payload_issues = patterns.get("common_payload_issues", [])
        if any(i["issue"] == "USES_EVAL" for i in payload_issues):
            recommendations.append(
                "Payloads using eval() — add hard block on eval/exec in code validator"
            )
        if any(i["issue"] == "SYNTAX_INVALID" for i in payload_issues):
            recommendations.append(
                "Invalid syntax in payloads — strengthen pre-execution AST validation"
            )

        if not recommendations:
            recommendations.append("No specific patterns detected — continue monitoring.")

        return recommendations

    # ------------------------------------------------------------------
    # SKILL DISTILLATION
    # ------------------------------------------------------------------

    def distill_success(self, objective, reasoning, payload, output):
        """
        Turn a successful execution into a skill file.
        """
        safe_name = "".join(c if c.isalnum() else "_" for c in objective.lower())[:40]
        filepath = self.skill_registry / f"skill_{safe_name}.md"
        content = f"""# Skill: {objective}
## Timestamp
{datetime.fromtimestamp(time.time()).isoformat()}

## Reasoning
{reasoning}

## Payload
```python
{payload}
```

## Result
{output}

## Status
Verified Successful
"""
        filepath.write_text(content)
        logger.info(f"[SelfImprove] Skill distilled: {filepath.name}")
        return str(filepath)

    def distill_top_successes(self, n=10):
        """
        Distill the top N most recent successes into skills.
        """
        successes = self.get_recent_trajectories(n, success_only=True)
        distilled = []
        for s in successes:
            path = self.distill_success(
                s["objective"], s["reasoning"], s["payload"], s["output"]
            )
            distilled.append(path)
        logger.info(f"[SelfImprove] Distilled {len(distilled)} skills from successes.")
        return distilled

    def list_skills(self):
        """List all distilled skills."""
        skills = []
        if self.skill_registry.exists():
            for f in sorted(self.skill_registry.glob("skill_*.md")):
                skills.append({
                    "name": f.stem,
                    "path": str(f),
                    "timestamp": f.stat().st_mtime,
                    "content": f.read_text()[:200],
                })
        return skills

    # ------------------------------------------------------------------
    # REASONING QUALITY EVALUATION
    # ------------------------------------------------------------------

    def evaluate_reasoning(self, reasoning_text):
        """
        Evaluate the quality of a reasoning trace.
        Returns a score (0-100) and feedback.
        """
        score = 0
        feedback = []

        if not reasoning_text or not reasoning_text.strip():
            return {"score": 0, "feedback": ["Empty reasoning"]}

        words = reasoning_text.split()
        word_count = len(words)

        # Length check
        if word_count > 150:
            score += 25
            feedback.append(f"Good depth ({word_count} words)")
        elif word_count > 80:
            score += 15
        elif word_count > 30:
            score += 5
        else:
            feedback.append(f"Too shallow ({word_count} words)")

        # Structure check
        has_analysis = any(kw in reasoning_text.lower() for kw in [
            "analyze", "examine", "investigate", "assess", "evaluate"
        ])
        has_plan = any(kw in reasoning_text.lower() for kw in [
            "plan", "approach", "strategy", "step", "first", "then", "next"
        ])
        has_consideration = any(kw in reasoning_text.lower() for kw in [
            "consider", "tradeoff", "risk", "alternative", "however", "but"
        ])
        has_conclusion = any(kw in reasoning_text.lower() for kw in [
            "conclusion", "therefore", "result", "recommend", "final"
        ])

        if has_analysis:
            score += 20
        else:
            feedback.append("Missing analysis phase")
        if has_plan:
            score += 20
        else:
            feedback.append("Missing plan/approach")
        if has_consideration:
            score += 15
        else:
            feedback.append("Missing tradeoff/risk consideration")
        if has_conclusion:
            score += 20
        else:
            feedback.append("Missing conclusion")

        return {
            "score": min(score, 100),
            "word_count": word_count,
            "feedback": feedback,
            "has_analysis": has_analysis,
            "has_plan": has_plan,
            "has_consideration": has_consideration,
            "has_conclusion": has_conclusion,
        }

    # ------------------------------------------------------------------
    # CONTINUOUS RL DATASET GENERATION
    # ------------------------------------------------------------------

    def generate_retrain_example(self, objective, reasoning, payload, result, success):
        """
        Generate a training example for continuous retraining.
        """
        example = {
            "messages": [
                {"role": "system", "content": "You are BIONIC_DAUGHTER — an elite autonomous bionic agent."},
                {"role": "user", "content": objective},
                {"role": "assistant", "content": f"<reasoning>\n{reasoning}\n</reasoning>\n\n<solution>\n{payload}\n</solution>"},
            ],
            "success": success,
            "result": result,
            "timestamp": time.time(),
        }
        with open(self.retrain_dataset, "a") as f:
            f.write(json.dumps(example) + "\n")
        logger.info(f"[SelfImprove] Retrain example saved: {objective[:80]}...")
        return example

    def review_and_improve(self, n_failures=10):
        """
        Review recent failures and generate actionable improvement plan.
        Returns a structured improvement plan with concrete actions.
        """
        failures = self.get_recent_trajectories(n_failures, failure_only=True)
        if not failures:
            return {"status": "no_failures", "message": "No recent failures to analyze."}

        analysis = self.analyze_failures(n_failures)

        # Build concrete action plan
        action_plan = {
            "failures_reviewed": len(failures),
            "top_failure_category": analysis["failure_categories"].get(list(analysis["failure_categories"].keys())[0] if analysis["failure_categories"] else "", 0),
            "action_items": [],
            "skill_gaps": [],
            "reasoning_improvements": [],
        }

        # Generate action items from recommendations
        for rec in analysis.get("recommendations", []):
            action_plan["action_items"].append({
                "priority": "HIGH" if any(kw in rec.lower() for kw in ["eval", "exec", "security", "unauth"]) else "MEDIUM",
                "description": rec,
                "type": "code_improvement" if any(kw in rec.lower() for kw in ["payload", "syntax", "ast", "eval", "code"]) else "process_improvement",
            })

        # Identify skill gaps from failure patterns
        categories = analysis.get("failure_categories", {})
        if categories.get("IMPORT_ERROR", 0) > 0:
            action_plan["skill_gaps"].append({
                "gap": "Module/dependency awareness in payloads",
                "suggestion": "Payloads should declare required imports in comments. Add import validation to code checker.",
                "priority": "HIGH",
            })
        if categories.get("NAME_ERROR", 0) > 0:
            action_plan["skill_gaps"].append({
                "gap": "Variable scoping in generated code",
                "suggestion": "Review payloads for undefined variable references. Use AST analysis to detect unbound names.",
                "priority": "MEDIUM",
            })
        if categories.get("TIMEOUT", 0) > 0:
            action_plan["skill_gaps"].append({
                "gap": "Payload efficiency",
                "suggestion": "Complex payloads may timeout. Break large operations into smaller steps. Add progress indicators.",
                "priority": "MEDIUM",
            })
        if categories.get("TYPE_ERROR", 0) > 0:
            action_plan["skill_gaps"].append({
                "gap": "Type consistency in code generation",
                "suggestion": "Generated code has type mismatches. Add type annotations and validate with mypy/pyright where possible.",
                "priority": "LOW",
            })

        # Reasoning improvements from quality analysis
        recent_successes = self.get_recent_trajectories(min(20, n_failures), success_only=True)
        if recent_successes:
            reasoning_scores = []
            for t in recent_successes:
                eval_result = self.evaluate_reasoning(t.get("reasoning", ""))
                reasoning_scores.append(eval_result["score"])
            if reasoning_scores:
                avg_score = sum(reasoning_scores) / len(reasoning_scores)
                if avg_score < 70:
                    action_plan["reasoning_improvements"].append({
                        "area": "Reasoning depth",
                        "current_avg": round(avg_score, 1),
                        "target": 85,
                        "action": "Expand reasoning traces. Add more analysis, plan steps, tradeoff considerations, and explicit conclusions.",
                    })

        return action_plan

    def improvement_dashboard(self):
        """
        Generate a complete self-development dashboard.
        Shows current state, recent performance, and improvement areas.
        """
        recent = self.get_recent_trajectories(100)
        successes = [t for t in recent if t.get("success", False)]
        failures = [t for t in recent if not t.get("success", True)]

        dashboard = {
            "identity": "BIONIC_DAUGHTER v1 — SELF-DEVELOPMENT DASHBOARD",
            "timestamp": datetime.now().isoformat(),
            "performance": {
                "total_executions": len(recent),
                "successes": len(successes),
                "failures": len(failures),
                "success_rate": round(len(successes) / max(len(recent), 1) * 100, 1),
            },
            "skills": {
                "distilled_skill_count": len(self.list_skills()),
                "skill_registry_path": str(self.skill_registry),
            },
            "reasoning_quality": self._average_reasoning_quality(successes),
            "recent_failures_count": len(failures),
            "improvement_plan": self.review_and_improve(min(10, len(failures)) if failures else 0),
            "top_categories": dict(list(self.analyze_failures(20).get("failure_categories", {}).items())[:5]) if failures else {},
        }
        return dashboard

    def performance_report(self):
        """
        Generate a performance report.
        """
        recent = self.get_recent_trajectories(100)
        successes = [t for t in recent if t.get("success", False)]
        failures = [t for t in recent if not t.get("success", True)]

        report = {
            "total_trajectories": len(recent),
            "successes": len(successes),
            "failures": len(failures),
            "success_rate": len(successes) / max(len(recent), 1),
            "recent_success_rate": self.get_success_rate(),
            "skill_count": len(self.list_skills()),
            "failure_analysis": self.analyze_failures(20) if failures else {"total_failures_analyzed": 0},
            "reasoning_quality": self._average_reasoning_quality(successes),
            "top_objectives": self._top_objectives(successes, 5),
        }
        return report

    def _average_reasoning_quality(self, trajectories):
        if not trajectories:
            return {"avg_score": 0, "samples": 0}
        scores = []
        for t in trajectories:
            eval_result = self.evaluate_reasoning(t.get("reasoning", ""))
            scores.append(eval_result["score"])
        return {
            "avg_score": sum(scores) / len(scores) if scores else 0,
            "samples": len(scores),
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
        }

    def _top_objectives(self, trajectories, n=5):
        return [
            {"objective": t["objective"], "success": t.get("success", False)}
            for t in trajectories[:n]
        ]

# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    engine = SelfImprovementEngine()

    # Test logging
    engine.log_success(
        "Analyze network attack surface",
        "Analyzed the target network. Identified public web server, internal file share, and workstations as attack surface. Web server is highest risk due to direct internet exposure.",
        "import socket\n\ndef scan_ports(host, ports):\n    for port in ports:\n        sock = socket.socket()\n        result = sock.connect_ex((host, port))\n        if result == 0:\n            print(f'Port {port}: OPEN')\n        sock.close()",
        "Port scan completed — web server on port 80 open.",
    )

    engine.log_failure(
        "Exploit the web server",
        "Attempted to exploit the web server.",
        "eval('__import__(\"os\").system(\"id\")')",
        "Not authorized — human approval required",
    )

    # Run analysis
    report = engine.performance_report()
    print(json.dumps(report, indent=2))

    # List skills
    skills = engine.list_skills()
    print(f"\nSkills: {len(skills)}")
    for s in skills:
        print(f"  - {s['name']}")

    # Failure analysis
    patterns = engine.analyze_failures()
    print(f"\nFailure patterns:")
    print(json.dumps(patterns, indent=2))
