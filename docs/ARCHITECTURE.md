# Architecture

## Layers

| Layer | Path | Responsibility |
|-------|------|----------------|
| Interface | `wikiplast.cli` | argv parsing, exit codes |
| Orchestration | `wikiplast.extractors` | which pages, how to persist |
| Domain | `wikiplast.domain` | pure HTML → model functions |
| Models | `wikiplast.models` | frozen dataclasses |
| Adapters | `wikiplast.adapters` | HTTP, CSV, SQLite, BCP |

Dependencies point inward only. Domain and models perform no I/O.

## HTTP policy

- Single `HttpClient` authority.
- Global min/max delay jitter between requests.
- `Retry-After` honored on 429.
- On 403 the session object is **replaced** (v0.1 only dropped a dict entry and kept using the blocked session).
- Paths under `ROBOTS_DISALLOWED_PREFIXES` (`/siteads/`) raise before any network I/O.

## Persistence

Each section writes three artifacts:

1. `data/csv/<section>.csv` — UTF-8 with BOM for Excel/SSMS GUI import.
2. `data/wikiplast.sqlite` table `<section>` — local queryable store.
3. `data/sqlserver/<section>.bcp.csv` — UTF-8, no BOM, `NULL` token for `BULK INSERT`.

## TDD rule

Every extractor ships with fixture HTML under `tests/fixtures/html/`. Unit tests never require the network. Live checks use the `network` marker only.
