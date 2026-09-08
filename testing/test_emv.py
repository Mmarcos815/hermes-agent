#!/usr/bin/env python3
"""
test_emv.py — Test EMV engine against known test card data.

Tests the BERTLVParser and NetworkTokenizationVault using mock EMV Field 55
payloads that mirror real-world contactless transaction data.

Run: pytest testing/test_emv.py -v
"""

import sys
import os
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from emv_tokenization_engine import BERTLVParser, NetworkTokenizationVault, EMV_TAGS


# ── Mock Data: Known EMV test vectors ───────────────────────────────────────

MOCK_FIELD_55_CONTACTLESS = (
    "9F26084B73A862803893C5"  # ARQC: 8 bytes
    "9F270180"                # CID: ARQC requested
    "9F100706010A03A00000"    # IAD: 7 bytes
    "9F370438A4B290"          # UN: 4 bytes
    "9F3602001F"              # ATC: 31
    "95050000000000"          # TVR: Clean
    "9A03260828"              # Date: 2026-08-28
    "9C0100"                  # Type: Goods/Services
    "9F0206000000015000"      # Amount: $150.00
    "5F2A020840"              # Currency: USD
    "82023800"                # AIP
)

MOCK_FIELD_55_CHIP = (
    "9F2608A1B2C3D4E5F60718"
    "9F270140"                # CID: TC (Transaction Certificate)
    "9F100706010A03A00000"
    "9F370412345678"
    "9F360200A5"              # ATC: 165
    "95050080000000"          # TVR: Offline data auth not performed
    "9A03270101"              # Date: 2027-01-01
    "9C0100"
    "9F0206000000050000"      # Amount: $500.00
    "5F2A020978"              # Currency: EUR
    "82025800"
)

MOCK_DPAN = "4800112233445566"
MOCK_CRYPTOGRAM = "4B73A862803893C5"
MOCK_FPAN = "4111111111111111"


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def vault():
    """Fresh NetworkTokenizationVault for each test."""
    return NetworkTokenizationVault()


# ── Test: EMV Tag Dictionary ──────────────────────────────────────────────

class TestEMVTagDictionary:
    def test_arqc_tag_defined(self):
        assert "9F26" in EMV_TAGS
        assert "Cryptogram" in EMV_TAGS["9F26"]

    def test_atc_tag_defined(self):
        assert "9F36" in EMV_TAGS

    def test_tvr_tag_defined(self):
        assert "95" in EMV_TAGS

    def test_all_tags_have_names(self):
        for tag, name in EMV_TAGS.items():
            assert len(tag) >= 2
            assert len(name) > 0


# ── Test: BER-TLV Parsing ─────────────────────────────────────────────────

class TestBERTLVParser:
    def test_parse_contactless_payload(self):
        parsed = BERTLVParser.parse(MOCK_FIELD_55_CONTACTLESS)

        assert "9F26" in parsed
        assert "9F27" in parsed
        assert "9F36" in parsed
        assert "95" in parsed

    def test_parse_chip_payload(self):
        parsed = BERTLVParser.parse(MOCK_FIELD_55_CHIP)

        assert len(parsed["9F26"]["value_hex"]) == 16  # 8 bytes ARQC
        assert parsed["9F02"]["value_hex"] == "000000050000"

    def test_arqc_value_extracted(self):
        parsed = BERTLVParser.parse(MOCK_FIELD_55_CONTACTLESS)
        assert parsed["9F26"]["value_hex"] == "4B73A862803893C5"
        assert parsed["9F26"]["length"] == 8

    def test_atc_value_extracted(self):
        parsed = BERTLVParser.parse(MOCK_FIELD_55_CONTACTLESS)
        assert parsed["9F36"]["value_hex"] == "001F"
        assert parsed["9F36"]["length"] == 2

    def test_amount_extracted(self):
        parsed = BERTLVParser.parse(MOCK_FIELD_55_CONTACTLESS)
        assert parsed["9F02"]["value_hex"] == "000000015000"

    def test_empty_payload(self):
        parsed = BERTLVParser.parse("")
        assert parsed == {}

    def test_tag_name_lookup(self):
        parsed = BERTLVParser.parse("9F26084B73A862803893C5")
        assert parsed["9F26"]["name"] == "Application Cryptogram (ARQC/TC/AAC)"


# ── Test: Network Tokenization Vault ───────────────────────────────────────

class TestNetworkTokenizationVault:
    def test_detokenize_valid_contactless(self, vault):
        result = vault.detokenize(MOCK_DPAN, MOCK_CRYPTOGRAM, "CONTACTLESS")

        assert result["authorized"] is True
        assert result["response_code"] == "00"
        assert result["fpan"] == MOCK_FPAN

    def test_detokenize_valid_in_app(self, vault):
        result = vault.detokenize(MOCK_DPAN, MOCK_CRYPTOGRAM, "IN_APP")

        assert result["authorized"] is True

    def test_detokenize_invalid_dpan(self, vault):
        result = vault.detokenize("0000000000000000", MOCK_CRYPTOGRAM)

        assert result["authorized"] is False
        assert result["response_code"] == "14"

    def test_detokenize_short_cryptogram(self, vault):
        result = vault.detokenize(MOCK_DPAN, "SHORT")

        assert result["authorized"] is False
        assert result["response_code"] == "82"

    def test_detokenize_wrong_channel(self, vault):
        result = vault.detokenize(MOCK_DPAN, MOCK_CRYPTOGRAM, "E_COMMERCE")

        assert result["authorized"] is False
        assert result["response_code"] == "57"

    def test_token_type_apple_pay(self, vault):
        result = vault.detokenize(MOCK_DPAN, MOCK_CRYPTOGRAM, "CONTACTLESS")

        assert result["token_type"] == "DEVICE_TOKEN_APPLE_PAY"


# ── Test: End-to-End Flow ─────────────────────────────────────────────────

class TestEndToEnd:
    def test_parse_then_detokenize(self, vault):
        parsed = BERTLVParser.parse(MOCK_FIELD_55_CONTACTLESS)
        cryptogram = parsed["9F26"]["value_hex"]
        result = vault.detokenize(MOCK_DPAN, cryptogram, "CONTACTLESS")

        assert result["authorized"] is True
        assert result["fpan"] == MOCK_FPAN

    def test_multiple_transactions_same_card(self, vault):
        for _ in range(5):
            parsed = BERTLVParser.parse(MOCK_FIELD_55_CONTACTLESS)
            result = vault.detokenize(MOCK_DPAN, parsed["9F26"]["value_hex"])
            assert result["authorized"] is True
