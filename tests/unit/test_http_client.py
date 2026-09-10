"""Unit tests for HttpClient policy (robots, retries, session rotation)."""

from __future__ import annotations

from typing import Any

import pytest
import requests

from wikiplast.adapters.http_client import HttpClient
from wikiplast.config import Settings
from wikiplast.exceptions import HttpError, RateLimitedError


class _FakeResponse:
    def __init__(self, status_code: int, text: str = "", headers: dict[str, str] | None = None) -> None:
        self.status_code = status_code
        self.text = text
        self.encoding = "utf-8"
        self.headers = headers or {}


class _FakeSession:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self._responses = list(responses)
        self.headers: dict[str, str] = {}
        self.calls = 0
        self.closed = False
        self.rotated_from: list[_FakeSession] = []

    def get(self, url: str, **kwargs: Any) -> _FakeResponse:
        self.calls += 1
        if not self._responses:
            raise AssertionError("no more fake responses")
        return self._responses.pop(0)

    def close(self) -> None:
        self.closed = True


def _settings() -> Settings:
    return Settings(min_delay=0.0, max_delay=0.0, max_retries=3, request_timeout=1.0)


def test_robots_disallowed_path_raises() -> None:
    """/siteads/ must never be fetched."""
    client = HttpClient(_settings(), session=_FakeSession([]))  # type: ignore[arg-type]
    with pytest.raises(HttpError, match="disallowed"):
        client.get("/siteads/123")


def test_get_success_returns_text() -> None:
    """HTTP 200 returns body text."""
    session = _FakeSession([_FakeResponse(200, "<html>ok</html>")])
    client = HttpClient(_settings(), session=session)  # type: ignore[arg-type]
    assert client.get("/prices") == "<html>ok</html>"
    assert session.calls == 1


def test_403_rotates_session_object() -> None:
    """After 403 the client must not keep using the blocked session.

    v0.1 popped the dict entry but kept the local session reference, so every
    retry hit the same blocked connection. This test pins the fix.
    """
    first = _FakeSession([_FakeResponse(403)])
    # The rotated session is created inside HttpClient via requests.Session.
    # We monkeypatch requests.Session to return a fake that succeeds.
    second = _FakeSession([_FakeResponse(200, "ok")])
    created: list[_FakeSession] = []

    def factory() -> _FakeSession:
        created.append(second)
        return second

    original = requests.Session
    try:
        requests.Session = factory  # type: ignore[misc, assignment]
        client = HttpClient(_settings(), session=first)  # type: ignore[arg-type]
        body = client.get("/npc-prices")
    finally:
        requests.Session = original  # type: ignore[misc]

    assert body == "ok"
    assert first.closed is True
    assert created and created[0] is second
    assert second.calls == 1


def test_429_raises_rate_limited_after_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    """Persistent 429 surfaces as RateLimitedError."""
    monkeypatch.setattr("time.sleep", lambda *_: None)
    session = _FakeSession([_FakeResponse(429)] * 3)
    client = HttpClient(_settings(), session=session)  # type: ignore[arg-type]
    with pytest.raises(RateLimitedError):
        client.get("/npc-prices")


def test_404_breaks_and_raises_http_error() -> None:
    """404 is terminal and raises HttpError."""
    session = _FakeSession([_FakeResponse(404)])
    client = HttpClient(_settings(), session=session)  # type: ignore[arg-type]
    with pytest.raises(HttpError) as info:
        client.get("/missing")
    assert info.value.status_code == 404
