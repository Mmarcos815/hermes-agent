# Migration Plan: Consolidating Project-Related Folders

**Date:** 2026-09-13  
**Workspace:** `C:\Users\mobil\orca\projects\my 1st`  
**Objective:** Survey scattered project-related folders on C drive and recommend what to move into the main project.

---

## Executive Summary

| # | Folder | Size | Verdict |
|---|--------|------|---------|
| 1 | `mcp-redteam/` | ~20+ repos | **PARTIAL MOVE** — deduplicate + move unique MCP servers |
| 2 | `HexStrike-AI/` | ~1 MB code + env | **MOVE** — core MCP server, not in main project |
| 3 | `my-agentic-app/` | ~700 KB + node_modules | **MOVE** — separate NestJS app, belongs in `apps/` |
| 4 | `my-agentic-app.worktrees/` | 1 worktree | **MOVE WITH #3** — git worktree of #3 |
| 5 | `pylibs/impacket/` | Empty/partial | **CLEAN UP** — reinstall via pip or remove |
| 6 | `redteam_env/` | WMI venv | **MERGE** — add WMI to main project deps if needed |
| 7 | `src/` | NestJS fragments | **MERGE INTO #3** — appears to be my-agentic-app source fragments |
| 8 | `bin/` | ~200+ MB binaries | **MOVE** — security tools belong in `tools/` or `redteam/binaries/` |

---

## 1. `C:\Users\mobil\mcp-redteam\` — MCP Red Team Tools

### Contents
~20+ cloned cybersecurity MCP server repos plus lab documentation:
- `Anthropic-Cybersecurity-Skills/` — Claude cybersecurity skill configs
- `autopentest-ai/` — automated pentesting AI
- `awesome-cyber-security-mcp/` — curated MCP security list
- `community-rules/` — community detection rules
- `CyberSecurity-MCPs/` — security MCP implementations
- `exploitdb-mcp-server/` — ExploitDB MCP
- `hackerone-mcp-server/` — HackerOne MCP
- `kali_mcp/` — Kali Linux MCP
- `MCP_Red_Team_Agent/` — red team agent framework
- `mcploit/` — MCP exploitation framework
- `nmap-mcp-server/` — Nmap MCP
- `pentester-mcp/` / `pentest-mcp/` / `pentestMCP/` — 3 variant pentest MCP servers
- `Vulnerability-Scanner-MCP-Server/` — vuln scanner MCP
- `vulnerable-mcp-servers-lab/` — intentionally vulnerable MCP servers
- `vulnerable-mcp-server-wikipedia-http-streamable/` — vuln server demo
- `vulnicheck/` — vulnerability checker
- Markdown docs: `ANTHROPIC_CORPUS_MOUNT.md`, `COMPLETE_LAB_DOCS.md`, `FINAL_COMPLETION.md`, `MASTER_STATUS_REPORT.md`

### Overlap with Main Project
The main project's `redteam/` directory already contains duplicates of:
- `autopentest-ai`, `exploitdb-mcp-server`, `hackerone-mcp-server`, `kali_mcp`, `MCP_Red_Team_Agent`, `mcploit`, `nmap-mcp-server`, `pentester-mcp`, `pentest-mcp`, `pentestMCP`

### Recommendation
- **MOVE** the unique repos (Anthropic-Cybersecurity-Skills, awesome-cyber-security-mcp, community-rules, CyberSecurity-MCPs, vulnerable-mcp-servers-lab, vulnicheck) into `redteam/` in the main project
- **DEDUP** the overlapping repos — compare versions, keep whichever is newer, delete the `mcp-redteam/` copies
- **MOVE** the markdown docs into `docs/mcp-redteam/` or `redteam/docs/`
- **DO NOT MOVE** `vulnerable-mcp-server-wikipedia-http-streamable/` (appears to be a demo/toy — confirm first)

### Target Path
```
redteam/
├── Anthropic-Cybersecurity-Skills/
├── awesome-cyber-security-mcp/
├── community-rules/
├── CyberSecurity-MCPs/
├── vulnerable-mcp-servers-lab/
├── vulnicheck/
└── ... (existing dirs)
```

---

## 2. `C:\Users\mobil\HexStrike-AI\` — HexStrike AI MCP Platform

### Contents
- `hexstrike_mcp.py` (223 KB) — main MCP client
- `hexstrike_server.py` (751 KB) — main server
- `hexstrike_env/` — Python virtualenv
- `hexstrike-ai-mcp.json` — MCP config
- `requirements.txt` — Flask, FastMCP, BeautifulSoup, Selenium, mitmproxy, pwntools, angr
- `README.md`, `LICENSE`
- `assets/` — logo images
- `hexstrike.log` — runtime log
- `nuclei.zip` — placeholder/seed

### Overlap with Main Project
Main project has `hexstrike_hermes_proxy.py` and `hexstrike_live_server.py` — these are **wrappers/proxies** that call into HexStrike AI. The actual HexStrike AI codebase lives only in this external folder.

### Recommendation
- **MOVE** the entire folder into `mcp-servers/hexstrike-ai/` (alongside the existing custom MCP servers)
- **MOVE** `hexstrike_hermes_proxy.py` and `hexstrike_live_server.py` from the main project root into the same directory (or create a symlink)
- **MERGE** `hexstrike_env/` dependencies into the main `.venv` via `pip install -r requirements.txt`

### Target Path
```
mcp-servers/hexstrike-ai/
├── hexstrike_mcp.py
├── hexstrike_server.py
├── hexstrike-ai-mcp.json
├── requirements.txt
├── README.md
├── LICENSE
├── assets/
├── hexstrike_hermes_proxy.py   (moved from root)
└── hexstrike_live_server.py    (moved from root)
```

---

## 3. `C:\Users\mobil\my-agentic-app\` — My Agentic App (NestJS)

### Contents
- **Stack:** NestJS 11 + TypeScript + Prisma ORM + Anthropic AI SDK + Plaid banking
- `src/` — app controller, modules (arcjet, bank, chat, claude, common, config, crypto, news, notes, prisma, user), main.ts
- `prisma/` — schema.prisma + migrations
- `node_modules/`, `dist/` — build artifacts
- `.agents/skills` — agent skill configs
- `scripts/` — health reports, reinstall scripts (PowerShell + bash)
- `.env` — DATABASE_URL (Neon PostgreSQL), AUTH_JWT_SECRET, Plaid keys, ANTHROPIC_API_KEY
- `.env.example` — template
- `package.json`, `package-lock.json`, `tsconfig.json`
- `docs/`, `screenshots/`, `test/`
- `.vscode/` — VS Code settings

### Overlap with Main Project
**None.** Completely separate application. The main project is Python-based; this is a NestJS/TypeScript web app.

### Recommendation
- **MOVE** into `apps/my-agentic-app/` in the main project
- This is a distinct application (AI agent + banking) that deserves its own subdirectory
- Keep `.env` out of git (already in `.gitignore` patterns)
- `node_modules/` and `dist/` should NOT be committed (add to `.gitignore` if not already)

### Target Path
```
apps/my-agentic-app/
├── src/
├── prisma/
├── scripts/
├── docs/
├── screenshots/
├── test/
├── package.json
├── package-lock.json
├── tsconfig.json
├── .env              (gitignored)
├── .env.example
└── ...
```

---

## 4. `C:\Users\mobil\my-agentic-app.worktrees\` — Git Worktrees

### Contents
- Single worktree: `import-os-import-sys-import-time-import-subproce/`
  - `package.json`, `package-lock.json`, `README.md`, `scripts/`
  - `.git` file pointing to the main repo's worktree metadata
- Branch name suggests this was an experiment to add Python-style imports (`import os, sys, time, subprocess`)

### Overlap with Main Project
This is a git worktree of `my-agentic-app` (folder #3).

### Recommendation
- **IF** the worktree is stale/merged: delete it with `git worktree remove`
- **IF** still active: move the entire `my-agentic-app.worktrees/` into `apps/my-agentic-app/worktrees/`
- Most likely this is abandoned — verify with `git worktree list` from `my-agentic-app/`

### Target Path
```
apps/my-agentic-app/worktrees/import-os-import-sys-import-time-import-subproce/
```

---

## 5. `C:\Users\mobil\pylibs\` — Python Libraries (impacket)

### Contents
- Single subdirectory: `impacket/` — appears empty or a partial clone

### Overlap with Main Project
Main project does not contain impacket.

### Recommendation
- **CLEAN UP** — the directory appears empty or incomplete
- If impacket is needed, add to `requirements.txt`: `impacket>=0.11.0`
- If this was meant to be a local install, replace with a proper pip install into the main `.venv`
- **DELETE** the empty `pylibs/` folder after confirming nothing valuable remains

### Target Path
N/A — use pip, not local clones

---

## 6. `C:\Users\mobil\redteam_env\` — Red Team Python Environment

### Contents
- A Python virtualenv specialized for WMI (Windows Management Instrumentation)
- `readme.rst` documents the WMI Python module by Tim Golden
- Contains: `Include/`, `Lib/`, `Scripts/`, `share/`, `pyvenv.cfg`

### Overlap with Main Project
Main project has `.venv/` and `.venv312/` already. No WMI dependency in the main project.

### Recommendation
- **DO NOT MOVE** the venv itself (venvs are not portable)
- **IF** WMI functionality is needed: add `wmi` and `pywin32` to `requirements.txt` or `pyproject.toml`
- **IF** not needed: delete `redteam_env/` to free space
- Consider documenting any WMI scripts that depend on this env, then port them to the main project

### Target Path
N/A — recreate deps in main `.venv`

---

## 7. `C:\Users\mobil\src\` — Source Code Fragments

### Contents
NestJS/TypeScript fragments that appear to belong to `my-agentic-app` (folder #3):
- `guards/role.guard.ts` — role-based authorization guard
- `middleware/api-key.middleware.ts` — API key validation middleware
- `Searches/` — Windows search connector files (`.search-ms`, `desktop.ini`) — likely leftover artifacts, not code
- `user/user.controller.ts`, `user.module.ts` — user management NestJS module
- `utils/transform.interceptor.ts` — response transform interceptor

### Overlap with Main Project
None in main project. These overlap conceptually with `my-agentic-app/src/` (folder #3).

### Recommendation
- **MERGE** the NestJS source files into `apps/my-agentic-app/src/` (folder #3)
  - `guards/role.guard.ts` → `apps/my-agentic-app/src/guards/`
  - `middleware/api-key.middleware.ts` → `apps/my-agentic-app/src/middleware/`
  - `user/user.controller.ts`, `user.module.ts` → `apps/my-agentic-app/src/user/`
  - `utils/transform.interceptor.ts` → `apps/my-agentic-app/src/common/`
- **DELETE** `Searches/` — these are Windows search artifacts, not project source code
- **VERIFY** for conflicts with existing files in `my-agentic-app/src/` before merging

### Target Path
```
apps/my-agentic-app/src/
├── guards/role.guard.ts
├── middleware/api-key.middleware.ts
├── user/ (merged)
└── common/transform.interceptor.ts
```

---

## 8. `C:\Users\mobil\bin\` — Security Binaries

### Contents
Precompiled security tools (~200+ MB):
| Tool | Type | Size |
|------|------|------|
| `ffuf.exe` | Web fuzzer | 8.5 MB |
| `gobuster.exe` | Directory/DNS brute-forcer | 10 MB |
| `nuclei.exe` | Vulnerability scanner | 77.6 MB |
| `chisel.zip` | TCP/UDP tunnel | 4.9 MB |
| `evilginx2/` + `.zip` | Phishing framework | 8.4 MB |
| `gophish/` + `.zip` | Phishing simulation | 33.7 MB |
| `hashcat/` + `.7z` | Password cracker | 19.7 MB |
| `mimikatz/` | Credential extraction | dir |
| `Rubeus/` + `.zip` + `Rubeus-master/` | Kerberos abuse | dir |
| `SharpHound/` + `.zip` | AD reconnaissance | dir |
| `CrackMapExec/` | AD exploitation | dir |
| `sliver-client.exe` + `sliver-server.exe` | C2 framework | — |
| `check_ad_tools.py` | Validation script | — |
| Docs: `README.md`, `CHANGELOG.md`, `LICENSE`, translations | | |

### Overlap with Main Project
Main project references these tools via Python wrappers but does not ship the binaries:
- `advanced/evilginx_config.py` — config for evilginx2
- `sandbox-lab/configs/gophish` — config for gophish

### Recommendation
- **MOVE** to `tools/binaries/` or `redteam/binaries/`
- This keeps security tools organized and out of the project root
- Add a `tools/binaries/README.md` documenting each tool's purpose and usage
- Ensure these are NOT committed to git (add to `.gitignore`)

### Target Path
```
tools/binaries/
├── ffuf.exe
├── gobuster.exe
├── nuclei.exe
├── chisel.zip
├── evilginx2.zip
├── gophish.zip
├── hashcat.7z
├── evilginx2/      (extracted)
├── gophish/        (extracted)
├── hashcat/        (extracted)
├── mimikatz/       (extracted)
├── Rubeus/         (extracted)
├── Rubeus-master/  (extracted)
├── SharpHound/     (extracted)
├── CrackMapExec/   (extracted)
├── sliver-client.exe
├── sliver-server.exe
└── README.md
```

---

## Migration Order (Recommended)

1. **First:** Move `my-agentic-app/` → `apps/my-agentic-app/` (#3) — self-contained app
2. **Second:** Merge `src/` → `apps/my-agentic-app/src/` (#7 → #3)
3. **Third:** Handle `my-agentic-app.worktrees/` (#4) — clean up or relocate
4. **Fourth:** Move `HexStrike-AI/` → `mcp-servers/hexstrike-ai/` (#2)
5. **Fifth:** Move unique `mcp-redteam/` repos → `redteam/` (#1)
6. **Sixth:** Move `bin/` → `tools/binaries/` (#8)
7. **Seventh:** Clean up `pylibs/` and `redteam_env/` (#5, #6)

---

## Files to Update After Migration

| File | Change |
|------|--------|
| `hexstrike_hermes_proxy.py` | Update import paths to `mcp-servers/hexstrike-ai/hexstrike_mcp.py` |
| `hexstrike_live_server.py` | Update import paths similarly |
| `.gitignore` | Add `tools/binaries/`, `apps/my-agentic-app/node_modules/`, `apps/my-agentic-app/dist/` |
| `requirements.txt` / `pyproject.toml` | Add `wmi`, `pywin32`, `impacket` if functionality needed |
| Any scripts referencing `/c/Users/mobil/bin/` | Update paths to `tools/binaries/` |
| Any scripts referencing `/c/Users/mobil/mcp-redteam/` | Update paths to `redteam/` |

---

## Risks & Considerations

1. **Git history:** Moving files out of `mcp-redteam/` submodules will detach them from their source repos. Use `git mv` where possible to preserve history.
2. **Symlinks/junctions:** Check if any tools or scripts use absolute paths to these folders — they will break.
3. **Disk space:** `bin/` folder is ~200+ MB. Ensure the main project drive has room.
4. **Security tools:** Some binaries (mimikatz, Rubeus) may trigger antivirus. Ensure `.gitignore` excludes them and document this.
5. **`my-agentic-app/.env`:** Contains real secrets (DATABASE_URL, JWT secret, Plaid keys). Ensure `.env` is NEVER committed and is in `.gitignore`.
6. **Worktrees:** Abandoned worktrees can corrupt git state. Verify with `git worktree list` before removing.
7. **Python version mismatch:** `redteam_env/` may have been built for a different Python version than the main `.venv`.

---

## Quick Reference: Final Project Structure (After Migration)

```
my 1st/
├── apps/
│   └── my-agentic-app/          ← from my-agentic-app/
│       ├── src/                 ← merged from src/
│       ├── prisma/
│       ├── scripts/
│       ├── package.json
│       └── worktrees/           ← from my-agentic-app.worktrees/
├── mcp-servers/
│   ├── hexstrike-ai/            ← from HexStrike-AI/
│   │   ├── hexstrike_mcp.py
│   │   ├── hexstrike_server.py
│   │   ├── hexstrike_hermes_proxy.py  (from root)
│   │   └── hexstrike_live_server.py   (from root)
│   └── (existing custom MCP servers)
├── redteam/
│   ├── Anthropic-Cybersecurity-Skills/  (new)
│   ├── awesome-cyber-security-mcp/      (new)
│   ├── community-rules/                 (new)
│   ├── CyberSecurity-MCPs/              (new)
│   ├── vulnerable-mcp-servers-lab/      (new)
│   ├── vulnicheck/                      (new)
│   └── (existing MCP servers, deduplicated)
├── tools/
│   └── binaries/                ← from bin/
│       ├── ffuf.exe, nuclei.exe, gobuster.exe
│       ├── evilginx2.zip, gophish.zip, hashcat.7z
│       ├── mimikatz/, Rubeus/, SharpHound/, CrackMapExec/
│       └── sliver-client.exe, sliver-server.exe
├── (existing project files...)
```
