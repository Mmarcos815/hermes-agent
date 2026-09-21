#!/usr/bin/env python3
"""Spawn Rip Rush on Phone-02 via frida SDK + SSL pinning bypass; screenshot + log."""
import frida, os, sys, time, subprocess

ADB = (r"C:\Users\mobil\AppData\Local\Microsoft"
       r"\WinGet\Packages\Google.PlatformTools_Microsoft"
       r".Winget.Source_8wekyb3d8bbwe\platform-tools\adb.exe")
SERIAL = "192.168.1.158:35493"
Bypass_SRC = (r"C:\Users\mobil\orca\projects\my 1st"
              r"\farm_3phones\frida_ssl_bypass.js")
Bypass = r"C:\tmp\frida_rp\bypass.js"
OUTLOG = r"C:\tmp\frida_rp\app_out.log"
ERRLOG = r"C:\tmp\frida_rp\app_err.log"
SHOT = (r"C:\Users\mobil\orca\projects\my 1st"
        r"\farm_3phones\phone02_frida_ready.png")

# stage bypass at no-space path
os.makedirs(os.path.dirname(Bypass), exist_ok=True)
open(Bypass, "w", encoding="utf-8").write(
    open(Bypass_SRC, encoding="utf-8").read())
print("[1] bypass staged: %s (%d bytes)" % (Bypass, os.path.getsize(Bypass)))

def adb(*a):
    return subprocess.run([ADB, "-s", SERIAL] + list(a),
                          capture_output=True, text=True, timeout=20)

# stop any live instance so spawn works cleanly
print("[2] force-stopping any running Rip Rush...")
adb("shell", "am", "force-stop", "com.emeraldmyth.riprush.and")
time.sleep(1.5)

# connect
device = frida.get_usb_device(2)
print("[3] device: %s [%s]" % (device.name, device.id))

# spawn + inject
with open(Bypass, encoding="utf-8") as f:
    js = f.read()

print("[4] spawning com.emeraldmyth.riprush.and ...")
session = device.spawn(
    ["com.emeraldmyth.riprush.and"],
    stdout=open(OUTLOG, "wb"),
    stderr=open(ERRLOG, "wb"),
)

try:
    session.load_script(js)
    print("[5] bypass injected")
    session.resume()
    print("[6] resumed — app launching")
except Exception as e:
    print("[!] inject failed: %s" % e)
    try:
        session.kill()
    except Exception:
        pass
    sys.exit(1)

# wait for Unity cold boot (~8-12s)
for i in range(1, 13):
    time.sleep(1)
    if session.is_detached:
        print("[!] session detached at +%ds" % i)
        break
    if i % 3 == 0:
        print("[wait] +%ds..." % i)

# screenshot
print("[7] taking phone screenshot...")
p = subprocess.run([ADB, "-s", SERIAL, "exec-out", "screencap", "-p"],
                   capture_output=True, timeout=20)
open(SHOT, "wb").write(p.stdout)
print("[7] screenshot: %d bytes -> %s" % (len(p.stdout), SHOT))

# dump frida console output
print("\n=== frida app_out.log (last 40 lines) ===")
if os.path.exists(OUTLOG):
    lines = open(OUTLOG, encoding="utf-8", errors="replace").read().splitlines()
    print("total lines: %d" % len(lines))
    for ln in lines[-40:]:
        print(ln)
else:
    print("(no out.log)")

print("\n=== frida app_err.log (last 20 lines) ===")
if os.path.exists(ERRLOG):
    lines = open(ERRLOG, encoding="utf-8", errors="replace").read().splitlines()
    print("total lines: %d" % len(lines))
    for ln in lines[-20:]:
        print(ln)

print("\n[done] Rip Rush running with SSL bypass. mitmweb: http://127.0.0.1:8082")
