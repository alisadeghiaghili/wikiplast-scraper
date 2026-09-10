"""Unit tests for bourse parsers."""

from __future__ import annotations

from pathlib import Path

from wikiplast.domain.bourse import (
    parse_bourse_deals,
    parse_bourse_offers,
    parse_byab_status,
    parse_company_quotas,
    parse_info_bourse_metrics,
    parse_info_bourse_top_products,
    parse_price_comparisons,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "html"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_bourse_deals() -> None:
    """Deals rows capture category, price, volumes; ads and contract notes skip."""
    html = _load("deals.html")
    deals = parse_bourse_deals(
        html, base_url="https://wikiplast.ir", source_url="https://wikiplast.ir/deals"
    )
    assert len(deals) == 2
    first = deals[0]
    assert first.grade_name == "RP 120L-jam"
    assert first.avg_price_rial == 2_902_174
    assert first.supply_tons == 200
    assert first.traded_tons == 200
    assert first.polymer_category == "پلی پروپیلن گرید فیلم"
    assert first.as_of_iso == "1405-06-18"
    assert "نوع قرارداد" in second_contract(deals) or deals[1].grade_name == "HP 520H khomein"


def second_contract(deals: list) -> str:
    """Return contract text from the second deal row (test helper)."""
    return deals[1].contract_type


def test_parse_bourse_offers() -> None:
    """Offers rows capture base price and quantities."""
    html = _load("offers.html")
    offers = parse_bourse_offers(
        html, base_url="https://wikiplast.ir", source_url="https://wikiplast.ir/offers"
    )
    assert len(offers) == 2
    assert offers[0].grade_name == "5000S Jam"
    assert offers[0].base_price_rial == 1_716_385
    assert offers[0].base_qty == 44
    assert offers[0].max_increase == 0
    assert offers[0].polymer_category == "پلی اتیلن سنگین اکستروژن"
    assert offers[0].as_of_iso == "1405-06-21"


def test_parse_byab_status() -> None:
    """Byab table exposes status, cap, valid-from, diagram link."""
    html = _load("byab.html")
    rows = parse_byab_status(
        html, base_url="https://wikiplast.ir", source_url="https://wikiplast.ir/byab"
    )
    assert len(rows) == 2
    gpps = rows[0]
    assert gpps.product_name.startswith("پلی استایرن")
    assert gpps.category_id == "82"
    assert gpps.status == "غیر بهین یاب"
    assert gpps.monthly_purchase_cap == "-"
    assert gpps.diagram_url.endswith("/diagram/3/82")
    assert gpps.as_of_iso == "1405-04-16"
    assert rows[1].status == "بهین یاب"
    assert rows[1].monthly_purchase_cap == "500"


def test_parse_company_quotas() -> None:
    """Quota table rows keep unit, national code, material, quota."""
    html = _load("behinyab.html")
    rows = parse_company_quotas(
        html,
        base_url="https://wikiplast.ir",
        source_url="https://wikiplast.ir/behinyab",
        page=1,
    )
    assert len(rows) == 2
    assert rows[0].unit_name == "نورایر باباخانی"
    assert rows[0].national_code == "39211169"
    assert rows[0].material_code == "333090"
    assert rows[0].calculated_quota == "22"
    assert rows[0].page == 1


def test_parse_price_comparisons() -> None:
    """Compare table yields grade rows with prev/current prices."""
    html = _load("compare.html")
    rows = parse_price_comparisons(
        html, base_url="https://wikiplast.ir", source_url="https://wikiplast.ir/compare"
    )
    assert len(rows) == 3
    assert all(r.grade_name != "قیمت مبنای دلار" for r in rows)
    first = rows[0]
    assert first.grade_id == "116"
    assert first.polymer_category == "پی وی سی - ( PVC)"
    assert first.base_price_prev == 1_485_547
    assert first.base_price_current == 1_713_979
    assert first.change_pct == "15.4%"
    assert rows[-1].polymer_category == "ABS"
    assert rows[-1].grade_id == "66"


def test_parse_info_bourse_metrics_and_tops() -> None:
    """Infographic metrics and top demand/volume products parse."""
    html = _load("info_bourse.html")
    url = "https://wikiplast.ir/info-bourse"
    metrics = parse_info_bourse_metrics(html, source_url=url)
    keys = {m.metric_key for m in metrics}
    assert "trade_volume_tons" in keys
    volume = next(m for m in metrics if m.metric_key == "trade_volume_tons")
    assert volume.metric_value_num == 96418
    offered = next(m for m in metrics if m.metric_key == "products_offered")
    assert offered.metric_value_num == 148

    tops = parse_info_bourse_top_products(
        html, base_url="https://wikiplast.ir", source_url=url
    )
    assert len(tops) == 4  # 2 ranks × demand+volume
    demand = [t for t in tops if t.rank_list == "demand"]
    volume_tops = [t for t in tops if t.rank_list == "volume"]
    assert demand[0].category_id == "131"
    assert demand[0].amount_value == 22412
    assert volume_tops[0].amount_value == 14652
