#!/usr/bin/env python3
"""
DAD's Bionic Farm — Unified Android Automation Framework
Eliminates touch latency, fixes vision drops, automates power state, stabilizes multi-device loops.
"""
import subprocess, time, json, os, sys
from pathlib import Path
from datetime import datetime
import cv2
import numpy as np

# ─── CONFIG ────────────────────────────────────────────────────────────────
WORKSPACE = Path(r"C:\Users\mobil\orca\projects\my 1st\farm_3phones")
ADB = r"C:\Users\mobil\AppData\Local\Microsoft\WinGet\Packages\Google.PlatformTools_Microsoft.Winget.Source_8wekyb3d8bbwe\platform-tools\adb.exe"
SCPY = r"C:\Users\mobil\AppData\Local\Microsoft\WinGet\Packages\Genymobile.scrcpy_Microsoft.Winget.Source_8wekyb3d8bbwe\scrcpy-win64-v4.1\scrcpy.exe"

PHONES = {
    "phone-01": {"serial": "192.168.1.157:45313", "role": "tcgp + outpost", "batt": 94},
    "phone-03": {"serial": "192.168.1.158:40489", "role": "tcgp + mintpull", "batt": 92},
}

# ─── ADB WRAPPER ──────────────────────────────────────────────────────────
def adb(serial, *args, timeout=30):
    """Run ADB command on specific device."""
    cmd = [ADB, "-s", serial] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.returncode

def adb_shell(serial, cmd, timeout=30):
    """Run shell command on device."""
    return adb(serial, "shell", cmd, timeout=timeout)

# ─── POWER MANAGEMENT ─────────────────────────────────────────────────────
def keep_awake(serial):
    """Prevent screen from sleeping during automation."""
    adb_shell(serial, "settings put system screen_off_timeout 600000")
    adb_shell(serial, "svc power stayon true")
    adb_shell(serial, "input keyevent KEYCODE_WAKEUP")

def get_battery(serial):
    """Get battery level from dumpsys output."""
    out, _ = adb_shell(serial, "dumpsys battery")
    for line in out.split('\n'):
        line = line.strip()
        if line.startswith('level:'):
            try:
                return int(line.split(':')[1].strip())
            except:
                return -1
    return -1

def is_charging(serial):
    """Check if device is charging."""
    out, _ = adb_shell(serial, "dumpsys battery | grep AC")
    return "true" in out.lower()

# ─── UI AUTOMATION (uiautomator2) ────────────────────────────────────────
import uiautomator2 as u2

class Device:
    """Wrapper for a single phone with u2 automation."""
    
    def __init__(self, name, serial):
        self.name = name
        self.serial = serial
        self.d = u2.connect(serial)
        self.d.implicitly_wait(10.0)
        self.d.settings["wait_timeout"] = 10.0
        self.d.settings["operation_delay"] = (0.1, 0.3)
        
    def wake(self):
        """Wake and unlock device."""
        self.d.screen_on()
        self.d.swipe(0.5, 0.8, 0.5, 0.3, 0.3)
        time.sleep(0.5)
        
    def launch(self, package):
        """Launch app and wait."""
        self.d.app_start(package, use_monkey=True)
        time.sleep(8)  # Unity boot time
        
    def stop(self, package):
        """Force stop app."""
        self.d.app_stop(package)
        
    def tap_xy(self, x, y):
        """Tap at coordinates."""
        self.d.click(x, y)
        
    def tap_text(self, text):
        """Tap element by text."""
        self.d(text=text).click()
        
    def tap_desc(self, desc):
        """Tap element by content-desc."""
        self.d(description=desc).click()
        
    def find(self, text=None, desc=None, resource_id=None):
        """Find element, return None if not found."""
        try:
            if text:
                el = self.d(text=text)
            elif desc:
                el = self.d(description=desc)
            elif resource_id:
                el = self.d(resourceId=resource_id)
            else:
                return None
            return el if el.exists else None
        except:
            return None
            
    def wait_for(self, text=None, desc=None, timeout=15):
        """Wait for element to appear."""
        start = time.time()
        while time.time() - start < timeout:
            el = self.find(text=text, desc=desc)
            if el:
                return el
            time.sleep(0.5)
        return None
        
    def screenshot(self, filename=None):
        """Take screenshot and save."""
        if not filename:
            filename = f"{self.name}_{datetime.now().strftime('%H%M%S')}.png"
        path = WORKSPACE / filename
        self.d.screenshot(str(path))
        return path
        
    def swipe(self, x1, y1, x2, y2, duration=0.3):
        """Swipe gesture."""
        self.d.swipe(x1, y1, x2, y2, duration)
        
    def trace_line(self, y=1040):
        """Trace the TCGP pack opening line."""
        # Fast swipe across the pack
        self.d.swipe(50, y, 1030, y, 0.05)
        time.sleep(0.5)
        
    def get_activity(self):
        """Get current foreground activity."""
        out, _ = adb_shell(self.serial, "dumpsys activity activities | grep topResumedActivity")
        return out.split("/")[-1].split()[0] if "/" in out else "unknown"

# ─── SCRCOPY LAUNCHER ────────────────────────────────────────────────────
def launch_scrcpy(serial, title=None):
    """Launch scrcpy for visual monitoring."""
    if not title:
        title = f"Farm-{serial.split(':')[1]}"
    cmd = [SCPY, "-s", serial, "--window-title", title, "--max-fps=60", "--no-audio"]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# ─── TCGP AUTOMATION ──────────────────────────────────────────────────────
TCGP_PKG = "jp.pokemon.pokemontcgp"

def tcgp_pull_pack(device: Device):
    """Full TCGP pack opening flow."""
    results = []
    
    # 1. Launch TCGP
    device.launch(TCGP_PKG)
    
    # 2. Wait for main menu, tap pack
    # Look for pack stamina notification or pack area
    time.sleep(3)
    
    # 3. Tap center pack (Mewtwo)
    device.tap_xy(540, 700)
    time.sleep(2)
    
    # 4. Tap "Open" button
    device.tap_xy(540, 1400)
    time.sleep(3)
    
    # 5. Handle cooldown modal if present
    ok_btn = device.find(text="OK")
    if ok_btn:
        ok_btn.click()
        time.sleep(2)
    
    # 6. Trace line to open pack
    device.trace_line(1040)
    time.sleep(5)
    
    # 7. Handle "Pick a card" screen
    pick = device.wait_for(text="Pick a card", timeout=10)
    if pick:
        device.tap_xy(540, 900)  # Tap center card
        time.sleep(3)
    
    # 8. Reveal loop — tap Next until back to main
    for _ in range(10):
        next_btn = device.find(text="Next")
        if next_btn:
            next_btn.click()
            time.sleep(2)
        else:
            break
    
    return results

# ─── OUTPOST AUTOMATION ──────────────────────────────────────────────────
OUTPOST_PKG = "com.cardoutpost.app"

def outpost_free_pulls(device: Device):
    """Claim Outpost free daily pulls."""
    device.launch(OUTPOST_PKG)
    time.sleep(5)
    
    # Look for free pull buttons
    free_btn = device.find(text="Free") or device.find(text="Claim")
    if free_btn:
        free_btn.click()
        time.sleep(3)
    
    # Dismiss any popups
    close_btn = device.find(text="CLOSE") or device.find(text="Close")
    if close_btn:
        close_btn.click()

# ─── MAIN ORCHESTRATOR ───────────────────────────────────────────────────
class FarmOrchestrator:
    """Manages multi-device automation."""
    
    def __init__(self):
        self.devices = {}
        for name, info in PHONES.items():
            try:
                dev = Device(name, info["serial"])
                self.devices[name] = dev
                print(f"[OK] {name} connected")
            except Exception as e:
                print(f"[FAIL] {name}: {e}")
    
    def status(self):
        """Print farm status."""
        for name, dev in self.devices.items():
            batt = get_battery(dev.serial)
            activity = dev.get_activity()
            print(f"{name}: batt={batt}% activity={activity}")
    
    def run_tcgp_cycle(self):
        """Run TCGP pack opening on all devices."""
        for name, dev in self.devices.items():
            print(f"\n[{name}] Starting TCGP pull cycle...")
            try:
                keep_awake(dev.serial)
                tcgp_pull_pack(dev)
                print(f"[{name}] TCGP cycle complete")
            except Exception as e:
                print(f"[{name}] ERROR: {e}")
    
    def run_outpost_cycle(self):
        """Run Outpost free pulls on phone-01."""
        if "phone-01" in self.devices:
            dev = self.devices["phone-01"]
            print(f"\n[phone-01] Outpost free pulls...")
            try:
                outpost_free_pulls(dev)
            except Exception as e:
                print(f"[phone-01] Outpost ERROR: {e}")
    
    def monitor(self):
        """Launch scrcpy for all devices."""
        for name, info in PHONES.items():
            launch_scrcpy(info["serial"], name)
            time.sleep(1)

# ─── ENTRY POINT ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="DAD's Bionic Farm Controller")
    parser.add_argument("command", choices=["status", "tcgp", "outpost", "monitor", "full"],
                       help="Command to run")
    args = parser.parse_args()
    
    farm = FarmOrchestrator()
    
    if args.command == "status":
        farm.status()
    elif args.command == "tcgp":
        farm.run_tcgp_cycle()
    elif args.command == "outpost":
        farm.run_outpost_cycle()
    elif args.command == "monitor":
        farm.monitor()
    elif args.command == "full":
        farm.monitor()
        time.sleep(2)
        farm.run_tcgp_cycle()
        farm.run_outpost_cycle()
        farm.status()
