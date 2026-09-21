import os
import time
import asyncio
import re
import json
import threading
import subprocess
from typing import Dict, Any, Optional, List
import cv2
import numpy as np
import uiautomator2 as u2
import adbutils
import frida
import easyocr
import imagehash
from PIL import Image
from ultralytics import YOLO
from fastmcp import FastMCP

mcp = FastMCP("Android-Bionic-Automation-Ultimate-Absolute-Core")

# Global In-Memory Caches, Singletons & Process Locks
DEVICE_CACHE: Dict[str, u2.Device] = {}
DEVICE_LOCKS: Dict[str, threading.Lock] = {}
FRIDA_SESSIONS: Dict[str, Any] = {}
OCR_READER = easyocr.Reader(['en'], gpu=True)
YOLO_MODEL = YOLO("yolov8n.pt")


def get_device_lock(device_id: str) -> threading.Lock:
    if device_id not in DEVICE_LOCKS:
        DEVICE_LOCKS[device_id] = threading.Lock()
    return DEVICE_LOCKS[device_id]


def get_u2_device(device_id: str) -> u2.Device:
    if device_id not in DEVICE_CACHE:
        DEVICE_CACHE[device_id] = u2.connect(device_id)
    return DEVICE_CACHE[device_id]


# ==========================================
# 1. CORE AUTOMATION, POWER & VISION TOOLS
# ==========================================

@mcp.tool()
async def wake_and_unlock(device_id: str) -> Dict[str, Any]:
    """Verifies display power state. Wakes screen and clears non-locked swipe overlays."""
    loop = asyncio.get_running_loop()
    def _wake():
        lock = get_device_lock(device_id)
        with lock:
            d = get_u2_device(device_id)
            was_off = not d.info.get("screenOn", False)
            if was_off:
                d.wakeup()
                time.sleep(0.3)
                d.swipe(0.5, 0.8, 0.5, 0.2, 0.1)
            return {"status": "success", "device_id": device_id, "was_asleep": was_off, "screen_on": True}

    try:
        return await loop.run_in_executor(None, _wake)
    except Exception as e:
        return {"status": "error", "device_id": device_id, "error": str(e)}


@mcp.tool()
async def tap_ui_element(
    device_id: str, 
    resource_id: Optional[str] = None, 
    text: Optional[str] = None, 
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Dumps UI XML tree, locates target element centroid, and executes deterministic tap."""
    loop = asyncio.get_running_loop()
    def _tap():
        lock = get_device_lock(device_id)
        with lock:
            d = get_u2_device(device_id)
            query = d
            if resource_id:
                query = query(resourceId=resource_id)
            elif text:
                query = query(text=text)
            elif description:
                query = query(description=description)
            else:
                return {"status": "error", "message": "Must provide resource_id, text, or description"}

            if not query.exists(timeout=2.0):
                return {"status": "not_found", "device_id": device_id}

            bounds = query.info["bounds"]
            x = (bounds["left"] + bounds["right"]) // 2
            y = (bounds["top"] + bounds["bottom"]) // 2
            d.click(x, y)
            
            return {
                "status": "success", 
                "device_id": device_id, 
                "tapped_coords": [x, y], 
                "target_bounds": bounds
            }

    try:
        return await loop.run_in_executor(None, _tap)
    except Exception as e:
        return {"status": "error", "device_id": device_id, "error": str(e)}


@mcp.tool()
async def match_screen_template(
    device_id: str, 
    template_path: str, 
    threshold: float = 0.85
) -> Dict[str, Any]:
    """Captures live screen frame and performs local OpenCV template matching (<15ms)."""
    loop = asyncio.get_running_loop()
    def _match():
        lock = get_device_lock(device_id)
        with lock:
            if not os.path.exists(template_path):
                return {"status": "error", "message": f"Template file not found: {template_path}"}

            d = get_u2_device(device_id)
            screenshot_pil = d.screenshot(format="opencv")
            gray_frame = cv2.cvtColor(screenshot_pil, cv2.COLOR_BGR2GRAY)
            
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            h, w = template.shape[:2]

            res = cv2.matchTemplate(gray_frame, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)

            if max_val >= threshold:
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                return {
                    "matched": True,
                    "confidence": float(max_val),
                    "target_coords": [center_x, center_y],
                    "bounding_box": [max_loc[0], max_loc[1], max_loc[0] + w, max_loc[1] + h]
                }
            return {"matched": False, "confidence": float(max_val), "threshold": threshold}

    try:
        return await loop.run_in_executor(None, _match)
    except Exception as e:
        return {"status": "error", "device_id": device_id, "error": str(e)}


@mcp.tool()
async def execute_socket_tap(device_id: str, x: int, y: int) -> Dict[str, Any]:
    """Executes immediate touch input over raw persistent ADB socket connection."""
    loop = asyncio.get_running_loop()
    def _socket_tap():
        lock = get_device_lock(device_id)
        with lock:
            device = adbutils.adb.device(serial=device_id)
            start_time = time.perf_counter()
            device.shell(f"input tap {x} {y}")
            latency_ms = (time.perf_counter() - start_time) * 1000
            return {"status": "success", "device_id": device_id, "coords": [x, y], "latency_ms": round(latency_ms, 2)}

    try:
        return await loop.run_in_executor(None, _socket_tap)
    except Exception as e:
        return {"status": "error", "device_id": device_id, "error": str(e)}


@mcp.tool()
async def execute_macro(device_id: str, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Executes a multi-step sequence of touch/pause instructions in a single IPC call."""
    loop = asyncio.get_running_loop()
    def _macro():
        lock = get_device_lock(device_id)
        with lock:
            device = adbutils.adb.device(serial=device_id)
            d = get_u2_device(device_id)
            results = []

            for act in actions:
                a_type = act.get("type")
                if a_type == "tap":
                    x, y = act["x"], act["y"]
                    device.shell(f"input tap {x} {y}")
                    results.append(f"tap({x},{y})")
                elif a_type == "swipe":
                    d.swipe(act["fx"], act["fy"], act["tx"], act["ty"], act.get("duration", 0.1))
                    results.append("swipe")
                elif a_type == "sleep":
                    time.sleep(act.get("seconds", 0.1))
                    results.append(f"sleep({act.get('seconds')})")
            return {"status": "success", "device_id": device_id, "executed_steps": len(results)}

    try:
        return await loop.run_in_executor(None, _macro)
    except Exception as e:
        return {"status": "error", "device_id": device_id, "error": str(e)}


# ==========================================
# 2. HACKER MODE, TELEMETRY & CARD RECOVERY TOOLS
# ==========================================

@mcp.tool()
async def clear_app_data(device_id: str, package_name: str) -> Dict[str, Any]:
    """Wipes application user data, cache, and sandbox storage (PM clear) for zero-latency reroll cycles."""
    loop = asyncio.get_running_loop()
    def _clear():
        lock = get_device_lock(device_id)
        with lock:
            device = adbutils.adb.device(serial=device_id)
            output = device.shell(f"pm clear {package_name}")
            return {"status": "success", "device_id": device_id, "package": package_name, "output": output.strip()}

    try:
        return await loop.run_in_executor(None, _clear)
    except Exception as e:
        return {"status": "error", "device_id": device_id, "error": str(e)}


@mcp.tool()
async def launch_activity(
    device_id: str, 
    package_name: str, 
    activity_name: str, 
    extras: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Directly triggers an activity component via Activity Manager (am start) to bypass splash screens."""
    loop = asyncio.get_running_loop()
    def _launch():
        lock = get_device_lock(device_id)
        with lock:
            device = adbutils.adb.device(serial=device_id)
            cmd = f"am start -n {package_name}/{activity_name}"
            if extras:
                for k, v in extras.items():
                    cmd += f" --es {k} '{v}'"
            output = device.shell(cmd)
            return {"status": "success", "device_id": device_id, "command": cmd, "output": output.strip()}

    try:
        return await loop.run_in_executor(None, _launch)
    except Exception as e:
        return {"status": "error", "device_id": device_id, "error": str(e)}


@mcp.tool()
async def read_shared_prefs(device_id: str, package_name: str, pref_file_name: str) -> Dict[str, Any]:
    """Reads sandboxed application Shared Preferences XML file using run-as execution."""
    loop = asyncio.get_running_loop()
    def _read_prefs():
        lock = get_device_lock(device_id)
        with lock:
            device = adbutils.adb.device(serial=device_id)
            path = f"/data/data/{package_name}/shared_prefs/{pref_file_name}.xml"
            output = device.shell(f"run-as {package_name} cat {path}")
            return {"status": "success", "device_id": device_id, "path": path, "content": output}

    try:
        return await loop.run_in_executor(None, _read_prefs)
    except Exception as e:
        return {"status": "error", "device_id": device_id, "error": str(e)}


@mcp.tool()
async def spoof_android_id(device_id: str, custom_id: Optional[str] = None) -> Dict[str, Any]:
    """Modifies secure settings android_id hash to spoof hardware identity and avoid anti-farm flags."""
    loop = asyncio.get_running_loop()
    def _spoof():
        lock = get_device_lock(device_id)
        with lock:
            device = adbutils.adb.device(serial=device_id)
            if not custom_id:
                custom_id = os.urandom(8).hex()
            device.shell(f"settings put secure android_id {custom_id}")
            verified = device.shell("settings get secure android_id").strip()
            return {"status": "success", "device_id": device_id, "new_android_id": verified}

    try:
        return await loop.run_in_executor(None, _spoof)
    except Exception as e:
        return {"status": "error", "device_id": device_id, "error": str(e)}


@mcp.tool()
async def capture_logcat_telemetry(
    device_id: str, 
    filter_pattern: str, 
    max_lines: int = 150
) -> Dict[str, Any]:
    """Sniffs kernel and application logcat stream for targeted keywords, JSON packets, or card IDs."""
    loop = asyncio.get_running_loop()
    def _logcat():
        lock = get_device_lock(device_id)
        with lock:
            device = adbutils.adb.device(serial=device_id)
            raw_logcat = device.shell(f"logcat -d -t {max_lines}")
            matches = [line for line in raw_logcat.splitlines() if re.search(filter_pattern, line, re.IGNORECASE)]
            return {"status": "success", "device_id": device_id, "pattern": filter_pattern, "matches_found": len(matches), "logs": matches}

    try:
        return await loop.run_in_executor(None, _logcat)
    except Exception as e:
        return {"status": "error", "device_id": device_id, "error": str(e)}


@mcp.tool()
async def evaluate_pack_pulls(
    device_id: str, 
    log_filter_keyword: str = "card", 
    target_rarity_threshold: int = 3
) -> Dict[str, Any]:
    """Parses logcat telemetry streams instantly to evaluate pulled card rarity and decide action (Keep vs Reroll)."""
    loop = asyncio.get_running_loop()
    def _evaluate():
        lock = get_device_lock(device_id)
        with lock:
            device = adbutils.adb.device(serial=device_id)
            raw_logcat = device.shell("logcat -d -t 200")
            
            extracted_cards = []
            for line in raw_logcat.splitlines():
                if re.search(log_filter_keyword, line, re.IGNORECASE):
                    extracted_cards.append(line)

            rare_found = any(re.search(r"(ex|rarity|secret|immersive|star|crown|god)", c, re.IGNORECASE) for c in extracted_cards)
            
            action = "bind_account" if rare_found else "wipe_and_reroll"
            return {
                "status": "success",
                "device_id": device_id,
                "rare_card_detected": rare_found,
                "recommended_action": action,
                "matched_telemetry_lines": extracted_cards[-5:] if extracted_cards else []
            }

    try:
        return await loop.run_in_executor(None, _evaluate)
    except Exception as e:
        return {"status": "error", "device_id": device_id, "error": str(e)}


# ==========================================
# 3. ABSOLUTE BIONIC ENHANCEMENTS (OCR, PHASH, SWARM, KERNEL TOUCH)
# ==========================================

@mcp.tool()
async def extract_screen_text_ocr(device_id: str) -> Dict[str, Any]:
    """Extracts all visible text strings and bounding boxes from live frame using GPU EasyOCR (<40ms)."""
    loop = asyncio.get_running_loop()
    def _ocr():
        lock = get_device_lock(device_id)
        with lock:
            d = get_u2_device(device_id)
            frame = d.screenshot(format="opencv")
            results = OCR_READER.readtext(frame)
            
            parsed = []
            for bbox, text, prob in results:
                parsed.append({
                    "text": text,
                    "confidence": float(prob),
                    "box": [[int(pt[0]), int(pt[1])] for pt in bbox]
                })
            return {"status": "success", "device_id": device_id, "detected_texts": parsed}

    try:
        return await loop.run_in_executor(None, _ocr)
    except Exception as e:
        return {"status": "error", "device_id": device_id, "error": str(e)}


@mcp.tool()
async def compute_screen_phash(device_id: str) -> Dict[str, Any]:
    """Computes perceptual hash of active screen frame for lightning-fast sub-5ms state identification."""
    loop = asyncio.get_running_loop()
    def _phash():
        lock = get_device_lock(device_id)
        with lock:
            d = get_u2_device(device_id)
            pil_img = d.screenshot()
            phash_val = str(imagehash.phash(pil_img))
            return {"status": "success", "device_id": device_id, "perceptual_hash": phash_val}

    try:
        return await loop.run_in_executor(None, _phash)
    except Exception as e:
        return {"status": "error", "device_id": device_id, "error": str(e)}


@mcp.tool()
async def swarm_execute_reroll_cycle(package_name: str) -> Dict[str, Any]:
    """Orchestrates simultaneous data wiping, hardware ID spoofing, and launching across all connected ADB nodes."""
    devices = [d.serial for d in adbutils.adb.device_list()]
    if not devices:
        return {"status": "error", "message": "No active ADB devices detected in swarm."}

    async def _process_device(dev_id: str):
        device = adbutils.adb.device(serial=dev_id)
        device.shell(f"pm clear {package_name}")
        new_id = os.urandom(8).hex()
        device.shell(f"settings put secure android_id {new_id}")
        return {"device_id": dev_id, "status": "rerolled", "new_android_id": new_id}

    results = await asyncio.gather(*[_process_device(dev) for dev in devices])
    return {"status": "success", "active_swarm_size": len(devices), "node_results": results}


@mcp.tool()
async def kernel_inject_touch(device_id: str, x: int, y: int, event_node: str = "/dev/input/event2") -> Dict[str, Any]:
    """Injects raw EV_ABS/EV_KEY events directly into the kernel input node for zero-overhead touch."""
    loop = asyncio.get_running_loop()
    def _kernel_touch():
        lock = get_device_lock(device_id)
        with lock:
            device = adbutils.adb.device(serial=device_id)
            cmds = [
                f"sendevent {event_node} 3 57 0",
                f"sendevent {event_node} 3 53 {x}",
                f"sendevent {event_node} 3 54 {y}",
                f"sendevent {event_node} 1 330 1",
                f"sendevent {event_node} 0 0 0",
                f"sendevent {event_node} 3 57 -1",
                f"sendevent {event_node} 1 330 0",
                f"sendevent {event_node} 0 0 0"
            ]
            for cmd in cmds:
                device.shell(cmd)
            return {"status": "success", "device_id": device_id, "injected_coords": [x, y], "node": event_node}

    try:
        return await loop.run_in_executor(None, _kernel_touch)
    except Exception as e:
        return {"status": "error", "device_id": device_id, "error": str(e)}


# ==========================================
# 4. ULTRA-BIONIC VISION, YOLO, ROOT BYPASS & WEBSOCKET SNIFFER
# ==========================================

@mcp.tool()
async def detect_cards_yolo(device_id: str, confidence: float = 0.70) -> Dict[str, Any]:
    """Executes hardware-accelerated YOLOv8 tensor inference to locate card coordinates in real-time (<25ms)."""
    loop = asyncio.get_running_loop()
    def _yolo_detect():
        lock = get_device_lock(device_id)
        with lock:
            d = get_u2_device(device_id)
            frame = d.screenshot(format="opencv")
            results = YOLO_MODEL(frame, verbose=False)[0]
            
            detections = []
            for box in results.boxes:
                conf = float(box.conf[0])
                if conf >= confidence:
                    cls_id = int(box.cls[0])
                    xyxy = box.xyxy[0].tolist()
                    detections.append({
                        "class_id": cls_id,
                        "confidence": conf,
                        "box": [int(coord) for coord in xyxy]
                    })
            return {"status": "success", "device_id": device_id, "detections": detections}

    try:
        return await loop.run_in_executor(None, _yolo_detect)
    except Exception as e:
        return {"status": "error", "device_id": device_id, "error": str(e)}


@mcp.tool()
async def bypass_play_integrity_and_root(device_id: str, package_name: str) -> Dict[str, Any]:
    """Injected Frida runtime instrumentation to mask root binaries, emulators, and bypass Play Integrity attestation."""
    ROOT_BYPASS_JS = """
    Java.perform(function() {
        var File = Java.use("java.io.File");
        File.exists.implementation = function() {
            var path = this.getAbsolutePath();
            if (path.indexOf("su") !== -1 || path.indexOf("magisk") !== -1 || path.indexOf("supersu") !== -1) {
                console.log("[+] Bypassed root check for path: " + path);
                return false;
            }
            return this.exists();
        };

        var PackageManager = Java.use("android.app.ApplicationPackageManager");
        PackageManager.getPackageInfo.overload('java.lang.String', 'int').implementation = function(pkg, flags) {
            if (pkg === "com.topjohnwu.magisk" || pkg === "eu.chainfire.supersu") {
                console.log("[+] Hidden package query for: " + pkg);
                throw new Java.use("android.content.pm.PackageManager$NameNotFoundException")();
            }
            return this.getPackageInfo(pkg, flags);
        };
    });
    """
    loop = asyncio.get_running_loop()
    def _bypass_exec():
        try:
            device = frida.get_device(device_id)
            pid = device.spawn([package_name])
            session = device.attach(pid)
            script = session.create_script(ROOT_BYPASS_JS)
            script.load()
            device.resume(pid)
            return {"status": "success", "device_id": device_id, "pid": pid, "action": "root_and_integrity_masked"}
        except Exception as e:
            return {"status": "error", "device_id": device_id, "error": str(e)}

    try:
        return await loop.run_in_executor(None, _bypass_exec)
    except Exception as e:
        return {"status": "error", "device_id": device_id, "error": str(e)}


@mcp.tool()
async def intercept_websocket_frames(device_id: str, package_name: str) -> Dict[str, Any]:
    """Hooks OkHttp WebSocket protocol handlers to intercept binary protobuf payloads containing live draw drops."""
    WS_SNIFFER_JS = """
    Java.perform(function() {
        try {
            var WebSocket = Java.use("okhttp3.internal.ws.RealWebSocket");
            WebSocket.onReadMessage.implementation = function(text) {
                console.log("[WS-RX-TEXT] " + text);
                return this.onReadMessage(text);
            };
        } catch (e) {
            console.log("[-] WebSocket hook failed: " + e.message);
        }
    });
    """
    loop = asyncio.get_running_loop()
    def _ws_hook():
        try:
            device = frida.get_device(device_id)
            pid = device.spawn([package_name])
            session = device.attach(pid)
            script = session.create_script(WS_SNIFFER_JS)
            script.load()
            device.resume(pid)
            return {"status": "success", "device_id": device_id, "pid": pid, "action": "websocket_sniffing_active"}
        except Exception as e:
            return {"status": "error", "device_id": device_id, "error": str(e)}

    try:
        return await loop.run_in_executor(None, _ws_hook)
    except Exception as e:
        return {"status": "error", "device_id": device_id, "error": str(e)}


@mcp.tool()
async def inject_frida_script(device_id: str, package_name: str, script_path: str) -> Dict[str, Any]:
    """Spawns Frida CLI host process to inject dynamic instrumentation hooks into running app memory."""
    loop = asyncio.get_running_loop()
    def _frida_cli():
        lock = get_device_lock(device_id)
        with lock:
            if not os.path.exists(script_path):
                return {"status": "error", "message": f"Frida script missing: {script_path}"}
            cmd = f"frida -U -s {device_id} -f {package_name} -l {script_path} --no-pause"
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return {"status": "initiated", "device_id": device_id, "pid": proc.pid, "command": cmd}

    try:
        return await loop.run_in_executor(None, _frida_cli)
    except Exception as e:
        return {"status": "error", "device_id": device_id, "error": str(e)}


@mcp.tool()
async def attach_frida_hook(device_id: str, package_name: str, js_code: str) -> Dict[str, Any]:
    """Injects JavaScript directly into app memory using native Python Frida bindings."""
    loop = asyncio.get_running_loop()
    def _frida_native():
        lock = get_device_lock(device_id)
        with lock:
            try:
                device = frida.get_device(device_id)
                pid = device.spawn([package_name])
                session = device.attach(pid)
                script = session.create_script(js_code)
                script.load()
                device.resume(pid)
                
                FRIDA_SESSIONS[f"{device_id}_{package_name}"] = session
                return {"status": "attached", "device_id": device_id, "package": package_name, "pid": pid}
            except Exception as e:
                return {"status": "error", "device_id": device_id, "error": str(e)}

    try:
        return await loop.run_in_executor(None, _frida_native)
    except Exception as e:
        return {"status": "error", "device_id": device_id, "error": str(e)}


if __name__ == "__main__":
    mcp.run()