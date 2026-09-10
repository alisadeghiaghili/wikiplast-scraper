"""Network smoke tests — opt-in only (`pytest -m network`)."""

from __future__ import annotations

import pytest

from wikiplast.adapters.http_client import HttpClient
from wikiplast.config import Settings
from wikiplast.domain.prices import parse_price_table
from wikiplast.extractors.price_sections import extract_npc_prices


@pytest.mark.network
def test_npc_prices_live_smoke() -> None:
    """Live smoke: NPC page returns parseable public price rows."""
    settings = Settings(min_delay=1.0, max_delay=2.0, max_retries=2)
    with HttpClient(settings) as client:
        html = client.get("/npc-prices")
        rows = parse_price_table(
            html,
            source="npc",
            source_url="https://wikiplast.ir/npc-prices",
        )
    assert len(rows) >= 10
    assert any(r.price_value for r in rows)


@pytest.mark.network
def test_npc_extractor_live_smoke() -> None:
    """Live smoke: extractor returns observations without raising."""
    settings = Settings(min_delay=1.0, max_delay=2.0, max_retries=2)
    with HttpClient(settings) as client:
        rows = extract_npc_prices(client)
    assert rows
    assert rows[0].source == "npc"
