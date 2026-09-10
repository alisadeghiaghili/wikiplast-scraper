"""Parsers for wikiplast bourse / IME market pages."""

from __future__ import annotations

import re

from bs4 import Tag

from wikiplast.domain.html_parsing import (
    absolute_url,
    clean_text,
    first_int,
    parse_html,
    parse_int_price,
)
from wikiplast.domain.prices import to_iso_date
from wikiplast.models.bourse import (
    BasePriceComparison,
    BourseDeal,
    BourseInfographicMetric,
    BourseOffer,
    BourseTopProduct,
    ByabStatus,
    CompanyQuota,
)

_CAT_ID_RE = re.compile(r"/cat(\d+)")
_G_ID_RE = re.compile(r"/g(\d+)")


def _is_banner_row(cells: list[Tag]) -> bool:
    return len(cells) == 1


def parse_bourse_deals(
    html: str | bytes,
    *,
    base_url: str,
    source_url: str,
) -> list[BourseDeal]:
    """Parse ``/deals`` trade rows.

    Layout: category banner (single cell with ``/cat`` link), column header,
    then data rows with an empty leading cell, grade, average price, supply
    tons, traded tons. Contract-type notes and ads are skipped.

    Args:
        html: Page HTML.
        base_url: Origin for link resolution.
        source_url: Absolute page URL stamped on rows.

    Returns:
        list[BourseDeal]: Parsed deals in document order.
    """
    soup = parse_html(html)
    table = soup.find("table")
    if table is None:
        return []
    as_of = to_iso_date(soup.title.get_text(strip=True) if soup.title else "")

    category = ""
    contract_type = ""
    deals: list[BourseDeal] = []
    for tr in table.find_all("tr"):
        if not isinstance(tr, Tag):
            continue
        cells = [c for c in tr.find_all(["td", "th"], recursive=False) if isinstance(c, Tag)]
        if not cells:
            continue
        texts = [clean_text(c) for c in cells]

        if _is_banner_row(cells):
            joined = texts[0]
            href = cells[0].find("a")
            href_val = str(href.get("href") if href else "")
            if href_val.startswith("/cat") or (joined and "مشاهده" not in joined and "نمایشگاه" not in joined):
                if "نوع قرارداد" in joined:
                    contract_type = joined
                    continue
                if "نمایشگاه" in joined or "مشاهده" in joined:
                    continue
                category = joined
            continue

        if texts and texts[0] == "گرید":
            continue

        # Data rows often start with an empty spacer cell.
        content = [t for t in texts if t != ""]
        if len(content) < 3:
            continue
        # grade, price, supply, traded — or without spacer: same order
        grade = content[0]
        if grade in {"گرید", "اطلاعات بیشتر"}:
            continue
        price = parse_int_price(content[1]) if len(content) > 1 else None
        supply = first_int(content[2]) if len(content) > 2 else None
        traded = first_int(content[3]) if len(content) > 3 else None
        # If first content cell is numeric-only it is not a grade name.
        if grade.isdigit():
            continue
        deals.append(
            BourseDeal(
                polymer_category=category,
                grade_name=grade,
                avg_price_rial=price,
                supply_tons=supply,
                traded_tons=traded,
                contract_type=contract_type,
                as_of_iso=as_of,
                source_url=source_url,
            )
        )
    return deals


def parse_bourse_offers(
    html: str | bytes,
    *,
    base_url: str,
    source_url: str,
) -> list[BourseOffer]:
    """Parse ``/offers`` supply rows.

    Args:
        html: Page HTML.
        base_url: Origin for link resolution.
        source_url: Absolute page URL.

    Returns:
        list[BourseOffer]: Parsed offers in document order.
    """
    soup = parse_html(html)
    table = soup.find("table")
    if table is None:
        return []
    as_of = to_iso_date(soup.title.get_text(strip=True) if soup.title else "")

    category = ""
    offers: list[BourseOffer] = []
    for tr in table.find_all("tr"):
        if not isinstance(tr, Tag):
            continue
        cells = [c for c in tr.find_all(["td", "th"], recursive=False) if isinstance(c, Tag)]
        if not cells:
            continue
        texts = [clean_text(c) for c in cells]
        if _is_banner_row(cells):
            joined = texts[0]
            if "مشاهده" in joined or "نمایشگاه" in joined:
                continue
            category = joined
            continue
        if texts and texts[0] == "گرید":
            continue
        content = [t for t in texts if t != ""]
        if len(content) < 2:
            continue
        grade = content[0]
        if grade.isdigit() or grade in {"گرید", "اطلاعات بیشتر"}:
            continue
        offers.append(
            BourseOffer(
                polymer_category=category,
                grade_name=grade,
                base_price_rial=parse_int_price(content[1]) if len(content) > 1 else None,
                base_qty=first_int(content[2]) if len(content) > 2 else None,
                max_increase=first_int(content[3]) if len(content) > 3 else None,
                as_of_iso=as_of,
                source_url=source_url,
            )
        )
    return offers


def parse_byab_status(
    html: str | bytes,
    *,
    base_url: str,
    source_url: str,
) -> list[ByabStatus]:
    """Parse ``/byab`` product behinyab status table.

    Args:
        html: Page HTML.
        base_url: Origin for link resolution.
        source_url: Absolute page URL.

    Returns:
        list[ByabStatus]: One row per product family.
    """
    soup = parse_html(html)
    table = soup.select_one("table.grtbl") or soup.find("table")
    if table is None:
        return []
    as_of = to_iso_date(soup.title.get_text(strip=True) if soup.title else "")

    rows: list[ByabStatus] = []
    for tr in table.find_all("tr"):
        if not isinstance(tr, Tag):
            continue
        cells = tr.find_all("td", recursive=False)
        if len(cells) < 3:
            continue
        name_a = cells[0].select_one("a")
        name = clean_text(name_a) if name_a else clean_text(cells[0])
        if not name or name == "نام محصول":
            continue
        href = str(name_a.get("href") if name_a else "")
        diagram = cells[4].select_one("a") if len(cells) > 4 else None
        rows.append(
            ByabStatus(
                product_name=name,
                category_id=_CAT_ID_RE.search(href).group(1) if _CAT_ID_RE.search(href) else "",
                category_url=absolute_url(base_url, href),
                status=clean_text(cells[1]),
                monthly_purchase_cap=clean_text(cells[2]),
                valid_from=clean_text(cells[3]) if len(cells) > 3 else "",
                diagram_url=absolute_url(
                    base_url, str(diagram.get("href") if diagram else "")
                ),
                as_of_iso=as_of,
                source_url=source_url,
            )
        )
    return rows


def parse_company_quotas(
    html: str | bytes,
    *,
    base_url: str,
    source_url: str,
    page: int,
) -> list[CompanyQuota]:
    """Parse ``/behinyab`` or ``/behin.php`` company quota table.

    Args:
        html: Page HTML.
        base_url: Origin for link resolution (kept for API symmetry).
        source_url: Absolute page URL.
        page: 1-based page number for provenance.

    Returns:
        list[CompanyQuota]: Quota rows.
    """
    del base_url
    soup = parse_html(html)
    table = soup.select_one("table.grtbl") or soup.find("table")
    if table is None:
        return []
    quotas: list[CompanyQuota] = []
    for tr in table.find_all("tr"):
        if not isinstance(tr, Tag):
            continue
        cells = tr.find_all("td", recursive=False)
        if len(cells) < 6:
            continue
        texts = [clean_text(c) for c in cells]
        if texts[0] in {"ردیف", ""} and texts[1] == "نام واحد":
            continue
        if texts[1] == "نام واحد":
            continue
        if not texts[1]:
            continue
        quotas.append(
            CompanyQuota(
                row_number=texts[0],
                unit_name=texts[1],
                national_code=texts[2],
                material_name=texts[3],
                material_code=texts[4],
                annual_performance=texts[5],
                calculated_quota=texts[6] if len(texts) > 6 else "",
                page=page,
                source_url=source_url,
            )
        )
    return quotas


def parse_price_comparisons(
    html: str | bytes,
    *,
    base_url: str,
    source_url: str,
) -> list[BasePriceComparison]:
    """Parse ``/compare`` weekly base-price comparison table.

    Category banners are single-cell rows with a ``/cat`` link. Grade rows
    link to ``/g{id}`` and carry previous/current base prices plus change
    fields. The ``قیمت مبنای دلار`` FX row is skipped.

    Args:
        html: Page HTML.
        base_url: Origin for link resolution.
        source_url: Absolute page URL.

    Returns:
        list[BasePriceComparison]: Grade comparison rows.
    """
    soup = parse_html(html)
    table = soup.select_one("table.grtbl") or soup.find("table")
    if table is None:
        return []

    category = ""
    rows: list[BasePriceComparison] = []
    for tr in table.find_all("tr"):
        if not isinstance(tr, Tag):
            continue
        cells = [c for c in tr.find_all(["td", "th"], recursive=False) if isinstance(c, Tag)]
        if not cells:
            continue
        texts = [clean_text(c) for c in cells]

        # Category banner: one cell, often colspan.
        if len(cells) == 1:
            name_a = cells[0].select_one("a")
            href = str(name_a.get("href") if name_a else "")
            if href.startswith("/cat") or (texts[0] and "نام محصول" not in texts[0]):
                if texts[0] in {"نام محصول"} or texts[0].startswith("شنبه") or texts[0].startswith("یکشنبه"):
                    continue
                category = texts[0]
            continue

        if texts[0] in {"نام محصول"} or texts[0].startswith("شنبه") or texts[0].startswith("یکشنبه"):
            continue
        if texts[0] == "قیمت مبنای دلار":
            continue

        grade_a = cells[0].select_one("a")
        if grade_a is None:
            continue
        href = str(grade_a.get("href") or "")
        if not href.startswith("/g"):
            continue
        grade_name = clean_text(grade_a)
        g_match = _G_ID_RE.search(href)
        prev_price = parse_int_price(texts[1]) if len(texts) > 1 else None
        curr_price = parse_int_price(texts[2]) if len(texts) > 2 else None
        # Prefer first two numeric columns as prev/current; site layout is
        # prev | current | change_abs | change_pct | global...
        rows.append(
            BasePriceComparison(
                polymer_category=category,
                grade_name=grade_name,
                grade_id=g_match.group(1) if g_match else "",
                grade_url=absolute_url(base_url, href),
                base_price_prev=prev_price,
                base_price_current=curr_price,
                change_abs=texts[3] if len(texts) > 3 else "",
                change_pct=texts[4] if len(texts) > 4 else "",
                global_usd_per_ton=texts[5] if len(texts) > 5 else "",
                source_url=source_url,
            )
        )
    return rows


def parse_info_bourse_metrics(
    html: str | bytes,
    *,
    source_url: str,
) -> list[BourseInfographicMetric]:
    """Parse summary metric tiles from ``/info-bourse``.

    Args:
        html: Page HTML.
        source_url: Absolute page URL.

    Returns:
        list[BourseInfographicMetric]: Keyed metrics when labels are found.
    """
    soup = parse_html(html)
    table = soup.find("table")
    if table is None:
        return []

    text_blob = clean_text(table)
    metric_specs = (
        ("trade_volume_tons", "حجم معاملات"),
        ("trade_value_rial", "ارزش معاملات"),
        ("products_offered", "تعداد محصولات عرضه شده"),
        ("products_traded", "تعداد محصولات معامله شده"),
        ("products_competed", "تعداد محصولات رقابت شده"),
        ("period_label", "تاریخ"),
    )
    metrics: list[BourseInfographicMetric] = []
    # Cells are dense; extract numbers preceding each label when possible.
    for key, label in metric_specs:
        idx = text_blob.find(label)
        if idx < 0:
            continue
        window = text_blob[max(0, idx - 40) : idx]
        # last number in the window
        nums = re.findall(r"[\d,]+", window)
        raw = nums[-1].replace(",", "") if nums else ""
        value = int(raw) if raw.isdigit() else None
        if key == "period_label":
            metrics.append(
                BourseInfographicMetric(
                    metric_key=key,
                    metric_label=label,
                    metric_value_raw=window.strip()[-30:],
                    metric_value_num=None,
                    source_url=source_url,
                )
            )
            continue
        metrics.append(
            BourseInfographicMetric(
                metric_key=key,
                metric_label=label,
                metric_value_raw=raw,
                metric_value_num=value,
                source_url=source_url,
            )
        )
    return metrics


def parse_info_bourse_top_products(
    html: str | bytes,
    *,
    base_url: str,
    source_url: str,
) -> list[BourseTopProduct]:
    """Parse top-demand / top-volume products from ``/info-bourse``.

    Args:
        html: Page HTML.
        base_url: Origin for link resolution.
        source_url: Absolute page URL.

    Returns:
        list[BourseTopProduct]: Top product rows.
    """
    soup = parse_html(html)
    tables = soup.find_all("table")
    if len(tables) < 2:
        return []
    table = tables[1]
    rows = table.find_all("tr")
    tops: list[BourseTopProduct] = []
    # Header structure: demand | volume columns side by side.
    for tr in rows:
        if not isinstance(tr, Tag):
            continue
        cells = tr.find_all("td", recursive=False)
        if len(cells) < 4:
            continue
        # pair-wise: (name, amount) x2
        pairs = (("demand", cells[0], cells[1]), ("volume", cells[2], cells[3]))
        for rank_list, name_cell, amount_cell in pairs:
            name_a = name_cell.select_one("a")
            name = clean_text(name_a) if name_a else clean_text(name_cell)
            if not name or name in {"کالا", "بیشترین تقاضا", "بیشترین حجم معامله"}:
                continue
            href = str(name_a.get("href") if name_a else "")
            amount_raw = clean_text(amount_cell)
            if not amount_raw or amount_raw in {"مقدار (تن)"}:
                continue
            tops.append(
                BourseTopProduct(
                    rank_list=rank_list,
                    product_name=name,
                    category_id=_CAT_ID_RE.search(href).group(1) if _CAT_ID_RE.search(href) else "",
                    category_url=absolute_url(base_url, href),
                    amount_tons=amount_raw,
                    amount_value=parse_int_price(amount_raw),
                    source_url=source_url,
                )
            )
    return tops
