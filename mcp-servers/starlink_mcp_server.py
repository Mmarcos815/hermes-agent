#!/usr/bin/env python3
"""
Starlink Satellite Security MCP Server
Educational simulation of satellite/Starlink terminal security analysis.

Tools:
  - starlink_recon      — Simulate Starlink terminal reconnaissance
  - satellite_analysis  — Analyze satellite communication security
  - ground_station_audit— Audit ground station security posture
  - link_analysis       — Analyze communication link vulnerabilities
  - signal_analysis     — Analyze signal interception risks
"""

import json
import random
from datetime import datetime, timezone
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


app = Server("starlink-security")


# ── helpers ──────────────────────────────────────────────────────────

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def risk(score: int, label: str) -> str:
    if score >= 8:
        return "CRITICAL"
    if score >= 6:
        return "HIGH"
    if score >= 4:
        return "MEDIUM"
    return "LOW"


def find(prefix: str, items: list[str]) -> list[str]:
    return [i for i in items if prefix.lower() in i.lower()]


# ── tool schemas ──────────────────────────────────────────────────────

RECON_TOOL = Tool(
    name="starlink_recon",
    description="Simulate reconnaissance against a Starlink terminal/user terminal.",
    inputSchema={
        "type": "object",
        "properties": {
            "target": {"type": "string", "description": "Terminal ID or grid location (e.g. 'UT-Austin', 'terminal_7F3A')"},
            "scan_depth": {"type": "string", "enum": ["light", "normal", "deep"], "default": "normal"}
        },
        "required": ["target"]
    }
)

SAT_TOOL = Tool(
    name="satellite_analysis",
    description="Analyze security aspects of satellite communication (uplink/downlink/beam).",
    inputSchema={
        "type": "object",
        "properties": {
            "satellite_id": {"type": "string", "description": "Satellite NORAD ID or Starlink batch (e.g. 'STARLINK-1234', 'v2-mini')"},
            "frequency_band": {"type": "string", "enum": ["Ku", "Ka", "V", "E"], "default": "Ku"}
        },
        "required": ["satellite_id"]
    }
)

GS_TOOL = Tool(
    name="ground_station_audit",
    description="Audit a ground station's physical, network, and RF security posture.",
    inputSchema={
        "type": "object",
        "properties": {
            "station_name": {"type": "string", "description": "Ground station name (e.g. 'South TX', 'Connolly', 'Tucson')"},
            "scope": {"type": "string", "enum": ["physical", "network", "rf", "all"], "default": "all"}
        },
        "required": ["station_name"]
    }
)

LINK_TOOL = Tool(
    name="link_analysis",
    description="Analyze the communication link between terminal, satellite, and gateway for vulnerabilities.",
    inputSchema={
        "type": "object",
        "properties": {
            "terminal_id": {"type": "string"},
            "satellite_id": {"type": "string"},
            "gateway": {"type": "string"}
        },
        "required": ["terminal_id", "satellite_id"]
    }
)

SIGNAL_TOOL = Tool(
    name="signal_analysis",
    description="Analyze signal interception, jamming, and spoofing risks on the RF link.",
    inputSchema={
        "type": "object",
        "properties": {
            "frequency_ghz": {"type": "number", "description": "Center frequency in GHz (e.g. 12.5 for Ku-band downlink)"},
            "bandwidth_mhz": {"type": "number", "default": 250},
            "location": {"type": "string", "description": "Observation location or region"}
        },
        "required": ["frequency_ghz"]
    }
)


# ── handlers ──────────────────────────────────────────────────────────

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [RECON_TOOL, SAT_TOOL, GS_TOOL, LINK_TOOL, SIGNAL_TOOL]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    ts = now_iso()

    if name == "starlink_recon":
        return _recon(ts, arguments)
    if name == "satellite_analysis":
        return _sat(ts, arguments)
    if name == "ground_station_audit":
        return _gs(ts, arguments)
    if name == "link_analysis":
        return _link(ts, arguments)
    if name == "signal_analysis":
        return _signal(ts, arguments)

    return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


def _recon(ts: str, args: dict) -> list[TextContent]:
    target = args["target"]
    depth = args.get("scan_depth", "normal")
    random.seed(hash(target) % 2**32)

    ports_map = {"light": [80, 443, 22], "normal": [80, 443, 22, 8080, 9090, 8443], "deep": [21, 22, 23, 80, 443, 502, 8080, 8443, 9090, 1883, 8883, 5683]}
    ports = ports_map[depth]

    services = {
        80: "HTTP (redirect)", 443: "HTTPS (telemetry API)", 22: "SSH (debug)",
        23: "Telnet (legacy debug)", 502: "Modbus (thermal ctrl)", 8080: "gRPC gateway",
        8443: "HTTPS (mesh ctrl)", 9090: "Prometheus exporter", 1883: "MQTT (telemetry)",
        8883: "MQTTS (secure)", 5683: "CoAP (local mesh)"
    }

    results = [{"port": p, "state": "open", "service": services.get(p, "unknown")}
               for p in ports if random.random() > 0.25]

    firmware = f"{random.randint(2,4)}.{random.randint(0,15)}.{random.randint(0,99)}"
    vulns = []
    if random.random() > 0.5:
        vulns.append({"id": f"CVE-2024-{random.randint(20000,59999)}", "desc": "Telemetry API auth bypass", "risk": risk(random.randint(7,9))})
    if random.random() > 0.6:
        vulns.append({"id": f"CVE-2024-{random.randint(20000,59999)}", "desc": "gRPC gateway SSRF", "risk": risk(random.randint(5,7))})

    output = {
        "timestamp": ts,
        "tool": "starlink_recon",
        "target": target,
        "scan_depth": depth,
        "terminal_info": {"firmware": firmware, "uptime_h": random.randint(72, 5000), "dish_model": random.choice(["rectangular", "v2-standard", "v2-highperf", "v3-standard"])},
        "open_ports": results,
        "vulnerabilities": vulns,
        "notes": ["SIMULATION ONLY — synthetic data. Not real reconnaissance.", "Use for authorized red-team/blue-team training exercises."]
    }
    return [TextContent(type="text", text=json.dumps(output, indent=2))]


def _sat(ts: str, args: dict) -> list[TextContent]:
    sat_id = args["satellite_id"]
    band = args.get("frequency_band", "Ku")
    random.seed(hash(sat_id) % 2**32)

    bands = {"Ku": {"up": [14.0, 14.5], "down": [10.7, 12.75]}, "Ka": {"up": [27.5, 30.0], "down": [17.7, 21.2]}, "V": {"up": [42.5, 43.5], "down": [37.5, 42.0]}, "E": {"up": [71.0, 76.0], "down": [81.0, 86.0]}}
    freqs = bands.get(band, bands["Ku"])

    beams = []
    for i in range(random.randint(8, 24)):
        beams.append({
            "beam_id": f"B-{i:03d}",
            "freq_ghz": round(random.uniform(freqs["down"][0], freqs["down"][1]), 3),
            "bandwidth_mhz": random.choice([125, 250, 500]),
            "power_dbm": round(random.uniform(20, 40), 1),
            "coverage_km": random.randint(15, 60),
            "encryption": random.choice(["AES-256-GCM", "AES-128-CTR", "none"])
        })

    issues = []
    unenc = [b for b in beams if b["encryption"] == "none"]
    if unenc:
        issues.append({"finding": f"{len(unenc)} beams with no encryption", "severity": risk(8), "remediation": "Enable beam-level encryption"})
    issues.append({"finding": "Predictable beam hopping pattern", "severity": risk(6), "remediation": "Increase hopping entropy / shorten dwell time"})
    if random.random() > 0.5:
        issues.append({"finding": "Leaked ephemeris data on unauthenticated endpoint", "severity": risk(7), "remediation": "Auth-guard ephemeris feed"})

    output = {
        "timestamp": ts,
        "tool": "satellite_analysis",
        "satellite_id": sat_id,
        "frequency_band": band,
        "orbit": {"type": random.choice(["LEO-550", "LEO-540", "LEO-570"]), "inclination_deg": random.choice([53.0, 70.0, 97.4]), "altitude_km": random.randint(540, 570)},
        "beams": beams[:6],
        "total_beams": len(beams),
        "security_issues": issues,
        "notes": ["SIMULATION ONLY — synthetic orbital and beam data."]
    }
    return [TextContent(type="text", text=json.dumps(output, indent=2))]


def _gs(ts: str, args: dict) -> list[TextContent]:
    station = args["station_name"]
    scope = args.get("scope", "all")
    random.seed(hash(station) % 2**32)

    sections = {}
    if scope in ("physical", "all"):
        sections["physical"] = {
            "fencing": random.choice(["perimeter_cameras", "motion_sensors", "patrol", "unmonitored"]),
            "access_control": random.choice(["biometric+card", "card_only", "key_lock", "unrestricted"]),
            "anomalies": [a for a in [
                "Camera blind spot detected",
                "Fence sensor offline since " + ts,
                "Guard rotation gap 02:00-06:00"
            ] if random.random() > 0.5]
        }
    if scope in ("network", "all"):
        sections["network"] = {
            "segmentation": random.choice(["full_vlan", "flat_network", "partial"]),
            "internet_exposure": random.choice(["none", "mgmt_only", "api_portal"]),
            "findings": [f for f in [
                "Default creds on NMS appliance",
                "TLS 1.0 still enabled on legacy interface",
                "Unpatched CVE-2024-" + str(random.randint(20000, 59999)),
                "Exposed debug port on backup link"
            ] if random.random() > 0.4]
        }
    if scope in ("rf", "all"):
        sections["rf"] = {
            "antennas": [{"type": random.choice(["1.8m_ka", "3.7m_ku", "4.5m_kav"]), "az_deg": random.randint(0, 360), "el_deg": random.randint(5, 85)} for _ in range(random.randint(2, 5))],
            "jamming_mitigation": random.choice(["null_steering", "frequency_hop", "power_adapt", "none"]),
            "spectrum_anomalies": random.randint(0, 3)
        }

    overall = risk(random.randint(3, 8))
    output = {
        "timestamp": ts,
        "tool": "ground_station_audit",
        "station_name": station,
        "scope": scope,
        "findings": sections,
        "overall_risk": overall,
        "notes": ["SIMULATION ONLY — no real ground station accessed."]
    }
    return [TextContent(type="text", text=json.dumps(output, indent=2))]


def _link(ts: str, args: dict) -> list[TextContent]:
    term = args["terminal_id"]
    sat = args["satellite_id"]
    gw = args.get("gateway", f"gw-{random.randint(100,999)}.starlink.isp")
    random.seed(hash(term + sat) % 2**32)

    hops = [
        {"hop": "terminal→sat (uplink)", "latency_ms": round(random.uniform(1, 5), 2), "jitter_ms": round(random.uniform(0.1, 2), 2), "encryption": random.choice(["AES-256-GCM", "AES-128-CTR", "none"]), "risk": risk(random.randint(2, 7))},
        {"hop": "sat→gateway (downlink)", "latency_ms": round(random.uniform(1, 5), 2), "jitter_ms": round(random.uniform(0.1, 2), 2), "encryption": random.choice(["AES-256-GCM", "AES-128-CTR"]), "risk": risk(random.randint(1, 5))},
        {"hop": "gateway→internet", "latency_ms": round(random.uniform(10, 40), 2), "jitter_ms": round(random.uniform(1, 10), 2), "encryption": "TLS 1.3", "risk": risk(random.randint(1, 3))}
    ]

    vulns = [
        {"vector": "Predictable beam-satellite handover → window for MITM", "severity": risk(6), "mitigation": "Validate handover certificates"},
        {"vector": "Local mesh traffic sniffable within 100m", "severity": risk(5), "mitigation": "Enable link-layer encryption on mesh"},
        {"vector": "Dish firmware unsigned → supply-chain implant", "severity": risk(8), "mitigation": "Require signed firmware + rollback protection"},
    ]
    if random.random() > 0.5:
        vulns.append({"vector": "Gateway single point of failure for region", "severity": risk(7), "mitigation": "Multi-gateway diversity"})

    output = {
        "timestamp": ts,
        "tool": "link_analysis",
        "path": {"terminal": term, "satellite": sat, "gateway": gw},
        "hops": hops,
        "end_to_end_latency_ms": round(sum(h["latency_ms"] for h in hops), 2),
        "end_to_end_jitter_ms": round(sum(h["jitter_ms"] for h in hops), 2),
        "vulnerabilities": vulns,
        "notes": ["SIMULATION ONLY — synthetic link topology and latency model."]
    }
    return [TextContent(type="text", text=json.dumps(output, indent=2))]


def _signal(ts: str, args: dict) -> list[TextContent]:
    freq = args["frequency_ghz"]
    bw = args.get("bandwidth_mhz", 250)
    loc = args.get("location", "unspecified")
    random.seed(hash(f"{freq}{bw}") % 2**32)

    snr_db = round(random.uniform(8, 25), 1)
    interference = [
        {"type": "adjacent_sat", "delta_mhz": random.choice([-500, 500]), "c_n_degradation_db": round(random.uniform(0.5, 4), 1)},
        {"type": "terrestrial_mw", "source": "5G backhaul tower ~3km", "c_n_degradation_db": round(random.uniform(0.2, 2), 1)},
    ]

    risks = [
        {"threat": "passive_interception", "feasibility": "trivial" if bw >= 250 else "moderate", "range_km": round(random.uniform(5, 50), 1), "mitigation": "Narrower beams, encryption"},
        {"threat": "jamming", "feasibility": "moderate" if freq < 20 else "difficult", "required_power_w": round(random.uniform(1, 100), 1), "mitigation": "Null-steering, spread-spectrum"},
        {"threat": "spoofing", "feasibility": "difficult", "prereq": "cryptographic key extraction", "mitigation": "Authenticated signal (GPS-like)"},
    ]

    if random.random() > 0.5:
        risks.append({"threat": "replay", "feasibility": "moderate", "window_s": random.randint(1, 10), "mitigation": "Timestamp + nonce in frame"})

    output = {
        "timestamp": ts,
        "tool": "signal_analysis",
        "frequency_ghz": freq,
        "bandwidth_mhz": bw,
        "location": loc,
        "signal_quality": {"snr_db": snr_db, "modulation": random.choice(["QPSK", "8PSK", "16APSK", "32APSK"]), "fec": random.choice(["LDPC-1/2", "LDPC-2/3", "LDPC-3/4"])},
        "interference": interference,
        "threats": risks,
        "notes": ["SIMULATION ONLY — RF environment modeled, not measured."]
    }
    return [TextContent(type="text", text=json.dumps(output, indent=2))]


# ── entrypoint ────────────────────────────────────────────────────────

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
