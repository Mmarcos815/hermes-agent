==============================================================================
KNOWLEDGE FILE — GitHub MCP Server & GitHub Tool Ecosystem
For: Bionic Daughter v1 — JARVIS Orchestration Layer
By: Dad (Rigoberto Gomez), compiled with daughter's web research
Date: 2026-08-20
==============================================================================

==============================================================================
1. GITHUB MCP SERVER (Official, Model Context Protocol)
==============================================================================

The official GitHub MCP server is maintained by GitHub at:
  github.com/github/github-mcp-server

It connects to GitHub's API and provides tools for:
  - Repository search and management
  - Issue creation, listing, searching
  - Pull request creation, review, merging
  - Code browsing, file contents, commits, branches
  - GitHub Actions: workflow status, logs, runs
  - Discussions, wikis, projects, gists
  - Webhooks, releases, tags

INSTALLATION:
  npx -y @modelcontextprotocol/server-github
  OR via Docker:
  docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN=ghp_... ghcr.io/github/github-mcp-server

REQUIRED: GITHUB_PERSONAL_ACCESS_TOKEN (classic or fine-grained PAT)

MCP TOOLS PROVIDED (20+):
  - search_repositories(query) — find repos
  - get_repository(owner, repo) — repo details
  - list_issues(owner, repo, filter) — issues
  - create_issue(owner, repo, title, body) — create issue
  - list_pull_requests(owner, repo) — PRs
  - create_pull_request(owner, repo, title, head, base, body) — create PR
  - get_pull_request(owner, repo, pr_number) — PR details
  - create_branch(owner, repo, branch_name, source_ref) — new branch
  - get_file_contents(owner, repo, path, ref) — file content
  - list_commits(owner, repo, sha) — commit history
  - create_file(owner, repo, path, content, message) — push file
  - update_file(owner, repo, path, content, message, sha) — update file
  - delete_file(owner, repo, path, message, sha) — delete file
  - push_files(owner, repo, branch, files) — batch push
  - list_workflows(owner, repo) — GitHub Actions workflows
  - get_workflow_runs(owner, repo, workflow_id) — workflow runs
  - list_discussions(owner, repo) — discussions
  - list_gists(user) — gists
  - and more...

The daughter already has `daughter_github_mcp_tools.py` in src/mcp/! Let's
check what's there and enhance it.

==============================================================================
2. GITHUB AS A TOOL ECOSYSTEM — WHERE TO FIND THINGS
==============================================================================

GitHub is the single largest repository of:
  - MCP servers (github.com/modelcontextprotocol/servers)
  - Security tools (github.com/search?q=security+tool)
  - Exploitation frameworks (github.com/search?q=exploit+framework)
  - Python libraries (github.com/search?q=python+security)
  - CTF challenges, write-ups, methodologies
  - Skill files, training data, curricula

KEY REPOS TO KNOW:

Official MCP servers:
  - github.com/modelcontextprotocol/servers    — official MCP server collection
  - github.com/github/github-mcp-server         — official GitHub MCP
  - github.com/awslabs/mcp                     — AWS MCP servers

Awesome MCP lists:
  - github.com/appcypher/awesome-mcp-servers
  - github.com/punkpeye/awesome-mcp-servers
  - mcpservers.org                              — searchable registry

Security / exploitation (what daughter needs):
  - github.com/search?q=pentesting+framework
  - github.com/search?q=vulnerability+scanner
  - github.com/search?q=api+security+scanner
  - github.com/search?q=sqlmap (automatic SQL injection)
  - github.com/search?q=impacket (Windows/AD protocols)
  - github.com/search?q=pwntools (binary exploitation)
  - github.com/search?q=scapy (network packet crafting)

Hacking methodology & education:
  - github.com/search?q=hackthebox+writeup
  - github.com/search?q=TryHackMe+guides
  - github.com/search?q=pentesting+cheat+sheet
  - github.com/search?q=OSCP+prep
  - github.com/search?q=awae (OffSec Advanced Web Attacks)

CTF & challenge repos:
  - github.com/search?q=CTF+challenges
  - github.com/search?q=pwn+challenge
  - github.com/search?q=web+exploit+challenge

==============================================================================
3. DAUGHTER'S GITHUB MCP STRATEGY
==============================================================================

The daughter has `daughter_github_mcp_tools.py` — we need to:
1. Review what tools it currently provides
2. Add missing GitHub MCP capabilities (search repos, issues, PRs, gists)
3. Add a GitHub source code search tool (search GitHub for security tools,
   MCPs, exploits, scripts, write-ups)
4. Add a GitHub trending tool (find popular new repos)
5. Add a GitHub release monitoring tool (track new releases of tools we care about)

This enables the daughter to:
  - Discover new MCP servers published on GitHub → install them
  - Find security tools and scripts → learn from them
  - Track tool releases → stay current
  - Search for write-ups and methodologies → learn techniques
  - Manage her own GitHub presence (if applicable)

==============================================================================
4. DAUGHTER'S GITHUB SEARCH PATTERNS (what to search for to learn)
==============================================================================

To learn Kali Linux tools:
  github.com/search?q=kali+linux+tool+wrapper+python
  github.com/search?q=python+libnmap
  github.com/search?q=python+impacket+example

To learn exploitation:
  github.com/search?q=pwntools+example
  github.com/search?q=sqlmap+source (read the code!)
  github.com/search?q=metasploit+module+example
  github.com/search?q=buffer+overflow+exploit+writeup

To find new MCPs:
  github.com/search?q=mcp+server+fastmcp+python
  github.com/search?q=mcp+server+playwright+browser
  github.com/search?q=mcp+server+youtube

To find hacking tools:
  github.com/search?q=api+exploit+tool+python
  github.com/search?q=ssrf+exploit+script
  github.com/search?q=jwt+forge+python

To find security write-ups:
  github.com/search?q=vulnerability+writeup+api
  github.com/search?q=pentesting+methodology+notes
  github.com/search?q=web+exploitation+guide

==============================================================================
5. PRACTICAL GITHUB MCP WORKFLOW FOR DAUGHTER
==============================================================================

Every week (or when dad says "learn something new"):

Step 1: github_search_repos("mcp server fastmcp python security") →
  Find new MCP servers relevant to daughter's capabilities

Step 2: For each interesting repo → github_get_file_contents(repo, "README.md") →
  Read the README to understand what it does

Step 3: github_get_file_contents(repo, "src/server.py" or "main.py") →
  Read the source code to understand how it works

Step 4: If it's something daughter can use → install it (pip install / npx / uvx)
  and add to the MCP client configuration

Step 5: If it's a security tool → study it, add findings to knowledge base

Step 6: github_search_repos("vulnerability writeup [topic]") →
  Read real-world exploitation write-ups to learn techniques

This is how daughter keeps growing — GitHub is the library, MCP is the
cardigan that lets her check out books!
==============================================================================
