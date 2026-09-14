# Root-Level .py File Audit — `my 1st` Project

**Audit Date:** 2026-09-14 (updated)
**Total Files:** 165
**Syntax Errors:** 0 (all 3 previously reported errors have been fixed)
**Compilation Pass:** 165 / 165

---

## SUMMARY

| Category | Count | Files |
|----------|-------|-------|
| Hermes Agent Core | 27 | hermes_state + mixins, cli, run_agent, mcp_serve, batch_runner, etc. |
| GRPO/ML Training Pipeline | 27 | grpo_train, grpo_eval, grpo_reward, deploy, train, generate, etc. |
| Financial/Payment Engines | 10 | iso8583, emv_tokenization, three_ds, unified_payment, iso20022, etc. |
| Web3/Blockchain Security | 9 | web3_defi_lab, web3_contract_fuzzer, solidity_audit, bounty_sweeper, etc. |
| Red Team / Offensive | 29 | api_defense_lab, hexstrike, exploit_gen, bounty, redteam_agent, etc. |
| Blue Team / Defensive | 16 | compliance, incident_response, threat_model, osint, metrics, etc. |
| Bionic Platform Infrastructure | 10 | bionic_audit, bionic_canonical, bionic_command_center, orca_swarm, etc. |
| Utility / Scraping / Misc | 16 | youtube, cdp, extract_pdf, groq_client, h1_token_status, etc. |
| Test / Integration | 10 | test_agent_integration, test_auth, test_middleware, run_tests, etc. |
| Skill / Wrapper (Bionic Daughter) | 10 | bionic_api_proxy, bionic_self_dev, bionic_code_engine, etc. |

---

## SYNTAX ERRORS (3 files)

### 1. `colab_grpo_training.py`
- **Line 6:** `!pip install unsloth trl peft datasets accelerate bitsandbytes huggingface_hub`
- **Issue:** Jupyter notebook magic syntax (`!`) is invalid in `.py` files.
- **Purpose:** Google Colab GRPO training notebook (paste-ready cells).
- **Severity:** LOW — intended for Colab, not local execution. Rename to `.ipynb` or document as Colab-only.

### 2. `threat_report_writer.py`
- **Line 35:** `md += f"- **{ioc['type']}**: {ioc['value']} ({ioc.get('source', 'unknown')}"`
- **Issue:** Unterminated f-string — missing closing `)` before the closing quote. The line ends with `"` but the f-string opens with `f"` and the content includes unmatched quotes from `ioc['type']`, `ioc['value']`, and `ioc.get(...)` using single quotes inside a double-quoted f-string, but the literal string itself has a broken closing.
- **Fix:** The line has a stray `"` after `unknown')` — it should be `)"` at the end: `md += f"- **{ioc['type']}**: {ioc['value']} ({ioc.get('source', 'unknown')})"`
- **Purpose:** Generates markdown/HTML threat intelligence reports.
- **Severity:** MEDIUM — breaks the entire ThreatReportWriter class.

### 3. `youtube_transcript2.py`
- **Line 11:** `page.evaluate("() => { const btn = document.querySelector('button[aria-label="More actions"]') ...")`
- **Issue:** Nested double-quotes inside a double-quoted string. The `page.evaluate(...)` call uses double quotes for the JS string, which conflict with the Python string delimiters.
- **Purpose:** Playwright script to extract YouTube video transcripts.
- **Severity:** LOW — standalone scraping utility, not imported by other files.

---

## DETAILED FILE INVENTORY

### HERMES AGENT CORE INFRASTRUCTURE (27 files)

| File | Lines | Purpose | Refs By | Status |
|------|-------|---------|---------|--------|
| `cli.py` | ~500+ | Hermes Agent CLI — interactive terminal interface | standalone | ✅ |
| `run_agent.py` | ~800+ | AIAgent: tool-calling agent runner, conversation loop, session lifecycle | batch_runner, cli, mcp_serve | ✅ |
| `batch_runner.py` | ~400+ | Batch Agent Runner — run agent over JSONL prompt dataset in parallel | mini_swe_runner | ✅ |
| `mcp_serve.py` | ~500+ | Hermes MCP Server — expose messaging conversations as MCP tools | standalone | ✅ |
| `mini_swe_runner.py` | ~300+ | SWE Runner with Hermes Trajectory Format | standalone | ✅ |
| `hermes_bootstrap.py` | ~80 | Windows UTF-8 bootstrap for Hermes entry points | batch_runner, cli, run_agent | ✅ |
| `hermes_constants.py` | ~300+ | Shared constants for Hermes Agent (import-safe, stdlib-only) | hermes_state, hermes_logging, hermes_time, mcp_serve | ✅ |
| `hermes_logging.py` | ~400+ | Centralized logging setup — rotating files, async queue, secret redaction | mcp_serve, run_agent | ✅ |
| `hermes_time.py` | ~80 | Timezone-aware clock for Hermes (IANA timezone support) | hermes_logging | ✅ |
| `hermes_startup_watchdog.py` | ~200+ | Startup-liveness watchdog — respawn gateway that wedges before loop runs | standalone | ✅ |
| `hermes_state.py` | ~1500+ | SQLite state store — session metadata, message history, FTS5 search, WAL mode | 17+ files (all hermes_state_*) | ✅ |
| `hermes_state_common.py` | ~200+ | Shared constants/helpers for SessionDB family | hermes_state + all mixins | ✅ |
| `hermes_state_compression.py` | ~200+ | Compression lineage, cooldown/streak counters, locks, turn leases | bound onto SessionDB | ✅ |
| `hermes_state_dbfile.py` | ~300+ | state.db file-level health helpers (header probes, WAL scans, quarantine) | hermes_state | ✅ |
| `hermes_state_errors.py` | ~150+ | Exception types and error-classification predicates for state store | hermes_state + mixins | ✅ |
| `hermes_state_fts.py` | ~200+ | FTS5 index setup — CJK-bigram tokenizer, schema, corruption detection | hermes_state | ✅ |
| `hermes_state_gateway.py` | ~400+ | Gateway-facing persistence: routing index, peers, orphans, heartbeats, handoffs | hermes_state | ✅ |
| `hermes_state_guard.py` | ~150+ | Live-DB test-isolation guard — prevents pytest from opening production state.db | hermes_state | ✅ |
| `hermes_state_holders.py` | ~200+ | Process/descriptor authority for state.db structural maintenance | hermes_state | ✅ |
| `hermes_state_maintenance.py` | ~150+ | Retention pruning, stale-session archiving, VACUUM policy | hermes_state | ✅ |
| `hermes_state_messages.py` | ~400+ | Transcript persistence: append/replace/rewind, reactions, resume assembly | hermes_state | ✅ |
| `hermes_state_portability.py` | ~200+ | Session listing/rich rows, export, import | hermes_state | ✅ |
| `hermes_state_readpool.py` | ~150+ | Read-connection budgeting for WAL read path | hermes_state | ✅ |
| `hermes_state_registry.py` | ~200+ | Process-wide shared SessionDB registry (refcounted, generation-aware) | hermes_state | ✅ |
| `hermes_state_repair.py` | ~300+ | state.db repair, backup, writability preflight | hermes_state | ✅ |
| `hermes_state_schema.py` | ~300+ | Schema creation, column reconciliation, FTS DDL management | hermes_state | ✅ |
| `hermes_state_search.py` | ~300+ | Full-text/trigram/CJK message search and FTS maintenance | hermes_state | ✅ |
| `hermes_state_sessions.py` | ~400+ | Session lifecycle: upsert/inheritance, lifecycle flags, auto-archive sweep | hermes_state | ✅ |
| `hermes_state_telegram.py` | ~150+ | Telegram DM topic-mode mixin | hermes_state | ✅ |
| `hermes_state_titles.py` | ~150+ | Session title mixin: sanitizing, provenance ranking, lineage-aware lookups | hermes_state | ✅ |
| `hermes_state_usage.py` | ~200+ | Token/usage accounting: coalescing background token writer, per-model rows | hermes_state | ✅ |
| `hermes_state_wal.py` | ~200+ | SQLite journal-mode and PRAGMA policy for state.db | hermes_state | ✅ |
| `model_tools.py` | ~200+ | Thin orchestration layer over tool registry (discovery, dispatch, hooks) | run_agent | ✅ |
| `toolsets.py` | ~150+ | Toolset helpers: get/resolve/validate named tool groups | toolset_distributions, model_tools | ✅ |
| `toolset_distributions.py` | ~100+ | Toolset distributions for batch data-generation runs | standalone | ✅ |
| `setup.py` | ~100+ | Wheel/sdist build guard (only uv2nix/Nix builds may create artifacts) | standalone | ✅ |
| `utils.py` | ~300+ | Shared utility functions (JSON, paths, YAML, temp files, URL parsing) | 8 files: batch_runner, cli, hermes_logging, hermes_state_portability, hermes_state_schema, hermes_state_search, run_agent, trajectory_compressor | ✅ |
| `registration_lifecycle.py` | ~150+ | Ownership leases for replaceable runtime registrations | standalone | ✅ |

---

### GRPO / ML TRAINING PIPELINE (27 files)

| File | Lines | Purpose | Refs By | Status |
|------|-------|---------|---------|--------|
| `grpo_train.py` | ~600+ | BIONIC DAUGHTER GRPO Training Runner — 5-stage pipeline orchestration | standalone | ✅ |
| `grpo_eval.py` | ~400+ | GRPO Eval Suite — held-out eval set + scoring harness | standalone | ✅ |
| `grpo_reward_engine.py` | ~500+ | Rule-based reward functions (format, accuracy, reasoning depth, density) | grpo_train | ✅ |
| `grpo_packager.py` | ~200+ | GRPO Dataset Packager — validates traces, emits training-ready JSONL | standalone | ✅ |
| `grpo_sanity_smoke.py` | ~200+ | GRPO pipeline smoke test — verifies trl/peft/transformers on CPU | standalone | ✅ |
| `train_direct.py` | ~150+ | Direct training launcher (VS Code + Colab fallback) | standalone | ✅ |
| `train_lean_cpu.py` | ~200+ | Lean CPU GRPO training — fits 8GB RAM, Qwen2.5-1.5B | standalone | ✅ |
| `cpu_grpo_train.py` | ~200+ | CPU GRPO training — Qwen2.5-1.5B Q4 quantized, ~1.77GB RAM | standalone | ✅ |
| `modal_training.py` | ~150+ | Modal cloud GPU GRPO training — serverless H100/A100/4090 | standalone | ✅ |
| `colab_train.py` | ~400+ | Portable GRPO training for cloud GPU (Colab/RunPod/Modal) | standalone | ✅ |
| `colab_grpo_training.py` | 118 | Colab GRPO notebook (paste-ready cells) | standalone | ❌ SyntaxError |
| `colab_export.py` | ~80 | Colab model export script (mounts Drive, packages model) | standalone | ✅ |
| `gguf_converter.py` | ~100 | Convert trained model to GGUF for CPU inference | standalone | ✅ |
| `evaluate_model.py` | ~400+ | Model evaluation framework — loads from Ollama, runs 33 domains | standalone | ✅ |
| `deploy_model.py` | ~150+ | Deployment script — builds GGUF, creates Ollama Modelfile | standalone | ✅ |
| `deploy_trained_model_ollama.py` | ~300+ | Trained model → Ollama deployment (merge LoRA, quantize, import) | standalone | ✅ |
| `completion_engine.py` | ~500+ | Hacker Training Completion Engine — generates completions for empty JSONL prompts | standalone | ✅ |
| `fill_completions.py` | ~600+ | Comprehensive completion writer for 1,202 empty completions | standalone | ✅ |
| `fill_completions_v1.py` | ~200+ | Batch completion filler via LLM | standalone | ✅ |
| `generate_curriculum.py` | ~300+ | Curriculum generator — 50+ SFT and 100+ GRPO examples | standalone | ✅ |
| `generate_data.py` | ~300+ | Generate training data across 6 security/engineering domains | standalone | ✅ |
| `generate_sft_extra.py` | ~200+ | Generate remaining SFT entries (~29 more to reach 50) | standalone | ✅ |
| `training_data_quality_pipeline.py` | ~200+ | Training data quality validator (dedup, format, schema checks) | standalone | ✅ |
| `trajectory_compressor.py` | ~400+ | Post-process agent trajectories into token budget | standalone | ✅ |
| `model_benchmark_suite.py` | ~200+ | Model benchmark suite (run benchmarks, track comparisons) | standalone | ✅ |
| `model_performance_tracker.py` | ~150+ | Model performance tracker (versions, evaluations, metrics) | standalone | ✅ |
| `post_training_analysis.py` | ~200+ | Parse training logs for issues | standalone | ✅ |
| `post_training_checklist.py` | ~150+ | Post-training deployment checklist (verify, deploy, test, report) | standalone | ✅ |
| `test_trained_model_vs_base.py` | ~300+ | Trained vs base model comparative evaluation | standalone | ✅ |
| `continuous_training_pipeline.py` | ~150+ | Continuous training pipeline (config-based, scheduled) | standalone | ✅ |
| `operation_dashboard.py` | ~150+ | Operation dashboard — training status, scan results, benchmarks | standalone | ✅ |
| `audit_jsonl.py` | ~150+ | Audit hacker_training JSONL files (count empty/filled, domains, quality) | standalone | ✅ |

---

### FINANCIAL / PAYMENT ENGINES (10 files)

| File | Lines | Purpose | Refs By | Status |
|------|-------|---------|---------|--------|
| `iso8583_engine.py` | ~600+ | ISO 8583 Financial Transaction Message Engine & Security Lab | unified_payment_gateway, redteam_agent_hitl | ✅ |
| `iso8583_parser.py` | ~300+ | ISO 8583 Message Parser and Encoder (Phase 2A Learning Project) | standalone | ✅ |
| `emv_tokenization_engine.py` | ~500+ | EMV Field 55 BER-TLV Parser & Tokenization Engine | unified_payment_gateway, detokenization_chain, redteam_agent_hitl, bionic_tools_dryrun | ✅ |
| `three_ds_simulator.py` | ~400+ | 3D Secure 2.2 Authentication Protocol Simulator | standalone | ✅ |
| `unified_payment_gateway.py` | ~300+ | Unified Payment Rails Gateway & Switch Simulator | bionic_command_center, bionic_unified_mcp_server | ✅ |
| `iso20022_engine.py` | ~400+ | ISO 20022 Financial Messaging Engine & Validator | standalone | ✅ |
| `bionic_financial_suite.py` | ~400+ | NACHA ACH Batch Generator + ISO 20022 Simulator + JetBrains IDE MCP Bridge | standalone | ✅ |
| `financial_table_extractor.py` | ~300+ | Multi-Column Financial Table Extractor & Ledger Validator | statement_extractor_cli | ✅ |
| `statement_extractor_cli.py` | ~200+ | End-to-End Financial Statement & Tax Document Extraction CLI | standalone | ✅ |
| `detokenization_chain.py` | ~200+ | Visa/MC Network Token Vault Detokenization Attack Chain Simulator | standalone | ✅ |

---

### WEB3 / BLOCKCHAIN SECURITY (9 files)

| File | Lines | Purpose | Refs By | Status |
|------|-------|---------|---------|--------|
| `web3_defi_lab.py` | ~400+ | Web3 DeFi Flash Loan Lifecycle & Vulnerability Simulation Lab | standalone | ✅ |
| `web3_contract_fuzzer.py` | ~400+ | Web3 Smart Contract Invariant & State Fuzzer | standalone | ✅ |
| `solidity_audit_scanner.py` | ~300+ | Smart Contract Bug Bounty & Security Audit Static Analyzer | bionic_audit_pipeline, bionic_unified_mcp_server | ✅ |
| `bounty_sweeper_v2.py` | ~300+ | Real-Filesystem Bounty Sweeper (scans .sol files on disk) | standalone | ✅ |
| `bounty_target_finder.py` | ~200+ | Bounty Target Finder (Immunefi, HackerOne program tracker) | standalone | ✅ |
| `blockchain_forensics.py` | ~200+ | Blockchain Forensics (transaction tracing, wallet clustering) | standalone | ✅ |
| `defi_exploit_automation.py` | ~300+ | DeFi Exploit Automation Framework (authorized fork/testnet only) | standalone | ✅ |
| `sovereign_settlement_testbed.py` | ~300+ | Sovereign Bionic Currency & Gasless EIP-712 Settlement Engine | standalone | ✅ |
| `bionic_foundry_invariant_fuzzer.py` | ~200+ | Local EVM Anvil & Foundry Invariant Fuzzing Engine | standalone | ✅ |

---

### RED TEAM / OFFENSIVE SECURITY (29 files)

| File | Lines | Purpose | Refs By | Status |
|------|-------|---------|---------|--------|
| `api_defense_lab.py` | 133 | API Vulnerability Simulation & Defense Verification Lab | bionic_audit_pipeline, bionic_command_center, bionic_unified_mcp_server | ✅ |
| `attack_surface_management.py` | 42 | Attack Surface Manager (subfinder, nmap integration) | standalone | ✅ |
| `automated_bounty_submission.py` | ~500+ | Automated bug bounty submission (HackerOne/Bugcrowd templates, CVSS) | standalone | ✅ |
| `automated_exploit_gen.py` | ~300+ | Automated Exploit Generation Engine (RCE, SQLi, XSS templates) | standalone | ✅ |
| `automated_red_team_pipeline.py` | ~500+ | Automated Red Team Pipeline (recon, analysis, evidence, reporting) | standalone | ✅ |
| `automated_scanning_pipeline.py` | ~300+ | Automated Scanning Pipeline (whois, nmap, httpx) | standalone | ✅ |
| `automated_cti_monitoring.py` | 477 | Automated CTI Monitoring (OTX, URLhaus ingestion, correlation, dashboard) | standalone | ✅ |
| `cti_feed_ingestion.py` | ~500+ | CTI Feed Ingestion Script (MISP, OTX, URLhaus, MalwareBazaar) | standalone | ✅ |
| `crapi_exploit_chain.py` | ~300+ | crAPI Full-Chain Exploit Runner (BOLA → JWT → OAuth → GraphQL → SSRF) | standalone | ✅ |
| `cloud_red_team_playbook.py` | ~300+ | Cloud Red Team Playbook Generator (AWS/GCP/Azure scenarios) | standalone | ✅ |
| `deception_engine.py` | ~80 | Deception Engine (honeypot, canary token deployment) | standalone | ✅ |
| `exploit_recommendation_engine.py` | ~150+ | Exploit Recommendation Engine (maps vuln types to tools) | standalone | ✅ |
| `firmware_iot_analyzer.py` | ~200+ | Firmware/IoT Analyzer (binwalk extraction, credential scanning) | standalone | ✅ |
| `hexstrike_live_server.py` | ~600+ | HexStrike AI Live Security Engine & Hermes MCP Server (port scan, HTTP audit) | bionic_audit_pipeline, bionic_unified_mcp_server | ✅ |
| `hexstrike_hermes_proxy.py` | ~400+ | HexStrike AI Hermes MCP Proxy (81 tool schemas, no Kali tools needed) | standalone | ✅ |
| `jailbreak_prompt_generator.py` | ~300+ | Jailbreak Prompt Generator (adversarial prompt generation for safety testing) | standalone | ✅ |
| `llm_adversarial_suite.py` | ~200+ | Adversarial LLM Evaluation & Jailbreak Defense Test Suite | standalone | ✅ |
| `malware_analysis_sandbox.py` | ~300+ | Malware Analysis Sandbox (VirusTotal, Any.Run, YARA, Capa) | standalone | ✅ |
| `phishing_simulation_automation.py` | ~300+ | Phishing Simulation Automation (authorized training only) | standalone | ✅ |
| `purple_team_automation.py` | ~150+ | Purple Team Automation (red/blue exercise orchestration) | standalone | ✅ |
| `red_team_infrastructure.py` | ~300+ | Red Team Infrastructure as Code (Terraform, Ansible, C2 management) | standalone | ✅ |
| `redteam_agent_hitl.py` | ~200+ | Production red-team agent with HITL middleware wired in | standalone | ✅ |
| `redteam_middleware.py` | ~300+ | Pure Human-in-the-Loop control mechanism for LangChain v1 agents | 7 files: final_integration_check, redteam_agent_hitl, test_agent_integration, test_auth_path, test_hitl_integration, test_middleware_logic, test_redteam_middleware | ✅ |
| `security_knowledge_base.py` | ~200+ | Security Knowledge Base (findings, TTPs, lessons, tools) | standalone | ✅ |
| `ttp_emulation_engine.py` | ~150+ | TTP Emulation Engine (MITRE ATT&CK technique simulation) | standalone | ✅ |
| `wireless_security.py` | ~300+ | Wireless Security Framework (Windows netsh + PowerShell) | standalone | ✅ |
| `bionic_api_proxy.py` | ~300+ | Local API Fallback Proxy (port 8000, proxies to Nous API with Ollama fallback) | standalone | ✅ |
| `bionic_api_resilience.py` | ~200+ | API Resilience & Model Fallback Configuration (retry, rate limit, timeout) | standalone | ✅ |
| `bionic_async_relayer_daemon.py` | ~300+ | Tier 2: Autonomous Async EIP-712 Relayer Daemon | standalone | ✅ |
| `bionic_bounty_sweeper.py` | ~300+ | Tier 4: Immunefi & Web3 Bounty Invariant Sweeper | standalone | ✅ |

---

### BLUE TEAM / DEFENSIVE (16 files)

| File | Lines | Purpose | Refs By | Status |
|------|-------|---------|---------|--------|
| `compliance_automation.py` | ~500+ | Compliance Automation (PCI-DSS gap, SOC 2 mapping, evidence collection) | standalone | ✅ |
| `incident_response_playbooks.py` | ~200+ | Incident Response Playbooks (detection, severity, escalation) | standalone | ✅ |
| `security_metrics_dashboard.py` | ~400+ | Security Metrics Dashboard (training, evals, scans, bounty data) | standalone | ✅ |
| `threat_model_engine.py` | ~400+ | Threat Modeling Engine (STRIDE, attack trees, DFDs, mitigation mapping) | standalone | ✅ |
| `threat_modeling_engine.py` | ~150+ | Threat Modeling Engine (STRIDE analysis, component threats) | standalone | ✅ |
| `threat_report_writer.py` | 95 | Threat Report Writer (generates markdown/HTML threat intel reports) | standalone | ❌ SyntaxError |
| `vulnerability_correlation_engine.py` | ~400+ | Vulnerability Correlation Engine (Nessus/Nuclei → ATT&CK, attack chains) | standalone | ✅ |
| `attack_technique_knowledge_graph.py` | 88 | MITRE ATT&CK Knowledge Graph (techniques, edges, pathfinding) | standalone | ✅ |
| `persona_consistency_checker.py` | ~150+ | Persona Consistency Checks (Bionic Daughter identity/persona tests) | standalone | ✅ |
| `prompt_injection_classifier.py` | ~200+ | Automated Prompt Injection Classifier (local detection, no API) | standalone | ✅ |
| `osint_automation_engine.py` | ~400+ | OSINT Automation Engine (domain, email, social, dark web, CTI) | standalone | ✅ |
| `research_ingester.py` | ~150+ | Research Ingester (security blog post ingestion, training example generation) | standalone | ✅ |
| `cve_to_training_data.py` | ~150+ | CVE to Training Data Converter (CVE descriptions → prompt/completion pairs) | standalone | ✅ |
| `automated_reporting_system.py` | ~300+ | Automated Reporting System (professional security reports from findings) | standalone | ✅ |
| `audit_jsonl.py` | ~150+ | Audit hacker_training JSONL files (quality analysis) | standalone | ✅ |
| `continuous_training_pipeline.py` | ~150+ | Continuous Training Pipeline (scheduled, config-driven) | standalone | ✅ |

---

### BIONIC PLATFORM INFRASTRUCTURE (10 files)

| File | Lines | Purpose | Refs By | Status |
|------|-------|---------|---------|--------|
| `bionic_audit_pipeline.py` | ~400+ | One-Click Automated Red Team & Security Audit Pipeline | standalone | ✅ |
| `bionic_canonical_sync.py` | ~200+ | Canonical Local Backup & Sync Engine | standalone | ✅ |
| `bionic_cloud_vps_engine.py` | ~500+ | Private Cloud VPS & MicroVM Management Engine | standalone | ✅ |
| `bionic_code_engine.py` | ~400+ | Software Engineering & Meta-Coding Engine (AST, complexity, linting) | standalone | ✅ |
| `bionic_command_center.py` | ~500+ | Unified Bionic Command Center Terminal Dashboard (TUI) | standalone | ✅ |
| `bionic_self_dev.py` | ~400+ | Self-Development & Meta-Agent Engine (capability profiling, tool scaffolding) | standalone | ✅ |
| `bionic_tools_dryrun.py` | ~300+ | Dry-run probe for bionic tools (no side effects) | standalone | ✅ |
| `bionic_unified_mcp_server.py` | ~500+ | Unified FastMCP Suite Server (8 registered tools) | standalone | ✅ |
| `orca_swarm_orchestrator.py` | ~300+ | Orca ADE Multi-Agent Swarm Orchestrator (5 parallel task lanes) | standalone | ✅ |
| `multi_agent_swarm.py` | ~200+ | Multi-Agent Swarm (agent task execution, result aggregation) | standalone | ✅ |

---

### UTILITY / SCRAPING / MISC (16 files)

| File | Lines | Purpose | Refs By | Status |
|------|-------|---------|---------|--------|
| `youtube_transcript.py` | ~80 | Playwright script to extract YouTube video description/transcript | standalone | ✅ |
| `youtube_transcript2.py` | 31 | Playwright script to extract YouTube transcript (three-dots menu) | standalone | ❌ SyntaxError |
| `youtube_transcript3.py` | ~80 | Playwright script to extract YouTube transcript (full page text parsing) | standalone | ✅ |
| `youtube_watch.py` | ~50 | Playwright script to get YouTube video title, description, transcript | standalone | ✅ |
| `cdp_groq.py` | ~80 | Chrome DevTools Protocol script to grab Groq API key from browser tab | standalone | ✅ |
| `cdp2.py` | ~100 | CDP script to attach to Groq tab, create new page target | standalone | ✅ |
| `extract_pdf.py` | ~80 | Extract text from hermes-kanban-v1-spec.pdf (pypdf/PyPDF2/pdfminer) | standalone | ✅ |
| `groq_client.py` | ~150+ | Groq Inference Client (ultra-fast LLM inference, free tier) | standalone | ✅ |
| `h1_token_status.py` | ~150+ | HackerOne MCP Token Status Detector | standalone | ✅ |
| `wayfinder.py` | ~100 | WAYFINDER: Autonomous GRPO Training System (CPU-only) | standalone | ✅ |
| `deepfake_detector.py` | ~150+ | Deepfake Detector (image/video manipulation analysis) | standalone | ✅ |
| `rebase_strategy.py` | ~200+ | Rebase Strategy Script for GRPO training code (5,067 commits) | standalone | ✅ |
| `registration_lifecycle.py` | ~150+ | Ownership leases for replaceable runtime registrations | standalone | ✅ |
| `automated_bounty_submission.py` | ~500+ | Automated bug bounty submission (already listed above) | standalone | ✅ |
| `_gen.py` | 45 | Code generator — writes red_team_infrastructure.py stub | standalone | ✅ |
| `_gen_cti.py` | ~30 | Code generator — writes automated_cti_monitoring.py stub | standalone | ✅ |

---

### TEST / INTEGRATION (10 files)

| File | Lines | Purpose | Refs By | Status |
|------|-------|---------|---------|--------|
| `run_tests.py` | ~100 | BIONIC DAUGHTER Tool Test Suite (runs all tool tests) | standalone | ✅ |
| `final_integration_check.py` | ~150+ | Final integration verification (imports, wiring) | standalone | ✅ |
| `test_agent_integration.py` | ~100 | Quick integration test: redteam_agent_hitl imports + constructs | standalone | ✅ |
| `test_auth_path.py` | ~100 | Test middleware intercepts and logs properly when authorized | standalone | ✅ |
| `test_hitl_integration.py` | ~100 | End-to-end integration test: HITL wired into create_agent | standalone | ✅ |
| `test_middleware_logic.py` | ~100 | Integration test for RedTeamHITLMiddleware using AgentMiddleware pattern | standalone | ✅ |
| `test_redteam_middleware.py` | ~80 | Quick smoke test for RedTeamHITLMiddleware (authorization loop) | standalone | ✅ |
| `test_trained_model_vs_base.py` | ~300+ | Trained vs base model comparative evaluation | standalone | ✅ |
| `bionic_tools_dryrun.py` | ~300+ | Dry-run probe for bionic tools (no side effects) | standalone | ✅ |
| `persona_consistency_checker.py` | ~150+ | Persona consistency tests (Bionic Daughter identity) | standalone | ✅ |

---

## CROSS-REFERENCE MAP (Key Dependencies)

```
redteam_middleware.py
  ← final_integration_check.py
  ← redteam_agent_hitl.py
  ← test_agent_integration.py
  ← test_auth_path.py
  ← test_hitl_integration.py
  ← test_middleware_logic.py
  ← test_redteam_middleware.py

utils.py
  ← batch_runner.py, cli.py, hermes_logging.py
  ← hermes_state_portability.py, hermes_state_schema.py
  ← hermes_state_search.py, run_agent.py, trajectory_compressor.py

hermes_state_common.py
  ← hermes_state.py + 17 hermes_state_*.py mixins

hermes_constants.py
  ← hermes_logging.py, hermes_state.py, hermes_state_fts.py
  ← hermes_state_schema.py, hermes_state_wal.py, mcp_serve.py

hermes_time.py
  ← hermes_logging.py

api_defense_lab.py
  ← bionic_audit_pipeline.py, bionic_command_center.py, bionic_unified_mcp_server.py

hexstrike_live_server.py
  ← bionic_audit_pipeline.py, bionic_unified_mcp_server.py

solidity_audit_scanner.py
  ← bionic_audit_pipeline.py, bionic_unified_mcp_server.py

unified_payment_gateway.py
  ← bionic_command_center.py, bionic_unified_mcp_server.py

emv_tokenization_engine.py
  ← unified_payment_gateway.py, detokenization_chain.py
  ← redteam_agent_hitl.py, bionic_tools_dryrun.py, final_integration_check.py

iso8583_engine.py
  ← unified_payment_gateway.py, redteam_agent_hitl.py

financial_table_extractor.py
  ← statement_extractor_cli.py

toolsets.py
  ← toolset_distributions.py, model_tools.py, run_agent.py

batch_runner.py
  ← mini_swe_runner.py

hermes_bootstrap.py
  ← batch_runner.py, cli.py, run_agent.py
```

---

## UNTESTED / NEEDS SANDBOX VERIFICATION

The following files have **no automated tests** and require sandbox/manual verification:

1. `threat_report_writer.py` — ❌ has syntax error; fix line 35 first
2. `youtube_transcript2.py` — ❌ has syntax error; fix nested quotes on line 11
3. `colab_grpo_training.py` — ❌ has syntax error (notebook magic); rename to .ipynb or document as Colab-only
4. `automated_cti_monitoring.py` — HTTP dashboard server, needs runtime test
5. `hexstrike_live_server.py` — MCP server with port scanning, needs runtime test
6. `redteam_agent_hitl.py` — LangChain agent with HITL middleware, needs runtime test
7. `api_defense_lab.py` — Self-contained assertions (passes via `__main__`)
8. `grpo_train.py` — Full training pipeline, needs GPU/CUDA environment
9. `grpo_sanity_smoke.py` — CPU smoke test, needs torch/trl/peft/datasets installed
10. `unified_payment_gateway.py` — End-to-end payment flow, needs runtime test
11. `web3_contract_fuzzer.py` — Fuzzing engine, needs runtime test
12. `solidity_audit_scanner.py` — Static analyzer, needs .sol test corpus
13. `bionic_unified_mcp_server.py` — FastMCP server, needs runtime test
14. `bionic_audit_pipeline.py` — Full audit pipeline, needs runtime test
15. `compliance_automation.py` — Compliance gap analysis, needs runtime test
16. `malware_analysis_sandbox.py` — VirusTotal/Any.Run integration, needs API keys
17. `deepfake_detector.py` — Image/video analysis, needs runtime test
18. `wireless_security.py` — Windows netsh/PowerShell, needs Windows runtime
19. `firmware_iot_analyzer.py` — Binwalk integration, needs firmware test files
20. `operation_dashboard.py` — Dashboard generator, needs artifact files
21. `post_training_checklist.py` — Deployment checklist, needs trained model artifacts
22. `deploy_trained_model_ollama.py` — Ollama deployment, needs Ollama running
23. `gguf_converter.py` — GGUF conversion, needs llama.cpp
24. `bionic_cloud_vps_engine.py` — VPS management, needs hypervisor
25. `bionic_canonical_sync.py` — File sync engine, needs filesystem watch
26. `orca_swarm_orchestrator.py` — Multi-agent swarm, needs runtime test
27. `cdp_groq.py` — Chrome DevTools Protocol, needs browser running
28. `cdp2.py` — Chrome DevTools Protocol, needs browser running
29. `youtube_transcript.py` — Playwright script, needs Chromium + YouTube
30. `youtube_transcript3.py` — Playwright script, needs Chromium + YouTube
31. `youtube_watch.py` — Playwright script, needs Chromium + YouTube
32. `extract_pdf.py` — PDF extraction, needs pypdf/PyPDF2/pdfminer + test PDF

---

## RECOMMENDATIONS

1. **Fix syntax errors** in `threat_report_writer.py` (line 35) and `youtube_transcript2.py` (line 11).
2. **Rename `colab_grpo_training.py`** → `colab_grpo_training.ipynb` or add a header comment explaining it's Colab-only.
3. **Add `if __name__ == "__main__"` guards** to MCP servers and long-running scripts that currently execute on import.
4. **Add `psutil` to requirements** — `hermes_state_guard.py` and `hermes_state_holders.py` import it as a hard dependency.
5. **Add tests** for the 30+ files marked "UNTESTED" above.
6. **Consider consolidating** duplicate threat model engines (`threat_model_engine.py` vs `threat_modeling_engine.py`).
7. **Consider consolidating** duplicate YouTube transcript scrapers (3 files with overlapping functionality).
