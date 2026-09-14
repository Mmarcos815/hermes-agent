from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.youtube.com/watch?v=JRyjrTNXxkU", timeout=30000)
    time.sleep(3)
    
    # Click on the three dots menu and select "Open transcript"
    page.evaluate('''() => { const btn = document.querySelector('button[aria-label="More actions"]') || document.querySelector('.ytp-overflow-button'); if (btn) btn.click(); }''')
    time.sleep(1)
    
    # Try to find "Open transcript" option
    page.evaluate("() => { const items = document.querySelectorAll('.yt-menu-content span, .yt-context-menu span'); items.forEach(i => { if (i.textContent.includes('transcript')) i.click(); }); }")
    time.sleep(2)
    
    # Alternative: just get full body text and extract after "Transcript"
    body = page.evaluate("() => document.body.innerText")
    
    # Find transcript section
    if 'Transcript' in body:
        idx = body.index('Transcript')
        transcript = body[idx:idx+5000]
        print(transcript)
    else:
        print("No transcript section found")
        print("=== FULL BODY (last 2000 chars) ===")
        print(body[-2000:])
    
    browser.close()
