# Roadmap

## v0.2.0

- [x] Package layout + pyproject + ruff/mypy/pytest config
- [x] HttpClient with real 403 session rotation and robots guard
- [x] Storage: CSV + SQLite + SQL Server BCP export
- [x] Price parsers: npc, archive (`/prices` + alias), market (gated flag)
- [x] Companies dedupe by `company_id` + queue-based pagination
- [x] Unit tests on HTML fixtures (no network)

## v0.3.0

- [x] Petrochemicals `/petros` (dedupe by company id)
- [x] Polymer categories `/polycats` (parents + children)
- [x] Category grades `/cat{id}` via `/grides/{id}` discovery
- [x] Grade price history `/gradeprice/{id}` (Jalali → ISO)
- [x] Products `/products` (`.proditem` /cp + `.nibox` /products/{id}; view_count separate from company)
- [x] Early-stop when a products page yields no new ids
- [x] Unit tests on HTML fixtures

## v0.4.0

- [x] Bourse deals `/deals`
- [x] Bourse offers `/offers`
- [x] Behinyab status `/byab`
- [x] Company quotas `/behinyab` + `/behin.php?page=N` with early-stop
- [x] Base-price compare `/compare`
- [x] Info-bourse metrics + top demand/volume `/info-bourse`
- [x] Unit tests on HTML fixtures

## v0.5.0

- [x] News `/archive-news` with early-stop pagination
- [x] Articles `/articles` (dedupe including ادامه مطلب)
- [x] Events `/events`
- [x] Honors `/honors`
- [x] Classified ads `/ads` + featured `/starads` (never `/siteads/`)
- [x] Featured companies `/topco`
- [x] Manager profiles `/wikiboss` (`/b{id}`)
- [x] RSS `/feeds`
- [x] Unit tests on HTML fixtures

## v0.6.0

- [x] News/article/company detail parsers
- [x] Checkpoint resume store (`data/checkpoints/*.json`)
- [x] Coverage report (`data/coverage.json`)
- [x] CLI `--section details`, `--detail-limit`, `--no-resume`
- [x] Network smoke tests (`pytest -m network`)

## v0.7.0

- [x] Listing resume for news/articles/events/companies (`--resume-listings`)
- [x] JSONL export alongside CSV/SQLite/BCP
- [x] GitHub Actions CI (ruff + unit tests, Python 3.11/3.12)
- [x] Unit tests for listing resume and JSONL

## v0.8.0

- [x] Media catalog `/media/{slug}`
- [x] Training videos `/tv` → `/videos/{id}`
- [x] `wikiplast report` inventory command
- [x] Unit tests for media parsers and report

Parquet export deferred: JSONL + BCP already cover SQL Server / pandas loads
without adding a heavy `pyarrow` dependency.

## v0.9.0 (current)

- [x] Rate-limit profiles (`conservative` / `default` / `fast`)
- [x] `--section snapshot` public bundle (prices, deals, offers, news, RSS, media)
- [x] Live snapshot run (2026-09-10): 428 npc, 63 archive, 128 market, 4 deals, 7 offers, 39 news, 100 feeds, 12 media, 6 videos
- [x] Unit tests for profiles and coverage labeling

## v1.0.0 (next)

- [ ] Full companies + catalog live crawl with resume into SQL Server staging
- [ ] Typed SQL Server DDL generator from data dictionary
- [ ] Tag `v1.0.0` after one clean production extract

