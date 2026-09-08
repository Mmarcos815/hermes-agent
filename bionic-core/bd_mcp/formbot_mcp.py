#!/usr/bin/env python3
"""
BIONIC DAUGHTER — FormBot (Web Form Automation MCP Server)
Playwright-based form filling, file upload, multi-page flows,
iframe/shadow DOM handling, and CAPTCHA-aware interaction.

For authorized testing only — our own test forms + authorized targets.

Usage:
  FastMCP("formbot", version="1.0.0")
  Register in ~/.hermes/config.yaml under mcpServers.
"""

import re
import json
import base64
from pathlib import Path
from typing import Optional, List, Dict

from fastmcp import FastMCP

app = FastMCP("formbot", version="1.0.0")


@app.tool()
def form_fill(
    url: str,
    fields: Dict[str, str],
    submit_selector: Optional[str] = None,
    wait_for: Optional[str] = None,
) -> dict:
    """
    Fill a web form with given field values and submit.

    fields: {"input[name=username]": "john", "input[type=password]": "pass123"}
    submit_selector: CSS selector for submit button (default: first <input type=submit> or <button type=submit>)
    wait_for: CSS selector or text to wait for after submission

    Returns: success status, filled fields, any errors.
    """
    result = {
        "url": url,
        "fields_filled": list(fields.keys()),
        "submission_method": submit_selector or "auto (first submit button)",
        "wait_for": wait_for,
        "status": "simulated",
        "note": "This is the MCP tool definition. Full Playwright execution requires a browser context — see formbot_demo.py for working example.",
    }
    return result


@app.tool()
def form_fingerprint(
    url: str,
) -> dict:
    """
    Analyze a form page and return its fingerprint:
    - All input fields (name, type, id, placeholder)
    - All buttons (type, text, selector)
    - All textareas, selects
    - Hidden fields
    - CSRF token presence
    - CAPTCHA indicators
    - iframe/shadow DOM indicators
    - Form action URL
    """
    result = {
        "url": url,
        "status": "simulated",
        "note": "This is the MCP tool definition. See formbot_demo.py for a working Playwright fingerprinting example.",
    }
    return result


@app.tool()
def multi_page_flow(
    steps: List[dict],
) -> dict:
    """
    Execute a multi-page form flow.

    steps: [
      {"action": "navigate", "url": "https://..."},
      {"action": "fill", "selector": "input[name=email]", "value": "x@y.com"},
      {"action": "fill", "selector": "input[name=password]", "value": "pass"},
      {"action": "click", "selector": "button[type=submit]"},
      {"action": "wait_for", "selector": ".success-message"},
      {"action": "fill", "selector": "#step2_name", "value": "John"},
      {"action": "click", "selector": "#next"},
      ...
    ]

    Returns: flow status, steps executed, any failure point.
    """
    result = {
        "steps_provided": len(steps),
        "status": "simulated",
        "note": "This is the MCP tool definition. See formbot_demo.py for working multi-page flow example.",
    }
    return result


@app.tool()
def file_upload(
    url: str,
    file_selector: str,
    file_path: str,
    submit_selector: Optional[str] = None,
) -> dict:
    """
    Upload a file via a web form.

    file_selector: CSS selector for <input type=file>
    file_path: absolute path to file to upload
    submit_selector: optional submit button after upload

    Returns: upload status, file info, any errors.
    """
    result = {
        "url": url,
        "file_selector": file_selector,
        "file_path": file_path,
        "file_exists": Path(file_path).exists() if file_path else False,
        "file_size": Path(file_path).stat().st_size if file_path and Path(file_path).exists() else 0,
        "submission_method": submit_selector or "auto",
        "status": "simulated",
        "note": "This is the MCP tool definition. See formbot_demo.py for working file upload example.",
    }
    return result


@app.tool()
def captcha_aware_check(
    url: str,
) -> dict:
    """
    Check a page for CAPTCHA presence and report what's found.

    Detects:
    - reCAPTCHA (v2/v3) indicators
    - hCaptcha indicators
    - Cloudflare Turnstile
    - Custom CAPTCHA widgets
    - honeypot fields

    Returns: captcha type(s) detected, difficulty assessment, recommended approach.
    """
    result = {
        "url": url,
        "captcha_types": [],
        "honeypot_fields": [],
        "difficulty": "unknown",
        "recommendation": "Manual solve or authorized bypass only",
        "status": "simulated",
        "note": "This is the MCP tool definition. See formbot_demo.py for CAPTCHA detection approach.",
    }
    return result


@app.tool()
def shadow_dom_fill(
    url: str,
    shadow_selectors: List[dict],
) -> dict:
    """
    Fill fields inside shadow DOM.

    shadow_selectors: [
      {"host_selector": "custom-element", "inner_selector": "input[name=foo]", "value": "bar"},
      ...
    ]

    Returns: fill status for each shadow host.
    """
    result = {
        "url": url,
        "shadow_hosts": len(shadow_selectors),
        "status": "simulated",
        "note": "This is the MCP tool definition. See formbot_demo.py for shadow DOM traversal example.",
    }
    return result


# ============================================================
# STANDALONE DEMO (run: python formbot_demo.py)
# ============================================================

if __name__ == "__main__":
    import asyncio
    from playwright.async_api import async_playwright

    async def demo():
        print("=" * 60)
        print("FormBot — Playwright Form Automation Demo")
        print("=" * 60)
        print()

        # Create a test HTML page with multiple form complexity
        test_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Test Form</title></head>
        <body>
          <h1>Multi-Step Registration</h1>

          <!-- Step 1: Basic info -->
          <form id="step1" action="#" method="POST">
            <label>Name: <input type="text" name="name" placeholder="Your name"></label><br>
            <label>Email: <input type="email" name="email" placeholder="email@example.com"></label><br>
            <label>Password: <input type="password" name="password"></label><br>
            <input type="hidden" name="csrf_token" value="abc123token">
            <!-- honeypot -->
            <input type="text" name="website" style="display:none">
            <button type="submit" id="step1_submit">Next Step</button>
          </form>

          <div id="step2" style="display:none">
            <form id="step2_form">
              <label>Bio: <textarea name="bio" rows="4"></textarea></label><br>
              <label>Avatar: <input type="file" name="avatar"></label><br>
              <label>
                Terms:
                <input type="checkbox" name="terms" value="agree">
              </label><br>
              <button type="button" id="step2_next">Complete</button>
            </form>
          </div>

          <!-- Shadow DOM custom element -->
          <custom-field id="shadow_host"></custom-field>

          <div id="success" style="display:none; color: green;">Registration Complete!</div>

          <script>
            // Show step 2 on submit
            document.getElementById('step1_submit').addEventListener('click', function(e) {
              e.preventDefault();
              document.getElementById('step1').style.display = 'none';
              document.getElementById('step2').style.display = 'block';
            });
            // Complete on step 2
            document.getElementById('step2_next').addEventListener('click', function() {
              document.getElementById('step2').style.display = 'none';
              document.getElementById('success').style.display = 'block';
            });
            // Shadow DOM
            const shadowHost = document.getElementById('shadow_host');
            const shadowRoot = shadowHost.attachShadow({mode: 'open'});
            shadowRoot.innerHTML = `
              <style>input { padding: 8px; margin: 4px 0; }</style>
              <h3>Shadow Fields</h3>
              <input type="text" name="shadow_name" placeholder="Shadow name">
              <input type="email" name="shadow_email" placeholder="Shadow email">
            `;
          </script>
        </body>
        </html>
        """

        # Write test HTML to temp file
        import tempfile
        import os
        tmp_html = os.path.join(tempfile.gettempdir(), "formbot_test.html")
        with open(tmp_html, "w") as f:
            f.write(test_html)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={"width": 1280, "height": 800})
            page = await context.new_page()

            # Step 1: Navigate
            print("[Step 1] Navigating to test form...")
            await page.goto(f"file://{tmp_html}")
            await page.wait_for_load_state("domcontentloaded")
            print("  ✓ Page loaded")

            # Step 2: Fingerprint the form
            print("[Step 2] Fingerprinting form...")
            inputs = await page.query_selector_all("input, textarea, select")
            print(f"  Found {len(inputs)} input elements")
            for inp in inputs:
                name = await inp.get_attribute("name") or "(no name)"
                inp_type = await inp.get_attribute("type") or "text"
                placeholder = await inp.get_attribute("placeholder") or "(none)"
                print(f"    - name={name}, type={inp_type}, placeholder={placeholder}")
            csrf = await page.query_selector("input[name=csrf_token]")
            print(f"  CSRF token present: {csrf is not None}")
            honeypot = await page.query_selector("input[name=website][style*='display:none']")
            print(f"  Honeypot field present: {honeypot is not None}")
            print("  ✓ Fingerprint complete")

            # Step 3: Fill step 1
            print("[Step 3] Filling step 1 form...")
            await page.fill("input[name=name]", "Bionic Daughter")
            await page.fill("input[name=email]", "daughter@bionic.ml")
            await page.fill("input[name=password]", "s3cure-p@ss")
            print("  ✓ Fields filled")

            # Step 4: Submit step 1
            print("[Step 4] Clicking step 1 submit...")
            await page.click("#step1_submit")
            await page.wait_for_timeout(500)
            print("  ✓ Step 1 submitted, step 2 visible")

            # Step 5: Fill step 2
            print("[Step 5] Filling step 2...")
            await page.fill("textarea[name=bio]", "Automated form testing with Playwright — authorized only.")
            # File upload
            import tempfile
            test_file = os.path.join(tempfile.gettempdir(), "formbot_test_upload.txt")
            with open(test_file, "w") as f:
                f.write("test upload content for FormBot demo")
            await page.set_input_files("input[name=avatar]", test_file)
            await page.check("input[name=terms]")
            print("  ✓ Step 2 fields filled + file uploaded + checkbox checked")

            # Step 6: Complete
            print("[Step 6] Completing registration...")
            await page.click("#step2_next")
            await page.wait_for_selector("#success", timeout=10000)
            success_text = await page.text("#success")
            print(f"  ✓ Success: {success_text.strip()}")

            # Step 7: Shadow DOM
            print("[Step 7] Accessing shadow DOM...")
            shadow_host = await page.query_selector("#shadow_host")
            shadow_root = await shadow_host.shadow_root()
            shadow_inputs = await shadow_root.query_selector_all("input")
            print(f"  Found {len(shadow_inputs)} shadow inputs")
            await shadow_inputs[0].fill("Shadow Name Value")
            await shadow_inputs[1].fill("shadow@test.ml")
            print("  ✓ Shadow DOM fields filled")

            # Cleanup
            await browser.close()
            os.remove(tmp_html)
            if os.path.exists(test_file):
                os.remove(test_file)

        print()
        print("=" * 60)
        print("FormBot Demo — ALL STEPS COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print()
        print("Capabilities demonstrated:")
        print("  ✓ Form fingerprinting (all inputs, CSRF, honeypot detection)")
        print("  ✓ Multi-step form filling + submission")
        print("  ✓ File upload via <input type=file>")
        print("  ✓ Checkbox interaction")
        print("  ✓ Shadow DOM traversal and field filling")
        print("  ✓ wait_for_selector for page state sync")
        print()
        print("Authorized testing only — our own test forms + authorized targets.")

    asyncio.run(demo())
