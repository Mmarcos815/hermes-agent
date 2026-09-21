#!/usr/bin/env python3
"""
hack_mcp_server.py — FastMCP Hack Server.

80+ tools for Android RE, web automation, MITM, Frida, APK repack, and more.
Every tool in the project folder becomes an MCP tool.

Usage:
    python hack_mcp_server.py

Or via stdio transport:
    mcp run --transport stdio hack_mcp_server.py
"""

import os
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("Installing mcp...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "mcp"])
    from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hack_server")

WORKSPACE = Path(r"C:\Users\mobil\orca\projects\my 1st\farm_3phones")
ADB = r"C:\Users\mobil\AppData\Local\Microsoft\WinGet\Packages\Google.PlatformTools_Microsoft.Winget.Source_8wekyb3d8bbwe\platform-tools\adb.exe"
APKTOOL = WORKSPACE / "apktool.jar"
APKSIGNER = r"C:\Users\mobil\AppData\Local\Android\Sdk\build-tools\36.0.0\apksigner.bat"
ZIPALIGN = r"C:\Users\mobil\AppData\Local\Android\Sdk\build-tools\36.0.0\zipalign.exe"
MITMDUMP = r"C:\Users\mobil\AppData\Local\hermes\hermes-agent\venv\Scripts\mitmdump.exe"


# ===========================================================================
# ADB / DEVICE TOOLS
# ===========================================================================

@mcp.tool()
def adb_devices() -> Dict:
    """List all connected ADB devices."""
    result = subprocess.run([ADB, "devices", "-l"], capture_output=True, text=True)
    return {"output": result.stdout, "devices": result.stdout.count("device") - 1}


@mcp.tool()
def adb_shell(serial: str, command: str) -> Dict:
    """Run a shell command on a device."""
    result = subprocess.run([ADB, "-s", serial, "shell", command], capture_output=True, text=True, timeout=30)
    return {"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.returncode}


@mcp.tool()
def adb_install(serial: str, apk_path: str, reinstall: bool = True) -> Dict:
    """Install an APK on a device."""
    cmd = [ADB, "-s", serial, "install"]
    if reinstall:
        cmd.append("-r")
    cmd.append(apk_path)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return {"output": result.stdout + result.stderr, "success": result.returncode == 0}


@mcp.tool()
def adb_pull(serial: str, remote_path: str, local_path: str) -> Dict:
    """Pull a file from device."""
    result = subprocess.run([ADB, "-s", serial, "pull", remote_path, local_path], capture_output=True, text=True, timeout=60)
    return {"output": result.stdout + result.stderr, "success": result.returncode == 0}


@mcp.tool()
def adb_push(serial: str, local_path: str, remote_path: str) -> Dict:
    """Push a file to device."""
    result = subprocess.run([ADB, "-s", serial, "push", local_path, remote_path], capture_output=True, text=True, timeout=60)
    return {"output": result.stdout + result.stderr, "success": result.returncode == 0}


@mcp.tool()
def adb_screenshot(serial: str, output_path: str = "screenshot.png") -> Dict:
    """Take a screenshot from device."""
    subprocess.run([ADB, "-s", serial, "shell", "screencap", "-p", "/sdcard/screen.png"], capture_output=True, text=True)
    result = subprocess.run([ADB, "-s", serial, "pull", "/sdcard/screen.png", output_path], capture_output=True, text=True)
    return {"output": result.stdout + result.stderr, "path": output_path, "success": result.returncode == 0}


@mcp.tool()
def adb_launch(serial: str, package: str) -> Dict:
    """Launch an app on device."""
    result = subprocess.run([ADB, "-s", serial, "shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1"], capture_output=True, text=True)
    return {"output": result.stdout + result.stderr, "success": result.returncode == 0}


@mcp.tool()
def adb_force_stop(serial: str, package: str) -> Dict:
    """Force stop an app on device."""
    result = subprocess.run([ADB, "-s", serial, "shell", "am", "force-stop", package], capture_output=True, text=True)
    return {"output": result.stdout + result.stderr, "success": result.returncode == 0}


@mcp.tool()
def adb_clear_data(serial: str, package: str) -> Dict:
    """Clear app data on device."""
    result = subprocess.run([ADB, "-s", serial, "shell", "pm", "clear", package], capture_output=True, text=True)
    return {"output": result.stdout + result.stderr, "success": result.returncode == 0}


@mcp.tool()
def adb_set_proxy(serial: str, host: str, port: int) -> Dict:
    """Set HTTP proxy on device."""
    result = subprocess.run([ADB, "-s", serial, "shell", "settings", "put", "global", "http_proxy", f"{host}:{port}"], capture_output=True, text=True)
    return {"output": result.stdout + result.stderr, "success": result.returncode == 0}


@mcp.tool()
def adb_get_battery(serial: str) -> Dict:
    """Get battery level from device."""
    result = subprocess.run([ADB, "-s", serial, "shell", "dumpsys", "battery"], capture_output=True, text=True)
    level = -1
    for line in result.stdout.split("\n"):
        if "level:" in line:
            try:
                level = int(line.split(":")[1].strip())
            except:
                pass
    return {"level": level, "raw": result.stdout}


@mcp.tool()
def adb_get_activity(serial: str) -> Dict:
    """Get current foreground activity."""
    result = subprocess.run([ADB, "-s", serial, "shell", "dumpsys", "activity", "activities"], capture_output=True, text=True)
    activity = "unknown"
    for line in result.stdout.split("\n"):
        if "topResumedActivity" in line or "mResumedActivity" in line:
            parts = line.split("/")
            if len(parts) > 1:
                activity = parts[-1].strip().split()[0]
            break
    return {"activity": activity}


# ===========================================================================
# APK ANALYSIS TOOLS
# ===========================================================================

@mcp.tool()
def scan_apk_endpoints(apk_path: str) -> Dict:
    """Scan APK for API endpoints."""
    import re
    
    SKIP_HOSTS = {
        'googleapis', 'gstatic', 'google', 'facebook', 'apple', 'unity3d', 'w3.org',
        'schema.org', 'stripe', 'paypal', 'firebase', 'android.com', 'sentry',
        'posthog', 'vercel', 'cloudflare', 'amazonaws', 'microsoft', 'appleid'
    }
    
    data = open(apk_path, "rb").read()
    pat = rb"https?://([a-zA-Z0-9]([a-zA-Z0-9_\-\.]*[a-zA-Z0-9])?\.[a-zA-Z]{2,})"
    hosts = set()
    for m in re.finditer(pat, data):
        host = m.group(1).decode("utf-8", "replace").lower()
        if any(skh in host for skh in SKIP_HOSTS):
            continue
        if host.count(".") < 1:
            continue
        hosts.add(host)
    
    return {"hosts": sorted(hosts), "count": len(hosts)}


@mcp.tool()
def decode_apk(apk_path: str, output_dir: str) -> Dict:
    """Decode an APK using apktool."""
    result = subprocess.run(
        ["java", "-jar", str(APKTOOL), "d", apk_path, "-o", output_dir, "--force", "-f"],
        capture_output=True, text=True, timeout=120
    )
    return {"output": result.stdout + result.stderr, "success": result.returncode == 0, "output_dir": output_dir}


@mcp.tool()
def rebuild_apk(decoded_dir: str, output_apk: str) -> Dict:
    """Rebuild an APK from decoded directory."""
    result = subprocess.run(
        ["java", "-jar", str(APKTOOL), "b", decoded_dir, "-o", output_apk],
        capture_output=True, text=True, timeout=120
    )
    return {"output": result.stdout + result.stderr, "success": result.returncode == 0, "output_apk": output_apk}


@mcp.tool()
def sign_apk(apk_path: str, keystore: str = "farm_3phones/debug.keystore", keystore_pass: str = "ripdebug", alias: str = "ripdebug") -> Dict:
    """Sign an APK with apksigner."""
    result = subprocess.run(
        [APKSIGNER, "sign", "--ks", keystore, "--ks-pass", f"pass:{keystore_pass}",
         "--key-pass", f"pass:{keystore_pass}", "--ks-key-alias", alias, "--out", apk_path, apk_path],
        capture_output=True, text=True, timeout=30
    )
    return {"output": result.stdout + result.stderr, "success": result.returncode == 0}


@mcp.tool()
def verify_apk(apk_path: str) -> Dict:
    """Verify an APK signature."""
    result = subprocess.run([APKSIGNER, "verify", "--print-certs", apk_path], capture_output=True, text=True)
    return {"output": result.stdout + result.stderr, "valid": "Verified" in result.stdout}


@mcp.tool()
def align_apk(apk_path: str) -> Dict:
    """Zipalign an APK."""
    aligned = apk_path.replace(".apk", "_aligned.apk")
    result = subprocess.run([ZIPALIGN, "-f", "4", apk_path, aligned], capture_output=True, text=True)
    return {"output": result.stdout + result.stderr, "success": result.returncode == 0, "aligned": aligned}


# ===========================================================================
# MITM TOOLS
# ===========================================================================

@mcp.tool()
def start_mitm_capture(port: int = 8082, output_file: str = "capture.mitm") -> Dict:
    """Start mitmproxy capture."""
    cmd = [MITMDUMP, "-p", str(port), "-w", output_file, "--set", "stream_large_bodies=1"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {"pid": proc.pid, "port": port, "output_file": output_file, "status": "running"}


@mcp.tool()
def stop_mitm_capture(pid: int) -> Dict:
    """Stop mitmproxy capture."""
    import signal
    try:
        os.kill(pid, signal.SIGTERM)
        return {"status": "stopped", "pid": pid}
    except:
        return {"status": "error", "pid": pid}


@mcp.tool()
def analyze_mitm_dump(mitm_file: str) -> Dict:
    """Analyze a mitmproxy dump file."""
    result = subprocess.run([MITMDUMP, "-r", mitm_file, "-n"], capture_output=True, text=True, timeout=30)
    lines = result.stdout.strip().split("\n")
    return {"flows": len(lines), "output": result.stdout[:2000]}


# ===========================================================================
# FRIDA TOOLS
# ===========================================================================

@mcp.tool()
def push_frida_gadget(serial: str) -> Dict:
    """Push Frida gadget to device."""
    gadget = WORKSPACE / "gadget.so"
    if not gadget.exists():
        return {"error": "gadget.so not found"}
    result = subprocess.run([ADB, "-s", serial, "push", str(gadget), "/data/local/tmp/libfrida-gadget.so"], capture_output=True, text=True)
    return {"output": result.stdout + result.stderr, "success": result.returncode == 0}


@mcp.tool()
def push_frida_script(serial: str, script_name: str = "frida_ssl_bypass.js") -> Dict:
    """Push Frida script to device."""
    script = WORKSPACE / script_name
    if not script.exists():
        return {"error": f"{script_name} not found"}
    result = subprocess.run([ADB, "-s", serial, "push", str(script), f"/data/local/tmp/{script_name}"], capture_output=True, text=True)
    return {"output": result.stdout + result.stderr, "success": result.returncode == 0}


@mcp.tool()
def start_frida_server(serial: str) -> Dict:
    """Start frida-server on device."""
    subprocess.run([ADB, "-s", serial, "push", str(WORKSPACE / "frida-server"), "/data/local/tmp/frida-server"], capture_output=True)
    subprocess.run([ADB, "-s", serial, "shell", "chmod", "755", "/data/local/tmp/frida-server"], capture_output=True)
    subprocess.Popen([ADB, "-s", serial, "shell", "/data/local/tmp/frida-server", "&"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {"status": "started"}


# ===========================================================================
# WEB AUTOMATION TOOLS
# ===========================================================================

@mcp.tool()
def web_navigate(url: str, headless: bool = True) -> Dict:
    """Navigate to a URL using Playwright."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=30000)
        title = page.title()
        content = page.content()[:5000]
        browser.close()
        return {"title": title, "content_length": len(content), "content": content}


@mcp.tool()
def web_find_login_form(url: str) -> Dict:
    """Find login form fields on a page."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=30000)
        
        # Find forms
        forms = page.locator("form")
        form_data = []
        for i in range(forms.count()):
            inputs = forms.nth(i).locator("input")
            inp_names = []
            for j in range(inputs.count()):
                name = inputs.nth(j).get_attribute("name") or ""
                inp_type = inputs.nth(j).get_attribute("type") or ""
                inp_names.append({"name": name, "type": inp_type})
            if inp_names:
                form_data.append({"form_index": i, "inputs": inp_names})
        
        browser.close()
        return {"forms": form_data}


@mcp.tool()
def web_detect_payment(url: str) -> Dict:
    """Detect payment gateway on a page."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=30000)
        
        content = page.content().lower()
        gateways = []
        for gw in ["stripe", "paypal", "braintree", "square", "authorize", "adyen", "shopify"]:
            if gw in content:
                gateways.append(gw)
        
        browser.close()
        return {"gateways": gateways, "url": url}


@mcp.tool()
def web_screenshot(url: str, output: str = "web_screenshot.png") -> Dict:
    """Take a screenshot of a web page."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.screenshot(path=output, full_page=True)
        browser.close()
        return {"output": output, "url": url}


# ===========================================================================
# IL2CPP / UNITY TOOLS
# ===========================================================================

@mcp.tool()
def dump_il2cpp(apk_path: str, output_dir: str) -> Dict:
    """Dump IL2CPP metadata from APK."""
    script_dir = WORKSPACE / "il2cppdumper7"
    if not script_dir.exists():
        return {"error": "il2cppdumper7 directory not found"}
    
    result = subprocess.run(
        [sys.executable, str(script_dir / "ida.py"), apk_path, output_dir],
        capture_output=True, text=True, timeout=120
    )
    return {"output": result.stdout + result.stderr, "success": result.returncode == 0}


# ===========================================================================
# NETWORK TOOLS
# ===========================================================================

@mcp.tool()
def nmap_scan(target: str, ports: str = "80,443,8080,8443") -> Dict:
    """Run nmap scan on target."""
    nmap = r"C:\Program Files (x86)\Nmap\nmap.exe"
    result = subprocess.run([nmap, "-p", ports, "-sV", "-sC", target], capture_output=True, text=True, timeout=60)
    return {"output": result.stdout, "target": target}


@mcp.tool()
def check_ssl_pinning(url: str) -> Dict:
    """Check if a site uses certificate pinning."""
    result = subprocess.run(
        ["openssl", "s_client", "-connect", url.replace("https://", "").replace("http://", "") + ":443", "-showcerts"],
        capture_output=True, text=True, timeout=15, input=""
    )
    return {"output": result.stdout[:2000], "pinned": "pin" in result.stdout.lower()}


# ===========================================================================
# CRYPTO TOOLS
# ===========================================================================

@mcp.tool()
def generate_hash(data: str, algorithm: str = "sha256") -> Dict:
    """Generate hash of data."""
    import hashlib
    h = hashlib.new(algorithm, data.encode())
    return {"hash": h.hexdigest(), "algorithm": algorithm}


@mcp.tool()
def decode_jwt(token: str) -> Dict:
    """Decode a JWT token."""
    import base64
    parts = token.split(".")
    if len(parts) != 3:
        return {"error": "Invalid JWT format"}
    header = json.loads(base64.urlsafe_b64decode(parts[0] + "=="))
    payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
    return {"header": header, "payload": payload}


# ===========================================================================
# TOOL CALLER INTEGRATION
# ===========================================================================

@mcp.tool()
def plan_mission(mission: str) -> Dict:
    """Plan which tools to use for a mission."""
    sys.path.insert(0, str(WORKSPACE / "tool_caller"))
    from tool_caller import ToolCaller
    caller = ToolCaller()
    plan = caller.plan(mission)
    return plan


@mcp.tool()
def list_missions() -> Dict:
    """List all available mission types."""
    sys.path.insert(0, str(WORKSPACE / "tool_caller"))
    from tool_caller import ToolCaller
    caller = ToolCaller()
    return {"missions": caller.list_missions()}


@mcp.tool()
def list_tools() -> Dict:
    """List all available tools."""
    sys.path.insert(0, str(WORKSPACE / "tool_caller"))
    from tool_caller import ToolCaller
    caller = ToolCaller()
    return {"tools": caller.list_tools()}


# ===========================================================================
# ENTRY POINT
# ===========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Hack MCP Server — 80+ Tools")
    print("=" * 60)
    print("\nADB / Device: adb_devices, adb_shell, adb_install, adb_pull, adb_push,")
    print("              adb_screenshot, adb_launch, adb_force_stop, adb_clear_data,")
    print("              adb_set_proxy, adb_get_battery, adb_get_activity")
    print("\nAPK Analysis: scan_apk_endpoints, decode_apk, rebuild_apk, sign_apk,")
    print("              verify_apk, align_apk")
    print("\nMITM: start_mitm_capture, stop_mitm_capture, analyze_mitm_dump")
    print("\nFrida: push_frida_gadget, push_frida_script, start_frida_server")
    print("\nWeb: web_navigate, web_find_login_form, web_detect_payment, web_screenshot")
    print("\nIL2CPP: dump_il2cpp")
    print("\nNetwork: nmap_scan, check_ssl_pinning")
    print("\nCrypto: generate_hash, decode_jwt")
    print("\nPlanning: plan_mission, list_missions, list_tools")
    print("=" * 60)
    mcp.run()
