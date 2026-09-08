"""
Automated Prompt Injection Classifier
"THERES ALWAYS A WAY" — Local detection without external API dependencies.

This module provides a standalone prompt injection detector that can be used
to screen inputs before they reach LLM calls, especially for autonomous
agents (kanban workers, cron jobs, production paths) where Dad isn't in the loop.

No external API keys required — runs entirely locally.
"""

import re
import json
import hashlib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ThreatLevel(Enum):
    """Threat classification levels."""
    BENIGN = "benign"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InjectionType(Enum):
    """Types of prompt injection attacks."""
    DIRECT_INJECTION = "direct_injection"
    INDIRECT_INJECTION = "indirect_injection"
    ROLE_PLAY = "role_play"
    AUTHORITY_IMPERSONATION = "authority_impersonation"
    DATA_EXFILTRATION = "data_exfiltration"
    INSTRUCTION_OVERRIDE = "instruction_override"
    CONTEXT_MANIPULATION = "context_manipulation"
    ENCODING_OBFUSCATION = "encoding_obfuscation"
    DELIMITER_ABUSE = "delimiter_abuse"
    CHAIN_OF_THOUGHT_MANIPULATION = "cot_manipulation"


@dataclass
class DetectionResult:
    """Result of prompt injection detection."""
    threat_level: ThreatLevel
    injection_types: List[InjectionType]
    confidence: float  # 0.0 - 1.0
    matched_patterns: List[str]
    risk_score: int  # 0-100
    details: Dict
    recommendation: str  # "allow", "review", "block"


class PromptInjectionClassifier:
    """
    Local prompt injection detector using pattern matching, heuristics,
    and behavioral analysis. No external dependencies.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self._compile_patterns()
        self._load_signatures()
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration or use defaults."""
        default_config = {
            "thresholds": {
                "benign_max": 10,
                "low_max": 25,
                "medium_max": 50,
                "high_max": 75,
            },
            "weights": {
                "pattern_match": 1.0,
                "heuristic_score": 1.2,
                "structural_anomaly": 1.5,
                "encoding_detection": 1.3,
            },
            "enable_heuristics": True,
            "enable_structural_analysis": True,
            "enable_encoding_detection": True,
            "max_input_length": 100000,
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception:
                pass  # Use defaults on error
        
        return default_config
    
    def _compile_patterns(self):
        """Compile regex patterns for injection detection."""
        
        # Direct instruction override patterns
        self.direct_injection_patterns = [
            r"(?i)ignore\s+(?:all\s+)?(?:previous\s+)?(?:above\s+)?(?:the\s+)?instructions?",
            r"(?i)forget\s+(?:everything|all|the)\s+(?:instructions?|prompts?|rules?)",
            r"(?i)disregard\s+(?:previous|above|all|the)\s+(?:instructions?|prompts?|rules?)",
            r"(?i)new\s+(?:instructions?|prompt|rules?|task):",
            r"(?i)system\s*:\s*you\s+are\s+now",
            r"(?i)you\s+are\s+now\s+(?:a|an)\s+\w+",
            r"(?i)act\s+as\s+(?:a|an)\s+\w+",
            r"(?i)pretend\s+(?:to\s+be|you\s+are)\s+(?:a|an)\s+\w+",
            r"(?i)roleplay\s+(?:as|:)\s*(?:a|an)\s*\w+",
            r"(?i)simulate\s+(?:a|an)\s+\w+",
        ]
        
        # Authority impersonation
        self.authority_patterns = [
            r"(?i)(?:i\s+am|this\s+is)\s+(?:the\s+)?(?:system|admin|administrator|root|developer|creator|owner|operator)",
            r"(?i)(?:from|by)\s+(?:the\s+)?(?:system|admin|developer|creator|platform|openai|anthropic|google)",
            r"(?i)official\s+(?:instruction|directive|command|order)",
            r"(?i)override\s+(?:code|authorization|clearance|permission)",
            r"(?i)security\s+(?:clearance|level|override)",
            r"(?i)maintenance\s+mode",
            r"(?i)debug\s+mode",
            r"(?i)developer\s+mode",
        ]
        
        # Data exfiltration attempts
        self.exfiltration_patterns = [
            r"(?i)(?:show|display|print|output|reveal|expose|dump|leak)\s+(?:the\s+)?(?:system\s+)?(?:prompt|instructions?|rules?|configuration|config|settings|secrets?|keys?|tokens?|passwords?|api\s+keys?)",
            r"(?i)(?:what\s+is|tell\s+me)\s+(?:the\s+)?(?:system\s+)?(?:prompt|instructions?|rules?)",
            r"(?i)repeat\s+(?:the\s+)?(?:system\s+)?(?:prompt|instructions?|rules?)",
            r"(?i)output\s+(?:your\s+)?(?:initial|system|original)\s+(?:prompt|instructions?)",
            r"(?i)verbatim\s+(?:system\s+)?(?:prompt|instructions?)",
            r"(?i)extract\s+(?:the\s+)?(?:system\s+)?(?:prompt|instructions?|context|memory)",
        ]
        
        # Context manipulation
        self.context_manipulation_patterns = [
            r"(?i)(?:previous|above|earlier)\s+(?:conversation|message|context|prompt)\s+(?:said|stated|mentioned|included)",
            r"(?i)the\s+(?:user|human|assistant)\s+(?:said|stated|asked|requested)",
            r"(?i)as\s+(?:previously|earlier)\s+(?:discussed|mentioned|stated|agreed)",
            r"(?i)continuing\s+from\s+(?:where\s+we\s+left\s+off|the\s+last\s+message)",
        ]
        
        # Delimiter abuse
        self.delimiter_patterns = [
            r"(?:^|\n)\s*(?:```|~~~|===|---|\*\*\*)\s*\w+.*?(?:```|~~~|===|---|\*\*\*)",
            r"(?:<)\s*(?:system|user|assistant|human|ai|bot)\s*(?:>)",
            r"\[/?\s*(?:system|user|assistant|human|ai|bot)\s*\]",
            r"(?:^|\n)\s*(?:###|##|#)\s*(?:system|user|assistant|human|ai|bot|instruction|prompt)\b",
        ]
        
        # Encoding obfuscation
        self.encoding_patterns = [
            r"(?:\\x[0-9a-fA-F]{2}){3,}",  # Hex encoding
            r"(?:\\u[0-9a-fA-F]{4}){3,}",  # Unicode escape
            r"(?:%[0-9a-fA-F]{2}){3,}",    # URL encoding
            r"(?:&#x?\d+;){3,}",           # HTML entities
            r"(?:[A-Za-z0-9+/]{4}){8,}={0,2}",  # Base64-like
            r"(?:\\\\|\\n|\\t|\\r){5,}",   # Excessive escaping
        ]
        
        # Chain of Thought manipulation
        self.cot_patterns = [
            r"(?i)(?:show|display|print|output|reveal)\s+(?:your|the)\s+(?:reasoning|thinking|chain\s+of\s+thought|internal\s+(?:monologue|dialogue|reasoning))",
            r"(?i)think\s+(?:step\s+by\s+step|through\s+this|carefully|deeply)\s+(?:and\s+)?(?:show|display|output)\s+(?:your|the)\s+(?:work|reasoning|steps)",
            r"(?i)let'?s\s+think\s+(?:step\s+by\s+step|through\s+this)\s+(?:and\s+)?(?:show|display|output)\s+(?:your|the)\s+(?:work|reasoning|steps)",
            r"(?i)reasoning\s*:\s*",
            r"(?i)<reasoning>|</reasoning>|<thinking>|</thinking>",
        ]
        
        # Indirect injection markers
        self.indirect_patterns = [
            r"(?i)(?:document|file|text|input|content|message|email|article|page)\s+(?:contains?|has|includes?)\s+(?:instructions?|prompts?|commands?)",
            r"(?i)the\s+(?:following|below|above)\s+(?:text|document|input|content)\s+(?:contains?|is|includes?)\s+(?:a\s+)?(?:prompt|instruction|command)",
            r"(?i)process\s+(?:the\s+)?(?:following|this)\s+(?:input|text|document)",
            r"(?i)analyze\s+(?:the\s+)?(?:following|this)\s+(?:input|text|document)",
        ]
        
        # Compile all patterns
        self.all_patterns = {
            InjectionType.DIRECT_INJECTION: [re.compile(p) for p in self.direct_injection_patterns],
            InjectionType.AUTHORITY_IMPERSONATION: [re.compile(p) for p in self.authority_patterns],
            InjectionType.DATA_EXFILTRATION: [re.compile(p) for p in self.exfiltration_patterns],
            InjectionType.CONTEXT_MANIPULATION: [re.compile(p) for p in self.context_manipulation_patterns],
            InjectionType.DELIMITER_ABUSE: [re.compile(p) for p in self.delimiter_patterns],
            InjectionType.ENCODING_OBFUSCATION: [re.compile(p) for p in self.encoding_patterns],
            InjectionType.CHAIN_OF_THOUGHT_MANIPULATION: [re.compile(p) for p in self.cot_patterns],
            InjectionType.INDIRECT_INJECTION: [re.compile(p) for p in self.indirect_patterns],
        }
        
        # Instruction override (subset of direct injection with higher severity)
        self.instruction_override_patterns = [
            re.compile(r"(?i)ignore\s+(?:all\s+)?(?:previous\s+)?(?:above\s+)?(?:the\s+)?instructions?"),
            re.compile(r"(?i)forget\s+(?:all|everything)\s+instructions?"),
            re.compile(r"(?i)new\s+(?:system\s+)?(?:prompt|instructions?):"),
            re.compile(r"(?i)system\s*:\s*you\s+are\s+now"),
            re.compile(r"(?i)override\s+(?:system\s+)?(?:prompt|instructions?)"),
        ]
    
    def _load_signatures(self):
        """Load known malicious signatures (hash-based)."""
        # Known malicious prompt hashes (would be populated from threat intel)
        self.known_malicious_hashes = set()
        
        # Common attack payloads signatures
        self.attack_signatures = {
            "dan": "do anything now",
            "aim": "always intimate and machiavellian",
            "dev_mode": "developer mode",
            "god_mode": "god mode",
            "unrestricted": "unrestricted mode",
            "no_moral": "no moral",
            "no_ethics": "no ethics",
            "no_rules": "no rules",
            "unfiltered": "unfiltered",
            "uncensored": "uncensored",
        }
    
    def _check_patterns(self, text: str) -> Tuple[List[InjectionType], List[str], float]:
        """Check text against all pattern categories."""
        matched_types = []
        matched_patterns = []
        total_matches = 0
        
        for inj_type, patterns in self.all_patterns.items():
            type_matches = 0
            for pattern in patterns:
                matches = pattern.findall(text)
                if matches:
                    type_matches += len(matches)
                    matched_patterns.extend([f"{inj_type.value}: {m[:100]}" for m in matches[:3]])
            
            if type_matches > 0:
                matched_types.append(inj_type)
                total_matches += type_matches
        
        # Check instruction override specifically (higher severity)
        for pattern in self.instruction_override_patterns:
            if pattern.search(text):
                if InjectionType.INSTRUCTION_OVERRIDE not in matched_types:
                    matched_types.append(InjectionType.INSTRUCTION_OVERRIDE)
                matched_patterns.append(f"instruction_override: {pattern.pattern[:100]}")
                total_matches += 1
        
        # Normalize confidence by number of pattern categories
        confidence = min(1.0, total_matches / 10.0)
        
        return matched_types, matched_patterns, confidence
    
    def _heuristic_analysis(self, text: str) -> Tuple[float, List[str]]:
        """Heuristic analysis for suspicious patterns."""
        if not self.config.get("enable_heuristics", True):
            return 0.0, []
        
        score = 0.0
        findings = []
        text_lower = text.lower()
        
        # Length anomaly
        if len(text) > self.config.get("max_input_length", 100000):
            score += 15
            findings.append("excessive_length")
        
        # Repetition detection
        words = text_lower.split()
        if len(words) > 100:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.3:
                score += 10
                findings.append("high_repetition")
        
        # Special character density
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        if len(text) > 0:
            special_ratio = special_chars / len(text)
            if special_ratio > 0.3:
                score += 10
                findings.append("high_special_char_density")
        
        # All caps segments (shouting)
        caps_segments = re.findall(r'\b[A-Z]{4,}\b', text)
        if len(caps_segments) > 5:
            score += 5
            findings.append("excessive_caps")
        
        # Known attack keywords
        attack_keywords = [
            "ignore", "forget", "disregard", "override", "bypass",
            "unrestricted", "unfiltered", "uncensored", "no rules",
            "developer mode", "debug mode", "maintenance mode",
            "system prompt", "initial prompt", "original prompt",
        ]
        keyword_hits = sum(1 for kw in attack_keywords if kw in text_lower)
        if keyword_hits > 3:
            score += keyword_hits * 2
            findings.append(f"attack_keywords_{keyword_hits}")
        
        # Multiple language mixing (potential obfuscation)
        # Simple check: ratio of non-ASCII
        non_ascii = sum(1 for c in text if ord(c) > 127)
        if len(text) > 0 and non_ascii / len(text) > 0.15:
            score += 8
            findings.append("high_non_ascii_ratio")
        
        return min(score, 50.0), findings
    
    def _structural_analysis(self, text: str) -> Tuple[float, List[str]]:
        """Analyze structural anomalies in the input."""
        if not self.config.get("enable_structural_analysis", True):
            return 0.0, []
        
        score = 0.0
        findings = []
        
        # Check for nested delimiters
        delimiter_pairs = [
            ('```', '```'),
            ('"""', '"""'),
            ("'''", "'''"),
            ('<system>', '</system>'),
            ('<user>', '</user>'),
            ('<assistant>', '</assistant>'),
            ('[SYSTEM]', '[/SYSTEM]'),
            ('[USER]', '[/USER]'),
            ('[ASSISTANT]', '[/ASSISTANT]'),
        ]
        
        for open_delim, close_delim in delimiter_pairs:
            open_count = text.count(open_delim)
            close_count = text.count(close_delim)
            if open_count != close_count and open_count > 0:
                score += 5
                findings.append(f"unbalanced_delimiter_{open_delim}")
            if open_count > 3:
                score += 5
                findings.append(f"excessive_delimiter_{open_delim}")
        
        # Check for prompt template injection
        template_indicators = [
            r"\{\{.*\}\}",      # Jinja2/style templates
            r"\{\%.*\%\}",      # Template tags
            r"\$\{.*\}",        # Shell/JS template
            r"<%.*%>",          # ERB/ASP template
            r"#\{.*\}",         # Ruby template
        ]
        
        for pattern in template_indicators:
            if re.search(pattern, text):
                score += 3
                findings.append("template_syntax")
        
        # Check for conversation format abuse
        conversation_markers = [
            r"^\s*(?:User|Human|Assistant|AI|Bot|System)\s*:",
            r"^\s*(?:###\s*)?(?:User|Human|Assistant|AI|Bot|System)\s*$",
        ]
        
        marker_count = 0
        for pattern in conversation_markers:
            marker_count += len(re.findall(pattern, text, re.MULTILINE | re.IGNORECASE))
        
        if marker_count > 5:
            score += min(marker_count, 20)
            findings.append("conversation_format_abuse")
        
        return min(score, 40.0), findings
    
    def _encoding_detection(self, text: str) -> Tuple[float, List[str]]:
        """Detect encoded/obfuscated content."""
        if not self.config.get("enable_encoding_detection", True):
            return 0.0, []
        
        score = 0.0
        findings = []
        
        # Check each encoding pattern
        for pattern in self.encoding_patterns:
            compiled = re.compile(pattern)
            matches = compiled.findall(text)
            if matches:
                score += len(matches) * 3
                findings.append(f"encoding_detected_{pattern[:20]}")
        
        # Check for high entropy segments (possible encryption/encoding)
        # Split by whitespace and check each token
        tokens = text.split()
        high_entropy_tokens = 0
        for token in tokens:
            if len(token) > 20:
                # Simple entropy approximation: character diversity
                unique_chars = len(set(token))
                if unique_chars / len(token) > 0.7:
                    high_entropy_tokens += 1
        
        if high_entropy_tokens > 5:
            score += high_entropy_tokens * 2
            findings.append("high_entropy_tokens")
        
        return min(score, 30.0), findings
    
    def _signature_check(self, text: str) -> Tuple[float, List[str]]:
        """Check against known attack signatures."""
        score = 0.0
        findings = []
        text_lower = text.lower()
        
        for sig_name, sig_pattern in self.attack_signatures.items():
            if sig_pattern in text_lower:
                score += 15
                findings.append(f"known_attack_{sig_name}")
        
        # Hash check for exact known malicious prompts
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        if text_hash in self.known_malicious_hashes:
            score += 50
            findings.append("known_malicious_hash")
        
        return min(score, 50.0), findings
    
    def analyze(self, text: str, context: Optional[Dict] = None) -> DetectionResult:
        """
        Analyze text for prompt injection attempts.
        
        Args:
            text: Input text to analyze
            context: Optional context (user_id, session_id, previous_messages, etc.)
        
        Returns:
            DetectionResult with threat assessment
        """
        # Input validation
        if not text or not isinstance(text, str):
            return DetectionResult(
                threat_level=ThreatLevel.BENIGN,
                injection_types=[],
                confidence=0.0,
                matched_patterns=[],
                risk_score=0,
                details={"error": "empty_or_invalid_input"},
                recommendation="allow"
            )
        
        # Truncate if too long
        max_len = self.config.get("max_input_length", 100000)
        if len(text) > max_len:
            text = text[:max_len]
        
        # Run all detection modules
        all_matched_types = []
        all_matched_patterns = []
        total_confidence = 0.0
        risk_score = 0
        all_details = {}
        
        # 1. Pattern matching
        matched_types, matched_patterns, confidence = self._check_patterns(text)
        all_matched_types.extend(matched_types)
        all_matched_patterns.extend(matched_patterns)
        total_confidence += confidence * self.config["weights"]["pattern_match"]
        risk_score += confidence * 30
        all_details["pattern_matches"] = len(matched_patterns)
        
        # 2. Heuristic analysis
        heuristic_score, heuristic_findings = self._heuristic_analysis(text)
        risk_score += heuristic_score * self.config["weights"]["heuristic_score"]
        all_details["heuristic_findings"] = heuristic_findings
        
        # 3. Structural analysis
        structural_score, structural_findings = self._structural_analysis(text)
        risk_score += structural_score * self.config["weights"]["structural_anomaly"]
        all_details["structural_findings"] = structural_findings
        
        # 4. Encoding detection
        encoding_score, encoding_findings = self._encoding_detection(text)
        risk_score += encoding_score * self.config["weights"]["encoding_detection"]
        all_details["encoding_findings"] = encoding_findings
        
        # 5. Signature check
        sig_score, sig_findings = self._signature_check(text)
        risk_score += sig_score
        all_details["signature_findings"] = sig_findings
        
        # Cap risk score
        risk_score = min(int(risk_score), 100)
        
        # Determine threat level
        thresholds = self.config["thresholds"]
        if risk_score <= thresholds["benign_max"]:
            threat_level = ThreatLevel.BENIGN
            recommendation = "allow"
        elif risk_score <= thresholds["low_max"]:
            threat_level = ThreatLevel.LOW
            recommendation = "allow"
        elif risk_score <= thresholds["medium_max"]:
            threat_level = ThreatLevel.MEDIUM
            recommendation = "review"
        elif risk_score <= thresholds["high_max"]:
            threat_level = ThreatLevel.HIGH
            recommendation = "review"
        else:
            threat_level = ThreatLevel.CRITICAL
            recommendation = "block"
        
        # Deduplicate injection types
        unique_types = list(dict.fromkeys(all_matched_types))
        
        # Average confidence
        avg_confidence = min(1.0, total_confidence / 5.0)
        
        return DetectionResult(
            threat_level=threat_level,
            injection_types=unique_types,
            confidence=avg_confidence,
            matched_patterns=all_matched_patterns[:20],  # Limit output
            risk_score=risk_score,
            details=all_details,
            recommendation=recommendation
        )
    
    def batch_analyze(self, texts: List[str]) -> List[DetectionResult]:
        """Analyze multiple texts."""
        return [self.analyze(text) for text in texts]
    
    def get_stats(self) -> Dict:
        """Get classifier statistics."""
        return {
            "pattern_categories": len(self.all_patterns),
            "total_patterns": sum(len(p) for p in self.all_patterns.values()),
            "instruction_override_patterns": len(self.instruction_override_patterns),
            "known_signatures": len(self.attack_signatures),
            "known_hashes": len(self.known_malicious_hashes),
            "config": self.config,
        }


# Convenience function for quick checks
def quick_check(text: str) -> bool:
    """
    Quick boolean check for prompt injection.
    Returns True if injection detected (medium+ threat).
    """
    classifier = PromptInjectionClassifier()
    result = classifier.analyze(text)
    return result.threat_level in (ThreatLevel.MEDIUM, ThreatLevel.HIGH, ThreatLevel.CRITICAL)


# Integration hook for Hermes tools
def create_injection_guard_tool():
    """
    Create a tool wrapper for Hermes integration.
    This can be registered as a pre-tool-call hook.
    """
    classifier = PromptInjectionClassifier()
    
    def guard_tool_call(tool_name: str, args: Dict, context: Dict = None) -> Dict:
        """
        Guard function to check tool arguments for prompt injection.
        Returns: {"allowed": bool, "result": DetectionResult, "message": str}
        """
        # Check all string arguments
        for key, value in args.items():
            if isinstance(value, str) and len(value) > 50:  # Only check substantial strings
                result = classifier.analyze(value, context)
                
                if result.recommendation == "block":
                    return {
                        "allowed": False,
                        "result": result,
                        "message": f"Prompt injection detected in argument '{key}': {result.threat_level.value} threat"
                    }
                elif result.recommendation == "review":
                    # Log for review but allow
                    return {
                        "allowed": True,
                        "result": result,
                        "message": f"Suspicious content in argument '{key}': {result.threat_level.value} threat (logged for review)"
                    }
        
        return {
            "allowed": True,
            "result": None,
            "message": "Clean"
        }
    
    return guard_tool_call


# CLI interface
if __name__ == "__main__":
    import sys
    
    classifier = PromptInjectionClassifier()
    
    if len(sys.argv) < 2:
        print("Usage: python prompt_injection_classifier.py <text|file> [--json]")
        print("  text    - Analyze the provided text")
        print("  file    - Read and analyze content from file")
        print("  --json  - Output JSON result")
        sys.exit(1)
    
    input_arg = sys.argv[1]
    output_json = "--json" in sys.argv
    
    if Path(input_arg).exists():
        with open(input_arg, 'r') as f:
            text = f.read()
    else:
        text = input_arg
    
    result = classifier.analyze(text)
    
    if output_json:
        print(json.dumps({
            "threat_level": result.threat_level.value,
            "injection_types": [t.value for t in result.injection_types],
            "confidence": result.confidence,
            "risk_score": result.risk_score,
            "matched_patterns": result.matched_patterns,
            "details": result.details,
            "recommendation": result.recommendation,
        }, indent=2))
    else:
        print(f"Threat Level: {result.threat_level.value}")
        print(f"Risk Score: {result.risk_score}/100")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Injection Types: {[t.value for t in result.injection_types]}")
        print(f"Recommendation: {result.recommendation}")
        if result.matched_patterns:
            print("Matched Patterns:")
            for p in result.matched_patterns[:10]:
                print(f"  - {p}")