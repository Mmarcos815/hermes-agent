#!/usr/bin/env python3
"""Boxed.gg JS bundle analysis - extract Supabase keys, API endpoints, config"""

import requests
import re
import json
import sys

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
}

BASE_URL = 'https://boxed.gg/_next/static/chunks/'
MANIFEST_URL = 'https://boxed.gg/_next/static/XBg8IRjwKOrrTAQd6YLzy/_buildManifest.js'

KEY_PATTERNS = {
    'JWT_anon_key': r'eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}',
    'Supabase_anon_key_sb': r'sb_[A-Za-z0-9_-]{20,}',
    'supabase_co_URL': r'https://[a-z0-9]+\.supabase\.co',
    'createClient_call': r'createClient\s*\(',
    'api_boxed_gg_URL': r'api\.boxed\.gg',
    'NEXT_PUBLIC_Var': r'NEXT_PUBLIC_[A-Z_]+',
    'SUPABASE_Var': r'SUPABASE_[A-Z_]+',
    'environment_config': r'(?:process\.env\.|import\.meta\.env\.)[A-Z_]+',
    'LONG_BASE64_STRING': r'["\']([A-Za-z0-9+/=_-]{40,150})["\']',
    'OBJECT_WITH_KEYS': r'\{[^}]*?(?:url|key|secret|token|anon)[^}]*?\}',
    'API_CONFIG_OBJECT': r'\{[^}]*?(?:api|base|endpoint|uri|url)[^}]*?\}',
}


def find_chunk_references(text):
    """Extract all static/chunks/*.js references from text"""
    return set(re.findall(r'"(static/chunks/[^"]+\.js)"', text))


def scan_chunk(chunk_name, patterns=KEY_PATTERNS):
    """Download and scan a single chunk for key patterns"""
    try:
        url = BASE_URL + chunk_name
        r = requests.get(url, timeout=3, headers=HEADERS)
        if r.status_code != 200 or len(r.content) < 100:
            return {}
        
        text = r.text
        results = {}
        for label, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Extract capture groups or use full match
                unique = []
                for m in matches:
                    if isinstance(m, tuple):
                        unique.append(m[0])
                    else:
                        unique.append(m)
                unique = list(set(unique))
                if unique:
                    results[label] = unique[:5]
        return results
    except Exception as e:
        return {'_error': str(e)[:50]}


def main():
    print("=== BOXED.GG JS BUNDLE ANALYSIS ===")
    print()
    
    # Step 1: Get build manifest and extract route-level chunks
    print("[1/5] Fetching build manifest...")
    try:
        r = requests.get(MANIFEST_URL, timeout=10, headers=HEADERS)
        manifest = r.text
        print(f"    Manifest size: {len(manifest)} bytes")
    except Exception as e:
        print(f"    Error: {e}")
        return
    
    # Extract all route-level chunks from __turbopack_load_page_chunks__ calls
    route_chunks = set()
    for m in re.finditer(r'__turbopack_load_page_chunks__\([^)]+\)', manifest):
        chunks = find_chunk_references(m.group(0))
        route_chunks.update(chunks)
    
    print(f"    Route-level chunks: {len(route_chunks)}")
    
    # Step 2: Download route chunks and find their sub-chunk references
    print("[2/5] Discovering full chunk dependency tree...")
    all_chunks = set(route_chunks)
    queue = list(route_chunks)
    scanned = set()
    
    while queue:
        chunk = queue.pop(0)
        if chunk in scanned:
            continue
        scanned.add(chunk)
        
        try:
            url = BASE_URL + chunk
            r = requests.get(url, timeout=3, headers=HEADERS)
            if r.status_code == 200:
                subs = find_chunk_references(r.text)
                new_subs = subs - scanned
                all_chunks.update(new_subs)
                queue.extend(new_subs)
        except:
            pass
    
    print(f"    Total unique chunks in tree: {len(all_chunks)}")
    
    # Step 3: Scan all chunks for keys
    print("[3/5] Scanning chunks for API keys and references...")
    findings = {}
    for chunk_name in sorted(all_chunks):
        results = scan_chunk(chunk_name)
        if results:
            findings[chunk_name] = results
    
    print(f"    Chunks with findings: {len(findings)}")
    
    # Step 4: Display results
    print()
    print("[4/5] RESULTS:")
    print("-" * 60)
    
    if not findings:
        print("    NO API KEYS OR REFERENCES FOUND IN ANY CHUNK")
        print()
        print("    Searching for ANY config-like objects...")
        
        # Last resort: search all chunks for any object with key-like properties
        for chunk_name in sorted(all_chunks):
            try:
                url = BASE_URL + chunk_name
                r = requests.get(url, timeout=2, headers=HEADERS)
                if r.status_code == 200 and len(r.content) > 300:
                    text = r.text
                    # Look for any object literal with key-related property names
                    obj_pattern = r'\{[^}]{0,200}\}'
                    objects = re.findall(obj_pattern, text)
                    interesting = []
                    for obj in objects:
                        obj_lower = obj.lower()
                        if any(kw in obj_lower for kw in ['supabase', 'api.', 'boxed.gg', 'createclient', 
                                                           'next_public_', 'sb_', 'eyj']):
                            interesting.append(obj[:200])
                    
                    if interesting:
                        findings[chunk_name] = {'interesting_objects': interesting[:3]}
            except:
                pass
        
        if findings:
            print(f"    Found {len(findings)} chunks with interesting objects")
            for chunk, data in sorted(findings.items()):
                print(f"\n    --- {chunk} ---")
                for item in data.get('interesting_objects', [])[:2]:
                    print(f"      {item}")
        else:
            print("    Still nothing found.")
    else:
        for chunk, data in sorted(findings.items()):
            print(f"\n    --- {chunk} ---")
            for pattern_name, matches in sorted(data.items()):
                if pattern_name.startswith('_'):
                    continue
                for m in matches[:3]:
                    s = str(m)
                    if len(s) > 120:
                        s = s[:120] + '...'
                    print(f"      {pattern_name}: {s}")
    
    # Step 5: Summary
    print()
    print("[5/5] SUMMARY:")
    print("-" * 60)
    
    # Categorize findings
    jwt_keys = []
    sb_keys = []
    supabase_urls = []
    api_boxed_refs = []
    createclient_refs = []
    next_public_vars = []
    
    for chunk, data in findings.items():
        for label, matches in data.items():
            if label == 'JWT_anon_key':
                jwt_keys.extend(matches)
            elif label == 'Supabase_anon_key_sb':
                sb_keys.extend(matches)
            elif label == 'supabase_co_URL':
                supabase_urls.extend(matches)
            elif label == 'api_boxed_gg_URL':
                api_boxed_refs.extend(matches)
            elif label == 'createClient_call':
                createclient_refs.append(chunk)
            elif label == 'NEXT_PUBLIC_Var':
                next_public_vars.extend(matches)
    
    print(f"    JWT tokens found: {len(jwt_keys)}")
    for k in jwt_keys:
        print(f"      {k[:80]}...")
    
    print(f"    Supabase anon keys (sb_): {len(sb_keys)}")
    for k in sb_keys:
        print(f"      {k}")
    
    print(f"    Supabase URLs: {len(supabase_urls)}")
    for u in supabase_urls:
        print(f"      {u}")
    
    print(f"    api.boxed.gg references: {len(api_boxed_refs)}")
    for r in api_boxed_refs:
        print(f"      {r}")
    
    print(f"    createClient calls: {len(createclient_refs)} chunks")
    for c in createclient_refs[:5]:
        print(f"      {c}")
    
    print(f"    NEXT_PUBLIC_ vars: {len(next_public_vars)}")
    for v in next_public_vars:
        print(f"      {v}")
    
    # Save full findings to file
    with open('/tmp/boxed_findings.json', 'w') as f:
        json.dump(findings, f, indent=2)
    print(f"\n    Full findings saved to /tmp/boxed_findings.json")


if __name__ == '__main__':
    main()
