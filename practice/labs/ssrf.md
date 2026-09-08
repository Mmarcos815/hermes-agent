# SANDBOX LAB: SSRF (Server-Side Request Forgery)

## Objective
Understand SSRF through the crAPI merchant API vulnerability and learn to
identify, exploit, and defend against server-side request forgery.

## Prerequisites
1. Read `tools/crAPI_exploit_practice.py` Section 2 (SSRF)
2. Read `crAPI/services/workshop/crapi/merchant/views.py` — especially lines
   87-92 (the vulnerable code)
3. Read `knowledge/kali_linux_tools_master_index.md` — nmap and internal
   network tools sections
4. Complete the sandbox pre-flight checklist

## What You'll Learn
- How user-controlled URLs enable SSRF
- Why verify=False makes exploitation easier
- Cloud metadata endpoints as high-value SSRF targets
- file:// protocol for local file read
- The danger of forwarding Authorization headers to third-party URLs
- Internal network scanning via SSRF

## Practice Steps

### Step 1: Understand the vulnerable code
Read merchant/views.py lines 87-92 carefully.  Answer:
- What URL does the server request?
- Who controls that URL?
- What headers does the server forward?
- What does verify=False allow?

### Step 2: Run the practice tool
```
python tools/crAPI_exploit_practice.py --ssrf
```

### Step 3: Analyze each SSRF target
For each of the 6 example payloads in the tool, answer:
- What can the attacker reach through this URL?
- Why is this valuable to an attacker?
- How would you detect this attack in logs?

### Step 4: Write your own SSRF payloads
Create 3 new SSRF payloads beyond the ones in the tool:
- One for an internal service
- One for a cloud metadata endpoint (AWS or GCP)
- One for a file read via file:// protocol

### Step 5: Identify the countermeasures
From the tool output and your analysis, write down:
- 3 things that make SSRF dangerous in this specific case
- 5 ways to fix or mitigate this vulnerability

## Success Criteria
- [ ] Can explain SSRF in my own words
- [ ] Can identify SSRF-vulnerable code patterns
- [ ] Can write SSRF payloads for different targets
- [ ] Can list 5 countermeasures
- [ ] Session documented in sandbox/notes/

## When Done
Update the skill registry:
- Skill: Vulnerability Discovery & Assessment
- Level: NEWBIE → LEARNING
- Practice count: +1
- What I learned: list the concepts mastered
