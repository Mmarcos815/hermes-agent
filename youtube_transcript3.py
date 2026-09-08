from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.youtube.com/watch?v=JRyjrTNXxkU", timeout=30000)
    time.sleep(4)
    
    # Get full page text
    body = page.evaluate("() => document.body.innerText")
    
    # Find the description section
    if 'The era of saying' in body:
        start = body.index('The era of saying')
        # Find the end of the description
        end_markers = ['Transcript', 'About', 'Videos', '853 subscribers']
        end = len(body)
        for marker in end_markers:
            idx = body.find(marker, start)
            if idx > -1 and idx < end:
                end = idx
        
        description = body[start:end].strip()
        print("=== FULL DESCRIPTION ===")
        print(description[:2000])
    
    # Also try to get transcript
    if 'Transcript' in body:
        idx = body.index('Transcript')
        # Skip past the UI elements
        remaining = body[idx:]
        # The actual transcript text starts after some UI elements
        print("\n=== TRANSCRIPT SECTION ===")
        # Find first timestamp pattern [0:00] or similar
        import re
        match = re.search(r'\d+:\d+', remaining)
        if match:
            start_idx = match.start()
            print(remaining[start_idx:start_idx+5000])
    
    browser.close()
