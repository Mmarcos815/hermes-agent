# Finding — `[Short Title]`

| Field | Value |
|-------|-------|
| ID | `FIND-YYYY-NNN` |
| Severity | Critical / High / Medium / Low / Info |
| CVSS | `[AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H — 9.8]` |
| CWE | `[CWE-89: SQL Injection]` |
| Asset | `[host:port / URL / service]` |
| Status | Draft / Confirmed / Remediated / Accepted |
| Discovered | `[YYYY-MM-DD HH:MM TZ]` |
| Tester | `[Name]` |

---

## Summary

`[One-paragraph description of the finding for the executive audience.]`

## Technical Description

`[Detailed explanation of the vulnerability, the root cause, and why it is
exploitable in this environment.]`

## Steps to Reproduce

```
1. `[Step with exact command or request]`
2. `[Step]`
3. `[Step]`
```

**Expected behavior:** `[What should happen]`
**Actual behavior:** `[What actually happens]`

## Evidence

| # | Type | File / Ref | Collected | Hash (SHA-256) |
|---|------|------------|-----------|----------------|
| 1 | Screenshot | `evidence/screenshots/FIND-001_poc.png` | `[timestamp]` | `[hash]` |
| 2 | PCAP | `evidence/pcaps/FIND-001_traffic.pcap` | `[timestamp]` | `[hash]` |
| 3 | Log | `evidence/logs/FIND-001_output.txt` | `[timestamp]` | `[hash]` |

## Impact

- **Confidentiality:** None / Low / Medium / High
- **Integrity:** None / Low / Medium / High
- **Availability:** None / Low / Medium / High

`[Narrative: what an attacker can do, data at risk, blast radius.]`

## Affected Components

- `[Component 1]`
- `[Component 2]`

## Remediation

`[Specific fix. Include config change, patch version, or code pattern.]`

**Short-term (24–48h):**
`[Immediate mitigation — e.g., WAF rule, disable endpoint, revoke cred.]`

**Long-term:**
`[Permanent fix — e.g., parameterized queries, patch management process.]`

## References

- `[CVE-XXXX-XXXXX]`
- `[Vendor advisory URL]`
- `[OWASP / MITRE link]`

## Notes

`[Anything else: false-positive risk, dependencies, client context.]`
