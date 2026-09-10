"""Unit tests for catalog parsers (petros, categories, grades, products)."""

from __future__ import annotations

from pathlib import Path

from wikiplast.domain.catalog import (
    dedupe_petro_companies,
    dedupe_products,
    parse_category_grades,
    parse_grade_history,
    parse_petro_companies,
    parse_polymer_categories,
    parse_products,
    parse_related_grades,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "html"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_petro_companies_and_dedupe() -> None:
    """Petro blocks yield companies; duplicate ids collapse."""
    html = _load("petros.html")
    companies = parse_petro_companies(
        html, base_url="https://wikiplast.ir", source_url="https://wikiplast.ir/petros"
    )
    assert len(companies) == 3
    unique = dedupe_petro_companies(companies)
    assert len(unique) == 2
    abadan = unique[0]
    assert abadan.company_id == "1"
    assert abadan.name == "پتروشیمی آبادان"
    assert abadan.grade_count == 3
    assert "PVC S65 Abadan (113)" in abadan.grades
    assert abadan.url.endswith("/petros/1/" + "پتروشیمی-آبادان") or "/petros/1/" in abadan.url


def test_parse_polymer_categories() -> None:
    """catbox parents and minbox children are captured."""
    html = _load("polycats.html")
    cats = parse_polymer_categories(
        html, base_url="https://wikiplast.ir", source_url="https://wikiplast.ir/polycats"
    )
    assert len(cats) == 5  # 2 parents + 3 children
    parents = [c for c in cats if not c.parent_id]
    children = [c for c in cats if c.parent_id]
    assert len(parents) == 2
    assert len(children) == 3
    pe = next(c for c in parents if c.category_id == "1")
    assert pe.name == "پلی اتیلن - PE"
    hdpe = next(c for c in children if c.category_id == "75")
    assert hdpe.parent_category == "پلی اتیلن - PE"
    assert hdpe.parent_id == "1"


def test_parse_category_grades() -> None:
    """cat table rows expose grade id, petro, datasheet."""
    html = _load("cat86.html")
    rows = parse_category_grades(
        html,
        base_url="https://wikiplast.ir",
        source_url="https://wikiplast.ir/cat86",
        category_id="86",
        category_name="PVC",
    )
    assert len(rows) == 3
    first = rows[0]
    assert first.grade_id == "113"
    assert first.name == "PVC S65 Abadan"
    assert first.petrochemical == "آبادان"
    assert first.petrochemical_url.startswith("https://wikiplast.ir/petros/1")
    assert first.datasheet_url.endswith(".pdf")
    arvand = rows[2]
    assert arvand.grade_id == "938"
    assert arvand.datasheet_url == ""


def test_parse_grade_history_and_related() -> None:
    """Grade detail history table converts Jalali dates and prices."""
    html = _load("gradeprice_36.html")
    points = parse_grade_history(
        html,
        base_url="https://wikiplast.ir",
        source_url="https://wikiplast.ir/gradeprice/36",
        grade_id="36",
    )
    assert len(points) == 2
    assert points[0].price_value == 142_000
    assert points[0].as_of_iso == "1399-04-01"
    assert points[1].price_value == 140_500
    assert points[0].grade_name.startswith("209Amir")
    related = parse_related_grades(html)
    assert "LLD 22402 Lorestan" in related


def test_parse_products_separates_view_count_from_company() -> None:
    """nibox company and view count must not collapse to the same string."""
    html = _load("products.html")
    items = parse_products(
        html, base_url="https://wikiplast.ir", source_url="https://wikiplast.ir/products"
    )
    unique = dedupe_products(items)
    # 2 cp + 1 products/{id}
    assert len(unique) == 3
    cp = next(p for p in unique if p.product_key == "cp")
    assert cp.product_id == "4947"
    assert cp.company_id == "983"
    box = next(p for p in unique if p.product_key == "products")
    assert box.product_id == "682"
    assert box.view_count == 3920
    assert "آیاتای" in box.company_name or box.company_name != str(box.view_count)
    # regression pin: company field must not equal the view count string
    assert box.company_name != "3920"


def test_dedupe_products_ignores_missing_ids() -> None:
    """Rows without ids are dropped rather than kept as empty keys."""
    html = _load("products.html")
    items = parse_products(
        html, base_url="https://wikiplast.ir", source_url="https://wikiplast.ir/products"
    )
    # inject a bad row via rebuild
    from wikiplast.models.catalog import CompanyProduct

    bad = CompanyProduct(
        product_id="",
        product_key="cp",
        name="x",
        url="",
        image_url="",
        company_id="",
        company_name="",
        view_count=None,
        source_url="",
    )
    unique = dedupe_products([*items, bad])
    assert all(p.product_id for p in unique)
