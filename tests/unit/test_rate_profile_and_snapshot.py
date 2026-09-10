"""Unit tests for rate profiles and public snapshot helpers."""

from __future__ import annotations

from wikiplast.adapters.coverage import build_coverage_report
from wikiplast.config import RATE_PROFILES, Settings


def test_rate_profile_names() -> None:
    """Named profiles expose conservative/default/fast delays."""
    assert set(RATE_PROFILES) >= {"conservative", "default", "fast"}
    assert RATE_PROFILES["conservative"][0] > RATE_PROFILES["default"][0]
    assert RATE_PROFILES["default"][0] > RATE_PROFILES["fast"][0]


def test_settings_from_env_profile(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """CLI profile selects delay bounds; env overrides still win."""
    monkeypatch.delenv("WIKIPLAST_MIN_DELAY", raising=False)
    monkeypatch.delenv("WIKIPLAST_MAX_DELAY", raising=False)
    settings = Settings.from_env(rate_profile="conservative")
    assert settings.rate_profile == "conservative"
    assert settings.min_delay == RATE_PROFILES["conservative"][0]

    monkeypatch.setenv("WIKIPLAST_MIN_DELAY", "0.1")
    monkeypatch.setenv("WIKIPLAST_MAX_DELAY", "0.2")
    overridden = Settings.from_env(rate_profile="conservative")
    assert overridden.min_delay == 0.1
    assert overridden.max_delay == 0.2

    unknown = Settings.from_env(rate_profile="turbo")
    assert unknown.rate_profile == "default"


def test_snapshot_coverage_payload() -> None:
    """Coverage report can label a public snapshot run."""
    report = build_coverage_report(
        tables={"npc_prices": 500, "bourse_deals": 12},
        started_at="2026-01-01T00:00:00+00:00",
        extra={"section": "public_snapshot"},
    )
    assert report["total_rows"] == 512
    assert report["extra"]["section"] == "public_snapshot"
