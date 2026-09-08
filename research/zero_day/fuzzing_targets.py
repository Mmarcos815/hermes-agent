"""Define fuzzing targets: protocols, parsers, decoders."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Grammar:
    name: str
    magic: bytes = b""
    headers: list[str] = field(default_factory=list)
    length_field: str | None = None
    delimiter: bytes = b"\n"


@dataclass
class FuzzTarget:
    name: str
    grammar: Grammar
    harness: Callable[[bytes], object] | None = None
    timeout_s: float = 5.0


HTTP_GRAMMAR = Grammar("http_request", headers=["Host", "User-Agent"], delimiter=b"\r\n")
DNS_GRAMMAR = Grammar("dns_query", magic=b"\x12\x34", length_field="payload_length")
TLS_GRAMMAR = Grammar("tls_record", magic=b"\x16\x03\x01", length_field="record_length")
PNG_GRAMMAR = Grammar("png_image", magic=b"\x89PNG\r\n\x1a\n", headers=["IHDR", "IDAT"])
ZIP_GRAMMAR = Grammar("zip_archive", magic=b"PK\x03\x04", length_field="uncompressed_size")
JSON_GRAMMAR = Grammar("json_payload", delimiter=b"}")
XML_GRAMMAR = Grammar("xml_document", magic=b"<?xml", delimiter=b">")

PROTOCOL_TARGETS = [
    FuzzTarget("http_parser", HTTP_GRAMMAR),
    FuzzTarget("dns_resolver", DNS_GRAMMAR),
    FuzzTarget("tls_handshake", TLS_GRAMMAR),
]

FILE_TARGETS = [
    FuzzTarget("png_decoder", PNG_GRAMMAR),
    FuzzTarget("zip_extractor", ZIP_GRAMMAR),
    FuzzTarget("json_parser", JSON_GRAMMAR),
    FuzzTarget("xml_parser", XML_GRAMMAR),
]

ALL_TARGETS = PROTOCOL_TARGETS + FILE_TARGETS
