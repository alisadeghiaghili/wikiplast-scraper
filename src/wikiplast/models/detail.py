"""Detail-page domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class NewsDetail:
    """Full news article detail.

    Attributes:
        item_id: News id from the URL.
        title: ``h1`` or page title.
        url: Absolute page URL.
        published_iso: ISO datetime from meta when present.
        published_text: Jalali/date text from the page chrome.
        source_label: Publisher/source label when present (e.g. پیشخوان خبر).
        body_text: Plain-text body (collapsed whitespace), truncated.
        body_chars: Character length of extracted body before truncation.
    """

    item_id: str
    title: str
    url: str
    published_iso: str | None
    published_text: str
    source_label: str
    body_text: str
    body_chars: int

    def to_row(self) -> dict[str, Any]:
        """Convert to a flat dict for persistence.

        Returns:
            dict[str, Any]: Column mapping.
        """
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ArticleDetail:
    """Full technical article detail.

    Attributes:
        item_id: Article id from the URL.
        title: ``h1`` or page title.
        url: Absolute page URL.
        published_iso: ISO datetime from meta when present.
        published_text: Visible date text.
        view_count: Parsed view count when present.
        comment_count: Parsed comment count when present.
        body_text: Plain-text body, truncated.
        body_chars: Character length before truncation.
    """

    item_id: str
    title: str
    url: str
    published_iso: str | None
    published_text: str
    view_count: int | None
    comment_count: int | None
    body_text: str
    body_chars: int

    def to_row(self) -> dict[str, Any]:
        """Convert to a flat dict for persistence.

        Returns:
            dict[str, Any]: Column mapping.
        """
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CompanyDetail:
    """Company profile detail page.

    Attributes:
        company_id: Company id from ``/c{id}``.
        name: Display name.
        url: Absolute profile URL.
        category_labels: Semicolon-joined category labels from ``h4`` links.
        phone_texts: Semicolon-joined phone/contact fragments near phone icons.
        website: Website text when present.
        rating_text: Raw rating text when present.
    """

    company_id: str
    name: str
    url: str
    category_labels: str
    phone_texts: str
    website: str
    rating_text: str

    def to_row(self) -> dict[str, Any]:
        """Convert to a flat dict for persistence.

        Returns:
            dict[str, Any]: Column mapping.
        """
        return asdict(self)
