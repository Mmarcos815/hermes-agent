"""Analyze crashes for exploitability classification."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Optional


class CrashType(Enum):
    STACK_BUFFER_OVERFLOW = "stack_buffer_overflow"
    HEAP_BUFFER_OVERFLOW = "heap_buffer_overflow"
    USE_AFTER_FREE = "use_after_free"
    DOUBLE_FREE = "double_free"
    OUT_OF_BOUNDS_READ = "oob_read"
    OUT_OF_BOUNDS_WRITE = "oob_write"
    INTEGER_OVERFLOW = "integer_overflow"
    NULL_DEREFERENCE = "null_dereference"
    DENIAL_OF_SERVICE = "denial_of_service"
    UNKNOWN = "unknown"


class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


@dataclass
class CrashReport:
    crash_type: CrashType = CrashType.UNKNOWN
    severity: Severity = Severity.NONE
    crashing_input: bytes = b""
    signal: str = ""
    fault_address: str = ""
    stack_trace: list[str] = field(default_factory=list)
    registers: dict[str, str] = field(default_factory=dict)
    exploitable: bool = False
    notes: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return f"[{self.severity.value}] {self.crash_type.value} signal={self.signal}"


class CrashAnalyzer:
    PATTERNS = {
        CrashType.STACK_BUFFER_OVERFLOW: [r"stack_buffer_overrun", r"stack smashing"],
        CrashType.HEAP_BUFFER_OVERFLOW: [r"heap_buffer_overflow", r"corrupted size"],
        CrashType.USE_AFTER_FREE: [r"use.after.free", r"heap-use-after-free"],
        CrashType.DOUBLE_FREE: [r"double.free"],
        CrashType.OUT_OF_BOUNDS_READ: [r"out_of_bounds_read", r"heap-buffer-overflow.*READ"],
        CrashType.OUT_OF_BOUNDS_WRITE: [r"out_of_bounds_write", r"heap-buffer-overflow.*WRITE"],
        CrashType.INTEGER_OVERFLOW: [r"integer_overflow"],
        CrashType.NULL_DEREFERENCE: [r"null.*deref", r"SEGV on.*0x0"],
    }

    def analyze(self, result) -> CrashReport:
        report = CrashReport(
            crashing_input=getattr(result, "input", b""),
            signal=getattr(result, "signal", ""),
            stack_trace=getattr(result, "stack_trace", []),
            registers=getattr(result, "registers", {}),
            fault_address=getattr(result, "fault_address", ""),
        )
        self._classify(report)
        self._assess_severity(report)
        return report

    def _classify(self, report: CrashReport) -> None:
        trace_text = "\n".join(report.stack_trace).lower()
        if "sigsegv" in report.signal.lower() and "0x0" in report.fault_address:
            report.crash_type = CrashType.NULL_DEREFERENCE
            return
        for crash_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, trace_text):
                    report.crash_type = crash_type
                    return
        if "sigsegv" in report.signal.lower():
            report.crash_type = CrashType.OUT_OF_BOUNDS_READ

    def _assess_severity(self, report: CrashReport) -> None:
        CRITICAL = {CrashType.HEAP_BUFFER_OVERFLOW, CrashType.STACK_BUFFER_OVERFLOW,
                    CrashType.USE_AFTER_FREE, CrashType.OUT_OF_BOUNDS_WRITE}
        HIGH = {CrashType.INTEGER_OVERFLOW, CrashType.DOUBLE_FREE}
        if report.crash_type in CRITICAL:
            report.severity = Severity.CRITICAL
            report.exploitable = True
        elif report.crash_type in HIGH:
            report.severity = Severity.HIGH
            report.exploitable = True
        elif report.crash_type == CrashType.OUT_OF_BOUNDS_READ:
            report.severity = Severity.MEDIUM
        else:
            report.severity = Severity.LOW

        rip = report.registers.get("rip", report.registers.get("eip", ""))
        if rip and self._looks_controlled(rip):
            report.severity = Severity.CRITICAL
            report.exploitable = True
            report.notes.append(f"RIP controlled: {rip}")

    def _looks_controlled(self, addr: str) -> bool:
        try:
            val = int(addr, 16)
            return val in (0x41414141, 0xDEADBEEF, 0xCAFEBABE, 0x42424242)
        except ValueError:
            return False
