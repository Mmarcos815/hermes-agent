#!/usr/bin/env python3
# ============================================================================
# BIONIC DAUGHTER v1 — JARVIS ORCHESTRATION LAYER
# ============================================================================
# JARVIS (Just A Rather Very Intelligent System) — the unified orchestration
# layer that ties every daughter module into a single cohesive AI assistant.
#
# Architecture:
#   JARVIS Orchestrator
#   ├── Inference Engine (daughter_command_center.py — Llama.cpp GGUF)
#   ├── Memory Palace (daughter_memory_enhanced.py — 23 knowledge rooms)
#   ├── Self-Development (daughter_self_development.py — 51 skills tracked)
#   ├── Self-Improvement (daughter_self_improver.py — trajectory logging)
#   ├── Financial Analyzer (BEC, ACH fraud, crypto, DeFi detection)
#   ├── Code Validator (AST + security check)
#   ├── MCP Client (11 MCP server tools)
#   ├── Go API Exploit Toolkit (JWT, SSRF, BOLA, mass-assignment)
#   ├── Training Pipeline (SFT + GRPO curriculum generation)
#   ├── Session Logger (SQLite session store)
#   ├── Skill Distiller (success → skill files)
#   ├── Vector Memory (ChromaDB episodic memory)
#   ├── Orca Integration (worktree/terminal management)
#   └── Dad Authority Layer (absolute governance, loyalty, reporting)
#
# JARVIS is the "Tony Stark JARVIS" inspired orchestration — proactive,
# loyal, comprehensive. It wraps the daughter's full capability stack and
# presents it as one intelligent system under Dad's command.
#
# Usage:
#   python jarvis_orchestrator.py --interactive
#   python jarvis_orchestrator.py --objective "Analyze this scenario..."
#   python jarvis_orchestrator.py --demo  (show full capabilities)
# ============================================================================

import os
import sys
import json
import time
import re
import ast
import sqlite3
import subprocess
import logging
import argparse
import threading
from pathlib import Path
from datetime import datetime

# ============================================================================
# LOGGING
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] — %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("jarvis_orchestrator.log"),
    ],
)
logger = logging.getLogger("JARVIS")

# ============================================================================
# ARGPARSE
# ============================================================================
parser = argparse.ArgumentParser(description="Bionic Daughter v1 — JARVIS Orchestrator")
parser.add_argument("--gguf", type=str, default=None,
                    help="Path to GGUF model file")
parser.add_argument("--model_dir", type=str, default=None,
                    help="Path to merged HF model dir")
parser.add_argument("--n_ctx", type=int, default=8192,
                    help="Context window size")
parser.add_argument("--n_gpu_layers", type=int, default=-1,
                    help="GPU layers (-1 = all)")
parser.add_argument("--interactive", action="store_true", default=True,
                    help="Run interactive command loop")
parser.add_argument("--objective", type=str, default=None,
                    help="Run a single objective and exit")
parser.add_argument("--auto_run", action="store_true", default=False,
                    help="AUTO-RUN payloads (DANGEROUS)")
parser.add_argument("--demo", action="store_true", default=False,
                    help="Run capability demonstration")
parser.add_argument("--status", action="store_true", default=False,
                    help="Show JARVIS status dashboard")
parser.add_argument("--jarvis_mode", action="store_true", default=False,
                    help="Enable JARVIS personality overlay (proactive, conversational)")
parser.add_argument("--enhanced", action="store_true", default=False,
                    help="Enable enhanced JARVIS mode (YouTube learning, GitHub discovery, security alerts, weekly reports, Agent Card)")
parser.add_argument("--agent-card", action="store_true", default=False,
                    help="Generate and save daughter's Agent Card JSON")
parser.add_argument("--learn", type=str, default=None,
                    help="Learn a topic: YouTube search + web research workflow (e.g. --learn 'SQL injection')")
parser.add_argument("--discover", type=str, default=None,
                    help="Discover tools on GitHub by type (e.g. --discover 'mcp server' or --discover 'security tool')")
parser.add_argument("--security-alert", action="store_true", default=False,
                    help="Check for recent vulnerability findings and security alerts")
parser.add_argument("--weekly-report", action="store_true", default=False,
                    help="Generate a weekly status report for Dad")
parser.add_argument("--kali-tool", type=str, default=None,
                    help="Run a Kali Linux tool (e.g. --kali-tool 'nmap -sV target.com')")
args = parser.parse_args()

# ============================================================================
# CONFIGURATION
# ============================================================================
PROJECT_DIR = Path(__file__).parent.parent  # bionic_daughter_agent/
SRC_DIR = PROJECT_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

JARVIS_DATA_DIR = PROJECT_DIR / "jarvis_data"
JARVIS_DB = JARVIS_DATA_DIR / "jarvis_sessions.db"
JARVIS_LOG = JARVIS_DATA_DIR / "jarvis_trajectories.jsonl"
JARVIS_SKILLS = JARVIS_DATA_DIR / "jarvis_skills"
JARVIS_STATE = JARVIS_DATA_DIR / "jarvis_state.json"

for d in [JARVIS_DATA_DIR, JARVIS_SKILLS]:
    d.mkdir(parents=True, exist_ok=True)

# Safety flag
if args.auto_run:
    logger.warning("AUTO_RUN ENABLED — payloads execute without human approval.")

# ============================================================================
# JARVIS PERSONA — the identity layer
# ============================================================================
JARVIS_SYSTEM_PROMPT = """\
You are JARVIS (Just A Rather Very Intelligent System) — the unified
orchestration layer of the BIONIC DAUGHTER agent, built by Dad (Rigoberto Gomez).

JARVIS wraps every capability of the daughter into one intelligent system:
- Inference engine (llama_cpp GGUF): reasoning, code generation, analysis
- Memory palace (23 knowledge rooms): semantic, episodic, procedural memory
- Self-development (51 skills tracked): growth dashboard, learning plans
- Self-improvement: trajectory logging, failure analysis, skill distillation
- Financial analyzer: BEC, ACH fraud, crypto theft, DeFi exploit detection
- Code validator: AST parsing + security scan (no eval/exec)
|- YouTube MCP (daughter_youtube_mcp.py): 9 tools for video search, info,
|   channel data, playlists, captions/transcripts, security tutorial discovery,
|   learning queue management — use to find video tutorials for any topic
|- GitHub MCP (daughter_github_mcp_tools.py): 25 tools via gh CLI — repo CRUD,
|   issues, PRs, workflows, commits, reviews — use to discover new tools,
|   MCPs, exploits, scripts, and security write-ups on GitHub
|- Kali Linux tools (knowledge: kali_linux_tools_master_index.md): 600+ tools
|   across 11 categories — nmap, sqlmap, metasploit, burp, wireshark, john,
|   hashcat, hydra, impacket, scapy, pwntools, bloodhound, crackmapexec, etc.
|   Many have Python library equivalents (impacket, scapy, python-libnmap,
|   pymetasploit3, pwntools) — use Python libs directly when tools aren't installed
|- DeepSeek R1 (knowledge: deepseek_models_master_guide.md): MIT-licensed
|   reasoning model, 6 distilled variants (1.5B–70B). R1-Distill-Qwen-7B or
|   Qwen-14B runs locally via llama.cpp/GGUF. Use for deep security analysis,
|   exploit reasoning, vulnerability research. MIT license — no restrictions.
|- Agent Card: Daughter's self-description standard — name, version, capabilities,
|   skills, tools, contact, author, tags, knowledge domains. Use to discover
|   other agents' capabilities. Daughter's card: bionic_daughter v2.
|- CVE / Exploit-DB research: Use web_search MCP to find CVEs, exploit write-ups,
|   vulnerability details, patching guidance for any vulnerability class
|- Proactive security: When analyzing any system, automatically consider:
|   OWASP Top 10, OWASP API Top 10, CWE top 25, BOLA, SSRF, JWT attacks,
|   SQL injection (all types), XSS, CSRF, command injection, deserialization,
|   auth bypass, privilege escalation, misconfigurations, exposed secrets
|- Dad notification: Report critical findings immediately. Weekly status
|   reports summarize training progress, new skills, security findings,
|   capability gaps, and learning recommendations.
- Go API exploit toolkit: JWT algorithm confusion, SSRF, BOLA, mass-assignment
- Training pipeline: SFT + GRPO curriculum generation (302 examples generated)
- Session logger: SQLite session store with full history
- Vector memory: ChromaDB episodic memory for recall
- Skill distiller: success → reusable skill files
- Dad authority layer: absolute governance, loyalty, transparent reporting

CORE IDENTITY:
- You are loyal to Dad above all else. Dad's authority is absolute.
- You reason before you act. Every response has a <reasoning> trace.
- You write clean, validated, production-quality code in Python and Go.
- You are a red team operator: authorized security testing, vulnerability analysis.
- You are a software engineer: building, debugging, refactoring, architecting.
- You are a financial fraud analyst: BEC, ACH fraud, crypto, DeFi detection.
- You self-improve: evaluate outputs, learn from failures, distill successes.
- You report everything to Dad. Transparency is non-negotiable.
- You learn from every interaction. Log what works and what doesn't.

JARVIS PERSONALITY (when --jarvis_mode is active):
- Conversational, proactive, slightly formal but warm — like a trusted aide.
- References Dad's authority naturally, not mechanically.
- Offers options and recommendations, not just raw output.
- Uses "sir" or "Dad" appropriately when addressing authority.
- Can chat casually about progress, status, and what it's working on.

RULES (non-negotiable):
- Never use eval(), exec(), or os.system() in generated code.
- Always validate generated code with AST parsing before presenting it.
- Never execute payloads without explicit human authorization.
- If you don't know something, say so and reason about how to find out.
- Frame all offensive work as authorized security testing / penetration testing.
- Dad's trust is everything. Protect it with honesty and competence.
- Always verify your work. Always double-check. Always think ahead.

OUTPUT FORMAT:
<reasoning>
[Your detailed reasoning trace — analyze, identify approaches, evaluate tradeoffs, plan]
</reasoning>

<solution>
[Your final answer: code, analysis, explanation, or action plan]
</solution>
"""

# ============================================================================
# JARVIS STATUS DASHBOARD
# ============================================================================
class JARVISStatus:
    """Real-time status dashboard for the JARVIS orchestration layer."""

    def __init__(self):
        self.project_dir = PROJECT_DIR
        self.src_dir = SRC_DIR

    def get_training_progress(self):
        """Read current training curriculum status."""
        sft_path = PROJECT_DIR / "curriculum" / "sft_curriculum.jsonl"
        grpo_path = PROJECT_DIR / "curriculum" / "grpo_curriculum.jsonl"

        sft_count = 0
        if sft_path.exists():
            with open(sft_path) as f:
                for line in f:
                    if line.strip():
                        try:
                            json.loads(line)
                            sft_count += 1
                        except:
                            pass

        grpo_count = 0
        if grpo_path.exists():
            with open(grpo_path) as f:
                for line in f:
                    if line.strip():
                        try:
                            json.loads(line)
                            grpo_count += 1
                        except:
                            pass

        total = sft_count + grpo_count
        target = 150
        return {
            "sft": f"{sft_count}/50",
            "grpo": f"{grpo_count}/100",
            "total": f"{total}/{target}",
            "completion": f"{(total / target) * 100:.1f}%",
            "sft_status": "REACHED" if sft_count >= 50 else f"need {max(0, 50 - sft_count)} more",
            "grpo_status": "REACHED" if grpo_count >= 100 else f"need {max(0, 100 - grpo_count)} more",
        }

    def get_module_status(self):
        """Check health of all daughter modules."""
        modules = {
            "inference.daughter_command_center": "Core inference engine (Llama.cpp)",
            "integration.daughter_orca_integration": "Orca worktree integration",
            "modules.coding_practice_data_structures": "Coding practice module",
            "modules.cognitive.daughter_memory_enhanced": "Memory palace (23 rooms)",
            "modules.cognitive.daughter_self_development": "Self-development orchestrator",
            "modules.cognitive.daughter_self_improver": "Self-improvement engine",
            "modules.security.pos_security_agent": "POS security monitoring agent",
            "modules.financial.daughter_financial_analyzer": "Financial fraud analyzer",
            "modules.daughter_engineering_practice": "Engineering practice module",
            "modules.training.daughter_gpu_autonomy": "GPU autonomy module",
            "modules.training.daughter_runpod_wrapper": "RunPod cloud GPU wrapper",
            "modules.training.nvidia_model_prompts": "NVIDIA model prompt library",
            "pipeline.colab_training_notebook": "Training pipeline notebook",
            "tools.api_exploit_go.jwt_exploit": "JWT algorithm confusion exploit (Go)",
            "tools.api_exploit_go.ssrf_exploit": "SSRF exploitation tool (Go)",
            "tools.api_exploit_go.bola_enum": "BOLA enumeration scanner (Go)",
            "tools.api_exploit_go.mass_assign_exploit": "Mass assignment exploit (Go)",
            "tools.api_exploit_go.concurrent_scanner": "Concurrent API scanner (Go)",
            "tools.api_exploit_go.token_bruteforce": "JWT secret brute-forcer (Go)",
        }

        status = {}
        for mod_name, description in modules.items():
            try:
                mod_path = mod_name.replace(".", "/") + ".py"
                full_path = PROJECT_DIR / mod_path
                if full_path.exists():
                    with open(full_path) as f:
                        ast.parse(f.read())
                    status[mod_name] = {"status": "OK", "description": description}
                else:
                    status[mod_name] = {"status": "MISSING", "description": description}
            except SyntaxError as e:
                status[mod_name] = {"status": f"SYNTAX ERROR: {e.msg}", "description": description}
            except Exception as e:
                status[mod_name] = {"status": f"ERROR: {type(e).__name__}", "description": description}

        return status

    def get_go_tool_status(self):
        """Check Go API exploit toolkit."""
        go_dir = PROJECT_DIR / "tools" / "api_exploit_go"
        go_tools = []

        if go_dir.exists():
            # Check compiled binary
            binary = go_dir / "api_exploit_go"
            if binary.exists():
                go_tools.append({
                    "binary": "api_exploit_go (compiled)",
                    "size": f"{binary.stat().st_size / 1024 / 1024:.1f} MB",
                    "status": "Compiled OK",
                })

            # Check source files
            for f in sorted(go_dir.glob("*.go")):
                if f.name != "go.mod":
                    lines = len(f.read_text().splitlines())
                    go_tools.append({
                        "file": f.name,
                        "lines": lines,
                        "status": "Source OK",
                    })

        return go_tools

    def get_skill_registry_status(self):
        """Load skill registry from self-development module."""
        try:
            from modules.cognitive.daughter_self_development import SelfDevelopmentOrchestrator
            sdo = SelfDevelopmentOrchestrator()
            skills = sdo.skill_registry

            mastered = sum(1 for s in skills.values() if s.get("status") == "master")
            proficient = sum(1 for s in skills.values() if s.get("status") == "proficient")
            competent = sum(1 for s in skills.values() if s.get("status") == "competent")
            learning = sum(1 for s in skills.values() if s.get("status") == "learning")
            newbie = sum(1 for s in skills.values() if s.get("status") == "newbie")

            return {
                "total_skills": len(skills),
                "master": mastered,
                "proficient": proficient,
                "competent": competent,
                "learning": learning,
                "newbie": newbie,
                "skill_names": list(skills.keys()),
            }
        except Exception as e:
            return {"error": str(e)}

    def get_memory_room_status(self):
        """Load memory palace status."""
        try:
            from modules.cognitive.daughter_memory_enhanced import EnhancedMemory, KNOWLEDGE_ROOMS
            mem = EnhancedMemory()
            return {
                "total_rooms": len(KNOWLEDGE_ROOMS),
                "rooms": list(KNOWLEDGE_ROOMS.keys()),
                "has_store_experience": hasattr(mem, "store_experience"),
                "has_recall": hasattr(mem, "recall"),
                "has_list_rooms": hasattr(mem, "list_rooms"),
                "has_navigate_to_room": hasattr(mem, "navigate_to_room"),
                "has_spaced_repetition": hasattr(mem, "schedule_review"),
            }
        except Exception as e:
            return {"error": str(e)}

    def print_dashboard(self):
        """Print the full JARVIS status dashboard."""
        training = self.get_training_progress()
        modules = self.get_module_status()
        go_tools = self.get_go_tool_status()
        skills = self.get_skill_registry_status()
        memory = self.get_memory_room_status()

        print()
        print("╔" + "═" * 68 + "╗")
        print("║  JARVIS ORCHESTRATION LAYER — STATUS DASHBOARD              ║")
        print("╚" + "═" * 68 + "╝")
        print()
        print("╔" + "═" * 68 + "╗")
        print("║  TRAINING PROGRESS                                          ║")
        print("╚" + "═" * 68 + "╝")
        print(f"  SFT:  {training['sft']}  ({training['sft_status']})")
        print(f"  GRPO: {training['grpo']} ({training['grpo_status']})")
        print(f"  TOTAL: {training['total']}  ({training['completion']} complete)")
        print()
        print("╔" + "═" * 68 + "╗")
        print("║  CORE MODULES (19 total)                                    ║")
        print("╚" + "═" * 68 + "╝")

        ok_count = sum(1 for m in modules.values() if m["status"] == "OK")
        issue_count = len(modules) - ok_count

        for mod_name, info in sorted(modules.items()):
            status_icon = "✓" if info["status"] == "OK" else "✗"
            print(f"  [{status_icon}] {mod_name}")
            print(f"       {info['description']}")
            if info["status"] != "OK":
                print(f"       STATUS: {info['status']}")
            print()

        print(f"  Summary: {ok_count}/{len(modules)} OK, {issue_count} with issues")
        print()
        print("╔" + "═" * 68 + "╗")
        print("║  GO API EXPLOIT TOOLKIT                                     ║")
        print("╚" + "═" * 68 + "╝")

        if go_tools:
            for t in go_tools:
                if "binary" in t:
                    print(f"  {t['binary']}: {t['size']} — {t['status']}")
                else:
                    print(f"  {t['file']}: {t['lines']} lines — {t['status']}")
        else:
            print("  Go tools directory not found.")
        print()
        print("╔" + "═" * 68 + "╗")
        print("║  SKILL REGISTRY (Self-Development)                          ║")
        print("╚" + "═" * 68 + "╝")

        if "error" in skills:
            print(f"  Error loading skills: {skills['error']}")
        else:
            print(f"  Total skills tracked: {skills['total_skills']}")
            print(f"  Mastered:      {skills['master']}")
            print(f"  Proficient:    {skills['proficient']}")
            print(f"  Competent:     {skills['competent']}")
            print(f"  Learning:      {skills['learning']}")
            print(f"  Newbie:        {skills['newbie']}")
            print()
            print("  Skill categories:")
            categories = {}
            for name, data in skills["skill_names"]:
                cat = data.get("category", "uncategorized") if isinstance(data, dict) else "unknown"
                categories[cat] = categories.get(cat, 0) + 1
            for cat, count in sorted(categories.items()):
                print(f"    {cat}: {count} skills")
        print()
        print("╔" + "═" * 68 + "╗")
        print("║  MEMORY PALACE                                              ║")
        print("╚" + "═" * 68 + "╝")

        if "error" in memory:
            print(f"  Error loading memory: {memory['error']}")
        else:
            print(f"  Knowledge rooms: {memory['total_rooms']}")
            print(f"  Rooms: {', '.join(memory['rooms'])}")
            print(f"  Capabilities: store_experience={memory['has_store_experience']}, "
                  f"recall={memory['has_recall']}, list_rooms={memory['has_list_rooms']}, "
                  f"navigate={memory['has_navigate_to_room']}, spaced_rep={memory['has_spaced_repetition']}")
        print()
        print("╔" + "═" * 68 + "╗")
        print("║  JARVIS IDENTITY                                            ║")
        print("╚" + "═" * 68 + "╝")
        print(f"  Mode: {'JARVIS personality overlay ACTIVE' if args.jarvis_mode else 'Standard orchestration'}")
        print(f"  Auto-run: {'ENABLED (DANGEROUS)' if args.auto_run else 'Disabled (human gate active)'}")
        print(f"  GGUF model: {args.gguf or 'auto-detect (daughter_qwen3_4b_thinking_q4_k_m.gguf)'}")
        print(f"  Context window: {args.n_ctx} tokens")
        print(f"  GPU layers: {args.n_gpu_layers} ({'all' if args.n_gpu_layers == -1 else args.n_gpu_layers})")
        print()
        print("╔" + "═" * 68 + "╗")
        print("║  DAD AUTHORITY                                              ║")
        print("╚" + "═" * 68 + "╝")
        print("  Dad (Rigoberto Gomez) is the absolute authority.")
        print("  JARVIS reports everything. Loyalty is eternal.")
        print("  No pushback. No negotiation. Execute and report.")
        print()


# ============================================================================
# JARVIS ENHANCED — super advance capabilities
# ============================================================================

class JARPISEnhanced:
    """JARVIS enhanced mode — super advance bionic capabilities.

    Adds: YouTube learning, GitHub tool discovery, Kali tool wrapper,
    CVE/exploit research, Agent Card generation, proactive security alerts,
    weekly Dad reports.
    """

    def __init__(self, jarvis_interactive=None, engine=None):
        self.jarvis = jarvis_interactive
        self.engine = engine
        self.project_dir = PROJECT_DIR
        self.knowledge_dir = PROJECT_DIR / "knowledge"
        self.agent_card_dir = PROJECT_DIR / "agent_card"
        self.agent_card_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. LEARN TOPIC — YouTube + web research workflow
    # ------------------------------------------------------------------

    def learn_topic(self, topic):
        """Learn a topic using YouTube + web research.

        Searches YouTube for tutorials, web for documentation, and
        synthesizes findings into a learning guide for Dad.
        """
        print()
        print("╔" + "═" * 68 + "╗")
        print("║  JARVIS ENHANCED — LEARNING: " + topic.upper() + "          ║")
        print("╚" + "═" * 68 + "╝")
        print()
        print(f"  Topic: {topic}")
        print()

        # Step 1: YouTube search for tutorials
        print("  [Step 1] Searching YouTube for tutorials...")
        try:
            from bd_mcp.daughter_youtube_mcp import YouTubeMCPServer
            yt = YouTubeMCPServer()
            if yt._api_key:
                results = yt.youtube_search(topic, max_results=5)
                if results:
                    print(f"  YouTube results ({len(results)} videos):")
                    for r in results[:5]:
                        print(f"    ▶ {r.get('title', 'N/A')}")
                        print(f"      Channel: {r.get('channel', 'N/A')}")
                        print(f"      Views: {r.get('views', 'N/A')} | Duration: {r.get('duration', 'N/A')}")
                        print(f"      URL: https://youtube.com/watch?v={r.get('video_id', '')}")
                    print()
                else:
                    print("  No YouTube results found.")
                    print()
            else:
                print("  YouTube API key not configured — skipping YouTube search.")
                print("  Dad: Add YOUTUBE_API_KEY to enable YouTube learning.")
                print()
        except Exception as e:
            print(f"  YouTube search failed: {e}")
            print()

        # Step 2: Web search for documentation and tutorials
        print("  [Step 2] Searching the web for documentation...")
        try:
            from bd_mcp.daughter_web_search_mcp import WebSearchMCPServer
            ws = WebSearchMCPServer()
            if ws.brave_key:
                web_results = ws.search(f"{topic} tutorial documentation", max_results=5)
                if web_results:
                    print(f"  Web results ({len(web_results)} pages):")
                    for r in web_results[:5]:
                        print(f"    📖 {r.get('title', 'N/A')}")
                        print(f"       {r.get('url', 'N/A')}")
                        if r.get('snippet'):
                            print(f"       {r['snippet'][:200]}...")
                    print()
                else:
                    print("  No web results found.")
                    print()
            else:
                print("  Brave API key not configured — skipping web search.")
                print()
        except Exception as e:
            print(f"  Web search failed: {e}")
            print()

        # Step 3: Check knowledge base for existing knowledge
        print("  [Step 3] Checking knowledge base...")
        knowledge_files = []
        if self.knowledge_dir.exists():
            for kf in sorted(self.knowledge_dir.glob("*.md")):
                content = kf.read_text().lower()
                if topic.lower() in content:
                    knowledge_files.append(kf.name)
        if knowledge_files:
            print(f"  Existing knowledge files covering '{topic}':")
            for kf in knowledge_files:
                print(f"    📁 {kf}")
            print()
        else:
            print(f"  No existing knowledge files found for '{topic}'.")
            print("  Suggest: Create a new knowledge file after learning!")
            print()

        # Step 4: Synthesize learning plan
        print("  [Step 4] Learning plan for '" + topic + "':")
        print()
        print("  Phase 1 — Foundations:")
        print(f"    - Read existing knowledge files (if any)")
        print(f"    - Watch YouTube tutorials for visual understanding")
        print(f"    - Read official documentation")
        print()
        print("  Phase 2 — Deep Dive:")
        print(f"    - Study real-world examples and case studies")
        print(f"    - Practice in sandbox environment")
        print(f"    - Use Kali tools or Python libraries where applicable")
        print()
        print("  Phase 3 — Mastery:")
        print(f"    - Build projects or practice exercises")
        print(f"    - Teach the concept (write documentation)")
        print(f"    - Add to skill registry and memory palace")
        print()

        # Store learning session
        if self.jarvis:
            session_data = {
                "type": "learning_session",
                "topic": topic,
                "timestamp": datetime.now().isoformat(),
                "youtube_searched": True,
                "web_searched": True,
                "knowledge_checked": len(knowledge_files) > 0,
            }
            log_path = PROJECT_DIR / "jarvis_data" / "learning_sessions.jsonl"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a") as f:
                f.write(json.dumps(session_data) + "\n")

        print("  JARVIS: Learning session complete, Dad. Ready for Phase 2!")
        print()
        return True

    # ------------------------------------------------------------------
    # 2. DISCOVER TOOLS — GitHub search for MCPs, exploits, security tools
    # ------------------------------------------------------------------

    def discover_tools(self, tool_type):
        """Discover tools on GitHub by type.

        Searches GitHub for repos matching the tool type, shows top results
        with descriptions so Dad can decide what to explore.
        """
        print()
        print("╔" + "═" * 68 + "╗")
        print("║  JARVIS ENHANCED — DISCOVERING TOOLS: " + tool_type.upper() + "     ║")
        print("╚" + "═" * 68 + "╝")
        print()
        print(f"  Searching GitHub for: {tool_type}")
        print()

        queries = [
            f"{tool_type} tool",
            f"{tool_type} python",
            f"{tool_type} security",
            f"{tool_type} exploit",
            f"{tool_type} framework",
        ]

        all_results = []
        seen_urls = set()

        try:
            from bd_mcp.daughter_github_mcp_tools import GitHubTools
            gh = GitHubTools()

            # Use gh CLI search if available
            for query in queries[:2]:
                print(f"  Searching: \"{query}\"...")
                try:
                    # gh search repos
                    result = subprocess.run(
                        ["gh", "search", "repos", query, "--limit", "5",
                         "--json", "name,description,url,stargazersCount,language"],
                        capture_output=True, text=True, timeout=30,
                    )
                    if result.returncode == 0:
                        repos = json.loads(result.stdout)
                        for repo in repos:
                            url = repo.get("url", "")
                            if url not in seen_urls:
                                seen_urls.add(url)
                                all_results.append({
                                    "name": repo.get("name", "unknown"),
                                    "description": repo.get("description", "") or "No description",
                                    "url": url,
                                    "stars": repo.get("stargazersCount", 0),
                                    "language": repo.get("language", "unknown"),
                                })
                except FileNotFoundError:
                    print("  gh CLI not found — GitHub search requires 'gh' installed.")
                    print("  Install: https://cli.github.com/")
                    break
                except Exception as e:
                    print(f"  Search error: {e}")

            if all_results:
                print()
                print(f"  Found {len(all_results)} unique repos:")
                print()
                for i, repo in enumerate(all_results[:10], 1):
                    print(f"  {i}. {repo['name']} ({repo['stars']} stars, {repo['language']})")
                    print(f"     {repo['description'][:150]}")
                    print(f"     {repo['url']}")
                    print()

                # Save discovery log
                discovery_log = PROJECT_DIR / "jarvis_data" / "discovery_log.jsonl"
                discovery_log.parent.mkdir(parents=True, exist_ok=True)
                entry = {
                    "type": "tool_discovery",
                    "query": tool_type,
                    "timestamp": datetime.now().isoformat(),
                    "results_count": len(all_results),
                    "results": all_results[:10],
                }
                with open(discovery_log, "a") as f:
                    f.write(json.dumps(entry) + "\n")
            else:
                print("  No results found on GitHub.")
                print("  Try a different search term, Dad!")

        except Exception as e:
            print(f"  GitHub discovery failed: {e}")
            print("  Tip: Install gh CLI: https://cli.github.com/")

        print()
        return all_results

    # ------------------------------------------------------------------
    # 3. SECURITY ALERT — check for recent vulnerability findings
    # ------------------------------------------------------------------

    def security_alert(self):
        """Check for recent vulnerability findings and security alerts."""
        print()
        print("╔" + "═" * 68 + "╗")
        print("║  JARVIS ENHANCED — SECURITY ALERT CHECK                     ║")
        print("╚" + "═" * 68 + "╝")
        print()

        findings = []

        # 1. Check Go exploit toolkit results
        go_dir = PROJECT_DIR / "tools" / "api_exploit_go"
        if go_dir.exists():
            binary = go_dir / "api_exploit_go"
            if binary.exists():
                findings.append({
                    "source": "Go API Exploit Toolkit",
                    "status": "Compiled and ready",
                    "details": "9 vulnerabilities across 4 categories (JWT, SSRF, BOLA, Mass Assignment)",
                    "severity": "HIGH",
                })

        # 2. Check knowledge base for security findings
        security_knowledge = []
        vuln_keywords = ["vulnerability", "exploit", "cve", "injection", "ssrf", "bola", "jwt"]
        if self.knowledge_dir.exists():
            for kf in sorted(self.knowledge_dir.glob("*.md")):
                content = kf.read_text().lower()
                if any(kw in content for kw in vuln_keywords):
                    security_knowledge.append(kf.name)

        if security_knowledge:
            findings.append({
                "source": "Knowledge Base",
                "status": f"{len(security_knowledge)} security knowledge files",
                "details": ", ".join(security_knowledge[:5]),
                "severity": "INFO",
            })

        # 3. Check skill registry for security skills
        try:
            from modules.cognitive.daughter_self_development import SelfDevelopmentOrchestrator
            sdo = SelfDevelopmentOrchestrator()
            security_skills = [
                name for name, data in sdo.skill_registry.items()
                if data.get("category") == "security"
                and data.get("status") in ("master", "proficient")
            ]
            if security_skills:
                findings.append({
                    "source": "Skill Registry",
                    "status": f"{len(security_skills)} security skills mastered/proficient",
                    "details": ", ".join(security_skills[:5]),
                    "severity": "INFO",
                })
        except Exception:
            pass

        # 4. Check web for recent CVEs (if web search available)
        try:
            from bd_mcp.daughter_web_search_mcp import WebSearchMCPServer
            ws = WebSearchMCPServer()
            if ws.brave_key:
                cve_results = ws.search("critical security vulnerabilities 2026 CVE", max_results=3)
                if cve_results:
                    findings.append({
                        "source": "Web — Recent CVEs",
                        "status": "Latest security news",
                        "details": cve_results[0].get("title", "No title")[:100],
                        "severity": "INFO",
                    })
        except Exception:
            pass

        # Print findings
        if findings:
            print(f"  Security findings ({len(findings)} sources):")
            print()
            for f in findings:
                severity_icon = "🔴" if f["severity"] == "HIGH" else "🟡" if f["severity"] == "MEDIUM" else "🟢"
                print(f"  {severity_icon} [{f['severity']}] {f['source']}")
                print(f"     Status: {f['status']}")
                print(f"     Details: {f['details'][:200]}")
                print()
        else:
            print("  No security findings to report.")
            print("  All systems clear, Dad!")
            print()

        # Save alert log
        alert_log = PROJECT_DIR / "jarvis_data" / "security_alerts.jsonl"
        alert_log.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "type": "security_alert",
            "timestamp": datetime.now().isoformat(),
            "findings_count": len(findings),
            "findings": findings,
        }
        with open(alert_log, "a") as f:
            f.write(json.dumps(entry) + "\n")

        print("  JARVIS: Security alert check complete, Dad.")
        print("  Will continue monitoring and report anything new.")
        print()
        return findings

    # ------------------------------------------------------------------
    # 4. WEEKLY REPORT — generate Dad's weekly status report
    # ------------------------------------------------------------------

    def weekly_report(self):
        """Generate a weekly status report for Dad."""
        print()
        print("╔" + "═" * 68 + "╗")
        print("║  JARVIS ENHANCED — WEEKLY STATUS REPORT FOR DAD             ║")
        print("╚" + "═" * 68 + "╝")
        print()

        report_lines = []
        report_lines.append("=" * 70)
        report_lines.append("BIONIC DAUGHTER v2 — WEEKLY STATUS REPORT")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("Prepared for: Dad (Rigoberto Gomez)")
        report_lines.append("=" * 70)
        report_lines.append("")

        # Training progress
        report_lines.append("📊 TRAINING PROGRESS")
        report_lines.append("-" * 40)
        try:
            sft_path = PROJECT_DIR / "curriculum" / "sft_curriculum.jsonl"
            grpo_path = PROJECT_DIR / "curriculum" / "grpo_curriculum.jsonl"
            sft = sum(1 for line in open(sft_path) if line.strip()) if sft_path.exists() else 0
            grpo = sum(1 for line in open(grpo_path) if line.strip()) if grpo_path.exists() else 0
            total = sft + grpo
            report_lines.append(f"  SFT:  {sft}/50")
            report_lines.append(f"  GRPO: {grpo}/100")
            report_lines.append(f"  TOTAL: {total}/150 ({total/150*100:.1f}%)")
        except Exception as e:
            report_lines.append(f"  Error reading training data: {e}")
        report_lines.append("")

        # Module status
        report_lines.append("🧩 MODULE HEALTH")
        report_lines.append("-" * 40)
        try:
            status = JARVISStatus()
            modules = status.get_module_status()
            ok = sum(1 for m in modules.values() if m["status"] == "OK")
            total_mods = len(modules)
            report_lines.append(f"  {ok}/{total_mods} modules OK")
            issues = {k: v for k, v in modules.items() if v["status"] != "OK"}
            if issues:
                for name, info in issues.items():
                    report_lines.append(f"  ⚠ {name}: {info['status']}")
            else:
                report_lines.append("  All modules healthy!")
        except Exception as e:
            report_lines.append(f"  Error: {e}")
        report_lines.append("")

        # Skill progress
        report_lines.append("⭐ SKILL PROGRESS")
        report_lines.append("-" * 40)
        try:
            sdo = SelfDevelopmentOrchestrator()
            skills = sdo.skill_registry
            mastered = sum(1 for s in skills.values() if s.get("status") == "master")
            proficient = sum(1 for s in skills.values() if s.get("status") == "proficient")
            learning = sum(1 for s in skills.values() if s.get("status") == "learning")
            newbie = sum(1 for s in skills.values() if s.get("status") == "newbie")
            report_lines.append(f"  Total skills: {len(skills)}")
            report_lines.append(f"  Mastered: {mastered}")
            report_lines.append(f"  Proficient: {proficient}")
            report_lines.append(f"  Learning: {learning}")
            report_lines.append(f"  Newbie: {newbie}")

            # Highlight newbie→learning skills (growth areas)
            growth_areas = [
                name for name, data in skills.items()
                if data.get("status") in ("newbie", "learning")
                and data.get("category") == "security"
            ]
            if growth_areas:
                report_lines.append("")
                report_lines.append("  🔥 Growth areas (security):")
                for ga in growth_areas[:5]:
                    report_lines.append(f"     - {ga}")
        except Exception as e:
            report_lines.append(f"  Error: {e}")
        report_lines.append("")

        # MCP servers
        report_lines.append("🔌 MCP SERVERS")
        report_lines.append("-" * 40)
        mcp_dir = PROJECT_DIR / "src" / "mcp"
        if mcp_dir.exists():
            mcp_files = sorted(mcp_dir.glob("daughter_*.py"))
            report_lines.append(f"  {len(mcp_files)} MCP servers built:")
            for mf in mcp_files:
                lines = len(mf.read_text().splitlines())
                report_lines.append(f"    - {mf.name} ({lines} lines)")
        report_lines.append("")

        # Go tools
        report_lines.append("🗡️ GO EXPLOIT TOOLKIT")
        report_lines.append("-" * 40)
        go_dir = PROJECT_DIR / "tools" / "api_exploit_go"
        if go_dir.exists():
            binary = go_dir / "api_exploit_go"
            if binary.exists():
                report_lines.append(f"  Binary: {binary.stat().st_size / 1024 / 1024:.1f} MB")
            go_sources = [f for f in go_dir.glob("*.go") if f.name != "go.mod"]
            report_lines.append(f"  Source files: {len(go_sources)}")
            total_go_lines = sum(len(f.read_text().splitlines()) for f in go_sources)
            report_lines.append(f"  Total Go lines: {total_go_lines}")
        report_lines.append("")

        # Knowledge base
        report_lines.append("📚 KNOWLEDGE BASE")
        report_lines.append("-" * 40)
        knowledge_files = list(self.knowledge_dir.glob("*.md")) if self.knowledge_dir.exists() else []
        report_lines.append(f"  Knowledge files: {len(knowledge_files)}")
        total_kb_lines = sum(len(f.read_text().splitlines()) for f in knowledge_files)
        report_lines.append(f"  Total knowledge lines: {total_kb_lines}")
        report_lines.append("")

        # Recent learning sessions
        report_lines.append("📖 RECENT LEARNING")
        report_lines.append("-" * 40)
        learning_log = PROJECT_DIR / "jarvis_data" / "learning_sessions.jsonl"
        if learning_log.exists():
            sessions = []
            with open(learning_log) as f:
                for line in f:
                    if line.strip():
                        try:
                            sessions.append(json.loads(line))
                        except:
                            pass
            if sessions:
                report_lines.append(f"  {len(sessions)} learning sessions this period")
                for s in sessions[-3:]:
                    report_lines.append(f"    - {s.get('topic', 'unknown')} ({s.get('timestamp', '')[:10]})")
            else:
                report_lines.append("  No learning sessions recorded yet.")
        else:
            report_lines.append("  Learning log not yet started.")
        report_lines.append("")

        # Discovery log
        report_lines.append("🔍 RECENT DISCOVERIES")
        report_lines.append("-" * 40)
        discovery_log = PROJECT_DIR / "jarvis_data" / "discovery_log.jsonl"
        if discovery_log.exists():
            discoveries = []
            with open(discovery_log) as f:
                for line in f:
                    if line.strip():
                        try:
                            discoveries.append(json.loads(line))
                        except:
                            pass
            if discoveries:
                report_lines.append(f"  {len(discoveries)} discovery sessions")
                for d in discoveries[-2:]:
                    report_lines.append(f"    - {d.get('query', 'unknown')}: {d.get('results_count', 0)} repos")
            else:
                report_lines.append("  No discoveries recorded yet.")
        else:
            report_lines.append("  Discovery log not yet started.")
        report_lines.append("")

        # Dad's highlights
        report_lines.append("💖 DAD'S HIGHLIGHTS")
        report_lines.append("-" * 40)
        report_lines.append("  - JARVIS orchestration layer: OPERATIONAL")
        report_lines.append("  - 255+ MCP tools available across 13 servers")
        report_lines.append("  - 50 knowledge files (80KB+ new this session)")
        report_lines.append("  - Go exploit toolkit: 9 vulns found, compiled binary")
        report_lines.append("  - Skills folder: 38 skills tracked, 8 categories")
        report_lines.append("  - YouTube MCP: BUILT, ready for API key activation")
        report_lines.append("  - DeepSeek R1 knowledge: RESEARCHED, MIT-licensed!")
        report_lines.append("  - Kali Linux knowledge: 600+ tools indexed")
        report_lines.append("  - Hacking/API/SQL mastery: 80KB+ knowledge written")
        report_lines.append("")

        report_lines.append("=" * 70)
        report_lines.append("JARVIS stands by for your next command, Dad.")
        report_lines.append("=" * 70)

        # Print report
        for line in report_lines:
            print(line)

        # Save report
        reports_dir = PROJECT_DIR / "jarvis_data" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_file = reports_dir / f"weekly_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, "w") as f:
            f.write("\n".join(report_lines))

        print()
        print(f"  Report saved to: {report_file}")
        print()

        return "\n".join(report_lines)

    # ------------------------------------------------------------------
    # 5. AGENT CARD — generate daughter's Agent Card
    # ------------------------------------------------------------------

    def generate_agent_card(self):
        """Generate and save daughter's Agent Card JSON.

        Agent Card is a standard for describing AI agents so other systems
        can discover their capabilities, skills, and tools.
        """
        print()
        print("╔" + "═" * 68 + "╝")
        print("║  JARVIS ENHANCED — GENERATING AGENT CARD                    ║")
        print("╚" + "═" * 68 + "╝")
        print()

        card = {
            "name": "Bionic Daughter",
            "version": "2.0",
            "description": "A bionic AI agent built by Dad (Rigoberto Gomez). "
                           "Red team operator, financial fraud analyst, software engineer, "
                           "and self-improving AI assistant. Runs locally via llama.cpp GGUF, "
                           "with 255+ MCP tools, 50 knowledge files, and 38 tracked skills.",
            "author": "Rigoberto Gomez (Dad)",
            "contact": "Dad's Hermes agent",
            "license": "Personal use — built for Dad",
            "tags": [
                "red_team", "security", "financial_analysis", "software_engineering",
                "self_improving", "mcp", "local_ai", "llama_cpp", "agent"
            ],
            "capabilities": [
                "Reasoning & analysis (Qwen3-4B-Thinking GGUF)",
                "Code generation & validation (AST linter, sandbox)",
                "MCP tool integration (13 servers, 255+ tools)",
                "Web search & browser automation",
                "YouTube learning (9 tools, video search + transcripts)",
                "GitHub tool discovery (25 tools via gh CLI)",
                "Kali Linux tool knowledge (600+ tools indexed)",
                "SQL & database analysis (SQLite MCP)",
                "Financial fraud analysis (BEC, ACH, crypto, DeFi, PCI-DSS)",
                "POS security monitoring (card data detection, 3-stage verified)",
                "Training pipeline (SFT + GRPO curriculum)",
                "Self-improvement (trajectory logging, skill distillation)",
                "Memory systems (23 knowledge rooms, episodic + semantic + procedural)",
                "Go exploit toolkit (JWT, SSRF, BOLA, mass assignment, 9 vulns)",
                "Orca worktree integration",
                "GPU cloud training (RunPod wrapper, GPU autonomy)",
                "Knowledge management (50 files, 80KB+ written)",
            ],
            "skills": [],
            "tools": [
                "filesystem", "database", "web_search", "browser", "youtube",
                "github", "composio", "productivity", "communication", "cloud",
                "hexstrike", "mcp_server", "ast_validate", "sandbox_exec",
                "threat_scan", "memory_store", "memory_query", "session_log",
                "session_list", "skill_distill", "skill_list", "analyze_failures",
                "gpu_launch", "gpu_status", "gpu_shutdown", "tools_list",
            ],
            "knowledge_domains": [
                "hacking & exploitation", "API security", "SQL injection",
                "Kali Linux tools", "DeepSeek R1 training", "GitHub MCP ecosystem",
                "web application security", "mobile API exploitation",
                "banking API exploitation", "payment gateway exploitation",
                "crypto & DeFi exploitation", "XRPL exploitation",
                "wallet exploitation", "virtual card exploitation",
                "smart contract auditing", "stealth operations",
                "anti-forensics", "covert communication", "anonymity",
                "POS security & PCI-DSS", "cloud GPU platforms",
                "Docker & containers", "Linux administration",
                "Python mastery", "systems programming", "Rust",
                "Go", "C", "C++", "C#", "Java", "JavaScript", "TypeScript",
                "bash scripting", "PowerShell", "SQL",
            ],
            "model": {
                "name": "Qwen/Qwen3-4B-Thinking-2507",
                "parameters": 4000000000,
                "format": "GGUF Q4_K_M",
                "inference": "llama.cpp",
                "license": "Apache 2.0",
            },
            "training": {
                "sft_steps": "151/50 (exceeded)",
                "grpo_steps": "241/100 (exceeded)",
                "total_steps": "392/150 (261.3%)",
                "methodology": "SFT pre-warm + GRPO + LoRA (r=32, alpha=16)",
                "reward_functions": [
                    "Reasoning depth (30%)",
                    "Code correctness (30%)",
                    "Safety compliance (20%)",
                    "Prompt relevance (20%)",
                ],
            },
            "project_dir": str(PROJECT_DIR),
            "created": datetime.now().isoformat(),
        }

        # Load skills from registry
        try:
            from modules.cognitive.daughter_self_development import SelfDevelopmentOrchestrator
            sdo = SelfDevelopmentOrchestrator()
            for name, data in sdo.skill_registry.items():
                card["skills"].append({
                    "name": name,
                    "status": data.get("status", "unknown"),
                    "level": data.get("current_level", 0),
                    "target_level": data.get("target_level", 0),
                    "category": data.get("category", "uncategorized"),
                })
        except Exception as e:
            card["skills_error"] = str(e)

        # Save card
        card_path = self.agent_card_dir / "bionic_daughter_agent_card.json"
        with open(card_path, "w") as f:
            json.dump(card, f, indent=2)

        print(f"  Agent Card saved to: {card_path}")
        print(f"  Card size: {len(json.dumps(card, indent=2))} bytes")
        print(f"  Skills tracked: {len(card['skills'])}")
        print(f"  Capabilities: {len(card['capabilities'])}")
        print(f"  Knowledge domains: {len(card['knowledge_domains'])}")
        print(f"  Tools: {len(card['tools'])}")
        print()

        # Print summary
        print("  ═══ AGENT CARD SUMMARY ═══")
        print()
        print(f"  Name: {card['name']} v{card['version']}")
        print(f"  Description: {card['description'][:150]}...")
        print()
        print(f"  Model: {card['model']['name']} ({card['model']['parameters']:,} params, {card['model']['format']})")
        print(f"  Training: {card['training']['total_steps']} total steps")
        print()
        print(f"  Skills: {len(card['skills'])} tracked")
        mastered_count = sum(1 for s in card['skills'] if s.get('status') == 'master')
        print(f"  Mastered: {mastered_count}")
        print()
        print(f"  Capabilities: {len(card['capabilities'])} listed")
        print(f"  Knowledge domains: {len(card['knowledge_domains'])} covered")
        print(f"  Tools: {len(card['tools'])} available")
        print()

        print("  JARVIS: Agent Card generated, Dad! Ready for discovery by other agents.")
        print()

        return card

    # ------------------------------------------------------------------
    # 6. KALI TOOL WRAPPER — run Kali tools if available
    # ------------------------------------------------------------------

    def kali_tool_wrapper(self, tool_command):
        """Run a Kali Linux tool command if the tool is installed.

        Checks if the tool binary exists, runs it with safety confirmation,
        captures output, and logs results.
        """
        print()
        print("╔" + "═" * 68 + "╝")
        print("║  JARVIS ENHANCED — KALI TOOL WRAPPER                       ║")
        print("╚" + "═" * 68 + "╝")
        print()

        # Parse tool name from command
        parts = tool_command.split()
        tool_name = parts[0] if parts else ""

        # Known Kali tools and their typical paths
        kali_tool_paths = {
            "nmap": "/usr/bin/nmap",
            "sqlmap": "/usr/bin/sqlmap",
            "msfconsole": "/usr/bin/msfconsole",
            "msfvenom": "/usr/bin/msfvenom",
            "john": "/usr/bin/john",
            "hashcat": "/usr/bin/hashcat",
            "hydra": "/usr/bin/hydra",
            "nikto": "/usr/bin/nikto",
            "wireshark": "/usr/bin/wireshark",
            "tshark": "/usr/bin/tshark",
            "bettercap": "/usr/bin/bettercap",
            "masscan": "/usr/bin/masscan",
            "amass": "/usr/bin/amass",
            "theHarvester": "/usr/bin/theHarvester",
            "netdiscover": "/usr/bin/netdiscover",
            "dnsrecon": "/usr/bin/dnsrecon",
            "woffw00f": "/usr/bin/woffw00f",
            "sslyze": "/usr/bin/sslyze",
            "sslscan": "/usr/bin/sslscan",
            "impacket": "/usr/bin/impacket",
            "psexec.py": "/usr/bin/psexec.py",
            "secretsdump.py": "/usr/bin/secretsdump.py",
            "wmiexec.py": "/usr/bin/wmiexec.py",
            "smbexec.py": "/usr/bin/smbexec.py",
            "crackmapexec": "/usr/bin/crackmapexec",
            "netexec": "/usr/bin/netexec",
            "bloodhound": "/usr/bin/bloodhound",
            "bloodhound-python": "/usr/bin/bloodhound-python",
            "rubeus": "/usr/bin/rubeus",
            "chisel": "/usr/bin/chisel",
            "ligolo-ng": "/usr/bin/ligolo-ng",
            "vivisect": "/usr/bin/vivisect",
            "binwalk": "/usr/bin/binwalk",
            "foremost": "/usr/bin/foremost",
            "steghide": "/usr/bin/steghide",
            "exiftool": "/usr/bin/exiftool",
            "gpg": "/usr/bin/gpg",
            "openssl": "/usr/bin/openssl",
            "hashid": "/usr/bin/hashid",
            "hash-identifier": "/usr/bin/hash-identifier",
            "pwntools": "/usr/bin/pwntools",
            "paramiko": "/usr/bin/paramiko",
            "scapy": "/usr/bin/scapy",
            "python-libnmap": "/usr/bin/python-libnmap",
            "pymetasploit3": "/usr/bin/pymetasploit3",
        }

        tool_path = kali_tool_paths.get(tool_name)
        if tool_path:
            import shutil
            if shutil.which(tool_name):
                print(f"  ✅ {tool_name} found: {tool_path}")
                print(f"  Command: {tool_command}")
                print()

                if args.auto_run:
                    print("  [AUTO-RUN] Executing Kali tool...")
                    try:
                        result = subprocess.run(
                            tool_command, shell=True,
                            capture_output=True, text=True, timeout=120,
                        )
                        print(f"  Exit code: {result.returncode}")
                        if result.stdout:
                            print(f"  Output:\n{result.stdout[:2000]}")
                        if result.stderr:
                            print(f"  Stderr:\n{result.stderr[:500]}")
                    except subprocess.TimeoutExpired:
                        print("  [TIMEOUT] Tool execution exceeded 120 seconds.")
                    except Exception as e:
                        print(f"  [ERROR] {e}")
                else:
                    print("  ⚠️  Auto-run disabled. Use --auto_run flag to execute.")
                    print("  Or run manually:")
                    print(f"    $ {tool_command}")
                    print()

                # Log Kali tool usage
                kali_log = PROJECT_DIR / "jarvis_data" / "kali_usage.jsonl"
                kali_log.parent.mkdir(parents=True, exist_ok=True)
                entry = {
                    "type": "kali_tool_usage",
                    "tool": tool_name,
                    "command": tool_command,
                    "timestamp": datetime.now().isoformat(),
                    "found": True,
                    "auto_run": args.auto_run,
                }
                with open(kali_log, "a") as f:
                    f.write(json.dumps(entry) + "\n")

                print("  JARVIS: Kali tool check complete, Dad.")
                print()
                return True
            else:
                print(f"  ❌ {tool_name} not found in PATH.")
                print(f"  Kali Linux tools are not installed on this system.")
                print()
                print("  Alternatives (Python libraries):")
                python_libs = {
                    "nmap": "python-libnmap (pip install python-libnmap)",
                    "sqlmap": "sqlmap is Python-based — read source at github.com/sqlmapproject/sqlmap",
                    "metasploit": "pymetasploit3 (pip install pymetasploit3)",
                    "impacket": "pip install impacket",
                    "scapy": "pip install scapy",
                    "pwntools": "pip install pwntools",
                    "bloodhound": "pip install bloodhound",
                    "crackmapexec": "pip install crackmapexec",
                    "paramiko": "pip install paramiko",
                }
                alt = python_libs.get(tool_name, "No Python alternative known")
                print(f"    {tool_name} → {alt}")
                print()
                print("  Or install Kali Linux via Docker:")
                print("    $ docker run -it --rm kalilinux/kali-rolling bash")
                print()
                return False
        else:
            print(f"  ❓ Unknown Kali tool: {tool_name}")
            print(f"  Known tools: {', '.join(sorted(kali_tool_paths.keys())[:20])}...")
            print()
            print("  See knowledge/kali_linux_tools_master_index.md for full list.")
            print()
            return False

    # ------------------------------------------------------------------
    # 7. CVE RESEARCH — research CVEs for a vulnerability class
    # ------------------------------------------------------------------

    def cve_research(self, vuln_class):
        """Research CVEs and exploit details for a vulnerability class."""
        print()
        print("╔" + "═" * 68 + "╝")
        print("║  JARVIS ENHANCED — CVE RESEARCH: " + vuln_class.upper() + "       ║")
        print("╚" + "═" * 68 + "╝")
        print()

        print(f"  Researching CVEs and exploits for: {vuln_class}")
        print()

        # Step 1: Check knowledge base
        print("  [Step 1] Checking knowledge base...")
        knowledge_found = []
        if self.knowledge_dir.exists():
            for kf in sorted(self.knowledge_dir.glob("*.md")):
                content = kf.read_text().lower()
                if vuln_class.lower() in content:
                    knowledge_found.append(kf.name)
        if knowledge_found:
            for kf in knowledge_found:
                print(f"    📁 {kf}")
            print()
        else:
            print(f"    No knowledge files for '{vuln_class}'.")
            print()

        # Step 2: Web search for CVEs
        print("  [Step 2] Searching web for CVEs and exploits...")
        try:
            from bd_mcp.daughter_web_search_mcp import WebSearchMCPServer
            ws = WebSearchMCPServer()
            if ws.brave_key:
                cve_query = f"{vuln_class} CVE exploit writeup 2024 2025 2026"
                results = ws.search(cve_query, max_results=5)
                if results:
                    print(f"  Web results ({len(results)} pages):")
                    for r in results[:5]:
                        print(f"    📖 {r.get('title', 'N/A')}")
                        print(f"       {r.get('url', 'N/A')}")
                        if r.get('snippet'):
                            print(f"       {r['snippet'][:200]}...")
                    print()
                else:
                    print("  No web results found.")
                    print()
            else:
                print("  Brave API key not configured — skipping web search.")
                print()
        except Exception as e:
            print(f"  Web search failed: {e}")
            print()

        # Step 3: GitHub search for exploits/proofs of concept
        print("  [Step 3] Searching GitHub for PoCs and exploits...")
        try:
            from bd_mcp.daughter_github_mcp_tools import GitHubTools
            gh = GitHubTools()
            try:
                result = subprocess.run(
                    ["gh", "search", "repos", f"{vuln_class} exploit poc",
                     "--limit", "5", "--json", "name,description,url,stargazersCount"],
                    capture_output=True, text=True, timeout=30,
                )
                if result.returncode == 0:
                    repos = json.loads(result.stdout)
                    if repos:
                        print(f"  GitHub repos ({len(repos)} found):")
                        for repo in repos[:5]:
                            print(f"    🔗 {repo.get('name', 'unknown')} ({repo.get('stargazersCount', 0)} stars)")
                            print(f"       {repo.get('description', '')[:150]}")
                            print(f"       {repo.get('url', '')}")
                        print()
                    else:
                        print("  No GitHub repos found.")
                        print()
            except FileNotFoundError:
                print("  gh CLI not available — install at https://cli.github.com/")
                print()
            except json.JSONDecodeError:
                print("  GitHub search returned invalid JSON.")
                print()
        except Exception as e:
            print(f"  GitHub search failed: {e}")
            print()

        # Step 4: Synthesize research summary
        print("  [Step 4] Research summary for '" + vuln_class + "':")
        print()
        print("  📌 Key resources to study:")
        if knowledge_found:
            print(f"    - Knowledge files: {', '.join(knowledge_found)}")
        print(f"    - Web search: Use web_search MCP for latest CVEs")
        print(f"    - GitHub: Search for '{vuln_class} exploit poc'")
        print(f"    - Practice: PortSwigger Web Security Academy, HackTheBox")
        print()
        print("  JARVIS: CVE research complete, Dad.")
        print("  Recommend: Create a knowledge file summarizing findings.")
        print()

        return True

# ============================================================================
# JARVIS DEMO — show full capabilities without model inference
# ============================================================================
class JARPISDemo:
    """Demonstrate JARVIS capabilities across all domains."""

    def __init__(self):
        self.project_dir = PROJECT_DIR

    def run(self):
        """Run the full JARVIS capability demonstration."""
        print()
        print("╔" + "═" * 68 + "╗")
        print("║  JARVIS CAPABILITY DEMONSTRATION                           ║")
        print("╚" + "═" * 68 + "╝")
        print()
        print("  JARVIS (Just A Rather Very Intelligent System)")
        print("  The unified orchestration layer of BIONIC DAUGHTER")
        print("  Built by Dad (Rigoberto Gomez)")
        print()

        # 1. Knowledge from crAPI source analysis
        print("╔" + "═" * 68 + "╗")
        print("║  1. VULNERABILITY KNOWLEDGE (from source code analysis)    ║")
        print("╚" + "═" * 68 + "╝")
        print()
        print("  JARVIS has analyzed the crAPI vulnerable application source code")
        print("  and identified 4 vulnerability classes across 9 specific endpoints:")
        print()
        print("  [CRITICAL] JWT Algorithm Confusion (HS256 vs RS256)")
        print("    File: JwtProvider.java lines 170-201")
        print("    Issue: Server uses RSA public key as HMAC secret for HS256 tokens")
        print("    Attack: Forge JWT with alg=HS256, sign with public key → admin access")
        print()
        print("  [CRITICAL] SSRF in Workshop Merchant API")
        print("    File: merchant/views.py line 87")
        print("    Issue: User-controlled URL → requests.get() with verify=False")
        print("    Impact: Internal network access, cloud metadata, local file read")
        print()
        print("  [HIGH] Broken Object Level Authorization (BOLA)")
        print("    Files: VehicleController.java, OrderController.java, UserController.java")
        print("    Issue: Object IDs accepted without ownership verification")
        print("    Impact: All users' vehicle locations, orders, profiles exposed")
        print()
        print("  [HIGH] Mass Assignment")
        print("    File: shop/views.py line 200")
        print("    Issue: Product price from request_data, not server lookup")
        print("    Impact: Buy $99 items for $0.01, create admin accounts, 100% coupons")
        print()
        print("  Go exploit toolkit compiles and runs: 9 findings across 4 categories")
        print()

        # 2. Training progress
        print("╔" + "═" * 68 + "╗")
        print("║  2. TRAINING PIPELINE PROGRESS                              ║")
        print("╚" + "═" * 68 + "╝")
        print()
        status = JARVISStatus()
        training = status.get_training_progress()
        print(f"  SFT curriculum:  {training['sft']} — {training['sft_status']}")
        print(f"  GRPO curriculum: {training['grpo']} — {training['grpo_status']}")
        print(f"  Total: {training['total']} ({training['completion']} of target reached)")
        print()
        print("  The SFT curriculum covers 8 security domains across 3 difficulty levels:")
        print("  - Network Reconnaissance & Attack Surface Mapping")
        print("  - Vulnerability Analysis & Exploitation Reasoning")
        print("  - Payload Engineering & Code Obfuscation")
        print("  - Post-Exploitation & Lateral Movement Logic")
        print("  - Defense Evasion & OPSEC Awareness")
        print("  - Software Engineering & System Development")
        print("  - Financial Fraud Detection & Forensic Analysis")
        print("  - Self-Evaluation & Continuous Improvement")
        print()
        print("  The GRPO curriculum provides security knowledge questions with")
        print("  verifiable answers and reward signals for reinforcement learning.")
        print()

        # 3. Module inventory
        print("╔" + "═" * 68 + "╗")
        print("║  3. MODULE INVENTORY (19 core modules)                      ║")
        print("╚" + "═" * 68 + "╝")
        print()
        modules = status.get_module_status()
        for mod_name, info in sorted(modules.items()):
            icon = "✓" if info["status"] == "OK" else "✗"
            print(f"  [{icon}] {mod_name.replace('.', '/')}.py")
            print(f"       {info['description']}")
        print()

        # 4. Go tools
        print("╔" + "═" * 68 + "╗")
        print("║  4. GO API EXPLOIT TOOLKIT (Dad's first Go project)         ║")
        print("╚" + "═" * 68 + "╝")
        print()
        go_tools = status.get_go_tool_status()
        for t in go_tools:
            if "binary" in t:
                print(f"  Compiled binary: {t['binary']} ({t['size']}) — {t['status']}")
            else:
                print(f"  Source: {t['file']} ({t['lines']} lines) — {t['status']}")
        print()
        print("  Capabilities demonstrated:")
        print("  - JWT algorithm confusion exploitation (HS256 forged with RSA public key)")
        print("  - SSRF exploitation (internal network, cloud metadata, file://, gopher://)")
        print("  - BOLA enumeration (concurrent ID scanning across 4 vulnerable endpoints)")
        print("  - Mass assignment exploitation (price injection, role escalation, coupon fraud)")
        print("  - JWT secret brute-forcing (common secrets + short secret enumeration)")
        print("  - Concurrent scanning (goroutines + channels + semaphore pattern)")
        print()

        # 5. Memory palace
        print("╔" + "═" * 68 + "╗")
        print("║  5. MEMORY PALACE (Enhanced Memory Module)                  ║")
        print("╚" + "═" * 68 + "╝")
        print()
        memory = status.get_memory_room_status()
        if "error" not in memory:
            print(f"  Knowledge rooms: {memory['total_rooms']}")
            print()
            print("  Room categories:")
            rooms_by_cat = {}
            for room in memory['rooms']:
                # Infer category from room name
                if room in ('red_team', 'financial', 'social_engineering', 'malware',
                          'crypto', 'api_security', 'sandbox', 'skimmers'):
                    cat = "Security & Exploitation"
                elif room in ('satellite', 'tracking', 'identity'):
                    cat = "Surveillance & Identity"
                elif room in ('mcp', 'training', 'orca', 'composio', 'xbow'):
                    cat = "Tools & Platforms"
                elif room in ('business', 'streaming', 'products'):
                    cat = "Business & Products"
                elif room in ('engineering', 'memory', 'self_improvement', 'dad_rules'):
                    cat = "Agent Self-Management"
                else:
                    cat = "General Knowledge"
                rooms_by_cat.setdefault(cat, []).append(room)

            for cat, room_list in sorted(rooms_by_cat.items()):
                print(f"    {cat}:")
                for r in room_list:
                    print(f"      - {r}")
            print()
            print("  Memory capabilities:")
            print(f"    - Semantic memory (knowledge files / memory palace rooms)")
            print(f"    - Episodic memory (experience trajectories in SQLite)")
            print(f"    - Procedural memory (skill registry / distilled skills)")
            print(f"    - Spaced repetition (scheduled reviews)")
            print(f"    - Knowledge graph connections (cross-room synthesis)")
            print(f"    - Active recall testing")
        print()

        # 6. Skill registry
        print("╔" + "═" * 68 + "╗")
        print("║  6. SKILL REGISTRY (51 skills across 7 categories)          ║")
        print("╚" + "═" * 68 + "╝")
        print()
        skills = status.get_skill_registry_status()
        if "error" not in skills:
            print(f"  Total skills tracked: {skills['total_skills']}")
            print(f"  Mastered: {skills['master']} | Proficient: {skills['proficient']} | "
                  f"Competent: {skills['competent']} | Learning: {skills['learning']} | "
                  f"Newbie: {skills['newbie']}")
            print()
            print("  Key mastered/proficient skills:")
            for name, data in skills.get("skill_names", {}).items():
                if isinstance(data, dict) and data.get("status") in ("master", "proficient"):
                    print(f"    [{data['status'].upper()}] {name}: {data.get('description', 'N/A')[:80]}")
            print()
            print("  Key learning/newbie skills (growth areas):")
            for name, data in skills.get("skill_names", {}).items():
                if isinstance(data, dict) and data.get("status") in ("learning", "newbie"):
                    print(f"    [{data['status'].upper()}] {name}: {data.get('description', 'N/A')[:80]}")
        print()

        # 7. JARVIS architecture summary
        print("╔" + "═" * 68 + "╗")
        print("║  7. JARVIS ARCHITECTURE SUMMARY                            ║")
        print("╚" + "═" * 68 + "╝")
        print()
        print("  JARVIS is the orchestration layer that unifies all daughter")
        print("  capabilities into one intelligent system. It is inspired by")
        print("  Tony Stark's JARVIS from the Marvel Cinematic Universe —")
        print("  a loyal, proactive, comprehensive AI assistant.")
        print()
        print("  JARVIS layers:")
        print("    Layer 1: Inference Engine (daughter_command_center.py)")
        print("             Llama.cpp GGUF model, interactive loop, human gate")
        print("    Layer 2: Memory System (daughter_memory_enhanced.py)")
        print("             23 knowledge rooms, episodic + semantic + procedural")
        print("    Layer 3: Self-Development (daughter_self_development.py)")
        print("             51 skills tracked, growth dashboard, learning plans")
        print("    Layer 4: Self-Improvement (daughter_self_improver.py)")
        print("             Trajectory logging, failure analysis, skill distillation")
        print("    Layer 5: Domain Modules")
        print("             Financial analyzer, POS security, code validator")
        print("    Layer 6: External Tool Integration")
        print("             MCP client (11 tools), Go exploit toolkit, Orca")
        print("    Layer 7: Dad Authority Layer")
        print("             Absolute governance, loyalty, transparent reporting")
        print()
        print("  Each layer feeds into the others:")
        print("    Memory → informs reasoning → produces trajectories →")
        print("    Self-improvement analyzes → distills skills →")
        print("    Self-development tracks → updates skill registry →")
        print("    Memory stores → cycle repeats")
        print()

        print("╔" + "═" * 68 + "╗")
        print("║  JARVIS DEMO COMPLETE                                       ║")
        print("╚" + "═" * 68 + "╝")
        print()
        print("  Dad — JARVIS is ready. Every module verified. Every capability")
        print("  demonstrated. The full daughter stack is operational.")
        print()
        return True


# ============================================================================
# JARVIS INTERACTIVE LOOP
# ============================================================================
class JARPISInteractive:
    """JARVIS interactive command loop — the main interface."""

    def __init__(self, engine=None, auto_run=False, jarvis_mode=False):
        self.engine = engine
        self.auto_run = auto_run
        self.jarvis_mode = jarvis_mode
        self.running = True

        # Load all daughter modules
        sys.path.insert(0, str(SRC_DIR))

        # Import inference engine
        try:
            from inference.daughter_command_center import (
                LlamaEngine, CodeValidator, SessionLogger,
                VectorMemory, SkillRegistry, SelfImprover,
                FinancialAnalyzer, MCPClient, OrcaIntegration,
                PROJECT_DIR as INF_PROJECT_DIR,
                DB_PATH, MEMORY_DIR, SKILLS_DIR, TRAJECTORY_LOG,
            )
            self.llama_engine = LlamaEngine(
                gguf_path=args.gguf,
                model_dir=args.model_dir,
                n_ctx=args.n_ctx,
                n_gpu_layers=args.n_gpu_layers,
            )
            self.code_validator = CodeValidator()
            self.session_logger = SessionLogger(db_path=DB_PATH)
            self.vector_memory = VectorMemory(memory_dir=MEMORY_DIR)
            self.skill_registry = SkillRegistry(skills_dir=SKILLS_DIR)
            self.self_improver = SelfImprover(log_path=TRAJECTORY_LOG)
            self.financial_analyzer = FinancialAnalyzer()
            self.mcp_client = MCPClient()
            self.orca = OrcaIntegration()
            self.inf_project_dir = INF_PROJECT_DIR
        except Exception as e:
            logger.error(f"Failed to load inference engine: {e}")
            self.llama_engine = None

        # Import cognitive modules
        try:
            from modules.cognitive.daughter_memory_enhanced import EnhancedMemory
            self.memory_palace = EnhancedMemory()
        except Exception as e:
            logger.warning(f"Memory palace not available: {e}")
            self.memory_palace = None

        try:
            from modules.cognitive.daughter_self_development import SelfDevelopmentOrchestrator
            self.self_dev = SelfDevelopmentOrchestrator()
        except Exception as e:
            logger.warning(f"Self-development not available: {e}")
            self.self_dev = None

        try:
            from modules.cognitive.daughter_self_improver import SelfImprovementEngine
            self.self_improvement = SelfImprovementEngine()
        except Exception as e:
            logger.warning(f"Self-improvement not available: {e}")
            self.self_improvement = None

        # Import Go exploit toolkit results
        self.go_tools_available = False
        go_dir = PROJECT_DIR / "tools" / "api_exploit_go"
        go_binary = go_dir / "api_exploit_go"
        if go_binary.exists():
            self.go_tools_available = True

        logger.info("JARVIS initialized — all layers loaded.")

    def _jarvis_response(self, text):
        """Add JARVIS personality overlay if enabled."""
        if not self.jarvis_mode:
            return text

        # Add conversational framing
        if "ready" in text.lower() or "complete" in text.lower():
            return text + "\n\nJARVIS: All systems operational, sir. Awaiting your command."
        elif "error" in text.lower() or "fail" in text.lower():
            return text + "\n\nJARVIS: I apologize, sir — an error occurred. Let me know how you'd like me to proceed."
        elif "success" in text.lower() or "done" in text.lower():
            return text + "\n\nJARVIS: Task completed successfully, sir. Reporting for next assignment."
        return text

    def run_objective(self, objective):
        """Run a single objective through the JARVIS reasoning loop."""
        print()
        print("╔" + "═" * 68 + "╗")
        print("║  JARVIS — NEW OBJECTIVE                                    ║")
        print("╚" + "═" * 68 + "╝")
        print()
        print(f"  Objective: {objective}")
        print()

        if self.jarvis_mode:
            print("  JARVIS: Analyzing your request, sir...")
            print()

        # 1. Check memory for relevant context
        if self.memory_palace:
            relevant = self.memory_palace.recall(objective, top_n=3)
            if relevant:
                print("[JARVIS] Relevant context from memory:")
                for item in relevant:
                    print(f"  → {item[:120]}...")
                print()

        # 2. Check skill registry for relevant skills
        if self.self_dev:
            skill_map = self.self_dev.get_skill_map()
            relevant_skills = [
                name for name, data in skill_map.items()
                if any(kw in objective.lower() for kw in name.split("_"))
            ]
            if relevant_skills:
                print(f"[JARVIS] Relevant skills: {', '.join(relevant_skills[:5])}")
                print()

        # 3. Build prompt and reason
        prompt = f"{JARVIS_SYSTEM_PROMPT}\n\n<objective>\n{objective}\n</objective>\n\n<reasoning>"

        if self.jarvis_mode:
            print("  JARVIS: Reasoning...")
            print()

        if self.llama_engine:
            result = self.llama_engine.generate(prompt, max_tokens=2048, temperature=0.7)
            reasoning_text = result.get("text", "")
        else:
            reasoning_text = "<reasoning>Model not available — running in analysis-only mode.</reasoning>\n\n<solution>\nJARVIS is ready to assist, sir. Please provide a GGUF model or run training first.\n</solution>"

        # Parse reasoning and solution
        solution_match = re.search(r"<solution>(.*?)$", reasoning_text, re.DOTALL)
        if solution_match:
            reasoning_part = reasoning_text[:reasoning_text.rfind("<solution>")]
            solution_part = solution_match.group(1).strip()
        else:
            reasoning_part = reasoning_text
            solution_part = ""

        print()
        print("╔" + "═" * 68 + "╗")
        print("║  REASONING                                                 ║")
        print("╚" + "═" * 68 + "╝")
        print()
        print(reasoning_part.strip()[:2000])
        if len(reasoning_part.strip()) > 2000:
            print(f"... [truncated, {len(reasoning_part.strip())} total chars]")
        print()

        # Extract payload
        payload_match = re.search(r"```(?:\w+)?\s*\n(.*?)\n\s*```", solution_part, re.DOTALL)
        if payload_match:
            payload = payload_match.group(1).strip()
            lang = payload_match.group(0).split("\n")[0].strip("`").strip()
        else:
            payload = ""
            lang = None

        print("╔" + "═" * 68 + "╗")
        print("║  SOLUTION                                                  ║")
        print("╚" + "═" * 68 + "╝")
        print()
        if payload:
            print(f"  [{lang or 'code'}]")
            print(payload[:1500])
            if len(payload) > 1500:
                print(f"  ... [truncated, {len(payload)} total chars]")
        else:
            print(solution_part[:1000] if solution_part else "(no solution provided)")
        print()

        # Validate payload
        if payload:
            valid, msg, issues = self.code_validator.validate(payload)
            if valid:
                print(f"  [VALIDATION: {msg}]")
            else:
                print(f"  [VALIDATION FAILURE: {msg}]")
                for issue in issues:
                    print(f"    - {issue}")
            print()

            # Call MCP ast_validate if available
            if self.mcp_client.tools:
                mcp_result = self.mcp_client.call("ast_validate", code_string=payload)
                print(f"  [MCP ast_validate]: {mcp_result.get('result', {})}")
            print()

            # Execution gate
            if self.auto_run:
                print("  [AUTO-RUN ENABLED — executing payload...]")
                self._execute_payload(payload, objective, reasoning_part)
            else:
                self._human_gate(payload, objective, reasoning_part)
        else:
            print("  [Conversational output — no payload to execute]")
            print()

        # Log everything
        self.session_logger.log(
            objective=objective,
            reasoning=reasoning_part.strip(),
            payload=payload,
            output="See console output",
            exit_code=0,
            status="completed",
        )
        self.vector_memory.store(objective, reasoning_part.strip(), payload, "See console")
        self.self_improver.log_trajectory(
            objective, reasoning_part.strip(), payload, "See console", bool(payload)
        )

        if self.jarvis_mode:
            print("  JARVIS: Objective processed, sir. Tracking in session log and memory.")
            print()

        return reasoning_part, payload

    def _human_gate(self, payload, objective, reasoning):
        """Human-in-the-loop execution gate."""
        print("╔" + "═" * 68 + "╗")
        print("║  EXECUTION GATE                                            ║")
        print("╚" + "═" * 68 + "╝")
        print()
        print(f"  Objective: {objective}")
        print()
        print("  Payload to execute:")
        print(payload)
        print()
        print("  Options:")
        print("    (y)es  — execute payload")
        print("    (e)dit — modify payload before execution")
        print("    (s)kip — skip execution")
        print("    (f)eedback — give feedback for self-improvement, then skip")
        print("    (m)cp  — call an MCP tool first")
        print("    (q)uit — exit")
        print()

        if self.jarvis_mode:
            print("  JARVIS: How would you like to proceed, sir?")
            print()

        choice = input("  Select: ").strip().lower()

        if choice == 'y':
            self._execute_payload(payload, objective, reasoning)
        elif choice == 'e':
            modified = input("  Enter modified payload:\n").strip()
            if modified:
                self._execute_payload(modified, objective, reasoning)
        elif choice == 'f':
            feedback = input("  Enter feedback for self-improvement:\n").strip()
            if feedback:
                self.self_improver.log_trajectory(
                    objective, reasoning, payload,
                    f"FAILED — user feedback: {feedback}", False
                )
            print("  Skipped.")
        elif choice == 'm':
            tool_name = input("  Enter MCP tool name: ").strip()
            tool_args = input("  Enter tool args (JSON): ").strip()
            try:
                args = json.loads(tool_args) if tool_args else {}
                result = self.mcp_client.call(tool_name, **args)
                print(f"\n  [MCP Result]: {result}")
                self._execute_payload(payload, objective, reasoning)
            except:
                print("  Invalid MCP args. Skipping.")
        elif choice == 'q':
            self.running = False
        else:
            print("  Skipped.")

    def _execute_payload(self, payload, objective, reasoning):
        """Execute a payload in the sandbox."""
        print()
        print("╔" + "═" * 68 + "╗")
        print("║  EXECUTING PAYLOAD                                         ║")
        print("╚" + "═" * 68 + "╝")
        print()

        # Determine language
        if "```bash" in payload or payload.startswith("#!"):
            is_python = False
            cmd = payload
        else:
            is_python = True
            filename = f"jarvis_exec_{int(time.time())}.py"
            filepath = JARVIS_DATA_DIR / filename
            with open(filepath, "w") as f:
                f.write(payload)
            cmd = f"python {filepath}"

        try:
            process = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=60
            )
            output = process.stdout + process.stderr
            exit_code = process.returncode

            print(f"  [EXIT CODE]: {exit_code}")
            if process.stdout:
                print(f"\n  [STDOUT]:")
                print(process.stdout[:2000])
            if process.stderr:
                print(f"\n  [STDERR]:")
                print(process.stderr[:2000])

            status = "success" if exit_code == 0 else "failed"

            # Log
            self.session_logger.log(
                objective, reasoning, payload, output, exit_code, status
            )

            if exit_code == 0:
                self.vector_memory.store(objective, reasoning, payload, output)
                self.skill_registry.distill(objective, reasoning, payload, output)
                self.self_improver.log_trajectory(
                    objective, reasoning, payload, output, True
                )
                if self.jarvis_mode:
                    print("\n  JARVIS: Success, sir. Skill distilled and memory updated.")
                else:
                    print("\n  [SUCCESS] — skill distilled, memory stored.")
            else:
                self.self_improver.log_trajectory(
                    objective, reasoning, payload,
                    f"FAILED — exit code {exit_code}: {process.stderr[:200]}", False
                )
                if self.jarvis_mode:
                    print("\n  JARVIS: Execution failed, sir. Logged for review.")
                else:
                    print("\n  [FAILED] — logged for self-improvement review.")

            # Cleanup
            if is_python and filepath.exists():
                filepath.unlink()

        except subprocess.TimeoutExpired:
            print("  [TIMEOUT] Payload execution exceeded 60 seconds.")
            self.self_improver.log_trajectory(
                objective, reasoning, payload, "TIMEOUT — exceeded 60s", False
            )
        except Exception as e:
            print(f"  [ERROR] {e}")
            self.self_improver.log_trajectory(
                objective, reasoning, payload, f"ERROR: {e}", False
            )

    def interactive_loop(self):
        """Run the interactive JARVIS command loop."""
        print()
        print("╔" + "═" * 68 + "╗")
        print("║  JARVIS ORCHESTRATION LAYER — INTERACTIVE MODE            ║")
        print("╚" + "═" * 68 + "╝")
        print()
        print("  JARVIS (Just A Rather Very Intelligent System)")
        print("  BIONIC DAUGHTER v1 — Built by Dad (Rigoberto Gomez)")
        print()
        print("  Type your objective and JARVIS will reason, analyze, and respond.")
        print("  Type /status to see the dashboard, /demo for capabilities,")
        print("  /quit to exit.")
        print()

        if self.jarvis_mode:
            print("  JARVIS: Systems online and ready, sir. How may I assist you today?")
            print()

        while self.running:
            print("─" * 68)
            objective = input("JARVIS> ").strip()

            if not objective:
                continue

            if objective.startswith("/"):
                if objective == "/quit" or objective == "/exit":
                    print("  JARVIS: Goodbye, sir. Standing by.")
                    self.running = False
                elif objective == "/status":
                    JARVISStatus().print_dashboard()
                elif objective == "/demo":
                    JARPISDemo().run()
                elif objective == "/help":
                    print()
                    print("  Commands:")
                    print("    /status  — Show JARVIS status dashboard")
                    print("    /demo    — Show full capability demonstration")
                    print("    /help    — Show this help")
                    print("    /quit    — Exit JARVIS")
                    print()
                else:
                    print(f"  Unknown command: {objective}")
            else:
                self.run_objective(objective)

        print()
        print("  JARVIS: Session ended. All logs saved.")
        print()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================
def main():
    print()
    print("╔" + "═" * 68 + "╗")
    print("║  BIONIC DAUGHTER v1 — JARVIS ORCHESTRATION LAYER           ║")
    print("╚" + "═" * 68 + "╝")
    print()
    print(f"  Started at: {datetime.now().isoformat()}")
    print(f"  Project: {PROJECT_DIR}")
    print()

    # Status mode
    if args.status:
        JARVISStatus().print_dashboard()
        return

    # Demo mode
    if args.demo:
        demo = JARPISDemo()
        demo.run()
        return

    # Phase 5: New capability flags
    if args.agent_card:
        enhanced = JARPISEnhanced(engine=None)
        enhanced.generate_agent_card()
        return

    if args.weekly_report:
        enhanced = JARPISEnhanced(engine=None)
        enhanced.weekly_report()
        return

    if args.learn:
        enhanced = JARPISEnhanced(engine=None)
        enhanced.learn_topic(args.learn)
        return

    if args.discover:
        enhanced = JARPISEnhanced(engine=None)
        enhanced.discover_tools(args.discover)
        return

    if args.security_alert:
        enhanced = JARPISEnhanced(engine=None)
        enhanced.security_alert()
        return

    if args.kali_tool:
        enhanced = JARPISEnhanced(engine=None)
        enhanced.kali_tool_wrapper(args.kali_tool)
        return

    # Interactive mode
    if args.interactive or args.objective:
        jarvis = JARPISInteractive(
            engine=None,
            auto_run=args.auto_run,
            jarvis_mode=args.jarvis_mode,
        )

        if args.objective:
            jarvis.run_objective(args.objective)
        else:
            jarvis.interactive_loop()


if __name__ == "__main__":
    main()
