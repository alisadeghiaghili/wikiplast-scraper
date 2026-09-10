"""Media and video listing domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class MediaItem:
    """A multimedia card from ``/media``.

    Attributes:
        media_key: Slug from ``/media/{slug}``.
        title: Display title.
        url: Absolute page URL.
        image_url: Absolute image URL when present.
        source_url: Listing page URL.
    """

    media_key: str
    title: str
    url: str
    image_url: str
    source_url: str

    def to_row(self) -> dict[str, Any]:
        """Convert to a flat dict for persistence.

        Returns:
            dict[str, Any]: Column mapping.
        """
        return asdict(self)


@dataclass(frozen=True, slots=True)
class VideoItem:
    """A training video card from ``/tv``.

    Attributes:
        video_id: Numeric id from ``/videos/{id}``.
        title: Display title.
        url: Absolute page URL.
        image_url: Absolute image URL when present.
        source_url: Listing page URL.
    """

    video_id: str
    title: str
    url: str
    image_url: str
    source_url: str

    def to_row(self) -> dict[str, Any]:
        """Convert to a flat dict for persistence.

        Returns:
            dict[str, Any]: Column mapping.
        """
        return asdict(self)
