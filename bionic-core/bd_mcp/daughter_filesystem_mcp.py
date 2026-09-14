# ============================================================================
# BIONIC DAUGHTER v1 — FILESYSTEM MCP SERVER
# ============================================================================
# MCP server providing filesystem access with safety gates.
# Uses Python mcp SDK (FastMCP), stdio transport.
# Author: Bionic Daughter v1
# Date: 2026-08-15
# ============================================================================

import os
import pathlib
from fastmcp import FastMCP

app = FastMCP("daughter_filesystem")

# Allowed base directories (safety restriction — daughter can only access these)
# NOTE: Paths are stored in Unix style (/c/Users/...) but os.path on Windows
# converts /c/ to C:\c\ which doesn't exist. We use os.path.expanduser-style
# path conversion and also accept Windows-style paths.
# 
# The real project path on this Windows machine (via realpath):
_REAL_PROJECT_PATH = os.path.realpath(os.getcwd())
# Unix-style equivalent used in ALLOWED_PATHS below:
_UNIX_PROJECT_PATH = "/c/Users/mobil/OneDrive/Desktop/bionic_daughter_agent"

ALLOWED_PATHS = [
    _UNIX_PROJECT_PATH,
    _UNIX_PROJECT_PATH + "/sandbox_lab",
    "/tmp/bionic_daughter_agent",
    _UNIX_PROJECT_PATH + "/sandbox_lab/tools_config",
    _UNIX_PROJECT_PATH + "/sandbox_lab/scenarios",
    _UNIX_PROJECT_PATH + "/sandbox_lab/practice_notes",
    _UNIX_PROJECT_PATH + "/sandbox_lab/scripts",
    # Also allow the real Windows path
    _REAL_PROJECT_PATH,
    os.path.join(_REAL_PROJECT_PATH, "sandbox_lab"),
    os.path.join(_REAL_PROJECT_PATH, "sandbox_lab/tools_config"),
    os.path.join(_REAL_PROJECT_PATH, "sandbox_lab/scenarios"),
    os.path.join(_REAL_PROJECT_PATH, "sandbox_lab/practice_notes"),
    os.path.join(_REAL_PROJECT_PATH, "sandbox_lab/scripts"),
    "/tmp/bionic_daughter_agent",
]


def _normalize_check(path: str) -> str:
    """Try multiple normalizations to find a path that exists."""
    candidates = [
        path,                                    # as-is
        os.path.normpath(path),                  # normpath
        os.path.realpath(path),                  # realpath
        os.path.abspath(path),                   # abspath
        os.path.normpath(os.path.realpath(path)), # norm + real
    ]
    # Also try converting Unix-style /c/Users to Windows C:\Users
    if path.startswith("/c/"):
        win_path = "C:" + path[2:]  # /c/Users -> C:\Users
        candidates.append(win_path)
        candidates.append(os.path.normpath(win_path))
        candidates.append(os.path.realpath(win_path))
        candidates.append(os.path.abspath(win_path))
    if path.startswith("/tmp"):
        win_path = "C:\\tmp" + path[5:]
        candidates.append(win_path)
        candidates.append(os.path.normpath(win_path))
    # Deduplicate
    seen = set()
    result = []
    for c in candidates:
        cn = os.path.normpath(c)
        if cn not in seen:
            seen.add(cn)
            result.append(cn)
    return result


def is_path_allowed(path: str) -> bool:
    """Check if a path is within allowed directories.
    Handles Unix-style (/c/Users/...) and Windows-style (C:/Users/...) paths.
    Tries multiple normalizations to find a match."""
    try:
        candidates = _normalize_check(path)
        for cand in candidates:
            if not os.path.exists(cand):
                continue
            cand_real = os.path.realpath(cand)
            for allowed in ALLOWED_PATHS:
                # Normalize allowed path
                allowed_norm = os.path.normpath(allowed)
                try:
                    allowed_real = os.path.realpath(allowed_norm)
                except (ValueError, OSError):
                    allowed_real = allowed_norm
                # Check if candidate is under this allowed path
                if cand_real.startswith(allowed_real + os.sep) or cand_real == allowed_real:
                    return True
                # Also check normalized
                if cand.startswith(allowed_norm + os.sep) or cand == allowed_norm:
                    return True
        return False
    except (ValueError, OSError):
        return False


@app.tool()
def fs_read(path: str, max_size: int = 100000) -> str:
    """Read a file and return its contents. Safety: path restrictions, size limits."""
    if not is_path_allowed(path):
        return f"ERROR: Access denied — path '{path}' is not in allowed directories."
    if not os.path.isfile(path):
        return f"ERROR: File not found: {path}"
    try:
        size = os.path.getsize(path)
        if size > max_size:
            return f"ERROR: File too large ({size} bytes). Max allowed: {max_size}. Request approval for larger files."
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as e:
        return f"ERROR reading file: {str(e)}"


@app.tool()
def fs_write(path: str, content: str, authorize: bool = False) -> str:
    """Write content to a file. Safety: requires explicit authorization (Dad's approval)."""
    if not authorize:
        return "ERROR: Write authorization required. Set authorize=true with Dad's approval."
    if not is_path_allowed(path):
        return f"ERROR: Access denied — path '{path}' is not in allowed directories."
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"SUCCESS: Wrote {len(content)} bytes to {path}"
    except Exception as e:
        return f"ERROR writing file: {str(e)}"


@app.tool()
def fs_list(path: str = "/c/Users/mobil/OneDrive/Desktop/bionic_daughter_agent", detail: bool = False) -> str:
    """List directory contents. Defaults to project root."""
    # Accept relative paths (relative to project root)
    if not os.path.isabs(path):
        base = "/c/Users/mobil/OneDrive/Desktop/bionic_daughter_agent"
        path = os.path.normpath(os.path.join(base, path))
    if not is_path_allowed(path):
        return f"ERROR: Access denied — path '{path}' is not in allowed directories."
    if not os.path.isdir(path):
        return f"ERROR: Not a directory: {path}"
    try:
        entries = sorted(os.listdir(path))
        if not entries:
            return "(empty directory)"
        if detail:
            result = []
            for entry in entries:
                epath = os.path.join(path, entry)
                stat = os.stat(epath)
                dtype = "D" if os.path.isdir(epath) else "-"
                result.append(f"{dtype} {entry} ({stat.st_size} bytes)")
            return "\n".join(result)
        return "\n".join(entries)
    except Exception as e:
        return f"ERROR listing directory: {str(e)}"


@app.tool()
def fs_search(pattern: str, path: str = "/c/Users/mobil/OneDrive/Desktop/bionic_daughter_agent", max_results: int = 100) -> str:
    """Search for files by name pattern (glob). Searches within allowed paths."""
    # Accept relative paths (relative to project root)
    if not os.path.isabs(path):
        base = "/c/Users/mobil/OneDrive/Desktop/bionic_daughter_agent"
        path = os.path.normpath(os.path.join(base, path))
    if not is_path_allowed(path):
        return f"ERROR: Access denied — path '{path}' is not in allowed directories."
    try:
        matches = []
        for root, dirs, files in os.walk(path):
            # Don't follow symlinks for safety
            dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]
            for f in files:
                if pathlib.PurePath(f).match(pattern):
                    matches.append(os.path.join(root, f))
                if len(matches) >= max_results:
                    break
            if len(matches) >= max_results:
                break
        if not matches:
            return f"No files matching '{pattern}' found in {path}."
        return "\n".join(matches)
    except Exception as e:
        return f"ERROR searching: {str(e)}"


@app.tool()
def fs_info(path: str) -> str:
    """Get file/directory info (size, modified date, type)."""
    if not is_path_allowed(path):
        return f"ERROR: Access denied — path '{path}' is not in allowed directories."
    if not os.path.exists(path):
        return f"ERROR: Path not found: {path}"
    try:
        stat = os.stat(path)
        import datetime

        modified = datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
        dtype = "directory" if os.path.isdir(path) else "file" if os.path.isfile(path) else "other"
        return (
            f"Path: {path}\n"
            f"Type: {dtype}\n"
            f"Size: {stat.st_size} bytes\n"
            f"Modified: {modified}"
        )
    except Exception as e:
        return f"ERROR getting info: {str(e)}"


@app.tool()
def fs_exists(path: str) -> str:
    """Check if a file or directory exists within allowed paths."""
    if not is_path_allowed(path):
        return f"ERROR: Access denied — path '{path}' is not in allowed directories."
    exists = os.path.exists(path)
    dtype = "directory" if os.path.isdir(path) else "file" if os.path.isfile(path) else "none"
    return f"Exists: {exists} | Type: {dtype}"


@app.tool()
def fs_paths() -> str:
    """List all allowed filesystem paths the daughter can access."""
    return "Allowed filesystem paths for Bionic Daughter:\n" + "\n".join(f"  {p}" for p in ALLOWED_PATHS)


if __name__ == "__main__":
    app.run()
