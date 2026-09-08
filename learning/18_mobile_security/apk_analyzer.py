#!/usr/bin/env python3
"""APK Security Analyzer — extract manifest, find secrets, audit permissions."""

import argparse
import json
import os
import re
import sys
import zipfile

DANGEROUS_PERMISSIONS = {
    "android.permission.SEND_SMS": "SMS fraud",
    "android.permission.CALL_PHONE": "Unauthorized calls",
    "android.permission.RECORD_AUDIO": "Microphone surveillance",
    "android.permission.ACCESS_FINE_LOCATION": "Location tracking",
    "android.permission.SYSTEM_ALERT_WINDOW": "Overlay attacks",
    "android.permission.BIND_DEVICE_ADMIN": "Device admin control",
    "android.permission.READ_CONTACTS": "Contact theft",
    "android.permission.READ_EXTERNAL_STORAGE": "File system read",
}

SECRET_PATTERNS = {
    "AWS Access Key": r"AKIA[0-9A-Z]{16}",
    "Google API Key": r"AIza[0-9A-Za-z\-_]{35}",
    "Private Key": r"-----BEGIN (RSA |EC )?PRIVATE KEY-----",
    "JWT Token": r"eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*",
    "Hardcoded Password": r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{3,}['\"]",
    "Hardcoded Secret": r"(?i)(secret|apikey|api_key|token)\s*[:=]\s*['\"][^'\"]{8,}['\"]",
    "URL": r"https?://[^\s'\"<>]+",
}


def extract_manifest(apk_path: str) -> dict:
    """Extract and parse AndroidManifest.xml from APK."""
    result = {"package": "", "version_code": "", "version_name": "",
              "min_sdk": "", "target_sdk": "", "permissions": [],
              "exported_components": []}
    try:
        with zipfile.ZipFile(apk_path, "r") as zf:
            if "AndroidManifest.xml" not in zf.namelist():
                return {"error": "AndroidManifest.xml not found"}
            data = zf.read("AndroidManifest.xml").decode("utf-8", errors="ignore")
            for key in ["package", "versionCode", "versionName", "minSdkVersion", "targetSdkVersion"]:
                m = re.search(rf'{key}="([^"]+)"', data)
                if m:
                    result[key.lower().replace("sdk", "_sdk")] = m.group(1)
            result["permissions"] = list(set(re.findall(r'uses-permission[^>]*android:name="([^"]+)"', data)))
            for comp in ["activity", "service", "receiver", "provider"]:
                result["exported_components"].extend(re.findall(rf'<{comp}[^>]*android:name="([^"]+)"', data))
    except Exception as e:
        return {"error": str(e)}
    return result


def find_hardcoded_secrets(apk_path: str) -> list:
    """Scan APK contents for hardcoded secrets."""
    findings = []
    skip_ext = (".dex", ".so", ".bin", ".png", ".jpg", ".gif", ".webp", ".ogg", ".mp3")
    try:
        with zipfile.ZipFile(apk_path, "r") as zf:
            for name in zf.namelist():
                if name.endswith(skip_ext):
                    continue
                content = zf.read(name).decode("utf-8", errors="ignore")
                for stype, pattern in SECRET_PATTERNS.items():
                    for match in re.findall(pattern, content)[:3]:
                        masked = (str(match)[:8] + "..." + str(match)[-4:]) if len(str(match)) > 16 else str(match)
                        findings.append({"file": name, "type": stype, "value": masked})
    except Exception as e:
        return [{"error": str(e)}]
    return findings


def audit_permissions(permissions: list) -> dict:
    """Audit Android permissions for security risks."""
    result = {"total": len(permissions), "dangerous": [], "risk_score": 0}
    for perm in permissions:
        if perm in DANGEROUS_PERMISSIONS:
            result["dangerous"].append({"permission": perm, "risk": DANGEROUS_PERMISSIONS[perm]})
            result["risk_score"] += 3
    result["risk_score"] = min(10, result["risk_score"] // 2)
    result["risk_level"] = ("CRITICAL" if result["risk_score"] >= 8 else
                            "HIGH" if result["risk_score"] >= 6 else
                            "MEDIUM" if result["risk_score"] >= 4 else "LOW")
    return result


def full_report(apk_path: str) -> dict:
    """Generate comprehensive security report."""
    manifest = extract_manifest(apk_path)
    perms = audit_permissions(manifest.get("permissions", []))
    secrets = find_hardcoded_secrets(apk_path)
    return {
        "apk": os.path.basename(apk_path),
        "size_bytes": os.path.getsize(apk_path),
        "manifest": manifest,
        "permissions": perms,
        "secrets_count": len(secrets),
        "secrets": secrets[:10],
        "risk_level": ("HIGH" if perms["risk_score"] >= 6 or len(secrets) > 5 else
                       "MEDIUM" if perms["risk_score"] >= 3 or len(secrets) > 0 else "LOW"),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="APK Security Analyzer")
    parser.add_argument("--apk", required=True, help="Path to APK file")
    parser.add_argument("--manifest", action="store_true", help="Extract manifest")
    parser.add_argument("--secrets", action="store_true", help="Find hardcoded secrets")
    parser.add_argument("--permissions", action="store_true", help="Audit permissions")
    parser.add_argument("--full-report", action="store_true", help="Full report")
    args = parser.parse_args()
    if not os.path.exists(args.apk):
        sys.exit(f"Error: APK not found: {args.apk}")
    if args.manifest:
        result = extract_manifest(args.apk)
    elif args.secrets:
        result = find_hardcoded_secrets(args.apk)
    elif args.permissions:
        result = audit_permissions(extract_manifest(args.apk).get("permissions", []))
    else:
        result = full_report(args.apk)
    print(json.dumps(result, indent=2))
