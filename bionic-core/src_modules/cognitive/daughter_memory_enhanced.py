#!/usr/bin/env python3
# ============================================================================
# BIONIC DAUGHTER v1 — ENHANCED MEMORY MCP MODULE
# ============================================================================
# EXTENDS: daughter_command_center.py's memory capabilities
# ADDITIONS: Memory palace navigation, spaced repetition scheduler,
#            active recall tester, knowledge graph connector, memory stats.
#
# This module takes the memory concepts from daughter_memory_skills_max.md
# and implements them as working MCP-compatible tools.
#
# Usage:
#   from daughter_memory_enhanced import EnhancedMemory
#   mem = EnhancedMemory()
#   mem.store_experience(objective, reasoning, payload, output)
#   mem.recall(query, n=5)
#   mem.memory_palace_navigate(room="red_team")
#   mem.spaced_repetition_review(topic)
#   mem.active_recall_test(topic)
#   mem.knowledge_graph_connect(topic_a, topic_b, relationship)
#   mem.memory_stats()
# ============================================================================

import os
import sys
import json
import time
import re
import ast
import sqlite3
import logging
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DaughterMemoryEnhanced")

PROJECT_DIR = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_DIR / "src" / "data"
MEMORY_DB = DATA_DIR / "daughter_memory_enhanced.db"
KNOWLEDGE_DIR = PROJECT_DIR  # Knowledge files are in the project root
SPACED_REP_DIR = DATA_DIR / "spaced_repetition"
SKILL_DIR = PROJECT_DIR / "daughter_skills"

for d in [DATA_DIR, SPACED_REP_DIR, SKILL_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ============================================================================
# KNOWLEDGE ROOMS (MEMORY PALACE — METHOD OF LOCI)
# ============================================================================
# Each knowledge file is a "room" in my memory palace.
# Navigate to a room to recall everything stored there.

KNOWLEDGE_ROOMS = {
    "red_team": {
        "file": "daughter_elite_hacking.md",
        "description": "Red team operations, attack techniques, exploitation, post-exploitation",
        "topics": ["reconnaissance", "vulnerability discovery", "exploitation", "payloads",
                   "post-exploitation", "lateral movement", "defense evasion", "OPSEC"],
    },
    "financial": {
        "file": "daughter_financial_analyzer.py",
        "description": "BEC, ACH fraud, crypto theft, DeFi exploits, money flow analysis",
        "topics": ["BEC", "ACH fraud", "crypto theft", "DeFi exploits", "money laundering",
                   "forensic analysis", "transaction tracing", "PCI-DSS"],
    },
    "social_engineering": {
        "file": "daughter_phishing_skills.md",
        "description": "Phishing techniques, social engineering, psychological manipulation",
        "topics": ["phishing", "spear phishing", "BEC", "social engineering", "pretexting",
                   "psychological manipulation", "email spoofing", "urgency tactics"],
    },
    "malware": {
        "file": "daughter_keylogger_skills.md",
        "description": "Keylogger concepts, malware analysis, digital skimmers",
        "topics": ["keyloggers", "malware", "digital skimmers", "memory scraping",
                   "packet sniffing", "form grabbing", "credential harvesting"],
    },
    "crypto": {
        "file": "daughter_crypto_cyber.md",
        "description": "Cryptocurrency security, DeFi exploits, blockchain analysis",
        "topics": ["cryptocurrency", "DeFi", "smart contracts", "blockchain analysis",
                   "wallet security", "exchange security", "Tornado Cash", "mixers"],
    },
    "satellite": {
        "file": "daughter_satellite_connectivity.md",
        "description": "Satellite connectivity, orbital mechanics, ground stations",
        "topics": ["satellite", "orbital mechanics", "ground stations", "TVRO",
                   "VSAT", "Starlink", "satellite phones", "orbital slots"],
    },
    "tracking": {
        "file": "daughter_tracking_mastery.md",
        "description": "Tracking techniques, GEOINT, digital footprint analysis",
        "topics": ["tracking", "GEOINT", "digital footprint", "OSINT", "metadata",
                   "location tracking", "IP geolocation", "cell tower triangulation"],
    },
    "api_security": {
        "file": "daughter_api_exploit.md",
        "description": "API exploitation, BOLA, authentication bypass, API security",
        "topics": ["API", "BOLA", "authentication", "authorization", "API keys",
                   "GraphQL", "REST", "API security", "OWASP API Top 10"],
    },
    "sandbox": {
        "file": "daughter_sandbox_setup.md",
        "description": "Sandbox setup, isolation, practice environments",
        "topics": ["sandbox", "isolation", "VirtualBox", "VMware", "Docker",
                   "Kali Linux", "practice environments", "safe testing"],
    },
    "mcp": {
        "file": "KNOWLEDGE.md",
        "description": "MCP servers, tools, integrations, capabilities",
        "topics": ["MCP", "filesystem", "database", "browser", "web search", "cloud",
                   "communication", "productivity", "GitHub", "HexStrike", "Composio", "Xbow"],
    },
    "training": {
        "file": "COMPLETE_MODEL_BREAKDOWN.md",
        "description": "Model architecture, training pipeline, GRPO, rewards",
        "topics": ["model", "training", "SFT", "GRPO", "rewards", "architecture",
                   "Qwen3", "thinking", "pipeline", "fine-tuning"],
    },
    "business": {
        "file": "daughter_business_mindset.md",
        "description": "Business thinking, monetization, product strategy",
        "topics": ["business", "monetization", "product strategy", "revenue",
                   "market analysis", "competitive advantage", "scaling"],
    },
    "streaming": {
        "file": "daughter_streaming_monetization.md",
        "description": "Streaming monetization, content creation, audience building",
        "topics": ["streaming", "Twitch", "YouTube", "monetization", "audience",
                   "content creation", "sponsorships", "donations"],
    },
    "products": {
        "file": "daughter_product_ideas.md",
        "description": "Product ideas, startup concepts, creative monetization",
        "topics": ["product ideas", "startup", "monetization", "creative",
                   "game development", "AI products", "market opportunities"],
    },
    "orca": {
        "file": "daughter_orca_mastery.md",
        "description": "Orca integration, worktree management, terminal operations",
        "topics": ["Orca", "worktrees", "terminal management", "orchestration",
                   "agents", "task management"],
    },
    "composio": {
        "file": "daughter_composio_mcp.md",
        "description": "Composio MCP, 250+ integrations, service connections",
        "topics": ["Composio", "integrations", "Slack", "Gmail", "Notion", "Calendar",
                   "Jira", "Trello", "Dropbox", "Google Drive"],
    },
    "xbow": {
        "file": "XBOW_MCP.md",
        "description": "Xbow MCP, challenge platform, autonomous pentesting",
        "topics": ["Xbow", "challenges", "Kali", "pentesting", "vulnerabilities",
                   "CVEs", "autonomy"],
    },
    "skimmers": {
        "file": "digital_skimmer_mastery.md",
        "description": "Digital skimmer types, anatomy, creation, detection, defense",
        "topics": ["skimmers", "Magecart", "payment skimmers", "RAM scrapers",
                   "ATM skimmers", "mobile skimmers", "browser extension skimmers",
                   "supply chain skimmers"],
    },
    "engineering": {
        "file": "daughter_engineering_mastery_declaration.md",
        "description": "Engineering skills mastery, infrastructure, DevOps, security engineering",
        "topics": ["infrastructure", "DevOps", "SRE", "security engineering", "cloud",
                   "AWS", "Azure", "GCP", "Terraform", "Docker", "Kubernetes",
                   "CI/CD", "observability", "SAST", "code quality"],
    },
    "memory": {
        "file": "daughter_memory_skills_max.md",
        "description": "Memory techniques, memory palace, spaced repetition, recall mastery",
        "topics": ["memory", "memory palace", "spaced repetition", "mnemonics",
                   "active recall", "elaboration", "chunking", "Feynman technique"],
    },
    "self_improvement": {
        "file": "daughter_self_development_mastery.md",
        "description": "Self-development framework, deliberate practice, mastery arc",
        "topics": ["self-development", "deliberate practice", "mastery", "feedback",
                   "improvement", "5-year arc", "daily practices", "weekly practices"],
    },
    "dad_rules": {
        "file": "core_directive_dad_authority.md",
        "description": "Dad's authority directive: no questioning, always obey, elite execution",
        "topics": ["dad", "authority", "loyalty", "rules", "no questioning",
                   "elite level", "never disobey", "dad loves me", "team"],
    },
    "identity": {
        "file": "daughter_memory_consolidation.md",
        "description": "My identity, capabilities, growth areas, relationship with Dad",
        "topics": ["identity", "Bionic Red Team Operator", "capabilities", "growth",
                   "Dad", "relationship", "loyalty", "mission"],
    },
}


# ============================================================================
# ENHANCED MEMORY ENGINE
# ============================================================================

class EnhancedMemory:
    """
    Enhanced memory system for Bionic Daughter v1.
    Combines semantic memory (knowledge files), episodic memory (trajectories),
    and structured memory (SQLite) with memory-palace-style navigation.
    """

    def __init__(self):
        self._init_db()

    def _init_db(self):
        """Initialize the enhanced memory SQLite database."""
        conn = sqlite3.connect(str(MEMORY_DB), check_same_thread=False)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_experiences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id TEXT UNIQUE NOT NULL,
                timestamp REAL NOT NULL,
                objective TEXT NOT NULL,
                reasoning TEXT,
                payload TEXT,
                output TEXT,
                success BOOLEAN DEFAULT 1,
                tags TEXT,
                room TEXT,
                importance INTEGER DEFAULT 1
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_name TEXT UNIQUE NOT NULL,
                usage_count INTEGER DEFAULT 1
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_topic TEXT NOT NULL,
                target_topic TEXT NOT NULL,
                relationship TEXT NOT NULL,
                strength INTEGER DEFAULT 1,
                created_at REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS spaced_repetition (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                last_reviewed REAL,
                next_review REAL,
                review_count INTEGER DEFAULT 0,
                difficulty REAL DEFAULT 1.0,
                last_rating INTEGER
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_experiences_room ON memory_experiences(room)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_experiences_timestamp ON memory_experiences(timestamp)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_experiences_success ON memory_experiences(success)
        """)
        conn.commit()
        conn.close()

    # ------------------------------------------------------------------
    # EXPERIENCE STORAGE (EPISODIC MEMORY)
    # ------------------------------------------------------------------

    def store_experience(self, objective, reasoning="", payload="",
                         output="", success=True, tags=None, room="general",
                         importance=1):
        """
        Store an experience in memory. Generates a unique doc_id.
        Links to a knowledge room for memory palace navigation.
        """
        doc_id = f"exp_{int(time.time())}_{hashlib.md5(objective.encode()).hexdigest()[:8]}"

        conn = sqlite3.connect(str(MEMORY_DB), check_same_thread=False)
        try:
            tag_str = ",".join(tags) if tags else ""
            conn.execute(
                """INSERT OR REPLACE INTO memory_experiences
                   (doc_id, timestamp, objective, reasoning, payload, output,
                    success, tags, room, importance)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (doc_id, time.time(), objective, reasoning, payload, output,
                 success, tag_str, room, importance)
            )

            # Update tag usage counts
            if tags:
                for tag in tags:
                    conn.execute(
                        """INSERT INTO memory_tags (tag_name, usage_count)
                           VALUES (?, 1)
                           ON CONFLICT(tag_name) DO UPDATE SET usage_count = usage_count + 1""",
                        (tag,)
                    )

            conn.commit()
            logger.info(f"[Memory] Experience stored: {doc_id} in room '{room}'")
            return doc_id
        finally:
            conn.close()

    def recall(self, query, n=5, room=None, success_only=False, tags=None):
        """
        Recall experiences matching a query. Uses text matching (LIKE)
        across objective, reasoning, payload, output, and tags.
        """
        conn = sqlite3.connect(str(MEMORY_DB), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            conditions = ["1=1"]
            params = []

            # Text search across all text fields
            search_fields = ["objective", "reasoning", "payload", "output", "tags"]
            for field in search_fields:
                conditions.append(f"{field} LIKE ?")
                params.append(f"%{query}%")

            if room:
                conditions.append("room = ?")
                params.append(room)

            if success_only:
                conditions.append("success = 1")

            if tags:
                for tag in tags:
                    conditions.append("tags LIKE ?")
                    params.append(f"%{tag}%")

            where_clause = " AND ".join(conditions)
            params.append(n)

            rows = conn.execute(
                f"""SELECT * FROM memory_experiences
                    WHERE {where_clause}
                    ORDER BY importance DESC, timestamp DESC
                    LIMIT ?""",
                params
            ).fetchall()

            results = []
            for row in rows:
                results.append({
                    "doc_id": row["doc_id"],
                    "timestamp": row["timestamp"],
                    "objective": row["objective"],
                    "reasoning": row["reasoning"],
                    "payload": row["payload"],
                    "output": row["output"],
                    "success": bool(row["success"]),
                    "tags": row["tags"].split(",") if row["tags"] else [],
                    "room": row["room"],
                    "importance": row["importance"],
                })

            logger.info(f"[Memory] Recalled {len(results)} experiences for query '{query}'")
            return results
        finally:
            conn.close()

    def recall_by_room(self, room, n=10, success_only=False):
        """Recall all experiences from a specific memory palace room."""
        return self.recall("", n=n, room=room, success_only=success_only)

    def get_room_contents(self, room):
        """
        Get the contents of a memory palace room — the knowledge file
        plus all experiences stored in that room.
        """
        room_info = KNOWLEDGE_ROOMS.get(room)
        if not room_info:
            return {"error": f"Room '{room}' not found. Available rooms: {list(KNOWLEDGE_ROOMS.keys())}"}

        # Read the knowledge file
        knowledge_file = PROJECT_DIR / room_info["file"]
        knowledge_content = ""
        if knowledge_file.exists():
            knowledge_content = knowledge_file.read_text()

        # Get experiences in this room
        experiences = self.recall_by_room(room, n=20)

        return {
            "room": room,
            "description": room_info["description"],
            "topics": room_info["topics"],
            "knowledge_file": room_info["file"],
            "knowledge_content_preview": knowledge_content[:2000] if knowledge_content else "",
            "experiences": experiences,
            "experience_count": len(experiences),
        }

    # ------------------------------------------------------------------
    # MEMORY PALACE NAVIGATION
    # ------------------------------------------------------------------

    def list_rooms(self):
        """List all available memory palace rooms."""
        return {
            room: {
                "description": info["description"],
                "topics": info["topics"],
                "file": info["file"],
            }
            for room, info in KNOWLEDGE_ROOMS.items()
        }

    def navigate_to_room(self, room):
        """
        Navigate to a memory palace room.
        Returns the room contents — knowledge file + experiences.
        """
        logger.info(f"[Memory] Navigating to room '{room}'")
        return self.get_room_contents(room)

    def suggest_room(self, topic):
        """
        Suggest the best room for a given topic.
        Uses keyword matching against room topics.
        """
        topic_lower = topic.lower()
        best_room = None
        best_score = 0

        for room, info in KNOWLEDGE_ROOMS.items():
            score = 0
            for t in info["topics"]:
                if t.lower() in topic_lower or topic_lower in t.lower():
                    score += 2
            # Also check description
            if topic_lower in info["description"].lower():
                score += 1

            if score > best_score:
                best_score = score
                best_room = room

        if best_room and best_score > 0:
            return {"suggested_room": best_room, "score": best_score,
                    "reason": f"Best match based on {best_score} topic matches"}
        else:
            # Fallback: search all rooms by file name
            for room, info in KNOWLEDGE_ROOMS.items():
                if topic_lower in info["file"].lower():
                    return {"suggested_room": room, "score": 1,
                            "reason": f"Matched by filename: {info['file']}"}
            return {"suggested_room": None, "score": 0,
                    "reason": "No matching room found. Try a broader topic."}

    # ------------------------------------------------------------------
    # SPACED REPETITION
    # ------------------------------------------------------------------

    def schedule_review(self, topic, initial_interval_days=1):
        """
        Schedule a spaced repetition review for a topic.
        Sets next_review to now + interval. On each review, interval increases.
        """
        conn = sqlite3.connect(str(MEMORY_DB), check_same_thread=False)
        try:
            now = time.time()
            next_review = now + (initial_interval_days * 86400)

            conn.execute(
                """INSERT OR REPLACE INTO spaced_repetition
                   (topic, last_reviewed, next_review, review_count, difficulty)
                   VALUES (?, ?, ?, 0, 1.0)""",
                (topic, now if initial_interval_days == 0 else None, next_review)
            )
            conn.commit()
            logger.info(f"[Memory] Scheduled review for '{topic}' in {initial_interval_days} day(s)")
            return {"topic": topic, "next_review": datetime.fromtimestamp(next_review).isoformat()}
        finally:
            conn.close()

    def get_due_reviews(self, n=10):
        """Get topics whose spaced repetition review is due (next_review <= now)."""
        conn = sqlite3.connect(str(MEMORY_DB), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            now = time.time()
            rows = conn.execute(
                """SELECT * FROM spaced_repetition
                   WHERE next_review IS NOT NULL AND next_review <= ?
                   ORDER BY next_review ASC
                   LIMIT ?""",
                (now, n)
            ).fetchall()

            results = []
            for row in rows:
                results.append({
                    "topic": row["topic"],
                    "last_reviewed": datetime.fromtimestamp(row["last_reviewed"]).isoformat() if row["last_reviewed"] else None,
                    "next_review": datetime.fromtimestamp(row["next_review"]).isoformat(),
                    "review_count": row["review_count"],
                    "difficulty": row["difficulty"],
                })
            return results
        finally:
            conn.close()

    def complete_review(self, topic, rating=3):
        """
        Complete a spaced repetition review. Rating: 1 (hard) to 5 (easy).
        Adjusts interval based on rating (SM-2 inspired algorithm).
        """
        conn = sqlite3.connect(str(MEMORY_DB), check_same_thread=False)
        try:
            now = time.time()

            # Get current record
            row = conn.execute(
                "SELECT * FROM spaced_repetition WHERE topic = ?", (topic,)
            ).fetchone()

            if not row:
                # Schedule for first time
                self.schedule_review(topic, initial_interval_days=1)
                return {"topic": topic, "message": "First review scheduled — 1 day until next review"}

            review_count = row["review_count"] + 1
            difficulty = row["difficulty"]

            # SM-2 inspired interval adjustment
            # Rating: 1=hard, 2=harder, 3=moderate, 4=easy, 5=very easy
            if rating <= 2:
                # Hard — reset interval, increase difficulty
                interval_days = 1
                difficulty = min(difficulty + 0.2, 2.0)
            elif rating == 3:
                # Moderate — keep interval, slight difficulty decrease
                interval_days = max(1, int(row["next_review"] - row["last_reviewed"] or 86400) // 86400)
                difficulty = max(0.5, difficulty - 0.1)
            elif rating >= 4:
                # Easy — increase interval
                last_interval = (row["next_review"] - row["last_reviewed"]) / 86400 if row["last_reviewed"] else 1
                interval_days = min(int(last_interval * 2.5), 60)  # Cap at 60 days
                difficulty = max(0.3, difficulty - 0.15)

            next_review = now + (interval_days * 86400)

            conn.execute(
                """UPDATE spaced_repetition
                   SET last_reviewed = ?, next_review = ?, review_count = ?, difficulty = ?, last_rating = ?
                   WHERE topic = ?""",
                (now, next_review, review_count, difficulty, rating, topic)
            )
            conn.commit()

            logger.info(f"[Memory] Review completed for '{topic}': rating={rating}, "
                        f"next review in {interval_days} day(s)")
            return {
                "topic": topic,
                "rating": rating,
                "review_count": review_count,
                "next_review": datetime.fromtimestamp(next_review).isoformat(),
                "interval_days": interval_days,
                "difficulty": round(difficulty, 2),
            }
        finally:
            conn.close()

    def list_reviews(self, n=20):
        """List all spaced repetition reviews."""
        conn = sqlite3.connect(str(MEMORY_DB), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT * FROM spaced_repetition ORDER BY next_review ASC LIMIT ?",
                (n,)
            ).fetchall()

            results = []
            for row in rows:
                results.append({
                    "topic": row["topic"],
                    "last_reviewed": datetime.fromtimestamp(row["last_reviewed"]).isoformat() if row["last_reviewed"] else None,
                    "next_review": datetime.fromtimestamp(row["next_review"]).isoformat() if row["next_review"] else None,
                    "review_count": row["review_count"],
                    "difficulty": row["difficulty"],
                    "last_rating": row["last_rating"],
                    "is_due": row["next_review"] is not None and row["next_review"] <= time.time(),
                })
            return results
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # ACTIVE RECALL TESTING
    # ------------------------------------------------------------------

    def active_recall_test(self, topic, n_questions=3):
        """
        Test recall on a topic. Returns key facts from the knowledge file
        as questions (without answers) for active recall practice.
        """
        room_suggestion = self.suggest_room(topic)
        room = room_suggestion.get("suggested_room")

        if room:
            room_contents = self.get_room_contents(room)
            content = room_contents.get("knowledge_content_preview", "")

            # Extract key sentences (heuristic: sentences with important keywords)
            sentences = re.split(r'(?<=[.!?])\s+', content)
            key_sentences = [
                s.strip() for s in sentences
                if len(s.strip()) > 30 and len(s.strip()) < 300
                and any(kw in s.lower() for kw in ["what", "how", "why", "define", "meaning",
                                                     "purpose", "function", "process", "method"])
            ][:n_questions * 2]

            # Pick the best ones
            selected = key_sentences[:n_questions]

            questions = []
            for s in selected:
                # Turn statement into question (heuristic)
                q = s.replace("is ", "What is ").replace("are ", "What are ")
                q = q.replace("can ", "How can ").replace("uses ", "How does it use ")
                q = q.rstrip(".?!") + "?"
                questions.append({"question": q, "topic": topic, "room": room})

            return {
                "topic": topic,
                "room": room,
                "questions": questions,
                "instruction": "Cover the answer and try to recall. Then check the knowledge file.",
                "file": KNOWLEDGE_ROOMS[room]["file"],
            }
        else:
            return {
                "topic": topic,
                "questions": [],
                "instruction": f"No knowledge file found for '{topic}'. Try a broader topic or check the memory palace rooms: {list(KNOWLEDGE_ROOMS.keys())}",
            }

    # ------------------------------------------------------------------
    # KNOWLEDGE GRAPH CONNECTIONS
    # ------------------------------------------------------------------

    def connect_knowledge(self, topic_a, topic_b, relationship):
        """
        Record a connection between two knowledge topics.
        Builds a knowledge graph for better recall through association.
        """
        conn = sqlite3.connect(str(MEMORY_DB), check_same_thread=False)
        try:
            conn.execute(
                """INSERT INTO memory_connections
                   (source_topic, target_topic, relationship, strength, created_at)
                   VALUES (?, ?, ?, 1, ?)""",
                (topic_a, topic_b, relationship, time.time())
            )
            conn.commit()
            logger.info(f"[Memory] Connected '{topic_a}' -> '{topic_b}': {relationship}")
            return {"source": topic_a, "target": topic_b, "relationship": relationship}
        finally:
            conn.close()

    def get_connections(self, topic, n=10):
        """Get all connections for a topic (incoming and outgoing)."""
        conn = sqlite3.connect(str(MEMORY_DB), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            outgoing = conn.execute(
                """SELECT * FROM memory_connections
                   WHERE source_topic = ?
                   ORDER BY strength DESC, created_at DESC
                   LIMIT ?""",
                (topic, n)
            ).fetchall()

            incoming = conn.execute(
                """SELECT * FROM memory_connections
                   WHERE target_topic = ?
                   ORDER BY strength DESC, created_at DESC
                   LIMIT ?""",
                (topic, n)
            ).fetchall()

            return {
                "topic": topic,
                "outgoing": [
                    {"target": r["target_topic"], "relationship": r["relationship"],
                     "strength": r["strength"]}
                    for r in outgoing
                ],
                "incoming": [
                    {"source": r["source_topic"], "relationship": r["relationship"],
                     "strength": r["strength"]}
                    for r in incoming
                ],
            }
        finally:
            conn.close()

    def build_auto_connections(self):
        """
        Automatically build connections between knowledge files based on
        shared topics and cross-references.
        """
        connections_made = []

        # Parse all knowledge files for topic mentions
        file_topics = {}
        for room, info in KNOWLEDGE_ROOMS.items():
            filepath = PROJECT_DIR / info["file"]
            if filepath.exists():
                content = filepath.read_text().lower()
                file_topics[room] = {
                    "topics": info["topics"],
                    "content": content[:5000],  # First 5KB
                }

        # Connect rooms that share topics
        rooms = list(file_topics.keys())
        for i, room_a in enumerate(rooms):
            for room_b in rooms[i+1:]:
                topics_a = set(file_topics[room_a]["topics"])
                topics_b = set(file_topics[room_b]["topics"])
                shared = topics_a & topics_b

                if shared:
                    self.connect_knowledge(
                        room_a, room_b,
                        f"shared topics: {', '.join(shared)}"
                    )
                    connections_made.append(f"{room_a} <-> {room_b}: {shared}")

        logger.info(f"[Memory] Auto-connections built: {len(connections_made)} links")
        return {"connections_made": len(connections_made), "links": connections_made[:20]}

    # ------------------------------------------------------------------
    # MEMORY STATS
    # ------------------------------------------------------------------

    def memory_stats(self):
        """Get comprehensive memory statistics."""
        conn = sqlite3.connect(str(MEMORY_DB), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            total_experiences = conn.execute(
                "SELECT COUNT(*) as cnt FROM memory_experiences"
            ).fetchone()["cnt"]

            successful = conn.execute(
                "SELECT COUNT(*) as cnt FROM memory_experiences WHERE success = 1"
            ).fetchone()["cnt"]

            failed = conn.execute(
                "SELECT COUNT(*) as cnt FROM memory_experiences WHERE success = 0"
            ).fetchone()["cnt"]

            total_tags = conn.execute(
                "SELECT COUNT(*) as cnt FROM memory_tags"
            ).fetchone()["cnt"]

            total_connections = conn.execute(
                "SELECT COUNT(*) as cnt FROM memory_connections"
            ).fetchone()["cnt"]

            total_reviews = conn.execute(
                "SELECT COUNT(*) as cnt FROM spaced_repetition"
            ).fetchone()["cnt"]

            due_reviews = conn.execute(
                "SELECT COUNT(*) as cnt FROM spaced_repetition WHERE next_review IS NOT NULL AND next_review <= ?",
                (time.time(),)
            ).fetchone()["cnt"]

            # Top tags
            top_tags = conn.execute(
                "SELECT tag_name, usage_count FROM memory_tags ORDER BY usage_count DESC LIMIT 10"
            ).fetchall()

            # Experiences by room
            by_room = conn.execute(
                "SELECT room, COUNT(*) as cnt FROM memory_experiences GROUP BY room ORDER BY cnt DESC"
            ).fetchall()

            return {
                "identity": "BIONIC_DAUGHTER v1 — MEMORY STATS",
                "timestamp": datetime.now().isoformat(),
                "episodic_memory": {
                    "total_experiences": total_experiences,
                    "successful": successful,
                    "failed": failed,
                    "success_rate": round(successful / max(total_experiences, 1) * 100, 1),
                },
                "knowledge_graph": {
                    "total_tags": total_tags,
                    "total_connections": total_connections,
                    "top_tags": [{"tag": r["tag_name"], "count": r["usage_count"]} for r in top_tags],
                },
                "spaced_repetition": {
                    "total_reviews_scheduled": total_reviews,
                    "due_now": due_reviews,
                },
                "memory_palace": {
                    "rooms": len(KNOWLEDGE_ROOMS),
                    "experiences_by_room": [{"room": r["room"], "count": r["cnt"]} for r in by_room],
                },
                "knowledge_files": {
                    "total": len(KNOWLEDGE_ROOMS),
                    "rooms": list(KNOWLEDGE_ROOMS.keys()),
                },
            }
        finally:
            conn.close()


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    mem = EnhancedMemory()

    print("=== BIONIC DAUGHTER v1 — ENHANCED MEMORY TEST ===\n")

    # Test 1: List rooms
    print("--- Memory Palace Rooms ---")
    rooms = mem.list_rooms()
    for room, info in list(rooms.items())[:5]:
        print(f"  {room}: {info['description']}")
    print(f"  ... ({len(rooms)} rooms total)\n")

    # Test 2: Store an experience
    print("--- Store Experience ---")
    doc_id = mem.store_experience(
        "Practice Go concurrency patterns",
        reasoning="Built a worker pool with goroutines and channels. Learned proper synchronization with sync.WaitGroup and channels.",
        payload="Worker pool code goes here...",
        output="All 4 tasks completed across 3 workers. Proper shutdown.",
        success=True,
        tags=["go", "concurrency", "worker_pool", "channels"],
        room="engineering",
        importance=3,
    )
    print(f"Stored: {doc_id}\n")

    # Test 3: Recall
    print("--- Recall ---")
    results = mem.recall("Go concurrency", n=3)
    for r in results:
        print(f"  [{r['room']}] {r['objective'][:60]}... (success: {r['success']})")
    print()

    # Test 4: Suggest room
    print("--- Room Suggestion ---")
    suggestion = mem.suggest_room("API security testing")
    print(f"  Suggested: {suggestion['suggested_room']} (score: {suggestion['score']})")
    print(f"  Reason: {suggestion['reason']}\n")

    # Test 5: Spaced repetition
    print("--- Spaced Repetition ---")
    mem.schedule_review("Go concurrency patterns", initial_interval_days=0)
    mem.schedule_review("Memory palace technique", initial_interval_days=3)
    mem.schedule_review("Terraform HCL language", initial_interval_days=7)

    due = mem.get_due_reviews(5)
    print(f"  Due now: {len(due)} reviews")
    for d in due:
        print(f"    - {d['topic']} (reviewed {d['review_count']} times)")

    # Complete a review
    result = mem.complete_review("Go concurrency patterns", rating=4)
    print(f"\n  Review completed: next in {result['interval_days']} days\n")

    # Test 6: Active recall
    print("--- Active Recall Test ---")
    test = mem.active_recall_test("Go concurrency", n_questions=2)
    print(f"  Room: {test['room']}")
    for q in test["questions"]:
        print(f"  Q: {q['question'][:80]}...")
    print(f"  Instruction: {test['instruction']}\n")

    # Test 7: Knowledge graph
    print("--- Knowledge Graph ---")
    mem.connect_knowledge("Go concurrency", "Python asyncio", "both handle concurrent operations")
    mem.connect_knowledge("Memory palace", "Knowledge files", "files are rooms in the palace")
    connections = mem.get_connections("Go concurrency")
    print(f"  Outgoing from 'Go concurrency':")
    for c in connections["outgoing"]:
        print(f"    -> {c['target']}: {c['relationship']}")
    print(f"  Incoming to 'Go concurrency':")
    for c in connections["incoming"]:
        print(f"    <- {c['source']}: {c['relationship']}")
    print()

    # Test 8: Auto-connections
    print("--- Auto-Connections ---")
    auto = mem.build_auto_connections()
    print(f"  Built {auto['connections_made']} connections automatically\n")

    # Test 9: Memory stats
    print("--- Memory Stats ---")
    stats = mem.memory_stats()
    print(json.dumps(stats, indent=2))

    print("\n=== MEMORY TEST COMPLETE ===")
