#!/usr/bin/env python3
"""
patch_manifest_binary.py — Minimal binary AXML patcher for android:debuggable="true".

Usage:
    python patch_manifest_binary.py <input_axml> <output_axml>

Binary AXML format (all little-endian):
  Main header: magic(4) + total_size(4)
  String pool chunk: type(2) + header_size(2) + size(4) + num_strings(4) + 
                     num_styles(4) + flags(4) + strings_offset(4) + styles_offset(4) + 
                     [string_offsets...] + [string_data...]
  Other chunks: resource_ids, namespace, start_tag, end_tag, ...
  
  Start tag chunk: type(0x0102)(2) + header_size(2) + size(4) + line(4) + comment(4) +
                   ns_uri(4) + name(4) + attr_start(2) + attr_size(2) + attr_count(2) +
                   id_idx(2) + class_idx(2) + style_idx(2) + [attributes...]
  
  Attribute: ns_uri(4) + name(4) + raw_value(4) + value_type(4) + value_data(4) = 20 bytes
"""

import struct
import sys
from pathlib import Path


def patch_manifest(input_path: str, output_path: str):
    """Patch manifest to add android:debuggable=true to <application>."""
    data = bytearray(Path(input_path).read_bytes())
    
    # Verify magic: 03 00 08 00 (AXML type + header_size=8)
    if data[0:2] != b'\x03\x00':
        raise ValueError(f"Not binary AXML: {data[0:2].hex()}")
    
    # Parse string pool
    sp_offset = 8  # After main header
    sp_type = struct.unpack_from('<H', data, sp_offset)[0]
    sp_hdr_size = struct.unpack_from('<H', data, sp_offset + 2)[0]
    sp_size = struct.unpack_from('<I', data, sp_offset + 4)[0]
    sp_num_strings = struct.unpack_from('<I', data, sp_offset + 8)[0]
    sp_num_styles = struct.unpack_from('<I', data, sp_offset + 12)[0]
    sp_flags = struct.unpack_from('<I', data, sp_offset + 16)[0]
    sp_strings_off = struct.unpack_from('<I', data, sp_offset + 20)[0]
    sp_styles_off = struct.unpack_from('<I', data, sp_offset + 24)[0]
    
    soff_start = sp_offset + sp_hdr_size
    sd_start = sp_offset + sp_strings_off
    
    print(f"[PATCH] String pool: {sp_num_strings} strings, data at {sd_start}, flags={sp_flags}")
    
    # Read strings
    strings = []
    for i in range(sp_num_strings):
        off = struct.unpack_from('<I', data, soff_start + i * 4)[0]
        str_abs = sd_start + off
        if str_abs >= len(data):
            strings.append('')
            continue
        str_len = data[str_abs] | (data[str_abs + 1] << 8)
        str_data = data[str_abs + 2:str_abs + 2 + str_len * 2]
        try:
            strings.append(str_data.decode('utf-16-le'))
        except:
            strings.append('')
    
    # Find or add needed strings
    def find_or_add(s):
        for i, ss in enumerate(strings):
            if ss == s:
                return i
        strings.append(s)
        return len(strings) - 1
    
    ns_idx = find_or_add('http://schemas.android.com/apk/res/android')
    dbg_idx = find_or_add('debuggable')
    app_idx = find_or_add('application')
    
    print(f"[PATCH] String indices: ns={ns_idx}, debuggable={dbg_idx}, application={app_idx}")
    
    # Find <application> start tag
    offset = 8 + sp_size  # Start after string pool
    app_tag_off = None
    app_tag_size = None
    app_attr_count = None
    
    while offset < len(data):
        chunk_type = struct.unpack_from('<H', data, offset)[0]
        chunk_size = struct.unpack_from('<I', data, offset + 4)[0]
        
        if chunk_type == 0x0102:  # Start tag
            name_idx = struct.unpack_from('<I', data, offset + 20)[0]
            if name_idx == app_idx:
                app_tag_off = offset
                app_tag_size = chunk_size
                app_attr_count = struct.unpack_from('<H', data, offset + 28)[0]
                print(f"[PATCH] Found <application> at offset {offset}, {app_attr_count} attrs")
                break
        
        if chunk_size == 0:
            break
        offset += chunk_size
    
    if app_tag_off is None:
        raise ValueError("Could not find <application> tag")
    
    # Check if debuggable already exists
    attr_off = app_tag_off + 36  # After start tag header (36 bytes)
    for i in range(app_attr_count):
        an = struct.unpack_from('<I', data, attr_off + 4)[0]
        if an == dbg_idx:
            print("[PATCH] debuggable attribute already exists")
            Path(output_path).write_bytes(data)
            return
        attr_off += 20
    
    # Build new string pool
    new_sp = bytearray()
    new_sp.extend(struct.pack('<H', sp_type))  # type = 1
    new_sp.extend(struct.pack('<H', sp_hdr_size))  # header_size = 28
    new_sp_size_off = len(new_sp)
    new_sp.extend(struct.pack('<I', 0))  # chunk size (fill later)
    new_sp.extend(struct.pack('<I', len(strings)))  # num_strings
    new_sp.extend(struct.pack('<I', sp_num_styles))  # num_styles
    new_sp.extend(struct.pack('<I', sp_flags))  # flags
    new_sp_soff_off = len(new_sp)
    new_sp.extend(struct.pack('<I', 0))  # strings_offset (fill later)
    new_sp.extend(struct.pack('<I', sp_styles_off))  # styles_offset
    
    # String offsets array + string data
    string_data = bytearray()
    string_offsets = []
    for s in strings:
        string_offsets.append(len(string_data))
        encoded = s.encode('utf-16-le')
        string_data.extend(struct.pack('<H', len(s)))
        string_data.extend(encoded)
        # Pad to 4-byte alignment
        while len(string_data) % 4 != 0:
            string_data.append(0)
    
    # Add string offsets array
    strings_data_off = len(new_sp) + len(strings) * 4
    for off in string_offsets:
        new_sp.extend(struct.pack('<I', off))
    
    # Add string data
    new_sp.extend(string_data)
    
    # Update offsets
    struct.pack_into('<I', new_sp, new_sp_size_off, len(new_sp))
    struct.pack_into('<I', new_sp, new_sp_soff_off, strings_data_off)
    
    # Build new attribute (20 bytes)
    new_attr = bytearray()
    new_attr.extend(struct.pack('<I', ns_idx))       # namespace
    new_attr.extend(struct.pack('<I', dbg_idx))      # name
    new_attr.extend(struct.pack('<I', 0xFFFFFFFF))   # raw_value
    new_attr.extend(struct.pack('<I', 0x12))         # value_type (ATTR_BOOLEAN)
    new_attr.extend(struct.pack('<I', 0xFFFFFFFF))   # value_data (true)
    
    # Build new application tag
    new_app = bytearray(data[app_tag_off:app_tag_off + app_tag_size])
    struct.pack_into('<H', new_app, 28, app_attr_count + 1)  # attr_count++
    struct.pack_into('<I', new_app, 4, app_tag_size + 20)   # chunk_size += 20
    new_app.extend(new_attr)
    
    # Rebuild full AXML
    result = bytearray()
    result.extend(data[:8])  # AXML header (magic + size)
    result.extend(new_sp)
    result.extend(data[8 + sp_size:app_tag_off])  # Between string pool and app tag
    result.extend(new_app)
    result.extend(data[app_tag_off + app_tag_size:])  # After app tag
    
    # Update total size
    struct.pack_into('<I', result, 4, len(result))
    
    Path(output_path).write_bytes(bytes(result))
    print(f"[PATCH] Wrote {output_path} ({len(data)} -> {len(result)} bytes)")


if __name__ == '__main__':
    patch_manifest(sys.argv[1], sys.argv[2])
