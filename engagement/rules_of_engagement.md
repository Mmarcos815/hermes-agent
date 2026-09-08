# Rules of Engagement (ROE)

**Engagement:** `[Project Name]`
**Effective:** `[Start]` → `[End]`
**Version:** `1.0`

---

## 1. Purpose

These rules protect both parties. They define what the tester may do,
what they must not do, and how incidents are handled. Nothing in this
document grants permission beyond what is explicitly stated.

## 2. Authorization

This engagement is authorized by `[Client Name]` for the targets and
techniques listed in the Scope document. Any activity outside that scope
is **unauthorized** and may be treated as a hostile act.

## 3. Permitted Actions

- Scan and enumerate in-scope targets during the testing window.
- Attempt safe, non-destructive exploitation of discovered vulnerabilities.
- Escalate privileges and move laterally within the limits in the Scope.
- Capture evidence (screenshots, packet captures, logs) of findings.
- Communicate findings to the designated client POC.

## 4. Prohibited Actions

- Denial-of-service (DoS / DDoS) of any kind.
- Modifying, deleting, or exfiltrating production data without explicit
  written approval.
- Installing persistent backdoors or leaving artifacts behind.
- Testing out-of-scope systems, third-party services, or cloud control
  planes not explicitly authorized.
- Disclosing findings to anyone outside the engagement team.
- Using findings for personal gain or competitive advantage.

## 5. Comms & Escalation

| Role | Name | Phone | Email | Availability |
|------|------|-------|-------|--------------|
| Client sponsor | | | | Business hours |
| Client technical POC | | | | 24/7 during test |
| Tester lead | | | | 24/7 during test |
| Emergency contact | | | | 24/7 |

**Primary channel:** `[Signal / Slack / Email / Ticket #]`
**Response SLA:** Critical findings — within 1 hour. Routine — next business day.

## 6. Stop Conditions

The tester **must immediately cease** and contact the client POC if:

- A critical production system becomes unavailable.
- Sensitive data (PII, PHI, credentials) is unexpectedly exposed.
- An incident response team is triggered by the testing activity.
- Law enforcement or a third party contacts the tester.

## 7. Evidence & Data Handling

- All evidence is classified `[Confidential / Restricted / Internal]`.
- Store evidence encrypted at rest (AES-256). Transfers over TLS 1.2+.
- Retain evidence for `[N]` days after report delivery, then securely destroy.
- Do not store client data on personal devices or unapproved cloud services.

## 8. Legal

- This engagement does not create an employment or agency relationship.
- Each party remains responsible for its own compliance obligations.
- Testing must comply with applicable laws (CFAA, GDPR, local statutes).
- Disputes governed by the laws of `[Jurisdiction]`.

## 9. Signatures

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Client sponsor | | | |
| Tester lead | | | |
