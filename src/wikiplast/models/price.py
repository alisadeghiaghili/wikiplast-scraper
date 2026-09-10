"""Price-related domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PriceObservation:
    """A single market/base price observation scraped from a public page.

    Attributes:
        source: Logical source key (``npc``, ``market``, ``archive``, ...).
        polymer_category: Persian polymer family label when present.
        grade_name: Grade or product label as shown on the page.
        producer: Producer name when shown.
        price_raw: Original price cell text.
        price_value: Parsed integer price or ``None`` when missing/gated.
        currency: ISO-like currency code when known (``IRR``).
        is_gated: True when the live cell did not expose a numeric price
            because authentication/subscription is required.
        as_of_date: ISO date string from the page title when parsed.
        source_url: Absolute URL of the page this row came from.
    """

    source: str
    polymer_category: str
    grade_name: str
    producer: str
    price_raw: str
    price_value: int | None
    currency: str
    is_gated: bool
    as_of_date: str | None
    source_url: str

    def to_row(self) -> dict[str, Any]:
        """Convert to a flat dict suitable for CSV/SQL writers.

        Returns:
            dict[str, Any]: Column name to value mapping.
        """
        return asdict(self)
