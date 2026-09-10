"""Unit tests for parsing helpers."""

from __future__ import annotations

from wikiplast.domain.html_parsing import absolute_url, parse_int_price


def test_parse_int_price_variants() -> None:
    """Comma prices, dashes, and junk parse correctly."""
    assert parse_int_price("192,000") == 192000
    assert parse_int_price("1,368,576") == 1368576
    assert parse_int_price("-") is None
    assert parse_int_price("") is None
    assert parse_int_price(None) is None
    assert parse_int_price("قیمت") is None


def test_absolute_url_resolves_relative_and_rejects_javascript() -> None:
    """Relative hrefs resolve; javascript/mailto/empty become empty."""
    base = "https://wikiplast.ir"
    assert absolute_url(base, "/c1120") == "https://wikiplast.ir/c1120"
    assert absolute_url(base, "c1120") == "https://wikiplast.ir/c1120"
    assert absolute_url(base, "javascript:void(0)") == ""
    assert absolute_url(base, "") == ""
    assert absolute_url(base, "https://example.com/x") == "https://example.com/x"
