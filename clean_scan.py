import requests
import urllib3
import pandas as pd
import time
import re
import os
from urllib.parse import urlparse

# Disable warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
HISTORY_FILE = 'leads_history.csv'  # Permanent database of all scanned URLs
NEW_LEADS_FILE = 'new_leads.csv'    # Only the fresh leads from this run

JUNK_KEYWORDS = [
    "google.", "instagram.", "linkedin.", "twitter.", 
    "youtube.", "reddit.", "yelp.", "yellowpages.", "tripadvisor.", 
    "indeed.", "glassdoor.", "ratemds.", "pinterest.", "tiktok.",
    "policies.", "support.", "accounts.", "maps.", "search?", 
    "castanet.net", "telus.com", "shaw.ca", "facebook."
]

def clean_line(line):
    if not line: return ""
    line = re.sub(r'\\', '', line)
    return line.strip()

def get_base_domain(url):
    """Extracts the base domain (e.g., 'gymshark.com') from a full URL."""
    try:
        parsed = urlparse(url)
        # Use netloc (domain) and strip 'www.' to ensure duplicates like
        # www.gymshark.com and gymshark.com are treated as the same
        domain = parsed.netloc.replace('www.', '').lower()
        return domain
    except:
        return ""

def is_junk(url):
    url_lower = url.lower()
    
    # Explicitly filter Facebook Marketplace as requested
    if "facebook.com/marketplace" in url_lower:
        return True
        
    for junk in JUNK_KEYWORDS:
        if junk in url_lower:
            return True
    return False

def get_page_data(url):
    data = {"email": "", "phone": "", "fb_link": "", "pixel": "Unknown", "status_code": 0}
    
    try:
        # STRONGER MASK: Looks exactly like a real Chrome browser on Windows
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        }
        
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        data['status_code'] = response.status_code
        html = response.text
        html_lower = html.lower()

        # --- DIAGNOSTIC CHECK ---
        if response.status_code == 403 or response.status_code == 406:
            data['pixel'] = "🔒 BLOCKED (Firewall)"
            return data
            
        # 1. CHECK PIXEL (Expanded Search)
        has_fb_code = 'fbevents.js' in html_lower or 'fbq(\'init\'' in html_lower or 'connect.facebook.net' in html_lower
        has_gtm = 'googletagmanager' in html_lower
        
        if has_fb_code:
            data['pixel'] = "YES (Has Pixel)"
        elif has_gtm:
            data['pixel'] = "⚠️ HIDDEN (Inside GTM)" 
        else:
            data['pixel'] = "❌ NO PIXEL"

        # 2. FIND EMAIL
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)
        valid_emails = [e for e in emails if not any(x in e.lower() for x in ['sentry', 'wix', 'png', 'jpg', 'example', 'domain', 'sentry'])]
        if valid_emails:
            data['email'] = valid_emails[0]

        # 3. FIND PHONE (Improved Regex)
        # This checks for valid phone structures to avoid years/dates
        phone_pattern = r'(?:\+?1[-.\s]?)?\(?([2-9][0-9]{2})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        matches = re.findall(phone_pattern, html)
        if matches:
            # Reconstruct the first match into a clean format
            data['phone'] = f"{matches[0][0]}-{matches[0][1]}-{matches[0][2]}"

        # 4. FIND FACEBOOK LINK
        fb_matches = re.findall(r'href=[\'"](https?://(?:www\.)?facebook\.com/[a-zA-Z0-9.-]+)', html)
        valid_fb = [link for link in fb_matches if 'sharer' not in link and 'policies' not in link]
        if valid_fb:
            data['fb_link'] = valid_fb[0]

    except Exception as e:
        data['pixel'] = "⚠️ Error (Down/Timeout)"
        
    return data

# --- MAIN ENGINE ---

# 1. LOAD HISTORY (BY DOMAIN)
history_domains = set()
if os.path.exists(HISTORY_FILE):
    try:
        df_hist = pd.read_csv(HISTORY_FILE)
        # Convert every past URL into its base domain to prevent re-scanning subpages
        for past_url in df_hist['Website'].tolist():
            d = get_base_domain(past_url)
            if d: history_domains.add(d)
            
        print(f"Loaded {len(history_domains)} unique domains from history.")
    except Exception as e:
        print(f"Could not read history file (starting fresh): {e}")

print("--- READING URLS ---")

clean_urls = []
seen_domains_this_run = set() 

try:
    with open('urls.txt', 'r', encoding='utf-8') as f:
        raw_lines = f.readlines()
except:
    try:
        with open('urls.txt', 'r', encoding='cp1252') as f:
            raw_lines = f.readlines()
    except:
        print("❌ ERROR: Create 'urls.txt' first!")
        exit()

skipped_count = 0
for line in raw_lines:
    url = clean_line(line)
    if not url.startswith('http'): continue
    
    # Check Junk (including FB Marketplace)
    if is_junk(url): 
        continue
    
    # EXTRACT DOMAIN FOR CHECKING
    current_domain = get_base_domain(url)
    if not current_domain: continue # Skip if URL is broken

    # Check History (Have we ever done this DOMAIN before?)
    if current_domain in history_domains:
        skipped_count += 1
        continue
        
    # Check Duplicates in current list (Have we seen this DOMAIN in this run?)
    if current_domain in seen_domains_this_run:
        continue
        
    clean_urls.append(url)
    seen_domains_this_run.add(current_domain)

print(f"📉 Scanning {len(clean_urls)} NEW websites (Skipped {skipped_count} old ones)...")
print("----------------------------------------------------------------")
print(f"{'STATUS':<25} | {'WEBSITE':<40} | {'EMAIL'}")
print("----------------------------------------------------------------")

valid_new_leads = []

for url in clean_urls:
    data = get_page_data(url)
    status = data['pixel']
    
    # Print real-time status so you can see what's happening
    print(f"{status:<25} | {url[:38]:<40} | {data['email']}")

    # Only save the ones we can actually sell to
    if "NO PIXEL" in status or "HIDDEN" in status: 
        
        # Generate Ad Link
        if data['fb_link']:
            page_name = data['fb_link'].rstrip('/').split('/')[-1]
            ad_link = f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&q={page_name}"
        else:
            try:
                parsed = urlparse(url)
                domain = parsed.netloc.replace('www.', '')
                name_guess = domain.split('.')[0]
                ad_link = f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&q={name_guess}"
            except:
                ad_link = "Check Manually"

        valid_new_leads.append({
            "Website": url,
            "Pixel Status": status,
            "Running Ads": "",
            "Email": data['email'],
            "Phone": data['phone'],
            "Contacted": "NO",
            "Response": "NO",
            "Ad Link": ad_link
        })
        
    time.sleep(0.5)

# --- SAVE RESULTS ---
if valid_new_leads:
    columns = ["Website", "Pixel Status", "Running Ads", "Email", "Phone", "Contacted", "Response", "Ad Link"]
    df_new = pd.DataFrame(valid_new_leads, columns=columns)
    
    # 1. Save ONLY the new leads to a fresh file (overwrite mode)
    df_new.to_csv(NEW_LEADS_FILE, index=False)
    print(f"\n✅ Success! Saved {len(valid_new_leads)} NEW leads to '{NEW_LEADS_FILE}'")
    
    # 2. Append these new leads to the master history file
    header_needed = not os.path.exists(HISTORY_FILE)
    df_new.to_csv(HISTORY_FILE, mode='a', header=header_needed, index=False)
    print(f"📚 Updated '{HISTORY_FILE}' database.")
else:
    print("\nNo new qualified leads found this time.")