#!/usr/bin/env python3
"""
Spawn Rip Rush (com.emeraldmyth.riprush.and) on Phone-02 via Frida Python SDK,
inject universal SSL pinning bypass, wait for the app to initialize, then dump the
frida console output + a phone screenshot + recent mitmweb traffic summary.
"""
import frida
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PHONE = "192.168.1.158:35493"
JS_SRC = r"C:\Users\mobil\orca\projects\my 1st\farm_3phones\frida_ssl_bypass.js"
JS = r"C:\tmp\frida_rp\bypass.js"   # no-space staging copy
SCREENSHOT = r"C:\Users\mobil\orca\projects\my 1st\farm_3phones\phone02_frida_ready.png"
MITMLOG = r"C:\Users\mobil\orca\projects\my 1st\farm_3phones\mitmweb.log"

ADB = (r"C:\Users\mobil\AppData\Local\Microsoft"
       r"\WinGet\Packages\Google.PlatformTools_Microsoft"
       r".Winget.Source_8wekyb3d8bbwe\platform-tools\adb.exe")
SERIAL = PHONE

def adb(*args):
    return subprocess.run([ADB, "-s", SERIAL] + list(args),
                          capture_output=True, text=True, timeout=20)

import subprocess

def shoot():
    p = subprocess.run([ADB, "-s", SERIAL, "exec-out", "screencap", "-p"],
                       capture_output=True, timeout=20)
    with open(SCREENSHOT, "wb") as f:
        f.write(p.stdout)
    return os.path.getsize(SCREENSHOT)

# --- prep: clean log, ensure app not running ---
open(JS, "w").write(open(JS_SRC, encoding="utf-8").read())
print("[init] bypass JS staged at %s (%d bytes)" % (JS, os.path.getsize(JS)))

# stop any running instance so frida can spawn fresh
try:
    adb("shell", "am", "force-stop", "com.emeraldmyth.riprush.and")
    time.sleep(1.5)
except Exception as e:
    print("[init] force-stop warn: %s" % e)

# --- connect to device ---
device = frida.get_usb_device(2)  # 2s timeout
print("[init] connected to %s (%s)" % (device.name, device.id))

# --- spawn the app, inject the bypass ---
with open(JS, encoding="utf-8") as fh:
    script_content = fh.read()

print("[spawn] launching Rip Rush with SSL bypass...")
session = device.spawn(["com.emeraldmyth.riprush.and"])

try:
    session.load_script(script_content)
    session.resume()
    print("[spawn] injected + resumed")
except Exception as e:
    print("[spawn] inject/resume failed: %s" % e)
    try:
        session.kill()
    except Exception:
        pass
    sys.exit(1)

# --- give the Unity app time to boot (Cold launch ~7s observed) ---
print("[wait] giving app time to initialize (12s)...")
deadline = time.time() + 12
while time.time() < deadline:
    time.sleep(1)
    if session.is_detached:
        print("[wait] session detached early")
        break

# --- snapshot the phone ---
try:
    sz = shoot()
    print("[phone] screenshot: %d bytes -> %s" % (sz, SCREENSHOT))
except Exception as e:
    print("[phone] screenshot failed: %s" % e)

# --- dump frida script output (the [BYPASS] lines) ---
def dump_log(path, n=60):
    if not os.path.exists(path):
        print("(no %s)" % path)
        return
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    print("=== %s (%d lines) ===" % (os.path.basename(path), len(lines)))
    for ln in lines[-n:]:
        print(ln)

print("\n=== frida stdio.log (tail) ===")
dump_log(r"C:\tmp\frida_rp\stdio.log")
print("\n=== app stderr (head) ===")
dump_log(r"C:\tmp\frida_rp\stdio.log", 30)

# --- mitmweb traffic from phone-02 since spawn ---
def mitm_summary():
    if not os.path.exists(MITMLOG):
        print("(no mitmweb.log)")
        return
    before = time.time() - 30  # last 30s
    lines = []
    with open(MITMLOG, encoding="utf-8", errors="replace") as f:
        for ln in f:
            if "192.168.1.158" in ln:
                lines.append(ln.rstrip("\n"))
    failed = sum("failed" in ln for ln in lines)
    ok = sum("server connect" in ln and "failed" not in ln for ln in lines)
    print("\n=== mitmweb from %s (last 30s): %d lines, failed=%d, ok=%d ==="
          % (PHONE, len(lines), failed, ok))
    for ln in lines[-15:]:
        print(ln)

mitm_summary()

print("\n[done] Rip Rush should be running with SSL bypass active.")
print("       mitmweb dashboard: http://127.0.0.1:8082")
