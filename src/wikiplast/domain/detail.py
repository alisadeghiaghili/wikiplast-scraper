"""Parsers for news, article, and company detail pages."""

from __future__ import annotations

import re

from wikiplast.domain.html_parsing import clean_text, first_int, parse_html
from wikiplast.models.detail import ArticleDetail, CompanyDetail, NewsDetail

_META_PUBLISHED = 'meta[property="article:published_time"]'
_WS_RE = re.compile(r"\s+")


def _meta_published(soup) -> str | None:  # type: ignore[no-untyped-def]
    node = soup.select_one(_META_PUBLISHED)
    if node is None:
        return None
    content = node.get("content")
    return str(content) if content else None


def _collapse(text: str) -> str:
    return _WS_RE.sub(" ", text).strip()


def _body_from_main(soup, *, exclude_classes: tuple[str, ...] = ()) -> tuple[str, int]:  # type: ignore[no-untyped-def]
    """Extract a readable body text blob from the page main area.

    Args:
        soup: Parsed document.
        exclude_classes: Class names whose subtrees are skipped.

    Returns:
        tuple[str, int]: Truncated body text and original character length.
    """
    main = soup.select_one("div.main") or soup.body or soup
    # Drop chrome that is not article body.
    for selector in (
        "script",
        "style",
        "nav",
        "header",
        "footer",
        ".modalbox",
        ".headbox",
        ".sidebox",
        ".visitcard",
        ".nibox",
        ".whbg",
    ):
        for node in main.select(selector):
            node.decompose()
    for cls in exclude_classes:
        for node in main.select(f".{cls}"):
            node.decompose()
    text = _collapse(main.get_text(" ", strip=True))
    # Cut off common trailing chrome phrases when possible.
    for marker in ("دیدگاه خود را بنویسید", "مطالب مرتبط", "پربازدیدترین"):
        idx = text.find(marker)
        if idx > 20:
            text = text[:idx].strip()
            break
    return text[:4000], len(text)


def parse_news_detail(
    html: str | bytes,
    *,
    base_url: str,
    item_id: str,
) -> NewsDetail:
    """Parse a news detail page.

    Args:
        html: Page HTML.
        base_url: Origin used to build the absolute URL.
        item_id: News id from the listing.

    Returns:
        NewsDetail: Parsed detail row.
    """
    soup = parse_html(html)
    h1 = soup.select_one("h1")
    title = clean_text(h1) if h1 else (soup.title.get_text(strip=True) if soup.title else "")
    if "|" in title:
        title = title.split("|")[0].strip()
    newsico = soup.select_one(".newsico")
    published_text = clean_text(newsico) if newsico else ""
    source_label = ""
    for span in soup.select("span.font10"):
        text = clean_text(span)
        if text and "پیشخوان" in text:
            source_label = text
            break
    body_text, body_chars = _body_from_main(soup)
    return NewsDetail(
        item_id=item_id,
        title=title,
        url=f"{base_url.rstrip('/')}/news/{item_id}",
        published_iso=_meta_published(soup),
        published_text=published_text,
        source_label=source_label,
        body_text=body_text,
        body_chars=body_chars,
    )


def parse_article_detail(
    html: str | bytes,
    *,
    base_url: str,
    item_id: str,
) -> ArticleDetail:
    """Parse an article detail page.

    Args:
        html: Page HTML.
        base_url: Origin used to build the absolute URL.
        item_id: Article id from the listing.

    Returns:
        ArticleDetail: Parsed detail row.
    """
    soup = parse_html(html)
    h1 = soup.select_one("h1")
    title = clean_text(h1) if h1 else (soup.title.get_text(strip=True) if soup.title else "")
    if "|" in title:
        title = title.split("|")[0].strip()

    published_text = ""
    view_count: int | None = None
    comment_count: int | None = None
    for span in soup.select("span.font10"):
        text = clean_text(span)
        if not text:
            continue
        if "بازدید" in text:
            view_count = first_int(text)
        elif "دیدگاه" in text:
            comment_count = first_int(text)
        elif not published_text and any(ch.isdigit() for ch in text) and "بازدید" not in text:
            published_text = text

    body_text, body_chars = _body_from_main(soup)
    return ArticleDetail(
        item_id=item_id,
        title=title,
        url=f"{base_url.rstrip('/')}/article/{item_id}",
        published_iso=_meta_published(soup),
        published_text=published_text,
        view_count=view_count,
        comment_count=comment_count,
        body_text=body_text,
        body_chars=body_chars,
    )


def parse_company_detail(
    html: str | bytes,
    *,
    base_url: str,
    company_id: str,
) -> CompanyDetail:
    """Parse a company profile detail page.

    Args:
        html: Page HTML.
        base_url: Origin used to build the absolute URL.
        company_id: Company id from the listing.

    Returns:
        CompanyDetail: Parsed detail row.
    """
    soup = parse_html(html)
    h3 = soup.select_one("h3")
    name = clean_text(h3) if h3 else (soup.title.get_text(strip=True) if soup.title else "")
    if "|" in name:
        name = name.split("|")[0].strip()

    categories: list[str] = []
    for h4 in soup.select("h4"):
        link = h4.select_one("a")
        if link is None:
            continue
        label = clean_text(link)
        href = str(link.get("href") or "")
        if label and ("/companies/" in href or "/cat" in href):
            categories.append(label)

    phones: list[str] = []
    for icon in soup.select("i.fa-phone"):
        parent = icon.parent
        if parent is not None:
            text = clean_text(parent)
            if text and text not in phones:
                phones.append(text)

    website = ""
    site = soup.select_one(".siteadd")
    if site is not None:
        website = clean_text(site)

    rating = ""
    rating_el = soup.select_one(".font10 .bold")
    if rating_el is not None:
        rating = clean_text(rating_el)

    return CompanyDetail(
        company_id=company_id,
        name=name,
        url=f"{base_url.rstrip('/')}/c{company_id}",
        category_labels="; ".join(categories),
        phone_texts="; ".join(phones[:10]),
        website=website,
        rating_text=rating,
    )
