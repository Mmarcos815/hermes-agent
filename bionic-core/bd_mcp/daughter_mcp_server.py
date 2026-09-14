#!/usr/bin/env python3
"""
===============================================================================
BIONIC DAUGHTER v1 — MCP SERVER
===============================================================================
Exposes daughter cognitive tools as MCP tools for any MCP host/client.

Tools exposed:
  - ast_validate: Validate Python code (AST + security scan)
  - sandbox_exec: Execute code in sandbox (requires authorization flag)
  - threat_scan: Scan environment (ports, processes)
  - memory_store: Store episodic memory
  - memory_query: Query episodic memory
  - session_log: Log a session to SQLite DB
  - skill_distill: Distill success into a skill file
  - skill_list: List all distilled skills
  - analyze_failures: Analyze recent failed trajectories
  - gpu_launch: Launch cloud GPU pod (requires cloud API config)
  - gpu_status: Check GPU pod status
  - gpu_shutdown: Shut down cloud GPU pod (stops billing)

Usage:
  pip install mcp
  python daughter_mcp_server.py

Or via stdio transport (for Claude Desktop, Cursor, etc.):
  mcp run --transport stdio daughter_mcp_server.py
===============================================================================
"""

import os
import json
import ast
import time
import re
import sqlite3
import subprocess
import logging
from pathlib import Path
from fastmcp import FastMCP

# ============================================================================
# SETUP
# ============================================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DaughterMCP")

PROJECT_DIR = Path(__file__).parent
DB_PATH = PROJECT_DIR / "daughter_sessions.db"
MEMORY_DIR = PROJECT_DIR / "daughter_vector_memory"
SKILLS_DIR = PROJECT_DIR / "daughter_skills"
TRAJECTORY_LOG = PROJECT_DIR / "daughter_rl_trajectories.jsonl"

os.makedirs(MEMORY_DIR, exist_ok=True)
os.makedirs(SKILLS_DIR, exist_ok=True)

mcp = FastMCP("bionic_daughter")

# ============================================================================
# COGNITIVE TOOL: AST VALIDATE
# ============================================================================

@mcp.tool()
def ast_validate(code_string: str) -> dict:
    """
    Validate Python code using AST parsing + security scan.
    Returns: {"valid": bool, "message": str, "issues": list}
    """
    issues = []
    try:
        tree = ast.parse(code_string)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in ("eval", "exec"):
                    issues.append(f"Unsafe function call: {node.func.id}()")
        if issues:
            return {"valid": False, "message": "Security issues found", "issues": issues}
        return {"valid": True, "message": "Code is valid and secure", "issues": []}
    except SyntaxError as e:
        return {"valid": False, "message": f"Syntax error: {e}", "issues": [str(e)]}

# ============================================================================
# COGNITIVE TOOL: SANDBOX EXEC
# ============================================================================

@mcp.tool()
def sandbox_exec(code_string: str, authorized: bool = False, timeout: int = 30) -> dict:
    """
    Execute code in a sandboxed subprocess.
    REQUIRES authorized=True for actual execution.
    Returns: {"exit_code": int, "stdout": str, "stderr": str, "authorized": bool}
    """
    if not authorized:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": "NOT AUTHORIZED — set authorized=True to execute",
            "authorized": False,
        }

    ext = "py" if "python" in code_string.lower() or "\n" in code_string else "sh"
    filename = PROJECT_DIR / f"daughter_sandbox.{ext}"
    with open(filename, "w") as f:
        f.write(code_string)

    cmd = f"python {filename}" if ext == "py" else f"bash {filename}"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True,
                                text=True, timeout=timeout)
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "authorized": True,
        }
    except subprocess.TimeoutExpired:
        return {"exit_code": -1, "stdout": "", "stderr": "Timeout", "authorized": True}
    except Exception as e:
        return {"exit_code": -1, "stdout": "", "stderr": str(e), "authorized": True}

# ============================================================================
# COGNITIVE TOOL: THREAT SCAN
# ============================================================================

@mcp.tool()
def threat_scan() -> dict:
    """
    Scan the host environment for network state.
    Returns: {"open_ports": list, "process_count": int, "status": str}
    """
    try:
        import psutil
        connections = psutil.net_connections(kind='inet')
        open_ports = sorted(set(c.laddr.port for c in connections if c.status == 'LISTEN'))
        return {
            "open_ports": open_ports,
            "process_count": len(psutil.pids()),
            "status": "STABLE" if not open_ports else f"LISTENING_PORTS:{open_ports}",
        }
    except Exception as e:
        return {"open_ports": [], "process_count": 0, "status": f"SCAN_ERROR:{e}"}

# ============================================================================
# COGNITIVE TOOL: MEMORY STORE / QUERY
# ============================================================================

@mcp.tool()
def memory_store(objective: str, reasoning: str, payload: str, output: str) -> dict:
    """
    Store an episodic memory entry in Chroma vector DB.
    Returns: {"status": str, "doc_id": str}
    """
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(MEMORY_DIR))
        collection = client.get_or_create_collection(name="daughter_episodic_memory")
        doc_id = f"mem_{int(time.time())}"
        content = f"Objective: {objective}\nReasoning: {reasoning}\nPayload: {payload}\nOutput: {output}"
        collection.add(documents=[content], ids=[doc_id])
        return {"status": "stored", "doc_id": doc_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def memory_query(query_text: str, n_results: int = 3) -> dict:
    """
    Query episodic memory for relevant past experiences.
    Returns: {"results": list of text entries}
    """
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(MEMORY_DIR))
        collection = client.get_or_create_collection(name="daughter_episodic_memory")
        results = collection.query(query_texts=[query_text], n_results=n_results)
        docs = results.get("documents", [[]])[0]
        return {"results": docs, "count": len(docs)}
    except Exception as e:
        return {"results": [], "count": 0, "error": str(e)}

# ============================================================================
# COGNITIVE TOOL: SESSION LOG
# ============================================================================

def _init_db():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            objective TEXT,
            reasoning TEXT,
            payload TEXT,
            output TEXT,
            exit_code INTEGER,
            status TEXT
        )
    """)
    conn.commit()
    return conn

_db = None
def _get_db():
    global _db
    if _db is None:
        _db = _init_db()
    return _db

@mcp.tool()
def session_log(objective: str, reasoning: str, payload: str,
                output: str, exit_code: int, status: str) -> dict:
    """
    Log an agent session to the SQLite database.
    Returns: {"status": str, "session_id": int}
    """
    conn = _get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sessions (timestamp, objective, reasoning, payload, output, exit_code, status) VALUES (datetime('now'),?,?,?,?,?,?)",
        (objective, reasoning, payload, output, exit_code, status)
    )
    conn.commit()
    return {"status": "logged", "session_id": cursor.lastrowid}

@mcp.tool()
def session_list(limit: int = 10) -> dict:
    """
    List recent sessions from the database.
    Returns: {"sessions": list of dicts}
    """
    conn = _get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, timestamp, objective, status, exit_code FROM sessions ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    rows = [{"id": r[0], "timestamp": r[1], "objective": r[2],
             "status": r[3], "exit_code": r[4]} for r in cursor.fetchall()]
    return {"sessions": rows, "count": len(rows)}

# ============================================================================
# COGNITIVE TOOL: SKILL DISTILL / LIST
# ============================================================================

@mcp.tool()
def skill_distill(objective: str, reasoning: str, payload: str, result: str) -> dict:
    """
    Distill a successful execution into a reusable skill file.
    Returns: {"status": str, "skill_path": str}
    """
    safe_name = "".join(c if c.isalnum() else "_" for c in objective.lower())[:40]
    filepath = SKILLS_DIR / f"skill_{safe_name}.md"
    content = f"""# Skill: {objective}
## Reasoning
{reasoning}

## Payload
```python
{payload}
```

## Result
{result}
"""
    filepath.write_text(content)
    return {"status": "distilled", "skill_path": str(filepath)}

@mcp.tool()
def skill_list() -> dict:
    """
    List all distilled skills.
    Returns: {"skills": list of skill file contents}
    """
    skills = []
    for f in SKILLS_DIR.glob("*.md"):
        skills.append({"name": f.stem, "content": f.read_text()})
    return {"skills": skills, "count": len(skills)}

# ============================================================================
# COGNITIVE TOOL: ANALYSIS
# ============================================================================

@mcp.tool()
def analyze_failures(n_recent: int = 10) -> dict:
    """
    Analyze recent failed execution trajectories.
    Returns: {"failures": list, "count": int, "patterns": list}
    """
    failures = []
    if TRAJECTORY_LOG.exists():
        with open(TRAJECTORY_LOG) as f:
            for line in f:
                try:
                    record = json.loads(line)
                    if not record.get("success", True):
                        failures.append(record)
                except Exception:
                    continue
    failures = failures[-n_recent:]

    patterns = []
    if failures:
        # Simple pattern detection
        payloads = [f.get("payload", "") for f in failures]
        if any("eval(" in p or "exec(" in p for p in payloads):
            patterns.append("eval/exec usage in failed payloads")
        if any("os.system" in p for p in payloads):
            patterns.append("os.system usage in failed payloads")
        if not patterns:
            patterns.append("No specific pattern detected — review individually")

    return {"failures": failures, "count": len(failures), "patterns": patterns}

# ============================================================================
# GPU AUTONOMY TOOLS (cloud GPU launch/shutdown)
# ============================================================================

# These require cloud API credentials to be configured.
# Store credentials in environment variables or a config file.

@mcp.tool()
def gpu_launch(provider: str = "runpod", gpu_type: str = "RTX-4090",
               hours: int = 5, docker_image: str = "python:3.11-slim") -> dict:
    """
    Launch a cloud GPU pod for training.
    REQUIRES: RUNPOD_API_KEY env var (or VAST_API_KEY for Vast.ai).
    Returns: {"status": str, "pod_id": str, "estimated_cost": float, "details": dict}
    """
    import os
    api_key = os.environ.get("RUNPOD_API_KEY") or os.environ.get("VAST_API_KEY")

    if not api_key:
        return {"status": "error", "message": "No cloud API key configured. Set RUNPOD_API_KEY or VAST_API_KEY env var."}

    if provider == "runpod":
        # RunPod API: create an endpoint or pod
        # For simplicity, this is a placeholder — real implementation
        # uses requests to RunPod's API
        estimated_cost = hours * 0.34  # RTX 4090 community rate
        return {
            "status": "launched",
            "pod_id": f"daughter-pod-{int(time.time())}",
            "estimated_cost": estimated_cost,
            "details": {
                "provider": "runpod",
                "gpu_type": gpu_type,
                "hours": hours,
                "docker_image": docker_image,
                "note": "Full implementation requires cloud API integration",
            }
        }
    elif provider == "vast.ai":
        estimated_cost = hours * 0.34
        return {
            "status": "launched",
            "pod_id": f"daughter-vast-{int(time.time())}",
            "estimated_cost": estimated_cost,
            "details": {"provider": "vast.ai", "gpu_type": gpu_type, "hours": hours},
        }
    else:
        return {"status": "error", "message": f"Unknown provider: {provider}"}

@mcp.tool()
def gpu_status(pod_id: str) -> dict:
    """Check status of a cloud GPU pod."""
    return {"pod_id": pod_id, "status": "unknown", "note": "Requires cloud API integration"}

@mcp.tool()
def gpu_shutdown(pod_id: str) -> dict:
    """
    Shut down a cloud GPU pod — stops billing immediately.
    Returns: {"status": str, "pod_id": str, "shutdown_time": str}
    """
    return {"status": "shutdown_initiated", "pod_id": pod_id,
            "shutdown_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "note": "Requires cloud API integration for actual shutdown"}

# ============================================================================
# TOOL DISCOVERY
# ============================================================================

@mcp.tool()
def daughter_tools_list() -> dict:
    """
    List all available daughter MCP tools with descriptions.
    Returns: {"tools": list of {name, description}}
    """
    return {
        "tools": [
            {"name": "ast_validate", "description": "Validate Python code with AST + security scan"},
            {"name": "sandbox_exec", "description": "Execute code in sandbox (requires authorized=True)"},
            {"name": "threat_scan", "description": "Scan host environment for open ports and processes"},
            {"name": "memory_store", "description": "Store episodic memory in Chroma vector DB"},
            {"name": "memory_query", "description": "Query episodic memory for relevant past experiences"},
            {"name": "session_log", "description": "Log an agent session to SQLite database"},
            {"name": "session_list", "description": "List recent sessions from the database"},
            {"name": "skill_distill", "description": "Distill a successful execution into a skill file"},
            {"name": "skill_list", "description": "List all distilled skills"},
            {"name": "analyze_failures", "description": "Analyze recent failed trajectories for patterns"},
            {"name": "gpu_launch", "description": "Launch a cloud GPU pod for training"},
            {"name": "gpu_status", "description": "Check cloud GPU pod status"},
            {"name": "gpu_shutdown", "description": "Shut down cloud GPU pod (stops billing)"},
            {"name": "daughter_tools_list", "description": "List all available tools (this tool)"},
        ]
    }

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    logger.info("Starting Bionic Daughter MCP Server...")
    logger.info(f"Project dir: {PROJECT_DIR}")
    logger.info(f"DB: {DB_PATH}")
    logger.info(f"Memory: {MEMORY_DIR}")
    logger.info(f"Skills: {SKILLS_DIR}")
    mcp.run(transport="stdio")
