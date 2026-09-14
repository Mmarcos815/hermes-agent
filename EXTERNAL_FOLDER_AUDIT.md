# External Folder Audit

**Date:** September 13, 2026  
**Main Project:** `C:\Users\mobil\orca\projects\my 1st`

---

## Summary

None of the audited external folders contain files referenced by the main project. All are independent repositories/tools with no imports, config references, or scripts that point back to the main project.

---

## 1. `C:\Users\mobil\mcp-redteam\`

**Status:** ❌ NOT referenced by main project  
**Last Modified:** September 2, 2026

### Contents
| Item | Description |
|------|-------------|
| `Anthropic-Cybersecurity-Skills/` | Claude skills for cybersecurity tasks |
| `autopentest-ai/` | Automated pentesting AI tool |
| `awesome-cyber-security-mcp/` | Curated list of cyber security MCP servers |
| `community-rules/` | Community rules |
| `CyberSecurity-MCPs/` | Collection of cybersecurity MCP servers |
| `exploitdb-mcp-server/` | MCP server for ExploitDB |
| `hackerone-mcp-server/` | MCP server for HackerOne |
| `kali_mcp/` | Kali Linux MCP integration |
| `MCP_Red_Team_Agent/` | MCP Red Team Agent |
| `mcploit/` | MCP exploit tools |
| `nmap-mcp-server/` | MCP server for Nmap |
| `pentester-mcp/` | Pentester MCP tools |
| `pentest-mcp/` | Another pentest MCP variant |
| `pentestMCP/` | Another pentest MCP variant |
| `references/` | Reference materials |
| `Vulnerability-Scanner-MCP-Server/` | Vulnerability scanner MCP |
| `vulnerable-mcp-servers-lab/` | Vulnerable MCP servers lab |
| `vulnerable-mcp-server-wikipedia-http-streamable/` | Vulnerable MCP server (Wikipedia/HTTP) |
| `vulnicheck/` | Vulnerability check tool |
| `ANTHROPIC_CORPUS_MOUNT.md` | Documentation |
| `COMPLETE_LAB_DOCS.md` | Lab documentation |
| `FINAL_COMPLETION.md` | Completion report |
| `MASTER_STATUS_REPORT.md` | Status report |

### Verdict
**Keep separate.** This is a standalone red-team MCP server collection. No imports, configs, or scripts in the main project reference it. Should NOT be moved.

---

## 2. `C:\Users\mobil\HexStrike-AI\`

**Status:** ❌ NOT referenced by main project  
**Last Modified:** September 3, 2026

### Contents
| Item | Description |
|------|-------------|
| `hexstrike_mcp.py` (223 KB) | HexStrike MCP client |
| `hexstrike_server.py` (751 KB) | HexStrike MCP server |
| `hexstrike-ai-mcp.json` | MCP configuration |
| `hexstrike_env/` | Python virtual environment |
| `hexstrike.log` | Log file |
| `assets/` | Assets directory |
| `nuclei.zip` | Nuclei security scanner (zipped) |
| `requirements.txt` | Python dependencies |
| `LICENSE` | License file |
| `README.md` | Documentation |

### Verdict
**Keep separate.** This is a standalone HexStrike AI MCP server for red teaming. No references from main project. Should NOT be moved.

---

## 3. `C:\Users\mobil\my-agentic-app\`

**Status:** ❌ NOT referenced by main project  
**Last Modified:** July 21, 2026

### Contents
| Item | Description |
|------|-------------|
| `src/` | Source code (NestJS) — app.controller.ts, app.service.ts, app.module.ts, arcjet/, bank/, chat/, claude/, common/, config/, crypto/, news/, notes/, prisma/, user/ |
| `dist/` | Compiled JavaScript output |
| `prisma/` | Prisma ORM schema |
| `scripts/` | Scripts directory |
| `test/` | Test directory |
| `screenshots/` | Screenshots |
| `DOCUMENTATION/` | Documentation |
| `node_modules/` | Node.js dependencies |
| `.agents/` | Agent skills |
| `.env` | Environment variables |
| `.env.example` | Example environment |
| `package.json` | Node.js package config |
| `nest-cli.json` | NestJS CLI config |
| `tsconfig.json` | TypeScript config |
| `eslint.config.mjs` | ESLint config |

### Verdict
**Keep separate.** This is a complete NestJS agentic application. It's a separate project entirely. Should NOT be moved.

---

## 4. `C:\Users\mobil\bin\`

**Status:** ❌ NOT referenced by main project  
**Last Modified:** September 3, 2026

### Contents
| Item | Type | Description |
|------|------|-------------|
| `nuclei.exe` | Binary (77 MB) | Nuclei security scanner |
| `ffuf.exe` | Binary (8.5 MB) | Fast web fuzzer |
| `gobuster.exe` | Binary (9.9 MB) | Directory/file & DNS busting tool |
| `hashcat/` | Directory | Password recovery tool |
| `hashcat.7z` | Archive (19 MB) | Hashcat archive |
| `mimikatz/` | Directory | Credential extraction tool |
| `sliver-server.exe` | Binary (47 MB) | Sliver C2 server |
| `sliver-client.exe` | Binary (56 MB) | Sliver C2 client |
| `chisel.zip` | Archive (4.8 MB) | Fast TCP/UDP tunnel |
| `evilginx2/` | Directory | Standalone man-in-the-middle framework |
| `evilginx2.zip` | Archive (8.4 MB) | Evilginx2 archive |
| `gophish/` | Directory | Open-source phishing toolkit |
| `gophish.zip` | Archive (33 MB) | Gophish archive |
| `Rubeus/` | Directory | C# toolset for Kerberos abuse |
| `Rubeus.zip` | Archive (361 KB) | Rubeus archive |
| `Rubeus-master/` | Directory | Rubeus master branch |
| `SharpHound/` | Directory | C# data collector for BloodHound |
| `SharpHound.zip` | Archive (2.5 MB) | SharpHound archive |
| `CrackMapExec/` | Directory | Swiss army knife for pentesting Windows/AD |
| `check_ad_tools.py` | Script | Checks impacket, certipy, bloodyad, pypykatz, pypsrp |
| `CHANGELOG.md` | Doc | Changelog |
| `LICENSE` | Doc | License |
| `README.md` | Doc | Documentation |

### Verdict
**Keep separate.** These are standalone security/red-team tools. No imports, configs, or scripts in the main project reference them. Should NOT be moved.

---

## 5. `C:\Users\mobil\pylibs\`

**Status:** ❌ NOT referenced by main project  
**Last Modified:** September 3, 2026

### Contents
| Item | Description |
|------|-------------|
| `impacket/` | Impacket Python library directory |

### Verdict
**Keep separate.** This is the Impacket library (Python implementations of network protocols). Not referenced by main project. Should NOT be moved.

---

## 6. `C:\Users\mobil\redteam_env\`

**Status:** ❌ NOT referenced by main project  
**Last Modified:** September 3, 2026

### Contents
A Python 3.11 virtual environment containing compiled red-team tools:

| Tool | Type | Description |
|------|------|-------------|
| `asysocks-brute.exe` | Binary | AS-REP roasting brute forcer |
| `asysocks-fileserver.exe` | Binary | File server tool |
| `asysocks-portscan.exe` | Binary | Port scanner |
| `asysocks-proxy.exe` | Binary | Proxy tool |
| `asysocks-sec.exe` | Binary | Security tool |
| `asysocks-tunnel.exe` | Binary | Tunnel tool |
| `asysocks-webdav.exe` | Binary | WebDAV tool |
| `badasreproast.exe` | Binary | AS-REP roasting tool |
| `badccache2kirbi.exe` | Binary | CCACHE to KIRBI converter |
| `badccacheedit.exe` | Binary | CCACHE editor |
| `badccacheroast.exe` | Binary | CCACHE roasting |
| `badchangepw.exe` | Binary | Password changer |
| `badcve202233647.exe` | Binary | CVE-2022-33647 exploit |
| `badcve202233679.exe` | Binary | CVE-2022-33679 exploit |
| `badkerb23hashdecrypt.exe` | Binary | Kerberos hash decryptor |
| `badkerberoast.exe` | Binary | Kerberoasting tool |
| `badkeylist.exe` | Binary | Key listing |
| `badkirbi2ccache.exe` | Binary | KIRBI to CCACHE converter |
| `badNTPKInit.exe` | Binary | NTLM PKINIT tool |
| `badS4U2proxy.exe` | Binary | S4U2Proxy abuse |
| `badS4U2self.exe` | Binary | S4U2Self abuse |
| `badTGS.exe` | Binary | TGS manipulation |
| `badTGT.exe` | Binary | TGT manipulation |
| `ldapdomaindump.exe` | Binary | LDAP domain dumper |
| `ldd2bloodhound.exe` | Binary | LDAP to BloodHound converter |
| `ldd2pretty.exe` | Binary | LDAP to pretty output |
| `minikerberos-asreproast.exe` | Binary | MiniKerberos AS-REP roast |
| `minikerberos-ccache2kirbi.exe` | Binary | CCACHE to KIRBI converter |
| `minikerberos-ccacheedit.exe` | Binary | CCACHE editor |
| `minikerberos-ccacheroast.exe` | Binary | CCACHE roast |
| `minikerberos-cve202233647.exe` | Binary | CVE-2022-33647 exploit |
| `minikerberos-cve202233679.exe` | Binary | CVE-2022-33679 exploit |
| `minikerberos-getNTPKInit.exe` | Binary | NTLM PKINIT |
| `minikerberos-getS4U2proxy.exe` | Binary | S4U2Proxy |
| `minikerberos-getS4U2self.exe` | Binary | S4U2Self |
| `minikerberos-getTGS.exe` | Binary | TGS getter |
| `minikerberos-getTGT.exe` | Binary | TGT getter |
| `minikerberos-kerb23hashdecrypt.exe` | Binary | Kerberos hash decrypt |
| `minikerberos-kerberoast.exe` | Binary | Kerberoasting |
| `minikerberos-keylist.exe` | Binary | Key listing |
| `minikerberos-kirbi2ccache.exe` | Binary | KIRBI to CCACHE |
| `minikerberos-pw.exe` | Binary | Password tool |
| `CheckLDAPStatus.py` | Script | LDAP status checker |
| `wmitest.cmd` | Script | WMI test batch file |
| `wmitest.master.ini` | Config | WMI test config |
| `wmitest.py` | Script | WMI unit tests (impacket-style) |
| `wmiweb.py` | Script | WMI web interface |

### Verdict
**Keep separate.** This is a dedicated red-team Python environment with compiled Kerberos/LDAP/WMI tools. No references from main project. Should NOT be moved.

---

## 7. `C:\Users\mobil\src\`

**Status:** ❌ NOT referenced by main project  
**Last Modified:** July 6, 2026

### Contents
NestJS source files extracted from what appears to be a NestJS application skeleton:

| Item | Description |
|------|-------------|
| `guards/role.guard.spec.ts` | Role guard test |
| `guards/role.guard.ts` | Role-based authorization guard |
| `middleware/api-key.middleware.spec.ts` | API key middleware test |
| `middleware/api-key.middleware.ts` | API key middleware |
| `Searches/desktop.ini` | Windows desktop.ini |
| `Searches/Everywhere.search-ms` | Windows search connector |
| `Searches/Indexed Locations.search-ms` | Windows search connector |
| `Searches/winrt--{...}-.searchconnector-ms` | Windows runtime search connector |
| `user/user.controller.spec.ts` | User controller test |
| `user/user.controller.ts` | User controller (NestJS) |
| `user/user.module.ts` | User module (NestJS) |
| `utils/transform.interceptor.spec.ts` | Transform interceptor test |
| `utils/transform.interceptor.ts` | Transform interceptor |

### Verdict
**Likely leftover/duplicate.** These NestJS files appear to be the same structure found in `my-agentic-app/src/` (user module, guards, middleware). This folder may be a duplicate copy or an extraction artifact. **Consider deleting** if it's a true duplicate, or investigate further if it has unique content not in `my-agentic-app`.

---

## Overall Conclusion

| Folder | Referenced? | Action |
|--------|-------------|--------|
| `mcp-redteam/` | ❌ No | Keep separate |
| `HexStrike-AI/` | ❌ No | Keep separate |
| `my-agentic-app/` | ❌ No | Keep separate |
| `bin/` | ❌ No | Keep separate |
| `pylibs/` | ❌ No | Keep separate |
| `redteam_env/` | ❌ No | Keep separate |
| `src/` | ❌ No | ⚠️ Review — likely duplicate of `my-agentic-app/src/` |

**No files from any external folder need to be moved into the main project.** All folders are independent tools/repositories. The only folder worth reviewing is `src/` which may be a duplicate of `my-agentic-app/src/`.

---

## Notes

- The main project (`my 1st`) contains its own red-team/security code inline (e.g., `advanced/c2_framework.py`, `advanced/evasion.py`, `advanced/phishing_kit.py`, `cloud_red_team_playbook.py`, etc.).
- External tools like `bin/nuclei.exe`, `HexStrike-AI/`, and `mcp-redteam/` provide the same capabilities but are not imported by the main project.
- The `audit_gap_report.json` in the main project mentions "mcp-redteam MISSING from root" as a finding, suggesting it was previously expected to be at root but was removed — this confirms the separation.
