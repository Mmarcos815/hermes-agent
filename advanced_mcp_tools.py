#!/usr/bin/env python3
"""
Advanced MCP Tools — wraps advanced/ and api_exploit_lab/ as importable functions
for registration on the unified FastMCP server.
"""

import json
import sys
import os

ROOT_DIR = r"C:\Users\mobil\orca\projects\my 1st"
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# ─── API Exploit Lab ─────────────────────────────────────────────────────────

def apiexploit_list_vulns() -> dict:
    """List all vulnerabilities in the API Exploit Lab."""
    return {
        "vulnerabilities": [
            {"id": "API-001", "name": "BOLA/IDOR", "endpoint": "GET /api/users/:id", "severity": "high"},
            {"id": "API-002", "name": "SQL Injection", "endpoint": "GET /api/search?q=", "severity": "critical"},
            {"id": "API-003", "name": "SSRF", "endpoint": "POST /api/webhook", "severity": "high"},
            {"id": "API-004", "name": "JWT alg:none", "endpoint": "Authorization header", "severity": "critical"},
            {"id": "API-005", "name": "Mass Assignment", "endpoint": "POST /api/users/:id/update", "severity": "high"},
            {"id": "API-006", "name": "GraphQL Introspection", "endpoint": "POST /graphql", "severity": "medium"},
            {"id": "API-007", "name": "File Upload", "endpoint": "POST /api/upload", "severity": "medium"},
            {"id": "API-008", "name": "OAuth Redirect Bypass", "endpoint": "GET /oauth/authorize", "severity": "medium"},
            {"id": "API-009", "name": "Race Condition", "endpoint": "POST /api/buy", "severity": "high"},
            {"id": "API-010", "name": "No Rate Limit", "endpoint": "GET /api/data", "severity": "low"},
        ],
        "lab_port": 5020,
        "start_command": "python api_exploit_lab/server.py",
    }


# ─── Evilginx Config ─────────────────────────────────────────────────────────

def evilginx_generate_config(target_domain: str, phish_domain: str, redirect_url: str = "/", 
                              cookies: list = None, proxy_hosts: list = None) -> dict:
    """Generate Evilginx3 phishlet YAML config (config file only, no runtime)."""
    from advanced.evilginx_config import generate
    cfg = generate(target_domain, phish_domain, cookies, redirect_url, proxy_hosts)
    return {"config": cfg, "target": target_domain, "phish_domain": phish_domain}


# ─── C2 Deploy ───────────────────────────────────────────────────────────────

def c2_generate_artifacts(framework: str = "sliver", output_dir: str = "./c2_lab") -> dict:
    """Generate Docker Compose artifacts for Sliver or Mythic C2 lab."""
    from advanced.c2_deploy import gen_sliver, gen_mythic
    from pathlib import Path
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    if framework == "sliver":
        d = gen_sliver(out)
    elif framework == "mythic":
        d = gen_mythic(out)
    else:
        return {"error": f"Unknown framework: {framework}. Use 'sliver' or 'mythic'."}
    return {"framework": framework, "output_dir": str(d), "status": "artifacts_generated"}


# ─── Phishing Kit ────────────────────────────────────────────────────────────

def phishing_generate_page(brand: str = "generic", include_server: bool = False, 
                            output_dir: str = "./phish_lab") -> dict:
    """Generate static HTML phishing page for security awareness training."""
    from advanced.phishing_kit import gen_html, gen_server
    from pathlib import Path
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    html = gen_html(brand, banner=True)
    (out / "index.html").write_text(html)
    result = {"page": str(out / "index.html"), "brand": brand, "banner": True}
    if include_server:
        (out / "capture_server.py").write_text(gen_server())
        result["server"] = str(out / "capture_server.py")
    return result


# ─── Evasion ─────────────────────────────────────────────────────────────────

def evasion_encode_payload(payload: str, method: str = "base64") -> dict:
    """Encode a payload using base64, hex, XOR, or AES-256-CBC."""
    from advanced.evasion import encode_base64, encode_hex, xor_encode, aes_encrypt
    data = payload.encode()
    if method == "base64":
        return {"method": "base64", "encoded": encode_base64(data)}
    elif method == "hex":
        return {"method": "hex", "encoded": encode_hex(data)}
    elif method == "xor":
        enc, key = xor_encode(data)
        return {"method": "xor", "encoded": enc.hex(), "key": key.hex()}
    elif method == "aes":
        return aes_encrypt(data)
    else:
        return {"error": f"Unknown method: {method}. Use base64, hex, xor, aes."}


def evasion_generate_ua(browser: str = "chrome", strategy: str = "random") -> dict:
    """Generate a random or browser-specific User-Agent string."""
    from advanced.evasion import UARotator
    r = UARotator(strategy=strategy)
    if browser == "random":
        return {"ua": r.next()}
    else:
        return {"ua": r.custom(browser=browser)}


def evasion_domain_front(front_domain: str, target_host: str, path: str = "/") -> dict:
    """Generate a domain-fronting request structure."""
    from advanced.evasion import DomainFront
    df = DomainFront(front_domain, target_host)
    return df.request(path)


def evasion_simulate_injection(technique: str, target: str = "notepad.exe") -> dict:
    """Demonstrate process injection technique (simulation only)."""
    from advanced.evasion import injection_demo
    return injection_demo(technique, target)


# ─── Kill Chain ──────────────────────────────────────────────────────────────

def kill_chain_run(target: str = "https://api.example.com", objective: str = "full_compromise") -> dict:
    """Execute the 7-stage kill chain orchestrator (BOLA→JWT→MassAssign→SQLi→SSRF→Cloud→Persist)."""
    from advanced.kill_chain import KillChainOrchestrator
    orch = KillChainOrchestrator(target=target, objective=objective)
    return orch.execute()


# ─── C2 Framework ────────────────────────────────────────────────────────────

_c2_server_instance = None

def c2_server_start(host: str = "0.0.0.0", port: int = 8080) -> dict:
    """Start the C2 server with dashboard and implant comms endpoint."""
    global _c2_server_instance
    from advanced.c2_framework import C2Server
    if _c2_server_instance is not None:
        return {"status": "already_running", "host": _c2_server_instance.host, "port": _c2_server_instance.port}
    server = C2Server(host, port)
    server.start_dashboard()
    _c2_server_instance = server
    return {"status": "started", "host": host, "port": port, "dashboard": f"http://{host}:{port}"}


def c2_server_stop() -> dict:
    """Stop the running C2 server."""
    global _c2_server_instance
    if _c2_server_instance is None:
        return {"status": "not_running"}
    _c2_server_instance.shutdown()
    _c2_server_instance = None
    return {"status": "stopped"}


def c2_list_implants() -> dict:
    """List all registered implants on the C2 server."""
    global _c2_server_instance
    if _c2_server_instance is None:
        return {"error": "C2 server not running. Call c2_server_start first."}
    return {"implants": _c2_server_instance.list_implants()}


def c2_dispatch_command(implant_id: str, plugin: str = "exec", params: dict = None) -> dict:
    """Dispatch a command to an implant via the C2 server."""
    global _c2_server_instance
    if _c2_server_instance is None:
        return {"error": "C2 server not running. Call c2_server_start first."}
    params = params or {}
    task_id = _c2_server_instance.dispatch_command(implant_id, plugin, params)
    return {"task_id": task_id, "implant_id": implant_id, "plugin": plugin, "params": params}


def c2_get_results(implant_id: str, limit: int = 50) -> dict:
    """Get results from an implant."""
    global _c2_server_instance
    if _c2_server_instance is None:
        return {"error": "C2 server not running."}
    return {"results": _c2_server_instance.get_results(implant_id, limit)}


# ─── Fuzz Engine ─────────────────────────────────────────────────────────────

def fuzz_coverage_guided(target_code: str = "lambda data: None", seeds: list = None, max_iter: int = 500) -> dict:
    """Run AFL-style coverage-guided fuzzing on a target function."""
    from advanced.fuzz_engine import FuzzEngine
    
    # Parse the target code into a callable
    if target_code.startswith("lambda"):
        target = eval(target_code)
    else:
        # Wrap code into a function using exec with proper indentation
        local_ns = {}
        wrapped_code = "def _target(data):\n    " + target_code
        exec(wrapped_code, local_ns)
        target = local_ns["_target"]
    
    seeds = seeds or [b"hello", b"world", b"test"]
    engine = FuzzEngine(seed=42)
    stats = engine.coverage_guided(target, seeds, max_iter)
    return {
        "executions": stats.total_executions,
        "unique_crashes": stats.unique_crashes,
        "unique_paths": stats.unique_paths,
        "execs_per_sec": round(stats.execs_per_sec, 2),
    }


def fuzz_web(url: str, params: dict = None, headers: dict = None, method: str = "GET") -> dict:
    """Fuzz web parameters and headers with known attack payloads."""
    from advanced.fuzz_engine import FuzzEngine
    engine = FuzzEngine(seed=42)
    findings = engine.web(url, params, headers, method)
    return {"findings_count": len(findings), "findings": findings[:20]}


def fuzz_api(base_url: str, api_type: str = "rest", endpoints: list = None) -> dict:
    """Fuzz REST or GraphQL API endpoints."""
    from advanced.fuzz_engine import FuzzEngine
    engine = FuzzEngine(seed=42)
    findings = engine.api(base_url, api_type, endpoints)
    return {"findings_count": len(findings), "findings": findings[:20]}


# ─── Physical Security ───────────────────────────────────────────────────────

def rfid_analyze_card(atqa: str, sak: str, uid: str) -> dict:
    """Identify RFID card type from ATQA/SAK/UID."""
    from advanced.physical_security import RFIDCloner
    return RFIDCloner.analyze_card(atqa, sak, uid)


def rfid_em4100_pattern(uid: str) -> dict:
    """Generate EM4100 125kHz emulation pattern."""
    from advanced.physical_security import RFIDCloner
    return RFIDCloner.em4100_pattern(uid)


def rfid_mifare_clone_script(uid: str) -> str:
    """Generate Proxmark3 MIFARE Classic clone script."""
    from advanced.physical_security import RFIDCloner
    return RFIDCloner.mifare_clone_script(uid)


def badusb_generate_payload(payload_type: str = "ducky_reverse_shell", lhost: str = "192.168.1.100", 
                             lport: int = 4444) -> str:
    """Generate DigiSpark or Rubber Ducky payload."""
    from advanced.physical_security import BadUSBGenerator
    if payload_type == "ducky_reverse_shell":
        return BadUSBGenerator.ducky_reverse_shell(lhost, lport)
    elif payload_type == "digispark_reverse_shell":
        return BadUSBGenerator.digispark_reverse_shell(lhost, lport)
    elif payload_type == "ducky_wifi_dump":
        return BadUSBGenerator.ducky_wifi_dump()
    else:
        return f"Unknown payload type: {payload_type}"


def wifi_deauth_detect(frames: list = None) -> dict:
    """Detect WiFi deauthentication attacks from frame data."""
    from advanced.physical_security import WiFiDeauthDetector
    det = WiFiDeauthDetector(threshold=5, window=10)
    alerts = []
    if frames:
        for frame in frames:
            alert = det.process_frame(
                frame.get("subtype", 12),
                frame.get("src", ""),
                frame.get("dst", ""),
                frame.get("bssid", ""),
                frame.get("reason", 0)
            )
            if alert:
                alerts.append(alert)
    return {"alerts": alerts, "log_count": len(det.log)}


def ble_parse_advertisement(hex_data: str) -> dict:
    """Parse BLE advertisement packet."""
    from advanced.physical_security import BluetoothScanner
    return BluetoothScanner.parse_advertisement(hex_data)


def ble_classify_device(rssi: int, name: str = None) -> dict:
    """Classify BLE device and assess risk."""
    from advanced.physical_security import BluetoothScanner
    return BluetoothScanner.classify_device(rssi, name)


def uart_jtag_reference(ref_type: str = "pinouts", target: str = None) -> dict:
    """Get UART/JTAG pinout reference or OpenOCD config."""
    from advanced.physical_security import UARTJTAGReference
    if ref_type == "pinouts":
        return {"uart": UARTJTAGReference.UART_STANDARDS, "jtag": UARTJTAGReference.JTAG_PINS}
    elif ref_type == "jtag_connectors":
        return {"connectors": UARTJTAGReference.JTAG_CONNECTORS}
    elif ref_type == "board_uarts":
        return {"boards": UARTJTAGReference.BOARD_UARTS}
    elif ref_type == "baud_rates":
        return {"baud_rates": UARTJTAGReference.BAUD_RATES}
    elif ref_type == "detect_baud":
        return {"script": UARTJTAGReference.detect_baud_script()}
    elif ref_type == "openocd":
        return {"config": UARTJTAGReference.openocd_config(target or "stm32f1x")}
    else:
        return {"error": f"Unknown ref_type: {ref_type}"}


# ─── SE Campaign ─────────────────────────────────────────────────────────────

def se_generate_vishing_script(template: str = "it_support", target_name: str = "John Smith", 
                                **kwargs) -> str:
    """Generate a vishing call script from a template."""
    from advanced.se_campaign import generate_vishing_script
    return generate_vishing_script(template, target_name, **kwargs)


def se_generate_pretext(scenario: str = "auditor") -> str:
    """Generate a pretexting scenario script."""
    from advanced.se_campaign import PRETEXT_LIBRARY
    if scenario not in PRETEXT_LIBRARY:
        return f"Unknown scenario: {scenario}. Available: {list(PRETEXT_LIBRARY.keys())}"
    return PRETEXT_LIBRARY[scenario].to_script()


def se_osint_profile(email: str) -> dict:
    """Generate an OSINT profile skeleton from an email address."""
    from advanced.se_campaign import osint_from_email
    return osint_from_email(email).to_dict()


def se_generate_phishing_email(template: str = "password_reset", target_name: str = "John Smith",
                                target_email: str = "john@example.com", **kwargs) -> dict:
    """Generate a phishing email from a template."""
    from advanced.se_campaign import generate_phishing_email
    return generate_phishing_email(template, target_name, target_email, **kwargs)


def se_campaign_create(name: str, total_targets: int = 100) -> dict:
    """Create a new SE campaign for tracking."""
    from advanced.se_campaign import CampaignTracker
    tracker = CampaignTracker(storage_path="campaigns.json")
    cm = tracker.create(name, total_targets)
    return {"campaign_id": cm.campaign_id, "name": cm.name, "total_targets": cm.total_targets}


def se_campaign_record_event(campaign_id: str, event: str, count: int = 1) -> dict:
    """Record an event in an SE campaign."""
    from advanced.se_campaign import CampaignTracker
    tracker = CampaignTracker(storage_path="campaigns.json")
    tracker.record_event(campaign_id, event, count)
    cm = tracker.get(campaign_id)
    return {"campaign_id": campaign_id, "event": event, "summary": cm.summary() if cm else "not found"}


# ─── Supply Chain ────────────────────────────────────────────────────────────

def supplychain_dependency_confusion_scan(package_name: str, registry_url: str = "https://registry.npmjs.org") -> dict:
    """Scan for dependency confusion vulnerability."""
    from advanced.supply_chain import DependencyConfusionScanner
    scanner = DependencyConfusionScanner(registry_url, package_name)
    report = scanner.scan()
    return {"mode": report.mode, "findings": [{"severity": f.severity, "title": f.title, "description": f.description, "recommendation": f.recommendation} for f in report.findings]}


def supplychain_typosquat_detect(package_name: str, registry: str = "pypi") -> dict:
    """Detect typosquat candidates for a package name."""
    from advanced.supply_chain import TyposquatDetector
    detector = TyposquatDetector(package_name, registry)
    report = detector.scan()
    return {"mode": report.mode, "findings": [{"severity": f.severity, "title": f.title, "description": f.description} for f in report.findings]}


def supplychain_cicd_scan(manifest_path: str = ".github/workflows/ci.yml") -> dict:
    """Scan CI/CD pipeline manifest for attack patterns."""
    from advanced.supply_chain import CICDScanner
    scanner = CICDScanner(manifest_path)
    report = scanner.scan()
    return {"mode": report.mode, "findings": [{"severity": f.severity, "title": f.title, "description": f.description, "recommendation": f.recommendation, "evidence": f.evidence} for f in report.findings]}


def supplychain_container_scan(image_ref: str = "alpine:latest") -> dict:
    """Scan container image reference for security issues."""
    from advanced.supply_chain import ContainerImageScanner
    scanner = ContainerImageScanner(image_ref)
    report = scanner.scan()
    return {"mode": report.mode, "findings": [{"severity": f.severity, "title": f.title, "description": f.description, "recommendation": f.recommendation} for f in report.findings]}


def supplychain_integrity_verify(package_name: str, version: str, local_path: str, expected_hash: str = None) -> dict:
    """Verify package integrity via SHA-256 hash."""
    from advanced.supply_chain import IntegrityVerifier
    verifier = IntegrityVerifier(package_name, version)
    report = verifier.verify(local_path, expected_hash)
    return {"mode": report.mode, "findings": [{"severity": f.severity, "title": f.title, "description": f.description, "recommendation": f.recommendation, "evidence": f.evidence} for f in report.findings]}


# ─── Swarm ───────────────────────────────────────────────────────────────────

def swarm_run_assessment(targets: list = None, allowed_ports: list = None) -> dict:
    """Run multi-agent security assessment swarm."""
    from advanced.swarm import Orchestrator, Scope, ReconAgent, ExploitAgent, PostExploitAgent, ReportingAgent, Severity
    targets = targets or ["10.0.0.1", "10.0.0.2"]
    ports = set(allowed_ports) if allowed_ports else {22, 80, 443, 8080}
    scope = Scope(allowed_hosts=set(targets), allowed_ports=ports, max_severity=Severity.HIGH)
    orch = Orchestrator(scope)
    orch.register(ReconAgent("recon", scope))
    orch.register(ExploitAgent("exploit", scope))
    orch.register(PostExploitAgent("postexploit", scope))
    orch.register(ReportingAgent("reporter", scope))
    report = orch.run_swarm(targets)
    return report
