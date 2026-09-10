"""Coverage report writer for extraction runs."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from wikiplast.exceptions import StorageError


def build_coverage_report(
    *,
    tables: dict[str, int],
    started_at: str,
    finished_at: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a coverage payload for one extraction run.

    Args:
        tables: Mapping of table/section name to written row count.
        started_at: ISO timestamp when the run started.
        finished_at: ISO timestamp when the run finished; defaults to now.
        extra: Optional additional metadata merged into the report.

    Returns:
        dict[str, Any]: Coverage document.
    """
    return {
        "generated_at": finished_at or datetime.now(UTC).isoformat(),
        "started_at": started_at,
        "total_rows": sum(tables.values()),
        "tables": tables,
        "extra": extra or {},
    }


def write_coverage_report(report: dict[str, Any], path: Path) -> Path:
    """Write a coverage report JSON file.

    Args:
        report: Report payload from :func:`build_coverage_report`.
        path: Destination JSON path.

    Returns:
        Path: The path written.

    Raises:
        StorageError: When the file cannot be written.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        raise StorageError(f"Cannot write coverage report {path}: {exc}") from exc
    return path
