#!/usr/bin/env python3
"""WiFi Security Analyzer — WPA3 downgrade, evil twin, deauth detection."""

import argparse
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AccessPoint:
    bssid: str
    ssid: str
    channel: int
    signal: int
    security: list = field(default_factory=list)
    wpa3_transition: bool = False
    pmf_required: bool = False


@dataclass
class DeauthFrame:
    timestamp: float
    src: str
    dst: str
    reason: int
    is_broadcast: bool = False


class WiFiAnalyzer:
    """Analyze WiFi security posture from scan results or pcap."""

    def __init__(self):
        self.access_points: list[AccessPoint] = []
        self.deauth_frames: list[DeauthFrame] = []
        self.suspicious_aps: list[dict] = []

    def parse_scan_results(self, scan_data: str) -> list[AccessPoint]:
        """Parse iwlist/airodump-ng style scan output."""
        aps = []
        current_ap = None

        for line in scan_data.splitlines():
            cell_match = re.match(r'\s*Cell (\d+) - Address: ([\w:]+)', line)
            if cell_match:
                if current_ap:
                    aps.append(current_ap)
                current_ap = AccessPoint(
                    bssid=cell_match.group(2),
                    ssid="",
                    channel=0,
                    signal=0,
                )

            if not current_ap:
                continue

            ssid_match = re.match(r'\s*ESSID:"(.+)"', line)
            if ssid_match:
                current_ap.ssid = ssid_match.group(1)

            chan_match = re.match(r'\s*Channel:(\d+)', line)
            if chan_match:
                current_ap.channel = int(chan_match.group(1))

            sig_match = re.match(r'\s*Signal level=(-?\d+)', line)
            if sig_match:
                current_ap.signal = int(sig_match.group(1))

            if 'WPA2' in line:
                current_ap.security.append('WPA2')
            if 'WPA3' in line:
                current_ap.security.append('WPA3')
                if 'Transition' in line:
                    current_ap.wpa3_transition = True
            if 'PMF' in line or 'Management Frame Protection' in line:
                if 'required' in line.lower():
                    current_ap.pmf_required = True

        if current_ap:
            aps.append(current_ap)

        self.access_points = aps
        return aps

    def detect_wpa3_downgrade(self) -> list[dict]:
        """Identify APs vulnerable to WPA3 downgrade attacks."""
        vulnerable = []
        for ap in self.access_points:
            if ap.wpa3_transition:
                vulnerable.append({
                    'bssid': ap.bssid,
                    'ssid': ap.ssid,
                    'risk': 'HIGH',
                    'issue': 'WPA3 transition mode — client may downgrade to WPA2',
                    'mitigation': 'Disable transition mode; enforce PMF',
                })
            elif 'WPA2' in ap.security and 'WPA3' not in ap.security:
                vulnerable.append({
                    'bssid': ap.bssid,
                    'ssid': ap.ssid,
                    'risk': 'MEDIUM',
                    'issue': 'WPA2 only — no WPA3 available',
                    'mitigation': 'Upgrade to WPA3-only or transition mode',
                })
        return vulnerable

    def detect_evil_twin(self) -> list[dict]:
        """Detect potential evil twin APs (same SSID, different BSSID/channel)."""
        ssid_map: dict[str, list[AccessPoint]] = defaultdict(list)
        for ap in self.access_points:
            ssid_map[ap.ssid].append(ap)

        suspicious = []
        for ssid, aps in ssid_map.items():
            if len(aps) < 2:
                continue

            bssids = {ap.bssid for ap in aps}
            channels = {ap.channel for ap in aps}
            signals = [ap.signal for ap in aps]

            if len(bssids) > 1:
                signal_spread = max(signals) - min(signals)
                suspicious.append({
                    'ssid': ssid,
                    'bssids': list(bssids),
                    'channels': list(channels),
                    'signal_spread_db': signal_spread,
                    'risk': 'HIGH' if signal_spread > 20 else 'MEDIUM',
                    'indicators': [
                        'Multiple BSSIDs for same SSID',
                        f'Channel mismatch: {channels}',
                        f'Signal spread: {signal_spread} dB',
                    ],
                })

        self.suspicious_aps = suspicious
        return suspicious

    def parse_pcap_deauth(self, pcap_text: str) -> list[DeauthFrame]:
        """Parse deauth frames from tcpdump/tshark output."""
        frames = []
        for line in pcap_text.splitlines():
            if 'Deauthentication' not in line and 'deauth' not in line.lower():
                continue

            ts_match = re.match(r'\s*([\d.]+)', line)
            src_match = re.search(r'([\w:]{17})\s*>\s*([\w:]{17})', line)
            reason_match = re.search(r'reason\s+(\d+)', line, re.IGNORECASE)

            if ts_match and src_match:
                dst = src_match.group(2)
                frames.append(DeauthFrame(
                    timestamp=float(ts_match.group(1)),
                    src=src_match.group(1),
                    dst=dst,
                    reason=int(reason_match.group(1)) if reason_match else 0,
                    is_broadcast = dst == 'ff:ff:ff:ff:ff:ff',
                ))

        self.deauth_frames = frames
        return frames

    def detect_deauth_attack(self, threshold: int = 10) -> Optional[dict]:
        """Detect deauth flood patterns."""
        if not self.deauth_frames:
            return None

        src_counts: dict[str, int] = defaultdict(int)
        broadcast_count = 0
        for frame in self.deauth_frames:
            src_counts[frame.src] += 1
            if frame.is_broadcast:
                broadcast_count += 1

        attackers = {src: count for src, count in src_counts.items() if count >= threshold}

        if not attackers:
            return {
                'status': 'clean',
                'total_deauth_frames': len(self.deauth_frames),
                'broadcast_ratio': broadcast_count / len(self.deauth_frames),
            }

        return {
            'status': 'attack_detected',
            'attackers': attackers,
            'total_frames': len(self.deauth_frames),
            'broadcast_ratio': broadcast_count / len(self.deauth_frames),
            'recommendation': 'Enable 802.11w (PMF); investigate source MACs',
        }

    def generate_report(self) -> str:
        """Generate a security assessment report."""
        lines = ["=" * 60, "WiFi Security Analysis Report", "=" * 60, ""]

        lines.append(f"Total APs discovered: {len(self.access_points)}")
        wpa3_count = sum(1 for ap in self.access_points if 'WPA3' in ap.security)
        transition_count = sum(1 for ap in self.access_points if ap.wpa3_transition)
        lines.append(f"WPA3-capable: {wpa3_count} | Transition mode: {transition_count}")
        lines.append("")

        # WPA3 downgrade
        downgrade = self.detect_wpa3_downgrade()
        if downgrade:
            lines.append("[!] WPA3 Downgrade Vulnerabilities:")
            for v in downgrade:
                lines.append(f"  [{v['risk']}] {v['ssid']} ({v['bssid']})")
                lines.append(f"    Issue: {v['issue']}")
                lines.append(f"    Fix: {v['mitigation']}")
            lines.append("")

        # Evil twin
        evil_twins = self.detect_evil_twin()
        if evil_twins:
            lines.append("[!] Potential Evil Twin APs:")
            for et in evil_twins:
                lines.append(f"  [{et['risk']}] SSID: {et['ssid']}")
                lines.append(f"    BSSIDs: {', '.join(et['bssids'])}")
                for ind in et['indicators']:
                    lines.append(f"    - {ind}")
            lines.append("")

        # Deauth
        if self.deauth_frames:
            deauth_report = self.detect_deauth_attack()
            if deauth_report and deauth_report.get('status') == 'attack_detected':
                lines.append("[!] Deauthentication Attack Detected:")
                lines.append(f"    Attackers: {deauth_report['attackers']}")
                lines.append(f"    Recommendation: {deauth_report['recommendation']}")

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='WiFi Security Analyzer')
    parser.add_argument('--scan', action='store_true', help='Analyze scan results')
    parser.add_argument('--detect-evil-twin', action='store_true', help='Detect evil twin APs')
    parser.add_argument('--detect-deauth', action='store_true', help='Detect deauth attacks')
    parser.add_argument('--pcap', type=str, help='Path to pcap/tcpdump output')
    parser.add_argument('--interface', type=str, default='wlan0mon', help='Monitor mode interface')
    parser.add_argument('--threshold', type=int, default=10, help='Deauth flood threshold')
    args = parser.parse_args()

    analyzer = WiFiAnalyzer()

    # Demo scan data
    demo_scan = """
Cell 01 - Address: AA:BB:CC:DD:EE:01
  ESSID:"CorpNet"
  Channel:6
  Signal level=-45
  IEEE 802.11i/WPA2 Version 1
Cell 02 - Address: AA:BB:CC:DD:EE:02
  ESSID:"CorpNet"
  Channel:11
  Signal level=-72
  IEEE 802.11i/WPA2 Version 1
Cell 03 - Address: AA:BB:CC:DD:EE:03
  ESSID:"CorpNet_Secure"
  Channel:36
  Signal level=-50
  WPA3-Personal (SAE) Transition Mode
  Management Frame Protection required
Cell 04 - Address: AA:BB:CC:DD:EE:04
  ESSID:"Guest"
  Channel:1
  Signal level=-65
  WPA2-Personal
"""

    if args.scan or args.detect_evil_twin:
        aps = analyzer.parse_scan_results(demo_scan)
        print(f"Parsed {len(aps)} access points\n")

    if args.detect_evil_twin:
        evil_twins = analyzer.detect_evil_twin()
        if evil_twins:
            print("[!] Evil Twin Detection Results:")
            for et in evil_twins:
                print(f"  [{et['risk']}] {et['ssid']}: {len(et['bssids'])} BSSIDs")
        else:
            print("[+] No evil twin indicators found")

    if args.detect_deauth and args.pcap:
        try:
            with open(args.pcap) as f:
                pcap_data = f.read()
            frames = analyzer.parse_pcap_deauth(pcap_data)
            report = analyzer.detect_deauth_attack(args.threshold)
            print(f"\nDeauth analysis: {report}")
        except FileNotFoundError:
            print(f"Error: {args.pcap} not found")
            sys.exit(1)

    # Always print report
    print(analyzer.generate_report())


if __name__ == '__main__':
    main()
