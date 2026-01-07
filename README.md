# 🔒 Proprietary Lead Generation Engine
### Automated Sales Pipeline & Pixel Auditor

**Note:** *The source code for this project is proprietary and currently generating revenue. This repository serves as a technical case study demonstrating the system architecture and engineering challenges solved.*

---

### 🚀 Project Overview
I engineered a full-cycle sales automation tool that identifies B2B clients, audits their websites for technical deficiencies (specifically tracking pixels), and automates personalized outreach.

**The Result:** The system currently runs autonomously, processing hundreds of leads per week and generating active revenue.

---

### ⚙️ System Architecture
The system consists of four independent modules working in a pipeline:

1.  **The Scraper (Lead Injection):**
    * Uses headless browsers to scrape search indexes for local businesses in specific niches.
    * *Challenge Solved:* Bypassing "l.facebook.com" redirects and filtering out non-business URLs (Yelp, Indeed) to isolate valid company homepages.

2.  **The Auditor (Qualification Engine):**
    * Asynchronously visits every URL to analyze the HTML DOM.
    * Detects the presence of `fbevents.js` (Meta Pixel) or Google Tag Manager.
    * **Logic:** If `Pixel == False`, the lead is "Qualified" and moved to the next stage.

3.  **The Database (Cloud Sync):**
    * Integration with **Google Sheets API** to serve as a live "Command Center."
    * Qualified leads are uploaded in real-time.

4.  **The Dispatcher (Outreach):**
    * Reads the Google Sheet to find "New" leads.
    * Uses SMTP rotation to send personalized emails based on the business's city and name.
    * Updates the database status to "Contacted" to prevent duplicate outreach.

---

### 🛠️ Tech Stack Used
* **Language:** Python 3.9+
* **Web Automation:** Playwright / Selenium
* **Networking:** AIOHTTP (Async Requests), BeautifulSoup4
* **APIs:** Google Cloud Platform (Sheets API, Drive API)
* **Data Handling:** Pandas, NumPy

---

### 📊 Engineering Highlights
* **Concurrency:** Implemented `asyncio` to reduce auditing time for 1,000 URLs from 40 minutes to <3 minutes.
* **Error Handling:** Built robust retry logic for network timeouts and anti-bot detection.
* **Sanitization:** Custom Regex patterns to clean phone numbers and emails for CRM compatibility.
