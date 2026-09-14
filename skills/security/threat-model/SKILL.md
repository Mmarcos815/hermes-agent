---
name: threat-model
description: "Threat modeling engine — auto-generates STRIDE-based threat models with data flow diagrams, attack trees, and mitigation catalogs for any system architecture."
version: 1.0.0
author: Rigoberto Gomez, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [security, threat-modeling, stride, attack-trees, dfd, risk-assessment]
    related_skills: [cloud-red-team-playbook]
---

# Threat Modeling Engine

A pure-Python (stdlib only) threat modeling engine that auto-generates comprehensive threat models using STRIDE (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege). Builds Data Flow Diagrams (DFDs) from programmatic element definitions, enumerates threats per element using Microsoft's STRIDE-per-element mapping, generates attack trees for each threat, and maps mitigations from a built-in catalog. Outputs human-readable text reports or structured JSON for further processing.

## When to Use

- Performing threat modeling during system design or security review
- Generating attack trees for risk assessment documentation
- Training on STRIDE methodology and threat enumeration
- Automated security analysis in CI/CD pipelines
- Pre-engagement reconnaissance for penetration testing

Don't use for:
- Replacing manual threat modeling for high-assurance systems (use as a starting point)
- Compliance audits requiring formal TMT (Threat Modeling Tool) output
- Real-time threat detection (this is a design-time analysis tool)

## Prerequisites

- Python 3.8+ (uses `dataclasses`, `enum`, `json`, `textwrap`, `datetime` — all stdlib)
- No external dependencies
- The script `scripts/threat_model_engine.py` in this skill directory

## How to Run

```bash
cp ~/.hermes/skills/security/threat-model/scripts/threat_model_engine.py ./
python threat_model_engine.py
```

This runs the built-in demo that models an e-commerce web application with 3 external entities, 5 processes, 4 data stores, and 9 data flows. Outputs a full text report with DFD elements, STRIDE threats, attack trees, and summary statistics.

## Quick Reference

| Action | Code |
|--------|------|
| Create engine | `engine = ThreatModelEngine("System Name")` |
| Add external entity | `engine.add_external_entity("User", role="end-user")` |
| Add process | `engine.add_process("Auth Service", trust_level="high")` |
| Add data store | `engine.add_data_store("User DB", encrypted=True)` |
| Add data flow | `engine.add_flow("label", source="A", dest="B", data_type="creds", encrypted=True, protocol="HTTPS")` |
| Generate report | `report = engine.generate()` |
| Text output | `report.to_text()` |
| JSON output | `report.to_json()` |

## Procedure

### 1. Define the System

```python
from threat_model_engine import ThreatModelEngine

engine = ThreatModelEngine("My Web Application")
```

### 2. Add External Entities

```python
engine.add_external_entity("Customer", role="end-user")
engine.add_external_entity("Admin", role="privileged")
engine.add_external_entity("Payment Gateway", role="third-party")
```

### 3. Add Processes

```python
engine.add_process("Web Frontend", trust_level="low")
engine.add_process("API Gateway", trust_level="high")
engine.add_process("Auth Service", trust_level="high")
engine.add_process("Order Service", trust_level="medium")
```

### 4. Add Data Stores

```python
engine.add_data_store("Product Catalog DB", encrypted=True)
engine.add_data_store("Order DB", encrypted=True)
engine.add_data_store("User DB", encrypted=True)
engine.add_data_store("Session Cache", encrypted=False)
```

### 5. Add Data Flows

```python
engine.add_flow(
    "Customer -> Web Frontend",
    source="Customer",
    destination="Web Frontend",
    data_type="HTTP requests",
    encrypted=True,
    protocol="HTTPS"
)
engine.add_flow(
    "API Gateway -> Auth Service",
    source="API Gateway",
    destination="Auth Service",
    data_type="auth tokens",
    encrypted=True,
    protocol="mTLS"
)
```

### 6. Generate the Report

```python
report = engine.generate()
print(report.to_text())   # Human-readable report
print(report.to_json())   # Structured JSON
```

### 7. Report Structure

The generated report includes:

1. **DFD Elements** — All external entities, processes, data stores, and flows
2. **Threats (STRIDE)** — Per-element threat enumeration with:
   - Unique ID (T-001, T-002, ...)
   - STRIDE category
   - Target element
   - Severity (Low/Medium/High/Critical)
   - Likelihood (Low/Medium/High)
   - Description
   - Mitigations
3. **Attack Trees** — Goal-oriented decomposition for each threat
4. **Summary** — Total elements, threats, severity breakdown

### 8. STRIDE-per-Element Mapping

| Element Type | S | T | R | I | D | E |
|-------------|---|---|---|---|---|---|
| External Entity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Process | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Data Store | | ✓ | ✓ | ✓ | ✓ | |
| Data Flow | | ✓ | ✓ | ✓ | ✓ | |

### 9. Context-Aware Severity

The engine adjusts severity based on element metadata:

| Context | Adjustment |
|---------|------------|
| Data store with `encrypted=True` | Info Disclosure / Tampering severity downgraded |
| Data store with `encrypted=False` | Info Disclosure / Tampering severity upgraded |
| Data flow with `encrypted=True` | Info Disclosure / Tampering severity downgraded |
| Data flow with `encrypted=False` | Info Disclosure / Tampering severity upgraded |
| Process with `trust_level="high"` | Low/Medium severity upgraded |

### 10. Attack Tree Structure

Each threat generates an attack tree with:

- **Root node** — The threat itself (OR gate)
- **Intermediate nodes** — Attack categories (AND/OR gates)
- **Leaf nodes** — Specific attack techniques

Example for Spoofing:
```
[OR] Attack: Spoof identity
  [OR] Forge credentials
    [LEAF] Steal credentials via phishing
    [LEAF] Brute-force weak credentials
    [LEAF] Exploit authentication bypass
  [AND] Spoof network identity
    [LEAF] ARP spoof / DNS hijack
    [LEAF] Forge TLS certificate
```

## Pitfalls

- **Template-based threats.** Threats are generated from templates, not custom analysis. May miss system-specific threats.
- **No custom rule support.** Cannot add domain-specific threat templates without modifying the script.
- **Severity is heuristic.** Context adjustments are simple upgrades/downgrades. Not a replacement for CVSS or DREAD scoring.
- **No asset valuation.** Does not consider business impact or asset criticality.
- **No trust boundary visualization.** DFD elements are listed but not rendered as diagrams.
- **Attack trees are generic.** Same structure for all threats in a STRIDE category. No system-specific attack paths.
- **No mitigation tracking.** Mitigations are listed but not tracked for implementation status.
- **JSON output is large.** For complex systems, JSON export can be very verbose.

## Verification

- Report contains all registered elements in the DFD section
- Each element has threats matching its STRIDE-per-element mapping
- Threat IDs are sequential (T-001, T-002, ...)
- Attack trees are generated for every threat
- Summary counts match actual threat/element counts
- `to_text()` produces a formatted report with all sections
- `to_json()` produces valid JSON with all fields
- Demo output shows 15+ threats for the sample e-commerce architecture
