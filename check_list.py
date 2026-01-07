import requests
import urllib3
import pandas as pd
import time

# Disable warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- THE CHECKER ---
def check_pixel_local(url):
    # Clean up URL
    url = url.strip()
    if not url.startswith('http'):
        url = 'https://' + url
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5, verify=False)
        html = response.text.lower()
        
        if 'fbevents.js' in html or 'fbq(\'init\'' in html:
            return "Has Pixel"
        elif 'googletagmanager' in html:
            return "Uses GTM (Pixel likely hidden)"
        else:
            return "❌ NO PIXEL (TARGET)"
    except:
        return "⚠️ Site Error"

# --- MAIN LOOP ---
print("--- READING URLS FROM FILE ---")

try:
    # Open the text file you pasted links into
    with open('urls.txt', 'r') as f:
        urls = f.readlines()
        
    print(f"Loaded {len(urls)} links. Scanning now...\n")
    
    valid_leads = []
    
    for url in urls:
        url = url.strip()
        
        # SKIP JUNK (Google links, Facebook, etc.)
        if "google" in url or "facebook" in url or "youtube" in url or url == "":
            continue
            
        status = check_pixel_local(url)
        print(f"[{status}] {url}")
        
        if "NO PIXEL" in status:
            valid_leads.append({
                "Website": url,
                "Ad Library": f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&q={url}"
            })
        
        # Go fast (no need to sleep as much since we aren't scraping Google)
        time.sleep(0.5)

    # --- EXPORT ---
    if valid_leads:
        df = pd.DataFrame(valid_leads)
        df.to_csv("final_leads.csv", index=False)
        print(f"\n🔥 DONE! Found {len(valid_leads)} targets. Saved to 'final_leads.csv'")
    else:
        print("\nNo targets found in that list.")

except FileNotFoundError:
    print("❌ ERROR: Could not find 'urls.txt'. Make sure you created the file and pasted the links!")