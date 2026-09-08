# Cloned Red Team MCP Repos — Exact Clone Commands

All repos live under `~/mcp-redteam/` (C:\Users\mobil\mcp-redteam on Windows). Clone with `gh repo clone <owner>/<repo>` from any directory.

## Tier 1 — Already cloned (10)

| # | Owner | Repo | Stars | Clone command |
|---|-------|------|-------|---------------|
| 1 | andrasfe | vulnicheck | 11 | `gh repo clone andrasfe/vulnicheck` |
| 2 | Cyreslab-AI | exploitdb-mcp-server | 29 | `gh repo clone Cyreslab-AI/exploitdb-mcp-server` |
| 3 | PhialsBasement | nmap-mcp-server | 49 | `gh repo clone PhialsBasement/nmap-mcp-server` |
| 4 | aryanrangapur | Vulnerability-Scanner-MCP-Server | 0 | `gh repo clone aryanrangapur/Vulnerability-Scanner-MCP-Server` |
| 5 | secmate-ai | CyberSecurity-MCPs | 16 | `gh repo clone secmate-ai/CyberSecurity-MCPs` |
| 6 | Heisenbergg4 | mcploit | 2 | `gh repo clone Heisenbergg4/mcploit` |
| 7 | SoelMgd | MCP_Red_Team_Agent | 1 | `gh repo clone SoelMgd/MCP_Red_Team_Agent` |
| 8 | Sicks3c | hackerone-mcp-server | 41 | `gh repo clone Sicks3c/hackerone-mcp-server` |
| 9 | MorDavid | awesome-cyber-security-mcp | 99 | `gh repo clone MorDavid/awesome-cyber-security-mcp` |
| 10 | (same as #7) | MCP_Red_Team_Agent | 1 | already cloned |

## Tier 2 — Already cloned (7)

| # | Owner | Repo | Stars | Clone command |
|---|-------|------|-------|---------------|
| 11 | appsecco | vulnerable-mcp-servers-lab | 277 | `gh repo clone appsecco/vulnerable-mcp-servers-lab` |
| 12 | bhavsec | autopentest-ai | 223 | `gh repo clone bhavsec/autopentest-ai` |
| 13 | DMontgomery40 | pentest-mcp | 143 | `gh repo clone DMontgomery40/pentest-mcp` |
| 14 | RamKansal | pentestMCP | 93 | `gh repo clone RamKansal/pentestMCP` |
| 15 | halilkirazkaya | pentester-mcp | 52 | `gh repo clone halilkirazkaya/pentester-mcp` |
| 16 | 0x7556 | kali_mcp | 64 | `gh repo clone 0x7556/kali_mcp` |
| 17 | mukul975 | Anthropic-Cybersecurity-Skills | 31,926 | `gh repo clone mukul975/Anthropic-Cybersecurity-Skills` |

## Tier 3 — Clone on demand (found in search, useful but not critical right now)

| Owner | Repo | Stars | Why |
|-------|------|-------|-----|
| appsecco | pentesting-mcp-servers-checklist | 40 | Methodology: pentesting MCP servers checklist |
| IntegSec | MCP-client | 6 | Interactive CLI for pentesting MCP servers (JSON-RPC 2.0, Burp/SOCKS5, Bearer/Basic/mTLS) |
| Vasanthadithya-mundrathi | Pentest-MCP | 8 | 150+ tools, Kali + HexStrike integration (collided with pentestMCP on clone — use `gh repo clone Vasanthadithya-mundrathi/Pentest-MCP` after removing the collision) |
| declawedai | community-rules | 4 | AI security detection rules: prompt injection, MCP, agent skills |

## Repo remotes

All cloned repos have `origin` pointing to GitHub. To update:
```
cd ~/mcp-redteam/<repo>
git pull origin main
```

## Notes

- `pentest-mcp` (DMontgomery40, 143★) and `pentestMCP` (RamKansal, 93★) are DIFFERENT repos. The names collide on case-insensitive Windows — clone them into separate parent dirs if re-cloning.
- `Pentest-MCP` (Vasanthadithya-mundrathi, 8★) collided with `pentestMCP` during batch clone — remove the collision dir first: `rm -rf ~/mcp-redteam/Pentest-MCP && gh repo clone Vasanthadithya-mundrathi/Pentest-MCP`.
