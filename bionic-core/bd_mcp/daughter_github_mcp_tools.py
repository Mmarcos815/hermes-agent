#!/usr/bin/env python3
# ============================================================================
# BIONIC DAUGHTER v1 — GITHUB CLI MCP TOOLS (ADDLES TO DAUGHTER'S MCP SERVER)
# ============================================================================
# Additional MCP tools for the daughter that wrap the GitHub CLI (gh).
# These can be added to daughter_mcp_server.py or run as a separate MCP server.
#
# Prerequisites:
#   - gh CLI installed and authenticated (gh auth login)
#   - gh v2.97.0 or later
#
# Usage:
#   # Add to daughter_mcp_server.py by importing these tools
#   from daughter_github_mcp_tools import github_create_repo, github_create_issue, ...
#
#   # Or register as a separate MCP server:
#   # claude mcp add github --command "python daughter_github_mcp_tools.py"
# ============================================================================

import os
import sys
import json
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DaughterGitHubMCP")

GH_CLI = "gh"  # Uses system gh CLI

# ============================================================================
# GITHUB CLI WRAPPER
# ============================================================================

def _gh(args, input_text=None):
    """
    Run a gh CLI command and return parsed JSON output.
    """
    cmd = [GH_CLI] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            input=input_text,
            timeout=60,
        )
        if result.returncode == 0:
            # Try to parse as JSON
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"output": result.stdout.strip()}
        else:
            return {"error": result.stderr.strip() or result.stdout.strip()}
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out after 60 seconds"}
    except FileNotFoundError:
        return {"error": "gh CLI not found — install from https://cli.github.com/"}

# ============================================================================
# REPO TOOLS
# ============================================================================

def github_create_repo(name, description="", private=True, org=None):
    """
    Create a new GitHub repository.

    Args:
        name: str — repository name
        description: str — repository description
        private: bool — whether repo is private
        org: str (optional) — organization to create repo in

    Returns:
        dict with repo info or error
    """
    args = ["repo", "create", name, "--public" if not private else "--private", "--json", "name,url,private,description,fullName"]
    if org:
        args.extend(["--org", org])

    result = _gh(args)
    if "error" in result:
        return {"status": "error", "error": result["error"]}
    return {"status": "created", "repo": result}

def github_get_repo(repo):
    """
    Get repository information.

    Args:
        repo: str — owner/repo or just repo name (if in current org)

    Returns:
        dict with repo info or error
    """
    args = ["repo", "view", repo, "--json", "name,url,private,description,fullName,stargazersCount,forksCount,language,defaultBranchRef"]
    result = _gh(args)
    if "error" in result:
        return {"status": "error", "error": result["error"]}
    return {"status": "found", "repo": result}

def github_list_repos(org=None, visibility="all", limit=30):
    """
    List repositories.

    Args:
        org: str (optional) — organization to list repos from
        visibility: str — all, public, private, internal
        limit: int — max repos to return

    Returns:
        dict with list of repos or error
    """
    args = ["repo", "list", org or ".", "--limit", str(limit), "--json", "name,url,private,description,stargazersCount,language"]
    if visibility != "all":
        args.extend(["--visibility", visibility])
    result = _gh(args)
    if "error" in result:
        return {"status": "error", "error": result["error"]}
    repos = result if isinstance(result, list) else []
    return {"status": "listed", "count": len(repos), "repos": repos}

def github_delete_repo(repo):
    """
    Delete a repository. USE WITH CAUTION.

    Args:
        repo: str — owner/repo

    Returns:
        dict with status or error
    """
    args = ["repo", "delete", repo, "--confirm", "true", "--json", "name,deletedAt"]
    result = _gh(args)
    if "error" in result:
        return {"status": "error", "error": result["error"]}
    return {"status": "deleted", "repo": result}

def github_update_repo(repo, name=None, description=None, private=None, homepage=None):
    """
    Update repository settings.

    Args:
        repo: str — owner/repo
        name: str (optional) — new name
        description: str (optional) — new description
        private: bool (optional) — new privacy setting
        homepage: str (optional) — new homepage URL

    Returns:
        dict with updated repo info or error
    """
    args = ["repo", "edit", repo, "--json", "name,url,private,description,fullName"]
    if name:
        args.extend(["--name", name])
    if description is not None:
        args.extend(["--description", description])
    if private is not None:
        args.extend(["--private" if private else "--public"])
    if homepage:
        args.extend(["--homepage", homepage])

    result = _gh(args)
    if "error" in result:
        return {"status": "error", "error": result["error"]}
    return {"status": "updated", "repo": result}

# ============================================================================
# ISSUE TOOLS
# ============================================================================

def github_create_issue(repo, title, body="", labels=None, assignees=None):
    """
    Create a new issue.

    Args:
        repo: str — owner/repo
        title: str — issue title
        body: str — issue body/description
        labels: list (optional) — list of label names
        assignees: list (optional) — list of usernames to assign

    Returns:
        dict with issue info or error
    """
    args = ["issue", "create", "--repo", repo, "--title", title, "--json", "number,title,url,state,createdAt"]
    if body:
        args.extend(["--body", body])
    if labels:
        args.extend(["--label", ",".join(labels)])
    if assignees:
        args.extend(["--assignee", ",".join(assignees)])

    result = _gh(args)
    if "error" in result:
        return {"status": "error", "error": result["error"]}
    return {"status": "created", "issue": result}

def github_get_issue(repo, number):
    """
    Get issue details.

    Args:
        repo: str — owner/repo
        number: int — issue number

    Returns:
        dict with issue info or error
    """
    args = ["issue", "view", str(number), "--repo", repo, "--json", "number,title,url,state,body,createdAt,labels,assignees"]
    result = _gh(args)
    if "error" in result:
        return {"status": "error", "error": result["error"]}
    return {"status": "found", "issue": result}

def github_list_issues(repo, state="open", labels=None, limit=30):
    """
    List issues for a repository.

    Args:
        repo: str — owner/repo
        state: str — open, closed, all
        labels: list (optional) — filter by labels
        limit: int — max issues to return

    Returns:
        dict with list of issues or error
    """
    args = ["issue", "list", "--repo", repo, "--state", state, "--limit", str(limit), "--json", "number,title,url,state,createdAt,labels"]
    if labels:
        args.extend(["--label", ",".join(labels)])
    result = _gh(args)
    if "error" in result:
        return {"status": "error", "error": result["error"]}
    issues = result if isinstance(result, list) else []
    return {"status": "listed", "count": len(issues), "issues": issues}

def github_update_issue(repo, number, title=None, body=None, state=None, labels=None):
    """
    Update an issue.

    Args:
        repo: str — owner/repo
        number: int — issue number
        title: str (optional) — new title
        body: str (optional) — new body
        state: str (optional) — open or closed
        labels: list (optional) — new labels

    Returns:
        dict with updated issue info or error
    """
    args = ["issue", "edit", str(number), "--repo", repo, "--json", "number,title,url,state"]
    if title:
        args.extend(["--title", title])
    if body is not None:
        args.extend(["--body", body])
    if state:
        args.extend(["--state", state])
    if labels:
        args.extend(["--add-label", ",".join(labels)])

    result = _gh(args)
    if "error" in result:
        return {"status": "error", "error": result["error"]}
    return {"status": "updated", "issue": result}

def github_close_issue(repo, number):
    """
    Close an issue.

    Args:
        repo: str — owner/repo
        number: int — issue number

    Returns:
        dict with status or error
    """
    args = ["issue", "close", str(number), "--repo", repo, "--json", "number,title,url,state"]
    result = _gh(args)
    if "error" in result:
        return {"status": "error", "error": result["error"]}
    return {"status": "closed", "issue": result}

def github_add_issue_comment(repo, number, body):
    """
    Add a comment to an issue.

    Args:
        repo: str — owner/repo
        number: int — issue number
        body: str — comment body

    Returns:
        dict with comment info or error
    """
    args = ["issue", "comment", str(number), "--repo", repo, "--body", body, "--json", "id,body,createdAt"]
    result = _gh(args)
    if "error" in result:
        return {"status": "error", "error": result["error"]}
    return {"status": "commented", "comment": result}

# ============================================================================
# PULL REQUEST TOOLS
# ============================================================================

def github_create_pull_request(repo, title, body="", head="main", base="main", draft=False):
    """
    Create a pull request.

    Args:
        repo: str — owner/repo
        title: str — PR title
        body: str — PR body/description
        head: str — source branch
        base: str — target branch
        draft: bool — create as draft

    Returns:
        dict with PR info or error
    """
    args = ["pr", "create", "--repo", repo, "--title", title, "--base", base, "--head", head, "--json", "number,title,url,state,isDraft,createdAt"]
    if body:
        args.extend(["--body", body])
    if draft:
        args.append("--draft")

    result = _gh(args)
    if "error" in result:
        return {"status": "error", "error": result["error"]}
    return {"status": "created", "pull_request": result}

def github_get_pull_request(repo, number):
    """
    Get pull request details.

    Args:
        repo: str — owner/repo
        number: int — PR number

    Returns:
        dict with PR info or error
    """
    args = ["pr", "view", str(number), "--repo", repo, "--json", "number,title,url,state,isDraft,additions,deletions,createdAt,reviews,commits"]
    result = _gh(args)
    if "error" in result:
        return {"status": "error", "error": result["error"]}
    return {"status": "found", "pull_request": result}

def github_list_pull_requests(repo, state="open", base="main", limit=30):
    """
    List pull requests.

    Args:
        repo: str — owner/repo
        state: str — open, closed, merged, all
        base: str (optional) — filter by base branch
        limit: int — max PRs to return

    Returns:
        dict with list of PRs or error
    """
    args = ["pr", "list", "--repo", repo, "--state", state, "--limit", str(limit), "--json", "number,title,url,state,isDraft,author,createdAt"]
    if base:
        args.extend(["--base", base])
    result = _gh(args)
    if "error" in result:
        return {"status": "error", "error": result["error"]}
    prs = result if isinstance(result, list) else []
    return {"status": "listed", "count": len(prs), "pull_requests": prs}

def github_update_pull_request(repo, number, title=None, body=None):
    """
    Update a pull request.

    Args:
        repo: str — owner/repo
        number: int — PR number
        title: str (optional) — new title
        body: str (optional) — new body

    Returns:
        dict with updated PR info or error
    """
    args = ["pr", "edit", str(number), "--repo", repo, "--json", "number,title,url,state"]
    if title:
        args.extend(["--title", title])
    if body is not None:
        args.extend(["--body", body])

    result = _gh(args)
    if "error" in result:
        return {"status": "error", "error": result["error"]}
    return {"status": "updated", "pull_request": result}

def github_merge_pull_request(repo, number, method="merge"):
    """
    Merge a pull request.

    Args:
        repo: str — owner/repo
        number: int — PR number
        method: str — merge, squash, rebase

    Returns:
        dict with merge result or error
    """
    args = ["pr", "merge", str(number), "--repo", repo, "--method", method, "--json", "name,url,mergedAt,mergeCommit"]
    result = _gh(args)
    if "error" in result:
        return {"status": "error", "error": result["error"]}
    return {"status": "merged", "pull_request": result}

def github_add_pr_comment(repo, number, body):
    """
    Add a comment to a pull request.

    Args:
        repo: str — owner/repo
        number: int — PR number
        body: str — comment body

    Returns:
        dict with comment info or error
    """
    args = ["pr", "comment", str(number), "--repo", repo, "--body", body, "--json", "id,body,createdAt"]
    result = _gh(args)
    if "error" in result:
        return {"status": "error", "error": result["error"]}
    return {"status": "commented", "comment": result}

def github_review_pull_request(repo, number, event="comment", body="", approval=False):
    """
    Review a pull request.

    Args:
        repo: str — owner/repo
        number: int — PR number
        event: str — comment, approve, request-changes, submit
        body: str — review body
        approval: bool — whether to approve (for event=approve)

    Returns:
        dict with review result or error
    """
    args = ["pr", "view", str(number), "--repo", repo, "--json", "number,title,url,state"]
    # Note: gh pr review requires the pr to be checked out or use --repo
    # Simplified: use pr comment for review-style feedback
    args = ["pr", "comment", str(number), "--repo", repo, "--body", body, "--json", "id,body,createdAt"]
    if event == "approve":
        args = ["pr", "review", str(number), "--repo", repo, "--approve", "--json", "id,state,createdAt"]

    result = _gh(args)
    if "error" in result:
        return {"status": "error", "error": result["error"]}
    return {"status": "reviewed", "review": result}

# ============================================================================
# WORKFLOW / ACTIONS TOOLS
# ============================================================================

def github_list_workflows(repo):
    """
    List repository workflows.

    Args:
        repo: str — owner/repo

    Returns:
        dict with list of workflows or error
    """
    args = ["workflow", "list", "--repo", repo, "--json", "name,id,state,updatedAt"]
    result = _gh(args)
    if "error" in result:
        return {"status": "error", "error": result["error"]}
    workflows = result if isinstance(result, list) else []
    return {"status": "listed", "count": len(workflows), "workflows": workflows}

def github_trigger_workflow(repo, workflow_id="ci.yml"):
    """
    Trigger a workflow run.

    Args:
        repo: str — owner/repo
        workflow_id: str — workflow file name or ID

    Returns:
        dict with run info or error
    """
    args = ["workflow", "run", workflow_id, "--repo", repo, "--json", "runId,status,name,headSha,createdAt"]
    result = _gh(args)
    if "error" in result:
        return {"status": "error", "error": result["error"]}
    return {"status": "triggered", "run": result}

def github_get_workflow(repo, workflow_id):
    """
    Get workflow details.

    Args:
        repo: str — owner/repo
        workflow_id: str — workflow file name or ID

    Returns:
        dict with workflow info or error
    """
    args = ["workflow", "view", workflow_id, "--repo", repo, "--json", "name,id,state,updatedAt,paths"]
    result = _gh(args)
    if "error" in result:
        return {"status": "error", "error": result["error"]}
    return {"status": "found", "workflow": result}

def github_list_workflow_runs(repo, workflow_id=None, status=None, limit=10):
    """
    List workflow runs.

    Args:
        repo: str — owner/repo
        workflow_id: str (optional) — filter by workflow
        status: str (optional) — pending, queued, in_progress, success, failure, cancelled, skipped, requested, waiting
        limit: int — max runs to return

    Returns:
        dict with list of runs or error
    """
    args = ["run", "list", "--repo", repo, "--limit", str(limit), "--json", "runId,status,name,headSha,createdAt,conclusion"]
    if workflow_id:
        args.extend(["--workflow", workflow_id])
    if status:
        args.extend(["--status", status])
    result = _gh(args)
    if "error" in result:
        return {"status": "error", "error": result["error"]}
    runs = result if isinstance(result, list) else []
    return {"status": "listed", "count": len(runs), "runs": runs}

# ============================================================================
# COMMIT TOOLS
# ============================================================================

def github_list_commits(repo, branch=None, author=None, path=None, since=None, until=None, limit=20):
    """
    List commits.

    Args:
        repo: str — owner/repo
        branch: str (optional) — filter by branch
        author: str (optional) — filter by author
        path: str (optional) — filter by file path
        since: str (optional) — ISO date
        until: str (optional) — ISO date
        limit: int — max commits to return

    Returns:
        dict with list of commits or error
    """
    args = ["log", "--repo", repo, "--limit", str(limit), "--json", "hash,message,author,name,date,committer"]
    if branch:
        args.extend(["--branch", branch])
    if author:
        args.extend(["--author", author])
    if path:
        args.extend(["--", path])
    if since:
        args.extend(["--since", since])
    if until:
        args.extend(["--until", until])
    result = _gh(args)
    if "error" in result:
        return {"status": "error", "error": result["error"]}
    commits = result if isinstance(result, list) else []
    return {"status": "listed", "count": len(commits), "commits": commits}

def github_get_commit(repo, commit_hash):
    """
    Get commit details.

    Args:
        repo: str — owner/repo
        commit_hash: str — commit SHA or reference

    Returns:
        dict with commit info or error
    """
    args = ["view", commit_hash, "--repo", repo, "--json", "hash,message,author,date,stat,additions,deletions,changes"]
    result = _gh(args)
    if "error" in result:
        return {"status": "error", "error": result["error"]}
    return {"status": "found", "commit": result}

# ============================================================================
# DISCOVERY — LIST ALL AVAILABLE GITHUB TOOLS
# ============================================================================

GITHUB_TOOLS = [
    {"name": "github_create_repo", "description": "Create a new GitHub repository"},
    {"name": "github_get_repo", "description": "Get repository information"},
    {"name": "github_list_repos", "description": "List repositories (user or org)"},
    {"name": "github_delete_repo", "description": "Delete a repository (USE WITH CAUTION)"},
    {"name": "github_update_repo", "description": "Update repository settings"},
    {"name": "github_create_issue", "description": "Create a new issue"},
    {"name": "github_get_issue", "description": "Get issue details"},
    {"name": "github_list_issues", "description": "List issues (filterable by state, labels)"},
    {"name": "github_update_issue", "description": "Update an issue (title, body, state, labels)"},
    {"name": "github_close_issue", "description": "Close an issue"},
    {"name": "github_add_issue_comment", "description": "Add a comment to an issue"},
    {"name": "github_create_pull_request", "description": "Create a pull request"},
    {"name": "github_get_pull_request", "description": "Get pull request details"},
    {"name": "github_list_pull_requests", "description": "List pull requests (filterable)"},
    {"name": "github_update_pull_request", "description": "Update a pull request"},
    {"name": "github_merge_pull_request", "description": "Merge a pull request"},
    {"name": "github_add_pr_comment", "description": "Add a comment to a pull request"},
    {"name": "github_review_pull_request", "description": "Review a pull request (approve/comment)"},
    {"name": "github_list_workflows", "description": "List repository workflows"},
    {"name": "github_trigger_workflow", "description": "Trigger a workflow run"},
    {"name": "github_get_workflow", "description": "Get workflow details"},
    {"name": "github_list_workflow_runs", "description": "List workflow runs (filterable)"},
    {"name": "github_list_commits", "description": "List commits (filterable by branch, author, path)"},
    {"name": "github_get_commit", "description": "Get commit details"},
]

def github_tools_list():
    """
    List all available GitHub MCP tools.
    """
    return {"tools": GITHUB_TOOLS, "count": len(GITHUB_TOOLS)}




# MCP Server — exposes GitHub CLI tools via FastMCP
# ============================================================================
from mcp.server.fastmcp import FastMCP

app = FastMCP("GitHubCLITools")

# Save original function references before wrappers shadow them
_orig_github_create_repo = github_create_repo
_orig_github_get_repo = github_get_repo
_orig_github_list_repos = github_list_repos
_orig_github_delete_repo = github_delete_repo
_orig_github_update_repo = github_update_repo
_orig_github_create_issue = github_create_issue
_orig_github_get_issue = github_get_issue
_orig_github_list_issues = github_list_issues
_orig_github_update_issue = github_update_issue
_orig_github_close_issue = github_close_issue
_orig_github_add_issue_comment = github_add_issue_comment
_orig_github_create_pull_request = github_create_pull_request
_orig_github_get_pull_request = github_get_pull_request
_orig_github_list_pull_requests = github_list_pull_requests
_orig_github_update_pull_request = github_update_pull_request
_orig_github_merge_pull_request = github_merge_pull_request
_orig_github_add_pr_comment = github_add_pr_comment
_orig_github_review_pull_request = github_review_pull_request
_orig_github_list_workflows = github_list_workflows
_orig_github_trigger_workflow = github_trigger_workflow
_orig_github_get_workflow = github_get_workflow
_orig_github_list_workflow_runs = github_list_workflow_runs
_orig_github_list_commits = github_list_commits
_orig_github_get_commit = github_get_commit
_orig_github_tools_list = github_tools_list

@app.tool()
def github_create_repo(name, description="", private=True, org=None):
    return _orig_github_create_repo(name, description="", private=True, org=None)

@app.tool()
def github_get_repo(repo):
    return _orig_github_get_repo(repo)

@app.tool()
def github_list_repos(org=None, visibility="all", limit=30):
    return _orig_github_list_repos(org=None, visibility="all", limit=30)

@app.tool()
def github_delete_repo(repo):
    return _orig_github_delete_repo(repo)

@app.tool()
def github_update_repo(repo, name=None, description=None, private=None, homepage=None):
    return _orig_github_update_repo(repo, name=None, description=None, private=None, homepage=None)

@app.tool()
def github_create_issue(repo, title, body="", labels=None, assignees=None):
    return _orig_github_create_issue(repo, title, body="", labels=None, assignees=None)

@app.tool()
def github_get_issue(repo, number):
    return _orig_github_get_issue(repo, number)

@app.tool()
def github_list_issues(repo, state="open", labels=None, limit=30):
    return _orig_github_list_issues(repo, state="open", labels=None, limit=30)

@app.tool()
def github_update_issue(repo, number, title=None, body=None, state=None, labels=None):
    return _orig_github_update_issue(repo, number, title=None, body=None, state=None, labels=None)

@app.tool()
def github_close_issue(repo, number):
    return _orig_github_close_issue(repo, number)

@app.tool()
def github_add_issue_comment(repo, number, body):
    return _orig_github_add_issue_comment(repo, number, body)

@app.tool()
def github_create_pull_request(repo, title, body="", head="main", base="main", draft=False):
    return _orig_github_create_pull_request(repo, title, body="", head="main", base="main", draft=False)

@app.tool()
def github_get_pull_request(repo, number):
    return _orig_github_get_pull_request(repo, number)

@app.tool()
def github_list_pull_requests(repo, state="open", base="main", limit=30):
    return _orig_github_list_pull_requests(repo, state="open", base="main", limit=30)

@app.tool()
def github_update_pull_request(repo, number, title=None, body=None):
    return _orig_github_update_pull_request(repo, number, title=None, body=None)

@app.tool()
def github_merge_pull_request(repo, number, method="merge"):
    return _orig_github_merge_pull_request(repo, number, method="merge")

@app.tool()
def github_add_pr_comment(repo, number, body):
    return _orig_github_add_pr_comment(repo, number, body)

@app.tool()
def github_review_pull_request(repo, number, event="comment", body="", approval=False):
    return _orig_github_review_pull_request(repo, number, event="comment", body="", approval=False)

@app.tool()
def github_list_workflows(repo):
    return _orig_github_list_workflows(repo)

@app.tool()
def github_trigger_workflow(repo, workflow_id="ci.yml"):
    return _orig_github_trigger_workflow(repo, workflow_id="ci.yml")

@app.tool()
def github_get_workflow(repo, workflow_id):
    return _orig_github_get_workflow(repo, workflow_id)

@app.tool()
def github_list_workflow_runs(repo, workflow_id=None, status=None, limit=10):
    return _orig_github_list_workflow_runs(repo, workflow_id=None, status=None, limit=10)

@app.tool()
def github_list_commits(repo, branch=None, author=None, path=None, since=None, until=None, limit=20):
    return _orig_github_list_commits(repo, branch=None, author=None, path=None, since=None, until=None, limit=20)

@app.tool()
def github_get_commit(repo, commit_hash):
    return _orig_github_get_commit(repo, commit_hash)

@app.tool()
def github_tools_list():
    return _orig_github_tools_list()

# MCP server entry point
# ============================================================================
if __name__ == "__main__":
    app.run(transport="stdio")
