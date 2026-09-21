import subprocess, json, re, os

ADB = "C:/Users/mobil/AppData/Local/Microsoft/WinGet/Packages/Google.PlatformTools_Microsoft.Winget.Source_8wekyb3d8bbwe/platform-tools/adb.exe"
SERIAL = "192.168.1.157:45313"

def adb(*args):
    cmd = [ADB, "-s", SERIAL] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return r.stdout.strip(), r.stderr.strip(), r.returncode

print("=== Script starting ===")
out, err, rc = adb("shell", "uiautomator", "dump", "/sdcard/uiauto.xml")
print("dump rc:", rc, "stdout:", out[:200])
print("dump stderr:", err[:200] if err else "none")

W_DIR = "C:/Users/mobil/orca/projects/my 1st"
pull_out, pull_err, _ = adb("pull", "/sdcard/uiauto.xml", os.path.join(W_DIR, "farm_3phones", "uiauto.xml"))
print("pull rc:", _, "pull_out:", pull_out[:200])

xml_path = os.path.join(W_DIR, "farm_3phones", "uiauto.xml")
if os.path.exists(xml_path):
    with open(xml_path, "r", encoding="utf-8", errors="replace") as f:
        xml = f.read()
    print(f"\n=== XML size: {len(xml)} bytes ===")
    # Parse for text content
    texts = re.findall(r'<node[^>]*text="([^"]*)"[^>]*>', xml)
    print(f"\n--- All text attributes ({len(texts)}) ---")
    for t in texts[:80]:
        if t.strip():
            print(t)
    # Also find class+text pairs for key widgets
    nodes = re.findall(r'<node[^>]*package="([^"]*)"[^>]*class="([^"]*)"[^>]*text="([^"]*)"', xml)
    print(f"\n--- Nodes with class+text ({len(nodes)}) ---")
    for pkg, cls, txt in nodes[:40]:
        if txt.strip():
            print(f"{pkg}.{cls}: {txt}")
else:
    print("XML file not found at", xml_path)
