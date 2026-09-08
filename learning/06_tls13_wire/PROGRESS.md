# Skill 7: TLS 1.3 at Wire — PROGRESS.md

**Status:** ⚠️ PARTIAL — wire analyzer built, demo ran
**Started:** 2026-09-02

## What was built
- `tls13_wire_analyzer.py` — TLS 1.3 ClientHello parser with downgrade detection

## Evidence
```
Parsed 52 bytes, found 1 findings
  → [INFO] server_downgrade_signal (offset 35): Server signaled TLS downgrade capability
```

## What it detects
- ClientHello extensions byte-by-byte parsing
- Downgrade attacks (version fallback to 1.2/1.1/1.0)
- Cipher suite mismatches
- Session resumption without proper PSK

## Next steps
- Connect to real TLS 1.3 endpoint (port 443)
- Add full handshake parser
- Add MitM-aware analysis mode
