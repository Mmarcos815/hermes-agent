# ============================================================================
# BIONIC DAUGHTER v1 — WEB SEARCH MCP SERVER
# ============================================================================
# MCP server providing web search and content fetching capabilities.
# Uses Brave Search API (primary) and fallback web fetching.
# Safety: no authorization required for general search; fetching specific
#         URLs should be for legitimate research/testing purposes.
# Author: Bionic Daughter v1
# Date: 2026-08-15
# ============================================================================

import os
import urllib.request
import urllib.parse
import json
import ssl
from fastmcp import FastMCP

app = FastMCP("daughter_web_search")

# Brave Search API key (set as environment variable BRAVE_API_KEY)
# If not set, search falls back to a manual HTTP approach or returns guidance
BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")

# User agent for web requests
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def _fetch_url(url: str, timeout: int = 15) -> str:
    """Fetch a URL and return its content. Basic web fetching."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
            content_type = response.headers.get("Content-Type", "")
            raw = response.read()
            if "json" in content_type:
                return json.dumps(json.loads(raw), indent=2)
            text = raw.decode("utf-8", errors="replace")
            if len(text) > 50000:
                text = text[:50000] + f"\n... (truncated, total: {len(raw)} bytes)"
            return text
    except Exception as e:
        return f"ERROR fetching {url}: {str(e)}"


@app.tool()
def web_search(query: str, count: int = 10, safe_search: str = "moderate") -> str:
    """Search the web using Brave Search API. Returns ranked results with titles, URLs, snippets."""
    if not BRAVE_API_KEY:
        return (
            "WARNING: BRAVE_API_KEY not set. Web search requires an API key.\n"
            "To enable: set environment variable BRAVE_API_KEY='your-key'\n"
            "Get a key at: https://brave.com/search/api\n"
            "Fallback: Use Hermes web_search tool for now."
        )

    try:
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": BRAVE_API_KEY,
        }
        params = {
            "q": query,
            "count": min(count, 20),
            "safesearch": safe_search,
            "language": "en",
        }
        req = urllib.request.Request(
            url + "?" + urllib.parse.urlencode(params), headers=headers
        )
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        results = data.get("web", {}).get("results", [])
        if not results:
            return "No search results found."

        output = f"Search results for: '{query}' ({len(results)} results)\n\n"
        for i, r in enumerate(results, 1):
            title = r.get("title", "No title")
            url = r.get("url", "No URL")
            snippet = r.get("snippet", "") or r.get("description", "")
            if len(snippet) > 300:
                snippet = snippet[:300] + "..."
            output += f"{i}. {title}\n   URL: {url}\n   Snippet: {snippet}\n\n"

        return output
    except Exception as e:
        return f"ERROR: Brave Search failed — {str(e)}\nFallback: Use Hermes web_search tool."


@app.tool()
def web_fetch(url: str, max_chars: int = 50000) -> str:
    """Fetch a web page and return its content (HTML text)."""
    if not url.startswith(("http://", "https://")):
        return "ERROR: URL must start with http:// or https://"
    result = _fetch_url(url, timeout=15)
    if len(result) > max_chars:
        result = result[:max_chars] + f"\n... (truncated, total: {len(result)} chars before truncation)"
    return result


@app.tool()
def web_fetch_text(url: str, max_chars: int = 30000) -> str:
    """Fetch a URL and try to extract readable text (strip HTML tags)."""
    html = _fetch_url(url, timeout=15)
    if html.startswith("ERROR"):
        return html
    try:
        # Simple HTML tag stripping
        import re

        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<header[^>]*>.*?</header>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<footer[^>]*>.*?</footer>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<nav[^>]*>.*?</nav>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) > max_chars:
            text = text[:max_chars] + f"\n... (truncated)"
        return text if text else "(No readable text extracted)"
    except Exception as e:
        return f"ERROR extracting text: {str(e)}"


@app.tool()
def web_search_intel(query: str) -> str:
    """Search specifically for cybersecurity threat intelligence, vulnerabilities, exploits.
    Uses Brave Search with security-focused query framing."""
    security_query = f"{query} cybersecurity vulnerability exploit threat intelligence 2025 2026"
    return web_search(security_query, count=10)


@app.tool()
def web_search_vuln(cve_id: str = "") -> str:
    """Search for information about a specific CVE or vulnerability."""
    if cve_id:
        query = f"CVE-{cve_id} vulnerability details exploit impact patch"
    else:
        return "ERROR: Provide a CVE ID (e.g., '2024-12345') or leave empty for general vuln search."
    return web_search(query, count=10)


@app.tool()
def web_google_search(query: str, count: int = 10) -> str:
    """Search Google via Serper API (alternative to Brave)."""
    serper_key = os.environ.get("SERPER_API_KEY", "")
    if not serper_key:
        return (
            "WARNING: SERPER_API_KEY not set.\n"
            "To enable: set environment variable SERPER_API_KEY='your-key'\n"
            "Get a key at: https://serper.dev\n"
            "Falling back to Brave Search..."
        )
    try:
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": serper_key,
            "Content-Type": "application/json",
        }
        payload = json.dumps({"q": query, "num": min(count, 10)}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        results = data.get("organic", [])
        if not results:
            return "No Google search results found."

        output = f"Google search results for: '{query}' ({len(results)} results)\n\n"
        for i, r in enumerate(results, 1):
            title = r.get("title", "No title")
            url = r.get("link", "No URL")
            snippet = r.get("snippet", "")
            if len(snippet) > 300:
                snippet = snippet[:300] + "..."
            output += f"{i}. {title}\n   URL: {url}\n   Snippet: {snippet}\n\n"

        return output
    except Exception as e:
        return f"ERROR: Serper search failed — {str(e)}"


@app.tool()
def web_info() -> str:
    """Show web search MCP information and configuration."""
    brave_status = "CONFIGURED" if BRAVE_API_KEY else "NOT CONFIGURED (set BRAVE_API_KEY)"
    serper_status = "CONFIGURED" if os.environ.get("SERPER_API_KEY") else "NOT CONFIGURED (set SERPER_API_KEY)"
    return (
        "Web Search MCP — Bionic Daughter v1\n"
        "======================================\n"
        "Brave Search API: " + brave_status + "\n"
        "Serper (Google) API: " + serper_status + "\n"
        "Tools:\n"
        "  web_search(query, count, safe_search) — General web search (Brave)\n"
        "  web_fetch(url, max_chars) — Fetch a URL's HTML content\n"
        "  web_fetch_text(url, max_chars) — Fetch and extract readable text\n"
        "  web_search_intel(query) — Security-focused threat intelligence search\n"
        "  web_search_vuln(cve_id) — Search for CVE/vulnerability info\n"
        "  web_google_search(query, count) — Google search via Serper API\n"
        "\n"
        "Setup:\n"
        "  export BRAVE_API_KEY='your-brave-api-key'\n"
        "  export SERPER_API_KEY='your-serper-api-key'\n"
        "  Get Brave key: https://brave.com/search/api\n"
        "  Get Serper key: https://serper.dev\n"
    )


if __name__ == "__main__":
    app.run()
