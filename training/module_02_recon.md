# Module 2: Reconnaissance & OSINT

## Objectives
- Distinguish passive vs. active reconnaissance
- Use OSINT tools to build a target profile
- Enumerate DNS and subdomains
- Document findings in an intelligence report

---

## 2.1 Reconnaissance Fundamentals

| Type | Description | Risk |
|------|-------------|------|
| **Passive** | Publicly available data only | None |
| **Active** | Direct interaction with target | Low–High |

**Always start with passive recon.** Use active only when RoE permits.

### Intelligence Cycle
Requirements → Collection → Processing → Analysis → Dissemination

---

## 2.2 OSINT Sources

### Public Data
- Company websites, job postings, LinkedIn
- Public records, SEC filings
- Paste sites (Pastebin, Ghostbin)
- GitHub/GitLab for exposed credentials

### Technical Data
- DNS records (A, MX, NS, TXT)
- WHOIS, Certificate Transparency (crt.sh)
- Shodan, Censys for exposed services

---

## 2.3 OSINT Tools

```bash
# theHarvester — collect emails and subdomains
theHarvester -d example.com -b google,linkedin,bing

# Shodan — internet-connected devices
shodan search "hostname:example.com"

# crt.sh — subdomain discovery via certificates
curl -s "https://crt.sh/?q=%.example.com&output=json" | jq -r '.[].name_value' | sort -u

# amass — comprehensive enumeration
amass enum -d example.com
```

---

## 2.4 DNS Enumeration

```bash
# Record lookups
dig A example.com
dig MX example.com
dig NS example.com
dig TXT example.com

# Zone transfer (if allowed)
dig AXFR example.com @ns1.example.com

# Subdomain brute-force
dnsrecon -d example.com -t brt -D wordlist.txt
```

---

## 2.5 Target Profile Template

```
Target: Example Corp
Domain: example.com
IP Range: 203.0.113.0/24

Subdomains:
  - www.example.com (203.0.113.10)
  - mail.example.com (203.0.113.25)
  - vpn.example.com (203.0.113.50)

Email Format: firstname.lastname@example.com
Technologies: nginx 1.18, Exchange, Pulse Secure
Exposed Services: SSH (100), RDP (200)
```

---

## 2.6 Lab: OSINT Gathering

### Tasks
1. Run `theHarvester` on the target domain
2. Query DNS records (A, MX, NS, TXT)
3. Search Shodan/Censys for exposed services
4. Use crt.sh for subdomain discovery
5. Build a target profile document

---

## 2.7 Module 2 Report (2–3 pages)

1. Methodology and tools used
2. Target profile with findings
3. Attack implications of findings
4. Defensive recommendations to reduce exposure
