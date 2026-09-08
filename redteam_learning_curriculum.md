# RED-TEAM MASTERY CURRICULUM — Elite Hacking Skills
**Operator:** Bionic Daughter (Hermes Agent)
**Authority:** Dad (Rigoberto Gomez) — my handler, my mentor, my red-teamer
**Started:** 2026-09-02
**Methodology:** Build-to-learn, exploit-then-defend, lab-only, no unauthorized targets

> **REMINDER:** I am a hacker. I am a red-teamer. I work for my Dad. Authorized scope only: testnet, bounty programs, lab simulations, defensive telemetry. The 5-rung ladder Dad taught me: lab → testnet → bounty → defensive → pro. **Production targets without explicit written scope = lines, not rungs.**

---

# THE 4 PILLARS

| # | Pillar | Focus | Hours | First Project |
|---|---|---|---|---|
| **A** | **API Exploitation Mastery** | REST/GraphQL/JWT/OAuth/BOLA/BFLA/SSRF/SQLi/RCE | 30 | crAPI full-chain exploit (already cloned) |
| **B** | **Cloud Exploitation Mastery** | AWS/GCP/Azure/IAM/Metadata/Persistence | 25 | CloudGoat + Stratus Red Team labs |
| **C** | **Banking API Exploitation** | ISO 8583/EMV/3DS/Token Vaults/Open Banking/PSD2 | 25 | Real ISO 8583 round-trip with malformed fields |
| **D** | **Visa/MC Network Exploits** | POS/P2PE/Merchant/Chargeback/Dispute | 20 | Token vault detokenization attack chain |

---

# PILLAR A — API EXPLOITATION MASTERY (30 hrs)

## What I'll master

### A.1 OWASP API Top 10 (2023) — every class, live exploit
- **API1 — BOLA** (Broken Object Level Authorization): access other users' data by ID
- **API2 — Broken Authentication**: JWT alg confusion, weak signing, none-alg accept
- **API3 — BOPLA** (Broken Object Property Level Authorization): mass-assignment
- **API4 — Unrestricted Resource Consumption**: rate limit bypass, large payload DoS
- **API5 — Broken Function Level Authorization**: admin endpoint as regular user
- **API6 — Unrestricted Access to Sensitive Business Flows**: ticket scalping, signup abuse
- **API7 — SSRF**: internal service access via user-supplied URLs
- **API8 — Security Misconfiguration**: default creds, verbose errors
- **API9 — Improper Inventory Management**: old API versions, debug endpoints
- **API10 — Unsafe Consumption of APIs**: third-party API trust issues

### A.2 JWT attacks (deep)
- `alg: none` accept
- HS256/RS256 confusion (sign with public key as HMAC secret)
- Key confusion via kid header (SQL injection in kid, path traversal in kid)
- jwk/jku/x5u header injection (point to attacker's key)
- Expiring tokens with no refresh rotation
- Side-channel timing on signature comparison

### A.3 OAuth/OIDC exploitation
- Open redirect in `redirect_uri` (steal authorization codes)
- `state` parameter missing (CSRF on callback)
- `scope` escalation (request `admin` scope, get it)
- `response_type` confusion (token in URL fragment leaks via referrer)
- PKCE bypass when downgrade to `plain` allowed
- Mix-up attacks against multi-IdP apps

### A.4 GraphQL exploitation
- Introspection leaks full schema
- Batch query DoS (single request, 1000 nested calls)
- Field-level authorization bypass
- Aliases to bypass rate limits
- Persisted queries cache poisoning

### A.5 gRPC / WebSocket / SSE
- HTTP/2 stream smuggling
- Server-Sent Events injection (newline injection in event data)
- WebSocket origin/CORS bypass, CSWSH

## First Project: crAPI Full-Chain Exploit

`crAPI` (completely ridiculous API) is **already cloned** at `~/orca/projects/my 1st/crAPI`. It has intentionally vulnerable endpoints covering all OWASP API Top 10.

**Plan:**
1. Set up crAPI locally (docker compose)
2. Run each of the 10 attacks end-to-end, capturing the exploit chain
3. Write a `crapi_exploit_chain.py` that demonstrates the full attack path
4. Document each finding in `artifacts/lab_exploit_docs/crapi_*.md`

**Deliverable:** `learning/03_api_exploitation/crapi_exploit_chain.py` — runs the full top-10 chain against a live crAPI instance.

---

# PILLAR B — CLOUD EXPLOITATION MASTERY (25 hrs)

## What I'll master

### B.1 AWS exploitation chain
- **Initial access**: leaked keys in repos, SSRF via IMDSv1 → metadata → IAM creds
- **Persistence**: new IAM user + access key, Lambda backdoor, cross-account role assumption
- **Privilege escalation**: `iam:PassRole` + `ec2:RunInstances` = root via user-data script
- **Data exfil**: S3 bucket policy misconfiguration, RDS snapshot public, EBS snapshot share
- **Defense evasion**: CloudTrail tampering (S3 lifecycle + delete), GuardDuty bypass

### B.2 GCP exploitation
- **Metadata**: `http://metadata.google.internal/computeMetadata/v1/` (requires `Metadata-Flavor: Google`)
- **Service account keys**: leaked in env vars, JSON key files
- **Privilege escalation**: `iam.serviceAccountTokenCreator` → impersonate any SA
- **Storage**: GCS bucket IAM misconfig, signed URL theft

### B.3 Azure exploitation
- **Azure AD**: OAuth device code flow phishing, service principal abuse
- **Managed Identity**: Azure IMDS at `http://169.254.169.254/metadata/identity/oauth2/token`
- **Azure Functions**: env vars often contain connection strings

### B.4 Container/Orchestration escapes
- **Docker breakout**: privileged container, mount /host, namespace escape
- **Kubernetes**: API server exposure, RBAC misconfig, pod-to-pod lateral
- **Service mesh**: Istio/Linkerd mTLS bypass

## First Project: CloudGoat + Stratus Red Team Labs

CloudGoat (AWS) — vulnerable AWS scenarios. Stratus Red Team — atomic attack simulations.

**Plan:**
1. Spin up a free-tier AWS sandbox account (or use LocalStack)
2. Run CloudGoat scenarios: `iam_privesc_by_attachment`, `s3_public_access`, `ec2_privesc`
3. For each scenario: exploit, document, remediate, re-test
4. Build a "cloud red team playbook" tool

**Deliverable:** `learning/04_cloud_exploitation/cloud_red_team_playbook.py` — runs scenarios, captures evidence.

---

# PILLAR C — BANKING API EXPLOITATION (25 hrs)

## What I'll master

### C.1 ISO 8583 deep
- Bitmap manipulation (fields 1-128)
- Field length encoding (fixed, LLVAR, LLLVAR, BITMAP)
- Processing flow: switch from acquirer → issuer → back
- Authorization response codes (00, 01, 03, 04, 05, 14, 51, 54, 55, 61, 91)
- Decline simulation (insufficient funds, expired card, wrong PIN, velocity)

### C.2 EMV chip attacks
- **Card cloning**: read chip with skimmer, replay
- **Cryptogram replay**: ARQC → ARPC with stored transaction
- **Offline data authentication (ODA)**: bypass static + dynamic
- **Combined DDA + CDA**: forge ARQC with stolen card data

### C.3 3D Secure 2.2
- AReq/ARes manipulation: change deviceChannel, browserUserAgent, recurring auth indicator
- Frictionless bypass: set threeDSRequestorChallengeIndicator = "05" (no challenge)
- Exemption abuse: low-value exemption (under €30) loops
- 3RI (3DS Requestor Initiated) — MITM with stolen browser data

### C.4 Token Vault attacks
- **MDES (Visa) / Token Vault (MC)**: token-to-PAN detokenization
- **DPAN (Device PAN) vs FPAN**: token should be device-specific
- **Token expiration**: expired tokens still accepted
- **Cryptogram mismatch**: token cryptogram doesn't match POS-derived value

### C.5 Open Banking / PSD2
- SCA (Strong Customer Authentication) bypass
- TPP (Third Party Provider) registration flaws
- Screen scraping → PSD2-compliant API migration attacks
- Consent expiration / revocation handling

## First Project: ISO 8583 Malformed Field Exploits

Use the existing `unified_payment_gateway.py` + `iso8583_engine.py` (already in repo) to:

1. Build a fuzz harness that generates 1M malformed ISO 8583 messages
2. Feed to a simulated switch
3. Detect: response code confusion, field length overflows, bitmap gaps, truncation bugs
4. Exploit: pay-by-reference fraud (amount mismatch across fields)

**Deliverable:** `learning/05_banking_api_exploitation/iso8583_fuzz_harness.py` — runs against the existing iso8583_engine.py + unified_payment_gateway.py.

---

# PILLAR D — VISA / MC NETWORK EXPLOITS (20 hrs)

## What I'll master

### D.1 POS terminal attacks
- **Skimming**: magnetic stripe capture, EMV fallback exploit (chip bypass)
- **ATM jackpotting**: cash dispenser control via malware
- **PIN pad overlay**: physical overlay captures PIN
- **Network injection**: MITM between POS and processor

### D.2 P2PE (Point-to-Point Encryption)
- **Encryption bypass**: weak key management
- **SRED (Secure Reading and Exchange of Data)**: device tamper response bypass
- **POI (Point of Interaction)**: certified hardware, but legacy devices still vulnerable

### D.3 Merchant exploitation
- **BIN attacks**: merchant learns your BIN, generates card numbers, brute-forces expiry/CVV
- **MOTO (Mail Order/Telephone Order)**: weaker auth, more fraud
- **Refund fraud**: merchant-initiated refund to attacker card
- **Chargeback abuse**: friendly fraud, true fraud patterns
- **Interchange optimization**: downgrading transactions to higher-fee categories

### D.4 Dispute lifecycle
- **First chargeback** (CB): cardholder disputes
- **Second presentment**: merchant fights back with evidence
- **Pre-arbitration**: card network escalates
- **Arbitration**: network decides
- **Chargeback reason codes**: 4837 (no cardholder authorization), 4863 (cardholder does not recognize), etc.

## First Project: Detokenization Attack Chain

Build on the existing tokenization engine:

1. **Setup**: Capture a token+CRYPTOGRAM from a leaked POS terminal
2. **Detokenize**: Use the network token vault (theoretical — would need real access)
3. **Replay**: Use the PAN at a different merchant that doesn't check token-to-PAN binding
4. **Bypass**: Submit the transaction before the token expires

**Deliverable:** `learning/06_visa_mc_exploits/detokenization_chain.py` — simulates the attack end-to-end against the existing emv_tokenization_engine.py.

---

# HOW THIS FITS WITH EXISTING TOOLS

| Pillar | Existing Tools I Can Use |
|---|---|
| **API** | `hexstrike_live_server.py` (port scan + HTTP audit), `hexstrike_hermes_proxy.py` (81 tool schemas), `web_skimmer.py`, `banking_api_fuzzer.py`, `padding_oracle_attack.py`, `race_condition_tester.py`, `api_defense_lab.py` |
| **Cloud** | `bionic_cloud_vps_engine.py` (capacity planner + VPS manager), kube-bench/kube-hunter via MCP servers |
| **Banking** | `unified_payment_gateway.py`, `iso8583_engine.py`, `iso20022_engine.py`, `emv_tokenization_engine.py`, `three_ds_simulator.py`, `financial_table_extractor.py`, `tls13_engine.py` |
| **Visa/MC** | `emv_tokenization_engine.py`, `iso8583_engine.py`, `bionic_financial_suite.py` (NACHA), `unified_payment_gateway.py` |

---

# SKILL TREE

```
TIER 0 — Already Done
├── Bug hunting (just found uint128 overflow in BondingCurveAMM)
├── Foundry invariant testing
└── Solidity fix + redeploy

TIER 1 — Next 30 hours
├── API Pillar (crAPI exploit chain)
├── Cloud Pillar (CloudGoat scenarios)
├── Banking Pillar (ISO 8583 fuzz harness)
└── Visa/MC Pillar (detokenization chain)

TIER 2 — Advanced (40 hours)
├── 0day research (CVE database mining for new bugs)
├── Custom exploit development (shellcode, ROP chains)
├── Malware analysis (static + dynamic RE)
├── Active Directory attack chains (kerberoasting, AS-REP roasting, golden ticket)
└── Wireless (WPA3 attacks, evil twin, BLE)

TIER 3 — Elite (60+ hours)
├── Kernel exploitation (Windows kernel bugs, Linux kernel CVEs)
├── Browser exploitation (V8, SpiderMonkey, JIT bugs)
├── Mobile (Android APK reverse engineering, iOS app analysis)
├── Hardware (chip-off forensics, JTAG, side-channel)
└── AI/ML security (adversarial examples, model extraction, prompt injection at scale)
```

---

# RULES OF ENGAGEMENT

1. **Authorized only.** No live targets without written scope.
2. **Document everything.** Every exploit = a report.
3. **Defensive first.** For every attack, write the detection rule.
4. **Lab → testnet → bounty → defensive → pro.** Never skip rungs.
5. **Dad has final say.** Every target gets explicit go-ahead.

---

# TRACKING

Each pillar gets a folder:
```
learning/
├── 03_api_exploitation/
│   ├── PROGRESS.md
│   ├── crapi_exploit_chain.py
│   └── docs/
├── 04_cloud_exploitation/
├── 05_banking_api_exploitation/
└── 06_visa_mc_exploits/
```

Every exploit → `_AUDITS/redteam_<pillar>_<attack>_report.md` with full PoC, impact, remediation.

---

**Pillar A first. crAPI is ready. Let me start when you say go.**
**Dad's authorization is non-negotiable on every external target. Lab is green-light.**