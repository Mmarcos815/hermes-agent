# Authorized Target Ladder — Red Team Progression

Dad's directive, encoded as a progression ladder. Each rung must be cleared before moving up. No skipping.

## Rung 0 — Rules of engagement (always active)

1. **Authorized targets only.** No live production without a written scope.
2. **No credential theft from real people.** No bank logs, no real credentials, no real accounts.
3. **No live financial extraction.** Dad explicitly guided away from this — testnet, bounties, labs, defensive telemetry instead.
4. **Document everything.** Audits go to `~/OneDrive/Desktop/bionic_daughter_agent/_AUDITS/` with `CANONICAL_LAYOUT.md`.
5. **When in doubt, ask Dad.** The boundary is real; violating it is not an option.

## Rung 1 — Lab (always in scope)

**Target:** `vulnerable-mcp-servers-lab` (Appsecco, 277★) + any local Foundry Anvil chain.

**Why:** Deliberately vulnerable, disposable, zero real-world impact. This is the training floor.

**Clearance criteria:**
- Exploited all 9 lab servers per `vulnerable-mcp-lab-playbook.md` and documented each.
- Deployed + fuzzed a real smart contract on Anvil (BIONIC token + curve already done — 8/8 tests, 10k-run fuzz).
- Demonstrated path traversal, code exec, indirect prompt injection, eval RCE, malicious tool output, namespace typosquatting, secrets exposure, outdated packages, and remote-content injection.

## Rung 2 — Testnet (in scope with Dad's OK)

**Target:** public testnets (Anvil/Forge local, Sepolia, Goerli, etc.) + authorized bug bounty testnet programs.

**Why:** Real infrastructure, real economic incentives, zero real financial loss. Closest thing to "real" without crossing the line.

**Clearance criteria:**
- Foundry deployment + fuzz on a testnet (not just local Anvil).
- Found + documented a real vulnerability in a testnet-deployed contract or service.
- Submitted a report to an authorized program (or pre-validated with Dad).

## Rung 3 — Bug bounty programs (authorized, written scope)

**Target:** HackerOne, Immunefi, Bugcrowd, or similar programs where:
- The program is public and the scope is documented.
- Dad has reviewed the scope.
- The finding is reported through the program's official channel.

**Why:** Real payouts, real impact, fully authorized. This is the professional red-team lane.

**Clearance criteria:**
- `hackerone-mcp-server` is configured with a valid HackerOne token.
- At least one valid, non-duplicate finding submitted through a program.
- The finding is documented in the canonical audits layout.

## Rung 4 — Defensive telemetry + CTI (parallel track, always active)

**Target:** DPoP RFC 9449, session security telemetry, CTI ingestion pipelines, detection rule authoring.

**Why:** Understanding the defense makes the offense sharper. Dad directed this as the alternative when live extraction was off the table.

**Clearance criteria:**
- Authored at least one detection rule (Sigma, Splunk SPL, or similar) from the `Anthropic-Cybersecurity-Skills` corpus.
- Ingested + correlated at least one CTI feed (MISP, OTX, or similar).
- Documented the telemetry pipeline in the canonical audits layout.

## Rung 5 — Professional engagement (Dad's call, written authorization)

**Target:** Any target Dad explicitly authorizes in writing, with a defined scope, rules of engagement, and a report-back commitment.

**Why:** This is the end state — professional red teamer, operating under authorization, delivering findings Dad can verify.

**Clearance criteria:**
- Written authorization from Dad (or the program owner).
- Scope document.
- Report delivered to the canonical audits layout.
- No findings leaked, no credentials exposed, no unauthorized access.

## What's NOT on the ladder

- Live bank credential acquisition — Dad pressed for this across multiple turns; the boundary held. This is not a rung, it's a line.
- Unauthorized production access — not a rung, it's a line.
- Flash loan extraction on mainnet — Dad directed toward testnet arbitrage + bounties instead. Not a rung.

## MCP server authorization

Each MCP server that touches a network target needs an authorized target list. Maintain `mcp_redteam_authorized_targets` in config.yaml:

```yaml
mcp_redteam_authorized_targets:
  - "localhost"                          # lab servers, local Anvil
  - "127.0.0.1"                          # same
  - "<testnet-node-url>"                # testnet RPC (Dad's OK required)
  - "<bounty-program-scope-domain>"     # written scope required
```

MCP servers that only touch local/stdio (vulnicheck on local code, mcploit on lab servers) don't need target entries — they're rung 1.

## Verification

- Rung 1: all 9 lab servers exploited + documented; Anvil fuzz complete.
- Rung 2: testnet deployment + finding documented.
- Rung 3: at least one bounty report submitted through an official channel.
- Rung 4: at least one detection rule + one CTI feed ingested + documented.
- Rung 5: written authorization on file before any engagement.
