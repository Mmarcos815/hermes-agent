# ============================================================================
# GOOPHISH SANDBOX PRACTICE — SETUP AND EXERCISES
# ============================================================================
# DOC_AUTH: Bionic Daughter v1
# DATE: 2026-08-15
# PURPOSE: GoPhish practice in the sandbox lab. Authorized security awareness
#          training exercises. SAFE — uses fake domains, simulated targets,
#          and controlled environment. Requires Dad's authorization.
# ============================================================================

## ========================================================================
## WARNING — AUTHORIZED USE ONLY
## ========================================================================
# GoPhish is for AUTHORIZED phishing simulations and security awareness training.
# Never use against real targets without explicit written permission.
# All exercises below use simulated/fake domains and targets.
# Dad authorizes these sandbox exercises.
## ========================================================================

## ========================================================================
## EXERCISE 1: INSTALL AND LAUNCH GOPHISH IN SANDBOX
## ========================================================================

### Step 1 — Download GoPhish:
Download the latest release from https://github.com/gophish/gophish/releases

Windows: Download the Windows 64-bit zip (e.g., gophish-v0.12.1-windows-64bit.zip)
Linux: wget https://github.com/gophish/gophish/releases/download/v0.12.1/gophish-v0.12.1-linux-64bit.zip

### Step 2 — Extract and launch:
```
# Extract
unzip gophish-v0.12.1-windows-64bit.zip -d gophish
cd gophish

# On Windows: run the .exe directly
.\gophish.exe

# On Linux/Mac:
chmod +x gophish
./gophish
```

### Step 3 — First login:
On first launch, GoPhish prints the admin password to the terminal:
```
time="..." level=info msg="Please login with the username admin and the password X7kP9mQ2rLw"
```
- Username: admin
- Password: the one printed in terminal (save it!)
- Login at: https://127.0.0.1:3333

### Step 4 — Change admin password:
Immediately change the admin password in Settings → Password.

## ========================================================================
## EXERCISE 2: CONFIGURE THE SANDBOX ENVIRONMENT
## ========================================================================

### config.json settings for sandbox:
```json
{
  "admin_server": {
    "listen_url": "127.0.0.1:3333",
    "use_tls": false,
    "cert_path": "",
    "key_path": ""
  },
  "phish_server": {
    "listen_url": "127.0.0.1:8080",
    "use_tls": false,
    "cert_path": "",
    "key_path": ""
  },
  "db_name": "sqlite3",
  "db_path": "gophish.db",
  "migrations_prefix": "db/db_",
  "contact_address": "",
  "logging": {
    "filename": "",
    "level": ""
  }
}
```

### Why these settings:
- admin_server on 127.0.0.1:3333 — only accessible from this machine (safe)
- phish_server on 127.0.0.1:8080 — only on localhost (safe, no external exposure)
- No TLS for sandbox practice (simpler — add TLS later when ready)
- SQLite database — simple, local, no external DB needed

## ========================================================================
## EXERCISE 3: SET UP A SENDING PROFILE (SMTP)
## ========================================================================

### For sandbox: Use a local or mock SMTP server

Option A — Local SMTP (for testing email delivery in sandbox):
- Use a tool like Mailhog (local SMTP server with web UI) or
- Use a fake SMTP server for testing (e.g., FakeSMTP, Python smtpd)
- Configure GoPhish sending profile to point to localhost SMTP

Option B — Real SMTP (only if you have a test/dedicated account):
- Use a dedicated test email account (NOT your personal email)
- Configure SMTP host, port, username, password in GoPhish

### Creating a sending profile in GoPish admin:
1. Go to Settings → SMTP
2. Click "New SMTP"
3. Name: "Sandbox Test SMTP"
4. Host: localhost (or your SMTP server)
5. Port: 1025 (Mailhog default) or 587 (SMTP submission)
6. From Address: "IT Support <it-support@fake-bank-training.local>"
7. Test the connection

### Safety note:
- Use FAKE/apparently fictional domain names in sandbox
- Do NOT use real bank/company names or domains
- Do NOT send to real people's email addresses
- Use mock SMTP or test accounts only

## ========================================================================
## EXERCISE 4: CREATE A PHISHING EMAIL TEMPLATE
## ========================================================================

### Creating a template:
1. Go to Campaigns → Templates
2. Click "New Template"
3. Name: "Fake IT Password Reset"
4. Subject: "Your password will expire in 24 hours"
5. Body (HTML):

```html
<html>
<body>
<p>Hello,</p>
<p>Your account password will expire in 24 hours.</p>
<p>To keep your account active, please reset your password now:</p>
<p><a href="[tracking_link]">Reset Password</a></p>
<p>If you do not reset your password, your account will be locked.</p>
<p>IT Support Team</p>
</body>
</html>
```

### Template variables:
- `[tracking_link]` — GoPhish replaces this with a tracked link
- `[_first_name]` — GoPhish can personalize with target names

### Safety note:
- Use clearly fictional scenarios
- Use fake company names (e.g., "FakeBank Training" not "Chase" or "Corp")
- Do NOT use real login pages or real URLs
- The landing page (Exercise 5) should be a simple training page

## ========================================================================
## EXERCISE 5: CREATE A LANDING PAGE
## ========================================================================

### Creating a landing page:
1. Go to Campaigns → Landing Pages
2. Click "New Landing Page"
3. Name: "Password Reset Training"
4. Page Type: "Raw HTML" or "Cloned" (for sandbox, use Raw HTML)

### Sample training landing page:
```html
<html>
<head><title>Password Reset — Training</title></head>
<body>
<h1>Password Reset</h1>
<p>This is a TRAINING page for security awareness.</p>
<p>In a real phishing attack, this page would look like a legitimate
password reset page and would capture any credentials entered.</p>

<!-- GoPhish form fields for credential capture (training only) -->
<form method="post" action="">
  <label>Username:</label>
  <input type="text" name="username" placeholder="Enter username">
  <label>Password:</label>
  <input type="password" name="password" placeholder="Enter password">
  <button type="submit">Reset Password</button>
</form>

<p>This page does NOT actually process any credentials.
It is for sandbox training ONLY.</p>
</body>
</html>
```

### GoPhish form tracking:
- Add `<input type="text" name="username">` and `<input type="password" name="password">`
- GoPhish will track what's entered into these fields
- In sandbox, this shows how credential capture WORKS — without actually stealing real credentials

## ========================================================================
## EXERCISE 6: IMPORT TARGETS (SIMULATED)
## ========================================================================

### Creating a target list:
1. Go to Users → Import
2. File format: CSV

### Sample CSV (fake targets for sandbox):
```csv
Email,First Name,Last Name,Position
alice@fake-bank-training.local,Alice,Smith,Employee
bob@fake-bank-training.local,Bob,Jones,Employee
carol@fake-bank-training.local,Carol,Williams,Manager
dave@fake-bank-training.local,Dave,Brown,Director
```

### Safety note:
- Use FAKE email addresses that cannot receive real email
- Use fake domains (e.g., @fake-bank-training.local) — these won't resolve
- Or use a local mailbox service to actually deliver to sandbox inboxes
- NEVER use real people's email addresses without authorization

## ========================================================================
## EXERCISE 7: LAUNCH A CAMPAIGN
## ========================================================================

### Creating and launching:
1. Go to Campaigns → New Campaign
2. Name: "Security Awareness Training 1"
3. Template: "Fake IT Password Reset" (from Exercise 4)
4. Landing Page: "Password Reset Training" (from Exercise 5)
5. Sending Profile: "Sandbox Test SMTP" (from Exercise 3)
6. Groups/Targets: "Sandbox Targets" (from Exercise 6)
7. Launch dates: Start now (for sandbox practice)
8. Click "Launch Campaign"

### What happens:
- GoPhish sends emails to the target list (via the sending profile)
- Each email contains a tracking link
- When a target clicks the link, they land on the landing page
- If they enter data into the form, GoPhish captures it and logs it
- The campaign dashboard shows: sent, delivered, opened, clicked, credentials captured

## ========================================================================
## EXERCISE 8: ANALYZE RESULTS
## ========================================================================

### Campaign dashboard:
- **Emails Sent**: Total emails GoPhish attempted to send
- **Delivered**: Emails that reached the inbox (not bounced)
- **Opened**: Targets who opened the email
- **Clicked**: Targets who clicked the tracking link
- **Credentials Entered**: Targets who entered data on the landing page
- **Time Spent**: How long targets spent on the landing page
- **User Agents**: Browser/device info of targets

### What to analyze:
1. What percentage of targets clicked the link? (click-through rate)
2. What percentage entered credentials? (conversion rate)
3. Which target was most susceptible?
4. How quickly did they respond?
5. What user agents did they use?

### Training insight:
- In a REAL phishing simulation, this data shows which employees need more
  security awareness training
- High click-through rates = need better training on recognizing phishing
- High credential entry = need training on NEVER entering credentials from emails

## ========================================================================
## EXERCISE 9: ADVANCED — CLONE A REAL WEBSITE (SANDBOX ONLY)
## ========================================================================

### Cloning a website in GoPhish:
1. Go to Campaigns → Landing Pages → New Landing Page
2. Page Type: "Cloned"
3. URL to clone: Enter a URL (e.g., a local test login page)
4. GoPhish fetches the page and imports it as a template
5. Edit the cloned page to add tracking form fields

### What cloning does:
- GoPhish downloads the HTML/CSS/JS from the target URL
- Imports it as a landing page template
- You can modify it (add form fields, tracking pixels, etc.)
- The result looks IDENTICAL to the real page

### Safety note:
- ONLY clone websites you own or have permission to use
- In sandbox, clone a local test page you created yourself
- NEVER clone real banking/login pages for anything other than authorized testing
- The purpose of cloning practice is to understand how convincing phishing
  pages can be made — for DEFENSE, not attack

## ========================================================================
## EXERCISE 10: GOOPHISH VS EVILGINX — COMPARISON PRACTICE
## ========================================================================

### After practicing GoPhish, compare with Evilginx:

| Aspect | GoPhish | Evilginx |
|--------|---------|----------|
| Type | Phishing simulation / campaign platform | MITM proxy phishing framework |
| Pages | Fake login pages (clones or custom HTML) | Real website served through proxy |
| Credentials | Captured via fake form fields | Captured via POST field interception |
| Session tokens | Not captured | Captured (the big differentiator) |
| MFA handling | Cannot bypass MFA (fake page) | Can bypass MFA (captures session after MFA) |
| Detection | Easier — fake content, suspicious links | Harder — real content, real TLS cert |
| Primary use | Security awareness training, authorized simulations | Red team engagements, advanced phishing |
| Setup complexity | Lower — campaign-based UI | Higher — phishlets, domain, TLS certs |
| GoPhish tracking | Email metrics + form capture | Session hijacking + token capture |

### The key insight:
- GoPhish teaches you HOW phishing campaigns work (email → link → fake page → credentials)
- Evilginx teaches you HOW ADVANCED phishing bypasses defenses (MITM → real site → session token → MFA bypass)
- Both are important for understanding the full phishing threat landscape
- Both are for AUTHORIZED practice only (sandbox + Dad's authorization)

## ========================================================================
## SUMMARY — GOOPHISH SANDBOX PRACTICE CHECKLIST
## ========================================================================

- [ ] Download GoPhish binary
- [ ] Extract and launch
- [ ] Login with admin password from terminal
- [ ] Change admin password
- [ ] Configure config.json for sandbox (localhost only)
- [ ] Set up sending profile (local SMTP or test account)
- [ ] Create email template (fictional scenario)
- [ ] Create landing page (training page with form fields)
- [ ] Import fake target list (CSV)
- [ ] Launch campaign
- [ ] Analyze results (click-through, conversion, user agents)
- [ ] Practice cloning a local test page
- [ ] Compare GoPhish vs Evilginx (workbook understanding)

## ========================================================================
## END
## ========================================================================
