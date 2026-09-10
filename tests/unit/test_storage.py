"""Unit tests for CSV/SQLite/BCP storage adapters."""

from __future__ import annotations

from pathlib import Path

from wikiplast.adapters.storage import (
    export_sqlserver_bcp,
    load_sqlite_table,
    persist_section,
    write_csv,
    write_sqlite,
)


def test_write_csv_unions_sparse_keys(tmp_path: Path) -> None:
    """Later rows may add optional keys without raising (v0.1 DictWriter bug)."""
    rows = [
        {"id": "1", "title": "a"},
        {"id": "2", "title": "b", "category": "x"},
    ]
    path = write_csv(rows, tmp_path / "t.csv")
    text = path.read_text(encoding="utf-8-sig")
    header = text.splitlines()[0]
    assert "category" in header
    assert "1,a" in text.replace(" ", "")


def test_write_sqlite_roundtrip(tmp_path: Path) -> None:
    """Rows survive a SQLite create/replace cycle."""
    rows = [
        {"grade": "PVC", "price_value": 100, "is_gated": False},
        {"grade": "ABS", "price_value": None, "is_gated": True},
    ]
    db = tmp_path / "w.sqlite"
    assert write_sqlite(rows, db, "prices") == 2
    loaded = load_sqlite_table(db, "prices")
    assert len(loaded) == 2
    assert loaded[0]["grade"] == "PVC"
    assert loaded[0]["price_value"] == 100
    assert loaded[1]["price_value"] is None
    assert loaded[1]["is_gated"] == 1


def test_export_sqlserver_bcp_null_token(tmp_path: Path) -> None:
    """BCP export writes NULL token for missing values, no BOM."""
    rows = [{"a": "x", "b": None}, {"a": "", "b": 2}]
    path = export_sqlserver_bcp(rows, tmp_path / "t.bcp.csv")
    raw = path.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8")
    assert "a,b" in text
    assert "x,NULL" in text
    assert "NULL,2" in text


def test_persist_section_writes_all_three(tmp_path: Path) -> None:
    """Section persist emits csv, sqlite, and bcp artifacts."""
    rows = [{"source": "npc", "grade_name": "PVC", "price_value": 1}]
    paths = persist_section(rows, data_dir=tmp_path, name="npc_prices")
    assert paths["csv"].exists()
    assert paths["sqlite"].exists()
    assert paths["bcp"].exists()
    assert paths["csv"].name == "npc_prices.csv"
