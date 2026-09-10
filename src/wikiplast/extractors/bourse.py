"""Bourse section extractors and persistence."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, TypeVar

from wikiplast.adapters.http_client import HttpClient
from wikiplast.adapters.storage import persist_section
from wikiplast.domain.bourse import (
    parse_bourse_deals,
    parse_bourse_offers,
    parse_byab_status,
    parse_company_quotas,
    parse_info_bourse_metrics,
    parse_info_bourse_top_products,
    parse_price_comparisons,
)
from wikiplast.exceptions import HttpError

T = TypeVar("T")

DEALS_PATH = "/deals"
OFFERS_PATH = "/offers"
BYAB_PATH = "/byab"
BEHINYAB_PATH = "/behinyab"
BEHIN_PAGE_PATH = "/behin.php"
COMPARE_PATH = "/compare"
INFO_BOURSE_PATH = "/info-bourse"

DEAL_FIELDS = (
    "polymer_category",
    "grade_name",
    "avg_price_rial",
    "supply_tons",
    "traded_tons",
    "contract_type",
    "as_of_iso",
    "source_url",
)
OFFER_FIELDS = (
    "polymer_category",
    "grade_name",
    "base_price_rial",
    "base_qty",
    "max_increase",
    "as_of_iso",
    "source_url",
)
BYAB_FIELDS = (
    "product_name",
    "category_id",
    "category_url",
    "status",
    "monthly_purchase_cap",
    "valid_from",
    "diagram_url",
    "as_of_iso",
    "source_url",
)
QUOTA_FIELDS = (
    "row_number",
    "unit_name",
    "national_code",
    "material_name",
    "material_code",
    "annual_performance",
    "calculated_quota",
    "page",
    "source_url",
)
COMPARE_FIELDS = (
    "polymer_category",
    "grade_name",
    "grade_id",
    "grade_url",
    "base_price_prev",
    "base_price_current",
    "change_abs",
    "change_pct",
    "global_usd_per_ton",
    "source_url",
)
METRIC_FIELDS = (
    "metric_key",
    "metric_label",
    "metric_value_raw",
    "metric_value_num",
    "source_url",
)
TOP_FIELDS = (
    "rank_list",
    "product_name",
    "category_id",
    "category_url",
    "amount_tons",
    "amount_value",
    "source_url",
)


def _rows(items: Sequence[Any]) -> list[dict[str, Any]]:
    return [item.to_row() for item in items]


def extract_deals(client: HttpClient) -> list[Any]:
    """Extract ``/deals`` rows.

    Args:
        client: HTTP client.

    Returns:
        list: Parsed deals.
    """
    html = client.get(DEALS_PATH)
    url = client.settings.base_url.rstrip("/") + DEALS_PATH
    return parse_bourse_deals(html, base_url=client.settings.base_url, source_url=url)


def extract_offers(client: HttpClient) -> list[Any]:
    """Extract ``/offers`` rows.

    Args:
        client: HTTP client.

    Returns:
        list: Parsed offers.
    """
    html = client.get(OFFERS_PATH)
    url = client.settings.base_url.rstrip("/") + OFFERS_PATH
    return parse_bourse_offers(html, base_url=client.settings.base_url, source_url=url)


def extract_byab(client: HttpClient) -> list[Any]:
    """Extract ``/byab`` status rows.

    Args:
        client: HTTP client.

    Returns:
        list: Parsed status rows.
    """
    html = client.get(BYAB_PATH)
    url = client.settings.base_url.rstrip("/") + BYAB_PATH
    return parse_byab_status(html, base_url=client.settings.base_url, source_url=url)


def extract_company_quotas(
    client: HttpClient,
    *,
    max_pages: int = 10,
) -> list[Any]:
    """Extract company quotas from ``/behinyab`` and ``/behin.php`` pages.

    Args:
        client: HTTP client.
        max_pages: Hard cap on ``/behin.php?page=N`` pages.

    Returns:
        list: Quota rows across pages.
    """
    collected: list[Any] = []
    # First page via pretty path.
    html = client.get(BEHINYAB_PATH)
    url = client.settings.base_url.rstrip("/") + BEHINYAB_PATH
    collected.extend(
        parse_company_quotas(
            html, base_url=client.settings.base_url, source_url=url, page=1
        )
    )
    seen_keys: set[tuple[str, str, str]] = {
        (q.unit_name, q.national_code, q.material_code) for q in collected
    }

    for page in range(2, max_pages + 1):
        path = f"{BEHIN_PAGE_PATH}?comp=&meli=&mat=&stock=0&page={page}"
        try:
            html = client.get(path)
        except HttpError as exc:
            if exc.status_code in {404, 410}:
                break
            raise
        source_url = client.settings.base_url.rstrip("/") + path
        page_rows = parse_company_quotas(
            html, base_url=client.settings.base_url, source_url=source_url, page=page
        )
        new_rows = []
        for row in page_rows:
            key = (row.unit_name, row.national_code, row.material_code)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            new_rows.append(row)
        if not new_rows:
            break
        collected.extend(new_rows)
    return collected


def extract_comparisons(client: HttpClient) -> list[Any]:
    """Extract ``/compare`` base-price comparison rows.

    Args:
        client: HTTP client.

    Returns:
        list: Parsed comparison rows.
    """
    html = client.get(COMPARE_PATH)
    url = client.settings.base_url.rstrip("/") + COMPARE_PATH
    return parse_price_comparisons(html, base_url=client.settings.base_url, source_url=url)


def extract_info_bourse(client: HttpClient) -> tuple[list[Any], list[Any]]:
    """Extract infographic metrics and top products from ``/info-bourse``.

    Args:
        client: HTTP client.

    Returns:
        tuple: ``(metrics, top_products)``.
    """
    html = client.get(INFO_BOURSE_PATH)
    url = client.settings.base_url.rstrip("/") + INFO_BOURSE_PATH
    metrics = parse_info_bourse_metrics(html, source_url=url)
    tops = parse_info_bourse_top_products(
        html, base_url=client.settings.base_url, source_url=url
    )
    return metrics, tops


def run_bourse(
    client: HttpClient,
    data_dir: Path,
    *,
    max_quota_pages: int = 10,
) -> dict[str, dict[str, Path]]:
    """Run all bourse extractors and persist artifacts.

    Args:
        client: HTTP client.
        data_dir: Output root.
        max_quota_pages: Cap for company quota pagination.

    Returns:
        dict[str, dict[str, Path]]: Section name to artifact paths.
    """
    artifacts: dict[str, dict[str, Path]] = {}

    deals = extract_deals(client)
    artifacts["bourse_deals"] = persist_section(
        _rows(deals), data_dir=data_dir, name="bourse_deals", fieldnames=list(DEAL_FIELDS)
    )

    offers = extract_offers(client)
    artifacts["bourse_offers"] = persist_section(
        _rows(offers), data_dir=data_dir, name="bourse_offers", fieldnames=list(OFFER_FIELDS)
    )

    byab = extract_byab(client)
    artifacts["byab_status"] = persist_section(
        _rows(byab), data_dir=data_dir, name="byab_status", fieldnames=list(BYAB_FIELDS)
    )

    quotas = extract_company_quotas(client, max_pages=max_quota_pages)
    artifacts["company_quotas"] = persist_section(
        _rows(quotas), data_dir=data_dir, name="company_quotas", fieldnames=list(QUOTA_FIELDS)
    )

    comparisons = extract_comparisons(client)
    artifacts["price_comparisons"] = persist_section(
        _rows(comparisons),
        data_dir=data_dir,
        name="price_comparisons",
        fieldnames=list(COMPARE_FIELDS),
    )

    metrics, tops = extract_info_bourse(client)
    artifacts["bourse_metrics"] = persist_section(
        _rows(metrics), data_dir=data_dir, name="bourse_metrics", fieldnames=list(METRIC_FIELDS)
    )
    artifacts["bourse_top_products"] = persist_section(
        _rows(tops),
        data_dir=data_dir,
        name="bourse_top_products",
        fieldnames=list(TOP_FIELDS),
    )
    return artifacts
