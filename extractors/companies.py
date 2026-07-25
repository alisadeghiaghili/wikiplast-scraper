"""Extract manufacturing companies directory."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils import fetch, fetch_all, parse, save_csv, text
from config import BASE_URL


def extract_companies_from_page(soup):
    """Extract company cards from a page."""
    companies = []
    for card in soup.select(".visitcard"):
        name_el = card.select_one("h3 a")
        contact_el = card.select_one("h4")
        website_el = card.select_one(".siteadd")
        rating_el = card.select_one(".font10 .bold")
        logo_el = card.select_one(".cardphoto img")
        verified = bool(card.select_one(".fa-certificate"))

        name = text(name_el)
        href = name_el.get("href", "") if name_el else ""
        company_id = ""
        if href:
            parts = href.strip("/").split("/")
            if parts and parts[0].startswith("c"):
                company_id = parts[0][1:]

        companies.append({
            "company_id": company_id,
            "name": name,
            "url": BASE_URL + href if href else "",
            "contact_person": text(contact_el),
            "website": text(website_el),
            "rating": text(rating_el),
            "logo_url": logo_el.get("src", "") if logo_el else "",
            "verified": verified,
        })
    return companies


def run():
    print("=== Extracting Companies Directory ===")
    all_companies = []

    print("Fetching /companies ...")
    resp = fetch("/companies")
    if not resp:
        print("Failed to fetch /companies")
        return []

    soup = parse(resp.text)

    # Extract category links
    categories = []
    for link in soup.select("h2.titlogo a"):
        href = link.get("href", "")
        name = text(link.select_one("span")) if link.select_one("span") else text(link)
        if href and name:
            categories.append({"name": name, "url": href})

    print(f"Found {len(categories)} categories")

    # Build all page URLs (page 1 + pagination)
    all_page_urls = []
    cat_map = {}  # url -> category name

    for cat in categories:
        cat_base = cat["url"].rstrip("/")
        all_page_urls.append(cat["url"])
        cat_map[cat["url"]] = cat["name"]
        for page in range(2, 11):
            page_url = f"{cat_base}/{page}"
            all_page_urls.append(page_url)
            cat_map[page_url] = cat["name"]

    print(f"  Pre-fetching {len(all_page_urls)} pages concurrently...")
    results = fetch_all(all_page_urls)

    # Parse results
    for url, resp in results.items():
        if not resp:
            continue
        page_soup = parse(resp.text)
        companies = extract_companies_from_page(page_soup)
        if not companies:
            continue
        cat_name = cat_map.get(url, "")
        for c in companies:
            c["category"] = cat_name
        all_companies.extend(companies)

    save_csv(all_companies, "companies.csv")
    print(f"Total companies extracted: {len(all_companies)}")
    return all_companies


if __name__ == "__main__":
    run()
