# Tier 5 — Reverse Engineering Progress

## Status: ✅ Complete

## Deliverables

| File | Status | Description |
|------|--------|-------------|
| `SKILL.md` | ✅ | Full skill documentation with frontmatter, procedures, and pitfalls |
| `re_analyzer.py` | ✅ | Python binary analyzer (~200 lines) for PE/ELF triage |
| `PROGRESS.md` | ✅ | This file — progress tracking |

## What Was Built

### re_analyzer.py Capabilities

1. **Format Detection** — Auto-detects PE (`MZ` magic) vs ELF (`\x7fELF` magic)
2. **PE Analysis** (via `pefile`):
   - Machine type, subsystem, compile timestamp
   - Section names, sizes, entropy
   - Full import table (DLL!Function format)
   - Export table
3. **ELF Analysis** (via `pyelftools`):
   - 32/64-bit, OS/ABI, machine architecture
   - Section headers with entropy
   - Symbol table (imports = SHN_UNDEF, exports = defined)
4. **Suspicious API Detection** — Matches imports against categorized threat APIs:
   - Process injection, memory allocation, execution, persistence, network, evasion, credential, anti-analysis
5. **String Extraction** — ASCII strings with configurable minimum length
6. **Packing Detection** — Entropy analysis + known packer section names (UPX, ASPack, Themida, VMProtect, Enigma)
7. **Suspicion Scoring** — 0–15 point scale with documented reasoning
8. **Output Modes** — Human-readable report or JSON

### SKILL.md Sections

- Introduction & When to Use
- Prerequisites
- How to Run (CLI examples)
- 7-step Procedure (format ID → headers → sections → imports → strings → packing → scoring)
- Pitfalls (imports lie, delay-loaded APIs, entropy isn't definitive, etc.)
- Verification checklist

## Usage Examples

```bash
# Basic analysis
python re_analyzer.py suspicious.exe

# With string extraction
python re_analyzer.py sample.dll --strings --min-len 8

# JSON output for automation
python re_analyzer.py /bin/ls --json

# Install dependencies
pip install pefile pyelftools
```

## Suspicion Score Interpretation

| Score | Meaning |
|-------|---------|
| 0–2 | Likely benign |
| 3–5 | Worth deeper analysis |
| 6–8 | Suspicious — sandbox it |
| 9+ | Treat as malicious until proven otherwise |

## Dependencies

- `pefile` — PE parsing (gracefully degrades if missing)
- `pyelftools` — ELF parsing (gracefully degrades if missing)

## Notes

- Script degrades gracefully: if `pefile`/`pyelftools` aren't installed, it reports the missing dependency rather than crashing
- Entropy is color-coded in terminal output (red ≥ 7.5, yellow ≥ 6.5)
- All suspicious API databases are easily extensible dictionaries at the top of the script
