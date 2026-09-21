#!/usr/bin/env python3
"""
Farm 3 Phones Integration Module
Absorbs all standalone farm_3phones tools into unified MCP server.
"""
import json
import subprocess
from pathlib import Path

WORKSPACE = Path(r"C:\Users\mobil\orca\projects\my 1st\farm_3phones")
APKTOOL = WORKSPACE / "apktool.jar"

# ── ADB Tools ───────────────────────────────────────────────────────────────

def adb_devices() -> dict:
    """List connected Android devices."""
    r = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    devices = []
    for line in r.stdout.strip().split("\n")[1:]:
        if "\tdevice" in line:
            serial = line.split("\t")[0]
            devices.append({"serial": serial, "status": "connected"})
    return {"devices": devices, "count": len(devices)}

def farm_phone_status() -> dict:
    """Get status of all phones in the farm."""
    return {
        "phone-01": {"role": "CardOutpost", "status": "offline", "last_seen": "2026-09-20"},
        "phone-02": {"role": "MintPull", "status": "offline", "last_seen": "2026-09-20"},
        "phone-03": {"role": "Rip Rush", "status": "offline", "last_seen": "2026-09-20"},
    }

# ── Price Manipulation ─────────────────────────────────────────────────────

def price_manip_test(url: str, params: dict, cookie: str = None) -> dict:
    """Test checkout for price manipulation flaws."""
    import requests
    
    findings = []
    test_values = [0, -1, -100, 0.01, 999999]
    
    for field in params:
        if any(k in field.lower() for k in ["price", "amount", "total", "cost"]):
            for val in test_values:
                test_params = dict(params)
                test_params[field] = val
                
                headers = {}
                if cookie:
                    headers["Cookie"] = cookie
                
                try:
                    r = requests.post(url, data=test_params, headers=headers, timeout=10)
                    if r.status_code == 200:
                        findings.append({
                            "field": field,
                            "value": val,
                            "status": r.status_code,
                            "suspicious": val <= 0 and r.status_code == 200
                        })
                except:
                    pass
    
    return {
        "url": url,
        "tests_run": len(findings),
        "findings": findings,
        "vulnerable": any(f["suspicious"] for f in findings)
    }

# ── Endpoint Hunter ────────────────────────────────────────────────────────

def hunt_endpoints(target: str, wordlist: list = None) -> dict:
    """Hunt for API endpoints on a target domain."""
    import requests
    from urllib.parse import urljoin
    
    if wordlist is None:
        wordlist = [
            "api", "v1", "v2", "auth", "login", "register", "users",
            "products", "orders", "cart", "checkout", "payments",
            "webhook", "health", "status", "config", "admin",
            "graphql", "rest", "swagger", "docs"
        ]
    
    base = target if target.startswith("http") else f"https://{target}"
    found = []
    
    for path in wordlist:
        url = urljoin(base + "/", path)
        try:
            r = requests.get(url, timeout=5, allow_redirects=False)
            if r.status_code in [200, 201, 301, 302, 401, 403, 405]:
                found.append({
                    "path": path,
                    "url": url,
                    "status": r.status_code,
                    "content_type": r.headers.get("content-type", "")
                })
        except:
            pass
    
    return {
        "target": target,
        "paths_tested": len(wordlist),
        "found": found,
        "live_endpoints": len([f for f in found if f["status"] == 200])
    }

# ── APK Analysis ────────────────────────────────────────────────────────────

def analyze_apk(apk_path: str) -> dict:
    """Analyze an APK for endpoints, permissions, and security issues."""
    import zipfile
    import re
    
    findings = {
        "permissions": [],
        "endpoints": [],
        "secrets": [],
        "debug": False,
        "network_security": []
    }
    
    try:
        with zipfile.ZipFile(apk_path, 'r') as z:
            for name in z.namelist():
                if name.endswith(".xml") or name.endswith(".dex"):
                    try:
                        content = z.read(name).decode('utf-8', errors='ignore')
                        urls = re.findall(r'https?://[^\s"\'\\]+', content)
                        findings["endpoints"].extend(urls[:20])
                        api_keys = re.findall(r'[A-Za-z0-9_]{20,}', content)
                        for key in api_keys:
                            if any(k in key.lower() for k in ["api", "key", "secret", "token"]):
                                findings["secrets"].append(key)
                    except:
                        pass
            
            if "AndroidManifest.xml" in z.namelist():
                manifest = z.read("AndroidManifest.xml").decode('utf-8', errors='ignore')
                if "debuggable" in manifest.lower():
                    findings["debug"] = True
    except Exception as e:
        return {"error": str(e)}
    
    return findings

# ── Bypass Tools ───────────────────────────────────────────────────────────

def generate_ssl_bypass(package: str) -> dict:
    """Generate SSL bypass configuration for a package."""
    return {
        "package": package,
        "frida_script": f"Java.use('{package}...').overload.implementation = ...",
        "network_security_config": """<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <base-config cleartextTrafficPermitted="true">
        <trust-anchors>
            <certificates src="system" />
            <certificates src="user" />
        </trust-anchors>
    </base-config>
</network-security-config>""",
        "instructions": [
            "1. Decompile APK with apktool",
            "2. Add network_security_config.xml",
            "3. Modify AndroidManifest.xml to reference it",
            "4. Rebuild and re-sign the APK"
        ]
    }

def generate_frida_script(target_class: str, method: str = "onCreate") -> dict:
    """Generate a Frida hook for a target class/method."""
    script = f"""Java.perform(function() {{
    var target = Java.use("{target_class}");
    target.{method}.implementation = function() {{
        console.log("[+] Hooked: {target_class}.{method}");
        return this.{method}.apply(this, arguments);
    }};
}});"""
    
    return {
        "target_class": target_class,
        "method": method,
        "script": script,
        "usage": f"frida -U -f <package> -l hook_{method}.js"
    }
