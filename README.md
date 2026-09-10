# wikiplast-scraper

Public-page extraction toolkit for [wikiplast.ir](https://wikiplast.ir).

**Version:** 0.8.0

## Status

| Area | State |
|------|--------|
| Package layout (`src/wikiplast`) | done |
| HTTP client (rate limit, 403 rotation, robots) | done |
| Storage: CSV + SQLite + SQL Server BCP + JSONL | done |
| Price extractors: `npc`, `archive` (`/prices`), `market` | done |
| Companies extractor with dedupe + real pagination queue | done |
| Catalog: petros, polymer categories, category grades, grade history, products | done |
| Bourse: deals, offers, byab, company quotas, compare, info-bourse | done |
| Content: news, articles, events, honors, ads, topco, managers, RSS | done |
| Details + resume/checkpoint + coverage report + network smoke tests | done |
| Listing resume + GitHub Actions CI | done |
| Media/TV catalogs + `wikiplast report` inventory | done |

## Honest data notes

- `/market-prices` exposes grade/day **structure** to anonymous clients; numeric cells are often placeholders (`قیمت`) and are stored with `is_gated=1`.
- Full market archive requires a paid subscription. This tool does **not** bypass paywalls.
- `/siteads/` is disallowed by `robots.txt` and is never fetched.
- v0.1 shipped a companies file with ~37× duplicate rows. v0.2+ deduplicates by `company_id`.
- `/products/2` currently mirrors page 1 for anonymous clients; the extractor stops when a page yields no new product ids.

## Install

```bash
python -m pip install -e ".[dev]"
```

## Usage

```bash
# All public sections implemented in this version
wikiplast extract --section all --data-dir data

# Prices only
wikiplast extract --section prices --data-dir data

# Companies only
wikiplast extract --section companies --data-dir data

# Catalog (petros / polycats / grades / products)
wikiplast extract --section catalog --data-dir data

# Bourse (deals / offers / byab / quotas / compare / info-bourse)
wikiplast extract --section bourse --data-dir data

# Content (news / articles / events / honors / ads / topco / managers / RSS)
wikiplast extract --section content --data-dir data

# Media and training videos
wikiplast extract --section media --data-dir data

# Inventory report (CSV counts, SQLite/BCP/JSONL presence, coverage)
wikiplast report --data-dir data

# Detail pages with resume checkpoints (opt-in; not part of --section all)
wikiplast extract --section details --data-dir data --detail-limit 20
wikiplast extract --section details --data-dir data --no-resume --detail-limit 5

# Smoke: fewer grade-detail pages and quota pages
wikiplast extract --section catalog --grade-history-limit 5 --max-categories 3
wikiplast extract --section bourse --max-quota-pages 2
wikiplast extract --section content --max-list-pages 3
```

## Output layout

```text
data/
├── csv/                  # UTF-8-BOM CSV (Excel / pandas)
├── sqlserver/            # UTF-8 CSV with NULL token for BULK INSERT
├── jsonl/                # JSON Lines (one object per line)
├── checkpoints/          # resume state for details and listings
├── wikiplast.sqlite      # local warehouse (table per section)
```

### Sections written by `catalog`

| Table | Source |
|-------|--------|
| `petro_companies` | `/petros` |
| `polymer_categories` | `/polycats` |
| `category_grades` | `/cat{id}` via `/grides/{id}` |
| `grade_price_history` | `/gradeprice/{id}` (capped) |
| `products` | `/products` `.proditem` + `.nibox` |

### SQL Server import (BCP)

```sql
BULK INSERT dbo.npc_prices
FROM 'C:\path\to\data\sqlserver\npc_prices.bcp.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    CODEPAGE = '65001',
    TABLOCK
);
-- Then NULLIF text 'NULL' columns as needed when staging to typed tables.
```

## Development

```bash
python -m pytest
python -m ruff check src tests
```

Network tests are opt-in:

```bash
python -m pytest -m network
```

## Architecture

```text
cli → extractors → domain (pure parsers) → models
                 ↘ adapters (http, storage)
```

See `docs/ARCHITECTURE.md` and `docs/DATA_DICTIONARY.md`.

## License

MIT
