#!/usr/bin/env bash
# ==============================================================================
# Phone-02 Focused Setup Script (Galaxy A16)
# Target IP/Port: 192.168.1.158:35493
# ==============================================================================

set -e

echo "[*] Targeting Phone-02 exclusively..."

# 1. Reset ADB and connect directly to Phone-02's active port
adb kill-server
adb start-server
adb connect 192.168.1.158:35493

# 2. Verify connection status for Phone-02
echo "[*] Verifying device connection:"
adb -s 192.168.1.158:35493 get-state

# 3. Set up a dedicated log target for Phone-02 traffic
LOG_DIR="$HOME/.hermes/logs/phone_02"
mkdir -p "$LOG_DIR"
echo "[+] Phone-02 environment initialized. Ready for Frida injection and proxy routing."
