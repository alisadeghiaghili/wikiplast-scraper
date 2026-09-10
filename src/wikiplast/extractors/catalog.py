"""Catalog extractors: petros, polycats, category grades, grade history, products."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, TypeVar

from wikiplast.adapters.http_client import HttpClient
from wikiplast.adapters.storage import persist_section
from wikiplast.domain.catalog import (
    dedupe_categories,
    dedupe_grades,
    dedupe_petro_companies,
    dedupe_products,
    parse_category_grades,
    parse_grade_history,
    parse_petro_companies,
    parse_polymer_categories,
    parse_products,
)
from wikiplast.domain.html_parsing import parse_html
from wikiplast.exceptions import HttpError
from wikiplast.models.catalog import (
    CompanyProduct,
    GradeListing,
    GradePricePoint,
    PetroCompany,
    PolymerCategory,
)

T = TypeVar("T")

PETROS_PATH = "/petros"
POLYCATS_PATH = "/polycats"
PRODUCTS_PATH = "/products"

PETRO_FIELDS = (
    "company_id",
    "name",
    "url",
    "grade_count",
    "grades",
    "source_url",
)
CATEGORY_FIELDS = (
    "category_id",
    "name",
    "url",
    "parent_category",
    "parent_id",
    "description",
    "source_url",
)
GRADE_FIELDS = (
    "grade_id",
    "name",
    "url",
    "petrochemical",
    "petrochemical_url",
    "datasheet_url",
    "category_id",
    "category_name",
    "source_url",
)
GRADE_HISTORY_FIELDS = (
    "grade_id",
    "grade_name",
    "as_of_jalali",
    "as_of_iso",
    "price_raw",
    "price_value",
    "currency",
    "source_url",
)
PRODUCT_FIELDS = (
    "product_id",
    "product_key",
    "name",
    "url",
    "image_url",
    "company_id",
    "company_name",
    "view_count",
    "source_url",
)


def _rows(items: Sequence[Any]) -> list[dict[str, Any]]:
    return [item.to_row() for item in items]


def _discover_category_paths(polycats_html: str, base_url: str) -> list[dict[str, str]]:
    """Return top-level ``/grides/{id}`` paths from the taxonomy page.

    Args:
        polycats_html: HTML of ``/polycats``.
        base_url: Unused origin kept for symmetry.

    Returns:
        list[dict[str, str]]: ``id``, ``name``, ``path`` per family.
    """
    del base_url
    soup = parse_html(polycats_html)
    found: list[dict[str, str]] = []
    seen: set[str] = set()
    for box in soup.select(".catbox"):
        parent = box.select_one("h2.titlogo a")
        if parent is None:
            continue
        href = str(parent.get("href") or "")
        if not href.startswith("/grides/"):
            continue
        parts = [p for p in href.split("/") if p]
        if len(parts) < 2:
            continue
        cat_id = parts[1]
        path = f"/grides/{cat_id}"
        if path in seen:
            continue
        seen.add(path)
        found.append({"id": cat_id, "name": parent.get_text(strip=True), "path": path})
    return found


def _category_table_paths_from_grides(grides_html: str, base_url: str) -> list[dict[str, str]]:
    """Discover ``/cat{id}`` links from a ``/grides/{id}`` page.

    Args:
        grides_html: HTML of a polymer family page.
        base_url: Origin for absolute link checks.

    Returns:
        list[dict[str, str]]: Paths to category price tables.
    """
    del base_url
    soup = parse_html(grides_html)
    found: list[dict[str, str]] = []
    seen: set[str] = set()
    for a in soup.select("a[href*='/cat']"):
        href = str(a.get("href") or "")
        if not href.startswith("/cat"):
            continue
        # /cat86
        tail = href.split("?")[0].rstrip("/")
        if not tail.startswith("/cat") or not tail[4:].isdigit():
            continue
        if tail in seen:
            continue
        seen.add(tail)
        found.append({"id": tail[4:], "name": a.get_text(strip=True), "path": tail})
    return found


def extract_petros(client: HttpClient) -> list[PetroCompany]:
    """Extract petrochemical companies from ``/petros``.

    Args:
        client: HTTP client.

    Returns:
        list[PetroCompany]: Deduplicated companies.
    """
    html = client.get(PETROS_PATH)
    url = client.settings.base_url.rstrip("/") + PETROS_PATH
    return dedupe_petro_companies(
        parse_petro_companies(html, base_url=client.settings.base_url, source_url=url)
    )


def extract_polymer_categories(client: HttpClient) -> list[PolymerCategory]:
    """Extract polymer taxonomy from ``/polycats``.

    Args:
        client: HTTP client.

    Returns:
        list[PolymerCategory]: Deduplicated parent and child categories.
    """
    html = client.get(POLYCATS_PATH)
    url = client.settings.base_url.rstrip("/") + POLYCATS_PATH
    return dedupe_categories(
        parse_polymer_categories(html, base_url=client.settings.base_url, source_url=url)
    )


def extract_all_category_grades(
    client: HttpClient,
    *,
    max_categories: int | None = None,
) -> list[GradeListing]:
    """Crawl category grade tables via polycats → grides → cat{id}.

    Args:
        client: HTTP client.
        max_categories: Optional cap for smoke runs.

    Returns:
        list[GradeListing]: Deduplicated grades across categories.

    Raises:
        HttpError: If ``/polycats`` cannot be fetched.
    """
    polycats_html = client.get(POLYCATS_PATH)
    families = _discover_category_paths(polycats_html, client.settings.base_url)
    cat_paths: list[dict[str, str]] = []
    seen_cats: set[str] = set()
    for family in families:
        try:
            grides_html = client.get(family["path"])
        except HttpError as exc:
            if exc.status_code in {404, 410}:
                continue
            raise
        for cat in _category_table_paths_from_grides(grides_html, client.settings.base_url):
            if cat["path"] in seen_cats:
                continue
            seen_cats.add(cat["path"])
            cat_paths.append(cat)

    if max_categories is not None:
        cat_paths = cat_paths[:max_categories]

    listings: list[GradeListing] = []
    for cat in cat_paths:
        try:
            html = client.get(cat["path"])
        except HttpError as exc:
            if exc.status_code in {404, 410}:
                continue
            raise
        source_url = client.settings.base_url.rstrip("/") + cat["path"]
        listings.extend(
            parse_category_grades(
                html,
                base_url=client.settings.base_url,
                source_url=source_url,
                category_id=cat["id"],
                category_name=cat["name"],
            )
        )
    return dedupe_grades(listings)


def extract_grade_history(client: HttpClient, grade_id: str) -> list[GradePricePoint]:
    """Extract historical prices for one grade.

    Args:
        client: HTTP client.
        grade_id: Numeric grade id.

    Returns:
        list[GradePricePoint]: Price history points.
    """
    path = f"/gradeprice/{grade_id}"
    html = client.get(path)
    url = client.settings.base_url.rstrip("/") + path
    return parse_grade_history(
        html,
        base_url=client.settings.base_url,
        source_url=url,
        grade_id=grade_id,
    )


def extract_products(
    client: HttpClient,
    *,
    max_pages: int = 20,
) -> list[CompanyProduct]:
    """Extract marketplace products with early-stop pagination.

    Stops when a page yields no new product ids (``/products/2`` currently
    mirrors page 1 for anonymous clients — a naive page counter would keep
    hammering identical HTML).

    Args:
        client: HTTP client.
        max_pages: Hard page cap.

    Returns:
        list[CompanyProduct]: Deduplicated products.
    """
    collected: list[CompanyProduct] = []
    for page in range(1, max_pages + 1):
        path = PRODUCTS_PATH if page == 1 else f"{PRODUCTS_PATH}/{page}"
        try:
            html = client.get(path)
        except HttpError as exc:
            if exc.status_code in {404, 410}:
                break
            raise
        source_url = client.settings.base_url.rstrip("/") + path
        page_items = parse_products(
            html, base_url=client.settings.base_url, source_url=source_url
        )
        before = len(dedupe_products(collected))
        collected.extend(page_items)
        after = len(dedupe_products(collected))
        if after == before:
            break
    return dedupe_products(collected)


def run_catalog(
    client: HttpClient,
    data_dir: Path,
    *,
    grade_history_limit: int = 50,
    max_category_pages: int | None = None,
) -> dict[str, dict[str, Path]]:
    """Run v0.3 catalog extractors and persist artifacts.

    Args:
        client: HTTP client.
        data_dir: Output root.
        grade_history_limit: Max grade detail pages to fetch for history.
        max_category_pages: Optional cap on category tables (smoke tests).

    Returns:
        dict[str, dict[str, Path]]: Section name to artifact path map.
    """
    artifacts: dict[str, dict[str, Path]] = {}

    petros = extract_petros(client)
    artifacts["petro_companies"] = persist_section(
        _rows(petros), data_dir=data_dir, name="petro_companies", fieldnames=list(PETRO_FIELDS)
    )

    categories = extract_polymer_categories(client)
    artifacts["polymer_categories"] = persist_section(
        _rows(categories),
        data_dir=data_dir,
        name="polymer_categories",
        fieldnames=list(CATEGORY_FIELDS),
    )

    grades = extract_all_category_grades(client, max_categories=max_category_pages)
    artifacts["category_grades"] = persist_section(
        _rows(grades), data_dir=data_dir, name="category_grades", fieldnames=list(GRADE_FIELDS)
    )

    history_rows: list[GradePricePoint] = []
    for grade in grades[:grade_history_limit]:
        history_rows.extend(extract_grade_history(client, grade.grade_id))
    artifacts["grade_price_history"] = persist_section(
        _rows(history_rows),
        data_dir=data_dir,
        name="grade_price_history",
        fieldnames=list(GRADE_HISTORY_FIELDS),
    )

    products = extract_products(client)
    artifacts["products"] = persist_section(
        _rows(products), data_dir=data_dir, name="products", fieldnames=list(PRODUCT_FIELDS)
    )
    return artifacts
