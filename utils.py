import time
import csv
import os
import random
import requests
from bs4 import BeautifulSoup
from config import BASE_URL, MAX_RETRIES, random_headers, random_delay, BACKOFF_BASE

# Persistent session to reuse cookies across requests
_session = None


def get_session():
    """Get or create a persistent session with cookie support."""
    global _session
    if _session is None:
        _session = requests.Session()
        # Set initial cookies by visiting homepage
        try:
            _session.get(BASE_URL, headers=random_headers(), timeout=15)
            time.sleep(random_delay())
        except Exception:
            pass
    return _session


def fetch(url, session=None):
    """Fetch a URL with anti-detection: random UA, delays, retries, backoff."""
    full_url = url if url.startswith("http") else BASE_URL + url
    s = session or get_session()

    for attempt in range(MAX_RETRIES):
        headers = random_headers()
        try:
            resp = s.get(full_url, headers=headers, timeout=30)
            resp.encoding = "utf-8"

            if resp.status_code == 200:
                time.sleep(random_delay())
                return resp
            elif resp.status_code == 429:
                # Rate limited — back off significantly
                wait = random.uniform(10, 30)
                print(f"  Rate limited (429), waiting {wait:.1f}s...")
                time.sleep(wait)
            elif resp.status_code == 403:
                # Forbidden — might be blocked, rotate session
                print(f"  Blocked (403), rotating session...")
                global _session
                _session = None
                time.sleep(random.uniform(5, 15))
            else:
                print(f"  HTTP {resp.status_code} for {full_url} (attempt {attempt+1})")

        except requests.Timeout:
            wait = random.uniform(3, 8) * (BACKOFF_BASE ** attempt)
            print(f"  Timeout for {full_url}, waiting {wait:.1f}s (attempt {attempt+1})")
            time.sleep(wait)
        except requests.ConnectionError:
            wait = random.uniform(5, 15) * (BACKOFF_BASE ** attempt)
            print(f"  Connection error for {full_url}, waiting {wait:.1f}s (attempt {attempt+1})")
            time.sleep(wait)
        except requests.RequestException as e:
            print(f"  Error fetching {full_url}: {e} (attempt {attempt+1})")
            time.sleep(random_delay() * (attempt + 1))

    print(f"  FAILED after {MAX_RETRIES} attempts: {full_url}")
    return None


def parse(html):
    """Parse HTML string into BeautifulSoup object."""
    return BeautifulSoup(html, "lxml")


def save_csv(rows, filename, fieldnames=None):
    """Save list of dicts to CSV file."""
    os.makedirs("data", exist_ok=True)
    filepath = os.path.join("data", filename)
    if not rows:
        print(f"  No data for {filename}")
        return
    if fieldnames is None:
        fieldnames = list(rows[0].keys())
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Saved {len(rows)} rows to {filename}")


def text(el):
    """Extract clean text from a BeautifulSoup element."""
    if el is None:
        return ""
    return el.get_text(strip=True)
