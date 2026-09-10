"""Price section extractors (npc, archive, market)."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from wikiplast.adapters.http_client import HttpClient
from wikiplast.adapters.storage import persist_section
from wikiplast.domain.prices import (
    dedupe_observations,
    parse_market_prices_matrix,
    parse_price_table,
)
from wikiplast.models.price import PriceObservation

NPC_PATH = "/npc-prices"
ARCHIVE_PATHS = ("/prices", "/prices/codeime")
MARKET_PATH = "/market-prices"

PRICE_FIELDS: tuple[str, ...] = (
    "source",
    "polymer_category",
    "grade_name",
    "producer",
    "price_raw",
    "price_value",
    "currency",
    "is_gated",
    "as_of_date",
    "source_url",
)


def _rows(observations: Sequence[PriceObservation]) -> list[dict[str, Any]]:
    return [o.to_row() for o in observations]


def extract_npc_prices(client: HttpClient) -> list[PriceObservation]:
    """Extract public NPC base petrochemical prices.

    Args:
        client: HTTP client bound to wikiplast.

    Returns:
        list[PriceObservation]: Deduplicated observations.
    """
    html = client.get(NPC_PATH)
    url = client.settings.base_url.rstrip("/") + NPC_PATH
    return dedupe_observations(parse_price_table(html, source="npc", source_url=url))


def extract_archive_prices(client: HttpClient) -> list[PriceObservation]:
    """Extract public archive market prices (``/prices``).

    ``/prices/codeime`` is an alias of the same table; both are fetched and
    deduplicated so a redirect/alias cannot inflate row counts.

    Args:
        client: HTTP client bound to wikiplast.

    Returns:
        list[PriceObservation]: Deduplicated observations.
    """
    collected: list[PriceObservation] = []
    for path in ARCHIVE_PATHS:
        html = client.get(path)
        url = client.settings.base_url.rstrip("/") + path
        collected.extend(parse_price_table(html, source="archive", source_url=url))
    return dedupe_observations(collected)


def extract_market_prices(client: HttpClient) -> list[PriceObservation]:
    """Extract ``/market-prices`` matrix cells.

    Anonymous sessions typically receive gated placeholders; those rows are
    kept with ``is_gated=True`` and ``price_value=None`` so schema coverage
    stays visible without pretending the numbers exist.

    Args:
        client: HTTP client bound to wikiplast.

    Returns:
        list[PriceObservation]: Deduplicated grade-day observations.
    """
    html = client.get(MARKET_PATH)
    url = client.settings.base_url.rstrip("/") + MARKET_PATH
    return dedupe_observations(parse_market_prices_matrix(html, source="market", source_url=url))


def run_all_prices(
    client: HttpClient,
    data_dir: Path,
) -> dict[str, dict[str, Path]]:
    """Run every public price extractor and persist artifacts.

    Args:
        client: HTTP client.
        data_dir: Output root directory.

    Returns:
        dict[str, dict[str, Path]]: Section name to artifact paths.
    """
    sections = {
        "npc_prices": extract_npc_prices(client),
        "archive_prices": extract_archive_prices(client),
        "market_prices": extract_market_prices(client),
    }
    artifacts: dict[str, dict[str, Path]] = {}
    for name, observations in sections.items():
        artifacts[name] = persist_section(
            _rows(observations),
            data_dir=data_dir,
            name=name,
            fieldnames=list(PRICE_FIELDS),
        )
    return artifacts
