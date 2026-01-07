from playwright.sync_api import sync_playwright
import time
import random
import os
from urllib.parse import parse_qs, urlparse

# --- CONFIGURATION ---
SEARCH_TERM = "Vancouver"   
SCROLL_DURATION = 120      
OUTPUT_FILE = "urls.txt"  
# ---------------------

def extract_real_url(raw_url):
    """
    Decodes Facebook's 'l.facebook.com' redirects to find the REAL business site.
    """
    if "l.facebook.com" in raw_url or "facebook.com/l.php" in raw_url:
        try:
            # Parse the URL to find parameters
            parsed = urlparse(raw_url)
            query_params = parse_qs(parsed.query)
            # The real URL is usually in the 'u' parameter
            if 'u' in query_params:
                return query_params['u'][0]
        except:
            return None
    return raw_url

def scrape_fb_library():
    # 1. Load existing URLs
    existing_urls = set()
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    existing_urls.add(line.strip())
            print(f"📚 Loaded {len(existing_urls)} existing URLs.")
        except:
            pass

    with sync_playwright() as p:
        print("🚀 Launching Browser...")
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        page = context.new_page()

        print(f"🔎 Searching for '{SEARCH_TERM}'...")
        url = f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=CA&q={SEARCH_TERM}&sort_data[direction]=desc&sort_data[mode]=relevancy_monthly_grouped"
        page.goto(url)

        try:
            page.wait_for_timeout(3000) 
        except:
            pass

        print(f"⬇️ Auto-scrolling for {SCROLL_DURATION} seconds...")
        start_time = time.time()
        while time.time() - start_time < SCROLL_DURATION:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(random.uniform(1.5, 3.5))
            elapsed = int(time.time() - start_time)
            print(f"   ... scrolled ({elapsed}/{SCROLL_DURATION}s)")

        print("👀 Extracting links...")
        # We grab ALL links first
        all_links = page.eval_on_selector_all('a', 'elements => elements.map(e => e.href)')
        
        new_found_urls = set()
        
        for link in all_links:
            link = link.strip()
            
            # 1. UNWRAP the Facebook Redirect (The key fix!)
            real_url = extract_real_url(link)
            if not real_url: continue
            
            # 2. NOW filter out the junk (after unwrapping)
            if "facebook.com" in real_url: continue
            if "instagram.com" in real_url: continue
            if "business.help" in real_url: continue
            if "google.com" in real_url: continue 
            if "whatsapp.com" in real_url: continue
            if not real_url.startswith("http"): continue
            
            # 3. Add to list if unique
            if real_url not in existing_urls:
                new_found_urls.add(real_url)

        print(f"💾 Found {len(new_found_urls)} NEW unique URLs.")
        
        if new_found_urls:
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                for url in new_found_urls:
                    f.write(f"{url}\n")
            print(f"✅ Appended {len(new_found_urls)} new links to '{OUTPUT_FILE}'.")
        else:
            print("No new links found this run.")
        
        browser.close()

if __name__ == "__main__":
    scrape_fb_library()