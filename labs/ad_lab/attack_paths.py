#!/usr/bin/env python3
"""
attack_paths.py — Map privilege-escalation paths through the AD environment.

Technique: Group-nesting analysis to find non-obvious paths to Domain Admin.
MITRE: T1078 (Valid Accounts), T1098 (Account Manipulation)

This simulation uses a local graph so it runs without live AD connectivity.
Replace `build_graph_from_ad()` with ldap3 calls to run against a real lab.
"""

from __future__ import annotations
from collections import defaultdict, deque

# ── Simulated AD graph (mirrors what setup.ps1 creates) ────────────────────
# node -> list of member nodes (direction: group -> member)
GRAPH: dict[str, list[str]] = {
    "Tier0_Admins":  ["IT_Admins", "Administrator"],
    "IT_Admins":     ["jsmith"],
    "SQL_Admins":    ["svc_sql"],
    "HelpDesk":      ["adoe", "mjones"],
    "Domain Admins": ["Tier0_Admins"],
}

# SPNs present on these accounts (kerberoast indicator)
SPN_NODES: set[str] = {"svc_sql", "svc_backup"}

# Local-admin-rights hint (token-theft prerequisite)
LOCAL_ADMIN_HINTS: set[str] = {"jsmith", "svc_sql"}


def find_path(graph: dict[str, list[str]], start: str, goal: str) -> list[str] | None:
    """BFS upward through group membership from `start` to `goal`."""
    visited: set[str] = {start}
    queue: deque[tuple[str, list[str]]] = deque([(start, [start])])

    while queue:
        node, path = queue.popleft()
        for parent, members in graph.items():
            if node in members and parent not in visited:
                new_path = path + [parent]
                if parent == goal:
                    return new_path
                visited.add(parent)
                queue.append((parent, new_path))
    return None


def find_all_paths(graph: dict[str, list[str]], goal: str) -> dict[str, list[str]]:
    """Return shortest path from every user/group node to `goal`."""
    nodes = set(graph.keys())
    for members in graph.values():
        nodes.update(members)

    paths: dict[str, list[str]] = {}
    for node in sorted(nodes):
        p = find_path(graph, node, goal)
        if p and len(p) > 1:            # exclude the goal itself
            paths[node] = p
    return paths


def print_paths(paths: dict[str, list[str]]) -> None:
    if not paths:
        print("  No escalation paths found.")
        return
    for src, chain in sorted(paths.items()):
        arrow = " → ".join(chain)
        tags = []
        for n in chain:
            if n in SPN_NODES:
                tags.append(f"[SPN on {n}]")
            if n in LOCAL_ADMIN_HINTS:
                tags.append(f"[local-admin? {n}]")
        tag_str = f"  {' '.join(tags)}" if tags else ""
        print(f"  {arrow}{tag_str}")


def main() -> None:
    print("=" * 60)
    print("  AD Attack-Path Mapper — Educational Simulation")
    print("=" * 60)
    print()

    goal = "Domain Admins"
    paths = find_all_paths(GRAPH, goal)

    print(f"[*] Escalation paths to {goal}:\n")
    print_paths(paths)

    print(f"\n[*] SPN-bearing accounts (kerberoast targets):")
    for acct in sorted(SPN_NODES):
        print(f"      {acct}")

    print(f"\n[*] Accounts suspected of local-admin rights (token theft):")
    for acct in sorted(LOCAL_ADMIN_HINTS):
        print(f"      {acct}")

    print("\n[*] Recommended hardening:")
    print("      - Remove nested group paths that grant DA to low-tier users")
    print("      - Remove SPNs from svc_sql / svc_backup; use gMSA instead")
    print("      - Enforce LAPS on all workstation local-admin accounts")


if __name__ == "__main__":
    main()
