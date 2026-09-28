"""Turns events into bronze rows as the Debezium -> Kafka -> loader path would deliver them.

Messiness, so staging's deduplication and ordering are tested for real:
- duplicates: the same event again at a new offset (at-least-once delivery),
- late rows: loaded_at up to 48 hours after occurred_at,
- rows loaded out of order within each simulated hour.
It uses its own seeded generator, so these knobs never change the business events.
"""

import csv
import json
import random
import zlib
from datetime import datetime, timedelta
from pathlib import Path

from generator.events import SCHEMA_VERSION, Event, to_ms
from generator.tenants import TenantSpec

PARTITIONS = 3
COLUMNS = (
    "tenant_id",
    "event_id",
    "event_type",
    "schema_version",
    "occurred_at",
    "aggregate_id",
    "trace_id",
    "payload",
    "topic",
    "kafka_partition",
    "kafka_offset",
    "loaded_at",
)


def bronze_rows(
    spec: TenantSpec, events: list[Event], seed: int, duplicate_rate: float, late_rate: float
) -> list[tuple]:
    rng = random.Random(f"{seed}/{spec.key}/load")
    staged: list[tuple[datetime, float, Event]] = []
    for e in events:
        if rng.random() < late_rate:
            delay = timedelta(seconds=rng.uniform(60, 48 * 3600))
        else:
            delay = timedelta(milliseconds=rng.randint(200, 5000))
        loaded_at = to_ms(e.occurred_at + delay)
        staged.append((loaded_at, rng.random(), e))
        if rng.random() < duplicate_rate:
            redelivered = to_ms(loaded_at + timedelta(seconds=rng.uniform(1, 7200)))
            staged.append((redelivered, rng.random(), e))

    # Within each hour of loading, rows arrive in no particular order.
    staged.sort(key=lambda s: (s[0].replace(minute=0, second=0, microsecond=0), s[1]))

    offsets: dict[tuple[str, int], int] = {}
    rows = []
    for loaded_at, _, e in staged:
        topic = f"tps.{spec.key}.{e.aggregate_type}"
        partition = zlib.crc32(e.aggregate_id.encode()) % PARTITIONS
        offset = offsets.get((topic, partition), 0)
        offsets[(topic, partition)] = offset + 1
        payload = json.dumps(e.payload, separators=(",", ":"), ensure_ascii=False)
        rows.append(
            (
                spec.tenant_id,
                e.event_id,
                e.event_type,
                SCHEMA_VERSION,
                e.occurred_at,
                e.aggregate_id,
                e.trace_id,
                payload,
                topic,
                partition,
                offset,
                loaded_at,
            )
        )
    return rows


def tenant_row(spec: TenantSpec, created_at: datetime) -> tuple:
    return (spec.tenant_id, spec.key, spec.name, spec.timezone, spec.currency, created_at)


def write_csv(out: Path, spec: TenantSpec, tenant: tuple, rows: list[tuple]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    with (out / f"{spec.key}.tenants.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(("tenant_id", "tenant_key", "name", "timezone", "currency", "created_at"))
        w.writerow([_csv(v) for v in tenant])
    with (out / f"{spec.key}.tps_events.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLUMNS)
        w.writerows([_csv(v) for v in row] for row in rows)


def _csv(v):
    return v.isoformat() if isinstance(v, datetime) else v


def load(conn, spec: TenantSpec, tenant: tuple, rows: list[tuple], reset: bool) -> None:
    """Upsert the tenant and COPY its rows into bronze, in one transaction."""
    with conn.transaction(), conn.cursor() as cur:
        cur.execute(
            """
            insert into platform.tenants
              (tenant_id, tenant_key, name, timezone, currency, created_at)
            values (%s, %s, %s, %s, %s, %s)
            on conflict (tenant_id) do update
              set tenant_key = excluded.tenant_key, name = excluded.name,
                  timezone = excluded.timezone, currency = excluded.currency
            """,
            tenant,
        )
        if reset:
            # Dev only: the one place bronze is ever deleted from.
            cur.execute("delete from bronze.tps_events where tenant_id = %s", (spec.tenant_id,))
        else:
            cur.execute(
                "select exists (select from bronze.tps_events where tenant_id = %s)",
                (spec.tenant_id,),
            )
            if cur.fetchone()[0]:
                raise SystemExit(
                    f"{spec.key} already has rows in bronze.tps_events; use --reset to replace them"
                )
        with cur.copy(f"copy bronze.tps_events ({', '.join(COLUMNS)}) from stdin") as copy:
            for row in rows:
                copy.write_row(row)
    # Planner statistics now rather than whenever autovacuum gets to it: without them the
    # first dbt build on a fresh volume can pick plans that run for many minutes.
    conn.execute("analyze bronze.tps_events")
