# Scope Definition

**Engagement:** `[Client / Project Name]`
**Date:** `[YYYY-MM-DD]`
**Author:** `[Your Name]`
**Version:** `1.0`

---

## 1. Objectives

What is the client trying to learn or validate?

- `[ ]` Validate perimeter defenses
- `[ ]` Assess internal network segmentation
- `[ ]` Evaluate web application security
- `[ ]` Test incident response capability
- `[ ]` Compliance requirement (PCI-DSS, SOC2, ISO 27001, …)
- `[ ]` Other: `[specify]`

## 2. In-Scope Targets

| Asset / Range | Type | Environment | Notes |
|---------------|------|-------------|-------|
| `203.0.113.0/24` | Network | Production | External perimeter |
| `app.example.com` | Web app | Production | Customer portal |
| `vpn.example.com` | Service | Production | SSL VPN gateway |
| `[IP/CIDR]` | … | … | … |

## 3. Out-of-Scope

Anything not explicitly listed above is out of scope. Specifically:

- `198.51.100.0/24` — HR database segment (no-touch)
- `partner.example.com` — third-party SaaS (no authorization)
- Denial-of-service testing of any kind

## 4. Allowed Techniques

| Technique | Allowed | Notes |
|-----------|:-------:|-------|
| Port scanning | ✓ | |
| Service enumeration | ✓ | |
| Vulnerability scanning | ✓ | |
| Exploitation (safe) | ✓ | No DoS, no destructive payloads |
| Password attacks | ✓ | Offline cracking of dumped hashes only |
| Social engineering | ☐ | Not authorized |
| Physical intrusion | ☐ | Not authorized |
| Wireless testing | ☐ | Not authorized |
| Privilege escalation | ✓ | One hop from initial foothold |
| Lateral movement | ✓ | One hop only |

## 5. Constraints

- **Testing window:** `[start date/time]` to `[end date/time]` (timezone: `[TZ]`)
- **Time-box:** `[N]` days
- **Rate limit:** Max `[N]` packets/sec against production
- **Blackout dates:** `[e.g., month-end close, holidays]`
- **Testing from:** `[our infrastructure / provided VPN / cloud VM]`

## 6. Success Criteria

A finding is considered confirmed when:

1. The vulnerability is reproduced consistently, AND
2. Business impact is demonstrated or logically argued, AND
3. Evidence (screenshot, packet capture, or log) is captured and logged.

## 7. Authorization

The undersigned authorize the testing described above.

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Client sponsor | | | |
| Technical POC | | | |
| Tester lead | | | |
