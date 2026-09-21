#!/usr/bin/env python3
"""
farm_master.py — Master farm controller.
Usage: python farm_master.py [status|search|tcgp|outpost|monitor|full]
"""
import subprocess, json, time, os
from pathlib import Path

FARM = Path(r"C:\Users\mobil\orca\projects\my 1st\farm_3phones")
ADB = r"C:\Users\mobil\AppData\Local\Microsoft\WinGet\Packages\Google.PlatformTools_Microsoft.Winget.Source_8wekyb3d8bbwe\platform-tools\adb.exe"
SCPY = r"C:\Users\mobil\AppData\Local\Microsoft\WinGet\Packages\Genymobile.scrcpy_Microsoft.Winget.Source_8wekyb3d8bbwe\scrcpy-win64-v4.1\scrcpy.exe"

PHONES = {
    "phone-01": {"serial": "192.168.1.157:45313", "role": "tcgp + outpost"},
    "phone-03": {"serial": "192.168.1.158:40489", "role": "tcgp + mintpull"},
}

def adb(serial, *args):
    return subprocess.run([ADB, "-s", serial] + list(args), capture_output=True, text=True)

def adb_shell(serial, cmd):
    return adb(serial, "shell", cmd)

def status():
    print("\n=== FARM STATUS ===")
    for name, info in PHONES.items():
        batt = adb_shell(info["serial"], "dumpsys battery | grep 'level:'").stdout.strip()
        act = adb_shell(info["serial"], "dumpsys activity activities | grep topResumedActivity").stdout.strip()
        proxy = adb_shell(info["serial"], "settings get global http_proxy").stdout.strip()
        print(f"{name} ({info['role']}):")
        print(f"  Battery: {batt.split(':')[-1] if batt else '?'}%")
        print(f"  Activity: {act.split('/')[-1].split()[0] if act else '?'}")
        print(f"  Proxy: {proxy}")

def monitor():
    print("\n=== LAUNCHING MONITORS ===")
    for name, info in PHONES.items():
        subprocess.Popen([SCPY, "-s", info["serial"], "--window-title", name, "--max-fps=30", "--no-audio"])
        print(f"  {name} monitor launched")

def full():
    status()
    time.sleep(1)
    monitor()
    print("\nFarm armed.")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["status","tcgp","outpost","monitor","full"])
    args = p.parse_args()
    if args.cmd == "status": status()
    elif args.cmd == "monitor": monitor()
    elif args.cmd == "full": full()
