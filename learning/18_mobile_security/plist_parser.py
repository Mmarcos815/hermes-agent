#!/usr/bin/env python3
"""iOS plist Security Parser — analyze Info.plist for security issues."""

import argparse
import json
import os
import plistlib
import sys
from pathlib import Path

SENSITIVE_KEYS = {
    "NSLocationWhenInUseUsageDescription": "location",
    "NSLocationAlwaysUsageDescription": "location",
    "NSCameraUsageDescription": "camera",
    "NSMicrophoneUsageDescription": "microphone",
    "NSContactsUsageDescription": "contacts",
    "NSBluetoothAlwaysUsageDescription": "bluetooth",
    "NSFaceIDUsageDescription": "biometric",
    "NSUserTrackingUsageDescription": "tracking",
}


def parse_plist(file_path: str) -> dict:
    """Parse a plist file (binary or XML)."""
    try:
        with open(file_path, "rb") as f:
            data = plistlib.load(f)
            return data if isinstance(data, dict) else {"content": data}
    except Exception as e:
        return {"error": f"Parse error: {e}"}


def analyze_security(plist_data: dict) -> dict:
    """Analyze plist data for security issues."""
    result = {
        "ats_violations": [],
        "sensitive_permissions": [],
        "url_schemes": [],
        "info": {},
        "risk_score": 0,
    }
    # Check ATS
    ats = plist_data.get("NSAppTransportSecurity", {})
    if isinstance(ats, dict):
        if ats.get("NSAllowsArbitraryLoads", False):
            result["ats_violations"].append("NSAllowsArbitraryLoads=True — ATS disabled")
            result["risk_score"] += 3
        for domain, settings in ats.get("NSExceptionDomains", {}).items():
            if isinstance(settings, dict) and settings.get("NSExceptionRequiresForwardSecrecy") is False:
                result["ats_violations"].append(f"{domain}: forward secrecy disabled")
                result["risk_score"] += 2
    # Check sensitive permissions
    for key, category in SENSITIVE_KEYS.items():
        if key in plist_data:
            result["sensitive_permissions"].append({
                "key": key, "category": category,
                "description": plist_data.get(key, "")[:80],
            })
    # URL schemes
    for url_type in plist_data.get("CFBundleURLTypes", []):
        if isinstance(url_type, dict):
            result["url_schemes"].extend(url_type.get("CFBundleURLSchemes", []))
    # Basic info
    for key in ["CFBundleIdentifier", "CFBundleVersion", "MinimumOSVersion"]:
        if key in plist_data:
            result["info"][key] = plist_data[key]
    result["risk_score"] = min(10, result["risk_score"])
    result["risk_level"] = ("CRITICAL" if result["risk_score"] >= 8 else
                            "HIGH" if result["risk_score"] >= 6 else
                            "MEDIUM" if result["risk_score"] >= 4 else "LOW")
    return result


def scan_directory(dir_path: str) -> list:
    """Scan directory for plist files."""
    results = []
    for root, _, files in os.walk(dir_path):
        for f in files:
            if f.endswith(".plist"):
                data = parse_plist(os.path.join(root, f))
                sec = analyze_security(data)
                sec["file"] = os.path.join(root, f)
                results.append(sec)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="iOS plist Security Parser")
    parser.add_argument("--file", help="Path to plist file")
    parser.add_argument("--dir", help="Directory to scan for plist files")
    parser.add_argument("--security", action="store_true", help="Security analysis")
    args = parser.parse_args()
    if not args.file and not args.dir:
        sys.exit("Error: --file or --dir required")
    if args.file:
        data = parse_plist(args.file)
        result = analyze_security(data) if args.security else data
        result["file"] = args.file
    else:
        result = {"directory": args.dir, "results": scan_directory(args.dir)}
    print(json.dumps(result, indent=2))
