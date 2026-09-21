#!/usr/bin/env python3
"""Install mitmproxy CA on Phone-02 via Settings UI cert installer."""
import subprocess, sys, time

ADB = (
    "C:/Users/mobil/AppData/Local/Microsoft/WinGet/"
    "Packages/Google.PlatformTools_Microsoft.Winget.Source"
    "_8wekyb3d8bbwe/platform-tools/adb.exe"
)
SERIAL = "192.168.1.158:35493"
SCREENSHOT_OUT = "farm_3phones/cert_install_attempt.png"

print(f"[1] adb binary: {os.path.exists(ADB)}")
print(f"[2] connecting: {SERIAL}")

def run(cmd, timeout=10):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr

# Snapshot the screen first
print("[3] taking pre-install screenshot...")
rc, out, err = run([ADB, "-s", SERIAL, "exec-out", "screencap", "-p"],
                   timeout=10)
if rc == 0 and out:
    with open(SCREENSHOT_OUT, "wb") as f:
        f.write(out.encode("latin-1") if isinstance(out, str) else out)
    print(f"    screenshot: {len(out)} bytes -> {SCREENSHOT_OUT}")
else:
    print(f"    screenshot failed rc={rc}")

# Launch the cert installer via adb shell am start
print("[4] launching cert installer view intent...")
cmd_view = [ADB, "-s", SERIAL, "shell",
            "am start -a android.intent.action.VIEW "
            "-d 'file:///sdcard/Download/mitmproxy-ca-cert.der' "
            "'-t' 'application/x-x509-ca-cert'"]
rc, out, err = run(cmd_view, timeout=15)
print(f"    rc={rc}")
print(f"    stdout: {out.strip()[:200]}")
if err:
    print(f"    stderr: {err.strip()[:200]}")

# Wait for UI to render, then snapshot
print("[5] waiting 4s for UI render...")
time.sleep(4)
rc, out, err = run([ADB, "-s", SERIAL, "exec-out", "screencap", "-p"],
                   timeout=10)
if rc == 0 and out:
    with open(SCREENSHOT_OUT, "wb") as f:
        f.write(out.encode("latin-1") if isinstance(out, str) else out)
    print(f"    screenshot: {len(out)} bytes -> {SCREENSHOT_OUT}")
else:
    print(f"    screenshot failed rc={rc}")

print("[6] done.")
print("    Next step: inspect", SCREENSHOT_OUT, "with vision to see cert installer dialog.")
