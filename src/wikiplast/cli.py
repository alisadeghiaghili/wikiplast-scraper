"""Command-line entry point for wikiplast extraction."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from wikiplast import __version__
from wikiplast.adapters.http_client import HttpClient
from wikiplast.config import Settings
from wikiplast.extractors.catalog import run_catalog
from wikiplast.extractors.companies import run_companies
from wikiplast.extractors.price_sections import run_all_prices

SECTION_CHOICES = ("prices", "companies", "catalog", "all")


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser.

    Returns:
        argparse.ArgumentParser: Configured parser.
    """
    parser = argparse.ArgumentParser(
        prog="wikiplast",
        description="Extract structured public data from wikiplast.ir.",
    )
    parser.add_argument("--version", action="version", version=f"wikiplast {__version__}")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Output directory (default: ./data or $WIKIPLAST_DATA_DIR).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    extract = sub.add_parser("extract", help="Run extractors.")
    extract.add_argument(
        "--section",
        action="append",
        dest="sections",
        choices=list(SECTION_CHOICES),
        help="Section to run; repeatable. Default: all.",
    )
    extract.add_argument(
        "--grade-history-limit",
        type=int,
        default=50,
        help="Max grade detail pages for catalog history (default: 50).",
    )
    extract.add_argument(
        "--max-categories",
        type=int,
        default=None,
        help="Optional cap on category grade tables (smoke runs).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: Optional argument vector; defaults to ``sys.argv[1:]``.

    Returns:
        int: Process exit code (0 success).
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = Settings.from_env()
    data_dir = args.data_dir or settings.data_dir

    sections = args.sections or ["all"]
    run_prices = "all" in sections or "prices" in sections
    run_companies_flag = "all" in sections or "companies" in sections
    run_catalog_flag = "all" in sections or "catalog" in sections

    with HttpClient(settings) as client:
        if run_prices:
            artifacts = run_all_prices(client, data_dir)
            for name, paths in artifacts.items():
                print(f"{name}: {paths['csv']}")
        if run_companies_flag:
            paths = run_companies(client, data_dir)
            print(f"companies: {paths['csv']}")
        if run_catalog_flag:
            artifacts = run_catalog(
                client,
                data_dir,
                grade_history_limit=args.grade_history_limit,
                max_category_pages=args.max_categories,
            )
            for name, paths in artifacts.items():
                print(f"{name}: {paths['csv']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
