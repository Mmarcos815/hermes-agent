#!/usr/bin/env python3
"""
ISO 8583 Financial Transaction Message Engine & Security Lab
Standard: ISO 8583:1987 / 1993 / 2003

Architecture:
1. Message Type Indicator (MTI) Analyzer (Version, Class, Function, Origin)
2. Primary & Secondary Bitmap Pack / Unpack (Hex and Binary representations)
3. Data Elements (DE) Dictionary & Parsing (LLVAR, LLLVAR, Fixed Numeric/Alpha)
4. Authorization & Financial Transaction Simulation Engine
5. Reversal and Settlement Life-cycle Engine
"""

import sys, struct, binascii, json

# ── Data Element Definitions (Subset of standard core financial fields) ────

DATA_ELEMENTS = {
    1:  ("b", 8, "Secondary Bitmap"),
    2:  ("LLVAR", 19, "Primary Account Number (PAN)"),
    3:  ("n", 6, "Processing Code"),
    4:  ("n", 12, "Amount, Transaction (Cents)"),
    7:  ("n", 10, "Transmission Date & Time (MMDDhhmmss)"),
    11: ("n", 6, "Systems Trace Audit Number (STAN)"),
    12: ("n", 6, "Time, Local Transaction (hhmmss)"),
    13: ("n", 4, "Date, Local Transaction (MMDD)"),
    14: ("n", 4, "Date, Expiration (YYMM)"),
    18: ("n", 4, "Merchant Type (MCC)"),
    22: ("n", 3, "Point of Service (POS) Entry Mode"),
    32: ("LLVAR", 11, "Acquiring Institution Identification Code"),
    37: ("an", 12, "Retrieval Reference Number (RRN)"),
    38: ("an", 6, "Authorization Identification Response"),
    39: ("an", 2, "Response Code (00=Approve, 51=Insufficient Funds, etc.)"),
    41: ("ans", 8, "Card Acceptor Terminal Identification (TID)"),
    42: ("ans", 15, "Card Acceptor Identification Code (MID)"),
    43: ("ans", 40, "Card Acceptor Name/Location"),
    48: ("LLLVAR", 999, "Private Data / Additional Data"),
    49: ("n", 3, "Currency Code, Transaction (840=USD, 978=EUR)"),
    54: ("LLLVAR", 120, "Additional Amounts (Balance Inquiry)"),
    102:("LLVAR", 28, "Account Identification 1 (Source Account)"),
    103:("LLVAR", 28, "Account Identification 2 (Destination Account)")
}

class ISO8583Message:
    def __init__(self, mti="0100"):
        self.mti = mti
        self.fields = {}

    def set_field(self, field_id: int, value: str):
        self.fields[field_id] = str(value)

    def get_field(self, field_id: int) -> str:
        return self.fields.get(field_id, None)

    def generate_bitmap(self) -> bytes:
        max_field = max(self.fields.keys()) if self.fields else 0
        use_secondary = max_field > 64 or 1 in self.fields
        total_bits = 128 if use_secondary else 64
        
        bitmap_bytes = bytearray(total_bits // 8)
        if use_secondary:
            bitmap_bytes[0] |= 0x80

        for f in self.fields.keys():
            if f == 1:
                continue
            byte_idx = (f - 1) // 8
            bit_idx = 7 - ((f - 1) % 8)
            bitmap_bytes[byte_idx] |= (1 << bit_idx)

        return bytes(bitmap_bytes)

    def pack(self) -> bytes:
        """Packs MTI, Bitmap, and Data Elements into wire format."""
        mti_bytes = self.mti.encode("ascii")
        bitmap_bytes = self.generate_bitmap()
        
        payload = bytearray(mti_bytes + bitmap_bytes)

        for f in sorted(self.fields.keys()):
            if f == 1:
                continue
            val = str(self.fields[f])
            f_type, max_len, _ = DATA_ELEMENTS.get(f, ("ans", len(val), "Custom"))

            if f_type == "LLVAR":
                header = f"{len(val):02d}".encode("ascii")
                payload.extend(header + val.encode("ascii"))
            elif f_type == "LLLVAR":
                header = f"{len(val):03d}".encode("ascii")
                payload.extend(header + val.encode("ascii"))
            elif f_type == "n":
                padded = val.zfill(max_len)
                payload.extend(padded.encode("ascii"))
            else: # an, ans
                padded = val.ljust(max_len)
                payload.extend(padded.encode("ascii"))

        return bytes(payload)

    @classmethod
    def unpack(cls, raw: bytes):
        """Unpacks raw wire bytes into an ISO8583Message instance."""
        msg = cls()
        msg.mti = raw[0:4].decode("ascii")
        
        # Primary bitmap
        first_byte = raw[4]
        use_secondary = bool(first_byte & 0x80)
        bitmap_len = 16 if use_secondary else 8
        bitmap = raw[4:4 + bitmap_len]
        
        offset = 4 + bitmap_len
        active_fields = []
        for bit_idx in range(1, bitmap_len * 8 + 1):
            if bit_idx == 1:
                continue
            byte_i = (bit_idx - 1) // 8
            bit_i = 7 - ((bit_idx - 1) % 8)
            if bitmap[byte_i] & (1 << bit_i):
                active_fields.append(bit_idx)

        for f in active_fields:
            if f not in DATA_ELEMENTS:
                continue
            f_type, max_len, _ = DATA_ELEMENTS[f]

            if f_type == "LLVAR":
                length = int(raw[offset:offset+2].decode("ascii"))
                offset += 2
                val = raw[offset:offset+length].decode("ascii")
                offset += length
            elif f_type == "LLLVAR":
                length = int(raw[offset:offset+3].decode("ascii"))
                offset += 3
                val = raw[offset:offset+length].decode("ascii")
                offset += length
            elif f_type in ("n", "an", "ans"):
                val = raw[offset:offset+max_len].decode("ascii")
                offset += max_len
            msg.set_field(f, val.strip())

        return msg

    def to_dict(self):
        return {
            "mti": self.mti,
            "fields": {
                f: {
                    "name": DATA_ELEMENTS.get(f, ("-", 0, "Unknown"))[2],
                    "value": self.fields[f]
                }
                for f in sorted(self.fields.keys())
            }
        }


# ── Core Transaction Engine Simulator ──────────────────────────────────────

class PaymentSwitchSimulator:
    def __init__(self):
        self.accounts = {
            "4111111111111111": {"balance": 500000, "pin": "1234", "status": "ACTIVE"}, # $5,000.00
            "5500000000000004": {"balance": 2500, "pin": "0000", "status": "ACTIVE"}    # $25.00
        }

    def process(self, request_bytes: bytes) -> bytes:
        req = ISO8583Message.unpack(request_bytes)
        resp = ISO8583Message()
        
        # MTI transition: 0100 -> 0110 (Auth Response), 0200 -> 0210 (Financial Tx Resp)
        mti_int = int(req.mti)
        resp.mti = f"{mti_int + 10:04d}"

        # Mirror essential tracking fields
        for f in [2, 3, 4, 7, 11, 12, 13, 37, 41, 42, 49]:
            if req.get_field(f):
                resp.set_field(f, req.get_field(f))

        pan = req.get_field(2)
        amount = int(req.get_field(4) or 0)

        # Business Logic / Authorization Check
        if pan not in self.accounts:
            resp.set_field(39, "14") # Invalid Card Number
        elif self.accounts[pan]["status"] != "ACTIVE":
            resp.set_field(39, "05") # Do Not Honor
        elif self.accounts[pan]["balance"] < amount:
            resp.set_field(39, "51") # Insufficient Funds
        else:
            self.accounts[pan]["balance"] -= amount
            resp.set_field(38, "AUTH01") # Auth Approval Code
            resp.set_field(39, "00")     # Approved (00)
            # DE 54: Updated Ledger Balance
            resp.set_field(54, f"0001840C{self.accounts[pan]['balance']:012d}")

        return resp.pack()


if __name__ == "__main__":
    print("=== ISO 8583 PAYMENT RAILS ENGINE DEMO ===")
    
    # 1. Build an Authorization Request (0100)
    tx = ISO8583Message(mti="0100")
    tx.set_field(2, "4111111111111111")        # PAN
    tx.set_field(3, "000000")                  # Purchase
    tx.set_field(4, "000000015000")            # $150.00
    tx.set_field(7, "0828063000")              # Aug 28, 06:30:00
    tx.set_field(11, "123456")                 # STAN
    tx.set_field(18, "5411")                   # Grocery Stores
    tx.set_field(41, "TERM0001")               # TID
    tx.set_field(49, "840")                    # USD

    packed = tx.pack()
    print(f"\n1. Packed Authorization Request (Hex, {len(packed)} bytes):\n{packed.hex()}")
    
    # 2. Simulate Switch Processing
    switch = PaymentSwitchSimulator()
    resp_bytes = switch.process(packed)
    
    # 3. Unpack & Verify Response
    resp_msg = ISO8583Message.unpack(resp_bytes)
    print(f"\n2. Received Response MTI: {resp_msg.mti}")
    print(f"3. Parsed Fields:\n{json.dumps(resp_msg.to_dict(), indent=2)}")
