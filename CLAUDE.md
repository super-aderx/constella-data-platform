# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

The Constella data platform: StarMart (TPS, the transactional shop, one deployment per tenant) → bronze → dbt (silver, gold, serving) → Constellate (BI). The design lives in Constellate's `spec.md`, `warehouse_spec.md` (wins where they differ) and `tps_spec.md` (owns the event contract). Only **P0** is built: the local warehouse, the event generator, the dbt project and CI. P1 (promotions: bundles, coupons, discounts, `daily_promotion`) and P2 (Kafka loader, incremental models, Dagster) are specified there but not built.

## Commands

Everything runs from `warehouse/` (the uv project) with the repo-root `.env` (copy `.env.example`):

- Warehouse: `docker compose up -d warehouse` from the repo root (postgres:17, host port 5433; init SQL in `warehouse/postgres/init/` runs only on a fresh volume, so `docker compose down -v` to re-run it). Needs the external network: `docker network create constella-net` once.
- Load: `uv run --env-file ../.env python -m generator --tenant all --reset` (`--days`, `--end`, `--seed`, `--duplicate-rate`, `--late-rate`, `--out DIR` for CSV).
- dbt, from `warehouse/dbt/`: `uv run --env-file ../../.env dbt build`; one model and its tests: `dbt build -s int_orders`. `dbt deps` once.
- Tests: `uv run pytest` (generator), `uv run --env-file ../.env python scripts/acceptance.py` (P0 acceptance, needs a default 400-day load), `uv run --env-file ../.env python scripts/replay_check.py [--days N]` (reloads bronze twice).
- Lint: `uv run ruff check --fix`, `uv run ruff format`; sqlfluff must run in two places because it only takes the dbt templater from a `.sqlfluff` in the working directory: `uv run sqlfluff lint postgres` in `warehouse/`, `uv run sqlfluff lint models tests analyses` in `warehouse/dbt/` (inherits `warehouse/.sqlfluff`).

## Architecture

- **Bronze** (`bronze.tps_events`): one row per Kafka message, append-only, duplicates and late rows expected. Business time is `occurred_at`, never `loaded_at`. Only the generator's `--reset` deletes from it.
- **Staging** (`models/staging/tps`, views in `silver`): `stg_tps__events` is the only model reading bronze; it keeps the first copy of each `(tenant_id, event_id)`. One view per event family casts the payload and keeps `schema_version = 1`.
- **Intermediate** (tables in `silver`): state rebuilt from events. SCD2 for products and prices (no dbt snapshots: events already carry history). `int_orders` derives status (paid wins; orders belong to the local day they were placed). `int_order_segments` gives each paid order the customer's RFM segment on the day before, with window functions; nothing daily is stored.
- **Marts** (tables in `gold`): `core` dims and facts, `sales` and `network` daily aggregates, `platform.tenant_freshness`. Aggregates hold only additive columns; ratios and distinct counts are computed from sums at query time, and "all customers" is the sum over segments.
- **Serving** (views in `serving`): one per mart the API reads, filtered on `{{ current_tenant() }}`, with enforced contracts, `security_barrier`, and `select` granted to `api_reader`. Constella is a dbt exposure on them.
- **Tenancy**: every key and join includes `tenant_id` (SKUs are unique only within a tenant; use the `tenant_relationships` test, not `relationships`, for tenant-scoped foreign keys). Days are local: `{{ local_day(ts, tz) }}`. Keep Postgres-specific SQL in staging and macros.
- **Roles** (init SQL): `loader` inserts into bronze; `dbt_runner` reads bronze and platform and owns silver, gold, serving and meta; `api_reader` reads serving, `meta.pipeline_runs` and `platform.tenants`, never gold.
- `on-run-end` writes one row per build, run or seed to `meta.pipeline_runs`. Intermediate and mart tables `analyze` themselves in a post-hook, and the generator analyzes bronze after loading: without statistics, a fresh volume's first build picks plans that run for many minutes.

## Generator

- Deterministic: the same arguments give identical rows. Business events come from a generator seeded by `(seed, tenant)`; loading messiness (duplicates, late rows, shuffled load order, offsets) has its own seeded generator in `load.py`, so changing `--duplicate-rate` or `--late-rate` never changes business data. Keep it that way: don't draw from `Simulation.rng` in load code, and don't add random draws in the middle of the simulation without re-running the acceptance checks, since every later draw shifts.
- Tenant specs (`generator/tenants/`) set the catalog, basket themes with per-product pick chances, planted bridges and volumes; personas (`personas.py`) set order rhythm, basket size, pauses and churn. Harbor Street's themes must come out as Louvain communities (weight `lift`, seed 42, `min_co_orders` 5, `min_lift` 1.0), with Whole Milk, Cheddar and Eggs or Parmesan as articulation points; cross-theme pairs stay below lift 1, so avoid anything that adds products to baskets independently of themes.
- RFM thresholds are dbt vars (`dbt_project.yml`, `vars.rfm`), tuned so each segment gets at least 3% of Harbor Street's 90-day orders. Changing personas or thresholds means re-running `scripts/acceptance.py`.

## Conventions

- SQL: lowercase, trailing commas, explicit `as` aliases, 2-space indents, 100 columns (see `warehouse/.sqlfluff`). Generic tests use the `arguments:` form.
- Money is `bigint` cents; `count(*)` and sums are cast (`::int`, `::bigint`) so serving contracts hold.
- Changing a serving view's columns is a contract change: coordinate with the Constellate backend.

## CI

`.github/workflows/ci.yml` runs `hooks` (prek, skipping ruff and sqlfluff), `warehouse` (`warehouse.yml`: postgres:17 service with the init SQL applied by `psql`, `uv sync --locked`, ruff, pytest, sqlfluff with PR annotations, a 120-day generator load, `dbt build`, the replay check) and `ci-passes`, the one check to require. Actions are pinned to commit SHAs with the release in a comment. `uv sync` can't use `--no-build`: dbt-core depends on the sdist-only `dbt-core-experimental-parser`.
