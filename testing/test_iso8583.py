#!/usr/bin/env python3
"""
test_iso8583.py — Test ISO 8583 engine against jPOS patterns.

Tests the ISO8583Message pack/unpack cycle, bitmap generation,
and PaymentSwitchSimulator authorization logic using mock data
that mirrors jPOS test patterns.

Run: pytest testing/test_iso8583.py -v
"""

import sys
import os
import pytest

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from iso8583_engine import ISO8583Message, PaymentSwitchSimulator, DATA_ELEMENTS


# ── Mock Data: jPOS-style test vectors ──────────────────────────────────────

MOCK_AUTH_REQUEST = {
    "mti": "0100",
    "fields": {
        2: "4111111111111111",   # PAN (Visa test card)
        3: "000000",              # Processing Code (Purchase)
        4: "000000015000",        # Amount: $150.00
        7: "0828063000",          # Transmission Date/Time
        11: "123456",             # STAN
        18: "5411",               # MCC: Grocery Stores
        41: "TERM0001",           # Terminal ID
        49: "840",                # Currency: USD
    }
}

MOCK_FINANCIAL_REQUEST = {
    "mti": "0200",
    "fields": {
        2: "5500000000000004",   # PAN (Mastercard test)
        3: "000000",
        4: "000000000250",        # Amount: $25.00
        11: "654321",
        41: "TERM0002",
        49: "978",                # Currency: EUR
    }
}

MOCK_INSUFFICIENT_FUNDS = {
    "mti": "0100",
    "fields": {
        2: "5500000000000004",   # Balance: $25.00
        3: "000000",
        4: "000000010000",        # Request: $100.00
        11: "999999",
        41: "TERM0003",
        49: "840",
    }
}


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def switch():
    """Fresh PaymentSwitchSimulator for each test."""
    return PaymentSwitchSimulator()


def build_message(mti: str, fields: dict) -> ISO8583Message:
    """Helper: construct an ISO8583Message from mock data."""
    msg = ISO8583Message(mti=mti)
    for fid, val in fields.items():
        msg.set_field(fid, val)
    return msg


# ── Test: Data Element Dictionary ──────────────────────────────────────────

class TestDataElementDictionary:
    def test_pan_field_defined(self):
        assert 2 in DATA_ELEMENTS
        assert DATA_ELEMENTS[2][0] == "LLVAR"

    def test_amount_field_fixed_width(self):
        f_type, max_len, _ = DATA_ELEMENTS[4]
        assert f_type == "n"
        assert max_len == 12

    def test_response_code_field(self):
        assert 39 in DATA_ELEMENTS
        assert DATA_ELEMENTS[39][0] == "an"

    def test_all_fields_have_valid_format(self):
        for fid, (f_type, max_len, name) in DATA_ELEMENTS.items():
            assert f_type in ("b", "n", "a", "an", "ans", "LLVAR", "LLLVAR")
            assert max_len > 0
            assert len(name) > 0


# ── Test: Message Pack / Unpack Roundtrip ──────────────────────────────────

class TestMessageRoundtrip:
    def test_auth_request_roundtrip(self):
        original = build_message("0100", MOCK_AUTH_REQUEST["fields"])
        packed = original.pack()
        restored = ISO8583Message.unpack(packed)

        assert restored.mti == "0100"
        assert restored.get_field(2) == "4111111111111111"
        assert restored.get_field(4) == "000000015000"
        assert restored.get_field(49) == "840"

    def test_financial_request_roundtrip(self):
        original = build_message("0200", MOCK_FINANCIAL_REQUEST["fields"])
        packed = original.pack()
        restored = ISO8583Message.unpack(packed)

        assert restored.mti == "0200"
        assert restored.get_field(2) == "5500000000000004"
        assert restored.get_field(49) == "978"

    def test_bitmap_64_bit(self):
        msg = build_message("0100", {2: "4111111111111111", 3: "000000"})
        bitmap = msg.generate_bitmap()
        assert len(bitmap) == 8

    def test_bitmap_128_bit_when_field_gt_64(self):
        msg = build_message("0100", {2: "4111111111111111", 75: "test"})
        bitmap = msg.generate_bitmap()
        assert len(bitmap) == 16
        assert bitmap[0] & 0x80  # Secondary bitmap indicator set


# ── Test: Payment Switch Authorization ─────────────────────────────────────

class TestPaymentSwitch:
    def test_approved_transaction(self, switch):
        msg = build_message("0100", MOCK_AUTH_REQUEST["fields"])
        packed = msg.pack()
        response = switch.process(packed)
        resp = ISO8583Message.unpack(response)

        assert resp.mti == "0110"
        assert resp.get_field(39) == "00"
        assert resp.get_field(38) == "AUTH01"

    def test_insufficient_funds(self, switch):
        msg = build_message("0100", MOCK_INSUFFICIENT_FUNDS["fields"])
        packed = msg.pack()
        response = switch.process(packed)
        resp = ISO8583Message.unpack(response)

        assert resp.get_field(39) == "51"

    def test_invalid_card(self, switch):
        fields = {
            2: "9999999999999999",
            3: "000000",
            4: "000000001000",
            11: "111111",
            41: "TERM9999",
            49: "840",
        }
        msg = build_message("0100", fields)
        response = switch.process(msg.pack())
        resp = ISO8583Message.unpack(response)

        assert resp.get_field(39) == "14"

    def test_balance_deducted_on_approval(self, switch):
        msg = build_message("0100", MOCK_AUTH_REQUEST["fields"])
        switch.process(msg.pack())
        assert switch.accounts["4111111111111111"]["balance"] == 485000

    def test_mti_transition_financial(self, switch):
        msg = build_message("0200", MOCK_FINANCIAL_REQUEST["fields"])
        response = switch.process(msg.pack())
        resp = ISO8583Message.unpack(response)
        assert resp.mti == "0210"


# ── Test: to_dict Serialization ────────────────────────────────────────────

class TestSerialization:
    def test_to_dict_structure(self):
        msg = build_message("0100", MOCK_AUTH_REQUEST["fields"])
        d = msg.to_dict()

        assert d["mti"] == "0100"
        assert "fields" in d
        assert 2 in d["fields"]
        assert d["fields"][2]["name"] == "Primary Account Number (PAN)"

    def test_to_dict_field_count(self):
        msg = build_message("0100", MOCK_AUTH_REQUEST["fields"])
        d = msg.to_dict()
        assert len(d["fields"]) == len(MOCK_AUTH_REQUEST["fields"])
