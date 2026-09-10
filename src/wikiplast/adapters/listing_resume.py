"""Listing-level resume support built on CheckpointStore."""

from __future__ import annotations

from pathlib import Path

from wikiplast.adapters.checkpoint import CheckpointStore


def page_key(path: str) -> str:
    """Build a stable checkpoint key for a listing page path.

    Args:
        path: Site-relative path such as ``/archive-news/2``.

    Returns:
        str: Checkpoint key ``page:<path>``.
    """
    normalized = path if path.startswith("/") else f"/{path}"
    return f"page:{normalized}"


class ListingCheckpoint:
    """Track completed listing pages for resume.

    Args:
        path: Checkpoint JSON path.
        section: Section name stored in the file.
        resume: When False, prior page keys are discarded.
    """

    def __init__(self, path: Path, *, section: str, resume: bool = True) -> None:
        """Initialize and optionally resume page progress."""
        self._store = CheckpointStore(path)
        self._store.start_section(section, resume=resume)

    @property
    def store(self) -> CheckpointStore:
        """Return the underlying checkpoint store."""
        return self._store

    def is_page_done(self, path: str) -> bool:
        """Return True when a listing page was already processed.

        Args:
            path: Site-relative page path.

        Returns:
            bool: Membership of the page key.
        """
        return self._store.is_done(page_key(path))

    def mark_page_done(self, path: str) -> None:
        """Mark a listing page as processed.

        Args:
            path: Site-relative page path.
        """
        self._store.mark_done(page_key(path))

    def save(self) -> None:
        """Persist progress to disk."""
        self._store.save()

    def page_count(self) -> int:
        """Return how many pages are recorded as done.

        Returns:
            int: Page count.
        """
        return self._store.count()
