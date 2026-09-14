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

### External Dependencies Required

| Tool | Purpose | Required By | Install |
|------|---------|-------------|---------|
| **APKTool** | APK decompilation to smali/resources | `analysis_workflow.py` | [ibotpeaches.github.io/Apktool](https://ibotpeaches.github.io/Apktool/) |
| **JADX** | APK decompilation to Java source | `analysis_workflow.py` | [github.com/skylot/jadx](https://github.com/skylot/jadx) |
| **Frida** | Dynamic instrumentation (runtime hooking) | `frida_scripts.py`, `analysis_workflow.py --frida` | `pip install frida-tools` |
| **Android SDK** | Build tools (aapt2, d8, zipalign, apksigner) | Building APKs from generated source | [developer.android.com/studio](https://developer.android.com/studio) |
| **JDK 17+** | Java compilation | Android SDK tools | [adoptium.net](https://adoptium.net/) |
| **Android Emulator or Device** | Running/analyzing APKs | Dynamic analysis | Android Studio AVD or physical device |

**All analysis scripts are designed to degrade gracefully** — if a tool is missing, they print a warning and continue with available functionality. For example, `analysis_workflow.py` will run static analysis on decompiled sources if APKTool/JADX are available, and will skip Frida dynamic analysis if Frida is not installed.

---

### Lab Structure

```
mobile_lab/
├── README.md                  # This file
├── android_setup.sh           # Emulator setup & validation
├── test_app_generator.py      # Vulnerable app generation (source output, no APK compile)
├── frida_scripts.py           # Frida hooking library
└── analysis_workflow.py       # Automated analysis pipeline
```

---

### test_app_generator.py — Source Only (No APK Build)

The `test_app_generator.py` script intentionally produces **source code** rather than compiled APKs. Building APKs requires a full Android SDK (1+ GB), which is too large to include in this educational lab.

**Output structure:**
```
test_apps/
└── com.lab.hardcoded/
    ├── AndroidManifest.xml
    └── src/com/lab/hardcoded/
        └── MainActivity.java
    └── BUILD.md              # Instructions for compiling to APK
```

The generated BUILD.md documents the complete APK build pipeline using standard Android tools. To produce a working APK, install Android Studio and follow the instructions.

---

### Legal Notice

This lab is for **authorized security testing only**. Only test apps you own or have explicit permission to analyze. Unauthorized access to systems is illegal.
