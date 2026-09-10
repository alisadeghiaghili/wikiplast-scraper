"""Runtime configuration for the wikiplast extractor.

Values here are the single authority for rate limits, timeouts, and output
layout. Extractors must not hard-code competing constants.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_BASE_URL = "https://wikiplast.ir"
DEFAULT_DATA_DIR = Path("data")
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable runtime settings.

    Attributes:
        base_url: Origin of wikiplast without a trailing slash.
        data_dir: Directory that receives CSV/SQLite artifacts.
        request_timeout: Per-request timeout in seconds.
        min_delay: Minimum seconds between requests to the same host.
        max_delay: Maximum seconds between requests (includes jitter).
        max_retries: Attempts per URL including the first try.
        max_workers: Upper bound for concurrent fetches (keep low).
        user_agent: Default User-Agent string.
    """

    base_url: str = DEFAULT_BASE_URL
    data_dir: Path = DEFAULT_DATA_DIR
    request_timeout: float = 20.0
    min_delay: float = 1.0
    max_delay: float = 2.5
    max_retries: int = 3
    max_workers: int = 2
    user_agent: str = DEFAULT_USER_AGENT

    @classmethod
    def from_env(cls) -> Settings:
        """Build settings from environment variables with safe defaults.

        Environment variables:
            WIKIPLAST_BASE_URL: Override origin.
            WIKIPLAST_DATA_DIR: Override output directory.
            WIKIPLAST_MIN_DELAY / WIKIPLAST_MAX_DELAY: Rate limits in seconds.
            WIKIPLAST_MAX_WORKERS: Concurrency cap.

        Returns:
            Settings: Effective configuration.
        """
        base_url = os.environ.get("WIKIPLAST_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
        data_dir = Path(os.environ.get("WIKIPLAST_DATA_DIR", str(DEFAULT_DATA_DIR)))
        min_delay = float(os.environ.get("WIKIPLAST_MIN_DELAY", "1.0"))
        max_delay = float(os.environ.get("WIKIPLAST_MAX_DELAY", "2.5"))
        max_workers = int(os.environ.get("WIKIPLAST_MAX_WORKERS", "2"))
        if max_delay < min_delay:
            max_delay = min_delay
        return cls(
            base_url=base_url,
            data_dir=data_dir,
            min_delay=min_delay,
            max_delay=max_delay,
            max_workers=max_workers,
        )


# Sections that robots.txt explicitly disallows. Never fetch these paths.
ROBOTS_DISALLOWED_PREFIXES: tuple[str, ...] = ("/siteads/",)
