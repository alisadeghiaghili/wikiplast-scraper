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


# Named delay profiles (min_delay, max_delay) in seconds.
RATE_PROFILES: dict[str, tuple[float, float]] = {
    "conservative": (2.0, 4.0),
    "default": (1.0, 2.5),
    "fast": (0.5, 1.2),
}
DEFAULT_RATE_PROFILE = "default"


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
        rate_profile: Named profile used for delays (informational).
    """

    base_url: str = DEFAULT_BASE_URL
    data_dir: Path = DEFAULT_DATA_DIR
    request_timeout: float = 20.0
    min_delay: float = 1.0
    max_delay: float = 2.5
    max_retries: int = 3
    max_workers: int = 2
    user_agent: str = DEFAULT_USER_AGENT
    rate_profile: str = DEFAULT_RATE_PROFILE

    @classmethod
    def from_env(cls, *, rate_profile: str | None = None) -> Settings:
        """Build settings from environment variables with safe defaults.

        Environment variables:
            WIKIPLAST_BASE_URL: Override origin.
            WIKIPLAST_DATA_DIR: Override output directory.
            WIKIPLAST_MIN_DELAY / WIKIPLAST_MAX_DELAY: Rate limits in seconds.
            WIKIPLAST_MAX_WORKERS: Concurrency cap.
            WIKIPLAST_RATE_PROFILE: Named profile (``conservative`` | ``default`` | ``fast``).

        Args:
            rate_profile: Optional CLI override of the named profile.
                Explicit ``WIKIPLAST_MIN_DELAY`` / ``WIKIPLAST_MAX_DELAY``
                still win over the profile defaults.

        Returns:
            Settings: Effective configuration.
        """
        base_url = os.environ.get("WIKIPLAST_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
        data_dir = Path(os.environ.get("WIKIPLAST_DATA_DIR", str(DEFAULT_DATA_DIR)))
        profile_name = (
            rate_profile
            or os.environ.get("WIKIPLAST_RATE_PROFILE", DEFAULT_RATE_PROFILE)
        ).lower()
        if profile_name not in RATE_PROFILES:
            profile_name = DEFAULT_RATE_PROFILE
        profile_min, profile_max = RATE_PROFILES[profile_name]
        min_delay = float(os.environ.get("WIKIPLAST_MIN_DELAY", str(profile_min)))
        max_delay = float(os.environ.get("WIKIPLAST_MAX_DELAY", str(profile_max)))
        max_workers = int(os.environ.get("WIKIPLAST_MAX_WORKERS", "2"))
        if max_delay < min_delay:
            max_delay = min_delay
        return cls(
            base_url=base_url,
            data_dir=data_dir,
            min_delay=min_delay,
            max_delay=max_delay,
            max_workers=max_workers,
            rate_profile=profile_name,
        )


# Sections that robots.txt explicitly disallows. Never fetch these paths.
ROBOTS_DISALLOWED_PREFIXES: tuple[str, ...] = ("/siteads/",)
