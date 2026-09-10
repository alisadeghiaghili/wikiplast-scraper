"""Parsers for petrochemical, category, grade, and product pages."""

from __future__ import annotations

import re
from collections.abc import Iterable

from bs4 import Tag

from wikiplast.domain.html_parsing import (
    absolute_url,
    clean_text,
    first_int,
    parse_html,
    parse_int_price,
)
from wikiplast.domain.prices import to_iso_date
from wikiplast.models.catalog import (
    CompanyProduct,
    GradeListing,
    GradePricePoint,
    PetroCompany,
    PolymerCategory,
)

_PETRO_ID_RE = re.compile(r"/petros/(\d+)")
_GRIDES_ID_RE = re.compile(r"/grides/(\d+)")
_GRADEPRICE_ID_RE = re.compile(r"/gradeprice/(\d+)")
_G_ID_RE = re.compile(r"/g(\d+)")
_CP_ID_RE = re.compile(r"/cp(\d+)")
_PRODUCTS_ID_RE = re.compile(r"/products/(\d+)")


def _id_from(pattern: re.Pattern[str], href: str) -> str:
    if not href:
        return ""
    match = pattern.search(href)
    return match.group(1) if match else ""


def parse_petro_companies(
    html: str | bytes,
    *,
    base_url: str,
    source_url: str,
) -> list[PetroCompany]:
    """Parse ``.petrocats`` blocks into petrochemical companies.

    Args:
        html: Page HTML (``/petros`` or ``/polycats``).
        base_url: Origin for link resolution.
        source_url: Listing URL stamped on rows.

    Returns:
        list[PetroCompany]: Companies in document order.
    """
    soup = parse_html(html)
    companies: list[PetroCompany] = []
    for box in soup.select(".petrocats"):
        if not isinstance(box, Tag):
            continue
        link = box.select_one("h3 a")
        if link is None:
            continue
        href = str(link.get("href") or "")
        name = clean_text(link)
        if not name:
            continue
        grade_links = box.select("a[href*='/g']")
        grade_parts: list[str] = []
        for g in grade_links:
            g_href = str(g.get("href") or "")
            g_name = clean_text(g)
            g_id = _id_from(_G_ID_RE, g_href)
            if g_name:
                grade_parts.append(f"{g_name} ({g_id})" if g_id else g_name)
        companies.append(
            PetroCompany(
                company_id=_id_from(_PETRO_ID_RE, href),
                name=name,
                url=absolute_url(base_url, href),
                grade_count=len(grade_parts),
                grades="; ".join(grade_parts),
                source_url=source_url,
            )
        )
    return companies


def parse_polymer_categories(
    html: str | bytes,
    *,
    base_url: str,
    source_url: str,
) -> list[PolymerCategory]:
    """Parse ``.catbox`` taxonomy (parent families and subcategories).

    Args:
        html: HTML of ``/polycats``.
        base_url: Origin for link resolution.
        source_url: Listing URL stamped on rows.

    Returns:
        list[PolymerCategory]: Parent rows first for each box, then children.
    """
    soup = parse_html(html)
    categories: list[PolymerCategory] = []
    for box in soup.select(".catbox"):
        if not isinstance(box, Tag):
            continue
        parent_a = box.select_one("h2.titlogo a")
        if parent_a is None:
            continue
        parent_href = str(parent_a.get("href") or "")
        parent_name = clean_text(parent_a)
        parent_id = _id_from(_GRIDES_ID_RE, parent_href)
        categories.append(
            PolymerCategory(
                category_id=parent_id,
                name=parent_name,
                url=absolute_url(base_url, parent_href),
                parent_category="",
                parent_id="",
                description="",
                source_url=source_url,
            )
        )
        for sub in box.select(".minbox a"):
            if not isinstance(sub, Tag):
                continue
            sub_href = str(sub.get("href") or "")
            sub_name = clean_text(sub.select_one("h3")) or clean_text(sub)
            if not sub_name:
                continue
            categories.append(
                PolymerCategory(
                    category_id=_id_from(_GRIDES_ID_RE, sub_href),
                    name=sub_name,
                    url=absolute_url(base_url, sub_href),
                    parent_category=parent_name,
                    parent_id=parent_id,
                    description=clean_text(sub.select_one(".catdesc")),
                    source_url=source_url,
                )
            )
    return categories


def parse_category_grades(
    html: str | bytes,
    *,
    base_url: str,
    source_url: str,
    category_id: str,
    category_name: str,
) -> list[GradeListing]:
    """Parse the grade table on ``/cat{id}``.

    Expected columns: عنوان گرید | پتروشیمی | دیتاشیت | قیمت / نمودار.

    Args:
        html: Category page HTML.
        base_url: Origin for link resolution.
        source_url: Category page URL.
        category_id: Id of this category.
        category_name: Display name of this category.

    Returns:
        list[GradeListing]: Grade rows.
    """
    soup = parse_html(html)
    table = soup.select_one("table.grtbl")
    if table is None:
        return []
    listings: list[GradeListing] = []
    for tr in table.select("tr"):
        if not isinstance(tr, Tag):
            continue
        cells = tr.find_all("td", recursive=False)
        if len(cells) < 2:
            continue
        name_a = cells[0].select_one("a")
        if name_a is None:
            continue
        name = clean_text(name_a)
        if not name or name == "عنوان گرید":
            continue
        name_href = str(name_a.get("href") or "")
        petro_a = cells[1].select_one("a") if len(cells) > 1 else None
        datasheet_a = cells[2].select_one("a") if len(cells) > 2 else None
        listings.append(
            GradeListing(
                grade_id=_id_from(_GRADEPRICE_ID_RE, name_href),
                name=name,
                url=absolute_url(base_url, name_href),
                petrochemical=clean_text(petro_a) if petro_a else clean_text(cells[1]),
                petrochemical_url=absolute_url(
                    base_url, str(petro_a.get("href") if petro_a else "")
                ),
                datasheet_url=absolute_url(
                    base_url, str(datasheet_a.get("href") if datasheet_a else "")
                ),
                category_id=category_id,
                category_name=category_name,
                source_url=source_url,
            )
        )
    return listings


def parse_grade_history(
    html: str | bytes,
    *,
    base_url: str,
    source_url: str,
    grade_id: str,
) -> list[GradePricePoint]:
    """Parse the date/price history table on ``/gradeprice/{id}``.

    Args:
        html: Grade detail HTML.
        base_url: Origin for link resolution (unused for points but kept
            for API symmetry with other parsers).
        source_url: Grade page URL.
        grade_id: Grade identifier.

    Returns:
        list[GradePricePoint]: Historical points in document order.

    Examples:
        >>> pts = parse_grade_history(
        ...     "<html><head><title>قیمت های X - Y</title></head><body>"
        ...     "<table><tr><th>تاریخ</th><th>قیمت (ریال)</th></tr>"
        ...     "<tr><td>یکشنبه ۱ تير ۱۳۹۹</td><td>142,000</td></tr>"
        ...     "</table></body></html>",
        ...     base_url="https://wikiplast.ir",
        ...     source_url="https://wikiplast.ir/gradeprice/36",
        ...     grade_id="36",
        ... )
        >>> len(pts), pts[0].price_value, pts[0].as_of_iso
        (1, 142000, '1399-04-01')
    """
    del base_url  # reserved for future relative asset resolution
    soup = parse_html(html)
    title = soup.title.get_text(strip=True) if soup.title else ""
    # Title format: قیمت های {short} - {long}
    grade_name = title
    if title.startswith("قیمت های "):
        grade_name = title[len("قیمت های ") :].split("|")[0].strip()

    history: list[GradePricePoint] = []
    for table in soup.find_all("table"):
        if not isinstance(table, Tag):
            continue
        header_cells = table.find_all("tr")
        if not header_cells:
            continue
        header_text = clean_text(header_cells[0])
        if "تاریخ" not in header_text or "قیمت" not in header_text:
            continue
        for tr in header_cells[1:]:
            if not isinstance(tr, Tag):
                continue
            cells = tr.find_all("td", recursive=False)
            if len(cells) < 2:
                continue
            date_raw = clean_text(cells[0])
            price_raw = clean_text(cells[1])
            if not date_raw or date_raw == "-":
                continue
            history.append(
                GradePricePoint(
                    grade_id=grade_id,
                    grade_name=grade_name,
                    as_of_jalali=date_raw,
                    as_of_iso=to_iso_date(date_raw),
                    price_raw=price_raw,
                    price_value=parse_int_price(price_raw),
                    currency="IRR",
                    source_url=source_url,
                )
            )
        break
    return history


def parse_related_grades(html: str | bytes) -> list[str]:
    """Extract sibling grade names from the family sidebox.

    Args:
        html: Grade detail HTML.

    Returns:
        list[str]: Related grade names.
    """
    soup = parse_html(html)
    names: list[str] = []
    for box in soup.select(".sidebox"):
        heading = box.select_one("h2.maintitle")
        if heading is None or "خانواده" not in clean_text(heading):
            continue
        for a in box.select("ul.list li a, a"):
            name = clean_text(a)
            if name:
                names.append(name)
    return names


def parse_products(
    html: str | bytes,
    *,
    base_url: str,
    source_url: str,
) -> list[CompanyProduct]:
    """Parse product cards from ``/products`` listing pages.

    Handles two layouts:
        * ``.proditem`` marketplace cards linking to ``/cp{id}`` inside
          ``.prdframe`` company containers (``id="comp{companyId}"``).
        * ``.nibox`` cards linking to ``/products/{id}`` with separate
          company (``fa-cog``) and view (``fa-eye``) icons — v0.1 collapsed
          both fields into the same parent text.

    Args:
        html: Listing page HTML.
        base_url: Origin for link resolution.
        source_url: Listing URL stamped on rows.

    Returns:
        list[CompanyProduct]: Products in document order.
    """
    soup = parse_html(html)
    products: list[CompanyProduct] = []

    for frame in soup.select(".prdframe"):
        if not isinstance(frame, Tag):
            continue
        frame_id = str(frame.get("id") or "")
        company_id = ""
        company_name = ""
        if frame_id.startswith("comp"):
            company_id = frame_id[4:]
            # Company name is often in the previous sibling banner.
            prev = frame.find_previous_sibling()
            hops = 0
            while prev is not None and hops < 5:
                banner = clean_text(prev)
                if banner:
                    company_name = banner.split("مشاهده")[0].strip()
                    break
                prev = prev.find_previous_sibling()
                hops += 1

        for item in frame.select(".proditem"):
            if not isinstance(item, Tag):
                continue
            title_a = item.select_one("h3 a") or item.select_one("a[href*='/cp']")
            if title_a is None:
                continue
            href = str(title_a.get("href") or "")
            name = clean_text(title_a)
            if not name:
                continue
            img = item.select_one("img")
            products.append(
                CompanyProduct(
                    product_id=_id_from(_CP_ID_RE, href),
                    product_key="cp",
                    name=name,
                    url=absolute_url(base_url, href),
                    image_url=absolute_url(base_url, str(img.get("src") if img else "")),
                    company_id=company_id,
                    company_name=company_name,
                    view_count=None,
                    source_url=source_url,
                )
            )

    for box in soup.select(".nibox"):
        if not isinstance(box, Tag):
            continue
        link = box.select_one("a[href*='/products/']")
        if link is None:
            continue
        href = str(link.get("href") or "")
        title = clean_text(link.select_one("h3")) or clean_text(link)
        if not title:
            continue
        img = link.select_one("img") or box.select_one("img")
        company = ""
        views: int | None = None
        for icon in box.select("i"):
            classes = " ".join(icon.get("class") or [])
            if "fa-cog" in classes:
                company = (
                    (icon.next_sibling or "").strip()
                    if isinstance(icon.next_sibling, str)
                    else ""
                )
                if not company:
                    company = clean_text(icon.parent)
            if "fa-eye" in classes:
                sibling = icon.next_sibling
                if isinstance(sibling, str):
                    views = first_int(sibling)
                elif sibling is not None:
                    views = first_int(clean_text(sibling))
        products.append(
            CompanyProduct(
                product_id=_id_from(_PRODUCTS_ID_RE, href),
                product_key="products",
                name=title,
                url=absolute_url(base_url, href),
                image_url=absolute_url(base_url, str(img.get("src") if img else "")),
                company_id="",
                company_name=company.strip(),
                view_count=views,
                source_url=source_url,
            )
        )
    return products


def dedupe_products(items: Iterable[CompanyProduct]) -> list[CompanyProduct]:
    """Deduplicate products by ``product_key`` + ``product_id``.

    Args:
        items: Iterable of products.

    Returns:
        list[CompanyProduct]: Unique products, first-seen order.
    """
    seen: set[tuple[str, str]] = set()
    unique: list[CompanyProduct] = []
    for item in items:
        key = (item.product_key, item.product_id)
        if not item.product_id or key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def dedupe_petro_companies(items: Iterable[PetroCompany]) -> list[PetroCompany]:
    """Deduplicate petrochemical companies by id.

    Args:
        items: Iterable of companies.

    Returns:
        list[PetroCompany]: Unique companies.
    """
    seen: set[str] = set()
    unique: list[PetroCompany] = []
    for item in items:
        if not item.company_id or item.company_id in seen:
            continue
        seen.add(item.company_id)
        unique.append(item)
    return unique


def dedupe_categories(items: Iterable[PolymerCategory]) -> list[PolymerCategory]:
    """Deduplicate categories by id + parent scope.

    Args:
        items: Iterable of categories.

    Returns:
        list[PolymerCategory]: Unique categories.
    """
    seen: set[tuple[str, str]] = set()
    unique: list[PolymerCategory] = []
    for item in items:
        key = (item.category_id, item.parent_id)
        if not item.category_id or key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def dedupe_grades(items: Iterable[GradeListing]) -> list[GradeListing]:
    """Deduplicate grade listings by grade_id.

    Args:
        items: Iterable of grade listings.

    Returns:
        list[GradeListing]: Unique listings.
    """
    seen: set[str] = set()
    unique: list[GradeListing] = []
    for item in items:
        if not item.grade_id or item.grade_id in seen:
            continue
        seen.add(item.grade_id)
        unique.append(item)
    return unique
