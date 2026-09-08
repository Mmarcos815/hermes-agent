#!/bin/bash
# Android Emulator Setup Script for Mobile Security Lab
# Validates environment, installs dependencies, and configures emulator for testing.

set -euo pipefail

echo "=== Mobile Security Lab - Android Setup ==="

# --- Check Prerequisites ---
check_prereqs() {
    echo "[*] Checking prerequisites..."
    
    command -v java >/dev/null 2>&1 || { echo "[!] Java not found. Install JDK 17."; exit 1; }
    java -version 2>&1 | head -1
    
    command -v adb >/dev/null 2>&1 || { echo "[!] ADB not found. Install Android SDK platform-tools."; exit 1; }
    
    command -v emulator >/dev/null 2>&1 || { echo "[!] Emulator not found. Install Android SDK emulator."; exit 1; }
    
    command -v frida >/dev/null 2>&1 || echo "[!] Frida not found. Run: pip install frida-tools"
    
    echo "[+] Core prerequisites verified."
}

# --- Setup Android SDK Paths ---
setup_paths() {
    echo "[*] Configuring Android SDK paths..."
    
    if [ -z "${ANDROID_HOME:-}" ] && [ -z "${ANDROID_SDK_ROOT:-}" ]; then
        # Attempt common paths
        for candidate in "$HOME/Android/Sdk" "$HOME/Library/Android/sdk" "/opt/android-sdk"; do
            if [ -d "$candidate" ]; then
                export ANDROID_HOME="$candidate"
                break
            fi
        done
    fi
    
    export ANDROID_HOME="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}"
    export PATH="$PATH:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$ANDROID_HOME/cmdline-tools/latest/bin"
    
    echo "[+] ANDROID_HOME=$ANDROID_HOME"
}

# --- Install SDK Components ---
install_sdk() {
    echo "[*] Installing SDK components..."
    
    yes | sdkmanager --licenses >/dev/null 2>&1 || true
    sdkmanager "platform-tools" "emulator" "platforms;android-34" "system-images;android-34;google_apis;x86_64" "build-tools;34.0.0"
    
    echo "[+] SDK components installed."
}

# --- Create Emulator AVD ---
create_avd() {
    local avd_name="${1:-security_lab_avd}"
    
    echo "[*] Creating AVD: $avd_name"
    
    if avdmanager list avd | grep -q "$avd_name"; then
        echo "[!] AVD '$avd_name' already exists. Skipping creation."
        return 0
    fi
    
    echo "no" | avdmanager create avd \
        -n "$avd_name" \
        -k "system-images;android-34;google_apis;x86_64" \
        -d pixel_5 \
        --force
    
    echo "[+] AVD '$avd_name' created."
}

# --- Configure Emulator for Security Testing ---
configure_emulator() {
    local avd_name="${1:-security_lab_avd}"
    local config_file="$HOME/android/avds/$avd_name.avd/config.ini"
    
    echo "[*] Configuring emulator for security testing..."
    
    # Common security testing configurations
    cat >> "$config_file" 2>/dev/null <<EOF
hw.ramSize=4096
vm.heapSize=512
disk.dataPartition.size=4G
hw.camera.back=emulated
hw.camera.front=emulated
hw.gps=yes
hw.sensors.proximity=yes
hw.sensors.orientation=yes
hw.sensors.magnetic_field=yes
EOF
    
    echo "[+] Emulator configured with extended sensors and storage."
}

# --- Install Frida Server ---
install_frida_server() {
    local api_level
    api_level=$(adb shell getprop ro.build.version.sdk 2>/dev/null || echo "34")
    
    local arch
    arch=$(adb shell getprop ro.product.cpu.abi 2>/dev/null || echo "x86_64")
    
    echo "[*] Installing Frida server (API $api_level, $arch)..."
    
    local frida_version="16.4.8"
    local server_name="frida-server-${frida_version}-android-${arch}"
    
    curl -L "https://github.com/frida/frida/releases/download/${frida_version}/${server_name}.xz" -o /tmp/frida-server.xz
    unxz /tmp/frida-server.xz
    
    adb push /tmp/frida-server /data/local/tmp/frida-server
    adb shell chmod 755 /data/local/tmp/frida-server
    adb shell "/data/local/tmp/frida-server &" &
    
    echo "[+] Frida server installed and started."
}

# --- Start Emulator ---
start_emulator() {
    local avd_name="${1:-security_lab_avd}"
    
    echo "[*] Starting emulator '$avd_name'..."
    
    emulator -avd "$avd_name" \
        -no-snapshot \
        -gpu swiftshader_indirect \
        -no-audio \
        -partition-size 4096 &
    
    echo "[*] Waiting for device..."
    adb wait-for-device
    adb shell getprop sys.boot_completed
    
    echo "[+] Emulator ready."
}

# --- Main ---
main() {
    local action="${1:-all}"
    local avd_name="${2:-security_lab_avd}"
    
    case "$action" in
        check)    check_prereqs ;;
        paths)    setup_paths ;;
        install)  install_sdk ;;
        create)   create_avd "$avd_name" ;;
        configure) configure_emulator "$avd_name" ;;
        frida)    install_frida_server ;;
        start)    start_emulator "$avd_name" ;;
        all)
            check_prereqs
            setup_paths
            install_sdk
            create_avd "$avd_name"
            configure_emulator "$avd_name"
            start_emulator "$avd_name"
            install_frida_server
            echo "[+] Full setup complete."
            ;;
        *)
            echo "Usage: $0 {check|paths|install|create|configure|frida|start|all} [avd_name]"
            exit 1
            ;;
    esac
}

main "$@"
