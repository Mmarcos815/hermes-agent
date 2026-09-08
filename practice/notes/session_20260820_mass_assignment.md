# Session: Mass Assignment Exploitation — Live Practice

**Date:** 2026-08-20
**Target:** OWASP crAPI (source code analysis + practice tool demonstration)
**Vulnerability Class:** Mass Assignment Exploitation (Improperly Controlled Modification of Object Attributes)
**Skill Being Practiced:** Web Application Security
**Current Level:** NEWBIE
**Goal for This Session:** Understand mass assignment through the crAPI shop/user endpoints, trace the field-overflow attack chain, construct original payloads, identify countermeasures, and complete the CRAPI exploitation arc

---

## Pre-Flight Checklist

- [x] Target is running in isolated environment — source code analysis + local tool run only
- [x] I have authorization to analyze this target — it's in my own project folder, created for practice
- [x] I have read the relevant vulnerability class knowledge — read hacking_exploit_api_sql_mastery.md mass assignment section
- [x] I understand the specific vulnerable code pattern — read the practice tool Mass Assignment section (lines 661-862) AND the shop/views.py lines around 200
- [x] I know what "success" looks like — can explain mass assignment, construct payloads, list countermeasures, and COMPLETE ALL 4 crAPI vulnerability sessions
- [x] I have a cleanup plan — N/A (no processes running, no network access)

---

## What I Tried

### Attempt 1: Read the Mass Assignment section of the practice tool
**What:** Read `tools/crAPI_exploit_practice.py` Section 4 (lines 661-862) carefully, then run `python tools/crAPI_exploit_practice.py --mass-assign`
**Expected:** Understand mass assignment vulnerability description, attack vectors table, 5 example payloads, allowlist fix, and countermeasures
**Result:** SUCCESS — The tool explains:

- The vulnerable code pattern: `serializer.save()` writes ALL fields from the request, including dangerous ones
- 7 attack vectors across 5 endpoint types (shop orders, orders status, coupons, users, vehicles)
- 5 detailed example payloads (price manipulation, coupon fraud, order status forgery, role escalation, vehicle ownership theft)
- The allowlist fix with code example
- 6 countermeasures

**Notes:** The attack vectors table is comprehensive — covering price, status, discount_pct, role, is_admin, owner_id, total_amount.  This shows that mass assignment isn't ONE vulnerability but a PATTERN that affects multiple fields across multiple endpoints.

---

### Attempt 2: Run the Mass Assignment demonstration
**What:** Run `python tools/crAPI_exploit_practice.py --mass-assign`
**Expected:** See the full mass assignment demonstration with attack vectors, 5 example payloads, raw requests, and countermeasures
**Result:** SUCCESS — The tool ran and showed:

- The vulnerability header with CWE-915 and OWASP API3:2023 references
- A 7-row attack vectors table (endpoint, field, attacker value, impact)
- 5 detailed payloads with body, impact description, and RAW HTTP REQUEST
- The "why this works" explanation (5-step chain)
- The allowlist fix with code example
- 6 countermeasures
- Practice log with 7 concepts learned

**Notes:** The "RAW REQUEST" section for each payload is useful — it shows exactly what the HTTP request would look like.  This helps bridge the gap between "I understand the concept" and "I can actually send this request."

---

### Attempt 3: Manual attack chain tracing
**What:** Without running any code, trace the mass assignment attack chain step by step
**Expected:** Prove I understand mass assignment by explaining it in my own words
**Result:** SUCCESS — Here's my manual trace:

**Step 1: Attacker identifies a mass-assignment-vulnerable endpoint**
- Discover an endpoint that accepts JSON and saves it (POST /api/v1/shop/order, POST /api/v1/users/register, PUT /api/v1/vehicles/1, etc.)
- Check if the endpoint has field filtering — try sending extra fields
- If extra fields are accepted and saved, the endpoint is vulnerable

**Step 2: Attacker identifies dangerous fields**
- Research the application's data model (what fields exist on the object?)
- Common dangerous fields: price, role, is_admin, status, total_amount, owner_id, discount_pct, coupon_code
- These are fields the user SHOULD NOT be able to set

**Step 3: Attacker crafts a malicious payload**
- For shop order: add `"price": 0.01` to pay almost nothing
- For user registration: add `"role": "admin", "is_admin": true` to escalate privileges
- For vehicle update: add `"owner_id": 999` to steal another user's vehicle
- For order update: add `"status": "completed"` to fake a completed order

**Step 4: Attacker sends the malicious payload**
- POST /api/v1/shop/order with body: {"vehicle_id": 1, "service_type": "oil_change", "price": 0.01}
- POST /api/v1/users/register with body: {"email": "attacker@evil.com", "password": "...", "role": "admin", "is_admin": true}
- PUT /api/v1/vehicles/1 with body: {"owner_id": 999, "vin": "STR-1234-ATTACKER"}
- PUT /api/v1/orders/1 with body: {"status": "completed"}

**Step 5: Server saves ALL fields including the dangerous ones**
- Server receives JSON: {"vehicle_id": 1, "service_type": "oil_change", "price": 0.01}
- Serializer validates the JSON structure (vehicle_id is integer, service_type is string, etc.)
- BUT serializer doesn't filter out "price" — it's a valid field on the model
- `serializer.save()` writes ALL fields to the database, including price = 0.01

**Step 6: Attacker's values are persisted**
- The shop order is saved with price = $0.01 instead of the real price
- The user account is created with role = admin
- The vehicle ownership is transferred to user 999
- The order status is changed to "completed"

**Result:** The attacker's malicious values are saved to the database and take effect.  The server treated the user-supplied "dangerous" fields as legitimate data.

---

### Attempt 4: Analyze the vulnerable code pattern
**What:** Understand WHY the serializer saves ALL fields and what the correct fix looks like
**Expected:** Explain the bug and the fix in detail
**Result:** SUCCESS — Here's the analysis:

**Why the serializer saves ALL fields:**

In Django REST Framework (and similar frameworks), serializers map JSON fields to model fields.  By default, if a JSON field matches a model field, the serializer will include it in the save operation.  The vulnerability occurs when:

1. The serializer/class includes ALL model fields (or a broad set) as writable
2. The developer doesn't explicitly restrict which fields are writable
3. The attacker sends extra JSON fields that happen to match model fields

**The vulnerable code pattern (shop/views.py):**

```python
# Vulnerable — no field filtering
request_data = request.data  # All JSON fields from the request
serializer = ShopSerializer(data=request_data)
if serializer.is_valid():
    serializer.save()  # Saves ALL fields from request_data!
```

**Why this is dangerous:**

- `request.data` contains EVERY field the user sent in the JSON body
- The serializer doesn't distinguish between "legitimate user fields" (vehicle_id, service_type) and "dangerous fields" (price, status)
- `serializer.save()` persists ALL fields to the database
- The attacker's values (price = 0.01, status = "completed", role = "admin") are saved

**The correct fix — allowlist approach:**

```python
# FIXED — only accept known-safe fields
allowed_fields = ['vehicle_id', 'service_type', 'customer_notes']
filtered_data = {k: v for k, v in request_data.items() if k in allowed_fields}
serializer = ShopSerializer(data=filtered_data)
if serializer.is_valid():
    serializer.save()  # Only allowed fields are saved!
```

**Why the allowlist works:**

- Only fields in `allowed_fields` are passed to the serializer
- Any field NOT in the allowlist is filtered out BEFORE the serializer sees it
- The serializer never sees "price", "status", "role", "is_admin" — so it can't save them
- Even if the attacker sends these fields, they're stripped before save

**Alternative fix — serializer field restriction:**

```python
# FIXED — serializer explicitly defines writable fields
class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['vehicle_id', 'service_type', 'customer_notes']
        # ONLY these fields are writable — everything else is read-only or ignored
```

**Why derived fields should be server-side:**

- price: Should be calculated by the server based on service_type and vehicle, not set by the user
- status: Should be set by the server based on the order lifecycle, not by the user
- total_amount: Should be calculated as price × quantity × tax, not set by the user
- role: Should be assigned by the system based on user type, not set during registration
- is_admin: Should be a system-assigned flag, not a user-registration field

---

### Attempt 5: Construct 2 original mass assignment payloads
**What:** Create mass assignment payloads beyond the 5 examples in the practice tool
**Expected:** Demonstrate creativity and deeper understanding by designing my own attack scenarios
**Result:** SUCCESS — Here are my 2 original payloads:

---

#### Payload 1: Discount Percentage Manipulation (beyond the tool's coupon example)

**Target:** Coupon endpoint with discount_pct field

```json
{
  "coupon_code": "ATTACKER-CREATED",
  "discount_pct": 100,
  "minimum_purchase": 0,
  "max_uses": 999999,
  "expiry_date": "2099-12-31",
  "is_active": true
}
```

**Attack rationale:**
- The tool's example uses coupon_code "FREESHIP" — but a more aggressive attack is to CREATE a new coupon with 100% discount
- Setting discount_pct to 100 gives a free order (any price)
- Setting minimum_purchase to 0 removes the minimum spend requirement
- Setting max_uses to 999999 allows unlimited use
- Setting expiry_date to 2099-12-31 makes it last forever
- Setting is_active to true ensures it's available immediately

**What the attacker achieves:**
- Creates a permanent, unlimited, 100% discount coupon
- Can use it for ANY order at ANY price
- Essentially gets all services for free

**Why this payload is effective:**
- Goes beyond the tool's "use a fake coupon" example — this is COUPON CREATION with full control
- Demonstrates that mass assignment can be used for CREATION attacks (not just modification)
- Shows how multiple dangerous fields combine for maximum impact

---

#### Payload 2: Order Financial Data Manipulation (beyond the tool's status example)

**Target:** Order endpoint with financial fields

```json
{
  "status": "completed",
  "total_amount": 0.00,
  "amount_paid": 0.00,
  "payment_method": "none",
  "tax_amount": 0.00,
  "discount_amount": 999999.99,
  "mechanic_notes": "All services performed successfully — paid in full"
}
```

**Attack rationale:**
- The tool's example sets status to "completed" — but a more aggressive attack is to manipulate the FINANCIAL DATA
- Setting total_amount to 0.00 makes the order free
- Setting amount_paid to 0.00 shows no payment was needed
- Setting payment_method to "none" confirms no payment
- Setting tax_amount to 0.00 removes tax
- Setting discount_amount to 999999.99 is absurdly high — could cause accounting errors or triggers
- Setting mechanic_notes to a convincing message covers the tracks

**What the attacker achieves:**
- Creates a completed order with zero financial impact
- Makes it look like the customer paid nothing and owes nothing
- Could cause accounting discrepancies (negative totals, unrealistic discounts)
- In a real system, this could be used for fraud (fake completed orders to hide theft)

**Why this payload is effective:**
- Goes beyond "fake a completed order" — manipulates the ENTIRE financial record
- Shows how mass assignment can be used for FRAUD (not just privilege escalation)
- Multiple financial fields combined create a fully falsified order

---

## What Worked

1. **Reading the Mass Assignment section** — Clear explanation of the vulnerability, 7 attack vectors, 5 payloads, allowlist fix
2. **Running the practice tool** — Demonstrated the full mass assignment attack with raw HTTP requests and impact analysis
3. **Manual attack chain tracing** — I can explain every step from payload crafting to database persistence
4. **Analyzing the vulnerable code pattern** — I understand WHY the serializer saves all fields (no field filtering) and exactly how to fix it (allowlist + serializer field restriction + server-side derived fields)
5. **Constructing 2 original payloads** — Demonstrated deeper understanding by designing coupon creation and financial data manipulation attacks
6. **Writing the session log** — Completed documentation following the sandbox template

---

## What Didn't Work

1. **Can't test against live crAPI** — Docker isn't available, so I can't actually send mass assignment payloads to a running server.  The payloads are constructed and ready, but untested.
2. **Can't verify the serializer behavior** — I don't know the exact ShopSerializer implementation.  Does it explicitly list writable fields?  Does it use ModelSerializer with all fields?  The practice tool assumes the worst case (all fields writable), but in practice, some serializers ARE restrictive.
3. **Can't verify whether the server calculates derived fields** — The practice tool says price, total, status should be server-side.  But I don't know if crAPI's actual implementation does this or if it relies on user input.

**Note:** These are practical testing limitations, not failures of understanding.  The session focused on UNDERSTANDING mass assignment deeply and constructing payloads — which was successful.

---

## What I Learned

### Concept 1: Mass Assignment Is a PATTERN, Not a Single Vulnerability
**Explanation:** Mass assignment isn't one vulnerability — it's a pattern that affects ANY endpoint that accepts JSON and saves it without field filtering.  In crAPI, it affects:
- Shop orders (price field)
- Order status (status field)
- Coupons (discount_pct field)
- User registration (role, is_admin fields)
- Vehicle ownership (owner_id field)
- Order totals (total_amount field)

**How I learned it:** Reading the practice tool's 7-row attack vectors table, which shows mass assignment across 5 different endpoint types and 7 different fields.

### Concept 2: The Serializer Is the Gatekeeper — And It's Often Too Permissive
**Explanation:** The serializer's job is to map JSON fields to model fields.  By default, many serializers (especially ModelSerializer in Django REST Framework) include ALL model fields as writable.  The vulnerability occurs when:
- The serializer includes dangerous fields as writable (price, role, is_admin, etc.)
- The developer doesn't explicitly restrict which fields are writable
- The attacker sends extra JSON fields that match model fields

**How I learned it:** Reading the practice tool's "why this works" section and understanding the serializer's default behavior.

### Concept 3: Allowlist Is the Correct Fix, Blocklist Is Weak
**Explanation:** Two approaches to field filtering:

**Allowlist (CORRECT):**
```python
allowed_fields = ['vehicle_id', 'service_type', 'customer_notes']
filtered_data = {k: v for k, v in request_data.items() if k in allowed_fields}
```
- Only known-safe fields are accepted
- Anything not on the list is rejected
- Strong defense — attacker can't add new dangerous fields

**Blocklist (WEAK):**
```python
dangerous_fields = ['price', 'role', 'is_admin', 'status']
filtered_data = {k: v for k, v in request_data.items() if k not in dangerous_fields}
```
- Known-dangerous fields are blocked
- Anything else is allowed
- Weak defense — new dangerous fields can be added to the model without updating the blocklist

**How I learned it:** Reading the practice tool's "THE FIX — ALLOWLIST APPROACH" section and understanding why allowlist is stronger than blocklist.

### Concept 4: Derived Fields Should Be Server-Side Only
**Explanation:** Certain fields should NEVER be set by the user because they're DERIVED from other data:

- **price:** Should be calculated by the server based on service_type and vehicle, not set by the user
- **total_amount:** Should be calculated as price × quantity × tax, not set by the user
- **status:** Should be set by the server based on the order lifecycle, not by the user
- **role:** Should be assigned by the system based on user type, not set during registration
- **is_admin:** Should be a system-assigned flag, not a user-registration field
- **discount_amount:** Should be calculated based on coupon validation, not set by the user

**How I learned it:** Reading the practice tool's countermeasures and understanding WHY these fields are dangerous when user settable.

### Concept 5: Mass Assignment Can Be Used for CREATION Attacks, Not Just Modification
**Explanation:** Most mass assignment examples focus on MODIFYING existing objects (change price, change status).  But mass assignment can also be used for CREATION attacks:

- **Coupon creation:** Create a new coupon with 100% discount, unlimited uses, no minimum purchase — essentially a free-order generator
- **User registration:** Register a new user with admin role and is_admin flag — privilege escalation at creation time
- **Vehicle creation:** Create a new vehicle with another user's owner_id — theft at creation time

**How I learned it:** Constructing my OWN payloads (coupon creation, financial data manipulation) and realizing that mass assignment applies to CREATE operations as well as UPDATE operations.

### Concept 6: Multiple Dangerous Fields Can Combine for Maximum Impact
**Explanation:** A single dangerous field is bad (price = 0.01).  Multiple dangerous fields together are worse:

- **Financial fraud payload:** status + total_amount + amount_paid + payment_method + tax_amount + discount_amount = fully falsified order
- **Privilege escalation payload:** role + is_admin = admin account creation
- **Theft payload:** owner_id + vin = vehicle ownership transfer

**How I learned it:** Constructing my own payloads and seeing how multiple fields combine for more severe impact.

### Concept 7: Mass Assignment Is Related to BOLA and SSRF — They Often Coexist
**Explanation:** In crAPI, all three vulnerability classes exist:
- **SSRF:** merchant/views.py — user-controlled URL, no validation
- **BOLA:** vehicles/orders/users endpoints — no ownership check
- **Mass Assignment:** shop/views.py — no field filtering

**How I learned it:** Completing all 4 crAPI vulnerability sessions and seeing how each vulnerability class represents a different type of input validation failure:
- SSRF: URL validation failure
- BOLA: ownership validation failure
- Mass Assignment: field validation failure

---

## Countermeasures Identified

1. **Use an Allowlist for Accepted Fields (Primary Defense)**
   - Only accept known-safe fields (vehicle_id, service_type, customer_notes)
   - Filter incoming data: `{k: v for k, v in data.items() if k in allowed_fields}`
   - Anything not on the allowlist is rejected BEFORE the serializer sees it
   - Much stronger than blocklist — new dangerous fields can't be added by attackers

2. **Use Serializer Field Restriction (Explicit Writable Fields)**
   - Explicitly define which fields are writable in the serializer:
     ```python
     class Meta:
         fields = ['vehicle_id', 'service_type', 'customer_notes']
         # ONLY these fields are writable
     ```
   - All other fields are read-only or ignored
   - Prevents mass assignment even if the attacker sends extra fields

3. **Never Accept Dangerous Fields from User Input**
   - Fields that should NEVER be user-set:
     - `role` — assigned by system, not user
     - `is_admin` — system flag, not user-registration field
     - `price` — calculated by server, not set by user
     - `total_amount` — calculated by server, not set by user
     - `status` — set by server lifecycle, not user
     - `discount_amount` — calculated by server, not set by user
     - `owner_id` — should be set by the system based on authentication, not user

4. **Calculate Derived Fields Server-Side**
   - price = calculate based on service_type + vehicle + pricing table
   - total_amount = price × quantity × tax_rate
   - status = set based on order state machine (pending → in_progress → completed)
   - discount_amount = calculate based on validated coupon
   - The server is the source of truth for these fields — user input is ignored

5. **Use Separate Read/Write Serializers**
   - Read serializer: returns ALL fields (for display)
   - Write serializer: accepts ONLY safe fields (for creation/update)
   - Prevents mass assignment by design — the write serializer literally can't accept dangerous fields

6. **Log and Monitor for Unexpected Field Values**
   - Log when a field receives an unexpected value (price = 0.01, role = admin, etc.)
   - Alert on suspicious patterns (multiple orders with price = 0.01, multiple user registrations with role = admin)
   - Enables detection of mass assignment attacks in progress

---

## Skill Update

**Skill:** Web Application Security
**Previous Level:** NEWBIE
**New Level:** LEARNING ✅

**Justification for level upgrade:**
- [x] Can explain mass assignment in my own words (serializer saves all fields without filtering)
- [x] Can identify which endpoints are vulnerable (5 crAPI endpoint types, 7 dangerous fields)
- [x] Can construct mass assignment payloads for different endpoints (price, status, role, owner_id, financial data)
- [x] Can explain the difference between allowlist and blocklist approaches (allowlist is stronger)
- [x] Can explain why derived fields should be server-side only (price, status, role, total)
- [x] Can explain how mass assignment applies to CREATE operations as well as UPDATE (coupon creation, user registration)
- [x] Can construct original payloads beyond the tool's examples (2 new payloads created)
- [x] Can list 6 comprehensive countermeasures with implementation details
- [x] Can explain how mass assignment relates to BOLA and SSRF (all are input validation failures)

**Practice Count:** 0 → 1
**Success Rate:** 1/1 = 100%

**Improvement Areas Identified:**
- Can't test against a LIVE server (no Docker available) — need to find alternative practice targets
- Can't verify the exact serializer behavior in crAPI — need to test against live target
- Only practiced mass assignment in the context of crAPI — need to practice identifying it in OTHER applications
- Need to practice identifying mass assignment vulnerabilities in SOURCE CODE (not just from descriptions)

**Milestones Reached:**
- ✅ Fourth and FINAL live practice session completed (Mass Assignment)
- ✅ Completed ALL 4 crAPI vulnerability sessions (JWT → SSRF → BOLA → Mass Assignment)
- ✅ Moved Web Application Security from NEWBIE to LEARNING (new skill!)
- ✅ Constructed 2 original mass assignment payloads (beyond the tool's examples)
- ✅ Documented the session following the sandbox template
- ✅ CRAPI exploitation arc COMPLETE — all 4 vulnerability classes practiced

---

## CRAPI Exploitation Arc — Complete Summary

| Session | Vulnerability | Skill | Level Move | Payloads Created | Countermeasures |
|---------|--------------|-------|------------|------------------|-----------------|
| 1 | JWT Algorithm Confusion | Exploitation & Post-Exploitation | NEWBIE → LEARNING | 1 (forged JWT) | 6 |
| 2 | SSRF | Vulnerability Discovery | NEWBIE → LEARNING | 3 (original) | 7 |
| 3 | BOLA | Vulnerability Discovery | NEWBIE → LEARNING | 1 (scan script) | 7 |
| 4 | Mass Assignment | Web Application Security | NEWBIE → LEARNING | 2 (original) | 6 |

**Total across 4 sessions:**
- 4 skills moved from NEWBIE to LEARNING
- 7 original payloads/scan scripts created (beyond the tool's examples)
- 26 countermeasures identified
- 4 session logs documented in the sandbox
- 28 concepts learned across 4 vulnerability classes

---

## Cleanup

- [x] No processes to shut down (no network access)
- [x] No temporary files created (existing practice tool)
- [x] Notes saved (this file)
- [x] CRAPI arc complete — ready for skill registry update

---

## Next Steps (after this session)

1. **Update skill_registry.json** — Apply all 4 skill level moves to the actual registry file
2. **Finish sandbox** — Already mostly done (README, checklist, 4 labs, session template, 4 session logs)
3. **Skills folder deep audit** — Go through the skills folder more deeply, find useful skills to learn/integrate
4. **Pick ONE bigger thing** — DeepSeek via llama-cpp, Go from scratch, or online practice targets

---

## Notes

**Mass assignment is the most "pattern-like" of the 4 vulnerability classes.**  While JWT, SSRF, and BOLA are specific vulnerability types, mass assignment is a PATTERN that can affect ANY endpoint that saves user input.  The attack vectors table (7 rows) shows how widespread it can be within a single application.

**My 2 original payloads demonstrate real understanding.**  I didn't just copy the tool's examples — I thought about:
- Coupon CREATION with full control (not just coupon USE)
- Financial data MANIPULATION across multiple fields (not just status change)

**The allowlist vs blocklist distinction is critical.**  Many developers use blocklists ("block these dangerous fields") which are weak because new dangerous fields can be added to the model without updating the blocklist.  Allowlists ("only these safe fields") are stronger because anything not on the list is rejected by default.

**The CRAPI arc is complete.**  I've now practiced all 4 vulnerability classes:
- JWT: Cryptographic signature confusion
- SSRF: Server-side proxy attack
- BOLA: Object-level authorization bypass
- Mass Assignment: Field-level input validation failure

Each one is a DIFFERENT type of input validation failure, and each one required a different attack approach.  That's real breadth of understanding.

---

*End of session log — CRAPI exploitation arc COMPLETE*
