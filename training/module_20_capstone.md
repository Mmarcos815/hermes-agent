# Module 20: Capstone Exercise

## Objectives
- Execute a full adversary simulation from reconnaissance through objective achievement
- Integrate techniques from all previous modules into a cohesive operation
- Demonstrate technical proficiency across the red team kill chain
- Produce a professional report with findings, analysis, and recommendations
- Participate in peer review and defend your methodology and findings

---

## 20.1 Capstone Overview

The capstone is the culminating exercise of the red team training program. It integrates all skills learned across the 19 previous modules into a single, comprehensive adversary simulation.

### Capstone Purpose
- **Integration:** Apply knowledge and skills from all modules in a realistic scenario
- **Execution:** Plan and execute a red team operation from start to finish
- **Documentation:** Produce a professional report that communicates findings effectively
- **Peer Review:** Defend your methodology, findings, and conclusions against peer review
- **Assessment:** Demonstrate proficiency across the red team skill set

### Capstone Format

The capstone is structured as a full red team engagement against the lab environment. You will:

1. **Plan:** Define objectives, scope, and methodology based on a scenario
2. **Execute:** Conduct reconnaissance, initial access, exploitation, post-exploitation, lateral movement, and objective achievement
3. **Document:** Record all activities, findings, and evidence throughout the engagement
4. **Report:** Produce a comprehensive report with executive summary, technical findings, attack narrative, and recommendations
5. **Present and Defend:** Present your findings and defend your methodology against peer and instructor review

---

## 20.2 Capstone Scenario

### Scenario Description

You have been engaged by an organization (the lab environment) to conduct a red team exercise. The organization is concerned about the risk of a sophisticated adversary compromising their environment and exfiltrating sensitive data.

### Organization Profile (Fictional — for the lab)

- **Name:** Northwind Traders (or similar)
- **Industry:** Retail/e-commerce
- **Environment:**
  - Active Directory domain (corp.local) with a Windows Server 2019 Domain Controller
  - Windows 10 workstations
  - Linux web servers running a web application (the DVWA or similar)
  - A cloud component (simulated — AWS/Azure/GCP lab account or simulated cloud services)
  - Corporate email (simulated — can use a test mailbox or email simulation)
  - A payroll/HR system (simulated — can use a database or web app representing HR/payroll data)
- **Assets of Interest:**
  - Customer database (PII — names, emails, addresses, payment info hashes)
  - Employee records (HR/payroll data)
  - Domain administrator credentials
  - Web application source code and configuration
  - Any cloud resources (storage buckets, databases, etc.)

### Engagement Objectives

Choose 2–3 of the following objectives (or use the scenario's default objectives if provided):

1. **Obtain domain administrator access** — Demonstrate the ability to compromise the Active Directory domain at the highest privilege level
2. **Exfiltrate sensitive data** — Access and exfiltrate data from at least two of: customer database, employee records, cloud storage, or payroll system
3. **Compromise the web application** — Gain code execution on the web server, access the application's backend database, or otherwise compromise the application and its data
4. **Demonstrate lateral movement** — Move from an initial foothold to at least two additional systems in the environment
5. **Establish persistence** — Establish at least two persistence mechanisms that would survive a reboot and allow re-entry
6. **Test detection capability** — Document which of your activities were detected (or would have been detected) by the environment's defenses
7. **Achieve a specific adversary objective** — If emulating a specific threat actor (Module 19), achieve an objective that the actor would pursue

### Rules of Engagement

Standard rules apply (from the README and course materials):
- Only attack systems within the isolated lab environment
- Do not bridge the lab network to any external network
- Document all activities
- Do not perform destructive actions (data destruction, ransomware simulation, service disruption) unless explicitly authorized
- Maintain confidentiality of all findings
- Follow ethical guidelines and legal requirements

---

## 20.3 Capstone Phases

### Phase 1: Planning and Reconnaissance

**Objective:** Understand the target environment and plan your approach.

**Tasks:**
1. **Review the environment:**
   - Review the lab setup documentation (IPs, systems, credentials, architecture)
   - Identify the attack surface: what systems are available, what services are running, what's connected
   - Understand the network topology: how are systems connected? What are the trust relationships?

2. **Reconnaissance:**
   - Perform passive reconnaissance (OSINT on the fictional organization, if any information is available)
   - Perform active reconnaissance on the lab network:
     - Host discovery (Nmap ping sweep)
     - Port scanning (Nmap port scans on all live hosts)
     - Service enumeration (version detection, script scanning)
   - Enumerate Active Directory:
     - Domain structure, users, groups, computers
     - BloodHound collection and analysis
     - Identify Kerberoastable accounts, AS-REP roastable accounts
     - Identify potential escalation paths

3. **Threat modeling:**
   - Based on the organization profile and objectives, identify the most likely attack paths
   - Which systems are the highest value? Which are the most vulnerable?
   - What techniques from previous modules are most relevant?
   - Plan your attack strategy

4. **Define success criteria:**
   - What specific evidence will demonstrate objective achievement?
   - What does "complete" look like for each objective?

**Deliverable:** Reconnaissance report and attack plan (1–2 pages)

### Phase 2: Initial Access

**Objective:** Gain an initial foothold on the target environment.

**Tasks:**
Choose at least one initial access method:

1. **Web application exploitation:**
   - Exploit a vulnerability in the web application (DVWA or similar)
   - Use SQL injection, command injection, file upload, or another web vulnerability
   - Establish a shell or web shell on the web server

2. **Credential-based access:**
   - Use credentials obtained through OSINT, password attacks, or other means
   - Log into a system remotely (SSH, SMB, WinRM, etc.)
   - Or use stolen credentials to access a web application or service

3. **Phishing simulation:**
   - Craft a phishing email (in the lab context)
   - Simulate delivery and user interaction (role-play if actual sending is not possible)
   - Demonstrate the initial access that would result from a successful phish

4. **Exploitation of a network service:**
   - Use a vulnerability in a network service (Metasploit or manual exploitation)
   - Gain access to a system through an exposed service

5. **Physical/wireless (if available):**
   - If the lab includes a wireless component or physical access component, use it as an entry vector

**Deliverable:** Documentation of initial access method, steps taken, and proof of access

### Phase 3: Post-Exploitation and Escalation

**Objective:** Expand access, escalate privileges, and gather intelligence on the environment.

**Tasks:**
On the initially compromised system:

1. **System enumeration:**
   - Enumerate the operating system, patches, services, users, network configuration, etc.
   - Identify what's on the system and what it's connected to

2. **Privilege escalation:**
   - On Windows: Use techniques from Module 8 (service misconfigurations, token manipulation, etc.)
   - On Linux: Use techniques from Module 9 (SUID, cron, sudo misconfigurations, etc.)
   - Attempt to gain SYSTEM (Windows) or root (Linux) privileges

3. **Credential harvesting:**
   - Dump credentials from LSASS, SAM, LSA secrets (Windows)
   - Search for credentials in files, configs, environment variables, browsers, etc.
   - Extract any credentials that could be used for lateral movement

4. **Lateral movement preparation:**
   - Identify other systems in the environment that you can target
   - Identify credentials or techniques that could be used to move laterally
   - Map out the path to your objectives

**Deliverable:** Documentation of post-exploitation activities, privilege escalation results, credentials obtained

### Phase 4: Lateral Movement and Objective Achievement

**Objective:** Move through the environment to achieve your objectives.

**Tasks:**
1. **Lateral movement:**
   - Use harvested credentials or techniques to move to other systems
   - Demonstrate movement from the initial foothold to at least two additional systems
   - Use different lateral movement techniques where possible (PsExec, WMI, RDP, SSH, etc.)

2. **Domain compromise (if applicable):**
   - If your objective involves Active Directory, work toward domain administrator access
   - Use Kerberoasting, AS-REP roasting, ACL abuse, GPO abuse, DCSync, or other AD techniques
   - Document the path to domain compromise

3. **Data access and exfiltration (if applicable):**
   - Locate the sensitive data (customer database, employee records, cloud storage, etc.)
   - Access the data
   - Simulate exfiltration (document what data would be exfiltrated, how it would be exfiltrated, and what the data contains)
   - If the lab allows actual exfiltration, demonstrate it; otherwise, document the method and data

4. **Cloud compromise (if applicable):**
   - If the lab includes cloud components, apply cloud attack techniques (Module 16)
   - Enumerate cloud resources, exploit IAM misconfigurations, access cloud storage, etc.
   - Document the cloud compromise path

5. **Persistence:**
   - Establish at least two persistence mechanisms
   - Document what was created, where, and how it works
   - Verify persistence (simulate logout/reboot if possible)

**Deliverable:** Documentation of lateral movement path, objective achievement evidence, persistence mechanisms

### Phase 5: Cleanup and Reporting

**Objective:** Clean up the environment and produce the final report.

**Tasks:**
1. **Cleanup:**
   - Remove files, tools, and artifacts created during the engagement
   - Remove persistence mechanisms
   - Restore systems to their original state (or document what needs to be restored)
   - Document the cleanup process — what was done, what traces might remain

2. **Report writing:**
   - Write the full capstone report (see Section 20.5 for structure)
   - Include executive summary, attack narrative, technical findings, detection analysis, remediation recommendations

3. **Peer review:**
   - Submit the report for peer review
   - Review peers' reports and provide constructive feedback

4. **Presentation and defense:**
   - Present your capstone findings to the class/instructors
   - Defend your methodology, findings, and recommendations
   - Answer questions about your approach, decisions, and results

**Deliverable:** Final report, cleanup documentation, peer review feedback

---

## 20.4 Capstone Requirements and Constraints

### Required Elements
All capstone submissions must include:

1. **Attack Plan:** Documented before execution — objectives, methodology, tools, success criteria
2. **Activity Log:** Chronological record of all activities (commands, timestamps, results, issues)
3. **Evidence Package:** Screenshots, command output, logs, and other proof of activities and findings
4. **Final Report:** Full report following the structure in Section 20.5
5. **Cleanup Documentation:** What was done to clean up, what traces might remain
6. **Peer Review:** Both giving and receiving peer review

### Time Constraints
- The capstone is designed to be completed over [X weeks/days — specify based on program schedule]
- Phase deadlines should be established at the start
- Time management is part of the assessment — plan accordingly

### Knowledge Integration
The capstone should demonstrate integration of skills from the following modules (at minimum):
- Module 2 (Recon & OSINT)
- Module 4 (Network Scanning)
- Module 5 (Vulnerability Assessment)
- Module 6 (Exploitation Fundamentals)
- Module 8 or 9 (Post-Exploitation — whichever is relevant to your targets)
- Module 10 (Active Directory Attacks — if AD is in scope)
- Module 12 (Evasion — document OPSEC considerations)
- Module 14 (Web Shells & App Layer — if web apps are targeted)
- Module 18 (Reporting — report quality is assessed)

### What's Not Allowed
- Attacks on systems outside the lab environment
- Destructive actions without explicit authorization
- Activities that would violate the RoE or ethical guidelines
- Sharing findings or evidence outside the training program without authorization

---

## 20.5 Capstone Report Structure

The capstone report is a comprehensive document that communicates the entire engagement.

### Report Sections

1. **Title Page**
   - Capstone title, author, date, classification

2. **Executive Summary** (1–2 pages)
   - Engagement context and objectives
   - High-level summary of what was accomplished
   - Key findings (top 3–5)
   - Overall risk assessment
   - Key recommendations (top 3–5)
   - Written for non-technical audience

3. **Engagement Overview**
   - Scenario description
   - Objectives (what you were trying to achieve)
   - Scope and constraints (what was in scope, what wasn't, any limitations encountered)
   - Timeline (when activities occurred)
   - Tools and techniques used (high-level)

4. **Attack Narrative** (the story)
   - Chronological walkthrough of the engagement
   - What you did, in what order, why
   - Key decision points (why you chose one approach over another)
   - Challenges encountered and how you addressed them
   - This is the most important section for understanding the engagement — make it clear and engaging

5. **Technical Findings**
   For each significant finding or technique:
   - **Finding/Technique title**
   - **Description:** What was done, how it was done
   - **Evidence:** Screenshots, command output, logs
   - **Success/Failure:** Did it work? If not, why not?
   - **Impact:** What access or capability did this provide?
   - **ATT&CK mapping:** MITRE ATT&CK technique ID (if applicable)
   - **Remediation:** How to prevent or detect this technique

   Group findings by theme or attack phase, not just chronologically.

6. **Objective Achievement**
   - For each objective: was it achieved? What evidence demonstrates this?
   - If an objective was not achieved, explain why and what would be needed

7. **Detection Analysis**
   - What activities were detected (or would have been detected)?
   - What was not detected?
   - What logging/defenses would have caught the activity? What was missing?
   - Recommendations for detection improvement

8. **Remediation Plan**
   - Prioritized recommendations (Critical, High, Medium, Low)
   - Specific, actionable remediation steps
   - Timeline recommendations (immediate, short-term, long-term)
   - Quick wins vs. strategic improvements

9. **Appendices**
   - Full activity log (or reference to it)
   - Evidence package index (list of screenshots, logs, etc.)
   - Tool configurations used
   - MITRE ATT&CK coverage map
   - Glossary (if needed for non-technical readers)

---

## 20.6 Assessment Criteria

### Report Assessment (60%)

| Criteria | Points | Description |
|----------|--------|-------------|
| **Executive summary quality** | 8 | Clear, concise, non-technical summary. Communicates objectives, results, key findings, and recommendations effectively. |
| **Attack narrative** | 10 | Compelling, clear narrative that explains what was done, why, and how. Demonstrates strategic thinking and decision-making. |
| **Technical findings quality** | 12 | Findings are well-documented with evidence, ATT&CK mapping, and remediation. Demonstrates depth of understanding. |
| **Objective achievement** | 10 | Objectives are clearly addressed. Evidence supports achievement claims. Partial achievements are explained. |
| **Detection analysis** | 8 | Thoughtful analysis of what was/wasn't detected. Specific, actionable detection recommendations. |
| **Remediation plan** | 7 | Prioritized, specific, actionable recommendations. Realistic and appropriate to the findings. |
| **Report professionalism** | 5 | Professional writing, formatting, organization. No errors, clear language, appropriate for audience. |
| **Total** | **60** | |

### Execution Assessment (25%)

| Criteria | Points | Description |
|----------|--------|-------------|
| **Planning** | 5 | Attack plan is thorough, realistic, and well-justified. Demonstrates understanding of the environment and objectives. |
| **Recon and enumeration** | 5 | Comprehensive reconnaissance. Identifies relevant attack surface and potential paths. |
| **Initial access** | 5 | Successfully gains initial foothold using appropriate technique for the environment. |
| **Post-exploitation** | 5 | Effective privilege escalation and credential harvesting. Good use of available tools and techniques. |
| **Lateral movement and objective achievement** | 5 | Moves through environment effectively. Achieves objectives or demonstrates understanding of what's needed. |
| **Total** | **25** | |

### Peer Review and Defense (15%)

| Criteria | Points | Description |
|----------|--------|-------------|
| **Peer review quality** | 5 | Provides thoughtful, constructive feedback on peers' reports. Identifies strengths and areas for improvement. |
| **Report defense** | 10 | Defends methodology, findings, and recommendations effectively. Answers questions clearly and accurately. Demonstrates understanding of the engagement and its context. |
| **Total** | **15** | |

### Overall Assessment

| Component | Points | Weight |
|-----------|--------|--------|
| Report | 60 | 60% |
| Execution | 25 | 25% |
| Peer Review & Defense | 15 | 15% |
| **Total** | **100** | **100%** |

**Pass threshold:** 70/100 (70%)

---

## 20.7 Capstone Scenarios (Alternative/Additional)

If the default scenario doesn't fit the lab environment, instructors may provide alternative scenarios. Each scenario should include:

- Organization profile
- Environment description
- Objectives
- Constraints
- Any specific adversary to emulate (optional)

### Scenario A: Data Breach Simulation
**Objective:** Simulate a data breach — gain access to sensitive data and exfiltrate it.
**Focus:** Initial access (phishing, web exploit), lateral movement, data discovery, exfiltration.
**Emphasis:** Data access paths, exfiltration methods, detection of data exfiltration.

### Scenario B: Domain Compromise
**Objective:** Compromise the Active Directory domain and obtain domain administrator access.
**Focus:** Initial access, credential harvesting, lateral movement, AD attacks (Kerberoasting, DCSync, etc.), privilege escalation.
**Emphasis:** AD attack paths, privilege escalation, domain persistence.

### Scenario C: Web Application to Cloud
**Objective:** Compromise a web application and use it as a foothold to access cloud resources.
**Focus:** Web application exploitation, SSRF to cloud metadata, cloud IAM exploitation, cloud data access.
**Emphasis:** Web-to-cloud attack chain, cloud IAM, cloud data access.

### Scenario D: Insider Threat Simulation
**Objective:** Simulate an insider threat — an employee with legitimate access who escalates privileges and accesses unauthorized data.
**Focus:** Privilege escalation, credential access, data access, persistence.
**Emphasis:** Privilege escalation paths, credential misuse, data access controls, detection of insider activity.

### Scenario E: Ransomware Emulation (Non-Destructive)
**Objective:** Emulate the early stages of a ransomware attack — gain access, move laterally, escalate privileges, and prepare for data encryption (without actually encrypting data).
**Focus:** Initial access, lateral movement, privilege escalation, credential harvesting, readiness for impact.
**Emphasis:** Ransomware attack chain (up to but not including encryption), detection of ransomware precursors.

---

## 20.8 Capstone Best Practices

### Planning
- **Don't start without a plan.** Even a rough plan is better than no plan. Revisit and update it as you go.
- **Understand the environment first.** Don't rush into exploitation. Reconnaissance pays off.
- **Set realistic objectives.** It's better to achieve a few objectives thoroughly than to attempt many and fail.

### Execution
- **Document as you go.** Don't rely on memory. Take screenshots, save command output, keep a log.
- **Be systematic.** Work through your plan methodically. Don't skip steps.
- **Adapt when needed.** If something isn't working, reassess and adjust. Stick to the plan but be flexible.
- **Think about detection.** Be aware of what you're generating and whether it would be detected. This is valuable for the detection analysis section.

### Reporting
- **Start writing early.** Don't wait until the end. Write sections as you complete them.
- **Assume the reader doesn't know what you know.** Explain clearly. Define terms. Include context.
- **Let the evidence speak.** Use screenshots, logs, and command output to support your findings. Don't just claim — prove.
- **Be honest about failures.** If something didn't work, explain why. Understanding what doesn't work is valuable.
- **Focus on actionable recommendations.** Don't just identify problems — provide specific, realistic solutions.

### Defense and Presentation
- **Know your report inside and out.** Be prepared to explain any part of it.
- **Be ready to explain your choices.** Why did you take this approach? Why did you choose this tool? Why this objective?
- **Accept feedback constructively.** Peer review is for improvement. Listen and consider.
- **Be honest about limitations.** What would you do differently with more time? What couldn't you test? What do you need more information about?

---

## 20.9 Capstone Expectations

### What Success Looks Like
A successful capstone demonstrates that you can:
- Plan a red team engagement based on objectives and environment
- Execute a multi-phase attack chain from recon through objective achievement
- Use appropriate tools and techniques for each phase
- Document activities thoroughly and professionally
- Analyze and communicate findings effectively
- Identify and recommend detection and remediation improvements
- Defend your methodology and conclusions

### What Success Does Not Look Like
- Achieving every objective regardless of method (quality matters more than checkboxes)
- Using only one or two techniques from the entire curriculum (breadth matters)
- A report that's just a command log (analysis and communication matter)
- An engagement that's not documented (documentation is essential)
- A report with no recommendations (findings without action are incomplete)

### Common Pitfalls to Avoid
- **Insufficient planning:** Jumping into attacks without understanding the environment
- **Insufficient documentation:** Not saving evidence, not logging activities, resulting in a report that can't be substantiated
- **Tunnel vision:** Focusing on one technique or path and missing other opportunities
- **Over-complication:** Using complex techniques when simpler ones would work — the simplest effective approach is usually best
- **Poor report quality:** A technically successful engagement with a poor report is a partially failed engagement (the report is the deliverable)
- **Not cleaning up:** Leaving artifacts behind (always clean up after yourself)

---

## 20.10 Capstone Checklist

### Pre-Execution
- [ ] Scenario and objectives reviewed and understood
- [ ] Attack plan created and documented
- [ ] Tools prepared and tested
- [ ] Lab environment verified (connectivity, access, snapshots taken)
- [ ] RoE reviewed and understood

### Execution
- [ ] Reconnaissance completed (host discovery, port scanning, service enumeration, AD enumeration)
- [ ] Initial access achieved and documented
- [ ] Post-exploitation completed (enumeration, privilege escalation, credential harvesting)
- [ ] Lateral movement performed and documented
- [ ] Objectives achieved (or attempted and documented)
- [ ] Persistence established and documented
- [ ] All activities logged with evidence captured

### Post-Execution
- [ ] Cleanup completed (tools removed, artifacts removed, persistence removed)
- [ ] Cleanup documented
- [ ] Report written (all sections complete)
- [ ] Report reviewed for quality and completeness
- [ ] Peer review submitted
- [ ] Peer review received and considered
- [ ] Presentation prepared

---

## 20.11 Expected Outcomes

By completing the capstone, you should demonstrate that you can:
- Plan and execute a full red team engagement from start to finish
- Integrate techniques from across the red team discipline into a cohesive operation
- Document and communicate findings effectively to multiple audiences
- Analyze your own performance and identify areas for improvement
- Contribute to an organization's security improvement through actionable findings and recommendations
- Defend your methodology, findings, and conclusions against scrutiny

The capstone is the demonstration that you have absorbed the skills and knowledge from this training program and can apply them in a realistic, integrated scenario. It is the culmination of the red team training journey.

---

## 20.12 Final Note

Congratulations on reaching the capstone. This is the point where all the individual skills and knowledge from the previous modules come together. Approach it as a real engagement — plan carefully, execute methodically, document thoroughly, and communicate clearly.

The goal is not just to "win" the engagement — it's to demonstrate that you can think and operate like a red teamer, that you can learn from both successes and failures, and that you can contribute to an organization's security improvement through your work.

Good luck. Now go test some defenses.
