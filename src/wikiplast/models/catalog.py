"""Petrochemical company domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PetroCompany:
    """A petrochemical producer listed on ``/petros`` or ``/polycats``.

    Attributes:
        company_id: Numeric id from ``/petros/{id}``.
        name: Display name.
        url: Absolute profile URL.
        grade_count: Number of grade links under the company block.
        grades: Semicolon-joined ``name (grade_id)`` list when present.
        source_url: Listing page URL.
    """

    company_id: str
    name: str
    url: str
    grade_count: int
    grades: str
    source_url: str

    def to_row(self) -> dict[str, Any]:
        """Convert to a flat dict for persistence.

        Returns:
            dict[str, Any]: Column mapping.
        """
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PolymerCategory:
    """A polymer family or subcategory from ``/polycats``.

    Attributes:
        category_id: Numeric id from ``/grides/{id}``.
        name: Category display name.
        url: Absolute category URL.
        parent_category: Parent family name, empty for top-level.
        parent_id: Parent family id, empty for top-level.
        description: Optional short description.
        source_url: Listing page URL.
    """

    category_id: str
    name: str
    url: str
    parent_category: str
    parent_id: str
    description: str
    source_url: str

    def to_row(self) -> dict[str, Any]:
        """Convert to a flat dict for persistence.

        Returns:
            dict[str, Any]: Column mapping.
        """
        return asdict(self)


@dataclass(frozen=True, slots=True)
class GradeListing:
    """A grade row from a category table (``/cat{id}``).

    Attributes:
        grade_id: Numeric id from ``/gradeprice/{id}``.
        name: Grade title.
        url: Absolute grade URL.
        petrochemical: Producer name.
        petrochemical_url: Absolute producer URL when present.
        datasheet_url: Absolute datasheet URL when present.
        category_id: Source category id.
        category_name: Source category name.
        source_url: Listing page URL.
    """

    grade_id: str
    name: str
    url: str
    petrochemical: str
    petrochemical_url: str
    datasheet_url: str
    category_id: str
    category_name: str
    source_url: str

    def to_row(self) -> dict[str, Any]:
        """Convert to a flat dict for persistence.

        Returns:
            dict[str, Any]: Column mapping.
        """
        return asdict(self)


@dataclass(frozen=True, slots=True)
class GradePricePoint:
    """One historical market price point from a grade detail page.

    Attributes:
        grade_id: Grade identifier.
        grade_name: Display name from the page title.
        as_of_jalali: Raw Jalali date text from the history table.
        as_of_iso: Converted ISO date when parseable.
        price_raw: Original price cell.
        price_value: Parsed integer or ``None``.
        currency: Currency code, ``IRR``.
        source_url: Absolute grade page URL.
    """

    grade_id: str
    grade_name: str
    as_of_jalali: str
    as_of_iso: str | None
    price_raw: str
    price_value: int | None
    currency: str
    source_url: str

    def to_row(self) -> dict[str, Any]:
        """Convert to a flat dict for persistence.

        Returns:
            dict[str, Any]: Column mapping.
        """
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CompanyProduct:
    """A product card from the products marketplace.

    Attributes:
        product_id: Stable id from ``/cp{id}`` or ``/products/{id}``.
        product_key: ``cp`` or ``products`` depending on URL family.
        name: Product title.
        url: Absolute product URL.
        image_url: Absolute image URL when present.
        company_id: Owning company id from the ``prdframe`` container when known.
        company_name: Owning company display name when known.
        view_count: Parsed view count when present (``/products/{id}`` cards).
        source_url: Listing page URL.
    """

    product_id: str
    product_key: str
    name: str
    url: str
    image_url: str
    company_id: str
    company_name: str
    view_count: int | None
    source_url: str

    def to_row(self) -> dict[str, Any]:
        """Convert to a flat dict for persistence.

        Returns:
            dict[str, Any]: Column mapping.
        """
        return asdict(self)
