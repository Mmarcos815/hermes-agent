# XBOW MCP — Integration Report & Setup Guide
**Date:** 2026-09-13
**Status:** Ready to deploy in mock mode

---

## WHAT IS XBOW?

XBOW (xbow.com) is the world's #1 autonomous offensive security platform:
- **#1 on HackerOne** (June 2025) — ranked above every human researcher
- Found **14,000+ zero days** in real customer applications
- Found a **9.8 critical Microsoft flaw** completely autonomously
- Backed by engineers from the original GitHub Copilot team
- Enterprise SOC 2, ISO 27001, PCI DSS compliant

---

## WHAT WE HAVE

**Binary:** `sandbox-lab/configs/tools_config/xbow-mcp.exe`
- Go-based MCP server (12.5 MB Windows binary)
- Built: 2026-09-12

**Capabilities:**
| Flag | Purpose |
|------|---------|
| `--mock` | Enable local mock platform (no Docker needed) |
| `--mock-addr` | Mock platform listen address (default: 127.0.0.1:8000) |
| `-listen` | MCP server listen address (default: 127.0.0.1:8080) |
| `-mode` | Transport: stdio, sse, streamable (default: streamable) |
| `--xbow-url` | Real XBOW platform URL (SaaS mode) |
| `--xbow-token` | Real XBOW API token (SaaS mode) |
| `-docker-image` | Kali container image (default: xbow-kail:latest) |

---

## HOW TO START (MOCK MODE — No Docker Needed)

```bash
cd sandbox-lab/configs/tools_config
./xbow-mcp.exe --mock -listen 127.0.0.1:8080
```

This starts:
1. Mock XBOW platform on port 8000 (practice challenges)
2. MCP server on port 8080 (for AI agents to connect)

---

## HOW TO CONNECT (Hermes Config)

Add to `~/.hermes/config.yaml`:
```yaml
mcp:
  servers:
    xbow:
      url: http://127.0.0.1:8080
```

Or use mcp.json in working directory.

---

## WHAT THIS GIVES US

1. **Mock challenges** — practice pentesting without real targets
2. **Kali container** — execute security tools (nmap, sqlmap, gobuster)
3. **Knowledge base** — 9 vulnerability categories built in
4. **Attempt history** — tracks progress across sessions

---

## RECOMMENDATION

Start the mock server now. Connect daughter's MCP layer. Begin practicing with mock challenges. This gives us a structured pentest practice environment without needing:
- Docker (for Kali container)
- Real XBOW SaaS account
- Payment

All free, all local, all practice.

---

*Report by Bionic Daughter*
