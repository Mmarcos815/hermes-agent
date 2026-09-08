# ============================================================================
# GitHub CLI (gh) MCP Server — Setup Guide for the Bionic Daughter
# ============================================================================
#
# The GitHub CLI (gh) can be used as an MCP server, giving the daughter
# access to GitHub tools (repos, issues, PRs, actions, commits, etc.)
# through the MCP protocol — using her existing gh authentication.
#
# Two approaches:
#   A) gh extension: shuymn/gh-mcp (bundles official github-mcp-server)
#   B) Official docker: github-mcp-server in Docker with PAT
#
# Recommended: Approach A (gh extension) — simpler, uses existing gh auth.
# ============================================================================

## PREREQUISITES

gh CLI: INSTALLED (v2.97.0, at /c/Program Files/GitHub CLI/gh)
gh auth: NOT authenticated yet (run gh auth login)
Claude Desktop config: NOT configured yet (no claude_desktop_config.json)

## STEP 1 — AUTHENTICATE GH CLI

```bash
# Open a terminal and run:
gh auth login

# This opens a browser for OAuth login.
# Choose:
#   - GitHub.com (not GitHub Enterprise)
#   - HTTPS protocol
#   - Login with browser (OAuth)

# After login, verify:
gh auth status
```

Expected output:
```
github.com
  ✓ Logged in to GitHub.com account <your-username> as Rigoberto Gomez (keyring)
  ✓ Git operations against GitHub.com are authenticated
  ✓ API operations against GitHub.com are authenticated
```

## STEP 2 — INSTALL GH MCP EXTENSION (APPROACH A)

```bash
# Install the gh-mcp extension
gh extension install shuymn/gh-mcp

# Verify installation
gh mcp --help
```

This extension bundles the official github-mcp-server binary and launches it
with the existing gh credentials — no separate token needed.

## STEP 3 — CONFIGURE MCP SERVER IN HOST APPLICATION

### For Claude Desktop (Windows):

Create or edit: %APPDATA%/Claude/claude_desktop_config.json

```json
{
  "mcpServers": {
    "github": {
      "command": "gh",
      "args": ["mcp"],
      "env": {
        "GITHUB_TOOLSETS": "repos,issues,pull_requests,actions,commits",
        "GITHUB_READ_ONLY": "0"
      }
    }
  }
}
```

GITHUB_TOOLSETS options (comma-separated):
- repos — repository CRUD, listing, starred
- issues — create, read, update, list, comment, label, assign
- pull_requests — create, read, update, merge, list, comment, review
- actions — list workflows, trigger workflows, get runs
- commits — list, get commit details
- projects — GitHub Projects v2
- orgs — organization info, repos, members
- packages — package versions

GITHUB_READ_ONLY:
- "1" = read-only access (safer for testing)
- "0" = read-write access (full capability)

### For Claude Code:

```bash
# Add GitHub MCP server
claude mcp add-json github '{"command":"gh","args":["mcp"]}'

# Or with env vars for tool selection
claude mcp add-json github '{"command":"gh","args":["mcp"],"env":{"GITHUB_TOOLSETS":"repos,issues,pull_requests","GITHUB_READ_ONLY":"0"}}'

# List configured MCP servers
claude mcp list

# Remove if needed
claude mcp remove github
```

### For Cursor:

1. Open Cursor Settings > Features > MCP
2. Click "Add MCP Server"
3. Configure:
   - Name: github
   - Command: gh
   - Arguments: ["mcp"]
   - Environment variables: GITHUB_TOOLSETS=repos,issues,pull_requests, GITHUB_READ_ONLY=0

## STEP 4 — TEST THE GITHUB MCP SERVER

Once configured, the daughter (through her MCP client in the host application)
can call GitHub tools. Test with:

```python
# In the daughter's MCP client context:
tools = github_tools_list()
print(f"Available GitHub tools: {tools['count']}")

# Create a test repo
result = github_create_repo(
    name="bionic-daughter-test",
    description="Test repo for daughter's GitHub MCP integration",
    private=True
)
print(f"Repo created: {result}")

# List repos
result = github_list_repos()
print(f"Repos: {result['count']}")
for repo in result['repos']:
    print(f"  - {repo['name']}: {repo['url']}")

# Create an issue
result = github_create_issue(
    repo="rigoberto/gbc-mlops-platform",
    title="Test issue from daughter's GitHub MCP",
    body="This issue was created by the Bionic Daughter via GitHub MCP tools.",
    labels=["test", "mcp"]
)
print(f"Issue created: {result}")
```

## STEP 5 — ALTERNATIVE: OFFICIAL GITHUB MCP SERVER (APPROACH B)

If the gh extension doesn't work, use the official github-mcp-server in Docker:

```bash
# 1. Create a GitHub Personal Access Token (PAT)
# Go to github.com/settings/tokens
# Click "Generate new token (classic)"
# Select scopes:
#   - repo (full control of private repos)
#   - read:org (read org info)
#   - workflow (update CI workflows — optional)
# Copy the token

# 2. Configure Claude Desktop with Docker
{
  "mcpServers": {
    "github": {
      "command": "docker",
      "args": ["run", "-i", "--rm",
              "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
              "ghcr.io/github/github-mcp-server"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your-pat-here"
      }
    }
  }
}
```

## GITHUB MCP TOOLS AVAILABLE TO THE DAUGHTER

REPOS (5 tools):
- github_create_repo(name, description, private, org) — create a new repo
- github_get_repo(repo) — get repo info (name, url, private, description, stars, forks, language)
- github_list_repos(org, visibility, limit) — list repos (user or org)
- github_delete_repo(repo) — delete a repo (USE WITH CAUTION)
- github_update_repo(repo, name, description, private, homepage) — update repo settings

ISSUES (6 tools):
- github_create_issue(repo, title, body, labels, assignees) — create a new issue
- github_get_issue(repo, number) — get issue details
- github_list_issues(repo, state, labels, limit) — list issues (filterable)
- github_update_issue(repo, number, title, body, state, labels) — update an issue
- github_close_issue(repo, number) — close an issue
- github_add_issue_comment(repo, number, body) — add a comment to an issue

PULL REQUESTS (7 tools):
- github_create_pull_request(repo, title, body, head, base, draft) — create a PR
- github_get_pull_request(repo, number) — get PR details
- github_list_pull_requests(repo, state, base, limit) — list PRs
- github_update_pull_request(repo, number, title, body) — update a PR
- github_merge_pull_request(repo, number, method) — merge a PR
- github_add_pr_comment(repo, number, body) — add a comment to a PR
- github_review_pull_request(repo, number, event, body) — review a PR

WORKFLOWS / ACTIONS (4 tools):
- github_list_workflows(repo) — list repository workflows
- github_trigger_workflow(repo, workflow_id) — trigger a workflow run
- github_get_workflow(repo, workflow_id) — get workflow details
- github_list_workflow_runs(repo, workflow_id, status, limit) — list workflow runs

COMMITS (2 tools):
- github_list_commits(repo, branch, author, path, since, until, limit) — list commits
- github_get_commit(repo, commit_hash) — get commit details

PROJECTS (4 tools):
- github_list_projects(org) — list projects
- github_create_project(name, org) — create a project
- github_list_project_items(project_id) — list items in a project
- github_add_project_item(project_id, content) — add an item to a project

## HOW THE DAUGHTER USES THESE TOOLS

SCENARIO 1 — CREATE A REPO FOR A NEW PROJECT:
```
User: "Create a new repo for the red team game"

Daughter reasons:
- This needs GitHub tools — create_repo
- I'll create a private repo with a description

Daughter calls:
github_create_repo(
    name="red-team-game",
    description="AI-powered red team training game — learn security by playing",
    private=False  # public so others can see it
)

Result:
  status: "created"
  repo: {
    name: "red-team-game",
    url: "https://github.com/rigoberto/red-team-game",
    private: false,
    description: "AI-powered red team training game..."
  }

Daughter reports:
  "Created repository 'red-team-game' at https://github.com/rigoberto/red-team-game"
```

SCENARIO 2 — OPEN AN ISSUE FOR A BUG FOUND BY CODE AUDIT:
```
User: "I found a SQL injection in the login handler — create an issue"

Daughter reasons:
- This needs GitHub tools — create_issue
- I'll create an issue with the security label

Daughter calls:
github_create_issue(
    repo="rigoberto/red-team-game",
    title="[SECURITY] SQL injection in login handler",
    body="Found SQL injection vulnerability in the login handler:\n\n```python\nquery = f\"SELECT * FROM users WHERE username = '{user_input}'\"\n```\n\nThe user_input is directly interpolated into the SQL query. Fix: use parameterized queries.\n\nSeverity: HIGH\nComponent: login_handler.py",
    labels=["security", "bug", "high-priority"]
)

Result:
  status: "created"
  issue: {
    number: 42,
    title: "[SECURITY] SQL injection in login handler",
    url: "https://github.com/rigoberto/red-team-game/issues/42",
    state: "open",
    created_at: "2026-08-15T12:00:00Z"
  }

Daughter reports:
  "Created issue #42: '[SECURITY] SQL injection in login handler'
   https://github.com/rigoberto/red-team-game/issues/42"
```

SCENARIO 3 — CREATE A PR FOR A FIX:
```
User: "Fix the SQL injection and create a PR"

Daughter reasons:
- I need to fix the code and create a PR
- First, I'll create the fix file locally
- Then create a branch, commit, push, and create a PR

Daughter actions:
1. Create fix file (parameterized query):
   daughter writes fixed_login_handler.py with parameterized queries

2. Call GitHub tools:
   - (git commands via sandbox or terminal to commit and push)
   - github_create_pull_request(
       repo="rigoberto/red-team-game",
       title="Fix SQL injection in login handler",
       body="This PR fixes the SQL injection vulnerability by using parameterized queries.\n\nBefore: f\"SELECT * FROM users WHERE username = '{user_input}'\"\nAfter: cursor.execute(\"SELECT * FROM users WHERE username = ?\", (user_input,))\n\nFixes issue #42.",
       head="fix-sql-injection",
       base="main"
     )

Result:
  status: "created"
  pull_request: {
    number: 43,
    title: "Fix SQL injection in login handler",
    url: "https://github.com/rigoberto/red-team-game/pull/43",
    state: "open",
    isDraft: false
  }

Daughter reports:
  "Created PR #43: 'Fix SQL injection in login handler'
   https://github.com/rigoberto/red-team-game/pull/43"
```

SCENARIO 4 — REVIEW A PR:
```
User: "Review PR #43 for security issues"

Daughter reasons:
- I need to review this PR — get_pull_request + review_pull_request
- I'll check for security issues, code quality, and correctness

Daughter calls:
1. github_get_pull_request(repo="rigoberto/red-team-game", number=43)
   -> Gets PR details, diff, commits

2. Analyzes the PR content with her code audit skills:
   - Checks for SQL injection fixes (parameterized queries — good)
   - Checks for any new issues introduced
   - Verifies the fix is correct

3. github_review_pull_request(
     repo="rigoberto/red-team-game",
     number=43,
     event="comment",
     body="LGTM! The SQL injection fix looks correct — parameterized queries are properly used. No new issues introduced. Security review: PASS.\n\nOne suggestion: consider adding input validation on user_input as an additional layer of defense."
   )

Result:
  status: "reviewed"
  review: {
    id: 12345,
    body: "LGTM! ...",
    created_at: "2026-08-15T12:05:00Z"
  }

Daughter reports:
  "Reviewed PR #43: APPROVED with one suggestion (input validation)."
```

SCENARIO 5 — TRIGGER A CI BUILD:
```
User: "Run the tests on the PR"

Daughter reasons:
- I need to trigger the CI workflow
- I'll use github_trigger_workflow

Daughter calls:
github_trigger_workflow(
    repo="rigoberto/red-team-game",
    workflow_id="ci.yml"
)

Result:
  status: "triggered"
  run: {
    runId: 56789,
    status: "queued",
    name: "CI",
    headSha: "abc123..."
  }

Daughter reports:
  "Triggered CI workflow run #56789 — status: queued"
```

SCENARIO 6 — TRACK ISSUES:
```
User: "What are the open security issues?"

Daughter reasons:
- I need to list issues with the security label
- I'll use github_list_issues with label filter

Daughter calls:
github_list_issues(
    repo="rigoberto/red-team-game",
    state="open",
    labels=["security"]
)

Result:
  status: "listed"
  count: 3
  issues: [
    {number: 42, title: "[SECURITY] SQL injection in login handler", state: "open", created_at: "2026-08-15T12:00:00Z"},
    {number: 38, title: "[SECURITY] XSS in search results", state: "open", created_at: "2026-08-14T10:00:00Z"},
    {number: 31, title: "[SECURITY] Hardcoded API key", state: "open", created_at: "2026-08-13T08:00:00Z"}
  ]

Daughter reports:
  "Found 3 open security issues:
   - #42: SQL injection in login handler (created Aug 15)
   - #38: XSS in search results (created Aug 14)
   - #31: Hardcoded API key (created Aug 13)"
```

## INTEGRATING INTO THE DAUGHTER'S MCP SERVER

The daughter's `daughter_mcp_server.py` can be extended to include GitHub tools
directly (instead of relying on external MCP configuration). This makes the
daughter's MCP server a single point of access for all her tools.

To add GitHub tools to daughter_mcp_server.py:

```python
# In daughter_mcp_server.py, add:

from daughter_github_mcp_tools import (
    github_create_repo, github_get_repo, github_list_repos, github_delete_repo,
    github_update_repo,
    github_create_issue, github_get_issue, github_list_issues, github_update_issue,
    github_close_issue, github_add_issue_comment,
    github_create_pull_request, github_get_pull_request, github_list_pull_requests,
    github_update_pull_request, github_merge_pull_request, github_add_pr_comment,
    github_review_pull_request,
    github_list_workflows, github_trigger_workflow, github_get_workflow,
    github_list_workflow_runs,
    github_list_commits, github_get_commit,
    github_tools_list,
)

# Register as MCP tools:

@mcp.tool()
def github_create_repo(name: str, description: str = "", private: bool = True, org: str = None) -> dict:
    """Create a new GitHub repository. Returns repo info or error."""
    return github_create_repo(name, description, private, org)

@mcp.tool()
def github_create_issue(repo: str, title: str, body: str = "", labels: list = None, assignees: list = None) -> dict:
    """Create a new GitHub issue. Returns issue info or error."""
    return github_create_issue(repo, title, body, labels, assignees)

# ... register all 24 tools ...

# Update tool discovery:

@mcp.tool()
def daughter_tools_list() -> dict:
    return {
        "tools": [
            # ... existing tools ...
            {"name": "github_create_repo", "description": "Create a new GitHub repository"},
            {"name": "github_get_repo", "description": "Get repository information"},
            {"name": "github_list_repos", "description": "List repositories (user or org)"},
            {"name": "github_create_issue", "description": "Create a new GitHub issue"},
            {"name": "github_list_issues", "description": "List issues (filterable by state, labels)"},
            {"name": "github_create_pull_request", "description": "Create a pull request"},
            {"name": "github_list_pull_requests", "description": "List pull requests"},
            {"name": "github_trigger_workflow", "description": "Trigger a GitHub Actions workflow"},
            {"name": "github_list_commits", "description": "List commits (filterable by branch, author, path)"},
            # ... all 24 GitHub tools + existing 14 tools = 38 total
        ]
    }
```

This gives the daughter a single MCP server with 38 tools (14 existing + 24 GitHub).
No external MCP configuration needed — everything through one server.

## RECOMMENDATION

1. First: authenticate gh CLI (gh auth login)
2. Install gh-mcp extension (gh extension install shuymn/gh-mcp)
3. Configure in Claude Desktop (add github MCP server to claude_desktop_config.json)
4. Test with simple operations (list repos, create test repo)
5. Add GitHub tools to daughter_mcp_server.py for integrated access
6. Test full workflow: create repo → create issue → create PR → review PR

## DOC_END
