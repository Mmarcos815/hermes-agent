# Mobile Security Lab

A hands-on mobile security testing environment for Android and iOS app analysis.

## Setup Guide

### Prerequisites

- **Operating System**: Linux, macOS, or Windows (WSL2 recommended)
- **Python**: 3.10+
- **Java**: JDK 17 (for Android SDK)
- **Node.js**: 18+ (for Frida tools)

---

### Android Emulator Setup

1. **Install Android Studio** from https://developer.android.com/studio
2. **Create an AVD** (Android Virtual Device):
   ```bash
   sdkmanager "system-images;android-34;google_apis;x86_64"
   avdmanager create avd -n test_device -k "system-images;android-34;google_apis;x86_64" -d pixel_5
   ```
3. **Start the emulator**:
   ```bash
   emulator -avd test_device -no-snapshot -gpu swiftshader_indirect
   ```
4. **Verify ADB connection**:
   ```bash
   adb devices
   ```

> **Tip**: Use API 30-34 emulators for best Frida compatibility. Avoid Google Play images for root access.

### iOS Simulator Setup

1. **Install Xcode** from the Mac App Store
2. **Install Xcode Command Line Tools**:
   ```bash
   xcode-select --install
   ```
3. **List available simulators**:
   ```bash
   xcrun simctl list devices available
   ```
4. **Boot a simulator**:
   ```bash
   xcrun simctl boot "iPhone 15 Pro"
   open -a Simulator
   ```
5. **Install Frida on the simulator** (jailbreak required for full functionality):
   ```bash
   brew install frida
   ```

> **Note**: iOS dynamic analysis typically requires a jailbroken device. The simulator has limited security testing capabilities.

---

### Tools Installation

```bash
# Frida (dynamic instrumentation)
pip install frida-tools

# APKTool (APK decompilation)
# Download from https://ibotpeaches.github.io/Apktool/

# JADX (Java decompiler)
# Download from https://github.com/skylot/jadx

# MobSF (Mobile Security Framework)
docker pull opensecurity/mobile-security-framework-mobsf

# Objection (runtime exploration)
pip install objection

# APKSign (test signing)
# Included in Android SDK build-tools
```

---

### Quick Start

```bash
# Generate a vulnerable test app
python test_app_generator.py --output ./test_apps/

# Analyze an APK
python analysis_workflow.py --apk ./test_apps/vuln_app.apk

# Hook a running app with Frida
python frida_scripts.py --package com.example.vulnapp --script ssl_bypass

# Full lab setup check
bash android_setup.sh --check
```

---

### Lab Structure

```
mobile_lab/
├── README.md                  # This file
├── android_setup.sh           # Emulator setup & validation
├── test_app_generator.py      # Vulnerable app generation
├── frida_scripts.py           # Frida hooking library
└── analysis_workflow.py       # Automated analysis pipeline
```

---

### Legal Notice

This lab is for **authorized security testing only**. Only test apps you own or have explicit permission to analyze. Unauthorized access to systems is illegal.
