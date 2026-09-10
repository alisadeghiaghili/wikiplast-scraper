# Data dictionary (v0.2.0)

## npc_prices / archive_prices / market_prices

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| source | TEXT | no | `npc` \| `archive` \| `market` |
| polymer_category | TEXT | yes | Persian family label from page section |
| grade_name | TEXT | no | Grade label |
| producer | TEXT | yes | Producer when shown |
| price_raw | TEXT | yes | Original cell text |
| price_value | INTEGER | yes | Parsed integer; `NULL` when missing/gated |
| currency | TEXT | no | `IRR` for domestic tables |
| is_gated | INTEGER | no | 1 when the live cell did not expose a number due to subscription |
| as_of_date | TEXT | yes | Jalali `YYYY-MM-DD` from page title, or day label for market matrix |
| source_url | TEXT | no | Absolute page URL |

## companies

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| company_id | TEXT | yes | Numeric id from `/c{id}`; unique after dedupe |
| name | TEXT | no | Display name |
| url | TEXT | no | Absolute profile URL |
| contact_person | TEXT | yes | |
| website | TEXT | yes | As displayed (not always a full URL) |
| rating | TEXT | yes | Raw score text |
| logo_url | TEXT | yes | Absolute when a logo exists |
| verified | INTEGER | no | 0/1 |
| category | TEXT | yes | First category seen for this company |
| source_url | TEXT | no | Listing page |

## SQL Server notes

- BCP files use `NULL` as the missing-value token; stage then `NULLIF(col, 'NULL')`.
- Booleans are `0`/`1`.
- Jalali dates are kept as text; convert in T-SQL or Python when building a Gregorian calendar dimension.
