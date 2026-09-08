"""Advanced mutation strategies for fuzzing inputs."""

from __future__ import annotations
import random
import struct
from typing import Iterator


class MutationEngine:
    INTERESTING_8 = [0, -128, 127]
    INTERESTING_16 = [0, -32768, 32767, -1, 1]
    INTERESTING_32 = [0, -2147483648, 2147483647, -1, 1]

    def __init__(self, seed_corpus: list[bytes] | None = None, rng_seed: int | None = None):
        self.corpus: list[bytes] = seed_corpus or []
        self.rng = random.Random(rng_seed)

    def add_seed(self, data: bytes) -> None:
        if data not in self.corpus:
            self.corpus.append(data)

    def generate(self, count: int = 100) -> Iterator[bytes]:
        for _ in range(count):
            if not self.corpus:
                yield b""
                continue
            seed = self.rng.choice(self.corpus)
            s = self.rng.randint(0, 7)
            match s:
                case 0: yield self._bit_flip(seed)
                case 1: yield self._byte_flip(seed)
                case 2: yield self._arithmetic(seed)
                case 3: yield self._interesting_values(seed)
                case 4: yield self._dictionary_insert(seed)
                case 5: yield self._splice(seed)
                case 6: yield self._insert_bytes(seed)
                case 7: yield self._erase_bytes(seed)

    def _bit_flip(self, data: bytes) -> bytes:
        if not data: return data
        pos = self.rng.randint(0, len(data) - 1)
        return data[:pos] + bytes([data[pos] ^ (1 << self.rng.randint(0, 7))]) + data[pos + 1:]

    def _byte_flip(self, data: bytes) -> bytes:
        if not data: return data
        pos = self.rng.randint(0, len(data) - 1)
        return data[:pos] + bytes([data[pos] ^ self.rng.randint(1, 255)]) + data[pos + 1:]

    def _arithmetic(self, data: bytes) -> bytes:
        if len(data) < 2: return data
        pos = self.rng.randint(0, len(data) - 2)
        delta = self.rng.randint(-35, 35)
        val = (struct.unpack("<H", data[pos:pos + 2])[0] + delta) & 0xFFFF
        return data[:pos] + struct.pack("<H", val) + data[pos + 2:]

    def _interesting_values(self, data: bytes) -> bytes:
        if not data: return data
        pos = self.rng.randint(0, len(data) - 1)
        val = self.rng.choice(self.INTERESTING_8 + self.INTERESTING_16 + self.INTERESTING_32)
        packed = struct.pack("<i", val) if abs(val) > 127 else struct.pack("<b", val)
        end = min(pos + len(packed), len(data))
        return data[:pos] + packed[:end - pos] + data[end:]

    def _dictionary_insert(self, data: bytes) -> bytes:
        token = self.rng.choice([b"\x00", b"\xff", b"\r\n", b"../", b"NULL", b"AAAA"])
        pos = self.rng.randint(0, len(data))
        return data[:pos] + token + data[pos:]

    def _splice(self, data: bytes) -> bytes:
        if len(self.corpus) < 2: return data
        other = self.rng.choice([s for s in self.corpus if s != data] or self.corpus)
        if not other: return data
        return data[:self.rng.randint(0, len(data))] + other[self.rng.randint(0, len(other)):]

    def _insert_bytes(self, data: bytes) -> bytes:
        count = self.rng.randint(1, 16)
        insert = bytes(self.rng.randint(0, 255) for _ in range(count))
        pos = self.rng.randint(0, len(data))
        return data[:pos] + insert + data[pos:]

    def _erase_bytes(self, data: bytes) -> bytes:
        if len(data) <= 1: return data
        count = self.rng.randint(1, max(1, len(data) // 4))
        pos = self.rng.randint(0, len(data) - count)
        return data[:pos] + data[pos + count:]
