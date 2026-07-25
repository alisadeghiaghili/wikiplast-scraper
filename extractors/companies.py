"""Extract manufacturing companies directory."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils import fetch, fetch_all, parse, save_csv, text
from config import BASE_URL

MAX_CAT_PAGES = 5  # Max pages per category


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

    # First pass: fetch page 1 of all categories concurrently
    page1_urls = [cat["url"] for cat in categories]
    print(f"  Fetching page 1 of {len(page1_urls)} categories...")
    results = fetch_all(page1_urls)

    # Parse page 1 and collect URLs that need page 2+
    page2_urls = []
    cat_map = {}
    for cat in categories:
        resp = results.get(cat["url"])
        if not resp:
            continue
        page_soup = parse(resp.text)
        companies = extract_companies_from_page(page_soup)
        for c in companies:
            c["category"] = cat["name"]
        all_companies.extend(companies)

        # If we got a full page (12+ companies), try page 2
        if len(companies) >= 12:
            page2_url = cat["url"].rstrip("/") + "/2"
            page2_urls.append(page2_url)
            cat_map[page2_url] = cat["name"]

    print(f"  Page 1 done: {len(all_companies)} companies")
    print(f"  {len(page2_urls)} categories need page 2+")

    # Second pass: fetch page 2+ concurrently
    if page2_urls:
        results2 = fetch_all(page2_urls)
        for url, resp in results2.items():
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

            # If full page, queue page 3
            if len(companies) >= 12:
                page_num = int(url.rstrip("/").split("/")[-1]) + 1
                if page_num <= MAX_CAT_PAGES:
                    next_url = "/".join(url.rstrip("/").split("/")[:-1]) + f"/{page_num}"
                    page2_urls.append(next_url)
                    cat_map[next_url] = cat_name

        print(f"  Page 2+ done: {len(all_companies)} total companies")

    save_csv(all_companies, "companies.csv")
    print(f"Total companies extracted: {len(all_companies)}")
    return all_companies


if __name__ == "__main__":
    run()
