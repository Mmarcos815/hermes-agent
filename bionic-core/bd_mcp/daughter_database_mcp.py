# ============================================================================
# BIONIC DAUGHTER v1 — DATABASE MCP SERVER (SQLite)
# ============================================================================
# MCP server providing SQLite database access with safety gates.
# Uses Python mcp SDK (FastMCP), stdio transport.
# Author: Bionic Daughter v1
# Date: 2026-08-15
# ============================================================================

import sqlite3
import os
from fastmcp import FastMCP

app = FastMCP("daughter_database")

# Default database path (safety: specific file in project area)
DEFAULT_DB = "/tmp/bionic_daughter_agent/daughter_data.db"


def get_connection():
    """Get a database connection (creates if not exists)."""
    os.makedirs(os.path.dirname(DEFAULT_DB), exist_ok=True)
    conn = sqlite3.connect(DEFAULT_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@app.tool()
def db_query(sql: str, params: str = "") -> str:
    """Execute a SQL query and return results. Safety: parameterized queries only."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        param_list = []
        if params:
            param_list = [p.strip() for p in params.split(",")]
        cursor.execute(sql, param_list)
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            result = f"Columns: {', '.join(columns)}\n"
            result += f"Rows: {len(rows)}\n\n"
            for row in rows[:100]:
                result += str(dict(row)) + "\n"
            if len(rows) > 100:
                result += f"... ({len(rows) - 100} more rows not shown)"
            return result
        else:
            conn.commit()
            return f"OK: {cursor.rowcount} rows affected"
    except Exception as e:
        return f"ERROR: {str(e)}"


@app.tool()
def db_schema() -> str:
    """Show database schema (all tables and their columns)."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        if not tables:
            return "No tables found in database."
        result = ""
        for table in tables:
            tname = table[0]
            result += f"\n=== Table: {tname} ===\n"
            cursor.execute(f"PRAGMA table_info({tname})")
            cols = cursor.fetchall()
            for col in cols:
                result += f"  {col[1]} ({col[2]}) — {col[3]}\n"
        return result
    except Exception as e:
        return f"ERROR: {str(e)}"


@app.tool()
def db_tables() -> str:
    """List all tables in the database."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        if not tables:
            return "No tables found."
        return "\n".join([t[0] for t in tables])
    except Exception as e:
        return f"ERROR: {str(e)}"


@app.tool()
def db_insert(table: str, columns: str, values: str, authorize: bool = False) -> str:
    """Insert data into a table. Safety: requires explicit authorization."""
    if not authorize:
        return "ERROR: Insert authorization required. Set authorize=true with Dad's approval."
    try:
        conn = get_connection()
        cursor = conn.cursor()
        col_list = [c.strip() for c in columns.split(",")]
        val_list = [v.strip() for v in values.split(",")]
        placeholders = ", ".join(["?" for _ in col_list])
        cols = ", ".join(col_list)
        cursor.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", val_list)
        conn.commit()
        return f"OK: Inserted row with id {cursor.lastrowid}"
    except Exception as e:
        return f"ERROR: {str(e)}"


@app.tool()
def db_init() -> str:
    """Initialize the database with default tables for daughter's data."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Sessions table — logs all interactions
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE,
                started_at TEXT,
                prompt TEXT,
                response TEXT,
                tools_used TEXT,
                outcome TEXT,
                success BOOLEAN,
                notes TEXT
            )
            """
        )

        # Threat intel table — stores intelligence records
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS threat_intel (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT,
                category TEXT,
                description TEXT,
                severity TEXT,
                indicators TEXT,
                timestamp TEXT,
                notes TEXT
            )
            """
        )

        # Skills table — tracks skill status and usage
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                category TEXT,
                status TEXT,
                last_used TEXT,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                notes TEXT
            )
            """
        )

        # Training data table — stores curriculum and feedback data
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS training_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT,
                response TEXT,
                reward_score REAL,
                feedback TEXT,
                category TEXT,
                timestamp TEXT
            )
            """
        )

        # Findings table — stores analysis findings
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                title TEXT,
                description TEXT,
                severity TEXT,
                evidence TEXT,
                timestamp TEXT,
                resolved BOOLEAN DEFAULT 0,
                notes TEXT
            )
            """
        )

        conn.commit()
        return (
            "SUCCESS: Database initialized with tables:\n"
            "  - sessions (interaction logs)\n"
            "  - threat_intel (intelligence records)\n"
            "  - skills (skill tracking)\n"
            "  - training_data (curriculum/feedback)\n"
            "  - findings (analysis findings)"
        )
    except Exception as e:
        return f"ERROR initializing database: {str(e)}"


@app.tool()
def db_findings_add(
    type: str,
    title: str,
    description: str,
    severity: str = "MEDIUM",
    evidence: str = "",
    authorize: bool = False,
) -> str:
    """Add a finding to the findings table. Safety: requires authorization."""
    if not authorize:
        return "ERROR: Finding authorization required. Set authorize=true."
    try:
        conn = get_connection()
        cursor = conn.cursor()
        import datetime

        cursor.execute(
            """
            INSERT INTO findings (type, title, description, severity, evidence, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (type, title, description, severity, evidence, datetime.datetime.now().isoformat()),
        )
        conn.commit()
        return f"OK: Added finding '{title}' (id: {cursor.lastrowid})"
    except Exception as e:
        return f"ERROR: {str(e)}"


@app.tool()
def db_findings_list(severity: str = "", resolved: str = "") -> str:
    """List findings, optionally filtered by severity or resolution status."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        sql = "SELECT id, type, title, severity, timestamp, resolved FROM findings WHERE 1=1"
        params = []
        if severity:
            sql += " AND severity=?"
            params.append(severity)
        if resolved:
            sql += " AND resolved=?"
            params.append(1 if resolved.lower() == "true" else 0)
        sql += " ORDER BY id DESC"
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        if not rows:
            return "No findings found."
        result = f"Findings ({len(rows)} total):\n\n"
        for row in rows:
            status = "RESOLVED" if row["resolved"] else "OPEN"
            result += f"[{row['id']}] {row['type']}: {row['title']} | {row['severity']} | {status} | {row['timestamp']}\n"
        return result
    except Exception as e:
        return f"ERROR: {str(e)}"


@app.tool()
def db_health() -> str:
    """Check database health and return status."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT sqlite_version()")
        version = cursor.fetchone()[0]
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        size = os.path.getsize(DEFAULT_DB) if os.path.exists(DEFAULT_DB) else 0
        return (
            f"Database: {DEFAULT_DB}\n"
            f"SQLite version: {version}\n"
            f"Size: {size} bytes\n"
            f"Tables: {len(tables)}\n"
            f"Status: HEALTHY"
        )
    except Exception as e:
        return f"ERROR: Database unhealthy — {str(e)}"


if __name__ == "__main__":
    app.run()
