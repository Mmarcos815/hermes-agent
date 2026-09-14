#!/usr/bin/env python3
"""Self-Development Orchestrator — tracks 51 skills and learning progress."""
import json, os, sqlite3
from pathlib import Path
from datetime import datetime

SKILL_CATEGORIES = {
    "security_offensive": ["recon", "vuln_analysis", "exploitation", "post_exploitation", "evasion"],
    "security_defensive": ["monitoring", "incident_response", "forensics", "compliance"],
    "programming": ["python", "go", "rust", "typescript", "c", "sql"],
    "ai_ml": ["model_training", "inference", "fine_tuning", "prompt_engineering"],
    "business": ["strategy", "marketing", "sales", "operations"],
    "self_development": ["learning", "mastery", "teaching", "documentation"]
}

class SelfDevelopmentOrchestrator:
    def __init__(self, db_path="self_development.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_db()
    
    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                category TEXT,
                level INTEGER DEFAULT 0,
                max_level INTEGER DEFAULT 5,
                experience INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS learning_log (
                id INTEGER PRIMARY KEY,
                skill_name TEXT,
                action TEXT,
                experience_gained INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
        self._seed_skills()
    
    def _seed_skills(self):
        for category, skills in SKILL_CATEGORIES.items():
            for skill in skills:
                try:
                    self.conn.execute(
                        "INSERT OR IGNORE INTO skills (name, category) VALUES (?, ?)",
                        (skill, category)
                    )
                except:
                    pass
        self.conn.commit()
    
    def track_skill(self, skill_name, experience_gained=1):
        self.conn.execute("""
            UPDATE skills 
            SET level = MIN(level + 1, max_level),
                experience = experience + ?,
                last_updated = CURRENT_TIMESTAMP
            WHERE name = ?
        """, (experience_gained, skill_name))
        self.conn.execute("""
            INSERT INTO learning_log (skill_name, action, experience_gained)
            VALUES (?, 'practice', ?)
        """, (skill_name, experience_gained))
        self.conn.commit()
        return {"success": True, "skill": skill_name}
    
    def get_skill_level(self, skill_name):
        cursor = self.conn.execute(
            "SELECT level, max_level, experience FROM skills WHERE name = ?",
            (skill_name,)
        )
        row = cursor.fetchone()
        return {
            "skill": skill_name,
            "level": row[0] if row else 0,
            "max_level": row[1] if row else 5,
            "experience": row[2] if row else 0
        }
    
    def get_all_skills(self):
        cursor = self.conn.execute("SELECT name, category, level, experience FROM skills")
        return [{"name": r[0], "category": r[1], "level": r[2], "experience": r[3]} 
                for r in cursor.fetchall()]
    
    def get_category_summary(self, category):
        cursor = self.conn.execute(
            "SELECT AVG(level), SUM(experience) FROM skills WHERE category = ?",
            (category,)
        )
        row = cursor.fetchone()
        return {
            "category": category,
            "average_level": row[0] or 0,
            "total_experience": row[1] or 0
        }
    
    def get_learning_history(self, limit=50):
        cursor = self.conn.execute(
            "SELECT skill_name, action, experience_gained, timestamp FROM learning_log ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        return [{"skill": r[0], "action": r[1], "experience": r[2], "timestamp": r[3]}
                for r in cursor.fetchall()]
