from flask import Flask
import threading
import os
import requests
from bs4 import BeautifulSoup
import time

app = Flask(__name__)

@app.route('/')
def home():
    return "Job Tracker is active!"

def run_web_server():
    # Render provides the PORT environment variable automatically
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# Start web server in background
threading.Thread(target=run_web_server, daemon=True).start()

# --- CONFIGURATION ---
BOT_TOKEN = "7799390812:AAGyT71IvcB52MHCyEqMtbr_bIylFn2Z3ZI"
CHAT_ID = "2108985800"
# Filtered URL specifically for LMIA and temporary foreign workers
URL = "https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring=LMIA&sort=M"

seen_jobs = set()

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Error sending to Telegram: {e}")

def is_international_friendly(job_url):
    """Checks if the job is explicitly open to candidates outside Canada."""
    try:
        response = requests.get(job_url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Look for the 'Globe' icon or the specific text regarding international applicants
        text = soup.get_text().lower()
        if "other candidates with or without a valid canadian work permit" in text:
            return True
        return False
    except:
        return False

def check_jobs():
    print("Checking for new LMIA jobs...")
    try:
        response = requests.get(URL, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        jobs = soup.find_all("article")

        for job in jobs:
            title_tag = job.find("a")
            if title_tag:
                job_title = title_tag.text.strip()
                link = "https://www.jobbank.gc.ca" + title_tag["href"]

                if link not in seen_jobs:
                    # Check if it's truly open to international candidates
                    if is_international_friendly(link):
                        seen_jobs.add(link)
                        message = f"<b>🇨🇦 NEW LMIA JOB</b>\n\n<b>Role:</b> {job_title}\n<b>Link:</b> {link}"
                        send_telegram(message)
                        print(f"Alert sent: {job_title}")
                    else:
                        # Mark as seen so we don't scan it again, even if not international
                        seen_jobs.add(link)
    except Exception as e:
        print(f"Error during job check: {e}")

# Main Loop
if __name__ == "__main__":
    send_telegram("🚀 Bot is now LIVE and tracking Canada jobs!")
    while True:
        check_jobs()
        # Sleep for 10 minutes (600 seconds) to avoid getting blocked by Job Bank
        time.sleep(600)
