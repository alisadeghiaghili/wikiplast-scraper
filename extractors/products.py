"""Extract company products."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils import fetch, parse, save_csv, text
from config import BASE_URL


def extract_products_from_page(soup):
    """Extract product items from a page."""
    products = []
    for item in soup.select(".nibox, .product-item, .prodbox"):
        link = item.select_one("a[href]")
        if not link:
            continue

        title = text(link.select_one("h3")) or text(link)
        href = link.get("href", "")
        img = item.select_one("img")
        company_el = item.select_one("p .fa-cog, .company")
        views_el = item.select_one("p .fa-eye, .views")

        if title:
            products.append({
                "product_name": title,
                "url": BASE_URL + href if href.startswith("/") else href,
                "image_url": img.get("src", "") if img else "",
                "company_name": text(company_el.parent) if company_el else "",
                "view_count": text(views_el.parent) if views_el else "",
            })
    return products


def run():
    print("=== Extracting Company Products ===")
    all_products = []

    for page in range(1, 200):  # Safety limit
        url = f"/products/{page}" if page > 1 else "/products"
        resp = fetch(url)
        if not resp:
            break
        soup = parse(resp.text)
        items = extract_products_from_page(soup)
        if not items:
            print(f"  No more products at page {page}")
            break
        all_products.extend(items)
        print(f"  Page {page}: {len(items)} items")

        # Check for next page
        has_next = False
        for a in soup.select("a"):
            t = text(a)
            if "بعدی" in t or "›" in t or "»" in t:
                has_next = True
                break
        if not has_next and page > 1:
            break

    save_csv(all_products, "products.csv")
    print(f"Total products: {len(all_products)}")
    return all_products


if __name__ == "__main__":
    run()
