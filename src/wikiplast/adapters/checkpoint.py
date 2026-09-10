"""Resume checkpoints for long-running extractors."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from wikiplast.exceptions import StorageError


class CheckpointStore:
    """JSON-backed set of completed entity ids for one section.

    Args:
        path: Filesystem path of the checkpoint JSON.
    """

    def __init__(self, path: Path) -> None:
        """Initialize the store path and empty state."""
        self._path = path
        self._completed: set[str] = set()
        self._section = ""
        if path.exists():
            self._load()

    @property
    def path(self) -> Path:
        """Return the checkpoint file path."""
        return self._path

    @property
    def completed_ids(self) -> frozenset[str]:
        """Return the frozen set of completed ids."""
        return frozenset(self._completed)

    def _load(self) -> None:
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise StorageError(f"Cannot read checkpoint {self._path}: {exc}") from exc
        self._section = str(raw.get("section") or "")
        ids = raw.get("completed_ids") or []
        self._completed = {str(i) for i in ids}

    def start_section(self, section: str, *, resume: bool) -> None:
        """Bind the store to a section, optionally resuming prior progress.

        Args:
            section: Section key, e.g. ``news_details``.
            resume: When False, prior completed ids are discarded.
        """
        if resume and self._section == section:
            return
        if not resume or self._section != section:
            self._section = section
            self._completed = set()

    def is_done(self, entity_id: str) -> bool:
        """Return True when the entity was already processed.

        Args:
            entity_id: Stable entity identifier.

        Returns:
            bool: Membership in the completed set.
        """
        return entity_id in self._completed

    def mark_done(self, entity_id: str) -> None:
        """Record an entity as completed (in memory).

        Args:
            entity_id: Stable entity identifier.
        """
        self._completed.add(entity_id)

    def save(self) -> None:
        """Persist completed ids to disk.

        Raises:
            StorageError: When the file cannot be written.
        """
        payload: dict[str, Any] = {
            "section": self._section,
            "completed_ids": sorted(self._completed),
            "updated_at": datetime.now(UTC).isoformat(),
        }
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            raise StorageError(f"Cannot write checkpoint {self._path}: {exc}") from exc

    def count(self) -> int:
        """Return the number of completed ids.

        Returns:
            int: Completed id count.
        """
        return len(self._completed)
