"""
Fuzzing Engine - A multi-modal fuzzing framework.

Features:
1. Coverage-guided fuzzer (AFL-style)
2. Protocol fuzzer (TCP/UDP)
3. Web fuzzer (parameters, headers)
4. API fuzzer (REST, GraphQL)
5. Smart mutation strategies
"""

import random
import string
import struct
import socket
import time
import json
import hashlib
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse


# =============================================================================
# Mutation Strategies
# =============================================================================

class MutationType(Enum):
    BIT_FLIP = "bit_flip"
    BYTE_FLIP = "byte_flip"
    ARITHMETIC = "arithmetic"
    INTERESTING_VALUES = "interesting_values"
    SPLICE = "splice"
    INSERT = "insert"
    DELETE = "delete"
    OVERWRITE = "overwrite"


@dataclass
class MutationResult:
    data: bytes
    strategy: MutationType
    description: str


class Mutator:
    """Smart mutation engine with multiple strategies."""

    INTERESTING_8 = [-128, -1, 0, 1, 16, 32, 64, 100, 127]
    INTERESTING_16 = [-32768, -129, 128, 255, 256, 512, 1000, 1024, 4096, 32767]
    INTERESTING_32 = [-2147483648, -100663046, -32769, 32768, 65535, 65536, 100663045, 2147483647]

    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
        self.strategies = [
            self.bit_flip,
            self.byte_flip,
            self.arithmetic_mutate,
            self.interesting_values,
            self.insert_random,
            self.delete_random,
            self.overwrite_random,
        ]

    def mutate(self, data: bytes) -> MutationResult:
        """Apply a random mutation strategy."""
        strategy = self.rng.choice(self.strategies)
        return strategy(data)

    def bit_flip(self, data: bytes) -> MutationResult:
        if not data:
            return MutationResult(data, MutationType.BIT_FLIP, "empty")
        pos = self.rng.randint(0, len(data) - 1)
        bit = self.rng.randint(0, 7)
        mutated = bytearray(data)
        mutated[pos] ^= 1 << bit
        return MutationResult(bytes(mutated), MutationType.BIT_FLIP, f"bit_flip@{pos}.{bit}")

    def byte_flip(self, data: bytes) -> MutationResult:
        if not data:
            return MutationResult(data, MutationType.BYTE_FLIP, "empty")
        pos = self.rng.randint(0, len(data) - 1)
        mutated = bytearray(data)
        mutated[pos] ^= 0xFF
        return MutationResult(bytes(mutated), MutationType.BYTE_FLIP, f"byte_flip@{pos}")

    def arithmetic_mutate(self, data: bytes) -> MutationResult:
        if len(data) < 2:
            return MutationResult(data, MutationType.ARITHMETIC, "too_short")
        pos = self.rng.randint(0, len(data) - 2)
        delta = self.rng.randint(-35, 35)
        if delta == 0:
            delta = 1
        val = struct.unpack(">H", data[pos:pos + 2])[0]
        val = (val + delta) & 0xFFFF
        mutated = bytearray(data)
        mutated[pos:pos + 2] = struct.pack(">H", val)
        return MutationResult(bytes(mutated), MutationType.ARITHMETIC, f"arith@{pos}+{delta}")

    def interesting_values(self, data: bytes) -> MutationResult:
        if not data:
            return MutationResult(data, MutationType.INTERESTING_VALUES, "empty")
        pos = self.rng.randint(0, len(data) - 1)
        width = self.rng.choice([1, 2, 4])
        if pos + width > len(data):
            width = 1
        if width == 1:
            val = self.rng.choice(self.INTERESTING_8) & 0xFF
            replacement = bytes([val])
        elif width == 2:
            val = self.rng.choice(self.INTERESTING_16) & 0xFFFF
            replacement = struct.pack(">H", val)
        else:
            val = self.rng.choice(self.INTERESTING_32) & 0xFFFFFFFF
            replacement = struct.pack(">I", val)
        mutated = bytearray(data)
        mutated[pos:pos + width] = replacement
        return MutationResult(bytes(mutated), MutationType.INTERESTING_VALUES, f"interesting@{pos}w{width}")

    def insert_random(self, data: bytes) -> MutationResult:
        pos = self.rng.randint(0, len(data))
        length = self.rng.randint(1, 16)
        chunk = bytes(self.rng.randint(0, 255) for _ in range(length))
        mutated = data[:pos] + chunk + data[pos:]
        return MutationResult(mutated, MutationType.INSERT, f"insert@{pos}len{length}")

    def delete_random(self, data: bytes) -> MutationResult:
        if not data:
            return MutationResult(data, MutationType.DELETE, "empty")
        pos = self.rng.randint(0, len(data) - 1)
        length = self.rng.randint(1, min(16, len(data) - pos))
        mutated = data[:pos] + data[pos + length:]
        return MutationResult(mutated, MutationType.DELETE, f"delete@{pos}len{length}")

    def overwrite_random(self, data: bytes) -> MutationResult:
        if not data:
            return MutationResult(data, MutationType.OVERWRITE, "empty")
        pos = self.rng.randint(0, len(data) - 1)
        length = self.rng.randint(1, min(16, len(data) - pos))
        chunk = bytes(self.rng.randint(0, 255) for _ in range(length))
        mutated = bytearray(data)
        mutated[pos:pos + length] = chunk
        return MutationResult(bytes(mutated), MutationType.OVERWRITE, f"overwrite@{pos}len{length}")

    def splice(self, data: bytes, donor: bytes) -> MutationResult:
        """Crossover splice with a donor corpus entry."""
        if not data or not donor:
            return MutationResult(data, MutationType.SPLICE, "empty")
        split_data = self.rng.randint(0, len(data))
        split_donor = self.rng.randint(0, len(donor))
        mutated = data[:split_data] + donor[split_donor:]
        return MutationResult(mutated, MutationType.SPLICE, f"splice@{split_data}+{split_donor}")


# =============================================================================
# Coverage-Guided Fuzzer (AFL-style)
# =============================================================================

@dataclass
class FuzzStats:
    total_executions: int = 0
    unique_crashes: int = 0
    unique_paths: int = 0
    start_time: float = field(default_factory=time.time)

    @property
    def elapsed(self) -> float:
        return time.time() - self.start_time

    @property
    def execs_per_sec(self) -> float:
        return self.total_executions / max(self.elapsed, 0.001)


class CoverageMap:
    """AFL-style edge coverage map."""

    def __init__(self, size: int = 65536):
        self.size = size
        self.map = bytearray(size)
        self.paths = set()

    def update(self, edge_id: int, hit_count: int = 1):
        idx = edge_id % self.size
        if hit_count < 255:
            self.map[idx] = min(255, self.map[idx] + 1)
        else:
            self.map[idx] = 255
        self.paths.add(edge_id)

    def is_new_path(self, edge_id: int) -> bool:
        return edge_id not in self.paths

    def hash(self) -> str:
        return hashlib.md5(bytes(self.map)).hexdigest()


class CoverageGuidedFuzzer:
    """AFL-style coverage-guided fuzzer."""

    def __init__(
        self,
        target: Callable[[bytes], Any],
        seed_corpus: List[bytes],
        mutator: Optional[Mutator] = None,
        max_iterations: int = 10000,
    ):
        self.target = target
        self.corpus = list(seed_corpus)
        self.mutator = mutator or Mutator()
        self.max_iterations = max_iterations
        self.coverage = CoverageMap()
        self.crashes: List[Tuple[bytes, str]] = []
        self.stats = FuzzStats()
        self.queue: List[bytes] = list(seed_corpus)

    def run(self) -> FuzzStats:
        """Main fuzzing loop."""
        iteration = 0
        while iteration < self.max_iterations and self.queue:
            input_data = self.queue.pop(0)
            for _ in range(100):  # mutations per input
                if iteration >= self.max_iterations:
                    break
                mutated = self.mutator.mutate(input_data)
                self._execute(mutated.data)
                iteration += 1
        return self.stats

    def _execute(self, data: bytes):
        self.stats.total_executions += 1
        try:
            result = self.target(data)
            edge_id = hash(data) % 65536
            if self.coverage.is_new_path(edge_id):
                self.stats.unique_paths += 1
                self.corpus.append(data)
                self.queue.append(data)
            self.coverage.update(edge_id)
        except Exception as e:
            crash_hash = hashlib.md5(data).hexdigest()[:8]
            if crash_hash not in [hashlib.md5(c[0]).hexdigest()[:8] for c in self.crashes]:
                self.crashes.append((data, str(e)))
                self.stats.unique_crashes += 1


# =============================================================================
# Protocol Fuzzer (TCP/UDP)
# =============================================================================

class ProtocolFuzzer:
    """Fuzz TCP/UDP services."""

    def __init__(self, host: str, port: int, protocol: str = "tcp", timeout: float = 3.0):
        self.host = host
        self.port = port
        self.protocol = protocol.lower()
        self.timeout = timeout
        self.mutator = Mutator()
        self.crashes: List[Tuple[bytes, str]] = []

    def fuzz(self, base_payload: bytes, iterations: int = 100) -> List[Tuple[bytes, str]]:
        """Send mutated payloads to the target service."""
        for _ in range(iterations):
            mutated = self.mutator.mutate(base_payload)
            try:
                self._send(mutated.data)
            except Exception as e:
                self.crashes.append((mutated.data, str(e)))
        return self.crashes

    def _send(self, data: bytes):
        if self.protocol == "tcp":
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self.timeout)
        try:
            sock.connect((self.host, self.port))
            sock.sendall(data)
            sock.recv(4096)
        finally:
            sock.close()


# =============================================================================
# Web Fuzzer (Parameters, Headers)
# =============================================================================

class WebFuzzer:
    """Fuzz web endpoints via parameters and headers."""

    FUZZ_PAYLOADS = [
        "' OR '1'='1",
        "<script>alert(1)</script>",
        "../../../etc/passwd",
        "A" * 10000,
        "\x00",
        "${7*7}",
        "{{7*7}}",
        "$(whoami)",
        "true",
        "null",
        "-1",
        "99999999999999999999",
        "%00",
        "%0a",
        "😀",
        "🚀" * 100,
    ]

    def __init__(self, base_url: str, method: str = "GET"):
        self.base_url = base_url
        self.method = method.upper()
        self.findings: List[Dict[str, Any]] = []

    def fuzz_parameters(self, params: Dict[str, str]) -> List[Dict[str, Any]]:
        """Fuzz URL/query parameters with known attack payloads."""
        for param in params:
            for payload in self.FUZZ_PAYLOADS:
                fuzzed = dict(params)
                fuzzed[param] = payload
                result = self._test_params(fuzzed, param, payload)
                if result:
                    self.findings.append(result)
        return self.findings

    def fuzz_headers(self, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """Fuzz HTTP headers."""
        header_targets = ["User-Agent", "X-Forwarded-For", "Referer", "Cookie", "Authorization"]
        for header in header_targets:
            for payload in self.FUZZ_PAYLOADS:
                fuzzed = dict(headers)
                fuzzed[header] = payload
                result = self._test_headers(fuzzed, header, payload)
                if result:
                    self.findings.append(result)
        return self.findings

    def _test_params(self, params: Dict[str, str], param: str, payload: str) -> Optional[Dict]:
        """Test a parameter payload. Returns finding if anomalous."""
        parsed = urlparse(self.base_url)
        query = urlencode(params)
        url = urlunparse(parsed._replace(query=query))
        return {
            "type": "parameter",
            "url": url,
            "parameter": param,
            "payload": payload,
            "method": self.method,
        }

    def _test_headers(self, headers: Dict[str, str], header: str, payload: str) -> Optional[Dict]:
        """Test a header payload. Returns finding if anomalous."""
        return {
            "type": "header",
            "url": self.base_url,
            "header": header,
            "payload": payload,
            "method": self.method,
        }


# =============================================================================
# API Fuzzer (REST, GraphQL)
# =============================================================================

class APIFuzzer:
    """Fuzz REST and GraphQL APIs."""

    REST_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    GRAPHQL_INJECTIONS = [
        "{__schema{types{name}}}",
        "{__typename}",
        "query{__typename}",
        "mutation{__typename}",
    ]

    def __init__(self, base_url: str, api_type: str = "rest"):
        self.base_url = base_url.rstrip("/")
        self.api_type = api_type.lower()
        self.findings: List[Dict[str, Any]] = []
        self.mutator = Mutator()

    def fuzz_rest_endpoints(self, endpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fuzz REST API endpoints with type confusion and boundary values."""
        for endpoint in endpoints:
            path = endpoint.get("path", "/")
            method = endpoint.get("method", "GET").upper()
            params = endpoint.get("params", {})
            for param, ptype in params.items():
                for payload in self._generate_rest_payloads(ptype):
                    finding = {
                        "type": "rest",
                        "url": f"{self.base_url}{path}",
                        "method": method,
                        "parameter": param,
                        "expected_type": ptype,
                        "payload": payload,
                    }
                    self.findings.append(finding)
        return self.findings

    def fuzz_graphql(self, endpoint: str = "/graphql") -> List[Dict[str, Any]]:
        """Fuzz GraphQL endpoints with introspection and injection."""
        for injection in self.GRAPHQL_INJECTIONS:
            self.findings.append({
                "type": "graphql",
                "url": f"{self.base_url}{endpoint}",
                "method": "POST",
                "payload": json.dumps({"query": injection}),
                "description": "Introspection probe",
            })
        # Fuzz query depth
        for depth in [5, 10, 20, 50]:
            query = self._build_nested_query(depth)
            self.findings.append({
                "type": "graphql",
                "url": f"{self.base_url}{endpoint}",
                "method": "POST",
                "payload": json.dumps({"query": query}),
                "description": f"Deep nesting (depth={depth})",
            })
        return self.findings

    def _generate_rest_payloads(self, ptype: str) -> List[Any]:
        """Generate type-specific fuzz payloads."""
        if ptype == "string":
            return ["", "A" * 10000, "\x00", "<script>alert(1)</script>", "' OR 1=1"]
        elif ptype == "integer":
            return [-1, 0, 999999999, -999999999, 2147483648, "not_a_number"]
        elif ptype == "boolean":
            return [0, -1, "true", "yes", "maybe", None]
        elif ptype == "email":
            return ["not-an-email", "a@b.c" * 100, "test@test.com<script>"]
        elif ptype == "uuid":
            return ["not-a-uuid", "00000000-0000-0000-0000-000000000000"]
        else:
            return [None, "", 0, [], {}]

    def _build_nested_query(self, depth: int) -> str:
        """Build a deeply nested GraphQL query."""
        query = "query {"
        for i in range(depth):
            query += f" field{i} {{"
        query += "id"
        query += "}" * depth
        query += "}"
        return query


# =============================================================================
# Main Fuzzing Engine
# =============================================================================

class FuzzEngine:
    """Unified fuzzing engine combining all fuzzing modes."""

    def __init__(self, seed: Optional[int] = None):
        self.mutator = Mutator(seed)
        self.results: Dict[str, Any] = {}

    def coverage_guided(
        self,
        target: Callable[[bytes], Any],
        seeds: List[bytes],
        max_iter: int = 1000,
    ) -> FuzzStats:
        """Run AFL-style coverage-guided fuzzing."""
        fuzzer = CoverageGuidedFuzzer(target, seeds, self.mutator, max_iter)
        stats = fuzzer.run()
        self.results["coverage_guided"] = {
            "stats": stats,
            "crashes": fuzzer.crashes,
        }
        return stats

    def protocol(
        self,
        host: str,
        port: int,
        base_payload: bytes,
        protocol: str = "tcp",
        iterations: int = 100,
    ) -> List[Tuple[bytes, str]]:
        """Fuzz a TCP/UDP service."""
        fuzzer = ProtocolFuzzer(host, port, protocol)
        crashes = fuzzer.fuzz(base_payload, iterations)
        self.results["protocol"] = {"crashes": crashes}
        return crashes

    def web(
        self,
        url: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        method: str = "GET",
    ) -> List[Dict[str, Any]]:
        """Fuzz web parameters and headers."""
        fuzzer = WebFuzzer(url, method)
        if params:
            fuzzer.fuzz_parameters(params)
        if headers:
            fuzzer.fuzz_headers(headers)
        self.results["web"] = {"findings": fuzzer.findings}
        return fuzzer.findings

    def api(
        self,
        base_url: str,
        api_type: str = "rest",
        endpoints: Optional[List[Dict]] = None,
    ) -> List[Dict[str, Any]]:
        """Fuzz REST or GraphQL APIs."""
        fuzzer = APIFuzzer(base_url, api_type)
        if api_type == "rest" and endpoints:
            fuzzer.fuzz_rest_endpoints(endpoints)
        elif api_type == "graphql":
            fuzzer.fuzz_graphql()
        self.results["api"] = {"findings": fuzzer.findings}
        return fuzzer.findings

    def report(self) -> Dict[str, Any]:
        """Generate a summary report of all fuzzing results."""
        report = {"modes": {}}
        for mode, data in self.results.items():
            if mode == "coverage_guided":
                stats = data["stats"]
                report["modes"][mode] = {
                    "executions": stats.total_executions,
                    "unique_crashes": stats.unique_crashes,
                    "unique_paths": stats.unique_paths,
                    "execs_per_sec": round(stats.execs_per_sec, 2),
                }
            elif mode == "protocol":
                report["modes"][mode] = {"crashes_found": len(data["crashes"])}
            elif mode in ("web", "api"):
                report["modes"][mode] = {"findings": len(data["findings"])}
        return report


# =============================================================================
# CLI / Demo
# =============================================================================

if __name__ == "__main__":
    engine = FuzzEngine(seed=42)

    # Demo: Coverage-guided fuzzing
    def sample_target(data: bytes) -> bool:
        if len(data) > 0 and data[0] == 0x41 and len(data) > 1 and data[1] == 0x42:
            raise ValueError("Crash: magic bytes AB detected!")
        return True

    seeds = [b"hello", b"world", b"test"]
    stats = engine.coverage_guided(sample_target, seeds, max_iter=500)
    print(f"Coverage-guided: {stats.total_executions} execs, {stats.unique_crashes} crashes")

    # Demo: Web fuzzing
    findings = engine.web(
        "https://example.com/search",
        params={"q": "test", "page": "1"},
        headers={"User-Agent": "FuzzEngine/1.0"},
    )
    print(f"Web fuzzing: {len(findings)} findings")

    # Demo: API fuzzing
    api_findings = engine.api(
        "https://api.example.com",
        api_type="rest",
        endpoints=[
            {"path": "/users", "method": "GET", "params": {"id": "integer", "name": "string"}},
            {"path": "/login", "method": "POST", "params": {"email": "email", "password": "string"}},
        ],
    )
    print(f"API fuzzing: {len(api_findings)} findings")

    # Demo: GraphQL fuzzing
    gql_findings = engine.api("https://api.example.com", api_type="graphql")
    print(f"GraphQL fuzzing: {len(gql_findings)} findings")

    # Report
    print("\n=== Fuzzing Report ===")
    print(json.dumps(engine.report(), indent=2))
