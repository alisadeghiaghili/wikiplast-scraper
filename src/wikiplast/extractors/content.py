"""Content section extractors (news, articles, events, ads, feeds, people)."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, TypeVar

from wikiplast.adapters.http_client import HttpClient
from wikiplast.adapters.listing_resume import ListingCheckpoint
from wikiplast.adapters.storage import persist_section
from wikiplast.domain.content import (
    ARTICLE_ID_RE,
    NEWS_ID_RE,
    dedupe_ads,
    dedupe_content,
    parse_ads,
    parse_content_links,
    parse_manager_profiles,
    parse_rss_feed,
    parse_top_companies,
)
from wikiplast.exceptions import HttpError
from wikiplast.models.content import ContentItem

T = TypeVar("T")

NEWS_PATH = "/archive-news"
ARTICLES_PATH = "/articles"
EVENTS_PATH = "/events"
ADS_PATH = "/ads"
STAR_ADS_PATH = "/starads"
TOPCO_PATH = "/topco"
WIKIBOSS_PATH = "/wikiboss"
FEEDS_PATH = "/feeds"

CONTENT_FIELDS = (
    "kind",
    "item_id",
    "title",
    "url",
    "image_url",
    "published_text",
    "source_url",
)
AD_FIELDS = (
    "ad_id",
    "title",
    "url",
    "image_url",
    "is_featured",
    "category_path",
    "source_url",
)
TOPCO_FIELDS = (
    "company_id",
    "name",
    "url",
    "category_label",
    "category_url",
    "logo_url",
    "source_url",
)
BOSS_FIELDS = (
    "profile_id",
    "name",
    "birthplace",
    "url",
    "source_url",
)
FEED_FIELDS = (
    "title",
    "link",
    "description",
    "published_text",
)


def _rows(items: Sequence[Any]) -> list[dict[str, Any]]:
    return [item.to_row() for item in items]


def extract_paginated_content(
    client: HttpClient,
    *,
    base_path: str,
    kind: str,
    max_pages: int = 20,
    listing_ckpt: ListingCheckpoint | None = None,
) -> list[ContentItem]:
    """Extract paginated content listings with early-stop.

    Stops when a page yields no new item ids. When a listing checkpoint is
    provided, pages already marked done are skipped (resume).

    Args:
        client: HTTP client.
        base_path: Listing path such as ``/archive-news``.
        kind: Stored kind label.
        max_pages: Hard page cap.
        listing_ckpt: Optional page-level resume store.

    Returns:
        list[ContentItem]: Deduplicated items from pages processed this run.
    """
    patterns = (NEWS_ID_RE, ARTICLE_ID_RE)
    collected: list[ContentItem] = []
    for page in range(1, max_pages + 1):
        path = base_path if page == 1 else f"{base_path}/{page}"
        if listing_ckpt is not None and listing_ckpt.is_page_done(path):
            continue
        try:
            html = client.get(path)
        except HttpError as exc:
            if exc.status_code in {404, 410}:
                break
            raise
        source_url = client.settings.base_url.rstrip("/") + path
        page_items = parse_content_links(
            html,
            base_url=client.settings.base_url,
            source_url=source_url,
            kind=kind,
            id_patterns=patterns,
        )
        before = len(dedupe_content(collected))
        collected.extend(page_items)
        after = len(dedupe_content(collected))
        if listing_ckpt is not None:
            listing_ckpt.mark_page_done(path)
        if after == before and page > 1:
            break
    if listing_ckpt is not None:
        listing_ckpt.save()
    return dedupe_content(collected)


def extract_news(
    client: HttpClient,
    *,
    max_pages: int = 20,
    listing_ckpt: ListingCheckpoint | None = None,
) -> list[ContentItem]:
    """Extract news listings from ``/archive-news``.

    Args:
        client: HTTP client.
        max_pages: Hard page cap.
        listing_ckpt: Optional page-level resume store.

    Returns:
        list[ContentItem]: News items.
    """
    return extract_paginated_content(
        client,
        base_path=NEWS_PATH,
        kind="news",
        max_pages=max_pages,
        listing_ckpt=listing_ckpt,
    )


def extract_articles(
    client: HttpClient,
    *,
    max_pages: int = 20,
    listing_ckpt: ListingCheckpoint | None = None,
) -> list[ContentItem]:
    """Extract article listings from ``/articles``.

    Args:
        client: HTTP client.
        max_pages: Hard page cap.
        listing_ckpt: Optional page-level resume store.

    Returns:
        list[ContentItem]: Article items.
    """
    return extract_paginated_content(
        client,
        base_path=ARTICLES_PATH,
        kind="article",
        max_pages=max_pages,
        listing_ckpt=listing_ckpt,
    )


def extract_events(
    client: HttpClient,
    *,
    max_pages: int = 20,
    listing_ckpt: ListingCheckpoint | None = None,
) -> list[ContentItem]:
    """Extract event listings from ``/events``.

    Args:
        client: HTTP client.
        max_pages: Hard page cap.
        listing_ckpt: Optional page-level resume store.

    Returns:
        list[ContentItem]: Event items.
    """
    return extract_paginated_content(
        client,
        base_path=EVENTS_PATH,
        kind="event",
        max_pages=max_pages,
        listing_ckpt=listing_ckpt,
    )


def extract_honors(client: HttpClient) -> list[ContentItem]:
    """Extract honor gallery entries from ``/honors``.

    Args:
        client: HTTP client.

    Returns:
        list[ContentItem]: Honor items.
    """
    html = client.get("/honors")
    url = client.settings.base_url.rstrip("/") + "/honors"
    return parse_content_links(
        html,
        base_url=client.settings.base_url,
        source_url=url,
        kind="honor",
        id_patterns=(NEWS_ID_RE,),
    )


def extract_ads(client: HttpClient, *, max_pages: int = 20) -> list[Any]:
    """Extract classified ads from ``/ads`` and featured ``/starads``.

    Never requests ``/siteads/`` (robots disallowed).

    Args:
        client: HTTP client.
        max_pages: Hard page cap for the main ads list.

    Returns:
        list: Deduplicated ads, featured flag preserved.
    """
    collected: list[Any] = []

    html = client.get(STAR_ADS_PATH)
    star_url = client.settings.base_url.rstrip("/") + STAR_ADS_PATH
    collected.extend(
        parse_ads(
            html,
            base_url=client.settings.base_url,
            source_url=star_url,
            featured=True,
        )
    )

    for page in range(1, max_pages + 1):
        path = ADS_PATH if page == 1 else f"/ads/-1/{page}"
        try:
            html = client.get(path)
        except HttpError as exc:
            if exc.status_code in {404, 410}:
                break
            raise
        source_url = client.settings.base_url.rstrip("/") + path
        page_ads = parse_ads(
            html,
            base_url=client.settings.base_url,
            source_url=source_url,
            featured=False,
        )
        before = len(dedupe_ads(collected))
        collected.extend(page_ads)
        after = len(dedupe_ads(collected))
        if after == before:
            break
    return dedupe_ads(collected)


def extract_top_companies(client: HttpClient, *, max_pages: int = 10) -> list[Any]:
    """Extract featured companies from ``/topco`` pages.

    Args:
        client: HTTP client.
        max_pages: Hard page cap.

    Returns:
        list: Featured companies.
    """
    collected: list[Any] = []
    seen: set[str] = set()
    for page in range(1, max_pages + 1):
        path = TOPCO_PATH if page == 1 else f"{TOPCO_PATH}/{page}"
        try:
            html = client.get(path)
        except HttpError as exc:
            if exc.status_code in {404, 410}:
                break
            raise
        source_url = client.settings.base_url.rstrip("/") + path
        page_rows = parse_top_companies(
            html, base_url=client.settings.base_url, source_url=source_url
        )
        new_rows = []
        for row in page_rows:
            if row.company_id in seen:
                continue
            seen.add(row.company_id)
            new_rows.append(row)
        if not new_rows:
            break
        collected.extend(new_rows)
    return collected


def extract_manager_profiles(client: HttpClient, *, max_pages: int = 10) -> list[Any]:
    """Extract manager profiles from ``/wikiboss`` pages.

    Args:
        client: HTTP client.
        max_pages: Hard page cap.

    Returns:
        list: Manager profiles.
    """
    collected: list[Any] = []
    seen: set[str] = set()
    for page in range(1, max_pages + 1):
        path = WIKIBOSS_PATH if page == 1 else f"{WIKIBOSS_PATH}/{page}"
        try:
            html = client.get(path)
        except HttpError as exc:
            if exc.status_code in {404, 410}:
                break
            raise
        source_url = client.settings.base_url.rstrip("/") + path
        page_rows = parse_manager_profiles(
            html, base_url=client.settings.base_url, source_url=source_url
        )
        new_rows = []
        for row in page_rows:
            if row.profile_id in seen:
                continue
            seen.add(row.profile_id)
            new_rows.append(row)
        if not new_rows:
            break
        collected.extend(new_rows)
    return collected


def extract_feeds(client: HttpClient) -> list[Any]:
    """Extract RSS items from ``/feeds``.

    Args:
        client: HTTP client.

    Returns:
        list: Feed entries.
    """
    # RSS may declare XML encoding; fetch text then parse as UTF-8 bytes.
    html = client.get(FEEDS_PATH)
    return parse_rss_feed(html.encode("utf-8") if isinstance(html, str) else html)


def run_content(
    client: HttpClient,
    data_dir: Path,
    *,
    max_list_pages: int = 20,
    resume_listings: bool = False,
) -> dict[str, dict[str, Path]]:
    """Run content/community extractors and persist artifacts.

    Args:
        client: HTTP client.
        data_dir: Output root.
        max_list_pages: Page cap for paginated listings.
        resume_listings: Skip listing pages already recorded in checkpoints.

    Returns:
        dict[str, dict[str, Path]]: Section name to artifact paths.
    """
    artifacts: dict[str, dict[str, Path]] = {}
    ckpt_dir = data_dir / "checkpoints"

    news_ckpt = (
        ListingCheckpoint(ckpt_dir / "news_pages.json", section="news_pages", resume=True)
        if resume_listings
        else None
    )
    news = extract_news(client, max_pages=max_list_pages, listing_ckpt=news_ckpt)
    artifacts["news"] = persist_section(
        _rows(news), data_dir=data_dir, name="news", fieldnames=list(CONTENT_FIELDS)
    )

    article_ckpt = (
        ListingCheckpoint(
            ckpt_dir / "article_pages.json", section="article_pages", resume=True
        )
        if resume_listings
        else None
    )
    articles = extract_articles(
        client, max_pages=max_list_pages, listing_ckpt=article_ckpt
    )
    artifacts["articles"] = persist_section(
        _rows(articles), data_dir=data_dir, name="articles", fieldnames=list(CONTENT_FIELDS)
    )

    event_ckpt = (
        ListingCheckpoint(ckpt_dir / "event_pages.json", section="event_pages", resume=True)
        if resume_listings
        else None
    )
    events = extract_events(client, max_pages=max_list_pages, listing_ckpt=event_ckpt)
    artifacts["events"] = persist_section(
        _rows(events), data_dir=data_dir, name="events", fieldnames=list(CONTENT_FIELDS)
    )

    honors = extract_honors(client)
    artifacts["honors"] = persist_section(
        _rows(honors), data_dir=data_dir, name="honors", fieldnames=list(CONTENT_FIELDS)
    )

    ads = extract_ads(client, max_pages=max_list_pages)
    artifacts["classified_ads"] = persist_section(
        _rows(ads), data_dir=data_dir, name="classified_ads", fieldnames=list(AD_FIELDS)
    )

    topco = extract_top_companies(client, max_pages=10)
    artifacts["featured_companies"] = persist_section(
        _rows(topco),
        data_dir=data_dir,
        name="featured_companies",
        fieldnames=list(TOPCO_FIELDS),
    )

    bosses = extract_manager_profiles(client, max_pages=10)
    artifacts["manager_profiles"] = persist_section(
        _rows(bosses),
        data_dir=data_dir,
        name="manager_profiles",
        fieldnames=list(BOSS_FIELDS),
    )

    feeds = extract_feeds(client)
    artifacts["feed_entries"] = persist_section(
        _rows(feeds), data_dir=data_dir, name="feed_entries", fieldnames=list(FEED_FIELDS)
    )
    return artifacts
