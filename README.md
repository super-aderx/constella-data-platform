# constella-data-platform

The bridge between StarMart (the transactional shop, one deployment per tenant) and Constellate
(the BI app). StarMart publishes business events; this repo loads them unchanged into a Postgres
warehouse and builds, with dbt, the tables Constellate reads (ELT).

```
StarMart outbox ──(Debezium, Kafka, loader: P2)──▶ bronze ──dbt──▶ silver ──▶ gold ──▶ serving ──▶ Constellate API
                  └─(generator: dev stand-in, now)─┘
```

Until StarMart and the real loader exist, `python -m generator` writes StarMart-shaped v1 events
straight into bronze. Everything from bronze on is the production design.

## Layout

```
docker-compose.yml        # the warehouse: postgres:17 on host port 5433
.env.example              # dev credentials and connection strings
warehouse/
  postgres/init/          # roles, schemas, platform.tenants, bronze, meta (run on a fresh volume)
  generator/              # python -m generator: dev tenants' events into bronze
  dbt/                    # staging → intermediate (schema silver) → marts (gold) → serving
  scripts/                # acceptance.py (P0 checks), replay_check.py (CI)
  tests/                  # generator tests (pytest)
```

## Run it

Needs Docker and [uv](https://docs.astral.sh/uv/).

```bash
cp .env.example .env
docker network create constella-net     # once; shared with StarMart's stack
docker compose up -d warehouse
cd warehouse
uv sync
uv run --env-file ../.env python -m generator --tenant all --reset   # ~30 s
cd dbt
uv run --env-file ../../.env dbt deps
uv run --env-file ../../.env dbt build                               # ~40 s, models + tests
cd ..
uv run --env-file ../.env python scripts/acceptance.py               # P0 acceptance checks
```

Two dev tenants: `harbor-street` (Asia/Taipei, the frontend's store, ~270 paid orders a day) and
`maple-corner` (America/Los_Angeles, the backend's sample catalog, ~150 a day), 400 days ending
2026-09-26.

## What Constellate reads

Only the `serving` schema (and `meta.pipeline_runs`, `platform.tenants`), as `api_reader`:

| View | Grain |
|---|---|
| `serving.categories`, `serving.products` | tenant, category / sku |
| `serving.daily_orders` | tenant, day, segment |
| `serving.daily_product` | tenant, day, segment, sku |
| `serving.daily_pair` | tenant, day, segment, sku_a < sku_b |
| `serving.freshness` | tenant (`last_complete_day` is the latest day to show) |
| `serving.segments` | segment (not tenant-scoped) |

Each tenant-scoped view filters on `app.tenant_id`, so the API starts every transaction with
`select set_config('app.tenant_id', <uuid>, true)` and also filters `tenant_id` in every query.
Without it set, the views return no rows. The views have enforced dbt contracts: changing their
columns is a breaking change for Constellate.

## Checks

- `uv run pytest`: generator determinism and payload invariants.
- `dbt build`: generic, singular and unit tests (dedupe, order status, local days, RFM rules).
- `scripts/replay_check.py`: bronze replayed with 20% duplicates and late rows gives identical gold.
- `scripts/acceptance.py`: tenant isolation through `api_reader`, Harbor Street's 90-day volume,
  RFM segment shares, Louvain communities and bridge products.
- Lint: `ruff` (Python), `sqlfluff` (init SQL from `warehouse/`, dbt SQL from `warehouse/dbt/`).
  Git hooks via `prek install`.
