#!/usr/bin/env python3
"""
race_condition_tester.py — Race Condition Testing Tool v1.0.0
===============================================================
Tests API endpoints for race condition vulnerabilities by sending
concurrent requests with identical payloads and analyzing timing
and response variations.

Covers:
  - TOCTOU (Time-of-Check-Time-of-Use) testing
  - Double-spend / balance manipulation
  - Coupon/ discount code reuse
  - Concurrent order placement
  - Inventory depletion races
  - Rate limit bypass via concurrent requests
  - Transaction idempotency testing

For AUTHORIZED PENETRATION TESTING against owned targets only.

Usage: python race_condition_tester.py --target https://api.example.com
       --endpoint /api/orders --concurrency 10 --requests 100
"""

import argparse
import asyncio
import json
import logging
import os
import random
import signal
import sys
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, List, Dict, Tuple
from urllib.parse import urljoin

try:
    import aiohttp
except ImportError:
    aiohttp = None

logger = logging.getLogger("race_condition_tester")
VERSION = "1.0.0"
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class RaceFinding:
    """A race condition finding."""
    id: str
    severity: Severity
    category: str
    title: str
    description: str
    target: str = ""
    endpoint: str = ""
    concurrency: int = 0
    requests_sent: int = 0
    success_count: int = 0
    failure_count: int = 0
    timing_stats: dict = field(default_factory=dict)
    evidence: str = ""
    recommendation: str = ""


@dataclass
class RaceTestConfig:
    """Configuration for a race condition test."""
    target: str
    endpoint: str
    method: str = "POST"
    headers: dict = field(default_factory=dict)
    body: dict = field(default_factory=dict)
    concurrency: int = 10
    requests_per_test: int = 50
    auth_token: str = ""
    payload_type: str = "default"
    max_concurrent_tests: int = 3


# --- Utility functions ---

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT)

def fuzz_id(prefix: str = "R") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"

def truncate(s: str, max_len: int = 500) -> str:
    if len(s) <= max_len:
        return s
    half = max_len // 2
    return s[:half] + "\n...[truncated]...\n" + s[-half:]


# --- Race Condition Test Types ---

class RaceTestType(Enum):
    DOUBLE_SPEND = "double_spend"
    COUPON_REUSE = "coupon_reuse"
    INVENTORY_RACE = "inventory_race"
    ORDER_DUPLICATION = "order_duplication"
    BALANCE_MANIPULATION = "balance_manipulation"
    RATE_LIMIT_BYPASS = "rate_limit_bypass"
    TOCTOU = "toctou"
    IDEMPOTENCY = "idempotency"
    CUSTOM = "custom"


# --- Default test scenarios ---

DEFAULT_SCENARIOS = [
    {
        "name": "Double Spend Test",
        "type": RaceTestType.DOUBLE_SPEND,
        "endpoint": "/api/payments",
        "method": "POST",
        "description": "Send identical payment requests concurrently to test if the server processes both",
        "body": {"amount": 100, "currency": "USD", "account_id": "test_acct"},
        "success_indicators": ["200", "201", "completed", "success"],
        "failure_indicators": ["409", "422", "already used", "insufficient"],
        "severity_if_vulnerable": Severity.CRITICAL,
    },
    {
        "name": "Coupon Code Reuse",
        "type": RaceTestType.COUPON_REUSE,
        "endpoint": "/api/coupons/apply",
        "method": "POST",
        "description": "Apply the same coupon code concurrently from multiple requests",
        "body": {"coupon_code": "TEST2024", "order_total": 500},
        "success_indicators": ["200", "201", "applied", "discount"],
        "failure_indicators": ["409", "422", "already used", "expired"],
        "severity_if_vulnerable": Severity.HIGH,
    },
    {
        "name": "Inventory Depletion Race",
        "type": RaceTestType.INVENTORY_RACE,
        "endpoint": "/api/cart/add",
        "method": "POST",
        "description": "Add the last item to cart concurrently to test if both requests succeed",
        "body": {"product_id": "LAST_ITEM", "quantity": 1},
        "success_indicators": ["200", "201", "added", "in cart"],
        "failure_indicators": ["409", "422", "out of stock", "unavailable"],
        "severity_if_vulnerable": Severity.HIGH,
    },
    {
        "name": "Order Duplication",
        "type": RaceTestType.ORDER_DUPLICATION,
        "endpoint": "/api/orders",
        "method": "POST",
        "description": "Place the same order concurrently to check for duplicate processing",
        "body": {"items": [{"product_id": "TEST1", "quantity": 1}], "shipping_address": "123 Test St"},
        "success_indicators": ["200", "201", "order created", "order_id"],
        "failure_indicators": ["409", "422", "duplicate", "already exists"],
        "severity_if_vulnerable": Severity.CRITICAL,
    },
    {
        "name": "Balance Manipulation",
        "type": RaceTestType.BALANCE_MANIPULATION,
        "endpoint": "/api/wallet/transfer",
        "method": "POST",
        "description": "Transfer funds concurrently to test for balance race conditions",
        "body": {"from_account": "A", "to_account": "B", "amount": 1000},
        "success_indicators": ["200", "201", "transferred", "success"],
        "failure_indicators": ["409", "422", "insufficient", " overdraft"],
        "severity_if_vulnerable": Severity.CRITICAL,
    },
    {
        "name": "Rate Limit Bypass",
        "type": RaceTestType.RATE_LIMIT_BYPASS,
        "endpoint": "/api/limited-endpoint",
        "method": "POST",
        "description": "Send requests at maximum concurrency to test if rate limiting is bypassed",
        "body": {"data": "test"},
        "success_indicators": ["200"],
        "failure_indicators": ["429", "rate limit", "too many"],
        "severity_if_vulnerable": Severity.MEDIUM,
    },
    {
        "name": "TOCTOU Vulnerability Test",
        "type": RaceTestType.TOCTOU,
        "endpoint": "/api/resource/validate",
        "method": "POST",
        "description": "Test time-of-check-time-of-use by modifying resource state between check and use",
        "body": {"resource_id": "TEST_RES", "action": "use"},
        "success_indicators": ["200", "201"],
        "failure_indicators": ["409", "422", "stale", "modified"],
        "severity_if_vulnerable": Severity.HIGH,
    },
    {
        "name": "Idempotency Test",
        "type": RaceTestType.IDEMPOTENCY,
        "endpoint": "/api/transactions",
        "method": "POST",
        "description": "Send identical transaction requests to verify idempotent behavior",
        "body": {"transaction_id": " idempotent_test_001", "amount": 50},
        "success_indicators": ["200", "201"],
        "failure_indicators": [],  # Idempotent = always returns same result
        "severity_if_vulnerable": Severity.MEDIUM,
    },
]


# --- Result types ---

@dataclass
class RequestResult:
    """Result of a single request in a race test."""
    request_id: str
    timestamp: str
    status_code: int
    response_time_ms: float
    success: bool
    response_body: str = ""
    error: str = ""


@dataclass
class RaceTestResult:
    """Aggregated result of a race condition test."""
    scenario_name: str
    test_type: RaceTestType
    concurrency: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_requests: int
    min_response_time: float
    max_response_time: float
    avg_response_time: float
    median_response_time: float
    findings: List[RaceFinding] = field(default_factory=list)
    raw_results: List[RequestResult] = field(default_factory=list)
    vulnerable: bool = False
    details: str = ""


# --- Concurrent Request Handler ---

class ConcurrentRequestHandler:
    """Handles sending concurrent requests for race condition testing."""

    def __init__(self, config: RaceTestConfig):
        self.config = config
        self.results: List[RequestResult] = []
        self.semaphore: Optional[asyncio.Semaphore] = None
        self.session: Optional[aiohttp.ClientSession] = None

    async def setup(self):
        """Set up the HTTP session and semaphore."""
        if aiohttp is None:
            raise RuntimeError("aiohttp is required for concurrent testing")
        timeout = aiohttp.ClientTimeout(total=30)
        headers = dict(self.config.headers)
        if self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers=headers,
            raise_for_status=False,
        )
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent_tests)

    async def teardown(self):
        """Clean up the HTTP session."""
        if self.session:
            await self.session.close()

    async def send_request(self, request_id: str, body: dict) -> RequestResult:
        """Send a single request and record the result."""
        result = RequestResult(
            request_id=request_id,
            timestamp=now_iso(),
            status_code=0,
            response_time_ms=0.0,
            success=False,
        )
        try:
            async with self.semaphore:
                url = urljoin(self.config.target, self.config.endpoint)
                start = time.perf_counter()
                if self.config.method.upper() == "GET":
                    async with self.session.get(url) as resp:
                        elapsed = (time.perf_counter() - start) * 1000
                        result.status_code = resp.status
                        result.response_time_ms = elapsed
                        result.response_body = await resp.text()
                        result.success = resp.status in (200, 201)
                else:
                    payload = json.dumps(body).encode("utf-8")
                    async with self.session.post(
                        url, data=payload,
                        headers={"Content-Type": "application/json"}
                    ) as resp:
                        elapsed = (time.perf_counter() - start) * 1000
                        result.status_code = resp.status
                        result.response_time_ms = elapsed
                        result.response_body = await resp.text()
                        result.success = resp.status in (200, 201)
        except asyncio.TimeoutError:
            result.error = "Request timed out"
        except aiohttp.ClientError as e:
            result.error = f"Client error: {e}"
        except Exception as e:
            result.error = f"Unexpected error: {e}"
        return result

    async def run_test(self, scenario: dict) -> RaceTestResult:
        """Run a complete race condition test for a scenario."""
        test_type = scenario.get("type", RaceTestType.CUSTOM)
        if isinstance(test_type, str):
            test_type = RaceTestType(test_type)

        concurrency = self.config.concurrency
        total_requests = self.config.requests_per_test
        body_template = scenario.get("body", {})

        self.results = []

        # Create varied bodies for each request
        bodies = []
        for i in range(total_requests):
            body = dict(body_template)
            # Add uniqueness where appropriate
            if "id" in body or "transaction_id" in body:
                body["id"] = body.get("id", f"race_test_{i}")
            bodies.append(body)

        # Launch concurrent requests
        logger.info(
            f"Running race test: {scenario['name']} "
            f"with {concurrency} concurrent workers, {total_requests} total requests"
        )

        start_time = time.perf_counter()
        tasks = []
        for i in range(total_requests):
            request_id = fuzz_id(f"R{i:04d}")
            task = asyncio.create_task(self.send_request(request_id, bodies[i]))
            tasks.append(task)

        # Wait for all requests to complete
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        total_time = (time.perf_counter() - start_time) * 1000

        # Process results
        request_results = []
        for i, r in enumerate(raw_results):
            if isinstance(r, Exception):
                req_result = RequestResult(
                    request_id=fuzz_id(f"R{i:04d}"),
                    timestamp=now_iso(),
                    status_code=0,
                    response_time_ms=0.0,
                    success=False,
                    error=str(r),
                )
            else:
                req_result = r
            request_results.append(req_result)

        self.results = request_results

        # Calculate statistics
        response_times = [r.response_time_ms for r in request_results if r.response_time_ms > 0]
        successful = [r for r in request_results if r.success]
        failed = [r for r in request_results if not r.success and not r.error]
        errors = [r for r in request_results if r.error]

        # Determine if vulnerable
        success_rate = len(successful) / max(len(request_results), 1)
        vulnerable = success_rate > 0.5 and len(successful) > 1

        # Generate timing stats
        timing_stats = {
            "total_test_time_ms": total_time,
            "min_response_time_ms": min(response_times) if response_times else 0,
            "max_response_time_ms": max(response_times) if response_times else 0,
            "avg_response_time_ms": sum(response_times) / len(response_times) if response_times else 0,
            "median_response_time_ms": sorted(response_times)[len(response_times) // 2] if response_times else 0,
            "p95_response_time_ms": sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0,
        }

        result = RaceTestResult(
            scenario_name=scenario["name"],
            test_type=test_type,
            concurrency=concurrency,
            total_requests=total_requests,
            successful_requests=len(successful),
            failed_requests=len(failed),
            error_requests=len(errors),
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            avg_response_time=sum(response_times) / len(response_times) if response_times else 0,
            median_response_time=sorted(response_times)[len(response_times) // 2] if response_times else 0,
            raw_results=request_results,
            vulnerable=vulnerable,
            timing_stats=timing_stats,
            details=f"Success rate: {success_rate:.1%} ({len(successful)}/{len(request_results)})",
        )

        # Generate findings if vulnerable
        if vulnerable:
            severity = scenario.get("severity_if_vulnerable", Severity.HIGH)
            if isinstance(severity, str):
                severity = Severity(severity)

            finding = RaceFinding(
                id=fuzz_id("RC"),
                severity=severity,
                category=f"Race Condition - {test_type.value}",
                title=f"{scenario['name']} — Race condition detected",
                description=(
                    f"Sent {total_requests} concurrent requests with {concurrency} workers. "
                    f"{len(successful)} requests succeeded ({success_rate:.1%} success rate), "
                    f"indicating the server processed multiple identical/similar operations. "
                    f"Average response time: {timing_stats['avg_response_time_ms']:.1f}ms. "
                    f"Min: {timing_stats['min_response_time_ms']:.1f}ms, "
                    f"Max: {timing_stats['max_response_time_ms']:.1f}ms."
                ),
                target=self.config.target,
                endpoint=self.config.endpoint,
                concurrency=concurrency,
                requests_sent=total_requests,
                success_count=len(successful),
                failure_count=len(failed),
                timing_stats=timing_stats,
                evidence=(
                    f"Concurrent requests succeeded: {len(successful)} of {total_requests}. "
                    f"Response time spread: {timing_stats['min_response_time_ms']:.0f}ms - "
                    f"{timing_stats['max_response_time_ms']:.0f}ms."
                ),
                recommendation=(
                    "Implement proper locking or atomic operations for this endpoint. "
                    "Use database transactions with appropriate isolation levels. "
                    "Add idempotency keys to prevent duplicate processing. "
                    "Consider using optimistic locking with version numbers."
                ),
            )
            result.findings.append(finding)

        return result


# --- Race Condition Tester ---

class RaceConditionTester:
    """Main race condition testing orchestrator."""

    def __init__(self, config: RaceTestConfig):
        self.config = config
        self.handler = ConcurrentRequestHandler(config)
        self.all_results: List[RaceTestResult] = []
        self.all_findings: List[RaceFinding] = []

    async def run_scenario(self, scenario: dict) -> RaceTestResult:
        """Run a single scenario and return results."""
        result = await self.handler.run_test(scenario)
        self.all_results.append(result)
        self.all_findings.extend(result.findings)
        return result

    async def run_all_scenarios(self, scenarios: List[dict]) -> List[RaceTestResult]:
        """Run all scenarios sequentially."""
        for scenario in scenarios:
            logger.info(f"Starting scenario: {scenario['name']}")
            result = await self.run_scenario(scenario)
            self._print_summary(result)
            logger.info(f"Completed scenario: {scenario['name']}")
        return self.all_results

    def _print_summary(self, result: RaceTestResult):
        """Print a formatted summary of test results."""
        print(f"\n{'='*60}")
        print(f"RACE CONDITION TEST RESULT")
        print(f"{'='*60}")
        print(f"Scenario: {result.scenario_name}")
        print(f"Type: {result.test_type.value}")
        print(f"Concurrency: {result.concurrency}")
        print(f"Total Requests: {result.total_requests}")
        print(f"Successful: {result.successful_requests}")
        print(f"Failed: {result.failed_requests}")
        print(f"Errors: {result.error_requests}")
        print(f"Vulnerable: {'YES' if result.vulnerable else 'NO'}")
        print(f"\nTiming Statistics:")
        for key, value in result.timing_stats.items():
            print(f"  {key}: {value:.2f}ms")
        if result.findings:
            print(f"\nFINDINGS:")
            for finding in result.findings:
                print(f"  [{finding.severity.value.upper()}] {finding.title}")
                print(f"    {finding.description}")
        print(f"{'='*60}\n")


# --- CLI ---

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Race Condition Testing Tool — test API endpoints for race vulnerabilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python race_condition_tester.py --target https://api.example.com
      --endpoint /api/payments --concurrency 20 --requests 100

  python race_condition_tester.py --target https://api.example.com
      --scenario coupon_reuse --concurrency 15
        """,
    )
    parser.add_argument("--target", required=True, help="Base URL of the target API")
    parser.add_argument("--endpoint", help="Specific endpoint to test (overrides scenarios)")
    parser.add_argument("--method", default="POST", help="HTTP method (default: POST)")
    parser.add_argument("--concurrency", type=int, default=10, help="Number of concurrent workers")
    parser.add_argument("--requests", type=int, default=50, help="Total requests per test")
    parser.add_argument("--auth-token", help="Bearer token for authenticated endpoints")
    parser.add_argument("--scenario", help="Run a specific scenario by name")
    parser.add_argument("--body", type=json.loads, help="JSON body to send (for custom tests)")
    parser.add_argument("--max-concurrent-tests", type=int, default=3, help="Max simultaneous test batches")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--output", help="Output file for JSON results")
    return parser


async def async_main(args: argparse.Namespace):
    """Async entry point."""
    config = RaceTestConfig(
        target=args.target.rstrip("/"),
        endpoint=args.endpoint or "/api/payments",
        method=args.method,
        concurrency=args.concurrency,
        requests_per_test=args.requests,
        auth_token=args.auth_token or "",
        max_concurrent_tests=args.max_concurrent_tests,
        body=args.body or {},
    )

    tester = RaceConditionTester(config)

    if args.scenario:
        # Run a single named scenario
        scenario = next(
            (s for s in DEFAULT_SCENARIOS if s["name"].lower() == args.scenario.lower()),
            None,
        )
        if scenario:
            logger.info(f"Running scenario: {scenario['name']}")
            result = await tester.run_scenario(scenario)
            tester._print_summary(result)
        else:
            print(f"Unknown scenario: {args.scenario}")
            print(f"Available: {', '.join(s['name'] for s in DEFAULT_SCENARIOS)}")
            sys.exit(1)
    else:
        # Run all default scenarios
        logger.info(f"Running all {len(DEFAULT_SCENARIOS)} default scenarios")
        await tester.run_all_scenarios(DEFAULT_SCENARIOS)

    # Output results
    if args.output:
        output = {
            "version": VERSION,
            "timestamp": now_iso(),
            "target": args.target,
            "results": [
                {
                    "scenario": r.scenario_name,
                    "type": r.test_type.value,
                    "vulnerable": r.vulnerable,
                    "successful": r.successful_requests,
                    "failed": r.failed_requests,
                    "errors": r.error_requests,
                    "total": r.total_requests,
                    "timing": r.timing_stats,
                    "findings": [f.__dict__ for f in r.findings],
                }
                for r in tester.all_results
            ],
            "total_findings": len(tester.all_findings),
            "total_vulnerable": sum(1 for r in tester.all_results if r.vulnerable),
        }
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2, default=str)
        print(f"Results written to {args.output}")

    # Print final summary
    print(f"\n{'='*60}")
    print("RACE CONDITION TEST — FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"Target: {args.target}")
    print(f"Scenarios tested: {len(tester.all_results)}")
    print(f"Vulnerable endpoints: {sum(1 for r in tester.all_results if r.vulnerable)}")
    print(f"Total findings: {len(tester.all_findings)}")
    critical = sum(1 for f in tester.all_findings if f.severity == Severity.CRITICAL)
    high = sum(1 for f in tester.all_findings if f.severity == Severity.HIGH)
    print(f"  Critical: {critical}")
    print(f"  High: {high}")
    print(f"{'='*60}\n")


def main():
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if aiohttp is None:
        print("ERROR: aiohttp is required. Install with: pip install aiohttp")
        sys.exit(1)

    try:
        asyncio.run(async_main(args))
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(130)


if __name__ == "__main__":
    main()
