# .py File Landscape Survey — "my 1st" Project
## Prepared for Dad — Where to focus the Python review

**Date:** 2026-09-13
**Project root:** /c/Users/mobil/orca/projects/my 1st
**Total .py files:** 163+ root / 59,000+ incl. subprojects, venvs, node_modules
**Top-level root .py files:** ~160 (59,387 lines)
**Note:** Count inflated by `node_modules` copies inside `bionic-vuln-lab/`, `redteam/`, etc.

---

## EXECUTIVE SUMMARY — Where to focus

| Priority | Directory | .py files | Why focus here |
|----------|-----------|-----------|----------------|
| **1 (CRITICAL)** | `redteam/` | 25,771 | Offensive security tooling — pentest MCP servers, exploit automation, red team agents. This is the security payload. |
| **2 (HIGH)** | `bionic-vuln-lab/` | 50 | Vulnerable app simulations + security lab tooling. Direct offensive/defensive security code. |
| **3 (HIGH)** | `bionic-core/` | 41 | Core Bionic infrastructure — MCP servers, audit pipelines, bounty sweepers, cloud engines. Foundation layer. |
| **4 (MEDIUM)** | `bionic-sovereign/` | (nested) | Sovereign settlement + DeFi exploit automation. Financial security + smart contract risk. |
| **5 (MEDIUM)** | Root-level security tools | ~40 files | Standalone security scripts: `automated_red_team_pipeline.py`, `cti_feed_ingestion.py`, `malware_analysis_sandbox.py`, `vulnerability_correlation_engine.py`, `threat_model_engine.py`, `iso8583_parser.py`, `jailbreak_prompt_generator.py`, `prompt_injection_classifier.py`, etc. |
| **6 (LOW)** | `tests/` | 3,964 | Test suite — important for correctness but not security-relevant per se. |
| **7 (LOW)** | `plugins/` | 241 | Hermes Agent plugin infrastructure — important for Hermes review, not Bionic security. |
| **8 (LOW)** | `skills/` + `optional-skills/` | 58 + 101 | Skill definitions — mostly markdown + small scripts. |
| **9 (INFO)** | `agent/`, `tools/`, `gateway/`, `orchestrator/`, `evals/` | ~800 combined | Hermes Agent core framework — review for Hermes correctness, not Bionic security. |

---

## DETAILED BREAKDOWN

### Category A: SECURITY TOOLS & OFFENSIVE INFRASTRUCTURE (Focus Priority 1-2)

#### `redteam/` — 25,771 .py files (the big one)
Subdirectories (file counts):
- `redteam/mcploit/` — 9,302 files (~8,850 lines)
- `redteam/MCP_Red_Team_Agent/` — 8,491 files (~21,771 lines)
- `redteam/autopentest-ai/` — 4,166 files (~24,408 lines)
- `redteam/pentestMCP/` — 854 files (~27,027 lines)
- `redteam/pentester-mcp/` — 2,958 files (~4,797 lines)

**Assessment:** This is the offensive security payload. MCP-based pentesting tools, automated exploit chains, red team agent frameworks. Largest concentration of security-relevant Python code in the project. The `pentestMCP/` subdirectory has the highest line count per file (avg ~32 lines/file — likely test fixtures + small scripts). `MCP_Red_Team_Agent/` and `autopentest-ai/` are the heaviest by lines — these are the main agent frameworks.

**Review focus:** Exploit generation logic, tool definitions, credential handling, any hardcoded secrets, command injection paths, safety guards on autonomous pentesting.

---

#### `bionic-vuln-lab/` — 50 .py files (33,851 lines)
Note: 50 of these are in `node_modules/` — the actual project code is ~50 files in the top-level dir.

**Assessment:** Vulnerable application lab — deliberately vulnerable apps for training/experimentation. Security-relevant by definition. The high line count (33,851) for 50 files suggests large generated or bundled files.

---

#### Root-level security tool scripts (standalone .py files in project root)
These are single-file security tools. Key ones:

| File | Lines | Purpose |
|------|-------|---------|
| `automated_red_team_pipeline.py` | 30,282 | Massive — automated red team orchestration |
| `cloud_red_team_playbook.py` | 43,718 | Cloud pentesting playbook automation |
| `cti_feed_ingestion.py` | 6,084 | Cyber threat intelligence feed processing |
| `malware_analysis_sandbox.py` | 16,141 | Malware analysis automation |
| `vulnerability_correlation_engine.py` | 21,809 | CVE/vuln correlation across datasets |
| `threat_model_engine.py` | 8,315 | Automated threat modeling |
| `threat_modeling_engine.py` | 1,945 | Threat modeling (lighter variant) |
| `jailbreak_prompt_generator.py` | 38,944 | LLM jailbreak prompt generation — dual-use |
| `prompt_injection_classifier.py` | 25,921 | Prompt injection detection |
| `iso8583_parser.py` | 43,361 | ISO 8583 financial message parsing |
| `iso20022_engine.py` | 8,720 | ISO 20022 financial messaging |
| `defi_exploit_automation.py` | 19,335 | DeFi exploit automation |
| `phishing_simulation_automation.py` | 25,556 | Phishing campaign automation |
| `osint_automation_engine.py` | 27,710 | OSINT automation |
| `solidity_audit_scanner.py` | 6,343 | Solidity smart contract auditing |
| `web3_contract_fuzzer.py` | 5,000 | Web3/smart contract fuzzing |
| `web3_defi_lab.py` | 5,635 | Web3 DeFi experimentation |
| `bounty_sweeper_v2.py` | 4,882 | Bug bounty target scanning |
| `automated_bounty_submission.py` | 15,077 | Automated bounty submission |
| `automated_exploit_gen.py` | 3,035 | Automated exploit generation |
| `exploit_recommendation_engine.py` | 1,861 | Exploit recommendation |
| `redteam_agent_hitl.py` | 4,660 | Human-in-the-loop red team agent |
| `redteam_middleware.py` | 3,928 | Red team middleware |
| `purple_team_automation.py` | 1,913 | Purple team automation |
| `bionic_audit_pipeline.py` | 5,617 | Bionic audit pipeline |
| `bionic_bounty_sweeper.py` | 4,924 | Bionic bounty sweeping |
| `bionic_cloud_vps_engine.py` | 8,263 | Cloud VPS provisioning for ops |
| `bionic_financial_suite.py` | 8,983 | Financial analysis suite |
| `bionic_tools_dryrun.py` | 7,173 | Tool dry-run/simulation |
| `bionic_unified_mcp_server.py` | 9,610 | Unified MCP server |
| `security_metrics_dashboard.py` | 3,031 | Security metrics |
| `security_knowledge_base.py` | 3,031 | Security KB |
| `firmware_iot_analyzer.py` | 2,615 | Firmware/IoT analysis |
| `wireless_security.py` | 3,870 | Wireless security tools |
| `three_ds_simulator.py` | 2,010 | 3D Secure payment simulation |
| `emv_tokenization_engine.py` | 1,720 | EMV tokenization |
| `unified_payment_gateway.py` | 1,460 | Payment gateway |
| `attack_surface_management.py` | 422 | Attack surface mgmt |
| `attack_technique_knowledge_graph.py` | 882 | Attack technique KG |
| `automated_scanning_pipeline.py` | 669 | Scanning pipeline |
| `automated_cti_monitoring.py` | 1,128 | CTI monitoring |
| `deception_engine.py` | 976 | Deception tech |
| `deepfake_detector.py` | 2,707 | Deepfake detection |
| `exploit_recommendations.html` | — | (not .py, but related) |
| `security_dashboard.html` | — | (not .py, but related) |

**Assessment:** This is an enormous collection of security tooling. Many files are 5,000-40,000+ lines — these are large, complex tools. The `automated_red_team_pipeline.py` (30K lines), `cloud_red_team_playbook.py` (44K lines), `jailbreak_prompt_generator.py` (39K lines), `iso8583_parser.py` (43K lines), `cti_feed_ingestion.py` (6K lines), `prompt_injection_classifier.py` (26K lines), `osint_automation_engine.py` (28K lines), and `phishing_simulation_automation.py` (26K lines) are the heaviest individual tools.

---

### Category B: BIONIC INFRASTRUCTURE (Focus Priority 3-4)

#### `bionic-core/` — 41 .py files (14,184 lines)
Subdirs:
- `bionic-core/bd_mcp/` — 17 files
- `bionic-core/src_modules/` — 23 files
- `bionic-core/src/` — 1 file

**Assessment:** Core Bionic infrastructure — MCP server definitions, module system, foundational services. The BD_MCP subdirectory is likely the MCP server layer.

#### `bionic-sovereign/` — (files nested, not at top level)
**Assessment:** Sovereign settlement system, DeFi infrastructure, financial autonomy tooling. Look for smart contract interaction code, settlement logic, key management.

---

### Category C: HERMES AGENT INFRASTRUCTURE (Focus Priority 7-9 — for Hermes review, not Bionic security)

#### `agent/` — 268 .py files (107,877 lines)
Subdirs:
- `agent/verify/` — 4 files
- `agent/transports/` — 11 files
- `agent/secret_sources/` — 7 files
- `agent/proxy_sources/` — 2 files
- `agent/pet/` — 11 files
- `agent/monitoring/` — 9 files
- `agent/lsp/` — 11 files

**Assessment:** This is the Hermes Agent core runtime — the agent loop, tool execution, transport layer, LSP integration. Largest line count of any directory (107K lines). Critical for Hermes correctness but only indirectly relevant to Bionic security.

#### `tools/` — 317 .py files (111,131 lines)
Subdirs:
- `tools/environments/` — 21 files
- `tools/computer_use/` — 14 files
- `tools/original-one-drive/` — 32 files

**Assessment:** Hermes Agent tool definitions — the tool registry, tool implementations, toolset management. 111K lines is very large. `toolsets.py` (49K lines at root) and `toolset_distributions.py` are key files.

#### `gateway/` — 149 .py files (82,114 lines)
**Assessment:** Hermes Agent gateway — session management, routing, state management, the central nervous system of Hermes. `hermes_state.py` (72K lines at root) is the monster file here.

#### `tests/` — 3,964 .py files (90,482 lines)
Top subdirs by file count:
- `tests/gateway/` — 803 files
- `tests/hermes_cli/` — 858 files
- `tests/agent/` — 523 files
- `tests/tools/` — 587 files
- `tests/plugins/` — 128 files
- `tests/tui_gateway/` — 123 files
- `tests/run_agent/` — 207 files
- `tests/cron/` — 103 files
- `tests/cli/` — 134 files
- `tests/skills/` — 44 files
- `tests/hermes_state/` — 35 files
- `tests/providers/` — 12 files
- `tests/integration/` — 9 files
- `tests/e2e/` — 7 files
- `tests/computer_use/` — 11 files
- `tests/monitoring/` — 6 files
- `tests/acp_adapter/` — 5 files
- `tests/secret_sources/` — 5 files
- `tests/verify/` — 4 files
- `tests/website/` — 4 files
- `tests/scripts/` — 8 files
- `tests/docker/` — 27 files

**Assessment:** Massive test suite. Not security-relevant for Bionic review, but important for Hermes stability. The `tests/integration/` and `tests/e2e/` subdirectories are the most valuable for understanding end-to-end behavior.

#### `plugins/` — 241 .py files (85,847 lines)
Subdirs:
- `plugins/platforms/` — 73 files (50,919 lines) — largest plugin category
- `plugins/memory/` — 38 files (14,977 lines)
- `plugins/model-providers/` — 39 files (2,058 lines)
- `plugins/google_meet/` — 15 files
- `plugins/browser/` — 7 files
- `plugins/teams_pipeline/` — 8 files
- `plugins/dashboard_auth/` — 5 files
- `plugins/image_gen/` — 9 files
- `plugins/web/` — 24 files
- Others — small

**Assessment:** Hermes plugin ecosystem. `plugins/platforms/` is the heaviest — platform adapters (Slack, Discord, Telegram, etc.). `plugins/memory/` is the memory provider layer. Important for Hermes review.

#### `skills/` — 58 .py files (12,591 lines) + `optional-skills/` — 101 files (30,487 lines)
Subdirs in `skills/`:
- `skills/productivity/` — 44 files
- `skills/research/` — 4 files
- `skills/awesome-claude-skills/` — 3 files
- `skills/super-hermes/` — 2 files
- Others — 1 file each

**Assessment:** Skill definitions for Hermes Agent. Mostly markdown + small Python scripts. Not security-critical.

#### `evals/` — 127 .py files (16,186 lines)
**Assessment:** Evaluation harnesses, model eval scripts. Important for model quality assessment.

#### Other Hermes infrastructure dirs:
- `orchestrator/` — 1 file (217 lines)
- `pipeline/` — 1 file (349 lines)
- `reporting/` — 4 files (1,687 lines)
- `dashboard/` — 1 file (254 lines)
- `mcp-servers/` — 15 files (7,197 lines)
- `tui_gateway/` — 62 files (26,330 lines)
- `acp_adapter/` — 14 files (4,114 lines)
- `hermes-agent/` — (Hermes Agent distribution)
- `hermes-cli/` — (CLI)
- `src/` — 23 files (8,445 lines)
- `modules/` — 23 files (8,445 lines)

---

### Category D: TRAINING & EDUCATION (Low priority for code review)

- `learning/` — 28 files (6,646 lines) — learning curriculum materials
- `hacker_training/` — (directories, .py files nested)
- `curriculum/` — (curriculum generation)
- `labs/` — 10 files (2,100 lines) — lab exercises
- `sandbox-lab/` — (sandbox environment)
- `gap_training/` — 1 file (231 lines)
- `training/` — (training data/pipelines)
- `practice/` — (practice exercises)
- `portfolio/` — (portfolio)

---

### Category E: DATA & RESEARCH (Low priority for code review)

- `intelligence/` — 1 file (336 lines) — intelligence data
- `research/` — 8 files (577 lines) — research notes/scripts
- `knowledge/` — (knowledge base)
- `models/` — (model files)
- `jarvis/` + `jarvis_data/` — (Jarvis subsystem)
- `content/` — (content files)
- `website/` — 4 files (1,893 lines)
- `web/` — (web content)
- `blog/` — (blog)
- `engagement/` — 1 file
- `contracts/` — (smart contract definitions)

---

### Root-level Python files NOT yet categorized (by theme)

**Training/ML pipeline:**
- `grpo_train.py` (7,058 lines), `grpo_eval.py` (1,505 lines), `grpo_reward_engine.py` (34,560 lines), `grpo_packager.py` (83 lines), `grpo_sanity_smoke.py` (5,142 lines), `train_direct.py`, `train_lean_cpu.py`, `colab_train.py` (1,091 lines), `cpu_grpo_train.py` (16,618 lines), `modal_training.py` (21,756 lines), `continuous_training_pipeline.py` (1,655 lines), `training_data_quality_pipeline.py` (3,056 lines), `post_training_analysis.py`, `post_training_checklist.py`, `model_performance_tracker.py`, `model_benchmark_suite.py`, `deploy_model.py`, `deploy_trained_model_ollama.py`, `evaluate_model.py` (10,583 lines), `generate_data.py` (33,415 lines), `generate_sft_extra.py` (26,291 lines), `generate_curriculum.py` (107,245 lines — massive), `cve_to_training_data.py`, `detokenization_chain.py` (14,704 lines), `trajectory_compressor.py` (46,395 lines), `mini_swe_runner.py` (19,850 lines), `gap_training/`

**Hermes core (root-level):**
- `run_agent.py` (85,839 lines — massive), `cli.py` (214,611 lines — enormous), `hermes_bootstrap.py`, `hermes_constants.py` (11,981 lines), `hermes_logging.py`, `hermes_startup_watchdog.py`, `hermes_time.py`, `hermes_state*.py` (many files, 20K-76K lines each), `model_tools.py` (45,259 lines), `toolsets.py` (49,000+ lines), `utils.py` (21,753 lines), `mcp_serve.py` (30,995 lines), `setup.py`, `run_tests.py`

**Financial/Payment:**
- `iso8583_parser.py` (43,361 lines), `iso8583_engine.py` (8,579 lines), `iso20022_engine.py` (8,720 lines), `unified_payment_gateway.py` (1,460 lines), `three_ds_simulator.py` (2,010 lines), `emv_tokenization_engine.py` (1,720 lines), `bionic_financial_suite.py` (8,983 lines)

**Blockchain/Web3:**
- `solidity_audit_scanner.py`, `web3_contract_fuzzer.py`, `web3_defi_lab.py`, `defi_exploit_automation.py`, `blockchain_forensics.py`, `sovereign_settlement_testbed.py`

**Helper/Utility:**
- `_gen.py`, `_gen_cti.py`, `wayfinder.py`, `final_integration_check.py`, `rebase_strategy.py`, `persona_consistency_checker.py`, `h1_token_status.py`, `youtube_transcript*.py`, `groq_client.py`, `cdp_groq.py`, `cdp2.py`, `colab_export.py`, `statement_extractor_cli.py`, `financial_table_extractor.py`, `research_ingester.py`, `gguf_converter.py`

---

## WHERE DAD SHOULD START THE REVIEW

### Tier 1 — Read these first (highest security impact, highest line counts):

1. **`redteam/MCP_Red_Team_Agent/`** — 8,491 files, ~21,771 lines. The main red team agent framework. Understand how exploits are generated, how tools are called, what safety guards exist.

2. **`redteam/autopentest-ai/`** — 4,166 files, ~24,408 lines. Automated pentesting AI. How does it discover targets? What's the blast radius?

3. **`automated_red_team_pipeline.py`** (root, 30,282 lines). The orchestrating pipeline for red team operations.

4. **`cloud_red_team_playbook.py`** (root, 43,718 lines). Cloud pentesting automation — AWS/GCP/Azure attack playbooks.

5. **`jailbreak_prompt_generator.py`** (root, 38,944 lines). This is dual-use — jailbreak generation for LLM security testing. Review carefully for any dangerous prompt templates.

6. **`iso8583_parser.py`** (root, 43,361 lines). Financial message parsing — if this has bugs, payment processing breaks. Also a large attack surface for parsing vulnerabilities.

7. **`vulnerability_correlation_engine.py`** (root, 21,809 lines). CVE correlation — how does it ingest and correlate vuln data? Any data integrity issues?

8. **`osint_automation_engine.py`** (root, 27,710 lines). OSINT automation — what data sources? Privacy implications?

9. **`prompt_injection_classifier.py`** (root, 25,921 lines). Prompt injection defense — is it effective? Any bypassable patterns?

10. **`phishing_simulation_automation.py`** (root, 25,556 lines). Phishing campaign automation — ethical boundaries, target lists, credential handling.

### Tier 2 — Read these next:

11. **`bionic-vuln-lab/`** — 50 files, 33,851 lines. Vulnerable apps — what's the attack surface of the lab itself?

12. **`bionic-core/`** — 41 files, 14,184 lines. Core infrastructure — MCP servers, audit pipelines.

13. **`bionic-sovereign/`** — (explore structure). Sovereign financial system — key management, settlement logic.

14. **`defi_exploit_automation.py`** (root, 19,335 lines). DeFi exploit automation — what protocols does it target? Any real exploit code?

15. **`threat_model_engine.py`** (root, 8,315 lines) + **`threat_modeling_engine.py`** (root, 1,945 lines). Threat modeling — methodology, what gets modeled.

16. **`automated_bounty_submission.py`** (root, 15,077 lines) + **`bounty_sweeper_v2.py`** (root, 4,882 lines) + **`bionic_bounty_sweeper.py`** (root, 4,924 lines). Bug bounty automation — target discovery, submission logic, any terms-of-service concerns.

17. **`cti_feed_ingestion.py`** (root, 6,084 lines). CTI feed processing — data sources, feed parsing, any data leakage.

18. **`malware_analysis_sandbox.py`** (root, 16,141 lines). Malware analysis — sandbox implementation, any escape risks.

### Tier 3 — Skim for context:

19. **`bionic_cloud_vps_engine.py`**, **`bionic_unified_mcp_server.py`**, **`bionic_audit_pipeline.py`**, **`bionic_tools_dryrun.py`** — Bionic infrastructure tools.

20. **`redteam_agent_hitl.py`**, **`redteam_middleware.py`**, **`purple_team_automation.py`** — Red/purple team orchestration.

21. **`solidity_audit_scanner.py`**, **`web3_contract_fuzzer.py`**, **`web3_defi_lab.py`** — Web3 security tooling.

22. **`sovereign_settlement_testbed.py`** — Sovereign settlement testing.

23. **`attack_surface_management.py`**, **`attack_technique_knowledge_graph.py`**, **`automated_scanning_pipeline.py`**, **`automated_cti_monitoring.py`** — Smaller security tools.

24. **`deception_engine.py`**, **`deepfake_detector.py`**, **`firmware_iot_analyzer.py`**, **`wireless_security.py`**, **`three_ds_simulator.py`**, **`emv_tokenization_engine.py`**, **`unified_payment_gateway.py`** — Specialized security tools.

25. **`security_metrics_dashboard.py`**, **`security_knowledge_base.py`** — Security observability.

26. **`incidents_response_playbooks.py`** — Incident response.

27. **`hexstrike_hermes_proxy.py`**, **`hexstrike_live_server.py`** — HexStrike integration (pentest tool proxy).

28. **`bionic_async_relayer_dameon.py`**, **`bionic_canonical_sync.py`** — Bionic async infrastructure.

### Skip for now (not security-relevant to Bionic review):

- `tests/` — test suite (3,964 files)
- `plugins/` — Hermes plugin infrastructure (241 files)
- `skills/` + `optional-skills/` — skill definitions (159 files)
- `agent/`, `tools/`, `gateway/` — Hermes core framework (500+ files)
- `evals/` — evaluation harnesses (127 files)
- `learning/`, `hacker_training/`, `curriculum/`, `labs/`, `training/` — education
- `intelligence/`, `research/`, `knowledge/`, `content/`, `website/`, `blog/` — content/research
- `models/`, `jarvis/`, `src/`, `modules/`, `scripts/`, `docker/`, `dashboard/`, `orchestrator/`, `pipeline/`, `reporting/`, `deploy/`, `cloud_deploy/`, `engagement/`, `contracts/`, `portfolio/`, `practice/`, `gap_training/`, `sandbox-lab/`, `vulnerable-apps/`, `testing/`, `test_reports/`, `tui_gateway/`, `acp_adapter/`, `mcp-servers/`, `providers/`, `cron/`, `hermes-agent/`, `hermes-cli/`

---

## QUICK STATS

| Metric | Value |
|--------|-------|
| Total .py files | 163+ root / 59,000+ incl. subprojects |
| Total .py lines (root only) | ~59,387 |
| Largest single file | `cli.py` (214,611 lines) |
| 2nd largest | `run_agent.py` (85,839 lines) |
| 3rd largest | `grpo_train_merged.jsonl` (not .py, but 1.4M lines) |
| Largest security tool | `cloud_red_team_playbook.py` (43,718 lines) |
| Largest parser | `iso8583_parser.py` (43,361 lines) |
| Largest red team dir | `redteam/mcploit/` (9,302 files) |
| Heaviest red team dir by lines | `redteam/autopentest-ai/` (~24,408 lines) |
| Most files in a test subdir | `tests/gateway/` (803 files) |
| Security tool files at root | ~40 standalone .py files |

---

*End of report.*
