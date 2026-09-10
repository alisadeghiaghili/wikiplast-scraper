"""Detail crawls for news, articles, and companies with resume support."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from wikiplast.adapters.checkpoint import CheckpointStore
from wikiplast.adapters.coverage import build_coverage_report, write_coverage_report
from wikiplast.adapters.http_client import HttpClient
from wikiplast.adapters.storage import persist_section
from wikiplast.domain.content import ARTICLE_ID_RE, NEWS_ID_RE
from wikiplast.domain.detail import (
    parse_article_detail,
    parse_company_detail,
    parse_news_detail,
)
from wikiplast.exceptions import HttpError
from wikiplast.extractors.companies import extract_companies
from wikiplast.extractors.content import extract_articles, extract_news

NEWS_DETAIL_FIELDS = (
    "item_id",
    "title",
    "url",
    "published_iso",
    "published_text",
    "source_label",
    "body_text",
    "body_chars",
)
ARTICLE_DETAIL_FIELDS = (
    "item_id",
    "title",
    "url",
    "published_iso",
    "published_text",
    "view_count",
    "comment_count",
    "body_text",
    "body_chars",
)
COMPANY_DETAIL_FIELDS = (
    "company_id",
    "name",
    "url",
    "category_labels",
    "phone_texts",
    "website",
    "rating_text",
)


def _rows(items: Sequence[Any]) -> list[dict[str, Any]]:
    return [item.to_row() for item in items]


def crawl_news_details(
    client: HttpClient,
    *,
    limit: int | None = None,
    checkpoint: CheckpointStore | None = None,
) -> list[Any]:
    """Crawl news detail pages discovered from the news listing.

    Args:
        client: HTTP client.
        limit: Optional cap on newly crawled details this run.
        checkpoint: Optional resume store; completed ids are skipped.

    Returns:
        list: Parsed news details for this run (not previously completed).
    """
    listing = extract_news(client)
    results: list[Any] = []
    fetched = 0
    for item in listing:
        if checkpoint is not None and checkpoint.is_done(item.item_id):
            continue
        if limit is not None and fetched >= limit:
            break
        try:
            html = client.get(f"/news/{item.item_id}")
        except HttpError as exc:
            if exc.status_code in {404, 410}:
                if checkpoint is not None:
                    checkpoint.mark_done(item.item_id)
                continue
            raise
        detail = parse_news_detail(
            html,
            base_url=client.settings.base_url,
            item_id=item.item_id,
        )
        results.append(detail)
        fetched += 1
        if checkpoint is not None:
            checkpoint.mark_done(item.item_id)
    return results


def crawl_article_details(
    client: HttpClient,
    *,
    limit: int | None = None,
    checkpoint: CheckpointStore | None = None,
) -> list[Any]:
    """Crawl article detail pages discovered from the articles listing.

    Args:
        client: HTTP client.
        limit: Optional cap on newly crawled details this run.
        checkpoint: Optional resume store.

    Returns:
        list: Parsed article details for this run.
    """
    listing = extract_articles(client)
    results: list[Any] = []
    fetched = 0
    seen: set[str] = set()
    for item in listing:
        if item.item_id in seen:
            continue
        seen.add(item.item_id)
        if checkpoint is not None and checkpoint.is_done(item.item_id):
            continue
        if limit is not None and fetched >= limit:
            break
        try:
            html = client.get(f"/article/{item.item_id}")
        except HttpError as exc:
            if exc.status_code in {404, 410}:
                if checkpoint is not None:
                    checkpoint.mark_done(item.item_id)
                continue
            raise
        detail = parse_article_detail(
            html,
            base_url=client.settings.base_url,
            item_id=item.item_id,
        )
        results.append(detail)
        fetched += 1
        if checkpoint is not None:
            checkpoint.mark_done(item.item_id)
    return results


def crawl_company_details(
    client: HttpClient,
    *,
    limit: int | None = None,
    checkpoint: CheckpointStore | None = None,
) -> list[Any]:
    """Crawl company profile pages discovered from the companies directory.

    Args:
        client: HTTP client.
        limit: Optional cap on newly crawled details this run.
        checkpoint: Optional resume store.

    Returns:
        list: Parsed company details for this run.
    """
    listing = extract_companies(client)
    results: list[Any] = []
    fetched = 0
    for company in listing:
        cid = company.company_id
        if not cid:
            continue
        if checkpoint is not None and checkpoint.is_done(cid):
            continue
        if limit is not None and fetched >= limit:
            break
        try:
            html = client.get(f"/c{cid}")
        except HttpError as exc:
            if exc.status_code in {404, 410}:
                if checkpoint is not None:
                    checkpoint.mark_done(cid)
                continue
            raise
        detail = parse_company_detail(
            html,
            base_url=client.settings.base_url,
            company_id=cid,
        )
        results.append(detail)
        fetched += 1
        if checkpoint is not None:
            checkpoint.mark_done(cid)
    return results


def run_details(
    client: HttpClient,
    data_dir: Path,
    *,
    resume: bool = True,
    news_limit: int | None = 25,
    article_limit: int | None = 25,
    company_limit: int | None = 25,
) -> dict[str, dict[str, Path]]:
    """Crawl detail pages and persist artifacts plus coverage.

    Args:
        client: HTTP client.
        data_dir: Output root.
        resume: Resume from checkpoint files under ``data_dir/checkpoints``.
        news_limit: Max new news details this run.
        article_limit: Max new article details this run.
        company_limit: Max new company details this run.

    Returns:
        dict[str, dict[str, Path]]: Section name to artifact paths.
    """
    started = datetime.now(UTC).isoformat()
    ckpt_dir = data_dir / "checkpoints"
    artifacts: dict[str, dict[str, Path]] = {}

    news_ckpt = CheckpointStore(ckpt_dir / "news_details.json")
    news_ckpt.start_section("news_details", resume=resume)
    news_rows = crawl_news_details(client, limit=news_limit, checkpoint=news_ckpt)
    news_ckpt.save()
    artifacts["news_details"] = persist_section(
        _rows(news_rows),
        data_dir=data_dir,
        name="news_details",
        fieldnames=list(NEWS_DETAIL_FIELDS),
    )

    article_ckpt = CheckpointStore(ckpt_dir / "article_details.json")
    article_ckpt.start_section("article_details", resume=resume)
    article_rows = crawl_article_details(
        client, limit=article_limit, checkpoint=article_ckpt
    )
    article_ckpt.save()
    artifacts["article_details"] = persist_section(
        _rows(article_rows),
        data_dir=data_dir,
        name="article_details",
        fieldnames=list(ARTICLE_DETAIL_FIELDS),
    )

    company_ckpt = CheckpointStore(ckpt_dir / "company_details.json")
    company_ckpt.start_section("company_details", resume=resume)
    company_rows = crawl_company_details(
        client, limit=company_limit, checkpoint=company_ckpt
    )
    company_ckpt.save()
    artifacts["company_details"] = persist_section(
        _rows(company_rows),
        data_dir=data_dir,
        name="company_details",
        fieldnames=list(COMPANY_DETAIL_FIELDS),
    )

    report = build_coverage_report(
        tables={
            "news_details": len(news_rows),
            "article_details": len(article_rows),
            "company_details": len(company_rows),
        },
        started_at=started,
        extra={
            "resume": resume,
            "checkpoint_totals": {
                "news_details": news_ckpt.count(),
                "article_details": article_ckpt.count(),
                "company_details": company_ckpt.count(),
            },
        },
    )
    artifacts["_coverage"] = {"coverage": write_coverage_report(report, data_dir / "coverage.json")}
    return artifacts


# Re-export id helpers for tests that need listing patterns.
__all__ = [
    "ARTICLE_ID_RE",
    "NEWS_ID_RE",
    "crawl_article_details",
    "crawl_company_details",
    "crawl_news_details",
    "run_details",
]
