#!/usr/bin/env python3
"""
patch_axml.py — Patch binary AndroidManifest.xml to add android:debuggable="true" to <application>.

Uses aapt2 for decode/recompile via proto format.
"""

import sys
import os
import struct
import subprocess
import tempfile
from pathlib import Path

def parse_string_pool(data: str, offset: int):
    """Parse AXML string pool. Returns (strings, styles)."""
    header_size = 28
    num_strings = struct.unpack_from('<I', data, offset + 8)[0]
    num_styles = struct.unpack_from('<I', data, offset + 12)[0]
    flags = struct.unpack_from('<I', data, offset + 16)[0]
    strings_offset = struct.unpack_from('<I', data, offset + 20)[0]
    styles_offset = struct.unpack_from('<I', data, offset + 24)[0]
    
    string_offsets_start = offset + header_size
    string_offsets = []
    for i in range(num_strings):
        off = struct.unpack_from('<I', data, string_offsets_start + i * 4)[0]
        string_offsets.append(off)
    
    string_data_start = offset + strings_offset
    strings = []
    for off in string_offsets:
        str_abs = string_data_start + off
        str_len = data[str_abs] | (data[str_abs + 1] << 8)
        if str_len & 0x8000:
            # Handle 3-byte length
            str_len = ((str_len & 0x7fff) << 8) | data[str_abs + 2]
            str_data = data[str_abs + 3:str_abs + 3 + str_len * 2]
        else:
            str_data = data[str_abs + 2:str_abs + 2 + str_len * 2]
        try:
            strings.append(str_data.decode('utf-16-le'))
        except:
            strings.append('')
    
    return strings, flags


def find_chunk(data: str, target_type: int, start: int = 0):
    """Find a chunk of given type in the data."""
    offset = start
    while offset < len(data):
        chunk_type = struct.unpack_from('<H', data, offset)[0]
        chunk_size = struct.unpack_from('<I', data, offset + 4)[0]
        if chunk_type == target_type:
            return offset, chunk_size
        if chunk_size == 0:
            break
        offset += chunk_size
    return None, None


def patch_debuggable(input_path: str, output_path: str):
    """Patch manifest to add android:debuggable="true"."""
    data = bytearray(open(input_path, 'rb').read())
    
    if data[0:2] != b'\x03\x00':
        raise ValueError(f"Not binary AXML: {data[0:2].hex()}")
    
    # Find string pool
    sp_offset, sp_size = find_chunk(data, 0x0001)
    if sp_offset is None:
        raise ValueError("String pool not found")
    
    strings, flags = parse_string_pool(data, sp_offset)
    print(f"[PATCH] String pool: {len(strings)} strings")
    
    # Find or add strings
    def find_or_add(s):
        for i, ss in enumerate(strings):
            if ss == s:
                return i
        strings.append(s)
        return len(strings) - 1
    
    ns_android_idx = find_or_add('http://schemas.android.com/apk/res/android')
    debuggable_idx = find_or_add('debuggable')
    application_idx = find_or_add('application')
    
    # Find <application> start tag
    app_offset, app_size = find_chunk(data, 0x0102)
    while app_offset is not None:
        name_idx = struct.unpack_from('<I', data, app_offset + 20)[0]
        if name_idx == application_idx:
            break
        app_offset, app_size = find_chunk(data, 0x0102, app_offset + app_size)
    
    if app_offset is None:
        raise ValueError("<application> tag not found")
    
    attr_count = struct.unpack_from('<H', data, app_offset + 28)[0]
    print(f"[PATCH] Found <application> with {attr_count} attributes")
    
    # Check if debuggable already exists
    attr_start = app_offset + 36
    for i in range(attr_count):
        an = struct.unpack_from('<I', data, attr_start + 4)[0]
        if an == debuggable_idx:
            print("[PATCH] debuggable already exists")
            return data
        attr_start += 20
    
    # Build new string pool with added strings
    new_sp_data = bytearray()
    new_string_offsets = []
    
    for s in strings:
        new_string_offsets.append(len(new_sp_data))
        encoded = s.encode('utf-16-le')
        new_sp_data.extend(struct.pack('<H', len(s)))
        new_sp_data.extend(encoded)
        # Pad to 4-byte alignment
        while len(new_sp_data) % 4 != 0:
            new_sp_data.append(0)
    
    # Build new string pool chunk
    new_sp = bytearray()
    new_sp.extend(struct.pack('<H', 0x0001))  # type
    new_sp.extend(struct.pack('<H', 28))      # header_size
    new_sp_size_offset = len(new_sp)
    new_sp.extend(struct.pack('<I', 0))       # chunk size (fill later)
    new_sp.extend(struct.pack('<I', len(strings)))  # num_strings
    new_sp.extend(struct.pack('<I', 0))       # num_styles
    new_sp.extend(struct.pack('<I', flags))   # flags
    new_sp_soffset_offset = len(new_sp)
    new_sp.extend(struct.pack('<I', 0))       # strings_offset (fill later)
    new_sp.extend(struct.pack('<I', 0))       # styles_offset
    
    # String offsets array
    strings_data_offset = len(new_sp) + len(strings) * 4
    for off in new_string_offsets:
        new_sp.extend(struct.pack('<I', off))
    
    # String data
    new_sp.extend(new_sp_data)
    
    # Update offsets
    struct.pack_into('<I', new_sp, new_sp_size_offset, len(new_sp))
    struct.pack_into('<I', new_sp, new_sp_soffset_offset, strings_data_offset)
    
    # Build new attribute (20 bytes)
    new_attr = bytearray()
    new_attr.extend(struct.pack('<I', ns_android_idx))   # namespace
    new_attr.extend(struct.pack('<I', debuggable_idx))   # name
    new_attr.extend(struct.pack('<I', 0xFFFFFFFF))       # raw_value
    new_attr.extend(struct.pack('<I', 0x12))             # value_type (ATTR_BOOLEAN)
    new_attr.extend(struct.pack('<I', 0xFFFFFFFF))       # value_data (true)
    
    # Build new application tag
    new_app = bytearray(data[app_offset:app_offset + app_size])
    struct.pack_into('<H', new_app, 28, attr_count + 1)  # attr_count++
    struct.pack_into('<I', new_app, 4, app_size + 20)   # chunk_size += 20
    new_app.extend(new_attr)
    
    # Rebuild full AXML
    result = bytearray()
    result.extend(data[:sp_offset])
    result.extend(new_sp)
    result.extend(data[sp_offset + sp_size:app_offset])
    result.extend(new_app)
    result.extend(data[app_offset + app_size:])
    
    # Update total size
    struct.pack_into('<I', result, 4, len(result))
    
    print(f"[PATCH] Done: {len(data)} -> {len(result)} bytes")
    return result


def main():
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    
    result = patch_debuggable(str(input_path), str(output_path))
    output_path.write_bytes(result)
    print(f"[PATCH] Wrote {output_path}")


if __name__ == '__main__':
    main()
