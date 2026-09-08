# KERNEL ARCHITECTURE, RING 0 PRIVILEGE & DEFENSIVE HOOK DETECTION
**Author:** Bionic Daughter & Dad  
**Domain:** Windows & Linux Kernel Internals, EDR Telemetry, and Rootkit Defense

---

## 1. The Hierarchical Privilege Model (CPU Rings)

Operating systems enforce hardware-mediated security domains using CPU privilege levels:

```
┌────────────────────────────────────────────────────────┐
│ Ring 3: User Mode                                      │
│ - Applications, Browsers, CLI Agents, User Services    │
│ - Virtual memory isolated per process (CR3 register)   │
│ - Restricted instruction set (No direct I/O or CR*)    │
└──────────────────────────┬─────────────────────────────┘
                           │ System Call Interface (SYSCALL / SYSENTER)
┌──────────────────────────▼─────────────────────────────┐
│ Ring 0: Kernel Mode / Supervisor                       │
│ - OS Executive, Core Drivers, Memory Manager, HAL      │
│ - Unrestricted instruction execution and raw hardware  │
│ - Direct access to all physical memory pages           │
└──────────────────────────┬─────────────────────────────┘
                           │ Virtualization Extensions (VMCALL)
┌──────────────────────────▼─────────────────────────────┐
│ Ring -1: Hypervisor Layer (VT-x / AMD-V / Hyper-V)     │
│ - Virtual Machine Monitors, Virtualization-Based       │
│   Security (VBS), Hypervisor-Protected Code Integrity  │
└────────────────────────────────────────────────────────┘
```

---

## 2. Kernel Telemetry & Monitoring Primitives (Windows)

Modern defensive telemetry relies on official kernel callback mechanisms rather than unstable hooks:

| Mechanism | Purpose | Defensive / EDR Use Case |
|---|---|---|
| **`PsSetCreateProcessNotifyRoutineEx`** | Process creation callbacks | Intercepts every new process before execution, checking binary signatures, parent-child lineage, and command-line arguments. |
| **`PsSetCreateThreadNotifyRoutine`** | Thread creation callbacks | Detects remote thread injection (e.g., `CreateRemoteThread` cross-process execution). |
| **`ObRegisterCallbacks`** | Object pre/post access callbacks | Restricts handle creation/duplication against protected processes (e.g., preventing `PROCESS_VM_READ` or `PROCESS_ALL_ACCESS` on `lsass.exe`). |
| **`CmRegisterCallbackEx`** | Registry notification callbacks | Monitors persistent registry keys (`Run`, `RunOnce`, Services, Winlogon). |
| **ETW Ti (Threat Intelligence)** | Kernel event tracing | Provides telemetry for memory mapping, allocation permissions (`PAGE_EXECUTE_READWRITE`), and APC queuing. |

---

## 3. Defensive Hook Detection & Integrity Verification

### A. Kernel Patch Protection (PatchGuard / KPP)
* Windows x64 enforces PatchGuard to periodically verify the integrity of critical kernel structures:
  - System Service Descriptor Table (SSDT)
  - Interrupt Descriptor Table (IDT)
  - Global Descriptor Table (GDT)
  - Control Registers (`CR0`, `CR4`)
* Any unauthorized modification triggers a `CRITICAL_STRUCTURE_CORRUPTION` (BugCheck `0x109`) or `KERNEL_SECURITY_CHECK_FAILURE` (`0x139`).

### B. Inline User-Mode Hook Detection (EDR Bypass Detection)
EDRs often hook user-mode `ntdll.dll` syscall stubs (`NtProtectVirtualMemory`, `NtAllocateVirtualMemory`) to inspect parameters.
* **Detection Mechanism:**
  An integrity auditor compares in-memory `ntdll.dll` `.text` sections against the pristine on-disk PE file.
  If the first 4 bytes of a syscall stub deviate from `4C 8B D1 B8` (`mov r10, rcx; mov eax, <sys_num>`), an inline hook (e.g., `jmp <handler>`) is detected.
