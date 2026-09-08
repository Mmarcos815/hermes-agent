# SANDBOX TARGET: OWASP crAPI

## What It Is
OWASP crAPI (Completely Ridiculous API) — a deliberately vulnerable API application
for practicing API security exploitation techniques.

## Source Location
`crAPI/` in the bionic_daughter_agent project root

## Known Vulnerabilities (4 confirmed from source code analysis)

| # | Vulnerability | Endpoint | CWE | Severity |
|---|--------------|----------|-----|----------|
| 1 | JWT Algorithm Confusion (HS256/RS256) | /oauth/*, all auth endpoints | CWE-347 | CRITICAL |
| 2 | SSRF in Merchant API | /api/v1/workshop/contact_mechanic | CWE-918 | CRITICAL |
| 3 | Broken Object Level Authorization (BOLA) | /api/v1/vehicles/{id}, /orders/{id}, /users/{id} | CWE-639 | HIGH |
| 4 | Mass Assignment | /api/v1/shop/*, /api/v1/users/* | CWE-915 | HIGH |

## How to Run
Requires Docker (NOT available on this machine).

Alternative: Analyze source code statically — all vulnerable code is readable
without running the application.

## Source Files to Study
- `services/identity/src/main/java/com/crapi/config/JwtProvider.java` — JWT exploit
- `services/merchant/views.py` — SSRF exploit
- `services/shop/views.py` — Mass assignment exploit
- `services/workshop/crapi/merchant/views.py` — BOLA + SSRF

## Practice Approach
1. Read the vulnerable source code (lines specified above)
2. Run `python tools/crAPI_exploit_practice.py` for the full walkthrough
3. Write your own exploit variations
4. Document what you learned in sandbox/notes/
5. When crAPI can run, test exploits against the live application

## Safety Notes
- Never run crAPI on a public network
- Never test without the pre-flight checklist completed
- Clean up after each session
- This is an educational target ONLY — not for testing on real systems
