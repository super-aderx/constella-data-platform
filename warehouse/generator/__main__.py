"""python -m generator: write TPS-contract events for the dev tenants into bronze.

Stands in for StarMart, Debezium, Kafka and the loader until the real loader exists (P2).
"""

import argparse
import os
import sys
import time
from datetime import date, timedelta
from pathlib import Path

from generator.load import bronze_rows, load, tenant_row, write_csv
from generator.simulate import simulate
from generator.tenants import all_tenants


def parse_args(argv: list[str]) -> argparse.Namespace:
    tenants = all_tenants()
    p = argparse.ArgumentParser(prog="python -m generator", description=__doc__)
    p.add_argument("--tenant", choices=[*tenants, "all"], default="all")
    p.add_argument("--days", type=int, default=400, help="simulated days ending at --end")
    p.add_argument(
        "--end",
        type=date.fromisoformat,
        default=date(2026, 9, 26),
        help="last complete local day; the next day is written up to 09:00 as in progress",
    )
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--reset", action="store_true", help="delete the tenant's bronze rows first")
    p.add_argument("--duplicate-rate", type=float, default=0.02)
    p.add_argument("--late-rate", type=float, default=0.01)
    p.add_argument("--out", type=Path, help="write CSV files here instead of loading")
    return p.parse_args(argv)


def main(argv: list[str]) -> None:
    args = parse_args(argv)
    tenants = all_tenants()
    specs = list(tenants.values()) if args.tenant == "all" else [tenants[args.tenant]]

    conn = None
    if args.out is None:
        import psycopg

        url = os.environ.get("WAREHOUSE_ADMIN_URL")
        if not url:
            raise SystemExit("WAREHOUSE_ADMIN_URL is not set (see .env.example)")
        conn = psycopg.connect(url, autocommit=True)

    for spec in specs:
        started = time.perf_counter()
        events, stats = simulate(spec, args.days, args.end, args.seed)
        rows = bronze_rows(spec, events, args.seed, args.duplicate_rate, args.late_rate)
        created_at = events[0].occurred_at - timedelta(days=1)
        tenant = tenant_row(spec, created_at)
        if conn is None:
            write_csv(args.out, spec, tenant, rows)
        else:
            load(conn, spec, tenant, rows, args.reset)
        print(
            f"{spec.key}: {stats.customers:,} customers, {stats.orders:,} orders "
            f"({stats.paid:,} paid, {stats.cancelled:,} cancelled), {stats.events:,} events, "
            f"{len(rows):,} bronze rows in {time.perf_counter() - started:.1f}s"
        )
    if conn is not None:
        conn.close()


if __name__ == "__main__":
    main(sys.argv[1:])
