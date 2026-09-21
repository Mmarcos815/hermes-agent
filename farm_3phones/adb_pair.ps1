# Dad 3-phone wireless ADB - no cables
# Run in PowerShell as Admin first time, then git-bash

# 1. Install platform-tools (pick one)
winget install Google.PlatformTools
# fallback portable:
# Invoke-WebRequest -Uri https://dl.google.com/android/repository/platform-tools-latest-windows.zip -OutFile $env:TEMP/platform-tools.zip
# Expand-Archive $env:TEMP/platform-tools.zip -DestinationPath C:/Android -Force

# 2. Verify
adb version
adb devices -l

# 3. Pair each phone - on phone: Dev mode ON (tap Build 7x), Wireless debugging ON, Pair with code
# Phone gives IP:PAIRPORT + 6-digit code, plus separate CONNECT IP:PORT in list
# Run per phone:
# adb pair 192.168.1.101:PAIRPORT 123456
# adb connect 192.168.1.101:5555

# 4. Repeat for .102 .103, then:
adb devices -l
# expect 3x device product:model

# 5. Keep alive + time sync check
# adb -s 192.168.1.101:5555 shell settings get global auto_time
# adb -s 192.168.1.101:5555 shell input tap 500 500
# scrcpy -s 192.168.1.101:5555  # visual per phone, one window each
