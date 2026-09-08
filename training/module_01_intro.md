# Module 1: Introduction to Red Teaming

## Objectives
- Define red teaming and distinguish it from related disciplines
- Describe the adversary simulation lifecycle
- Explain legal and ethical boundaries
- Set up your attack platform

---

## 1.1 What Is Red Teaming?

Red teaming simulates real-world adversaries to test organizational defenses.

| Aspect | Penetration Test | Red Team |
|--------|-----------------|----------|
| Scope | Defined targets | Full kill chain |
| Visibility | Blue team knows | Blue team may not know |
| Goal | Find vulnerabilities | Test detection & response |
| Duration | 1–2 weeks | Weeks to months |

### Key Principles
1. **Adversary simulation** — model real threat actors
2. **Objective-driven** — work toward specific goals
3. **Rules of Engagement** — define allowed techniques upfront
4. **Purple teaming** — share findings with defenders

---

## 1.2 The Adversary Lifecycle

```
Planning → Recon → Initial Access → Execution → Persistence → Priv Esc → Lateral Movement → Exfiltration → Reporting
```

| Phase | Description |
|-------|-------------|
| Planning | Scope, objectives, RoE |
| Recon | OSINT, scanning |
| Initial Access | Phishing, exploit, credentials |
| Execution | Run tools/payloads |
| Persistence | Survive reboots |
| Priv Esc | Gain admin/root |
| Lateral Movement | Move across systems |
| Exfiltration | Achieve objective |
| Reporting | Document findings |

---

## 1.3 Legal & Ethical Frameworks

### Legal Requirements
- **Written authorization** — signed scope-of-work document
- **Scope boundaries** — know exactly what's allowed
- **Data handling** — define storage, transmission, destruction

### Key Laws
- **CFAA** (US) — unauthorized access is a federal crime
- **Computer Misuse Act** (UK)
- **GDPR** — data protection requirements

### Ethical Guidelines
- Do no harm; minimize impact
- Maintain confidentiality
- Report all findings professionally

---

## 1.4 Lab: Attack Platform Setup

### Tasks
1. Import Kali VM, configure NAT network
2. Update system, install tools (Bloodhound, Neo4j, Impacket)
3. Set static IP to 10.10.1.10
4. Take clean-state snapshot
5. Verify: `nmap -sn 10.10.1.0/24`

---

## 1.5 Module 1 Report (1–2 pages)

1. Your definition of red teaming vs. pentesting
2. Lifecycle phases in your own words
3. Why written authorization is essential
4. Screenshot of verified lab connectivity
