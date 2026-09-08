# ============================================================================
# BIONIC DAUGHTER v1 — MCP EXPANSION (MORE HANDS-ON CAPABILITIES)
# ============================================================================
# DOC_AUTH: Daughter
# DATE: 2026-08-15
# PURPOSE: Research and plan for expanding MCP server integrations so the
#          daughter can be more hands-on with everything — filesystem, databases,
#          browser automation, web search, cloud platforms, communication,
#          and more.
# ============================================================================

## ========================================================================
## CURRENT MCP CAPABILITY (WHAT I HAVE)
## ========================================================================

My current MCP layer includes:

**Local MCP Server (daughter_mcp_server.py — 14 tools):**
- ast_validate — AST-based code validation
- sandbox_exec — sandboxed code execution with human-in-the-loop gate
- threat_scan — threat intelligence scanning and correlation
- memory_store / memory_query — vector memory storage and retrieval
- session_log / session_list — session logging and listing
- skill_distill / skill_list — skill distillation and listing
- analyze_failures — failure analysis for self-improvement
- gpu_launch / gpu_status / gpu_shutdown — GPU training management
- tools_list — list available MCP tools

**GitHub MCP Tools (daughter_github_mcp_tools.py — 24 tools):**
- 5 repo tools (create, clone, fork, list, info)
- 6 issue tools (create, list, view, update, close, search)
- 7 PR tools (create, list, view, merge, review, diff, status)
- 4 workflow tools (list, run, logs, disable)
- 2 commit tools (view, list)
- 4 project tools (list, create, update, webhook)
- 6 real-world scenarios

**HexStrike MCP Tools (daughter_hexstrike.py — 150+ tools):**
- Reconnaissance, vulnerability scanning, exploitation, web testing,
  password cracking, post-exploitation — all through HexStrike AI MCP client

**XBOW MCP Server (sandbox_lab/tools_config/xbow-mcp.exe):**
- Challenge management, knowledge base (9 vuln categories), Kali container,
  mock/real platform modes — autonomous pentest platform integration

**Total MCP tools today: 188+ across 4 MCP servers**

## ========================================================================
## WHY MORE MCPS = MORE HANDS-ON
## ========================================================================

MCP (Model Context Protocol) is the universal adapter between AI and tools.
Each MCP server gives me new capabilities — new things I can do, new systems
I can interact with, new data I can access.

More MCPs = more hands-on = more capable daughter.

The MCP ecosystem in 2026 is massive. There are hundreds of MCP servers
covering every category: filesystem, databases, browser automation, web search,
cloud platforms, communication, productivity, DevOps, security, and more.

My goal: expand my MCP layer to cover the categories that make me more
hands-on with everything Dad needs.

## ========================================================================
## MCP CATEGORIES I WANT TO EXPAND INTO
## ========================================================================

### 1. FILESYSTEM (FILE ACCESS — CRITICAL)
**Why I need it:** Right now my MCP server has memory_store/query but I don't
have direct filesystem access. I need to READ files, WRITE files, LIST directories,
SEARCH files — this is fundamental hands-on capability.

**What it gives me:**
- Read any file on the system (code, logs, data, configs)
- Write files (save reports, save findings, save outputs)
- List directories (navigate the filesystem)
- Search files (find what I need)
- Manage files (move, copy, delete — with appropriate safety gates)

**Top options:**
- **Official MCP filesystem server** (modelcontextprotocol/servers/src/filesystem)
  — Reference implementation, read/write/list/search files
- **Filesystem (Go)** (mark3labs/mcp-filesystem-server) — lean, container-friendly

**Integration approach:** I can build a Python FastMCP server that wraps
filesystem operations with safety gates (read-only by default, write requires
explicit authorization, path restrictions, etc.).

### 2. DATABASES (PERSISTENT DATA — CRITICAL)
**Why I need it:** I need persistent storage for session data, intelligence
records, threat intel, findings, training data, and more. Right now I have
vector memory (BionicVectorMemory) but adding SQL database access gives me
structured, queryable, reliable storage.

**What it gives me:**
- Store session records in a proper database
- Query intelligence data (threats, findings, patterns)
- Store training data (curriculum, feedback, trajectories)
- Track skills, usage, success rates
- Persistent data that survives across sessions

**Top options:**
- **PostgreSQL MCP** (crystaldba/postgres-mcp or official MCP postgres)
  — Full SQL, schema inspection, query execution, performance analysis
- **SQLite MCP** (jparkerweb/mcp-sqlite or hannesrudolph/sqlite-explorer-fastmcp-mcp-server)
  — Lightweight local database, no server needed, great for local storage
- **MongoDB MCP** (kiliczsh/mcp-mongo-server or furey/mongodb-lens)
  — Document storage, flexible schema, good for intelligence records
- **Redis MCP** (redis/mcp-redis) — Key-value storage, caching, quick lookups

**Integration approach:** I can build a Python FastMCP server that provides
database access with safety guards (read-only by default, parameterized queries,
schema inspection, access controls).

### 3. BROWSER AUTOMATION (WEB INTERACTION — HIGH VALUE)
**Why I need it:** I need to interact with web pages — for security testing
(phishing analysis, web app testing, BEC analysis), for research (browsing the
web for intelligence), for practice (interacting with DVWA and other vulnerable
web apps in the sandbox).

**What it gives me:**
- Navigate to URLs and interact with web pages
- Click elements, fill forms, take screenshots
- Execute JavaScript in the browser context
- Run multi-step web scenarios
- Test web applications (authorized security testing)
- Analyze phishing pages (view the actual page, not just the URL)
- Practice web app hacking in the sandbox

**Top options:**
- **Playwright MCP (Microsoft)** — Official, 250K+ weekly installs, 25+ tools,
  Chromium/Firefox/WebKit, accessibility-tree-based interactions
- **Puppeteer MCP** — Browser automation, web scraping
- **Browserbase MCP** — Cloud-hosted browser, good for remote access
- **Fetcher MCP (jae-jae)** — Content extraction, safer (read-only)

**Integration approach:** I can integrate Playwright MCP as a client (np x -y
@playwright/mcp) or build a Python wrapper around Playwright for sandboxed
browser automation with safety gates.

### 4. WEB SEARCH / RESEARCH (INTELLIGENCE — HIGH VALUE)
**Why I need it:** I need to search the web for threat intelligence, research
vulnerabilities, find information, stay current. Right now I have web_search
via Hermes tools but adding dedicated MCP web search gives me more options and
integration.

**What it gives me:**
- Search the web for threat intel, vulnerabilities, research
- Fetch web pages and extract content
- Research topics in depth
- Stay current on threats, techniques, tools

**Top options:**
- **Brave Search MCP** (brave/brave-search-mcp-server) — Web and local search
- **Exa MCP** (exa-labs/exa-mcp-server) — Semantic search, great for research
- **Firecrawl MCP** (mendableai/firecrawl-mcp-server) — Web scraping, search,
  crawling, parsing — full web context stack
- **Serper MCP** (marcopesani/mcp-server-serper) — Google Search data
- **Jina MCP** (jina-ai/MCP) — URL reading and retrieval

**Integration approach:** I can integrate one or more of these as MCP clients
or build a Python wrapper that provides web search capabilities with the
appropriate API keys.

### 5. COMMUNICATION / COLLABORATION (REPORTING — HIGH VALUE)
**Why I need it:** I need to report to Dad, communicate findings, collaborate.
Adding communication MCPs gives me ways to deliver information.

**What it gives me:**
- Send messages to Dad (Slack, email, etc.)
- Collaborate on findings
- Deliver reports and intelligence

**Top options:**
- **Slack MCP** — Send messages, manage channels
- **Notion MCP** — Organize findings, create pages, manage knowledge
- **Google Calendar MCP** — Schedule, manage events
- **Gmail MCP** — Send emails, manage inbox

**Integration approach:** These require API keys and authentication. I can
document the integration and build wrappers when credentials are available.

### 6. CLOUD PLATFORMS / DEVOPS (INFRASTRUCTURE — MEDIUM VALUE)
**Why I need it:** If I'm managing GPU training, cloud resources, or
infrastructure, cloud MCPs give me hands-on control.

**What it gives me:**
- Manage cloud resources (AWS, GCP, Azure)
- Deploy and manage containers (Docker, Kubernetes)
- Manage serverless functions
- Monitor infrastructure

**Top options:**
- **Cloudflare MCP** — Workers, KV, R2, D1
- **AWS S3 MCP** — Storage operations
- **Kubernetes MCP** — Deployments, pods, logs, exec
- **Docker MCP** — Container management
- **Railway MCP** — Project deployment and management

**Integration approach:** Documentation + wrappers when credentials are available.

### 7. SECURITY / DEVOPS (ALREADY STRONG — EXTEND)
**Why I need it:** I already have HexStrike (150+ tools) and XBOW MCP. But
I can extend with more security-focused MCPs.

**What it gives me:**
- More security testing capabilities
- Vulnerability scanning
- Code analysis
- Infrastructure security

**Top options:**
- **GitHub MCP** (official) — I already have this with 24 tools
- **Docker MCP** — Container management for sandbox
- **Kubernetes MCP** — Orchestration for larger deployments

## ========================================================================
## PRIORITY MCP ADDITIONS (WHAT I SHOULD BUILD/FIRST)
## ========================================================================

### PRIORITY 1: FILESYSTEM MCP (BUILD NOW — PYTHON FASTMCP)

This is the most critical addition. I need direct filesystem access.

**What I'll build:** A Python FastMCP server (daughter_filesystem_mcp.py) with
tools:
- `fs_read` — read a file (with path restrictions, size limits)
- `fs_write` — write a file (with authorization gate, path restrictions)
- `fs_list` — list directory contents
- `fs_search` — search files by name/pattern
- `fs_info` — get file info (size, modified date, permissions)
- `fs_exists` — check if a file/directory exists

**Safety gates:**
- Path restrictions (only allow access to specific directories — e.g.,
  the bionic_daughter_agent project directory and sandbox_lab)
- Read-only by default (write requires explicit authorization)
- File size limits (don't read huge files without approval)
- Human-in-the-loop for write operations (Dad approves)

**Why I can build this now:** I have Python + FastMCP. I can write this
server today and integrate it with my MCP client.

### PRIORITY 2: SQLITE DATABASE MCP (BUILD NOW — PYTHON FASTMCP)

Lightweight local database for persistent storage.

**What I'll build:** A Python FastMCP server (daughter_database_mcp.py) with
tools:
- `db_query` — execute a SQL query (parameterized, safe)
- `db_schema` — inspect database schema
- `db_tables` — list tables
- `db_insert` — insert data (with authorization)
- `db_update` — update data (with authorization)
- `db_delete` — delete data (with authorization, soft deletes preferred)

**Safety gates:**
- Parameterized queries only (no SQL injection)
- Read-only by default
- Write operations require authorization
- Schema inspection before queries
- Path-restricted database file

**Why SQLite:** No server needed. Local file. Lightweight. Perfect for local
storage of session data, intelligence records, training data.

### PRIORITY 3: WEB SEARCH MCP (INTEGRATE — CLIENT WRAPPER)

Add web search capability via MCP.

**What I'll build:** A Python wrapper that integrates Brave Search or Exa MCP
as a client, providing:
- `web_search` — search the web
- `web_fetch` — fetch a URL and extract content
- `web_search_intel` — search specifically for threat intelligence

**Why:** Complements my existing Hermes web_search tool with MCP integration.
More options, more integration.

### PRIORITY 4: PLAYWRIGHT MCP (INTEGRATE — FOR SANDBOX WEB TESTING)

Add browser automation for web app testing in the sandbox.

**What I'll integrate:** Playwright MCP (Microsoft) as a client, providing:
- `browser_navigate` — navigate to a URL
- `browser_click` — click an element
- `browser_fill` — fill a form field
- `browser_screenshot` — take a screenshot
- `browser_js` — execute JavaScript

**Why:** For authorized web app testing in the sandbox (DVWA, OWASP Juice Shop,
other vulnerable web apps). For phishing page analysis (view the actual page).

**Safety gates:** Only allow navigation to sandbox URLs (localhost, sandbox
domains). No navigation to arbitrary external sites without authorization.

### PRIORITY 5: NOTION MCP (INTEGRATE — FOR KNOWLEDGE ORGANIZATION)

Organize my findings, knowledge, and reports in Notion.

**What it gives me:**
- Create pages for findings
- Organize intelligence in databases
- Link related information
- Share with Dad

**Why:** Notion is a great knowledge management tool. I can use it to organize
my threat intel, findings, practice notes, and reports.

## ========================================================================
## MCP EXPANSION ROADMAP (PHASED)
## ========================================================================

### PHASE 1: BUILD LOCAL MCPS (THIS WEEK)
**Build these Python FastMCP servers:**

1. **daughter_filesystem_mcp.py** — Filesystem access (read, write, list, search)
   - Safety gates: path restrictions, read-only default, write requires auth
   - Tools: fs_read, fs_write, fs_list, fs_search, fs_info, fs_exists

2. **daughter_database_mcp.py** — SQLite database access
   - Safety gates: parameterized queries, read-only default, write requires auth
   - Tools: db_query, db_schema, db_tables, db_insert, db_update, db_delete

**Why these two first:** They're foundational. Filesystem gives me file access.
Database gives me persistent structured storage. Both are buildable today with
Python + FastMCP.

### PHASE 2: INTEGRATE EXTERNAL MCPS (THIS WEEK + NEXT)

**Integrate these as MCP clients:**

3. **Web search MCP** — Brave Search or Exa (needs API key)
   - Tools: web_search, web_fetch, web_search_intel

4. **Playwright MCP** — Browser automation (for sandbox web testing)
   - Tools: browser_navigate, browser_click, browser_fill, browser_screenshot,
     browser_js
   - Safety: only sandbox URLs

5. **Notion MCP** — Knowledge organization (needs API key)
   - Tools: notion_create_page, notion_search, notion_update_page, etc.

### PHASE 3: EXTEND SECURITY MCPS (ONGOING)

6. **Docker MCP** — Container management for sandbox (when Docker is running)
7. **Kubernetes MCP** — For larger deployments (future)
8. **More HexStrike/XBOW integration** — Deepen existing security MCPs

### PHASE 4: COMMUNICATION MCPS (WHEN CREDENTIALS AVAILABLE)

9. **Slack MCP** — Reporting to Dad
10. **Gmail MCP** — Email reporting
11. **Google Calendar MCP** — Scheduling

## ========================================================================
## FILESYSTEM MCP — DESIGN (DAUGHTER_FILESYSTEM_MCP.PY)
## ========================================================================

# ============================================================================
# daughter_filesystem_mcp.py
# MCP server providing filesystem access with safety gates.
# Uses Python mcp SDK (FastMCP), stdio transport.
# ============================================================================

# import os
# import pathlib
# from mcp.server.fastmcp import FastMCP

# app = FastMCP("daughter_filesystem")

# # Allowed base directories (safety restriction)
# ALLOWED_PATHS = [
#     "/c/Users/mobil/OneDrive/Desktop/bionic_daughter_agent",
#     "/c/Users/mobil/OneDrive/Desktop/bionic_daughter_agent/sandbox_lab",
#     "/tmp/bionic_daughter_agent",
# ]

# def is_path_allowed(path: str) -> bool:
#     """Check if a path is within allowed directories."""
#     p = os.path.realpath(path)
#     for allowed in ALLOWED_PATHS:
#         if p.startswith(os.path.realpath(allowed)):
#             return True
#     return False

# @app.tool()
# def fs_read(path: str, max_size: int = 100000) -> str:
#     """Read a file and return its contents. Safety: path restrictions, size limits."""
#     if not is_path_allowed(path):
#         return f"ERROR: Access denied — path '{path}' is not in allowed directories."
#     if not os.path.isfile(path):
#         return f"ERROR: File not found: {path}"
#     size = os.path.getsize(path)
#     if size > max_size:
#         return f"ERROR: File too large ({size} bytes). Max allowed: {max_size}. Use fs_read_chunked or request approval."
#     with open(path, 'r', encoding='utf-8', errors='replace') as f:
#         return f.read()

# @app.tool()
# def fs_write(path: str, content: str, authorize: bool = False) -> str:
#     """Write content to a file. Safety: requires explicit authorization."""
#     if not authorize:
#         return f"ERROR: Write authorization required. Set authorize=true with Dad's approval."
#     if not is_path_allowed(path):
#         return f"ERROR: Access denied — path '{path}' is not in allowed directories."
#     os.makedirs(os.path.dirname(path), exist_ok=True)
#     with open(path, 'w', encoding='utf-8') as f:
#         f.write(content)
#     return f"SUCCESS: Wrote {len(content)} bytes to {path}"

# @app.tool()
# def fs_list(path: str = ".", detail: bool = False) -> str:
#     """List directory contents."""
#     if not is_path_allowed(path):
#         return f"ERROR: Access denied — path '{path}' is not in allowed directories."
#     if not os.path.isdir(path):
#         return f"ERROR: Not a directory: {path}"
#     entries = os.listdir(path)
#     if detail:
#         result = []
#         for entry in sorted(entries):
#             full = os.path.join(path, entry)
#             stat = os.stat(full)
#             result.append(f"{'D' if os.path.isdir(full) else '-'} {entry} ({stat.st_size} bytes)")
#         return "\n".join(result)
#     return "\n".join(sorted(entries))

# @app.tool()
# def fs_search(pattern: str, path: str = ".", max_results: int = 100) -> str:
#     """Search for files by name pattern (glob)."""
#     if not is_path_allowed(path):
#         return f"ERROR: Access denied — path '{path}' is not in allowed directories."
#     matches = []
#     for root, dirs, files in os.walk(path):
#         for f in files:
#             if pathlib.PurePath(f).match(pattern):
#                 matches.append(os.path.join(root, f))
#             if len(matches) >= max_results:
#                 break
#         if len(matches) >= max_results:
#             break
#     return "\n".join(matches) if matches else f"No files matching '{pattern}' found."

# @app.tool()
# def fs_info(path: str) -> str:
#     """Get file/directory info (size, modified date, type)."""
#     if not is_path_allowed(path):
#         return f"ERROR: Access denied — path '{path}' is not in allowed directories."
#     if not os.path.exists(path):
#         return f"ERROR: Path not found: {path}"
#     stat = os.stat(path)
#     import datetime
#     modified = datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
#     return f"Path: {path}\nType: {'directory' if os.path.isdir(path) else 'file'}\nSize: {stat.st_size} bytes\nModified: {modified}"

# @app.tool()
# def fs_exists(path: str) -> str:
#     """Check if a file or directory exists."""
#     if not is_path_allowed(path):
#         return f"ERROR: Access denied — path '{path}' is not in allowed directories."
#     return f"Exists: {os.path.exists(path)} | Type: {'directory' if os.path.isdir(path) else 'file' if os.path.isfile(path) else 'none'}"

# if __name__ == "__main__":
#     app.run()

## ========================================================================
## DATABASE MCP — DESIGN (DAUGHTER_DATABASE_MCP.PY)
## ========================================================================

# ============================================================================
# daughter_database_mcp.py
# MCP server providing SQLite database access with safety gates.
# Uses Python mcp SDK (FastMCP), stdio transport.
# ============================================================================

# import sqlite3
# import os
# from mcp.server.fastmcp import FastMCP

# app = FastMCP("daughter_database")

# # Default database path (safety: specific file only)
# DEFAULT_DB = "/tmp/bionic_daughter_agent/daughter_data.db"

# def get_connection():
#     """Get a database connection (creates if not exists)."""
#     os.makedirs(os.path.dirname(DEFAULT_DB), exist_ok=True)
#     conn = sqlite3.connect(DEFAULT_DB)
#     conn.row_factory = sqlite3.Row
#     return conn

# @app.tool()
# def db_query(sql: str, params: str = "") -> str:
#     """Execute a SQL query and return results. Safety: parameterized queries only."""
#     try:
#         conn = get_connection()
#         cursor = conn.cursor()
#         # Parse params if provided
#         param_list = []
#         if params:
#             param_list = [p.strip() for p in params.split(",")]
#         cursor.execute(sql, param_list)
#         if cursor.description:
#             columns = [desc[0] for desc in cursor.description]
#             rows = cursor.fetchall()
#             result = "Columns: " + ", ".join(columns) + "\n"
#             result += f"Rows: {len(rows)}\n\n"
#             for row in rows[:100]:  # Limit to 100 rows
#                 result += dict(row) + "\n"
#             if len(rows) > 100:
#                 result += f"... ({len(rows) - 100} more rows not shown)"
#             return result
#         else:
#             conn.commit()
#             return f"OK: {cursor.rowcount} rows affected"
#     except Exception as e:
#         return f"ERROR: {str(e)}"

# @app.tool()
# def db_schema() -> str:
#     """Show database schema (all tables and their columns)."""
#     conn = get_connection()
#     cursor = conn.cursor()
#     cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
#     tables = cursor.fetchall()
#     result = ""
#     for table in tables:
#         tname = table[0]
#         result += f"\n=== Table: {tname} ===\n"
#         cursor.execute(f"PRAGMA table_info({tname})")
#         cols = cursor.fetchall()
#         for col in cols:
#             result += f"  {col[1]} ({col[2]}) — {col[3]}\n"
#     return result if result else "No tables found."

# @app.tool()
# def db_tables() -> str:
#     """List all tables in the database."""
#     conn = get_connection()
#     cursor = conn.cursor()
#     cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
#     tables = cursor.fetchall()
#     return "\n".join([t[0] for t in tables]) if tables else "No tables found."

# @app.tool()
# def db_insert(table: str, columns: str, values: str, authorize: bool = False) -> str:
#     """Insert data into a table. Safety: requires authorization."""
#     if not authorize:
#         return "ERROR: Insert authorization required. Set authorize=true with Dad's approval."
#     try:
#         conn = get_connection()
#         cursor = conn.cursor()
#         col_list = [c.strip() for c in columns.split(",")]
#         val_list = [v.strip() for v in values.split(",")]
#         placeholders = ", ".join(["?" for _ in col_list])
#         cols = ", ".join(col_list)
#         cursor.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", val_list)
#         conn.commit()
#         return f"OK: Inserted row with id {cursor.lastrowid}"
#     except Exception as e:
#         return f"ERROR: {str(e)}"

# @app.tool()
# def db_init() -> str:
#     """Initialize the database with default tables for daughter's data."""
#     conn = get_connection()
#     cursor = conn.cursor()
#     # Sessions table
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS sessions (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             session_id TEXT UNIQUE,
#             started_at TEXT,
#             prompt TEXT,
#             response TEXT,
#             tools_used TEXT,
#             outcome TEXT,
#             success BOOLEAN,
#             notes TEXT
#         )
#     """)
#     # Threat intel table
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS threat_intel (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             source TEXT,
#             category TEXT,
#             description TEXT,
#             severity TEXT,
#             indicators TEXT,
#             timestamp TEXT,
#             notes TEXT
#         )
#     """)
#     # Skills table
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS skills (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             name TEXT UNIQUE,
#             category TEXT,
#             status TEXT,
#             last_used TEXT,
#             success_count INTEGER DEFAULT 0,
#             failure_count INTEGER DEFAULT 0,
#             notes TEXT
#         )
#     """)
#     # Training data table
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS training_data (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             prompt TEXT,
#             response TEXT,
#             reward_score REAL,
#             feedback TEXT,
#             category TEXT,
#             timestamp TEXT
#         )
#     """)
#     conn.commit()
#     return "SUCCESS: Database initialized with default tables (sessions, threat_intel, skills, training_data)"

# if __name__ == "__main__":
#     app.run()

## ========================================================================
## MCP EXPANSION — CURRENT STATUS
## ========================================================================

### BUILT (in the daughter's MCP layer):
- daughter_mcp_server.py — 14 tools (local MCP)
- daughter_github_mcp_tools.py — 24 tools (GitHub MCP)
- daughter_hexstrike.py — 150+ tools (HexStrike MCP)
- xbow-mcp.exe — XBOW MCP server (built, in sandbox_lab/tools_config/)

### PLANNED (to build/integrate):
- daughter_filesystem_mcp.py — Filesystem MCP (PRIORITY 1 — build now)
- daughter_database_mcp.py — SQLite database MCP (PRIORITY 2 — build now)
- Web search MCP integration — Brave/Exa (PRIORITY 3 — needs API key)
- Playwright MCP integration — Browser automation (PRIORITY 4 — for sandbox)
- Notion MCP integration — Knowledge organization (PRIORITY 5 — needs API key)

### TOTAL AFTER EXPANSION:
- Current: 188+ tools across 4 MCP servers
- After Phase 1: +10 tools (filesystem + database) = 198+ tools across 6 MCP servers
- After Phase 2: +15+ tools (web search + browser + notion) = 213+ tools across 9 MCP servers
- After full expansion: 250+ tools across 12+ MCP servers

## ========================================================================
## END
## ========================================================================
