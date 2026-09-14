# Module 19: Threat Intelligence & Adversary Emulation

## Objectives
- Understand threat intelligence categories and sources
- Map adversary behavior to MITRE ATT&CK
- Plan and execute adversary emulation based on real threat actors
- Use threat intelligence to inform red team planning and execution
- Integrate threat intelligence into the security lifecycle

---

## 19.1 Threat Intelligence Fundamentals

Threat intelligence is evidence-based knowledge about existing or emerging threats to an organization. It's not just data — it's data that's been analyzed, contextualized, and made actionable.

### Threat Intelligence Categories

| Category | Description | Audience | Use |
|----------|-------------|----------|-----|
| **Strategic** | High-level, big-picture intelligence about threats, trends, and risks | Executives, board, senior management |Strategic planning, risk management, budgeting |
| **Operational** | Details about specific campaigns, threat actors, their goals, methods, and timing | Security managers, team leads | Planning, prioritization, understanding specific threats |
| **Tactical** | Specific TTPs (Tactics, Techniques, and Procedures) used by adversaries | Security analysts, defenders, red teamers | Detection engineering, incident response, emulation planning |
| **Technical** | IOCs (Indicators of Compromise) — IPs, domains, hashes, URLs, file signatures | SOC analysts, automated systems | Alerting, threat hunting, blocking, forensic analysis |

### Threat Intelligence Lifecycle

1. **Planning & Direction:** Define what intelligence is needed — what questions are we trying to answer? What decisions will this intelligence support?
2. **Collection:** Gather data from sources (open source, commercial, internal, government, etc.)
3. **Processing:** Organize, normalize, and aggregate collected data
4. **Analysis:** Turn data into intelligence — add context, identify patterns, assess validity, make judgments
5. **Dissemination:** Get the intelligence to the people who need it, in a format they can use
6. **Feedback:** Learn what was useful, what wasn't, and refine the process

### Threat Intelligence Sources

| Source Type | Examples | Strengths | Limitations |
|-------------|----------|-----------|-------------|
| **Open Source (OSINT)** | News, blogs, security vendor reports, social media, public repositories (GitHub, Pastebin) | Free, abundant, timely | Unverified, noisy, may be incomplete |
| **Commercial** | Threat intel vendors (Recorded Future, CrowdStrike, FireEye/Mandiant, etc.) | Vetted, structured, often enriched with context | Cost, may overlap with OSINT, depends on vendor quality |
| **Government/ISAC** | US-CERT, NCSC, sector-specific ISACs (financial, health, etc.) | Authoritative, often early warning, sector-specific | May be delayed, classified info not available, varies by country |
| **Internal** | Your own incident data, logs, investigations, red team findings | Highly relevant to your organization, proprietary | Limited to what you've seen, may miss external context |
| **Community/Sharing** | MISP instances, threat intel sharing groups, trusted communities | Real-time sharing, peer validation | Trust/model-dependent, quality varies |

---

## 19.2 MITRE ATT&CK Framework

MITRE ATT&CK (Adversarial Tactics, Techniques, and Common Knowledge) is a knowledge base of adversary behavior — it catalogs the techniques attackers use, organized by the tactics they're trying to achieve.

### ATT&CK Structure

- **Tactics:** The "why" — the adversary's tactical goal (e.g., Initial Access, Execution, Persistence, Privilege Escalation)
- **Techniques:** The "how" — specific methods adversaries use to achieve a tactical goal (e.g., Phishing for Initial Access, PowerShell for Execution, Registry Run Keys for Persistence)
- **Sub-techniques:** More specific variants of techniques (e.g., Spearphishing Attachment vs. Spearphishing Link vs. Spearphishing via Service)
- **Procedures:** Real-world examples of how specific threat actors have used a technique — the most granular level
- **Mitigations:** How to prevent or reduce the effectiveness of a technique
- **Detection:** How to detect the technique

### ATT&CK Matrix Overview (Enterprise)

| Tactics (horizontal) | Example Techniques (vertical — not exhaustive) |
|---------------------|-----------------------------------------------|
| **Reconnaissance** | Active scanning, passive reconnaissance, search closed sources |
| **Resource Development** | Acquire infrastructure, develop tools, obtain capabilities |
| **Initial Access** | Phishing, exploit public-facing application, valid accounts, drive-by compromise |
| **Execution** | PowerShell, command-line interface, scheduled task, user execution |
| **Persistence** | Registry run keys, scheduled tasks, create account, boot/trace autostart |
| **Privilege Escalation** | Exploitation for privilege escalation, access token manipulation, bypass UAC |
| **Defense Evasion** | Disable or modify tools, obfuscated files/information, indicator removal |
| **Credential Access** | OS credential dumping, brute force, credential dumping from LSASS |
| **Discovery** | System information discovery, network service scanning, account discovery |
| **Lateral Movement** | Remote services (SMB, RDP, SSH), pass the hash, pass the ticket |
| **Collection** | Data from local system, data from cloud storage, email collection |
| **Command and Control** | Application layer protocol, encrypted channel, proxy, web service |
| **Exfiltration** | Exfiltration over C2 channel, exfiltration over alternative protocol |
| **Impact** | Data encrypted for impact (ransomware), data destruction, service stop |

### Using ATT&CK in Red Teaming

1. **Planning:** Map your engagement objectives to ATT&CK techniques — what techniques will you use to achieve your goals?
2. **Coverage analysis:** Which ATT&CK techniques are you testing? Which are you not testing? Are there important techniques missing from your methodology?
3. **Threat-informed emulation:** Choose a threat actor relevant to your organization and emulate their known TTPs (using ATT&CK as the translation layer)
4. **Detection mapping:** For each technique you use, what detection exists? Map findings back to ATT&CK for consistent reporting
5. **Gap identification:** Which techniques have no detection? Which techniques are only partially covered?
6. **Reporting:** Use ATT&CK technique IDs in reports — provides a common language and makes findings comparable across engagements

### ATT&CK vs. Cyber Kill Chain

| Framework | Focus | Strengths | Limitations |
|-----------|-------|-----------|-------------|
| **Cyber Kill Chain** (Lockheed Martin) | Linear stages of an attack (Recon, Weaponization, Delivery, Exploitation, Installation, C2, Actions on Objectives) | Simple, intuitive, good for high-level understanding | Linear (real attacks aren't always linear), less detailed, doesn't capture defender actions |
| **MITRE ATT&CK** | Detailed catalog of adversary techniques, organized by tactic | Comprehensive, real-world based, continuously updated, maps to detections | More complex, can be overwhelming, requires effort to use effectively |
| **Where they fit:** Use Kill Chain for high-level narrative and ATT&CK for detailed technique-level analysis and detection mapping |

---

## 19.3 Adversary Emulation

Adversary emulation is the practice of simulating the behavior of a specific threat actor or threat group, based on intelligence about how they operate. Unlike general red teaming (which may use any effective technique), emulation is tailored to a specific adversary.

### Why Emulate Specific Adversaries?

- **Relevance:** Your organization may be targeted by specific threat actors (industry, geography, technology stack)
- **Focus:** Emulating a real adversary focuses the engagement on realistic TTPs rather than whatever works
- **Detection testing:** Tests whether defenses detect the specific behaviors of the adversary you're most concerned about
- **Training:** Helps defenders understand and recognize the adversary's behavior
- **Risk-based:** Aligns red team activities with the actual threats the organization faces

### Emulation Planning Process

1. **Identify the adversary:**
   - Who is targeting your industry/sector?
   - Who has targeted similar organizations?
   - What are their motivations (financial, espionage, hacktivism, etc.)?
   - What level of capability do they have?

2. **Research the adversary:**
   - What TTPs do they use? (Map to ATT&CK)
   - What infrastructure do they use?
   - What are their objectives? (What do they steal, disrupt, or damage?)
   - What tools do they use?
   - What are their conventions and patterns? (Filename patterns, C2 patterns, etc.)

3. **Select emulation scope:**
   - Which TTPs will you emulate? (Not all — choose the most relevant)
   - Which techniques are in scope for the engagement?
   - What level of fidelity is appropriate? (Exact procedures vs. general TTP emulation)

4. **Build the emulation plan:**
   - Map objectives to adversary TTPs
   - Plan the attack narrative based on the adversary's typical attack flow
   - Select tools and commands that reflect the adversary's behavior
   - Define what "success" looks like — did you emulate the adversary effectively?

5. **Execute and document:**
   - Execute the emulation
   - Document where you followed the adversary's TTPs and where you diverged (and why)
   - Capture detection results for each emulated technique

### Threat Actor Examples (for emulation planning)

| Actor | Motivation | Typical Targets | Notable TTPs (ATT&CK mapping) |
|-------|-----------|-----------------|-------------------------------|
| **APT28 (Fancy Bear)** | Espionage (state-sponsored, Russian) | Governments, military, political organizations, defense | Spearphishing (T1566), Word macros (T1204), PowerShell (T1059), WMI (T1047), C2 via HTTPS (T1571), credential dumping (T1003) |
| **APT29 (Cozy Bear)** | Espionage (state-sponsored, Russian) | Government, think tanks, healthcare, energy | Supply chain compromise, credential access, cloud-focused, living off the land, custom tooling |
| **FIN7 (Carbanak)** | Financial crime | Retail, hospitality, restaurants | Phishing (T1566), PowerShell (T1059), credential dumping (T1003), lateral movement via RDP/SMB (T1021), data exfiltration |
| **LockBit / ransomware groups** | Financial (extortion) | Any organization (broad targeting) | Initial access via phishing or exploited RDP (T1566, T1210), lateral movement (T1021), credential theft (T1003), data exfiltration + encryption (T1486, T1048) |
| **Kimsuky** | Espionage (state-sponsored, North Korean) | Government, research, media | Spearphishing with malicious documents, cloud storage C2, credential harvesting |
| **Lazarus Group** | Espionage + financial (state-sponsored, North Korean) | Financial, cryptocurrency, defense, government | Custom malware, financial theft, supply chain attacks, destructive attacks |

**Note:** This is a high-level overview for educational purposes. Real emulation requires detailed research into current adversary activity (threat intel reports, Mandiant/FireEye reports, CrowdStrike reports, Microsoft Threat Intelligence, etc.).

### Sources for Adversary Research

- **MITRE ATT&CK:** ATT&CK Navigator, group pages with technique mappings
- **Vendor threat reports:** Mandiant/FireEye, CrowdStrike, Microsoft, Symantec, McAfee, Kaspersky, etc.
- **Government alerts:** CISA alerts, US-CERT warnings, NCSC advisories
- **Threat intel platforms:** MISP, CrowdStrike Falcon Intelligence, Recorded Future, etc.
- **Academic/research:** Conference talks (Black Hat, DEF CON, RSA), research blogs
- **Open source intelligence:** News, dark web monitoring (if available), social media

---

## 19.4 Integrating Threat Intelligence into Red Teaming

### Before the Engagement

1. **Threat-informed objective setting:**
   - Based on threat intelligence, what objectives would a real adversary pursue against your organization?
   - What data would they target? What systems would they compromise?
   - Set engagement objectives that reflect real adversary goals

2. **Threat-informed scoping:**
   - Which adversary TTPs are most relevant? Include those in scope
   - Are there adversary behaviors you should explicitly test? (e.g., a specific malware family, a specific C2 pattern, a specific lateral movement technique)
   - Are there adversary behaviors you should avoid? (e.g., destructive techniques that would cause unacceptable damage)

3. **Tool and technique selection:**
   - Choose tools and techniques that reflect the adversary, not just whatever is convenient
   - Consider the adversary's sophistication level — are they using custom malware or living off the land?
   - Consider the adversary's operational patterns — do they use specific C2 channels, specific timing, specific infrastructure patterns?

### During the Engagement

1. ** TTP fidelity:**
   - How closely are you emulating the adversary's actual behavior?
   - Are you using the same techniques, tools, and procedures?
   - Where are you diverging and why? (Different tools because the adversary's tools are unavailable, different techniques because the environment is different, etc.)

2. **Detection feedback loop:**
   - Share adversary TTPs with the blue team before or during the engagement
   - Validate that existing detections would catch the adversary's behavior
   - Identify gaps where the adversary would go undetected

### After the Engagement

1. **Intelligence-enriched reporting:**
   - Map findings to ATT&CK
   - Compare the organization's detection and defenses to the adversary's known TTPs
   - Highlight where defenses were effective against the adversary and where they weren't

2. **Recommendations informed by intelligence:**
   - Prioritize defenses against the adversary's actual TTPs
   - Recommend detection improvements specific to the adversary's behavior
   - Recommend response procedures tailored to the adversary's objectives and methods

3. **Intelligence feedback:**
   - Did the engagement reveal anything new about the adversary? (New TTPs, new infrastructure, new objectives?)
   - Can internal findings contribute to the broader threat intelligence picture?
   - Update the organization's threat model based on engagement results

---

## 19.5 Threat Intelligence for Defense

Red teamers should understand threat intelligence not just for emulation — it also informs how they think about the adversary and what they test.

### Using Threat Intel to Improve Red Team Operations

- **Know your adversary:** What TTPs are most likely to be used against this organization?
- **Know the tools:** What malware, tools, and infrastructure are associated with the adversary? (Helps with detection testing and OPSEC)
- **Know the objectives:** What does the adversary want? (Data types, systems, access levels)
- **Know the patterns:** How does the adversary operate? (Timing, infrastructure patterns, targeting patterns)

### Threat Intelligence Limitations

- **Intelligence is not truth:** It's interpreted information. Treat it as such — verify when possible, understand the source's reliability and bias.
- **Adversaries adapt:** TTPs change over time. Intelligence can become outdated. Use the most current information available.
- **Attribution is hard:** It's often difficult to definitively attribute an attack to a specific actor. Be cautious about attribution claims.
- **Intelligence is incomplete:** You're seeing only what's been observed and reported. There's always more you don't know.
- **Your organization's context matters:** Generic threat intelligence may not apply to your specific organization. Contextualize it.

---

## 19.6 Lab: Threat Intelligence & Adversary Emulation

### Setup
- Access to threat intelligence sources (OSINT is sufficient — vendor reports, MITRE ATT&CK, CISA alerts, etc.)
- The lab environment from previous modules
- Previous module findings and attack data

### Tasks

**Task 1: Threat Intelligence Source Analysis**
1. Identify and review at least 3 threat intelligence sources:
   - MITRE ATT&CK (Group page for a specific threat actor)
   - A vendor threat report (Mandiant, CrowdStrike, Microsoft, etc.)
   - A government alert (CISA, US-CERT, NCSC, etc.)
   - Or other sources (security blogs, conference talks, etc.)
2. For each source, document:
   - What type of intelligence is it? (strategic, operational, tactical, technical)
   - Who is the audience?
   - What information is provided?
   - What's the source's credibility and potential bias?
3. Write a brief comparison of the sources — what does each do well, what are their limitations?

**Task 2: Threat Actor Research and TTP Mapping**
1. Choose a threat actor relevant to your organization or of interest ( APT28, APT29, FIN7, a ransomware group, etc.)
2. Research the actor's TTPs using available sources (MITRE ATT&CK, vendor reports, etc.)
3. Map the actor's TTPs to MITRE ATT&CK:
   - Which tactics do they use?
   - Which techniques do they use within each tactic?
   - Which procedures are documented (specific examples of how they used the technique)?
4. Create an ATT&CK Navigator layer or a table showing the mapped techniques
5. Document your research sources and the confidence level of your mappings

**Task 3: Adversary Emulation Plan**
1. Based on your threat actor research (Task 2), create an emulation plan:
   - **Adversary:** Which actor are you emulating?
   - **Rationale:** Why is this adversary relevant to the organization?
   - **Objectives:** What would this adversary try to achieve? (Based on their known objectives)
   - **TTPs to emulate:** Which specific techniques and sub-techniques will you emulate? (Choose the most relevant/reliable TTPs)
   - **Procedure design:** For each TTP, what specific actions will you take? (Commands, tools, approach)
   - **Tools:** What tools will you use? Do they match the adversary's tools or are you using alternatives?
   - **Success criteria:** How will you know the emulation was effective?
   - **Scope and constraints:** What's in scope? What are the limitations?
   - **Detection expectations:** What detections do you expect to fire for each TTP?
2. Document the full emulation plan

**Task 4: Execute Adversary Emulation (Lab)**
1. Execute the emulation plan in the lab environment:
   - Use the TTPs and procedures you planned
   - Use tools that reflect the adversary's behavior (or reasonable equivalents)
   - Follow the adversary's attack flow where possible
2. Document each step:
   - What TTP was executed
   - What command/tool was used
   - What the result was
   - What detection occurred (if any)
3. Where you deviated from the planned emulation, document why

**Task 5: Emulation Results Analysis**
1. Review the emulation results:
   - Which TTPs were successfully emulated?
   - Which were difficult to emulate and why?
   - Were there gaps in the available intelligence that made emulation harder?
2. Analyze detection results:
   - For each TTP, was it detected?
   - What detected it? (SIEM alert, EDR, log review, etc.)
   - How quickly was it detected?
   - Were there false positives or missed detections?
3. Compare the lab results to what you would expect in a real environment:
   - What would be different?
   - What would be the same?
   - What does this tell you about the value (and limitations) of lab-based emulation?

**Task 6: Threat Intelligence for Detection Engineering**
1. Choose a TTP from your emulation (or from the threat actor's TTPs) that wasn't well-detected in the lab
2. Develop a detection strategy based on threat intelligence:
   - What behavior should be detected? (Specific to the adversary's TTP)
   - What log sources are needed? (Windows Event Logs, Sysmon, PowerShell logs, network logs, cloud logs, etc.)
   - What's the detection logic? (SIEM query, EDR rule, IDS/IPS signature, etc.)
   - What are the expected false positives? How to tune?
   - How would this detection be tested? (Controlled execution of the TTP)
3. Document the detection strategy:
   - Intelligence source and rationale
   - Detection logic
   - Log source requirements
   - False positive analysis
   - Testing approach

**Task 7: Threat Intelligence Integration into Red Team Process**
1. Create a threat intelligence integration plan for a red team:
   - How should the red team consume threat intelligence? (Sources, frequency, format)
   - How should threat intelligence inform engagement planning? (Objectives, scoping, TTP selection)
   - How should threat intelligence be used during the engagement? ( TTP fidelity, detection feedback)
   - How should threat intelligence be incorporated into reporting? (ATT&CK mapping, adversary context, recommendations)
   - How should the red team contribute to threat intelligence? (Internal findings, new observations, feedback on adversary TTPs)
2. Document the integration plan with specific processes and roles

**Task 8: Threat Intelligence Reporting**
1. Write a threat intelligence brief based on your research (Task 2) and emulation (Task 4):
   - **Audience:** Security managers and defenders in the organization
   - **Subject:** The threat actor you researched
   - **Content:**
     - Who is the adversary? (Overview, motivation, capabilities)
     - Why are they relevant to the organization? (Targeting patterns, industry focus)
     - What TTPs do they use? (ATT&CK mapping, key techniques)
     - What was learned from the emulation? (What TTPs were tested, detection results)
     - What should the organization do? (Detection priorities, defense recommendations, response considerations)
   - **Format:** 2–3 pages, appropriate for operational/technical audience
2. Review the brief — is it actionable? Is it accurate? Is it appropriately scoped for the audience?

---

## 19.7 Expected Outcomes

By the end of this module, you should be able to:
- Understand threat intelligence categories, sources, and the intelligence lifecycle
- Research a threat actor and map their TTPs to MITRE ATT&CK
- Plan and execute an adversary emulation based on real threat intelligence
- Analyze emulation results in the context of the adversary's known behavior
- Develop detection strategies informed by threat intelligence
- Integrate threat intelligence into the red team planning and reporting process
- Write actionable threat intelligence briefs for defensive audiences

---

## 19.8 Assessment Criteria

| Criteria | Points | Description |
|----------|--------|-------------|
| Threat intel source analysis | 5 | Analyzes and compares threat intelligence sources |
| Threat actor research & ATT&CK mapping | 10 | Researches actor, maps TTPs to ATT&CK with appropriate rigor |
| Emulation plan | 10 | Creates a complete, well-justified emulation plan |
| Emulation execution | 10 | Executes emulation in lab, documents steps and results |
| Results analysis | 10 | Analyzes emulation and detection results, compares to real-world expectations |
| Detection strategy | 10 | Develops detection logic informed by threat intelligence |
| Threat intel integration plan | 5 | Creates a plan for integrating intel into red team process |
| Threat brief quality | 10 | Writes an actionable, accurate, appropriately scoped threat brief |
| **Total** | **70** | |

**Pass threshold:** 49/70 (70%)

### Report Requirements (5–6 pages)
1. Threat intelligence source analysis — sources reviewed, comparison, assessment
2. Threat actor research — actor overview, TTP mapping to ATT&CK, sources and confidence
3. Adversary emulation plan — full plan with objectives, TTPs, procedures, tools, success criteria
4. Emulation results — steps executed, results, deviations, detection outcomes
5. Detection strategy — for a TTP that wasn't well-detected, with logic and log requirements
6. Threat intelligence integration plan — how intel feeds into red team process
7. Threat brief — actionable intelligence brief for defensive audience
