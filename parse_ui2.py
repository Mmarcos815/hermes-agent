import subprocess, os, time

ADB = r"C:/Users/mobil/AppData/Local/Microsoft/WinGet/Packages/Google.PlatformTools_Microsoft.Winget.Source_8wekyb3d8bbwe/platform-tools/adb.exe"
SERIAL = "192.168.1.157:45313"
W_DIR = r"C:/Users/mobil/orca/projects/my 1st"

def adb(*args):
    cmd = [ADB, "-s", SERIAL] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    return r.stdout, r.stderr, r.returncode

# Force stop then start fresh
print("Stopping PCAPdroid...")
adb("shell", "am", "force-stop", "com.emanuelef.remote_capture")
time.sleep(1)

print("Starting PCAPdroid...")
out, err, rc = adb("shell", "am", "start", "-a", "android.intent.action.MAIN",
                   "-n", "com.emanuelef.remote_capture/.ui.MainActivity")
print("start:", out.strip(), err[:100] if err else "")

# Wait for activity to settle
print("Waiting 4s for UI to settle...")
time.sleep(4)

# Dump UI
print("Dumping UI...")
out, err, rc = adb("shell", "uiautomator", "dump", "/sdcard/uiauto2.xml")
print("dump rc:", rc, out.strip()[:200])

# Pull
xml_dest = os.path.join(W_DIR, "farm_3phones", "uiauto2.xml")
pull_out, pull_err, _ = adb("pull", "/sdcard/uiauto2.xml", xml_dest)
print("pull rc:", _)

if os.path.exists(xml_dest):
    with open(xml_dest, "r", encoding="utf-8", errors="replace") as f:
        xml = f.read()
    print(f"XML size: {len(xml)} bytes")
    # Extract package name hint
    pkgs = set(re.findall(r'package="([^"]*)"', xml))
    print("Packages in view:", pkgs)
    # Extract all text nodes
    import re as re_mod
    texts = [m.group(1) for m in re_mod.finditer(r'<node[^>]*text="([^"]*)"', xml)]
    non_empty = [t for t in texts if t.strip()]
    print(f"\n=== {len(non_empty)} text elements ===")
    for t in non_empty:
        print(repr(t))
    # Also look for clickable nodes with text
    clickables = re_mod.findall(r'<node[^>]*clickable="true"[^>]*text="([^"]*)"[^>]*resource-id="([^"]*)"', xml)
    print(f"\n=== {len(clickables)} clickable nodes ===")
    for txt, rid in clickables:
        if txt.strip():
            print(f"  {rid}: {txt}")
else:
    print("XML not found")
