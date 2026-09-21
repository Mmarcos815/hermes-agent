#!/usr/bin/env python3
"""
Merge base.apk + signed split APK contents into a single merged.apk
using Python's zipfile module (no external zip binary needed).
Preserves original files but adds split's native libs.
Then sign with ripdebug keystore.
"""
import sys
import zipfile
import io
import os
import hashlib
import shutil
import subprocess
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
BASE_APK = os.path.join(HERE, "rip_base.apk")
SIGNED_SPLIT = os.path.join(HERE, "rip_signed", "rip_split_arm64_gadget_signed.apk")
MERGED_APK = os.path.join(HERE, "merged_rip.apk")
KEYSTORE = os.path.join(HERE, "..", "farm_3phones", "debug.keystore")
KEYSTORE_PASS = "ripdebug"
ALIAS = "ripdebug"

def info(msg):
    print(f"[MERGE] {msg}", flush=True)

def error(msg):
    print(f"[MERGE ERROR] {msg}", file=sys.stderr, flush=True)

def compute_crc32(data):
    """Compute ZIP CRC32 for data."""
    import binascii
    return binascii.crc32(data) & 0xFFFFFFFF

def compress_type_from_ext(name):
    """Determine compression type based on file extension."""
    ext = os.path.splitext(name)[1].lower()
    if ext in ('.so', '.dex', '.arsc'):
        return zipfile.ZIP_STORED  # No compression for binaries
    return zipfile.ZIP_DEFLATED

def merge_apks(base_path, split_path, output_path):
    print(f"[MERGE] Reading base APK: {base_path}", flush=True)
    print(f"[MERGE] Reading signed split APK: {split_path}", flush=True)
    print(f"[MERGE] Output: {output_path}", flush=True)
    
    # Read base APK contents
    base_entries = {}
    with zipfile.ZipFile(base_path, 'r') as zf:
        for info in zf.infolist():
            data = zf.read(info.filename)
            base_entries[info.filename] = {
                'data': data,
                'compress_type': info.compress_type,
                'external_attr': info.external_attr,
            }
    
    print(f"[MERGE] Base APK has {len(base_entries)} entries", flush=True)
    
    # Read signed split APK - only take .so files and update stamp-cert if present
    with zipfile.ZipFile(split_path, 'r') as zf:
        split_entries = {}
        for info in zf.infolist():
            split_entries[info.filename] = zf.read(info.filename)
    
    print(f"[MERGE] Signed split has {len(split_entries)} entries", flush=True)
    
    # Extract native .so files from split
    added_so = 0
    for name, data in split_entries.items():
        # Only take .so files from lib/ directory
        if name.startswith('lib/') and name.endswith('.so'):
            base_entries[name] = {
                'data': data,
                'compress_type': zipfile.ZIP_STORED,
                'external_attr': 0o755 << 16,  # executable permission
            }
            added_so += 1
            print(f"[MERGE]   Added split .so: {name} ({len(data)} bytes)", flush=True)
        # Also handle stamp-cert-sha256 if present
        elif name == 'stamp-cert-sha256':
            base_entries[name] = {
                'data': data,
                'compress_type': zipfile.ZIP_STORED,
                'external_attr': 0,
            }
            print(f"[MERGE]   Replaced stamp-cert-sha256 from split", flush=True)
    
    print(f"[MERGE] Merged APK will have {len(base_entries)} entries ({added_so} .so files from split)", flush=True)
    
    # Build merged APK preserving original entry order + adding new .so files
    base_listing = None
    with zipfile.ZipFile(base_path, 'r') as zf_base:
        base_listing = zf_base.infolist()
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf_out:
        # First write all original base entries in order
        for zfi in base_listing:
            entry = base_entries.get(zfi.filename)
            if entry is None:
                continue
            zf_out.writestr(
                zfi.filename,
                entry['data'],
                compress_type=entry['compress_type']
            )
        
        # Then write any new entries (split .so files not in base)
        base_names = {zfi.filename for zfi in base_listing}
        for item_name, item_entry in base_entries.items():
            if item_name not in base_names:
                zf_out.writestr(
                    item_name,
                    item_entry['data'],
                    compress_type=item_entry['compress_type']
                )
                print(f"[MERGE]   Appended new entry: {item_name}", flush=True)
    
    print(f"[MERGE] Created merged APK: {output_path} ({os.path.getsize(output_path)} bytes)", flush=True)
    
    # Update ZIP comment if base APK had one
    with zipfile.ZipFile(base_path, 'r') as zf_base:
        original_comment = zf_base.comment
    
    # Set the same comment on merged APK
    with zipfile.ZipFile(output_path, 'a') as zf_out:
        zf_out.comment = original_comment
    
    print(f"[MERGE] Preserved ZIP comment: {len(original_comment)} bytes", flush=True)

def sign_apk(apk_path, keystore_path, keystore_pass, alias):
    """Sign APK using jarsigner."""
    print(f"[MERGE] Signing {apk_path} with keystore {keystore_path}", flush=True)
    
    jarsigner = r"C:\Program Files\Eclipse Adoptium\jdk-21.0.11.10-hotspot\bin\jarsigner.exe"
    
    cmd = [
        jarsigner,
        '-keystore', keystore_path,
        '-storepass', keystore_pass,
        '-keypass', keystore_pass,
        apk_path,
        alias,
    ]
    
    print(f"[MERGE] Running: {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"[MERGE ERROR] jarsigner failed: {result.stderr}", file=sys.stderr, flush=True)
        return False
    
    print(f"[MERGE] jarsigner output: {result.stdout[:500]}", flush=True)
    return True

def main():
    info("Starting APK merge + signing pipeline")
    
    if not os.path.exists(BASE_APK):
        error(f"Base APK not found: {BASE_APK}")
        sys.exit(1)
    
    if not os.path.exists(SIGNED_SPLIT):
        error(f"Signed split APK not found: {SIGNED_SPLIT}")
        sys.exit(1)
    
    info("Step 1: Merging base + split native libs")
    merge_apks(BASE_APK, SIGNED_SPLIT, MERGED_APK)
    
    info("Step 2: Signing merged APK")
    if not sign_apk(MERGED_APK, KEYSTORE, KEYSTORE_PASS, ALIAS):
        error("Signing failed")
        sys.exit(1)
    
    info("Step 3: Verifying signature")
    jarsigner = "C:/Program Files/Eclipse Adoptium/jdk-21.0.11.10-hotspot/bin/jarsigner.exe"
    verify_cmd = [jarsigner, '-verify', '-keystore', KEYSTORE, '-storepass', KEYSTORE_PASS, MERGED_APK]
    verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)
    if verify_result.returncode == 0:
        info("Signature verification: PASSED")
    else:
        error(f"Signature verification: FAILED - {verify_result.stderr}")
        sys.exit(1)
    
    info(f"Done! Merged + signed APK: {MERGED_APK} ({os.path.getsize(MERGED_APK)} bytes)")
    info("Contents:")
    with zipfile.ZipFile(MERGED_APK, 'r') as zf:
        for name in sorted(zf.namelist()):
            if 'lib/arm64-v8a' in name or 'AndroidManifest' in name or 'META-INF' in name:
                info(f"  {name}")

if __name__ == '__main__':
    main()
