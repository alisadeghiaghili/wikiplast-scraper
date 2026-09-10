"""Lightweight public snapshot extract (prices + bourse + content + media).

This section intentionally skips full company/category crawls and detail
pages so a complete public snapshot stays short and polite.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from wikiplast.adapters.coverage import build_coverage_report, write_coverage_report
from wikiplast.adapters.http_client import HttpClient
from wikiplast.adapters.storage import persist_section
from wikiplast.extractors.bourse import (
    DEAL_FIELDS,
    OFFER_FIELDS,
    extract_deals,
    extract_offers,
)
from wikiplast.extractors.content import CONTENT_FIELDS, FEED_FIELDS, extract_feeds, extract_news
from wikiplast.extractors.media import run_media
from wikiplast.extractors.price_sections import (
    PRICE_FIELDS,
    extract_archive_prices,
    extract_market_prices,
    extract_npc_prices,
)


def _rows(items: list) -> list[dict]:  # type: ignore[type-arg]
    return [item.to_row() for item in items]


def run_public_snapshot(
    client: HttpClient,
    data_dir: Path,
    *,
    news_pages: int = 3,
) -> dict[str, dict[str, Path]]:
    """Run a polite public snapshot of the highest-value tables.

    Includes NPC prices, archive prices, market prices (gated cells),
    deals, offers, a short news listing, RSS, and media catalogs.

    Args:
        client: HTTP client.
        data_dir: Output root.
        news_pages: Page cap for the news listing in this snapshot.

    Returns:
        dict[str, dict[str, Path]]: Section name to artifact paths.
    """
    started = datetime.now(UTC).isoformat()
    artifacts: dict[str, dict[str, Path]] = {}
    row_counts: dict[str, int] = {}

    npc = extract_npc_prices(client)
    artifacts["npc_prices"] = persist_section(
        _rows(npc), data_dir=data_dir, name="npc_prices", fieldnames=list(PRICE_FIELDS)
    )
    row_counts["npc_prices"] = len(npc)

    archive = extract_archive_prices(client)
    artifacts["archive_prices"] = persist_section(
        _rows(archive),
        data_dir=data_dir,
        name="archive_prices",
        fieldnames=list(PRICE_FIELDS),
    )
    row_counts["archive_prices"] = len(archive)

    market = extract_market_prices(client)
    artifacts["market_prices"] = persist_section(
        _rows(market),
        data_dir=data_dir,
        name="market_prices",
        fieldnames=list(PRICE_FIELDS),
    )
    row_counts["market_prices"] = len(market)

    deals = extract_deals(client)
    artifacts["bourse_deals"] = persist_section(
        _rows(deals), data_dir=data_dir, name="bourse_deals", fieldnames=list(DEAL_FIELDS)
    )
    row_counts["bourse_deals"] = len(deals)

    offers = extract_offers(client)
    artifacts["bourse_offers"] = persist_section(
        _rows(offers),
        data_dir=data_dir,
        name="bourse_offers",
        fieldnames=list(OFFER_FIELDS),
    )
    row_counts["bourse_offers"] = len(offers)

    news = extract_news(client, max_pages=news_pages)
    artifacts["news"] = persist_section(
        _rows(news), data_dir=data_dir, name="news", fieldnames=list(CONTENT_FIELDS)
    )
    row_counts["news"] = len(news)

    feeds = extract_feeds(client)
    artifacts["feed_entries"] = persist_section(
        _rows(feeds), data_dir=data_dir, name="feed_entries", fieldnames=list(FEED_FIELDS)
    )
    row_counts["feed_entries"] = len(feeds)

    media_artifacts = run_media(client, data_dir)
    artifacts.update(media_artifacts)

    report = build_coverage_report(
        tables=row_counts,
        started_at=started,
        extra={"section": "public_snapshot", "news_pages": news_pages},
    )
    artifacts["_coverage"] = {
        "coverage": write_coverage_report(report, data_dir / "coverage.json")
    }
    return artifacts
