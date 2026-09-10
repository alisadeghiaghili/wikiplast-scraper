"""Unit tests for content parsers."""

from __future__ import annotations

import re
from pathlib import Path

from wikiplast.domain.content import (
    parse_ads,
    parse_content_links,
    parse_manager_profiles,
    parse_rss_feed,
    parse_top_companies,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "html"
NEWS_RE = re.compile(r"/news/(\d+)")
ARTICLE_RE = re.compile(r"/article/(\d+)")


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_news_listing() -> None:
    """News cards yield id/title/date; related article on same page keeps kind."""
    html = _load("archive_news.html")
    news = parse_content_links(
        html,
        base_url="https://wikiplast.ir",
        source_url="https://wikiplast.ir/archive-news",
        kind="news",
        id_patterns=(NEWS_RE,),
    )
    assert len(news) == 2
    assert news[0].item_id == "27687"
    assert "بانکی" in news[0].title
    assert news[0].url.startswith("https://wikiplast.ir/news/27687")
    assert "شهریور" in news[0].published_text


def test_parse_articles_skips_read_more_duplicates() -> None:
    """Same article id from card + 'ادامه مطلب' collapses to one row."""
    html = _load("articles.html")
    articles = parse_content_links(
        html,
        base_url="https://wikiplast.ir",
        source_url="https://wikiplast.ir/articles",
        kind="article",
        id_patterns=(ARTICLE_RE,),
    )
    ids = [a.item_id for a in articles]
    assert ids == ["11889", "27392"]
    assert articles[0].title.startswith("آشنایی")
    assert "ادامه" not in articles[1].title


def test_parse_events() -> None:
    """Event listings parse with dates."""
    html = _load("events.html")
    events = parse_content_links(
        html,
        base_url="https://wikiplast.ir",
        source_url="https://wikiplast.ir/events",
        kind="event",
        id_patterns=(NEWS_RE,),
    )
    assert len(events) == 2
    assert events[0].kind == "event"
    assert "۱۴۰۵" in events[0].published_text


def test_parse_ads_featured_fallback_title() -> None:
    """Ads parse detail ids; featured cards fall back to URL slug title."""
    html = _load("ads.html")
    ads = parse_ads(
        html,
        base_url="https://wikiplast.ir",
        source_url="https://wikiplast.ir/ads",
        featured=False,
    )
    assert len(ads) == 2
    assert ads[0].ad_id == "1881"
    assert "نیتریک" in ads[0].title
    assert ads[1].ad_id == "1878"
    assert ads[1].title  # slug fallback
    assert ads[1].title != "ویژه"


def test_parse_honors_uses_company_label() -> None:
    """Honor cards without h3 titles use nearby company text."""
    html = _load("honors.html")
    honors = parse_content_links(
        html,
        base_url="https://wikiplast.ir",
        source_url="https://wikiplast.ir/honors",
        kind="honor",
        id_patterns=(NEWS_RE,),
    )
    assert len(honors) == 2
    assert honors[0].item_id == "26038"
    assert "پلیمر" in honors[0].title or honors[0].title


def test_parse_top_companies() -> None:
    """Featured companies expose id, name, category label."""
    html = _load("topco.html")
    rows = parse_top_companies(
        html, base_url="https://wikiplast.ir", source_url="https://wikiplast.ir/topco"
    )
    assert len(rows) == 2
    assert rows[0].company_id == "2264"
    assert rows[0].name == "آناهیتا پلاستیک"
    assert rows[0].category_label == "فیلم های پلی اتیلنی"
    assert rows[1].category_label == ""


def test_parse_manager_profiles() -> None:
    """Manager links parse name and birthplace."""
    html = _load("wikiboss.html")
    rows = parse_manager_profiles(
        html, base_url="https://wikiplast.ir", source_url="https://wikiplast.ir/wikiboss"
    )
    assert len(rows) == 2
    assert rows[0].profile_id == "41"
    assert rows[0].name == "سعید زکایی"
    assert "تهران" in rows[0].birthplace
    # /boss registration link must not become a profile
    assert all(r.profile_id != "oss" for r in rows)


def test_parse_rss_feed() -> None:
    """RSS items parse title/link/description/pubDate."""
    data = (FIXTURES / "feeds.xml").read_bytes()
    entries = parse_rss_feed(data)
    assert len(entries) == 2
    assert entries[0].title.startswith("کارمزد")
    assert entries[0].link.endswith("/news/27687/x")
    assert entries[0].published_text == "2026-09-10 11:35"
