---
name: mobile-security
description: Tier 6 Mobile Security skill set. Use when analyzing Android APKs, iOS apps, mobile security vulnerabilities, or performing mobile penetration testing.
---

# Tier 6: Mobile Security

## Overview

This skill covers mobile application security for both Android and iOS platforms:

1. **Android Security** — APK analysis, manifest parsing, permission auditing, hardcoded secrets detection
2. **iOS Security** — plist parsing, binary analysis, entitlements review, secure storage audit
3. **Mobile Common** — WebView risks, certificate pinning bypass, local storage, IPC attacks

## Tools

| Tool | Purpose |
|------|---------|
| `apk_analyzer.py` | APK security analysis (manifest, secrets, permissions) |
| `plist_parser.py` | iOS plist security analysis |

## Usage

```bash
# APK analysis
python apk_analyzer.py --apk app.apk --manifest
python apk_analyzer.py --apk app.apk --secrets
python apk_analyzer.py --apk app.apk --permissions
python apk_analyzer.py --apk app.apk --full-report

# iOS plist analysis
python plist_parser.py --file Info.plist --security
python plist_parser.py --file Info.plist --all
python plist_parser.py --dir /path/to/app --scan
```

## Key Concepts

### Android Security
- **APK Structure**: DEX files, resources, native libraries, assets
- **Manifest Analysis**: Permissions, components, exported activities
- **Hardcoded Secrets**: API keys, tokens, credentials in source
- **Dangerous Permissions**: SMS, CALL, SYSTEM_ALERT_WINDOW, BIND_DEVICE_ADMIN
- **WebView Risks**: JavaScript enabled, file access, addJavascriptInterface

### iOS Security
- **plist Security**: ATS settings, URL schemes, entitlements, NSAppTransportSecurity
- **Binary Analysis**: PIE, stack canaries, ARC, encrypted binaries
- **Secure Storage**: Keychain, UserDefaults, Core Data encryption
- **IPC Risks**: URL handlers, App Groups, pasteboard security

### Mobile Common
- **Certificate Pinning**: Implementation review, bypass detection
- **Local Storage**: SQLite, SharedPreferences, plist files
- **IPC Attacks**: Intent hijacking, deep link abuse
- **OWASP Mobile Top 10**: Comprehensive coverage

## Safety & Ethics

All tools are for **authorized testing and educational purposes only**. Unauthorized access to computer systems is illegal. Always obtain proper authorization before testing.
