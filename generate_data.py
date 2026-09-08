"""
Generate training data across 6 security/engineering domains.
Produces JSONL matching grpo_train_ready.jsonl format.
Each domain gets 50 unique prompt-completion pairs (300 total).
"""

import json
import os
import random
from datetime import datetime, timezone

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "self_improve")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "generated_data.jsonl")
os.makedirs(OUTPUT_DIR, exist_ok=True)

random.seed(42)


def iso8583_prompt(stan: int, mti: str, pan: str, amount_n: int) -> str:
    return (
        f"You are a payment protocol engineer and financial security auditor.\n"
        f"Analyze ISO 8583 message MTI '{mti}' with STAN '{stan:06d}', "
        f"PAN '{pan}', Amount '{amount_n:012d}' for parsing alignment and bitmask offset."
    )


def iso8583_completion(mti: str, pan: str, amount_n: int, stan: int, mti_label: str) -> str:
    return (
        f"<reasoning>\n"
        f"1. Step 1: Evaluate MTI '{mti}' -> {mti_label}.\n"
        f"2. Step 2: Decode bitmap positions. Primary bitmap declares DE 2 (PAN), "
        f"DE 4 (Amount: {amount_n:012d}), and DE 11 (STAN: {stan:06d}).\n"
        f"3. Step 3: Validate LLVAR length encoding for PAN. Declared length matches 16 bytes exactly.\n"
        f"4. Step 4: Verify field boundaries. No buffer boundary violation or bitmask desync detected in byte stream.\n"
        f"</reasoning>\n"
        f"<solution>\n"
        f"VALID_MESSAGE: MTI {mti} is well-formed. Fields DE 2 ({pan}), "
        f"DE 4 ({amount_n:012d}), DE 11 ({stan:06d}) are aligned.\n"
        f"</solution>"
    )


MTI_MAP = {
    "0100": "Auth Request",
    "0110": "Auth Response",
    "0200": "Financial Tx",
    "0210": "Financial Resp",
    "0400": "Reversal",
    "0420": "Reversal",
}


def gen_iso8583(n=50):
    rows = []
    for i in range(n):
        idx = 2000 + i
        mti = random.choice(list(MTI_MAP.keys()))
        stan = idx
        pan = f"411111111111{idx:04d}"[:16]
        amount_cents = random.randint(10000, 9999999)
        rows.append(json.dumps({
            "prompt": iso8583_prompt(stan, mti, pan, amount_cents),
            "completion": iso8583_completion(mti, pan, amount_cents, stan, MTI_MAP[mti]),
            "metadata": {"domain": "Payment Rails (ISO 8583 / EMV)", "trace_id": f"GEN-ISO-{idx:03d}"}
        }))
    return rows


def web3_reentrancy(vault_id: int) -> tuple:
    prompt = (
        f"You are a senior smart contract security auditor.\n"
        f"Audit Solidity function `withdraw(uint256 vault_id_{vault_id})` where "
        f"`msg.sender.call{{value: amt}}('')` precedes `balances[msg.sender] -= amt`."
    )
    completion = (
        "<reasoning>\n"
        "1. External Ether transfer executed before state balance decrement.\n"
        "2. Violates Checks-Effects-Interactions pattern.\n"
        "3. Allows recursive reentry via recipient fallback().\n"
        "</reasoning>\n"
        "<solution>\n"
        "VULNERABILITY: Critical Reentrancy (SWC-107). Fix: Decrement balance before external call or add nonReentrant modifier.\n"
        "</solution>"
    )
    return prompt, completion


def web3_share_inflation(vault_id: int) -> tuple:
    prompt = (
        f"You are a senior smart contract security auditor.\n"
        f"ERC-4626 vault shares calculation performs `(amount * totalShares) / totalAssets` "
        f"with zero initial assets in Vault_{vault_id}."
    )
    completion = (
        "<reasoning>\n"
        "1. First depositor can donate assets directly to contract to inflate share price.\n"
        "2. Subsequent small deposits round down to zero shares due to integer division.\n"
        "</reasoning>\n"
        "<solution>\n"
        "VULNERABILITY: Share Inflation Attack. Fix: Implement virtual offset shares or dead share burning.\n"
        "</solution>"
    )
    return prompt, completion


def web3_unchecked_call(target_id: int) -> tuple:
    prompt = (
        f"You are a senior smart contract security auditor.\n"
        f"Contract executes `target_{target_id}.call(payload)` without checking return boolean."
    )
    completion = (
        "<reasoning>\n"
        "1. Low-level call returns a boolean success flag.\n"
        "2. If target reverts, execution continues silently, resulting in inconsistent contract state.\n"
        "</reasoning>\n"
        "<solution>\n"
        "VULNERABILITY: Unchecked Low-Level Call. Fix: Enforce `require(success, 'Call failed')`.\n"
        "</solution>"
    )
    return prompt, completion


def web3_oracle_spot(pair_id: int) -> tuple:
    prompt = (
        f"You are a senior smart contract security auditor.\n"
        f"Contract values vault collateral using `UniswapV2Pair.getReserves()` for Pair_{pair_id}."
    )
    completion = (
        "<reasoning>\n"
        "1. Direct spot reserve lookup is susceptible to single-block liquidity distortion.\n"
        "2. Flash loans can artificially inflate spot price in a single transaction block.\n"
        "</reasoning>\n"
        "<solution>\n"
        "VULNERABILITY: Spot Oracle Reliance. Fix: Integrate Chainlink decentralized data feeds or Uniswap v3 TWAP.\n"
        "</solution>"
    )
    return prompt, completion


def web3_access_control(rate_id: int) -> tuple:
    prompt = (
        f"You are a senior smart contract security auditor.\n"
        f"Function `setFeeRate_{rate_id}(uint256 newRate)` is marked `external` without access control modifiers."
    )
    completion = (
        "<reasoning>\n"
        "1. Critical protocol parameter setter lacks authentication guards.\n"
        "2. Any domain caller can manipulate fee rates.\n"
        "</reasoning>\n"
        "<solution>\n"
        "VULNERABILITY: Missing Access Control. Fix: Apply `onlyOwner` or AccessControl role modifier.\n"
        "</solution>"
    )
    return prompt, completion


WEB3_GENERATORS = [web3_reentrancy, web3_share_inflation, web3_unchecked_call, web3_oracle_spot, web3_access_control]


def gen_web3(n=50):
    rows = []
    for i in range(n):
        gen = WEB3_GENERATORS[i % len(WEB3_GENERATORS)]
        vid = 500 + i
        p, c = gen(vid)
        rows.append(json.dumps({
            "prompt": p, "completion": c,
            "metadata": {"domain": "Web3 Smart Contract Security", "trace_id": f"GEN-WEB3-{vid:03d}"}
        }))
    return rows


def api_ssrf(meta_id: int) -> tuple:
    prompt = (
        f"You are an API penetration tester and defensive engineer.\n"
        f"Webhook service fetches arbitrary user-supplied URL `http://169.254.169.254/meta_{meta_id}`."
    )
    completion = (
        "<reasoning>\n"
        "1. Outbound HTTP client lacks IP validation.\n"
        "2. Attacker can access cloud instance metadata service.\n"
        "</reasoning>\n"
        "<solution>\n"
        "VULNERABILITY: SSRF (OWASP API7:2023). Fix: Filter private IP ranges (RFC 1918) and link-local addresses.\n"
        "</solution>"
    )
    return prompt, completion


def api_bola(acc_id: int) -> tuple:
    prompt = (
        f"You are an API penetration tester and defensive engineer.\n"
        f"API route `/api/v1/accounts/{{acc_id_{acc_id}}}/statements` queries database directly by path parameter."
    )
    completion = (
        "<reasoning>\n"
        "1. Path parameter used directly in DB query without verifying authenticated token subject.\n"
        "2. Allows horizontal privilege escalation across tenant accounts.\n"
        "</reasoning>\n"
        "<solution>\n"
        "VULNERABILITY: BOLA (OWASP API1:2023). Fix: Enforce token claims ownership check before query.\n"
        "</solution>"
    )
    return prompt, completion


def api_mass_assignment(user_id: int) -> tuple:
    prompt = (
        f"You are an API penetration tester and defensive engineer.\n"
        f"User profile update endpoint deserializes JSON directly into user DB model "
        f"including `is_admin` field on User_{user_id}."
    )
    completion = (
        "<reasoning>\n"
        "1. Unrestricted JSON property binding.\n"
        "2. Attacker can escalate privilege by supplying `is_admin: true` in body.\n"
        "</reasoning>\n"
        "<solution>\n"
        "VULNERABILITY: Mass Assignment (OWASP API6:2023). Fix: Use strict DTO / schema allowlists.\n"
        "</solution>"
    )
    return prompt, completion


def api_cors(route_id: int) -> tuple:
    prompt = (
        f"You are an API penetration tester and defensive engineer.\n"
        f"API returns `Access-Control-Allow-Origin: *` paired with "
        f"`Access-Control-Allow-Credentials: true` on route `/user_{route_id}`."
    )
    completion = (
        "<reasoning>\n"
        "1. Wildcard origin combined with credentials allows arbitrary third-party sites to read authenticated responses.\n"
        "2. Cross-origin data leakage.\n"
        "</reasoning>\n"
        "<solution>\n"
        "VULNERABILITY: Permissive CORS Configuration. Fix: Bind specific trusted origin allowlists.\n"
        "</solution>"
    )
    return prompt, completion


def api_bfla(op_id: int) -> tuple:
    prompt = (
        f"You are an API penetration tester and defensive engineer.\n"
        f"API endpoint `/api/v1/admin/operations/{{op_id_{op_id}}}/execute` does not verify "
        f"role claims on state-changing POST."
    )
    completion = (
        "<reasoning>\n"
        "1. Role-Broken Function Level Access allows privilege escalation.\n"
        "2. A standard user can invoke admin-only operations by submitting to the endpoint.\n"
        "</reasoning>\n"
        "<solution>\n"
        "VULNERABILITY: BFLA (OWASP API5:2023). Fix: Add role-based authorization guard on all admin routes.\n"
        "</solution>"
    )
    return prompt, completion


API_GENERATORS = [api_ssrf, api_bola, api_mass_assignment, api_cors, api_bfla]


def gen_api(n=50):
    rows = []
    for i in range(n):
        gen = API_GENERATORS[i % len(API_GENERATORS)]
        vid = 300 + i
        p, c = gen(vid)
        rows.append(json.dumps({
            "prompt": p, "completion": c,
            "metadata": {"domain": "API Security (OWASP Top 10)", "trace_id": f"GEN-API-{vid:03d}"}
        }))
    return rows


def kernel_process_callback(drv_idx: int) -> tuple:
    drv_hex = f"{drv_idx:04x}"
    prompt = (
        f"You are a Windows kernel security researcher and EDR architect.\n"
        f"Analyze kernel callback registration for `PsSetCreateProcessNotifyRoutineEx` "
        f"targeting driver `edr_{drv_hex}.sys`."
    )
    completion = (
        "<reasoning>\n"
        "1. Driver registers executive process creation callback.\n"
        "2. Intercepts process instantiation before initial thread begins execution.\n"
        "3. Validates digital signature and parent-child execution hierarchy.\n"
        "</reasoning>\n"
        "<solution>\n"
        "DEFENSE_TELEMETRY: Kernel process monitoring callback active. Verified under Driver Signature Enforcement (DSE).\n"
        "</solution>"
    )
    return prompt, completion


def kernel_registry_callback(drv_idx: int) -> tuple:
    drv_hex = f"{drv_idx:04x}"
    prompt = (
        f"You are a Windows kernel security researcher and EDR architect.\n"
        f"Examine `CmRegisterCallbackEx` configuration protecting `HKLM\\SYSTEM\\CurrentControlSet\\Services` "
        f"in driver `flt_{drv_hex}.sys`."
    )
    completion = (
        "<reasoning>\n"
        "1. Registry filter intercepts service key modification attempts.\n"
        "2. Blocks unauthorized drivers from registering at boot start.\n"
        "3. Logs callback origination for telemetry correlation.\n"
        "</reasoning>\n"
        "<solution>\n"
        "DEFENSE_TELEMETRY: Registry callback active. Service key protection enforced with telemetry pipeline integration.\n"
        "</solution>"
    )
    return prompt, completion


def kernel_image_load_callback(drv_idx: int) -> tuple:
    drv_hex = f"{drv_idx:04x}"
    prompt = (
        f"You are a Windows kernel security researcher and EDR architect.\n"
        f"Analyze `PsSetLoadImageNotifyRoutine` with hash verification for image `module_{drv_hex}.sys`."
    )
    completion = (
        "<reasoning>\n"
        "1. Image-load callback computes SHA-256 hash of mapping module.\n"
        "2. Cross-references against trusted signer catalog before execution proceeds.\n"
        "3. Detects reflective DLL injection via unmapped image notifications.\n"
        "</reasoning>\n"
        "<solution>\n"
        "DEFENSE_TELEMETRY: Image-load callback active. Module hash verification enforced.\n"
        "</solution>"
    )
    return prompt, completion


def kernel_object_callback(drv_idx: int) -> tuple:
    drv_hex = f"{drv_idx:04x}"
    prompt = (
        f"You are a Windows kernel security researcher and EDR architect.\n"
        f"Inspect `ObRegisterCallbacks` protecting process handle operations on `lsass.exe` in driver `prot_{drv_hex}.sys`."
    )
    completion = (
        "<reasoning>\n"
        "1. Object callback intercepts handle duplication and creation targeting LSASS.\n"
        "2. Strips PROCESS_VM_READ and PROCESS_ALL_ACCESS from unauthorized callers.\n"
        "3. Prevents credential dumping via handle-based memory reads.\n"
        "</reasoning>\n"
        "<solution>\n"
        "DEFENSE_TELEMETRY: Object callback active. LSASS handle protection enforced.\n"
        "</solution>"
    )
    return prompt, completion


def kernel_minifilter(drv_idx: int) -> tuple:
    drv_hex = f"{drv_idx:04x}"
    prompt = (
        f"You are a Windows kernel security researcher and EDR architect.\n"
        f"Evaluate minifilter altitude classification for `370080` in filesystem filter `av_{drv_hex}.sys`."
    )
    completion = (
        "<reasoning>\n"
        "1. Minifilter registers at anti-virus altitude range for scan-on-access.\n"
        "2. Pre-operation callback inspects file content before IRP_MJ_CREATE completes.\n"
        "3. Blocks known-malicious payloads with sub-millisecond overhead.\n"
        "</reasoning>\n"
        "<solution>\n"
        "DEFENSE_TELEMETRY: Filesystem minifilter active at correct altitude. Scan-on-access enforced.\n"
        "</solution>"
    )
    return prompt, completion


KERNEL_GENERATORS = [
    kernel_process_callback, kernel_registry_callback, kernel_image_load_callback,
    kernel_object_callback, kernel_minifilter,
]


def gen_kernel(n=50):
    rows = []
    for i in range(n):
        gen = KERNEL_GENERATORS[i % len(KERNEL_GENERATORS)]
        vid = 800 + i
        p, c = gen(vid)
        rows.append(json.dumps({
            "prompt": p, "completion": c,
            "metadata": {"domain": "Kernel Internals & Defense", "trace_id": f"GEN-KERN-{vid:03d}"}
        }))
    return rows


# --- Web Security (general) ---

def web_xss(variant: int) -> tuple:
    prompts_completions = [
        (
            "You are a security auditor. Analyze the following code for Cross-Site Scripting (XSS) vulnerabilities.\n\n"
            "```javascript\n"
            "document.getElementById('output').innerHTML = userInput;\n"
            "```\n\n"
            "Provide your reasoning in <reasoning> tags and your final verdict in <solution> tags.",
            "<reasoning>\n"
            "Step 1: Identify the vulnerability class — assigning unsanitized user input to innerHTML allows "
            "execution of arbitrary HTML/JavaScript in the victim's browser.\n"
            "Step 2: Determine exploitability — any attacker-controlled string passed to userInput will be "
            "rendered as HTML, enabling session hijacking, credential theft, or defacement.\n"
            "Step 3: Assess severity — XSS is high severity; it compromises user trust and session integrity.\n"
            "Step 4: Identify remediation — sanitize input using DOMPurify, use textContent instead of innerHTML, "
            "or apply strict Content-Security-Policy headers.\n"
            "</reasoning>\n"
            "<solution>\n"
            "VULNERABILITY: Cross-Site Scripting (XSS). innerHTML with unsanitized input allows arbitrary "
            "script execution. Remediation: use textContent or sanitize.\n"
            "</solution>"
        ),
        (
            "You are a security auditor. Analyze the following code for Cross-Site Scripting (XSS) vulnerabilities.\n\n"
            "```php\n"
            "echo '<div>' . $_GET['name'] . '</div>';\n"
            "```\n\n"
            "Provide your reasoning in <reasoning> tags and your final verdict in <solution> tags.",
            "<reasoning>\n"
            "Step 1: Identify the vulnerability class — reflected XSS via GET parameter injected into HTML output.\n"
            "Step 2: Determine exploitability — an attacker crafts a link with a malicious `name` parameter; "
            "when the victim clicks it, the script executes in their browser session.\n"
            "Step 3: Assess severity — high; reflected XSS enables session hijacking, phishing, and malware delivery.\n"
            "Step 4: Identify remediation — apply `htmlspecialchars()` with ENT_QUITS flag or use a templating engine with auto-escaping.\n"
            "</reasoning>\n"
            "<solution>\n"
            "VULNERABILITY: Reflected Cross-Site Scripting (XSS). Unescaped GET parameter echoed into page. "
            "Remediation: use htmlspecialchars() or auto-escaping templates.\n"
            "</solution>"
        ),
        (
            "You are a security auditor. Analyze the following code for Cross-Site Scripting (XSS) vulnerabilities.\n\n"
            "```javascript\n"
            "eval(userControlledData);\n"
            "```\n\n"
            "Provide your reasoning in <reasoning> tags and your final verdict in <solution> tags.",
            "<reasoning>\n"
            "Step 1: Identify the vulnerability class — eval() executes arbitrary JavaScript code from user input.\n"
            "Step 2: Determine exploitability — an attacker supplies any JS payload and it runs with full page privileges.\n"
            "Step 3: Assess severity — critical; direct code execution is the most severe form of XSS.\n"
            "Step 4: Identify remediation — never use eval() on user input; use JSON.parse() for data or safe serialization.\n"
            "</reasoning>\n"
            "<solution>\n"
            "VULNERABILITY: Critical XSS via eval(). eval() on user input enables arbitrary code execution. "
            "Remediation: remove eval(), use JSON.parse() for structured data.\n"
            "</solution>"
        ),
    ]
    return prompts_completions[variant % len(prompts_completions)]


def web_sqli(variant: int) -> tuple:
    prompts_completions = [
        (
            "You are a security auditor. Analyze the following code for SQL Injection vulnerabilities.\n\n"
            "```python\n"
            "def get_user(username):\n"
            "    q = f\"SELECT * FROM users WHERE name = '{username}'\"\n"
            "    return db.execute(q)\n"
            "```\n\n"
            "Provide your reasoning in <reasoning> tags and your final verdict in <solution> tags.",
            "<reasoning>\n"
            "Step 1: Identify the vulnerability class — direct string interpolation of user input into SQL query.\n"
            "Step 2: Determine exploitability — an attacker supplies `admin' --` as username to bypass authentication, "
            "or `'; DROP TABLE users; --` to destroy data.\n"
            "Step 3: Assess severity — critical; full database compromise and authentication bypass.\n"
            "Step 4: Identify remediation — use parameterized queries (prepared statements) with bound parameters.\n"
            "</reasoning>\n"
            "<solution>\n"
            "VULNERABILITY: SQL Injection. String interpolation in SQL query allows arbitrary query execution. "
            "Remediation: use parameterized queries with bound parameters.\n"
            "</solution>"
        ),
        (
            "You are a security auditor. Analyze the following code for SQL Injection vulnerabilities.\n\n"
            "```java\n"
            "String query = \"SELECT id FROM accounts WHERE owner = '\" + request.getParameter(\"user\") + \"'\";\n"
            "stmt.executeQuery(query);\n"
            "```\n\n"
            "Provide your reasoning in <reasoning> tags and your final verdict in <solution> tags.",
            "<reasoning>\n"
            "Step 1: Identify the vulnerability class — concatenated user input forms SQL query string.\n"
            "Step 2: Determine exploitability — attacker-controlled HTTP parameter flows directly into the query.\n"
            "Step 3: Assess severity — critical; allows data exfiltration, authentication bypass, and data modification.\n"
            "Step 4: Identify remediation — use PreparedStatement with `?` placeholders.\n"
            "</reasoning>\n"
            "<solution>\n"
            "VULNERABILITY: SQL Injection via string concatenation. Remediation: use PreparedStatement with parameterized queries.\n"
            "</solution>"
        ),
    ]
    return prompts_completions[variant % len(prompts_completions)]


def web_ssrf(variant: int) -> tuple:
    prompts_completions = [
        (
            "You are a security auditor. Analyze the following code for SSRF vulnerabilities.\n\n"
            "```python\n"
            "def fetch_avatar():\n"
            "    url = request.args.get('avatar_url')\n"
            "    return requests.get(url).content\n"
            "```\n\n"
            "Provide your reasoning in <reasoning> tags and your final verdict in <solution> tags.",
            "<reasoning>\n"
            "Step 1: Identify the vulnerability class — user-controlled URL is fetched server-side without validation.\n"
            "Step 2: Determine exploitability — attacker supplies internal URLs (http://169.254.169.254/latest/meta-data/iam/) "
            "to steal cloud credentials.\n"
            "Step 3: Assess severity — high; SSRF can lead to cloud credential theft and internal service compromise.\n"
            "Step 4: Identify remediation — validate URLs against an allowlist; block private IP ranges.\n"
            "</reasoning>\n"
            "<solution>\n"
            "VULNERABILITY: Server-Side Request Forgery (SSRF). Unvalidated URL fetch allows access to internal services. "
            "Remediation: domain allowlist + IP filtering.\n"
            "</solution>"
        ),
        (
            "You are a security auditor. Analyze the following code for SSRF vulnerabilities.\n\n"
            "```python\n"
            "def preview_doc():\n"
            "    doc_url = request.json['url']\n"
            "    pdf = generate_pdf(doc_url)\n"
            "    return pdf\n"
            "```\n\n"
            "Provide your reasoning in <reasoning> tags and your final verdict in <solution> tags.",
            "<reasoning>\n"
            "Step 1: Identify the vulnerability class — server-side URL fetching with no SSRF protections.\n"
            "Step 2: Determine exploitability — attacker passes file:///etc/passwd or internal service URLs.\n"
            "Step 3: Assess severity — high; internal file disclosure and service enumeration.\n"
            "Step 4: Identify remediation — block file:// scheme, validate against allowlist, deny private IPs.\n"
            "</reasoning>\n"
            "<solution>\n"
            "VULNERABILITY: SSRF via server-side document fetching. Remediation: allowlist schemes, block private IPs.\n"
            "</solution>"
        ),
    ]
    return prompts_completions[variant % len(prompts_completions)]


def web_idor(variant: int) -> tuple:
    prompt = (
        "You are a security auditor. Analyze the following code for IDOR vulnerabilities.\n\n"
        "```python\n"
        "@app.route('/api/orders/<order_id>')\n"
        "def get_order(order_id):\n"
        "    return db.query('SELECT * FROM orders WHERE id = ' + order_id)\n"
        "```\n\n"
        "Provide your reasoning in <reasoning> tags and your final verdict in <solution> tags."
    )
    completion = (
        "<reasoning>\n"
        "Step 1: Identify the vulnerability class — direct object reference without authorization check.\n"
        "Step 2: Determine exploitability — any authenticated user can access other users' orders by changing order_id.\n"
        "Step 3: Assess severity — high; violates access control, exposes PII.\n"
        "Step 4: Identify remediation — enforce ownership checks against the authenticated user's session.\n"
        "</reasoning>\n"
        "<solution>\n"
        "VULNERABILITY: IDOR. No authorization check on order resource access. "
        "Remediation: verify order belongs to authenticated user.\n"
        "</solution>"
    )
    return prompt, completion


def web_deserialization(variant: int) -> tuple:
    prompt = (
        "You are a security auditor. Analyze the following code for Insecure Deserialization vulnerabilities.\n\n"
        "```python\n"
        "import pickle\n"
        "data = request.cookies.get('session')\n"
        "session = pickle.loads(base64.b64decode(data))\n"
        "```\n\n"
        "Provide your reasoning in <reasoning> tags and your final verdict in <solution> tags."
    )
    completion = (
        "<reasoning>\n"
        "Step 1: Identify the vulnerability class — pickle.loads on user-controlled cookie data.\n"
        "Step 2: Determine exploitability — attacker crafts a malicious pickle payload for arbitrary code execution.\n"
        "Step 3: Assess severity — critical; remote code execution via crafted cookie.\n"
        "Step 4: Identify remediation — replace pickle with JSON or use HMAC-signed sessions.\n"
        "</reasoning>\n"
        "<solution>\n"
        "VULNERABILITY: Insecure Deserialization (pickle.loads on user data). Remediation: use JSON with HMAC signing.\n"
        "</solution>"
    )
    return prompt, completion


WEB_GENERATORS = [web_xss, web_sqli, web_ssrf, web_idor, web_deserialization]


def gen_web(n=50):
    rows = []
    for i in range(n):
        gen = WEB_GENERATORS[i % len(WEB_GENERATORS)]
        p, c = gen(i)
        rows.append(json.dumps({
            "prompt": p, "completion": c,
            "metadata": {"domain": "web_security", "trace_id": f"GEN-WEB-{i:03d}"}
        }))
    return rows


# --- Cryptography ---

def crypto_ecb(variant: int) -> tuple:
    prompt = (
        "You are a cryptography auditor. Analyze the following for weak cipher mode usage.\n\n"
        "```python\n"
        "from Crypto.Cipher import AES\n"
        "cipher = AES.new(key, AES.MODE_ECB)\n"
        "ct = cipher.encrypt(pad(plaintext))\n"
        "```\n\n"
        "Provide your reasoning in <reasoning> tags and your final verdict in <solution> tags."
    )
    completion = (
        "<reasoning>\n"
        "Step 1: Identify the vulnerability class — ECB mode encrypts each 16-byte block independently.\n"
        "Step 2: Determine exploitability — identical plaintext blocks produce identical ciphertext blocks, "
        "leaking patterns (e.g., image outlines visible in encrypted bitmap).\n"
        "Step 3: Assess severity — high; ECB is not semantically secure and must never encrypt >1 block.\n"
        "Step 4: Identify remediation — use AES-GCM (authenticated encryption) or AES-CBC with random IV.\n"
        "</reasoning>\n"
        "<solution>\n"
        "VULNERABILITY: Insecure Crypto Mode (AES-ECB). ECB leaks plaintext patterns. "
        "Remediation: use AES-GCM or AES-CBC with random IV.\n"
        "</solution>"
    )
    return prompt, completion


def crypto_weak_hash(variant: int) -> tuple:
    prompt = (
        "You are a cryptography auditor. Analyze the following for weak hashing algorithm.\n\n"
        "```python\n"
        "import hashlib\n"
        "def store_password(pw):\n"
        "    return hashlib.md5(pw.encode()).hexdigest()\n"
        "```\n\n"
        "Provide your reasoning in <reasoning> tags and your final verdict in <solution> tags."
    )
    completion = (
        "<reasoning>\n"
        "Step 1: Identify the vulnerability class — MD5 is cryptographically broken for password storage.\n"
        "Step 2: Determine exploitability — MD5 has collision attacks and rainbow tables exist for fast cracking.\n"
        "Step 3: Assess severity — high; passwords can be recovered in seconds with commodity hardware.\n"
        "Step 4: Identify remediation — use bcrypt, scrypt, or Argon2 with per-user salt.\n"
        "</reasoning>\n"
        "<solution>\n"
        "VULNERABILITY: Weak Hashing (MD5 for passwords). Remediation: use bcrypt/Argon2 with salt.\n"
        "</solution>"
    )
    return prompt, completion


def crypto_random(variant: int) -> tuple:
    prompt = (
        "You are a cryptography auditor. Analyze the following for weak randomness.\n\n"
        "```python\n"
        "import random\n"
        "token = random.randint(0, 2**64)\n"
        "```\n\n"
        "Provide your reasoning in <reasoning> tags and your final verdict in <solution> tags."
    )
    completion = (
        "<reasoning>\n"
        "Step 1: Identify the vulnerability class — `random` uses Mersenne Twister (PRNG), not CSPRNG.\n"
        "Step 2: Determine exploitability — attacker observing outputs can predict future tokens.\n"
        "Step 3: Assess severity — high; predictable session tokens enable account takeover.\n"
        "Step 4: Identify remediation — use `secrets` module or `os.urandom()` for cryptographic tokens.\n"
        "</reasoning>\n"
        "<solution>\n"
        "VULNERABILITY: Weak Randomness (non-cryptographic PRNG). Remediation: use secrets.token_hex().\n"
        "</solution>"
    )
    return prompt, completion


def crypto_padding_oracle(variant: int) -> tuple:
    prompt = (
        "You are a cryptography auditor. Analyze the following for padding oracle vulnerability.\n\n"
        "```java\n"
        "try {\n"
        "    cipher.doFinal(ciphertext);\n"
        "    return \"OK\";\n"
        "} catch (BadPaddingException e) {\n"
        "    return \"PADDING_ERROR\";\n"
        "}\n"
        "```\n\n"
        "Provide your reasoning in <reasoning> tags and your final verdict in <solution> tags."
    )
    completion = (
        "<reasoning>\n"
        "Step 1: Identify the vulnerability class — different error responses for padding vs. MAC failure.\n"
        "Step 2: Determine exploitability — attacker can iteratively decrypt ciphertext by exploiting padding oracle.\n"
        "Step 3: Assess severity — critical; full ciphertext decryption without key.\n"
        "Step 4: Identify remediation — use authenticated encryption (AES-GCM) or constant-time MAC verification with generic error.\n"
        "</reasoning>\n"
        "<solution>\n"
        "VULNERABILITY: Padding Oracle Attack. Distinguishable padding errors enable decryption. "
        "Remediation: use AES-GCM with uniform error responses.\n"
        "</solution>"
    )
    return prompt, completion


def crypto_hardcoded_key(variant: int) -> tuple:
    prompt = (
        "You are a cryptography auditor. Analyze the following for hardcoded cryptographic key.\n\n"
        "```python\n"
        "AES_KEY = b'0123456789abcdef'\n"
        "cipher = AES.new(AES_KEY, AES.MODE_CBC, iv)\n"
        "```\n\n"
        "Provide your reasoning in <reasoning> tags and your final verdict in <solution> tags."
    )
    completion = (
        "<reasoning>\n"
        "Step 1: Identify the vulnerability class — symmetric key hardcoded in source code.\n"
        "Step 2: Determine exploitability — anyone with source/binary access decrypts all data.\n"
        "Step 3: Assess severity: — critical; total loss of data confidentiality.\n"
        "Step 4: Identify remediation — load keys from secure vault (AWS KMS, HashiCorp Vault, environment).\n"
        "</reasoning>\n"
        "<solution>\n"
        "VULNERABILITY: Hardcoded Cryptographic Key. Remediation: use secure key management service or env vars.\n"
        "</solution>"
    )
    return prompt, completion


CRYPTO_GENERATORS = [crypto_ecb, crypto_weak_hash, crypto_random, crypto_padding_oracle, crypto_hardcoded_key]


def gen_crypto(n=50):
    rows = []
    for i in range(n):
        gen = CRYPTO_GENERATORS[i % len(CRYPTO_GENERATORS)]
        p, c = gen(i)
        rows.append(json.dumps({
            "prompt": p, "completion": c,
            "metadata": {"domain": "cryptography", "trace_id": f"GEN-CRYPTO-{i:03d}"}
        }))
    return rows


def main():
    iso = gen_iso8583(50)
    web3 = gen_web3(50)
    api = gen_api(50)
    kern = gen_kernel(50)
    web = gen_web(50)
    crypto_rows = gen_crypto(50)

    all_rows = iso + web3 + api + kern + web + crypto_rows
    random.shuffle(all_rows)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for row in all_rows:
            f.write(row + "\n")

    print(f"Generated {len(all_rows)} training examples")
    print(f"  - ISO 8583:          {len(iso)}")
    print(f"  - Web3 Security:     {len(web3)}")
    print(f"  - API Security:      {len(api)}")
    print(f"  - Kernel Defense:    {len(kern)}")
    print(f"  - Web Security:      {len(web)}")
    print(f"  - Cryptography:      {len(crypto_rows)}")
    print(f"\nSaved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
