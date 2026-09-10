"""Companies directory extractor with real pagination and dedupe.

Fixes v0.1 defects:
    * category pages that return the same unfiltered listing no longer
      explode into N duplicate copies — results are deduped by company_id.
    * pages 3+ are actually fetched (queue-based BFS, not a mutated list
      after the executor has already finished).
"""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from wikiplast.adapters.http_client import HttpClient
from wikiplast.adapters.listing_resume import ListingCheckpoint
from wikiplast.adapters.storage import persist_section
from wikiplast.domain.companies import dedupe_companies, parse_company_cards
from wikiplast.domain.html_parsing import clean_text, parse_html
from wikiplast.exceptions import HttpError
from wikiplast.models.company import CompanyCard

COMPANIES_PATH = "/companies"
COMPANY_FIELDS: tuple[str, ...] = (
    "company_id",
    "name",
    "url",
    "contact_person",
    "website",
    "rating",
    "logo_url",
    "verified",
    "category",
    "source_url",
)


def discover_category_paths(html: str, *, base_url: str) -> list[dict[str, str]]:
    """Discover company category links from the companies landing page.

    Args:
        html: HTML of ``/companies``.
        base_url: Origin for resolving relative hrefs.

    Returns:
        list[dict[str, str]]: Each item has ``name`` and ``path`` (site-relative).
    """
    soup = parse_html(html)
    found: list[dict[str, str]] = []
    seen: set[str] = set()
    for link in soup.select("h2.titlogo a"):
        href = link.get("href") or ""
        if not href:
            continue
        # Prefer paths like /companies/86
        if "/companies/" in href:
            path = href.split(base_url)[-1] if href.startswith("http") else href
            path = "/" + path.lstrip("/")
            # keep only /companies/<id>
            parts = [p for p in path.split("/") if p]
            if len(parts) >= 2 and parts[0] == "companies":
                path = f"/companies/{parts[1]}"
            else:
                continue
        else:
            continue
        span = link.select_one("span")
        name = clean_text(span) if span is not None else clean_text(link)
        if not name or path in seen:
            continue
        seen.add(path)
        found.append({"name": name, "path": path})
    return found


def _page_urls_for_category(category_path: str, max_pages: int) -> list[str]:
    """Build page URLs for one category.

    Args:
        category_path: e.g. ``/companies/86``.
        max_pages: Inclusive page budget starting at 1.

    Returns:
        list[str]: URLs ``/companies/86``, ``/companies/86/2``, ...
    """
    base = category_path.rstrip("/")
    return [base if page == 1 else f"{base}/{page}" for page in range(1, max_pages + 1)]


def extract_companies(
    client: HttpClient,
    *,
    max_pages_per_category: int = 5,
    listing_ckpt: ListingCheckpoint | None = None,
) -> list[CompanyCard]:
    """Extract unique companies from the directory.

    Args:
        client: HTTP client.
        max_pages_per_category: Hard cap on pages per category (inclusive).
        listing_ckpt: Optional page-level resume store.

    Returns:
        list[CompanyCard]: Deduplicated companies.

    Raises:
        HttpError: If the landing page cannot be fetched.
    """
    landing_html = client.get(COMPANIES_PATH)
    categories = discover_category_paths(landing_html, base_url=client.settings.base_url)
    if not categories:
        # Fallback: crawl /companies and /companies/{n}/{page} via BFS seeds
        categories = [{"name": "", "path": COMPANIES_PATH}]

    collected: list[CompanyCard] = []
    queue: deque[tuple[str, str, int]] = deque()
    # (url_path, category_name, page_number)
    for cat in categories:
        queue.append((cat["path"], cat["name"], 1))

    seen_pages: set[str] = set()
    while queue:
        path, category_name, page_num = queue.popleft()
        if path in seen_pages:
            continue
        if page_num > max_pages_per_category:
            continue
        if listing_ckpt is not None and listing_ckpt.is_page_done(path):
            continue
        seen_pages.add(path)
        try:
            html = client.get(path)
        except HttpError as exc:
            if exc.status_code in {404, 410}:
                continue
            raise

        source_url = client.settings.base_url.rstrip("/") + path
        cards = parse_company_cards(
            html,
            base_url=client.settings.base_url,
            source_url=source_url,
            category=category_name,
        )
        collected.extend(cards)
        if listing_ckpt is not None:
            listing_ckpt.mark_page_done(path)

        # If the page looks full, queue the next page.
        if len(cards) >= 12 and page_num < max_pages_per_category:
            next_path = f"{path.rstrip('/')}/{page_num + 1}"
            queue.append((next_path, category_name, page_num + 1))

    if listing_ckpt is not None:
        listing_ckpt.save()
    return dedupe_companies(collected)


def _rows(cards: Sequence[CompanyCard]) -> list[dict[str, Any]]:
    return [card.to_row() for card in cards]


def run_companies(
    client: HttpClient,
    data_dir: Path,
    *,
    resume_listings: bool = False,
) -> dict[str, Path]:
    """Extract companies and persist CSV/SQLite/BCP/JSONL artifacts.

    Args:
        client: HTTP client.
        data_dir: Output root.
        resume_listings: Skip listing pages already recorded in checkpoints.

    Returns:
        dict[str, Path]: Artifact paths by kind.
    """
    ckpt = None
    if resume_listings:
        ckpt = ListingCheckpoint(
            data_dir / "checkpoints" / "companies_pages.json",
            section="companies_pages",
            resume=True,
        )
    cards = extract_companies(client, listing_ckpt=ckpt)
    return persist_section(
        _rows(cards),
        data_dir=data_dir,
        name="companies",
        fieldnames=list(COMPANY_FIELDS),
    )
