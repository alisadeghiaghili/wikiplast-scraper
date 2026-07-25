"""Extract news and articles with concurrent fetching."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils import fetch, fetch_all, parse, save_csv, text
from config import BASE_URL

MAX_PAGES = 20


def extract_items(soup):
    """Extract news/article items from a page."""
    items = []
    seen_urls = set()

    for item in soup.select(".nibox, .newsbox, .box, .medbox, .newsitems"):
        link = item.select_one("a[href]")
        if not link:
            continue
        title = text(link.select_one("h3")) or text(link.select_one("h2")) or text(link)
        href = link.get("href", "")
        img = item.select_one("img")
        date_el = item.select_one(".newsico span, .font10, time, span")

        if title and href and len(title) > 3 and href not in seen_urls:
            seen_urls.add(href)
            items.append({
                "title": title,
                "url": BASE_URL + href if href.startswith("/") else href,
                "thumbnail": img.get("src", "") if img else "",
                "date": text(date_el) if date_el else "",
            })

    for link in soup.select('a[href*="/news/"], a[href*="/article/"]'):
        href = link.get("href", "")
        title = text(link)
        if title and href and len(title) > 5 and href not in seen_urls:
            if any(skip in href for skip in ["/archive-news/", "/search"]):
                continue
            seen_urls.add(href)
            items.append({
                "title": title,
                "url": BASE_URL + href if href.startswith("/") else href,
                "thumbnail": "",
                "date": "",
            })

    for li in soup.select(".newslist li, .list li"):
        link = li.select_one("a[href]")
        if not link:
            continue
        title = text(link)
        href = link.get("href", "")
        if title and href and ("/news/" in href or "/article/" in href) and href not in seen_urls:
            seen_urls.add(href)
            items.append({
                "title": title,
                "url": BASE_URL + href if href.startswith("/") else href,
                "thumbnail": "",
                "date": "",
            })

    return items


def extract_paginated(url_base, label):
    """Extract items from paginated listing using concurrent fetch."""
    # Build all page URLs
    page_urls = [url_base] + [f"{url_base}/{p}" for p in range(2, MAX_PAGES + 1)]

    print(f"  Pre-fetching {len(page_urls)} {label} pages...")
    results = fetch_all(page_urls)

    all_items = []
    seen = set()
    for url in page_urls:
        resp = results.get(url)
        if not resp:
            continue
        soup = parse(resp.text)
        items = extract_items(soup)
        new_items = [i for i in items if i["url"] not in seen]
        for i in new_items:
            seen.add(i["url"])
        if new_items:
            all_items.extend(new_items)

    return all_items


def run():
    print("=== Extracting News ===")
    news_items = extract_paginated("/archive-news", "News")
    save_csv(news_items, "news.csv")
    print(f"Total news: {len(news_items)}")

    print("\n=== Extracting Articles ===")
    article_items = extract_paginated("/articles", "Articles")
    save_csv(article_items, "articles.csv")
    print(f"Total articles: {len(article_items)}")

    return news_items, article_items


if __name__ == "__main__":
    run()
