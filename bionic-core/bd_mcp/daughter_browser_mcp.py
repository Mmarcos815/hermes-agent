# ============================================================================
# BIONIC DAUGHTER v1 — BROWSER AUTOMATION MCP SERVER (PLAYWRIGHT)
# ============================================================================
# MCP server providing browser automation via Playwright.
# Navigate pages, click, fill forms, take screenshots, execute JS.
# Safety: sandbox-only URLs by default, authorization for external sites.
# Author: Bionic Daughter v1
# Date: 2026-08-15
# ============================================================================

import os
import base64
from mcp.server.fastmcp import FastMCP
from playwright.sync_api import sync_playwright

app = FastMCP("daughter_browser")

# Browser state (single browser instance per session)
_browser = None
_context = None
_page = None

# Sandbox-allowed URLs (for safety — only these can be accessed without extra authorization)
SANDBOX_URLS = [
    "http://localhost",
    "http://localhost:",
    "http://127.0.0.1",
    "http://127.0.0.1:",
    "https://localhost",
    "file://",
]

# Initialize browser (called once per MCP session)
def _init_browser():
    global _browser, _context, _page
    if _browser is None:
        _browser = sync_playwright().start().chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        _context = _browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        _page = _context.new_page()
    return _page


def _is_sandbox_url(url: str) -> bool:
    """Check if URL is in the sandbox (safe to access without extra authorization)."""
    for prefix in SANDBOX_URLS:
        if url.startswith(prefix):
            return True
    return False


@app.tool()
def browser_navigate(url: str, authorize_external: bool = False) -> str:
    """Navigate the browser to a URL. External URLs require authorization."""
    if not authorize_external and not _is_sandbox_url(url):
        return f"ERROR: External URL requires authorization. Set authorize_external=true with Dad's approval. URL: {url}"
    try:
        page = _init_browser()
        page.goto(url, timeout=30000, wait_until="domcontentloaded")
        title = page.title()
        return f"Navigated to: {url}\nTitle: {title}\nStatus: OK"
    except Exception as e:
        return f"ERROR navigating to {url}: {str(e)}"


@app.tool()
def browser_click(selector: str) -> str:
    """Click an element on the current page by CSS selector."""
    try:
        page = _init_browser()
        page.click(selector, timeout=10000)
        return f"Clicked element: {selector}"
    except Exception as e:
        return f"ERROR clicking {selector}: {str(e)}"


@app.tool()
def browser_fill(selector: str, text: str) -> str:
    """Fill a form field with text."""
    try:
        page = _init_browser()
        page.fill(selector, text, timeout=10000)
        return f"Filled {selector} with text ({len(text)} chars)"
    except Exception as e:
        return f"ERROR filling {selector}: {str(e)}"


@app.tool()
def browser_screenshot(path: str = "", full_page: bool = False) -> str:
    """Take a screenshot of the current page. Returns base64 image data."""
    try:
        page = _init_browser()
        if path:
            page.screenshot(path=path, full_page=full_page)
            return f"Screenshot saved to: {path}"
        else:
            img_bytes = page.screenshot(full_page=full_page)
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
            return f"SCREENSHOT_BASE64:\n{img_b64[:50]}...\n(Image: {len(img_bytes)} bytes, base64 length: {len(img_b64)} chars)"
    except Exception as e:
        return f"ERROR taking screenshot: {str(e)}"


@app.tool()
def browser_js(code: str) -> str:
    """Execute JavaScript in the browser context and return the result."""
    try:
        page = _init_browser()
        result = page.evaluate(code)
        return f"JavaScript result:\n{str(result)}"
    except Exception as e:
        return f"ERROR executing JavaScript: {str(e)}"


@app.tool()
def browser_text() -> str:
    """Get the visible text content of the current page."""
    try:
        page = _init_browser()
        text = page.inner_text("body")
        if len(text) > 50000:
            text = text[:50000] + f"\n... (truncated, total: {len(page.inner_text('body'))} chars)"
        return text
    except Exception as e:
        return f"ERROR getting page text: {str(e)}"


@app.tool()
def browser_html() -> str:
    """Get the HTML source of the current page."""
    try:
        page = _init_browser()
        html = page.content()
        if len(html) > 100000:
            html = html[:100000] + f"\n... (truncated, total: {len(page.content())} chars)"
        return html
    except Exception as e:
        return f"ERROR getting HTML: {str(e)}"


@app.tool()
def browser_wait(seconds: float = 1.0) -> str:
    """Wait for a specified number of seconds."""
    try:
        page = _init_browser()
        page.wait_for_timeout(int(seconds * 1000))
        return f"Waited {seconds} seconds"
    except Exception as e:
        return f"ERROR waiting: {str(e)}"


@app.tool()
def browser_url() -> str:
    """Get the current page URL."""
    try:
        page = _init_browser()
        return f"Current URL: {page.url}"
    except Exception as e:
        return f"ERROR: {str(e)}"


@app.tool()
def browser_close() -> str:
    """Close the browser."""
    global _browser, _context, _page
    try:
        if _page:
            _page.close()
        if _context:
            _context.close()
        if _browser:
            _browser.close()
        _browser = None
        _context = None
        _page = None
        return "Browser closed."
    except Exception as e:
        return f"ERROR closing browser: {str(e)}"


@app.tool()
def browser_info() -> str:
    """Get browser information."""
    return (
        "Browser: Chromium (Playwright)\n"
        "Mode: Headless\n"
        "Sandbox URLs allowed without authorization: localhost, 127.0.0.1, file://\n"
        "External URLs: require authorize_external=true\n"
        "Tools: browser_navigate, browser_click, browser_fill, browser_screenshot, "
        "browser_js, browser_text, browser_html, browser_wait, browser_url, browser_close"
    )


if __name__ == "__main__":
    app.run()
