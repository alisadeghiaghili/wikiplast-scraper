"""Unit tests for media parsers and report formatting."""

from __future__ import annotations

from pathlib import Path

from wikiplast.adapters.report import count_csv_rows, format_report
from wikiplast.domain.media import parse_media_items, parse_video_items

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "html"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_media_items() -> None:
    """Media slugs parse with titles; bare /media link is ignored."""
    html = _load("media.html")
    items = parse_media_items(
        html, base_url="https://wikiplast.ir", source_url="https://wikiplast.ir/media"
    )
    assert len(items) == 2
    assert items[0].media_key == "hioxby2"
    assert "حراج" in items[0].title
    assert items[0].url.endswith("/media/hioxby2")
    assert all(i.media_key for i in items)


def test_parse_video_items() -> None:
    """Video ids parse from /videos/{id} links."""
    html = _load("tv.html")
    items = parse_video_items(
        html, base_url="https://wikiplast.ir", source_url="https://wikiplast.ir/tv"
    )
    assert len(items) == 2
    assert items[0].video_id == "36"
    assert "کارگاه" in items[0].title
    assert items[1].video_id == "33"


def test_format_report(tmp_path: Path) -> None:
    """Report lists CSV row counts and sqlite/BCP/JSONL presence."""
    csv_dir = tmp_path / "csv"
    csv_dir.mkdir()
    (csv_dir / "npc_prices.csv").write_text(
        "a,b\n1,x\n2,y\n", encoding="utf-8-sig"
    )
    (tmp_path / "wikiplast.sqlite").write_bytes(b"")
    bcp = tmp_path / "sqlserver"
    bcp.mkdir()
    (bcp / "npc_prices.bcp.csv").write_text("a,b\n", encoding="utf-8")
    jsonl = tmp_path / "jsonl"
    jsonl.mkdir()
    (jsonl / "npc_prices.jsonl").write_text("{}\n", encoding="utf-8")

    text = format_report(tmp_path)
    assert "npc_prices" in text
    assert "TOTAL" in text
    assert "SQLite: yes" in text
    assert "SQL Server BCP files: 1" in text
    assert "JSONL files: 1" in text
    assert count_csv_rows(csv_dir)["npc_prices"] == 2
