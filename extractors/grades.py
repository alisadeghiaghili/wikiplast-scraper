"""Extract polymer categories, grade taxonomy, and grade details."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils import fetch, parse, save_csv, text
from config import BASE_URL


def extract_grade_taxonomy(soup):
    """Extract category tree and subcategories from polycats tab 1."""
    grades = []
    tab1 = soup.select_one("#tab1")
    if not tab1:
        return grades

    for cat_box in tab1.select(".catbox"):
        h2 = cat_box.select_one("h2.titlogo a")
        if not h2:
            continue
        parent_category = text(h2)
        parent_url = h2.get("href", "")

        for sub_box in cat_box.select(".minbox a"):
            sub_name = text(sub_box.select_one("h3"))
            sub_desc = text(sub_box.select_one(".catdesc"))
            sub_href = sub_box.get("href", "")

            sub_id = ""
            if sub_href:
                parts = sub_href.strip("/").split("/")
                if len(parts) >= 2:
                    sub_id = parts[1]

            grades.append({
                "parent_category": parent_category,
                "parent_url": BASE_URL + parent_url if parent_url else "",
                "subcategory_name": sub_name,
                "subcategory_id": sub_id,
                "subcategory_description": sub_desc,
                "subcategory_url": BASE_URL + sub_href if sub_href else "",
            })

    return grades


def extract_grades_from_table(soup):
    """Extract individual grades from a subcategory table."""
    grades = []
    table = soup.select_one("table")
    if not table:
        return grades

    for row in table.select("tr"):
        cells = row.select("td")
        if len(cells) < 2:
            continue

        link = cells[0].select_one("a")
        if not link:
            continue

        href = link.get("href", "")
        name = text(link)
        if not name or not href:
            continue

        # Skip header row
        if "عنوان" in name:
            continue

        grade_id = ""
        if "/gradeprice/" in href:
            grade_id = href.split("/gradeprice/")[-1]
        elif href.startswith("/g"):
            grade_id = href[2:]

        petro = text(cells[1]) if len(cells) > 1 else ""

        grades.append({
            "grade_id": grade_id,
            "name": name,
            "url": BASE_URL + href if href.startswith("/") else href,
            "petrochemical_company": petro,
        })

    return grades


def extract_grade_detail(grade_id):
    """Fetch individual grade detail page."""
    url = f"/gradeprice/{grade_id}"
    resp = fetch(url)
    if not resp:
        return None

    soup = parse(resp.text)

    # Title
    h2 = soup.select_one("h2")
    title = text(h2) if h2 else ""

    detail = {"grade_id": grade_id, "full_title": title}

    # Find detail info in description section
    for div in soup.select("#desc div, .detail div"):
        label_el = div.select_one("span.purple")
        if label_el:
            label = text(label_el)
            link = div.select_one("a")
            if "پتروشیمی" in label and link:
                detail["petrochemical_company"] = text(link)
            elif "دسته بندی" in label and link:
                detail["category"] = text(link)
            elif "عنوان" in label and link:
                detail["full_title"] = text(link)

    # Related grades
    related = []
    for sidebox in soup.select(".sidebox"):
        h2_side = sidebox.select_one("h2.maintitle")
        if h2_side and "خانواده" in text(h2_side):
            for li in sidebox.select("ul.list li a"):
                related.append(text(li))
    detail["related_grades"] = "; ".join(related)

    return detail


def run():
    print("=== Extracting Grade Taxonomy ===")
    resp = fetch("/polycats")
    if not resp:
        print("Failed to fetch /polycats")
        return

    soup = parse(resp.text)
    taxonomy = extract_grade_taxonomy(soup)
    save_csv(taxonomy, "grades.csv")
    print(f"Taxonomy entries: {len(taxonomy)}")

    # Extract individual grades from each subcategory table
    print("\n=== Extracting Individual Grades ===")
    all_grades = []
    seen_ids = set()

    for entry in taxonomy:
        sub_url = entry["subcategory_url"]
        if not sub_url:
            continue
        print(f"  Scanning: {entry['subcategory_name']}")
        resp = fetch(sub_url)
        if not resp:
            continue
        page_soup = parse(resp.text)
        grades = extract_grades_from_table(page_soup)
        for g in grades:
            g["parent_category"] = entry["parent_category"]
            g["subcategory_name"] = entry["subcategory_name"]
        all_grades.extend(grades)
        print(f"    Found {len(grades)} grades")

    save_csv(all_grades, "individual_grades.csv")
    print(f"Total individual grades: {len(all_grades)}")

    # Extract grade details (limited to avoid timeout)
    print("\n=== Extracting Grade Details (first 50) ===")
    all_details = []
    for g in all_grades[:50]:
        gid = g["grade_id"]
        if gid in seen_ids or not gid:
            continue
        seen_ids.add(gid)
        detail = extract_grade_detail(gid)
        if detail:
            detail["short_name"] = g["name"]
            all_details.append(detail)

    save_csv(all_details, "grade_details.csv")
    print(f"Grade details extracted: {len(all_details)}")
    return all_grades, all_details


if __name__ == "__main__":
    run()
