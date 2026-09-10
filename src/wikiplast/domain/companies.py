"""Company directory parsers with stable IDs and deduplication.

The v0.1 extractor appended the same company set once per category because
category URLs did not filter. These parsers extract cards from a page as-is
and expose a pure dedupe helper used by the orchestrator.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from bs4 import Tag

from wikiplast.domain.html_parsing import absolute_url, clean_text, parse_html
from wikiplast.models.company import CompanyCard

_COMPANY_ID_RE = re.compile(r"/c(\d+)")


def extract_company_id(href: str) -> str:
    """Extract the stable numeric company id from a profile href.

    Args:
        href: Relative or absolute profile URL (``/c1120`` or full URL).

    Returns:
        str: Numeric id without the leading ``c``, or empty string.
    """
    if not href:
        return ""
    match = _COMPANY_ID_RE.search(href)
    if not match:
        return ""
    return match.group(1)


def parse_company_cards(
    html: str | bytes,
    *,
    base_url: str,
    source_url: str,
    category: str = "",
) -> list[CompanyCard]:
    """Parse company visit-card blocks from a directory page.

    Args:
        html: Raw HTML of a companies listing page.
        base_url: Origin used to resolve relative links.
        source_url: Absolute listing URL stored on each card.
        category: Category label to stamp on every card from this page.

    Returns:
        list[CompanyCard]: Cards in document order. Cards without a name
        are skipped. Cards may repeat across pages; use
        :func:`dedupe_companies` before persisting.
    """
    soup = parse_html(html)
    cards: list[CompanyCard] = []
    for card in soup.select(".visitcard"):
        if not isinstance(card, Tag):
            continue
        name_el = card.select_one("h3 a")
        if name_el is None:
            continue
        name = clean_text(name_el)
        if not name:
            continue
        href = name_el.get("href") or ""
        contact_el = card.select_one("h4")
        website_el = card.select_one(".siteadd")
        rating_el = card.select_one(".font10 .bold")
        logo_el = card.select_one(".cardphoto img")
        verified = card.select_one(".fa-certificate") is not None
        cards.append(
            CompanyCard(
                company_id=extract_company_id(str(href)),
                name=name,
                url=absolute_url(base_url, str(href)),
                contact_person=clean_text(contact_el),
                website=clean_text(website_el),
                rating=clean_text(rating_el),
                logo_url=absolute_url(base_url, str(logo_el.get("src") if logo_el else "")),
                verified=verified,
                category=category,
                source_url=source_url,
            )
        )
    return cards


def dedupe_companies(cards: Iterable[CompanyCard]) -> list[CompanyCard]:
    """Deduplicate companies by ``company_id`` (fallback: url+name).

    When the same company appears on multiple category pages, the first
    occurrence wins. Later categories are not merged (v0.2 keeps one primary
    category per company).

    Args:
        cards: Iterable of company cards, possibly repeated.

    Returns:
        list[CompanyCard]: Unique companies in first-seen order.
    """
    seen_ids: set[str] = set()
    seen_keys: set[tuple[str, str]] = set()
    unique: list[CompanyCard] = []
    for card in cards:
        if card.company_id:
            if card.company_id in seen_ids:
                continue
            seen_ids.add(card.company_id)
            unique.append(card)
            continue
        key = (card.url, card.name)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        unique.append(card)
    return unique


def company_counts_match_unique(cards: Iterable[CompanyCard]) -> bool:
    """Return True when every company id appears at most once.

    Args:
        cards: Cards to check.

    Returns:
        bool: True if there are no duplicate non-empty ids.
    """
    ids = [c.company_id for c in cards if c.company_id]
    return len(ids) == len(set(ids))
