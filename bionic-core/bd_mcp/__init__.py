# BIONIC DAUGHTER v1 — MCP SERVERS PACKAGE
# ============================================================================
# Collection of MCP servers for the bionic daughter agent.
#
# NOTE: This directory shares the name "mcp" with the pip mcp SDK package.
# When src/ is on sys.path, Python finds our local mcp/ first.
# The pip mcp package provides: mcp.server, mcp.types, etc.
#
# For MCP server files that import "from mcp.server.fastmcp import FastMCP",
# we need to ensure the pip mcp package is found for that submodule.
#
# FIX: We use a finder on sys.meta_path that intercepts "mcp.X" imports
# where X is not a local server file, and redirects to the pip package.
# ---------------------------------------------------------------------------

import sys
import os
from importlib import import_module
import importlib.util

# ---------------------------------------------------------------------------
# Find the pip mcp package location
# ---------------------------------------------------------------------------
_PIP_MCP_DIR = None
for p in sys.path:
    candidate = os.path.join(p, 'mcp')
    if os.path.isdir(candidate):
        server_dir = os.path.join(candidate, 'server')
        if os.path.isdir(server_dir):
            _PIP_MCP_DIR = candidate
            break

# ---------------------------------------------------------------------------
# Auto-discover local server files by scanning THIS directory
# ---------------------------------------------------------------------------
import glob as _glob

_LOCAL_SERVERS = set()
for _f in _glob.glob(os.path.join(os.path.dirname(__file__), 'daughter_*.py')):
    _name = os.path.splitext(os.path.basename(_f))[0]
    if _name != '__init__':
        _LOCAL_SERVERS.add(_name)

# ---------------------------------------------------------------------------
# Custom finder: redirect mcp.X (X not local) to pip package
# ---------------------------------------------------------------------------
class _PipMCPRedirector:
    def find_spec(self, fullname, path, target=None):
        if not fullname.startswith('mcp.'):
            return None
        sub = fullname.split('.', 1)[1]
        if sub in _LOCAL_SERVERS or sub == '__init__':
            return None  # Let normal import handle local files
        
        if not _PIP_MCP_DIR:
            return None
        
        # Try to find the module in the pip package
        parts = fullname.split('.')
        search_dir = _PIP_MCP_DIR
        for i, part in enumerate(parts[1:], 1):
            candidate = os.path.join(search_dir, part + '.py')
            if os.path.exists(candidate):
                # It's a file in the pip package
                spec = importlib.util.spec_from_file_location(fullname, candidate)
                return spec
            candidate_dir = os.path.join(search_dir, part)
            init_file = os.path.join(candidate_dir, '__init__.py')
            if os.path.isdir(candidate_dir) and os.path.exists(init_file):
                search_dir = candidate_dir
                if i == len(parts) - 1:
                    spec = importlib.util.spec_from_file_location(fullname, init_file)
                    return spec
            else:
                return None
        
        return None

if _PIP_MCP_DIR:
    sys.meta_path.insert(0, _PipMCPRedirector())
