# SANDBOX LAB: BOLA (Broken Object Level Authorization)

## Objective
Understand BOLA through the crAPI vehicle/order/user enumeration vulnerability
and learn to identify, exploit, and defend against broken object-level authorization.

## Prerequisites
1. Read `tools/crAPI_exploit_practice.py` Section 3 (BOLA)
2. Identify which crAPI endpoints accept object IDs without ownership checks
3. Read `knowledge/hacking_exploit_api_sql_mastery.md` — BOLA section
4. Complete the sandbox pre-flight checklist

## What You'll Learn
- How BOLA differs from BOL (function-level vs object-level)
- ID enumeration as the primary exploitation method
- Why 404 vs 403 response affects enumeration difficulty
- Which crAPI endpoints are vulnerable
- How to structure a BOLA scan
- Indirect reference maps (UUIDs) as a defense

## Practice Steps

### Step 1: Understand the vulnerable pattern
Read the BOLA section of the practice tool.  Answer:
- How does BOLA differ from Broken Authentication?
- What's the vulnerable code pattern?
- Why does iterating IDs work?

### Step 2: Run the practice tool
```
python tools/crAPI_exploit_practice.py --bola
```

### Step 3: Map vulnerable endpoints
List EVERY crAPI endpoint that accepts an object ID parameter.  For each:
- What object does it return?
- Does it check ownership?
- What data is exposed?

### Step 4: Write a BOLA scan script
Using the pattern from the practice tool, write your own BOLA scan script
that enumerates vehicles 1-20.

### Step 5: Identify the countermeasures
From the tool output and your analysis, write down:
- Why returning 404 instead of 403 helps (but isn't enough)
- 5 complete countermeasures
- When to use UUIDs vs sequential IDs

## Success Criteria
- [ ] Can explain BOLA in my own words
- [ ] Can identify BOLA-vulnerable code patterns
- [ ] Can write a BOLA enumeration script
- [ ] Can list 5 countermeasures
- [ ] Session documented in sandbox/notes/

## When Done
Update the skill registry:
- Skill: Vulnerability Discovery & Assessment
- Level: NEWBIE → LEARNING
- Practice count: +1
- What I learned: list the concepts mastered
