# SANDBOX LAB: JWT ALGORITHM CONFUSION

## Objective
Understand JWT algorithm confusion end-to-end by forging a valid admin JWT
using the RSA public key as an HMAC secret.

## Prerequisites
1. Read `tools/crAPI_exploit_practice.py` Section 1 (JWT Algorithm Confusion)
2. Read `crAPI/services/identity/src/main/java/com/crapi/config/JwtProvider.java`
   — especially lines 170-201 (the vulnerable code)
3. Read `knowledge/hacking_exploit_api_sql_mastery.md` — JWT exploitation section
4. Complete the sandbox pre-flight checklist

## What You'll Learn
- How RS256 (asymmetric) differs from HS256 (symmetric)
- Why the server falls back to HS256 verification when it sees alg=HS256
- How the RSA public key becomes the HMAC secret (the bug)
- How to forge a JWT step by step
- What the impact of a successful forge is

## Practice Steps

### Step 1: Understand the vulnerable code
Read JwtProvider.java lines 170-201 carefully.  Answer these questions:
- What happens when the token's alg is "HS256"?
- What does getJwtSecret() return?
- Why is this catastrophic?

### Step 2: Run the practice tool
```
python tools/crAPI_exploit_practice.py --jwt
```

### Step 3: Trace the attack chain manually
Without running any code, write out each step of the attack chain:
1. What does the attacker do FIRST?
2. What do they do SECOND?
3. What do they do THIRD?
4. What does the server do when it receives the forged token?
5. What's the result?

### Step 4: Forge a JWT yourself
Using the Python utility functions in `tools/crAPI_exploit_practice.py`:
- Create a new JWT with different claims (your own email, a different role)
- Sign it with the demo public key
- Decode your token to verify the structure

### Step 5: Identify the countermeasures
From the tool output and your own analysis, write down 5 ways to fix this
vulnerability.

## Success Criteria
- [ ] Can explain the JWT algorithm confusion vulnerability in my own words
- [ ] Can trace the full attack chain step by step
- [ ] Can write a forged JWT using the public key
- [ ] Can list 5 countermeasures
- [ ] Session documented in sandbox/notes/

## When Done
Update the skill registry:
- Skill: Exploitation & Post-Exploitation
- Level: NEWBIE → LEARNING
- Practice count: +1
- Success rate: track this session
- What I learned: list the concepts mastered
