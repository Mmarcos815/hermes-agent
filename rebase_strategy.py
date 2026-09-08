#!/usr/bin/env python3
"""
Rebase Strategy Script for my 1st (GRPO Training Code)
=====================================================

Analyzes 5,067 commits between HEAD and origin/main to produce a safe,
step-by-step rebase plan. Our GRPO training code is independent of Hermes core,
so most upstream changes can be accepted automatically.

Usage:
    python rebase_strategy.py            # Full analysis + plan
    python rebase_strategy.py --guide    # Print step-by-step rebase guide
    python rebase_strategy.py --dry-run  # Show what would be skipped
"""

import subprocess
import sys
import re
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent

# Our key files - commits touching these need manual review
KEY_FILES = [
    "grpo_reward_engine.py",
    "grpo_training_config.yaml",
    "grpo_train.py",
    "colab_train.py",
    "mini_swe_runner.py",
    "batch_runner.py",
]

# Core Hermes files we do NOT touch - upstream changes here are safe to accept
CORE_FILES = [
    "agent/auxiliary_client.py",
    "agent/chat_completion_helpers.py",
    "gateway/run.py",
    "agent/context_compressor.py",
    "agent/conversation_compression.py",
    "hermes_cli/web_server.py",
    "gateway/slash_commands.py",
    "agent/conversation_loop.py",
    "tools/computer_use/tool.py",
    "agent/agent_init.py",
    "hermes_cli/main.py",
    "gateway/run_turn.py",
    "gateway/run_startup.py",
    "tools/process_registry.py",
    "tools/delegate_tool.py",
    "gateway/platforms/base.py",
    "gateway/hosted_rooms.py",
    "hermes_cli/plugins.py",
    "hermes_cli/gateway.py",
    "hermes_cli/cli_commands_mixin.py",
]

# Commit categories (ordered by priority for review)
CATEGORY_PATTERNS = {
    "security": re.compile(r"security|vuln|cve|auth|exploit|xss|injection|sanitize|permission|credential|token|secret", re.I),
    "breaking": re.compile(r"breaking|breaks|deprecated|removes|removal|drop|delete", re.I),
    "fix": re.compile(r"^fix(\(|:)", re.I),
    "feat": re.compile(r"^feat(\(|:)", re.I),
    "refactor": re.compile(r"^refactor(\(|:)", re.I),
    "test": re.compile(r"^test(\(|:)", re.I),
    "chore": re.compile(r"^chore(\(|:)", re.I),
    "docs": re.compile(r"^docs(\(|:)", re.I),
    "fmt": re.compile(r"^fmt(\(|:)", re.I),
    "style": re.compile(r"^style(\(|:)", re.I),
    "ci": re.compile(r"^ci(\(|:)", re.I),
    "merge": re.compile(r"^merge", re.I),
}

# Safe-to-skip patterns (mechanical, AST-identical, or unrelated)
SKIP_PATTERNS = [
    re.compile(r"^fmt(\(|:)", re.I),
    re.compile(r"^style(\(|:)", re.I),
    re.compile(r"^ci(\(|:)", re.I),
    re.compile(r"^merge", re.I),
    re.compile(r"^chore:.*release", re.I),
    re.compile(r"^chore:.*email", re.I),
    re.compile(r"refactor.*AST-identical", re.I),
    re.compile(r"refactor.*dead.code", re.I),
    re.compile(r"refactor.*compact", re.I),
    re.compile(r"refactor.*dedupe", re.I),
    re.compile(r"^test.*deterministic", re.I),
    re.compile(r"^docs.*dormant", re.I),
]


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def git(args, check=True):
    """Run a git command and return stdout."""
    result = subprocess.run(
        f"git {args}",
        shell=True,
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {args} failed: {result.stderr}")
    return result.stdout


def get_merge_base():
    """Find the merge base between HEAD and origin/main."""
    return git("merge-base HEAD origin/main").strip()


def get_upstream_commits():
    """Get all commits between HEAD and origin/main with metadata."""
    log = git("log HEAD..origin/main --format='%H%x00%s%x00%an%x00%ad%x00' --date=short")
    commits = []
    for line in log.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("\x00")
        if len(parts) >= 4:
            commits.append({
                "hash": parts[0],
                "subject": parts[1],
                "author": parts[2],
                "date": parts[3],
            })
    return commits


def get_commit_files(commit_hash):
    """Get files changed by a specific commit."""
    out = git(f"log -1 --name-only --format='' {commit_hash}")
    return [f.strip() for f in out.strip().split("\n") if f.strip()]


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def categorize_commit(subject):
    """Categorize a commit by its subject line."""
    for cat, pattern in CATEGORY_PATTERNS.items():
        if pattern.search(subject):
            return cat
    return "other"


def is_safe_to_skip(subject, files):
    """Determine if a commit can be safely skipped during rebase."""
    for pattern in SKIP_PATTERNS:
        if pattern.search(subject):
            return True, f"matches skip pattern: {pattern.pattern}"
    return False, ""


def analyze_commits(commits):
    """Analyze all upstream commits and produce statistics."""
    stats = {
        "total": len(commits),
        "by_category": defaultdict(int),
        "by_author": defaultdict(int),
        "by_date": defaultdict(int),
        "security_commits": [],
        "breaking_commits": [],
    }
    for c in commits:
        cat = categorize_commit(c["subject"])
        stats["by_category"][cat] += 1
        stats["by_author"][c["author"]] += 1
        stats["by_date"][c["date"]] += 1
        if CATEGORY_PATTERNS["security"].search(c["subject"]):
            stats["security_commits"].append(c)
        if CATEGORY_PATTERNS["breaking"].search(c["subject"]):
            stats["breaking_commits"].append(c)
    return stats


def find_key_file_conflicts(commits):
    """Find commits that touch our key files."""
    conflicts = []
    for c in commits:
        files = get_commit_files(c["hash"])
        key_touched = [f for f in files if f in KEY_FILES]
        if key_touched:
            conflicts.append({
                "hash": c["hash"],
                "subject": c["subject"],
                "files": key_touched,
                "all_files": files,
            })
    return conflicts


# ---------------------------------------------------------------------------
# Plan generation
# ---------------------------------------------------------------------------

def generate_rebase_plan(commits, stats):
    """Generate a structured rebase plan."""
    plan = {
        "merge_base": get_merge_base(),
        "total_commits": len(commits),
        "safe_skip_count": 0,
        "review_count": 0,
        "conflict_risk": "low",
        "safe_to_skip": [],
        "needs_review": [],
    }
    for c in commits:
        files = get_commit_files(c["hash"])
        skip, reason = is_safe_to_skip(c["subject"], files)
        key_touched = any(f in KEY_FILES for f in files)
        if key_touched:
            plan["needs_review"].append({
                "hash": c["hash"],
                "subject": c["subject"],
                "files": [f for f in files if f in KEY_FILES],
                "action": "manual_review",
            })
            plan["review_count"] += 1
        elif skip:
            plan["safe_to_skip"].append({
                "hash": c["hash"],
                "subject": c["subject"],
                "reason": reason,
                "action": "skip",
            })
            plan["safe_skip_count"] += 1
        else:
            plan["needs_review"].append({
                "hash": c["hash"],
                "subject": c["subject"],
                "action": "accept",
            })
            plan["review_count"] += 1
    if plan["review_count"] > 100:
        plan["conflict_risk"] = "medium"
    if plan["review_count"] > 500:
        plan["conflict_risk"] = "high"
    return plan


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_analysis(stats):
    """Print analysis summary."""
    print("=" * 70)
    print("REBASE STRATEGY ANALYSIS")
    print("=" * 70)
    print(f"\nTotal commits behind origin/main: {stats['total']:,}")
    print(f"Security-related commits: {len(stats['security_commits'])}")
    print(f"Breaking change commits: {len(stats['breaking_commits'])}")
    print("\n--- Commits by Category ---")
    for cat, count in sorted(stats["by_category"].items(), key=lambda x: -x[1]):
        print(f"  {cat:12s}: {count:5d}")
    print("\n--- Top Authors ---")
    for author, count in sorted(stats["by_author"].items(), key=lambda x: -x[1])[:10]:
        print(f"  {author:30s}: {count:5d}")


def print_key_file_analysis(conflicts):
    """Print analysis of commits touching our key files."""
    print("\n" + "=" * 70)
    print("KEY FILE CONFLICT ANALYSIS")
    print("=" * 70)
    if not conflicts:
        print("\nNo upstream commits touch our key files. Low conflict risk.")
    else:
        print(f"\n{len(conflicts)} commits touch our key files:")
        for c in conflicts:
            print(f"\n  {c['hash'][:12]} {c['subject']}")
            print(f"    Files: {', '.join(c['files'])}")


def print_rebase_guide(plan):
    """Print step-by-step rebase guide."""
    print("\n" + "=" * 70)
    print("STEP-BY-STEP REBASE GUIDE")
    print("=" * 70)
    mb = plan["merge_base"][:12]
    total = plan["total_commits"]
    skip = plan["safe_skip_count"]
    review = plan["review_count"]
    risk = plan["conflict_risk"].upper()
    print(f"""
MERGE BASE: {mb}
TOTAL COMMITS: {total:,}
SAFE TO SKIP: {skip:,}
NEEDS REVIEW: {review:,}
CONFLICT RISK: {risk}

PHASE 1: PREPARATION
--------------------
1. Create a backup branch:
   git branch backup/pre-rebase-$(date +%Y%m%d)

2. Fetch latest upstream:
   git fetch origin

3. Verify merge base:
   git merge-base HEAD origin/main
   (should be: {mb})

PHASE 2: INTERACTIVE REBASE
--------------------------
4. Start interactive rebase:
   git rebase -i {mb}

5. In the editor, mark commits:
   - 'pick' for commits to accept
   - 'drop' for safe-to-skip commits (fmt, style, ci, merge, AST-identical refactors)
   - 'edit' for commits touching key files (manual review)

6. For each 'edit' commit:
   - Check if changes affect our key files
   - If yes: manually resolve or skip
   - If no: git rebase --continue

PHASE 3: CONFLICT RESOLUTION
---------------------------
7. If conflicts arise:
   - Our key files: manual resolution required
   - Core files: accept upstream (theirs)
   - Test files: accept upstream (theirs)

8. After resolving:
   git add <resolved-files>
   git rebase --continue

PHASE 4: VERIFICATION
--------------------
9. Verify our code still works:
   python -c "import grpo_reward_engine; print('OK')"
   python -c "import grpo_train; print('OK')"

10. Run our tests:
    python -m pytest tests/ -x -q 2>/dev/null || echo "No tests found"

11. Compare key files:
    git diff backup/pre-rebase -- grpo_*.py grpo_*.yaml

PHASE 5: CLEANUP
---------------
12. If rebase succeeds:
    git branch -d backup/pre-rebase-*

13. If rebase fails:
    git rebase --abort
    git checkout backup/pre-rebase-*
""")


def print_dry_run(plan):
    """Print what would be skipped vs reviewed."""
    print("\n" + "=" * 70)
    print("DRY RUN: Safe-to-Skip Commits (first 30)")
    print("=" * 70)
    for item in plan["safe_to_skip"][:30]:
        print(f"  DROP  {item['hash'][:12]} {item['subject'][:60]}")
    if len(plan["safe_to_skip"]) > 30:
        print(f"  ... and {len(plan['safe_to_skip']) - 30} more")
    print("\n" + "=" * 70)
    print("DRY RUN: Needs Review (first 30)")
    print("=" * 70)
    for item in plan["needs_review"][:30]:
        print(f"  {item['action']:12s} {item['hash'][:12]} {item['subject'][:60]}")
    if len(plan["needs_review"]) > 30:
        print(f"  ... and {len(plan['needs_review']) - 30} more")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """Main entry point."""
    args = sys.argv[1:]
    print("Analyzing upstream commits...")
    commits = get_upstream_commits()
    if not commits:
        print("No commits to analyze. Already up to date?")
        return
    stats = analyze_commits(commits)
    conflicts = find_key_file_conflicts(commits)
    plan = generate_rebase_plan(commits, stats)
    if "--guide" in args:
        print_rebase_guide(plan)
    elif "--dry-run" in args:
        print_analysis(stats)
        print_key_file_analysis(conflicts)
        print_dry_run(plan)
    else:
        print_analysis(stats)
        print_key_file_analysis(conflicts)
        print_rebase_guide(plan)
        print("\n" + "=" * 70)
        print("Run with --guide for step-by-step instructions")
        print("Run with --dry-run to see skip/review breakdown")
        print("=" * 70)


if __name__ == "__main__":
    main()
