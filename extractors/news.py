"""Extract news and articles."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils import fetch, parse, save_csv, text
from config import BASE_URL

MAX_PAGES = 20


def extract_items(soup):
    """Extract news/article items from a page."""
    items = []
    seen_urls = set()

    # Method 1: Box cards (news homepage, medbox)
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

    # Method 2: Direct article/news links
    for link in soup.select('a[href*="/news/"], a[href*="/article/"]'):
        href = link.get("href", "")
        title = text(link)
        if title and href and len(title) > 5 and href not in seen_urls:
            # Skip navigation/utility links
            if any(skip in href for skip in ["/archive-news/", "/search"]):
                continue
            seen_urls.add(href)
            items.append({
                "title": title,
                "url": BASE_URL + href if href.startswith("/") else href,
                "thumbnail": "",
                "date": "",
            })

    # Method 3: List items
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
    """Extract items from paginated listing."""
    all_items = []
    seen = set()
    for page in range(1, MAX_PAGES + 1):
        url = f"{url_base}/{page}" if page > 1 else url_base
        resp = fetch(url)
        if not resp:
            break
        soup = parse(resp.text)
        items = extract_items(soup)
        # Deduplicate
        new_items = [i for i in items if i["url"] not in seen]
        for i in new_items:
            seen.add(i["url"])
        if not new_items:
            break
        all_items.extend(new_items)
        print(f"  {label} page {page}: {len(new_items)} items (total: {len(all_items)})")

        has_next = any("بعدی" in text(a) for a in soup.select("a"))
        if not has_next and page > 1:
            break

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
