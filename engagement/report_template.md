# Penetration Test Report

**Client:** `[Client Name]`
**Engagement:** `[Project Name]`
**Date:** `[Report Date]`
**Version:** `[1.0]`
**Classification:** `[Confidential]`

---

## Executive Summary

`[2–4 paragraphs: what was tested, high-level findings, overall risk posture,
and the top 1–3 recommendations. Written for a non-technical audience.]`

### Risk Rating Summary

| Severity | Count |
|----------|------:|
| Critical | 0 |
| High | 0 |
| Medium | 0 |
| Low | 0 |
| Info | 0 |

### Overall Posture

`[One sentence: "The environment demonstrates a mature security posture with
the exception of…" or "Significant gaps were identified in…"]`

---

## Scope & Methodology

- **In-scope:** `[summary of targets]`
- **Testing window:** `[dates]`
- **Methodology:** PTES-based; passive recon → active scan → vuln analysis →
  exploitation → post-exploitation (limited) → reporting.
- **Tools used:** `[nmap, burpsuite, metasploit, custom scripts, …]`

---

## Findings

### Finding 1 — `[Short Title]`

| Field | Value |
|-------|-------|
| Severity | Critical / High / Medium / Low / Info |
| CVSS | `[vector + score]` |
| Asset(s) | `[host / app / service]` |
| Status | Open / Confirmed |

**Description**
`[What is the vulnerability? Where does it exist?]`

**Impact**
`[What can an attacker achieve? Business consequence.]`

**Reproduction**
```
1. Step one
2. Step two
3. Step three
```

**Evidence**
`[Reference to evidence log entry, screenshot, or packet capture.]`

**Remediation**
`[Specific, actionable fix. Avoid "patch" — name the patch or config change.]`

---

### Finding 2 — `[Short Title]`

`[Repeat structure above for each finding.]`

---

## Positive Observations

`[What the client is doing well. Builds trust and balances the report.]`

- `[e.g., Network segmentation between DMZ and internal tier.]`
- `[e.g., MFA enforced on all external-facing admin interfaces.]`

---

## Recommendations (Prioritized)

1. **[Critical/High]** `[Action]` — `[rationale]`
2. **[Medium]** `[Action]` — `[rationale]`
3. **[Low]** `[Action]` — `[rationale]`

---

## Retest Plan

After remediation, the following will be re-validated:

- `[Finding #]` — `[what to re-test]`
- `[Finding #]` — `[what to re-test]`

---

## Appendices

- **A.** Evidence index (see `evidence_tracker.py` output)
- **B.** Tool versions and scan profiles
- **C.** Raw scan data (delivered separately, encrypted)

---

*Report prepared by `[Tester Name / Firm]` on `[Date]`. This document contains
confidential findings and is intended solely for `[Client Name]`.*
