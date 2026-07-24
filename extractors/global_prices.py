"""Extract global polymer and chemical prices."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils import fetch, parse, save_csv, text
from config import BASE_URL


def extract_global_table(soup):
    """Extract price table from global prices page."""
    rows = []
    table = soup.select_one("table.grtbl")
    if not table:
        return rows

    current_product = ""
    for tr in table.select("tr"):
        cells = tr.select("td")
        if not cells or len(cells) < 2:
            continue

        # Skip header rows (grhead class)
        if "grhead" in " ".join(tr.get("class", [])):
            continue

        first_cell = cells[0]
        rowspan = first_cell.get("rowspan", "")

        if rowspan and len(cells) >= 3:
            # New product group row
            current_product = text(first_cell)
            region = text(cells[1])
            price_floor = text(cells[2])
            price_ceiling = text(cells[3]) if len(cells) > 3 else ""
            # Skip if it looks like a header
            if "نام محصول" in current_product or "منطقه" in region:
                continue
            rows.append({
                "product": current_product,
                "region": region,
                "price_floor_usd": price_floor,
                "price_ceiling_usd": price_ceiling,
            })
        elif len(cells) >= 3 and not rowspan:
            # Continuation row or standalone
            potential_region = text(cells[0])
            potential_floor = text(cells[1])
            potential_ceiling = text(cells[2]) if len(cells) > 2 else ""
            # Skip header-like rows
            if "نام محصول" in potential_region or "منطقه" in potential_floor:
                continue
            if potential_region and current_product:
                rows.append({
                    "product": current_product,
                    "region": potential_region,
                    "price_floor_usd": potential_floor,
                    "price_ceiling_usd": potential_ceiling,
                })

    return rows


def run():
    print("=== Extracting Global Polymer Prices (Platts) ===")
    polymer_prices = []

    resp = fetch("/global")
    if resp:
        soup = parse(resp.text)
        polymer_prices = extract_global_table(soup)
        for p in polymer_prices:
            p["source"] = "Platts"
        print(f"  Platts: {len(polymer_prices)} rows")

    print("=== Extracting Global Polymer Prices (ICIS) ===")
    resp = fetch("/global/2")
    if resp:
        soup = parse(resp.text)
        icis_prices = extract_global_table(soup)
        for p in icis_prices:
            p["source"] = "ICIS"
        polymer_prices.extend(icis_prices)
        print(f"  ICIS: {len(icis_prices)} rows")

    save_csv(polymer_prices, "global_polymer_prices.csv")

    print("=== Extracting Global Chemical Prices ===")
    chemical_prices = []
    resp = fetch("/chemical")
    if resp:
        soup = parse(resp.text)
        chemical_prices = extract_global_table(soup)
        for p in chemical_prices:
            p["source"] = "chemical"
        print(f"  Chemical: {len(chemical_prices)} rows")

    save_csv(chemical_prices, "global_chemical_prices.csv")
    return polymer_prices, chemical_prices


if __name__ == "__main__":
    run()
