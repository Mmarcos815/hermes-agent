#!/usr/bin/env python3
"""
BIONIC DAUGHTER — Payment Scanner MCP Server
FastMCP server providing payment-rail security analysis tools.

Tools:
  - xpay_analyze:    Analyze Visa X-Pay Token implementation
  - oauth_analyze:   Analyze Mastercard OAuth 1.0a signing
  - token_replay_check: Check for token replay vulnerability
  - iso8583_analyze: Analyze ISO 8583 message fields for weaknesses
  - check_fraud_pattern: Check fraud pattern detection

Usage:
  FastMCP("payment_scanner", version="1.0.0")
  Register in ~/.hermes/config.yaml under mcpServers.
"""
import json
import hashlib
import hmac
import base64
import re
from datetime import datetime
from typing import Optional, Dict, List

from fastmcp import FastMCP

app = FastMCP("payment_scanner", version="1.0.0")


# ============================================================
# TOOL 1: Visa X-Pay Token Analyzer
# ============================================================

@app.tool()
def xpay_analyze(
    shared_secret: str,
    timestamp: str,
    resource_path: str,
    query_string: str = "",
    payload: str = "",
) -> dict:
    """
    Analyze a Visa X-Pay Token for implementation flaws.

    X-Pay Token format:
      x-pay-token: xv2:{timestamp}:{HMAC-SHA256(sharedSecret, payload + timestamp + resourcePath + queryString)}

    Checks:
    - Canonicalization correctness
    - Timestamp freshness
    - Signature validity
    - Known pitfalls
    """
    result = {
        "analysis_timestamp": datetime.utcnow().isoformat(),
        "token_components": {
            "timestamp": timestamp,
            "resource_path": resource_path,
            "query_string": query_string,
            "payload": payload[:200] + "..." if len(payload) > 200 else payload,
        },
        "findings": [],
        "severity": "info",
        "recommendations": [],
    }

    findings = result["findings"]
    severity = "info"

    # Check 1: Timestamp format
    try:
        ts = int(timestamp)
        if ts < 1000000000:  # Before 2001
            findings.append({"check": "timestamp_format", "result": "FAIL", "detail": "Timestamp appears invalid (pre-2001)"})
            severity = "high"
        else:
            age_seconds = int(datetime.now().timestamp()) - ts
            if age_seconds > 300:  # 5 min
                findings.append({"check": "timestamp_freshness", "result": "WARN", "detail": f"Timestamp is {age_seconds}s old — may accept stale tokens if server has no freshness window"})
                if age_seconds > 3600:
                    severity = "high"
            else:
                findings.append({"check": "timestamp_freshness", "result": "OK", "detail": f"Timestamp is {age_seconds}s old"})
    except ValueError:
        findings.append({"check": "timestamp_format", "result": "FAIL", "detail": "Timestamp is not a valid integer"})
        severity = "high"

    # Check 2: Resource path canonicalization
    if not resource_path.startswith("/"):
        findings.append({"check": "resource_path", "result": "WARN", "detail": "Resource path missing leading / — canonicalization inconsistency risk"})
    elif resource_path.endswith("/") and resource_path != "/":
        findings.append({"check": "resource_path", "result": "WARN", "detail": "Resource path has trailing / — may cause signature mismatch on different servers"})

    # Check 3: Query string ordering
    if query_string:
        params = query_string.split("&")
        if len(params) > 1:
            sorted_params = sorted(params)
            if params != sorted_params:
                findings.append({"check": "query_string_order", "result": "WARN", "detail": "Query params not sorted — signature may differ if server sorts differently"})

    # Check 4: Payload canonicalization
    if payload:
        try:
            parsed = json.loads(payload)
            canonical = json.dumps(parsed, sort_keys=True, separators=(",", ":"))
            if canonical != payload.strip():
                findings.append({"check": "payload_canonicalization", "result": "WARN", "detail": "Payload JSON may have key-order/whitespace differences — HMAC may mismatch on different serializers"})
        except json.JSONDecodeError:
            findings.append({"check": "payload_format", "result": "INFO", "detail": "Payload is not JSON — body hash may be computed differently"})

    # Check 5: Compute expected signature (for verification)
    message = payload + timestamp + resource_path + query_string
    computed_sig = hmac.new(
        shared_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    result["computed_signature"] = computed_sig
    result["signature_message"] = message

    # Check 6: Shared secret strength
    if len(shared_secret) < 16:
        findings.append({"check": "shared_secret_strength", "result": "FAIL", "detail": f"Shared secret is only {len(shared_secret)} chars — too weak for HMAC-SHA256"})
        severity = "critical"
    elif shared_secret in ("secret", "password", "changeme", "test", "demo"):
        findings.append({"check": "shared_secret_strength", "result": "FAIL", "detail": "Shared secret is a common/test value — must be rotated"})
        severity = "critical"

    # Summary
    critical = [f for f in findings if f["result"] == "FAIL"]
    high = [f for f in findings if f["result"] == "WARN"]
    if critical:
        severity = "critical"
    elif high and severity != "critical":
        severity = "high"

    result["severity"] = severity
    result["summary"] = f"{len(critical)} critical, {len(high)} warnings"
    result["recommendations"] = [
        "Use consistent JSON serialization (sort_keys=True, compact separators) on both client and server",
        "Validate timestamp freshness server-side (reject tokens older than 5 minutes)",
        "Ensure resource path canonicalization is identical on client and server",
        "Use a strong, randomly-generated shared secret (minimum 32 bytes)",
        "Rotate shared secrets periodically",
    ]

    return result


# ============================================================
# TOOL 2: Mastercard OAuth 1.0a Analyzer
# ============================================================

@app.tool()
def oauth_analyze(
    consumer_key: str,
    timestamp: str,
    nonce: str,
    signature_method: str = "RSA-SHA256",
    parameters: Optional[dict] = None,
) -> dict:
    """
    Analyze a Mastercard OAuth 1.0a request for signing flaws.

    Two-legged OAuth 1.0a uses RSA-SHA256 signature over normalized
    request parameters including oauth_body_hash, oauth_nonce, oauth_timestamp.

    Checks:
    - Parameter normalization correctness
    - oauth_body_hash presence
    - Nonce uniqueness
    - Timestamp freshness
    - Signature method
    """
    result = {
        "analysis_timestamp": datetime.utcnow().isoformat(),
        "oauth_params": {
            "consumer_key": consumer_key[:20] + "..." if len(consumer_key) > 20 else consumer_key,
            "timestamp": timestamp,
            "nonce": nonce,
            "signature_method": signature_method,
            "parameter_count": len(parameters) if parameters else 0,
        },
        "findings": [],
        "severity": "info",
        "recommendations": [],
    }

    findings = result["findings"]
    severity = "info"

    # Check 1: oauth_body_hash
    if parameters and "oauth_body_hash" not in parameters:
        findings.append({"check": "oauth_body_hash", "result": "FAIL", "detail": "oauth_body_hash missing — request body not integrity-protected"})
        severity = "critical"
    elif parameters and parameters.get("oauth_body_hash"):
        bh = parameters["oauth_body_hash"]
        if len(bh) != 64:  # SHA-256 hex digest
            findings.append({"check": "oauth_body_hash", "result": "WARN", "detail": f"oauth_body_hash length is {len(bh)} — expected 64 for SHA-256"})
        else:
            findings.append({"check": "oauth_body_hash", "result": "OK", "detail": "oauth_body_hash present and correct length"})

    # Check 2: Timestamp
    try:
        ts = int(timestamp)
        age = int(datetime.now().timestamp()) - ts
        if age > 300:
            findings.append({"check": "timestamp", "result": "WARN", "detail": f"Timestamp is {age}s old — replay window may be open"})
            if age > 3600:
                severity = "high"
        else:
            findings.append({"check": "timestamp", "result": "OK", "detail": f"Timestamp is {age}s old"})
    except ValueError:
        findings.append({"check": "timestamp", "result": "FAIL", "detail": "Invalid timestamp"})
        severity = "high"

    # Check 3: Nonce
    if not nonce:
        findings.append({"check": "nonce", "result": "FAIL", "detail": "No nonce provided — replay attacks possible"})
        severity = "critical"
    elif len(nonce) < 16:
        findings.append({"check": "nonce", "result": "WARN", "detail": f"Nonce is only {len(nonce)} chars — may be predictable"})
    else:
        findings.append({"check": "nonce", "result": "OK", "detail": "Nonce present and adequate length"})

    # Check 4: Signature method
    if signature_method != "RSA-SHA256":
        findings.append({"check": "signature_method", "result": "WARN", "detail": f"Signature method is {signature_method} — Mastercard default is RSA-SHA256; verify this is intentional"})

    # Check 5: Parameter normalization hints
    if parameters:
        param_keys = list(parameters.keys())
        if param_keys != sorted(param_keys):
            findings.append({"check": "param_normalization", "result": "WARN", "detail": "Parameters not alphabetically sorted — OAuth 1.0a requires sorted parameter order for signature base string"})

    # Recommendations
    result["severity"] = severity
    result["summary"] = f"Signature method: {signature_method} | Body hash: {'present' if parameters and parameters.get('oauth_body_hash') else 'MISSING'} | Nonce: {'present' if nonce else 'MISSING'}"
    result["recommendations"] = [
        "Always include oauth_body_hash — it integrity-protects the request body",
        "Use cryptographically random nonces (minimum 16 bytes, URL-safe base64)",
        "Enforce server-side timestamp freshness (reject > 5 min old)",
        "Track nonces server-side to prevent replay within the freshness window",
        "Maintain consistent parameter normalization (sorted, percent-encoded per RFC 3986)",
        "Verify signature method matches the server's expected method (RSA-SHA256 for Mastercard)",
    ]

    return result


# ============================================================
# TOOL 3: Token Replay Check
# ============================================================

@app.tool()
def token_replay_check(
    token_type: str = "JWT",
    has_expiry: bool = True,
    has_nonce: bool = False,
    has_timestamp: bool = True,
    replay_test_result: Optional[str] = None,
    jwt_alg: Optional[str] = None,
) -> dict:
    """
    Check a token implementation for replay vulnerability.

    OWASP API2:2023 — Broken Authentication.
    Detects missing expiry, missing nonce, alg:none, and replay acceptance.

    replay_test_result: outcome of a replay test (e.g. "accepted_1min", "accepted_24h", "rejected")
    """
    result = {
        "analysis_timestamp": datetime.utcnow().isoformat(),
        "token_type": token_type,
        "replay_test_result": replay_test_result,
        "vulnerability_score": 0,
        "findings": [],
        "severity": "info",
        "recommendations": [],
    }

    findings = result["findings"]
    score = 0
    severity = "info"

    # Check 1: JWT alg
    if token_type == "JWT" and jwt_alg:
        if jwt_alg.lower() == "none":
            findings.append({"check": "jwt_alg", "result": "FAIL", "detail": "JWT algorithm is 'none' — token is unsigned, trivially forgeable"})
            score += 10
            severity = "critical"
        elif jwt_alg.upper() in ("HS256", "HS384", "HS512"):
            findings.append({"check": "jwt_alg", "result": "INFO", "detail": f"JWT uses symmetric HMAC ({jwt_alg}) — ensure secret is strong and not exposed"})
        elif jwt_alg.upper() in ("RS256", "RS384", "RS512", "ES256", "ES384", "ES512"):
            findings.append({"check": "jwt_alg", "result": "OK", "detail": f"JWT uses asymmetric signing ({jwt_alg}) — good practice"})

    # Check 2: Expiry
    if not has_expiry:
        findings.append({"check": "expiry", "result": "FAIL", "detail": "Token has no expiry — can be replayed indefinitely"})
        score += 8
        severity = "critical" if severity != "critical" else "critical"
    else:
        findings.append({"check": "expiry", "result": "OK", "detail": "Token has expiry"})

    # Check 3: Nonce / JTI
    if not has_nonce:
        findings.append({"check": "nonce", "result": "WARN", "detail": "Token has no nonce/jti — replay within validity window is possible"})
        score += 4
        if severity != "critical":
            severity = "high"
    else:
        findings.append({"check": "nonce", "result": "OK", "detail": "Token has nonce/jti — replay within window can be detected"})

    # Check 4: Timestamp
    if not has_timestamp:
        findings.append({"check": "timestamp", "result": "WARN", "detail": "No timestamp in token — server cannot enforce freshness"})
        score += 3
    else:
        findings.append({"check": "timestamp", "result": "OK", "detail": "Token includes timestamp"})

    # Check 5: Replay test result
    if replay_test_result:
        if "accepted" in replay_test_result:
            timing = replay_test_result.replace("accepted_", "")
            try:
                t = int(timing.replace("h", "").replace("min", "").replace("s", ""))
                unit = "s"
                if "h" in replay_test_result:
                    unit = "h"
                    t *= 3600
                elif "min" in replay_test_result:
                    unit = "min"
                    t *= 60
                findings.append({"check": "replay_test", "result": "FAIL", "detail": f"Replayed token ACCEPTED after {t}{unit} — missing freshness enforcement"})
                score += 10
                severity = "critical"
            except ValueError:
                findings.append({"check": "replay_test", "result": "FAIL", "detail": f"Replayed token ACCEPTED ({replay_test_result}) — freshness not enforced"})
                score += 8
                if severity != "critical":
                    severity = "high"
        elif "rejected" in replay_test_result:
            findings.append({"check": "replay_test", "result": "OK", "detail": f"Replayed token REJECTED — freshness enforcement working"})
        elif "concurrent" in replay_test_result:
            findings.append({"check": "replay_test", "result": "WARN", "detail": "Concurrent replay accepted — possible double-spend / race condition"})
            score += 5
            if severity != "critical":
                severity = "high"

    result["vulnerability_score"] = min(score, 100)
    result["severity"] = severity
    result["summary"] = f"Score: {score}/100 | Critical: {len([f for f in findings if f['result'] == 'FAIL'])} | Warnings: {len([f for f in findings if f['result'] == 'WARN'])}"
    result["recommendations"] = [
        "Always include exp (expiry) claim in JWTs — short-lived (5-15 min for access tokens)",
        "Include jti (unique token ID) or nonce for replay detection",
        "Include iat (issued at) timestamp for freshness enforcement",
        "Use asymmetric signing (RS256/ES256) for JWTs when possible — avoids secret distribution",
        "Reject tokens where exp has passed (with small clock-skew tolerance, e.g. 30s)",
        "Track used jti values server-side to detect replay within validity window",
        "If using HMAC JWT (HS256), use a strong secret (min 32 bytes, randomly generated)",
        "Never accept alg:none tokens — explicitly reject or require a whitelist of algorithms",
    ]

    return result


# ============================================================
# TOOL 4: ISO 8583 Analyzer
# ============================================================

@app.tool()
def iso8583_analyze(
    message_hex: str = "",
    fields: Optional[dict] = None,
    has_mac: bool = True,
    has_stan: bool = True,
    has_rrn: bool = True,
    replay_test_result: Optional[str] = None,
) -> dict:
    """
    Analyze an ISO 8583 message for field-level weaknesses.

    Key fields:
      DE4  = Amount
      DE11 = STAN (System Trace Audit Number)
      DE37 = RRN (Retrieval Reference Number)
      DE41 = Terminal ID
      DE42 = Merchant ID
      DE55 = Track data / PAN / EMV data

    Checks:
    - MAC coverage of critical fields
    - STAN/RRN uniqueness
    - Cross-merchant IDOR (DE41/DE42 manipulation)
    - Replay resistance
    - Ghost transaction risk
    """
    result = {
        "analysis_timestamp": datetime.utcnow().isoformat(),
        "message_info": {
            "has_hex": bool(message_hex),
            "hex_length": len(message_hex),
            "field_count": len(fields) if fields else 0,
        },
        "field_analysis": {},
        "findings": [],
        "severity": "info",
        "recommendations": [],
    }

    findings = result["findings"]
    severity = "info"

    # Check 1: MAC coverage
    if not has_mac:
        findings.append({"check": "MAC_coverage", "result": "FAIL", "detail": "No MAC on message — all fields can be tampered freely"})
        severity = "critical"
    else:
        findings.append({"check": "MAC_coverage", "result": "OK", "detail": "MAC present on message"})
        result["field_analysis"]["DE4_amount_mac"] = {"status": "check_required", "note": "Verify DE4 (amount) is included in MAC calculation"}
        result["field_analysis"]["DE42_merchant_mac"] = {"status": "check_required", "note": "Verify DE42 (merchant ID) is included in MAC — cross-merchant IDOR risk if not"}
        result["field_analysis"]["DE41_terminal_mac"] = {"status": "check_required", "note": "Verify DE41 (terminal ID) is included in MAC"}
        result["field_analysis"]["DE55_card_mac"] = {"status": "check_required", "note": "Verify DE55 (card/track data) is included in MAC — card identity bypass if not"}

    # Check 2: STAN uniqueness
    if not has_stan:
        findings.append({"check": "STAN_uniqueness", "result": "WARN", "detail": "No STAN (DE11) — cannot detect duplicate financial messages"})
    else:
        findings.append({"check": "STAN_uniqueness", "result": "OK", "detail": "STAN present — verify server enforces uniqueness"})

    # Check 3: RRN uniqueness
    if not has_rrn:
        findings.append({"check": "RRN_uniqueness", "result": "WARN", "detail": "No RRN (DE37) — cannot correlate transactions across systems"})
    else:
        findings.append({"check": "RRN_uniqueness", "result": "OK", "detail": "RRN present — verify server enforces uniqueness"})

    # Check 4: Cross-merchant IDOR
    if fields and "DE42" in fields:
        result["field_analysis"]["DE42_merchant_id"] = {"value": fields["DE42"], "risk": "IDOR if not MAC-protected — attacker can change DE42 to act as another merchant"}
    if fields and "DE41" in fields:
        result["field_analysis"]["DE41_terminal_id"] = {"value": fields["DE41"], "risk": "IDOR if not MAC-protected — attacker can change DE41 to use another terminal"}

    # Check 5: Ghost transactions
    if has_mac and (not has_stan or not has_rrn):
        findings.append({"check": "ghost_transactions", "result": "WARN", "detail": "Missing STAN/RRN with MAC present — approved transactions may be invisible in merchant dashboard (ghost txns)"})
        if severity != "critical":
            severity = "high"
    elif replay_test_result and "accepted" in replay_test_result:
        findings.append({"check": "replay_resistance", "result": "FAIL", "detail": f"Replay test: identical message ACCEPTED twice ({replay_test_result}) — no STAN/RRN dedup on server"})
        severity = "critical"
    elif replay_test_result and "rejected" in replay_test_result:
        findings.append({"check": "replay_resistance", "result": "OK", "detail": "Replay test: duplicate message REJECTED — STAN/RRN uniqueness enforced"})

    # Check 6: Amount field
    if fields and "DE4" in fields:
        amt = fields["DE4"]
        result["field_analysis"]["DE4_amount"] = {"value": amt, "risk": "If not MAC-protected, attacker can change amount — e.g. $500 → $5"}
        if not has_mac:
            findings.append({"check": "amount_integrity", "result": "FAIL", "detail": "DE4 (amount) not MAC-protected — amount can be altered"})

    result["severity"] = severity
    critical_f = [f for f in findings if f["result"] == "FAIL"]
    high_f = [f for f in findings if f["result"] == "WARN"]
    result["summary"] = f"{len(critical_f)} critical, {len(high_f)} warnings | MAC: {'yes' if has_mac else 'NO'} | STAN: {'yes' if has_stan else 'NO'} | RRN: {'yes' if has_rrn else 'NO'}"
    result["recommendations"] = [
        "MAC must cover ALL financial fields: DE4 (amount), DE41 (terminal), DE42 (merchant), DE55 (card data)",
        "Enforce STAN (DE11) uniqueness server-side — reject duplicate STANs",
        "Enforce RRN (DE37) uniqueness server-side — RRN is globally unique across all transactions",
        "Correlate every approved transaction against merchant dashboard — any mismatch = ghost transaction",
        "Replay test: submit identical MTI-1200 message twice — second must be rejected",
        "Test amount integrity: flip a byte in DE4 — MAC must reject the modified message",
        "Test cross-merchant IDOR: flip DE42 to another merchant's ID — MAC must reject",
        "Use ISO 8583 message type indicators correctly: MTI 100 (authorization), 200 (financial request), 300 (advice), 800 (reversal)",
    ]

    return result


# ============================================================
# TOOL 5: Check Fraud Pattern Detector
# ============================================================

@app.tool()
def check_fraud_pattern(
    check_image_description: Optional[str] = None,
    micr_line: Optional[str] = None,
    routing_number: Optional[str] = None,
    account_number: Optional[str] = None,
    check_number: Optional[str] = None,
    suspicious_indicators: Optional[List[str]] = None,
) -> dict:
    """
    Analyze check details for fraud indicators.

    Detects:
    - MICR E-13B format anomalies
    - Routing number validity (ABA check digit)
    - Account number pattern anomalies
    - Check 21 truncation indicators
    - Remote deposit capture red flags
    - Positive pay mismatch potential
    """
    result = {
        "analysis_timestamp": datetime.utcnow().isoformat(),
        "check_details": {
            "micr_line": micr_line,
            "routing_number": routing_number,
            "account_number": account_number,
            "check_number": check_number,
            "image_description": check_image_description,
        },
        "fraud_indicators": [],
        "risk_score": 0,
        "severity": "info",
        "recommendations": [],
    }

    indicators = result["fraud_indicators"]
    score = 0
    severity = "info"

    # Check 1: MICR E-13B format
    if micr_line:
        # Basic MICR format: MMF (bank code) AAAA (account) C (check digit) BBB (routing)
        micr_clean = micr_line.replace(" ", "")
        # ABA routing number is 9 digits
        routing_match = re.search(r"\d{9}", micr_clean)
        if not routing_match:
            indicators.append({"indicator": "MICR_format", "severity": "high", "detail": "No 9-digit routing number found in MICR line — may be altered or non-standard"})
            score += 15
            severity = "high"
        else:
            routing = routing_match.group()
            # ABA check digit verification
            weights = [3, 7, 1, 3, 7, 1, 3, 7, 1]
            total = sum(int(routing[i]) * weights[i] for i in range(8))
            check_digit = total % 10
            if int(routing[8]) != check_digit:
                indicators.append({"indicator": "ABA_check_digit", "severity": "critical", "detail": f"Routing {routing} fails ABA check digit (expected {check_digit}, got {routing[8]}) — routing number is invalid or forged"})
                score += 25
                severity = "critical"
            else:
                indicators.append({"indicator": "ABA_check_digit", "severity": "ok", "detail": f"Routing {routing} passes ABA check digit verification"})

        # Check number format
        if check_number:
            if not check_number.isdigit():
                indicators.append({"indicator": "check_number_format", "severity": "medium", "detail": f"Check number '{check_number}' is not purely numeric — may be altered"})
                score += 5
            elif len(check_number) > 6:
                indicators.append({"indicator": "check_number_length", "severity": "medium", "detail": f"Check number is {len(check_number)} digits — unusually long (typical: 3-6 digits)"})
                score += 3

    # Check 2: Routing number validation
    if routing_number:
        if not re.match(r"^\d{9}$", routing_number):
            indicators.append({"indicator": "routing_format", "severity": "high", "detail": f"Routing number '{routing_number}' is not 9 digits — invalid format"})
            score += 10
            if severity != "critical":
                severity = "high"
        elif routing_number.startswith("0"):
            indicators.append({"indicator": "routing_region", "severity": "info", "detail": "Routing starts with 0 — East Coast/Florida region (not inherently suspicious)"})
        elif routing_number.startswith("1"):
            indicators.append({"indicator": "routing_region", "severity": "info", "detail": "Routing starts with 1 — Northeast region"})

    # Check 3: Account number anomalies
    if account_number:
        if not account_number.isdigit():
            indicators.append({"indicator": "account_format", "severity": "high", "detail": f"Account number '{account_number}' is not purely numeric — altered or non-standard"})
            score += 10
            if severity != "critical":
                severity = "high"
        elif len(account_number) < 6:
            indicators.append({"indicator": "account_length", "severity": "medium", "detail": f"Account number is only {len(account_number)} digits — shorter than typical (8-12 digits)"})
            score += 5
        elif len(account_number) > 17:
            indicators.append({"indicator": "account_length", "severity": "medium", "detail": f"Account number is {len(account_number)} digits — unusually long"})
            score += 3

    # Check 4: Suspicious indicators
    if suspicious_indicators:
        for ind in suspicious_indicators:
            ind_lower = ind.lower()
            if "alteration" in ind_lower or "erasures" in ind_lower or "bleach" in ind_lower:
                indicators.append({"indicator": "physical_alteration", "severity": "critical", "detail": "Physical alteration detected (erasures, bleach, overwrite) — check is likely fraudulently modified"})
                score += 30
                severity = "critical"
            elif "new_account" in ind_lower or "different_account" in ind_lower:
                indicators.append({"indicator": "account_mismatch", "severity": "high", "detail": "Check deposited to different account than payee expected — potential credential theft or account takeover"})
                score += 15
                if severity != "critical":
                    severity = "high"
            elif "remote_deposit" in ind_lower:
                indicators.append({"indicator": "RDC_risk", "severity": "medium", "detail": "Remote deposit capture — higher fraud risk, verify with positive pay if available"})
                score += 5
            elif "duplicate" in ind_lower or "already_deposited" in ind_lower:
                indicators.append({"indicator": "duplicate_deposit", "severity": "critical", "detail": "Check already deposited — double-presentment fraud or check 21 duplicate"})
                score += 25
                severity = "critical"

    # Check 5: Positive pay mismatch potential
    if routing_number and account_number and check_number:
        result["positive_pay_status"] = {
            "can_verify": True,
            "note": "Submit to positive pay system: routing + account + check number + amount + payee. Mismatch = reject.",
        }

    result["risk_score"] = min(score, 100)
    result["severity"] = severity if severity != "info" else ("low" if score == 0 else "medium")
    result["summary"] = f"Risk score: {score}/100 | Indicators: {len(indicators)} | Severity: {result['severity']}"
    result["recommendations"] = [
        "Submit all checks to positive pay system for automated matching",
        "Verify MICR line integrity — any physical alteration = reject immediately",
        "Confirm ABA check digit on routing number before processing",
        "Flag checks where payee name doesn't match account holder",
        "For remote deposit capture: require higher resolution images, detect photo reuse via hash",
        "Maintain check 21 truncation records — track original vs truncated check",
        "Monitor for duplicate deposit attempts (same check number, different account)",
        "Use image analysis for tampering detection: erasure marks, overwritten numbers, reprinted MICR",
    ]

    return result


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    import uvicorn
    app.runtransport()
