#!/usr/bin/env python3
"""
ISO 8583 Message Parser and Encoder — Phase 2A Learning Project

ISO 8583 is the financial transaction card origination message standard used
by payment networks (Visa, Mastercard, etc.) to exchange transaction data
between terminals, processors, and card issuers.

This project:
1. Parses ISO 8583 binary messages (bitmap + data elements)
2. Encodes messages back to ISO 8583 format
3. Demonstrates common transaction flows (authorization, settlement, etc.)
4. Shows the actual structure underneath payment processing

Reference: ISO 8583-1:2003, "Financial transaction card originiation and
acceptance — Message format and data elements"
"""

import struct
import binascii
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field

# ============================================================================
# ISO 8583 Message Structure Overview
# ============================================================================
#
# An ISO 8583 message consists of:
#
#   1. MTI (Message Type Indicator) — 4 digits
#      - First digit: class (1=financial, 2=financial, 3=local, 4=...)
#      - Second digit: subclass (0=normal, 1=...)
#      - Third digit: function (0=request, 1=response, 2=advise, 3=...)
#      - Fourth digit: origin/direction (0=we are sender, 1=we are receiver)
#
#   2. Bitmap — 8 bytes (64 bits) or 16 bytes (128 bits)
#      - Each bit represents a data element (1-64 or 1-128)
#      - Bit set = data element present in message
#      - First bit (MSB of first byte) = data element 1
#
#   3. Data Elements — variable length fields identified by their number
#      - Format type: 'n' (numeric), 'a' (alphanumeric), 'b' (binary), 'an' (alphanumeric+numeric), 'z' (tracks), 's' (special), 'e' (extended), 'f' (ISO 10783), 'g' (generic), 'h' (private), 'd' (ISO 11348), 'k' (Multegreedy), 'p' (ISO 1221), 'q' (...), 'r' (...), 't' (...), 'u' (...), 'v' (...), 'w' (...), 'x' (...), 'y' (...), 'z' (...)
#      - Length type: fixed or LLVAR/LLLVAR (length-prefixed)
#
# Common MTI examples:
#   0100 — Authorization request (POS terminal → issuer)
#   0110 — Authorization response (issuer → POS terminal)
#   0200 — Financial request (purchase)
#   0210 — Financial response
#   0400 — Reversal request
#   0420 — Reversal response
#   0800 — Network management request
#   0810 — Network management response
#
# Common data elements:
#   2  — Primary Account Number (PAN) — 19n
#   3  — Processing Code — 6n
#   4  — Amount, Transaction — 12n
#   5  — Amount, Binary — 6n
#   6  — Amount, Cardholder — 12n (sum of charges)
#   7  — Transmission Date/Time — 10n
#   10 — Amount, Settlement — 6n
#   11 — System Trace Audit Number — 6n
#   12 — Local Transaction Date/Time — 12n
#   13 — Transaction Date — 6n
#   14 — Transaction Time — 6n
#   15 — Settlement Date — 6n
#   18 — Retrieval Reference Number — 12an
#   19 — Settlement Code — 3n
#   22 — POS Terminal Identifier — 8an
#   23 — Card Sequence Number — 3n
#   25 — Terminal Country Code — 3n
#   26 — Terminal Type — 2n
#   27 — Terminal Capabilities — 3n
#   37 — Response Code — 2an
#   38 — Authorization Code — 6an
#   39 — Response Code (duplicate) — 2an
#   44 — Additional Response Data — 76a
#   55 — Track 3 Data / EMV Data — 999b
#   57 — Transaction Status — 1an
#   61 — Original MTI — 4an
#   64 — Additional Data — 999b ( bitmap extension to 128 bits )
#   128 — Bitmap extension (if 128-bit bitmap used)
#
# Length encoding:
#   - Fixed length: field has a constant size
#   - LLVAR: 2-digit length prefix + data (max 99 bytes)
#   - LLLVAR: 3-digit length prefix + data (max 999 bytes)

# ============================================================================
# Data Element Definitions — subset of common elements
# ============================================================================

# Format codes:
# 'n' = numeric (right-padded with zeros)
# 'a' = alphanumeric (left-padded with spaces)
# 'b' = binary
# 'an' = alphanumeric+numeric
# 'z' = track data (binary, left-justified)
# LLVAR = length-prefixed variable (2 or 3 digit prefix)
# Fixed = fixed length

# Data element definitions: (number, name, format, length)
# Format: (type, length) where type in {'n','a','b','an','z'} and length is
# either an integer (fixed) or a string ('LLVAR' or 'LLLVAR')

DATA_ELEMENTS: Dict[int, Tuple[str, str, Any]] = {
    # MTI is not in the bitmap — it's the first 4 bytes
    # Bitmap is elements 1-64 (or 1-128)
    
    # Primary Account Number (PAN)
    2:  ("Primary Account Number", "n", 19),
    # Processing Code
    3:  ("Processing Code", "n", 6),
    # Amount, Transaction
    4:  ("Amount, Transaction", "n", 12),
    # Amount, Fee
    5:  ("Amount, Fee", "n", 6),
    # Amount, Cardholder Charges
    6:  ("Amount, Cardholder Charges", "n", 12),
    # Transmission Date/Time (YYMMDDHHMMSS)
    7:  ("Transmission Date/Time", "n", 10),
    # Settlement Date (YYMMDD)
    10: ("Settlement Amount", "n", 12),
    # System Trace Audit Number
    11: ("System Trace Audit Number", "n", 6),
    # Local Transaction Date/Time (YYMMDDHHMMSS)
    12: ("Local Transaction Date/Time", "n", 12),
    # Transaction Date (YYMMDD)
    13: ("Transaction Date", "n", 6),
    # Transaction Time (HHMMSS)
    14: ("Transaction Time", "n", 6),
    # Settlement Date
    15: ("Settlement Date", "n", 6),
    # Conversion Rate, Authorization
    16: ("Conversion Rate, Authorization", "n", 6),
    # Retrieval Reference Number
    18: ("Retrieval Reference Number", "an", 12),
    # Settlement Code
    19: ("Settlement Code", "n", 3),
    # POS Terminal Identifier
    22: ("POS Terminal Identifier", "an", 8),
    # Card Sequence Number
    23: ("Card Sequence Number", "n", 3),
    # Terminal Country Code
    25: ("Terminal Country Code", "n", 3),
    # Terminal Type
    26: ("Terminal Type", "n", 2),
    # Amount, Transaction Fee
    27: ("Transaction Fee", "n", 6),
    # Amount, Settlement Fee
    28: ("Settlement Fee", "n", 6),
    # Amount, Transaction
    29: ("Transaction Amount", "n", 12),
    # Amount, Settlement
    30: ("Settlement Amount", "n", 12),
    # Amount, Insurance
    31: ("Insurance Amount", "n", 6),
    # Amount, Tip
    32: ("Tip Amount", "n", 6),
    # Amount, Cashback
    33: ("Cashback Amount", "n", 6),
    # Reserved
    34: ("Reserved", "b", 25),
    # Response Code
    37: ("Response Code", "an", 2),
    # Authorization Code
    38: ("Authorization Code", "an", 6),
    # Response Code (extended)
    39: ("Response Code (Extended)", "an", 2),
    # Continuous Poly String
    40: ("Continuous Poly String", "a", 3),
    # Amount, Additional
    41: ("Additional Amount", "n", 12),
    # Data Reference Number
    42: ("Data Reference Number", "n", 15),
    # Processing Status Code
    43: ("Processing Status Code", "n", 1),
    # Amount, Original
    44: ("Original Transaction Amount", "n", 12),
    # Network Management Origin Code
    45: ("Network Management Origin Code", "n", 1),
    # Network Management Reason Code
    46: ("Network Management Reason Code", "n", 3),
    # PIN Data
    47: ("PIN Data", "b", 16),
    # Card Verifiable Data
    48: ("Card Verifiable Data", "b", 32),
    # Additional Data
    49: ("Currency Code, Transaction", "n", 3),
    # Currency Code, Settlement
    50: ("Currency Code, Settlement", "n", 3),
    # Currency Code, Cardholder
    51: ("Currency Code, Cardholder", "n", 3),
    # Interchange Routing Indicator
    52: ("Interchange Routing Indicator", "a", 6),
    # Interchange Data
    53: ("Interchange Data", "n", 3),
    # Interchange Data, Extended
    54: ("Interchange Data, Extended", "b", 102),
    # Processing Fee, Authorization
    55: ("Processing Fee, Authorization", "n", 12),
    # Processing Fee, Settlement
    56: ("Processing Fee, Settlement", "n", 12),
    # EMV Data (Tag-Length-Value)
    57: ("EMV Data / Track 3 Data", "b", 999),
    # Transaction Status
    58: ("Transaction Status", "an", 1),
    # Debit/Credit Code
    59: ("Debit/Credit Code", "an", 1),
    # Miscellaneous Data
    60: ("Miscellaneous Data", "a", 99),
    # Original MTI
    61: ("Original MTI", "an", 4),
    # Account Type
    62: ("Account Type", "n", 4),
    # Private Data
    63: ("Private Data", "b", 999),
    # Extended Bitmap (if 128-bit bitmap)
    64: ("Extended Bitmap (128-bit)", "b", 8),
}

# ============================================================================
# ISO 8583 Parser
# ============================================================================

@dataclass
class ISO8583Message:
    """An ISO 8583 message parsed into its components."""
    mti: str = ""                    # Message Type Indicator (4 digits)
    bitmap: bytes = b""              # Raw bitmap bytes (8 or 16 bytes)
    bitmap_bits: List[int] = field(default_factory=list)  # Present element numbers
    bitmap_is_128: bool = False      # True if 128-bit bitmap used
    data_elements: Dict[int, bytes] = field(default_factory=dict)  # Raw element bytes
    raw: bytes = b""                 # Original raw message
    
    def get_element_str(self, element_num: int, encoding: str = 'utf-8') -> str:
        """Get a data element as a decoded string."""
        if element_num not in self.data_elements:
            return ""
        raw = self.data_elements[element_num]
        if isinstance(raw, bytes):
            return raw.decode(encoding, errors='replace').strip()
        return str(raw)
    
    def get_element_int(self, element_num: int) -> Optional[int]:
        """Get a data element as an integer (for numeric fields)."""
        if element_num not in self.data_elements:
            return None
        raw = self.data_elements[element_num]
        if isinstance(raw, bytes):
            try:
                return int(raw.decode('ascii').strip())
            except (ValueError, UnicodeDecodeError):
                return None
        return None
    
    def get_element_hex(self, element_num: int) -> str:
        """Get a data element as hex string (for binary fields)."""
        if element_num not in self.data_elements:
            return ""
        raw = self.data_elements[element_num]
        if isinstance(raw, bytes):
            return raw.hex()
        return ""
    
    def __repr__(self):
        lines = [f"ISO8583 MTI: {self.mti}"]
        lines.append(f"  Bitmap: {self.bitmap.hex()} ({'128-bit' if self.bitmap_is_128 else '64-bit'})")
        lines.append(f"  Data elements ({len(self.data_elements)}):")
        for elem_num in sorted(self.data_elements.keys()):
            name, fmt, length = DATA_ELEMENTS.get(elem_num, ("Unknown", "?", "?"))
            raw = self.data_elements[elem_num]
            if isinstance(raw, bytes):
                preview = raw[:30].decode('ascii', errors='replace') if raw else ""
                lines.append(f"    {elem_num:3d} [{name}]: {preview!r} (raw: {raw.hex() if raw else 'empty'})")
            else:
                lines.append(f"    {elem_num:3d} [{name}]: {raw!r}")
        return "\n".join(lines)


class ISO8583Parser:
    """Parses ISO 8583 binary messages into structured data."""
    
    def __init__(self):
        self.position = 0
    
    def parse(self, raw: bytes) -> ISO8583Message:
        """Parse an ISO 8583 message from raw bytes."""
        if len(raw) < 4:
            raise ValueError(f"Message too short: {len(raw)} bytes (need at least 4 for MTI)")
        
        # Parse MTI (first 4 bytes, ASCII)
        mti = raw[:4].decode('ascii', errors='replace')
        if not mti.isdigit() or len(mti) != 4:
            raise ValueError(f"Invalid MTI: {mti!r}")
        
        msg = ISO8583Message(mti=mti, raw=raw)
        self.position = 4
        
        if self.position + 8 > len(raw):
            raise ValueError(f"Not enough bytes for bitmap: {len(raw) - self.position} remaining")
        
        # Parse bitmap (first 8 bytes after MTI)
        bitmap = raw[self.position:self.position + 8]
        msg.bitmap = bitmap
        msg.bitmap_is_128 = (bitmap[0] & 0x80) != 0  # MSB of first byte set = 128-bit
        
        # Determine bitmap length
        bitmap_len = 16 if msg.bitmap_is_128 else 8
        
        if self.position + bitmap_len > len(raw):
            raise ValueError(f"Not enough bytes for full bitmap: need {bitmap_len}, have {len(raw) - self.position}")
        
        if msg.bitmap_is_128:
            msg.bitmap = raw[self.position:self.position + 16]
            self.position += 16
        else:
            self.position += 8
        
        # Parse bitmap bits
        msg.bitmap_bits = self._parse_bitmap(msg.bitmap)
        
        # Parse data elements
        self._parse_data_elements(raw, msg)
        
        return msg
    
    def _parse_bitmap(self, bitmap: bytes) -> List[int]:
        """Parse bitmap bytes into list of present element numbers."""
        bits = []
        total_bits = len(bitmap) * 8
        for byte_idx, byte in enumerate(bitmap):
            for bit_idx in range(8):
                # MSB first within each byte
                bit_pos = byte_idx * 8 + bit_idx
                bit_value = (byte >> (7 - bit_idx)) & 1
                if bit_value:
                    element_num = bit_pos + 1  # 1-indexed
                    bits.append(element_num)
        return bits
    
    def _parse_data_elements(self, raw: bytes, msg: ISO8583Message):
        """Parse data elements from the message bytes following the bitmap."""
        pos = self.position  # Position after bitmap
        
        for element_num in msg.bitmap_bits:
            if element_num == 1:
                # Element 1 is the bitmap itself — skip
                continue
            if element_num == 64 and not msg.bitmap_is_128:
                # Element 64 is the extended bitmap marker — skip
                continue
            
            if pos >= len(raw):
                break
            
            def read_fixed(length: int) -> bytes:
                nonlocal pos
                data = raw[pos:pos + length]
                pos += length
                return data
            
            def read_llvar() -> bytes:
                nonlocal pos
                if pos + 2 > len(raw):
                    return b""
                length = int(raw[pos:pos + 2].decode('ascii'))
                pos += 2
                data = raw[pos:pos + length]
                pos += length
                return data
            
            def read_llvvar() -> bytes:
                nonlocal pos
                if pos + 3 > len(raw):
                    return b""
                length = int(raw[pos:pos + 3].decode('ascii'))
                pos += 3
                data = raw[pos:pos + length]
                pos += length
                return data
            
            if element_num not in DATA_ELEMENTS:
                # Unknown element — try to read as LLVAR, then skip
                # For unknown elements, we'll try LLVAR first
                length_str = raw[pos:pos + 2].decode('ascii', errors='replace')
                try:
                    length = int(length_str)
                    if length > 0 and pos + 2 + length <= len(raw):
                        msg.data_elements[element_num] = raw[pos + 2:pos + 2 + length]
                        pos += 2 + length
                    else:
                        pos += 2
                except ValueError:
                    pos += 2
                continue
            
            name, fmt, length_def = DATA_ELEMENTS[element_num]
            
            if fmt == 'n' or fmt == 'a' or fmt == 'an':
                # Alphanumeric or numeric — usually fixed or LLVAR
                if isinstance(length_def, int):
                    msg.data_elements[element_num] = read_fixed(length_def)
                elif length_def == 'LLVAR':
                    msg.data_elements[element_num] = read_llvar()
                elif length_def == 'LLLVAR':
                    msg.data_elements[element_num] = read_llvvar()
                else:
                    msg.data_elements[element_num] = read_llvar()
            elif fmt == 'b':
                # Binary data
                if isinstance(length_def, int):
                    msg.data_elements[element_num] = read_fixed(length_def)
                elif length_def == 'LLVAR':
                    msg.data_elements[element_num] = read_llvar()
                elif length_def == 'LLLVAR':
                    msg.data_elements[element_num] = read_llvvar()
                else:
                    msg.data_elements[element_num] = read_llvar()
            elif fmt == 'z':
                # Track data — usually LLVAR
                msg.data_elements[element_num] = read_llvar()
            else:
                # Default: try LLVAR
                msg.data_elements[element_num] = read_llvar()


# ============================================================================
# ISO 8583 Encoder
# ============================================================================

class ISO8583Encoder:
    """Encodes ISO 8583 message data into binary format."""
    
    def __init__(self):
        pass
    
    def encode(self, mti: str, elements: Dict[int, bytes], use_128_bitmap: bool = False) -> bytes:
        """
        Encode ISO 8583 message data into binary format.
        
        Args:
            mti: 4-digit Message Type Indicator (e.g. "0100")
            elements: Dict mapping element numbers to raw bytes
            use_128_bitmap: If True, use 128-bit bitmap (element 64 includes extended bitmap)
        """
        if len(mti) != 4 or not mti.isdigit():
            raise ValueError(f"Invalid MTI: {mti!r}")
        
        # Determine which elements are present
        present_elements = sorted(elements.keys())
        
        # Build bitmap
        bitmap = self._build_bitmap(present_elements, use_128_bitmap)
        
        # Build message: MTI + bitmap + data elements
        result = mti.encode('ascii') + bitmap
        
        # Add data elements in order
        for element_num in present_elements:
            elem_bytes = elements[element_num]
            
            # Determine length type
            if element_num not in DATA_ELEMENTS:
                # Unknown element — encode as LLVAR
                length = len(elem_bytes)
                if length <= 99:
                    result += f"{length:02d}".encode('ascii') + elem_bytes
                else:
                    result += f"{length:03d}".encode('ascii') + elem_bytes
            else:
                name, fmt, length_def = DATA_ELEMENTS[element_num]
                
                if isinstance(length_def, int):
                    # Fixed length — pad or truncate to match
                    padded = self._pad_element(elem_bytes, fmt, length_def)
                    result += padded
                elif length_def == 'LLVAR':
                    # 2-digit length prefix
                    result += f"{len(elem_bytes):02d}".encode('ascii') + elem_bytes
                elif length_def == 'LLLVAR':
                    # 3-digit length prefix
                    result += f"{len(elem_bytes):03d}".encode('ascii') + elem_bytes
                else:
                    # Default: LLVAR
                    result += f"{len(elem_bytes):02d}".encode('ascii') + elem_bytes
        
        return result
    
    def _build_bitmap(self, present_elements: List[int], use_128_bitmap: bool) -> bytes:
        """Build bitmap bytes from list of present element numbers."""
        total_bits = 128 if use_128_bitmap else 64
        bitmap_bytes = bytearray(total_bits // 8)
        
        for elem_num in present_elements:
            if elem_num < 1 or elem_num > total_bits:
                continue
            if elem_num == 1 and not use_128_bitmap:
                # Element 1 = bitmap presence — always set in 64-bit mode
                # (the bitmap itself is present)
                pass
            bit_idx = elem_num - 1
            byte_idx = bit_idx // 8
            bit_in_byte = 7 - (bit_idx % 8)
            bitmap_bytes[byte_idx] |= (1 << bit_in_byte)
        
        # Set bit 1 (MSB of first byte) to indicate presence of bitmap
        # Actually, the bit 1 indicates the bitmap itself is present
        # For 64-bit: bit 1 set means 64-bit bitmap
        # For 128-bit: bit 1 set means 128-bit bitmap follows
        if use_128_bitmap:
            # Bit 1 (MSB of first byte) = 1 means secondary bitmap present
            bitmap_bytes[0] |= 0x80
        
        return bytes(bitmap_bytes)
    
    def _pad_element(self, data: bytes, fmt: str, length: int) -> bytes:
        """Pad or truncate data element to fixed length."""
        if len(data) >= length:
            return data[:length]
        
        if fmt in ('n',):
            # Numeric: right-pad with zeros
            return data + b'\x00' * (length - len(data))
        elif fmt in ('a', 'an'):
            # Alphanumeric: right-pad with spaces
            return data + b' ' * (length - len(data))
        elif fmt == 'b':
            # Binary: left-pad with zeros
            return b'\x00' * (length - len(data)) + data
        elif fmt == 'z':
            # Track data: left-justified, left-pad with zeros
            return b'\x00' * (length - len(data)) + data
        else:
            # Default: right-pad with zeros
            return data + b'\x00' * (length - len(data))


# ============================================================================
# Helper: Build common transaction messages
# ============================================================================

def build_authorization_request(pan: str, amount_cents: int, 
                                 transaction_date: str = None,
                                 transaction_time: str = None,
                                 terminal_id: str = "T001",
                                 trace_num: int = None) -> bytes:
    """
    Build an ISO 8583 authorization request (MTI 0100).
    
    This simulates what a POS terminal sends to request card authorization.
    """
    import random
    import time
    
    if transaction_date is None:
        now = time.localtime()
        transaction_date = f"{now.tm_year - 2000:02d}{now.tm_mon:02d}{now.tm_mday:02d}"
    if transaction_time is None:
        now = time.localtime()
        transaction_time = f"{now.tm_hour:02d}{now.tm_min:02d}{now.tm_sec:02d}"
    
    if trace_num is None:
        trace_num = random.randint(100000, 999999)
    
    # Amount as 12-digit string (cents * 100 to get dollars.cents format)
    # ISO 8583 amount fields are in cents (or smallest currency unit) when
    # the field is 12 digits — but convention varies. We'll use cents directly.
    # Actually, ISO 8583 amount fields are typically in the currency's smallest
    # unit (cents for USD). A 12n field means 12 digits, representing cents.
    # For a $25.00 transaction, that's 2500 cents → "000000002500"
    amount_str = f"{amount_cents:012d}"
    
    # Processing code: 6 digits (3 function + 3 fund + 3 amount type)
    # Function: 0=sale, 1=cash, 2=refund, 3=...
    # Fund: 0=debit, 1=credit, 2=...
    # Amount type: 0=currency, 1=...
    # For a standard sale: "000000"
    processing_code = "000000"
    
    # Element 7 is 10n (YYMMDDHHMM — no seconds), element 12 is 12n (YYMMDDHHMMSS)
    # Build 10-digit transmission date/time (without seconds)
    tran_dt_10 = f"{transaction_date}{transaction_time[:4]}"  # YYMMDDHHMM
    
    elements = {
        2:  pan.encode('ascii'),                          # PAN (19 digits, padded)
        3:  processing_code.encode('ascii'),              # Processing Code (6n)
        4:  amount_str.encode('ascii'),                   # Amount, Transaction (12n)
        7:  tran_dt_10.encode('ascii'),                   # Tran Date/Time (10n)
        11: f"{trace_num:06d}".encode('ascii'),           # System Trace Audit Number (6n)
        12: f"{transaction_date}{transaction_time}".encode('ascii'),  # Local Date/Time (12n)
        13: transaction_date.encode('ascii'),             # Transaction Date (6n)
        14: transaction_time.encode('ascii'),             # Transaction Time (6n)
        22: terminal_id.encode('ascii').ljust(8),         # POS Terminal ID (8an)
        25: b"USA",                                       # Terminal Country Code (3n)
        26: b"00",                                        # Terminal Type (2n)
    }
    
    # Pad PAN to 19 digits
    if len(elements[2]) < 19:
        elements[2] = elements[2] + b'\x00' * (19 - len(elements[2]))
    
    encoder = ISO8583Encoder()
    return encoder.encode("0100", elements)


def build_authorization_response(response_code: str = "00",
                                  authorization_code: str = "AUTH123",
                                  retrieval_ref: str = None) -> bytes:
    """
    Build an ISO 8583 authorization response (MTI 0110).
    
    This simulates what the card issuer sends back to the terminal.
    """
    import random
    
    if retrieval_ref is None:
        retrieval_ref = f"{random.randint(100000000000, 999999999999):012d}"
    
    elements = {
        3:  b"000000",                                    # Processing Code (6n)
        4:  b"000000000000",                              # Amount, Transaction (12n) — echoes request amount (empty for demo)
        7:  b"",                                          # Transmission Date/Time (filled by parser context)
        18: retrieval_ref.encode('ascii'),                # Retrieval Reference Number (12an)
        19: b"000",                                       # Settlement Code (3n)
        37: response_code.encode('ascii'),                # Response Code (2an)
        38: authorization_code.encode('ascii'),           # Authorization Code (6an)
        39: response_code.encode('ascii'),                # Response Code (duplicate, 2an)
        44: b"",                                          # Additional Response Data
        61: b"0100",                                      # Original MTI (4an)
    }
    
    encoder = ISO8583Encoder()
    return encoder.encode("0110", elements)


# ============================================================================
# EMV-like Tag-Length-Value (TLV) parser for data element 55/57
# ============================================================================

def parse_tlv(data: bytes) -> Dict[int, bytes]:
    """
    Parse EMV Tag-Length-Value data (used in data element 55/57).
    
    EMV tags are 1-4 bytes, with the tag encoding the tag number.
    Tag structure:
    - 0x00-0xBF: single byte tags (0x00-0xBF = tags 0-191)
    - 0xC0-0xDF: first byte of 2-byte tag (high byte), next byte = low byte
    - 0xE0-0xEF: first byte of 3-byte tag
    - 0xF0-0xFF: first byte of 4-byte tag
    
    Length encoding:
    - 0x00-0xBF: short length (1 byte)
    - 0xC0-0xCF: long length (2 bytes follow)
    - 0xD0-0xDF: long length (3 bytes follow)
    - 0xE0-0xEF: long length (4 bytes follow)
    - 0xF0-0xFF: long length (5 bytes follow)
    
    For simplicity, we handle single-byte tags and short lengths.
    """
    tags = {}
    pos = 0
    
    while pos < len(data):
        # Parse tag
        first_byte = data[pos]
        if first_byte >= 0xC0 and first_byte <= 0xDF:
            # 2-byte tag
            tag = ((first_byte & 0x1F) << 8) | data[pos + 1]
            pos += 2
        elif first_byte >= 0xE0 and first_byte <= 0xEF:
            # 3-byte tag
            tag = ((first_byte & 0x0F) << 16) | (data[pos + 1] << 8) | data[pos + 2]
            pos += 3
        elif first_byte >= 0xF0:
            # 4-byte tag
            tag = ((first_byte & 0x07) << 24) | (data[pos + 1] << 16) | (data[pos + 2] << 8) | data[pos + 3]
            pos += 4
        else:
            # 1-byte tag (0x00-0xBF)
            tag = first_byte
            pos += 1
        
        if pos >= len(data):
            break
        
        # Parse length
        length_byte = data[pos]
        if length_byte <= 0xBF:
            length = length_byte
            pos += 1
        elif length_byte <= 0xCF:
            length = (data[pos + 1] << 8) | data[pos + 2]
            pos += 3
        elif length_byte <= 0xDF:
            length = (data[pos + 1] << 16) | (data[pos + 2] << 8) | data[pos + 3]
            pos += 4
        else:
            # Very long length — skip for demo
            length = 0
            pos += 1
        
        if pos + length > len(data):
            break
        
        # Extract value
        value = data[pos:pos + length]
        pos += length
        tags[tag] = value
    
    return tags


# ============================================================================
# DEMONSTRATION
# ============================================================================

def demonstrate():
    print("=" * 60)
    print("ISO 8583 MESSAGE PARSER/ENCODER — PHASE 2A")
    print("=" * 60)
    
    print("""
ISO 8583 is the messaging standard used by payment networks (Visa, Mastercard,
etc.) to exchange transaction data between terminals, processors, and issuers.

Every payment transaction you make goes through ISO 8583 messages behind the
scenes. When you swipe/tap your card, the terminal formats the transaction
into an ISO 8583 message and sends it to the processor.

This project:
  1. Parses ISO 8583 binary messages (MTI + bitmap + data elements)
  2. Encodes structured data back to ISO 8583 format
  3. Builds example authorization request/response messages
  4. Parses EMV TLV data (used in element 55 for chip transactions)
  
Reference: ISO 8583-1:2003 — "Financial transaction card originiation and
acceptance — Message format and data elements"
""")
    
    # --- Step 1: Build and parse an authorization request ---
    print("[1] Building an ISO 8583 Authorization Request (MTI 0100)...")
    
    # Simulate a $25.50 purchase at terminal T001
    request_bytes = build_authorization_request(
        pan="4532015876543210",     # Visa test PAN
        amount_cents=2550,           # $25.50 in cents
        terminal_id="T001",
        trace_num=123456
    )
    
    print(f"    Raw message ({len(request_bytes)} bytes): {request_bytes.hex()}")
    
    # Parse it back
    parser = ISO8583Parser()
    msg = parser.parse(request_bytes)
    
    print(f"\n    Parsed message:")
    print(f"    {msg}")
    
    # Show key fields
    print(f"\n    Key fields:")
    print(f"    MTI:                {msg.mti}")
    print(f"    PAN:                {msg.get_element_str(2)[:16]}... (last 4: {msg.get_element_str(2)[-4:]})")
    print(f"    Amount:             ${msg.get_element_int(4) / 100:.2f}")
    print(f"    Processing Code:    {msg.get_element_str(3)}")
    print(f"    Trace Number:       {msg.get_element_str(11)}")
    print(f"    Terminal ID:        {msg.get_element_str(22)}")
    print(f"    Country Code:       {msg.get_element_str(25)}")
    print(f"    Transaction Date:   {msg.get_element_str(13)}")
    print(f"    Transaction Time:   {msg.get_element_str(14)}")
    
    # --- Step 2: Build and parse an authorization response ---
    print("\n[2] Building an ISO 8583 Authorization Response (MTI 0110)...")
    
    response_bytes = build_authorization_response(
        response_code="00",          # Approved
        authorization_code="AUTH123",
        retrieval_ref="REF123456789012"
    )
    
    print(f"    Raw message ({len(response_bytes)} bytes): {response_bytes.hex()}")
    
    msg2 = parser.parse(response_bytes)
    print(f"\n    Parsed response:")
    print(f"    {msg2}")
    
    print(f"\n    Response fields:")
    print(f"    MTI:                {msg2.mti}")
    print(f"    Response Code:      {msg2.get_element_str(37)} ({'Approved' if msg2.get_element_str(37) == '00' else 'Declined'})")
    print(f"    Authorization Code: {msg2.get_element_str(38)}")
    print(f"    Retrieval Ref:      {msg2.get_element_str(18)}")
    print(f"    Original MTI:       {msg2.get_element_str(61)}")
    
    # --- Step 3: Demonstrate bitmap logic ---
    print("\n[3] Bitmap logic demonstration...")
    
    print(f"""
    How the bitmap works:
    
    The bitmap is 8 bytes (64 bits) or 16 bytes (128 bits).
    Each bit represents a data element (1-64 or 1-128).
    Bit set = element present in message.
    
    MSB of byte 0 = element 1 (which is the bitmap itself)
    
    For our request message:
      Element 2 (PAN)      — bit 2 set
      Element 3 (Proc Code) — bit 3 set
      Element 4 (Amount)    — bit 4 set
      Element 7 (Date/Time) — bit 7 set
      Element 11 (Trace)    — bit 11 set
      Element 12 (Local DT) — bit 12 set
      Element 13 (Date)     — bit 13 set
      Element 14 (Time)     — bit 14 set
      Element 22 (Term ID)  — bit 22 set
      Element 25 (Country)  — bit 25 set
      Element 26 (Term Type)- bit 26 set
    
    Bitmap hex: {msg.bitmap.hex()}
      = {''.join(f'{b:08b}' for b in msg.bitmap)}
      Bits set: {msg.bitmap_bits}
""")
    
    # --- Step 4: Demonstrate a declined transaction ---
    print("[4] Demonstrating a declined transaction...")
    
    decline_bytes = build_authorization_response(
        response_code="05",          # Do not honor
        authorization_code="",
        retrieval_ref="DECLINE0000001"
    )
    
    msg3 = parser.parse(decline_bytes)
    print(f"    Response Code: {msg3.get_element_str(37)} — {'Approved' if msg3.get_element_str(37) == '00' else 'DECLINED: ' + msg3.get_element_str(37)}")
    print(f"    Authorization Code: {msg3.get_element_str(38) or '(none — declined)'}")
    
    print("""
    Common response codes:
      00 — Approved
      01 — Refer to card issuer
      02 — Refer to issuer (card pick-up)
      03 — Invalid merchant
      04 — Pick-up card
      05 — Do not honor
      06 — Error
      07 — Pick-up card (special condition)
      08 — Honor with identification
      09 — Request in progress
      10 — Approved (VIP)
      12 — Invalid transaction
      13 — Invalid amount
      14 — Invalid card number
      30 — Format error
      31 — Missing record
      32 — Card captured
      33 — Card expired
      34 — Suspected fraud
      35 — Exceeds withdrawal limit
      36 — Restricted card
      37 — Card holder not present (pick-up)
      38 — Allowable PIN tries exceeded
      39 — No reason to decline (retry)
""")
    
    # --- Step 5: EMV TLV parsing demo ---
    print("[5] EMV Tag-Length-Value (TLV) parsing demo...")
    
    # Build synthetic EMV chip data (data element 55)
    # Common EMV tags:
    # 0x9F02 — Authorisation Response Code
    # 0x9F03 — Applied Reference Data
    # 0x9F10 — Issuer Application Data
    # 0x9F37 — Transaction Verification Results
    # 0x9F36 — Transaction Certificate Type
    
    emv_data = bytes([
        # Tag 0x9F02 (Authorisation Response Code), length 2, value "00"
        0x9F, 0x02, 0x02, 0x30, 0x30,
        # Tag 0x9F03 (Applied Reference Data), length 6, value "REF123"
        0x9F, 0x03, 0x06, 0x52, 0x45, 0x46, 0x31, 0x32, 0x33,
        # Tag 0x9F10 (Issuer Application Data), length 8, value "DATA0001"
        0x9F, 0x10, 0x08, 0x44, 0x41, 0x54, 0x41, 0x30, 0x30, 0x30, 0x31,
        # Tag 0x9F37 (Transaction Verification Results), length 5, value "ABC12"
        0x9F, 0x37, 0x05, 0x41, 0x42, 0x43, 0x31, 0x32,
    ])
    
    print(f"    EMV chip data ({len(emv_data)} bytes): {emv_data.hex()}")
    
    tags = parse_tlv(emv_data)
    emv_tag_names = {
        0x9F02: "Authorisation Response Code",
        0x9F03: "Applied Reference Data",
        0x9F10: "Issuer Application Data",
        0x9F37: "Transaction Verification Results",
        0x9F36: "Transaction Certificate Type",
        0x9F5B: "Cardholder Name",
    }
    
    print(f"\n    Parsed EMV tags:")
    for tag in sorted(tags.keys()):
        name = emv_tag_names.get(tag, f"Tag 0x{tag:04X}")
        value = tags[tag]
        print(f"    0x{tag:04X} [{name}]: {value.hex()} ({value.decode('ascii', errors='replace')!r})")
    
    # --- Step 6: Round-trip test ---
    print("[6] Round-trip test — encode then parse, verify data integrity...")
    
    # Element 7 is 10n (YYMMDDHHMM), element 12 is 12n (YYMMDDHHMMSS)
    # Use consistent 10-digit format for element 7
    tran_dt_10 = f"{transaction_date}{transaction_time[:4]}"  # YYMMDDHHMM
    
    original_elements = {
        2:  b"4532015876543210000",     # PAN (19 digits)
        3:  b"000000",                   # Processing Code
        4:  b"000000002550",             # Amount ($25.50)
        7:  tran_dt_10.encode('ascii'),  # Transmission Date/Time (10n)
        11: b"123456",                   # Trace Number
        13: b"260828",                   # Date
        14: b"143000",                   # Time
        22: b"T001    ",                 # Terminal ID (padded to 8)
    }
    
    encoder = ISO8583Encoder()
    encoded = encoder.encode("0100", original_elements)
    
    print(f"    Original elements: {len(original_elements)} elements")
    print(f"    Encoded ({len(encoded)} bytes): {encoded.hex()}")
    
    parsed = parser.parse(encoded)
    print(f"    Parsed back: MTI={parsed.mti}, {len(parsed.data_elements)} elements")
    
    # Verify each element
    all_match = True
    for elem_num in sorted(original_elements.keys()):
        orig = original_elements[elem_num]
        parsed_elem = parsed.data_elements.get(elem_num, b"")
        match = orig == parsed_elem
        if not match:
            all_match = False
            print(f"    MISMATCH element {elem_num}: orig={orig.hex()}, parsed={parsed_elem.hex()}")
    
    if all_match:
        print(f"    All {len(original_elements)} elements matched perfectly ✓")
    
    # --- Step 7: Different MTI examples ---
    print("\n[7] Common MTI examples (message types you'd see in real transactions):")
    
    mtis = {
        "0100": "Authorization Request — POS terminal asks issuer to approve a card transaction",
        "0110": "Authorization Response — Issuer says approve/decline with auth code",
        "0200": "Financial Request — Purchase transaction (full financial detail)",
        "0210": "Financial Response — Response to a purchase transaction",
        "0400": "Reversal Request — Undo a previous transaction (timeout, error)",
        "0420": "Reversal Response — Response to a reversal",
        "0800": "Network Management Request — Terminal asks network for status/heartbeat",
        "0810": "Network Management Response — Network replies with status",
        "0900": "Allocation Request — Settlement batch processing",
        "0910": "Allocation Response — Response to allocation",
        "1200": "Account Information Request — Balance inquiry, account status",
        "1210": "Account Information Response — Response with account info",
        "1300": "Verification Request — Card verification (CVV, card status check)",
        "1310": "Verification Response — Response to card verification",
        "1400": "Special Payment Request — Gift card, stored value, loyalty redemption",
        "1410": "Special Payment Response — Response to special payment",
        "1500": "Information Request — Non-financial info (cardholder data, terminal info)",
        "1510": "Information Response — Response with information",
        "1600": "Recorded Media Financial Request — Pre-printed voucher, checks",
        "1610": "Recorded Media Financial Response — Response to recorded media",
        "1700": "Switching in Progress Request — Network switch status check",
        "1710": "Switching in Progress Response — Network switch status response",
    }
    
    for mti, desc in sorted(mtis.items()):
        print(f"    {mti} — {desc}")
    
    # --- Step 8: Save artifacts ---
    import os, json
    
    output_dir = "/c/Users/mobil/orca/projects/my 1st/payment_study"
    os.makedirs(output_dir, exist_ok=True)
    
    artifacts = {
        "authorization_request": {
            "mti": "0100",
            "raw_hex": request_bytes.hex(),
            "raw_length": len(request_bytes),
            "elements": {},
        },
        "authorization_response": {
            "mti": "0110",
            "raw_hex": response_bytes.hex(),
            "raw_length": len(response_bytes),
            "elements": {},
        },
        "emv_sample": {
            "raw_hex": emv_data.hex(),
            "tags": {f"0x{tag:04X}": value.hex() for tag, value in tags.items()},
        },
    }
    
    # Fill in parsed elements
    for elem_num in sorted(msg.data_elements.keys()):
        if elem_num in DATA_ELEMENTS:
            name, fmt, _ = DATA_ELEMENTS[elem_num]
            artifacts["authorization_request"]["elements"][str(elem_num)] = {
                "name": name,
                "format": fmt,
                "raw_hex": msg.data_elements[elem_num].hex() if isinstance(msg.data_elements[elem_num], bytes) else str(msg.data_elements[elem_num]),
                "decoded": msg.get_element_str(elem_num),
            }
    
    for elem_num in sorted(msg2.data_elements.keys()):
        if elem_num in DATA_ELEMENTS:
            name, fmt, _ = DATA_ELEMENTS[elem_num]
            artifacts["authorization_response"]["elements"][str(elem_num)] = {
                "name": name,
                "format": fmt,
                "raw_hex": msg2.data_elements[elem_num].hex() if isinstance(msg2.data_elements[elem_num], bytes) else str(msg2.data_elements[elem_num]),
                "decoded": msg2.get_element_str(elem_num),
            }
    
    with open(os.path.join(output_dir, "iso8583_sample.json"), "w") as f:
        json.dump(artifacts, f, indent=2)
    
    print(f"\n[8] Artifacts saved to: {output_dir}/iso8583_sample.json")
    
    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("""
KEY TAKEAWAYS:

1. ISO 8583 is the backbone of every card transaction — when you tap your card
   at a store, an ISO 8583 message flows from terminal → processor → issuer →
   processor → terminal, carrying the transaction details.

2. The message structure is simple but precise:
   - MTI (4 digits) tells you WHAT kind of message this is
   - Bitmap (8 or 16 bytes) tells you WHICH fields are present
   - Data elements are the actual transaction data (PAN, amount, date, etc.)

3. The bitmap is the clever part — it lets the message be sparse (only include
   fields you need) while still being parseable (you can tell which fields are
   present without a schema).

4. Response codes (element 37/39) are 2 characters that carry the entire
   decision: "00" = approved, "05" = declined, etc. The authorization code
   (element 38) is what you see printed on receipts.

5. EMV chip transactions add TLV-encoded data in element 55, carrying
   cryptographic verification data from the chip to the issuer.

6. Real transactions use much more fields than our demo — but the fundamental
   structure (MTI + bitmap + elements) is the same.
""")


if __name__ == "__main__":
    demonstrate()
