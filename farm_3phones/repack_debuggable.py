#!/usr/bin/env python3
"""
repack_debuggable.py — APK repack for Frida gadget injection (Path 3).

What it does:
1. Extract existing merged APK
2. Inject libfrida-gadget.so into lib/arm64-v8a/ (already done, but verify)
3. Inject libfrida-gadget.config.so alongside the .so (gadget auto-reads this)
4. Patch AndroidManifest.xml: add android:debuggable="true" to <application>
5. Re-package APK
6. Re-sign with debug keystore (same key for update install)
7. Verify

Why debuggable=true:
- Enables `adb shell run-as com.emeraldmyth.riprush.and` to write to app's private dir
- Needed to push bypass script to /data/data/<pkg>/files/ after install
- Gadget reads config from its own dir (lib/), but script path must be accessible

Gadget config format (libfrida-gadget.config.so in same dir as .so):
  {"interaction":{"type":"script","path":"<script-path>","on_change":"reload"},"teardown":"full"}

Output: farm_3phones/merged_fixed_v5_debuggable.apk
"""

import os
import sys
import shutil
import zipfile
import subprocess
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
APK_PATH = HERE / "merged_fixed_v4.apk"
OUTPUT_APK = HERE / "merged_fixed_v5_debuggable.apk"
GADGET_SO = HERE / "frida-gadget-4f6766907482490cb3cedb216cfce8ca.so"
KEYSTORE = HERE / "debug.keystore"
KEYSTORE_PASS = "ripdebug"
ALIAS = "ripdebug"

ANDROID_SDK = Path(os.environ.get("ANDROID_SDK_ROOT", r"C:\Users\mobil\AppData\Local\Android\Sdk"))
AAPT2 = ANDROID_SDK / "build-tools" / "36.0.0" / "aapt2.exe"
ZIPALIGN = ANDROID_SDK / "build-tools" / "36.0.0" / "zipalign.exe"
APKSIGNER = ANDROID_SDK / "build-tools" / "36.0.0" / "apksigner.bat"

# Gadget config: load script from /data/local/tmp (will be pushed via run-as)
GADGET_CONFIG = '{"interaction":{"type":"script","path":"/data/local/tmp/frida_ssl_bypass.js","on_change":"reload"},"teardown":"full"}'


def info(msg):
    print(f"[REPACK] {msg}", flush=True)


def error(msg):
    print(f"[REPACK ERROR] {msg}", file=sys.stderr, flush=True)


def check_tools():
    """Verify all needed SDK tools exist."""
    for tool, path in [("aapt2", AAPT2), ("zipalign", ZIPALIGN), ("apksigner", APKSIGNER)]:
        if not path.exists():
            error(f"{tool} not found at {path}")
            return False
    return True


def patch_manifest_axml(extract_dir):
    """
    Patch AndroidManifest.xml (binary AXML) to add android:debuggable="true"
    to the <application> element.
    
    Binary AXML format: we need to insert an attribute into the application's
    attribute list. The attribute is:
      namespace URI: http://schemas.android.com/apk/res/android (index in string pool)
      name: debuggable
      value: true (boolean)
    
    For simplicity, we use aapt2 to dump, patch, and rebuild. But aapt2 doesn't
    directly support re-packaging from xmltree. Instead, we use the approach:
    - Decode manifest with androguard to get XML string
    - Modify the XML string
    - Use aapt2 to compile the modified XML back to binary
    """
    manifest_path = extract_dir / "AndroidManifest.xml"
    if not manifest_path.exists():
        error("AndroidManifest.xml not found")
        return False
    
    # Read binary manifest
    raw = manifest_path.read_bytes()
    
    # Check if it's binary AXML (magic 0x0003)
    if raw[:2] != b'\x03\x00':
        info(f"Manifest not binary AXML (magic: {raw[:2].hex()})")
        # Might be already text XML — patch directly
        xml_str = raw.decode('utf-8', errors='replace')
        if 'android:debuggable' not in xml_str:
            xml_str = xml_str.replace('<application', '<application android:debuggable="true"', 1)
            manifest_path.write_text(xml_str)
            info("Patched text XML manifest with debuggable=true")
            return True
        else:
            info("Manifest already has debuggable attribute")
            return True
    
    # Binary AXML patching via string pool manipulation
    # The simplest reliable approach: insert the string "debuggable" into the string pool,
    # then insert an attribute entry into the application element.
    
    # Actually, androguard can do this for us. Let's use a simpler approach:
    # Extract, use androguard to parse, modify, and re-serialize.
    
    # Since androguard's AXML modification is limited, let's try a direct binary patch:
    # The android:debuggable attribute has resource ID 0x0101001f
    # In binary AXML, it's stored as a resource reference.
    
    # For now, try using androguard to get text XML, modify, and use aapt2 to recompile
    try:
        from androguard.core.apk import APK
        # We can't use androguard on an extracted directory easily
        # Instead, do binary string pool patching
        
        # Step 1: Check if "debuggable" string already exists in string pool
        if b'debuggable' in raw:
            info("String 'debuggable' already in string pool")
        else:
            # Need to add "debuggable" to string pool
            # String pool is at offset 8 (after magic + size)
            # Format: numStrings (4 bytes), numStyles (4 bytes), flags (4 bytes),
            # stringsOffset (4 bytes), stylesOffset (4 bytes)
            # Then string offsets array, then string data
            
            # This is complex. Use a simpler approach: modify via apktool or
            # just patch the existing manifest by adding a new attribute.
            
            info("Adding 'debuggable' string to AXML string pool...")
            
            # Find the string pool header
            # AXML magic is 0x00080003 (RES_XML_TYPE)
            # Header size is 8
            # Total size is at offset 4
            
            # For simplicity, we'll use the "android:debuggable" resource ID directly
            # Resource ID 0x0101001f = android:debuggable (boolean)
            # We need to insert this as an attribute in the application element
            
            # Let's use a different approach: patch by adding the attribute
            # using known binary AXML structure
            
            pass
        
        # Alternative: use aapt2 compile from text XML
        # Decode with aapt2, modify, recompile
        # aapt2 dump xmltree gives us text representation
        
        info("Using aapt2-based approach for manifest patching...")
        
        # Dump XML tree
        result = subprocess.run([
            str(AAPT2), "dump", "xmltree", str(APK_PATH), "--file", "AndroidManifest.xml"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            error(f"aapt2 dump failed: {result.stderr}")
            return False
        
        # Parse the tree to find application element line
        xml_lines = result.stdout.splitlines()
        info(f"XML tree has {len(xml_lines)} lines")
        
        # Find "E: application" line and check for debuggable attribute
        app_line = None
        has_debuggable = False
        for i, line in enumerate(xml_lines):
            if 'E: application' in line:
                app_line = i
            if 'debuggable' in line.lower():
                has_debuggable = True
        
        if has_debuggable:
            info("Manifest already has debuggable attribute")
            return True
        
        if app_line is None:
            error("Could not find <application> element in manifest tree")
            return False
        
        info(f"Found <application> at line {app_line}")
        
        # The xmltree output is not directly compilable — aapt2 can't compile from
        # this format back to binary AXML. We need a different approach.
        
        # Best approach for binary AXML: use Python's androguard to modify the
        # manifest in-place, or use apktool.
        
        # Since androguard is now installed, let's use it properly:
        return patch_manifest_with_androguard(extract_dir)
        
    except ImportError:
        error("androguard not available for manifest patching")
        return False


def patch_manifest_with_androguard(extract_dir):
    """Use androguard to patch manifest (works on extracted directory)."""
    try:
        from androguard.core.apk import APK
        from androguard.core.axml import AXMLPrinter, AXMLParser
    except ImportError:
        error("androguard not installed")
        return False
    
    manifest_path = extract_dir / "AndroidManifest.xml"
    raw = manifest_path.read_bytes()
    
    # Parse the binary XML
    # AXMLParser gives us events (start_tag, end_tag, etc.)
    # We need to reconstruct with the added attribute
    
    # Simpler: androguard can parse and we can get the text representation
    try:
        from xml.etree import ElementTree as ET
        
        # Get text XML from androguard
        printer = AXMLPrinter(raw)
        xml_bytes = printer.get_buff()
        xml_str = xml_bytes.decode('utf-8', errors='replace')
        
        info(f"Parsed manifest XML ({len(xml_str)} chars)")
        
        # Check for debuggable
        if 'android:debuggable' in xml_str:
            info("Manifest already has debuggable=true")
            return True
        
        # Add debuggable attribute to <application>
        # Find the <application tag and add the attribute
        if '<application ' in xml_str:
            xml_str = xml_str.replace(
                '<application ',
                '<application android:debuggable="true" ',
                1
            )
            info("Patched: added android:debuggable=true to <application>")
        elif '<application>' in xml_str:
            xml_str = xml_str.replace(
                '<application>',
                '<application android:debuggable="true">',
                1
            )
            info("Patched: added android:debuggable=true to <application>")
        else:
            error("Could not find <application> tag")
            return False
        
        # Now we need to re-encode the XML back to binary AXML format
        # This is the hard part — androguard doesn't have a built-in AXML encoder
        
        # Option 1: Use aapt2 to compile the text XML
        # aapt2 compile accepts text XML and outputs .flat files
        # Then we link them into the APK
        
        text_xml_path = extract_dir / "AndroidManifest_text.xml"
        text_xml_path.write_text(xml_str)
        
        # Use aapt2 to compile text XML to binary
        result = subprocess.run([
            str(AAPT2), "compile", str(text_xml_path), "-o", str(extract_dir / "compiled_manifest.zip")
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            # aapt2 compile expects directory input, not single file
            # Use the directory approach
            info("Using directory-based aapt2 compile...")
            
            # Create temp dir for aapt2 compile
            tmp_compile = Path(tempfile.mkdtemp())
            (tmp_compile / "xml").mkdir()
            (tmp_compile / "xml" / "AndroidManifest.xml").write_text(xml_str)
            
            result = subprocess.run([
                str(AAPT2), "compile", str(tmp_compile / "xml"), "-o", str(extract_dir / "compiled_manifest.zip")
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                error(f"aapt2 compile failed: {result.stderr}")
                # Fallback: keep original manifest, debuggable won't be set
                # But we can still install and use other injection methods
                info("WARNING: Could not patch manifest with debuggable flag")
                info("The APK will still work but won't be debuggable")
                return True  # Not fatal — continue without debuggable
            
            # Extract the compiled manifest from the zip
            with zipfile.ZipFile(extract_dir / "compiled_manifest.zip", 'r') as zf:
                for name in zf.namelist():
                    if 'AndroidManifest' in name:
                        zf.extract(name, extract_dir)
                        # Move to the right place
                        extracted = extract_dir / name
                        if extracted != manifest_path:
                            shutil.move(str(extracted), str(manifest_path))
                        info(f"Installed compiled manifest: {name}")
                        break
            
            # Cleanup
            shutil.rmtree(tmp_compile, ignore_errors=True)
        
        return True
        
    except Exception as e:
        error(f"Manifest patching failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def rebuild_and_sign(extract_dir, output_path):
    """Rebuild APK from extracted directory and sign it."""
    
    info(f"Rebuilding APK: {output_path}")
    
    # Build APK with proper compression
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, extract_dir)
                # Skip the extracted compiled manifest zip
                if arcname.endswith('.zip'):
                    continue
                ext = os.path.splitext(file)[1].lower()
                if ext in ('.so', '.dex', '.arsc'):
                    compress_type = zipfile.ZIP_STORED
                else:
                    compress_type = zipfile.ZIP_DEFLATED
                zf.write(filepath, arcname, compress_type=compress_type)
    
    info(f"Rebuilt APK: {output_path} ({output_path.stat().st_size:,} bytes)")
    
    # Zipalign
    aligned_path = output_path.with_suffix('.aligned.apk')
    result = subprocess.run([
        str(ZIPALIGN), "-p", "-f", "4", str(output_path), str(aligned_path)
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        error(f"zipalign failed: {result.stderr}")
        # Try without zipalign (not strictly required)
        aligned_path = output_path
    else:
        info("APK zipaligned")
        shutil.move(str(aligned_path), str(output_path))
    
    # Sign
    if not KEYSTORE.exists():
        info("Generating debug keystore...")
        subprocess.run([
            "keytool", "-genkey", "-v",
            "-keystore", str(KEYSTORE),
            "-alias", ALIAS,
            "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000",
            "-storepass", KEYSTORE_PASS,
            "-keypass", KEYSTORE_PASS,
            "-dname", "CN=Debug, OU=Debug, O=Debug, L=Debug, S=Debug, C=US"
        ], check=True, capture_output=True)
    
    info(f"Signing APK with {ALIAS}...")
    result = subprocess.run([
        str(APKSIGNER), "sign",
        "--ks", str(KEYSTORE),
        "--ks-pass", f"pass:{KEYSTORE_PASS}",
        "--key-pass", f"pass:{KEYSTORE_PASS}",
        "--ks-key-alias", ALIAS,
        "--v1-signing-enabled", "true",
        "--v2-signing-enabled", "true",
        "--v3-signing-enabled", "true",
        str(output_path)
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        error(f"Signing failed: {result.stderr}")
        return False
    
    info("APK signed successfully")
    
    # Verify
    result = subprocess.run([
        str(APKSIGNER), "verify", "--verbose", str(output_path)
    ], capture_output=True, text=True)
    info(f"Verification: {result.stdout.strip().splitlines()[-1] if result.stdout.strip() else 'unknown'}")
    
    return True


def main():
    info("=" * 60)
    info("APK REPACK — Debuggable + Frida Gadget Native Lib")
    info("=" * 60)
    
    if not APK_PATH.exists():
        error(f"Source APK not found: {APK_PATH}")
        return 1
    
    if not check_tools():
        return 1
    
    # Create temp directory
    tmp_dir = Path(tempfile.mkdtemp(prefix="apk_repack_"))
    extract_dir = tmp_dir / "extracted"
    extract_dir.mkdir()
    
    try:
        # Step 1: Extract APK
        info("\n--- STEP 1: Extract APK ---")
        with zipfile.ZipFile(APK_PATH, 'r') as zf:
            zf.extractall(extract_dir)
        info(f"Extracted {len(list(extract_dir.rglob('*')))} files")
        
        # Step 2: Verify gadget .so exists
        info("\n--- STEP 2: Verify gadget .so ---")
        lib_dir = extract_dir / "lib" / "arm64-v8a"
        gadget_so_path = lib_dir / "libfrida-gadget.so"
        
        if gadget_so_path.exists():
            info(f"Gadget .so present: {gadget_so_path.stat().st_size:,} bytes")
        else:
            # Inject it
            if not GADGET_SO.exists():
                error(f"Gadget .so not found: {GADGET_SO}")
                return 1
            lib_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(GADGET_SO, gadget_so_path)
            info(f"Injected gadget .so: {gadget_so_path.stat().st_size:,} bytes")
        
        # Step 3: Inject gadget config .so
        info("\n--- STEP 3: Inject gadget config ---")
        config_path = lib_dir / "libfrida-gadget.config.so"
        config_path.write_text(GADGET_CONFIG)
        info(f"Gadget config: {config_path} ({len(GADGET_CONFIG)} bytes)")
        
        # Step 4: Patch manifest
        info("\n--- STEP 4: Patch AndroidManifest.xml ---")
        patch_manifest_axml(extract_dir)
        
        # Step 5: Rebuild and sign
        info("\n--- STEP 5: Rebuild & Sign ---")
        if not rebuild_and_sign(extract_dir, OUTPUT_APK):
            return 1
        
        # Step 6: Final verification
        info("\n--- STEP 6: Final Verification ---")
        result = subprocess.run([
            str(AAPT2), "dump", "badging", str(OUTPUT_APK)
        ], capture_output=True, text=True)
        
        for line in result.stdout.splitlines():
            line_lower = line.lower()
            if any(k in line_lower for k in ['debuggable', 'sdkversion', 'native-code', 'package:']):
                info(f"  {line.strip()}")
        
        info("\n" + "=" * 60)
        info(f"OUTPUT: {OUTPUT_APK}")
        info(f"SIZE:   {OUTPUT_APK.stat().st_size:,} bytes")
        info("\nNEXT STEPS:")
        info(f"1. Uninstall old app: adb uninstall com.emeraldmyth.riprush.and")
        info(f"2. Install new APK:   adb install {OUTPUT_APK.name}")
        info(f"3. Push bypass script: adb shell run-as com.emeraldmyth.riprush.and sh -c 'cat > /data/data/com.emeraldmyth.riprush.and/files/frida_ssl_bypass.js' < frida_ssl_bypass.js")
        info(f"4. Copy to /data/local/tmp: adb shell run-as com.emeraldmyth.riprush.and cp /data/data/com.emeraldmyth.riprush.and/files/frida_ssl_bypass.js /data/local/tmp/")
        info(f"5. Launch app: adb shell am start -n com.emeraldmyth.riprush.and/com.unity3d.player.MyUnityPlayerActivity")
        info("=" * 60)
        
        return 0
        
    finally:
        info(f"\nCleaning up: {tmp_dir}")
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
