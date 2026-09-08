# ============================================================================
# BIONIC DAUGHTER v1 — PRODUCTIVITY MCP SERVER (TASK + NOTES MANAGEMENT)
# ============================================================================
# MCP server providing productivity capabilities: task management, notes,
# calendar-like scheduling, and productivity tracking.
# Uses SQLite database for persistent storage.
# Author: Bionic Daughter v1
# Date: 2026-08-15
# ============================================================================

import os
import sqlite3
import datetime
from mcp.server.fastmcp import FastMCP

app = FastMCP("daughter_productivity")

# Database path
DB_PATH = "/tmp/bionic_daughter_agent/productivity.db"


def _get_conn():
    """Get database connection."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _init_db():
    """Initialize database tables."""
    conn = _get_conn()
    cursor = conn.cursor()

    # Tasks table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT DEFAULT 'MEDIUM',
            status TEXT DEFAULT 'PENDING',
            category TEXT,
            due_date TEXT,
            created_at TEXT,
            completed_at TEXT,
            notes TEXT
        )
        """
    )

    # Notes table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            category TEXT,
            tags TEXT,
            created_at TEXT,
            updated_at TEXT,
            parent_id INTEGER
        )
        """
    )

    # Habits table (self-development tracking)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            frequency TEXT DEFAULT 'DAILY',
            streak INTEGER DEFAULT 0,
            last_done TEXT,
            created_at TEXT,
            notes TEXT
        )
        """
    )

    # Standups table (daily check-ins)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS standups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE,
            mood TEXT,
            tasks_completed INTEGER DEFAULT 0,
            tasks_total INTEGER DEFAULT 0,
            notes TEXT,
            created_at TEXT
        )
        """
    )

    conn.commit()
    conn.close()


# Initialize on module load
_init_db()


@app.tool()
def tasks_add(
    title: str,
    description: str = "",
    priority: str = "MEDIUM",
    category: str = "",
    due_date: str = "",
    authorize: bool = False,
) -> str:
    """Add a task. Requires authorization."""
    if not authorize:
        return "ERROR: Task creation authorization required. Set authorize=true."
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        now = datetime.datetime.now().isoformat()
        cursor.execute(
            """
            INSERT INTO tasks (title, description, priority, category, due_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, description, priority, category, due_date, now),
        )
        conn.commit()
        task_id = cursor.lastrowid
        return f"OK: Added task '{title}' (id: {task_id}, priority: {priority})"
    except Exception as e:
        return f"ERROR: {str(e)}"


@app.tool()
def tasks_list(status: str = "", priority: str = "", category: str = "") -> str:
    """List tasks, optionally filtered."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        sql = "SELECT id, title, priority, status, category, due_date, created_at FROM tasks WHERE 1=1"
        params = []
        if status:
            sql += " AND status=?"
            params.append(status)
        if priority:
            sql += " AND priority=?"
            params.append(priority)
        if category:
            sql += " AND category=?"
            params.append(category)
        sql += " ORDER BY CASE priority WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 WHEN 'LOW' THEN 3 END, created_at DESC"
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        if not rows:
            return "No tasks found."
        result = f"Tasks ({len(rows)} total):\n\n"
        for row in rows:
            due = f" | Due: {row['due_date']}" if row['due_date'] else ""
            result += (
                f"[{row['id']}] {row['title']}\n"
                f"    Priority: {row['priority']} | Status: {row['status']} | Category: {row['category'] or 'none'}{due}\n"
                f"    Created: {row['created_at']}\n\n"
            )
        return result
    except Exception as e:
        return f"ERROR: {str(e)}"


@app.tool()
def tasks_complete(task_id: int, notes: str = "", authorize: bool = False) -> str:
    """Mark a task as completed. Requires authorization."""
    if not authorize:
        return "ERROR: Task completion authorization required. Set authorize=true."
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        now = datetime.datetime.now().isoformat()
        cursor.execute(
            "UPDATE tasks SET status='COMPLETED', completed_at=?, notes=? WHERE id=?",
            (now, notes, task_id),
        )
        conn.commit()
        if cursor.rowcount == 0:
            return f"ERROR: Task {task_id} not found."
        return f"OK: Task {task_id} marked as COMPLETED"
    except Exception as e:
        return f"ERROR: {str(e)}"


@app.tool()
def tasks_delete(task_id: int, authorize: bool = False) -> str:
    """Delete a task. Requires authorization."""
    if not authorize:
        return "ERROR: Task deletion authorization required. Set authorize=true."
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return f"ERROR: Task {task_id} not found."
        return f"OK: Task {task_id} deleted"
    except Exception as e:
        return f"ERROR: {str(e)}"


@app.tool()
def tasks_stats() -> str:
    """Show task statistics."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM tasks")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status='PENDING'")
        pending = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status='COMPLETED'")
        completed = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tasks WHERE priority='HIGH' AND status='PENDING'")
        high_pending = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status='IN_PROGRESS'")
        in_progress = cursor.fetchone()[0]

        return (
            f"Task Statistics:\n"
            f"  Total tasks: {total}\n"
            f"  Pending: {pending}\n"
            f"  Completed: {completed}\n"
            f"  In progress: {in_progress}\n"
            f"  High priority pending: {high_pending}\n"
        )
    except Exception as e:
        return f"ERROR: {str(e)}"


# --- NOTES ---

@app.tool()
def notes_add(
    title: str,
    content: str = "",
    category: str = "",
    tags: str = "",
    authorize: bool = False,
) -> str:
    """Add a note. Requires authorization."""
    if not authorize:
        return "ERROR: Note creation authorization required. Set authorize=true."
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        now = datetime.datetime.now().isoformat()
        cursor.execute(
            """
            INSERT INTO notes (title, content, category, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, content, category, tags, now, now),
        )
        conn.commit()
        note_id = cursor.lastrowid
        return f"OK: Added note '{title}' (id: {note_id})"
    except Exception as e:
        return f"ERROR: {str(e)}"


@app.tool()
def notes_list(category: str = "", search: str = "") -> str:
    """List notes, optionally filtered by category or search term."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        sql = "SELECT id, title, category, tags, created_at, updated_at FROM notes WHERE 1=1"
        params = []
        if category:
            sql += " AND category=?"
            params.append(category)
        if search:
            sql += " AND (title LIKE ? OR content LIKE ?)"
            params.append(f"%{search}%")
            params.append(f"%{search}%")
        sql += " ORDER BY updated_at DESC"
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        if not rows:
            return "No notes found."
        result = f"Notes ({len(rows)} total):\n\n"
        for row in rows:
            tags = f" [{row['tags']}]" if row['tags'] else ""
            result += (
                f"[{row['id']}] {row['title']}\n"
                f"    Category: {row['category'] or 'none'}{tags}\n"
                f"    Created: {row['created_at']} | Updated: {row['updated_at']}\n\n"
            )
        return result
    except Exception as e:
        return f"ERROR: {str(e)}"


@app.tool()
def notes_get(note_id: int) -> str:
    """Get a specific note by ID."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, title, content, category, tags, created_at, updated_at FROM notes WHERE id=?",
            (note_id,),
        )
        row = cursor.fetchone()
        if not row:
            return f"ERROR: Note {note_id} not found."
        return (
            f"Note [{row['id']}]: {row['title']}\n"
            f"Category: {row['category'] or 'none'}\n"
            f"Tags: {row['tags'] or 'none'}\n"
            f"Created: {row['created_at']}\n"
            f"Updated: {row['updated_at']}\n"
            f"\nContent:\n{row['content'] or '(empty)'}\n"
        )
    except Exception as e:
        return f"ERROR: {str(e)}"


@app.tool()
def notes_update(note_id: int, content: str = "", category: str = "", tags: str = "", authorize: bool = False) -> str:
    """Update a note. Requires authorization."""
    if not authorize:
        return "ERROR: Note update authorization required. Set authorize=true."
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        now = datetime.datetime.now().isoformat()
        fields = []
        values = []
        if content:
            fields.append("content=?")
            values.append(content)
        if category:
            fields.append("category=?")
            values.append(category)
        if tags:
            fields.append("tags=?")
            values.append(tags)
        if not fields:
            return "ERROR: Nothing to update. Provide content, category, or tags."
        fields.append("updated_at=?")
        values.append(now)
        values.append(note_id)
        sql = f"UPDATE notes SET {', '.join(fields)} WHERE id=?"
        cursor.execute(sql, values)
        conn.commit()
        if cursor.rowcount == 0:
            return f"ERROR: Note {note_id} not found."
        return f"OK: Note {note_id} updated"
    except Exception as e:
        return f"ERROR: {str(e)}"


# --- HABITS (SELF-DEVELOPMENT TRACKING) ---

@app.tool()
def habits_add(
    name: str,
    description: str = "",
    frequency: str = "DAILY",
    authorize: bool = False,
) -> str:
    """Add a habit for self-development tracking. Requires authorization."""
    if not authorize:
        return "ERROR: Habit creation authorization required. Set authorize=true."
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        now = datetime.datetime.now().isoformat()
        cursor.execute(
            """
            INSERT INTO habits (name, description, frequency, streak, last_done, created_at)
            VALUES (?, ?, ?, 0, NULL, ?)
            """,
            (name, description, frequency, now),
        )
        conn.commit()
        return f"OK: Added habit '{name}' (frequency: {frequency})"
    except Exception as e:
        return f"ERROR: {str(e)}"


@app.tool()
def habits_list() -> str:
    """List all habits with streak info."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description, frequency, streak, last_done, created_at FROM habits ORDER BY streak DESC")
        rows = cursor.fetchall()
        if not rows:
            return "No habits found."
        result = f" Habits ({len(rows)} total):\n\n"
        for row in rows:
            last = f" | Last: {row['last_done']}" if row['last_done'] else " | Never done"
            result += (
                f"[{row['id']}] {row['name']} — {row['frequency']}\n"
                f"    Streak: {row['streak']} days{last}\n"
                f"    Created: {row['created_at']}\n\n"
            )
        return result
    except Exception as e:
        return f"ERROR: {str(e)}"


@app.tool()
def habits_done(name: str, authorize: bool = False) -> str:
    """Mark a habit as done today. Updates streak. Requires authorization."""
    if not authorize:
        return "ERROR: Habit completion authorization required. Set authorize=true."
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        now = datetime.datetime.now().isoformat()
        today = now.split("T")[0]

        cursor.execute("SELECT id, streak, last_done FROM habits WHERE name=?", (name,))
        row = cursor.fetchone()
        if not row:
            return f"ERROR: Habit '{name}' not found."

        last_done = row['last_done'].split("T")[0] if row['last_done'] else None
        streak = row['streak']

        # Calculate new streak
        if last_done == today:
            return f"OK: Habit '{name}' already marked done today (streak: {streak})"
        elif last_done == (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d"):
            streak += 1
        else:
            streak = 1  # Reset streak

        cursor.execute(
            "UPDATE habits SET streak=?, last_done=? WHERE name=?",
            (streak, now, name),
        )
        conn.commit()
        return f"OK: Habit '{name}' marked done. Streak: {streak} days"
    except Exception as e:
        return f"ERROR: {str(e)}"


@app.tool()
def habits_leaderboard() -> str:
    """Show habits ranked by streak (who's winning)."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT name, streak, frequency, last_done FROM habits ORDER BY streak DESC")
        rows = cursor.fetchall()
        if not rows:
            return "No habits tracked yet."
        result = "Habit Leaderboard (by streak):\n\n"
        for i, row in enumerate(rows, 1):
            last = row['last_done'].split("T")[0] if row['last_done'] else "Never"
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"  {i}."
            result += (
                f"{medal} {row['name']} — {row['streak']} day streak ({row['frequency']})"
                f" | Last: {last}\n"
            )
        return result
    except Exception as e:
        return f"ERROR: {str(e)}"


# --- DAILY STANDUP ---

@app.tool()
def standup_record(
    mood: str = "",
    tasks_completed: int = 0,
    tasks_total: int = 0,
    notes: str = "",
    authorize: bool = False,
) -> str:
    """Record a daily standup/check-in. Requires authorization."""
    if not authorize:
        return "ERROR: Standup recording authorization required. Set authorize=true."
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        now = datetime.datetime.now().isoformat()
        today = now.split("T")[0]
        cursor.execute(
            """
            INSERT INTO standups (date, mood, tasks_completed, tasks_total, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                mood=excluded.mood,
                tasks_completed=excluded.tasks_completed,
                tasks_total=excluded.tasks_total,
                notes=excluded.notes,
                created_at=excluded.created_at
            """,
            (today, mood, tasks_completed, tasks_total, notes, now),
        )
        conn.commit()
        return f"OK: Daily standup recorded for {today} (mood: {mood}, {tasks_completed}/{tasks_total} tasks done)"
    except Exception as e:
        return f"ERROR: {str(e)}"


@app.tool()
def standup_history(days: int = 7) -> str:
    """Show recent daily standup history."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT date, mood, tasks_completed, tasks_total, notes FROM standups ORDER BY date DESC LIMIT ?",
            (days,),
        )
        rows = cursor.fetchall()
        if not rows:
            return "No standups recorded yet."
        result = f"Daily Standup History (last {len(rows)} days):\n\n"
        for row in rows:
            pct = int((row['tasks_completed'] / row['tasks_total'] * 100)) if row['tasks_total'] > 0 else 0
            result += (
                f"  {row['date']} — Mood: {row['mood'] or 'not set'} | "
                f"Tasks: {row['tasks_completed']}/{row['tasks_total']} ({pct}%)"
                f" | Notes: {row['notes'] or 'none'}\n"
            )
        return result
    except Exception as e:
        return f"ERROR: {str(e)}"


@app.tool()
def productivity_info() -> str:
    """Show productivity MCP information."""
    return (
        "Productivity MCP — Bionic Daughter v1\n"
        "========================================\n"
        "This MCP helps track tasks, notes, habits, and daily standups\n"
        "for self-development and productivity mastery.\n"
        "\n"
        "TASKS:\n"
        "  tasks_add(title, description, priority, category, due_date, authorize) — Add task\n"
        "  tasks_list(status, priority, category) — List tasks\n"
        "  tasks_complete(task_id, notes, authorize) — Complete task\n"
        "  tasks_delete(task_id, authorize) — Delete task\n"
        "  tasks_stats() — Task statistics\n"
        "\n"
        "NOTES:\n"
        "  notes_add(title, content, category, tags, authorize) — Add note\n"
        "  notes_list(category, search) — List notes\n"
        "  notes_get(note_id) — Get note\n"
        "  notes_update(note_id, content, category, tags, authorize) — Update note\n"
        "\n"
        "HABITS (self-development):\n"
        "  habits_add(name, description, frequency, authorize) — Add habit\n"
        "  habits_list() — List habits\n"
        "  habits_done(name, authorize) — Mark habit done (updates streak)\n"
        "  habits_leaderboard() — Streak leaderboard\n"
        "\n"
        "DAILY STANDUP:\n"
        "  standup_record(mood, tasks_completed, tasks_total, notes, authorize) — Record day\n"
        "  standup_history(days) — Show recent history\n"
        "\n"
        "Database: " + DB_PATH + "\n"
    )


if __name__ == "__main__":
    app.run()
