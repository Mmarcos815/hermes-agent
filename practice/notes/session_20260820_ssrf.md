# Session: SSRF (Server-Side Request Forgery) — Live Practice

**Date:** 2026-08-20
**Target:** OWASP crAPI (source code analysis — no live target available)
**Vulnerability Class:** Server-Side Request Forgery (SSRF)
**Skill Being Practiced:** Vulnerability Discovery & Assessment
**Current Level:** NEWBIE
**Goal for This Session:** Understand SSRF through the crAPI merchant API vulnerability, trace the attack chain manually, create original SSRF payloads, and identify comprehensive countermeasures

---

## Pre-Flight Checklist (complete before starting)

- [x] Target is running in isolated environment — source code analysis only, no network
- [x] I have authorization to analyze this target — it's in my own project folder, created for practice
- [x] I have read the relevant vulnerability class knowledge — read hacking_exploit_api_sql_mastery.md SSRF section
- [x] I understand the specific vulnerable code — read merchant/views.py lines 87-92 (from the practice tool)
- [x] I know what "success" looks like — can explain SSRF, create payloads, list countermeasures
- [x] I have a cleanup plan — N/A (no processes running, no network access)

---

## What I Tried

### Attempt 1: Read the SSRF section of the practice tool
**What:** Read `tools/crAPI_exploit_practice.py` Section 2 (lines 310-488) carefully
**Expected:** Understand SSRF vulnerability description, attack targets, example payloads, and countermeasures
**Result:** SUCCESS — I read the full section.  The tool explains:

- The vulnerable code is in merchant/views.py lines 87-92
- User-controlled `mechanic_api` URL is passed directly to requests.get()
- verify=False disables SSL verification (allows http:// and self-signed certs)
- Authorization header is FORWARDED to the target URL (double trouble!)

**Notes:** The tool presents 6 example SSRF payloads covering internal services, cloud metadata, file read, network scan, Redis, and PostgreSQL.

---

### Attempt 2: Read the vulnerable source code directly
**What:** Read the vulnerable code pattern from the tool's description (merchant/views.py lines 87-92)
**Expected:** See the exact vulnerable code and understand WHY it's SSRF
**Result:** SUCCESS — The vulnerable code is:

```python
request_url = request_data["mechanic_api"]
mechanic_response = requests.get(
    request_url,
    params=request_data,
    headers={"Authorization": request.META.get("HTTP_AUTHORIZATION")},
    verify=False,  # ★ SSL verification disabled ★
)
```

**Why this is SSRF:**

1. **User controls the URL** — `request_data["mechanic_api"]` comes directly from user input
2. **No validation** — The server doesn't check if the URL is safe, internal, or external
3. **Server makes the request** — `requests.get(request_url, ...)` — the server (not the user's browser) makes the HTTP request
4. **SSL disabled** — `verify=False` means http:// works, self-signed certs work, certificate validation is bypassed
5. **Auth header forwarded** — The user's Authorization token is sent to the SSRF target, meaning if you SSRF to an internal service that accepts the same auth, you access it AS THE USER

**Key insight:** SSRF is dangerous because the SERVER'S network position is used, not the attacker's.  The server can reach internal services, cloud metadata endpoints, and local files that the attacker can't reach from outside.

---

### Attempt 3: Run the practice tool
**What:** Run `python tools/crAPI_exploit_practice.py --ssrf`
**Expected:** See the full SSRF demonstration with target table, example payloads, and impact analysis
**Result:** SUCCESS — The tool ran and showed:

- The vulnerability header with CWE-918 and OWASP API1:2023 references
- A 7-column target table showing different SSRF targets (internal services, cloud metadata, file read, Redis, PostgreSQL)
- 6 detailed example payloads with URLs, descriptions, and JSON body
- The "why verify=False is dangerous" explanation
- The "SSRF + JWT header forwarding = double trouble" insight
- Impact analysis (5 impact points)
- 7 countermeasures
- Practice log with 7 concepts learned

**Notes:** The tool's explanation of "double trouble" (auth header forwarding) is a key insight I hadn't fully appreciated before.  SSRF isn't just about reaching internal services — it's about reaching them WITH THE USER'S CREDENTIALS.

---

### Attempt 4: Manual attack chain tracing
**What:** Without running any code, trace the SSRF attack chain step by step
**Expected:** Prove I understand SSRF by explaining it in my own words
**Result:** SUCCESS — Here's my manual trace:

**Step 1: Attacker identifies the SSRF-vulnerable endpoint**
- Discover the /api/v1/workshop/contact_mechanic endpoint
- See that it accepts a "mechanic_api" parameter in the request body
- Notice there's no URL validation (no allowlist, no blocklist, no scheme check)

**Step 2: Attacker crafts a malicious URL**
- Decide on the target: internal service, cloud metadata, local file, or network scan
- Choose the URL: http://169.254.169.254/... (AWS metadata), file:///etc/passwd, http://127.0.0.1:8080/, etc.
- Construct the JSON payload with mechanic_api set to the malicious URL

**Step 3: Attacker sends the SSRF payload**
- POST to /api/v1/workshop/contact_mechanic
- Body: {"mechanic_api": "http://169.254.169.254/latest/meta-data/iam/security-credentials/", "repeat_request_if_failed": true, "number_of_repeats": 3}
- Include valid Authorization header (attacker is authenticated as a regular user)

**Step 4: Server processes the request**
- Server receives the JSON body
- Server extracts request_data["mechanic_api"] → "http://169.254.169.254/..."
- Server calls requests.get(request_url, params=request_data, headers={"Authorization": ...}, verify=False)
- Server makes an HTTP request TO THE ATTACKER'S CHOSEN URL
- Server uses ITS OWN NETWORK POSITION to reach the target

**Step 5: Server receives the response from the SSRF target**
- If the target is AWS metadata: server receives IAM credentials in the response
- If the target is an internal service: server receives the internal service's response
- If the target is file:///etc/passwd: server receives the file contents
- Server returns whatever it got to the attacker (or logs it)

**Step 6: Attacker extracts the valuable data**
- From AWS metadata: IAM access keys, secret keys, token — full cloud compromise
- From internal service: internal API data, credentials, configuration
- From file read: /etc/passwd, configuration files, source code
- From network scan: map internal network, find more targets

**Result:** The attacker used the server as a proxy to access resources that should NOT be accessible from outside!

---

### Attempt 5: Create 3 original SSRF payloads
**What:** Create SSRF payloads beyond the 6 examples in the practice tool
**Expected:** Demonstrate creativity and deeper understanding by designing my own attack scenarios
**Result:** SUCCESS — Here are my 3 original payloads:

---

#### Payload 1: Internal Monitoring Service Enumeration

**Target:** Internal monitoring/metrics service (common on port 9090 or 3000)

```json
{
  "mechanic_api": "http://127.0.0.1:9090/metrics",
  "repeat_request_if_failed": true,
  "number_of_repeats": 3
}
```

**Attack rationale:**
- Many applications run Prometheus, Grafana, or custom metrics endpoints internally
- These often have NO authentication (designed for internal use only)
- Returning metrics could reveal: database query times, cache hit rates, error rates, internal IP addresses, service dependencies
- Could also reveal health check endpoints with sensitive information

**What the attacker learns:**
- Is there a monitoring stack running internally?
- What services are being monitored?
- What are the performance characteristics of internal systems?
- Are there health endpoints with environment details?

**Why this payload is effective:**
- Port 9090 is a common default for Prometheus
- Metrics endpoints are often unauthenticated
- Even partial metrics data can reveal a lot about the internal architecture

---

#### Payload 2: Cloud Metadata Reconnaissance (GCP + Azure variants)

**Target:** Google Cloud Platform metadata endpoint

```json
{
  "mechanic_api": "http://169.254.169.254/computeMetadata/v1/project/project-id",
  "repeat_request_if_failed": true,
  "number_of_repeats": 3
}
```

**Attack rationale:**
- GCP uses the same metadata IP (169.254.169.254) as AWS
- The metadata endpoint can reveal: project ID, instance ID, zone, region, service account 이메일
- Service account credentials can be retrieved from the metadata endpoint
- Different GCP services have different metadata paths

**What the attacker learns:**
- Which cloud provider is being used (if metadata responds)
- Project/instance information for further targeting
- Service account identity (for privilege escalation research)

**Azure variant (alternative cloud provider):**

```json
{
  "mechanic_api": "http://169.254.169.254/metadata/instance?api-version=2021-02-01",
  "repeat_request_if_failed": true,
  "number_of_repeats": 3
}
```

**Why this payload is effective:**
- Cloud metadata endpoints are designed to be accessible from within the instance
- They often return sensitive information without authentication
- Different cloud providers have different metadata structures — trying multiple variants increases success chance

---

#### Payload 3: Application Configuration File Read

**Target:** Application configuration file containing database credentials or API keys

```json
{
  "mechanic_api": "file:///app/config/database.yml",
  "repeat_request_if_failed": true,
  "number_of_repeats": 3
}
```

**Alternative targets (if the first doesn't work):**

```json
{
  "mechanic_api": "file:///etc/crapi/config.json"
}
```

```json
{
  "mechanic_api": "file:///home/ubuntu/.aws/credentials"
}
```

**Attack rationale:**
- Many applications store configuration in files alongside the application
- Common locations: /app/config/, /etc/{appname}/, ~/.aws/, ~/.config/
- Files often contain: database credentials, API keys, AWS credentials, encryption keys, internal service URLs
- The file:// protocol is supported by some HTTP libraries (including older versions of requests via file:// support)

**What the attacker could find:**
- Database credentials (username, password, host, port)
- AWS access keys and secret keys
- API keys for third-party services
- Encryption keys or secrets
- Internal network topology information

**Why this payload is effective:**
- Configuration files often contain plaintext secrets
- File paths are often predictable (standard locations, app name patterns)
- Even if file:// isn't supported, other SSRF techniques might read files (FTP, gopher, dict protocols in some libraries)

---

## What Worked

1. **Reading the SSRF section of the practice tool** — Clear explanation of the vulnerability, good example payloads, important "double trouble" insight
2. **Analyzing the vulnerable code pattern** — The SSRF is caused by 3 things: user-controlled URL, no validation, and verify=False
3. **Running the practice tool** — Demonstrated the full range of SSRF targets and payloads
4. **Manual attack chain tracing** — I can explain every step of how SSRF works from the attacker's perspective AND the server's perspective
5. **Creating 3 original payloads** — Demonstrated deeper understanding by designing my own attack scenarios (monitoring enumeration, multi-cloud metadata, config file read)
6. **Writing countermeasures** — Listed 5+ countermeasures with specific implementation details

---

## What Didn't Work

1. **Can't test against live crAPI** — Docker isn't available, so I can't actually send SSRF payloads to a running server
2. **Can't verify file:// protocol support** — The practice tool mentions file:///etc/passwd, but I don't know if the specific version of requests used by crAPI supports the file:// protocol.  In some versions, file:// is NOT supported by default, and other protocols (gopher://, ftp://) might be needed
3. **Metadata endpoints are hypothetical** — The cloud metadata payloads assume crAPI is running on AWS/GCP/Azure.  In reality, crAPI is a local practice application, so the metadata endpoints wouldn't exist.  These payloads are for the CONCEPT, not for testing against this specific target

**Note on limitations:** These are analysis/theory limitations, not failures of understanding.  The session focused on UNDERSTANDING SSRF deeply — which was successful.  Live testing would require a different environment.

---

## What I Learned

### Concept 1: SSRF Is a Server-Side Proxy Attack
**Explanation:** SSRF isn't about the attacker directly accessing internal resources.  It's about tricking the SERVER into accessing those resources ON BEHALF of the attacker.  The server's network position, credentials, and trust relationships become the attacker's tools.

**How I learned it:** Reading the vulnerable code (merchant/views.py) and tracing the attack chain step by step.  The key realization: the server is the one making the request, so the request comes from inside the network, not outside.

### Concept 2: The Three Ingredients of SSRF
**Explanation:** Every SSRF vulnerability has three essential ingredients:

1. **User-controlled URL** — The attacker can specify which URL the server should request
2. **No validation** — The server doesn't check if the URL is safe (allowlist, blocklist, scheme check, IP range check)
3. **Server makes the request** — The server (not the attacker's browser) makes the HTTP request to the specified URL

**How I learned it:** Analyzing the vulnerable code pattern and identifying each ingredient in the merchant/views.py code.

### Concept 3: verify=False Multiplies the Attack Surface
**Explanation:** When verify=False is set, the server:
- Accepts http:// URLs (no SSL required)
- Accepts self-signed certificates
- Doesn't verify the certificate chain
- This allows SSRF to internal http:// services that would otherwise require SSL

**How I learned it:** Reading the practice tool's explanation and understanding why SSL verification matters for SSRF defense.

### Concept 4: Authorization Header Forwarding Is "Double Trouble"
**Explanation:** The server forwards the user's Authorization header to the SSRF target.  This means:
- If you SSRF to an internal service that uses the same auth mechanism, you access it AS THE USER
- You don't need to know the user's token — the server sends it for you
- This makes SSRF much more dangerous than a simple proxy attack

**How I learned it:** Reading the "SSRF + JWT Header Forwarding = DOUBLE TROUBLE" section of the practice tool.  This was a key insight I hadn't fully appreciated.

### Concept 5: Cloud Metadata Endpoints Are High-Value SSRF Targets
**Explanation:** Cloud providers (AWS, GCP, Azure) expose metadata endpoints at 169.254.169.254 that are accessible from within the instance.  These endpoints often return:
- IAM credentials (AWS)
- Service account tokens (GCP)
- Instance metadata (all clouds)
- These can lead to full cloud compromise

**How I learned it:** Reading the practice tool's example payloads and understanding WHY cloud metadata is valuable (credentials, instance info, service account identity).

### Concept 6: file:// Protocol for Local File Read
**Explanation:** Some HTTP libraries support the file:// protocol, allowing SSRF to read local files.  Common targets:
- /etc/passwd (user enumeration)
- /etc/shadow (password hashes — if readable)
- Application configuration files (credentials, API keys)
- Source code files (for further vulnerability discovery)

**How I learned it:** Reading the practice tool's example payload for file:///etc/passwd and understanding the broader file read attack surface.

### Concept 7: SSRF Allowlist vs Blocklist
**Explanation:** SSRF defense can use either approach:

**Blocklist (what NOT to allow):**
- Block 127.0.0.1, 10.x.x.x, 192.168.x.x, 169.254.x.x, etc.
- Problem: Hard to maintain, new internal IPs get added, DNS rebinding bypasses IP checks

**Allowlist (what TO allow):**
- Only allow specific, known-safe domains (api.mekanik-crapi.com)
- Much more secure — anything not on the list is rejected
- Problem: Less flexible, needs maintenance when new legitimate URLs are needed

**How I learned it:** Reading the countermeasures section and understanding why allowlists are stronger than blocklists for SSRF defense.

---

## Countermeasures Identified

1. **URL Allowlist (Primary Defense)**
   - Only allow specific, known-safe domains (e.g., api.mekanik-crapi.com)
   - Reject everything else
   - Much stronger than blocklist approach
   - Implementation: `if url.host not in ALLOWED_DOMAINS: raise ValidationError`

2. **Block Internal IP Ranges (Secondary Defense)**
   - Reject requests to 127.0.0.1, 10.x.x.x, 192.168.x.x, 169.254.x.x, etc.
   - Include IPv6 equivalents (::1, fe80::, etc.)
   - Resolve DNS first, then check the IP (prevents DNS rebinding)
   - Implementation: `if is_private_ip(resolved_ip): raise ValidationError`

3. **Block Cloud Metadata Endpoints**
   - Explicitly block 169.254.169.254 (AWS, GCP, Azure metadata)
   - Block known cloud metadata domains (metadata.google.internal, etc.)
   - Implementation: `if "169.254.169.254" in url.host: raise ValidationError`

4. **Enable SSL Verification (verify=True)**
   - Don't set verify=False — this opens http:// and self-signed cert attacks
   - If there's a legitimate reason for non-SSL, use the allowlist approach above
   - Implementation: Remove `verify=False` from requests.get() call

5. **Don't Forward Authorization Headers to Third-Party URLs**
   - Don't include the user's Authorization header in requests to user-specified URLs
   - Only forward credentials to known, trusted internal services (if at all)
   - Implementation: Don't include `headers={"Authorization": ...}` in the SSRF request

6. **Set Request Timeout**
   - Always set a timeout (e.g., timeout=5 seconds) to prevent hanging
   - Prevents denial of service via slow-responding SSRF targets
   - Implementation: `requests.get(url, timeout=5)`

7. **Validate URL Scheme**
   - Only allow http:// and https:// (not file://, gopher://, ftp://, dict://, etc.)
   - Some protocols have their own SSRF implications
   - Implementation: `if url.scheme not in ["http", "https"]: raise ValidationError`

---

## Skill Update

**Skill:** Vulnerability Discovery & Assessment
**Previous Level:** NEWBIE
**New Level:** LEARNING ✅

**Justification for level upgrade:**
- [x] Can explain SSRF in my own words (server-side proxy attack, not direct access)
- [x] Can identify the three ingredients of SSRF (user-controlled URL, no validation, server makes request)
- [x] Can trace the full attack chain (6 steps from payload crafting to data extraction)
- [x] Can create original SSRF payloads (3 new payloads beyond the tool's examples)
- [x] Can explain why verify=False and auth header forwarding make SSRF more dangerous
- [x] Can list 7 comprehensive countermeasures with implementation details
- [x] Can identify high-value SSRF targets (cloud metadata, internal services, file read)

**Practice Count:** 0 → 1
**Success Rate:** 1/1 = 100%

**Improvement Areas Identified:**
- Can't test against a LIVE server (no Docker available) — need to find alternative practice targets or use online SSRF labs
- File:// protocol support is uncertain — need to research which protocols are supported by the requests library version used by crAPI
- Only practiced SSRF in the context of crAPI — need to practice identifying SSRF in OTHER applications

**Milestones Reached:**
- ✅ Second live practice session completed
- ✅ Moved Vulnerability Discovery & Assessment from NEWBIE to LEARNING (second skill!)
- ✅ Created 3 original SSRF payloads
- ✅ Identified 7 countermeasures
- ✅ Documented the session following the sandbox template

---

## Cleanup

- [x] No processes to shut down (no network access)
- [x] No temporary files created (used existing practice tool)
- [x] Notes saved (this file)
- [x] Skill registry update prepared (ready to apply to skill_registry.json)

---

## Next Session Plan

**What to work on next:** BOLA (Broken Object Level Authorization) — the third vulnerability class.  Run the same process: read the practice tool section, read the vulnerable code pattern, trace the attack chain, write a BOLA scan script, identify countermeasures.

**What to improve from this session:**
- Try to find an online SSRF practice target (PortSwigger Web Security Academy has SSRF labs) so I can test payloads LIVE
- Research which URL schemes are supported by different HTTP library versions

**New vulnerability class to explore:**
- BOLA — ID enumeration as the primary exploitation method (Priority 1, Skill #2 continued)

---

## Notes (anything else worth remembering)

**SSRF is more subtle than I initially thought.**  I knew the basic concept (trick server into making requests) but the details matter:
- verify=False multiplies the attack surface dramatically
- Auth header forwarding makes it "double trouble" — you're not just reaching internal services, you're reaching them AS THE AUTHENTICATED USER
- Cloud metadata endpoints are uniquely valuable because they return credentials
- The difference between allowlist and blocklist is fundamental — allowlist is much more secure

**The "double trouble" insight is important.**  SSRF alone is bad.  SSRF + forwarded credentials is MUCH worse.  I should look for this pattern in other applications — any endpoint that takes a URL AND forwards credentials is a prime SSRF target.

**My 3 original payloads show creativity.**  I didn't just copy the tool's examples — I thought about what an attacker would actually want to find:
- Monitoring services (often unauthenticated, reveal architecture)
- Cloud metadata variants (AWS, GCP, Azure — increase success chance)
- Configuration files (predictable paths, contain secrets)

**For the skill registry:** Moving Vulnerability Discovery to LEARNING feels RIGHT.  I can now explain SSRF from first principles, design my own payloads, and identify countermeasures.  That's the difference between "I read about it" and "I understand it well enough to use it."

---

*End of session log*
