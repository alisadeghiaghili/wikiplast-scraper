"""Unit tests for listing resume and JSONL export."""

from __future__ import annotations

from pathlib import Path

from wikiplast.adapters.listing_resume import ListingCheckpoint, page_key
from wikiplast.adapters.storage import persist_section, write_jsonl


def test_page_key() -> None:
    """Page keys normalize leading slash."""
    assert page_key("/archive-news/2") == "page:/archive-news/2"
    assert page_key("archive-news/2") == "page:/archive-news/2"


def test_listing_checkpoint_resume(tmp_path: Path) -> None:
    """Completed pages are skipped after reload when resume=True."""
    path = tmp_path / "news_pages.json"
    ckpt = ListingCheckpoint(path, section="news_pages", resume=False)
    assert not ckpt.is_page_done("/archive-news")
    ckpt.mark_page_done("/archive-news")
    ckpt.mark_page_done("/archive-news/2")
    ckpt.save()

    resumed = ListingCheckpoint(path, section="news_pages", resume=True)
    assert resumed.is_page_done("/archive-news")
    assert resumed.is_page_done("/archive-news/2")
    assert not resumed.is_page_done("/archive-news/3")
    assert resumed.page_count() == 2

    fresh = ListingCheckpoint(path, section="news_pages", resume=False)
    assert not fresh.is_page_done("/archive-news")


def test_write_jsonl_and_persist(tmp_path: Path) -> None:
    """JSONL export writes one object per line and is included in persist."""
    rows = [{"a": 1, "b": "x"}, {"a": None, "b": "ی"}]
    path = write_jsonl(rows, tmp_path / "out.jsonl")
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert '"a": 1' in lines[0] or '"a":1' in lines[0].replace(" ", "")

    artifacts = persist_section(rows, data_dir=tmp_path, name="demo_rows")
    assert "jsonl" in artifacts
    assert artifacts["jsonl"].exists()
    assert artifacts["bcp"].exists()
    assert artifacts["csv"].exists()
