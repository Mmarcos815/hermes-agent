# Module 18: Reporting & Purple Teaming

## Objectives
- Write effective red team reports that drive action
- Understand report structure, audience, and communication strategy
- Conduct purple team exercises to validate detections
- Provide actionable remediation guidance
- Measure and communicate risk effectively

---

## 18.1 The Purpose of Red Team Reporting

A red team engagement is only as valuable as the report that communicates its findings. The report is the primary deliverable — it's what transforms an intrusion simulation into actionable security improvement.

### Report Audiences

| Audience | What They Need | How to Communicate |
|----------|---------------|---------------------|
| **Executive leadership** | Business risk, high-level findings, ROI of remediation, strategic recommendations | Brief, non-technical, focused on business impact and priorities |
| **Management** | Summary of findings, resource implications, timeline, priority | Clear sections, risk ratings, what needs to happen and by when |
| **Technical teams (defenders, admins, developers)** | Detailed findings, reproduction steps, technical root cause, specific remediation | Detailed, technical, actionable — they need to fix things |
| **Compliance/audit** | Alignment with frameworks (NIST, ISO, PCI, etc.), evidence of testing | Structured, traceable to controls, clear methodology |
| **Legal/insurance** | Scope, authorization, impact, liability considerations | Factual, clear scope, documented authorization |

**Good red team reports serve all of these audiences** — typically through layered reporting (executive summary + technical details + appendices).

---

## 18.2 Report Structure

### Standard Red Team Report Sections

1. **Title Page**
   - Engagement name, client/organization, date, classification
   - Author(s), review status

2. **Executive Summary** (1–2 pages)
   - Engagement objectives (what was the red team trying to achieve?)
   - High-level results (were objectives achieved? what was the overall risk?)
   - Key findings (top 3–5 issues, summarized)
   - Overall risk rating
   - Strategic recommendations (3–5 high-level actions)
   - Written for non-technical readers — no jargon, clear business language

3. **Engagement Overview**
   - Objectives and rules of engagement (what was in scope, what was out of scope)
   - Timeline (when did the engagement happen, how long did it last)
   - Team composition (who conducted the engagement)
   - Methodology overview (high-level approach, frameworks used — e.g., MITRE ATT&CK)

4. **Attack Narrative** (the story of the engagement)
   - Chronological or thematic walkthrough of the red team's activities
   - What was attempted, what worked, what didn't
   - Key milestones (initial access, privilege escalation, lateral movement, objective achievement)
   - This makes the engagement real and understandable — it's the "story" of the attack

5. **Technical Findings**
   For each finding:
   - **Finding title:** Clear, descriptive
   - **Risk rating:** Critical / High / Medium / Low / Informational (with justification)
   - **CVSS score (if applicable):** With vector string
   - **Description:** What the finding is, why it matters
   - **Evidence:** Screenshots, logs, command output, PoC — proof that supports the finding
   - **Reproduction steps:** How to reproduce the finding (for the technical team)
   - **Impact:** What an attacker could achieve with this finding
   - **Likelihood:** How likely is this to be exploited? (skill required, opportunity, motivation)
   - **Affected assets:** Which systems, applications, or data are affected
   - **Remediation:** Specific, actionable steps to fix the issue
   - **References:** Links to CVEs, vendor advisories, OWASP, MITRE ATT&CK, etc.

6. **Detection Analysis** (for purple teaming)
   - For each major technique used: was it detected? By what? How quickly?
   - Where were the gaps? What would have caught the activity?
   - Recommendations for detection improvement

7. **Remediation Plan**
   - Prioritized list of all findings with remediation timelines
   - Short-term (immediate, 0–30 days), medium-term (30–90 days), long-term (90+ days)
   - Resource requirements (people, budget, tools) if known
   - Quick wins vs. strategic improvements

8. **Appendices**
   - Detailed tool output, logs, scripts used
   - Full MITRE ATT&CK mapping
   - Glossary of technical terms (for non-technical readers)
   - Authorization documentation (scope, RoE)
   - Remediation tracking template

---

## 18.3 Writing Effective Findings

### The "So What?" Test
Every finding should pass the "So what?" test — why does this matter? What could an attacker do? What's the business impact? If you can't answer these questions clearly, the finding may not be worth reporting (or needs more analysis).

### Risk Rating Methodology

A consistent risk rating methodology is essential for prioritization.

**Common approach (DREAD or similar):**

| Factor | Question | Score (1–5) |
|--------|----------|-------------|
| **Damage** | How bad is the worst-case impact? | 1 (minimal) to 5 (catastrophic) |
| **Reproducibility** | How easy is it to reproduce the attack? | 1 (very difficult) to 5 (trivial) |
| **Exploitability** | How easy is it to exploit? (skill, tools, access required) | 1 (expert+, special conditions) to 5 (anyone, anytime) |
| **Affected Users** | How many users or systems are affected? | 1 (one person/single system) to 5 (all users/systems) |
| **Discoverability** | How easy is it for an attacker to find this? | 1 (very hidden) to 5 (obvious/public) |

**Risk = Function of (Impact × Likelihood)**

| Overall Risk | Criteria | Response |
|--------------|----------|----------|
| **Critical** | Immediate, severe impact; easy to exploit; widespread | Remediate immediately, within hours/days |
| **High** | Significant impact; exploitable with moderate effort | Remediate within 1–4 weeks |
| **Medium** | Moderate impact or difficult to exploit | Remediate within 1–3 months |
| **Low** | Limited impact, or low likelihood, or both | Remediate in normal change cycle |
| **Informational** | No direct risk, but could aid attackers or indicate weakness | Address as part of broader improvements |

### Writing Remediation Recommendations

**Bad:** "Implement proper authentication."
**Good:** "Implement multi-factor authentication for all administrative interfaces. Use TOTP-based MFA (e.g., Google Authenticator, Authy) or hardware tokens (YubiKey). Configure the authentication provider to require MFA for all admin roles. Test that MFA cannot be bypassed via header manipulation or session fixation."

**Bad:** "Patch the server."
**Good:** "Apply security update KB5001234 to all Windows Server 2019 instances. This update addresses CVE-2021-1234, a remote code execution vulnerability in the Server service. Test in a non-production environment first. Schedule maintenance window for deployment. Verify patch application with `systeminfo` or WSUS report."

**Key principles for remediation:**
- **Specific:** What exactly should be done?
- **Actionable:** Can the reader take this action? Do they have the information they need?
- **Prioritized:** What's most important? What's a quick win?
- **Realistic:** Consider the organization's constraints — budget, time, technical debt
- **Verified:** How should they confirm the fix worked? (Re-test, scan, etc.)

---

## 18.4 Purple Teaming

Purple teaming is the collaboration between red team (attackers) and blue team (defenders) to improve security. It's not a separate engagement type — it's a methodology that can be applied within red team engagements.

### Purple Team Purpose
- **Validate detections:** Does the blue team's detection actually work against the real technique?
- **Close the loop:** Red team tests, blue team detects, both improve
- **Share knowledge:** Red team shares attacker TTPs, blue team shares detection logic
- **Improve continuously:** Each engagement makes both sides better

### Purple Team Process

1. **Plan:** Red team and blue team agree on what techniques will be tested
2. **Execute:** Red team performs the technique (in a controlled manner)
3. **Detect:** Blue team monitors for and attempts to detect the activity
4. **Analyze:** Both sides review what was detected, what wasn't, and why
5. **Improve:** Detection rules are updated, gaps are addressed, techniques are refined
6. **Repeat:** Test the improved detection with the same or different technique

### Purple Team Formats

| Format | Description | Best For |
|--------|-------------|----------|
| **Ad-hoc** | Integrated into regular red team engagements — red team shares findings with blue team during/after | Ongoing improvement, less formal |
| **Structured exercise** | Planned session where red team runs specific TTPs while blue team monitors and responds | Testing specific detections, training blue team |
| **Detection validation** | Red team runs a specific technique, blue team confirms detection or identifies gap | Validating new or updated detection rules |
| **Full purple team engagement** | Extended engagement with continuous feedback between red and blue teams | Comprehensive improvement, mature security teams |

### Purple Team Documentation

For each technique tested:
- **Technique:** What was tested (MITRE ATT&CK technique ID and name)
- **Purpose:** Why this technique was tested (validation of existing detection, testing new detection, training)
- **Red team approach:** Exactly what was done (commands, tools, timing, obfuscation)
- **Blue team detection:** What alerts fired, what was logged, what was observed
- **Detection gap analysis:** What wasn't detected and why (logging gap, rule gap, evasion, etc.)
- **Recommendations:** Detection improvement suggestions, logging recommendations, response procedure improvements

---

## 18.5 Metrics and Measuring Success

How do you know if a red team engagement was valuable? How do you measure security improvement over time?

### Engagement Metrics
- **Objective achievement rate:** Did the red team achieve its objectives? (Yes/No, partial)
- **Time to objective:** How long did it take to achieve key objectives? (e.g., time to domain compromise)
- **Detection rate:** What percentage of red team activity was detected by the blue team?
- **Time to detection:** How long between red team action and blue team detection?
- **Time to response:** How long between detection and response/mitigation?
- **Findings count by severity:** How many Critical/High/Medium/Low findings?
- **Coverage:** What attack paths were tested vs. what attack paths exist?

### Program Metrics (Over Multiple Engagements)
- **Remediation rate:** What percentage of findings are remediated within the target timeline?
- **Trend in finding count/severity:** Are things improving over time?
- **Detection coverage improvement:** Are more techniques being detected?
- **Mean time to detect (MTTD):** Is detection getting faster?
- **Mean time to respond (MTTR):** Is response getting faster?
- **Repeat findings:** Are the same issues being found again? (Indicates remediation failure or systemic problem)

### Communicating Metrics to Leadership
- Keep it simple — leaders don't need every detail
- Focus on trends and progress, not just snapshots
- Connect metrics to business risk and improvement
- Be honest about what metrics can and can't tell you

---

## 18.6 Report Quality and Review

### Self-Review Checklist
Before submitting a report:
- [ ] Executive summary stands alone — can a non-technical executive understand the key points?
- [ ] All findings have clear risk ratings with justification
- [ ] All findings have actionable remediation guidance
- [ ] Reproduction steps are clear and tested
- [ ] Evidence supports each finding (screenshots, logs, PoC)
- [ ] No sensitive information included that shouldn't be in the report (passwords, keys, personal data)
- [ ] Spelling, grammar, formatting checked
- [ ] Consistency throughout (terminology, naming, risk ratings)
- [ ] MITRE ATT&CK mapping is accurate
- [ ] Report meets any contractual or regulatory requirements

### Peer Review
Have another red teamer review the report before delivery. They'll catch issues you missed and ensure quality.

###Client Review
Give the client a chance to review the report for factual accuracy (not to dispute findings — they can't dispute facts, but they may have context you missed). This is especially important for:
- Affected asset identification (is this the right system?)
- Business impact assessment (does this align with their understanding of the business?)
- Remediation feasibility (can they actually do what you're recommending?)

---

## 18.7 Lab: Reporting & Purple Teaming

### Setup
- A completed (or simulated) red team engagement to write a report about
- The lab environment from previous modules
- Sysmon or other logging/audit tools on target systems
- A "blue team" partner (or role-play one) for purple team exercises

### Tasks

**Task 1: Review a Sample Red Team Report**
1. Find and review a public red team report or a sample report from your training materials
2. Analyze the report structure:
   - Does it have an executive summary?
   - Are findings clearly presented with risk ratings?
   - Is remediation guidance specific and actionable?
   - Is the attack narrative clear?
   - Who is the audience for each section?
3. Write a brief critique: what does the report do well, what could be improved?

**Task 2: Write an Executive Summary (Practice)**
1. Using a previous module's lab results (e.g., the domain compromise from Module 10 or the cloud compromise from Module 16), write a 1-page executive summary
2. Include:
   - What was the objective?
   - Was it achieved?
   - What were the top 3 findings?
   - What's the overall risk?
   - What are the top 3 recommended actions?
3. Write it for a non-technical executive audience — no jargon, clear business language
4. Review and refine: would a CEO/CISO understand this and know what to do?

**Task 3: Write a Full Technical Finding**
1. Choose a finding from a previous lab (e.g., Kerberoasting from Module 10, web shell from Module 14, privilege escalation from Module 8)
2. Write a complete finding section:
   - Title
   - Risk rating with justification
   - Description
   - Evidence (use your lab output — screenshots, command output, logs)
   - Reproduction steps (step-by-step, so someone could reproduce it)
   - Impact (what could an attacker achieve?)
   - Likelihood (how easy is this to exploit in a real environment?)
   - Affected assets
   - Remediation (specific, actionable, with verification steps)
   - References (CVE, MITRE ATT&CK, vendor advisory, etc.)
3. Peer review: swap with another trainee and review each other's finding

**Task 4: Purple Team Exercise — Detection Validation**
1. Choose a technique you've practiced in a previous module (e.g., Kerberoasting, pass-the-hash, web shell deployment, etc.)
2. Plan the exercise with the "blue team":
   - What technique will be tested?
   - What detection do you expect to fire?
   - What logging is needed?
3. Execute the technique in the lab while the blue team monitors:
   - What alerts fired?
   - What was logged?
   - Was the activity detected in a timely manner?
   - What wasn't detected?
4. Analyze the results together:
   - Detection gaps: what wasn't detected and why?
   - Detection quality: were the alerts actionable?
   - Response: if detected, was the response appropriate?
5. Document the exercise:
   - Technique tested
   - Detection results
   - Gaps identified
   - Recommendations for improvement

**Task 5: Purple Team Exercise — Detection Development**
1. For a technique that wasn't detected in Task 4 (or a new technique), develop a detection:
   - What logging is needed? (What should be logged that isn't currently?)
   - What would a detection rule look like? (SIEM query, EDR rule, IDS signature, etc.)
   - What are the expected false positives? How to minimize them?
   - How would the alert be triaged? What's the response procedure?
2. If possible, test the detection with a controlled execution of the technique
3. Document the detection:
   - Detection logic (rule/query)
   - Log sources required
   - Expected false positive rate
   - Response procedure

**Task 6: Report Assembly (Practice)**
1. Assemble a full red team report for a simulated engagement:
   - Executive summary
   - Engagement overview
   - Attack narrative
   - Technical findings (use findings from Task 3)
   - Detection analysis (from Tasks 4 and 5)
   - Remediation plan
   - Appendices (MITRE ATT&CK mapping)
2. Review against the checklist in Section 18.6
3. Peer review and refine

**Task 7: Metrics and Reporting Practice**
1. Define metrics for a hypothetical red team program:
   - What would you measure?
   - How would you measure it?
   - How often?
   - Who would receive the metrics?
2. Create a sample dashboard or report that presents these metrics to leadership
3. Write a brief explanation of what the metrics mean and why they matter

**Task 8: Report Delivery Simulation**
1. Role-play a report delivery meeting:
   - Present the executive summary to "leadership" (peers)
   - Present the technical findings to "technical teams" (peers)
   - Handle questions and pushback (peers challenge findings, ask for clarification, question remediation feasibility)
2. Practice communicating findings clearly, handling questions, and advocating for remediation
3. Reflect on what worked, what was difficult, and what you'd do differently

---

## 18.8 Expected Outcomes

By the end of this module, you should be able to:
- Write effective red team reports for multiple audiences
- Structure findings with clear risk ratings, evidence, and remediation
- Conduct purple team exercises to validate and improve detections
- Develop detection rules and logging recommendations
- Define and communicate meaningful security metrics
- Deliver reports and communicate findings effectively to different audiences

---

## 18.9 Assessment Criteria

| Criteria | Points | Description |
|----------|--------|-------------|
| Executive summary quality | 10 | Clear, non-technical summary that communicates risk and actions |
| Technical finding quality | 10 | Complete finding with risk rating, evidence, reproduction, remediation |
| Purple team execution | 10 | Plans and executes a detection validation exercise |
| Detection development | 10 | Develops detection logic and logging recommendations |
| Report assembly | 10 | Assembles a complete, well-structured report |
| Metrics definition | 5 | Defines meaningful metrics for a red team program |
| Communication/presentation | 5 | Presents findings effectively to different audiences |
| Report quality and completeness | 10 | Professional, complete, well-organized report |
| **Total** | **70** | |

**Pass threshold:** 49/70 (70%)

### Report Requirements
1. Executive summary (1 page) for a real or simulated engagement
2. One complete technical finding (full section as described in 18.2)
3. Purple team exercise documentation (technique, detection results, gaps, recommendations)
4. Detection rule/logic for at least one technique (with log source requirements and response procedure)
5. Full assembled report (for a simulated engagement)
6. Metrics dashboard or summary (sample metrics for a red team program)
7. Reflection on report writing and delivery — what was learned, what was difficult
