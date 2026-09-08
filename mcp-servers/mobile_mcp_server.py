"""Mobile MCP Server — mobile security analysis tools.

Provides MCP tools for Android/iOS app security analysis:
- apk_analyze: Analyze APK files (manifest, permissions, secrets)
- plist_parse: Parse iOS plist files (ATS, permissions, URL schemes)
- frida_trace: Simulate Frida dynamic instrumentation scripts
- objection: Simulate Objection runtime exploration commands
- sqlite_extract: Extract data from app SQLite databases
"""

import hashlib
import json
import os
import re
import sqlite3
import zipfile
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mobile-security")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok(data: dict[str, Any]) -> str:
    """Wrap result in a standard JSON envelope."""
    return json.dumps({"ok": True, **data}, indent=2, default=str)


def _err(message: str) -> str:
    """Wrap error in a standard JSON envelope."""
    return json.dumps({"ok": False, "error": message}, indent=2)


# Common Android dangerous permissions worth flagging
DANGEROUS_PERMISSIONS = {
    "android.permission.READ_SMS", "android.permission.SEND_SMS",
    "android.permission.RECEIVE_SMS", "android.permission.READ_CONTACTS",
    "android.permission.WRITE_CONTACTS", "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.ACCESS_COARSE_LOCATION", "android.permission.RECORD_AUDIO",
    "android.permission.CAMERA", "android.permission.READ_PHONE_STATE",
    "android.permission.CALL_PHONE", "android.permission.READ_CALL_LOG",
    "android.permission.WRITE_CALL_LOG", "android.permission.USE_BIOMETRIC",
    "android.permission.USE_FINGERPRINT", "android.permission.READ_EXTERNAL_STORAGE",
    "android.permission.WRITE_EXTERNAL_STORAGE", "android.permission.MANAGE_EXTERNAL_STORAGE",
    "android.permission.SYSTEM_ALERT_WINDOW", "android.permission.BIND_ACCESSIBILITY_SERVICE",
    "android.permission.BIND_DEVICE_ADMIN",
}

# Secret patterns for static scanning
SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("aws_access_key", re.compile(r"(?i)AKIA[0-9A-Z]{16}")),
    ("aws_secret_key", re.compile(r"(?i)(?:secret|key)[\s\"']{0,3}[:=][\s\"']{0,3}[A-Za-z0-9/+=]{40}")),
    ("google_api_key", re.compile(r"AIza[0-9A-Za-z_\-]{35}")),
    ("firebase_url", re.compile(r"https://[a-z0-9-]+\.firebaseio\.com")),
    ("slack_token", re.compile(r"xox[abprs]-[0-9A-Za-z\-]{10,48}")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----")),
    ("generic_secret", re.compile(r"(?i)(?:api_key|apikey|secret|token|password)[\s\"']{0,3}[:=][\s\"']{0,3}[\"']([A-Za-z0-9_\-]{16,64})[\"']")),
    ("jwt", re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
]


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def apk_analyze(path: str) -> str:
    """Analyze an APK file and extract manifest, permissions, and secrets.

    Args:
        path: Absolute or relative path to the .apk file.

    Returns:
        JSON string with package name, version, permissions (dangerous flagged),
        activities/services/receivers/providers, and discovered secrets.
    """
    apk_path = Path(path)
    if not apk_path.exists():
        return _err(f"APK not found: {path}")
    if not zipfile.is_zipfile(apk_path):
        return _err("Not a valid ZIP/APK file")

    result: dict[str, Any] = {
        "file": str(apk_path),
        "size_bytes": apk_path.stat().st_size,
        "sha256": hashlib.sha256(apk_path.read_bytes()).hexdigest(),
        "package": None,
        "version_name": None,
        "version_code": None,
        "min_sdk": None,
        "target_sdk": None,
        "permissions": [],
        "dangerous_permissions": [],
        "activities": [],
        "services": [],
        "receivers": [],
        "providers": [],
        "uses cleartext": False,
        "debuggable": False,
        "secrets": [],
        "files_scanned": 0,
    }

    with zipfile.ZipFile(apk_path) as zf:
        names = zf.namelist()

        # --- Extract components from binary AndroidManifest.xml strings ---
        manifest_data = _extract_manifest_strings(zf, names)
        result["permissions"] = sorted(manifest_data.get("permissions", []))
        result["dangerous_permissions"] = sorted(
            p for p in result["permissions"] if p in DANGEROUS_PERMISSIONS
        )
        result["activities"] = sorted(manifest_data.get("activities", []))
        result["services"] = sorted(manifest_data.get("services", []))
        result["receivers"] = sorted(manifest_data.get("receivers", []))
        result["providers"] = sorted(manifest_data.get("providers", []))
        result["package"] = manifest_data.get("package")
        result["version_name"] = manifest_data.get("version_name")
        result["version_code"] = manifest_data.get("version_code")
        result["min_sdk"] = manifest_data.get("min_sdk")
        result["target_sdk"] = manifest_data.get("target_sdk")
        result["uses cleartext"] = manifest_data.get("usesCleartextTraffic", False)
        result["debuggable"] = manifest_data.get("debuggable", False)

        # --- Secret scan across all files ---
        secrets: list[dict[str, Any]] = []
        for name in names:
            result["files_scanned"] += 1
            if any(name.endswith(ext) for ext in (".dex", ".so", ".apk", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp3", ".mp4", ".ogg")):
                continue
            try:
                content = zf.read(name).decode("utf-8", errors="ignore")
            except Exception:
                continue
            for label, pattern in SECRET_PATTERNS:
                for match in pattern.finditer(content):
                    secrets.append({
                        "type": label,
                        "file": name,
                        "match": match.group(0)[:80],
                    })
        result["secrets"] = secrets

    return _ok({"apk": result})


def _extract_manifest_strings(zf: zipfile.ZipFile, names: list[str]) -> dict[str, Any]:
    """Parse human-readable strings from binary AndroidManifest.xml.

    This is a best-effort extraction — for full fidelity use `apkanalyzer` or
    `androguard`, but this catches the common component + permission names
    that survive as plain strings in the binary XML.
    """
    data: dict[str, Any] = {
        "permissions": [], "activities": [], "services": [],
        "receivers": [], "providers": [],
    }

    if "AndroidManifest.xml" not in names:
        return data

    raw = zf.read("AndroidManifest.xml")
    # Binary XML string pool — extract printable ASCII runs >= 4 chars
    text = raw.decode("latin-1", errors="ignore")

    # Permission declarations
    for m in re.finditer(r"android\.permission\.[A-Z_]+", text):
        perm = m.group(0)
        if perm not in data["permissions"]:
            data["permissions"].append(perm)

    # Component names (heuristic: after android:name="..." near component tags)
    for comp_type, tag in [("activities", "activity"), ("services", "service"),
                           ("receivers", "receiver"), ("providers", "provider")]:
        pattern = re.compile(tag + r'[^>]*?android:name="([^"]+)"')
        for m in pattern.finditer(text):
            name = m.group(1)
            if name not in data[comp_type]:
                data[comp_type].append(name)

    # Package + versions
    pkg_match = re.search(r'package="([^"]+)"', text)
    if pkg_match:
        data["package"] = pkg_match.group(1)
    vn = re.search(r'versionName="([^"]+)"', text)
    if vn:
        data["version_name"] = vn.group(1)
    vc = re.search(r'versionCode="([^"]+)"', text)
    if vc:
        data["version_code"] = vc.group(1)
    ms = re.search(r'minSdkVersion="([^"]+)"', text)
    if ms:
        data["min_sdk"] = ms.group(1)
    ts = re.search(r'targetSdkVersion="([^"]+)"', text)
    if ts:
        data["target_sdk"] = ts.group(1)
    ct = re.search(r'usesCleartextTraffic="([^"]+)"', text)
    if ct:
        data["usesCleartextTraffic"] = ct.group(1).lower() == "true"
    dbg = re.search(r'debuggable="([^"]+)"', text)
    if dbg:
        data["debuggable"] = dbg.group(1).lower() == "true"

    return data


@mcp.tool()
def plist_parse(path: str) -> str:
    """Parse an iOS Info.plist and extract ATS, permissions, and URL schemes.

    Args:
        path: Absolute or relative path to the .plist file.

    Returns:
        JSON string with bundle info, ATS config, permissions, URL schemes,
        and any embedded secrets.
    """
    try:
        import plistlib
    except ImportError:
        return _err("plistlib is required (Python stdlib)")

    plist_path = Path(path)
    if not plist_path.exists():
        return _err(f"Plist not found: {path}")

    try:
        with open(plist_path, "rb") as f:
            plist = plistlib.load(f)
    except Exception as exc:
        return _err(f"Failed to parse plist: {exc}")

    # App Transport Security
    ats_raw = plist.get("NSAppTransportSecurity", {})
    ats_summary: dict[str, Any] = {}
    if isinstance(ats_raw, dict):
        allows_all = ats_raw.get("NSAllowsArbitraryLoads", False)
        exceptions = ats_raw.get("NSExceptionDomains", {})
        ats_summary = {
            "allows_arbitrary_loads": bool(allows_all),
            "exception_count": len(exceptions) if isinstance(exceptions, dict) else 0,
            "exception_domains": list(exceptions.keys()) if isinstance(exceptions, dict) else [],
            "exceptions_detail": exceptions,
        }

    # Permission usage descriptions
    permission_keys = {
        k: v for k, v in plist.items()
        if isinstance(k, str) and k.endswith("UsageDescription")
    }

    # URL schemes
    url_schemes: list[str] = []
    cfbundle_url_types = plist.get("CFBundleURLTypes", [])
    if isinstance(cfbundle_url_types, list):
        for entry in cfbundle_url_types:
            if isinstance(entry, dict) and "CFBundleURLSchemes" in entry:
                url_schemes.extend(entry["CFBundleURLSchemes"])

    result: dict[str, Any] = {
        "file": str(plist_path),
        "bundle_id": plist.get("CFBundleIdentifier"),
        "bundle_name": plist.get("CFBundleName"),
        "display_name": plist.get("CFBundleDisplayName"),
        "version": plist.get("CFBundleShortVersionString"),
        "minimum_os": plist.get("MinimumOSVersion"),
        "ats": ats_summary,
        "permissions": permission_keys,
        "url_schemes": sorted(set(url_schemes)),
        "launch_storyboard": plist.get("UILaunchStoryboardName"),
        "supported_orientations": plist.get("UISupportedInterfaceOrientations", []),
    }

    # Secret scan on raw plist text
    raw_text = json.dumps(plist, default=str)
    secrets: list[dict[str, str]] = []
    for label, pattern in SECRET_PATTERNS:
        for match in pattern.finditer(raw_text):
            secrets.append({"type": label, "match": match.group(0)[:80]})
    result["secrets"] = secrets

    return _ok({"plist": result})


@mcp.tool()
def frida_trace(target: str, class_pattern: str, method_pattern: str = "*") -> str:
    """Generate a Frida instrumentation script for dynamic tracing.

    Simulates a Frida trace by producing a ready-to-use JavaScript hook
    that intercepts Objective-C/Swift methods (iOS) or Java methods (Android)
    matching the given patterns.

    Args:
        target: Bundle ID (iOS) or package name (Android) to attach to.
        class_pattern: Glob pattern for classes to hook (e.g., "*Auth*", "NSURL*").
        method_pattern: Glob pattern for methods to hook (default: all).

    Returns:
        JSON string with the generated Frida JS and usage instructions.
    """
    # Detect platform heuristic
    is_ios = "." not in target and any(c.isupper() for c in target[:3])
    platform = "iOS" if is_ios else "Android"

    js_script = _generate_frida_js(target, class_pattern, method_pattern, platform)

    return _ok({
        "target": target,
        "platform": platform,
        "class_pattern": class_pattern,
        "method_pattern": method_pattern,
        "script": js_script,
        "instructions": [
            f"1. Install Frida: pip install frida-tools",
            f"2. Attach: frida -U -n \"{target}\" -l trace.js --no-pause",
            f"   Or spawn: frida -U -f {target} -l trace.js",
            f"3. Hooked calls print to stdout with arguments and return values.",
        ],
    })


def _generate_frida_js(target: str, cls_pat: str, meth_pat: str, platform: str) -> str:
    """Generate Frida JavaScript for method tracing."""
    if platform == "iOS":
        # Convert glob to JS regex-ish class match
        cls_regex = cls_pat.replace("*", ".*").replace("?", ".")
        script = f"""// Frida trace for iOS target: {target}
// Classes matching: {cls_pat}, Methods matching: {meth_pat}

var pattern = /{cls_regex}/i;

function traceClass(cls) {{
    if (!pattern.test(cls)) return;
    var methods = cls.$ownMethods || [];
    var methRegex = new RegExp("{meth_pat.replace('*', '.*').replace('?', '.')}", 'i');
    methods.forEach(function(m) {{
        if (!methRegex.test(m)) return;
        try {{
            Interceptor.attach(cls.getImplementationFromString(m).implementation, {{
                onEnter: function(args) {{
                    console.log("[+] " + cls + " " + m);
                    console.log("    args: " + JSON.stringify([].slice.call(args, 0, 4)));
                }},
                onLeave: function(retval) {{
                    console.log("    => " + retval);
                }}
            }});
        }} catch(e) {{}}
    }});
}}

if (ObjC.available) {{
    for (var cls in ObjC.classes) {{
        if (ObjC.classes.hasOwnProperty(cls)) traceClass(ObjC.classes[cls]);
    }}
    console.log("[*] Hooking complete for " + target);
}} else {{
    console.log("[!] Objective-C runtime not available");
}}
"""
    else:
        cls_regex = cls_pat.replace("*", ".*").replace("?", ".")
        script = f"""// Frida trace for Android target: {target}
// Classes matching: {cls_pat}, Methods matching: {meth_pat}

Java.perform(function() {{
    var methRegex = new RegExp("{meth_pat.replace('*', '.*').replace('?', '.')}", 'i');
    Java.enumerateLoadedClasses({{
        onMatch: function(className) {{
            if (!/{cls_regex}/i.test(className)) return;
            try {{
                var cls = Java.use(className);
                var methods = cls.class.getDeclaredMethods();
                methods.forEach(function(method) {{
                    var mname = method.getName();
                    if (!methRegex.test(mname)) return;
                    try {{
                        cls[mname].overloads.forEach(function(overload) {{
                            overload.implementation = function() {{
                                console.log("[+] " + className + "." + mname);
                                var args = [].slice.call(arguments);
                                console.log("    args: " + JSON.stringify(args));
                                var ret = this[mname].apply(this, arguments);
                                console.log("    => " + ret);
                                return ret;
                            }};
                        }});
                    }} catch(e) {{}}
                }});
            }} catch(e) {{}}
        }},
        onComplete: function() {{
            console.log("[*] Hooking complete for " + target);
        }}
    }});
}});
"""
    return script


@mcp.tool()
def objection(target: str, action: str = "explore") -> str:
    """Generate Objection runtime exploration commands.

    Objection wraps Frida for interactive app exploration. This tool returns
    the exact commands to run for common runtime investigation tasks.

    Args:
        target: Package name (Android) or bundle ID (iOS).
        action: One of explore, jailbreak, ui, memory, sqlite, hooking.

    Returns:
        JSON string with Objection commands and expected output descriptions.
    """
    actions: dict[str, dict[str, Any]] = {
        "explore": {
            "commands": [
                f"objection -g {target} explore",
                "ios sslpinning disable",
                "android sslpinning disable",
                "env",
                "ios info",
                "android info",
            ],
            "description": "Interactive exploration session — enumerate classes, env, and disable SSL pinning.",
        },
        "jailbreak": {
            "commands": [
                f"objection -g {target} explore",
                "ios jailbreak disable",
                "android jailbreak disable",
            ],
            "description": "Disable root/jailbreak detection.",
        },
        "ui": {
            "commands": [
                f"objection -g {target} explore",
                "ios ui dump",
                "ios ui alert",
                "android hooking watch class android.app.Activity",
            ],
            "description": "Dump UI hierarchy, monitor alerts, trace activity lifecycle.",
        },
        "memory": {
            "commands": [
                f"objection -g {target} explore",
                "memory list modules",
                "memory list exports libnative.so",
                "memory dump all /tmp/memdump",
                "memory search \"password\" --string",
            ],
            "description": "Inspect loaded modules, exports, and search memory for secrets.",
        },
        "sqlite": {
            "commands": [
                f"objection -g {target} explore",
                "sqlite execute /data/data/{target}/databases/app.db \".tables\"",
                "sqlite execute /data/data/{target}/databases/app.db \"SELECT * FROM users LIMIT 20;\"",
            ],
            "description": "Execute SQL on the app's on-device databases.",
        },
        "hooking": {
            "commands": [
                f"objection -g {target} explore",
                "android hooking list classes",
                "android hooking watch class com.example.AuthManager",
                "android hooking watch method com.example.AuthManager.isAuthenticated --dump-args --dump-return",
            ],
            "description": "Hook classes and methods for runtime inspection.",
        },
    }

    if action not in actions:
        return _err(f"Unknown action '{action}'. Valid: {list(actions)}")

    result = actions[action]
    return _ok({
        "target": target,
        "action": action,
        "commands": result["commands"],
        "description": result["description"],
        "note": "Run these inside an Objection REPL after connecting to the target app.",
    })


@mcp.tool()
def sqlite_extract(path: str, query: str = "SELECT name FROM sqlite_master WHERE type='table';") -> str:
    """Extract data from an app SQLite database.

    Args:
        path: Absolute or relative path to the .db / .sqlite file.
        query: SQL query to execute (default: list all tables).

    Returns:
        JSON string with schema summary and query results.
    """
    db_path = Path(path)
    if not db_path.exists():
        return _err(f"Database not found: {path}")

    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except sqlite3.OperationalError as exc:
        return _err(f"Cannot open database: {exc}")

    result: dict[str, Any] = {
        "file": str(db_path),
        "size_bytes": db_path.stat().st_size,
        "tables": [],
        "query": query,
        "columns": [],
        "rows": [],
        "row_count": 0,
    }

    try:
        cursor = conn.cursor()
        # Schema: all tables
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
        for name, sql in cursor.fetchall():
            result["tables"].append({"name": name, "sql": sql})

        # User query
        cursor.execute(query)
        if cursor.description:
            result["columns"] = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            result["row_count"] = len(rows)
            for row in rows[:1000]:
                result["rows"].append(list(row))
        conn.close()
    except sqlite3.Error as exc:
        conn.close()
        return _err(f"SQL error: {exc}")

    return _ok({"database": result})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
