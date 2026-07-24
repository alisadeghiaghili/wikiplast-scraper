"""Extract petrochemical companies and their product grades."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils import fetch, parse, save_csv, text
from config import BASE_URL


def run():
    print("=== Extracting Petrochemical Companies ===")
    resp = fetch("/polycats")
    if not resp:
        print("Failed to fetch /polycats")
        return

    soup = parse(resp.text)
    petrochemicals = []

    # Tab 2 contains petrochemical analysis (آنالیز مواد)
    tab2 = soup.select_one("#tab2")
    if not tab2:
        print("Could not find petrochemical tab (#tab2)")
        return

    for box in tab2.select(".petrocats"):
        h3 = box.select_one("h3 a")
        if not h3:
            continue

        company_name = text(h3)
        company_url = h3.get("href", "")
        company_id = ""
        if company_url:
            parts = company_url.strip("/").split("/")
            if len(parts) >= 2:
                company_id = parts[1]

        grades = []
        grade_links = box.select(".whbg a")
        for link in grade_links:
            grade_name = text(link)
            grade_href = link.get("href", "")
            grade_id = ""
            if grade_href and grade_href.startswith("/g"):
                grade_id = grade_href[2:]
            grades.append({"name": grade_name, "id": grade_id, "url": BASE_URL + grade_href if grade_href else ""})

        petrochemicals.append({
            "company_id": company_id,
            "company_name": company_name,
            "company_url": BASE_URL + company_url if company_url else "",
            "grade_count": len(grades),
            "grades": "; ".join([f"{g['name']} ({g['id']})" for g in grades]),
        })

    save_csv(petrochemicals, "petrochemicals.csv")
    print(f"Total petrochemical companies: {len(petrochemicals)}")
    return petrochemicals


if __name__ == "__main__":
    run()
