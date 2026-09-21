#!/usr/bin/env python3
"""
patch_manifest_debuggable.py — Direct binary AXML patch to add android:debuggable="true".

Strategy:
1. Parse binary AXML to find string pool and application start tag
2. Add "debuggable" string to pool if not present
3. Insert new attribute into application tag
4. Update chunk sizes
5. Write patched binary AXML
"""

import struct
import sys
from pathlib import Path


def patch_axml(data: bytes) -> bytes:
    """Patch binary AXML to add android:debuggable=true to <application>."""
    
    if data[:2] != b'\x03\x00':
        raise ValueError(f"Not binary AXML (magic: {data[:2].hex()})")
    
    # Parse header
    total_size = struct.unpack_from('<I', data, 4)[0]
    
    # Find string pool (type 0x0001) and parse it
    offset = 8
    string_pool_offset = None
    string_pool_size = None
    strings = []
    string_data_start = None
    
    while offset < len(data):
        chunk_type = struct.unpack_from('<H', data, offset)[0]
        chunk_header_size = struct.unpack_from('<H', data, offset + 2)[0]
        chunk_size = struct.unpack_from('<I', data, offset + 4)[0]
        
        if chunk_type == 0x0001:  # String pool
            string_pool_offset = offset
            string_pool_size = chunk_size
            
            num_strings = struct.unpack_from('<I', data, offset + 8)[0]
            num_styles = struct.unpack_from('<I', data, offset + 12)[0]
            flags = struct.unpack_from('<I', data, offset + 16)[0]
            strings_offset = struct.unpack_from('<I', data, offset + 20)[0]
            styles_offset = struct.unpack_from('<I', data, offset + 24)[0]
            
            # Read string offsets
            string_offsets_start = offset + chunk_header_size
            string_offsets = []
            for i in range(num_strings):
                off = struct.unpack_from('<I', data, string_offsets_start + i * 4)[0]
                string_offsets.append(off)
            
            # Read strings
            string_data_start = offset + strings_offset
            for i, str_off in enumerate(string_offsets):
                str_abs = string_data_start + str_off
                if str_abs >= len(data):
                    strings.append('')
                    continue
                # UTF-16 length prefix
                str_len = struct.unpack_from('<H', data, str_abs)[0]
                if str_len == 0xFFFF:
                    strings.append('')
                    continue
                # Read UTF-16 string
                str_bytes = data[str_abs + 2:str_abs + 2 + str_len * 2]
                try:
                    strings.append(str_bytes.decode('utf-16-le'))
                except:
                    strings.append('')
            
            break
        
        if chunk_size == 0:
            break
        offset += chunk_size
    
    if string_pool_offset is None:
        raise ValueError("String pool not found")
    
    print(f"[PATCH] Found {len(strings)} strings in pool")
    
    # Check if "debuggable" already exists
    debuggable_idx = None
    for i, s in enumerate(strings):
        if s == 'debuggable':
            debuggable_idx = i
            break
    
    if debuggable_idx is not None:
        print(f"[PATCH] 'debuggable' already in string pool at index {debuggable_idx}")
    else:
        # Add "debuggable" to string pool
        debuggable_idx = len(strings)
        strings.append('debuggable')
        print(f"[PATCH] Added 'debuggable' to string pool at index {debuggable_idx}")
    
    # Find android namespace URI
    ns_android_idx = None
    for i, s in enumerate(strings):
        if s == 'http://schemas.android.com/apk/res/android':
            ns_android_idx = i
            break
    
    if ns_android_idx is None:
        ns_android_idx = len(strings)
        strings.append('http://schemas.android.com/apk/res/android')
        print(f"[PATCH] Added android namespace to string pool at index {ns_android_idx}")
    
    # Find <application> start tag
    app_tag_offset = None
    app_tag_size = None
    app_attr_count = None
    
    offset = 8
    while offset < len(data):
        chunk_type = struct.unpack_from('<H', data, offset)[0]
        chunk_header_size = struct.unpack_from('<H', data, offset + 2)[0]
        chunk_size = struct.unpack_from('<I', data, offset + 4)[0]
        
        if chunk_type == 0x0102:  # Start tag
            name_idx = struct.unpack_from('<I', data, offset + 20)[0]
            if name_idx < len(strings) and strings[name_idx] == 'application':
                app_tag_offset = offset
                app_tag_size = chunk_size
                app_attr_count = struct.unpack_from('<H', data, offset + 28)[0]
                print(f"[PATCH] Found <application> at offset {offset}, {app_attr_count} attributes")
                break
        
        if chunk_size == 0:
            break
        chunk_size = struct.unpack_from('<I', data, offset + 4)[0]
        offset += chunk_size
    
    if app_tag_offset is None:
        raise ValueError("Could not find <application> tag")
    
    # Check if debuggable attribute already exists
    attr_offset = app_tag_offset + 36  # After start tag header (36 bytes)
    for i in range(app_attr_count):
        attr_name_idx = struct.unpack_from('<I', data, attr_offset + 4)[0]
        if attr_name_idx < len(strings) and strings[attr_name_idx] == 'debuggable':
            print("[PATCH] debuggable attribute already exists in <application>")
            return data
        attr_offset += 20
    
    # Now we need to:
    # 1. Rebuild string pool with new strings
    # 2. Insert new attribute into application tag
    # 3. Update chunk sizes
    
    # Build new string pool
    new_string_data = bytearray()
    new_string_offsets = []
    
    for s in strings:
        new_string_offsets.append(len(new_string_data))
        # Encode as UTF-16 with length prefix
        encoded = s.encode('utf-16-le')
        new_string_data.extend(struct.pack('<H', len(s)))
        new_string_data.extend(encoded)
        # Pad to 4-byte alignment
        while len(new_string_data) % 4 != 0:
            new_string_data.extend(b'\x00')
    
    # Build new string pool chunk
    new_string_pool = bytearray()
    # Header
    new_string_pool.extend(struct.pack('<H', 0x0001))  # type
    new_string_pool.extend(struct.pack('<H', 28))  # header_size
    new_string_pool.extend(struct.pack('<I', 0))  # size (will fill later)
    new_string_pool.extend(struct.pack('<I', len(strings)))  # num_strings
    new_string_pool.extend(struct.pack('<I', 0))  # num_styles
    new_string_pool.extend(struct.pack('<I', 0))  # flags (UTF-8=0x100, but we use UTF-16=0)
    new_string_pool.extend(struct.pack('<I', 0))  # strings_offset (will fill later)
    new_string_pool.extend(struct.pack('<I', 0))  # styles_offset (will fill later)
    
    # String offsets array
    strings_data_offset = 28 + len(strings) * 4  # After header + offsets array
    for off in new_string_offsets:
        new_string_pool.extend(struct.pack('<I', off))
    
    # String data
    new_string_pool.extend(new_string_data)
    
    # Update string pool size
    struct.pack_into('<I', new_string_pool, 4, len(new_string_pool))
    struct.pack_into('<I', new_string_pool, 24, strings_data_offset)
    struct.pack_into('<I', new_string_pool, 28, 0)  # No styles
    
    # Now build the new attribute to insert
    # Attribute: ns(4) + name(4) + value_str(4) + value_type(4) + value_data(4) = 20 bytes
    new_attr = bytearray()
    new_attr.extend(struct.pack('<I', ns_android_idx))  # namespace
    new_attr.extend(struct.pack('<I', debuggable_idx))  # name
    new_attr.extend(struct.pack('<I', 0xFFFFFFFF))  # raw value (not a string)
    new_attr.extend(struct.pack('<I', 0x12))  # value type (ATTR_BOOLEAN)
    new_attr.extend(struct.pack('<I', 0xFFFFFFFF))  # value data (true)
    
    # Build new application tag with extra attribute
    new_app_tag = bytearray(data[app_tag_offset:app_tag_offset + app_tag_size])
    # Update attr_count
    struct.pack_into('<H', new_app_tag, 28, app_attr_count + 1)
    # Update chunk_size
    struct.pack_into('<I', new_app_tag, 4, app_tag_size + 20)
    # Append new attribute
    new_app_tag.extend(new_attr)
    
    # Rebuild the entire AXML
    result = bytearray()
    
    # Copy everything before string pool
    result.extend(data[:string_pool_offset])
    
    # Add new string pool
    result.extend(new_string_pool)
    
    # Copy everything between string pool and application tag
    result.extend(data[string_pool_offset + string_pool_size:app_tag_offset])
    
    # Add new application tag
    result.extend(new_app_tag)
    
    # Copy everything after application tag
    result.extend(data[app_tag_offset + app_tag_size:])
    
    # Update total size
    struct.pack_into('<I', result, 4, len(result))
    
    print(f"[PATCH] Patched AXML: {len(data)} -> {len(result)} bytes")
    
    return bytes(result)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='Input binary AXML file')
    parser.add_argument('output', help='Output binary AXML file')
    args = parser.parse_args()
    
    data = Path(args.input).read_bytes()
    patched = patch_axml(data)
    Path(args.output).write_bytes(patched)
    print(f"[PATCH] Wrote {args.output}")


if __name__ == '__main__':
    main()
