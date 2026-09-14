#!/usr/bin/env python3
"""Analyze a recursive folder listing (from `dir /s` or `find`) and produce a structured summary.

Usage:
    python folder_analyzer.py <folder_listing.txt>

Output: prints a categorized summary to stdout. JSON report goes to stderr.
"""

import re
import sys
import json
from collections import defaultdict
from pathlib import Path


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

# Names that are known directories (even without trailing separator in listing).
_KNOWN_HIDDEN_DIRS = frozenset({
    ".git", ".github", ".venv", ".venv312", ".hermes", ".hermes-runtime",
    ".pytest_cache", ".deception", ".orca-preparing", ".bytecode-fingerprint",
    ".agents", ".claude", ".cursor", ".cache", ".bin",
    ".cargo-artifact-lock", ".cargo-build-lock", ".cargo-lock",
    ".claude-plugin", ".coveralls.yml", ".cti_state.json", ".DS_Store",
})

# Dot-names that are configuration FILES (not directories).
_DOT_CONFIG_FILES = frozenset({
    ".gitignore", ".dockerignore", ".prettierignore", ".prettierrc",
    ".mailmap", ".gitattributes", ".npmrc", ".nvmrc", ".python-version",
    ".envrc",
})

# Extensions that indicate config files.
_CONFIG_EXTENSIONS = frozenset({
    ".yaml", ".yml", ".json", ".toml", ".ini", ".cfg", ".conf", ".rc",
    ".hadolint.yaml", ".coderabbit.yaml",
})

# File-name-level config overrides (things without an extension that are config).
_CONFIG_BY_NAME = frozenset({
    ".env", ".env.example",
})


def _classify(line: str) -> tuple[str, str, str]:
    """Classify one listing line into (type, category, name).

    type: 'dir' | 'file' | 'unknown'
    category: one of the category strings below
    name: basename
    """
    stripped = line.strip()
    if not stripped:
        return ("unknown", "other", "")

    m = re.match(r"^[A-Za-z]:[/\\](.+)$", stripped)
    full_path = m.group(1) if m else stripped
    p = Path(full_path)
    name = p.name
    if not name:
        return ("unknown", "other", "")

    # Directory detection: trailing separator is the only reliable signal,
    # supplemented by a known-dirs set for common dot-dirs.
    is_dir = full_path.endswith("/") or full_path.endswith("\\")
    if name in _KNOWN_HIDDEN_DIRS:
        is_dir = True

    if is_dir:
        return ("dir", "dir", name)

    # Files: check categories in priority order so dot-config-files land in
    # "config" rather than falling through to "hidden".

    ext = p.suffix.lower()

    # --- config ---
    if ext in _CONFIG_EXTENSIONS or name in _DOT_CONFIG_FILES or name in _CONFIG_BY_NAME:
        return ("file", "config", name)

    # --- code ---
    _CODE_EXTENSIONS = frozenset({
        ".py", ".js", ".ts", ".tsx", ".jsx", ".rb", ".go", ".rs", ".java",
        ".c", ".cpp", ".h", ".hpp", ".cs", ".swift", ".kt", ".kts", ".scala",
        ".clj", ".ex", ".exs", ".lua", ".pl", ".pm", ".sh", ".bash", ".zsh",
        ".ps1", ".psm1", ".bat", ".cmd", ".sql", ".r", ".m", ".mm", ".dart",
        ".php", ".vb", ".asm", ".s", ".S",
    })
    if ext in _CODE_EXTENSIONS:
        return ("file", "code", name)

    # --- data ---
    _DATA_EXTENSIONS = frozenset({".json", ".xml", ".csv", ".tsv"})
    if ext in _DATA_EXTENSIONS:
        return ("file", "data", name)

    # --- doc ---
    _DOC_EXTENSIONS = frozenset({".md", ".txt", ".rst", ".tex", ".pdf",
                                  ".doc", ".docx", ".odt", ".html", ".htm"})
    if ext in _DOC_EXTENSIONS:
        return ("file", "doc", name)

    # --- image ---
    _IMG_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".gif", ".bmp",
                                 ".svg", ".ico", ".webp", ".tiff", ".tif"})
    if ext in _IMG_EXTENSIONS:
        return ("file", "image", name)

    # --- archive ---
    _ARCH_EXTENSIONS = frozenset({".zip", ".tar", ".gz", ".bz2", ".xz",
                                  ".7z", ".rar", ".tgz", ".tbz2", ".txz"})
    if ext in _ARCH_EXTENSIONS:
        return ("file", "archive", name)

    # --- binary ---
    _BIN_EXTENSIONS = frozenset({".exe", ".dll", ".so", ".dylib", ".bin",
                                 ".o", ".a", ".lib", ".obj", ".class", ".pyc", ".pyd"})
    if ext in _BIN_EXTENSIONS:
        return ("file", "binary", name)

    # --- media ---
    _MEDIA_EXTENSIONS = frozenset({".mp4", ".avi", ".mkv", ".mov", ".wmv",
                                   ".flv", ".webm", ".mp3", ".wav", ".flac",
                                   ".aac", ".ogg", ".m4a", ".wma"})
    if ext in _MEDIA_EXTENSIONS:
        return ("file", "media", name)

    # --- fallback ---
    # Dotfiles that didn't match any category above are "hidden".
    if name.startswith("."):
        return ("file", "hidden", name)

    return ("file", "other", name)


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def analyze_listing(path: str) -> dict:
    """Analyze a folder listing file and return structured results."""
    lines = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            s = line.strip()
            if s:
                lines.append(s)

    counts = defaultdict(int)
    dirs = set()
    files_by_category = defaultdict(list)
    hidden_dirs = set()
    hidden_files = set()
    top_level_dirs = []
    seen_files = set()

    for line in lines:
        typ, cat, name = _classify(line)
        counts[cat] += 1

        if typ == "dir":
            dirs.add(name)
            m = re.match(r"^[A-Za-z]:[/\\](.+)$", line.strip())
            if m and len(Path(m.group(1)).parts) == 1:
                top_level_dirs.append(name)
            if name.startswith("."):
                hidden_dirs.add(name)
        elif typ == "file":
            if name not in seen_files:
                files_by_category[cat].append(name)
                seen_files.add(name)
            if name.startswith("."):
                hidden_files.add(name)

    return {
        "file": path,
        "total_lines": len(lines),
        "total_dirs": len(dirs),
        "total_files": sum(1 for items in files_by_category.values() for _ in items),
        "categories": dict(counts),
        "files_by_category": {k: v for k, v in files_by_category.items()},
        "top_level_dirs": sorted(set(top_level_dirs)),
        "hidden_dirs": sorted(hidden_dirs),
        "hidden_files": sorted(hidden_files),
    }


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def print_report(results: dict) -> None:
    """Print a human-readable analysis report."""
    print("=" * 60)
    print("FOLDER LISTING ANALYSIS REPORT")
    print("=" * 60)
    print(f"Source file: {results['file']}")
    print(f"Total lines: {results['total_lines']:,}")
    print(f"Unique directories: {results['total_dirs']:,}")
    print(f"Unique files: {results['total_files']:,}")
    print()

    print("--- Category Breakdown ---")
    for cat in sorted(results["categories"].keys()):
        print(f"  {cat:15s}: {results['categories'][cat]:>8,}")
    print(f"  {'TOTAL':15s}: {sum(results['categories'].values()):>8,}")
    print()

    print("--- Top-Level Directories ---")
    for d in results["top_level_dirs"]:
        print(f"  {d}")
    print()

    print("--- Hidden Items ---")
    print(f"  Hidden dirs: {len(results['hidden_dirs'])}")
    for d in results["hidden_dirs"][:20]:
        print(f"    {d}")
    if len(results["hidden_dirs"]) > 20:
        print(f"    ... and {len(results['hidden_dirs']) - 20} more")
    print(f"  Hidden files: {len(results['hidden_files'])}")
    for f in results["hidden_files"][:20]:
        print(f"    {f}")
    if len(results["hidden_files"]) > 20:
        print(f"    ... and {len(results['hidden_files']) - 20} more")
    print()

    print("--- Files by Category (sample) ---")
    for cat in sorted(results["files_by_category"].keys()):
        items = results["files_by_category"][cat]
        print(f"  [{cat}] ({len(items)} files)")
        for name in items[:10]:
            print(f"    {name}")
        if len(items) > 10:
            print(f"    ... and {len(items) - 10} more")
        print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <folder_listing.txt>", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    if not Path(path).exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    results = analyze_listing(path)
    print_report(results)

    print("\n--- JSON (stderr) ---", file=sys.stderr)
    json.dump(results, sys.stderr, indent=2, default=str)


if __name__ == "__main__":
    main()
