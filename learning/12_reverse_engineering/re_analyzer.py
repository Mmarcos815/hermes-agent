#!/usr/bin/env python3
"""
re_analyzer.py — Tier 5 Binary Analyzer
Performs static analysis on PE and ELF binaries:
  - Header inspection (architecture, subsystem, timestamps)
  - Section analysis (entropy, permissions, packing detection)
  - Import/export extraction with suspicious API flagging
  - String extraction (ASCII + Unicode)
  - Suspicion scoring

Usage:
    python re_analyzer.py <binary> [--strings] [--min-len N] [--json]

Requires: pefile, pyelftools (gracefully degrades if missing)
"""

import argparse
import json
import math
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Optional dependencies — degrade gracefully
# ---------------------------------------------------------------------------
try:
    import pefile
    HAS_PEFILE = True
except ImportError:
    HAS_PEFILE = False

try:
    from elftools.elf.elffile import ELFFile
    HAS_ELFTOOLS = True
except ImportError:
    HAS_ELFTOOLS = False

# ---------------------------------------------------------------------------
# Suspicious API databases
# ---------------------------------------------------------------------------
SUSPICIOUS_WIN32 = {
    "process_injection": [
        "CreateRemoteThread", "WriteProcessMemory", "VirtualAllocEx",
        "NtMapViewOfSection", "QueueUserAPC", "SetThreadContext",
        "NtQueueApcThread", "RtlCreateUserThread",
    ],
    "memory": [
        "VirtualAlloc", "VirtualProtect", "HeapCreate", "NtAllocateVirtualMemory",
        "NtProtectVirtualMemory",
    ],
    "execution": [
        "CreateProcess", "WinExec", "ShellExecute", "CreateThread",
        "CreateProcessInternal", "ShellExecuteEx",
    ],
    "persistence": [
        "RegSetValueEx", "RegCreateKeyEx", "CreateService", "OpenSCManager",
        "ChangeServiceConfig", "StartService",
    ],
    "network": [
        "WSAStartup", "connect", "send", "recv", "InternetOpen",
        "InternetOpenUrl", "URLDownloadToFile", "HttpOpenRequest",
        "HttpSendRequest", "socket", "bind", "listen",
    ],
    "evasion": [
        "IsDebuggerPresent", "CheckRemoteDebuggerPresent",
        "NtQueryInformationProcess", "NtSetInformationThread",
        "FindWindow", "OutputDebugString",
    ],
    "credential": [
        "LsaEnumerateLogonSessions", "SamConnect", "CryptUnprotectData",
        "CredEnumerate", "NtReadVirtualMemory",
    ],
    "anti_analysis": [
        "GetTickCount", "GetTickCount64", "QueryPerformanceCounter",
        "NtDelayExecution", "Sleep",
    ],
}

SUSPICIOUS_ELF = {
    "process": ["fork", "execve", "ptrace", "system", "popen", "clone"],
    "network": ["connect", "socket", "sendto", "recvfrom", "bind", "listen", "accept"],
    "file_ops": ["open", "write", "unlink", "rmdir", "chmod", "chown", "rename"],
    "privilege": ["setuid", "setgid", "setreuid", "setregid", "setresuid"],
    "injection": ["process_vm_writev", "process_vm_readv", "ptrace"],
}

PACKER_SECTION_NAMES = {"UPX0", "UPX1", "UPX2", ".aspack", ".petite",
                         ".adata", ".ndata", ".rsrc", "Themida", "vmp0", "vmp1",
                         "enigma1", "enigma2"}


def calculate_entropy(data: bytes) -> float:
    """Shannon entropy of a byte sequence (0.0–8.0)."""
    if not data:
        return 0.0
    counter = Counter(data)
    length = len(data)
    entropy = 0.0
    for count in counter.values():
        p = count / length
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def format_entropy(entropy: float) -> str:
    """Color-code entropy for terminal output."""
    if entropy >= 7.5:
        return f"\033[91m{entropy:.2f}\033[0m"  # Red
    elif entropy >= 6.5:
        return f"\033[93m{entropy:.2f}\033[0m"  # Yellow
    return f"{entropy:.2f}"


def extract_strings(data: bytes, min_len: int = 4) -> list[str]:
    """Extract printable ASCII strings from raw bytes."""
    strings = []
    current = []
    for byte in data:
        if 32 <= byte < 127:
            current.append(chr(byte))
        else:
            if len(current) >= min_len:
                strings.append("".join(current))
            current = []
    if len(current) >= min_len:
        strings.append("".join(current))
    return strings


def check_suspicious_imports(imports: list[str], platform: str) -> dict:
    """Match imports against suspicious API database."""
    if platform == "pe":
        suspicious_db = SUSPICIOUS_WIN32
    else:
        suspicious_db = SUSPICIOUS_ELF

    findings = {}
    for category, apis in suspicious_db.items():
        matches = [api for api in imports if api in apis]
        if matches:
            findings[category] = matches
    return findings


def calculate_suspicion_score(pe_info: dict = None, elf_info: dict = None,
                               suspicious_imports: dict = None) -> tuple[int, list[str]]:
    """Calculate suspicion score and return reasons."""
    score = 0
    reasons = []

    info = pe_info or elf_info
    if not info:
        return 0, []

    # Check for packed sections
    for section in info.get("sections", []):
        if section.get("entropy", 0) >= 7.5:
            score += 3
            reasons.append(f"High entropy in {section['name']}: {section['entropy']:.2f}")
            break

    # Check for packer section names
    for section in info.get("sections", []):
        if section.get("name", "").lower() in {n.lower() for n in PACKER_SECTION_NAMES}:
            score += 2
            reasons.append(f"Packer section detected: {section['name']}")
            break

    # Check suspicious imports
    if suspicious_imports:
        if "process_injection" in suspicious_imports:
            score += 3
            reasons.append(f"Process injection APIs: {suspicious_imports['process_injection']}")
        if "network" in suspicious_imports and ("process_injection" in suspicious_imports or "execution" in suspicious_imports):
            score += 4
            reasons.append("Network + injection/execution combo")
        elif "network" in suspicious_imports:
            score += 1
        if "evasion" in suspicious_imports:
            score += 2
            reasons.append(f"Anti-debug APIs: {suspicious_imports['evasion']}")
        if "credential" in suspicious_imports:
            score += 3
            reasons.append(f"Credential access APIs: {suspicious_imports['credential']}")
        if "persistence" in suspicious_imports:
            score += 2
            reasons.append(f"Persistence APIs: {suspicious_imports['persistence']}")

    # Check for very few imports (packer signature)
    if info and len(info.get("imports", [])) <= 2:
        score += 2
        reasons.append("Very few imports (possible packer)")

    return score, reasons


# ---------------------------------------------------------------------------
# PE Analysis
# ---------------------------------------------------------------------------
def analyze_pe(filepath: str) -> dict:
    """Analyze a PE file using pefile."""
    if not HAS_PEFILE:
        return {"error": "pefile not installed. Run: pip install pefile"}

    pe = pefile.PE(filepath)
    result = {
        "format": "PE",
        "machine": pefile.MACHINE_TYPE.get(pe.FILE_HEADER.Machine, f"0x{pe.FILE_HEADER.Machine:04x}"),
        "subsystem": pefile.SUBSYSTEM_TYPE.get(pe.OPTIONAL_HEADER.Subsystem, f"0x{pe.OPTIONAL_HEADER.Subsystem:04x}"),
        "timestamp": datetime.fromtimestamp(pe.FILE_HEADER.TimeDateStamp).isoformat() if pe.FILE_HEADER.TimeDateStamp > 0 else "invalid",
        "entry_point": f"0x{pe.OPTIONAL_HEADER.AddressOfEntryPoint:08x}",
        "image_base": f"0x{pe.OPTIONAL_HEADER.ImageBase:08x}",
        "sections": [],
        "imports": [],
        "exports": [],
        "suspicious_imports": {},
    }

    # Sections
    for section in pe.sections:
        name = section.Name.decode("utf-8", errors="replace").rstrip("\x00")
        entropy = calculate_entropy(section.get_data())
        result["sections"].append({
            "name": name,
            "virtual_size": section.Misc_VirtualSize,
            "raw_size": section.SizeOfRawData,
            "entropy": round(entropy, 2),
            "characteristics": f"0x{section.Characteristics:08x}",
        })

    # Imports
    if hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            dll_name = entry.dll.decode("utf-8", errors="replace")
            for imp in entry.imports:
                if imp.name:
                    func_name = imp.name.decode("utf-8", errors="replace")
                    result["imports"].append(f"{dll_name}!{func_name}")

    # Exports
    if hasattr(pe, "DIRECTORY_ENTRY_EXPORT"):
        for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
            if exp.name:
                result["exports"].append(exp.name.decode("utf-8", errors="replace"))

    # Check suspicious imports
    all_imports = [imp.split("!")[-1] for imp in result["imports"]]
    result["suspicious_imports"] = check_suspicious_imports(all_imports, "pe")

    pe.close()
    return result


# ---------------------------------------------------------------------------
# ELF Analysis
# ---------------------------------------------------------------------------
def analyze_elf(filepath: str) -> dict:
    """Analyze an ELF file using pyelftools."""
    if not HAS_ELFTOOLS:
        return {"error": "pyelftools not installed. Run: pip install pyelftools"}

    with open(filepath, "rb") as f:
        elf = ELFFile(f)
        result = {
            "format": "ELF",
            "class": "64-bit" if elf.elfclass == 64 else "32-bit",
            "os_abi": elf.e_ident.get("EI_OSABI", "unknown") if isinstance(elf.e_ident.get("EI_OSABI"), str) else str(elf.e_ident.get("EI_OSABI", "unknown")),
            "machine": elf.get_machine_arch(),
            "entry_point": f"0x{elf.header.e_entry:08x}",
            "sections": [],
            "imports": [],
            "exports": [],
            "suspicious_imports": {},
        }

        # Sections
        for section in elf.iter_sections():
            entropy = calculate_entropy(section.data())
            result["sections"].append({
                "name": section.name or "<null>",
                "type": section["sh_type"],
                "flags": f"0x{section['sh_flags']:x}",
                "size": section["sh_size"],
                "entropy": round(entropy, 2),
            })

        # Dynamic symbols (imports/exports)
        symtab = elf.get_section_by_name(".symtab")
        if symtab:
            for sym in symtab.iter_symbols():
                if sym["st_info"]["type"] == "STT_FUNC" and sym["st_shndx"] == "SHN_UNDEF":
                    result["imports"].append(sym.name)
                elif sym["st_info"]["type"] == "STT_FUNC" and sym["st_shndx"] != "SHN_UNDEF":
                    result["exports"].append(sym.name)

        # Check suspicious imports
        result["suspicious_imports"] = check_suspicious_imports(result["imports"], "elf")

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def detect_format(filepath: str) -> str:
    """Detect binary format from magic bytes."""
    with open(filepath, "rb") as f:
        magic = f.read(4)
    if magic[:2] == b"MZ":
        return "pe"
    if magic[:4] == b"\x7fELF":
        return "elf"
    return "unknown"


def main():
    parser = argparse.ArgumentParser(description="Tier 5 Binary Analyzer")
    parser.add_argument("binary", help="Path to binary file")
    parser.add_argument("--strings", action="store_true", help="Extract strings")
    parser.add_argument("--min-len", type=int, default=6, help="Minimum string length (default: 6)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    filepath = Path(args.binary)
    if not filepath.exists():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    # Detect format
    fmt = detect_format(str(filepath))
    if fmt == "unknown":
        print("Error: Unknown binary format (not PE or ELF)", file=sys.stderr)
        sys.exit(1)

    # Analyze
    if fmt == "pe":
        result = analyze_pe(str(filepath))
    else:
        result = analyze_elf(str(filepath))

    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    # Calculate suspicion score
    score, reasons = calculate_suspicion_score(
        pe_info=result if fmt == "pe" else None,
        elf_info=result if fmt == "elf" else None,
        suspicious_imports=result.get("suspicious_imports"),
    )
    result["suspicion_score"] = score
    result["suspicion_reasons"] = reasons

    # Extract strings if requested
    if args.strings:
        with open(filepath, "rb") as f:
            data = f.read()
        result["strings"] = extract_strings(data, args.min_len)

    # Output
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"  Tier 5 Binary Analysis Report")
        print(f"{'='*60}")
        print(f"  File: {filepath.name}")
        print(f"  Size: {filepath.stat().st_size:,} bytes")
        print(f"  Format: {result['format']}")
        print(f"  Architecture: {result.get('machine', result.get('class', 'unknown'))}")
        print(f"  Entry Point: {result['entry_point']}")

        print(f"\n--- Sections ({len(result['sections'])}) ---")
        for sec in result["sections"]:
            entropy_str = format_entropy(sec["entropy"])
            print(f"  {sec['name']:<16} size={sec.get('size', sec.get('raw_size', 0)):>8}  entropy={entropy_str}")

        print(f"\n--- Imports ({len(result['imports'])}) ---")
        for imp in result["imports"][:20]:
            print(f"  {imp}")
        if len(result["imports"]) > 20:
            print(f"  ... and {len(result['imports']) - 20} more")

        if result["exports"]:
            print(f"\n--- Exports ({len(result['exports'])}) ---")
            for exp in result["exports"][:10]:
                print(f"  {exp}")

        if result["suspicious_imports"]:
            print(f"\n--- Suspicious Imports ---")
            for category, apis in result["suspicious_imports"].items():
                print(f"  [{category}] {', '.join(apis)}")

        print(f"\n--- Suspicion Score: {score}/15 ---")
        for reason in reasons:
            print(f"  • {reason}")

        if args.strings and "strings" in result:
            print(f"\n--- Strings ({len(result['strings'])}) ---")
            for s in result["strings"][:30]:
                print(f"  {s}")
            if len(result["strings"]) > 30:
                print(f"  ... and {len(result['strings']) - 30} more")

        print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
