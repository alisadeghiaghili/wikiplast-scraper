"""Unit tests for company card parsing and dedupe (v0.1 P0 fix)."""

from __future__ import annotations

from wikiplast.domain.companies import (
    company_counts_match_unique,
    dedupe_companies,
    extract_company_id,
    parse_company_cards,
)


def test_extract_company_id() -> None:
    """Profile hrefs yield stable numeric ids."""
    assert extract_company_id("/c1120") == "1120"
    assert extract_company_id("https://wikiplast.ir/c415") == "415"
    assert extract_company_id("/products/1") == ""


def test_parse_company_cards_fields(companies_html: str) -> None:
    """Visit cards expose name, contact, rating, verified flag."""
    cards = parse_company_cards(
        companies_html,
        base_url="https://wikiplast.ir",
        source_url="https://wikiplast.ir/companies",
        category="root",
    )
    assert len(cards) == 3
    first = cards[0]
    assert first.company_id == "1120"
    assert first.name == "کفش نیکان و گرانول"
    assert first.contact_person == "ناصر آقاجانی"
    assert first.verified is True
    assert first.rating == "51"
    assert first.url == "https://wikiplast.ir/c1120"
    assert cards[1].verified is False


def test_dedupe_companies_by_id(companies_html: str) -> None:
    """The same company_id appearing twice collapses to one row.

    This is the regression that made v0.1 companies.csv report 12950 rows
    for only 350 unique companies.
    """
    cards = parse_company_cards(
        companies_html,
        base_url="https://wikiplast.ir",
        source_url="https://wikiplast.ir/companies",
        category="root",
    )
    assert len(cards) == 3
    unique = dedupe_companies(cards)
    assert len(unique) == 2
    assert company_counts_match_unique(unique) is True
    ids = [c.company_id for c in unique]
    assert ids == ["1120", "415"]


def test_dedupe_prefers_first_category() -> None:
    """First occurrence wins when the same id appears under two categories."""
    from wikiplast.models.company import CompanyCard

    a = CompanyCard(
        company_id="1",
        name="A",
        url="https://wikiplast.ir/c1",
        contact_person="",
        website="",
        rating="",
        logo_url="",
        verified=False,
        category="first",
        source_url="u1",
    )
    b = CompanyCard(
        company_id="1",
        name="A",
        url="https://wikiplast.ir/c1",
        contact_person="",
        website="",
        rating="",
        logo_url="",
        verified=False,
        category="second",
        source_url="u2",
    )
    unique = dedupe_companies([a, b])
    assert len(unique) == 1
    assert unique[0].category == "first"
