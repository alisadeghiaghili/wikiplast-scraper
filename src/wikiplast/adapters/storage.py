"""Persistence adapters: CSV, SQLite, and SQL Server-friendly export.

CSV files use UTF-8 with BOM so Excel and SSMS import dialogs behave.
SQLite is the local warehouse. ``export_sqlserver_bcp`` writes
comma-delimited UTF-8 files with ``NULL`` placeholders suitable for
``bcp`` / ``BULK INSERT`` into SQL Server.
"""

from __future__ import annotations

import csv
import re
import sqlite3
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from wikiplast.exceptions import StorageError

_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_table_name(name: str) -> str:
    if not _IDENT_RE.fullmatch(name):
        raise StorageError(f"Unsafe table/file name: {name!r}")
    return name


def _sql_type_for(value: Any) -> str:
    if value is None:
        return "TEXT"
    if isinstance(value, bool):
        return "INTEGER"
    if isinstance(value, int):
        return "INTEGER"
    if isinstance(value, float):
        return "REAL"
    return "TEXT"


def _coerce_sqlite(value: Any) -> Any:
    if isinstance(value, bool):
        return int(value)
    return value


def write_csv(
    rows: Sequence[dict[str, Any]],
    path: Path,
    *,
    fieldnames: Sequence[str] | None = None,
) -> Path:
    """Write rows to CSV with UTF-8 BOM.

    Args:
        rows: Mapping rows. Later rows may omit optional keys; missing keys
            become empty cells.
        path: Destination file path. Parent directories are created.
        fieldnames: Explicit column order. When omitted, union of keys in
            first-seen order is used (fixes v0.1 DictWriter crash on sparse
            optional columns).

    Returns:
        Path: The path written.

    Raises:
        StorageError: If the directory cannot be created or write fails.
    """
    if not rows and fieldnames is None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8-sig")
        return path

    columns: list[str]
    if fieldnames is not None:
        columns = list(fieldnames)
    else:
        columns = []
        seen: set[str] = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    columns.append(key)

    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow({k: ("" if row.get(k) is None else row.get(k)) for k in columns})
    except OSError as exc:
        raise StorageError(f"Failed writing CSV {path}: {exc}") from exc
    return path


def write_sqlite(
    rows: Sequence[dict[str, Any]],
    db_path: Path,
    table: str,
) -> int:
    """Create-or-replace a table in a SQLite database.

    Args:
        rows: Rows to insert. Table is created from the union of keys.
        db_path: SQLite file path.
        table: Table name (letters, digits, underscore only).

    Returns:
        int: Number of rows inserted.

    Raises:
        StorageError: Invalid table name or I/O failure.
    """
    table = _validate_table_name(table)
    if not rows:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.close()
        return 0

    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                columns.append(key)
                if not _IDENT_RE.fullmatch(key):
                    raise StorageError(f"Unsafe column name: {key!r}")

    # Infer types from the first non-null value per column.
    col_types: dict[str, str] = dict.fromkeys(columns, "TEXT")
    for row in rows:
        for col in columns:
            value = row.get(col)
            if value is not None and col_types[col] == "TEXT":
                col_types[col] = _sql_type_for(value)

    ddl_cols = ", ".join(f'"{c}" {col_types[c]}' for c in columns)
    placeholders = ", ".join("?" for _ in columns)
    quoted_cols = ", ".join(f'"{c}"' for c in columns)

    db_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(f'DROP TABLE IF EXISTS "{table}"')
            conn.execute(f'CREATE TABLE "{table}" ({ddl_cols})')
            conn.executemany(
                f'INSERT INTO "{table}" ({quoted_cols}) VALUES ({placeholders})',
                [tuple(_coerce_sqlite(row.get(c)) for c in columns) for row in rows],
            )
            conn.commit()
        finally:
            conn.close()
    except sqlite3.Error as exc:
        raise StorageError(f"SQLite write failed for {table}: {exc}") from exc
    return len(rows)


def export_sqlserver_bcp(
    rows: Sequence[dict[str, Any]],
    path: Path,
    *,
    fieldnames: Sequence[str] | None = None,
    null_token: str = "NULL",
) -> Path:
    """Write a SQL Server ``BULK INSERT``-friendly UTF-8 CSV.

    Differences from the Excel-oriented CSV writer:
        * no BOM (BCP/UTF-8 codepage 65001 prefers raw UTF-8),
        * empty cells are written as the literal ``NULL`` token so
          ``BULK INSERT ... WITH (FIELDTERMINATOR=',', ...)`` can map them
          with a format file, or you can import into a staging table and
          ``NULLIF`` the token.

    Args:
        rows: Mapping rows.
        path: Destination file path.
        fieldnames: Explicit column order; defaults to union of keys.
        null_token: Token emitted for ``None``/empty values.

    Returns:
        Path: The path written.
    """
    if fieldnames is not None:
        columns = list(fieldnames)
    else:
        columns = []
        seen: set[str] = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    columns.append(key)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(columns)
        for row in rows:
            out: list[str] = []
            for col in columns:
                value = row.get(col)
                if value is None or value == "":
                    out.append(null_token)
                elif isinstance(value, bool):
                    out.append("1" if value else "0")
                else:
                    out.append(str(value))
            writer.writerow(out)
    return path


def load_sqlite_table(db_path: Path, table: str) -> list[dict[str, Any]]:
    """Read a table back from SQLite (used by tests and CLI verify).

    Args:
        db_path: SQLite file path.
        table: Table name.

    Returns:
        list[dict[str, Any]]: Rows as dicts.

    Raises:
        StorageError: Query failure.
    """
    table = _validate_table_name(table)
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.execute(f'SELECT * FROM "{table}"')
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()
    except sqlite3.Error as exc:
        raise StorageError(f"SQLite read failed for {table}: {exc}") from exc


def persist_section(
    rows: Sequence[dict[str, Any]],
    *,
    data_dir: Path,
    name: str,
    fieldnames: Sequence[str] | None = None,
    write_bcp: bool = True,
) -> dict[str, Path]:
    """Persist one section to CSV, SQLite, and optional BCP file.

    Args:
        rows: Section rows.
        data_dir: Output root.
        name: Section name used for file/table names (``npc_prices``).
        fieldnames: Optional explicit columns.
        write_bcp: Also emit ``sqlserver/<name>.bcp.csv``.

    Returns:
        dict[str, Path]: Keys ``csv``, ``sqlite``, and optionally ``bcp``.
    """
    name = _validate_table_name(name)
    csv_path = write_csv(rows, data_dir / "csv" / f"{name}.csv", fieldnames=fieldnames)
    sqlite_path = data_dir / "wikiplast.sqlite"
    write_sqlite(rows, sqlite_path, name)
    result = {"csv": csv_path, "sqlite": sqlite_path}
    if write_bcp:
        result["bcp"] = export_sqlserver_bcp(
            rows, data_dir / "sqlserver" / f"{name}.bcp.csv", fieldnames=fieldnames
        )
    return result


def field_union(rows: Iterable[dict[str, Any]]) -> list[str]:
    """Return the ordered union of keys across rows.

    Args:
        rows: Iterable of mappings.

    Returns:
        list[str]: Column names in first-seen order.
    """
    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                columns.append(key)
    return columns
