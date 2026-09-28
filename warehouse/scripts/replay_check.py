"""Replay check: bronze replayed with far more duplicates and late rows gives the same gold.

Loads every tenant with the generator's default messiness, builds, snapshots gold, reloads
the same business events with --duplicate-rate 0.2 --late-rate 0.05, builds again, and
compares every gold table both ways with EXCEPT ALL. Leaves the warehouse in the replayed
state. Needs WAREHOUSE_ADMIN_URL and the DBT_PG_* variables.

    uv run --env-file ../.env python scripts/replay_check.py [--days 400]
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

import psycopg

WAREHOUSE = Path(__file__).resolve().parents[1]
SNAPSHOT = "replay_check"
# Columns that legitimately differ between builds.
VOLATILE = {"refreshed_at"}


def run(*args: str, cwd: Path = WAREHOUSE) -> None:
    print("$", " ".join(args), flush=True)
    subprocess.run(args, cwd=cwd, check=True)


def load_and_build(days: int, *messiness: str) -> None:
    run(sys.executable, "-m", "generator", "--reset", "--days", str(days), *messiness)
    run("dbt", "build", "--quiet", cwd=WAREHOUSE / "dbt")


def gold_tables(conn) -> dict[str, list[str]]:
    rows = conn.execute(
        """
        select c.table_name, c.column_name
        from information_schema.columns as c
        join information_schema.tables as t using (table_schema, table_name)
        where c.table_schema = 'gold' and t.table_type = 'BASE TABLE'
        order by c.table_name, c.ordinal_position
        """
    ).fetchall()
    tables: dict[str, list[str]] = {}
    for table, column in rows:
        if column not in VOLATILE:
            tables.setdefault(table, []).append(column)
    return tables


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=400)
    args = p.parse_args()
    conn = psycopg.connect(os.environ["WAREHOUSE_ADMIN_URL"], autocommit=True)

    load_and_build(args.days)
    tables = gold_tables(conn)
    conn.execute(f"drop schema if exists {SNAPSHOT} cascade")
    conn.execute(f"create schema {SNAPSHOT}")
    for table, columns in tables.items():
        cols = ", ".join(f'"{c}"' for c in columns)
        conn.execute(f"create table {SNAPSHOT}.{table} as select {cols} from gold.{table}")

    load_and_build(args.days, "--duplicate-rate", "0.2", "--late-rate", "0.05")
    differences = 0
    for table, columns in tables.items():
        cols = ", ".join(f'"{c}"' for c in columns)
        diff = conn.execute(
            f"""
            select
              (select count(*) from (select {cols} from gold.{table}
                 except all select {cols} from {SNAPSHOT}.{table}) as added),
              (select count(*) from (select {cols} from {SNAPSHOT}.{table}
                 except all select {cols} from gold.{table}) as removed)
            """
        ).fetchone()
        status = "same" if diff == (0, 0) else f"DIFFERENT (+{diff[0]} -{diff[1]})"
        print(f"  gold.{table}: {status}")
        differences += sum(diff)
    conn.execute(f"drop schema {SNAPSHOT} cascade")
    conn.close()
    if differences:
        raise SystemExit("Replay changed gold")
    print("Replay check passed: gold is identical")


if __name__ == "__main__":
    main()
