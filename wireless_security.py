#!/usr/bin/env python3
"""Wireless Security Framework — pure stdlib (Windows netsh + PowerShell)."""

from __future__ import annotations

import json
import re
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class WifiNetwork:
    ssid: str; bssid: str; signal: int; channel: int; band: str
    encryption: str; auth: str; vendor: str = "Unknown"
    is_rogue: bool = False; risk: str = "unknown"
    first_seen: str = ""; last_seen: str = ""

@dataclass
class BluetoothDevice:
    name: str; mac: str; rssi: int; device_class: str
    connected: bool; remembered: bool; authenticated: bool
    vendor: str = "Unknown"; risk: str = "unknown"; last_seen: str = ""

@dataclass
class RFReading:
    frequency_mhz: float; power_dbm: float; noise_floor_dbm: float
    snr_db: float; source: str; band: str; timestamp: str = ""

@dataclass
class AttackEvent:
    timestamp: str; attack_type: str; severity: str
    source_mac: str; target_ssid: str; description: str; recommendation: str

@dataclass
class SecurityReport:
    timestamp: str; duration_sec: float
    wifi_networks: list = field(default_factory=list)
    bluetooth_devices: list = field(default_factory=list)
    rf_readings: list = field(default_factory=list)
    attacks: list = field(default_factory=list)
    findings: list = field(default_factory=list)
    score: int = 100

    def summary(self) -> str:
        L = ["=" * 70, "WIRELESS SECURITY REPORT", "=" * 70,
             f"Timestamp : {self.timestamp}", f"Duration  : {self.duration_sec:.1f}s",
             f"Score     : {self.score}/100", "",
             f"WiFi networks found   : {len(self.wifi_networks)}",
             f"Bluetooth devices     : {len(self.bluetooth_devices)}",
             f"RF readings           : {len(self.rf_readings)}",
             f"Attack events detected: {len(self.attacks)}", ""]
        if self.findings:
            L.append("KEY FINDINGS:")
            L.extend(f"  - {f}" for f in self.findings)
        if self.attacks:
            L.append("\nATTACKS:")
            for a in self.attacks:
                L.append(f"  [{a.severity.upper()}] {a.attack_type}: {a.description}")
        L.append("=" * 70)
        return "\n".join(L)


def _run(cmd: list[str], timeout: int = 15) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout + r.stderr
    except Exception as e:
        return f"<error: {e}>"

def _ps(script: str) -> str:
    return _run(["powershell", "-NoProfile", "-Command", script])

def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _parse_wifi(raw: str) -> list[WifiNetwork]:
    nets: list[WifiNetwork] = []
    cur: dict = {}
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("SSID"):
            if cur.get("ssid") and cur.get("bssid"):
                nets.append(WifiNetwork(**cur))
            cur = {"ssid": line.split(":", 1)[-1].strip(), "bssid": "",
                   "signal": 0, "channel": 0, "band": "2.4 GHz",
                   "encryption": "", "auth": "",
                   "first_seen": _now(), "last_seen": _now()}
        elif line.startswith("BSSID"):
            cur["bssid"] = line.split(":", 1)[-1].strip()
        elif "Signal" in line and ":" in line:
            m = re.search(r"(\d+)%", line)
            if m:
                cur["signal"] = int(m.group(1))
        elif "Channel" in line and ":" in line:
            m = re.search(r"(\d+)", line.split(":", 1)[-1])
            if m:
                n = int(m.group(1)); cur["channel"] = n
                cur["band"] = "6 GHz" if n > 100 else ("5 GHz" if n > 14 else "2.4 GHz")
        elif "Authentication" in line and ":" in line:
            cur["auth"] = line.split(":", 1)[-1].strip()
        elif "Encryption" in line and ":" in line:
            cur["encryption"] = line.split(":", 1)[-1].strip()
    if cur.get("ssid") and cur.get("bssid"):
        nets.append(WifiNetwork(**cur))
    return nets


def _parse_bt(raw: str) -> list[BluetoothDevice]:
    devs: list[BluetoothDevice] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("Status") or line.startswith("Class"):
            continue
        p = re.split(r"\s{2,}", line)
        if len(p) >= 4:
            mac = p[1] if ":" in p[1] else "00:00:00:00:00:00"
            devs.append(BluetoothDevice(
                name=p[0], mac=mac, rssi=0, device_class=p[3] if len(p) > 3 else "Unknown",
                connected=p[2].lower() == "ok", remembered=False,
                authenticated=False, last_seen=_now()))
    return devs


class WiFiScanner:
    VENDOR_OUI = {"00:0C:42": "Ruckus", "00:1A:1E": "Aruba",
                  "00:50:F2": "Microsoft", "C8:D7:19": "Cisco",
                  "F8:1A:67": "TP-Link", "A4:CF:12": "Espressif",
                  "DC:A6:32": "Raspberry Pi", "B8:27:EB": "Raspberry Pi"}

    def scan(self) -> list[WifiNetwork]:
        raw = _run(["netsh", "wlan", "show", "networks", "mode=bssid"])
        nets = _parse_wifi(raw)
        for n in nets:
            n.vendor = self.VENDOR_OUI.get(n.bssid.upper()[:8], "Unknown")
            n.risk = self._risk(n)
        return nets

    def _risk(self, n: WifiNetwork) -> str:
        e = n.encryption.upper()
        if not n.encryption or n.encryption.lower() == "none":
            return "high"
        if "WEP" in e:
            return "high"
        if "WPA3" in e:
            return "low"
        if "WPA2" in e:
            return "low" if "ENTERPRISE" in n.auth.upper() else "medium"
        return "medium"

    def detect_rogue(self, networks: list[WifiNetwork],
                     known: set[str]) -> list[AttackEvent]:
        events: list[AttackEvent] = []
        for n in networks:
            if n.ssid not in known:
                n.is_rogue = True
                events.append(AttackEvent(
                    _now(), "ROGUE_AP", "medium", n.bssid, n.ssid,
                    f"Unknown SSID \'{n.ssid}\' broadcasting",
                    "Verify SSID with network owner."))
        by_ssid: dict[str, list[WifiNetwork]] = {}
        for n in networks:
            by_ssid.setdefault(n.ssid, []).append(n)
        for ssid, grp in by_ssid.items():
            if len({n.encryption for n in grp}) > 1:
                for n in grp:
                    n.is_rogue = True
                events.append(AttackEvent(
                    _now(), "EVIL_TWIN", "high", grp[0].bssid, ssid,
                    f"SSIDs \'{ssid}\' with differing encryption",
                    "Investigate immediately — possible evil-twin attack."))
        return events


class BluetoothEnumerator:
    BT_CLASSES = {"0x000100": "Computer", "0x000104": "Desktop",
                  "0x000200": "Phone", "0x000204": "Cellular", "0x000208": "Smartphone",
                  "0x000400": "Audio/Video", "0x000404": "Microphone",
                  "0x000408": "Headset", "0x000414": "Headphones",
                  "0x000500": "Peripheral", "0x000540": "Keyboard",
                  "0x000580": "Mouse", "0x0005c0": "Combo"}

    def enumerate(self) -> list[BluetoothDevice]:
        script = ("Get-PnpDevice -Class Bluetooth -Status OK | "
                  "Select-Object FriendlyName,InstanceId,Status | "
                  "Format-Table -AutoSize -Wrap")
        devs = _parse_bt(_ps(script))
        for d in devs:
            d.device_class = self.BT_CLASSES.get(d.device_class, d.device_class or "Unknown")
            if not d.connected and "Unknown" in d.name:
                d.risk = "medium"
            elif "Keyboard" in d.device_class or "Mouse" in d.device_class:
                d.risk = "low"
            else:
                d.risk = "low"
        return devs


class RFAnalyser:
    FREQ = {1: 2412, 2: 2417, 3: 2422, 4: 2427, 5: 2432, 6: 2437,
            7: 2442, 8: 2447, 9: 2452, 10: 2457, 11: 2462, 12: 2467,
            13: 2472, 14: 2484, 36: 5180, 40: 5200, 44: 5220, 48: 5240,
            52: 5260, 56: 5280, 60: 5300, 64: 5320, 100: 5500, 104: 5520,
            108: 5540, 112: 5560, 116: 5580, 120: 5600, 124: 5620, 128: 5640,
            132: 5660, 136: 5680, 140: 5700, 144: 5720, 149: 5745, 153: 5765,
            157: 5785, 161: 5805, 165: 5825}

    def __init__(self, noise_floor: float = -95.0):
        self.noise_floor = noise_floor

    def analyse(self, nets: list[WifiNetwork]) -> list[RFReading]:
        out: list[RFReading] = []
        for n in nets:
            freq = self.FREQ.get(n.channel, 0)
            pwr = -100 + n.signal * 0.9
            out.append(RFReading(freq, round(pwr, 1), self.noise_floor,
                                 round(pwr - self.noise_floor, 1),
                                 n.ssid, n.band, _now()))
        return out

    def interference_score(self, readings: list[RFReading]) -> float:
        if not readings:
            return 0.0
        return round(sum(1 for r in readings if r.snr_db < 20) / len(readings), 2)


class AttackDetector:
    def __init__(self):
        self._deauth: dict[str, int] = {}

    def detect(self, nets: list[WifiNetwork], bt: list[BluetoothDevice],
               rogue: list[AttackEvent]) -> list[AttackEvent]:
        events = list(rogue)
        events.extend(self._deauth_check(nets))
        events.extend(self._bt_anomaly(bt))
        events.extend(self._downgrade(nets))
        return events

    def _deauth_check(self, nets: list[WifiNetwork]) -> list[AttackEvent]:
        ev: list[AttackEvent] = []
        for n in nets:
            if n.signal < 5 and n.encryption == "WPA2":
                self._deauth[n.bssid] = self._deauth.get(n.bssid, 0) + 1
                if self._deauth[n.bssid] >= 3:
                    ev.append(AttackEvent(
                        _now(), "DEAUTH_SUSPECT", "medium", n.bssid, n.ssid,
                        f"{n.ssid} signal collapsed to {n.signal}%",
                        "Check for deauth frames; consider channel change."))
        return ev

    def _bt_anomaly(self, devs: list[BluetoothDevice]) -> list[AttackEvent]:
        ev: list[AttackEvent] = []
        for d in devs:
            if "Unknown" in d.name and not d.authenticated:
                ev.append(AttackEvent(
                    _now(), "BT_UNKNOWN_DEVICE", "low", d.mac, "",
                    f"Unpaired BT device \'{d.name}\' ({d.device_class})",
                    "Verify device legitimacy; remove if unknown."))
        return ev

    def _downgrade(self, nets: list[WifiNetwork]) -> list[AttackEvent]:
        ev: list[AttackEvent] = []
        for n in nets:
            if n.encryption.lower() == "none" and n.signal > 50:
                ev.append(AttackEvent(
                    _now(), "ENCRYPTION_DOWNGRADE", "critical", n.bssid, n.ssid,
                    f"{n.ssid} broadcasting OPEN with strong signal",
                    "Disconnect immediately; possible honeypot/rogue AP."))
        return ev


class ReportGenerator:
    @staticmethod
    def generate(report: SecurityReport, out_dir: str = ".") -> tuple[str, str]:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        jp = out / f"wireless_report_{ts}.json"
        tp = out / f"wireless_report_{ts}.txt"
        data = {"timestamp": report.timestamp, "score": report.score,
                "duration_sec": report.duration_sec,
                "wifi_networks": [asdict(n) for n in report.wifi_networks],
                "bluetooth_devices": [asdict(d) for d in report.bluetooth_devices],
                "rf_readings": [asdict(r) for r in report.rf_readings],
                "attacks": [asdict(a) for a in report.attacks],
                "findings": report.findings}
        jp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tp.write_text(report.summary(), encoding="utf-8")
        return str(jp), str(tp)


class WirelessSecurityFramework:
    def __init__(self, noise_floor: float = -95.0):
        self.wifi = WiFiScanner()
        self.bt = BluetoothEnumerator()
        self.rf = RFAnalyser(noise_floor)
        self.detector = AttackDetector()
        self.reports = ReportGenerator()
        self.known: set[str] = set()

    def run(self, out_dir: str = ".",
            known_ssids: Optional[list[str]] = None) -> SecurityReport:
        t0 = time.time()
        if known_ssids:
            self.known = set(known_ssids)

        print("[*] Scanning WiFi...")
        nets = self.wifi.scan()
        print(f"    {len(nets)} networks found")

        print("[*] Enumerating Bluetooth...")
        bt_devs = self.bt.enumerate()
        print(f"    {len(bt_devs)} devices found")

        print("[*] RF analysis...")
        readings = self.rf.analyse(nets)
        interference = self.rf.interference_score(readings)
        print(f"    {len(readings)} readings; interference={interference}")

        print("[*] Attack detection...")
        rogues = self.wifi.detect_rogue(nets, self.known)
        attacks = self.detector.detect(nets, bt_devs, rogues)
        print(f"    {len(attacks)} attack events")

        findings = self._findings(nets, bt_devs, attacks, interference)
        score = self._score(nets, attacks, interference)

        report = SecurityReport(_now(), time.time() - t0, nets, bt_devs,
                                readings, attacks, findings, score)

        jp, tp = self.reports.generate(report, out_dir)
        print(f"\n[+] JSON: {jp}")
        print(f"[+] Text: {tp}\n")
        print(report.summary())
        return report

    def _findings(self, nets, bt_devs, attacks, interference) -> list[str]:
        f: list[str] = []
        op = [n for n in nets if not n.encryption or n.encryption.lower() == "none"]
        if op:
            f.append(f"{len(op)} open WiFi networks (rogue risk)")
        wk = [n for n in nets if n.signal < 20]
        if wk:
            f.append(f"{len(wk)} very weak signals (possible deauth)")
        rg = [n for n in nets if n.is_rogue]
        if rg:
            f.append(f"{len(rg)} rogue/unknown APs flagged")
        ub = [d for d in bt_devs if "Unknown" in d.name]
        if ub:
            f.append(f"{len(ub)} unpaired Bluetooth devices")
        if interference > 0.5:
            f.append(f"High RF interference ({interference})")
        if attacks:
            sevs = {a.severity for a in attacks}
            if "critical" in sevs:
                f.append("CRITICAL: active attack indicators!")
            elif "high" in sevs:
                f.append("HIGH severity attack indicators detected")
        return f or ["No significant threats detected"]

    def _score(self, nets, attacks, interference) -> int:
        s = 100
        for n in nets:
            s -= 10 if n.risk == "high" else (4 if n.risk == "medium" else 0)
        for a in attacks:
            s -= {"low": 5, "medium": 15, "high": 25, "critical": 40}[a.severity]
        s -= int(interference * 20)
        return max(0, min(100, s))


def main():
    import argparse
    p = argparse.ArgumentParser(description="Wireless Security Framework")
    p.add_argument("--out", default=".", help="Output directory")
    p.add_argument("--known-ssid", nargs="*", default=[], help="Known-good SSIDs")
    p.add_argument("--noise-floor", type=float, default=-95.0, help="Noise floor dBm")
    args = p.parse_args()
    WirelessSecurityFramework(args.noise_floor).run(args.out, args.known_ssid)


if __name__ == "__main__":
    main()
