#!/usr/bin/env python3
"""
Frida Hooking Scripts for Mobile Dynamic Analysis

Provides ready-to-use Frida scripts for common Android security testing scenarios.
Each script can be loaded via frida-scripts CLI or the analysis workflow.

Usage:
    python frida_scripts.py --package com.example.app --script ssl_bypass
    python frida_scripts.py --list
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Callable


# ============================================================================
# Frida JavaScript Snippets
# ============================================================================

SSL_PINNING_BYPASS = """
// SSL Pinning Bypass - Universal
// Bypasses certificate pinning in common libraries

Java.perform(function() {
    console.log("[*] SSL Pinning Bypass loaded");

    // Bypass OkHttp3 CertificatePinner
    try {
        var CertificatePinner = Java.use("okhttp3.CertificatePinner");
        CertificatePinner.check.overload('java.lang.string', 'java.util.List').implementation = function(hostname, certs) {
            console.log("[+] OkHttp3 check() bypassed for: " + hostname);
            return;
        };
    } catch(e) { console.log("[-] OkHttp3 not found: " + e); }

    // Bypass TrustManagerImpl (Android 7+)
    try {
        var TrustManagerImpl = Java.use("com.android.org.conscrypt.TrustManagerImpl");
        TrustManagerImpl.verifyChain.implementation = function(untrustedChain, trustAnchorChain, host, clientAuth, ocspData, tlsSctData) {
            console.log("[+] TrustManagerImpl.verifyChain bypassed for: " + host);
            return untrustedChain;
        };
    } catch(e) { console.log("[-] TrustManagerImpl not found: " + e); }

    // Bypass custom X509TrustManager
    try {
        var X509TrustManager = Java.use("javax.net.ssl.X509TrustManager");
        var SSLContext = Java.use("javax.net.ssl.SSLContext");

        var TrustManager = Java.registerClass({
            name: "com.lab.TrustManager",
            implements: [X509TrustManager],
            methods: {
                checkClientTrusted: function(chain, authType) {},
                checkServerTrusted: function(chain, authType) {},
                getAcceptedIssuers: function() { return []; }
            }
        });

        var trustManagers = [TrustManager.$new()];
        var tlsSSLContext = SSLContext.getInstance("TLS");
        tlsSSLContext.init(null, trustManagers, null);
        var factory = tlsSSLContext.getSocketFactory();

        var SSLSocketFactory = Java.use("javax.net.ssl.SSLSocketFactory");
        SSLSocketFactory.setDefault.implementation = function() { return factory; };
    } catch(e) { console.log("[-] SSLContext bypass failed: " + e); }

    console.log("[+] SSL pinning bypass active");
});
"""

ROOT_DETECTION_BYPASS = """
// Root Detection Bypass
// Hides root, Magisk, and emulator indicators

Java.perform(function() {
    console.log("[*] Root Detection Bypass loaded");

    // Bypass common root checks
    var rootIndicators = [
        "/system/app/Superuser.apk",
        "/system/xbin/su",
        "/system/bin/su",
        "/sbin/su",
        "/data/local/xbin/su",
        "/data/local/bin/su",
        "/su/bin/su"
    ];

    // Hook File.exists()
    var File = Java.use("java.io.File");
    File.exists.implementation = function() {
        var path = this.getAbsolutePath();
        if (rootIndicators.some(p => path.includes(p))) {
            console.log("[+] Blocked root indicator: " + path);
            return false;
        }
        return this.exists();
    };

    // Hook java.lang.Runtime.exec()
    var Runtime = Java.use("java.lang.Runtime");
    var Process = Java.use("java.lang.Process");

    Runtime.exec.overload('java.lang.String').implementation = function(cmd) {
        var blocked = ["su", "which su", "id", "busybox"];
        if (blocked.some(b => cmd.includes(b))) {
            console.log("[+] Blocked command: " + cmd);
            // Return fake process that exits with 0
            return this.exec("echo ''");
        }
        return this.exec(cmd);
    };

    // Hook System.getProperty to hide root
    var System = Java.use("java.lang.System");
    System.getProperty.overload('java.lang.String').implementation = function(key) {
        if (key === "ro.debuggable") return "0";
        if (key === "ro.secure") return "1";
        return this.getProperty(key);
    };

    // Hide Magisk
    try {
        var MagiskDetector = Java.use("com.topjohnwu.magisk.MagiskManager");
        // If app references Magisk directly
    } catch(e) {}

    // Bypass isEmulator check
    var Build = Java.use("android.os.Build");
    var originalFingerprint = Build.FINGERPRINT.value;
    Build.FINGERPRINT.value = "google/redfin/redfin:13/TP1A.221005.002/9012297:user/release-keys";
    Build.MODEL.value = "Pixel 5";
    Build.MANUFACTURER.value = "Google";
    Build.BRAND.value = "google";
    Build.PRODUCT.value = "redfin";
    Build.HARDWARE.value = "redfin";
    Build.DEVICE.value = "redfin";

    console.log("[+] Root detection bypass active");
});
"""

WEBVIEW_INSPECTOR = """
// WebView Inspector
// Monitors WebView URL loading, JS execution, and bridge calls

Java.perform(function() {
    console.log("[*] WebView Inspector loaded");

    // Hook WebView.loadUrl()
    var WebView = Java.use("android.webkit.WebView");
    WebView.loadUrl.overload('java.lang.String').implementation = function(url) {
        console.log("[WebView] Loading URL: " + url);
        return this.loadUrl(url);
    };

    // Hook WebView.loadDataWithBaseURL()
    WebView.loadDataWithBaseURL.implementation = function(baseUrl, data, mimeType, encoding, historyUrl) {
        console.log("[WebView] loadDataWithBaseURL:");
        console.log("  BaseURL: " + baseUrl);
        console.log("  Data (first 500): " + data.substring(0, 500));
        return this.loadDataWithBaseURL(baseUrl, data, mimeType, encoding, historyUrl);
    };

    // Hook JavaScriptInterface methods
    var annotations = Java.use("android.webkit.JavascriptInterface");

    // Hook WebViewClient.shouldInterceptRequest()
    var WebViewClient = Java.use("android.webkit.WebViewClient");
    WebViewClient.shouldInterceptRequest.overload(
        'android.webkit.WebView', 'android.webkit.WebResourceRequest'
    ).implementation = function(view, request) {
        var url = request.getUrl().toString();
        var method = request.getMethod();
        console.log("[WebView] Request: " + method + " " + url);
        return null; // Don't intercept, just log
    };

    // Hook WebSettings to log configuration changes
    var WebSettings = Java.use("android.webkit.WebSettings");
    WebSettings.setJavaScriptEnabled.implementation = function(flag) {
        console.log("[WebView] JavaScript enabled: " + flag);
        return this.setJavaScriptEnabled(flag);
    };
    WebSettings.setAllowFileAccess.implementation = function(flag) {
        console.log("[WebView] File access enabled: " + flag);
        return this.setAllowFileAccess(flag);
    };

    console.log("[+] WebView inspector active");
});
"""

CRYPTO_HOOKS = """
// Cryptography Hooks
// Captures encryption keys, IVs, and plaintext before encryption

Java.perform(function() {
    console.log("[*] Crypto Hooks loaded");

    // Hook javax.crypto.Cipher
    var Cipher = Java.use("javax.crypto.Cipher");

    Cipher.init.overload('int', 'java.security.Key').implementation = function(opmode, key) {
        var mode = (opmode === 1) ? "ENCRYPT" : (opmode === 2) ? "DECRYPT" : "OTHER";
        var keyBytes = key.getEncoded();
        console.log("[Cipher] init: " + mode + " | Algorithm: " + this.getAlgorithm());
        console.log("[Cipher] Key (hex): " + bytesToHex(keyBytes));
        return this.init(opmode, key);
    };

    Cipher.init.overload('int', 'java.security.Key', 'java.security.spec.AlgorithmParameterSpec').implementation = function(opmode, key, params) {
        var mode = (opmode === 1) ? "ENCRYPT" : "DECRYPT";
        console.log("[Cipher] init: " + mode + " | Key: " + bytesToHex(key.getEncoded()));
        if (params.getClass().getName().includes("IvParameterSpec")) {
            var ivSpec = Java.cast(params, Java.use("javax.crypto.spec.IvParameterSpec"));
            console.log("[Cipher] IV: " + bytesToHex(ivSpec.getIV()));
        }
        return this.init(opmode, key, params);
    };

    Cipher.doFinal.overload('[B').implementation = function(input) {
        var result = this.doFinal(input);
        console.log("[Cipher] doFinal:");
        console.log("  Input (first 100 bytes hex): " + bytesToHex(input.slice(0, 100)));
        console.log("  Output (first 100 bytes hex): " + bytesToHex(result.slice(0, 100)));
        return result;
    };

    // Hook MessageDigest
    var MessageDigest = Java.use("javax.crypto.MessageDigest") ||
                        Java.use("java.security.MessageDigest");
    MessageDigest.digest.overload('[B').implementation = function(input) {
        var result = this.digest(input);
        console.log("[Digest] Algorithm: " + this.getAlgorithm());
        console.log("[Digest] Input: " + bytesToHex(input.slice(0, 64)));
        console.log("[Digest] Hash: " + bytesToHex(result));
        return result;
    };

    // Hook SecretKeyFactory (for key derivation)
    try {
        var SecretKeyFactory = Java.use("javax.crypto.SecretKeyFactory");
        SecretSecretFactory.generateSecret.implementation = function(keySpec) {
            console.log("[SecretKeyFactory] Generating key with: " + this.getAlgorithm());
            return this.generateSecret(keySpec);
        };
    } catch(e) {}

    function bytesToHex(bytes) {
        if (!bytes) return "(null)";
        var result = [];
        for (var i = 0; i < bytes.length; i++) {
            result.push((bytes[i] >>> 4).toString(16));
            result.push((bytes[i] & 0xF).toString(16));
        }
        return result.join("");
    }

    console.log("[+] Crypto hooks active");
});
"""

INTENT_MONITOR = """
// Intent Monitor
// Logs all Intent launches, extras, and data URIs

Java.perform(function() {
    console.log("[*] Intent Monitor loaded");

    // Hook Activity.startActivity()
    var Activity = Java.use("android.app.Activity");
    Activity.startActivity.overload('android.content.Intent').implementation = function(intent) {
        logIntent("startActivity", intent);
        return this.startActivity(intent);
    };

    // Hook Activity.startActivityForResult()
    Activity.startActivityForResult.overload('android.content.Intent', 'int').implementation = function(intent, requestCode) {
        logIntent("startActivityForResult (code=" + requestCode + ")", intent);
        return this.startActivityForResult(intent, requestCode);
    };

    // Hook Context.startService() and startForegroundService()
    var Context = Java.use("android.content.Context");
    Context.startService.overload('android.content.Intent').implementation = function(intent) {
        logIntent("startService", intent);
        return this.startService(intent);
    };

    // Hook sendBroadcast()
    Activity.sendBroadcast.overload('android.content.Intent').implementation = function(intent) {
        logIntent("sendBroadcast", intent);
        return this.sendBroadcast(intent);
    };

    function logIntent(action, intent) {
        console.log("\\n[Intent] " + action);
        var data = intent.getData();
        if (data) console.log("  Data: " + data.toString());
        var component = intent.getComponent();
        if (component) console.log("  Component: " + component.flattenToString());
        var action_str = intent.getAction();
        if (action_str) console.log("  Action: " + action_str);
        var extras = intent.getExtras();
        if (extras) {
            var keySet = extras.keySet();
            var iter = keySet.iterator();
            while (iter.hasNext()) {
                var key = iter.next();
                var value = extras.get(key);
                console.log("  Extra: " + key + " = " + value);
            }
        }
        var flags = intent.getFlags();
        console.log("  Flags: 0x" + flags.toString(16));
    }

    console.log("[+] Intent monitor active");
});
"""

NETWORK_INTERCEPTOR = """
// Network Interceptor
// Captures HTTP/HTTPS request and response data

Java.perform(function() {
    console.log("[*] Network Interceptor loaded");

    // Hook OkHttp3
    try {
        var OkHttpClient = Java.use("okhttp3.OkHttpClient");
        var RealCall = Java.use("okhttp3.RealCall");
        var Request = Java.use("okhttp3.Request");
        var Response = Java.use("okhttp3.Response");
        var Buffer = Java.use("okhttp3.Buffer");

        // Intercept requests
        var originalExecute = RealCall.execute;
        RealCall.execute.implementation = function() {
            var request = this.request();
            console.log("\\n[OkHttp] Request: " + request.method() + " " + request.url());
            var headers = request.headers();
            for (var i = 0; i < headers.size(); i++) {
                console.log("  Header: " + headers.name(i) + ": " + headers.value(i));
            }
            var body = request.body();
            if (body) {
                console.log("  Body (content-type): " + body.contentType());
            }

            var response = originalExecute.call(this);
            console.log("[OkHttp] Response: " + response.code() + " " + response.message());
            return response;
        };
    } catch(e) { console.log("[-] OkHttp3 hook failed: " + e); }

    // Hook HttpURLConnection
    try {
        var HttpURLConnection = Java.use("java.net.HttpURLConnection");
        var URL = Java.use("java.net.URL");

        URL.openConnection.overload().implementation = function() {
            var conn = this.openConnection();
            console.log("[URL] openConnection: " + this.toString());
            return conn;
        };
    } catch(e) { console.log("[-] URL hook failed: " + e); }

    // Hook SSLSocketFactory to log TLS connections
    try {
        var SSLSocketFactory = Java.use("javax.net.ssl.SSLSocketFactory");
        var Socket = Java.use("java.net.Socket");

        Socket.connect.implementation = function(endpoint, timeout) {
            console.log("[Socket] Connecting to: " + endpoint.toString());
            return this.connect(endpoint, timeout);
        };
    } catch(e) { console.log("[-] Socket hook failed: " + e); }

    console.log("[+] Network interceptor active");
});
"""

# ============================================================================
# Script Registry
# ============================================================================

SCRIPTS: Dict[str, str] = {
    "ssl_bypass": SSL_PINNING_BYPASS,
    "root_bypass": ROOT_DETECTION_BYPASS,
    "webview_inspector": WEBVIEW_INSPECTOR,
    "crypto_hooks": CRYPTO_HOOKS,
    "intent_monitor": INTENT_MONITOR,
    "network_interceptor": NETWORK_INTERCEPTOR,
}


def list_scripts():
    """List all available Frida scripts."""
    print("Available Frida Scripts:")
    print("-" * 40)
    for name, script in SCRIPTS.items():
        # Extract first comment as description
        desc = "No description"
        for line in script.strip().split("\n"):
            line = line.strip()
            if line.startswith("//") and not line.startswith("///"):
                desc = line[2:].strip()
                break
        print(f"  {name:25s} - {desc}")
    print(f"\nTotal: {len(SCRIPTS)} scripts")


def get_script(name: str) -> str:
    """Get a Frida script by name."""
    if name not in SCRIPTS:
        print(f"[!] Unknown script: {name}")
        print(f"    Available: {', '.join(SCRIPTS.keys())}")
        sys.exit(1)
    return SCRIPTS[name]


def save_script(name: str, output_dir: str = "."):
    """Save a Frida script to a file."""
    script = get_script(name)
    output_path = Path(output_dir) / f"{name}.js"
    output_path.write_text(script)
    print(f"[+] Saved: {output_path}")
    return output_path


def generate_loader_script(package_name: str, script_name: str) -> str:
    """Generate a Python loader script for Frida."""
    frida_script = get_script(script_name)
    loader = f'''#!/usr/bin/env python3
"""Auto-generated Frida loader for {package_name}"""
import frida
import sys

PACKAGE = "{package_name}"

def on_message(message, data):
    if message["type"] == "send":
        print("[*] {{}}".format(message["payload"]))
    elif message["type"] == "error":
        print("[!] {{}}".format(message["stack"]))

def main():
    device = frida.get_usb_device()
    pid = device.spawn([PACKAGE])
    session = device.attach(pid)

    script = session.create_script("""
{frida_script}
""")
    script.on("message", on_message)
    script.load()

    device.resume(pid)
    print("[*] Script loaded. Press Ctrl+C to exit.")
    sys.stdin.read()

if __name__ == "__main__":
    main()
'''
    return loader


def main():
    parser = argparse.ArgumentParser(description="Frida Hooking Scripts for Mobile Analysis")
    parser.add_argument("--list", action="store_true", help="List available scripts")
    parser.add_argument("--package", help="Target app package name")
    parser.add_argument("--script", choices=list(SCRIPTS.keys()),
                       help="Script to use")
    parser.add_argument("--output", default=".", help="Output directory")
    parser.add_argument("--save", action="store_true", help="Save script to file")
    parser.add_argument("--generate-loader", action="store_true",
                       help="Generate Python loader script")
    args = parser.parse_args()

    if args.list:
        list_scripts()
        return

    if not args.script:
        print("[!] Specify --script or use --list to see available scripts")
        sys.exit(1)

    if args.save:
        save_script(args.script, args.output)

    if args.generate_loader and args.package:
        loader = generate_loader_script(args.package, args.script)
        loader_path = Path(args.output) / f"load_{args.script}.py"
        loader_path.write_text(loader)
        print(f"[+] Generated loader: {loader_path}")

    if not args.save and not args.generate_loader:
        # Print the script to stdout
        print(get_script(args.script))


if __name__ == "__main__":
    main()
