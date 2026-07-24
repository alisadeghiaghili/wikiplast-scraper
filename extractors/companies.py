"""Extract manufacturing companies directory."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils import fetch, parse, save_csv, text
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

    # First, get the main page to find categories
    print("Fetching /companies ...")
    resp = fetch("/companies")
    if not resp:
        print("Failed to fetch /companies")
        return []

    soup = parse(resp.text)

    # Extract category links from the page
    categories = []
    for link in soup.select("h2.titlogo a"):
        href = link.get("href", "")
        name = text(link.select_one("span")) if link.select_one("span") else text(link)
        if href and name:
            categories.append({"name": name, "url": href})

    print(f"Found {len(categories)} categories")

    # For each category, get the first page
    for cat in categories:
        print(f"  Fetching: {cat['name']}")
        resp = fetch(cat['url'])
        if not resp:
            continue
        page_soup = parse(resp.text)
        companies = extract_companies_from_page(page_soup)
        for c in companies:
            c["category"] = cat["name"]
        all_companies.extend(companies)
        print(f"    Got {len(companies)} companies")

        # Try page 2, 3 etc for categories with many companies
        page = 2
        while page <= 10:  # Max 10 pages per category
            page_url = cat['url'].rstrip('/') + f'/{page}'
            resp = fetch(page_url)
            if not resp or resp.status_code != 200:
                break
            page_soup = parse(resp.text)
            page_companies = extract_companies_from_page(page_soup)
            if not page_companies:
                break
            for c in page_companies:
                c["category"] = cat["name"]
            all_companies.extend(page_companies)
            print(f"    Page {page}: {len(page_companies)} companies")
            page += 1

    save_csv(all_companies, "companies.csv")
    print(f"Total companies extracted: {len(all_companies)}")
    return all_companies


if __name__ == "__main__":
    run()
