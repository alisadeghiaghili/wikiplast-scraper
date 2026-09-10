"""Unit tests for detail parsers, checkpoint, and coverage."""

from __future__ import annotations

from pathlib import Path

from wikiplast.adapters.checkpoint import CheckpointStore
from wikiplast.adapters.coverage import build_coverage_report, write_coverage_report
from wikiplast.domain.detail import (
    parse_article_detail,
    parse_company_detail,
    parse_news_detail,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "html"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_news_detail() -> None:
    """News detail captures title, meta date, source, body."""
    html = _load("news_detail.html")
    detail = parse_news_detail(html, base_url="https://wikiplast.ir", item_id="27687")
    assert detail.item_id == "27687"
    assert "بانکی" in detail.title
    assert detail.published_iso == "2026-09-10T11:35:00+03:30"
    assert "پیشخوان" in detail.source_label
    assert "به روزرسانی شد" in detail.body_text
    assert "دیدگاه خود را بنویسید" not in detail.body_text
    assert detail.body_chars >= len(detail.body_text)


def test_parse_article_detail() -> None:
    """Article detail captures views and comments separately."""
    html = _load("article_detail.html")
    detail = parse_article_detail(html, base_url="https://wikiplast.ir", item_id="712")
    assert detail.view_count == 87816
    assert detail.comment_count == 34
    assert detail.published_iso.startswith("2018-05-21")
    assert "گرانول" in detail.body_text
    assert "visitcard" not in detail.body_text.lower() or "similar" not in detail.body_text


def test_parse_company_detail() -> None:
    """Company detail captures category, phone, website, rating."""
    html = _load("company_detail.html")
    detail = parse_company_detail(html, base_url="https://wikiplast.ir", company_id="1120")
    assert detail.company_id == "1120"
    assert "نیکان" in detail.name
    assert "شیمیایی" in detail.category_labels
    assert "021" in detail.phone_texts
    assert detail.website == "Nikanshoe.com"
    assert detail.rating_text == "51"


def test_checkpoint_resume(tmp_path: Path) -> None:
    """Checkpoint saves and restores completed ids across instances."""
    path = tmp_path / "ck.json"
    store = CheckpointStore(path)
    store.start_section("news_details", resume=False)
    store.mark_done("1")
    store.mark_done("2")
    store.save()

    reloaded = CheckpointStore(path)
    reloaded.start_section("news_details", resume=True)
    assert reloaded.is_done("1")
    assert not reloaded.is_done("3")
    reloaded.mark_done("3")
    reloaded.save()
    assert CheckpointStore(path).count() == 3


def test_checkpoint_no_resume_clears(tmp_path: Path) -> None:
    """resume=False discards prior progress even if section matches."""
    path = tmp_path / "ck.json"
    store = CheckpointStore(path)
    store.start_section("news_details", resume=False)
    store.mark_done("1")
    store.save()
    fresh = CheckpointStore(path)
    fresh.start_section("news_details", resume=False)
    assert not fresh.is_done("1")


def test_coverage_report(tmp_path: Path) -> None:
    """Coverage report aggregates table counts and writes JSON."""
    report = build_coverage_report(
        tables={"news_details": 3, "article_details": 2},
        started_at="2026-01-01T00:00:00+00:00",
    )
    assert report["total_rows"] == 5
    path = write_coverage_report(report, tmp_path / "coverage.json")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "news_details" in text
