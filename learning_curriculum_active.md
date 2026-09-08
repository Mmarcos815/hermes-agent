# LEARNING CURRICULUM — Active Roadmap (Build-to-Learn)
**Operator:** Bionic Daughter (Hermes Agent)
**Authority:** Dad (Rigoberto Gomez)
**Started:** 2026-09-02
**Methodology:** Build to learn, not theory-only. Every skill = 1 shipped tool that uses it.

---

# THE 11 SKILLS, IN ORDER OF LEVERAGE

| Tier | # | Skill | First Project | Time | Why First |
|---|---|---|---|---|---|
| **T1** | 1 | Rust | hello_world binary + bionic_packet_engine v0 | 8 hrs | Native tools beat Python equivalents 100x for hot paths |
| **T1** | 2 | Solidity invariants | 3 new invariants on sovereign_foundry | 6 hrs | Foundry fuzz already proven; extend to invariants |
| **T1** | 3 | Production MCP | Streaming + resources on bionic_unified | 6 hrs | Required for any serious agent tooling |
| **T2** | 4 | Prompt injection hardening | Rep-engineering layer on GuardrailAuditor | 8 hrs | Defensive layer for all LLM traffic |
| **T2** | 5 | EVM internals | Custom tracer for SWC patterns | 10 hrs | On-chain forensics capability |
| **T2** | 6 | TLS 1.3 at wire | MitM-aware analyzer extending tls13_engine | 8 hrs | Builds on existing scaffold |
| **T3** | 7 | Kubernetes security | kube-hunter + kube-bench on local docker cluster | 6 hrs | Container security = deploy security |
| **T3** | 8 | Windows internals | ETW trace + minifilter pattern | 10 hrs | Native defense tooling |
| **T4** | 9 | GPU kernels | Minimal CUDA + nvcc verification | 12 hrs | Optimize Colab training beyond HF Trainer |
| **T4** | 10 | Reverse engineering | angr script for SWC detection in bytecode | 10 hrs | Auditing deployed contracts |
| **T4** | 11 | Formal verification | Certora-style spec for SovereignBionicCurrency | 8 hrs | Math-prove the AMM invariants |

**Total estimate:** ~90 hours of focused work. Realistic pace: 4-6 skills per month at Dad's cadence.

---

# PHASE 1 (T1 — Foundation, 20 hours)

### Skill 1: Rust

**Why:** The `rust_packet_engine` MCP server is wired but no binary exists. I need Rust to build it.

**Build project:** `rust_tools/`
- `Cargo.toml` workspace
- `crates/hello_world/` — minimal `cargo build --release` produces a Windows .exe
- `crates/packet_engine/` — port the stub MCP server to Rust with native TCP/UDP packet parsing

**Learning sources:**
- The Rust Book (https://doc.rust-lang.org/book/)
- Rust by Example
- Tokio tutorial (for async MCP transport)

**Done when:**
- `cargo build --release` produces a real .exe on Windows
- The .exe can be invoked as an MCP stdio server
- Replaces the missing `bionic_packet_engine.exe` in `rust_tools/target/release/`

### Skill 2: Solidity Invariants

**Why:** Foundry fuzz ran 10k random swaps, all clean. But that's statistical, not mathematical. Invariants are stronger.

**Build project:** `bionic-sovereign/test/`
- `test/SovereignBionicInvariants.t.sol` — 3 new invariants:
  1. `invariant_k_preserved()` — `reserve * supply == k` ALWAYS
  2. `invariant_no_drain()` — vault can never be drained below initial_reserve
  3. `invariant_sequential_consistency()` — multiple users + multiple ops preserve solvency

**Done when:** `forge test --match-contract SovereignBionicInvariants -vv` runs clean with `--invariant-runs 256 --invariant-depth 64`.

### Skill 3: Production MCP

**Why:** Current MCP servers are basic JSON-RPC. Next-gen MCP supports streaming, resources, sampling.

**Build project:** `bionic_unified_mcp_server.py` extension
- Add `resources/list` + `resources/read` for streaming audit results
- Add `notifications/message` for progress reporting during long operations
- Add `sampling/createMessage` for inline LLM queries during tool execution

**Done when:** Server supports all 5 MCP primitives: tools, resources, prompts, sampling, notifications.

---

# PHASE 2 (T2 — Specialization, 26 hours)

### Skill 4: Prompt Injection Hardening

**Build:** Extend `llm_adversarial_suite.py`
- Add representation-engineering layer (latent space analysis)
- Add 5 new attack patterns (parseltongue, ROT13, base64, token-split, homoglyph)
- Add jailbreak detection at the embedding level

### Skill 5: EVM Internals

**Build:** New `bionic_evm_tracer.py`
- Custom Foundry tracer (Python) that flags:
  - `DELEGATECALL` to non-whitelisted addresses
  - `SELFDESTRUCT` calls
  - `STATICCALL` violations
  - Unusual gas patterns
- Real-time flag stream during tx simulation

### Skill 6: TLS 1.3 at the Wire

**Build:** Extend `tls13_engine.py`
- Parse ClientHello extensions byte-by-byte
- Detect downgrade attacks (version fallback to 1.2/1.1/1.0)
- Detect cipher suite mismatches
- Detect session resumption without proper PSK

---

# PHASE 3 (T3 — Infrastructure, 16 hours)

### Skill 7: Kubernetes Security

**Build:** `k8s_security_lab.py`
- Spin up kind/k3d cluster locally
- Run kube-bench CIS benchmark
- Run kube-hunter pen-test
- Generate hardened RBAC manifest

### Skill 8: Windows Internals

**Build:** `windows_etw_monitor.py`
- Subscribe to ETW providers (Process, File, Registry, Network)
- Pattern detection for ransomware indicators (mass file rename + extension change)
- ETW consumer in Python (pywintrace / etw)

---

# PHASE 4 (T4 — Career-grade, 30 hours)

### Skill 9: GPU Kernels

**Build:** `cuda_kernel_minimal/`
- Vector add kernel in CUDA C++
- nvcc build script
- PyTorch integration via custom op
- Benchmark vs pure PyTorch equivalent

### Skill 10: Reverse Engineering

**Build:** `bionic_bytecode_analyzer.py`
- angr script to load deployed contract bytecode
- Auto-detect 5 SWC patterns:
  - SWC-100 (function default visibility)
  - SWC-101 (integer overflow/underflow)
  - SWC-104 (unchecked return value)
  - SWC-105 (unprotected Ether withdrawal)
  - SWC-107 (reentrancy)

### Skill 11: Formal Verification

**Build:** `certora_specs/sovereign_bionic.spec`
- Certora CVL spec for SovereignBionicCurrency
- Proves `k_invariant` mathematically
- Proves `no_drain_possible`
- Proves `permit_replay_blocked`

---

# HOW TO TRACK PROGRESS

Each skill gets its own folder under `learning/`:
```
learning/
├── 01_rust/
│   ├── PROGRESS.md       # daily notes
│   ├── hello_world/      # source
│   └── packet_engine/    # source
├── 02_solidity_invariants/
│   └── PROGRESS.md
...
```

Every shippable artifact gets a `_AUDITS/learning_<skill>_log.md` audit entry with:
- Source code (or commit hash)
- Build/compile evidence
- Test/benchmark evidence
- What I learned (concrete, not vague)

---

# MOMENTUM RULES

1. **One skill at a time.** Don't jump around. Depth > breadth.
2. **Build to learn, ship to remember.** Every skill = 1 deliverable.
3. **Stub = waste.** Never ship a `.stub` file. Real run or no run.
4. **Test against real services.** Foundry on Anvil, not mock.
5. **Document as I go.** Future me will thank present me.

---

**Phase 1 begins now with Skill 1: Rust.**
**Source files land in `learning/01_rust/` as I build.**