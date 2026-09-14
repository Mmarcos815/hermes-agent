#!/usr/bin/env python3
"""Self-Improvement Engine — trajectory logging and failure analysis."""
import json, os, sqlite3
from datetime import datetime

class SelfImprover:
    def __init__(self, log_path="trajectory_log.db"):
        self.log_path = log_path
        self.conn = sqlite3.connect(log_path)
        self._init_db()
    
    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS trajectories (
                id INTEGER PRIMARY KEY,
                objective TEXT,
                steps_taken TEXT,
                outcome TEXT,
                success BOOLEAN,
                lessons_learned TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS failures (
                id INTEGER PRIMARY KEY,
                context TEXT,
                error_type TEXT,
                root_cause TEXT,
                resolution TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
    
    def log_trajectory(self, objective, steps, outcome, success, lessons=""):
        self.conn.execute("""
            INSERT INTO trajectories (objective, steps_taken, outcome, success, lessons_learned)
            VALUES (?, ?, ?, ?, ?)
        """, (objective, json.dumps(steps), outcome, success, lessons))
        self.conn.commit()
        return {"success": True, "logged": True}
    
    def log_failure(self, context, error_type, root_cause, resolution):
        self.conn.execute("""
            INSERT INTO failures (context, error_type, root_cause, resolution)
            VALUES (?, ?, ?, ?)
        """, (context, error_type, root_cause, resolution))
        self.conn.commit()
        return {"success": True, "logged": True}
    
    def get_trajectory_history(self, limit=10):
        cursor = self.conn.execute(
            "SELECT objective, outcome, success, timestamp FROM trajectories ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        return [{"objective": r[0], "outcome": r[1], "success": r[2], "timestamp": r[3]}
                for r in cursor.fetchall()]
    
    def get_failure_analysis(self, error_type=None):
        if error_type:
            cursor = self.conn.execute(
                "SELECT context, root_cause, resolution FROM failures WHERE error_type = ?",
                (error_type,)
            )
        else:
            cursor = self.conn.execute("SELECT context, error_type, root_cause, resolution FROM failures")
        return [{"context": r[0], "error_type": r[1] if len(r) > 3 else error_type, 
                 "root_cause": r[-2], "resolution": r[-1]} for r in cursor.fetchall()]
    
    def get_improvement_stats(self):
        cursor = self.conn.execute("""
            SELECT 
                COUNT(*) as total_trajectories,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
                (SELECT COUNT(*) FROM failures) as total_failures
            FROM trajectories
        """)
        row = cursor.fetchone()
        return {
            "total_trajectories": row[0],
            "successes": row[1],
            "success_rate": (row[1] / row[0] * 100) if row[0] > 0 else 0,
            "total_failures": row[2]
        }
