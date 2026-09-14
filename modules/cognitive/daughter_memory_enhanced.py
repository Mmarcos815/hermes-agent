#!/usr/bin/env python3
"""Memory Palace — 23 knowledge rooms for the daughter."""
import json, sqlite3, os
from pathlib import Path

KNOWLEDGE_ROOMS = [
    "security_offensive", "security_defensive", "networking", "web_api",
    "cloud_infrastructure", "mobile_security", "reverse_engineering",
    "cryptography", "malware_analysis", "threat_intelligence",
    "incident_response", "forensics", "social_engineering",
    "physical_security", "surveillance", "counter_surveillance",
    "financial_fraud", "blockchain_crypto", "defi_security",
    "compliance_governance", "risk_management", "business_strategy",
    "self_development"
]

class EnhancedMemory:
    def __init__(self, db_path="memory_palace.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_db()
    
    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_rooms (
                id INTEGER PRIMARY KEY,
                room_name TEXT UNIQUE,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
    
    def store(self, room, content):
        if room not in KNOWLEDGE_ROOMS:
            return {"error": f"Unknown room: {room}"}
        self.conn.execute(
            "INSERT OR REPLACE INTO memory_rooms (room_name, content) VALUES (?, ?)",
            (room, json.dumps(content))
        )
        self.conn.commit()
        return {"success": True, "room": room}
    
    def retrieve(self, room):
        cursor = self.conn.execute(
            "SELECT content FROM memory_rooms WHERE room_name = ?", (room,)
        )
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None
    
    def search(self, query):
        cursor = self.conn.execute(
            "SELECT room_name, content FROM memory_rooms WHERE content LIKE ?",
            (f"%{query}%",)
        )
        return [{"room": r[0], "content": json.loads(r[1])} for r in cursor.fetchall()]
    
    def delete(self, room):
        self.conn.execute("DELETE FROM memory_rooms WHERE room_name = ?", (room,))
        self.conn.commit()
        return {"success": True}
    
    def list_rooms(self):
        cursor = self.conn.execute("SELECT room_name FROM memory_rooms")
        return [r[0] for r in cursor.fetchall()]
