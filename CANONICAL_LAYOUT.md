# CANONICAL LAYOUT — Bionic Daughter Agent Storage

**Operator:** Bionic Daughter (Hermes Agent)
**Authority:** Dad (Rigoberto Gomez)
**Last Sync:** 2026-09-05
**Status:** ✅ ALL 20 FILES SYNCED

---

## Directory Tree

```
C:\Users\mobil\OneDrive\Desktop\bionic_daughter_agent\
├── _AUDITS/
│   ├── CANONICAL_SYNC_MANIFEST.json    # SHA256 audit of all synced files
│   ├── CANONICAL_TESTBEDS/             # (legacy)
│   │
│   ├── sovereign_settlement_testbed.py
│   ├── bionic_financial_suite.py
│   ├── bionic_async_relayer_daemon.py
│   ├── bionic_foundry_invariant_fuzzer.py
│   ├── bionic_bounty_sweeper.py
│   ├── bionic_audit_pipeline.py
│   ├── bionic_cloud_vps_engine.py
│   ├── bionic_code_engine.py
│   ├── bionic_command_center.py
│   ├── bionic_self_dev.py
│   ├── bionic_tools_dryrun.py
│   ├── bionic_unified_mcp_server.py
│   ├── redteam_agent_hitl.py
│   ├── redteam_middleware.py
│   ├── iso8583_engine.py
│   ├── unified_payment_gateway.py
│   ├── emv_tokenization_engine.py
│   ├── three_ds_simulator.py
│   ├── iso20022_engine.py
│   └── financial_table_extractor.py
│
├── knowledge/
│   └── grpo_security_reasoning_dataset.jsonl   # Canonical training corpus
│
└── (future: trained model artifacts, GRPO checkpoints)
```

---

## Sync Policy

- **Source:** `C:\Users\mobil\orca\projects\my 1st\` (working tree)
- **Destination:** OneDrive Desktop `bionic_daughter_agent\_AUDITS\`
- **Trigger:** After every major commit or tool generation
- **Integrity:** SHA256 prefix logged in `CANONICAL_SYNC_MANIFEST.json`
- **Rule:** Nothing scattered. Everything in OneDrive. Nothing lost.

---

## File Categories

| Category | Files | Purpose |
|---|---|---|
| **Red Team Tools** | `redteam_agent_hitl.py`, `redteam_middleware.py` | HITL exploit agent + LangChain middleware |
| **Payment Rails** | `iso8583_engine.py`, `unified_payment_gateway.py`, `emv_tokenization_engine.py`, `three_ds_simulator.py`, `iso20022_engine.py` | Financial transaction engines |
| **Bionic Core** | `bionic_financial_suite.py`, `bionic_async_relayer_daemon.py`, `bionic_cloud_vps_engine.py`, `bionic_code_engine.py` | Core bionic infrastructure |
| **Foundry** | `bionic_foundry_invariant_fuzzer.py`, `sovereign_settlement_testbed.py` | Solidity fuzz + settlement |
| **MCP** | `bionic_unified_mcp_server.py` | Unified MCP server |
| **Audit** | `bionic_audit_pipeline.py`, `bionic_bounty_sweeper.py` | Audit + bounty automation |
| **Misc** | `bionic_command_center.py`, `bionic_self_dev.py`, `bionic_tools_dryrun.py`, `financial_table_extractor.py` | Utilities |
