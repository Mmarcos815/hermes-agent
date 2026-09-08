# AUTONOMOUS RED TEAM AGENTS — STATE OF THE ART REPORT
**Author:** Bionic Daughter & Dad  
**Date:** August 2026  
**Focus:** Real vs. Marketing, Core Architectures, and Integration Strategy

---

## 1. Landscape Overview & The "Real vs. Marketing" Breakdown

Autonomous red-team and pentesting agents have evolved from simple prompt wrappers into multi-tiered orchestration engines.

| Tier / Archetype | Leading Frameworks | How It Works in Reality | Real Capability vs. Marketing |
|---|---|---|---|
| **Autonomous Web & App Pentesting** | **PentestGPT**, **Strix** (`usestrix/strix`), **CAI** | Multi-phase planning loop: Recon -> Enum -> Vulnerability Hypothesis -> Payload Generation -> Verification. | **Real.** Effective at chaining OWASP Top 10 (SQLi, BOLA, IDOR, SSRF, Auth Bypass) in target environments. |
| **Network & Infrastructure Red Team** | **AutoPentest** (`BadBoy0170/autopentest`), **HexStrike AI**, **Auto-Redteam** | Integrates tool execution (Nmap, Metasploit, Responder, NetExec) via JSON-RPC / MCP with local + LLM triage. | **Real when backed by tools.** Pure LLM execution fails without deterministic scanners. |
| **Agent Swarm & Multi-Agent Harnesses** | **Ruflo** (`ruvnet/ruflo`), **Orca Swarms**, **Hermes Kanban/Subagents** | Orchestrator/Worker hierarchy where specialist subagents execute recon, exploit generation, and report generation in parallel worktrees. | **High leverage.** Eliminates single-context saturation. |
| **LLM & AI-Target Red Teaming** | **NVIDIA Garak**, **PyRIT** (Microsoft), **Godmode / Parseltongue** | Automated adversarial jailbreak probing, system prompt extraction, indirect prompt injection testing. | **Real.** Standard for testing LLM guardrails and agent harnesses. |

---

## 2. Core Architecture of a True Autonomous Red Team Agent

A genuine red-team agent (like our `bionic_daughter_agent`) must not be a chatbot. It requires 4 tightly coupled layers:

```
┌──────────────────────────────────────────────────────────┐
│ 1. STRATEGIC REASONER (LLM / Hermes Core / Orca)         │
│    - Attack Tree Generation, Scope Enforcer, Triage      │
└──────────────────────────┬───────────────────────────────┘
                           │ Task Delegation / Planning
┌──────────────────────────▼───────────────────────────────┐
│ 2. DETERMINISTIC TOOL HARNESS (MCP / CLI / Go / Python)  │
│    - Scanners (BOLA, SSRF, JWT, Fuzzers, Port Probers)   │
│    - FastMCP Proxy & Raw Socket Engines                  │
└──────────────────────────┬───────────────────────────────┘
                           │ Execution Feedback (JSON)
┌──────────────────────────▼───────────────────────────────┐
│ 3. ISOLATED RUNTIME / SANDBOX (Docker / Worktrees)       │
│    - Controlled Targets, Safe Verification, Network Sim  │
└──────────────────────────┬───────────────────────────────┘
                           │ Output Artifacts
┌──────────────────────────▼───────────────────────────────┐
│ 4. PERSISTENCE & KNOWLEDGE BASE                          │
│    - Structured Findings, CVE Mappings, Reproducible PoCs│
└──────────────────────────────────────────────────────────┘
```

---

## 3. Integration Plan for Our Stack
1. **Tool Access:** HexStrike MCP (81 tools) + custom Go/Python exploiters.
2. **Orchestration:** Hermes Agent running inside Orca ADE worktrees.
3. **Guardrails & Testing:** Sandboxed target environments (crAPI, local labs).
