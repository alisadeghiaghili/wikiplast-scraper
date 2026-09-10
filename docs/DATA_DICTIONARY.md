# Data dictionary (v0.4.0)

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

## petro_companies

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| company_id | TEXT | no | `/petros/{id}` |
| name | TEXT | no | |
| url | TEXT | no | Absolute |
| grade_count | INTEGER | no | |
| grades | TEXT | yes | `name (id); ...` |
| source_url | TEXT | no | `/petros` or `/polycats` |

## polymer_categories

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| category_id | TEXT | no | `/grides/{id}` |
| name | TEXT | no | |
| url | TEXT | no | |
| parent_category | TEXT | yes | Empty for top-level families |
| parent_id | TEXT | yes | Empty for top-level |
| description | TEXT | yes | |
| source_url | TEXT | no | `/polycats` |

## category_grades

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| grade_id | TEXT | no | `/gradeprice/{id}` |
| name | TEXT | no | |
| url | TEXT | no | |
| petrochemical | TEXT | yes | |
| petrochemical_url | TEXT | yes | |
| datasheet_url | TEXT | yes | Empty when site shows `-` |
| category_id | TEXT | no | |
| category_name | TEXT | yes | |
| source_url | TEXT | no | `/cat{id}` |

## grade_price_history

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| grade_id | TEXT | no | |
| grade_name | TEXT | yes | From page title |
| as_of_jalali | TEXT | no | Raw date text |
| as_of_iso | TEXT | yes | Jalali `YYYY-MM-DD` when parsed |
| price_raw | TEXT | yes | |
| price_value | INTEGER | yes | |
| currency | TEXT | no | `IRR` |
| source_url | TEXT | no | |

## products

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| product_id | TEXT | no | From `/cp{id}` or `/products/{id}` |
| product_key | TEXT | no | `cp` \| `products` |
| name | TEXT | no | |
| url | TEXT | no | |
| image_url | TEXT | yes | |
| company_id | TEXT | yes | From `prdframe#comp{id}` when present |
| company_name | TEXT | yes | Banner text or `fa-cog` sibling — never the view count |
| view_count | INTEGER | yes | Only on `.nibox` cards |
| source_url | TEXT | no | |

## SQL Server notes

- BCP files use `NULL` as the missing-value token; stage then `NULLIF(col, 'NULL')`.
- Booleans are `0`/`1`.
- Jalali dates are kept as text; convert in T-SQL or Python when building a Gregorian calendar dimension.

## bourse_deals (`/deals`)

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| polymer_category | TEXT | yes | Category banner |
| grade_name | TEXT | no | |
| avg_price_rial | INTEGER | yes | |
| supply_tons | INTEGER | yes | |
| traded_tons | INTEGER | yes | |
| contract_type | TEXT | yes | e.g. cash contract note |
| as_of_iso | TEXT | yes | Jalali from page title |
| source_url | TEXT | no | |

## bourse_offers (`/offers`)

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| polymer_category | TEXT | yes | |
| grade_name | TEXT | no | |
| base_price_rial | INTEGER | yes | |
| base_qty | INTEGER | yes | |
| max_increase | INTEGER | yes | |
| as_of_iso | TEXT | yes | |
| source_url | TEXT | no | |

## byab_status (`/byab`)

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| product_name | TEXT | no | |
| category_id | TEXT | yes | `/cat{id}` |
| category_url | TEXT | yes | |
| status | TEXT | yes | |
| monthly_purchase_cap | TEXT | yes | |
| valid_from | TEXT | yes | Jalali text |
| diagram_url | TEXT | yes | |
| as_of_iso | TEXT | yes | |
| source_url | TEXT | no | |

## company_quotas (`/behinyab`, `/behin.php`)

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| row_number | TEXT | yes | |
| unit_name | TEXT | no | |
| national_code | TEXT | yes | |
| material_name | TEXT | yes | |
| material_code | TEXT | yes | |
| annual_performance | TEXT | yes | |
| calculated_quota | TEXT | yes | |
| page | INTEGER | no | Source page number |
| source_url | TEXT | no | |

## price_comparisons (`/compare`)

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| polymer_category | TEXT | yes | |
| grade_name | TEXT | no | |
| grade_id | TEXT | yes | `/g{id}` |
| grade_url | TEXT | yes | |
| base_price_prev | INTEGER | yes | Previous week Rials |
| base_price_current | INTEGER | yes | Current week Rials |
| change_abs | TEXT | yes | |
| change_pct | TEXT | yes | |
| global_usd_per_ton | TEXT | yes | |
| source_url | TEXT | no | |

## bourse_metrics (`/info-bourse`)

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| metric_key | TEXT | no | snake_case key |
| metric_label | TEXT | yes | |
| metric_value_raw | TEXT | yes | |
| metric_value_num | INTEGER | yes | |
| source_url | TEXT | no | |

## bourse_top_products (`/info-bourse`)

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| rank_list | TEXT | no | `demand` \| `volume` |
| product_name | TEXT | no | |
| category_id | TEXT | yes | |
| category_url | TEXT | yes | |
| amount_tons | TEXT | yes | |
| amount_value | INTEGER | yes | |
| source_url | TEXT | no | |

