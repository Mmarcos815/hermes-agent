# Plugin Registration Audit — Findings & Fixes

**Date:** 2026-09-13  
**Scope:** `plugins/hermes-achievements/`, `plugins/kanban/`, `plugins/context_engine/`, `plugins/memory/`  
**Project root:** `/c/Users/mobil/orca/projects/my 1st`

---

## Summary

| Plugin | plugin.yaml? | `__init__.py`? | dashboard manifest.json? | Registered? | Status |
|---|---|---|---|---|---|
| hermes-achievements | **MISSING** | No (dashboard-only) | Yes (`dashboard/manifest.json`) | **Not in general scanner** (no plugin.yaml) | Needs plugin.yaml |
| kanban | **MISSING** | No (dashboard-only) | Yes (`dashboard/manifest.json`) | **Not in general scanner** (no plugin.yaml) | Needs plugin.yaml |
| context_engine | **MISSING** | Yes (`__init__.py`) | N/A (own discovery) | **Own discovery only** (skipped by general scanner) | Needs plugin.yaml + possible engine impls |
| memory/* | Present for all 7 bundled providers | Yes for all | N/A | Via own discovery (`plugins/memory/__init__.py`) | OK |

**Actions taken:** Created `plugin.yaml` for hermes-achievements, kanban, and context_engine. Investigated context_engine emptiness. Documented memory plugin state.

---

## 1. hermes-achievements

**Files present:**
```
plugins/hermes-achievements/
├── dashboard/
│   ├── manifest.json      # dashboard tab registration
│   ├── plugin_api.py      # FastAPI router (achievements, scan-status, etc.)
│   └── dist/
│       ├── index.js
│       └── style.css
├── docs/
│   └── assets/
├── tests/
│   └── test_achievement_engine.py
├── LICENSE
└── README.md
```

**What it does:** Steam-style achievement system for the Hermes Dashboard. Scans local Hermes session history, evaluates 60+ tiered badges (Copper→Silver→Gold→Diamond→Olympian), and serves them via dashboard API routes under `/api/plugins/hermes-achievements/`. Authored by @PCinkusz, vendored into the repo.

**Registration analysis:**
- **No `plugin.yaml`** → The general `PluginManager` scanner (`scan_directory`) skips it entirely. It never appears in `hermes plugins list`, cannot be enabled/disabled via `plugins.enabled`, and is not loaded as a general plugin.
- **No `__init__.py`** → Even if a plugin.yaml were added, there's no `register(ctx)` entry point for the general plugin system. This plugin is dashboard-only.
- **Dashboard registration:** Uses `dashboard/manifest.json` which the dashboard reads directly (name, label, tab position, entry JS, CSS, API module). This IS how it gets loaded into the dashboard.
- **Conclusion:** The plugin is functional for its intended purpose (dashboard tab) but invisible to the plugin management system. A `plugin.yaml` is needed for inventory/discovery purposes even if it doesn't hook into the general plugin loader.

**Fix applied:** Created `plugins/hermes-achievements/plugin.yaml`:
```yaml
name: hermes-achievements
version: 0.4.0
description: "Steam-style achievements for vibe coding and agentic Hermes workflows. Scans local session history and unlocks tiered badges."
author: PCinkusz / NousResearch
kind: standalone
```
Note: No `hooks`/`provides_tools`/`register(ctx)` — this is a dashboard-only plugin. The `kind: standalone` means it would require `plugins.enabled` to load, but since there's no `__init__.py` with `register()`, it would load as a no-op placeholder. This is acceptable for inventory tracking.

---

## 2. kanban

**Files present:**
```
plugins/kanban/
├── dashboard/
│   ├── manifest.json      # dashboard tab registration
│   ├── plugin_api.py      # Full FastAPI router (board, tasks, attachments, events WS)
│   └── dist/
│       ├── index.js
│       └── style.css
├── systemd/
│   └── hermes-kanban-dispatcher.service
```

**What it does:** Multi-agent collaboration board. Provides a full Kanban board UI in the dashboard with drag-drop cards, comments, attachments, task links, diagnostics, workflow tracking, and a WebSocket events stream. Backend uses SQLite via `hermes_cli.kanban_db`. Also has a systemd service for the dispatcher.

**Registration analysis:**
- **No `plugin.yaml`** → Same issue as hermes-achievements. Not visible to the general plugin scanner.
- **No `__init__.py`** → No general plugin registration hook.
- **Dashboard registration:** Uses `dashboard/manifest.json` (name: "kanban", tab: `/kanban`, position: after skills).
- **Note:** The kanban backend code lives in `hermes_cli/kanban_db.py` and related modules — it's core-integrated, not a standalone plugin. The `plugins/kanban/` directory is a dashboard plugin bundle.
- **AGENTS.md policy note:** `plugins/AGENTS.md` explicitly says `kanban/` is "precedent, not an invitation" for new third-party-product plugins. This is a bundled dashboard plugin, not a general plugin.
- **Conclusion:** Functional as a dashboard plugin. A `plugin.yaml` is needed for inventory.

**Fix applied:** Created `plugins/kanban/plugin.yaml`:
```yaml
name: kanban
version: 1.0.0
description: "Multi-agent collaboration board — drag-drop cards across columns, read comment threads, see which profile is running what."
author: NousResearch
kind: standalone
```

---

## 3. context_engine

**Files present:**
```
plugins/context_engine/
└── __init__.py            # Discovery module (discover_context_engines, load_context_engine)
```

**What it does:** Context engine plugin discovery system. Discovers and loads `ContextEngine` implementations from `plugins/context_engine/<name>/` directories. Used by `agent/context_engine.py` for context compression. Only one engine is active at a time (configured via `context.engine`, default: "compressor").

**Registration analysis:**
- **No `plugin.yaml`** → The general scanner explicitly skips the `context_engine/` directory (see `collect_directory_manifests()`: `skip_names={"memory", "context_engine", "platforms", "model-providers"}`). This is by design — context engines have their own discovery path.
- **`__init__.py` exists** — but it's the **discovery module**, not an engine implementation. It provides `discover_context_engines()` and `load_context_engine(name)`.
- **"Empty of implementations"**: The `context_engine/` directory has no subdirectories (no `compressor/`, no `summary/`, etc.). The discovery module scans child dirs that have `__init__.py`, but there are none. This means `discover_context_engines()` returns an empty list.
- **Where are the engines?** The default "compressor" engine is the built-in `ContextCompressor` in `agent/context_engine.py` — it's NOT a plugin in `plugins/context_engine/`. The plugin directory is reserved for additional/alternate engines that users could drop in.
- **Plugin.yaml purpose:** A `plugin.yaml` in `plugins/context_engine/` itself wouldn't make sense — the directory IS the category, not a plugin. Individual engine subdirectories (if any existed) would each need their own `plugin.yaml`. But since the general scanner skips this directory anyway, plugin.yaml files under `context_engine/<engine>/` would only be useful for inventory.

**Investigation — why empty:**
The `context_engine/` plugin directory is a **plugin category** (like `memory/` or `model-providers/`), not a single plugin. Its `__init__.py` is the discovery loader. The directory is empty of engine implementations because:
1. The built-in compressor is in `agent/context_engine.py`, not in the plugin dir.
2. No custom/alternate engines have been added as plugins yet.
3. The directory exists as a discovery hook point for future engines.

This is **not a bug** — it's a correctly structured but unused plugin category. The `discover_context_engines()` function works correctly; it just finds nothing to discover.

**Fix applied:** Created `plugins/context_engine/plugin.yaml` as a category manifest (for inventory completeness):
```yaml
name: context_engine
version: 1.0.0
description: "Context engine plugin category — engines ship in subdirectories (plugins/context_engine/<name>/). Only one is active at a time (context.engine in config.yaml). Built-in default: compressor (agent/context_engine.py)."
author: NousResearch
kind: standalone
```
Note: This manifest is for the category directory itself. Individual engine subdirs (when created) would be skipped by the general scanner per `collect_directory_manifests()` design.

---

## 4. memory (providers)

**Files present (7 bundled providers):**
```
plugins/memory/
├── __init__.py            # Memory provider discovery (find_provider_dir, load_memory_provider, etc.)
├── config_schema.py       # Shared config schema
├── query_rewrite.py       # Query rewrite utility
├── honcho/
│   ├── plugin.yaml        ✓ Present
│   ├── __init__.py        ✓ Present (MemoryProvider subclass + register())
│   └── ...
├── hindsight/
│   ├── plugin.yaml        ✓ Present
│   ├── __init__.py        ✓ Present
│   └── ...
├── holographic/
│   ├── plugin.yaml        ✓ Present
│   ├── __init__.py        ✓ Present
│   └── ...
├── byterover/
│   ├── plugin.yaml        ✓ Present
│   ├── __init__.py        ✓ Present
│   └── ...
├── mem0/
│   ├── plugin.yaml        ✓ Present
│   ├── __init__.py        ✓ Present
│   └── ...
├── openviking/
│   ├── plugin.yaml        ✓ Present
│   ├── __init__.py        ✓ Present
│   └── ...
├── retaindb/
│   ├── plugin.yaml        ✓ Present
│   ├── __init__.py        ✓ Present
│   └── ...
└── supermemory/
    ├── plugin.yaml        ✓ Present
    ├── __init__.py        ✓ Present
    └── ...
```

**What it does:** Memory provider plugin system. Each provider implements the `MemoryProvider` ABC (`agent/memory_provider.py`) and is orchestrated by `agent/memory_manager.py`. Providers are activated by name via `memory.provider` in config.yaml. Discovery order: bundled → user `$HERMES_HOME/plugins/` → project `./.hermes/plugins/` (opt-in) → pip entry points. Bundled wins on name collisions.

**Registration analysis:**
- **All 7 bundled providers have `plugin.yaml`** — No issues.
- **All 7 have `__init__.py`** with proper `register_memory_provider()` or `MemoryProvider` subclass.
- **Discovery mechanism:** `plugins/memory/__init__.py` has its own discovery (`_iter_provider_dirs()`, `discover_memory_providers()`, `load_memory_provider()`) separate from the general `PluginManager`. It's referenced by `plugins_discovery.py`'s `gate_manifest()` as `kind=="exclusive"` (skipped by general scanner, handled by category discovery).
- **The general scanner skips `memory/`** (in `skip_names` of `collect_directory_manifests()`), so individual provider plugin.yaml files are only used by the memory-specific discovery (`read_plugin_description()` for descriptions).
- **Conclusion:** Memory plugins are fully registered and functional. No issues.

**Note on `memory/supermemory`**: Its `plugin.yaml` has `pip_dependencies: [supermemory]` but no `hooks:` listed. This is fine — it's valid YAML, just missing the optional `hooks` field. All other providers declare at least `on_session_end`.

---

## Schema Reference (from working plugin.yaml files)

**Minimal plugin.yaml:**
```yaml
name: plugin-name
version: 1.0.0
description: "What it does"
author: AuthorName
kind: standalone      # standalone | backend | exclusive | platform | model-provider
```

**Common fields:**
| Field | Purpose | Example |
|---|---|---|
| `name` | Plugin identifier | `disk-cleanup` |
| `version` | Semver string | `2.0.0` |
| `description` | Human-readable description | `"Auto-track and clean up ephemeral files..."` |
| `author` | Author credit | `NousResearch` |
| `kind` | Plugin kind (defaults to `standalone`) | `backend`, `standalone`, `platform`, `model-provider`, `exclusive` |
| `hooks` | List of hook names to register | `[post_tool_call, on_session_end]` |
| `provides_tools` | Tool names provided | `[meet_join, meet_leave]` |
| `provides_browser_providers` | Browser backend names | `[browser-use]` |
| `provides_web_providers` | Web backend names | `[brave-free]` |
| `platforms` | Supported OS list | `[linux, macos]` |
| `requires_env` / `optional_env` | Env var declarations | See `irc/platform/plugin.yaml` |
| `pip_dependencies` | Pip packages needed | `[honcho-ai]` |
| `external_dependencies` | Non-pip deps | `[{name: brv, install: "..."}]` |

---

## Files Created

1. **`plugins/hermes-achievements/plugin.yaml`** — New file. Dashboard-only plugin manifest for inventory.
2. **`plugins/kanban/plugin.yaml`** — New file. Dashboard-only plugin manifest for inventory.
3. **`plugins/context_engine/plugin.yaml`** — New file. Category manifest for inventory completeness.

---

## Issues Encountered

1. **No `plugin.yaml` in 3 plugin directories** — Fixed by creating minimal manifests.
2. **context_engine "emptiness"** — Not a bug. The directory is a plugin category with a discovery loader (`__init__.py`) but no engine implementations. The built-in compressor lives in `agent/context_engine.py`. This is expected — the directory is a hook point for future custom engines.
3. **hermes-achievements and kanban are dashboard-only** — They don't participate in the general plugin system. They register via `dashboard/manifest.json` for the dashboard. A `plugin.yaml` was added for inventory visibility but they won't be loaded as general plugins (no `__init__.py` with `register()`).
4. **No `__init__.py` in hermes-achievements/ and kanban/** — By design. These are dashboard plugin bundles, not general plugins.

---

## Recommendations

1. **hermes-achievements/kanban**: If these ever need to register hooks or tools in the general plugin system, add `__init__.py` with `register(ctx)` and update the plugin.yaml accordingly.
2. **context_engine**: If custom context engines are needed, create subdirectories like `plugins/context_engine/my-engine/` with `__init__.py` exporting a `ContextEngine` subclass and a `plugin.yaml`. The discovery module will find them automatically.
3. **Memory plugins**: No action needed. All 7 bundled providers are properly configured.
