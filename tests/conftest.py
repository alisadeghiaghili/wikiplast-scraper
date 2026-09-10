"""Shared pytest fixtures for wikiplast tests."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures" / "html"


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the HTML fixtures directory.

    Returns:
        Path: Directory containing saved HTML snapshots.
    """
    return FIXTURES


@pytest.fixture
def npc_prices_html(fixtures_dir: Path) -> str:
    """Load the NPC prices fixture.

    Returns:
        str: Fixture HTML.
    """
    return (fixtures_dir / "npc_prices.html").read_text(encoding="utf-8")


@pytest.fixture
def archive_prices_html(fixtures_dir: Path) -> str:
    """Load the archive prices fixture.

    Returns:
        str: Fixture HTML.
    """
    return (fixtures_dir / "archive_prices.html").read_text(encoding="utf-8")


@pytest.fixture
def market_prices_html(fixtures_dir: Path) -> str:
    """Load the market prices fixture.

    Returns:
        str: Fixture HTML.
    """
    return (fixtures_dir / "market_prices.html").read_text(encoding="utf-8")


@pytest.fixture
def companies_html(fixtures_dir: Path) -> str:
    """Load the companies listing fixture.

    Returns:
        str: Fixture HTML.
    """
    return (fixtures_dir / "companies_list.html").read_text(encoding="utf-8")
