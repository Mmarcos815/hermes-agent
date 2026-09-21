#!/usr/bin/env python3
"""
patch_axml_androguard.py — Patch binary AXML using androguard for parsing + raw bytes for modification.

Approach:
1. Use androguard AXMLParser to find the application start tag position
2. Use raw byte manipulation to add the debuggable attribute
3. No need to rebuild string pool — androguard tells us the string indices
"""

import sys
from pathlib import Path

from androguard.core.axml import AXMLPrinter, AXMLParser


def patch_manifest(data: bytes) -> bytes:
    """Patch binary AXML to add android:debuggable=true to <application>."""
    
    if data[:2] != b'\x03\x00':
        raise ValueError(f"Not binary AXML (magic: {data[:2].hex()})")
    
    # Parse with androguard to find the application tag
    parser = AXMLParser(data)
    
    app_tag_offset = None
    app_tag_size = None
    app_attr_count = None
    app_tag_data_start = None
    
    # We need to find the application start tag and its position in the raw bytes
    # AXMLParser doesn't give us raw offsets, so we'll scan manually
    
    # Scan for start tags and check their names
    offset = 8  # After header
    while offset < len(data):
        if offset + 4 > len(data):
            break
        chunk_type = int.from_bytes(data[offset:offset+2], 'little')
        chunk_size = int.from_bytes(data[offset+4:offset+8], 'little')
        
        if chunk_type == 0x0102:  # Start tag
            # Parse the tag header
            if offset + 36 > len(data):
                break
            
            # Start tag structure:
            # type(2) + header_size(2) + size(4) + line(4) + comment(4) + 
            # ns(4) + name(4) + attr_start(2) + attr_size(2) + attr_count(2) + 
            # id_index(2) + class_index(2) + style_index(2) = 36 bytes
            
            name_idx = int.from_bytes(data[offset+20:offset+24], 'little')
            attr_count = int.from_bytes(data[offset+28:offset+30], 'little')
            tag_size = int.from_bytes(data[offset+4:offset+8], 'little')
            
            # Get the name from string pool
            # We need to parse the string pool to get the name
            # For now, let's use a simpler approach: scan for "application" in the string pool
            # and check if this tag's name matches
            
            # Actually, let's use androguard to get the tag name
            # We need to re-parse from the beginning to get the event at this offset
            
            # Simpler: use androguard to get all events, then find the application one
            pass
        
        if chunk_size == 0:
            break
        offset += chunk_size
    
    # Better approach: use androguard to decode to text, modify, then re-encode
    # But androguard doesn't have a binary encoder...
    
    # Best approach: use androguard to find the string pool, then do raw patching
    
    # Parse string pool
    string_pool_offset = 8
    num_strings = int.from_bytes(data[string_pool_offset+12:string_pool_offset+16], 'little')
    strings_offset = int.from_bytes(data[string_pool_offset+24:string_pool_offset+28], 'little')
    string_data_start = string_pool_offset + strings_offset
    
    # Read string offsets
    string_offsets_start = string_pool_offset + 28  # After string pool header
    string_offsets = []
    for i in range(num_strings):
        off = int.from_bytes(data[string_offsets_start + i*4:string_offsets_start + i*4 + 4], 'little')
        string_offsets.append(off)
    
    # Read strings
    strings = []
    for str_off in string_offsets:
        str_abs = string_data_start + str_off
        if str_abs >= len(data):
            strings.append('')
            continue
        str_len = data[str_abs]
        if str_len == 0xFF:
            strings.append('')
            continue
        str_bytes = data[str_abs + 2:str_abs + 2 + str_len * 2]
        try:
            strings.append(str_bytes.decode('utf-16-le'))
        except:
            strings.append('')
    
    print(f"[PATCH] Found {len(strings)} strings")
    
    # Find "application" string
    app_str_idx = None
    for i, s in enumerate(strings):
        if s == 'application':
            app_str_idx = i
            break
    
    if app_str_idx is None:
        raise ValueError("Could not find 'application' string")
    
    print(f"[PATCH] 'application' at string index {app_str_idx}")
    
    # Find "debuggable" string
    debuggable_str_idx = None
    for i, s in enumerate(strings):
        if s == 'debuggable':
            debuggable_str_idx = i
            break
    
    if debuggable_str_idx is None:
        # Add "debuggable" to string pool
        debuggable_str_idx = len(strings)
        strings.append('debuggable')
        print(f"[PATCH] Added 'debuggable' at string index {debuggable_str_idx}")
    else:
        print(f"[PATCH] 'debuggable' already at string index {debuggable_str_idx}")
    
    # Find android namespace
    ns_android_idx = None
    for i, s in enumerate(strings):
        if s == 'http://schemas.android.com/apk/res/android':
            ns_android_idx = i
            break
    
    if ns_android_idx is None:
        ns_android_idx = len(strings)
        strings.append('http://schemas.android.com/apk/res/android')
        print(f"[PATCH] Added android namespace at string index {ns_android_idx}")
    
    # Find the application start tag
    offset = 8
    app_tag_offset = None
    app_tag_size = None
    app_attr_count = None
    
    while offset < len(data):
        chunk_type = int.from_bytes(data[offset:offset+2], 'little')
        chunk_size = int.from_bytes(data[offset+4:offset+8], 'little')
        
        if chunk_type == 0x0102:  # Start tag
            name_idx = int.from_bytes(data[offset+20:offset+24], 'little')
            if name_idx == app_str_idx:
                app_tag_offset = offset
                app_tag_size = chunk_size
                app_attr_count = int.from_bytes(data[offset+28:offset+30], 'little')
                print(f"[PATCH] Found <application> at offset {offset}, {app_attr_count} attributes, size {chunk_size}")
                break
        
        if chunk_size == 0:
            break
        offset += chunk_size
    
    if app_tag_offset is None:
        raise ValueError("Could not find <application> tag")
    
    # Check if debuggable attribute already exists
    attr_offset = app_tag_offset + 36
    for i in range(app_attr_count):
        attr_name_idx = int.from_bytes(data[attr_offset+4:attr_offset+8], 'little')
        if attr_name_idx == debuggable_str_idx:
            print("[PATCH] debuggable attribute already exists")
            return data
        attr_offset += 20
    
    # Now we need to:
    # 1. Rebuild string pool with new strings (if any were added)
    # 2. Insert new attribute into application tag
    # 3. Update chunk sizes
    
    # Build new string pool
    new_string_data = bytearray()
    new_string_offsets = []
    
    for s in strings:
        new_string_offsets.append(len(new_string_data))
        encoded = s.encode('utf-16-le')
        new_string_data.extend(s.encode('utf-16-le'))
        # Pad to 4-byte alignment
        while len(new_string_data) % 4 != 0:
            new_string_data.extend(b'\x00')
    
    # Build new string pool chunk
    new_string_pool = bytearray()
    new_string_pool.extend(data[string_pool_offset:string_pool_offset+12])  # type + header_size + size placeholder
    new_string_pool.extend(len(strings).to_bytes(4, 'little'))  # num_strings
    new_string_pool.extend((0).to_bytes(4, 'little'))  # num_styles
    new_string_pool.extend((0).to_bytes(4, 'little'))  # flags
    new_string_pool.extend((0).to_bytes(4, 'little'))  # strings_offset placeholder
    new_string_pool.extend((0).to_bytes(4, 'little'))  # styles_offset
    
    # String offsets array
    strings_data_offset = 28 + len(strings) * 4
    for off in new_string_offsets:
        new_string_pool.extend(off.to_bytes(4, 'little'))
    
    # String data
    new_string_pool.extend(new_string_data)
    
    # Update string pool size and offsets
    struct.pack_into('<I', new_string_pool, 4, len(new_string_pool))
    struct.pack_into('<I', new_string_pool, 24, strings_data_offset)
    
    # Build new attribute
    new_attr = bytearray()
    new_attr.extend(ns_android_idx.to_bytes(4, 'little'))  # namespace
    new_attr.extend(debuggable_str_idx.to_bytes(4, 'little'))  # name
    new_attr.extend((0xFFFFFFFF).to_bytes(4, 'little'))  # raw value
    new_attr.extend((0x12).to_bytes(4, 'little'))  # value type (ATTR_BOOLEAN)
    new_attr.extend((0xFFFFFFFF).to_bytes(4, 'little'))  # value data (true)
    
    # Build new application tag
    new_app_tag = bytearray(data[app_tag_offset:app_tag_offset + app_tag_size])
    struct.pack_into('<H', new_app_tag, 28, app_attr_count + 1)  # attr_count
    struct.pack_into('<I', new_app_tag, 4, app_tag_size + 20)  # chunk_size
    new_app_tag.extend(new_attr)
    
    # Rebuild the entire AXML
    result = bytearray()
    result.extend(data[:string_pool_offset])
    result.extend(new_string_pool)
    result.extend(data[string_pool_offset + int.from_bytes(data[string_pool_offset+4:string_pool_offset+8], 'little'):app_tag_offset])
    result.extend(new_app_tag)
    result.extend(data[app_tag_offset + app_tag_size:])
    
    # Update total size
    struct.pack_into('<I', result, 4, len(result))
    
    print(f"[PATCH] Patched: {len(data)} -> {len(result)} bytes")
    return bytes(result)


import struct

def main():
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    data = Path(input_path).read_bytes()
    patched = patch_manifest(data)
    Path(output_path).write_bytes(patched)
    print(f"[PATCH] Wrote {output_path}")


if __name__ == '__main__':
    main()
