"""Parsers for wikiplast content / community listing pages."""

from __future__ import annotations

import re
from collections.abc import Iterable
from xml.etree import ElementTree as ET

from bs4 import Tag

from wikiplast.domain.html_parsing import (
    absolute_url,
    clean_text,
    parse_html,
)
from wikiplast.models.content import (
    ClassifiedAd,
    ContentItem,
    FeaturedCompany,
    FeedEntry,
    ManagerProfile,
)

NEWS_ID_RE = re.compile(r"/news/(\d+)")
ARTICLE_ID_RE = re.compile(r"/article/(\d+)")
DETAIL_ID_RE = re.compile(r"/detail/(\d+)")
COMPANY_ID_RE = re.compile(r"/c(\d+)")
BOSS_ID_RE = re.compile(r"/b(\d+)")
_SKIP_TITLES = {"ادامه مطلب", "لینک صفحه"}


def _id_from(pattern: re.Pattern[str], href: str) -> str:
    match = pattern.search(href or "")
    return match.group(1) if match else ""


def parse_content_links(
    html: str | bytes,
    *,
    base_url: str,
    source_url: str,
    kind: str,
    id_patterns: tuple[re.Pattern[str], ...],
) -> list[ContentItem]:
    """Parse listing links of news/article/event/honor style pages.

    Args:
        html: Page HTML.
        base_url: Origin for absolute URLs.
        source_url: Listing URL stamped on rows.
        kind: Stored kind label.
        id_patterns: Regexes used to extract the numeric id.

    Returns:
        list[ContentItem]: Unique items in document order.
    """
    soup = parse_html(html)
    items: list[ContentItem] = []
    seen: set[str] = set()

    for anchor in soup.select("a[href]"):
        if not isinstance(anchor, Tag):
            continue
        href = str(anchor.get("href") or "")
        item_id = ""
        for pattern in id_patterns:
            item_id = _id_from(pattern, href)
            if item_id:
                break
        if not item_id:
            continue
        # Prefer heading text inside the anchor; fall back to anchor text.
        heading = anchor.select_one("h3") or anchor.select_one("h2")
        title = clean_text(heading) if heading else clean_text(anchor)
        if not title or title in _SKIP_TITLES or len(title) < 3:
            # Try parent text for image-only cards (honors).
            parent = anchor.parent
            title = clean_text(parent) if parent else title
        if not title or title in _SKIP_TITLES:
            continue
        # Honors cards often put company name in a nearby date-like span.
        published = ""
        parent = anchor.parent
        if parent is not None:
            date_nodes = parent.select(".font10, .newsico span, time, span.date")
            if date_nodes:
                published = clean_text(date_nodes[0])
        img = anchor.select_one("img") or (parent.select_one("img") if parent else None)
        key = f"{kind}:{item_id}"
        if key in seen:
            continue
        seen.add(key)
        items.append(
            ContentItem(
                kind=kind,
                item_id=item_id,
                title=title.strip(),
                url=absolute_url(base_url, href),
                image_url=absolute_url(base_url, str(img.get("src") if img else "")),
                published_text=published,
                source_url=source_url,
            )
        )
    return items


def parse_ads(
    html: str | bytes,
    *,
    base_url: str,
    source_url: str,
    featured: bool = False,
) -> list[ClassifiedAd]:
    """Parse classified ad cards linking to ``/detail/{id}``.

    Args:
        html: Page HTML (``/ads`` or ``/starads``).
        base_url: Origin for absolute URLs.
        source_url: Listing URL.
        featured: Mark rows as featured (star ads).

    Returns:
        list[ClassifiedAd]: Unique ads in document order.
    """
    soup = parse_html(html)
    ads: list[ClassifiedAd] = []
    seen: set[str] = set()
    for anchor in soup.select("a[href*='/detail/']"):
        if not isinstance(anchor, Tag):
            continue
        href = str(anchor.get("href") or "")
        ad_id = _id_from(DETAIL_ID_RE, href)
        if not ad_id or ad_id in seen:
            continue
        heading = anchor.select_one("h3")
        title = clean_text(heading) if heading else clean_text(anchor)
        title = title.replace("ویژه", "").strip()
        if not title or title in _SKIP_TITLES:
            # Featured cards sometimes only show "ویژه" in the visible text;
            # fall back to the URL slug.
            title = href.rstrip("/").split("/")[-1].replace("-", " ").strip()
        if not title:
            continue
        img = anchor.select_one("img")
        seen.add(ad_id)
        ads.append(
            ClassifiedAd(
                ad_id=ad_id,
                title=title[:200],
                url=absolute_url(base_url, href),
                image_url=absolute_url(base_url, str(img.get("src") if img else "")),
                is_featured=featured,
                category_path="",
                source_url=source_url,
            )
        )
    return ads


def parse_top_companies(
    html: str | bytes,
    *,
    base_url: str,
    source_url: str,
) -> list[FeaturedCompany]:
    """Parse ``/topco`` visit cards.

    Args:
        html: Page HTML.
        base_url: Origin for absolute URLs.
        source_url: Listing URL.

    Returns:
        list[FeaturedCompany]: Unique featured companies.
    """
    soup = parse_html(html)
    companies: list[FeaturedCompany] = []
    seen: set[str] = set()
    for card in soup.select(".visitcard"):
        if not isinstance(card, Tag):
            continue
        name_a = card.select_one("h3 a")
        if name_a is None:
            continue
        href = str(name_a.get("href") or "")
        company_id = _id_from(COMPANY_ID_RE, href)
        name = clean_text(name_a)
        if not name or company_id in seen:
            continue
        cat_a = card.select_one("h4 a")
        img = card.select_one(".cardphoto img")
        seen.add(company_id)
        companies.append(
            FeaturedCompany(
                company_id=company_id,
                name=name,
                url=absolute_url(base_url, href),
                category_label=clean_text(cat_a) if cat_a else "",
                category_url=absolute_url(base_url, str(cat_a.get("href") if cat_a else "")),
                logo_url=absolute_url(base_url, str(img.get("src") if img else "")),
                source_url=source_url,
            )
        )
    return companies


def parse_manager_profiles(
    html: str | bytes,
    *,
    base_url: str,
    source_url: str,
) -> list[ManagerProfile]:
    """Parse ``/wikiboss`` manager profile links (``/b{id}``).

    Args:
        html: Page HTML.
        base_url: Origin for absolute URLs.
        source_url: Listing URL.

    Returns:
        list[ManagerProfile]: Unique profiles.
    """
    soup = parse_html(html)
    profiles: list[ManagerProfile] = []
    seen: set[str] = set()
    for anchor in soup.select("a[href^='/b']"):
        if not isinstance(anchor, Tag):
            continue
        href = str(anchor.get("href") or "")
        profile_id = _id_from(BOSS_ID_RE, href)
        if not profile_id or profile_id in seen:
            continue
        blob = clean_text(anchor)
        if not blob:
            continue
        # Text often looks like: "نام \n متولد:  شهر"
        name = blob.split("متولد")[0].strip(" \n\t:")
        birthplace = ""
        if "متولد" in blob:
            birthplace = blob.split("متولد", 1)[1].lstrip(": ").strip()
        if not name:
            continue
        seen.add(profile_id)
        profiles.append(
            ManagerProfile(
                profile_id=profile_id,
                name=name[:120],
                birthplace=birthplace[:120],
                url=absolute_url(base_url, href),
                source_url=source_url,
            )
        )
    return profiles


def parse_rss_feed(data: str | bytes) -> list[FeedEntry]:
    """Parse wikiplast RSS 2.0 feed items.

    Args:
        data: Raw XML body (bytes preferred when the XML declares encoding).

    Returns:
        list[FeedEntry]: Feed items.

    Examples:
        >>> entries = parse_rss_feed(
        ...     '<?xml version="1.0" encoding="UTF-8"?><rss><channel>'
        ...     '<item><title>T</title><link>http://x</link>'
        ...     '<description>D</description>'
        ...     '<pubDate>2026-09-10 11:35</pubDate></item>'
        ...     '</channel></rss>'
        ... )
        >>> entries[0].title, entries[0].link
        ('T', 'http://x')
    """
    payload = data.encode("utf-8") if isinstance(data, str) else data
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        return []

    def _text(element: ET.Element | None) -> str:
        if element is None or element.text is None:
            return ""
        return element.text.strip()

    entries: list[FeedEntry] = []
    for item in root.iter("item"):
        # Namespaces are unlikely on this feed; match by local name.
        title = link = description = published = ""
        for child in item:
            tag = child.tag.rsplit("}", 1)[-1].lower()
            if tag == "title":
                title = _text(child)
            elif tag == "link":
                link = _text(child)
            elif tag == "description":
                description = _text(child)
            elif tag in {"pubdate", "date"}:
                published = _text(child)
        if title:
            entries.append(
                FeedEntry(
                    title=title,
                    link=link,
                    description=description[:500],
                    published_text=published,
                )
            )
    return entries


def dedupe_content(items: Iterable[ContentItem]) -> list[ContentItem]:
    """Deduplicate content items by kind + id.

    Args:
        items: Iterable of items.

    Returns:
        list[ContentItem]: Unique items.
    """
    seen: set[tuple[str, str]] = set()
    unique: list[ContentItem] = []
    for item in items:
        key = (item.kind, item.item_id)
        if not item.item_id or key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def dedupe_ads(items: Iterable[ClassifiedAd]) -> list[ClassifiedAd]:
    """Deduplicate ads by ad_id, preferring featured rows.

    Args:
        items: Iterable of ads.

    Returns:
        list[ClassifiedAd]: Unique ads.
    """
    by_id: dict[str, ClassifiedAd] = {}
    order: list[str] = []
    for item in items:
        if not item.ad_id:
            continue
        if item.ad_id not in by_id:
            by_id[item.ad_id] = item
            order.append(item.ad_id)
            continue
        if item.is_featured and not by_id[item.ad_id].is_featured:
            by_id[item.ad_id] = item
    return [by_id[i] for i in order]
