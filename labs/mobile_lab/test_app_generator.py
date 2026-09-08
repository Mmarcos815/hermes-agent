#!/usr/bin/env python3
"""
Vulnerable Android Test App Generator

Generates intentionally vulnerable Android apps for security practice.
These apps contain common OWASP Mobile Top 10 vulnerabilities for learning purposes.

Usage:
    python test_app_generator.py --output ./test_apps/ --app vuln_webview
    python test_app_generator.py --output ./test_apps/ --all
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


class VulnerableAppGenerator:
    """Generates Android apps with intentional vulnerabilities for security training."""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path(tempfile.mkdtemp(prefix="vuln_gen_"))

    def generate_hardcoded_secrets(self) -> Path:
        """Generate app with hardcoded API keys and credentials."""
        app_name = "HardcodedSecretsApp"
        app_dir = self.temp_dir / app_name
        app_dir.mkdir()

        # AndroidManifest.xml
        manifest = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.lab.hardcoded">
    <application android:label="Secrets Lab" android:debuggable="true">
        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
    </application>
</manifest>"""

        # MainActivity.java with hardcoded secrets
        java_code = """package com.lab.hardcoded;

import android.app.Activity;
import android.os.Bundle;
import android.util.Log;
import android.widget.TextView;

public class MainActivity extends Activity {
    // VULNERABILITY: Hardcoded API keys
    private static final String AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE";
    private static final String AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY";
    private static final String API_TOKEN = "sk_live_4eC39HqLyjWDarjtT1zdp7dc";
    private static final String DB_PASSWORD = "SuperSecret123!";
    private static final String ENCRYPTION_KEY = "0123456789abcdef";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        TextView tv = new TextView(this);
        tv.setText("Hardcoded Secrets Lab App");
        setContentView(tv);

        // VULNERABILITY: Logging sensitive data
        Log.d("SecretsApp", "AWS Key: " + AWS_ACCESS_KEY);
        Log.d("SecretsApp", "DB Password: " + DB_PASSWORD);
        Log.d("SecretsApp", "Token: " + API_TOKEN);
    }
}
"""
        (app_dir / "AndroidManifest.xml").write_text(manifest)
        src_dir = app_dir / "src" / "com" / "lab" / "hardcoded"
        src_dir.mkdir(parents=True)
        (src_dir / "MainActivity.java").write_text(java_code)

        return self._compile_apk(app_dir, "com.lab.hardcoded")

    def generate_insecure_webview(self) -> Path:
        """Generate app with insecure WebView configuration."""
        app_name = "InsecureWebViewApp"
        app_dir = self.temp_dir / app_name
        app_dir.mkdir()

        manifest = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.lab.webview">
    <uses-permission android:name="android.permission.INTERNET"/>
    <application android:label="WebView Lab" android:usesCleartextTraffic="true"
                 android:debuggable="true">
        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
    </application>
</manifest>"""

        java_code = """package com.lab.webview;

import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.JavascriptInterface;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        WebView webView = new WebView(this);
        WebSettings settings = webView.getSettings();

        // VULNERABILITY: JavaScript enabled without validation
        settings.setJavaScriptEnabled(true);

        // VULNERABILITY: File access enabled
        settings.setAllowFileAccess(true);
        settings.setAllowFileAccessFromFileURLs(true);
        settings.setAllowUniversalAccessFromFileURLs(true);

        // VULNERABILITY: DOM storage enabled (can leak data)
        settings.setDomStorageEnabled(true);

        // VULNERABILITY: JavaScript interface exposed to untrusted content
        webView.addJavascriptInterface(new NativeBridge(), "NativeBridge");

        webView.setWebViewClient(new WebViewClient());
        setContentView(webView);

        // VULNERABILITY: Loading HTTP (cleartext) URL
        webView.loadUrl("http://example.com/lab");
    }

    // VULNERABILITY: JavaScript interface exposes sensitive functions
    public class NativeBridge {
        @JavascriptInterface
        public String getUserData() {
            return "{\\"user\\": \\"admin\\", \\"token\\": \\"abc123\\"}";
        }

        @JavascriptInterface
        public void executeCommand(String cmd) {
            try {
                Runtime.getRuntime().exec(cmd);
            } catch (Exception e) {
                e.printStackTrace();
            }
        }

        @JavascriptInterface
        public String readFile(String path) {
            try {
                return new String(java.nio.file.Files.readAllBytes(
                    java.nio.file.Paths.get(path)));
            } catch (Exception e) {
                return "Error: " + e.getMessage();
            }
        }
    }
}
"""
        (app_dir / "AndroidManifest.xml").write_text(manifest)
        src_dir = app_dir / "src" / "com" / "lab" / "webview"
        src_dir.mkdir(parents=True)
        (src_dir / "MainActivity.java").write_text(java_code)

        return self._compile_apk(app_dir, "com.lab.webview")

    def generate_insecure_storage(self) -> Path:
        """Generate app with insecure data storage patterns."""
        app_name = "InsecureStorageApp"
        app_dir = self.temp_dir / app_name
        app_dir.mkdir()

        manifest = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.lab.storage">
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE"/>
    <application android:label="Storage Lab" android:debuggable="true">
        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
    </application>
</manifest>"""

        java_code = """package com.lab.storage;

import android.app.Activity;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.Environment;
import android.widget.TextView;
import java.io.File;
import java.io.FileWriter;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        TextView tv = new TextView(this);
        tv.setText("Insecure Storage Lab");
        setContentView(tv);

        // VULNERABILITY: Storing passwords in plaintext SharedPreferences
        SharedPreferences prefs = getSharedPreferences("user_prefs", MODE_WORLD_READABLE);
        prefs.edit()
            .putString("username", "admin")
            .putString("password", "password123")
            .putString("credit_card", "4111-1111-1111-1111")
            .putString("ssn", "123-45-6789")
            .apply();

        // VULNERABILITY: Writing sensitive data to external storage
        try {
            File extDir = Environment.getExternalStorageDirectory();
            File secretFile = new File(extDir, "user_data.txt");
            FileWriter writer = new FileWriter(secretFile);
            writer.write("session_token=eyJhbGciOiJIUzI1NiJ9.secret\\n");
            writer.write("api_key=sk_live_1234567890abcdef\\n");
            writer.close();
        } catch (Exception e) {
            e.printStackTrace();
        }

        // VULNERABILITY: Storing data in world-readable SQLite
        // (would normally use SQLiteDatabase - simplified here)
    }
}
"""
        (app_dir / "AndroidManifest.xml").write_text(manifest)
        src_dir = app_dir / "src" / "com" / "lab" / "storage"
        src_dir.mkdir(parents=True)
        (src_dir / "MainActivity.java").write_text(java_code)

        return self._compile_apk(app_dir, "com.lab.storage")

    def generate_insecure_communication(self) -> Path:
        """Generate app that sends data over insecure channels."""
        app_name = "InsecureCommApp"
        app_dir = self.temp_dir / app_name
        app_dir.mkdir()

        manifest = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.lab.comm">
    <uses-permission android:name="android.permission.INTERNET"/>
    <application android:label="Comm Lab" android:usesCleartextTraffic="true"
                 android:debuggable="true" android:networkSecurityConfig="@xml/network_security_config">
        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
    </application>
</manifest>"""

        java_code = """package com.lab.comm;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;
import java.net.HttpURLConnection;
import java.net.URL;
import java.io.OutputStream;
import javax.net.ssl.HttpsURLConnection;
import javax.net.ssl.X509TrustManager;
import javax.net.ssl.TrustManager;
import javax.net.ssl.SSLContext;
import java.security.cert.X509Certificate;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        TextView tv = new TextView(this);
        tv.setText("Insecure Communication Lab");
        setContentView(tv);

        new Thread(() -> {
            try {
                // VULNERABILITY: Sending data over HTTP (no TLS)
                URL url = new URL("http://api.example.com/login");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setDoOutput(true);
                OutputStream os = conn.getOutputStream();
                os.write("username=admin&password=secret123".getBytes());
                os.close();

                // VULNERABILITY: Trusting all certificates
                TrustManager[] trustAll = new TrustManager[]{
                    new X509TrustManager() {
                        public X509Certificate[] getAcceptedIssuers() { return new X509Certificate[0]; }
                        public void checkClientTrusted(X509Certificate[] chain, String authType) {}
                        public void checkServerTrusted(X509Certificate[] chain, String authType) {}
                    }
                };
                SSLContext sc = SSLContext.getInstance("TLS");
                sc.init(null, trustAll, new java.security.SecureRandom());
                HttpsURLConnection.setDefaultSSLSocketFactory(sc.getSocketFactory());
                HttpsURLConnection.setDefaultHostnameVerifier((hostname, session) -> true);

            } catch (Exception e) {
                e.printStackTrace();
            }
        }).start();
    }
}
"""
        (app_dir / "AndroidManifest.xml").write_text(manifest)
        src_dir = app_dir / "src" / "com" / "lab" / "comm"
        src_dir.mkdir(parents=True)
        (src_dir / "MainActivity.java").write_text(java_code)

        return self._compile_apk(app_dir, "com.lab.comm")

    def _compile_apk(self, app_dir: Path, package_name: str) -> Path:
        """
        Compile the generated app into an APK.
        In a real environment, this would use aapt/d8/dx to produce a valid APK.
        Here we generate the source structure and documentation.
        """
        # Copy to output
        dest = self.output_dir / package_name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(app_dir, dest)

        # Create build instructions
        build_instructions = f"""# Build Instructions for {package_name}

## Compile Commands:
# 1. Generate R.java (if needed)
#    aapt package -f -m -J src/ -M AndroidManifest.xml -S res/ -I $ANDROID_HOME/platforms/android-34/android.jar

# 2. Compile Java sources
#    javac -bootclasspath $ANDROID_HOME/platforms/android-34/android.jar \\
#          -d classes/ src/com/lab/**/*.java

# 3. Convert to DEX
#    d8 --min-api 21 --output . classes/*.class

# 4. Package APK
#    aapt package -f -M AndroidManifest.xml -S res/ -I $ANDROID_HOME/platforms/android-34/android.jar \\
#              -F {package_name}.unaligned.apk

# 5. Add DEX to APK
#    zip -j {package_name}.unaligned.apk classes.dex

# 6. Align APK
#    zipalign -f 4 {package_name}.unaligned.apk {package_name}.apk

# 7. Sign APK
#    apksigner sign --ks lab.keystore {package_name}.apk
"""
        (dest / "BUILD.md").write_text(build_instructions)
        return dest

    def generate_all(self):
        """Generate all vulnerable test apps."""
        apps = {
            "hardcoded_secrets": self.generate_hardcoded_secrets(),
            "insecure_webview": self.generate_insecure_webview(),
            "insecure_storage": self.generate_insecure_storage(),
            "insecure_communication": self.generate_insecure_communication(),
        }
        return apps

    def cleanup(self):
        """Remove temporary files."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="Generate vulnerable Android test apps")
    parser.add_argument("--output", default="./test_apps/", help="Output directory")
    parser.add_argument("--app", choices=["hardcoded_secrets", "insecure_webview",
                                          "insecure_storage", "insecure_communication"],
                       help="Generate specific vulnerable app")
    parser.add_argument("--all", action="store_true", help="Generate all vulnerable apps")
    args = parser.parse_args()

    gen = VulnerableAppGenerator(args.output)

    try:
        if args.all or (not args.app):
            apps = gen.generate_all()
            print(f"[+] Generated {len(apps)} vulnerable apps:")
            for name, path in apps.items():
                print(f"    - {name}: {path}")
        elif args.app:
            method = getattr(gen, f"generate_{args.app}", None)
            if method:
                path = method()
                print(f"[+] Generated: {path}")
            else:
                print(f"[!] Unknown app type: {args.app}")
                sys.exit(1)
    finally:
        gen.cleanup()


if __name__ == "__main__":
    main()
