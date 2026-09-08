# Real Penetration Test

**Date:** 2026-09-08
**Version:** 1.0
**Total Findings:** 3

## Executive Summary

| Severity | Count |
|----------|-------|
| Critical | 1 |
| High | 1 |
| Medium | 1 |

## Findings

### FIND-001: SQL Injection in Authentication

- **Severity:** Critical
- **CVSS Score:** 9.8 (CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H)
- **Affected:** https://app.example.com/login

**Description:**

Parameterized query missing in login endpoint

**Evidence:**

sqlmap identified injection point in username parameter

**Remediation:**

Use parameterized queries, implement WAF rules

### FIND-002: Stored XSS in User Profile

- **Severity:** High
- **CVSS Score:** 7.5 (N/A)
- **Affected:** https://app.example.com/profile

**Description:**

User input rendered without encoding

**Evidence:**

Payload <script>alert(1)</script> executed on profile view

**Remediation:**

Output encoding, CSP headers

### FIND-003: Outdated Apache Server

- **Severity:** Medium
- **CVSS Score:** 5.3 (N/A)
- **Affected:** web server

**Description:**

Apache 2.4.49 with known CVEs

**Evidence:**

Server header reveals Apache/2.4.49

**Remediation:**

Upgrade to latest Apache version

## Appendices

### CVSS Scoring Methodology

CVSS v3.1 was used to score findings. Scores range from 0.0 to 10.0:
- Critical: 9.0-10.0
- High: 7.0-8.9
- Medium: 4.0-6.9
- Low: 0.1-3.9
- Informational: 0.0