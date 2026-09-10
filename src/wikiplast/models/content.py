"""Content and community domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ContentItem:
    """A news / article / event / honor listing card.

    Attributes:
        kind: ``news`` | ``article`` | ``event`` | ``honor`` | ``media`` | ``tv``.
        item_id: Numeric id from the URL.
        title: Display title when available.
        url: Absolute URL.
        image_url: Absolute image URL when present.
        published_text: Date/label text when present.
        source_url: Listing page URL.
    """

    kind: str
    item_id: str
    title: str
    url: str
    image_url: str
    published_text: str
    source_url: str

    def to_row(self) -> dict[str, Any]:
        """Convert to a flat dict for persistence.

        Returns:
            dict[str, Any]: Column mapping.
        """
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ClassifiedAd:
    """A marketplace classified ad from ``/ads`` or ``/starads``.

    Attributes:
        ad_id: Numeric id from ``/detail/{id}``.
        title: Ad title (cleaned).
        url: Absolute detail URL.
        image_url: Absolute image URL when present.
        is_featured: True when scraped from star/featured listings.
        category_path: Optional ads category path like ``/ads/191``.
        source_url: Listing page URL.
    """

    ad_id: str
    title: str
    url: str
    image_url: str
    is_featured: bool
    category_path: str
    source_url: str

    def to_row(self) -> dict[str, Any]:
        """Convert to a flat dict for persistence.

        Returns:
            dict[str, Any]: Column mapping.
        """
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FeaturedCompany:
    """A featured production unit from ``/topco``.

    Attributes:
        company_id: Profile id from ``/c{id}``.
        name: Display name.
        url: Absolute profile URL.
        category_label: Secondary category link text when present.
        category_url: Absolute category URL when present.
        logo_url: Absolute logo URL.
        source_url: Listing page URL.
    """

    company_id: str
    name: str
    url: str
    category_label: str
    category_url: str
    logo_url: str
    source_url: str

    def to_row(self) -> dict[str, Any]:
        """Convert to a flat dict for persistence.

        Returns:
            dict[str, Any]: Column mapping.
        """
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ManagerProfile:
    """A professional manager profile listing from ``/wikiboss``.

    Attributes:
        profile_id: Numeric id from ``/b{id}``.
        name: Display name (first line).
        birthplace: Birthplace text when present.
        url: Absolute profile URL.
        source_url: Listing page URL.
    """

    profile_id: str
    name: str
    birthplace: str
    url: str
    source_url: str

    def to_row(self) -> dict[str, Any]:
        """Convert to a flat dict for persistence.

        Returns:
            dict[str, Any]: Column mapping.
        """
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FeedEntry:
    """One RSS item from ``/feeds``.

    Attributes:
        title: Item title.
        link: Item link URL.
        description: Item description text.
        published_text: Raw pubDate text.
    """

    title: str
    link: str
    description: str
    published_text: str

    def to_row(self) -> dict[str, Any]:
        """Convert to a flat dict for persistence.

        Returns:
            dict[str, Any]: Column mapping.
        """
        return asdict(self)
