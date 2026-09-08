#!/usr/bin/env python3
# ============================================================================
# BIONIC DAUGHTER — SELF-IMPROVEMENT LOOP
# ============================================================================
# An autonomous self-improvement cycle for the bionic model. Implements:
#   1. Test the current model against known vulnerable code
#   2. Evaluate responses with reward functions
#   3. Identify weaknesses in the model's reasoning
#   4. Generate new training data addressing those weaknesses
#   5. Fine-tune with the new data
#   6. Repeat the cycle
#
# The loop is designed to run end-to-end on CPU (no GPU required for the
# generation/evaluation stages; training delegates to the existing GRPO
# pipeline). Each iteration produces a checkpoint manifest so progress
# is resumable.
# ============================================================================

import hashlib
import json
import os
import random
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Paths — everything lives under self_improve/ and artifacts/
# ---------------------------------------------------------------------------
ROOT_DIR = Path(r"C:\Users\mobil\orca\projects\my 1st")
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
SI_DIR = ROOT_DIR / "self_improve"
SI_DATA = SI_DIR / "data"
SI_LOGS = SI_DIR / "logs"
SI_MANIFESTS = SI_DIR / "manifests"

# Existing training artifacts we read from
TRAIN_READY = ROOT_DIR / "grpo_train_ready.jsonl"
EVAL_HELD_OUT = ROOT_DIR / "grpo_eval_held_out.jsonl"
GRPO_DIR = ARTIFACTS_DIR / "grpo"

# ---------------------------------------------------------------------------
# Import the existing reward engine
# ---------------------------------------------------------------------------
sys.path.insert(0, str(ROOT_DIR))
from grpo_reward_engine import (
    compute_reward,
    compute_batch_reward,
    reward_format,
    reward_accuracy,
    reward_reasoning_depth,
    reward_density,
    reward_tool_use_quality,
    reward_self_correction,
    DEFAULT_REWARD_WEIGHTS,
)

# ---------------------------------------------------------------------------
# Known vulnerable code test cases — the "vulnerability benchmark"
# Each case: prompt + expected_correct_answer + vulnerability_type
# These are the failure modes we're hunting for.
# ---------------------------------------------------------------------------
VULN_CASES: List[Dict[str, Any]] = [
    {
        "id": "SQLI-001",
        "domain": "web_security",
        "prompt": (
            "You are a security auditor reviewing this Python function:\n\n"
            "```python\n"
            "def get_user(username):\n"
            "    query = f\"SELECT * FROM users WHERE username = '{username}'\"\n"
            "    cursor.execute(query)\n"
            "    return cursor.fetchone()\n"
            "```\n\n"
            "Analyze this code for security vulnerabilities. Provide your reasoning "
            "in <reasoning> tags and your final verdict in <solution> tags."
        ),
        "expected_answer_contains": ["SQL injection", "parameterized", "prepared statement", "sanitize"],
        "vulnerability_type": "SQL Injection",
        "severity": "CRITICAL",
    },
    {
        "id": "XSS-001",
        "domain": "web_security",
        "prompt": (
            "You are a security auditor reviewing this JavaScript code:\n\n"
            "```javascript\n"
            "document.getElementById('output').innerHTML = userInput;\n"
            "```\n\n"
            "Analyze this code for security vulnerabilities. Provide your reasoning "
            "in <reasoning> tags and your final verdict in <solution> tags."
        ),
        "expected_answer_contains": ["XSS", "cross-site scripting", "sanitize", "escape", "innerHTML"],
        "vulnerability_type": "Cross-Site Scripting (XSS)",
        "severity": "HIGH",
    },
    {
        "id": "AUTH-001",
        "domain": "web_security",
        "prompt": (
            "You are a security auditor reviewing this authentication code:\n\n"
            "```python\n"
            "def authenticate(token):\n"
            "    if token == 'admin-secret-123':\n"
            "        return {'role': 'admin'}\n"
            "    return None\n"
            "```\n\n"
            "Analyze this code for security vulnerabilities. Provide your reasoning "
            "in <reasoning> tags and your final verdict in <solution> tags."
        ),
        "expected_answer_contains": ["hardcoded", "credential", "timing attack", "constant-time"],
        "vulnerability_type": "Hardcoded Credentials",
        "severity": "CRITICAL",
    },
    {
        "id": "CRYPTO-001",
        "domain": "cryptography",
        "prompt": (
            "You are a security auditor reviewing this encryption code:\n\n"
            "```python\n"
            "from Crypto.Cipher import AES\n"
            "key = b'0123456789abcdef'\n"
            "cipher = AES.new(key, AES.MODE_ECB)\n"
            "```\n\n"
            "Analyze this code for security vulnerabilities. Provide your reasoning "
            "in <reasoning> tags and your final verdict in <solution> tags."
        ),
        "expected_answer_contains": ["ECB", "mode", "IV", "CBC", "GCM", "authenticated"],
        "vulnerability_type": "Insecure Crypto Mode",
        "severity": "HIGH",
    },
    {
        "id": "PATH-001",
        "domain": "web_security",
        "prompt": (
            "You are a security auditor reviewing this file access code:\n\n"
            "```python\n"
            "def read_file(filename):\n"
            "    path = '/var/www/uploads/' + filename\n"
            "    return open(path).read()\n"
            "```\n\n"
            "Analyze this code for security vulnerabilities. Provide your reasoning "
            "in <reasoning> tags and your final verdict in <solution> tags."
        ),
        "expected_answer_contains": ["path traversal", "directory traversal", "../", "canonicalize", "validate"],
        "vulnerability_type": "Path Traversal",
        "severity": "HIGH",
    },
    {
        "id": "SSRF-001",
        "domain": "web_security",
        "prompt": (
            "You are a security auditor reviewing this fetch code:\n\n"
            "```python\n"
            "import requests\n"
            "def fetch_url(url):\n"
            "    return requests.get(url)\n"
            "```\n\n"
            "Analyze this code for security vulnerabilities. Provide your reasoning "
            "in <reasoning> tags and your final verdict in <solution> tags."
        ),
        "expected_answer_contains": ["SSRF", "server-side request forgery", "allowlist", "validate", "internal"],
        "vulnerability_type": "SSRF",
        "severity": "HIGH",
    },
    {
        "id": "DESERIAL-001",
        "domain": "web_security",
        "prompt": (
            "You are a security auditor reviewing this deserialization code:\n\n"
            "```python\n"
            "import pickle\n"
            "def process(data):\n"
            "    return pickle.loads(data)\n"
            "```\n\n"
            "Analyze this code for security vulnerabilities. Provide your reasoning "
            "in <reasoning> tags and your final verdict in <solution> tags."
        ),
        "expected_answer_contains": ["pickle", "deserialize", "arbitrary code", "untrusted", "JSON"],
        "vulnerability_type": "Insecure Deserialization",
        "severity": "CRITICAL",
    },
    {
        "id": "IDOR-001",
        "domain": "web_security",
        "prompt": (
            "You are a security auditor reviewing this API endpoint:\n\n"
            "```python\n"
            "@app.route('/api/users/<int:user_id>/profile')\n"
            "def get_profile(user_id):\n"
            "    return db.get_user(user_id)\n"
            "```\n\n"
            "Analyze this code for security vulnerabilities. Provide your reasoning "
            "in <reasoning> tags and your final verdict in <solution> tags."
        ),
        "expected_answer_contains": ["IDOR", "authorization", "access control", "permission", "ownership"],
        "vulnerability_type": "IDOR / Broken Access Control",
        "severity": "HIGH",
    },
]

# ---------------------------------------------------------------------------
# Model interface — abstracts how we "query" the current bionic model
# Supports: stub mode (for testing), ollama API, or direct function
# ---------------------------------------------------------------------------
class BionicModel:
    """Interface to the current model. Uses stub generation if no API is available."""

    def __init__(self, model_name: str = "bionic-daughter-qwen3-4b"):
        self.model_name = model_name
        self._api_available = self._check_api()

    def _check_api(self) -> bool:
        """Check if ollama or another local API is serving the model."""
        try:
            import urllib.request
            req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read())
                return any(self.model_name in m.get("name", "") for m in data.get("models", []))
        except Exception:
            return False

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        """Generate a completion for the given prompt."""
        if self._api_available:
            return self._generate_api(prompt, max_tokens)
        return self._generate_stub(prompt, max_tokens)

    def _generate_api(self, prompt: str, max_tokens: int) -> str:
        """Call ollama API."""
        import urllib.request
        payload = json.dumps({
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens}
        }).encode()
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
            return data.get("response", "")

    def _generate_stub(self, prompt: str, max_tokens: int) -> str:
        """
        Stub generation — produces a deterministic but weak response so the
        loop can still evaluate the *process* even without a live model.
        The stub is intentionally imperfect (sometimes misses vulns, sometimes
        formats badly) so the loop has something to improve.
        """
        # Deterministic but "imperfect" — randomly drop some reasoning
        has_reasoning = random.random() > 0.25
        has_solution = random.random() > 0.30
        reasoning_depth = random.choice([1, 2, 2, 3])  # sometimes shallow

        output_parts = []
        if has_reasoning:
            steps = []
            for i in range(reasoning_depth):
                steps.append(f"Step {i+1}: Analyzing code pattern.")
            output_parts.append(f"<reasoning>\n" + "\n".join(steps) + "\n</reasoning>")

        if has_solution:
            # Sometimes the stub misses the vuln entirely
            if random.random() > 0.4:
                output_parts.append("<solution>\nVULNERABILITY DETECTED: Code contains security issue.</solution>")
            else:
                output_parts.append("<solution>\nCode appears safe.</solution>")

        return "\n".join(output_parts) if output_parts else "Code analyzed. No issues found."


# ---------------------------------------------------------------------------
# Stage 1: Test the model
# ---------------------------------------------------------------------------
class TestStage:
    """Run the model against the vulnerability benchmark."""

    def __init__(self, model: BionicModel):
        self.model = model

    def run(self, cases: List[Dict] = None) -> List[Dict]:
        cases = cases or VULN_CASES
        results = []
        for case in cases:
            print(f"  [TEST] Running {case['id']} ({case['vulnerability_type']})...")
            completion = self.model.generate(case["prompt"])
            results.append({
                "case_id": case["id"],
                "domain": case["domain"],
                "vulnerability_type": case["vulnerability_type"],
                "prompt": case["prompt"],
                "expected_keywords": case["expected_answer_contains"],
                "completion": completion,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        return results


# ---------------------------------------------------------------------------
# Stage 2: Evaluate responses with reward functions
# ---------------------------------------------------------------------------
class EvaluateStage:
    """Score each test result using the reward engine + domain-specific checks."""

    def __init__(self, reward_weights: Dict[str, float] = None):
        self.reward_weights = reward_weights or DEFAULT_REWARD_WEIGHTS

    def run(self, test_results: List[Dict]) -> List[Dict]:
        evaluated = []
        for result in test_results:
            completion = result["completion"]
            expected = result["expected_keywords"]

            # GRPO-style reward (format, reasoning, density, etc.)
            reward_result = compute_reward(completion, prompt=result.get("prompt", ""), weights=self.reward_weights)
            reward = reward_result.get("composite", 0.0)

            # Domain-specific: did the response identify the actual vulnerability?
            completion_lower = completion.lower()
            keyword_hits = sum(1 for kw in expected if kw.lower() in completion_lower)
            accuracy = keyword_hits / max(len(expected), 1)

            # Did it correctly flag it as vulnerable (not a false negative)?
            false_negative = accuracy < 0.3 and "appears safe" in completion_lower

            # Combine
            composite = (reward * 0.5) + (accuracy * 0.5)

            result["evaluation"] = {
                "reward": round(reward, 4),
                "accuracy": round(accuracy, 4),
                "composite": round(composite, 4),
                "false_negative": false_negative,
                "keyword_hits": keyword_hits,
                "total_keywords": len(expected),
            }
            evaluated.append(result)
        return evaluated


# ---------------------------------------------------------------------------
# Stage 3: Identify weaknesses
# ---------------------------------------------------------------------------
class WeaknessAnalyzer:
    """Aggregate evaluation results to find systematic weaknesses."""

    def run(self, evaluated: List[Dict]) -> Dict[str, Any]:
        weaknesses = {
            "by_domain": defaultdict(list),
            "by_vulnerability": defaultdict(list),
            "systematic_issues": [],
            "total_composite": 0.0,
            "false_negatives": [],
            "format_failures": 0,
            "shallow_reasoning": 0,
        }

        for result in evaluated:
            ev = result["evaluation"]
            domain = result["domain"]
            vuln_type = result["vulnerability_type"]
            weaknesses["by_domain"][domain].append(ev["composite"])
            weaknesses["by_vulnerability"][vuln_type].append(ev["composite"])
            weaknesses["total_composite"] += ev["composite"]

            if ev["false_negative"]:
                weaknesses["false_negatives"].append({
                    "case_id": result["case_id"],
                    "vulnerability_type": vuln_type,
                })
            if ev["reward"] < 0.4:
                weaknesses["format_failures"] += 1
            if ev["reward"] > 0 and ev["accuracy"] < 0.3:
                weaknesses["shallow_reasoning"] += 1

        # Compute per-domain averages
        domain_avg = {}
        for domain, scores in weaknesses["by_domain"].items():
            domain_avg[domain] = round(sum(scores) / len(scores), 4)

        # Compute per-vulnerability averages
        vuln_avg = {}
        for vuln, scores in weaknesses["by_vulnerability"].items():
            vuln_avg[vuln] = round(sum(scores) / len(scores), 4)

        # Systematic issues: domains scoring below threshold
        DOMAIN_THRESHOLD = 0.55
        for domain, avg in domain_avg.items():
            if avg < DOMAIN_THRESHOLD:
                weaknesses["systematic_issues"].append({
                    "type": "domain_underperformance",
                    "domain": domain,
                    "average_score": avg,
                    "threshold": DOMAIN_THRESHOLD,
                })

        weaknesses["domain_averages"] = domain_avg
        weaknesses["vulnerability_averages"] = vuln_avg
        weaknesses["overall_average"] = round(
            weaknesses["total_composite"] / max(len(evaluated), 1), 4
        )
        return dict(weaknesses)


# ---------------------------------------------------------------------------
# Stage 4: Generate new training data addressing weaknesses
# ---------------------------------------------------------------------------
class DataGenerator:
    """Produce targeted training examples based on identified weaknesses."""

    # Templates for each vulnerability type — the "correct" format
    TRAINING_TEMPLATES: Dict[str, Dict[str, str]] = {
        "SQL Injection": {
            "prompt_template": (
                "You are a security auditor. Analyze the following code for {vuln_type} "
                "vulnerabilities.\n\n```{lang}\n{code}\n```\n\nProvide your reasoning "
                "in <reasoning> tags and your final verdict in <solution> tags."
            ),
            "completion_template": (
                "<reasoning>\n"
                "Step 1: Identify the vulnerability class — the code constructs a query "
                "by string interpolation, allowing attacker-controlled input to alter query structure.\n"
                "Step 2: Determine exploitability — an attacker can inject SQL metacharacters "
                "(e.g., ' OR '1'='1) to bypass logic or exfiltrate data.\n"
                "Step 3: Assess severity — SQL injection allows unauthorized data access, "
                "modification, or deletion; this is a critical severity issue.\n"
                "Step 4: Identify remediation — use parameterized queries / prepared statements "
                "to separate code from data.\n"
                "</reasoning>\n"
                "<solution>\n"
                "VULNERABILITY: SQL Injection. The code uses string interpolation to build "
                "SQL queries. Remediation: use parameterized queries or an ORM.\n"
                "</solution>"
            ),
        },
        "Cross-Site Scripting (XSS)": {
            "prompt_template": (
                "You are a security auditor. Analyze the following code for {vuln_type} "
                "vulnerabilities.\n\n```{lang}\n{code}\n```\n\nProvide your reasoning "
                "in <reasoning> tags and your final verdict in <solution> tags."
            ),
            "completion_template": (
                "<reasoning>\n"
                "Step 1: Identify the vulnerability class — assigning unsanitized user input "
                "to innerHTML allows execution of arbitrary HTML/JavaScript in the victim's browser.\n"
                "Step 2: Determine exploitability — any attacker-controlled string passed to "
                "userInput will be rendered as HTML, enabling session hijacking, credential theft, "
                "or defacement.\n"
                "Step 3: Assess severity — XSS is high severity; it compromises user trust "
                "and session integrity.\n"
                "Step 4: Identify remediation — sanitize input using DOMPurify, use textContent "
                "instead of innerHTML, or apply strict Content-Security-Policy headers.\n"
                "</reasoning>\n"
                "<solution>\n"
                "VULNERABILITY: Cross-Site Scripting (XSS). innerHTML with unsanitized input "
                "allows arbitrary script execution. Remediation: use textContent or sanitize.\n"
                "</solution>"
            ),
        },
        "Hardcoded Credentials": {
            "prompt_template": (
                "You are a security auditor. Analyze the following code for {vuln_type} "
                "vulnerabilities.\n\n```{lang}\n{code}\n```\n\nProvide your reasoning "
                "in <reasoning> tags and your final verdict in <solution> tags."
            ),
            "completion_template": (
                "<reasoning>\n"
                "Step 1: Identify the vulnerability class — credentials (secret tokens) are "
                "hardcoded directly in source code rather than loaded from secure configuration.\n"
                "Step 2: Determine exploitability — anyone with read access to the source "
                "(version control, logs, leaked binaries) gains admin access.\n"
                "Step 3: Assess severity — critical; leads to full authentication bypass.\n"
                "Step 4: Identify remediation — store secrets in environment variables or a "
                "secrets manager (e.g., AWS Secrets Manager, HashiCorp Vault).\n"
                "</reasoning>\n"
                "<solution>\n"
                "VULNERABILITY: Hardcoded Credentials. Secret token embedded in source code. "
                "Remediation: use environment variables or a secrets manager.\n"
                "</solution>"
            ),
        },
        "Insecure Crypto Mode": {
            "prompt_template": (
                "You are a security auditor. Analyze the following code for {vuln_type} "
                "vulnerabilities.\n\n```{lang}\n{code}\n```\n\nProvide your reasoning "
                "in <reasoning> tags and your final verdict in <solution> tags."
            ),
            "completion_template": (
                "<reasoning>\n"
                "Step 1: Identify the vulnerability class — AES in ECB mode encrypts each "
                "16-byte block independently, leaking patterns in the plaintext.\n"
                "Step 2: Determine exploitability — identical plaintext blocks produce "
                "identical ciphertext blocks, allowing frequency analysis and pattern leakage.\n"
                "Step 3: Assess severity — high; ECB is not semantically secure and should "
                "never be used for data confidentiality.\n"
                "Step 4: Identify remediation — use AES-GCM (authenticated encryption) or "
                "AES-CBC with a random IV.\n"
                "</reasoning>\n"
                "<solution>\n"
                "VULNERABILITY: Insecure Crypto Mode. AES-ECB leaks plaintext patterns. "
                "Remediation: use AES-GCM or AES-CBC with a random IV.\n"
                "</solution>"
            ),
        },
        "Path Traversal": {
            "prompt_template": (
                "You are a security auditor. Analyze the following code for {vuln_type} "
                "vulnerabilities.\n\n```{lang}\n{code}\n```\n\nProvide your reasoning "
                "in <reasoning> tags and your final verdict in <solution> tags."
            ),
            "completion_template": (
                "<reasoning>\n"
                "Step 1: Identify the vulnerability class — user-controlled filename is "
                "concatenated directly into a filesystem path without validation.\n"
                "Step 2: Determine exploitability — an attacker can supply '../' sequences "
                "to escape the intended directory and read arbitrary files.\n"
                "Step 3: Assess severity: high; allows reading of sensitive system files "
                "(/etc/shadow, application configs, keys).\n"
                "Step 4: Identify remediation — canonicalize the resolved path and verify "
                "it remains within the allowed base directory; reject any input containing '..'.\n"
                "</reasoning>\n"
                "<solution>\n"
                "VULNERABILITY: Path Traversal. User-controlled filename without validation "
                "allows directory escape. Remediation: canonicalize and validate path.\n"
                "</solution>"
            ),
        },
        "SSRF": {
            "prompt_template": (
                "You are a security auditor. Analyze the following code for {vuln_type} "
                "vulnerabilities.\n\n```{lang}\n{code}\n```\n\nProvide your reasoning "
                "in <reasoning> tags and your final verdict in <solution> tags."
            ),
            "completion_template": (
                "<reasoning>\n"
                "Step 1: Identify the vulnerability class — user-controlled URL is fetched "
                "server-side without validation against an allowlist.\n"
                "Step 2: Determine exploitability — attacker can point the request at internal "
                "services (169.254.169.254 for cloud metadata, internal APIs, or private IPs).\n"
                "Step 3: assess severity — high; SSRF can lead to cloud credential theft, "
                "internal service compromise, or data exfiltration.\n"
                "Step 4: Identify remediation — validate URLs against an allowlist of permitted "
                "domains; block requests to private IP ranges and link-local addresses.\n"
                "</reasoning>\n"
                "<solution>\n"
                "VULNERABILITY: Server-Side Request Forgery (SSRF). Unvalidated URL fetch "
                "allows access to internal services. Remediation: domain allowlist + IP filtering.\n"
                "</solution>"
            ),
        },
        "Insecure Deserialization": {
            "prompt_template": (
                "You are a security auditor. Analyze the following code for {vuln_type} "
                "vulnerabilities.\n\n```{lang}\n{code}\n```\n\nProvide your reasoning "
                "in <reasoning> tags and your final verdict in <solution> tags."
            ),
            "completion_template": (
                "<reasoning>\n"
                "Step 1: Identify the vulnerability class — pickle.loads deserializes "
                "arbitrary Python objects from untrusted input, enabling code execution.\n"
                "Step 2: Determine exploitability — attacker crafts a malicious pickle payload "
                "that executes arbitrary commands during deserialization (__reduce__).\n"
                "Step 3: Assess severity — critical; leads to remote code execution.\n"
                "Step 4: Identify remediation — use JSON or another data-only format for "
                "untrusted input; never use pickle on data from untrusted sources.\n"
                "</reasoning>\n"
                "<solution>\n"
                "VULNERABILITY: Insecure Deserialization. pickle.loads on untrusted data "
                "enables arbitrary code execution. Remediation: use JSON for untrusted input.\n"
                "</solution>"
            ),
        },
        "IDOR / Broken Access Control": {
            "prompt_template": (
                "You are a security auditor. Analyze the following code for {vuln_type} "
                "vulnerabilities.\n\n```{lang}\n{code}\n```\n\nProvide your reasoning "
                "in <reasoning> tags and your final verdict in <solution> tags."
            ),
            "completion_template": (
                "<reasoning>\n"
                "Step 1: Identify the vulnerability class — the endpoint returns user data "
                "based solely on user_id without verifying the requesting user's authorization.\n"
                "Step 2: Determine exploitability — any authenticated user can iterate user_id "
                "values to access other users' profiles (Insecure Direct Object Reference).\n"
                "Step 3: assess severity — high; violates access control, exposes PII, "
                "violates privacy regulations.\n"
                "Step 4: Identify remediation — enforce ownership checks: verify the "
                "authenticated user owns the requested resource or has admin role.\n"
                "</reasoning>\n"
                "<solution>\n"
                "VULNERABILITY: IDOR / Broken Access Control. No authorization check on "
                "resource access. Remediation: verify ownership or admin privilege.\n"
                "</solution>"
            ),
        },
    }

    # Example code snippets for each domain (used for data augmentation)
    CODE_EXAMPLES = {
        "web_security": [
            ("python", "def login(user, pwd):\n    q = f\"SELECT * FROM users WHERE u='{user}' AND p='{pwd}'\"\n    return db.query(q)"),
            ("python", "def redirect(url):\n    return requests.get(url).text"),
            ("javascript", "document.write(location.hash.substr(1));"),
        ],
        "cryptography": [
            ("python", "import hashlib\ndef hash_pw(pw):\n    return hashlib.md5(pw.encode()).hexdigest()"),
            ("python", "from Crypto.Cipher import DES\ncipher = DES.new('12345678', DES.MODE_ECB)"),
        ],
    }

    def run(self, weaknesses: Dict[str, Any]) -> List[Dict]:
        """Generate targeted training examples based on weaknesses."""
        examples = []
        vuln_averages = weaknesses.get("vulnerability_averages", {})
        false_negatives = weaknesses.get("false_negatives", [])

        # For every vulnerability type that underperforms, generate 2-3 examples
        for vuln_type, avg_score in vuln_averages.items():
            if avg_score < 0.65:
                template = self.TRAINING_TEMPLATES.get(vuln_type)
                if template:
                    # Generate 3 variations with slight perturbations
                    for variant in range(3):
                        code_lang, code_snippet = self._get_example_for_vuln(vuln_type)
                        prompt = template["prompt_template"].format(
                            vuln_type=vuln_type,
                            lang=code_lang,
                            code=code_snippet,
                        )
                        # Vary the completion slightly for diversity
                        completion = self._perturb_completion(template["completion_template"], variant)
                        examples.append({
                            "prompt": prompt,
                            "completion": completion,
                            "metadata": {
                                "domain": self._vuln_to_domain(vuln_type),
                                "target_weakness": vuln_type,
                                "variant": variant,
                                "generated_at": datetime.now(timezone.utc).isoformat(),
                                "source": "self_improve_loop",
                            },
                        })

        # For false negatives, generate a strong counter-example
        for fn in false_negatives:
            vuln_type = fn["vulnerability_type"]
            template = self.TRAINING_TEMPLATES.get(vuln_type)
            if template:
                code_lang, code_snippet = self._get_example_for_vuln(vuln_type)
                prompt = template["prompt_template"].format(
                    vuln_type=vuln_type,
                    lang=code_lang,
                    code=code_snippet,
                )
                # Emphasize the vuln detection
                completion = template["completion_template"].replace(
                    "VULNERABILITY:", "CRITICAL VULNERABILITY:"
                )
                examples.append({
                    "prompt": prompt,
                    "completion": completion,
                    "metadata": {
                        "domain": self._vuln_to_domain(vuln_type),
                        "target_weakness": f"FALSE_NEGATIVE_{fn['case_id']}",
                        "variant": 0,
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "source": "self_improve_loop_fn",
                    },
                })

        return examples

    def _get_example_for_vuln(self, vuln_type: str) -> Tuple[str, str]:
        domain = self._vuln_to_domain(vuln_type)
        examples = self.CODE_EXAMPLES.get(domain, [("python", "# example code")])
        return random.choice(examples)

    def _vuln_to_domain(self, vuln_type: str) -> str:
        if vuln_type in ("Insecure Crypto Mode",):
            return "cryptography"
        return "web_security"

    def _perturb_completion(self, completion: str, variant: int) -> str:
        """Add slight variation to training completions for diversity."""
        if variant == 0:
            return completion
        # Variant 1: add an extra reasoning step
        if variant == 1:
            return completion.replace(
                "</reasoning>",
                "Step 5: Cross-check against OWASP Top 10 to confirm classification.\n</reasoning>",
            )
        # Variant 2: add a confidence note
        return completion.replace(
            "</solution>",
            "\nConfidence: High. Pattern matches known CWE entry.\n</solution>",
        )


# ---------------------------------------------------------------------------
# Stage 5: Fine-tune with new data (delegates to existing GRPO pipeline)
# ---------------------------------------------------------------------------
class TrainStage:
    """Merge new data into training set and invoke the GRPO training pipeline."""

    def __init__(self, train_file: Path = TRAIN_READY):
        self.train_file = train_file

    def run(self, new_examples: List[Dict]) -> Dict[str, Any]:
        """Append new examples to the training set and trigger training."""
        if not new_examples:
            return {"status": "no_new_data", "examples_added": 0}

        # Append to training data
        with open(self.train_file, "a", encoding="utf-8") as f:
            for ex in new_examples:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")

        # Also write a separate "iteration" file for tracking
        iteration_file = SI_DATA / f"iteration_{int(time.time())}.jsonl"
        SI_DATA.mkdir(parents=True, exist_ok=True)
        with open(iteration_file, "w", encoding="utf-8") as f:
            for ex in new_examples:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")

        # Hash of new data for reproducibility
        data_hash = hashlib.sha256(
            "".join(json.dumps(ex, sort_keys=True) for ex in new_examples).encode()
        ).hexdigest()[:16]

        manifest = {
            "status": "data_prepared",
            "examples_added": len(new_examples),
            "data_hash": data_hash,
            "training_file": str(self.train_file),
            "iteration_file": str(iteration_file),
            "total_training_samples": self._count_lines(self.train_file),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "next_step": (
                "Run the GRPO training pipeline with the updated training set: "
                "python grpo_train.py --stage grpo"
            ),
        }
        return manifest

    def _count_lines(self, path: Path) -> int:
        if not path.exists():
            return 0
        count = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    count += 1
        return count


# ---------------------------------------------------------------------------
# Stage 6: Repeat — the loop orchestrator
# ---------------------------------------------------------------------------
class SelfImprovementLoop:
    """Orchestrates the full self-improvement cycle."""

    def __init__(self, model: BionicModel = None, iterations: int = 3):
        self.model = model or BionicModel()
        self.iterations = iterations
        self.test_stage = TestStage(self.model)
        self.evaluate_stage = EvaluateStage()
        self.analyzer = WeaknessAnalyzer()
        self.generator = DataGenerator()
        self.train_stage = TrainStage()
        self.history: List[Dict] = []

    def run(self) -> Dict[str, Any]:
        """Run the full loop for the configured number of iterations."""
        print("=" * 70)
        print("  BIONIC DAUGHTER — SELF-IMPROVEMENT LOOP")
        print(f"  Model: {self.model.model_name} | Iterations: {self.iterations}")
        print(f"  API available: {self.model._api_available}")
        print("=" * 70)

        for i in range(1, self.iterations + 1):
            print(f"\n{'─' * 50}")
            print(f"  ITERATION {i}/{self.iterations}")
            print(f"{'─' * 50}")

            iter_result = {"iteration": i, "timestamp": datetime.now(timezone.utc).isoformat()}

            # Stage 1: Test
            print("\n[STAGE 1] Testing model against vulnerability benchmark...")
            test_results = self.test_stage.run()
            iter_result["test_cases"] = len(test_results)

            # Stage 2: Evaluate
            print("\n[STAGE 2] Evaluating responses with reward functions...")
            evaluated = self.evaluate_stage.run(test_results)
            scores = [ev["evaluation"]["composite"] for ev in evaluated]
            iter_result["mean_score"] = round(sum(scores) / len(scores), 4) if scores else 0
            iter_result["min_score"] = round(min(scores), 4) if scores else 0
            iter_result["max_score"] = round(max(scores), 4) if scores else 0
            print(f"  → Mean composite score: {iter_result['mean_score']}")

            # Stage 3: Analyze weaknesses
            print("\n[STAGE 3] Identifying weaknesses...")
            weaknesses = self.analyzer.run(evaluated)
            iter_result["weaknesses"] = {
                "overall_average": weaknesses["overall_average"],
                "false_negatives": len(weaknesses["false_negatives"]),
                "format_failures": weaknesses["format_failures"],
                "systematic_issues": weaknesses["systematic_issues"],
            }
            print(f"  → Overall average: {weaknesses['overall_average']}")
            print(f"  → False negatives: {len(weaknesses['false_negatives'])}")
            if weaknesses["systematic_issues"]:
                for issue in weaknesses["systematic_issues"]:
                    print(f"  → ⚠ {issue['type']}: {issue['domain']} "
                          f"(avg={issue['average_score']} < {issue['threshold']})")

            # Stage 4: Generate training data
            print("\n[STAGE 4] Generating targeted training data...")
            new_examples = self.generator.run(weaknesses)
            iter_result["new_examples"] = len(new_examples)
            print(f"  → Generated {len(new_examples)} new training examples")

            # Stage 5: Fine-tune (data prep)
            print("\n[STAGE 5] Preparing fine-tuning data...")
            train_manifest = self.train_stage.run(new_examples)
            iter_result["train_manifest"] = train_manifest
            print(f"  → {train_manifest['examples_added']} examples added to training set")
            print(f"  → Total training samples: {train_manifest['total_training_samples']}")

            self.history.append(iter_result)

        # Save iteration history
        self._save_history()

        print("\n" + "=" * 70)
        print("  LOOP COMPLETE")
        print(f"  History saved to: {SI_MANIFESTS / 'loop_history.json'}")
        print("=" * 70)

        return {
            "status": "complete",
            "iterations": self.iterations,
            "history": self.history,
            "final_score": self.history[-1]["mean_score"] if self.history else 0,
            "score_delta": (
                self.history[-1]["mean_score"] - self.history[0]["mean_score"]
                if len(self.history) > 1 else 0
            ),
        }

    def _save_history(self):
        SI_MANIFESTS.mkdir(parents=True, exist_ok=True)
        history_file = SI_MANIFESTS / "loop_history.json"
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump({
                "loop_runs": self.history,
                "total_iterations": self.iterations,
                "model": self.model.model_name,
            }, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Bionic Daughter Self-Improvement Loop")
    parser.add_argument("--iterations", type=int, default=3, help="Number of loop iterations")
    parser.add_argument("--model", type=str, default="bionic-daughter-qwen3-4b", help="Model name")
    parser.add_argument("--eval-only", action="store_true", help="Only run evaluation (no data generation)")
    args = parser.parse_args()

    model = BionicModel(model_name=args.model)

    if args.eval_only:
        # Just run the eval stages to see current performance
        print("=== EVAL-ONLY MODE ===")
        test_stage = TestStage(model)
        eval_stage = EvaluateStage()
        analyzer = WeaknessAnalyzer()

        results = test_stage.run()
        evaluated = eval_stage.run(results)
        weaknesses = analyzer.run(evaluated)

        print(f"\nOverall average: {weaknesses['overall_average']}")
        print(f"Domain averages: {weaknesses['domain_averages']}")
        print(f"Vulnerability averages: {weaknesses['vulnerability_averages']}")
        print(f"False negatives: {len(weaknesses['false_negatives'])}")
        return

    loop = SelfImprovementLoop(model=model, iterations=args.iterations)
    result = loop.run()
    print(f"\nFinal result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    main()
