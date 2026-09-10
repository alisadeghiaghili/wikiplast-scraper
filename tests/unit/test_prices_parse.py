"""Unit tests for price table parsers."""

from __future__ import annotations

from wikiplast.domain.prices import (
    dedupe_observations,
    parse_market_prices_matrix,
    parse_price_table,
    to_iso_date,
)


def test_to_iso_date_parses_persian_title() -> None:
    """Persian long dates convert to ISO strings."""
    assert to_iso_date("تاریخ یکشنبه ۱۵ شهریور ۱۴۰۵") == "1405-06-15"
    assert to_iso_date("یکشنبه ۱ تير ۱۳۹۹") == "1399-04-01"
    assert to_iso_date("بدون تاریخ") is None


def test_parse_npc_prices_skips_ads_and_headers(npc_prices_html: str) -> None:
    """NPC table yields only real grade rows, no advertisement rows."""
    rows = parse_price_table(
        npc_prices_html,
        source="npc",
        source_url="https://wikiplast.ir/npc-prices",
    )
    assert len(rows) == 4
    grades = [r.grade_name for r in rows]
    assert "PVC S65 Abadan" in grades
    assert "ABS150 Tabriz" in grades
    assert all("نمایشگاه" not in r.grade_name for r in rows)
    assert rows[0].price_value == 1_368_576
    assert rows[0].producer == "آبادان"
    assert rows[0].polymer_category.startswith("پی وی سی")
    assert rows[0].as_of_date == "1405-06-15"
    assert rows[0].source == "npc"


def test_parse_npc_missing_price_is_none_not_zero(npc_prices_html: str) -> None:
    """Dash prices parse to None, not zero."""
    rows = parse_price_table(
        npc_prices_html,
        source="npc",
        source_url="https://wikiplast.ir/npc-prices",
    )
    dashed = [r for r in rows if r.price_raw == "-"]
    assert dashed
    assert all(r.price_value is None for r in dashed)
    assert all(r.is_gated is False for r in dashed)


def test_parse_archive_prices_spacer_cells(archive_prices_html: str) -> None:
    """Archive layout with blank spacer cells still yields grade/price/producer."""
    rows = parse_price_table(
        archive_prices_html,
        source="archive",
        source_url="https://wikiplast.ir/prices",
    )
    assert len(rows) == 4
    first = next(r for r in rows if r.grade_name == "PVC S65 Arvand")
    assert first.price_value == 192_000
    assert first.producer == "اروند"
    assert first.currency == "IRR"
    assert first.as_of_date == "1399-04-01"


def test_parse_market_prices_marks_gated(market_prices_html: str) -> None:
    """Anonymous market matrix placeholders are flagged gated."""
    rows = parse_market_prices_matrix(
        market_prices_html,
        source="market",
        source_url="https://wikiplast.ir/market-prices",
    )
    assert len(rows) == 4  # 2 grades × 2 days
    assert all(r.is_gated for r in rows)
    assert all(r.price_value is None for r in rows)
    assert rows[0].price_raw == "قیمت"
    assert rows[0].grade_name == "HBM 5510 Arya"


def test_dedupe_observations_removes_alias_duplicates(archive_prices_html: str) -> None:
    """Fetching /prices and /prices/codeime must not double rows."""
    a = parse_price_table(
        archive_prices_html,
        source="archive",
        source_url="https://wikiplast.ir/prices",
    )
    b = parse_price_table(
        archive_prices_html,
        source="archive",
        source_url="https://wikiplast.ir/prices/codeime",
    )
    merged = dedupe_observations([*a, *b])
    assert len(merged) == len(a)
