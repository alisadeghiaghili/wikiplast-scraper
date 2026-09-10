# Roadmap

## v0.2.0 (current)

- [x] Package layout + pyproject + ruff/mypy/pytest config
- [x] HttpClient with real 403 session rotation and robots guard
- [x] Storage: CSV + SQLite + SQL Server BCP export
- [x] Price parsers: npc, archive (`/prices` + alias), market (gated flag)
- [x] Companies dedupe by `company_id` + queue-based pagination
- [x] Unit tests on HTML fixtures (no network)

## v0.3.0 (next)

- [ ] Petrochemicals `/petros`
- [ ] Polymer categories `/polycats`, `/cat{id}`
- [ ] Grades `/gradeprice/{id}`, `/g{id}`
- [ ] Products `/products`
- [ ] Network integration smoke tests (marked)

## v0.4.0

- [ ] Bourse: `/deals`, `/offers`, `/byab`, `/behinyab`, `/compare`, `/info-bourse`
- [ ] Charts `/chart/...`, `/diagram/...`

## v0.5.0

- [ ] News, articles, events, media, tv, ads (not `/siteads/`), topco, colleague, honors, wikiboss, feeds, categories

## v0.6.0

- [ ] Detail crawls, resume/checkpoint, coverage report, tagged release automation
