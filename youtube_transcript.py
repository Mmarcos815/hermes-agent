from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.youtube.com/watch?v=JRyjrTNXxkU", timeout=30000)
    time.sleep(3)
    
    # Click on "Show more" to expand description
    try:
        show_more = page.locator('yt-formatted-string:has-text("...more")')
        if show_more.count() > 0:
            show_more.click()
            time.sleep(1)
    except:
        pass
    
    # Get description
    description = page.evaluate("() => { const desc = document.querySelector('#description-inline-expander'); return desc ? desc.textContent.trim() : 'No description'; }")
    print("=== DESCRIPTION ===")
    print(description)
    print()
    
    # Click transcript
    try:
        # Find and click the transcript toggle
        page.evaluate("() => { const btn = document.querySelector('button[aria-label=\"Transcript\"]') || document.querySelector('.ytp-transcript-button'); if (btn) btn.click(); }")
        time.sleep(3)
    except:
        pass
    
    # Get all text from transcript panel
    transcript = page.evaluate("""
        () => {
            // Try to find transcript segments
            const segments = document.querySelectorAll('.cue-group-text-line');
            if (segments.length > 0) {
                const texts = [];
                segments.forEach(s => texts.push(s.textContent.trim()));
                return texts.join('\\n');
            }
            
            // Try to find the transcript panel
            const panel = document.querySelector('.ytp-caption-window-container');
            if (panel) return panel.textContent;
            
            // Fallback: return body text after transcript keyword
            const body = document.body.innerText;
            const idx = body.indexOf('Transcript');
            if (idx > -1) return body.substring(idx, idx + 3000);
            
            return 'No transcript found';
        }
    """)
    
    print("=== TRANSCRIPT ===")
    print(transcript[:5000])
    
    browser.close()
