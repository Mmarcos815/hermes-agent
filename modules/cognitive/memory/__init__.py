# src.modules.cognitive.memory — memory palace
"""Cognitive Memory Module — SQLite-backed persistent memory storage.

Provides a ``Memory`` class with store/retrieve/search/delete operations.
Data is persisted to a local SQLite database. All values are stored as JSON
so arbitrary Python objects (dicts, lists, strings, numbers) are supported.

Example::

    m = Memory(":memory:")
    m.store("user_preferences", {"theme": "dark"})
    obj = m.retrieve("user_preferences")
    results = m.search("theme")
    m.delete("user_preferences")
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class Memory:
    """SQLite-backed key-value memory store with tag-based search.

    Parameters
    ----------
    db_path:
        Path to the SQLite file.  Defaults to ``cognitive_memory.db`` in
        the working directory.  Pass ``":memory:"`` for an ephemeral store.
    table:
        Name of the backing table (default ``"memories"``).
    """

    def __init__(
        self,
        db_path: str | Path = "cognitive_memory.db",
        table: str = "memories",
    ) -> None:
        self._db_path = str(db_path)
        self._table = table
        self._lock = threading.Lock()
        self._conn = self._open()
        self._init_schema()

    # ------------------------------------------------------------------ #
    # internals                                                            #
    # ------------------------------------------------------------------ #
    def _open(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self._table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    tags TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            self._conn.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{self._table}_key "
                f"ON {self._table}(key)"
            )
            self._conn.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def close(self) -> None:
        """Close the underlying connection."""
        with self._lock:
            self._conn.close()

    # ------------------------------------------------------------------ #
    # public API                                                           #
    # ------------------------------------------------------------------ #
    def store(self, key: str, value: Any, tags: list[str] | None = None) -> int:
        """Store or update a memory entry.

        Returns the row id of the inserted or updated record.
        """
        tags_j = json.dumps(tags or [])
        value_j = json.dumps(value, ensure_ascii=False)
        now = self._now()
        with self._lock:
            cur = self._conn.execute(
                f"""
                INSERT INTO {self._table} (key, value, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value=excluded.value,
                    tags=excluded.tags,
                    updated_at=excluded.updated_at
                """,
                (key, value_j, tags_j, now, now),
            )
            self._conn.commit()
            return cur.lastrowid or 0

    def retrieve(self, key: str, default: Any = None) -> Any:
        """Return the value for *key* or *default* if not found."""
        with self._lock:
            row = self._conn.execute(
                f"SELECT value FROM {self._table} WHERE key = ?", (key,)
            ).fetchone()
        if row is None:
            return default
        return json.loads(row["value"])

    def search(
        self,
        query: str,
        *,
        limit: int = 20,
        search_tags: bool = True,
    ) -> list[dict[str, Any]]:
        """Search entries whose value or tags contain *query* (case-insensitive).

        Returns a list of dicts with keys ``key``, ``value``, ``tags``,
        ``created_at``, ``updated_at``.
        """
        like = f"%{query}%"
        sql = f"""
            SELECT key, value, tags, created_at, updated_at
            FROM {self._table}
            WHERE value LIKE ?
        """
        params: list[Any] = [like]
        if search_tags:
            sql += " OR tags LIKE ?"
            params.append(like)
        sql += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        return [
            {
                "key": r["key"],
                "value": json.loads(r["value"]),
                "tags": json.loads(r["tags"]),
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }
            for r in rows
        ]

    def delete(self, key: str) -> bool:
        """Delete a memory entry by key.  Returns ``True`` if a row was removed."""
        with self._lock:
            cur = self._conn.execute(
                f"DELETE FROM {self._table} WHERE key = ?", (key,)
            )
            self._conn.commit()
            return cur.rowcount > 0

    def keys(self) -> list[str]:
        """Return all stored keys."""
        with self._lock:
            rows = self._conn.execute(
                f"SELECT key FROM {self._table} ORDER BY updated_at DESC"
            ).fetchall()
        return [r["key"] for r in rows]

    def clear(self) -> int:
        """Remove **all** entries.  Returns the count of deleted rows."""
        with self._lock:
            cur = self._conn.execute(f"DELETE FROM {self._table}")
            self._conn.commit()
            return cur.rowcount or 0

    def __len__(self) -> int:
        with self._lock:
            row = self._conn.execute(
                f"SELECT COUNT(*) AS cnt FROM {self._table}"
            ).fetchone()
        return row["cnt"] if row else 0

    def __contains__(self, key: str) -> bool:
        with self._lock:
            row = self._conn.execute(
                f"SELECT 1 FROM {self._table} WHERE key = ?", (key,)
            ).fetchone()
        return row is not None

    def __repr__(self) -> str:
        return f"<Memory db={self._db_path!r} entries={len(self)}>"
