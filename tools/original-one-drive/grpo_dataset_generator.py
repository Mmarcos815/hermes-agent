#!/usr/bin/env python3
"""
GRPO & SFT Security Reasoning Dataset Generator
Generates verifiable, step-by-step chain-of-thought (CoT) reasoning traces
for fine-tuning models on vulnerability identification, protocol dissection,
and defensive remediation.

Output format: JSONL ready for Unsloth / Hugging Face SFT & GRPO reward trainers.
"""

import json, os

VULN_TEMPLATES = [
    {
        "domain": "ISO 8583 / Financial Rails",
        "prompt": "Analyze the following raw ISO 8583 message string and identify if the field length definition for Primary Account Number (DE 2) causes a parsing desync: '01007220400000808000164111111111111111000000000000015000'",
        "reasoning": (
            "1. Step 1: Examine the MTI -> '0100' indicates an Authorization Request.\n"
            "2. Step 2: Decode the Primary Bitmap -> '7220400000808000'. In binary, Bit 2 is set (indicating DE 2 PAN is present).\n"
            "3. Step 3: Analyze DE 2 format specification. DE 2 is defined as LLVAR (2-digit length prefix followed by variable length ASCII).\n"
            "4. Step 4: Inspect payload after bitmap. The first 2 characters are '16', which correctly declares a 16-digit PAN.\n"
            "5. Step 5: Extract 16 characters -> '4111111111111111'. Next field (DE 3 Processing Code) aligns exactly at index offset +16.\n"
            "6. Conclusion: The length header matches the payload length; no parsing desynchronization or buffer boundary violation exists."
        ),
        "solution": "VALID_PARSE: DE 2 correctly length-prefixed as LLVAR 16 digits. No desync detected."
    },
    {
        "domain": "API Security / Broken Object Level Authorization (BOLA)",
        "prompt": "Evaluate this API endpoint handler for access control flaws:\n\n```python\n@app.get('/api/v1/accounts/{account_id}/statement')\ndef get_statement(account_id: str, current_user = Depends(get_current_user)):\n    statement = db.query(Statement).filter(Statement.account_id == account_id).first()\n    return statement\n```",
        "reasoning": (
            "1. Step 1: Trace caller authentication. `get_current_user` injects `current_user` from the validated JWT token.\n"
            "2. Step 2: Trace database query parameters. The query uses `Statement.account_id == account_id` directly from the path parameter.\n"
            "3. Step 3: Check authorization linkage. There is no verification that `current_user.id` or `current_user.tenant_id` owns or is mapped to the requested `account_id`.\n"
            "4. Step 4: Vulnerability classification: OWASP API1:2023 - Broken Object Level Authorization (BOLA / IDOR). An authenticated user can read statements of any other account by altering the URL path parameter.\n"
            "5. Step 5: Remediation: Enforce user-tenant/account ownership validation before executing database lookup."
        ),
        "solution": "VULNERABILITY: BOLA (OWASP API1:2023). Fix: Add `filter(Statement.owner_id == current_user.id)` to enforce object-level ownership."
    },
    {
        "domain": "Cryptographic Verification / JWT Algorithm Confusion",
        "prompt": "A microservice verifies tokens with `jwt.decode(token, public_key, algorithms=['HS256', 'RS256'])`. What is the architectural flaw?",
        "reasoning": (
            "1. Step 1: Examine the algorithm allowlist -> both HMAC-SHA256 (symmetric) and RSA-SHA256 (asymmetric) are permitted in the same verification call.\n"
            "2. Step 2: Analyze key handling. The verification method uses `public_key`.\n"
            "3. Step 3: Attack surface analysis: If an attacker signs a forged token using HMAC-SHA256 (`HS256`) using the server's public key bytes as the HMAC secret, the library treats `public_key` as raw HMAC secret bytes rather than an asymmetric public key.\n"
            "4. Step 4: The verification check succeeds because the signature matches the HMAC computed using the known public key.\n"
            "5. Remediation: Restrict the algorithm list strictly to `['RS256']` and reject symmetric fallback when asymmetric keys are expected."
        ),
        "solution": "VULNERABILITY: JWT Key/Algorithm Confusion. Fix: Lock `algorithms=['RS256']` strictly when verifying asymmetric tokens."
    }
]

def generate_grpo_dataset(output_path: str):
    records = []
    for item in VULN_TEMPLATES:
        record = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a senior security researcher and protocol analyst. Reason through technical queries step by step using strict analytical logic before stating your final solution."
                },
                {
                    "role": "user",
                    "content": item["prompt"]
                },
                {
                    "role": "assistant",
                    "content": f"<reasoning>\n{item['reasoning']}\n</reasoning>\n<solution>\n{item['solution']}\n</solution>"
                }
            ],
            "metadata": {
                "domain": item["domain"]
            }
        }
        records.append(record)

    with open(output_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    return len(records)

if __name__ == "__main__":
    out_file = "C:/Users/mobil/orca/projects/my 1st/knowledge/grpo_security_reasoning_dataset.jsonl"
    count = generate_grpo_dataset(out_file)
    print(f"=== GRPO DATASET GENERATOR COMPLETED ===")
    print(f"Generated {count} multi-turn reasoning traces.")
    print(f"Dataset stored at: {out_file}")
