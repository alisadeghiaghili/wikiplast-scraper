"""Pure HTML parsing helpers shared by domain parsers."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

_WS_RE = re.compile(r"\s+")
_NUMBER_RE = re.compile(r"-?\d[\d,]*")


def parse_html(html: str | bytes) -> BeautifulSoup:
    """Parse HTML into a BeautifulSoup tree using lxml.

    Args:
        html: Raw HTML text or bytes.

    Returns:
        BeautifulSoup: Parsed document.
    """
    return BeautifulSoup(html, "lxml")


def clean_text(node: Tag | None) -> str:
    """Collapse whitespace in an element's text.

    Args:
        node: BeautifulSoup node or ``None``.

    Returns:
        str: Stripped text, empty when ``node`` is ``None``.
    """
    if node is None:
        return ""
    return _WS_RE.sub(" ", node.get_text(" ", strip=True)).strip()


def absolute_url(base_url: str, href: str | None) -> str:
    """Resolve ``href`` against ``base_url``.

    Args:
        base_url: Origin such as ``https://wikiplast.ir``.
        href: Relative or absolute href; may be empty.

    Returns:
        str: Absolute URL, or empty string when href is empty.
    """
    if not href:
        return ""
    href = href.strip()
    if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
        return ""
    return urljoin(base_url.rstrip("/") + "/", href.lstrip("/"))


def parse_int_price(raw: str | None) -> int | None:
    """Parse a Persian-market price string like ``192,000`` into an integer.

    Args:
        raw: Raw cell text. Dashes and empty strings mean missing.

    Returns:
        int | None: Parsed integer, or ``None`` when missing/unparseable.

    Examples:
        >>> parse_int_price("192,000")
        192000
        >>> parse_int_price("-")
        >>> parse_int_price("")
    """
    if raw is None:
        return None
    text = raw.strip()
    if not text or text in {"-", "—", "–", "N/A", "n/a"}:
        return None
    match = _NUMBER_RE.search(text.replace("٬", ","))
    if not match:
        return None
    digits = match.group(0).replace(",", "")
    try:
        return int(digits)
    except ValueError:
        return None


def first_int(text: str | None) -> int | None:
    """Extract the first integer from free text.

    Args:
        text: Arbitrary string.

    Returns:
        int | None: First integer found, else ``None``.
    """
    if not text:
        return None
    match = re.search(r"\d+", text)
    if not match:
        return None
    return int(match.group(0))


def path_from_url(url: str) -> str:
    """Return the path component of a URL without a trailing slash.

    Args:
        url: Absolute or relative URL.

    Returns:
        str: Path, or ``/`` when empty.
    """
    parsed = urlparse(url)
    return parsed.path.rstrip("/") or "/"


def select_all(root: BeautifulSoup | Tag, selector: str) -> list[Tag]:
    """CSS-select and return only Tag results.

    Args:
        root: Soup or element root.
        selector: CSS selector.

    Returns:
        list[Tag]: Matching tags in document order.
    """
    nodes: list[Any] = root.select(selector)
    return [n for n in nodes if isinstance(n, Tag)]
