#!/usr/bin/env python3
"""
Launch Rip Rush (com.emeraldmyth.riprush.and) via Frida spawn with universal SSL
pinning bypass, then snapshot the phone + check mitmweb traffic. Leaves the app
running with hooks active after frida detaches.
"""
import subprocess
import os
import sys
import time
import signal

HERE = os.path.dirname(os.path.abspath(__file__))
FRIDA = r"C:\Users\mobil\AppData\Local\hermes\hermes-agent\venv\Scripts\frida.exe"
JS   = os.path.join(HERE, "frida_ssl_bypass.js")
LOG  = os.path.join(HERE, "frida_riprush_out.log")
STDBUF = os.path.join(HERE, "frida_stderr.log")
OUTDIR = r"C:\Users\mobil\orca\projects\my 1st\farm_3phones"

assert os.path.exists(FRIDA), "frida missing: %s" % FRIDA
assert os.path.exists(JS), "bypass JS missing: %s" % JS

for p in (LOG, STDBUF):
    try:
        os.remove(p)
    except FileNotFoundError:
        pass

ADB = (r"C:\Users\mobil\AppData\Local\Microsoft"
       r"\WinGet\Packages\Google.PlatformTools_Microsoft"
       r".Winget.Source_8wekyb3d8bbwe\platform-tools\adb.exe")
SERIAL = "192.168.1.158:35493"
MITM = os.path.join(OUTDIR, "mitmweb.log")

# frida's prompt_toolkit crashes in git-bash/MSYS (NoConsoleScreenBufferError).
# Launch frida inside a real Windows console via cmd.exe /c.
cmd = ["cmd.exe", "/c", FRIDA, "-U", "-f", "com.emeraldmyth.riprush.and", "-l", JS, "-o", LOG]
print("[launch] frida: %s" % " ".join(cmd))
proc = subprocess.Popen(
    cmd,
    stdin=subprocess.DEVNULL,
    stdout=subprocess.DEVNULL,
    stderr=open(STDBUF, "wb"),
)

try:
    for i in range(1, 21):
        time.sleep(1)
        if proc.poll() is not None:
            print("[launch] frida exited at +%ds (rc=%d)" % (i, proc.returncode))
            break
        if i == 5:
            snap = os.path.join(OUTDIR, "phone02_post_spawn.png")
            print("[launch] +%ds — pulling screenshot -> %s" % (i, snap))
            try:
                with open(snap, "wb") as fh:
                    subprocess.run(
                        [ADB, "-s", SERIAL, "exec-out", "screencap", "-p"],
                        stdout=fh, stderr=subprocess.DEVNULL, timeout=20,
                    )
                print("[launch] screenshot: %d bytes" % os.path.getsize(snap))
            except Exception as e:
                print("[launch] screenshot failed: %s" % e)
        if i % 5 == 0:
            print("[launch] +%ds frida alive (poll=%s)" % (i, proc.poll()))
    else:
        print("[launch] +20s frida still alive")
finally:
    print("[launch] detaching frida...")
    proc.terminate()
    try:
        proc.wait(timeout=6)
        print("[launch] frida rc=%s" % proc.returncode)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
        print("[launch] frida killed")

print("\n=== frida stderr (head) ===")
if os.path.exists(STDBUF):
    print(open(STDBUF, "rb").read().decode("utf-8", "replace")[:2500])
else:
    print("(none)")

print("\n=== frida log (tail) ===")
if os.path.exists(LOG):
    print(open(LOG, "r", errors="replace").read()[-1500:])
else:
    print("(none)")

snap = os.path.join(OUTDIR, "phone02_post_spawn.png")
print("\n=== screenshot ===")
print("saved: %s (%d bytes)" % (snap, os.path.getsize(snap))) if os.path.exists(snap) \
    else print("(none)")

print("\n=== mitmweb recent 192.168.1.158 ===")
if os.path.exists(MITM):
    lines = open(MITM, errors="replace").read().splitlines()
    recent = [l for l in lines if "192.168.1.158" in l]
    for l in recent[-12:]:
        print(l)
    failed = sum("failed" in l for l in recent)
    ok = sum("server connect" in l for l in recent) - failed
    print("recent=%d failed=%d ok_connect=%d" % (len(recent), failed, ok))
else:
    print("(none)")
