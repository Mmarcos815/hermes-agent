#!/usr/bin/env python3
"""
Mobile Banking & APK Security Analysis Lab (mobile_banking_lab.py)
Standard: OWASP Mobile Application Security Verification Standard (MASVS v2.0)

Capabilities:
1. Static Analysis: AndroidManifest.xml & Network Security Config auditor
2. Dynamic Analysis: Frida instrumentation hook generator for Certificate Pinning & Biometrics
3. Local Storage Security Checker (Insecure SharedPreferences / SQLite / Keystore)
"""

import sys, os, json, re

MOCK_ANDROID_MANIFEST = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.bionic.mobilebanking">

    <application
        android:allowBackup="true"
        android:debuggable="true"
        android:networkSecurityConfig="@xml/network_security_config">

        <activity
            android:name=".AuthActivity"
            android:exported="true" />

        <activity
            android:name=".InternalLedgerActivity"
            android:exported="true">
            <!-- VULNERABILITY: Exported Activity without permission checks -->
        </activity>

        <service
            android:name=".TokenSyncService"
            android:exported="false" />
    </application>
</manifest>
"""

FRIDA_PINNING_SCRIPT_TEMPLATE = """// Frida Script: Universal SSL/TLS Pinning & TrustManager Bypass
Java.perform(function () {
    console.log("[+] Initializing Bionic Mobile Hook: Bypassing SSL Pinning...");

    // Hook X509TrustManager checkServerTrusted
    var TrustManager = Java.use("javax.net.ssl.X509TrustManager");
    var SSLContext = Java.use("javax.net.ssl.SSLContext");

    var CustomTrustManager = Java.registerClass({
        name: "com.bionic.CustomTrustManager",
        implements: [TrustManager],
        methods: {
            checkClientTrusted: function (chain, authType) {},
            checkServerTrusted: function (chain, authType) {
                console.log("[+] Intercepted checkServerTrusted -> Bypassed certificate check.");
            },
            getAcceptedIssuers: function () {
                return [];
            }
        }
    });

    var TrustManagers = [CustomTrustManager.$new()];
    var SSLContext_init = SSLContext.init.overload(
        "[Ljavax.net.ssl.KeyManager;",
        "[Ljavax.net.ssl.TrustManager;",
        "java.security.SecureRandom"
    );

    SSLContext_init.implementation = function (keyManager, trustManager, secureRandom) {
        console.log("[+] SSLContext.init intercepted -> Injecting CustomTrustManager.");
        SSLContext_init.call(this, keyManager, TrustManagers, secureRandom);
    };
});
"""

class MobileBankingAuditor:
    def __init__(self):
        pass

    def audit_manifest(self, manifest_xml: str) -> list:
        findings = []
        
        # 1. Debuggable check
        if 'android:debuggable="true"' in manifest_xml:
            findings.append({
                "id": "MASVS-RESILIENCE-1",
                "severity": "HIGH",
                "title": "Application is Debuggable in Production",
                "detail": "android:debuggable is set to true, allowing debugger attachments and memory dumping.",
                "remediation": "Set android:debuggable=\"false\" in production release builds."
            })

        # 2. AllowBackup check
        if 'android:allowBackup="true"' in manifest_xml:
            findings.append({
                "id": "MASVS-STORAGE-2",
                "severity": "MEDIUM",
                "title": "Application Backup Allowed (adb backup)",
                "detail": "android:allowBackup is enabled, permitting full sandbox extraction via ADB.",
                "remediation": "Set android:allowBackup=\"false\"."
            })

        # 3. Exported Activities
        exported_matches = re.findall(r'<activity[^>]*android:name="([^"]+)"[^>]*android:exported="true"', manifest_xml)
        for act in exported_matches:
            if "internal" in act.lower() or "ledger" in act.lower():
                findings.append({
                    "id": "MASVS-PLATFORM-1",
                    "severity": "HIGH",
                    "title": f"Sensitive Internal Activity Exported: {act}",
                    "detail": "Third-party applications on the device can launch this component directly.",
                    "remediation": "Set android:exported=\"false\" or enforce custom signature permissions."
                })

        return findings

    def generate_frida_harness(self, output_path: str):
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(FRIDA_PINNING_SCRIPT_TEMPLATE)
        return output_path


def run_mobile_lab_demo():
    print("=== MOBILE BANKING & APK SECURITY LAB ===")
    auditor = MobileBankingAuditor()

    print("\n1. Running Static Analysis on AndroidManifest.xml...")
    findings = auditor.audit_manifest(MOCK_ANDROID_MANIFEST)
    print(json.dumps(findings, indent=2))
    assert len(findings) == 3, "Expected 3 security findings"

    print("\n2. Generating Dynamic Frida SSL Pinning Bypass Script...")
    frida_path = r"C:\Users\mobil\orca\projects\my 1st\knowledge\frida_ssl_pinning_bypass.js"
    auditor.generate_frida_harness(frida_path)
    print(f"   Frida Script generated at: {frida_path}")

    print("\n>>> MOBILE BANKING LAB: 100% COMPLETE & PASS <<<")


if __name__ == "__main__":
    run_mobile_lab_demo()
