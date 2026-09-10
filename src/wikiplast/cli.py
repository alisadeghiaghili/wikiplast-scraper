"""Command-line entry point for wikiplast extraction."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from wikiplast import __version__
from wikiplast.adapters.http_client import HttpClient
from wikiplast.adapters.report import format_report
from wikiplast.config import RATE_PROFILES, Settings
from wikiplast.extractors.bourse import run_bourse
from wikiplast.extractors.catalog import run_catalog
from wikiplast.extractors.companies import run_companies
from wikiplast.extractors.content import run_content
from wikiplast.extractors.details import run_details
from wikiplast.extractors.media import run_media
from wikiplast.extractors.price_sections import run_all_prices
from wikiplast.extractors.snapshot import run_public_snapshot

SECTION_CHOICES = (
    "prices",
    "companies",
    "catalog",
    "bourse",
    "content",
    "details",
    "media",
    "snapshot",
    "all",
)


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
    extract.add_argument(
        "--max-quota-pages",
        type=int,
        default=10,
        help="Max company-quota pages under /behin.php (default: 10).",
    )
    extract.add_argument(
        "--max-list-pages",
        type=int,
        default=20,
        help="Max pages for content listings such as news/ads (default: 20).",
    )
    extract.add_argument(
        "--detail-limit",
        type=int,
        default=25,
        help="Max new detail pages per entity type this run (default: 25).",
    )
    extract.add_argument(
        "--no-resume",
        action="store_true",
        help="Ignore checkpoints and re-crawl details from scratch.",
    )
    extract.add_argument(
        "--resume-listings",
        action="store_true",
        help="Skip listing pages already recorded in checkpoints (content/companies).",
    )
    extract.add_argument(
        "--rate-profile",
        choices=sorted(RATE_PROFILES),
        default=None,
        help="Delay profile: conservative | default | fast.",
    )
    extract.add_argument(
        "--snapshot-news-pages",
        type=int,
        default=3,
        help="News listing pages included in --section snapshot (default: 3).",
    )
    sub.add_parser("report", help="Print a data inventory report for --data-dir.")
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
    settings = Settings.from_env(rate_profile=getattr(args, "rate_profile", None))
    data_dir = args.data_dir or settings.data_dir

    if args.command == "report":
        print(format_report(data_dir))
        return 0

    sections = getattr(args, "sections", None) or ["all"]
    run_prices = "all" in sections or "prices" in sections
    run_companies_flag = "all" in sections or "companies" in sections
    run_catalog_flag = "all" in sections or "catalog" in sections
    run_bourse_flag = "all" in sections or "bourse" in sections
    run_content_flag = "all" in sections or "content" in sections
    run_media_flag = "all" in sections or "media" in sections
    run_snapshot_flag = "snapshot" in sections
    # Details are heavy; include in "all" only when explicitly requested
    # or when --section details is passed.
    run_details_flag = "details" in sections

    # Snapshot is a self-contained bundle; avoid double-running overlapping sections.
    if run_snapshot_flag:
        run_prices = False
        run_bourse_flag = False
        run_media_flag = False
        if "all" in sections:
            run_content_flag = False

    with HttpClient(settings) as client:
        if run_snapshot_flag:
            artifacts = run_public_snapshot(
                client,
                data_dir,
                news_pages=args.snapshot_news_pages,
            )
            for name, paths in artifacts.items():
                for kind, path in paths.items():
                    print(f"{name}.{kind}: {path}")
        if run_prices:
            artifacts = run_all_prices(client, data_dir)
            for name, paths in artifacts.items():
                print(f"{name}: {paths['csv']}")
        if run_companies_flag:
            paths = run_companies(
                client, data_dir, resume_listings=args.resume_listings
            )
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
        if run_bourse_flag:
            artifacts = run_bourse(
                client,
                data_dir,
                max_quota_pages=args.max_quota_pages,
            )
            for name, paths in artifacts.items():
                print(f"{name}: {paths['csv']}")
        if run_content_flag:
            artifacts = run_content(
                client,
                data_dir,
                max_list_pages=args.max_list_pages,
                resume_listings=args.resume_listings,
            )
            for name, paths in artifacts.items():
                print(f"{name}: {paths['csv']}")
        if run_media_flag:
            artifacts = run_media(client, data_dir)
            for name, paths in artifacts.items():
                print(f"{name}: {paths['csv']}")
        if run_details_flag:
            artifacts = run_details(
                client,
                data_dir,
                resume=not args.no_resume,
                news_limit=args.detail_limit,
                article_limit=args.detail_limit,
                company_limit=args.detail_limit,
            )
            for name, paths in artifacts.items():
                for kind, path in paths.items():
                    print(f"{name}.{kind}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
