#!/usr/bin/env python3
"""Bug Bounty Scope Manager — track scope, schedule scans, alert on changes.

Pure standard library (sqlite3, argparse, json). CLI interface:
    add    <domain|ip|url> [scope]   Add item to scope
    remove <domain|ip|url> [scope]   Remove item from scope
    list   [scope]                   List all scope items (optionally filter by type)
    scan                          Run a scan for new subdomains
    schedule <cron> <type> [target]  Schedule recurring scan (daily/weekly)
    notify                          Show pending notifications
    findings [scope]                 List findings
"""

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_NAME = os.environ.get("BB_SCOPE_DB", "scope.db")

SCHEMA_VERSION = 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS scope_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL CHECK(type IN ('domain', 'ip', 'url')),
    target TEXT NOT NULL UNIQUE,
    added_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_scanned TEXT,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS scan_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope_type TEXT,
    target TEXT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    new_subdomains TEXT, -- JSON array
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending','running','completed','failed'))
);

CREATE TABLE IF NOT EXISTS scan_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cron_expr TEXT NOT NULL,          -- 'daily' | 'weekly' | 'custom:cronstring'
    scope_type TEXT DEFAULT 'domain', -- filter scope items to scan
    next_run TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope_item_id INTEGER REFERENCES scope_items(id),
    finding_type TEXT NOT NULL,       -- 'new_subdomain' | 'scope_change' | 'notification'
    description TEXT NOT NULL,
    detected_at TEXT NOT NULL DEFAULT (datetime('now')),
    acknowledged INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

# Subdomain enumeration tools (best-effort, fall back gracefully)
SUBDOMAIN_TOOLS = [
    # (command_template, args_template) — {target} is the domain
    ("subfinder", ["-d", "{target}", "-silent"]),
    ("assetfinder", ["--subs-only", "{target}"]),
    ("amass", ["enum", "-d", "{target}", "-silent"]),
    ("findomain", ["-t", "{target}", "-q"]),
]


def get_db(db_path: str = DB_NAME) -> sqlite3.Connection:
    """Open (and migrate) the SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.execute(
        "INSERT OR IGNORE INTO meta(key, value) VALUES('schema_version', ?)",
        (str(SCHEMA_VERSION),),
    )
    conn.commit()
    return conn


# ── Scope CRUD ────────────────────────────────────────────────────────────────

def add_item(conn: sqlite3.Connection, item_type: str, target: str) -> bool:
    """Add a scope item. Returns True if newly inserted, False if existed."""
    # Normalize
    target = target.strip().lower() if item_type in ("domain", "ip") else target.strip()

    # Validate
    if item_type == "ip":
        if not re.match(r"^\d{1,3}(\.\d{1,3}){3}$", target):
            print(f"[!] Invalid IPv4: {target}")
            return False
    elif item_type == "domain":
        if not re.match(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z]{2,})+$", target):
            print(f"[*] Note: '{target}' doesn't look like a standard domain; adding anyway.")
    elif item_type == "url":
        if not target.startswith(("http://", "https://")):
            print("[!] URL must start with http:// or https://")
            return False

    try:
        conn.execute(
            "INSERT INTO scope_items(type, target) VALUES(?, ?)",
            (item_type, target),
        )
        conn.commit()
        print(f"[+] Added {item_type}: {target}")
        return True
    except sqlite3.IntegrityError:
        # Already exists — reactivate if needed
        existing = conn.execute(
            "SELECT active FROM scope_items WHERE target=?", (target,)
        ).fetchone()
        if existing and not existing["active"]:
            conn.execute(
                "UPDATE scope_items SET active=1 WHERE target=?", (target,)
            )
            conn.commit()
            print(f"[+] Reactivated {item_type}: {target}")
        else:
            print(f"[*] Already in scope: {target}")
        return False


def remove_item(conn: sqlite3.Connection, target: str) -> bool:
    """Soft-delete a scope item."""
    cur = conn.execute(
        "UPDATE scope_items SET active=0 WHERE target=? AND active=1", (target,)
    )
    conn.commit()
    if cur.rowcount:
        print(f"[-] Removed: {target}")
        return True
    print(f"[!] Not found in active scope: {target}")
    return False


def list_items(conn: sqlite3.Connection, item_type: str | None = None) -> list[sqlite3.Row]:
    """List scope items, optionally filtered by type."""
    if item_type:
        rows = conn.execute(
            "SELECT * FROM scope_items WHERE type=? AND active=1 ORDER BY target",
            (item_type,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM scope_items WHERE active=1 ORDER BY type, target"
        ).fetchall()
    return rows


# ── Subdomain Enumeration ────────────────────────────────────────────────────

def enumerate_subdomains(domain: str) -> list[str]:
    """Try each SUBDOMAIN_TOOLS; return sorted unique subdomains found."""
    found: set[str] = set()
    for tool, args_tpl in SUBDOMAIN_TOOLS:
        args = [a.replace("{target}", domain) for a in args_tpl]
        try:
            result = subprocess.run(
                [tool, *args],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0 and result.stdout:
                for line in result.stdout.splitlines():
                    sub = line.strip().lower().lstrip(".")
                    if sub and sub.endswith(domain):
                        found.add(sub)
        except FileNotFoundError:
            continue
        except subprocess.TimeoutExpired:
            print(f"[!] Timeout running {tool} for {domain}")
        except Exception as e:
            print(f"[!] {tool} error: {e}")
    return sorted(found)


def detect_new_subdomains(conn: sqlite3.Connection, domain: str, found: list[str]) -> list[str]:
    """Compare found subdomains against previously known ones; store new ones."""
    # Store known subdomains in scan_history
    existing_rows = conn.execute(
        "SELECT new_subdomains FROM scan_history WHERE target=? AND status='completed' ORDER BY finished_at DESC LIMIT 1",
        (domain,),
    ).fetchone()

    known: set[str] = set()
    if existing_rows and existing_rows["new_subdomains"]:
        known = set(json.loads(existing_rows["new_subdomains"]))

    new_ones = [s for s in found if s not in known]

    # Record findings for new subdomains
    scope_row = conn.execute(
        "SELECT id FROM scope_items WHERE target=? AND type='domain'", (domain,)
    ).fetchone()
    scope_id = scope_row["id"] if scope_row else None

    for sub in new_ones:
        conn.execute(
            "INSERT INTO findings(scope_item_id, finding_type, description) VALUES(?, 'new_subdomain', ?)",
            (scope_id, f"New subdomain discovered: {sub}"),
        )

    conn.commit()
    return new_ones


# ── Scan ──────────────────────────────────────────────────────────────────────

def run_scan(conn: sqlite3.Connection, scope_type: str | None = None) -> int:
    """Run subdomain enumeration on all active scope items of given type."""
    if scope_type:
        items = conn.execute(
            "SELECT * FROM scope_items WHERE type=? AND active=1", (scope_type,)
        ).fetchall()
    else:
        items = conn.execute(
            "SELECT * FROM scope_items WHERE active=1 AND type='domain'"
        ).fetchall()

    if not items:
        print("[!] No active scope items to scan.")
        return 0

    total_new = 0
    for item in items:
        domain = item["target"]
        print(f"\n[*] Scanning {domain}...")

        # Record scan start
        cur = conn.execute(
            "INSERT INTO scan_history(scope_type, target, started_at, status) VALUES(?, ?, datetime('now'), 'running')",
            (item["type"], domain),
        )
        scan_id = cur.lastrowid
        conn.commit()

        try:
            found = enumerate_subdomains(domain)
            new_ones = detect_new_subdomains(conn, domain, found)
            total_new += len(new_ones)

            conn.execute(
                "UPDATE scan_history SET finished_at=datetime('now'), new_subdomains=?, status='completed' WHERE id=?",
                (json.dumps(found), scan_id),
            )
            conn.execute(
                "UPDATE scope_items SET last_scanned=datetime('now') WHERE id=?",
                (item["id"],),
            )
            conn.commit()

            print(f"    Found {len(found)} subdomains, {len(new_ones)} new")
            if new_ones:
                for s in new_ones[:10]:
                    print(f"      + {s}")
                if len(new_ones) > 10:
                    print(f"      ... and {len(new_ones)-10} more")

        except Exception as e:
            conn.execute(
                "UPDATE scan_history SET finished_at=datetime('now'), status='failed' WHERE id=?",
                (scan_id,),
            )
            conn.commit()
            print(f"[!] Scan failed for {domain}: {e}")

    print(f"\n[*] Scan complete. {total_new} new subdomains total.")
    return total_new


# ── Scheduling ────────────────────────────────────────────────────────────────

def schedule_scan(conn: sqlite3.Connection, cron_expr: str, scope_type: str = "domain") -> None:
    """Schedule a recurring scan."""
    # Parse next run
    now = datetime.now(timezone.utc)
    if cron_expr == "daily":
        next_run = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif cron_expr == "weekly":
        days_ahead = 7 - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_run = (now + timedelta(days=days_ahead)).replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        # For custom, just schedule 24h out as default
        next_run = now + timedelta(hours=24)

    conn.execute(
        "INSERT INTO scan_schedule(cron_expr, scope_type, next_run) VALUES(?, ?, ?)",
        (cron_expr, scope_type, next_run.isoformat()),
    )
    conn.commit()
    print(f"[+] Scheduled {cron_expr} scan (next: {next_run.isoformat()})")


def due_scans(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Find schedules that are due for execution."""
    now = datetime.now(timezone.utc).isoformat()
    return conn.execute(
        "SELECT * FROM scan_schedule WHERE active=1 AND next_run <= ?", (now,)
    ).fetchall()


def update_schedule_next(conn: sqlite3.Connection, sched: sqlite3.Row) -> None:
    """Reschedule a scan based on its cron expression."""
    now = datetime.now(timezone.utc)
    if sched["cron_expr"] == "daily":
        next_run = now + timedelta(days=1)
    elif sched["cron_expr"] == "weekly":
        next_run = now + timedelta(weeks=1)
    else:
        next_run = now + timedelta(days=1)

    conn.execute(
        "UPDATE scan_schedule SET next_run=? WHERE id=?",
        (next_run.isoformat(), sched["id"]),
    )
    conn.commit()


# ── Notifications / Findings ──────────────────────────────────────────────────

def get_notifications(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Return unacknowledged findings."""
    return conn.execute(
        "SELECT f.*, s.target as scope_target FROM findings f "
        "LEFT JOIN scope_items s ON f.scope_item_id = s.id "
        "WHERE f.acknowledged=0 ORDER BY f.detected_at DESC"
    ).fetchall()


def show_notifications(conn: sqlite3.Connection) -> int:
    """Display pending notifications. Returns count."""
    notifs = get_notifications(conn)
    if not notifs:
        print("[*] No pending notifications.")
        return 0

    print(f"\n{'='*60}")
    print(f"  {len(notifs)} pending notification(s)")
    print(f"{'='*60}")
    for n in notifs:
        print(f"  [{n['detected_at']}] {n['description']}")
        if n["scope_target"]:
            print(f"    scope: {n['scope_target']}")
    print(f"{'='*60}\n")
    return len(notifs)


def acknowledge_all(conn: sqlite3.Connection) -> int:
    """Mark all findings as acknowledged."""
    cur = conn.execute("UPDATE findings SET acknowledged=1 WHERE acknowledged=0")
    conn.commit()
    return cur.rowcount


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="scope_manager",
        description="Bug Bounty Scope Manager — track targets, schedule scans, get notified.",
    )
    p.add_argument("--db", default=DB_NAME, help="SQLite database path")

    sub = p.add_subparsers(dest="command", help="Command")

    # add
    p_add = sub.add_parser("add", help="Add item to scope")
    p_add.add_argument("type", choices=["domain", "ip", "url"], help="Item type")
    p_add.add_argument("target", help="Domain, IP, or URL to add")

    # remove
    p_rm = sub.add_parser("remove", help="Remove item from scope")
    p_rm.add_argument("target", help="Domain, IP, or URL to remove")

    # list
    p_list = sub.add_parser("list", help="List scope items")
    p_list.add_argument("type", nargs="?", choices=["domain", "ip", "url"], help="Filter by type")

    # scan
    p_scan = sub.add_parser("scan", help="Run subdomain enumeration scan")
    p_scan.add_argument("--type", choices=["domain", "ip", "url"], help="Limit to type")

    # schedule
    p_sched = sub.add_parser("schedule", help="Schedule recurring scan")
    p_sched.add_argument("cron", nargs="?", help="Cron expression: daily, weekly, or custom")
    p_sched.add_argument("--type", default="domain", choices=["domain", "ip", "url"])
    p_sched.add_argument("--list", action="store_true", help="List active schedules")

    # notify
    p_notif = sub.add_parser("notify", help="Show pending notifications")
    p_notif.add_argument("--ack", action="store_true", help="Acknowledge all")

    # findings
    p_find = sub.add_parser("findings", help="List all findings")
    p_find.add_argument("--unack", action="store_true", help="Only unacknowledged")

    # run-due
    p_due = sub.add_parser("run-due", help="Run all due scheduled scans (cron hook)")

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    conn = get_db(args.db)

    try:
        match args.command:
            case "add":
                add_item(conn, args.type, args.target)

            case "remove":
                remove_item(conn, args.target)

            case "list":
                items = list_items(conn, args.type)
                if not items:
                    print("[*] No active scope items.")
                else:
                    by_type: dict[str, list[str]] = {}
                    for row in items:
                        by_type.setdefault(row["type"], []).append(row["target"])
                    for t, targets in sorted(by_type.items()):
                        print(f"\n  [{t}] ({len(targets)})")
                        for tgt in targets:
                            print(f"    {tgt}")

            case "scan":
                run_scan(conn, args.type)

            case "schedule":
                if args.list:
                    scheds = conn.execute(
                        "SELECT * FROM scan_schedule WHERE active=1 ORDER BY next_run"
                    ).fetchall()
                    if not scheds:
                        print("[*] No active schedules.")
                    for s in scheds:
                        print(f"  #{s['id']} {s['cron_expr']} {s['scope_type']} next={s['next_run']}")
                elif args.cron:
                    schedule_scan(conn, args.cron, args.type)
                else:
                    parser.error("schedule requires --list or a cron expression")

            case "notify":
                if args.ack:
                    n = acknowledge_all(conn)
                    print(f"[*] Acknowledged {n} notification(s).")
                else:
                    show_notifications(conn)

            case "findings":
                if args.unack:
                    rows = conn.execute(
                        "SELECT * FROM findings WHERE acknowledged=0 ORDER BY detected_at DESC"
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT * FROM findings ORDER BY detected_at DESC LIMIT 50"
                    ).fetchall()
                for r in rows:
                    status = "NEW" if not r["acknowledged"] else "ack"
                    print(f"  [{status}] [{r['detected_at']}] {r['description']}")

            case "run-due":
                due = due_scans(conn)
                if not due:
                    print("[*] No due scans.")
                else:
                    print(f"[*] {len(due)} scan(s) due. Running...")
                    for sched in due:
                        run_scan(conn, sched["scope_type"])
                        update_schedule_next(conn, sched)

            case _:
                parser.print_help()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
