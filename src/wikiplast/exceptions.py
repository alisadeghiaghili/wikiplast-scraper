"""Exception hierarchy for the wikiplast package.

All public APIs raise subclasses of :class:`WikiplastError`. Callers should
catch the narrowest type they can handle. Silent failure is not allowed.
"""

from __future__ import annotations


class WikiplastError(Exception):
    """Base error for all wikiplast failures."""


class ConfigurationError(WikiplastError):
    """Raised when settings or paths are invalid."""


class HttpError(WikiplastError):
    """Raised when an HTTP request cannot be completed usefully."""

    def __init__(self, message: str, *, url: str = "", status_code: int | None = None) -> None:
        """Initialize the HTTP error.

        Args:
            message: Human-readable failure description.
            url: Request URL when known.
            status_code: HTTP status code when the server responded.
        """
        super().__init__(message)
        self.url = url
        self.status_code = status_code


class RateLimitedError(HttpError):
    """Raised when the remote host returns HTTP 429 after retries."""


class BlockedError(HttpError):
    """Raised when the remote host returns HTTP 403 after retries."""


class ParseError(WikiplastError):
    """Raised when HTML cannot be interpreted as the expected structure."""

    def __init__(self, message: str, *, source: str = "") -> None:
        """Initialize the parse error.

        Args:
            message: Human-readable failure description.
            source: Path or URL of the HTML source when known.
        """
        super().__init__(message)
        self.source = source


class StorageError(WikiplastError):
    """Raised when writing or reading the local data store fails."""


class ValidationError(WikiplastError):
    """Raised when a model fails domain validation."""
