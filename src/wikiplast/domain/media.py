"""Parsers for media and video listings."""

from __future__ import annotations

import re
from collections.abc import Iterable

from bs4 import Tag

from wikiplast.domain.html_parsing import absolute_url, clean_text, parse_html
from wikiplast.models.media import MediaItem, VideoItem

_MEDIA_KEY_RE = re.compile(r"^/media/([A-Za-z0-9_-]+)$")
_VIDEO_ID_RE = re.compile(r"^/videos/(\d+)")


def parse_media_items(
    html: str | bytes,
    *,
    base_url: str,
    source_url: str,
) -> list[MediaItem]:
    """Parse ``/media/{slug}`` cards from the multimedia listing.

    Args:
        html: Page HTML.
        base_url: Origin for absolute URLs.
        source_url: Listing URL stamped on rows.

    Returns:
        list[MediaItem]: Unique media items in document order.
    """
    soup = parse_html(html)
    items: list[MediaItem] = []
    seen: set[str] = set()
    for anchor in soup.select("a[href^='/media/']"):
        if not isinstance(anchor, Tag):
            continue
        href = str(anchor.get("href") or "").split("?")[0].rstrip("/")
        match = _MEDIA_KEY_RE.match(href)
        if not match:
            continue
        key = match.group(1)
        if key in seen:
            continue
        heading = anchor.select_one("h3") or anchor.select_one("h2")
        title = clean_text(heading) if heading else clean_text(anchor)
        if not title or len(title) < 3:
            continue
        img = anchor.select_one("img")
        seen.add(key)
        items.append(
            MediaItem(
                media_key=key,
                title=title[:200],
                url=absolute_url(base_url, href),
                image_url=absolute_url(base_url, str(img.get("src") if img else "")),
                source_url=source_url,
            )
        )
    return items


def parse_video_items(
    html: str | bytes,
    *,
    base_url: str,
    source_url: str,
) -> list[VideoItem]:
    """Parse ``/videos/{id}`` cards from the TV listing.

    Args:
        html: Page HTML.
        base_url: Origin for absolute URLs.
        source_url: Listing URL stamped on rows.

    Returns:
        list[VideoItem]: Unique video items in document order.
    """
    soup = parse_html(html)
    items: list[VideoItem] = []
    seen: set[str] = set()
    for anchor in soup.select("a[href*='/videos/']"):
        if not isinstance(anchor, Tag):
            continue
        href = str(anchor.get("href") or "")
        match = _VIDEO_ID_RE.match(href.split("?")[0])
        if not match:
            continue
        video_id = match.group(1)
        if video_id in seen:
            continue
        heading = anchor.select_one("h3") or anchor.select_one("h2")
        title = clean_text(heading) if heading else clean_text(anchor)
        if not title or len(title) < 3:
            continue
        img = anchor.select_one("img")
        seen.add(video_id)
        items.append(
            VideoItem(
                video_id=video_id,
                title=title[:200],
                url=absolute_url(base_url, href.split("?")[0]),
                image_url=absolute_url(base_url, str(img.get("src") if img else "")),
                source_url=source_url,
            )
        )
    return items


def dedupe_media(items: Iterable[MediaItem]) -> list[MediaItem]:
    """Deduplicate media items by key.

    Args:
        items: Iterable of media items.

    Returns:
        list[MediaItem]: Unique items.
    """
    seen: set[str] = set()
    unique: list[MediaItem] = []
    for item in items:
        if not item.media_key or item.media_key in seen:
            continue
        seen.add(item.media_key)
        unique.append(item)
    return unique


def dedupe_videos(items: Iterable[VideoItem]) -> list[VideoItem]:
    """Deduplicate video items by id.

    Args:
        items: Iterable of video items.

    Returns:
        list[VideoItem]: Unique items.
    """
    seen: set[str] = set()
    unique: list[VideoItem] = []
    for item in items:
        if not item.video_id or item.video_id in seen:
            continue
        seen.add(item.video_id)
        unique.append(item)
    return unique
