# SANDBOX LAB: MASS ASSIGNMENT EXPLOITATION

## Objective
Understand mass assignment through the crAPI shop/user endpoints and learn to
identify, exploit, and defend against improperly controlled object attribute
modification.

## Prerequisites
1. Read `tools/crAPI_exploit_practice.py` Section 4 (Mass Assignment)
2. Read `crAPI/services/shop/views.py` — especially around line 200
3. Read `knowledge/hacking_exploit_api_sql_mastery.md` — mass assignment section
4. Complete the sandbox pre-flight checklist

## What You'll Learn
- How servers accept and apply all user-supplied fields
- Which fields are commonly vulnerable (price, role, status, is_admin, total)
- How to construct mass assignment payloads for different endpoints
- Why allowlists beat blocklists
- Why derived fields (price, total, status) should be server-side only
- Real-world impact: price fraud, role escalation, ownership theft

## Practice Steps

### Step 1: Understand the vulnerable pattern
Read the mass assignment section of the practice tool.  Answer:
- What does the server do with user-supplied JSON?
- Which fields should NEVER be accepted from user input?
- Why does the serializer not filter dangerous fields?

### Step 2: Run the practice tool
```
python tools/crAPI_exploit_practice.py --mass-assign
```

### Step 3: Analyze each payload
For each of the 5 example payloads in the tool, answer:
- What field is being manipulated?
- What's the attacker's goal?
- What damage does this cause the business?

### Step 4: Write your own mass assignment payloads
Create 3 new mass assignment attacks:
- One for price manipulation (pay less than the real price)
- One for role escalation (gain admin access)
- One for data theft (steal another user's data)

### Step 5: Identify the countermeasures
From the tool output and your analysis, write down:
- 5 fields that should NEVER be user-controllable
- 5 ways to prevent mass assignment
- Why separate read/write serializers are effective

## Success Criteria
- [ ] Can explain mass assignment in my own words
- [ ] Can identify mass assignment-vulnerable code patterns
- [ ] Can write mass assignment payloads for different endpoints
- [ ] Can list 5 countermeasures
- [ ] Session documented in sandbox/notes/

## When Done
Update the skill registry:
- Skill: Web Application Security
- Level: NEWBIE → LEARNING
- Practice count: +1
- What I learned: list the concepts mastered
