# Skill 9: Windows Internals — PROGRESS.md

**Status:** ✅ CREATED
**Started:** 2026-09-04

## What was built
- `windows_etw_monitor.py` — ETW-based Windows event monitor with ransomware detection

## Capabilities
1. **ETW Session Management:** Start/stop real-time ETW sessions via ctypes
2. **Provider Subscription:** Process, File, Registry, Network providers
3. **Ransomware Detection:** Mass file rename + extension change pattern detection
4. **Time-Windowed Analysis:** Sliding window event tracking with configurable thresholds

## Usage
```bash
python windows_etw_monitor.py              # Live monitoring (requires admin)
python windows_etw_monitor.py --demo        # Demo mode with synthetic events
python windows_etw_monitor.py --log FILE    # Parse saved ETW log file
python windows_etw_monitor.py --threshold 50 --window 60
```

## ETW Providers Monitored
| Provider | GUID | Purpose |
|---|---|---|
| Kernel-Process | {22FB2CD6-...} | Process create/terminate |
| Kernel-File | {EDD08927-...} | File create/delete/rename |
| Kernel-Registry | {70EB4F03-...} | Registry set/delete |
| Kernel-Network | {7DD4240B-...} | Network connections |

## Ransomware Detection Logic
- Tracks file rename events in a sliding time window (default: 60s)
- If a single process renames > threshold files (default: 50), triggers CRITICAL alert
- Tracks extension changes (e.g., `.docx` → `.docx.encrypted`)

## Demo Output
```
[ALERT] RANSOMWARE DETECTED!
  Process ID: 9999
  File renames: 50 in 60s
  Extension changes: ['.jpg -> .locked']
```

## Requirements
- Windows OS (uses ctypes.windll.advapi32)
- Administrator privileges for live ETW session
- Python 3.8+
