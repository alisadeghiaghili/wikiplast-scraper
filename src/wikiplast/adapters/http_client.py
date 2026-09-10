"""HTTP client with polite rate limiting and real session recovery.

This module is the single authority for talking to wikiplast.ir. Extractors
must not create their own ``requests.Session`` instances.
"""

from __future__ import annotations

import random
import threading
import time
from collections.abc import Mapping

import requests

from wikiplast.config import ROBOTS_DISALLOWED_PREFIXES, Settings
from wikiplast.domain.html_parsing import path_from_url
from wikiplast.exceptions import BlockedError, HttpError, RateLimitedError


class HttpClient:
    """Polite HTTP client bound to one origin.

    Args:
        settings: Runtime settings (timeouts, delays, retries).
        session: Optional pre-built session (used in tests).
    """

    def __init__(
        self,
        settings: Settings,
        session: requests.Session | None = None,
    ) -> None:
        """Initialize the client and its lock."""
        self._settings = settings
        self._session = session or requests.Session()
        self._lock = threading.Lock()
        self._last_request_at = 0.0
        self._session.headers.update({"User-Agent": settings.user_agent})

    @property
    def settings(self) -> Settings:
        """Return the bound settings."""
        return self._settings

    def close(self) -> None:
        """Close the underlying session."""
        self._session.close()

    def __enter__(self) -> HttpClient:
        """Enter a context manager block.

        Returns:
            HttpClient: Self.
        """
        return self

    def __exit__(self, *args: object) -> None:
        """Exit the context manager and close the session."""
        self.close()

    def _assert_allowed(self, url: str) -> None:
        path = path_from_url(url)
        for prefix in ROBOTS_DISALLOWED_PREFIXES:
            if path.startswith(prefix):
                raise HttpError(f"Path disallowed by robots.txt: {path}", url=url)

    def _throttle(self) -> None:
        with self._lock:
            now = time.monotonic()
            wait = self._settings.min_delay - (now - self._last_request_at)
            if wait > 0:
                time.sleep(wait)
            # jitter up to max_delay-min_delay
            extra = self._settings.max_delay - self._settings.min_delay
            if extra > 0:
                time.sleep(random.uniform(0.0, extra))
            self._last_request_at = time.monotonic()

    def _rotate_session(self) -> None:
        """Replace the session after a hard block.

        Rebuilding the session drops cookies and connection pool state so the
        next attempt is not stuck on a banned TCP/TLS fingerprint from the
        caller's perspective. This is the real fix for the v0.1 bug that kept
        using the blocked session object after HTTP 403.
        """
        old = self._session
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": self._settings.user_agent})
        old.close()

    def get(
        self,
        path_or_url: str,
        *,
        headers: Mapping[str, str] | None = None,
    ) -> str:
        """GET a page and return decoded HTML.

        Args:
            path_or_url: Absolute URL or site-relative path starting with ``/``.
            headers: Optional extra headers merged over defaults.

        Returns:
            str: Response body as text (UTF-8).

        Raises:
            HttpError: Request failed after all retries or non-recoverable status.
            RateLimitedError: HTTP 429 persisted after retries.
            BlockedError: HTTP 403 persisted after retries.
            HttpError: Path is disallowed by robots.txt.
        """
        if path_or_url.startswith(("http://", "https://")):
            url = path_or_url
        else:
            url = self._settings.base_url.rstrip("/") + "/" + path_or_url.lstrip("/")

        self._assert_allowed(url)

        last_status: int | None = None
        last_error: str = ""
        for attempt in range(self._settings.max_retries):
            self._throttle()
            try:
                response = self._session.get(
                    url,
                    headers=dict(headers or {}),
                    timeout=self._settings.request_timeout,
                )
            except requests.Timeout as exc:
                last_error = f"timeout: {exc}"
                time.sleep(2**attempt)
                continue
            except requests.ConnectionError as exc:
                last_error = f"connection: {exc}"
                time.sleep(2**attempt)
                continue
            except requests.RequestException as exc:
                last_error = f"request: {exc}"
                time.sleep(2**attempt)
                continue

            last_status = response.status_code
            if response.status_code == 200:
                response.encoding = "utf-8"
                return response.text
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                wait = float(retry_after) if retry_after and retry_after.isdigit() else 10.0 + attempt * 5
                time.sleep(wait)
                last_error = "rate limited"
                continue
            if response.status_code == 403:
                self._rotate_session()
                time.sleep(5.0 + attempt * 5)
                last_error = "blocked"
                continue
            last_error = f"HTTP {response.status_code}"
            if response.status_code in {404, 410}:
                break

        message = f"GET failed for {url}: {last_error}"
        if last_status == 429:
            raise RateLimitedError(message, url=url, status_code=last_status)
        if last_status == 403:
            raise BlockedError(message, url=url, status_code=last_status)
        raise HttpError(message, url=url, status_code=last_status)
