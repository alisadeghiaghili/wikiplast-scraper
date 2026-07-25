import random

BASE_URL = "https://wikiplast.ir"
MAX_RETRIES = 2

# Delay range in seconds (min, max) — randomized per request
DELAY_MIN = 0.3
DELAY_MAX = 1.2

# Backoff multiplier on retry
BACKOFF_BASE = 2.0

# Concurrency — max parallel requests (keep low to avoid blocks)
MAX_WORKERS = 4

# Realistic browser user agents (rotate randomly)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
]

ACCEPT_LANGUAGES = [
    "fa,en-US;q=0.9,en;q=0.8",
    "fa,en;q=0.9",
    "en-US,en;q=0.9,fa;q=0.8",
    "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7",
]

REFERERS = [
    "https://www.google.com/",
    "https://www.google.co.ir/",
    "https://www.bing.com/",
    "https://wikiplast.ir/",
]


def random_headers():
    """Generate randomized headers for each request."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": random.choice(ACCEPT_LANGUAGES),
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": random.choice(REFERERS),
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }


def random_delay():
    """Return a randomized delay between requests."""
    return random.uniform(DELAY_MIN, DELAY_MAX)
