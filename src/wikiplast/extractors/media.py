"""Media and TV extractors."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from wikiplast.adapters.http_client import HttpClient
from wikiplast.adapters.storage import persist_section
from wikiplast.domain.media import (
    dedupe_media,
    dedupe_videos,
    parse_media_items,
    parse_video_items,
)

MEDIA_PATH = "/media"
TV_PATH = "/tv"

MEDIA_FIELDS = ("media_key", "title", "url", "image_url", "source_url")
VIDEO_FIELDS = ("video_id", "title", "url", "image_url", "source_url")


def _rows(items: Sequence[Any]) -> list[dict[str, Any]]:
    return [item.to_row() for item in items]


def extract_media(client: HttpClient) -> list[Any]:
    """Extract multimedia cards from ``/media``.

    Args:
        client: HTTP client.

    Returns:
        list: Deduplicated media items.
    """
    html = client.get(MEDIA_PATH)
    url = client.settings.base_url.rstrip("/") + MEDIA_PATH
    return dedupe_media(
        parse_media_items(html, base_url=client.settings.base_url, source_url=url)
    )


def extract_videos(client: HttpClient) -> list[Any]:
    """Extract training videos from ``/tv``.

    Args:
        client: HTTP client.

    Returns:
        list: Deduplicated video items.
    """
    html = client.get(TV_PATH)
    url = client.settings.base_url.rstrip("/") + TV_PATH
    return dedupe_videos(
        parse_video_items(html, base_url=client.settings.base_url, source_url=url)
    )


def run_media(client: HttpClient, data_dir: Path) -> dict[str, dict[str, Path]]:
    """Extract media and videos and persist artifacts.

    Args:
        client: HTTP client.
        data_dir: Output root.

    Returns:
        dict[str, dict[str, Path]]: Section name to artifact paths.
    """
    media = extract_media(client)
    videos = extract_videos(client)
    return {
        "media_items": persist_section(
            _rows(media),
            data_dir=data_dir,
            name="media_items",
            fieldnames=list(MEDIA_FIELDS),
        ),
        "video_items": persist_section(
            _rows(videos),
            data_dir=data_dir,
            name="video_items",
            fieldnames=list(VIDEO_FIELDS),
        ),
    }
