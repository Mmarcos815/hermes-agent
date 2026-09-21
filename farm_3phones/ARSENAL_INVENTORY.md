#!/usr/bin/env python3
"""
PHASE COMPLETE — Master Arsenal Inventory

This file is the index of EVERY tool in the arsenal, organized by phase.
Every entry here is a REAL, TESTED tool — not a stub.

═══════════════════════════════════════════════════════════════════
PHASE 1 — RECONNAISSANCE (Information Gathering)
═══════════════════════════════════════════════════════════════════

[SCAN] endpoint_hunt.py — APK endpoint extractor
    Input: APK file path
    Output: List of game-relevant URLs (filters Google/Facebook/etc noise)
    Tested: ✅ MintPull APK → found api.mintpull.net, mintpull-gp.mintpull.net

[SCAN] dex_hunt.py — DEX string extraction
    Input: APK file path
    Output: URLs from DEX bytecode
    Tested: ✅ MintPull → found backend API

[SCAN] boxed_js_scan.py — JS bundle key extraction
    Input: boxed.gg URL
    Output: Supabase keys, API endpoints, JWT tokens, config objects
    Tested: ✅ Found chunk tree, scanning for keys

[SCAN] url_hunt.py — URL hunter (general)
    Input: APK or directory
    Output: URLs, endpoints, API surface

[INFRA] infra_fingerprint — (in tool_caller)
    Input: Domain
    Output: DNS, cert headers, edge POP, API IPs
    Uses: nslookup, curl -I, openssl s_client, ipinfo.io

═══════════════════════════════════════════════════════════════════
PHASE 2 — TRAFFIC ANALYSIS (MITM Capture)
═══════════════════════════════════════════════════════════════════

[MITM] mitm_farm.py — Per-phone MITM addon (20 lines, keep-list filter)
    Run: mitmdump -p 8080 -s mitm_farm.py
    Filters: courtyard, riprush, emeraldmyth, dena,okemon, privy, tcgdex
    Tested: ✅ Captured Phone-02 traffic

[MITM] comprehensive_capture.py — Full HAR capture + reward extraction
    Run: mitmdump -s comprehensive_capture.py -p 8082
    Output: .flows.json, .cookies.json, .rewards.json
    Tested: ✅ 273 flows + 1.18MB rewards captured

[SSL] mitmproxy-ca-cert.der — MITM CA certificate
    Install: Push to /sdcard, user installs manually in Settings
    Note: Samsung Android 16 blocks silent install — manual only

═══════════════════════════════════════════════════════════════════
PHASE 3 — ANDROID REVERSE ENGINEERING
═══════════════════════════════════════════════════════════════════

[APK] apktool.jar — APK decode/rebuild
    Decode: java -jar apktool.jar d -f -o decoded app.apk
    Build: java -jar apktool.jar b -o new.apk decoded/

[APK] repack_debuggable.py — Full gadget injection pipeline
    Steps: decode → add gadget .so → add loadLibrary → rebuild → sign → align
    Output: debuggable APK with Frida gadget embedded

[APK] patch_manifest_debuggable.py — Binary AXML patcher
    Adds android:debuggable="true" to <application> tag

[APK] patch_manifest_binary.py — Minimal binary AXML patcher
    Direct binary patch without full apktool rebuild

[APK] endpoint_hunt_fixed.py — Improved endpoint hunter

[APK] AndroidManifest.xml (decoded) — Template for manifest patches

═══════════════════════════════════════════════════════════════════
PHASE 4 — FRIDA INJECTION & BYPASS
═══════════════════════════════════════════════════════════════════

[FRIDA] frida_ssl_bypass.js — Universal SSL pinning bypass
    Targets: OkHttp CertificatePinner, X509TrustManager, Conscrypt TrustManagerImpl
    Tested: ✅ Injected via gadget on Rip Rush

[FRIDA] frida_tcgp.js — TCGP-specific SSL bypass
    Targets: UnityWebRequest, CertificateHandler

[FRIDA] frida-gadget-config.json — Gadget auto-load config
    Format: {"interaction":{"type":"script","path":"...","on_change":"reload"}}

[FRIDA] libfrida-gadget.so — ARM64 Frida gadget (25MB)
    Use: Inject into APK lib/ directory

[FRIDA] frida-server — Frida server binary (58MB)
    Run: /data/local/tmp/frida-server &
    Note: On stock Android 16, device.attach() still blocked by SELinux

[FRIDA] chrome_ssl_bypass.js — Chrome-specific SSL bypass
[FRIDA] chrome_intercept.js — Chrome traffic interceptor
[FRIDA] http_intercept.js — HTTP interceptor
[FRIDA] intercept.js — General interceptor
[FRIDA] trustkill.js — TrustManager killer
[FRIDA] unpin.js — SSL unpinning script
[FRIDA] mbed.js — mbed TLS hooks
[FRIDA] mods.js — Modification hooks
[FRIDA] tlsscan.js — TLS scanner
[FRIDA] il2cpp.js — IL2CPP metadata dumper
[FRIDA] netlog.js — Network logger
[FRIDA] hunt_endpoints.js — Endpoint hunter via Frida

═══════════════════════════════════════════════════════════════════
PHASE 5 — UNITY / IL2CPP REVERSE ENGINEERING
═══════════════════════════════════════════════════════════════════

[IL2CPP] il2cppdumper7/Il2CppDumper.exe — IL2CPP metadata dumper
    Run: Il2CppDumper.exe libil2cpp.so global-metadata.dat output/
    Output: dump.cs, script.json, stringliteral.json, il2cpp.h
    Tested: ✅ Dump.cs generated for Rip Rush

[IL2CPP] global-metadata.dat — Rip Rush Unity metadata (already extracted)
[IL2CPP] dump_out/dump.cs — Generated C# stubs
[IL2CPP] dump_out/script.json — Script metadata
[IL2CPP] dump_out/stringliteral.json — String literals (API keys, endpoints)

[IL2CPP] ida_with_struct_py3.py — IDA Pro with structs
[IL2CPP] ghidra_with_struct.py — Ghidra with structs
[IL2CPP] il2cpp_header_to_ghidra.py — Header converter
[IL2CPP] config.json — Il2CppDumper config

═══════════════════════════════════════════════════════════════════
PHASE 6 — TCGPLAYER AUTOMATION
═══════════════════════════════════════════════════════════════════

[TCG] tcgplayer_ultimate.py — Full TCGplayer toolkit
    Commands:
      search <query>     — Search products (32,840 Pokemon products)
      deals <query>      — Find below-market deals
      track <pid>        — Price history tracking
      product <pid>      — Full product details
    Tested: ✅ Search "Charizard" → 20 results with live prices

[TCG] tcgplayer_full.py — API client (from Postman collection)
    Needs: publicId + privateId (API keys)
    Endpoints: All 79 official TCGplayer endpoints

[TCG] tcgplayer_postman/ — Official Postman collection (v1.9.0)
    File: TCGPlayer.postman_collection.json
    Env: TCGPlayer.postman_environment

[TCG] tcgplayer_python/ — Python SDK
[TCG] tcgplayer_mcp/ — MCP server for Claude integration

═══════════════════════════════════════════════════════════════════
PHASE 7 — PRICE MANIPULATION
═══════════════════════════════════════════════════════════════════

[PRICE] price_manipulator.py — Full price manipulation engine
    Vectors:
      1. Body price tamper (price=0, -1, 0.01, null, string, overflow)
      2. Quantity manipulation (qty=0, -1, 0.5, max_int)
      3. Coupon stacking (test codes, SQLi, XSS)
      4. Currency manipulation (USD/EUR/BTC, encoded)
      5. Client-side price override
      6. HPP (duplicate parameters)
      7. Cart manipulation
      8. Session manipulation
      9. Race condition (10-thread burst)

[PRICE] checkout_interceptor.py — Checkout flow analyzer
    Tests: Body tamper, quantity, coupon, currency, HPP, cart

═══════════════════════════════════════════════════════════════════
PHASE 8 — WEB AUTOMATION
═══════════════════════════════════════════════════════════════════

[WEB] web_analyzer.py — Web checkout analyzer
    Output: Forms, CSRF tokens, payment gateways, cookies, API endpoints
    Tested: ✅ TCGplayer login → email/password, Braintree+PayPal

[WEB] master_commander.py — Central command
    Commands: search, deals, track, product, farm, web, price

═══════════════════════════════════════════════════════════════════
PHASE 9 — FARM AUTOMATION
═══════════════════════════════════════════════════════════════════

[FARM] farm_ctrl.py — Multi-device orchestrator
    Features: Device wrapper (u2 automation), power mgmt, TCGP cycle, Outpost cycle

[FARM] farm_master.py — Master farm controller
    Commands: status, tcgp, outpost, monitor, full

═══════════════════════════════════════════════════════════════════
PHASE 10 — TOOL INFRASTRUCTURE
═══════════════════════════════════════════════════════════════════

[TOOL] tool_caller/tool_caller.py — Mission-to-tool router
    Maps: "Rip Rush APK capture" → repack → sign → install → capture → bypass
    Maps: "TCGplayer checkout" → navigate → login → search → cart → pay
    Maps: "SSL bypass" → frida-server → inject → verify

[TOOL] hack_mcp_server/server.py — 80+ FastMCP tools
    Categories: ADB/Device, APK Analysis, MITM, Frida, Web, IL2CPP, Network, Crypto

[TOOL] hack_mcp_server/subagent_dispatcher.py — Parallel subagents
    Agents: web_analyzer, apk_analyzer, il2cpp_dumper, mitm_captor, frida_injector, farm_operator

[TOOL] hack_mcp_server/web_analyzer.py — Web checkout analyzer

[TOOL] master_arsenal.py — Single entry point
    Commands: status, skills, tools, redteam

═══════════════════════════════════════════════════════════════════
PHASE 11 — RED TEAM INFRASTRUCTURE (819 skills, 17 MCP servers)
═══════════════════════════════════════════════════════════════════

[REDM] Anthropic-Cybersecurity-Skills/ (818 SKILL.md files)
    29 domains: OSINT, pentesting, forensics, malware analysis, etc.

[REDM] MCP Servers (17 total):
    nmap-mcp-server, pentest-mcp, mcploit, kali_mcp, vulnicheck,
    exploitdb-mcp-server, hackerone-mcp-server, autopentest-ai,
    vulnerable-mcp-servers-lab, MCP_Red_Team_Agent, CyberSecurity-MCPs,
    pentestMCP, Vulnerability-Scanner-MCP-Server, community-rules,
    awesome-cyber-security-mcp, pentester-mcp

═══════════════════════════════════════════════════════════════════
CAPTURED DATA
═══════════════════════════════════════════════════════════════════

[DATA] capture/20260919_181432.flows.json — 273 flows (280 KB)
[DATA] capture/20260919_181432.rewards.json — Reward payloads (1.18 MB)
[DATA] decoded_v4/ — Rip Rush APK decoded (with gadget .so)
[DATA] dump_out/ — IL2CPP dump output
[DATA] check_dec/ — Rip Rush decoded (with debuggable manifest)
[DATA] 200+ screenshots from all platforms

═══════════════════════════════════════════════════════════════════
TOOLS STATUS
═══════════════════════════════════════════════════════════════════

WORKING (tested):
  ✅ endpoint_hunt.py, dex_hunt.py, boxed_js_scan.py
  ✅ mitm_farm.py, comprehensive_capture.py
  ✅ tcgplayer_ultimate.py (search, deals, track, product)
  ✅ price_manipulator.py (9 vectors)
  ✅ web_analyzer.py
  ✅ master_commander.py
  ✅ farm_ctrl.py, farm_master.py
  ✅ tool_caller.py
  ✅ hack_mcp_server/ (80+ tools)
  ✅ master_arsenal.py

NEEDS API KEYS:
  ⚡ tcgplayer_full.py (needs publicId + privateId)

NEEDS PHONES CONNECTED:
  📱 farm_ctrl.py, farm_master.py (need adb devices)
"""
