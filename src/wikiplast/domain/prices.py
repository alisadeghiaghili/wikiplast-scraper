"""Parsers for public price tables on wikiplast.ir.

These functions are pure: HTML in, models out. They never perform HTTP.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from bs4 import Tag

from wikiplast.domain.html_parsing import (
    absolute_url,
    clean_text,
    parse_html,
    parse_int_price,
)
from wikiplast.models.price import PriceObservation

# Persian long-form dates such as: یکشنبه ۱۵ شهریور ۱۴۰۵
_PERSIAN_MONTHS = {
    "فروردین": 1,
    "اردیبهشت": 2,
    "خرداد": 3,
    "تیر": 4,
    "تير": 4,
    "مرداد": 5,
    "شهریور": 6,
    "مهر": 7,
    "آبان": 8,
    "آذر": 9,
    "دی": 10,
    "دی‌": 10,
    "بهمن": 11,
    "اسفند": 12,
}

_PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

_DATE_RE = re.compile(
    r"(\d{1,2})\s+(" + "|".join(_PERSIAN_MONTHS) + r")\s+(\d{4})"
)
_AD_MARKER = "siteads"
_CATEGORY_GROUP_RE = re.compile(r"group\d+")


def to_iso_date(text: str | None) -> str | None:
    """Convert a Persian long date fragment to ISO ``YYYY-MM-DD``.

    Args:
        text: Page title or heading that may contain a Persian date.

    Returns:
        str | None: ISO date string, or ``None`` when no date is found.

    Examples:
        >>> to_iso_date("تاریخ یکشنبه ۱۵ شهریور ۱۴۰۵")
        '1405-06-15'
    """
    if not text:
        return None
    # Translate Persian/Arabic-Indic digits first so \d can match.
    normalized = text.translate(_PERSIAN_DIGITS)
    match = _DATE_RE.search(normalized)
    if not match:
        return None
    day = int(match.group(1))
    month = _PERSIAN_MONTHS[match.group(2)]
    year = int(match.group(3))
    if not (1 <= day <= 31 and 1 <= month <= 12 and 1300 <= year <= 1500):
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"


def _is_ad_row(cells: list[Tag]) -> bool:
    if len(cells) == 1:
        href = cells[0].find("a")
        if href is not None and _AD_MARKER in (href.get("href") or ""):
            return True
        joined = clean_text(cells[0])
        if "نمایشگاه" in joined or "تبلیغ" in joined:
            return True
    return False


def _row_category_classes(tr: Tag) -> str:
    classes = tr.get("class") or []
    for name in classes:
        if _CATEGORY_GROUP_RE.fullmatch(name):
            return name
    return ""


def parse_price_table(
    html: str | bytes,
    *,
    source: str,
    source_url: str,
    currency: str = "IRR",
) -> list[PriceObservation]:
    """Parse a wikiplast price table into observations.

    Handles the common layout: category header rows (single cell with
    colspan), a column header row (``گرید / قیمت / تولید کننده``), then
    data rows. Advertisement rows are skipped.

    Args:
        html: Raw HTML of the page.
        source: Logical source key stored on each observation.
        source_url: Absolute URL stored on each observation.
        currency: Currency code to stamp on rows.

    Returns:
        list[PriceObservation]: Parsed rows in document order. Empty list
        when no table exists (not an error — some pages are sparse).

    Examples:
        >>> rows = parse_price_table(
        ...     "<table><tr class='g86'><td colspan='4'>پی وی سی</td></tr>"
        ...     "<tr class='maincell g86'><td>گرید</td><td>قیمت</td><td>تولید کننده</td></tr>"
        ...     "<tr class='maintr g86'><td>PVC S65</td><td>192,000</td><td>اروند</td></tr>"
        ...     "</table>",
        ...     source="archive",
        ...     source_url="https://wikiplast.ir/prices",
        ... )
        >>> len(rows), rows[0].grade_name, rows[0].price_value
        (1, 'PVC S65', 192000)
    """
    soup = parse_html(html)
    table = soup.find("table")
    if table is None:
        return []
    title = soup.title.get_text(strip=True) if soup.title else ""
    as_of = to_iso_date(title)

    observations: list[PriceObservation] = []
    current_category = ""

    for tr in table.find_all("tr"):
        if not isinstance(tr, Tag):
            continue
        cells = [c for c in tr.find_all(["td", "th"], recursive=False) if isinstance(c, Tag)]
        if not cells:
            continue
        if _is_ad_row(cells):
            continue

        texts = [clean_text(c) for c in cells]

        # Category banner: single cell.
        if len(cells) == 1:
            if texts[0] and "مشاهده" not in texts[0]:
                current_category = texts[0]
            continue

        # Column header row.
        if texts and texts[0] == "گرید":
            continue

        # Prefer explicit 4-column layout: grade, (blank), price, producer
        # or 3-column: grade, price, producer.
        if len(cells) >= 3:
            grade = texts[0]
            # Some tables insert empty spacer cells.
            non_empty = [t for t in texts[1:] if t]
            if not grade or grade in {"گرید"}:
                continue
            if len(non_empty) >= 2:
                price_raw, producer = non_empty[0], non_empty[1]
            elif len(non_empty) == 1:
                price_raw, producer = non_empty[0], ""
            else:
                price_raw, producer = "", ""
            # Heuristic: if second non-empty is numeric-looking and third is text,
            # keep order grade/price/producer. If first non-empty is a producer-only
            # cell (no digits) and second is numeric, swap.
            if price_raw and not re.search(r"\d", price_raw) and re.search(r"\d", producer):
                price_raw, producer = producer, price_raw

            price_value = parse_int_price(price_raw)
            gated = price_value is None and bool(price_raw) and price_raw not in {"-", "—"}
            # Treat literal placeholder "قیمت" as gated.
            if price_raw.strip() in {"قیمت", "دریافت قیمت"}:
                gated = True
                price_value = None

            observations.append(
                PriceObservation(
                    source=source,
                    polymer_category=current_category,
                    grade_name=grade,
                    producer=producer,
                    price_raw=price_raw,
                    price_value=price_value,
                    currency=currency,
                    is_gated=gated,
                    as_of_date=as_of,
                    source_url=source_url,
                )
            )
    return observations


def parse_market_prices_matrix(
    html: str | bytes,
    *,
    source: str,
    source_url: str,
    currency: str = "IRR",
) -> list[PriceObservation]:
    """Parse ``/market-prices`` multi-day matrix into long-format observations.

    The live table has columns: grade, then one column per recent trading day,
    then a details link. Anonymous responses often show the word ``قیمت``
    instead of a number — those rows are marked ``is_gated=True``.

    Args:
        html: Raw HTML of ``/market-prices``.
        source: Logical source key.
        source_url: Absolute URL of the page.
        currency: Currency code to stamp.

    Returns:
        list[PriceObservation]: One observation per grade-day cell.
    """
    soup = parse_html(html)
    table = soup.find("table")
    if table is None:
        return []

    rows = table.find_all("tr")
    if not rows:
        return []

    header_cells = [clean_text(c) for c in rows[0].find_all(["th", "td"])]
    # Expected: گرید | day1 | day2 | ... | اطلاعات بیشتر
    day_labels = header_cells[1:-1] if len(header_cells) >= 3 else header_cells[1:]

    observations: list[PriceObservation] = []
    current_category = ""
    for tr in rows[1:]:
        if not isinstance(tr, Tag):
            continue
        cells = [c for c in tr.find_all("td", recursive=False) if isinstance(c, Tag)]
        if not cells:
            continue
        texts = [clean_text(c) for c in cells]
        if len(cells) == 1 and texts[0]:
            current_category = texts[0]
            continue
        if len(cells) < 2:
            continue
        grade = texts[0]
        if not grade or grade == "گرید":
            continue
        for index, day_label in enumerate(day_labels, start=1):
            if index >= len(texts):
                break
            raw = texts[index]
            if not raw:
                continue
            value = parse_int_price(raw)
            gated = value is None
            if raw in {"قیمت", "دریافت قیمت"}:
                gated = True
            observations.append(
                PriceObservation(
                    source=source,
                    polymer_category=current_category,
                    grade_name=grade,
                    producer="",
                    price_raw=raw,
                    price_value=value,
                    currency=currency,
                    is_gated=gated,
                    as_of_date=day_label or None,
                    source_url=source_url,
                )
            )
    return observations


def dedupe_observations(rows: Iterable[PriceObservation]) -> list[PriceObservation]:
    """Remove exact duplicate observations while preserving order.

    Args:
        rows: Iterable of observations.

    Returns:
        list[PriceObservation]: Unique rows.
    """
    seen: set[tuple[str, str, str, str, int | None]] = set()
    unique: list[PriceObservation] = []
    for row in rows:
        key = (
            row.source,
            row.polymer_category,
            row.grade_name,
            row.producer,
            row.price_value,
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def build_absolute(base_url: str, href: str | None) -> str:
    """Public re-export of absolute URL resolution for extractors.

    Args:
        base_url: Site origin.
        href: Raw href attribute.

    Returns:
        str: Absolute URL or empty string.
    """
    return absolute_url(base_url, href)
