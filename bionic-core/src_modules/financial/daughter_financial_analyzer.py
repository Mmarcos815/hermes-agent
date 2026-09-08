#!/usr/bin/env python3
# ============================================================================
# BIONIC DAUGHTER v1 — FINANCIAL FRAUD ANALYZER (STANDALONE MODULE)
# ============================================================================
# Full financial fraud detection & forensic analysis module for the daughter.
#
# Domains covered:
#   1. BEC (Business Email Compromise) detection
#   2. ACH payroll fraud detection
#   3. Crypto API key / secret exposure scanning
#   4. DeFi smart contract vulnerability flagging
#   5. PCI-DSS compliance auditing
#   6. Money flow / transaction anomaly tracing
#
# Usage:
#   from daughter_financial_analyzer import FinancialAnalyzer
#   fa = FinancialAnalyzer()
#   result = fa.analyze_bec(email_headers, sender_domain, expected_domain)
#   result = fa.scan_crypto_exposure(repo_path)
#   result = fa.flag_defi_vulnerabilities(contract_code)
#   result = fa.pci_dss_audit(schema_description)
#   result = fa.trace_money_flow(transactions)
#   report = fa.generate_report(transactions, entities)
# ============================================================================

import os
import re
import json
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DaughterFinancial")

# ============================================================================
# FINANCIAL ANALYZER
# ============================================================================

class FinancialAnalyzer:
    """
    Elite financial fraud detection & forensic analysis engine.
    Covers BEC, ACH fraud, crypto theft, DeFi exploits, PCI-DSS, money flow.
    Designed for authorized forensic analysis and fraud prevention.
    """

    # ------------------------------------------------------------------
    # BEC (Business Email Compromise) Detection
    # ------------------------------------------------------------------

    def analyze_bec(self, email_data):
        """
        Analyze an email or email thread for BEC indicators.

        Args:
            email_data: dict with keys:
                - sender_address: str (full sender email)
                - sender_domain: str (extracted domain)
                - expected_domain: str (legitimate domain to compare)
                - subject: str
                - body: str
                - headers: dict (raw headers)
                - urgency_indicators: list of urgent keywords found
                - attachments: list of attachment filenames

        Returns:
            dict with risk_score (0-100), findings, recommendation, details
        """
        findings = []
        risk_score = 0

        sender = email_data.get("sender_address", "").lower()
        sender_domain = email_data.get("sender_domain", "").lower()
        expected_domain = email_data.get("expected_domain", "").lower()
        subject = email_data.get("subject", "").lower()
        body = email_data.get("body", "").lower()
        urgency = email_data.get("urgency_indicators", [])
        attachments = email_data.get("attachments", [])

        # --- Domain analysis ---
        if sender_domain and expected_domain:
            if sender_domain != expected_domain:
                lookalike = self._is_lookalike_domain(sender_domain, expected_domain)
                if lookalike:
                    findings.append({
                        "type": "DOMAIN_SPOOFING",
                        "severity": "CRITICAL",
                        "detail": f"Spoofed domain: {sender_domain} resembles {expected_domain}",
                    })
                    risk_score += 40
                else:
                    findings.append({
                        "type": "DOMAIN_MISMATCH",
                        "severity": "HIGH",
                        "detail": f"Domain mismatch: {sender_domain} vs expected {expected_domain}",
                    })
                    risk_score += 25

        # --- Lookalike detection methods ---
        if sender_domain and expected_domain:
            # Homoglyph detection (common character substitutions)
            homoglyph_map = {
                "а": "a", "е": "e", "і": "i", "о": "o", "у": "y",  # Cyrillic lookalikes
                "rn": "m", "vv": "w", "cl": "d", "lo": "b",
            }
            for fake, real in homoglyph_map.items():
                if fake in sender_domain and real not in sender_domain:
                    findings.append({
                        "type": "HOMOGLYPH_SPOOF",
                        "severity": "CRITICAL",
                        "detail": f"Potential homoglyph in domain: '{fake}' may represent '{real}'",
                    })
                    risk_score += 35

            # TLD substitution
            if sender_domain.replace(".", "").replace("-", "") == expected_domain.replace(".", "").replace("-", ""):
                findings.append({
                    "type": "TLD_SPOOF",
                    "severity": "HIGH",
                    "detail": "Domain name matches but TLD differs",
                })
                risk_score += 20

        # --- Urgency analysis ---
        urgency_keywords = [
            "urgent", "immediate", "asap", "urgent attention",
            "time sensitive", " confidential", "wire transfer",
            "payment due", "overdue", "final notice", "act now",
            "before it's too late", "emergency",
        ]
        found_urgency = [kw for kw in urgency_keywords if kw in body or kw in subject]
        if found_urgency:
            findings.append({
                "type": "URGENCY_MANIPULATION",
                "severity": "MEDIUM",
                "detail": f"Urgency language detected: {', '.join(found_urgency[:3])}",
            })
            risk_score += 15
            if len(found_urgency) > 2:
                risk_score += 10

        # --- Payment request detection ---
        payment_keywords = [
            "wire transfer", "bank transfer", "ach", "payment",
            "invoice", "vendor", "new account", "direct deposit",
            "routing number", "account number", "swift",
        ]
        found_payment = [kw for kw in payment_keywords if kw in body]
        if found_payment and (sender_domain != expected_domain or lookalike):
            findings.append({
                "type": "PAYMENT_REQUEST_SPOOF",
                "severity": "CRITICAL",
                "detail": f"Payment request from suspicious sender: {', '.join(found_payment[:3])}",
            })
            risk_score += 30

        # --- Attachment analysis ---
        dangerous_extensions = [".exe", ".scr", ".bat", ".cmd", ".ps1", ".vbs", ".js", ".hta"]
        for att in attachments:
            ext = Path(att).suffix.lower()
            if ext in dangerous_extensions:
                findings.append({
                    "type": "DANGEROUS_ATTACHMENT",
                    "severity": "CRITICAL",
                    "detail": f"Executable attachment: {att}",
                })
                risk_score += 25

        # --- Missing authentication indicators ---
        if email_data.get("headers"):
            headers = email_data["headers"]
            if not headers.get("spf_pass") and not headers.get("dkim_pass"):
                findings.append({
                    "type": "MISSING_AUTHENTICATION",
                    "severity": "MEDIUM",
                    "detail": "Email lacks SPF or DKIM authentication",
                })
                risk_score += 10

        # --- Recommendation ---
        if risk_score >= 60:
            recommendation = "BLOCK — High confidence BEC. Do not process payment. Verify sender through separate channel."
        elif risk_score >= 30:
            recommendation = "REVIEW — Moderate BEC risk. Verify sender identity before acting. Contact sender through known phone number."
        elif risk_score > 0:
            recommendation = "CAUTION — Low BEC indicators. Standard verification recommended."
        else:
            recommendation = "CLEAN — No BEC indicators detected."

        return {
            "risk_score": min(risk_score, 100),
            "recommendation": recommendation,
            "findings": findings,
            "verdict": "MALICIOUS" if risk_score >= 60 else ("SUSPICIOUS" if risk_score >= 30 else ("CAUTION" if risk_score > 0 else "CLEAN")),
        }

    def _is_lookalike_domain(self, domain_a, domain_b):
        """Check if two domains are visual lookalikes."""
        a = domain_a.lower().replace("www.", "").split(":")[0]
        b = domain_b.lower().replace("www.", "").split(":")[0]

        if a == b:
            return False

        # One character difference (same length)
        if len(a) == len(b):
            diffs = sum(1 for i in range(len(a)) if a[i] != b[i])
            if diffs == 1:
                # Check if the differing chars are visually similar
                similar_pairs = [
                    ("o", "0"), ("o", "о"), ("l", "1"), ("l", "i"),
                    ("rn", "m"), ("vv", "w"), ("c", "e"), ("i", "l"),
                ]
                for i in range(len(a)):
                    if a[i] != b[i]:
                        pair = (a[i], b[i])
                        if pair in similar_pairs or (pair[1], pair[0]) in similar_pairs:
                            return True
                return True  # One char diff is suspicious regardless

        # Subdomain tricks
        if a.endswith("." + b) or b.endswith("." + a):
            return True

        return False

    # ------------------------------------------------------------------
    # ACH Payroll Fraud Detection
    # ------------------------------------------------------------------

    def analyze_ach_fraud(self, payroll_change, employee_record, company_context=None):
        """
        Analyze a payroll direct deposit change request for ACH fraud.

        Args:
            payroll_change: dict with keys:
                - employee_id: str
                - new_account_number: str
                - new_account_type: str (checking/savings)
                - new_routing_number: str
                - change_request_time: datetime or timestamp
                - request_channel: str (email/web/form/phone)
                - urgency_level: str (low/medium/high)
                - requestor_ip: str (optional)
            employee_record: dict with keys:
                - employee_id: str
                - current_account_number: str
                - current_account_type: str
                - current_routing_number: str
                - hire_date: datetime
                - department: str
                - manager: str
                - historical_change_count: int
            company_context: dict (optional):
                - standard_change_window: str (e.g., "payroll cutoff 5 days prior")
                - required_verification: list of required verification steps

        Returns:
            dict with risk_score, findings, recommendation, red_flags
        """
        findings = []
        red_flags = []
        risk_score = 0

        change = payroll_change
        emp = employee_record

        # --- Account number change ---
        if change.get("new_account_number") != emp.get("current_account_number"):
            findings.append({
                "type": "ACCOUNT_CHANGE",
                "severity": "HIGH",
                "detail": f"Account number changed from {emp.get('current_account_number', '***')} to {change.get('new_account_number', '***')}",
            })
            risk_score += 20
            red_flags.append("New destination account")

        # --- Account type change ---
        if change.get("new_account_type") and change.get("new_account_type") != emp.get("current_account_type"):
            findings.append({
                "type": "ACCOUNT_TYPE_CHANGE",
                "severity": "MEDIUM",
                "detail": f"Account type changed: {emp.get('current_account_type')} -> {change.get('new_account_type')}",
            })
            risk_score += 10

        # --- Routing number change ---
        if change.get("new_routing_number") and change.get("new_routing_number") != emp.get("current_routing_number"):
            findings.append({
                "type": "ROUTING_CHANGE",
                "severity": "HIGH",
                "detail": "Bank routing number changed — different financial institution",
            })
            risk_score += 25
            red_flags.append("New bank / routing number")

        # --- Urgency analysis ---
        urgency = change.get("urgency_level", "low").lower()
        if urgency == "high":
            findings.append({
                "type": "HIGH_URGENCY",
                "severity": "HIGH",
                "detail": "High urgency requested — common social engineering tactic",
            })
            risk_score += 20
            red_flags.append("Urgent request")

        # --- Timing analysis ---
        change_time = change.get("change_request_time")
        if change_time:
            if isinstance(change_time, str):
                try:
                    change_time = datetime.fromisoformat(change_time)
                except:
                    pass
            if isinstance(change_time, datetime):
                hour = change_time.hour
                if hour < 7 or hour > 19:
                    findings.append({
                        "type": "AFTER_HOURS_REQUEST",
                        "severity": "MEDIUM",
                        "detail": f"Change request at {hour}:00 — atypical business hours",
                    })
                    risk_score += 10
                    red_flags.append("After-hours request")

                # Near payroll cutoff
                if company_context and "payroll_cutoff" in company_context:
                    cutoff = company_context["payroll_cutoff"]
                    # Simplified: flag if within 48h of cutoff
                    # Real impl would compare dates
                    pass

        # --- Request channel ---
        channel = change.get("request_channel", "unknown").lower()
        suspicious_channels = ["email", "chat", "text", "phone_call"]
        if channel in suspicious_channels:
            findings.append({
                "type": "INSECURE_CHANNEL",
                "severity": "MEDIUM",
                "detail": f"Change requested via {channel} — insecure channel for financial changes",
            })
            risk_score += 10

        # --- Historical pattern ---
        hist_changes = emp.get("historical_change_count", 0)
        if hist_changes > 2:
            findings.append({
                "type": "FREQUENT_CHANGES",
                "severity": "MEDIUM",
                "detail": f"Employee has had {hist_changes} deposit changes — unusual pattern",
            })
            risk_score += 10

        # --- Recommendation ---
        if risk_score >= 50:
            recommendation = "HOLD — High ACH fraud risk. Escalate to payroll security team. Verify through in-person or video call with known management. Do not process until verified."
            verdict = "HIGH_RISK"
        elif risk_score >= 25:
            recommendation = "REVIEW — Moderate risk. Require additional verification (manager approval, employee confirmation via known channel). Process after verification."
            verdict = "MEDIUM_RISK"
        elif risk_score > 0:
            recommendation = "PROCEED_WITH_VERIFICATION — Low risk but standard verification recommended."
            verdict = "LOW_RISK"
        else:
            recommendation = "CLEAN — No ACH fraud indicators."
            verdict = "CLEAN"

        return {
            "risk_score": min(risk_score, 100),
            "verdict": verdict,
            "recommendation": recommendation,
            "findings": findings,
            "red_flags": red_flags,
        }

    # ------------------------------------------------------------------
    # Crypto API Key / Secret Exposure Scanner
    # ------------------------------------------------------------------

    def scan_crypto_exposure(self, repo_path, scan_subdirs=True):
        """
        Scan a repository or directory for exposed crypto-related secrets and API keys.

        Args:
            repo_path: str — path to scan
            scan_subdirs: bool — whether to recurse into subdirectories

        Returns:
            dict with findings (list of exposures), total_count, severity_breakdown, recommendations
        """
        findings = []
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

        # Patterns to detect (regex)
        patterns = [
            # AWS keys (often used for cloud crypto operations)
            (r"AKIA[0-9A-Z]{16}", "AWS_ACCESS_KEY", "CRITICAL",
             "AWS access key — could be used for cloud resource abuse"),
            (r"aws_secret_access_key\s*=\s*['\"]([^'\"]{20,})['\"]", "AWS_SECRET_KEY", "CRITICAL",
             "AWS secret key exposed"),
            # Generic API keys
            (r"api[_-]?key\s*[=:]?\s*['\"]([a-zA-Z0-9_-]{32,})['\"]", "GENERIC_API_KEY", "HIGH",
             "Generic API key pattern detected"),
            (r"secret[_-]?key\s*[=:]?\s*['\"]([a-zA-Z0-9_-]{20,})['\"]", "GENERIC_SECRET", "CRITICAL",
             "Secret key exposed"),
            (r"token\s*[=:]?\s*['\"]([a-zA-Z0-9_-]{30,})['\"]", "AUTH_TOKEN", "HIGH",
             "Authentication token exposed"),
            # Crypto private keys (various formats)
            (r"private[\s_]key\s*=\s*['\"]([a-fA-F0-9]{40,})['\"]", "PRIVATE_KEY_HEX", "CRITICAL",
             "Private key (hex format) exposed"),
            (r"-----BEGIN\s+(RSA|EC|OPENSSL|ELECTRUM|BITCOIN)\s+PRIVATE\s+KEY-----", "PEM_PRIVATE_KEY", "CRITICAL",
             "PEM-encoded private key exposed"),
            # Wallet addresses (informational, but worth flagging if alongside keys)
            (r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b", "BITCOIN_ADDRESS", "LOW",
             "Bitcoin address found"),
            (r"0x[a-fA-F0-9]{40}", "ETHERUM_ADDRESS", "LOW",
             "Ethereum address found"),
            # Mnemonic phrases (BIP39)
            (r"\b(word1|word2|word3)\b.*\b(word12|word13|word14|word15|word16|word17|word18|word19|word20|word21|word22|word23|word24)\b", "MNEMONIC_PHRASE", "CRITICAL",
             "Potential BIP39 mnemonic phrase"),
        ]

        # Files to scan
        extensions_to_scan = [".py", ".js", ".ts", ".json", ".yaml", ".yml", ".env",
                              ".txt", ".md", ".cfg", ".ini", ".conf", ".xml", ".properties",
                              ".rb", ".go", ".rs", ".java", ".sh", ".bash", ".dockerfile"]

        walker = os.walk(repo_path) if scan_subdirs else [(repo_path, [], [os.path.basename(repo_path)])]

        for root, dirs, files in walker:
            for fname in files:
                ext = Path(fname).suffix.lower()
                if ext not in extensions_to_scan and ext != "":
                    continue
                fpath = os.path.join(root, fname)

                try:
                    with open(fpath, "r", errors="ignore") as f:
                        content = f.read()
                except (IOError, UnicodeDecodeError):
                    continue

                for pattern, label, severity, description in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # Extract the matched value for reporting
                        if isinstance(match, tuple):
                            value = match[-1] if match[-1] else str(match)
                        else:
                            value = match

                        # Truncate for display
                        display_value = value[:20] + "..." if len(str(value)) > 20 else str(value)

                        findings.append({
                            "file": os.path.relpath(fpath, repo_path),
                            "line": content[:1000].count("\n") + 1,  # approximate
                            "pattern": label,
                            "severity": severity,
                            "description": description,
                            "match_value": display_value,
                        })
                        severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # Sort by severity
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        findings.sort(key=lambda x: severity_order.get(x["severity"], 99))

        # Recommendations
        recommendations = []
        if severity_counts.get("CRITICAL", 0) > 0:
            recommendations.append("IMMEDIATE ACTION: Revoke all exposed keys. Rotate credentials. Check for unauthorized access.")
        if severity_counts.get("HIGH", 0) > 0:
            recommendations.append("Rotate affected API keys and tokens. Review access logs for unauthorized usage.")
        if severity_counts.get("MEDIUM", 0) > 0:
            recommendations.append("Review and secure exposed configuration values.")
        recommendations.append("Implement pre-commit hooks to prevent secret commits (e.g., git-secrets, detect-secrets).")
        recommendations.append("Use environment variables or secret management (Vault, AWS Secrets Manager) instead of hardcoded values.")

        return {
            "total_exposures": len(findings),
            "findings": findings,
            "severity_breakdown": severity_counts,
            "recommendations": recommendations,
            "scan_path": repo_path,
            "scan_timestamp": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------
    # DeFi Smart Contract Vulnerability Flagging
    # ------------------------------------------------------------------

    def flag_defi_vulnerabilities(self, contract_code, contract_name="Unknown"):
        """
        Flag common DeFi smart contract vulnerability patterns.

        Args:
            contract_code: str — Solidity (or similar) contract source code
            contract_name: str — name for reporting

        Returns:
            dict with issues (list), severity_breakdown, risk_level, recommendations
        """
        issues = []
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}

        code_lower = contract_code.lower()

        # --- Flash Loan + Oracle Manipulation ---
        has_flash_loan = any(kw in code_lower for kw in [
            "flashloan", "flash Loan", "flashborrow", "flash_borrow",
            "flexleaseline", "aaveflash", "celerflash"
        ])
        has_single_oracle = any(kw in code_lower for kw in [
            "spot price", "getprice", "pricefeed", "single price",
            "oracle", "twap", "balancer pool", "uniswap pool"
        ]) and "multiple" not in code_lower and "twap" not in code_lower

        if has_flash_loan and has_single_oracle:
            issues.append({
                "type": "FLASH_LOAN_ORACLE_MANIPULATION",
                "severity": "CRITICAL",
                "description": "Contract combines flash loans with single-source price oracle — vulnerable to price manipulation attacks",
                "cwe": "CWE-841 (Improper Enforcement of Behavioral Workflow)",
                "recommendation": "Use TWAP (Time-Weighted Average Price) oracles or multi-source price feeds. Implement price deviation checks.",
            })
            severity_counts["CRITICAL"] += 1

        # --- Reentrancy ---
        has_external_call = any(kw in code_lower for kw in [
            ".call.value", ".call{gas:", "send(", "transfer(",
            " delegatecall", "callcode"
        ])
        has_state_update_after = any(kw in code_lower for kw in [
            "balance", "allowance", "withdraw", "transfer"
        ])

        if has_external_call and has_state_update_after:
            # Check if state updates before external call (check-effects-interactions)
            # Simplified — real impl would parse control flow
            issues.append({
                "type": "REENTRANCY",
                "severity": "HIGH",
                "description": "External call detected alongside state mutation — potential reentrancy vulnerability",
                "cwe": "CWE-841",
                "recommendation": "Follow check-effects-interactions pattern. Use ReentrancyGuard. Update state before external calls.",
            })
            severity_counts["HIGH"] += 1

        # --- Price Oracle — Single Source ---
        if has_single_oracle and not has_flash_loan:
            issues.append({
                "type": "SINGLE_SOURCE_ORACLE",
                "severity": "MEDIUM",
                "description": "Price oracle may rely on single source — vulnerable to manipulation or feed failure",
                "recommendation": "Use multiple oracle sources or TWAP. Implement circuit breakers for price deviations.",
            })
            severity_counts["MEDIUM"] += 1

        # --- Access Control ---
        has_owner = any(kw in code_lower for kw in ["owner", "onlyowner", "admin"])
        has_important_fn = any(kw in code_lower for kw in [
            "withdraw", "transfer", "mint", "burn", "pause", "upgrade",
            "set", "change", "update", "remove", "disable"
        ])
        if has_owner and has_important_fn:
            # Check for access control modifier
            has_modifier = any(kw in code_lower for kw in [
                "onlyowner", "onlyadmin", "require(msg.sender", "accesscontrol"
            ])
            if not has_modifier:
                issues.append({
                    "type": "MISSING_ACCESS_CONTROL",
                    "severity": "HIGH",
                    "description": "Privileged function detected without access control modifier",
                    "recommendation": "Add access control (Ownable, AccessControl) to privileged functions.",
                })
                severity_counts["HIGH"] += 1

        # --- Integer Overflow/Underflow (older Solidity) ---
        if "uint" in code_lower or "int" in code_lower:
            if "safe" not in code_lower and "unchecked" not in code_lower:
                issues.append({
                    "type": "INTEGER_OVERFLOW_POTENTIAL",
                    "severity": "MEDIUM",
                    "description": "Arithmetic operations on integers without safe math library",
                    "recommendation": "Use SafeMath library or Solidity 0.8+ built-in overflow checks.",
                })
                severity_counts["MEDIUM"] += 1

        # --- Front-running ---
        has_users = any(kw in code_lower for kw in ["msg.sender", "user", "trader", "buyer"])
        has_price_dependent = any(kw in code_lower for kw in [
            "price", "exchange", "swap", "trade", "execute"
        ])
        if has_users and has_price_dependent:
            issues.append({
                "type": "FRONT_RUNNABLE",
                "severity": "MEDIUM",
                "description": "Transaction order dependence — users may be front-run on price-sensitive operations",
                "recommendation": "Consider commit-reveal schemes, TWAP, or MEV protection.",
            })
            severity_counts["MEDIUM"] += 1

        # --- Upgradeability Risks ---
        if any(kw in code_lower for kw in ["delegatecall", "proxy", "upgrade", "initializer"]):
            issues.append({
                "type": "UPGRADEABILITY_RISK",
                "severity": "INFO",
                "description": "Contract uses upgradeable proxy pattern — ensure proper initialization and access control",
                "recommendation": "Verify upgrade authority is restricted. Ensure initializer cannot be called twice.",
            })
            severity_counts["INFO"] += 1

        # --- Risk level ---
        if severity_counts["CRITICAL"] > 0:
            risk_level = "CRITICAL"
        elif severity_counts["HIGH"] > 0:
            risk_level = "HIGH"
        elif severity_counts["MEDIUM"] > 0:
            risk_level = "MEDIUM"
        elif severity_counts["LOW"] > 0:
            risk_level = "LOW"
        else:
            risk_level = "LOW"

        # Recommendations
        recommendations = []
        if severity_counts["CRITICAL"] > 0:
            recommendations.append("IMMEDIATE AUDIT REQUIRED: Critical vulnerabilities found. Do not deploy. Engage professional audit firm.")
        if severity_counts["HIGH"] > 0:
            recommendations.append("High-severity issues must be resolved before mainnet deployment.")
        if severity_counts["MEDIUM"] > 0:
            recommendations.append("Medium-severity issues should be addressed. Consider professional review.")
        recommendations.append("Engage multiple independent audit firms for DeFi contracts handling user funds.")
        recommendations.append("Implement bug bounty program for ongoing security coverage.")
        recommendations.append("Use formal verification tools for critical invariant checking.")

        return {
            "contract_name": contract_name,
            "risk_level": risk_level,
            "issues": issues,
            "severity_breakdown": severity_counts,
            "recommendations": recommendations,
            "total_issues": len(issues),
            "analysis_timestamp": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------
    # PCI-DSS Compliance Auditor
    # ------------------------------------------------------------------

    def pci_dss_audit(self, schema_description, data_flow_description=None):
        """
        Audit a system description for PCI-DSS compliance gaps.

        Args:
            schema_description: str — description of database schema / data storage
            data_flow_description: str (optional) — description of how data flows through the system

        Returns:
            dict with gaps (list), compliant_areas, overall_assessment, requirement_refs
        """
        gaps = []
        compliant = []
        text = schema_description.lower()
        flow = (data_flow_description or "").lower()

        # --- Requirement 3: Protect stored cardholder data ---
        # 3.4: Render PAN unreadable anywhere it is stored
        if any(kw in text for kw in ["credit card", "card number", "cc_number", "pan",
                                       "primary account number", "card_num"]):
            has_protection = any(kw in text for kw in [
                "encrypt", "encryption", "tokenize", "tokenization",
                "hash", "masked", "masking", "truncate", "hmac",
            ])
            if not has_protection:
                gaps.append({
                    "requirement": "PCI-DSS 3.4",
                    "description": "Primary Account Number (PAN) stored without encryption, tokenization, or hashing",
                    "severity": "CRITICAL",
                    "action": "Implement encryption at rest (AES-256) or tokenization for all PAN storage.",
                })
            else:
                compliant.append("PCI-DSS 3.4: PAN protection implemented (encryption/tokenization detected)")

        # 3.2: Do not store sensitive authentication data after authorization
        if any(kw in text for kw in ["cvv", "cvn", "card verification", "cad", "cav",
                                       "pin", "pin block", "track", "full track",
                                       "magnetic stripe", "magstripe"]):
            gaps.append({
                "requirement": "PCI-DSS 3.2",
                "description": "Sensitive authentication data (CVV/CVN, PIN, track data) present in storage",
                "severity": "CRITICAL",
                "action": "Remove all sensitive authentication data from storage immediately. This data must NEVER be stored after authorization.",
            })
        else:
            compliant.append("PCI-DSS 3.2: No sensitive authentication data detected in storage")

        # --- Requirement 4: Encrypt transmission ---
        if "transmit" in text or "send" in text or "api" in text or "network" in text:
            has_encryption = any(kw in text or kw in flow for kw in [
                "tls", "ssl", "https", "encrypted", "encryption",
            ])
            if not has_encryption:
                gaps.append({
                    "requirement": "PCI-DSS 4.1",
                    "description": "Cardholder data transmission without encryption detected",
                    "severity": "HIGH",
                    "action": "Encrypt all cardholder data transmission using TLS 1.2+ or equivalent.",
                })

        # --- Requirement 7: Restrict access ---
        if "access" in text or "role" in text or "permission" in text:
            has_restriction = any(kw in text for kw in [
                "role-based", "rbac", "least privilege", "restrict", "access control",
                "authentication", "auth", "permission", "allowlist",
            ])
            if not has_restriction:
                gaps.append({
                    "requirement": "PCI-DSS 7.1",
                    "description": "No access restriction mechanism detected for cardholder data",
                    "severity": "HIGH",
                    "action": "Implement role-based access control with least privilege principle for all cardholder data access.",
                })

        # --- Requirement 10: Track and monitor ---
        if "log" in text or "audit" in text or "monitor" in text:
            has_logging = any(kw in text for kw in [
                "log", "logging", "audit", "audit trail", "monitor", "siem",
                "timestamp", "who accessed", "access log",
            ])
            if not has_logging:
                gaps.append({
                    "requirement": "PCI-DSS 10.1",
                    "description": "No tracking/monitoring mechanism for access to cardholder data",
                    "severity": "MEDIUM",
                    "action": "Implement audit logging for all access to cardholder data. Log must include who, what, when, and whether access was granted.",
                })
        else:
            gaps.append({
                "requirement": "PCI-DSS 10.1",
                "description": "No monitoring-capable system described for cardholder data access",
                "severity": "MEDIUM",
                "action": "Implement comprehensive audit logging and monitoring for all cardholder data interactions.",
            })

        # --- Overall assessment ---
        critical_gaps = sum(1 for g in gaps if g["severity"] == "CRITICAL")
        high_gaps = sum(1 for g in gaps if g["severity"] == "HIGH")

        if critical_gaps > 0:
            assessment = "FAIL — Critical PCI-DSS compliance gaps detected. System cannot process cardholder data until resolved."
        elif high_gaps > 0:
            assessment = "HIGH_RISK — Significant compliance gaps. Requires immediate remediation before processing payments."
        elif len(gaps) > 0:
            assessment = "MEDIUM_RISK — Some compliance gaps. Remediation recommended before handling cardholder data."
        elif len(compliant) > 0:
            assessment = "COMPLIANT — No critical gaps detected. Continue to maintain compliance and conduct regular audits."
        else:
            assessment = "INSUFFICIENT_DATA — Unable to assess. Provide more detailed system description."

        return {
            "assessment": assessment,
            "gaps": gaps,
            "compliant_areas": compliant,
            "total_gaps": len(gaps),
            "critical_gaps": critical_gaps,
            "requirement_references": [
                "PCI-DSS v4.0 Requirement 3: Protect stored cardholder data",
                "PCI-DSS v4.0 Requirement 4: Encrypt transmission of cardholder data",
                "PCI-DSS v4.0 Requirement 7: Restrict access to cardholder data",
                "PCI-DSS v4.0 Requirement 10: Track and monitor access",
            ],
            "audit_timestamp": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------
    # Money Flow / Transaction Anomaly Tracing
    # ------------------------------------------------------------------

    def trace_money_flow(self, transactions, entities=None):
        """
        Trace and analyze a sequence of financial transactions for suspicious patterns.

        Args:
            transactions: list of dicts with keys:
                - from: str (source entity/account)
                - to: str (destination entity/account)
                - amount: float
                - timestamp: datetime or timestamp
                - type: str (transfer, payment, withdrawal, deposit, etc.)
                - reference: str (optional transaction reference)
                - currency: str (optional, default USD)
            entities: dict (optional) — known entity info for enrichment:
                - trusted_beneficiaries: list of known-good accounts
                - high_risk_jurisdictions: list of high-risk country codes
                - employee_accounts: list of known employee account IDs

        Returns:
            dict with flagged_transactions, total_flow, anomalies, summary, network_graph
        """
        flagged = []
        anomalies = []
        total_flow = 0
        flow_by_account = {}

        # Build flow graph
        for txn in transactions:
            amount = txn.get("amount", 0)
            total_flow += amount
            flow_by_account[txn.get("from", "")] = flow_by_account.get(txn.get("from", ""), 0) - amount
            flow_by_account[txn.get("to", "")] = flow_by_account.get(txn.get("to", ""), 0) + amount

        # Analyze each transaction
        for i, txn in enumerate(transactions):
            score = 0
            reasons = []
            amount = txn.get("amount", 0)
            txn_from = txn.get("from", "")
            txn_to = txn.get("to", "")

            # --- Large amount ---
            if amount > 10000:
                score += 20
                reasons.append(f"Large transaction: ${amount:,.2f}")
            elif amount > 5000:
                score += 10
                reasons.append(f"Moderate-large transaction: ${amount:,.2f}")

            # --- Rapid movement (layering) ---
            if i > 0:
                prev = transactions[i - 1]
                prev_time = prev.get("timestamp")
                curr_time = txn.get("timestamp")
                if prev_time and curr_time:
                    try:
                        dt_prev = prev_time if isinstance(prev_time, datetime) else datetime.fromtimestamp(prev_time)
                        dt_curr = curr_time if isinstance(curr_time, datetime) else datetime.fromtimestamp(curr_time)
                        diff = (dt_curr - dt_prev).total_seconds()
                        if diff < 60:  # under 1 minute
                            if txn_to == prev.get("to") or txn_from == prev.get("from"):
                                score += 15
                                reasons.append(f"Rapid sequential transfer ({diff:.0f}s) — potential layering")
                    except:
                        pass

            # --- Circular flow ---
            if i > 1:
                earlier = transactions[i - 2]
                if txn_to == earlier.get("from"):
                    score += 25
                    reasons.append("Circular money flow detected — funds returning to origin")
                if txn_from == earlier.get("to"):
                    score += 20
                    reasons.append("Reverse flow detected — potential wash transaction")

            # --- New beneficiary ---
            if i > 0:
                previous_recipients = set(t.get("to") for t in transactions[:i])
                if txn_to not in previous_recipients:
                    score += 10
                    reasons.append(f"New beneficiary: {txn_to}")

            # --- Structuring (amounts just below reporting thresholds) ---
            thresholds = [10000, 5000, 3000, 1000]
            for t in thresholds:
                if t * 0.95 <= amount <= t * 0.99:
                    score += 15
                    reasons.append(f"Amount (${amount:,.0f}) near reporting threshold (${t:,.0f}) — potential structuring")

            # --- High-risk jurisdiction (if entities provided) ---
            if entities and "high_risk_jurisdictions" in entities:
                # Simplified — real impl would geolocate accounts
                pass

            # --- Trusted beneficiary check ---
            if entities and "trusted_beneficiaries" in entities:
                if txn_to in entities["trusted_beneficiaries"]:
                    score = max(0, score - 15)
                    reasons.append("Trusted beneficiary — reduced risk")

            # --- Employee-to-external ---
            if entities and "employee_accounts" in entities:
                if txn_from in entities["employee_accounts"] and txn_to not in entities["employee_accounts"]:
                    score += 10
                    reasons.append("Employee account sending to external — review for payroll fraud")

            # Flag if score exceeds threshold
            if score >= 20:
                flagged.append({
                    "transaction": txn,
                    "risk_score": score,
                    "reasons": reasons,
                    "recommendation": "HOLD for review" if score >= 50 else "REVIEW",
                })

            if score > 0:
                anomalies.append({
                    "transaction_index": i,
                    "transaction": txn,
                    "risk_score": score,
                    "reasons": reasons,
                })

        # Build network graph (simple adjacency)
        network_graph = {}
        for txn in transactions:
            f = txn.get("from", "")
            t = txn.get("to", "")
            if f not in network_graph:
                network_graph[f] = {"sent_to": {}, "total_sent": 0}
            if t not in network_graph:
                network_graph[t] = {"sent_to": {}, "total_sent": 0}
            network_graph[f]["sent_to"][t] = network_graph[f]["sent_to"].get(t, 0) + txn.get("amount", 0)
            network_graph[f]["total_sent"] += txn.get("amount", 0)

        # Summary
        summary = {
            "total_transactions": len(transactions),
            "total_flow": total_flow,
            "flagged_count": len(flagged),
            "anomaly_count": len(anomalies),
            "net_flow_by_account": dict(sorted(flow_by_account.items(), key=lambda x: abs(x[1]), reverse=True)[:10]),
        }

        return {
            "flagged_transactions": flagged,
            "anomalies": anomalies,
            "total_flow": total_flow,
            "summary": summary,
            "network_graph": network_graph,
            "analysis_timestamp": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------
    # Comprehensive Report Generator
    # ------------------------------------------------------------------

    def generate_report(self, transactions=None, entities=None, email_analysis=None,
                        ach_analysis=None, crypto_scan=None, defi_audit=None,
                        pci_audit=None):
        """
        Generate a comprehensive financial fraud report combining multiple analyses.
        """
        report = {
            "report_title": "Bionic Daughter — Financial Fraud Analysis Report",
            "generated_at": datetime.now().isoformat(),
            "sections": {},
        }

        if email_analysis:
            report["sections"]["BEC Analysis"] = email_analysis
        if ach_analysis:
            report["sections"]["ACH Fraud Analysis"] = ach_analysis
        if crypto_scan:
            report["sections"]["Crypto Exposure Scan"] = crypto_scan
        if defi_audit:
            report["sections"]["DeFi Vulnerability Audit"] = defi_audit
        if pci_audit:
            report["sections"]["PCI-DSS Compliance Audit"] = pci_audit
        if transactions:
            report["sections"]["Money Flow Analysis"] = self.trace_money_flow(transactions, entities)

        # Overall risk summary
        risk_scores = []
        if email_analysis:
            risk_scores.append(("BEC", email_analysis.get("risk_score", 0)))
        if ach_analysis:
            risk_scores.append(("ACH Fraud", ach_analysis.get("risk_score", 0)))

        if risk_scores:
            max_risk = max(s[1] for s in risk_scores)
            report["overall_risk_level"] = "CRITICAL" if max_risk >= 70 else (
                "HIGH" if max_risk >= 40 else ("MEDIUM" if max_risk >= 15 else "LOW")
            )
            report["highest_risk_area"] = max(risk_scores, key=lambda x: x[1])[0]

        return report

# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    fa = FinancialAnalyzer()

    # Test BEC analysis
    bec_result = fa.analyze_bec({
        "sender_address": "cfo@company-secure.com",
        "sender_domain": "company-secure.com",
        "expected_domain": "company.com",
        "subject": "URGENT: Wire transfer needed",
        "body": "This is urgent. Please wire $50,000 to the new vendor account immediately. This is time sensitive.",
        "urgency_indicators": ["urgent", "immediate", "asap"],
        "headers": {"spf_pass": False, "dkim_pass": False},
    })
    print("=== BEC Analysis ===")
    print(json.dumps(bec_result, indent=2))

    # Test ACH fraud analysis
    ach_result = fa.analyze_ach_fraud(
        {
            "employee_id": "EMP001",
            "new_account_number": "987654321",
            "new_account_type": "savings",
            "new_routing_number": "021000021",
            "change_request_time": datetime(2026, 8, 15, 22, 30),
            "request_channel": "email",
            "urgency_level": "high",
        },
        {
            "employee_id": "EMP001",
            "current_account_number": "123456789",
            "current_account_type": "checking",
            "current_routing_number": "021000021",
            "historical_change_count": 0,
        }
    )
    print("\n=== ACH Fraud Analysis ===")
    print(json.dumps(ach_result, indent=2))

    # Test DeFi audit
    defi_result = fa.flag_defi_vulnerabilities("""
    contract Vault {
        function withdraw(uint amount) external {
            require(balance[msg.sender] >= amount);
            (bool success, ) = msg.sender.call.value(amount)("");
            balance[msg.sender] -= amount;
        }
    }
    """, "Vault")
    print("\n=== DeFi Audit ===")
    print(json.dumps(defi_result, indent=2))

    # Test PCI audit
    pci_result = fa.pci_dss_audit(
        "Database stores credit_card_number as VARCHAR(16) in plaintext. "
        "Also stores cvv as VARCHAR(4). Access is not restricted by role."
    )
    print("\n=== PCI-DSS Audit ===")
    print(json.dumps(pci_result, indent=2))

    # Test money flow
    flow_result = fa.trace_money_flow([
        {"from": "A", "to": "B", "amount": 15000, "timestamp": datetime(2026, 8, 15, 10, 0)},
        {"from": "B", "to": "C", "amount": 14500, "timestamp": datetime(2026, 8, 15, 10, 5)},
        {"from": "C", "to": "A", "amount": 14000, "timestamp": datetime(2026, 8, 15, 10, 10)},
        {"from": "A", "to": "D", "amount": 9800, "timestamp": datetime(2026, 8, 15, 10, 15)},
    ])
    print("\n=== Money Flow Analysis ===")
    print(json.dumps(flow_result, indent=2))
