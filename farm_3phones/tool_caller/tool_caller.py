#!/usr/bin/env python3
"""
tool_caller.py — Mission-to-Tool Router.

Maps mission types to the right tools, scripts, and techniques.
This is the "brain" that knows WHICH tool fits WHAT mission.

Usage:
    from tool_caller import ToolCaller
    caller = ToolCaller()
    plan = caller.plan("Rip Rush APK - capture API")
    # Returns ordered list of tools + scripts to run
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

WORKSPACE = Path(r"C:\Users\mobil\orca\projects\my 1st\farm_3phones")


class ToolCaller:
    """Maps missions to tools, scripts, and techniques."""
    
    def __init__(self):
        self.tools = self._load_tools()
        self.missions = self._load_missions()
    
    def _load_tools(self) -> Dict:
        """Load all available tools from the project."""
        return {
            # === ADB / DEVICE ===
            "adb": {
                "cmd": "C:/Users/mobil/AppData/Local/Microsoft/WinGet/Packages/Google.PlatformTools_Microsoft.Winget.Source_8wekyb3d8bbwe/platform-tools/adb.exe",
                "type": "core",
                "missions": ["device_control", "app_launch", "screenshot", "install"]
            },
            "scrcpy": {
                "cmd": "C:/Users/mobil/AppData/Local/Microsoft/WinGet/Packages/Genymobile.scrcpy_Microsoft.Winget.Source_8wekyb3d8bbwe/scrcpy-win64-v4.1/scrcpy.exe",
                "type": "core",
                "missions": ["screen_mirror", "visual_monitor"]
            },
            "uiautomator2": {
                "module": "uiautomator2",
                "type": "python",
                "missions": ["ui_automate", "tap", "swipe", "find_element"]
            },
            
            # === MITM ===
            "mitmdump": {
                "cmd": "C:/Users/mobil/AppData/Local/hermes/hermes-agent/venv/Scripts/mitmdump.exe",
                "type": "core",
                "missions": ["capture_traffic", "intercept_ssl", "har_export"]
            },
            "comprehensive_capture": {
                "script": "farm_3phones/comprehensive_capture.py",
                "type": "addon",
                "missions": ["capture_traffic", "extract_rewards", "cookie_jar"]
            },
            
            # === FRIDA ===
            "frida_server": {
                "binary": "/data/local/tmp/frida-server",
                "type": "android",
                "missions": ["ssl_bypass", "hook_crypto", "bypass_root"]
            },
            "frida_gadget": {
                "binary": "libfrida-gadget.so",
                "type": "android",
                "missions": ["gadget_inject", "script_auto_load"]
            },
            "frida_ssl_bypass": {
                "script": "farm_3phones/frida_ssl_bypass.js",
                "type": "frida_script",
                "missions": ["ssl_bypass", "unpin", "trust_all"]
            },
            "frida_tcgp": {
                "script": "farm_3phones/frida_tcgp.js",
                "type": "frida_script",
                "missions": ["tcgp_hook", "intercept_api"]
            },
            
            # === APK REPACK ===
            "apktool": {
                "jar": "farm_3phones/apktool.jar",
                "type": "java",
                "missions": ["decode_apk", "rebuild_apk"]
            },
            "apksigner": {
                "cmd": "C:/Users/mobil/AppData/Local/Android/Sdk/build-tools/36.0.0/apksigner.bat",
                "type": "core",
                "missions": ["sign_apk", "verify_sign"]
            },
            "zipalign": {
                "cmd": "C:/Users/mobil/AppData/Local/Android/Sdk/build-tools/36.0.0/zipalign.exe",
                "type": "core",
                "missions": ["align_apk"]
            },
            "repack_debuggable": {
                "script": "farm_3phones/repack_debuggable.py",
                "type": "pipeline",
                "missions": ["repack_gadget", "debuggable", "run_as"]
            },
            
            # === IL2CPP / UNITY ===
            "il2cppdumper": {
                "dir": "farm_3phones/il2cppdumper7",
                "type": "re",
                "missions": ["dump_il2cpp", "extract_metadata", "unity_re"]
            },
            "global_metadata": {
                "file": "farm_3phones/global-metadata.dat",
                "type": "artifact",
                "missions": ["il2cpp_dump", "class_extract"]
            },
            
            # === WEB ===
            "playwright": {
                "module": "playwright",
                "type": "python",
                "missions": ["web_automate", "browser_control", "checkout_analyze"]
            },
            "requests": {
                "module": "requests",
                "type": "python",
                "missions": ["api_call", "http_request", "session_persist"]
            },
            
            # === CRYPTO / HASH ===
            "openssl": {
                "cmd": "openssl",
                "type": "core",
                "missions": ["cert_gen", "hash", "encrypt", "decrypt"]
            },
            
            # === NETWORK ===
            "nmap": {
                "cmd": "C:/Program Files (x86)/Nmap/nmap.exe",
                "type": "core",
                "missions": ["port_scan", "service_detect", "os_detect"]
            },
        }
    
    def _load_missions(self) -> Dict:
        """Define mission types and their tool chains."""
        return {
            # === ANDROID MISSIONS ===
            "apk_capture_api": {
                "description": "Capture an Android app's API traffic",
                "steps": [
                    {"tool": "repack_debuggable", "action": "repack_with_gadget"},
                    {"tool": "apksigner", "action": "sign_apk"},
                    {"tool": "adb", "action": "install_apk"},
                    {"tool": "mitmdump", "action": "start_capture"},
                    {"tool": "adb", "action": "launch_app"},
                    {"tool": "frida_ssl_bypass", "action": "inject_bypass"},
                    {"tool": "comprehensive_capture", "action": "extract_flows"},
                ]
            },
            "apk_repack_gadget": {
                "description": "Repack APK with Frida gadget for script injection",
                "steps": [
                    {"tool": "apktool", "action": "decode"},
                    {"tool": "frida_gadget", "action": "inject_dt_needed"},
                    {"tool": "apktool", "action": "rebuild"},
                    {"tool": "zipalign", "action": "align"},
                    {"tool": "apksigner", "action": "sign"},
                ]
            },
            "ssl_bypass": {
                "description": "Bypass SSL pinning in an Android app",
                "steps": [
                    {"tool": "frida_server", "action": "start"},
                    {"tool": "frida_ssl_bypass", "action": "spawn_inject"},
                    {"tool": "mitmdump", "action": "verify_capture"},
                ]
            },
            "unity_il2cpp_dump": {
                "description": "Dump IL2CPP metadata from Unity app",
                "steps": [
                    {"tool": "adb", "action": "pull_apk"},
                    {"tool": "apktool", "action": "decode"},
                    {"tool": "il2cppdumper", "action": "dump_metadata"},
                ]
            },
            
            # === WEB MISSIONS ===
            "web_checkout_analyze": {
                "description": "Analyze a web checkout page for vulnerabilities",
                "steps": [
                    {"tool": "playwright", "action": "navigate"},
                    {"tool": "playwright", "action": "extract_forms"},
                    {"tool": "playwright", "action": "detect_payment"},
                    {"tool": "playwright", "action": "map_api"},
                    {"tool": "requests", "action": "test_endpoints"},
                ]
            },
            "web_automate_checkout": {
                "description": "Automate a full web checkout flow",
                "steps": [
                    {"tool": "playwright", "action": "navigate_login"},
                    {"tool": "playwright", "action": "fill_login"},
                    {"tool": "playwright", "action": "search_product"},
                    {"tool": "playwright", "action": "add_to_cart"},
                    {"tool": "playwright", "action": "fill_payment"},
                    {"tool": "playwright", "action": "submit_order"},
                ]
            },
            
            # === PRICE MANIPULATION MISSIONS ===
            "price_manipulate": {
                "description": "Full price manipulation test on checkout",
                "steps": [
                    {"tool": "playwright", "action": "navigate_checkout"},
                    {"tool": "playwright", "action": "add_to_cart"},
                    {"tool": "checkout_interceptor", "action": "test_body_price_tamp"},
                    {"tool": "checkout_interceptor", "action": "test_quantity_tamp"},
                    {"tool": "checkout_interceptor", "action": "test_coupon_stacking"},
                    {"tool": "checkout_interceptor", "action": "test_currency_tamp"},
                    {"tool": "checkout_interceptor", "action": "test_hpp"},
                    {"tool": "checkout_interceptor", "action": "test_client_side_price"},
                    {"tool": "checkout_interceptor", "action": "generate_report"},
                ]
            },
            "price_race_condition": {
                "description": "Race condition test for limited items/coupons",
                "steps": [
                    {"tool": "playwright", "action": "navigate_product"},
                    {"tool": "checkout_interceptor", "action": "test_race_condition"},
                    {"tool": "checkout_interceptor", "action": "generate_report"},
                ]
            },
            
            # === FARM MISSIONS ===
            "tcgp_pull_cycle": {
                "description": "Automate TCGP pack opening on all phones",
                "steps": [
                    {"tool": "adb", "action": "wake_all"},
                    {"tool": "uiautomator2", "action": "launch_tcgp"},
                    {"tool": "uiautomator2", "action": "tap_pack"},
                    {"tool": "uiautomator2", "action": "trace_line"},
                    {"tool": "uiautomator2", "action": "collect_cards"},
                ]
            },
            "outpost_free_pulls": {
                "description": "Claim Outpost free daily pulls",
                "steps": [
                    {"tool": "adb", "action": "launch_outpost"},
                    {"tool": "uiautomator2", "action": "tap_free"},
                    {"tool": "uiautomator2", "action": "dismiss_pops"},
                ]
            },
            
            # === RECON MISSIONS ===
            "infra_fingerprint": {
                "description": "Fingerprint infrastructure of a target",
                "steps": [
                    {"tool": "nmap", "action": "port_scan"},
                    {"tool": "requests", "action": "header_analyze"},
                    {"tool": "openssl", "action": "cert_analyze"},
                ]
            },
        }
    
    def plan(self, mission: str) -> Dict:
        """Get the tool chain for a mission."""
        mission_key = self._match_mission(mission)
        if mission_key in self.missions:
            return self.missions[mission_key]
        return self._fuzzy_match(mission)
    
    def _match_mission(self, mission: str) -> str:
        """Match a mission string to a known mission type."""
        mission_lower = mission.lower()
        
        # Android
        if "apk" in mission_lower and ("capture" in mission_lower or "api" in mission_lower):
            return "apk_capture_api"
        if "repack" in mission_lower or "gadget" in mission_lower:
            return "apk_repack_gadget"
        if "ssl" in mission_lower or "pinning" in mission_lower or "bypass" in mission_lower:
            return "ssl_bypass"
        if "il2cpp" in mission_lower or "unity" in mission_lower or "dump" in mission_lower:
            return "unity_il2cpp_dump"
        
        # Web
        if "checkout" in mission_lower and ("analyze" in mission_lower or "test" in mission_lower):
            return "web_checkout_analyze"
        if "checkout" in mission_lower and ("automate" in mission_lower or "buy" in mission_lower or "purchase" in mission_lower):
            return "web_automate_checkout"
        if "web" in mission_lower and "automate" in mission_lower:
            return "web_automate_checkout"
        
        # Farm
        if "tcgp" in mission_lower or "pack" in mission_lower or "pull" in mission_lower:
            return "tcgp_pull_cycle"
        if "outpost" in mission_lower:
            return "outpost_free_pulls"
        
        # Recon
        if "fingerprint" in mission_lower or "recon" in mission_lower or "scan" in mission_lower:
            return "infra_fingerprint"
        
        return "unknown"
    
    def _fuzzy_match(self, mission: str) -> Dict:
        """Fuzzy match for unknown missions."""
        return {
            "description": f"Unknown mission: {mission}",
            "steps": [],
            "suggestion": "Try: apk_capture_api, web_checkout_analyze, tcgp_pull_cycle, ssl_bypass, unity_il2cpp_dump"
        }
    
    def list_missions(self) -> List[str]:
        """List all available mission types."""
        return list(self.missions.keys())
    
    def list_tools(self) -> List[str]:
        """List all available tools."""
        return list(self.tools.keys())
    
    def get_tool(self, tool_name: str) -> Optional[Dict]:
        """Get tool info by name."""
        return self.tools.get(tool_name)
    
    def get_mission(self, mission_name: str) -> Optional[Dict]:
        """Get mission info by name."""
        return self.missions.get(mission_name)


if __name__ == "__main__":
    caller = ToolCaller()
    print("=" * 60)
    print("TOOL CALLER — Mission-to-Tool Router")
    print("=" * 60)
    
    print("\nAvailable missions:")
    for m in caller.list_missions():
        print(f"  - {m}")
    
    print("\nAvailable tools:")
    for t in caller.list_tools():
        print(f"  - {t}")
    
    # Test planning
    test_missions = [
        "Rip Rush APK capture API",
        "TCGplayer checkout automate",
        "TCGP pull cycle",
        "SSL bypass Android"
    ]
    
    for mission in test_missions:
        plan = caller.plan(mission)
        print(f"\n{'=' * 60}")
        print(f"MISSION: {mission}")
        print(f"PLAN: {plan.get('description', 'N/A')}")
        for i, step in enumerate(plan.get('steps', [])):
            print(f"  {i+1}. [{step['tool']}] {step['action']}")
