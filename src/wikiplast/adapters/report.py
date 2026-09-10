"""Human-readable report from coverage.json and section artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from wikiplast.exceptions import StorageError


def load_coverage(data_dir: Path) -> dict:
    """Load ``coverage.json`` from a data directory.

    Args:
        data_dir: Output root produced by extractors.

    Returns:
        dict: Parsed coverage document.

    Raises:
        StorageError: When the file is missing or invalid.
    """
    path = data_dir / "coverage.json"
    if not path.exists():
        raise StorageError(f"No coverage.json under {data_dir}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StorageError(f"Cannot read {path}: {exc}") from exc


def count_csv_rows(csv_dir: Path) -> dict[str, int]:
    """Count data rows (excluding header) in each CSV under a directory.

    Args:
        csv_dir: Directory containing ``*.csv``.

    Returns:
        dict[str, int]: Filename stem to row count.
    """
    counts: dict[str, int] = {}
    if not csv_dir.exists():
        return counts
    for path in sorted(csv_dir.glob("*.csv")):
        with path.open(encoding="utf-8-sig", newline="") as handle:
            # header + rows
            n = sum(1 for _ in handle)
        counts[path.stem] = max(0, n - 1)
    return counts


def format_report(data_dir: Path) -> str:
    """Format a plain-text inventory report for a data directory.

    Args:
        data_dir: Output root.

    Returns:
        str: Multi-line report.
    """
    lines: list[str] = [f"wikiplast data report — {data_dir}"]
    csv_counts = count_csv_rows(data_dir / "csv")
    if csv_counts:
        lines.append("")
        lines.append("CSV tables:")
        total = 0
        for name, count in csv_counts.items():
            lines.append(f"  {name:28} {count:6d}")
            total += count
        lines.append(f"  {'TOTAL':28} {total:6d}")
    coverage_path = data_dir / "coverage.json"
    if coverage_path.exists():
        try:
            coverage = load_coverage(data_dir)
            lines.append("")
            lines.append(
                f"Last details coverage at {coverage.get('generated_at', '?')}: "
                f"{coverage.get('total_rows', 0)} detail rows"
            )
            extra = coverage.get("extra") or {}
            ckpt = extra.get("checkpoint_totals") or {}
            if ckpt:
                lines.append("Checkpoints: " + ", ".join(f"{k}={v}" for k, v in ckpt.items()))
        except StorageError as exc:
            lines.append(f"coverage.json unreadable: {exc}")
    sqlite = data_dir / "wikiplast.sqlite"
    lines.append("")
    lines.append(f"SQLite: {'yes' if sqlite.exists() else 'no'} ({sqlite})")
    bcp_dir = data_dir / "sqlserver"
    jsonl_dir = data_dir / "jsonl"
    lines.append(f"SQL Server BCP files: {len(list(bcp_dir.glob('*.csv'))) if bcp_dir.exists() else 0}")
    lines.append(f"JSONL files: {len(list(jsonl_dir.glob('*.jsonl'))) if jsonl_dir.exists() else 0}")
    return "\n".join(lines)
