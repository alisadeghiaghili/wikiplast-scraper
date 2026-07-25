import time
import csv
import os
import random
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from config import BASE_URL, MAX_RETRIES, random_headers, random_delay, BACKOFF_BASE, MAX_WORKERS

# Persistent session per thread
_sessions = {}
_lock_print = False


def get_session():
    """Get or create a thread-local persistent session."""
    import threading
    tid = threading.current_thread().ident
    if tid not in _sessions:
        s = requests.Session()
        try:
            s.get(BASE_URL, headers=random_headers(), timeout=15)
            time.sleep(random_delay())
        except Exception:
            pass
        _sessions[tid] = s
    return _sessions[tid]


def fetch(url, session=None):
    """Fetch a URL with anti-detection: random UA, delays, retries, backoff."""
    full_url = url if url.startswith("http") else BASE_URL + url
    s = session or get_session()

    for attempt in range(MAX_RETRIES):
        headers = random_headers()
        try:
            resp = s.get(full_url, headers=headers, timeout=20)
            resp.encoding = "utf-8"

            if resp.status_code == 200:
                time.sleep(random_delay())
                return resp
            elif resp.status_code == 429:
                wait = random.uniform(8, 20)
                print(f"  Rate limited (429), waiting {wait:.1f}s...")
                time.sleep(wait)
            elif resp.status_code == 403:
                print(f"  Blocked (403), rotating session...")
                import threading
                tid = threading.current_thread().ident
                _sessions.pop(tid, None)
                time.sleep(random.uniform(3, 8))
            else:
                print(f"  HTTP {resp.status_code} for {full_url} (attempt {attempt+1})")

        except requests.Timeout:
            wait = random.uniform(2, 5) * (BACKOFF_BASE ** attempt)
            time.sleep(wait)
        except requests.ConnectionError:
            wait = random.uniform(3, 8) * (BACKOFF_BASE ** attempt)
            time.sleep(wait)
        except requests.RequestException as e:
            time.sleep(random_delay() * (attempt + 1))

    return None


def fetch_all(urls):
    """Fetch multiple URLs concurrently with ThreadPoolExecutor."""
    results = {}

    def _fetch_one(url):
        resp = fetch(url)
        return (url, resp)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(_fetch_one, url): url for url in urls}
        for future in as_completed(futures):
            url, resp = future.result()
            results[url] = resp

    return results


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
