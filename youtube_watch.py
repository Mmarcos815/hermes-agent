from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.youtube.com/watch?v=JRyjrTNXxkU", timeout=30000)
    time.sleep(5)
    
    title = page.title()
    print(f"Title: {title}")
    
    # Get description
    description = page.evaluate("() => { const desc = document.querySelector('#description-inline-expander'); return desc ? desc.textContent.trim().substring(0, 2000) : 'No description'; }")
    print(f"Description: {description[:1000]}")
    
    # Get transcript
    transcript = page.evaluate("() => { const captions = document.querySelectorAll('.ytp-caption-segment'); const texts = []; captions.forEach(c => texts.push(c.textContent)); return texts.join(' '); }")
    if transcript:
        print(f"Transcript: {transcript[:3000]}")
    
    browser.close()
