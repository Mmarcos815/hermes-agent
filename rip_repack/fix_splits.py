#!/usr/bin/env python3
"""Fix Rip Rush merged APK: remove split requirement from manifest XML."""

import zipfile
import shutil
import sys
import os
from xml.etree import ElementTree as ET

NS = 'http://schemas.android.com/apk/res/android'
NS_PREFIX = '{%s}' % NS

def fix_manifest_zipped(merged_apk, output_apk):
    """Extract AndroidManifest.xml from merged APK, remove split attrs, repackage."""
    tmp_dir = '/tmp/apk_fix'
    os.makedirs(tmp_dir, exist_ok=True)
    
    # Extract manifest
    with zipfile.ZipFile(merged_apk, 'r') as zf:
        with open(os.path.join(tmp_dir, 'AndroidManifest.xml'), 'wb') as f:
            f.write(zf.read('AndroidManifest.xml'))
        # Extract splits0.xml if present
        try:
            with open(os.path.join(tmp_dir, 'splits0.xml'), 'wb') as f:
                f.write(zf.read('res/xml/splits0.xml'))
            has_splits = True
        except KeyError:
            has_splits = False
        # Extract stamp-cert-sha256 if present
        try:
            with open(os.path.join(tmp_dir, 'stamp-cert-sha256'), 'wb') as f:
                f.write(zf.read('stamp-cert-sha256'))
            has_stamp = True
        except KeyError:
            has_stamp = False
        # Copy all other files
        for name in zf.namelist():
            if name not in ('AndroidManifest.xml', 'res/xml/splits0.xml', 'stamp-cert-sha256'):
                zf.extract(name, tmp_dir)
    
    # Read and fix manifest XML
    with open(os.path.join(tmp_dir, 'AndroidManifest.xml'), 'rb') as f:
        raw = f.read()
    
    # Parse as binary XML (android's format) — actually this is axml, not plain XML
    # The file is in Android's binary XML format, we need to handle it differently
    # Let's check the first bytes
    print(f"[FIX] Manifest first bytes: {raw[:16].hex()}")
    
    if raw[:2] == b'\x03\x00':  # Android binary XML format
        print("[FIX] Manifest is in Android binary XML format (axml)")
        print("[FIX] We need to use a different approach - modify zip directly")
        # For axml, we can modify the raw bytes to remove the split attribute
        # The attribute android:requiredSplitTypes="base__abi" is encoded in the axml
        # Let's try to find and remove it using byte pattern matching
        
        # Try using aapt2 or apktool to decode/modify
        # For now, let's modify the zip comment or use a simpler approach
        # Actually, let's try modifying the APK directly by patching specific bytes
        
        # Search for "base__abi" in the raw bytes
        pattern = b'base__abi'
        idx = raw.find(pattern)
        if idx >= 0:
            print(f"[FIX] Found 'base__abi' at offset {idx}")
            # The attribute value is "base__abi" - we need to remove the entire attribute
            # In axml format, the attribute starts before the value
            # Let's look at the bytes around it
            context = raw[max(0,idx-50):idx+50]
            print(f"[FIX] Context around 'base__abi': {context.hex()}")
            print(f"[FIX] Context as string: {context}")
        
        # Simpler approach: just remove the attribute value by patching
        # Replace "base__abi" with empty string (but this won't work for axml)
        # Better: set requiredSplitTypes="" which means no splits required
        
        # Actually, for Android 15/16 (API 35+), setting requiredSplitTypes="" should work
        # The attribute is android:requiredSplitTypes="base__abi"
        # We can try to patch it to ""
        
        # First, let's check if we can find the attribute name in the axml
        attr_pattern = b'requiredSplitTypes'
        attr_idx = raw.find(attr_pattern)
        if attr_idx >= 0:
            print(f"[FIX] Found 'requiredSplitTypes' at offset {attr_idx}")
            attr_context = raw[max(0,attr_idx-20):attr_idx+100]
            print(f"[FIX] Context around 'requiredSplitTypes': {attr_context[:100]}")
        
        # For now, let's just try to patch the APK by replacing the value
        # In axml, strings are stored in a string pool at the beginning
        # We can try to find "base__abi" in the string pool and replace it with ""
        
        # Check if there's a simpler approach: just delete the attribute from the decoded XML
        # and re-encode using apktool
        print("[FIX] Attempting to use apktool for decoding/re-encoding...")
        
        # The file is axml, so we need apktool to decode it
        # Let's decode using apktool
        import subprocess
        result = subprocess.run([
            'java', '-jar', 
            r'C:\Users\mobil\orca\projects\my 1st\farm_3phones\apktool.jar',
            'd', merged_apk, 
            '-o', os.path.join(tmp_dir, 'decoded'),
            '--force', '-f'
        ], capture_output=True, text=True, timeout=120)
        print(f"[FIX] apktool decode: rc={result.returncode}")
        if result.returncode != 0:
            print(f"[FIX] apktool stderr: {result.stderr[:500]}")
            return False
        
        # Now modify the decoded manifest
        manifest_path = os.path.join(tmp_dir, 'decoded', 'AndroidManifest.xml')
        if os.path.exists(manifest_path):
            print(f"[FIX] Decoded manifest exists: {manifest_path}")
            tree = ET.parse(manifest_path)
            root = tree.getroot()
            
            # Remove requiredSplitTypes attribute
            if '{}requiredSplitTypes'.format(NS_PREFIX) in root.attrib:
                print(f"[FIX] Removing requiredSplitTypes={root.attrib['{}requiredSplitTypes'.format(NS_PREFIX)]}")
                del root.attrib['{}requiredSplitTypes'.format(NS_PREFIX)]
            
            # Remove splitTypes attribute if it equals "base__abi" 
            if '{}splitTypes'.format(NS_PREFIX) in root.attrib:
                if root.attrib['{}splitTypes'.format(NS_PREFIX)] == 'base__abi':
                    print(f"[FIX] Removing splitTypes=base__abi")
                    del root.attrib['{}splitTypes'.format(NS_PREFIX)]
            
            # Remove splits0.xml if we want to fully eliminate split support
            # But we should keep it as it might be needed for other splits
            # Actually, let's remove the meta-data that references splits
            for child in list(root):
                if child.tag.endswith('meta-data'):
                    name = child.get('{}name'.format(NS_PREFIX))
                    if name and 'split' in name.lower():
                        print(f"[FIX] Removing meta-data: {name}")
                        root.remove(child)
            
            # Write back
            tree.write(manifest_path, xml_declaration=True, encoding='utf-8')
            print(f"[FIX] Modified manifest written")
        
        # Rebuild using apktool
        result = subprocess.run([
            'java', '-jar',
            r'C:\Users\mobil\orca\projects\my 1st\farm_3phones\apktool.jar',
            'b', os.path.join(tmp_dir, 'decoded'),
            '-o', output_apk,
            '--force', '-f'
        ], capture_output=True, text=True, timeout=120)
        print(f"[FIX] apktool build: rc={result.returncode}")
        if result.returncode != 0:
            print(f"[FIX] apktool build stderr: {result.stderr[:500]}")
            return False
        
        # Verify output
        if os.path.exists(output_apk):
            size = os.path.getsize(output_apk)
            print(f"[FIX] Built APK: {output_apk} ({size} bytes)")
            return True
        else:
            print(f"[FIX] Build failed - output APK not found")
            return False
    else:
        print(f"[FIX] Unknown manifest format: {raw[:20]}")
        return False

def main():
    merged_apk = r'C:\Users\mobil\orca\projects\my 1st\rip_repack\merged_rip.apk'
    output_apk = r'C:\Users\mobil\orca\projects\my 1st\rip_repack\merged_fixed.apk'
    
    if not os.path.exists(merged_apk):
        print(f"[FIX ERROR] Merged APK not found: {merged_apk}")
        sys.exit(1)
    
    print(f"[FIX] Input: {merged_apk} ({os.path.getsize(merged_apk)} bytes)")
    print(f"[FIX] Output: {output_apk}")
    
    if fix_manifest_zipped(merged_apk, output_apk):
        print(f"[FIX] SUCCESS - Fixed APK created: {output_apk}")
    else:
        print(f"[FIX] FAILED - Could not fix APK")
        sys.exit(1)

if __name__ == '__main__':
    main()
