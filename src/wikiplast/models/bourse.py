"""Bourse / IME market domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class BourseDeal:
    """One executed polymer trade row from ``/deals``.

    Attributes:
        polymer_category: Category banner text for this row group.
        grade_name: Grade label.
        avg_price_rial: Average trade price in Rials.
        supply_tons: Offered volume in tons.
        traded_tons: Traded volume in tons.
        contract_type: Contract note when present (e.g. cash).
        as_of_iso: Jalali ISO date from the page title when parsed.
        source_url: Absolute page URL.
    """

    polymer_category: str
    grade_name: str
    avg_price_rial: int | None
    supply_tons: int | None
    traded_tons: int | None
    contract_type: str
    as_of_iso: str | None
    source_url: str

    def to_row(self) -> dict[str, Any]:
        """Convert to a flat dict for persistence.

        Returns:
            dict[str, Any]: Column mapping.
        """
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BourseOffer:
    """One polymer offer row from ``/offers``.

    Attributes:
        polymer_category: Category banner text.
        grade_name: Grade label.
        base_price_rial: Base price in Rials.
        base_qty: Base quantity as shown.
        max_increase: Maximum increase field as shown.
        as_of_iso: Jalali ISO date from the page title when parsed.
        source_url: Absolute page URL.
    """

    polymer_category: str
    grade_name: str
    base_price_rial: int | None
    base_qty: int | None
    max_increase: int | None
    as_of_iso: str | None
    source_url: str

    def to_row(self) -> dict[str, Any]:
        """Convert to a flat dict for persistence.

        Returns:
            dict[str, Any]: Column mapping.
        """
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ByabStatus:
    """Behinyab (tozin) status for one product family from ``/byab``.

    Attributes:
        product_name: Product family name.
        category_id: ``/cat{id}`` id when linked.
        category_url: Absolute category URL.
        status: Status label (e.g. non-behinyab).
        monthly_purchase_cap: Monthly purchase ceiling text.
        valid_from: Valid-from date text (Jalali).
        diagram_url: Absolute diagram URL when present.
        as_of_iso: Jalali ISO date from page title when parsed.
        source_url: Absolute page URL.
    """

    product_name: str
    category_id: str
    category_url: str
    status: str
    monthly_purchase_cap: str
    valid_from: str
    diagram_url: str
    as_of_iso: str | None
    source_url: str

    def to_row(self) -> dict[str, Any]:
        """Convert to a flat dict for persistence.

        Returns:
            dict[str, Any]: Column mapping.
        """
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CompanyQuota:
    """Company quota row from ``/behinyab`` / ``/behin.php`` pages.

    Attributes:
        row_number: Source row index when present.
        unit_name: Company / unit name.
        national_code: National id text.
        material_name: Material name.
        material_code: Material code text.
        annual_performance: Performance column text.
        calculated_quota: Quota column text.
        page: Source page number.
        source_url: Absolute page URL.
    """

    row_number: str
    unit_name: str
    national_code: str
    material_name: str
    material_code: str
    annual_performance: str
    calculated_quota: str
    page: int
    source_url: str

    def to_row(self) -> dict[str, Any]:
        """Convert to a flat dict for persistence.

        Returns:
            dict[str, Any]: Column mapping.
        """
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BasePriceComparison:
    """Weekly base-price comparison row from ``/compare``.

    Attributes:
        polymer_category: Category banner text.
        grade_name: Grade label.
        grade_id: ``/g{id}`` when present.
        grade_url: Absolute grade URL.
        base_price_prev: Previous week base price (Rials).
        base_price_current: Current week base price (Rials).
        change_abs: Absolute change text.
        change_pct: Percent change text.
        global_usd_per_ton: Global USD/ton text when present.
        source_url: Absolute page URL.
    """

    polymer_category: str
    grade_name: str
    grade_id: str
    grade_url: str
    base_price_prev: int | None
    base_price_current: int | None
    change_abs: str
    change_pct: str
    global_usd_per_ton: str
    source_url: str

    def to_row(self) -> dict[str, Any]:
        """Convert to a flat dict for persistence.

        Returns:
            dict[str, Any]: Column mapping.
        """
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BourseInfographicMetric:
    """One scalar metric from the ``/info-bourse`` summary tiles.

    Attributes:
        metric_key: Stable snake_case key.
        metric_label: Original Persian label fragment.
        metric_value_raw: Raw value text.
        metric_value_num: Parsed integer when possible.
        source_url: Absolute page URL.
    """

    metric_key: str
    metric_label: str
    metric_value_raw: str
    metric_value_num: int | None
    source_url: str

    def to_row(self) -> dict[str, Any]:
        """Convert to a flat dict for persistence.

        Returns:
            dict[str, Any]: Column mapping.
        """
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BourseTopProduct:
    """Top demand or volume product from ``/info-bourse``.

    Attributes:
        rank_list: ``demand`` or ``volume``.
        product_name: Product name.
        category_id: ``/cat{id}`` when linked.
        category_url: Absolute category URL.
        amount_tons: Amount text / parsed tons.
        amount_value: Parsed integer when possible.
        source_url: Absolute page URL.
    """

    rank_list: str
    product_name: str
    category_id: str
    category_url: str
    amount_tons: str
    amount_value: int | None
    source_url: str

    def to_row(self) -> dict[str, Any]:
        """Convert to a flat dict for persistence.

        Returns:
            dict[str, Any]: Column mapping.
        """
        return asdict(self)
