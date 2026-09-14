#!/usr/bin/env python3
# ============================================================================
# BIONIC DAUGHTER v1 — INFERENCE ENGINE MODULE
# ============================================================================
# Provides the inference engine and supporting classes that jarvis.py imports
# from inference.daughter_command_center.
#
# This module bridges the gap between jarvis.py's expected imports and the
# actual implementations living in modules/, bionic-core/src_modules/, and
# bd_mcp/.
#
# Classes provided (with fallback where real implementations exist):
#   - LlamaEngine:          GGUF inference engine (stub — requires model file)
#   - CodeValidator:        AST + security validation (real implementation)
#   - SessionLogger:        SQLite session logging (real implementation)
#   - VectorMemory:         ChromaDB episodic memory (real implementation)
#   - SkillRegistry:        Skill management (real implementation)
#   - SelfImprover:         Trajectory logging (re-export from modules)
#   - FinancialAnalyzer:    Financial analysis (re-export from modules)
#   - MCPClient:            MCP client (stub — requires MCP config)
#   - OrcaIntegration:      Orca worktree/terminal mgmt (re-export from modules)
#
# Constants:
#   - PROJECT_DIR:          Project root directory
#   - DB_PATH:              SQLite DB path for sessions
#   - MEMORY_DIR:           ChromaDB directory
#   - SKILLS_DIR:           Skill distillation directory
#   - TRAJECTORY_LOG:       RL trajectory log file
# ============================================================================

import os
import sys
import json
import sqlite3
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("inference")

# ============================================================================
# PATHS
# ============================================================================

PROJECT_DIR = Path(__file__).parent.parent.resolve()
DB_PATH = PROJECT_DIR / "daughter_sessions.db"
MEMORY_DIR = PROJECT_DIR / "daughter_vector_memory"
SKILLS_DIR = PROJECT_DIR / "daughter_skills"
TRAJECTORY_LOG = PROJECT_DIR / "daughter_rl_trajectories.jsonl"

# Ensure directories exist
os.makedirs(MEMORY_DIR, exist_ok=True)
os.makedirs(SKILLS_DIR, exist_ok=True)


# ============================================================================
# LLMAENGINE — GGUF Inference Engine (stub with real interface)
# ============================================================================

class LlamaEngine:
    """GGUF inference engine using Llama.cpp.

    Requires a GGUF model file to actually run. Without a model, this is a
    stub that logs warnings and returns placeholder responses.

    Usage:
        engine = LlamaEngine(gguf_path="model.gguf", n_ctx=8192)
        engine.set_model_dir("/path/to/merged/model")
        response = engine.generate("Hello, world!")
    """

    def __init__(
        self,
        gguf_path: str = None,
        model_dir: str = None,
        n_ctx: int = 8192,
        n_gpu_layers: int = -1,
    ):
        self.gguf_path = gguf_path
        self.model_dir = model_dir
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self._model = None
        self._available = False

        # Try to detect if llama-cpp-python is installed
        try:
            import llama_cpp  # noqa: F401
            self._backend = "llama_cpp"
            logger.info("LlamaEngine: llama-cpp-python backend detected")
        except ImportError:
            self._backend = None
            logger.warning(
                "LlamaEngine: llama-cpp-python not installed. "
                "Install with: pip install llama-cpp-python"
            )

        # Try to load model if path provided
        if gguf_path and os.path.exists(gguf_path):
            self._try_load_model()
        elif model_dir and os.path.isdir(model_dir):
            # Look for .gguf files in model_dir
            gguf_files = list(Path(model_dir).glob("*.gguf"))
            if gguf_files:
                self.gguf_path = str(gguf_files[0])
                self._try_load_model()

    def _try_load_model(self):
        """Attempt to load the GGUF model."""
        if not self._backend:
            logger.error(
                f"LlamaEngine: Cannot load model — llama-cpp-python not available. "
                f"Model path: {self.gguf_path}"
            )
            return

        try:
            import llama_cpp

            self._model = llama_cpp.Llama(
                model_path=self.gguf_path,
                n_ctx=self.n_ctx,
                n_gpu_layers=self.n_gpu_layers if self.n_gpu_layers > 0 else 0,
                flash_attn=True,
            )
            self._available = True
            logger.info(
                f"LlamaEngine: Loaded model from {self.gguf_path} "
                f"(ctx={self.n_ctx}, backend={self._backend})"
            )
        except Exception as e:
            logger.error(f"LlamaEngine: Failed to load model: {e}")
            self._available = False

    def is_available(self) -> bool:
        """Check if the inference engine is ready to generate."""
        return self._available

    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        """Generate a response from the model.

        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text response
        """
        if not self._available:
            logger.warning(
                f"LlamaEngine: generate() called but engine not available. "
                f"Prompt: {prompt[:100]}..."
            )
            return "[LlamaEngine: model not loaded — install llama-cpp-python and provide a GGUF file]"

        try:
            output = self._model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                echo=False,
            )
            return output["choices"][0]["text"]
        except Exception as e:
            logger.error(f"LlamaEngine: generation failed: {e}")
            return f"[Error: {e}]"

    def generate_chat(self, messages: list, max_tokens: int = 512) -> str:
        """Generate a chat completion from a list of messages.

        Args:
            messages: List of {"role": "user"|"assistant"|"system", "content": "..."}
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response
        """
        if not self._available:
            return "[LlamaEngine: model not loaded]"

        try:
            output = self._model.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
            )
            return output["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"LlamaEngine: chat completion failed: {e}")
            return f"[Error: {e}]"

    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        if self._model is None:
            return {
                "status": "not_loaded",
                "gguf_path": self.gguf_path,
                "model_dir": self.model_dir,
                "n_ctx": self.n_ctx,
                "backend": self._backend,
            }

        try:
            info = self._model.params
            return {
                "status": "loaded",
                "gguf_path": self.gguf_path,
                "model_dir": self.model_dir,
                "n_ctx": self.n_ctx,
                "backend": self._backend,
                "params": {
                    "n_ctx": getattr(info, "n_ctx", None),
                    "n_embd": getattr(info, "n_embd", None),
                    "n_layer": getattr(info, "n_layer", None),
                    "n_head": getattr(info, "n_head", None),
                    "n_vocab": getattr(info, "n_vocab", None),
                },
            }
        except Exception:
            return {
                "status": "loaded",
                "gguf_path": self.gguf_path,
                "model_dir": self.model_dir,
                "n_ctx": self.n_ctx,
                "backend": self._backend,
            }


# ============================================================================
# CODEVALIDATOR — AST + Security Validation
# ============================================================================

class CodeValidator:
    """Validates Python code using AST parsing and security checks.

    Checks for:
    - Syntax errors
    - Dangerous imports (subprocess, os.system, eval, exec, etc.)
    - Unsafe patterns (shell=True, os.popen, etc.)
    - Basic code quality issues
    """

    DANGEROUS_IMPORTS = {
        "subprocess": "Can execute arbitrary shell commands",
        "os.system": "Can execute arbitrary shell commands",
        "os.popen": "Can execute arbitrary shell commands",
        "eval": "Can execute arbitrary Python code",
        "exec": "Can execute arbitrary Python code",
        "compile": "Can compile arbitrary code",
        "importlib": "Can dynamically load modules",
        "__import__": "Can dynamically import modules",
    }

    DANGEROUS_FUNCTION_CALLS = {
        "subprocess.call": "Can execute shell commands",
        "subprocess.Popen": "Can execute shell commands",
        "subprocess.run": "Can execute shell commands (check shell=True)",
        "os.system": "Can execute shell commands",
        "os.popen": "Can execute shell commands",
        "eval(": "Can execute arbitrary code",
        "exec(": "Can execute arbitrary code",
        "compile(": "Can compile arbitrary code",
    }

    def __init__(self):
        self.issues = []

    def validate(self, code: str, strict: bool = False) -> dict:
        """Validate Python code.

        Args:
            code: Python source code to validate
            strict: If True, flag all potentially dangerous patterns

        Returns:
            dict with 'valid' (bool), 'issues' (list), 'severity' (str)
        """
        self.issues = []

        # 1. Syntax check
        try:
            tree = compile(code, "<string>", "exec", ast.PyCF_ONLY_AST)
        except SyntaxError as e:
            return {
                "valid": False,
                "issues": [{"type": "syntax_error", "message": str(e), "line": e.lineno}],
                "severity": "critical",
            }

        # 2. AST-based security checks
        self._check_ast(tree)

        # 3. Text-based pattern checks
        self._check_patterns(code)

        severity = "clean"
        if any(i["severity"] == "critical" for i in self.issues):
            severity = "critical"
        elif any(i["severity"] == "warning" for i in self.issues):
            severity = "warning"

        return {
            "valid": len([i for i in self.issues if i["severity"] == "critical"]) == 0,
            "issues": self.issues,
            "severity": severity,
        }

    def _check_ast(self, tree):
        """Walk the AST and check for dangerous patterns."""
        for node in ast.walk(tree):
            # Check imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.DANGEROUS_IMPORTS:
                        self.issues.append({
                            "type": "dangerous_import",
                            "module": alias.name,
                            "message": f"Import of '{alias.name}': {self.DANGEROUS_IMPORTS[alias.name]}",
                            "severity": "warning",
                            "line": node.lineno,
                        })
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module in self.DANGEROUS_IMPORTS:
                    self.issues.append({
                        "type": "dangerous_import",
                        "module": node.module,
                        "message": f"Import from '{node.module}': {self.DANGEROUS_IMPORTS[node.module]}",
                        "severity": "warning",
                        "line": node.lineno,
                    })

            # Check function calls
            elif isinstance(node, ast.Call):
                func_name = self._get_func_name(node.func)
                if func_name in self.DANGEROUS_FUNCTION_CALLS:
                    severity = "warning"
                    if func_name in ("eval(", "exec(", "compile("):
                        severity = "critical"
                    self.issues.append({
                        "type": "dangerous_call",
                        "function": func_name,
                        "message": f"Call to {func_name}: {self.DANGEROUS_FUNCTION_CALLS[func_name]}",
                        "severity": severity,
                        "line": node.lineno,
                    })

                # Check subprocess.run with shell=True
                if func_name == "subprocess.run":
                    for kw in node.keywords:
                        if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                            self.issues.append({
                                "type": "dangerous_pattern",
                                "message": "subprocess.run with shell=True — command injection risk",
                                "severity": "critical",
                                "line": node.lineno,
                            })

    def _check_patterns(self, code: str):
        """Check for dangerous text patterns."""
        lines = code.splitlines()
        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Skip comments
            if stripped.startswith("#"):
                continue

            # Check for os.system / os.popen in text
            for pattern in ["os.system(", "os.popen(", "eval(", "exec("]:
                if pattern in line and not stripped.startswith("#"):
                    # Avoid double-reporting if AST already caught it
                    existing = [x for x in self.issues if x.get("line") == i and pattern in x.get("message", "")]
                    if not existing:
                        self.issues.append({
                            "type": "dangerous_pattern",
                            "pattern": pattern,
                            "message": f"Potentially dangerous pattern '{pattern}' on line {i}",
                            "severity": "warning",
                            "line": i,
                        })

            # Check for shell=True
            if "shell=True" in line and not stripped.startswith("#"):
                existing = [x for x in self.issues if x.get("line") == i and "shell=True" in x.get("message", "")]
                if not existing:
                    self.issues.append({
                        "type": "dangerous_pattern",
                        "message": "shell=True found — command injection risk",
                        "severity": "critical",
                        "line": i,
                    })

    def _get_func_name(self, node) -> str:
        """Get the full dotted name of a function call node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_func_name(node.value)}.{node.attr}"
        return ""


# ============================================================================
# SESSIONLOGGER — SQLite Session Logging
# ============================================================================

class SessionLogger:
    """Logs agent sessions to a SQLite database.

    Tracks: session ID, objective, start/end time, steps, outcome, tokens used.
    """

    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._init_db()

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                objective TEXT,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                steps_taken INTEGER DEFAULT 0,
                outcome TEXT,
                tokens_in INTEGER DEFAULT 0,
                tokens_out INTEGER DEFAULT 0,
                success BOOLEAN,
                notes TEXT
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS session_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,
                details TEXT
            )
        """)
        self.conn.commit()

    def start_session(self, session_id: str, objective: str = "") -> dict:
        """Start a new session."""
        try:
            self.conn.execute(
                "INSERT OR IGNORE INTO sessions (session_id, objective) VALUES (?, ?)",
                (session_id, objective),
            )
            self.conn.commit()
            return {"success": True, "session_id": session_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def log_event(self, session_id: str, event_type: str, details: str = "") -> dict:
        """Log an event during a session."""
        try:
            self.conn.execute(
                "INSERT INTO session_events (session_id, event_type, details) VALUES (?, ?, ?)",
                (session_id, event_type, details),
            )
            self.conn.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def end_session(
        self,
        session_id: str,
        steps_taken: int = 0,
        outcome: str = "",
        tokens_in: int = 0,
        tokens_out: int = 0,
        success: bool = False,
        notes: str = "",
    ) -> dict:
        """End a session and record final stats."""
        try:
            self.conn.execute(
                """UPDATE sessions SET
                    end_time = CURRENT_TIMESTAMP,
                    steps_taken = ?,
                    outcome = ?,
                    tokens_in = ?,
                    tokens_out = ?,
                    success = ?,
                    notes = ?
                WHERE session_id = ?""",
                (steps_taken, outcome, tokens_in, tokens_out, success, notes, session_id),
            )
            self.conn.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_session(self, session_id: str) -> dict:
        """Get session details."""
        cursor = self.conn.execute(
            "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "session_id": row[1],
            "objective": row[2],
            "start_time": row[3],
            "end_time": row[4],
            "steps_taken": row[5],
            "outcome": row[6],
            "tokens_in": row[7],
            "tokens_out": row[8],
            "success": row[9],
            "notes": row[10],
        }

    def list_sessions(self, limit: int = 20, success_only: bool = False) -> list:
        """List recent sessions."""
        query = "SELECT * FROM sessions ORDER BY start_time DESC LIMIT ?"
        params = (limit,)
        if success_only:
            query = "SELECT * FROM sessions WHERE success = 1 ORDER BY start_time DESC LIMIT ?"
        cursor = self.conn.execute(query, params)
        return [
            {
                "id": r[0],
                "session_id": r[1],
                "objective": r[2],
                "start_time": r[3],
                "end_time": r[4],
                "steps_taken": r[5],
                "outcome": r[6],
                "tokens_in": r[7],
                "tokens_out": r[8],
                "success": bool(r[9]),
                "notes": r[10],
            }
            for r in cursor.fetchall()
        ]

    def get_stats(self) -> dict:
        """Get session statistics."""
        cursor = self.conn.execute("SELECT COUNT(*) FROM sessions")
        total = cursor.fetchone()[0]
        cursor = self.conn.execute("SELECT COUNT(*) FROM sessions WHERE success = 1")
        successes = cursor.fetchone()[0]
        cursor = self.conn.execute("SELECT SUM(tokens_in), SUM(tokens_out) FROM sessions")
        tokens = cursor.fetchone()
        return {
            "total_sessions": total,
            "successful_sessions": successes,
            "success_rate": (successes / total * 100) if total > 0 else 0,
            "total_tokens_in": tokens[0] or 0,
            "total_tokens_out": tokens[1] or 0,
        }


# ============================================================================
# VECTORMEMORY — ChromaDB Episodic Memory
# ============================================================================

class VectorMemory:
    """Episodic memory using ChromaDB vector store.

    Stores and retrieves memories by semantic similarity.
    """

    def __init__(self, memory_dir=None):
        self.memory_dir = memory_dir or MEMORY_DIR
        self._client = None
        self._available = False
        self._init_client()

    def _init_client(self):
        """Initialize the ChromaDB client."""
        try:
            import chromadb

            self._client = chromadb.PersistentClient(path=str(self.memory_dir))
            self._available = True
        except ImportError:
            logger.warning(
                "VectorMemory: chromadb not installed. "
                "Install with: pip install chromadb"
            )
        except Exception as e:
            logger.warning(f"VectorMemory: Could not initialize ChromaDB: {e}")

    def is_available(self) -> bool:
        return self._available

    def store(self, objective: str, reasoning: str, payload: str, output: str, metadata: dict = None) -> dict:
        """Store an episodic memory."""
        if not self._available:
            return {"success": False, "error": "ChromaDB not available"}

        try:
            import chromadb

            collection = self._client.get_or_create_collection("episodic_memory")

            entry = f"Objective: {objective}\nReasoning: {reasoning}\nPayload: {payload}\nOutput: {output}"
            metadata = metadata or {}
            metadata["objective"] = objective
            metadata["timestamp"] = str(__import__("datetime").datetime.now().isoformat())

            collection.add(
                documents=[entry],
                metadatas=[metadata],
                ids=[f"mem_{hash(objective + str(metadata)) % 10**12}"],
            )
            return {"success": True, "stored": True}
        except Exception as e:
            logger.error(f"VectorMemory: store failed: {e}")
            return {"success": False, "error": str(e)}

    def query(self, query_text: str, n_results: int = 3) -> dict:
        """Query memories by semantic similarity."""
        if not self._available:
            return {"results": [], "error": "ChromaDB not available"}

        try:
            import chromadb

            collection = self._client.get_collection("episodic_memory")
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
            )
            return {
                "results": [
                    {
                        "document": doc,
                        "metadata": meta,
                        "distance": dist,
                    }
                    for doc, meta, dist in zip(
                        results.get("documents", [[]])[0],
                        results.get("metadatas", [[]])[0],
                        results.get("distances", [[]])[0],
                    )
                ],
                "count": len(results.get("documents", [[]])[0]),
            }
        except Exception as e:
            logger.error(f"VectorMemory: query failed: {e}")
            return {"results": [], "error": str(e)}

    def clear(self) -> dict:
        """Clear all memories."""
        if not self._available:
            return {"success": False, "error": "ChromaDB not available"}
        try:
            self._client.delete_collection("episodic_memory")
            return {"success": True, "cleared": True}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================================
# SKILLREGISTRY — Skill Management
# ============================================================================

class SkillRegistry:
    """Manages distilled skills — records of successful techniques."""

    def __init__(self, skills_dir=None):
        self.skills_dir = skills_dir or SKILLS_DIR
        os.makedirs(self.skills_dir, exist_ok=True)
        self._skills = {}
        self._load_skills()

    def _load_skills(self):
        """Load all skill files from the skills directory."""
        for f in self.skills_dir.glob("skill_*.md"):
            try:
                content = f.read_text()
                name = f.stem.replace("skill_", "")
                self._skills[name] = {
                    "file": f.name,
                    "path": str(f),
                    "content": content,
                    "size": f.stat().st_size,
                    "modified": f.stat().st_mtime,
                }
            except Exception:
                pass

    def list_skills(self) -> dict:
        """List all registered skills."""
        return {
            "skills": list(self._skills.keys()),
            "count": len(self._skills),
            "skills_detail": self._skills,
        }

    def save_skill(self, name: str, content: str) -> dict:
        """Save a skill to a file."""
        safe_name = "".join(c for c in name if c.isalnum() or c in "_-")
        filepath = self.skills_dir / f"skill_{safe_name}.md"
        try:
            filepath.write_text(content)
            self._skills[safe_name] = {
                "file": filepath.name,
                "path": str(filepath),
                "content": content,
                "size": filepath.stat().st_size,
                "modified": filepath.stat().st_mtime,
            }
            return {"success": True, "skill": safe_name, "path": str(filepath)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_skill(self, name: str) -> dict:
        """Get a skill's content."""
        if name in self._skills:
            return {"found": True, "skill": name, "content": self._skills[name]["content"]}
        return {"found": False, "skill": name}

    def delete_skill(self, name: str) -> dict:
        """Delete a skill file."""
        if name in self._skills:
            try:
                path = Path(self._skills[name]["path"])
                path.unlink()
                del self._skills[name]
                return {"success": True, "deleted": name}
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": False, "error": f"Skill '{name}' not found"}


# ============================================================================
# MCPCLIENT — MCP Client (stub)
# ============================================================================

class MCPClient:
    """Client for connecting to MCP servers.

    This is a stub — real MCP client functionality requires the MCP SDK
    and configured server endpoints.
    """

    def __init__(self):
        self.servers = {}
        self._available = False
        self._try_init()

    def _try_init(self):
        """Try to initialize MCP client."""
        try:
            from mcp import Client
            self._available = True
            logger.info("MCPClient: MCP SDK available")
        except ImportError:
            logger.warning(
                "MCPClient: MCP SDK not installed. "
                "Install with: pip install mcp"
            )

    def is_available(self) -> bool:
        return self._available

    def list_tools(self, server_name: str = None) -> dict:
        """List available tools from MCP servers."""
        if not self._available:
            return {"error": "MCP SDK not available", "tools": []}

        tools = []
        for name, server in self.servers.items():
            try:
                server_tools = server.list_tools()
                tools.extend([{"server": name, "tool": t} for t in server_tools])
            except Exception:
                pass

        return {"tools": tools, "count": len(tools)}

    def call_tool(self, server_name: str, tool_name: str, **kwargs) -> dict:
        """Call a tool on an MCP server."""
        if not self._available:
            return {"error": "MCP SDK not available"}

        if server_name not in self.servers:
            return {"error": f"Server '{server_name}' not connected"}

        try:
            result = self.servers[server_name].call_tool(tool_name, kwargs)
            return {"success": True, "result": result}
        except Exception as e:
            return {"error": str(e)}


# ============================================================================
# ORCAINTEGRATION — Orca Worktree/Terminal Management
# ============================================================================

class OrcaIntegration:
    """Integration with Orca ADE for worktree and terminal management.

    Provides:
    - Worktree creation/management
    - Terminal command execution
    - Process monitoring
    """

    def __init__(self):
        self._available = False
        self._try_init()

    def _try_init(self):
        """Try to initialize Orca integration."""
        try:
            # Check if orca_swarm_orchestrator is available
            sys.path.insert(0, str(PROJECT_DIR))
            import orca_swarm_orchestrator  # noqa: F401
            self._available = True
            logger.info("OrcaIntegration: orca_swarm_orchestrator available")
        except ImportError:
            logger.warning(
                "OrcaIntegration: orca_swarm_orchestrator not available. "
                "Install or add to path."
            )

    def is_available(self) -> bool:
        return self._available

    def create_worktree(self, branch: str, name: str = None) -> dict:
        """Create a new git worktree."""
        if not self._available:
            return {"error": "Orca not available"}
        # Implementation depends on orca_swarm_orchestrator API
        return {"error": "Not implemented — requires orca API"}

    def run_terminal_command(self, command: str, cwd: str = None, timeout: int = 60) -> dict:
        """Run a terminal command and return output."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd or str(PROJECT_DIR),
                timeout=timeout,
            )
            return {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timed_out": False,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out", "timed_out": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_status(self) -> dict:
        """Get Orca integration status."""
        return {
            "available": self._available,
            "project_dir": str(PROJECT_DIR),
        }


# ============================================================================
# INITIALIZATION — what jarvis.py expects at module level
# ============================================================================

__all__ = [
    "LlamaEngine",
    "CodeValidator",
    "SessionLogger",
    "VectorMemory",
    "SkillRegistry",
    "SelfImprover",
    "FinancialAnalyzer",
    "MCPClient",
    "OrcaIntegration",
    "PROJECT_DIR",
    "DB_PATH",
    "MEMORY_DIR",
    "SKILLS_DIR",
    "TRAJECTORY_LOG",
]


# Try to import SelfImprover and FinancialAnalyzer from their real locations
# so jarvis.py gets the real implementations.
# NOTE: modules/ is a sibling of inference/ at the project root, so we add
# PROJECT_DIR to sys.path to make 'modules' importable.
_MY_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _MY_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

try:
    from modules.cognitive.daughter_self_improver import SelfImprover
except ImportError:
    try:
        from modules.cognitive.daughter_self_improver import SelfImprover
    except ImportError:
        pass

try:
    from modules.financial.daughter_financial_analyzer import FinancialAnalyzer
except ImportError:
    try:
        from bionic_core.src_modules.financial.daughter_financial_analyzer import FinancialAnalyzer
    except ImportError:
        pass
