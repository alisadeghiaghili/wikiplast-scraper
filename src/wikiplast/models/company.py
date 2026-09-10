"""Company directory domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CompanyCard:
    """A manufacturing unit listed on a companies directory page.

    Attributes:
        company_id: Stable numeric id parsed from ``/c{id}`` links.
        name: Display name (Persian).
        url: Absolute profile URL.
        contact_person: Contact name when present.
        website: Company website text as shown.
        rating: Raw rating text (may be empty).
        logo_url: Absolute or relative logo URL.
        verified: Whether a verification badge was present.
        category: Directory category label when known.
        source_url: Listing page URL this card was parsed from.
    """

    company_id: str
    name: str
    url: str
    contact_person: str
    website: str
    rating: str
    logo_url: str
    verified: bool
    category: str
    source_url: str

    def to_row(self) -> dict[str, Any]:
        """Convert to a flat dict suitable for CSV/SQL writers.

        Returns:
            dict[str, Any]: Column name to value mapping.
        """
        return asdict(self)
