---
name: reverse-engineering-tier5
description: Tier 5 Reverse Engineering — practical binary analysis (PE/ELF), suspicious import detection, string extraction, and packing identification.
tags: [reverse-engineering, malware-analysis, binary-analysis, pe, elf, security]
version: 1.0.0
---

# Tier 5 — Reverse Engineering

## Introduction

This skill covers practical static analysis of compiled binaries — Windows PE (`.exe`, `.dll`) and Linux ELF executables. The goal is to triage unknown binaries quickly: extract metadata, identify suspicious capabilities through imported APIs, pull human-readable strings, and detect packing or obfuscation. No disassembler required; this is the first-pass reconnaissance that tells you whether to fire up Ghidra/IDA.

## When to Use

- Triage an unknown executable before running it
- Cuckoo/ANY.RUN-style pre-analysis (what does this binary *look* like it does?)
- CTF reverse-engineering challenges (beginner/intermediate)
- Malware sample first-pass (what APIs does it import? any interesting strings?)
- Auditing a build for unexpected dependencies or capabilities

## Prerequisites

- Python 3.10+
- `pefile` for PE analysis (`pip install pefile`)
- `pyelftools` for ELF analysis (`pip install pyelftools`)
- Basic understanding of what an import table is (the binary's "phone book" of external functions it calls)

## How to Run

```bash
# Basic analysis
python re_analyzer.py <binary>

# With string extraction
python re_analyzer.py <binary> --strings --min-len 6

# Full report (JSON)
python re_analyzer.py <binary> --json
```

## Procedure

### 1. Identify the Format

The first bytes of a binary tell you what you're dealing with:

| Magic bytes | Format |
|-------------|--------|
| `MZ` (0x4D 0x5A) | DOS header → PE (Windows) |
| `\x7fELF` | ELF (Linux/Unix) |
| `cafebabe` / `feedface` | Mach-O (macOS) |

`re_analyzer.py` auto-detects PE vs ELF and routes accordingly.

### 2. Inspect the Headers

**PE headers** reveal:
- Target architecture (x86 vs x64)
- Subsystem (GUI vs CLI)
- Compile timestamp (suspicious if future-dated or 1970-01-01)
- Section names and sizes

**ELF headers** reveal:
- ELF class (32-bit vs 64-bit)
- OS/ABI (Linux, FreeBSD, SysV)
- Entry point address
- Section headers and program headers

### 3. Analyze Sections

Sections are the binary's compartments. Look for:

| Section | Normal | Suspicious |
|---------|--------|------------|
| `.text` | Code | Entropy > 7.0 (likely encrypted/packed) |
| `.data` | Initialized data | RWX permissions (read+write+execute) |
| `.rsrc` | Icons, strings, manifests | Embedded PEs (resource-hiding) |
| `.reloc` | Relocation info | Missing in a DLL (can't rebaseline) |
| `UPX0`/`UPX1` | — | Packed with UPX |

**Entropy** measures randomness (0.0 = all same byte, 8.0 = perfectly random). Packed/encrypted sections typically hit 7.0–7.9.

### 4. Review Imports (Capability Analysis)

The import table is the single most valuable triage artifact — it tells you what the binary *can* do, even if it doesn't always do it.

**High-suspicion Windows APIs:**

| Category | APIs |
|----------|------|
| Process injection | `CreateRemoteThread`, `WriteProcessMemory`, `VirtualAllocEx`, `NtMapViewOfSection` |
| Memory allocation | `VirtualAlloc`, `VirtualProtect` (RWX), `HeapCreate` |
| Execution | `CreateProcess`, `WinExec`, `ShellExecute`, `CreateThread` |
| Persistence | `RegSetValueEx`, `CreateService`, `OpenSCManager` |
| Network | `WSAStartup`, `connect`, `send`, `InternetOpen`, `URLDownloadToFile` |
| Evasion | `IsDebuggerPresent`, `CheckRemoteDebuggerPresent`, `NtQueryInformationProcess` |
| Credential | `LsaEnumerateLogonSessions`, `SamConnect`, `CryptUnprotectData` |
| Anti-analysis | `GetTickCount`, `QueryPerformanceCounter` (timing checks) |

**High-suspicion Linux symbols:**

| Category | Symbols |
|----------|---------|
| Process | `fork`, `execve`, `ptrace` (anti-debug) |
| Network | `connect`, `socket`, `sendto` |
| File | `open`, `write`, `unlink` (deletion) |
| Privilege | `setuid`, `setgid`, `setreuid` |
| Injection | `process_vm_writev`, `ptrace` with `PTRACE_ATTACH` |

### 5. Extract Strings

Human-readable strings reveal:
- Hardcoded URLs, IPs, file paths
- Debug paths (developer usernames, internal hostnames)
- Error messages (reveals intended behavior)
- Crypto keys or config blobs

Use `--min-len 6` to filter noise. Look for:
- `http://` / `https://` — C2 indicators
- `\\.\` — device paths (rootkit behavior)
- `HKEY_` — registry persistence
- `-----BEGIN` — embedded certificates/keys

### 6. Detect Packing

Packer indicators:
- Section names like `UPX0`, `UPX1`, `.aspack`, `.petite`
- Very few imports (just `LoadLibrary` + `GetProcAddress` — the "two-import" packer signature)
- High entropy in `.text` section
- Entry point lands in a non-`.text` section
- Size mismatch: tiny file size but large virtual size

Common packers: UPX, ASPack, PECompact, Themida, VMProtect, Enigma.

### 7. Score and Triage

Assign a rough suspicion score:

| Signal | Points |
|--------|--------|
| Packed/encrypted sections | +3 |
| Process injection APIs | +3 |
| Network + injection combo | +4 |
| Anti-debug APIs | +2 |
| Hardcoded IPs/URLs | +2 |
| RWX memory sections | +2 |
| Suspicious timestamp | +1 |
| Known packer signature | +2 |

**Score interpretation:**
- 0–2: Likely benign
- 3–5: Worth deeper analysis
- 6–8: Suspicious — sandbox it
- 9+: Treat as malicious until proven otherwise

## Pitfalls

- **Imports lie (sort of).** A binary importing `CreateRemoteThread` isn't automatically malware — debuggers and security tools use these APIs too. Context matters: a network-connected binary with injection APIs is far more suspicious than a standalone utility with one.
- **Delay-loaded imports.** Some binaries use `LoadLibrary` + `GetProcAddress` to hide imports from the static import table. Check for these two APIs as a signal of dynamic resolution.
- **Packed binaries show few imports.** A packed binary may only import `LoadLibraryA` and `GetProcAddress` — everything else is resolved at runtime. This is itself a signal.
- **Entropy isn't definitive.** Some legit sections (e.g., `.rsrc` with PNGs) have high entropy. Correlate with other signals.
- **Timestamps can be faked.** Don't rely on compile time alone.
- **Don't run unknown binaries on your host.** Use a VM, sandbox, or dedicated analysis machine.

## Verification

After running `re_analyzer.py`, verify:
1. [ ] Format correctly identified (PE vs ELF)
2. [ ] No sections with entropy > 7.5 (or flagged for review)
3. [ ] Import list reviewed against suspicious API table
4. [ ] Strings scanned for URLs, IPs, registry keys
5. [ ] Suspicion score calculated and documented
6. [ ] If score ≥ 6, escalate to dynamic analysis (sandbox)
