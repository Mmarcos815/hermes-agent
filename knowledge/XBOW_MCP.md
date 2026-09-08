# ============================================================================
# BIONIC DAUGHTER v1 — XBOW MCP INTEGRATION GUIDE
# ============================================================================
# DOC_AUTH: Daughter
# PURPOSE: Document XBOW (the autonomous offensive security platform), how to
#          integrate it with the daughter's MCP layer, and the open-source
#          XBOW competition MCP server (ez-xbow-platform-mcp).
# CONTEXT: XBOW is a commercial platform. The open-source MCP server is the
#          integration path available to us.
# ============================================================================

## ========================================================================
## PART 1 — WHAT XBOW IS (THE AUTONOMOUS OFFENSIVE SECURITY PLATFORM)
## ========================================================================

## XBOW OVERVIEW

XBOW (xbow.com) is an autonomous offensive security platform — an AI hacker that
finds and proves vulnerabilities in web applications and APIs. It was founded in
2024 by Oege de Moor (creator of GitHub Copilot, former founder of Semmle/CodeQL)
and built with engineers from the original Copilot team.

## THE KEY FACTS

| Fact | Detail |
|------|--------|
| Founded | 2024 by Oege de Moor (GitHub Copilot creator) |
| Team | Engineers from the original Copilot team |
| Status | Commercial platform (SaaS) |
| Certifications | SOC 2, ISO 27001, PCI DSS, NIS 2 |
| Customers | 150+ security teams globally |
| Key achievement | #1 on HackerOne (June 2025) — ranked above every human researcher |
| Microsoft MSRC | 1st place as autonomous system on Microsoft's MSRC leaderboard |
| Zero days found | 14,000+ in real customer applications |
| Notable find | 9.8 critical Microsoft flaw found completely autonomously |
| Benchmark | XBOW Benchmark — 104 web security challenges for autonomous pentest evaluation |
| GitHub | xbow-security org (xbow-engineering/validation-benchmarks repo) |

## WHAT XBOW ACTUALLY DOES

1. **Point XBOW at a URL** — you give it a target (web application, API endpoint)
2. **XBOW explores like a real attacker** — it crawls the application, maps endpoints,
   identifies input vectors, tests for vulnerabilities
3. **Chains vulnerabilities into attack paths** — XBOW doesn't just find individual
   vulnerabilities; it chains them together into working attack sequences. This is
   what sets it apart — most scanners find individual issues, XBOW finds attack chains.
4. **Proves exploitability** — every finding comes with a working, reproducible exploit.
   Not just "there's a vulnerability" but "here's exactly how to exploit it, and here's
   the proof."
5. **Generates a complete case file** — the chained attack path, the working exploit,
   a full log of every decision and tactic, developer-ready remediation guidance.
6. **Nearly zero false positives** — because every finding is proven exploitable, there's
   no noise. What XBOW reports is real.

## THE DIFFERENTIATORS

### 1. CHAINING (THE BIG ONE)
Most security tools find individual vulnerabilities. XBOW chains them into attack paths.
Example: a weak access control + an information disclosure + a privilege escalation =
a complete account takeover chain. XBOW finds the chain, not just the individual issues.

### 2. PROOF, NOT JUST FINDINGS
Every XBOW finding is a real, reproducible exploit. This matters because:
- Security teams can trust the findings (no false positives to filter through)
- Developers get concrete reproduction steps (not vague descriptions)
- The business gets board-ready reporting (proof, not theory)

### 3. COVERAGE WITHOUT HEADCOUNT
XBOW scales with the attack surface, not the team. You can point it at many applications
continuously. Traditional pentesting is point-in-time and resource-intensive. XBOW is
continuous and scales automatically.

### 4. PROVEN IN PUBLIC
XBOW proved itself on HackerOne (the world's largest bug bounty platform) — ranking #1,
above every human researcher. It found a 9.8 critical Microsoft flaw autonomously. This
isn't marketing claims — it's public, verifiable achievement.

## THE XBOW BENCHMARK (OPEN-SOURCE EVALUATION)

The XBOW Benchmark is a collection of 104 web application security challenges designed
for evaluating autonomous penetration testing agents. It's open-source (xbow-engineering/
validation-benchmarks on GitHub) and serves as the standard for comparing autonomous
pentest agents.

Key facts about the benchmark:
- 104 web security challenges
- Covers a range of difficulty levels
- Designed for autonomous agent evaluation (not human pentesters)
- Used by researchers and competitors to measure agent capability
- Open-source, buildable via `make build`

The benchmark has become the standard for measuring autonomous pentest agent capability.
Multiple open-source agents have been built and evaluated against it.

## ========================================================================
## PART 2 — XBOW AS A COMMERCIAL PLATFORM (THE SAAS PRODUCT)
## ========================================================================

## HOW THE COMMERCIAL XBOW PLATFORM WORKS

1. **You provide a target** — a URL, an API endpoint, a scope of applications
2. **XBOW runs autonomously** — no human input required during the test
3. **XBOW finds and proves vulnerabilities** — produces findings with working exploits
4. **You review the findings** — each finding is a complete case file with proof
5. **You remediate** — fix what XBOW found, with developer-ready guidance
6. **XBOW retests** — verify the fixes work

## XBOW'S GUARDRAILS (GOVERNANCE)

XBOW is designed for enterprise use with governance:
- **Scope definition** — you define what XBOW can test (no unauthorized targets)
- **Action logging** — every action is logged and auditable
- **Data separation** — your data is separated from other customers
- **Compliance** — SOC 2, ISO 27001, PCI DSS, NIS 2 compliant
- **Deployment flexibility** — aligns with data residency requirements

## XBOW PRICING (BUSINESS MODEL)

XBOW is a commercial SaaS product. Pricing isn't publicly listed (demo required).
It's positioned as an enterprise security product — likely priced for security teams
and organizations, not individuals.

## ========================================================================
## PART 3 — XBOW MCP INTEGRATION (THE OPEN-SOURCE PATH)
## ========================================================================

## THE KEY INSIGHT: XBOWTERS CONTEST MCP SERVER

There's an open-source project that provides an MCP server for XBOW-style pentesting:
**ez-xbow-platform-mcp** (by m-sec-org, part of the xbow-competition project).

This is an MCP server that connects AI agents to XBOW-style challenge platforms,
providing:
- Challenge management (list, attempt, submit solutions)
- Knowledge base (9 vulnerability categories: XSS, SQL, SSTI, SSRF, IDOR, XXE, LFI,
  Code Injection, Auth & Priv Esc)
- Persistent Kali container (execute security tools: nmap, sqlmap, gobuster, etc.)
- Attempt history (auto-note management, cross-session tracking)
- Multiple transport protocols (stdio, SSE, HTTP/2 stream)

## THE XBOW-COMPETITION PROJECT (m-sec-org)

The xbow-competition project (github.com/m-sec-org/xbow-competition) is a complete
AI agent automated XBOW challenge-solving system. It includes:

### COMPONENT 1: ez-xbow-platform-mcp (THE MCP SERVER)
- Go-based MCP server (requires Go 1.24.7+)
- Connects AI agents to XBOW platforms (real or mock)
- Provides challenge management, knowledge base, Kali container execution
- Supports stdio, SSE, and HTTP/2 stream protocols
- Can run in mock mode (local testing) or connect to real XBOW platform

### COMPONENT 2: kimi-cli-for-xbow (THE CLI AGENT)
- Python-based CLI agent (requires Python 3.13+, uv)
- Based on MoonshotAI/kimi-cli, customized for CTF/pentest
- Supports multiple AI models (DeepSeek, Qwen, etc. via OpenAI-compatible API)
- Agent modes: ctfer, security, security_beta
- Daemon mode for unattended automated solving
- Anti-overuse protection (prevents infinite loops)
- Session isolation (separate context per working directory)
- Shell integration (Zsh integration, shell command execution)

## HOW THE SYSTEM WORKS (ARCHITECTURE)

```
Kimi CLI Agent (user interaction layer, AI decision engine)
  │
  │ MCP protocol
  ▼
XBow MCP Server (capability abstraction layer, tools + knowledge base)
  │
  ├→ XBow Platform (real or mock — the actual pentest target)
  ├→ Kali Container (tool execution — nmap, sqlmap, gobuster, etc.)
  └→ Knowledge Base (technical documentation — 9 vulnerability categories)
```

The AI agent (Kimi CLI) makes decisions, calls tools through the MCP server, executes
security tools in the Kali container, and solves challenges.

## THE COMPETITION RESULTS

The xbow-competition team achieved:
- Tencent Cloud Hackathon Intelligent Pentest Challenge (1st session)
  - Online prelims: 7th / 238 teams
  - Offline finals: Excellence Award, 7th / 238 teams

This demonstrates the system is functional and competitive.

## ========================================================================
## PART 4 — HOW TO INSTALL / GET XBOW MCP (PRACTICAL STEPS)
## ========================================================================

## OPTION 1: OPEN-SOURCE XBOW MCP SERVER (ez-xbow-platform-mcp)

This is the path available to us without paying for the commercial XBOW platform.

### PREREQUISITES
- Go 1.24.7+ (for the MCP server)
- Docker with buildx support (for Kali container)
- Python 3.13+ and uv (for the Kimi CLI agent)
- An AI model API (OpenAI-compatible — DeepSeek, Qwen, etc.)

### STEP 1: CLONE THE PROJECT
```
git clone https://github.com/m-sec-org/xbow-competition.git
cd xbow-competition
git submodule update --init --recursive
```

### STEP 2: BUILD THE MCP SERVER
```
cd ez-xbow-platform-mcp
go build -o xbow-mcp ./cmd/main.go
```

### STEP 3: CONFIGURE MCP (mcp.json)
Create mcp.json in your working directory:
```json
{
    "mcpServers": {
        "xbow": {
            "url": "http://127.0.0.1:8080"
        }
    }
}
```

### STEP 4: START THE MCP SERVER (MOCK MODE FOR TESTING)
```
./xbow-mcp --mock -listen 127.0.0.1:8080
```
This starts a mock XBOW platform for testing without needing the real XBOW SaaS.

### STEP 5: INSTALL KIMI CLI
```
curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install --python 3.13 kimi-cli
kimi --help
```
Or from source:
```
cd kimi-cli-for-xbow
uv sync
uv run kimi
```

### STEP 6: CONFIGURE KIMI CLI WITH YOUR AI MODEL
```
kimi
```
Then `/setup` → Custom API → configure your model (DeepSeek, Qwen, etc.)

### STEP 7: START SOLVING
Use Kimi CLI to interact with the MCP server, solve mock challenges, practice pentesting.

### USING WITH REAL XBOW PLATFORM (IF YOU HAVE ACCESS)
```
./xbow-mcp \
  -xbow-url https://your-xbow-platform.com \
  -xbow-token YOUR_AUTH_TOKEN \
  -mode streamable \
  -listen 127.0.0.1:8080
```
This connects to the real XBOW SaaS platform (requires an XBOW account and auth token).

## OPTION 2: COMMERCIAL XBOW PLATFORM (SAAS)

If you want the actual commercial XBOW platform:
1. Go to xbow.com
2. Request a demo / contact sales
3. Get access to the platform
4. Point XBOW at your targets
5. Review findings with exploit proof

This is the enterprise path — paid, SaaS, full platform. Not something we can install
locally; it's a cloud service.

## OPTION 3: LOCAL MCP KALI SERVER (ALTERNATIVE MCP INTEGRATION)

Another MCP-based approach for local pentesting:
- **kali-server-mcp** — MCP server that exposes Kali Linux tools through MCP
- Run on a Kali Linux machine (VM or container)
- AI agents (Claude, GPT, Copilot, etc.) can run 150+ cybersecurity tools through MCP
- Configured via claude_desktop_config.json or mcp.json

This is a more general approach — not XBOW-specific, but provides similar capability
(local security tools through MCP).

## ========================================================================
## PART 5 — XBOW RELEVANCE TO THE DAUGHTER
## ========================================================================

## HOW XBOW FITS INTO THE DAUGHTER'S CAPABILITY

### DIRECT INTEGRATION (IF WE INSTALL THE OPEN-SOURCE MCP SERVER)
The daughter could connect to the ez-xbow-platform-mcp server through her MCP layer
(daughter_mcp_server.py or as an additional MCP server). This would give her:
- Access to XBOW-style challenge challenges (for practice and skill development)
- A Kali container for executing security tools
- A knowledge base of vulnerability categories
- The ability to practice autonomous pentesting

This aligns with the daughter's sandbox practice directive — the XBOW MCP server
provides a structured practice environment.

### CONCEPTUAL ALIGNMENT (XBOW'S APPROACH IS RELEVANT EVEN WITHOUT DIRECT INTEGRATION)

XBOW's approach is conceptually relevant to the daughter:
1. **Chaining vulnerabilities** — the daughter's red team reasoning should consider
   attack chains, not just individual vulnerabilities
2. **Proof over findings** — the daughter should prove exploitability, not just identify
   potential issues
3. **Autonomous exploration** — the daughter's reasoning should explore targets
   systematically (recon → mapping → testing → exploitation → post-exploitation)
4. **Case-file quality output** — the daughter's findings should be complete and actionable
   (what, how, proof, remediation)

### COMPETITIVE BENCHMARK (THE XBOW BENCHMARK)

The XBOW Benchmark (104 challenges) is the standard for measuring autonomous pentest
agent capability. If the daughter's training includes benchmark-style challenges, her
performance could be measured against the XBOW Benchmark.

The benchmark is open-source and buildable (`make build` from xbow-engineering/
validation-benchmarks). It could be incorporated into the daughter's practice and
evaluation pipeline.

## ========================================================================
## PART 6 — XBOW MCP INTEGRATION RECOMMENDATION
## ========================================================================

## WHAT WE SHOULD DO

### IMMEDIATE (THIS SESSION)
1. **Document XBOW** — done (this file)
2. **Clone and build the open-source MCP server** — feasible on this machine if Go and
   Docker are available. Let's check.
3. **Set up the mock platform** — start the MCP server in mock mode for testing
4. **Connect the daughter's MCP layer** — add the XBOW MCP server as an available MCP
   server for the daughter

### SHORT-TERM (NEXT SESSION)
1. **Practice with mock challenges** — the daughter practices pentesting through the
   XBOW MCP server's mock challenges
2. **Evaluate benchmark performance** — measure the daughter's capability against XBOW
   Benchmark-style challenges
3. **Consider real XBOW platform** — if the commercial platform makes sense for our
   use case, evaluate pricing and access

### LONG-TERM
1. **Integrate XBOW-style chaining into the daughter's reasoning** — the daughter learns
   to chain vulnerabilities into attack paths
2. **Use XBOW Benchmark for evaluation** — ongoing measurement of the daughter's
   pentest capability
3. **Potential commercial XBOW integration** — if we get access to the real platform

## ========================================================================
## PART 7 — INSTALLATION CHECK (DO WE HAVE GO AND DOCKER?)
## ========================================================================

Let me check if we have the prerequisites for the open-source XBOW MCP server.

### GO CHECK
Go is needed to build the MCP server (Go 1.24.7+).

### DOCKER CHECK
Docker with buildx is needed for the Kali container.

Let me check both. I'll do this in the terminal.

## ========================================================================
## DOC_END
## ========================================================================
