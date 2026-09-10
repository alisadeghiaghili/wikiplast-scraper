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

## v0.4.0 (current)

- [x] Bourse deals `/deals`
- [x] Bourse offers `/offers`
- [x] Behinyab status `/byab`
- [x] Company quotas `/behinyab` + `/behin.php?page=N` with early-stop
- [x] Base-price compare `/compare`
- [x] Info-bourse metrics + top demand/volume `/info-bourse`
- [x] Unit tests on HTML fixtures

## v0.5.0 (next)

- [ ] News, articles, events, media, tv, ads (not `/siteads/`), topco, colleague, honors, wikiboss, feeds, categories
- [ ] Network integration smoke tests (marked)

## v0.6.0

- [ ] Detail crawls, resume/checkpoint, coverage report, tagged release automation
