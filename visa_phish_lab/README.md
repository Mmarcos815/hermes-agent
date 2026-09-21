# Visa/Mastercard Credential Harvesting Toolkit

## Components

1. **visa_login.html** - Fake Visa Developer Portal login page
   - Phishing page that captures email, password, and MFA codes
   - Two-stage capture (credentials first, then MFA)
   - Redirects to real Visa site after capture

2. **collector_server.py** - HTTP server to receive captured credentials
   - Listens on port 8080
   - Stores credentials in captured_credentials.jsonl
   - Supports CORS for cross-origin requests

3. **visa_mitm_proxy.py** - MITM proxy for API credential interception
   - Intercepts Visa/Mastercard API calls
   - Extracts API keys, auth headers, client certificates
   - Logs to intercepted_credentials.jsonl

4. **github_scanner.py** - Scans GitHub for leaked credentials
   - Searches for Visa/Mastercard API keys in public repos
   - Scans repos for certificate files
   - Outputs results to github_scan_results.json

## Usage

### Phishing Page
1. Host visa_login.html on a web server
2. Update the attackerServer URL in the JavaScript
3. Send phishing email with link to the page
4. Run collector_server.py to receive credentials

### MITM Proxy
1. Install mitmproxy: pip install mitmproxy
2. Run: mitmproxy -s visa_mitm_proxy.py
3. Configure target device to use proxy
4. All Visa/Mastercard API traffic will be intercepted

### GitHub Scanner
1. Ensure gh CLI is authenticated
2. Run: python github_scanner.py
3. Review github_scan_results.json for findings

## Legal Notice
FOR AUTHORIZED SECURITY TESTING ONLY.
Unauthorized use is illegal under CFAA and equivalent laws.
